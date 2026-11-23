# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Measure real Results exports with PyMuPDF installed in the verification environment."""

from importlib import import_module
from itertools import combinations
from pathlib import Path
import re
from unittest.mock import patch
from xml.etree import ElementTree as ET

from PyQt6.QtWidgets import QDialogButtonBox, QFileDialog

from rc_metastudio.analysis.setup_dialog import AnalysisSetupDialog
from rc_metastudio.analysis.small_study_effects_dialog import SmallStudyEffectsDialog
from rc_metastudio.analysis.trial_sequential_dialog import TrialSequentialAnalysisDialog
from rc_metastudio.results.funnel_editor import FunnelPlotEditorDialog
from rc_metastudio.results.plot_editor import EditPlotDialog
from rc_metastudio.results.plot_export import PlotExportDialog
from rc_metastudio.results.window import ResultsWindow
from tests.python.gui.qt_test_support import metric_action, required, wait


EXPECTED_LABELS = {
    "regression": {"Absolute latitude", "Risk ratio", "Regression line"},
    "funnel": {"Mean difference", "Standard error (outcome scale)", "No effect"},
    "contour_funnel": {"Mean difference", "Standard error (outcome scale)", "Analysis CI 95%."},
    "trimfill_funnel": {"Odds ratio", "Standard error of log odds ratio", "Observed", "Imputed"},
    "deeks_funnel": {"Deeks effective-sample-size funnel", "Log diagnostic odds ratio"},
    "sroc": {"False positive rate", "Sensitivity", "Confidence region", "Joint prediction region"},
    "trial_sequential": {"Cumulative statistical information", "Cumulative Z-curve", "Conventional boundary"},
}


def pdf_observations(path: Path, width: float, height: float) -> dict:
    pdf = import_module("pymupdf")
    with pdf.open(path) as document:
        assert len(document) == 1
        page = document[0]
        assert abs(page.rect.width - 72 * width) <= .5
        assert abs(page.rect.height - 72 * height) <= .5
        spans = [
            span for block in page.get_text("dict", clip=pdf.INFINITE_RECT())["blocks"]
            for line in block.get("lines", ()) for span in line["spans"] if span["text"].strip()
        ]
        boxes = [(span["text"], pdf.Rect(span["bbox"])) for span in spans]
        page_box = page.rect + (-.5, -.5, .5, .5)
        outside = [label for label, box in boxes if not page_box.contains(box)]
        overlaps = []
        for (first, a), (second, b) in combinations(boxes, 2):
            intersection = a & b
            if intersection.get_area() > .2 * min(a.get_area(), b.get_area()):
                overlaps.append([first, second])
        return {
            "min_font_pt": round(min((span["size"] for span in spans), default=0), 3),
            "labels": [label for label, _ in boxes],
            "outside": outside,
            "overlaps": overlaps,
            "page_pt": [page.rect.width, page.rect.height],
        }


def sroc_observations(path: Path) -> dict:
    svg = ET.parse(path).getroot()
    ns = {"s": "http://www.w3.org/2000/svg"}
    clips = {
        f"url(#{clip.attrib['id']})": clip.find("s:rect", ns)
        for clip in svg.findall(".//s:clipPath", ns)
    }
    circles = clipped = 0
    for group in svg.findall(".//s:g[@clip-path]", ns):
        clip = clips.get(group.attrib["clip-path"])
        if clip is None:
            continue
        left, top, width, height = (float(clip.attrib[key]) for key in ("x", "y", "width", "height"))
        for circle in group.findall("s:circle", ns):
            x, y, radius = (float(circle.attrib[key]) for key in ("cx", "cy", "r"))
            circles += 1
            clipped += not (left <= x - radius and x + radius <= left + width
                            and top <= y - radius and y + radius <= top + height)
    colors = sorted(set(re.findall(r"stroke:\s*(#[0-9a-f]{6})", path.read_text(encoding="utf-8").lower())))
    return {"circles": circles, "clipped_circles": clipped, "stroke_colors": colors}


