"""Drive TSA setup, results, saved plot styles and exports through Qt and R."""
import csv
import json
import os
from math import ceil, isclose
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from PyQt6 import QtCore, QtGui, QtWidgets

from rc_metastudio import analysis_catalog, analysis_dataset, project_adapter, project_format
from rc_metastudio.analysis_setup_dialog import AnalysisSetupDialog
from rc_metastudio.analysis_unit import AnalysisUnit
from rc_metastudio.domain_ids import ArmId, RowId, SheetId
from rc_metastudio.plot_editor_dialog import EditPlotDialog
from rc_metastudio.results_window import ResultsWindow
from rc_metastudio.trial_sequential_analysis_dialog import TrialSequentialAnalysisDialog
from tests.e2e.report_retention import assert_exports, capture
from tests.python.gui.qt_test_support import key_clicks, wait

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "tests/analysis_regression/baseline"
NAMESPACE = "{http://www.w3.org/2000/svg}"


def input_project(work, case):
    if case in ("bcg", "peto", "hr"):
        return ROOT / "sample_projects" / ("BCG.rcms" if case != "hr" else "Pignon2000-HR.rcms")
    binary = case == "rr-mh"
    stress = case == "stress"
    metric = "RR" if binary else "MD" if stress else case.upper()
    arms = [analysis_dataset.Arm(ArmId(label), label) for label in ("Treatment", "Comparator")]
    sheet = analysis_dataset.Sheet(
        SheetId("tsa"), f"TSA {case}", analysis_catalog.BINARY if binary else analysis_catalog.CONTINUOUS,
        "proportions" if binary else ("smd" if case == "smd" else "means"),
        "binary" if binary else "continuous", arms,
        settings={"metric": metric, "favours_labels": ["Favours Treatment", "Favours Comparator"],
                  "analysis": {"method": "binary.fixed.mh" if binary else "continuous.fixed"}},
    )
    raw = (
        ([[0, 100], [0, 100]], *([[10, 100], [10, 100]] for _ in range(5)))
        if binary else (
            [[25, 4, 2], [25, 5, 2]],
            [[50, 4.5, 2], [50, 5, 2]],
            [[75, 4, 2], [75, 5, 2]],
        )
    )
    if stress:
        sheet.settings["favours_labels"] = [
            "Favours the new extended therapy programme",
            "Favours conventional outpatient management",
        ]
        raw = tuple([[25 + 2*i, 4.5, 2], [25 + 2*i, 5, 2]] for i in range(36))
    for i, cells in enumerate(raw):
        unit = AnalysisUnit(sheet, cells, arm_names=[a.name for a in arms], arm_stable_ids=[a.id for a in arms])
        sheet.rows.append(analysis_dataset.StudyRow(
            RowId(str(i)), "Double zero" if binary and i == 0 else f"Trial {i + 1}", unit, 2000 + i,
        ))
    path = work / f"{case}.rcms"
    project_format.save_project(path, project_adapter.dataset_to_project(analysis_dataset.Dataset(sheets=[sheet])),
                                {"schema_version": project_format.CURRENT_FORMAT_VERSION, "current_sheet_id": sheet.id})
    return path


def compare_numeric(table, case, record, view):
    contract = json.loads((BASELINE / "tsa-numeric-contract.json").read_text(encoding="utf-8"))
    expected = contract["cases"][case]
    actual = {}
    for row, column, role, value in expected:
        quantity, = [q for q in table.quantities[row][table.headers.index(column)] if q.role == role]
        assert isclose(quantity.value, value, rel_tol=1e-6, abs_tol=1e-10), (row, column, quantity.value, value)
        actual[f"{row + 1}: {column} ({role})"] = quantity.value
    record("tsa-numeric-contract", view, case=case, expected=expected, actual=actual)


