"""Audit journeys with real Qt, RCMetaR and the bundled projects."""
import csv
from unittest.mock import patch

from PyQt6 import QtCore, QtGui, QtWidgets, sip

from rc_metastudio import main_wizard
from rc_metastudio.analysis.setup_dialog import AnalysisSetupDialog
from rc_metastudio.calculators.binary_dialog import BinaryDataDialog
from rc_metastudio.calculators.continuous_dialog import ContinuousDataDialog
from rc_metastudio.results.window import ResultsWindow
from tests.python.gui.qt_test_support import key_click, mouse_click, required


def run(app, window, work, root, record, analyze):
    from advanced_workflows import modal
    from analysis_matrix import set_parameter
    from tests.e2e.plot_observations import load_saved_analysis
    from rc_metastudio import r_bridge
    from rc_metastudio.analysis.small_study_effects_dialog import SmallStudyEffectsDialog

    def visible(kind):
        app.processEvents()
        return next(widget for widget in app.topLevelWidgets()
                    if isinstance(widget, kind) and widget.isVisible())

    def open_sample(label):
        next(action for action in window.sample_menu.actions() if action.text() == label).trigger()
        app.processEvents()

    sample_button = required(window.start_page.findChild(QtWidgets.QPushButton, "empty_recent_sample"))
    assert sample_button.menu() is window.sample_menu
    assert window.sample_menu.menuAction() in window.menu_file.actions()
    record("sample-welcome", window)
    window.menu_file.popup(window.menu_file.parentWidget().mapToGlobal(QtCore.QPoint()))
    app.processEvents()
    record("sample-file-menu", window.menu_file)
    window.menu_file.close()
    sample = root / "sample_projects/amino.rcms"
    original = sample.read_bytes()
    open_sample("Aminoglycosides")
    assert window.workspace.path == sample
    saved = work / "amino-copy.rcms"
    with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(saved), "")) as picker:
        window.action_save.trigger()
    assert picker.call_count == 1 and saved.is_file() and sample.read_bytes() == original
    assert window.open(str(saved), raise_on_error=True)
    record("sample-save-as-reopened", window, file=str(saved))

    view = analyze(app, window, "binary.random")
    assert "Random-effects" in view.windowTitle() and "95% CI" in view.windowTitle()
    screen = required(view.screen()).availableGeometry()
    view.showNormal()
    app.processEvents()
    frame = view.frameGeometry()
    assert frame.width() >= min(screen.width(), 950) and frame.height() >= min(screen.height(), 630), frame
    record("results-restored-normal-frame", view, frame=frame.getRect(), screen=screen.getRect())
    for method, label, confidence in (("binary.fixed.mh", "Mantel–Haenszel", 90), ("binary.fixed.peto", "Peto", 95)):
        view.change_settings_action.trigger()
        setup = visible(AnalysisSetupDialog)
        setup.method_cbo_box.setCurrentIndex(setup.method_cbo_box.findData(method))
        set_parameter(app, setup, "conf.level", confidence)
        record("change-settings-" + method, setup)
        required(setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)).click()
        replacement = visible(ResultsWindow)
        assert replacement is not view and (sip.isdeleted(view) or not view.isVisible())
        view = replacement
        assert label in view.windowTitle() and f"{confidence}% CI" in view.windowTitle()
        counts = dict(view.results.manuscript_model_info)
        assert counts["Studies included"] == "19" and counts["Studies contributing"] == "17", counts
        assert "17 studies contributed" in view.manuscript.results and "df = 16" in view.manuscript.results
        load_saved_analysis(next(iter(view.params_paths.values())))
        actual = view.results.contributing_studies
        direct = list(r_bridge.ro.r(
            'local({ fit <- ' + ('metafor::rma.mh' if method.endswith("mh") else 'metafor::rma.peto') +
            '(ai=om.data@g1O1, bi=om.data@g1O2, ci=om.data@g2O1, di=om.data@g2O2); c(fit$k, fit$k.yi) })'
        ))
        assert actual == direct[1] == 17 and direct[0] == 19, direct
        assert int(r_bridge.ro.r("length(om.data@study.names)")[0]) == 19
        record("forest-keeps-included-studies-" + method, view)
        view.report_action.trigger()
        app.processEvents()
        record("results-prose-count-" + method, view, counts=counts, metafor_k=direct[0], metafor_k_yi=direct[1], prose=view.manuscript.results)
        view.tables_action.trigger()
        view.table_selector.setCurrentText("Model fit")
        table_cells = [view.result_table.item(row, 0).text() for row in range(view.result_table.rowCount())]
        assert "Studies included" in table_cells and "Studies contributing" in table_cells, table_cells
        record("model-fit-count-" + method, view, counts=counts)
    view.tables_action.trigger()
    app.processEvents()
    assert view.nav_tree.currentItem().text(0) == "Data tables (CSV)"
    view.table_selector.setCurrentText("Pooled effect")
    view.result_table.clearSelection()
    copy_action = view.copy_table_action
    for scope, cells in (
        ("Table", ()), ("Cell", ((0, 0),)), ("Selection", ((0, 0), (0, 1))),
    ):
        view.result_table.clearSelection()
        for row, column in cells:
            required(view.result_table.item(row, column)).setSelected(True)
        copy_action.trigger()
        assert view.statusbar.currentMessage() == scope + " copied"
        record("results-copy-" + scope.lower(), view, clipboard=app.clipboard().text())
    view.close()

    def run_small_study(dialog):
        dialog.sampling_confidence_combo.setCurrentText("90")
        required(dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)).click()

    modal(app, SmallStudyEffectsDialog, run_small_study, window.action_publication_bias.trigger)
    small = visible(ResultsWindow)
    assert small.change_settings_action.isEnabled() and "95% CI" in small.windowTitle()

    def change_small_study(dialog):
        assert dialog.sampling_confidence_combo.currentText() == "90"
        dialog.sampling_confidence_combo.setCurrentText("99")
        record("small-study-change-settings-restored", dialog)
        required(dialog.button_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)).click()

    modal(app, SmallStudyEffectsDialog, change_small_study, small.change_settings_action.trigger)
    changed = visible(ResultsWindow)
    assert changed is not small and (sip.isdeleted(small) or not small.isVisible())
    record("small-study-results-replaced", changed)
    changed.close()

    open_sample("Illustrative Mean")
    mean = analyze(app, window, "continuous.random")
    assert "135 participants" in mean.manuscript.results and "participants in Participants" not in mean.manuscript.results
    assert dict(mean.results.manuscript_model_info)["Participants"] == "135"
    mean.report_action.trigger()
    record("one-arm-participant-prose", mean, prose=mean.manuscript.results)
    mean.close()

    open_sample("Continuous outcome example")
    table = window.tableView
    table.setCurrentIndex(window.model.index(0, window.model.NAME))
    table.setFocus()
    window.activateWindow()
    app.processEvents()

    def inspect_continuous(dialog):
        if dialog.input_mode_combo.findData("pre-post") < 0:
            raise AssertionError(dialog.input_mode_combo.currentText())
        dialog.input_mode_combo.setCurrentIndex(dialog.input_mode_combo.findData("pre-post"))
        app.processEvents()
        assert dialog.preview_source_label.isVisible()
        record("continuous-pre-post-source", dialog, source=dialog.preview_source_label.text())
        dialog.reject()

    modal(app, ContinuousDataDialog, inspect_continuous, lambda: key_click(table, QtCore.Qt.Key.Key_F4))

    wizard = main_wizard.MainWizard(path="new_dataset")
    wizard.show()
    app.processEvents()
    page = wizard.currentPage()
    assert isinstance(page, main_wizard.DataTypePage)
    assert "Two-arm binary" in page.twoarm_proportions_Button.text()
    record("two-arm-binary-wizard-tile", wizard)
    page.time_rates_Button.click()
    wizard.next()
    metric = wizard.currentPage()
    assert isinstance(metric, main_wizard.ChooseMetricPage)
    for value, label in (("IRR", "Event rates"), ("HR", "Time-to-event")):
        metric.metric_cbo_box.setCurrentIndex(metric.metric_cbo_box.findData(value))
        assert metric.subTitle().endswith(label), metric.subTitle()
        record("wizard-breadcrumb-" + value, wizard)
    wizard.reject()

    study = "North-West Cardiovascular Outcomes Consortium, Multicentre Validation Cohort"
    outcome = "Mortality from all cardiovascular causes at twelve months after hospital discharge"
    wizard = main_wizard.MainWizard(path="new_dataset")
    wizard.set_dataset_info(dict(arms="two", data_type="binary", sub_type="proportions",
                                 effect="OR", metric_choices=[], name=outcome))
    window._handle_wizard_results({"path": "new_dataset", "outcome_info": wizard.require_dataset_info()})
    model = window.model
    assert model.setData(model.index(0, model.NAME), study)
    assert model.setData(model.index(0, model.YEAR), 2021)
    window.action_go.trigger()
    setup = visible(AnalysisSetupDialog)
    assert any(label.text() == outcome and label.wordWrap() for label in setup.findChildren(QtWidgets.QLabel))
    record("long-outcome-in-setup", setup)
    required(setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)).click()
    app.processEvents()
    error = setup.analysis_error_label.text()
    assert error.startswith("No study has enough data to analyse.") and f"{study} (2021)" in error and "events" in error and "total" in error
    assert not setup.analysis_error_toggle.isVisible()
    record("named-empty-study-blocked", setup, error=error)
    setup.reject()

    def inspect_binary(dialog):
        assert any(label.text() == study and label.wordWrap() for label in dialog.findChildren(QtWidgets.QLabel))
        record("long-study-in-calculator", dialog)
        dialog.reject()

    table.setCurrentIndex(model.index(0, model.NAME))
    modal(app, BinaryDataDialog, inspect_binary, table.study_calculator_action.trigger)
    index = table.currentIndex()
    point = table.visualRect(index).center()
    viewport = required(table.viewport())
    event = QtGui.QContextMenuEvent(QtGui.QContextMenuEvent.Reason.Mouse, point, viewport.mapToGlobal(point))
    app.sendEvent(viewport, event)
    menu = visible(QtWidgets.QMenu)
    record("row-context-calculator", menu)
    action = next(action for action in menu.actions() if action.text() == "Study calculator…")
    menu.close()
    modal(app, BinaryDataDialog, inspect_binary, action.trigger)

    window.workspace.mark_saved()
    open_sample("Niel-Weise 2008 — Catheter infections")
    audit_fixture = root / "tests/fixtures/irr-duplicate-labels.csv"
    with audit_fixture.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.reader(stream))
    conflict = work / "conflicting-years.csv"
    rows[6][1] = rows[5][1]
    with conflict.open("w", encoding="utf-8", newline="") as stream:
        csv.writer(stream).writerows(rows)

    def drive_import(wizard):
        page = wizard.currentPage()
        assert isinstance(page, main_wizard.CsvImportPage)
        page.data_type_combo.setCurrentText("Incidence rate ratio")
        assert not page.isComplete()
        assert "Rows 6 and 7" in page.import_status.text()
        assert not wizard.button(QtWidgets.QWizard.WizardButton.FinishButton).isEnabled()
        record("duplicate-study-preview-blocked", wizard, error=page.import_status.text())
        with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(audit_fixture), "")):
            page.select_file_btn.click()
        assert page.isComplete(), page.import_status.text()
        record("duplicate-name-distinct-years-preview", wizard)
        wizard.button(QtWidgets.QWizard.WizardButton.FinishButton).click()

    with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(conflict), "")):
        modal(app, main_wizard.MainWizard, drive_import, window.action_import_csv.trigger)
    jaeger = [row.year for row in window.model.current_sheet.rows if row.label == "Jaeger et al."]
    assert jaeger == [2001, 2005] and len(window.model.current_sheet.rows) == 9
    record("duplicate-name-imported", window, years=jaeger)
