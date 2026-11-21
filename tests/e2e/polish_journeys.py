"""Audit journeys with real Qt, RCMetaR and the bundled projects."""
import csv
import hashlib
import json
from unittest.mock import patch

from PyQt6 import QtCore, QtGui, QtWidgets, sip

from rc_metastudio import main_wizard
from rc_metastudio.analysis.setup_dialog import AnalysisSetupDialog
from rc_metastudio.calculators.binary_dialog import BinaryDataDialog
from rc_metastudio.calculators.continuous_dialog import ContinuousDataDialog
from rc_metastudio.results.window import ResultsWindow
from rc_metastudio.settings import get_recent_files, remove_recent_file
from tests.python.gui.qt_test_support import key_click, mouse_click, required, wait


def open_sample_menu_action(window, filename):
    next(action for action in window.sample_menu.actions() if action.data() == filename).trigger()
    assert window.workspace.path.name == filename


def check_sample_saves(app, window, work, sample, number, record):
    from advanced_workflows import modal

    sample_button = required(window.start_page.findChild(QtWidgets.QPushButton, "empty_recent_sample"))
    assert sample_button.isVisible() and sample_button.menu() is window.sample_menu
    original = hashlib.sha256(sample.read_bytes()).hexdigest()

    def open_welcome_sample():
        window.sample_menu.popup(sample_button.mapToGlobal(sample_button.rect().bottomLeft()))
        app.processEvents()
        record(f"sample-{number}-welcome-menu", window.sample_menu)
        open_sample_menu_action(window, sample.name)
        window.sample_menu.close()

    def open_file_sample():
        with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(sample), "")):
            window.action_open.trigger()

    def open_recent_sample():
        next(action for action in window.action_open_recent_2.actions()
             if action.data() == str(sample)).trigger()

    get_save_file_name = QtWidgets.QFileDialog.getSaveFileName
    window.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, False)
    try:
        for route, open_project in (
            ("welcome", open_welcome_sample),
            ("sample-menu", lambda: open_sample_menu_action(window, sample.name)),
            ("file-open", open_file_sample),
            ("recent", open_recent_sample),
        ):
            open_project()
            app.processEvents()
            assert window.workspace.path == sample
            assert "(sample)" in window.windowTitle()
            label = f"Edited study via {route}"
            assert window.model.setData(window.model.index(0, window.model.NAME), label)
            assert window.workspace.is_dirty
            saved = work / f"sample-{number}-{route}.rcms"
            picker_count = 0

            def pick_destination(**kwargs):
                nonlocal picker_count
                picker_count += 1
                assert kwargs["caption"] == "Save project as"
                submit = picker_count == 2
                result = None

                def drive_picker(dialog):
                    assert dialog.windowTitle() == "Save project as"
                    dialog.selectFile(str(saved))
                    record(f"sample-{number}-{route}-{'close' if submit else 'ctrl-s'}-save-as", dialog)
                    if submit:
                        dialog.accept()
                    else:
                        dialog.reject()

                def launch_picker():
                    nonlocal result
                    result = get_save_file_name(**kwargs, options=QtWidgets.QFileDialog.Option.DontUseNativeDialog)

                modal(app, QtWidgets.QFileDialog, drive_picker, launch_picker)
                return result

            def save_on_close(dialog):
                assert dialog.windowTitle() == "Unsaved changes"
                record(f"sample-{number}-{route}-unsaved-changes", dialog)
                required(dialog.button(QtWidgets.QMessageBox.StandardButton.Save)).click()

            with patch.object(QtWidgets.QFileDialog, "getSaveFileName", side_effect=pick_destination):
                window.activateWindow()
                app.setActiveWindow(window)
                window.tableView.setFocus()
                wait(100)
                key_click(window.tableView, QtCore.Qt.Key.Key_S, QtCore.Qt.KeyboardModifier.ControlModifier)
                assert picker_count == 1 and window.workspace.path == sample and window.workspace.is_dirty, (
                    sample.name, route, picker_count, app.activeWindow(), app.focusWidget()
                )
                modal(app, QtWidgets.QMessageBox, save_on_close, window.close)
            assert picker_count == 2 and saved.is_file() and window.workspace.path == saved
            assert hashlib.sha256(sample.read_bytes()).hexdigest() == original
            assert window.action_open_recent_2.actions()[0].data() == str(saved)
            window.show()
            assert window.open(str(saved), raise_on_error=True)
            assert window.model.current_sheet.rows[0].label == label and "(sample)" not in window.windowTitle()
            record(f"sample-{number}-{route}-copy-reopened", window, file=str(saved), original_sha256=original)
    finally:
        window.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)

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
        open_sample_menu_action(window, label + ".rcms")

    assert not window.tableView.study_calculator_action.isEnabled()
    entries = json.loads((root / "sample_projects/manifest.json").read_text(encoding="utf-8"))["projects"]
    assert [action.data() for action in window.sample_menu.actions()] == [entry["file"] for entry in entries]
    assert [action.text() for action in window.sample_menu.actions()] == [
        f"{entry['scientific_name']} — {entry['description']}" for entry in entries
    ]
    assert window.sample_menu.menuAction() in window.menu_file.actions()
    menu_bar = required(window.menuBar())
    mouse_click(menu_bar, QtCore.Qt.MouseButton.LeftButton,
                pos=menu_bar.actionGeometry(window.menu_file.menuAction()).center())
    app.processEvents()
    record("sample-file-menu", window.menu_file)
    window.menu_file.close()

    for number, entry in enumerate(entries, start=1):
        for recent in get_recent_files():
            remove_recent_file(recent)
        sample_window = type(window)()
        sample_window.start()
        try:
            check_sample_saves(app, sample_window, work, root / "sample_projects" / entry["file"], number, record)
        finally:
            sample_window.workspace.mark_saved()
            sample_window.close()
    window.activateWindow()
    app.setActiveWindow(window)
    open_sample("Binary - Aminoglycoside dosing, Barza 1996")

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

    open_sample("Single-arm mean - Handgrip strength in young adults, Abe 2025")
    window.model.rename_arm(window.model.arm_names[0], "Custom cohort")
    mean = analyze(app, window, "continuous.random")
    assert "265 participants)" in mean.manuscript.results and "participants in Custom cohort" not in mean.manuscript.results
    assert dict(mean.results.manuscript_model_info)["Participants"] == "265"
    mean.report_action.trigger()
    record("one-arm-participant-prose", mean, prose=mean.manuscript.results)
    mean.close()

    window.workspace.mark_saved()
    open_sample("Continuous - Monthly respiratory exacerbations, Poole 2003")
    table = window.tableView
    table.setCurrentIndex(window.model.index(0, window.model.NAME))
    table.setFocus()
    window.activateWindow()
    app.processEvents()
    assert table.study_calculator_action.isEnabled() and "F4" in table.accessibleDescription()
    with patch("rc_metastudio.r_runtime.is_ready", return_value=False):
        window.refresh_analysis_actions()
        assert not table.study_calculator_action.isEnabled()
    window.refresh_analysis_actions()

    def inspect_continuous(dialog):
        if dialog.input_mode_combo.findData("pre-post") < 0:
            raise AssertionError((dialog.current_effect, dialog.input_mode_combo.currentText()))
        dialog.input_mode_combo.setCurrentIndex(dialog.input_mode_combo.findData("pre-post"))
        app.processEvents()
        assert dialog.preview_source_label.isVisible()
        assert dialog.preview_source_label.wordWrap()
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
    viewport = required(setup.content_scroll_area.viewport())
    advanced = QtCore.QRect(setup.advanced_toggle.mapTo(viewport, QtCore.QPoint()), setup.advanced_toggle.size())
    assert viewport.rect().contains(advanced), (viewport.rect(), advanced)
    record("long-outcome-in-setup", setup)
    required(setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)).click()
    app.processEvents()
    error = setup.analysis_error_label.text()
    assert error.startswith("No study has enough data to analyze.") and f"{study} (2021)" in error and "events" in error and "total" in error
    assert "events and totals for both arms, or an estimate with its confidence interval or standard error" in error
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
    assert action.shortcut().toString() == "F4" and action.isShortcutVisibleInContextMenu()
    menu.close()
    modal(app, BinaryDataDialog, inspect_binary, action.trigger)

    for row, label in enumerate(("Second study", "Third study", "Fourth study", "Fifth study"), start=1):
        assert model.setData(model.index(row, model.NAME), label)
    table.setCurrentIndex(model.index(len(model.current_sheet.rows), model.NAME))
    assert not table.study_calculator_action.isEnabled()
    window.action_go.trigger()
    setup = visible(AnalysisSetupDialog)
    required(setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)).click()
    app.processEvents()
    error = setup.analysis_error_label.text()
    assert "and 2 more" in error and "Third study" in error and "Fourth study" not in error, error
    record("incomplete-study-message-bounded", setup, error=error)
    setup.reject()

    window.workspace.mark_saved()
    open_sample("Event rates (IRR) - Catheter infections, Niel-Weise 2008")
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
        assert "Row 7" in page.import_status.text() and "already exists in row 6" in page.import_status.text()
        assert page.import_tabs.currentWidget() is page.preview_grp_box
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

    model = window.model
    new_row = len(model.current_sheet.rows)
    assert model.setData(model.index(new_row, model.YEAR), 2008)
    assert model.setData(model.index(new_row, model.NAME), " Jaeger et al. ")
    assert model.current_sheet.rows[new_row].label == "Jaeger et al."
    record("study-identity-grid-distinct-year", window)
    def conflict_message(dialog):
        assert "Study ‘Jaeger et al.’ (2001) already exists in row 5." in dialog.text(), dialog.text()
        record("study-identity-year-conflict", dialog)
        dialog.accept()

    modal(app, QtWidgets.QMessageBox, conflict_message,
          lambda: model.setData(model.index(new_row, model.YEAR), 2001))
    assert model.current_sheet.rows[new_row].year == 2008
    paste_sources = []

    def paste_identity(row, year):
        window.tableView.setCurrentIndex(window.model.index(row, window.model.NAME))
        payload = f"Jaeger et al.\t{year}"
        clipboard = app.clipboard()
        clipboard.setText(payload)
        if app.platformName() == "windows" and not clipboard.ownsClipboard():
            paste_sources.append("seeded clipboard read after Windows denied access")
            with patch.object(QtGui.QClipboard, "text", return_value=payload):
                window.action_paste.trigger()
        else:
            paste_sources.append("Qt clipboard")
            window.action_paste.trigger()

    paste_identity(new_row + 1, 2009)
    assert window.model.current_sheet.rows[new_row + 1].year == 2009

    def paste_conflict(dialog):
        assert dialog.text() == "Study ‘Jaeger et al.’ (2005) already exists in row 6."
        record("study-identity-paste-conflict", dialog)
        dialog.accept()

    modal(app, QtWidgets.QMessageBox, paste_conflict, lambda: paste_identity(new_row + 2, 2005))
    assert len(window.model.current_sheet.rows) == new_row + 2
    record("study-identity-paste-atomic", window, clipboard_source=paste_sources)
