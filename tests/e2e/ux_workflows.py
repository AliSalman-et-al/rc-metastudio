"""Real desktop proof for result controls, mapped CSV and input recovery."""

import csv
from pathlib import Path
from typing import Callable, cast
from unittest.mock import patch

from PyQt6 import QtCore, QtWidgets, QtTest

from tests.python.gui.test_types import mouse_click, key_click, required, wait


def run(app, window, work, root, record, analyze):
    from rc_metastudio import add_new_dialogs, main_wizard

    window.showMaximized()
    app.processEvents()
    app.processEvents()
    assert not window.workspace.is_dirty
    assert "Unsaved changes" not in window.dataset_file_lbl.text()
    assert "*" not in window.windowTitle()
    record("ux-empty-workspace", window, guidance=window.workspace_hint.text(), device_pixel_ratio=window.devicePixelRatioF(), logical_size=[window.width(), window.height()])
    guide_errors = []
    def read_guide():
        dialog = app.activeModalWidget()
        try:
            assert isinstance(dialog, QtWidgets.QMessageBox)
            dialog.setProperty("verificationExpectedMessage", True)
            guide = dialog.text()
            assert all(name in guide for name in ("Intervention / Control", "Index test", "UTF-8 CSV")), guide
            assert "template" in guide.casefold() and "mapping" in guide.casefold(), guide
            record("ux-quick-start", dialog, text=dialog.text())
        except Exception as error:
            guide_errors.append(str(error))
        finally:
            if dialog is not None:
                dialog.close()
    QtCore.QTimer.singleShot(0, read_guide)
    next(action for action in window.menuHelp.actions() if "Quick start" in action.text()).trigger()
    assert not guide_errors, guide_errors

    assert window.open(str(root / "sample_projects/amino.rcms"), raise_on_error=True)
    year = str(window.model.data(window.model.index(0, window.model.YEAR)))
    assert window.tableView.columnWidth(window.model.YEAR) >= window.tableView.fontMetrics().horizontalAdvance(year) + 8
    lower_column = window.model.OUTCOMES[1]
    lower = str(window.model.data(window.model.index(2, lower_column)))
    assert window.tableView.columnWidth(lower_column) >= window.tableView.fontMetrics().horizontalAdvance(lower) + 8
    from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
    window.action_go.trigger()
    app.processEvents()
    setup = next(widget for widget in app.topLevelWidgets() if isinstance(widget, AnalysisSetupDialog) and widget.isVisible())
    assert setup.col1_str_edit.text() == "Study"
    setup.current_param_vals["rm.method"] = "invalid-estimator"
    mouse_click(required(setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)), QtCore.Qt.MouseButton.LeftButton)
    app.processEvents()
    assert setup.isVisible()
    assert setup.analysis_error_label.isVisible()
    assert setup.analysis_error_label.hasFocus()
    assert not any(isinstance(widget, QtWidgets.QMessageBox) and widget.isVisible() for widget in app.topLevelWidgets())
    record("ux-inline-analysis-error", setup, message=setup.analysis_error_label.text())
    setup.current_param_vals["rm.method"] = "DL"
    mouse_click(required(setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)), QtCore.Qt.MouseButton.LeftButton)
    app.processEvents()
    from rc_metastudio.results_window import ResultsWindow
    recovered = next(widget for widget in app.topLevelWidgets() if isinstance(widget, ResultsWindow) and widget.isVisible())
    assert recovered.results.images
    record("ux-analysis-recovered", recovered, plots=dict(recovered.results.display_images), texts=dict(recovered.texts))
    recovered.close()
    app.processEvents()
    view = analyze(app, window, "binary.random")
    assert "clinical failure" in view.results.identity
    assert "Odds Ratio" in view.results.identity
    assert view.nav_tree.width() < view.width() / 3, (view.nav_tree.width(), view.width(), view.results_nav_splitter.sizes(), view._restored_splitter_proportions)
    assert not view.report_action.isChecked()
    assert view.content_stack.currentWidget() is view.figure_page
    assert len(view.identity_label.text().splitlines()) <= 3
    initial_identity_height = view.identity_label.height()
    refit_waits = 0
    while (
        view.identity_label.height() > 3 * view.identity_label.fontMetrics().lineSpacing()
        and refit_waits < 100
    ):
        wait(20)
        refit_waits += 1
    geometry = dict(
        initial_identity_height=initial_identity_height,
        identity_height=view.identity_label.height(),
        measured_height=view.identity_label.heightForWidth(view.identity_label.width()),
        identity_width=view.identity_label.width(),
        font_height=view.identity_label.fontMetrics().height(),
        line_spacing=view.identity_label.fontMetrics().lineSpacing(),
        refit_waits=refit_waits,
    )
    assert view.identity_label.height() <= 3 * view.identity_label.fontMetrics().lineSpacing(), geometry
    record("ux-header-geometry", view, **geometry)
    assert "Included input studies" not in view.identity_label.text()
    assert "Studies used in the model" not in view.identity_label.text()
    view.report_action.trigger()
    app.processEvents()
    assert view.report_text.isVisible()
    view.activateWindow()
    view.report_text.setFocus()
    app.processEvents()
    assert cast(Callable[..., bool], QtTest.QTest.qWaitForWindowActive)(view, 2000)
    assert view.report_text.hasFocus()
    assert view.report_text.find("Model:")
    record("ux-copy-selection-before", view, selection=view.report_text.textCursor().selectedText(), focus=app.focusWidget().objectName(), active=view.isActiveWindow(), clipboard=app.clipboard().text())
    key_click(view.report_text, QtCore.Qt.Key.Key_C, QtCore.Qt.KeyboardModifier.ControlModifier)
    app.processEvents()
    record("ux-copy-selection-after", view, selection=view.report_text.textCursor().selectedText(), clipboard=app.clipboard().text(), owns=app.clipboard().ownsClipboard())
    assert app.clipboard().text() == "Model:", repr(app.clipboard().text())
    key_click(view.report_text, QtCore.Qt.Key.Key_C, QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.ShiftModifier)
    copied_report = app.clipboard().text()
    assert copied_report.startswith(view.results.identity + "\n")
    for section in view.results.sections:
        for table in section.tables:
            assert "\t".join(table.headers) in copied_report
            assert all("\t".join(row) in copied_report for row in table.rows)
    view.copy_report_action.trigger()
    assert app.clipboard().text() == copied_report
    report_path = work / "analysis.txt"
    with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(report_path), "")):
        view.export_report_action.trigger()
    assert report_path.read_text(encoding="utf-8") == app.clipboard().text()
    assert str(report_path) in view.statusbar.currentMessage()
    with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=("", "")):
        view.export_report_action.trigger()
    record("ux-readable-report", view, clipboard=app.clipboard().text(), saved=str(report_path))
    assert view.table_selector.count() >= 2
    key_click(view.report_text, QtCore.Qt.Key.Key_T, QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.ShiftModifier)
    app.processEvents()
    app.processEvents()
    table = view._report_tables[0]
    assert view.result_table.horizontalHeaderItem(0).text() == table.headers[0]
    assert view.result_table.item(0, 0).text() == table.rows[0][0]
    key_click(view.result_table, QtCore.Qt.Key.Key_C, QtCore.Qt.KeyboardModifier.ControlModifier)
    app.processEvents()
    assert list(csv.reader(app.clipboard().text().splitlines(), delimiter="\t")) == [list(table.headers), *map(list, table.rows)]
    csv_path = work / "model-results.csv"
    with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(csv_path), "CSV")):
        view.export_table_action.trigger()
    with csv_path.open(encoding="utf-8-sig", newline="") as exported:
        assert list(csv.reader(exported)) == [list(table.headers), *map(list, table.rows)]
    record("ux-native-result-table", view, title=table.title, headers=table.headers,
           rows=table.rows, csv=str(csv_path))
    view.report_action.trigger()
    view.zoom_control.setValue(200)
    app.processEvents()
    assert view.report_text.font().pointSizeF() >= 22
    assert not view.fit_width_action.isEnabled()
    text_zoom = view.zoom_control.value()
    view.report_action.trigger()
    app.processEvents()
    assert view.fit_width_action.isEnabled()
    view.zoom_control.setValue(125)
    view.report_action.trigger()
    app.processEvents()
    assert view.zoom_control.value() == text_zoom
    assert view.report_text.font().pointSizeF() >= 22
    assert view.graphics_view.transform().m11() == 1.25
    record("ux-independent-view-zoom", view, report_zoom=text_zoom,
           report_font=view.report_text.font().pointSizeF(), figure_zoom=125)
    view.zoom_control.setValue(100)
    plot_item = next(item for item in view._svg_plot_items)
    nav = next(item for item in view.nav_tree.findItems("Forest Plot", QtCore.Qt.MatchFlag.MatchExactly))
    mouse_click(view.nav_tree.viewport(), QtCore.Qt.MouseButton.LeftButton, pos=view.nav_tree.visualItemRect(nav).center())
    app.processEvents()
    assert view.export_plot_action.isEnabled()
    assert not view.report_text.isVisible()
    artifact = view._selected_plot()[0]
    saved_params = view.plot_service.load_params(artifact.params_path)
    assert saved_params["fp_col1_str"] == "Study", saved_params
    assert plot_item.sceneBoundingRect().width() <= view.graphics_view.viewport().width()
    plot_path = work / "toolbar-forest.pdf"
    with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(plot_path), "PDF")):
        view.activateWindow()
        view.nav_tree.setFocus()
        app.processEvents()
        key_click(view.nav_tree, QtCore.Qt.Key.Key_E, QtCore.Qt.KeyboardModifier.ControlModifier | QtCore.Qt.KeyboardModifier.ShiftModifier)
    assert plot_path.read_bytes().startswith(b"%PDF")
    assert str(plot_path) in view.statusbar.currentMessage()
    view.zoom_control.setValue(125)
    app.processEvents()
    assert view.graphics_view.transform().m11() == 1.25
    view.graphics_view.horizontalScrollBar().setValue(view.graphics_view.horizontalScrollBar().maximum())
    view.fit_width_action.trigger()
    app.processEvents()
    plot_rect = view.graphics_view.mapFromScene(plot_item.sceneBoundingRect()).boundingRect()
    assert plot_rect.left() >= 0 and plot_rect.right() < view.graphics_view.viewport().width(), plot_rect
    assert view.graphics_view.horizontalScrollBar().value() == 0
    record("ux-plot-toolbar", view, saved=str(plot_path), zoom=view.zoom_control.value(), plot_bounds=[plot_rect.left(), plot_rect.right()], viewport_width=view.graphics_view.viewport().width())
    view.close()

    wizard = main_wizard.MainWizard(path="csv_import")
    wizard.set_dataset_info({"arms": "two", "data_type": "binary", "sub_type": "proportions", "effect": "OR", "metric_choices": [], "name": "Mapped mortality"})
    name_page = wizard.page(main_wizard.Page_OutcomeName)
    assert isinstance(name_page, main_wizard.OutcomeNamePage)
    name_page.outcome_name_LineEdit.setText("Mapped mortality")
    wizard.setStartId(main_wizard.Page_CsvImport)
    wizard.restart()
    wizard.show()
    app.processEvents()
    page = wizard.currentPage()
    assert isinstance(page, main_wizard.CsvImportPage)
    cast(Callable[[int], None], QtTest.QTest.qWait)(100)
    scrollbar = required(page.pageScrollArea.verticalScrollBar())
    assert scrollbar.value() == 0
    assert page.instructions.mapTo(page, QtCore.QPoint()).y() >= 0
    scrollbar.setValue(scrollbar.maximum())
    assert page.instructions.visibleRegion().boundingRect().height() == page.instructions.height()
    scrollbar.setValue(0)
    record("ux-csv-page-entry", wizard, scroll=scrollbar.value())
    source = work / "mapped.csv"
    source.write_text('Citation,Year,A events,A total,B events,B total,OR,Lower,Upper,Dose\n"Alpha, München",2020,1,10,2,12,,,,5\nBeta,2021,3,11,4,13,,,,7\n', encoding="utf-8")
    with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(source), "")):
        mouse_click(page.select_file_btn, QtCore.Qt.MouseButton.LeftButton)
    assert not page.isComplete()
    assert "Study Name" in page.import_status.text()
    record("ux-csv-invalid", wizard, message=page.import_status.text())
    for control, index in zip(page.mapping_controls, range(9)):
        control.setCurrentIndex(control.findData(index))
    assert page.isComplete()
    assert page.preview_table.rowCount() == 2
    page.mapping_controls[1].setCurrentIndex(0)
    assert not page.isComplete()
    assert "Year" in page.import_status.text()
    assert not required(wizard.button(QtWidgets.QWizard.WizardButton.FinishButton)).isEnabled()
    assert page.csv_data() is None
    assert page.file_path == str(source)
    record("ux-csv-cleared-required", wizard, message=page.import_status.text(), selected_file=page.file_path)
    page.mapping_controls[1].setCurrentIndex(page.mapping_controls[1].findData(1))
    page.mapping_controls[1].setCurrentIndex(page.mapping_controls[1].findData(0))
    assert not page.isComplete()
    assert "different CSV column" in page.import_status.text()
    page.mapping_controls[1].setCurrentIndex(page.mapping_controls[1].findData(1))
    assert page.isComplete()
    template = work / "template.csv"
    with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(template), "")):
        mouse_click(page.template_btn, QtCore.Qt.MouseButton.LeftButton)
    with template.open(encoding="utf-8-sig", newline="") as stream:
        assert next(csv.reader(stream)) == page.required_header_labels
    record("ux-csv-mapped", wizard, headers=page.headers, template=str(template))
    with template.open("a", encoding="utf-8", newline="") as stream:
        csv.writer(stream).writerow(["Exact headers", 2022, 1, 10, 2, 12, "", "", ""])
    with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(template), "")):
        mouse_click(page.select_file_btn, QtCore.Qt.MouseButton.LeftButton)
    assert page.isComplete()
    page.mapping_controls[1].setCurrentIndex(0)
    assert not page.isComplete()
    assert page.preview_table.rowCount() == 0
    assert page.csv_data() is None
    assert "Year" in page.import_status.text()
    record("ux-csv-cleared-exact-headers", wizard, message=page.import_status.text())
    page.mapping_controls[1].setCurrentIndex(page.mapping_controls[1].findData(1))
    assert page.isComplete()
    assert required(page.preview_table.item(0, 0)).text() == "Exact headers"
    with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(source), "")):
        mouse_click(page.select_file_btn, QtCore.Qt.MouseButton.LeftButton)
    assert not page.isComplete()
    for control, index in zip(page.mapping_controls, range(9)):
        control.setCurrentIndex(control.findData(index))
    assert page.isComplete()
    record("ux-csv-recovered", wizard, headers=page.headers, rows=page.preview_table.rowCount())
    window._handle_wizard_results(wizard.get_results())
    wizard.close()
    assert window.model.dataset.studies[0].name == "Alpha, München"
    assert window.model.dataset.studies[1].covariate_values["Dose"] == 7.0
    assert window.model.get_current_raw_data_for_study(0) == [1, 10, 2, 12]
    window.out_path = str(work / "mapped.rcms")
    assert window.save()
    assert window.open(window.out_path, raise_on_error=True)
    analyze(app, window, "binary.random").close()
    for column, value in ((window.model.RAW_DATA[1], 10000), (window.model.RAW_DATA[3], 10000), (window.model.RAW_DATA[0], 1), (window.model.RAW_DATA[2], 5000)):
        assert window.model.setData(window.model.index(0, column), value)
    estimate = str(window.model.data(window.model.index(0, window.model.OUTCOMES[0])))
    assert 0 < float(estimate) < .001
    assert abs(float(estimate) - 1 / 9999) < 1e-6
    record("ux-small-ratio", window, raw=[1, 10000, 5000, 10000], displayed_estimate=estimate)

    form = add_new_dialogs.AddCovariateDialog(window, existing_names=window.model.dataset.get_covariate_names())
    form.show()
    app.processEvents()
    button = required(form.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
    assert not button.isEnabled()
    form.covariate_name_le.setText("Dose")
    mouse_click(button, QtCore.Qt.MouseButton.LeftButton)
    assert form.isVisible()
    assert form.error_label.text()
    if app.platformName() in {"windows", "xcb", "cocoa"}:
        wait(250)
    assert form.rect().contains(button.mapTo(form, button.rect().bottomRight()))
    assert form.rect().contains(form.error_label.mapTo(form, form.error_label.rect().bottomRight()))
    record("ux-covariate-error", form, error=form.error_label.text())
    form.covariate_name_le.setText("Region")
    mouse_click(button, QtCore.Qt.MouseButton.LeftButton)
    assert form.result() == QtWidgets.QDialog.DialogCode.Accepted.value
    record("ux-mapped-reopened", window, project=window.out_path)
