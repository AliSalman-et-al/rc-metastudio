"""Entered-effect capability and derived generic-IV import proof."""
import csv
import math
import subprocess
from PyQt6 import QtCore, QtWidgets
from rc_metastudio.runtime_types import required
from scripts.r_verification_support import resolve_rscript
from rc_metastudio import r_bridge
from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
from rc_metastudio.results_window import ResultsWindow


def run(app, window, ROOT, WORK, record_step):
    from rc_metastudio.rm5_import import read_rm5
    from rc_metastudio.project_adapter import dataset_to_project
    # Exercise existing entered-only paths before deciding their import mapping.
    for index, metric, method in ((0, 'OR', 'binary.fixed.inv.var'), (1, 'MD', 'continuous.fixed')):
        dataset = read_rm5(ROOT / 'tests/fixtures/rm5/Fleiss1993.rm5').dataset
        sheet = dataset.sheets[index]
        sheet.settings['metric'] = metric
        sheet.settings['analysis'] = dict(method=method, parameters={}, fixed_effects=True, covariates=[])
        for row in sheet.rows:
            unit = row.analysis_unit
            for arm in unit.arms.values():
                arm.raw_data = [None] * len(arm.raw_data)
            unit.set_effect_for_source('entered', metric, tuple(a.id for a in sheet.arms), -.1, standard_error=.2)
        window.set_model(dataset)
        window.sheet_tabs.setCurrentIndex(index)
        window.action_go.trigger()
        app.processEvents()
        setup = next(w for w in app.topLevelWidgets() if isinstance(w, AnalysisSetupDialog) and w.isVisible())
        assert setup.current_method == method
        setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).click()
        app.processEvents()
        view = next(w for w in app.topLevelWidgets() if isinstance(w, ResultsWindow) and w.isVisible())
        record_step('rm5-entered-only-probe', view, metric=metric, method=method)
        view.close()
    source = ROOT / 'tests/fixtures/rm5/generic-derived.rm5'
    imported = read_rm5(source)
    assert [s.settings['metric'] for s in imported.dataset.sheets] == ['HR', 'OR', 'MD']
    assert any('Custom score' in x for x in imported.not_imported)
    reference, pooled = WORK / 'giv-read.csv', WORK / 'giv-pooled.csv'
    subprocess.run([str(required(resolve_rscript("Rscript"), "Rscript for independent RM5 reference")), str(ROOT / 'tests/e2e/rm5_reference.R'), str(source), str(reference), str(pooled)], check=True)
    with reference.open() as f:
        rows = list(csv.DictReader(f))
    with pooled.open() as f:
        refs = list(csv.DictReader(f))
    from rc_metastudio.rm5_import import review_rm5
    def review():
        dialog = app.activeModalWidget()
        text = '\n'.join(w.text() for w in dialog.findChildren(QtWidgets.QLabel))
        assert 'Not imported' in text and 'Custom score' in text
        assert 'O-E survival: O-E/variance inputs are not supported.' in text
        record_step('rm5-giv-review', dialog, summary=text)
        dialog.accept()
    QtCore.QTimer.singleShot(0, review)
    assert review_rm5(source, window) is not None
    window.set_model(imported.dataset)
    for index, sheet in enumerate(imported.dataset.sheets):
        window.sheet_tabs.setCurrentIndex(index)
        for row, ref in zip(sheet.rows, [r for r in rows if int(r['outcome.no']) == index + 1]):
            te = float(ref['TE'])
            if ref['logscale'] == 'FALSE':
                te = math.log(te)
            if index == 0:
                value = row.analysis_unit.ratio_input([a.name for a in sheet.arms])
                actual_te = math.log(value.estimate) if value.scale == 'ratio' else value.estimate
                se = value.se
            else:
                entry = row.analysis_unit.entered_effects[sheet.settings['metric']][tuple(a.id for a in sheet.arms)]
                actual_te, se = entry['est'], entry['SE']
            assert abs(actual_te - te) <= 1e-6
            assert abs(se - float(ref['seTE'])) <= 1e-6
        window.action_go.trigger()
        app.processEvents()
        setup = next(w for w in app.topLevelWidgets() if isinstance(w, AnalysisSetupDialog) and w.isVisible())
        assert setup.current_method == ('time_to_event.fixed', 'binary.fixed.inv.var', 'continuous.fixed')[index]
        record_step('rm5-giv-default-setup', setup, metric=sheet.settings['metric'], method=setup.current_method)
        setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).click()
        app.processEvents()
        view = next(w for w in app.topLevelWidgets() if isinstance(w, ResultsWindow) and w.isVisible())
        actual = list(map(float, r_bridge.execute_r_string('c(result$res$b[1], result$res$ci.lb, result$res$ci.ub, result$res$I2)')))
        ref = refs[index]
        expected = [float(ref[k]) for k in ('estimate', 'lower', 'upper')] + [100 * float(ref['I2'])]
        record_step('rm5-giv-results', view, metric=sheet.settings['metric'], actual=actual, expected=expected)
        assert all(abs(a-b) <= 1e-6 for a,b in zip(actual, expected)), (actual, expected)
        view.close()
    expected = dataset_to_project(window.model.dataset)
    path = WORK / 'giv.rcms'
    from unittest.mock import patch
    with patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(str(path), '')):
        window.action_save_as.trigger()
    assert window.open(str(path), raise_on_error=True)
    assert dataset_to_project(window.model.dataset) == expected
    record_step('rm5-giv-reopened', window, project=str(path))
