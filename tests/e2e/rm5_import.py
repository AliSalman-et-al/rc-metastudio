"""Real-menu RM5 import, cancellation and persistence proof."""
import copy
import xml.etree.ElementTree as ET
import csv
import subprocess
from unittest.mock import patch
from PyQt6 import QtCore, QtWidgets
from tests.python.gui.qt_test_support import mouse_click

from rc_metastudio.project.adapter import dataset_to_project
from scripts.verification_evidence import desktop_tool_executable


def run(app, window, ROOT, WORK, record_step):
    from rc_metastudio.importing.revman import read_rm5
    rscript = desktop_tool_executable("Rscript")
    source = ROOT / 'tests/fixtures/rm5/Fleiss1993.rm5'
    original = ET.parse(source).getroot()
    # Synthetic counts in the structure observed in Bristol's real DTA review.
    dta_source = ROOT / 'tests/fixtures/rm5/dta-derived.rm5'
    dta_xml = ET.parse(dta_source).getroot()
    for case in ('missing-count', 'zero-counts'):
        root = copy.deepcopy(dta_xml)
        entry = next(root.iter('TEST_DATA_ENTRY'))
        if case == 'missing-count':
            del entry.attrib['TP']
        else:
            for key in ('TP', 'FN', 'FP', 'TN'):
                entry.set(key, '0')
        path = WORK / f'dta-{case}.rm5'
        ET.ElementTree(root).write(path)
        if case == 'missing-count':
            try:
                read_rm5(path)
            except ValueError as error:
                assert 'TP' in str(error) and 'missing' in str(error), str(error)
                record_step('rm5-dta-missing-count', window, error=str(error), input=str(path))
            else:
                raise AssertionError('A missing diagnostic count was accepted')
        else:
            imported = read_rm5(path)
            row = imported.dataset.sheets[0].rows[0]
            assert not row.include
            assert row.analysis_unit.get_raw_data_for_arm(imported.dataset.sheets[0].arms[0].name) == [0, 0, 0, 0]
            record_step('rm5-dta-zero-counts-pending', window, input=str(path))
    dta_names = {s.get('ID'): s.get('NAME') for s in dta_xml.iter('STUDY')}
    expected_dta = [(t.findtext('NAME'), [(dta_names[r.get('STUDY_ID')],
                    [int(r.attrib[k]) for k in ('TP', 'FN', 'FP', 'TN')])
                    for r in t.findall('TEST_DATA/TEST_DATA_ENTRY')])
                    for t in dta_xml.findall('ANALYSES_AND_DATA/TESTS/TEST')]
    from rc_metastudio.importing.revman_review import review_rm5
    def dta_review():
        dialog = app.activeModalWidget()
        table = dialog.findChild(QtWidgets.QTableWidget)
        assert [table.item(i, 0).text() for i in range(table.rowCount())] == [n for n, _ in expected_dta]
        record_step('rm5-dta-review', dialog)
        dialog.accept()
    QtCore.QTimer.singleShot(0, dta_review)
    dta_import = read_rm5(dta_source)
    assert review_rm5(dta_import, window)
    window.set_model(dta_import.dataset)
    for sheet, (name, rows) in zip(window.model.dataset.sheets, expected_dta):
        assert sheet.name == name
        assert [(r.label, next(iter(r.analysis_unit.arms.values())).raw_data) for r in sheet.rows] == rows
    assert len(window.model.dataset.sheets) == len(expected_dta)
    from rc_metastudio.analysis.diagnostic_metrics_dialog import DiagnosticMetricsDialog
    from rc_metastudio.analysis.setup_dialog import AnalysisSetupDialog
    from rc_metastudio.results.window import ResultsWindow
    window.action_go.trigger()
    app.processEvents()
    metrics = next(w for w in app.topLevelWidgets() if isinstance(w, DiagnosticMetricsDialog) and w.isVisible())
    metrics.btn_ok.click()
    app.processEvents()
    setup = next(w for w in app.topLevelWidgets() if isinstance(w, AnalysisSetupDialog) and w.isVisible())
    record_step('rm5-dta-default-setup', setup, method=setup.current_method)
    setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).click()
    app.processEvents()
    view = next(w for w in app.topLevelWidgets() if isinstance(w, ResultsWindow) and w.isVisible())
    record_step('rm5-dta-results', view, texts=dict(view.texts))
    view.close()
    dta_project = dataset_to_project(window.model.dataset)
    destination = WORK / 'dta-import.rcms'
    with patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(str(destination), '')):
        window.action_save_as.trigger()
    assert window.open(str(destination), raise_on_error=True)
    assert dataset_to_project(window.model.dataset) == dta_project
    record_step('rm5-dta-reopened', window, project=str(destination))
    subgroup_source = ROOT / 'tests/fixtures/rm5/Fleiss1993-subgroups-derived.rm5'
    subgroup_import = read_rm5(subgroup_source)
    subgroup_sheet = subgroup_import.dataset.sheets[0]
    assert len(subgroup_sheet.covariates) == 1
    covariate = subgroup_sheet.covariates[0]['id']
    groups = {row.label: row.covariate_values[covariate] for row in subgroup_sheet.rows}
    subgroup_xml = ET.parse(subgroup_source).getroot()
    expected_groups = {row.get('STUDY_ID'): group.findtext('NAME')
                       for group in subgroup_xml.iter('DICH_SUBGROUP')
                       for row in group.iter('DICH_DATA')}
    study_names = {study.get('ID'): study.get('NAME') for study in subgroup_xml.iter('STUDY')}
    assert groups == {study_names[row.get('STUDY_ID')]: expected_groups.get(row.get('STUDY_ID'), '')
                      for row in subgroup_xml.iter('DICH_DATA')}

    subgroup_reference = WORK / 'subgroup-read-rm5.csv'
    subprocess.run([rscript,
                    str(ROOT / 'tests/e2e/rm5_reference.R'), str(subgroup_source),
                    str(subgroup_reference), str(WORK / 'subgroup-metacr.csv')], check=True)
    with subgroup_reference.open(encoding="utf-8", newline="") as stream:
        for ref in csv.DictReader(stream):
            if ref['type'] == 'D':
                # read.rm5 prefixes group labels with comparison/outcome/group numbers.
                assert ref['grplab'].endswith(groups[ref['studlab']])
    window.set_model(subgroup_import.dataset)
    record_step('rm5-subgroup-covariate-imported', window, groups=groups,
                reference=str(subgroup_reference))
    from tests.fit_observations import observe_fit
    from rc_metastudio.analysis.subgroup_dialog import SubgroupAnalysisDialog
    from rc_metastudio.analysis.setup_dialog import AnalysisSetupDialog
    from rc_metastudio.results.window import ResultsWindow
    # read.rm5 omits the ungrouped row: compare identical study sets.
    for row in subgroup_sheet.rows:
        row.include = bool(row.covariate_values[covariate])
    subgroup_sheet.settings['analysis'] = dict(method='binary.fixed.inv.var',
        parameters={}, fixed_effects=True, covariates=[])
    window.set_model(subgroup_import.dataset)
    window.action_subgroup_ma.trigger()
    app.processEvents()
    selector = next(w for w in app.topLevelWidgets() if isinstance(w, SubgroupAnalysisDialog) and w.isVisible())
    assert selector.covariate_combo_box.currentText() == subgroup_sheet.covariates[0]['name']
    selector.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).click()
    app.processEvents()
    setup = next(w for w in app.topLevelWidgets() if isinstance(w, AnalysisSetupDialog) and w.isVisible())
    setup.method_cbo_box.setCurrentIndex(setup.method_cbo_box.findData('binary.fixed.inv.var'))
    assert setup.current_method == 'binary.fixed.inv.var'
    with observe_fit() as fit:
        setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).click()
        app.processEvents()
    view = next(w for w in app.topLevelWidgets() if isinstance(w, ResultsWindow) and w.isVisible())
    actual = list(map(float, fit.evaluate('unlist(lapply(result$res[1:2], function(x) c(x$b[1], x$ci.lb, x$ci.ub)))')))
    reference = WORK / 'subgroup-fit.csv'
    subprocess.run([rscript, '-e',
        "library(meta); x <- read.rm5(commandArgs(TRUE)[1]); m <- metacr(x, outcome.no=1, method='Inverse'); write.csv(data.frame(estimate=m$TE.common.w, lower=m$lower.common.w, upper=m$upper.common.w, Q=m$Q.b.common, p=m$pval.Q.b.common), commandArgs(TRUE)[2], row.names=FALSE, fileEncoding='UTF-8')",
        str(subgroup_source), str(reference)], check=True)
    with reference.open(encoding="utf-8", newline="") as stream:
        refs = list(csv.DictReader(stream))
    expected = [float(row[key]) for row in refs for key in ('estimate', 'lower', 'upper')]
    test = list(map(float, fit.evaluate('local({e <- new.env(); load(paste0(result$plot_params_paths[[1]], ".plotdata"), envir=e); t <- e$plot.data$subgroups$difference_test; c(t$QM, t$QMp)})')))
    actual.extend(test)
    expected.extend(float(refs[0][key]) for key in ('Q', 'p'))
    differences = [a - b for a, b in zip(actual, expected)]
    record_step('rm5-subgroup-results', view, actual=actual, expected=expected,
                differences=differences, reference=str(reference))
    assert len(actual) == len(expected) == 8
    assert all(abs(delta) <= 1e-6 for delta in differences[:6]), differences
    assert all(abs(delta) <= 1e-6 for delta in differences[6:]), differences
    view.close()
    failures = []
    from rc_metastudio.analysis.setup_dialog import AnalysisSetupDialog
    window.set_model(read_rm5(source).dataset)
    for index, method in enumerate(('binary.fixed.mh', 'continuous.fixed')):
        window.sheet_tabs.setCurrentIndex(index)
        window.action_go.trigger()
        app.processEvents()
        dialog = next(w for w in app.topLevelWidgets() if isinstance(w, AnalysisSetupDialog) and w.isVisible())
        if dialog.current_method != method:
            failures.append(f'method {index}: {dialog.current_method} != {method}')
        dialog.reject()

    for case in ('pending', 'year-empty', 'year-suffix', 'duplicate'):
        root = copy.deepcopy(original)
        if case == 'pending':
            row = next(root.iter('DICH_DATA'))
            for key in list(row.attrib):
                if key.startswith(('EVENTS_', 'TOTAL_')):
                    row.set(key, '0' if key.startswith('TOTAL_') else '')
        elif case.startswith('year'):
            next(root.iter('STUDY')).set('YEAR', '' if case == 'year-empty' else '1999a')
        else:
            comparison = next(root.iter('COMPARISON'))
            comparison.append(copy.deepcopy(next(root.iter('DICH_OUTCOME'))))
        path = WORK / f'{case}.rm5'
        ET.ElementTree(root).write(path)
        try:
            imported = read_rm5(path)
            if case == 'pending':
                assert not imported.dataset.sheets[0].rows[0].include
                assert imported.dataset.sheets[0].rows[0].label
                assert all(v is None for arm in imported.dataset.sheets[0].rows[0].analysis_unit.arms.values() for v in arm.raw_data)
            if case.startswith('year'):
                expected_years = {study.get('NAME'): int(study.get('YEAR') or '') if (study.get('YEAR') or '').isdigit() else None
                                  for study in root.iter('STUDY')}
                affected = [row for sheet in imported.dataset.sheets for row in sheet.rows]
                assert affected, ('year variant has no imported study', case)
                assert all(row.year == expected_years[row.label] for row in affected), (case, [(row.label, row.year) for row in affected], expected_years)
            if case == 'duplicate':
                assert imported.dataset.sheets[-1].name == imported.dataset.sheets[0].name + ' (2)'
        except (ValueError, KeyError, AssertionError) as error:
            failures.append(f'{case}: {error}')
    for source_method, random, expected_method in (('IV', 'YES', 'binary.random'), ('MH', 'YES', None), ('PETO', 'NO', 'binary.fixed.peto')):
        root = copy.deepcopy(original)
        outcome = next(root.iter('DICH_OUTCOME'))
        outcome.set('METHOD', source_method)
        outcome.set('RANDOM', random)
        path = WORK / f'method-{source_method}-{random}.rm5'
        ET.ElementTree(root).write(path)
        imported = read_rm5(path)
        sheet = imported.dataset.sheets[0]
        window.set_model(imported.dataset)
        window.action_go.trigger()
        app.processEvents()
        dialog = next(w for w in app.topLevelWidgets() if isinstance(w, AnalysisSetupDialog) and w.isVisible())
        assert dialog.current_method == (expected_method or 'binary.random')
        if expected_method == 'binary.random':
            assert dialog.current_param_vals['rm.method'] == 'DL'
        record_step('rm5-method-combination', dialog, source_method=source_method, random=random, selected=dialog.current_method)
        dialog.reject()
        assert sheet.settings.get('analysis', {}).get('method') == expected_method
        if expected_method == 'binary.random':
            assert sheet.settings['analysis']['parameters']['rm.method'] == 'DL'
        if expected_method is None:
            assert any('unavailable' in d for d in imported.differences)
    assert not failures, failures
    with patch.object(window, 'prompt_to_save_unsaved_data', return_value=QtWidgets.QMessageBox.StandardButton.Discard):
        assert window.open(str(ROOT / 'sample_projects/amino.rcms'), raise_on_error=True)
    window.model.setData(window.model.index(0, window.model.NAME), 'Dirty study', QtCore.Qt.ItemDataRole.EditRole)
    before = dataset_to_project(window.model.dataset)
    state = (window.workspace.path, window.workspace.is_dirty, tuple(window.workspace._history))
    action = window.action_import_csv
    def review(accept):
        dialog = app.activeModalWidget()
        assert dialog.objectName() == 'rm5_review'
        table = dialog.findChild(QtWidgets.QTableWidget)
        assert table is not None
        assert [table.item(i, 2).text() for i in range(2)] == ['7', '5']
        text = '\n'.join(w.text() for w in dialog.findChildren(QtWidgets.QLabel))
        assert 'Review text, references' in text
        assert 'Differs from RevMan\nSMD: RC MetaStudio uses exact Hedges' in text
        assert 'Not imported' not in text
        assert 'settings are not applied' not in text
        record_step('rm5-review', dialog, summary=text)
        dialog.accept() if accept else dialog.reject()
    with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(source), '')):
        QtCore.QTimer.singleShot(0, lambda: review(False))
        action.trigger()
        assert dataset_to_project(window.model.dataset) == before
        assert (window.workspace.path, window.workspace.is_dirty, tuple(window.workspace._history)) == state
        QtCore.QTimer.singleShot(0, lambda: review(True))
        with patch.object(window, 'prompt_to_save_unsaved_data', return_value=QtWidgets.QMessageBox.StandardButton.Cancel) as prompt:
            action.trigger()
            prompt.assert_called_once()
        assert dataset_to_project(window.model.dataset) == before
        QtCore.QTimer.singleShot(0, lambda: review(True))
        with patch.object(window, 'prompt_to_save_unsaved_data', return_value=QtWidgets.QMessageBox.StandardButton.Discard) as prompt:
            action.trigger()
            prompt.assert_called_once()
    window.resize(1024, 700)
    app.processEvents()
    tabs = window.sheet_tabs
    for index in range(tabs.count()):
        tabs.setCurrentIndex(index)
        app.processEvents()
        rect = tabs.tabRect(index)
        viewport = window.sheet_tab_scroll.viewport()
        visible = QtCore.QRect(tabs.mapTo(viewport, rect.topLeft()), rect.size())
        assert tabs.fontMetrics().horizontalAdvance(tabs.tabText(index)) > 0
        assert rect.width() > 24
        assert viewport.rect().intersected(visible).width() > 24 and viewport.rect().intersected(visible).height() >= rect.height(), (visible, viewport.rect())
        mouse_click(tabs, QtCore.Qt.MouseButton.LeftButton, rect.center())
        assert window.model.current_sheet_id == tabs.tabData(index)
    record_step('rm5-visible-tabs', window)
    assert len(window.model.dataset.sheets) == 2
    assert [len(s.rows) for s in window.model.dataset.sheets] == [7, 5]
    assert [a.name for a in window.model.dataset.sheets[0].arms] == ['Aspirin', 'Control']
    reference = WORK / 'read-rm5.csv'
    pooled = WORK / 'metacr.csv'
    subprocess.run([rscript, str(ROOT / 'tests/e2e/rm5_reference.R'), str(source), str(reference), str(pooled)], check=True)
    with reference.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for index, sheet in enumerate(window.model.dataset.sheets, 1):
        reference_rows = {r['studlab']: r for r in rows if int(r['outcome.no']) == index}
        assert len(reference_rows) == len(sheet.rows)
        for row in sheet.rows:
            ref = reference_rows[row.label]
            assert row.year == int(ref['year'])
            for arm, suffix in zip(sheet.arms, ('e', 'c')):
                fields = ('event', 'n') if sheet.family == 'binary' else ('n', 'mean', 'sd')
                assert row.analysis_unit.arms[arm.name].raw_data == [float(ref[f'{field}.{suffix}']) for field in fields]
        window.sheet_tabs.setCurrentIndex(index - 1)
        record_step(f'rm5-sheet-{index}', window, reference=str(reference), pooled_reference=str(pooled))
    from rc_metastudio.results.window import ResultsWindow
    from tests.analysis_regression.golden.support.golden_analysis import parsed_numeric_sections
    for index, method in enumerate(('binary.fixed.mh', 'continuous.fixed')):
        window.sheet_tabs.setCurrentIndex(index)
        window.action_go.trigger()
        app.processEvents()
        dialog = next(w for w in app.topLevelWidgets() if isinstance(w, AnalysisSetupDialog) and w.isVisible())
        assert dialog.current_method == method
        record_step('rm5-default-setup', dialog, method=dialog.current_method)
        with observe_fit() as fit:
            dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).click()
            app.processEvents()
        view = next(w for w in app.topLevelWidgets() if isinstance(w, ResultsWindow) and w.isVisible())
        numbers = parsed_numeric_sections(view.results)
        record_step('rm5-pooled', view, numbers=numbers, texts=dict(view.texts))
        actual = numbers['Summary']
        if index == 0:
            outcome = next(original.iter('DICH_OUTCOME'))
            expected = {key: float(outcome.attrib[attr]) for key, attr in
                        (('estimate', 'EFFECT_SIZE'), ('lower_bound', 'CI_START'), ('upper_bound', 'CI_END'), ('i_squared', 'I2'))}
        else:
            with pooled.open(encoding="utf-8", newline="") as stream:
                ref = next(row for row in csv.DictReader(stream) if int(row["outcome"]) == 2)
            expected = dict(estimate=float(ref['estimate']), lower_bound=float(ref['lower']), upper_bound=float(ref['upper']), i_squared=100 * float(ref['I2']))
        if index == 0:
            import math
            raw = list(fit.evaluate('c(exp(result$res$b[1]), exp(result$res$ci.lb), exp(result$res$ci.ub), result$res$I2)'))
            full_precision = dict(zip(('estimate', 'lower_bound', 'upper_bound', 'i_squared'), map(float, raw)))
            record_step('rm5-unrounded-aspirin', view, actual=full_precision, expected=expected)
            for key, value in expected.items():
                assert math.isclose(full_precision[key], value, rel_tol=0, abs_tol=1e-6), (key, full_precision, expected)
        else:
            # This display check does not claim SMD numerical parity (see the review).
            for key, value in expected.items():
                assert actual[key] == round(value, 1 if key == 'i_squared' else 2), (key, actual, expected)
        view.close()
    expected = dataset_to_project(window.model.dataset)
    destination = WORK / 'rm5.rcms'
    with patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(str(destination), '')):
        window.action_save_as.trigger()
    assert window.open(str(destination), raise_on_error=True)
    assert dataset_to_project(window.model.dataset) == expected
    record_step('rm5-reopened', window, project=str(destination))

    for name, data in (('malformed', b'<COCHRANE_REVIEW>'), ('other', b'<review/>')):
        path = WORK / f'{name}.rm5'
        path.write_bytes(data)
        unchanged = dataset_to_project(window.model.dataset)
        with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(path), '')), patch.object(QtWidgets.QMessageBox, 'warning') as warning:
            action.trigger()
            warning.assert_called_once()
            assert str(warning.call_args.args[2])
        assert dataset_to_project(window.model.dataset) == unchanged
    from rc_metastudio.main_wizard import MainWizard
    def welcome():
        wizard = app.activeModalWidget()
        assert isinstance(wizard, MainWizard)
        QtCore.QTimer.singleShot(0, lambda: review(True))
        wizard.currentPage().import_csv_btn.click()
    with patch.object(QtWidgets.QFileDialog, 'getOpenFileName', return_value=(str(source), '')):
        QtCore.QTimer.singleShot(0, welcome)
        wizard = MainWizard(parent=window)
        assert wizard.exec()
        window._handle_wizard_results(wizard.get_results())
    assert len(window.model.dataset.sheets) == 2
    record_step('rm5-welcome-imported', window)

    from tests.e2e.rm5_giv import run as run_giv
    run_giv(app, window, ROOT, WORK, record_step)
