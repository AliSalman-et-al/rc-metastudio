"""Real desktop proof for result controls, mapped CSV and input recovery."""

import csv
from pathlib import Path
from typing import Callable, cast
from unittest.mock import patch

from PyQt6 import QtCore, QtGui, QtWidgets, QtTest

from tests.python.gui.test_types import mouse_click, key_click, required, wait


def run(app, window, work, root, record, analyze):
    from rc_metastudio import add_new_dialogs, main_wizard, automation
    from PyQt6 import sip

    def close_result(view):
        view.close()
        automation.dispose_qobjects(app, (view,))
        assert sip.isdeleted(view)

    window.showMaximized()
    app.processEvents()
    app.processEvents()
    assert not window.workspace.is_dirty
    assert "Unsaved changes" not in window.dataset_file_lbl.text()
    assert "*" not in window.windowTitle()
    record("ux-empty-workspace", window, guidance=window.start_page.accessibleName(), device_pixel_ratio=window.devicePixelRatioF(), logical_size=[window.width(), window.height()])
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
    assert setup.analysis_error_label.text() == "Check the selected method and study data, then try again."
    assert setup.analysis_error_details.isHidden()
    mouse_click(setup.analysis_error_toggle, QtCore.Qt.MouseButton.LeftButton)
    assert setup.analysis_error_details.isVisible()
    assert "Unknown 'method' specified" in setup.analysis_error_details.toPlainText()
    mouse_click(setup.analysis_error_toggle, QtCore.Qt.MouseButton.LeftButton)
    assert not any(isinstance(widget, QtWidgets.QMessageBox) and widget.isVisible() for widget in app.topLevelWidgets())
    record("ux-inline-analysis-error", setup, message=setup.analysis_error_label.text())
    setup.current_param_vals["rm.method"] = "DL"
    mouse_click(required(setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)), QtCore.Qt.MouseButton.LeftButton)
    app.processEvents()
    from rc_metastudio.results_window import ResultsWindow
    recovered = next(widget for widget in app.topLevelWidgets() if isinstance(widget, ResultsWindow) and widget.isVisible())
    assert recovered.results.images
    record("ux-analysis-recovered", recovered, plots=dict(recovered.results.display_images), texts=dict(recovered.texts))
    close_result(recovered)
    app.processEvents()
    view = analyze(app, window, "binary.random")
    assert "clinical failure" in view.results.identity
    assert "Odds Ratio" in view.results.identity
    assert view.nav_tree.width() < view.width() / 3, (view.nav_tree.width(), view.width(), view.results_nav_splitter.sizes(), view._restored_splitter_proportions)
    assert not view.report_action.isChecked()
    assert view.content_stack.currentWidget() is view.figure_page
    from xml.etree import ElementTree
    svg = " ".join(ElementTree.parse(next(iter(view.results.display_images.values()))).getroot().itertext())
    nodes = list(ElementTree.parse(next(iter(view.results.display_images.values()))).getroot().iter("{http://www.w3.org/2000/svg}text"))
    directions = [node for node in nodes if "Favours" in "".join(node.itertext())]
    assert len(directions) == 2
    def box(node):
        import re
        x, y = float(node.attrib["x"]), float(node.attrib["y"])
        match = re.search(r"font-size:\s*([\d.]+)", node.attrib["style"])
        assert match is not None
        size = float(match[1])
        width = float(node.attrib["textLength"].removesuffix("px"))
        anchor = node.attrib.get("text-anchor", "start")
        x -= width if anchor == "end" else width / 2 if anchor == "middle" else 0
        return QtCore.QRectF(x, y - size, width, size)
    for node in directions:
        assert "\n" not in "".join(node.itertext())
        assert not any(box(node).intersects(box(other)) for other in nodes if other is not node)
    assert directions[0].attrib["y"] == directions[1].attrib["y"]
    view.showNormal()
    view.resize(1280, 800)
    app.processEvents()
    app.processEvents()
    selected_item = view._selected_plot()[1]
    effective_scale = selected_item.deviceTransform(view.graphics_view.viewportTransform()).m11()
    svg_root = ElementTree.parse(view._selected_plot()[0].display_path()).getroot()
    coordinate_scale = selected_item.boundingRect().width() / float(svg_root.attrib["viewBox"].split()[2])
    study = next(node for node in nodes if "Gonzalez" in "".join(node.itertext()))
    label_pt = box(study).height() * coordinate_scale * effective_scale * 72 / 96
    bounds = box(nodes[0])
    for node in nodes[1:]:
        bounds = bounds.united(box(node))
    coverage = bounds.width() * coordinate_scale * effective_scale / view.graphics_view.viewport().width()
    nav_names = {item.text(0) for item in view.nav_tree.findItems("", QtCore.Qt.MatchFlag.MatchContains | QtCore.Qt.MatchFlag.MatchRecursive)}
    duplicates = [action.text() for toolbar in view.findChildren(QtWidgets.QToolBar) for action in toolbar.actions() if action.text() in nav_names]
    record("slice8b-readability", view, study_label_pt=label_pt, drawn_width_fraction=coverage, duplicate_navigation=duplicates)
    assert not duplicates, duplicates
    assert label_pt >= 9, label_pt
    assert coverage >= .85, coverage
    original_palette = app.palette()
    for theme, background, text, base in (("light", "#efefef", "#202020", "#ffffff"), ("dark", "#303238", "#f0f0f0", "#25272b")):
        palette = QtGui.QPalette(original_palette)
        for role in (QtGui.QPalette.ColorRole.Window, QtGui.QPalette.ColorRole.Button):
            palette.setColor(role, QtGui.QColor(background))
        for role in (QtGui.QPalette.ColorRole.WindowText, QtGui.QPalette.ColorRole.Text, QtGui.QPalette.ColorRole.ButtonText):
            palette.setColor(role, QtGui.QColor(text))
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(base))
        app.setPalette(palette)
        for page in ("forest", "manuscript", "tables"):
            item = next(item for item in view.nav_tree.findItems("", QtCore.Qt.MatchFlag.MatchContains | QtCore.Qt.MatchFlag.MatchRecursive) if item.text(0) == {"forest": "Forest Plot", "manuscript": "Manuscript", "tables": "Tables"}[page])
            view.nav_tree.setCurrentItem(item)
            app.processEvents()
            app.processEvents()
            if page == "tables":
                table = view.result_table
                assert table.accessibleName() == "Model results"
                assert not table.horizontalScrollBar().isVisible()
                last_row = table.visualRect(table.model().index(table.rowCount() - 1, 0))
                row_bottom = table.viewport().mapTo(view.tables_page, last_row.bottomLeft()).y()
                button = view.table_controls.widgetForAction(view.copy_table_action)
                button_top = button.mapTo(view.tables_page, button.rect().topLeft()).y()
                assert 0 <= button_top - row_bottom <= 32, (button_top, row_bottom)
            record("slice8b-results-" + page + "-" + theme, view)
    app.setPalette(original_palette)
    view.nav_tree.setCurrentItem(next(item for item in view.nav_tree.findItems("Forest Plot", QtCore.Qt.MatchFlag.MatchExactly)))
    app.processEvents()


    for arm in window.model.arm_names:
        assert "Favours" in svg and arm in svg
    assert not hasattr(view, "identity_label")
    assert view._fit_width_active
    for width in (900, 796):
        view.resize(width, 796)
        app.processEvents()
        app.processEvents()
        selected_item = view._selected_plot()[1]
        effective_scale = selected_item.deviceTransform(view.graphics_view.viewportTransform()).m11()
        assert view.zoom_control.value() == round(effective_scale * 100), (view.zoom_control.value(), effective_scale)
    record("slice2d-results-forest", view, effective_scale=effective_scale)
    for item in view.nav_tree.findItems("", QtCore.Qt.MatchFlag.MatchContains | QtCore.Qt.MatchFlag.MatchRecursive):
        assert view.nav_tree.fontMetrics().horizontalAdvance(item.text(0)) + 30 < view.nav_tree.width(), item.text(0)
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
    assert copied_report.startswith(view.manuscript.title + "\n")
    for section in view.results.sections:
        for table in section.tables:
            assert all(cell in copied_report for cell in table.headers)
            assert all(cell in copied_report for row in table.rows for cell in row)
    view.copy_report_action.trigger()
    assert app.clipboard().text() == copied_report
    report_path = work / "analysis.pdf"
    with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(report_path), "")):
        view.export_report_action.trigger()
    assert report_path.read_bytes().startswith(b"%PDF")
    assert app.clipboard().mimeData().hasHtml()
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
    record("slice2c-results-forest", view)
    close_result(view)
    for custom in (False, True):
        if custom:
            edited = analyze(app, window, "binary.random")
            editor_errors = []
            def customise():
                dialog = app.activeModalWidget()
                try:
                    assert isinstance(dialog, QtWidgets.QDialog)
                    assert cast(Callable[..., bool], QtTest.QTest.qWaitForWindowExposed)(dialog, 5000)
                    record("ux-custom-editor-visible", dialog)
                    dialog.favours_left.setText("Favours custom first")
                    dialog.favours_right.setText("Favours custom second")
                    mouse_click(required(dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)), QtCore.Qt.MouseButton.LeftButton)
                except BaseException as error:
                    editor_errors.append(error)
                    if dialog is not None:
                        dialog.reject()
            record("ux-custom-editor-before", edited)
            QtCore.QTimer.singleShot(0, customise)
            edited.edit_plot_action.trigger()
            assert not editor_errors, editor_errors
            record("ux-custom-editor-after", edited)
            assert window.model.current_sheet.settings["favours_labels"] == ["Favours custom first", "Favours custom second"]
            close_result(edited)
        before = list(window.model.arm_names)
        window.action_swap_arms.trigger()
        swapped = analyze(app, window, "binary.random")
        text = " ".join(" ".join(ElementTree.parse(next(iter(swapped.results.display_images.values()))).getroot().itertext()).split())
        left, right = ("custom second", "custom first") if custom else (before[1], before[0])
        assert text.index(left) < text.index(right), text
        assert text.count("Favours") >= 2
        record("favours-swapped", swapped, custom=custom, svg_text=text)
        close_result(swapped)
        window.action_swap_arms.trigger()

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
    assert window.model.current_sheet.rows[0].label == "Alpha, München"
    assert window.model.current_sheet.rows[1].covariate_values[next(c["id"] for c in window.model.current_sheet.covariates if c["name"] == "Dose")] == 7.0
    assert window.model.get_current_raw_data_for_study(0) == [1, 10, 2, 12]
    window.out_path = str(work / "mapped.rcms")
    assert window.save()
    assert window.open(window.out_path, raise_on_error=True)
    analyze(app, window, "binary.random").close()
    for column, value in ((window.model.RAW_DATA[1], 10000), (window.model.RAW_DATA[3], 10000), (window.model.RAW_DATA[0], 1), (window.model.RAW_DATA[2], 5000)):
        assert window.model.setData(window.model.index(0, column), value)
    estimate = str(window.model.data(window.model.index(0, window.model.OUTCOMES[0])))
    assert estimate == "<0.01"
    stored_estimate = float(window.model.data(window.model.index(0, window.model.OUTCOMES[0]), QtCore.Qt.ItemDataRole.EditRole))
    assert 0 < stored_estimate < .001
    assert abs(stored_estimate - 1 / 9999) < 1e-6
    record("ux-small-ratio", window, raw=[1, 10000, 5000, 10000], displayed_estimate=estimate)

    form = add_new_dialogs.AddCovariateDialog(window, existing_names=[c["name"] for c in window.model.current_sheet.covariates])
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
