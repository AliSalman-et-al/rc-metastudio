"""Drive TSA setup, results, saved plot styles and exports through Qt and R."""
import csv
import json
import os
from math import ceil, isclose
from pathlib import Path
from statistics import median
from time import perf_counter
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
    if case in ("bcg", "hr"):
        return ROOT / "sample_projects" / ("BCG.rcms" if case == "bcg" else "Pignon2000-HR.rcms")
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


def check_artwork(path, case, style, contract):
    svg = ET.parse(path).getroot()
    text_nodes = list(svg.iter(NAMESPACE + "text"))
    labels = {"".join(node.itertext()) for node in text_nodes}
    assert set(contract["labels"]) <= labels, labels
    assert ("Penalised Z-curve" in labels) == (case == "bcg")
    assert any(label.startswith("Required information") and "Accrued:" in label for label in labels)
    if case == "hr":
        assert "Required information: 4,222.1 · Accrued: 1,775.3 (42%)" in labels
    ticks = [node for node in text_nodes if (node.text or "").endswith("%")]
    assert ticks and all("font-weight" not in node.attrib["style"] for node in ticks)
    expected_ticks = contract["information_ticks"]["bcg" if case == "bcg" else "through_200_percent"]
    assert [node.text for node in ticks] == [f"{value}%" for value in expected_ticks]
    favours = [node for node in text_nodes if f'fill: {contract["favours_color"]};' in node.attrib["style"]]
    assert sum((node.text or "").startswith("Favours ") for node in favours) == 2
    assert all("transform" not in node.attrib and "font-weight" not in node.attrib["style"]
               and node.attrib.get("text-anchor", "start") == "start" for node in favours)
    if case == "stress":
        lines = sorted(favours, key=lambda node: float(node.attrib["y"]))
        assert len(lines) == 4
        assert " ".join(node.text or "" for node in lines[:2]) == "Favours conventional outpatient management"
        assert " ".join(node.text or "" for node in lines[2:]) == "Favours the new extended therapy programme"
    assert "100%" in labels and "RIS" in labels
    accent = contract["accents"][style]
    assert accent.lower() in path.read_text(encoding="utf-8").lower()
    _, _, width, height = map(float, svg.attrib["viewBox"].split())
    assert 1.5 < width / height < 2.2
    for node in text_nodes:
        if "x" in node.attrib and "fill: #222222;" in node.attrib["style"]:
            assert node.attrib["style"].startswith(f'font-size: {contract["legend_font_size"]};')
            end = float(node.attrib["x"]) + float(node.attrib["textLength"].removesuffix("px"))
            assert end <= width, (node.text, end, width)
    monitoring = [node for node in svg.iter(NAMESPACE + "polyline")
                  if "#333333" in node.attrib.get("style", "") and "stroke-dasharray" not in node.attrib["style"]]
    assert monitoring and len(monitoring[0].attrib["points"].split()) >= 100
    panel, = [group for group in svg.iter(NAMESPACE + "g") if monitoring[0] in list(group)]
    clip = panel.attrib["clip-path"].removeprefix("url(#").removesuffix(")")
    bounds = svg.find(f".//{NAMESPACE}clipPath[@id='{clip}']/{NAMESPACE}rect")
    assert bounds is not None
    left, top, wide, tall = (float(bounds.attrib[key]) for key in ("x", "y", "width", "height"))
    panel_end = left + wide
    for node in favours:
        x, y = (float(node.attrib[key]) for key in ("x", "y"))
        size = float(node.attrib["textLength"].removesuffix("px"))
        assert left < x < left + .05 * wide and x + size < panel_end
        assert top < y < top + tall and min(y - top, top + tall - y) < .20 * tall
    lines = list(svg.iter(NAMESPACE + "line"))
    legend_samples = []
    for color in ("#A6A6A6", "#4A4A4A"):
        plotted = [node for node in lines if node in list(panel) and color in node.attrib["style"]]
        sample, = [node for node in lines if color in node.attrib["style"]
                   and float(node.attrib["x1"]) > panel_end]
        assert plotted and sample.attrib["style"] == plotted[0].attrib["style"]
        dash = sample.attrib["style"].split("stroke-dasharray: ")[1].split(";")[0]
        length = float(sample.attrib["x2"]) - float(sample.attrib["x1"])
        assert length >= sum(map(float, dash.split(","))) * contract["legend_min_dash_periods"]
        legend_samples.append(dash)
    assert len(set(legend_samples)) == 2
    wedge = [node for node in panel.findall(NAMESPACE + "polygon")
             if accent in node.attrib["style"] and "stroke-dasharray" in node.attrib["style"]]
    boxes = [node for node in panel.findall(NAMESPACE + "rect")
             if "stroke: none" in node.attrib.get("style", "")]
    assert len(boxes) == 2
    paint_order = list(svg.iter())
    assert max(map(paint_order.index, wedge)) < min(map(paint_order.index, boxes))
    assert max(map(paint_order.index, favours)) < min(map(paint_order.index, monitoring))
    if case == "stress":
        bottom = max(boxes, key=lambda node: float(node.attrib["y"]))
        x, y, w, h = (float(bottom.attrib[key]) for key in ("x", "y", "width", "height"))
        bubbles = [node for node in svg.iter(NAMESPACE + "circle") if f"fill: {accent};" in node.attrib["style"]
                   and x < float(node.attrib["cx"]) < x + w and y < float(node.attrib["cy"]) < y + h]
        assert bubbles and all(paint_order.index(node) > paint_order.index(bottom) for node in bubbles)
    swatch, = [node for node in svg.iter(NAMESPACE + "rect")
               if wedge and node.attrib.get("style") == wedge[0].attrib["style"]]
    assert float(swatch.attrib["x"]) > panel_end and float(swatch.attrib["width"]) >= 8
    crossings = [node for node in svg.iter(NAMESPACE + "circle") if "#333333" in node.attrib.get("style", "")]
    if case != "stress":
        assert bool(crossings) == (case != "md")
    if case == "bcg":
        held = [node for node in svg.iter(NAMESPACE + "line")
                if "#333333" in node.attrib.get("style", "") and "stroke-dasharray" in node.attrib["style"]]
        tip = monitoring[0].attrib["points"].split()[-1]
        assert any(f"{node.attrib['x1']},{node.attrib['y1']}" == tip for node in held), tip
        assert any(tip in node.attrib["points"].split() for node in wedge), tip