def run(app, window, work, root, record, analyze):
    from advanced_workflows import modal

    failures = []

    def visible(kind):
        for _ in range(100):
            wait(50)
            matches = [widget for widget in app.topLevelWidgets() if isinstance(widget, kind) and widget.isVisible()]
            if matches:
                dialog, = matches
                return dialog
        raise AssertionError(f"No visible {kind.__name__}")

    def open_sample(name):
        window.workspace.mark_saved()
        action, = [action for action in window.sample_menu.actions() if name in action.text()]
        action.trigger()
        assert window.workspace.path == root / "sample_projects" / action.data()
        record("print-sample", window, sample=action.data(), exports={"sample": str(window.workspace.path)})

    def pick_style(editor, style):
        selector = editor.style_combo if isinstance(editor, FunnelPlotEditorDialog) else editor.style_cbo
        selector.setCurrentIndex(selector.findData("bmj" if style == "custom" else style))
        if style == "custom":
            editor.sroc_prediction_color.setText("#a11159")
        editor.accept()
        assert not editor.isVisible()

    def export(view, kind, style, width, *, blocked=False):
        name = f"{kind}-{style}"
        destination = work / f"{name}-{width:.2f}.pdf"
        dimensions = []

        def configure(dialog):
            dialog.format_control.setCurrentIndex(dialog.format_control.findData("pdf"))
            dialog.units.setCurrentText("in")
            dialog.width_control.setValue(width)
            wait(350)
            dimensions.extend(dialog.dimensions()[:2])
            enabled = dialog.save_button.isEnabled()
            record("print-export-options", dialog, figure=name, dimensions=dimensions, save=enabled,
                   warning=dialog.legibility_warning.text(), error=dialog.raster_limit.text())
            if enabled == blocked:
                failures.append((name, width, "unexpected Save state", enabled))
            if blocked and not enabled:
                assert dialog.raster_limit.isVisible() and "fit at this size" in dialog.raster_limit.text()
            if blocked or not enabled:
                dialog.reject()
            else:
                dialog.save_button.click()

        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(destination), "")) as picker:
            modal(app, PlotExportDialog, configure, view.export_plot_action.trigger)
        if blocked:
            assert not picker.called
        elif picker.called:
            assert destination.is_file(), destination
            observed = pdf_observations(destination, *dimensions)
            record("print-export-pdf", figure=name, width=width, exports={"pdf": str(destination)}, **observed)
            if observed["min_font_pt"] < 6 or observed["outside"] or observed["overlaps"]:
                failures.append((name, width, observed))
            if missing := EXPECTED_LABELS[kind] - set(observed["labels"]):
                failures.append((name, width, "missing labels", sorted(missing)))

    def check_plots(view, kinds):
        for kind in kinds:
            matches = [entry for entry in view._plots.values() if entry.artifact.plot_kind == kind]
            assert len(matches) == 1, (kind, tuple(view.results.images), view.texts)
            entry, = matches
            view.nav_tree.setCurrentItem(entry.navigation_item)
            editor = FunnelPlotEditorDialog if "funnel" in kind else EditPlotDialog
            for style in ("default", "bmj"):
                modal(app, editor, lambda dialog: pick_style(dialog, style), view.edit_plot_action.trigger)
                for width in (2.60, 5.39):
                    export(view, kind, style, width)
            if kind == "sroc":
                export(view, kind, "bmj", .75, blocked=True)
                for style, expected in (("default", {"#2f5597", "#b45f06"}), ("revman", {"#000000"}),
                                        ("bmj", {"#5f4c9a"}), ("custom", {"#5f4c9a", "#a11159"})):
                    modal(app, editor, lambda dialog: pick_style(dialog, style), view.edit_plot_action.trigger)
                    path = Path(entry.artifact.display_path())
                    observed = sroc_observations(path)
                    colors = set(observed["stroke_colors"])
                    record("sroc-marker-and-palette", view, style=style, **observed)
                    if (not observed["circles"] or observed["clipped_circles"] or not expected <= colors
                            or (style != "default" and colors & {"#2f5597", "#b45f06"})):
                        failures.append((style, observed))
        view.close()

    def funnels(kinds):
        def start(dialog):
            dialog.ordinary_funnel_check.setChecked("deeks_funnel" not in kinds)
            dialog.contour_funnel_check.setChecked("contour_funnel" in kinds)
            dialog.trim_fill_check.setChecked("trimfill_funnel" in kinds)
            if dialog.trim_fill_check.isChecked():
                dialog.trim_fill_side_combo.setCurrentText("Left")
            dialog.extrapolation_check.setChecked("trimfill_funnel" in kinds)
            dialog.run()
        modal(app, SmallStudyEffectsDialog, start, window.action_publication_bias.trigger)
        check_plots(visible(ResultsWindow), kinds)

    open_sample("Colditz 1994")
    metric_action(window.menuMetric, "RR").trigger()
    window.action_meta_regression.trigger()
    setup = visible(AnalysisSetupDialog)
    for covariate, checkbox in setup.covs_and_check_boxes:
        checkbox.setChecked(covariate["name"] == "Absolute latitude")
    required(setup.buttonBox.button(QDialogButtonBox.StandardButton.Ok)).click()
    check_plots(visible(ResultsWindow), ("regression",))
    metric_action(window.menuMetric, "OR").trigger()
    funnels(("trimfill_funnel",))

    open_sample("Poole 2003")
    metric_action(window.menuMetric, "MD").trigger()
    funnels(("funnel", "contour_funnel"))

    open_sample("Kearon 1998")
    check_plots(analyze(app, window, "diagnostic.reitsma", diagnostic_metrics=("sens", "spec")), ("sroc",))
    funnels(("deeks_funnel",))

    open_sample("Pignon 2000")

    def start_tsa(dialog):
        dialog.order.setCurrentIndex(dialog.order.findData("table"))
        wait(400)
        assert dialog.run_button.isEnabled(), dialog.status.text()
        dialog.run_button.click()

    modal(app, TrialSequentialAnalysisDialog, start_tsa, window.action_trial_sequential_analysis.trigger)
    check_plots(visible(ResultsWindow), ("trial_sequential",))
    assert not failures, failures