def check_artwork(path, case, style, contract, *, percent=False):
    svg = ET.parse(path).getroot()
    text_nodes = list(svg.iter(NAMESPACE + "text"))
    labels = [node.text or "" for node in text_nodes]
    assert set(contract["labels"]) <= set(labels), labels
    assert ("Penalised Z-curve" in labels) == (case == "bcg")
    xlabel = contract["axis_titles"]["percent" if percent else "hr" if case == "hr" else "participants"]
    axis_index = labels.index(xlabel)
    assert any(label.startswith("Required information") and " · Accrued " in label for label in labels)
    if case == "hr":
        assert "Required information 4,222 · Accrued 1,775 (42%)" in labels
    if case == "peto":
        assert any("(6301%)" in label for label in labels), labels
    axis_end = next(i for i in range(axis_index + 1, len(labels)) if labels[i].startswith("−"))
    ticks = labels[axis_index + 1:axis_end]
    assert 1 <= len(ticks) <= 6, ticks
    assert ("//" in labels) == (case in ("bcg", "peto"))
    if case == "peto":
        assert "−8" in labels and "8" in labels, labels
    favours = [node for node in text_nodes if (node.text or "").startswith("Favours")]
    assert len(favours) == 2 and all("rotate(-90" in node.attrib.get("transform", "") for node in favours), labels
    assert contract["accents"][style].lower() in path.read_text(encoding="utf-8").lower()
    monitoring = [node for node in svg.iter(NAMESPACE + "polyline")
                  if "#333333" in node.attrib.get("style", "") and "stroke-dasharray" not in node.attrib["style"]]
    assert monitoring and len(monitoring[0].attrib["points"].split()) >= 2
    panel, = [group for group in svg.iter(NAMESPACE + "g") if monitoring[0] in list(group)]
    clip = panel.attrib["clip-path"].removeprefix("url(#").removesuffix(")")
    bounds = svg.find(f".//{NAMESPACE}clipPath[@id='{clip}']/{NAMESPACE}rect")
    assert bounds is not None
    _, _, width, _ = map(float, svg.attrib["viewBox"].split())
    assert float(bounds.attrib["width"]) / width >= .72, bounds.attrib
    if case == "peto":
        assert any("#333333" in node.attrib.get("style", "")
                   for node in svg.iter(NAMESPACE + "circle")), "Missing crossing ring"
    return ticks