def run(app, window, work, record, case):
    from advanced_workflows import click, export_formats, modal

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
    if case == "bcg":
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
            notice = dialog.fixed_effect_notice.text()
            assert notice.startswith("Fixed-effect model: the required information size ignores heterogeneity.")
            assert "With random effects, D² = " in notice
            record("tsa-peto-fixed-effect-notice", dialog, notice=notice, dpi_scale=dialog.devicePixelRatio())
            dialog.run_button.click()
            assert dialog.result() == dialog.DialogCode.Accepted, dialog.status.text()

        modal(app, TrialSequentialAnalysisDialog, run_default, action.trigger)
        default_view, = [widget for widget in app.topLevelWidgets()
                         if isinstance(widget, ResultsWindow) and widget.isVisible()]
        methods = default_view.manuscript.methods
        assert "fixed-effect (Peto) model" in methods
        record("tsa-default-run", default_view, project_dirty=window.workspace.is_dirty, methods=methods)
        default_view.close()
        assert not window.workspace.is_dirty, "Default TSA changed the project"
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
                assert source.text().split(" · ")[0] == "Entered" and button.isVisible()
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
                if case == "md":
                    wait(300)
                    assert dialog.run_button.isEnabled(), dialog.status.text()
                    record("tsa-md-calculated-preview", dialog, status=dialog.status.text())
            else:
                assert "fixed (MH)" in dialog.base_request.model_label
            dialog.manual.setChecked(True)
            dialog.manual_ris.setText("1000" if case == "rr-mh" else "10000")
            wait(300)
        assert dialog.run_button.isEnabled(), dialog.status.text()
        assert dialog.alpha.text() == "5.0%" and dialog.power.text() == "80.0%"
        samples = []
        if case in ("bcg", "hr"):
            for _ in range(7):
                start = perf_counter()
                dialog._preview()
                samples.append(round((perf_counter() - start) * 1000, 2))
        start = perf_counter()
        dialog._schedule_preview()
        wait(300)
        assert dialog.run_button.isEnabled() and "\n" not in dialog.status.text(), dialog.status.text()
        while "\n" not in dialog.status.text() and perf_counter() - start < 20:
            wait(30)
        assert "\nCrosses " in dialog.status.text(), dialog.status.text()
        elapsed = round((perf_counter() - start) * 1000, 2)
        record("tsa-configured", dialog, input=str(path), status=dialog.status.text(), dpi_scale=dialog.devicePixelRatio())
        if samples:
            record("tsa-preview-timings", dialog, case=case, milliseconds=samples,
                   median_ms=median(samples), conclusion_elapsed_ms=elapsed, dpi_scale=dialog.devicePixelRatio())
        dialog.run_button.click()
        assert dialog.result() == dialog.DialogCode.Accepted, dialog.status.text()

    modal(app, TrialSequentialAnalysisDialog, configure, action.trigger)
    view, = [widget for widget in app.topLevelWidgets() if isinstance(widget, ResultsWindow) and widget.isVisible()]
    table = view._report_tables[0]
    if case in ("bcg", "hr"):
        sensitivity = view._report_tables[1]
        assert sensitivity.title == "Sensitivity to the anticipated intervention effect"
        assert "Primary (default)" in sensitivity.rows[0][0]
        assert "Sensitivity analyses repeated the analysis with alternative anticipated intervention effects." in view.manuscript.methods
    else:
        assert len(view._report_tables) == 1
        assert "Sensitivity analyses repeated" not in view.manuscript.methods
    if case == "stress":
        assert len(table.rows) == 36
    else:
        compare_numeric(table, case, record, view)
    if case == "rr-mh":
        assert len(table.rows) == 5 and all(row[1] != "Double zero" for row in table.rows)
        assert table.rows[-1][3] == "100.0" and table.rows[-1][6] == ""
        assert "The fitted model excluded Double zero." in view.manuscript.methods
    if case == "bcg":
        adjusted = table.headers.index("TSA-adjusted CI")
        assert table.rows[0][adjusted] == "—" and table.rows[0][5].startswith("±")
        assert table.quantities[0][adjusted][0].value < .001
        assert "— Too little information for a finite TSA-adjusted interval." in view.manuscript.html()
        assert "Futility boundary" not in table.headers
        assert "We pooled odds ratios (OR)" in view.manuscript.methods
        assert "logarithm with λ = 2 (Hu 2007)" in view.manuscript.methods
    if comparison is not None:
        assert comparison in view.manuscript.results, view.manuscript.results
    assert "Accrued information is" in view.manuscript.results
    assert "Supplementary details" not in view.manuscript.html(supplementary=True)

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
        view.plot_service.export(regenerator=artifact.capability.regenerator, params_path=artifact.params_path,
                                 output_path=str(rendered))
        check_artwork(rendered, case, style, descriptor)
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
               input=str(path), viewport=str(screen_plot),
               plots={artifact.title: str(rendered)})
        if os.environ.get("RCMS_TSA_DESIGN_EXPORTS") == "1":
            export_formats(app, view, work / "design-exports", f"{case}-{style}", record)

    if case == "stress":
        window.workspace.mark_saved()
        return view

    view.report_action.setChecked(True)
    app.processEvents()
    record("tsa-report", view, results=view.manuscript.results)
    report = capture(view, work / "reports")
    # Poppler emits continuations of split HR cells in page order. DOCX,
    # clipboard and CSV still compare every cell in table order.
    assert_exports(view, report, pdf_ordered=case != "hr")
    if case in ("bcg", "hr"):
        caption = "Table 2. Sensitivity to the anticipated intervention effect"
        item, = view.nav_tree.findItems(caption, QtCore.Qt.MatchFlag.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive)
        assert not item.isHidden()
        view.nav_tree.setCurrentItem(item)
        record("tsa-sensitivity-report", view, caption=caption, rows=sensitivity.rows)
    view.tables_action.trigger()
    for index, exported_table in enumerate(view._report_tables):
        view.table_selector.setCurrentIndex(index)
        for action, name, filter_name in (
            (view.export_table_action, "formatted", "CSV table"),
            (view.export_values_action, "values", "CSV values"),
        ):
            export = work / f"{case}-{index + 1}-{name}.csv"
            with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(export), f"{filter_name} (*.csv)")):
                action.trigger()
            with export.open(encoding="utf-8-sig", newline="") as stream:
                if name == "formatted":
                    assert list(csv.reader(stream)) == [list(exported_table.headers), *map(list, exported_table.rows)]
                else:
                    values = list(csv.DictReader(stream))
                    column = "Required information size" if index else "Z"
                    exported = next(row for row in values if row["Column"] == column)
                    exact = exported_table.quantities[0][exported_table.headers.index(column)][0].value
                    assert float(exported["Value"]) == exact
                    if case == "bcg" and index == 0:
                        limit = next(row for row in values if row["Column"] == "TSA-adjusted CI")
                        assert float(limit["Value"]) == table.quantities[0][adjusted][0].value
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
    elif case == "bcg":
        saved = work / "bcg-with-tsa-settings.rcms"
        assert window.save(destination=saved)
        assert not window.workspace.is_dirty
        original_table = view._report_tables[0]
        original_methods = view.manuscript.methods

        def rerun(dialog, change):
            assert dialog.base_request.options.power == (.8 if change == "power" else .9)
            if change == "power":
                dialog.power.setValue(90)
            elif change == "effect":
                dialog.effect.setText("0.7")
            else:
                assert dialog.effect.text() == "0.7"
                assert dialog.default_inputs[dialog.effect][0].text().startswith("Entered · ")
            wait(300)
            assert dialog.run_button.isEnabled(), dialog.status.text()
            if change is None:
                deadline = perf_counter() + 3
                while dialog.conclusion_process.state() != QtCore.QProcess.ProcessState.Running and perf_counter() < deadline:
                    wait(20)
                assert dialog.conclusion_process.state() == QtCore.QProcess.ProcessState.Running
                assert dialog.run_button.isEnabled() and "\n" not in dialog.status.text()
            record("tsa-change-settings-dialog", dialog, power=dialog.power.text(),
                   effect=dialog.effect.text(), status=dialog.status.text(),
                   background_running=dialog.conclusion_process.state() == QtCore.QProcess.ProcessState.Running)
            dialog.run_button.click()
            assert dialog.result() == dialog.DialogCode.Accepted, dialog.status.text()

        modal(app, TrialSequentialAnalysisDialog, lambda dialog: rerun(dialog, "power"), view.change_settings_action.trigger)
        visible, = [widget for widget in app.topLevelWidgets() if isinstance(widget, ResultsWindow) and widget.isVisible()]
        assert visible is view
        assert view._report_tables[0].rows[-1][3] != original_table.rows[-1][3]
        assert "90% power" in view.manuscript.methods and view.manuscript.methods != original_methods
        assert window.workspace.is_dirty
        modal(app, TrialSequentialAnalysisDialog, lambda dialog: rerun(dialog, "effect"), view.change_settings_action.trigger)
        entered_rows = view._report_tables[0].rows
        assert "Primary (entered)" in view._report_tables[1].rows[0][0]
        # Change the live sheet before a rerun. The result must still use the
        # original study snapshot, while a later Save includes the live edit.
        assert window.model.setData(window.model.index(0, window.model.NAME), "Edited in source sheet")
        assert window.save(destination=saved)
        modal(app, TrialSequentialAnalysisDialog, lambda dialog: rerun(dialog, None), view.change_settings_action.trigger)
        assert not window.workspace.is_dirty and view._report_tables[0].rows == entered_rows
        view.report_action.setChecked(True)
        record("tsa-change-settings-result", view, same_window=visible is view, project_dirty=window.workspace.is_dirty,
               before=original_methods, after=view.manuscript.methods)
    else:
        window.workspace.mark_saved()
    return view
