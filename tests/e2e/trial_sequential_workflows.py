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

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from PyQt6 import QtCore, QtGui, QtWidgets

from rc_metastudio.analysis import catalog as analysis_catalog
from rc_metastudio.project import (
    model as analysis_dataset,
    adapter as project_adapter,
    archive as project_format,
)
from rc_metastudio.analysis.setup_dialog import AnalysisSetupDialog
from rc_metastudio.project.study import AnalysisUnit
from rc_metastudio.domain_ids import ArmId, RowId, SheetId
from rc_metastudio.results.plot_editor import EditPlotDialog
from rc_metastudio.results.window import ResultsWindow
from rc_metastudio.analysis.trial_sequential_dialog import TrialSequentialAnalysisDialog
from tests.e2e.report_retention import assert_exports, capture
from tests.python.gui.qt_test_support import key_clicks, wait

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "tests/analysis_regression/baseline"
NAMESPACE = "{http://www.w3.org/2000/svg}"


def capture_sensitivity(view, record, case, report):
    table = view._report_tables[1]
    measure = {"bcg": "OR", "hr": "HR", "md": "MD"}[case]
    assert table.title == "Sensitivity to the anticipated intervention effect"
    assert table.headers == (
        "Scenario", measure, *(("RRR",) if case != "md" else ()),
        "Required information size", "Accrued (% of required)", "Conclusion", "TSA-adjusted CI",
    )
    assert [row[0] for row in table.rows] == (
        ["Primary (entered)", "50% of primary", "150% of primary"] if case == "md" else
        ["Primary (default)", "RRR 10%", "RRR 20%", "RRR 30%"]
    )
    assert "Sensitivity analyses repeated the analysis with alternative anticipated intervention effects." in view.manuscript.methods
    if case == "bcg":
        assert table.rows[0][:3] == ("Primary (default)", "0.68", "30.7%")
        assert "Crosses monitoring boundary favoring BCG vaccine" in table.rows[0]
        assert "1,232,589" in table.rows[1]
    columns = [i for i, header in enumerate(table.headers) if header not in ("Scenario", "Conclusion")]
    document = Document(str(Path(report["directory"]) / "report.docx"))
    for row in document.tables[1].rows[1:]:
        for column in columns:
            cell = row.cells[column]
            if cell.text and cell.text != "—":
                assert cell.paragraphs[0].alignment == WD_ALIGN_PARAGRAPH.RIGHT, cell.text
    item, = view.nav_tree.findItems("Sensitivity", QtCore.Qt.MatchFlag.MatchExactly | QtCore.Qt.MatchFlag.MatchRecursive)
    assert not item.isHidden()
    view.nav_tree.setCurrentItem(item)
    record("tsa-sensitivity-report", view, caption=f"Table 2. {table.title}", headers=table.headers, rows=table.rows)


