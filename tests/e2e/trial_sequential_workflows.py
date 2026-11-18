"""Drive TSA setup, results, saved plot styles and exports through Qt and R."""
import csv
import json
import os
import re
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
    labels = {"".join(node.itertext()) for node in svg.iter(NAMESPACE + "text")}
    assert set(contract["labels"]) <= labels, labels
    assert ("Penalised Z-curve" in labels) == (case == "bcg")
    assert any(label.startswith("Required information") and "Accrued:" in label for label in labels)
    if case == "hr":
        assert "Required information: 4,222.1 · Accrued: 1,775.3 (42%)" in labels
    if case == "stress":
        tracks = {}
        for node in svg.iter(NAMESPACE + "text"):
            transform = re.fullmatch(r"translate\(([\d.]+),([\d.]+)\) rotate\(-90\)",
                                     node.attrib.get("transform", ""))
            if transform is None or node.text == "Cumulative Z-score":
                continue
            x, y = map(float, transform.groups())
            size = float(node.attrib["textLength"].removesuffix("px"))
            bounds = (y, y + size) if node.attrib.get("text-anchor") == "end" else (y - size, y)
            tracks.setdefault(x, []).append(bounds)
        assert sum(map(len, tracks.values())) == 4, tracks
        for intervals in tracks.values():
            ordered = sorted(intervals)
            assert all(a[1] < b[0] for a, b in zip(ordered, ordered[1:])), tracks
    assert "100%" in labels and "RIS" in labels
    accent = contract["accents"][style]
    assert accent.lower() in path.read_text(encoding="utf-8").lower()
    _, _, width, height = map(float, svg.attrib["viewBox"].split())
    assert 1.5 < width / height < 2.2
    monitoring = [node for node in svg.iter(NAMESPACE + "polyline")
                  if "#333333" in node.attrib.get("style", "") and "stroke-dasharray" not in node.attrib["style"]]
    assert monitoring and len(monitoring[0].attrib["points"].split()) >= 100
    crossings = [node for node in svg.iter(NAMESPACE + "circle") if "#333333" in node.attrib.get("style", "")]
    if case != "stress":
        assert bool(crossings) == (case != "md")
    if case == "bcg":
        held = [node for node in svg.iter(NAMESPACE + "line")
                if "#333333" in node.attrib.get("style", "") and "stroke-dasharray" in node.attrib["style"]]
        tip = monitoring[0].attrib["points"].split()[-1]
        assert any(f"{node.attrib['x1']},{node.attrib['y1']}" == tip for node in held), tip
        wedge = [node for node in svg.iter(NAMESPACE + "polygon")
                 if accent in node.attrib.get("style", "") and "stroke-dasharray" in node.attrib["style"]]
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

    modal(app, TrialSequentialAnalysisDialog, configure, action.trigger)
    view, = [widget for widget in app.topLevelWidgets() if isinstance(widget, ResultsWindow) and widget.isVisible()]
    table, = view._report_tables
    if case == "stress":
        assert len(table.rows) == 36
    else:
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