def run(app, window, work, record, case):
    from advanced_workflows import click, modal

    path = input_project(work, case)
    assert window.open(str(path), raise_on_error=True)
    action = window.action_trial_sequential_analysis
    if case == "smd":
        assert not action.isEnabled() and "supports two-arm RR" in action.toolTip()
        menu = window.menuAnalysis
        assert menu.toolTipsVisible()
        menu.popup(window.mapToGlobal(QtCore.QPoint(40, 40)))
        app.processEvents()
        target = menu.actionGeometry(action).center()
        global_target = menu.mapToGlobal(target)
        QtGui.QCursor.setPos(global_target)
        app.processEvents()
        help_event = QtGui.QHelpEvent(QtCore.QEvent.Type.ToolTip, target, global_target)
        assert menu.actionAt(target) is action
        handled = app.sendEvent(menu, help_event)
        wait(350)
        assert QtWidgets.QToolTip.isVisible() and QtWidgets.QToolTip.text() == action.toolTip(), (
            handled, target, menu.isVisible(), QtWidgets.QToolTip.text(),
        )
        tip, = [widget for widget in app.topLevelWidgets()
                if widget.windowType() == QtCore.Qt.WindowType.ToolTip and widget.isVisible()]
        tooltip_path = work / "smd-tooltip.png"
        assert tip.grab().save(str(tooltip_path))
        record("tsa-ineligible-smd", window, menu, tooltip=action.toolTip(),
               tooltip_image=str(tooltip_path), input=str(path))
        QtWidgets.QToolTip.hideText()
        menu.close()
        return None

    assert action.isEnabled() and not action.icon().isNull()
    if case in ("bcg", "peto"):
        window.action_go.trigger()
        app.processEvents()
        setup, = [widget for widget in app.topLevelWidgets()
                  if isinstance(widget, AnalysisSetupDialog) and widget.isVisible()]
        setup.method_cbo_box.setCurrentText(next(
            label for label, method in setup.available_method_d.items() if method == "binary.fixed.peto"
        ))
        click(app, setup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
        fit, = [widget for widget in app.topLevelWidgets() if isinstance(widget, ResultsWindow) and widget.isVisible()]
        fit.close()
        assert not window.workspace.is_dirty, "Ordinary meta-analysis changed the project"

        def run_default(dialog):
            assert dialog.run_button.isEnabled(), dialog.status.text()
            dialog.run_button.click()
            assert dialog.result() == dialog.DialogCode.Accepted, dialog.status.text()

        modal(app, TrialSequentialAnalysisDialog, run_default, action.trigger)
        default_view, = [widget for widget in app.topLevelWidgets()
                         if isinstance(widget, ResultsWindow) and widget.isVisible()]
        methods = default_view.manuscript.methods
        assert "fixed-effect (Peto) model" in methods
        record("tsa-default-run", default_view, project_dirty=window.workspace.is_dirty, methods=methods)
        assert not window.workspace.is_dirty, "Default TSA changed the project"
        if case == "bcg":
            default_view.close()
            assert window.open(str(path), raise_on_error=True)

    comparison = {
        "bcg": "crossed the monitoring boundary favouring",
        "rr-mh": "crossed the futility boundary",
        "md": "crossed neither a monitoring nor a futility boundary",
        "hr": "crossed the monitoring boundary favouring",
    }.get(case)

    def configure(dialog):
        if case == "hr":
            assert "Publication year is required" in dialog.status.text()
            dialog.order.setCurrentIndex(dialog.order.findData("table"))
        if case == "bcg":
            dialog.order.setCurrentIndex(dialog.order.findData("table"))
            dialog.lil.setChecked(True)
        wait(300)
        original = dialog.effect.text()
        if case == "bcg":
            assert original == "0.6835" and dialog.control.text() == "4.49"
            for index, label in enumerate(dialog.base_request.favoured_labels(), 1):
                assert dialog.test.itemText(index) == f"One-sided (favours {label})"
            record("tsa-dialog-default", dialog, input=str(path), effect=original, control=dialog.control.text())
            for field, value in ((dialog.effect, ".7"), (dialog.control, "5.00")):
                field.selectAll()
                key_clicks(field, value)
            wait(300)
            for field in (dialog.effect, dialog.control):
                source, button = dialog.default_inputs[field]
                assert source.text() == "Entered" and button.isVisible()
            record("tsa-dialog-entered", dialog, effect=dialog.effect.text(), control=dialog.control.text())
            for field in (dialog.effect, dialog.control):
                dialog.default_inputs[field][1].click()
            wait(300)
            assert dialog.effect.text() == original and dialog.control.text() == "4.49"
            assert not any(button.isVisible() for _, button in dialog.default_inputs.values())
            record("tsa-dialog-restored", dialog, effect=dialog.effect.text(), control=dialog.control.text())
        elif case in ("rr-mh", "md", "stress"):
            if case in ("md", "stress"):
                assert not dialog.run_button.isEnabled() and not original
                key_clicks(dialog.effect, "-1")
            else:
                assert "fixed (MH)" in dialog.base_request.model_label
            dialog.manual.setChecked(True)
            dialog.manual_ris.setText("1000" if case == "rr-mh" else "10000")
            wait(300)
        assert dialog.run_button.isEnabled(), dialog.status.text()
        record("tsa-configured", dialog, input=str(path), status=dialog.status.text())
        dialog.run_button.click()
        assert dialog.result() == dialog.DialogCode.Accepted, dialog.status.text()

    if case != "peto":
        modal(app, TrialSequentialAnalysisDialog, configure, action.trigger)
    view, = [widget for widget in app.topLevelWidgets() if isinstance(widget, ResultsWindow) and widget.isVisible()]
    table, = view._report_tables
    if case == "stress":
        assert len(table.rows) == 36
    elif case != "peto":
        compare_numeric(table, case, record, view)
    if case == "rr-mh":
        assert len(table.rows) == 5 and all(row[1] != "Double zero" for row in table.rows)
        assert table.rows[-1][3] == "100.0" and table.rows[-1][6] == ""
        assert "The fitted model excluded Double zero." in view.manuscript.methods
    if case == "bcg":
        assert table.rows[0][8] == "<0.001 to >1000"
        assert all(row[6] == "" for row in table.rows if float(row[3]) >= 100)
        assert "We pooled odds ratios (OR)" in view.manuscript.methods
        assert "logarithm with λ = 2 (Hu 2007)" in view.manuscript.methods
    if comparison is not None:
        assert comparison in view.manuscript.results, view.manuscript.results
    assert "Accrued information is" in view.manuscript.results
    assert "Supplementary details" not in view.manuscript.html(supplementary=True)
    assert "Marker area is proportional to the information each trial added." in view.manuscript.html()

    section, = [s for s in view.results.sections if s.kind == "image"]
    nav, = view.nav_tree.findItems(section.title, QtCore.Qt.MatchFlag.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive)
    view.nav_tree.setCurrentItem(nav)
    view.report_action.setChecked(False)
    view.showNormal()
    screen = view.screen().availableGeometry()
    height = int(.92 * screen.height())
    view.resize(min(screen.width() - 30, int(1.8 * (height - 140) + 170)), height)
    view.move(screen.topLeft() + QtCore.QPoint(12, 24))
    wait(250)
    view.fit_width_action.trigger()
    wait(150)
    artifact, _ = view._selected_plot()
    descriptor = json.loads((BASELINE / "tsa-plot-descriptors.json").read_text(encoding="utf-8"))
    assert artifact.title == descriptor["identity"]
    assert artifact.capability.plot_kind == descriptor["kind"]
    assert artifact.capability.regenerator == descriptor["regeneration"]
    assert artifact.capability.styleable and artifact.capability.editable
    if case == "peto":
        original_report = view.manuscript.plain_text()
        for before, after in (("participants", "percent"), ("percent", "participants")):
            def edit_axis(dialog):
                assert dialog.tsa_x_axis.currentData() == before
                dialog.tsa_x_axis.setCurrentIndex(dialog.tsa_x_axis.findData(after))
                click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
                assert dialog.result() == dialog.DialogCode.Accepted
            modal(app, EditPlotDialog, edit_axis, view.edit_plot_action.trigger)
            artifact, _ = view._selected_plot()
            params = view.plot_service.load_params(artifact.params_path)
            assert params and params["tsa_x_axis"] == after
            axis_artwork = work / f"peto-axis-{after}.svg"
            axis_artwork.write_bytes(Path(artifact.display_path()).read_bytes())
            ticks = check_artwork(axis_artwork, case, "default", descriptor, percent=after == "percent")
            assert view.manuscript.plain_text() == original_report
            record("tsa-axis-choice", view, units=after, ticks=ticks, plots={artifact.title: str(axis_artwork)})

    for style in ("default", "revman", "bmj"):
        if style != "default":
            def edit(dialog):
                dialog.style_cbo.setCurrentIndex(dialog.style_cbo.findData(style))
                dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).click()
                assert dialog.result() == dialog.DialogCode.Accepted
            modal(app, EditPlotDialog, edit, view.edit_plot_action.trigger)
        artifact, _ = view._selected_plot()
        view.fit_width_action.trigger()
        wait(150)
        rendered = work / f"{case}-{style}.svg"
        rendered.write_bytes(Path(artifact.display_path()).read_bytes())
        ticks = check_artwork(rendered, case, style, descriptor)
        for suffix in ("res", "params", "plotdata", "data"):
            bundle = Path(f"{artifact.params_path}.{suffix}")
            (work / f"{case}-{style}.{suffix}").write_bytes(bundle.read_bytes())
        _, item = view._selected_plot()
        assert item.sceneBoundingRect().width() >= .95 * view._plot_viewport_width()
        screen_plot = work / f"{case}-{style}-viewport.png"
        viewport = view.graphics_view.viewport()
        assert viewport is not None
        bounds = view.graphics_view.mapFromScene(item.sceneBoundingRect()).boundingRect()
        overflow = bounds.bottom() - viewport.rect().bottom()
        if overflow > 1:
            shrink = ceil((overflow + 8) * bounds.width() / bounds.height())
            view.resize(view.width() - shrink, view.height())
            view.fit_width_action.trigger()
            wait(150)
            bounds = view.graphics_view.mapFromScene(item.sceneBoundingRect()).boundingRect()
        assert viewport.rect().adjusted(-1, -1, 1, 1).contains(bounds), (viewport.rect(), bounds)
        assert viewport.grab(bounds.intersected(viewport.rect())).save(str(screen_plot))
        record(f"tsa-{case}-{style}", view, style=style, dpi_scale=view.devicePixelRatio(),
               input=str(path), viewport=str(screen_plot), ticks=ticks,
               plots={artifact.title: str(rendered)})
        if case == "peto" and style == "default" and os.environ.get("RCMS_TSA_DESIGN_EXPORTS") == "1":
            from PIL.TiffImagePlugin import TiffImageFile
            from rc_metastudio.plot_export_dialog import PlotExportDialog

            export = work / "peto-89mm-300dpi.tiff"

            def configure_export(dialog):
                dialog.format_control.setCurrentIndex(dialog.format_control.findData("tiff"))
                dialog.units.setCurrentText("cm")
                dialog.width_control.setValue(8.9)
                dialog.dpi.setValue(300)
                record("tsa-print-options", dialog, dimensions=dialog.dimensions())
                dialog.accept()

            with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(export), "")):
                modal(app, PlotExportDialog, configure_export, view.export_plot_action.trigger)
            with TiffImageFile(export) as image:
                assert abs(image.width - 89/25.4*300) <= 1
                dpi = tuple(map(float, image.info["dpi"]))
                assert image.tag_v2[259] == 5 and dpi == (300.0, 300.0)
                record("tsa-print-export", view, pixels=image.size, dpi=dpi,
                       exports={"tiff": str(export)})

    if case in ("stress", "peto"):
        window.workspace.mark_saved()
        return view

    view.report_action.setChecked(True)
    app.processEvents()
    record("tsa-report", view, results=view.manuscript.results)
    report = capture(view, work / "reports")
    # Poppler emits continuations of split HR cells in page order. DOCX,
    # clipboard and CSV still compare every cell in table order.
    assert_exports(view, report, pdf_ordered=case != "hr")
    view.tables_action.trigger()
    for action, name, filter_name in (
        (view.export_table_action, "formatted", "CSV table"),
        (view.export_values_action, "values", "CSV values"),
    ):
        export = work / f"{case}-{name}.csv"
        with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(export), f"{filter_name} (*.csv)")):
            action.trigger()
        with export.open(encoding="utf-8-sig", newline="") as stream:
            if name == "formatted":
                assert list(csv.reader(stream)) == [list(table.headers), *map(list, table.rows)]
            else:
                values = list(csv.DictReader(stream))
                exported_z = next(row for row in values if row["Column"] == "Z")
                assert float(exported_z["Value"]) == table.quantities[0][4][0].value
    view.report_action.setChecked(False)
    view.nav_tree.setCurrentItem(nav)
    app.processEvents()
    if case == "md":
        assert window.workspace.is_dirty, "Entered TSA design should be saved with the project"
        saved = work / "md-with-tsa-design.rcms"
        assert window.save(destination=saved)
        assert window.open(str(saved), raise_on_error=True)

        def rerun_saved(dialog):
            assert dialog.effect.text() == "-1" and dialog.manual_ris.text() == "10000"
            assert dialog.run_button.isEnabled(), dialog.status.text()
            record("tsa-reopened-design", dialog, input=str(saved), effect=dialog.effect.text(),
                   ris=dialog.manual_ris.text())
            dialog.run_button.click()
            assert dialog.result() == dialog.DialogCode.Accepted, dialog.status.text()

        modal(app, TrialSequentialAnalysisDialog, rerun_saved, window.action_trial_sequential_analysis.trigger)
        repeated, = [widget for widget in app.topLevelWidgets()
                     if isinstance(widget, ResultsWindow) and widget.isVisible() and widget is not view]
        repeated.close()
        assert not window.workspace.is_dirty, "Rerunning the saved TSA design changed the project"
    else:
        window.workspace.mark_saved()
    return view