def input_project(work, case):
    if case in ("bcg", "peto", "hr"):
        return ROOT / "sample_projects" / ("Binary - BCG vaccine and tuberculosis, Colditz 1994.rcms" if case != "hr" else "Time-to-event (HR) - Head and neck cancer, Pignon 2000.rcms")
    binary = case == "rr-mh"
    stress = case == "stress"
    metric = "RR" if binary else "MD" if stress else case.upper()
    labels = ("The new extended therapy programme", "Conventional outpatient management") if stress else (
        "Treatment", "Comparator",
    )
    arms = [analysis_dataset.Arm(ArmId(label), label) for label in labels]
    sheet = analysis_dataset.Sheet(
        SheetId("tsa"), f"TSA {case}", analysis_catalog.BINARY if binary else analysis_catalog.CONTINUOUS,
        "proportions" if binary else ("smd" if case == "smd" else "means"),
        arms,
        settings={"metric": metric, "effect_direction": "below",
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
        raw = tuple([[25 + 2*i, 4.5, 2], [25 + 2*i, 5, 2]] for i in range(36))
    for i, cells in enumerate(raw):
        unit = AnalysisUnit(sheet, cells)
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
    assert ("Penalized Z-curve" in labels) == (case == "bcg")
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
        limit = contract["peto"]["z_limit"]
        assert f"−{limit}" in labels and str(limit) in labels, labels
        units = "percent" if percent else "participants"
        assert ticks[-2] == contract["peto"]["join_tick"][units], ticks
    favours = [node for node in text_nodes if (node.text or "").startswith("Favors")]
    if case == "hr":
        assert not favours, labels
    else:
        assert len(favours) == 2 and all("rotate(-90" in node.attrib.get("transform", "") for node in favours), labels
        if case == "peto":
            assert {node.text for node in favours} == {"Favors BCG vaccine", "Favors Unvaccinated control"}
    assert contract["accents"][style].lower() in path.read_text(encoding="utf-8").lower()
    if case == "bcg" and style == "default":
        fills = [node.attrib.get("style", "") for node in svg.iter(NAMESPACE + "polygon")]
        assert any("fill: #DDE6F4;" in fill for fill in fills), fills
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
        setup.method_cbo_box.setCurrentIndex(setup.method_cbo_box.findData("binary.fixed.peto"))
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
        assert not window.workspace.is_dirty, "Default TSA changed the project"
        if case == "bcg":
            default_view.close()
            assert window.open(str(path), raise_on_error=True)
            window.model.current_sheet.settings["effect_direction"] = "below"

    if case == "md":
        def run_calculated(dialog):
            key_clicks(dialog.effect, "-1")
            wait(300)
            assert dialog.run_button.isEnabled(), dialog.status.text()
            dialog.run_button.click()
            assert dialog.result() == dialog.DialogCode.Accepted, dialog.status.text()

        modal(app, TrialSequentialAnalysisDialog, run_calculated, action.trigger)
        calculated, = [widget for widget in app.topLevelWidgets()
                       if isinstance(widget, ResultsWindow) and widget.isVisible()]
        calculated.report_action.setChecked(True)
        app.processEvents()
        report = capture(calculated, work / "calculated-reports")
        assert_exports(calculated, report)
        capture_sensitivity(calculated, record, case, report)
        calculated.close()
        window.workspace.mark_saved()
        assert window.open(str(path), raise_on_error=True)

    comparison = {
        "bcg": f"crossed the monitoring boundary favoring {window.model.arm_names[0]}",
        "rr-mh": "crossed the futility boundary",
        "md": "crossed neither a monitoring nor a futility boundary",
        "hr": "crossed the monitoring boundary below the null",
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
            labels = tuple(dialog.test.itemText(i) for i in (1, 2))
            assert labels == tuple(f"One-sided (favoring {arm})" for arm in window.model.arm_names), labels
            dialog.test.showPopup()
            app.processEvents()
            record("tsa-dialog-named-arms", dialog, dialog.test.view(), input=str(path), choices=labels)
            dialog.test.hidePopup()
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
        editors = (dialog.alpha, dialog.effect, dialog.heterogeneity, dialog.order, dialog.test, dialog.spending)
        editor_x = [editor.mapTo(dialog, QtCore.QPoint()).x() for editor in editors]
        assert len(set(editor_x)) == 1, editor_x
        inflation = dialog.heterogeneity_value.text()
        if " (size ×" in inflation:
            percent, factor = inflation.partition(" (size ×")[::2]
            percent = percent.split(" = ")[1]
            assert len(percent.partition(".")[2]) == 2, percent
            assert factor == f"{100 / (100 - float(percent.rstrip('%'))):.1f})", inflation
        samples = []
        if case in ("bcg", "hr"):
            for _ in range(7):
                start = perf_counter()
                dialog._preview()
                samples.append(round((perf_counter() - start) * 1000, 2))
        start = perf_counter()
        dialog.power.setValue(81)
        assert dialog.conclusion.text() == ""
        dialog.power.setValue(80)
        wait(300)
        pending = "Checking boundary crossings…"
        assert dialog.run_button.isEnabled() and dialog.conclusion.text() == pending, dialog.conclusion.text()
        if samples:
            record("tsa-preview-pending", dialog, status=dialog.status.text(), conclusion=pending)
        while dialog.conclusion.text() == pending and perf_counter() - start < 20:
            wait(30)
        conclusion = dialog.conclusion.text()
        assert conclusion.startswith("Crosses "), conclusion
        elapsed = round((perf_counter() - start) * 1000, 2)
        record("tsa-configured", dialog, input=str(path), status=dialog.status.text(), conclusion=conclusion,
               editor_x=editor_x, inflation=inflation, dpi_scale=dialog.devicePixelRatio())
        if samples:
            record("tsa-preview-timings", dialog, case=case, milliseconds=samples,
                   median_ms=median(samples), conclusion_elapsed_ms=elapsed, dpi_scale=dialog.devicePixelRatio())
        dialog.run_button.click()
        assert dialog.result() == dialog.DialogCode.Accepted, dialog.status.text()

    if case != "peto":
        modal(app, TrialSequentialAnalysisDialog, configure, action.trigger)
    view, = [widget for widget in app.topLevelWidgets() if isinstance(widget, ResultsWindow) and widget.isVisible()]
    table = view._report_tables[0]
    if case == "peto":
        assert len(view._report_tables) == 2
        sensitivity = view._report_tables[1]
        assert sensitivity.title == "Sensitivity to the anticipated intervention effect"
        assert sensitivity.rows[0][0] == "Primary (default)"
        assert "Sensitivity analyses repeated" in view.manuscript.methods
    elif case not in ("bcg", "hr"):
        assert len(view._report_tables) == 1
        assert "Sensitivity analyses repeated" not in view.manuscript.methods
    if case == "stress":
        assert len(table.rows) == 36
    elif case != "peto":
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
        assert "odds ratios (OR) were pooled" in view.manuscript.methods
        assert "logarithm with λ = 2" in view.manuscript.methods
    if comparison is not None:
        assert comparison in view.manuscript.results, view.manuscript.results
    assert "Accrued information reached" in view.manuscript.results
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
            from rc_metastudio.results.plot_export import PlotExportDialog

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
    if case == "bcg":
        assert comparison is not None
        for surface in ("copy", "pdf", "docx"):
            rendered = (Path(report["directory"]) / f"{surface}.txt").read_text(encoding="utf-8")
            assert comparison in " ".join(rendered.split()), rendered
    # Poppler emits continuations of split HR cells in page order. DOCX,
    # clipboard and CSV still compare every cell in table order.
    assert_exports(view, report, pdf_ordered=case != "hr")
    if case in ("bcg", "hr"):
        capture_sensitivity(view, record, case, report)
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
                dialog.conclusion_timer.stop()
                dialog._start_conclusion()
                assert dialog._cancel_worker_conclusion is not None
                assert dialog.run_button.isEnabled() and dialog.conclusion.text() == "Checking boundary crossings…"
            record("tsa-change-settings-dialog", dialog, power=dialog.power.text(),
                   effect=dialog.effect.text(), status=dialog.status.text(),
                   background_running=dialog._cancel_worker_conclusion is not None)
            dialog.run_button.click()
            assert dialog.result() == dialog.DialogCode.Accepted, dialog.status.text()

        modal(app, TrialSequentialAnalysisDialog, lambda dialog: rerun(dialog, "power"), view.change_settings_action.trigger)
        visible, = [widget for widget in app.topLevelWidgets() if isinstance(widget, ResultsWindow) and widget.isVisible()]
        assert visible is view
        assert view._report_tables[0].rows[-1][3] != original_table.rows[-1][3]
        assert "90% power" in view.manuscript.methods and view.manuscript.methods != original_methods
        clipboard = app.clipboard()
        assert clipboard is not None
        for section in ("methods", "results"):
            action = next(action for action in view.edit_menu.actions()
                          if action.text() == "Copy " + section + " section")
            clipboard.clear()
            action.trigger()
            expected = getattr(view.manuscript, section)
            assert clipboard.text() == expected, (section, clipboard.text(), expected)
        record("tsa-copy-updated-report", view, methods=view.manuscript.methods, results=view.manuscript.results)
        assert window.workspace.is_dirty
        modal(app, TrialSequentialAnalysisDialog, lambda dialog: rerun(dialog, "effect"), view.change_settings_action.trigger)
        entered_rows = view._report_tables[0].rows
        assert "Primary (entered)" in view._report_tables[1].rows[0][0]
        # Change the live sheet before a rerun. The result must still use the
        # original study snapshot, while a later Save includes the live edit.
        assert window.model.setData(window.model.index(0, window.model.NAME), "Edited in source sheet")
        assert window.save(destination=saved)
        started = perf_counter()
        modal(app, TrialSequentialAnalysisDialog, lambda dialog: rerun(dialog, None), view.change_settings_action.trigger)
        elapsed = perf_counter() - started
        assert elapsed < 30, elapsed
        assert not window.workspace.is_dirty and view._report_tables[0].rows == entered_rows
        record("tsa-worker-conclusion-reused", view, elapsed=elapsed, results_preserved=True)
        view.report_action.setChecked(True)
        record("tsa-change-settings-result", view, same_window=visible is view, project_dirty=window.workspace.is_dirty,
               before=original_methods, after=view.manuscript.methods)
    else:
        window.workspace.mark_saved()
    return view
