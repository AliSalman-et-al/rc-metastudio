"""Real desktop proof for result controls, mapped CSV and input recovery."""

import csv
from pathlib import Path
from unittest.mock import patch

from PyQt6 import QtCore, QtWidgets

from tests.python.gui.test_types import mouse_click, key_click, required


def run(app, window, work, root, record, analyze):
    from rc_metastudio import add_new_dialogs, main_wizard

    record("ux-empty-workspace", window, guidance=window.workspace_hint.text(), device_pixel_ratio=window.devicePixelRatioF(), logical_size=[window.width(), window.height()])

    assert window.open(str(root / "sample_projects/amino.rcms"), raise_on_error=True)
    view = analyze(app, window, "binary.random")
    assert "clinical failure" in view.identity_label.text()
    assert "Odds Ratio" in view.identity_label.text()
    assert view.nav_tree.width() < view.width() / 3, (view.nav_tree.width(), view.width(), view.results_nav_splitter.sizes(), view._restored_splitter_proportions)
    assert view.report_action.isChecked()
    view.report_action.trigger()
    assert not view.report_action.isChecked()
    view.report_action.trigger()
    app.processEvents()
    assert view.report_text.isVisible()
    view.copy_report_action.trigger()
    assert app.clipboard().text() == view.report_text.toPlainText()
    report_path = work / "analysis.txt"
    with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(report_path), "")):
        view.export_report_action.trigger()
    assert report_path.read_text(encoding="utf-8") == app.clipboard().text()
    assert str(report_path) in view.statusbar.currentMessage()
    with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=("", "")):
        view.export_report_action.trigger()
    record("ux-readable-report", view, clipboard=app.clipboard().text(), saved=str(report_path))
    plot_item = next(item for item in view._svg_plot_items)
    nav = next(item for item in view.nav_tree.findItems("Forest Plot", QtCore.Qt.MatchFlag.MatchExactly))
    view.nav_tree.setCurrentItem(nav)
    app.processEvents()
    assert view.export_plot_action.isEnabled()
    assert not view.report_text.isVisible()
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
    record("ux-plot-toolbar", view, saved=str(plot_path), zoom=125)
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
    source = work / "mapped.csv"
    source.write_text('Study,Year,A events,A total,B events,B total,OR,Lower,Upper,Dose\n"Alpha, München",2020,1,10,2,12,,,,5\nBeta,2021,3,11,4,13,,,,7\n', encoding="utf-8")
    with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(source), "")):
        mouse_click(page.select_file_btn, QtCore.Qt.MouseButton.LeftButton)
    assert not page.isComplete()
    assert "Study Name" in page.import_status.text()
    record("ux-csv-invalid", wizard, message=page.import_status.text())
    for control, index in zip(page.mapping_controls, range(9)):
        control.setCurrentIndex(control.findData(index))
    assert page.isComplete()
    assert page.preview_table.rowCount() == 2
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

    form = add_new_dialogs.AddCovariateDialog(window)
    form.show()
    app.processEvents()
    button = required(form.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
    assert not button.isEnabled()
    form.covariate_name_le.setText("Dose")
    mouse_click(button, QtCore.Qt.MouseButton.LeftButton)
    assert form.isVisible()
    assert form.error_label.text()
    record("ux-covariate-error", form, error=form.error_label.text())
    form.covariate_name_le.setText("Region")
    mouse_click(button, QtCore.Qt.MouseButton.LeftButton)
    assert form.result() == QtWidgets.QDialog.DialogCode.Accepted.value
    record("ux-mapped-reopened", window, project=window.out_path)
