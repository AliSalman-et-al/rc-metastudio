# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Measure real Results exports: PDF text sizes, bounds and overlaps, and SROC markers."""

from itertools import combinations
import math
from pathlib import Path
import re
import subprocess
from unittest.mock import patch
from xml.etree import ElementTree as ET

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTContainer, LTCurve, LTLine, LTRect
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QDialogButtonBox, QFileDialog
from scripts.verification_evidence import desktop_tool_executable

from rc_metastudio.analysis.setup_dialog import AnalysisSetupDialog
from rc_metastudio.analysis.small_study_effects_dialog import SmallStudyEffectsDialog
from rc_metastudio.analysis.trial_sequential_dialog import TrialSequentialAnalysisDialog
from rc_metastudio.project.archive import load_project, save_project
from rc_metastudio.results.funnel_editor import FunnelPlotEditorDialog
from rc_metastudio.results.plot_editor import EditPlotDialog
from rc_metastudio.results.plot_export import PlotExportDialog
from rc_metastudio.results.window import ResultsWindow
from tests.python.gui.qt_test_support import metric_action, required, wait


EXPECTED_LABELS = {
    "forest": {"Study", "Risk ratio"},
    "regression": {"Absolute latitude", "Risk ratio", "Regression line", "95% CI"},
    "funnel": {"Mean difference", "Standard error (outcome scale)", "No effect"},
    "contour_funnel": {"Mean difference", "Standard error (outcome scale)", "No effect", "Common-effect estimate"},
    "trimfill_funnel": {"Odds ratio", "Standard error of log odds ratio", "Observed", "Imputed"},
    "deeks_funnel": {"Deeks effective-sample-size funnel", "Log diagnostic odds ratio"},
    "sroc": {"False positive rate", "Sensitivity", "Confidence region", "Joint prediction region"},
    "trial_sequential": {"Cumulative statistical information", "Cumulative Z-curve", "Conventional boundary"},
}


def editorial_observations(kind, runs, page):
    numbers = [(text, size, box) for text, size, box in runs
               if re.fullmatch(r"[−-]?\d+(?:,\d{3})*(?:\.\d+)?", text)]
    observed = {}
    if kind == "forest":
        observed["top_gap_mm"] = round((page.height - max(box[3] for _, _, box in runs)) * 25.4 / 72, 2)
        observed["prediction_interval"] = next((text for text, _, _ in runs
                                                if "prediction interval" in text.lower()), "")
    axis_titles = {
        "regression": {"Absolute latitude", "Risk ratio"},
        "trial_sequential": {"Cumulative statistical information", "Cumulative Z-score"},
        "contour_funnel": {"Mean difference", "Standard error (outcome scale)"},
        "sroc": {"False positive rate", "Sensitivity"},
    }.get(kind, set())
    titles = [(size, box) for text, size, box in runs if text in axis_titles]
    if titles and numbers:
        sizes = [size for size, _ in titles]
        tick_size = max(size for _, size, _ in numbers)
        observed["axis_title_pt"] = [round(size, 2) for size in sizes]
        observed["tick_pt"] = round(tick_size, 2)
        observed["axis_font_ratio"] = round(max(sizes) / min(sizes), 2)
        observed["axis_to_tick_ratio"] = [round(size / tick_size, 2) for size in sizes]
    rectangles = [item for item in page if isinstance(item, LTRect)
                  and page.width * .25 < item.width < page.width - 2 and item.height > page.height * .25]
    frame = max(rectangles, key=lambda item: item.width * item.height).bbox if rectangles else None
    if kind == "trial_sequential":
        vertical = [item for item in page if isinstance(item, LTLine) and item.width < .1 and item.height > 10]
        horizontal = [item for item in page if isinstance(item, LTLine) and item.width > page.width * .3]
        if vertical and horizontal:
            left = min(vertical, key=lambda item: item.x0)
            right = max((item.x1 for item in horizontal if abs(item.x0 - left.x0) < 1), default=left.x0)
            frame = (left.x0, left.y0, right, left.y1)
            observed["panel_height_mm"] = round(left.height * 25.4 / 72, 2)
            y_title = next(((box[1] + box[3]) / 2 for text, _, box in runs
                            if text == "Cumulative Z-score"), None)
            if y_title is not None:
                observed["y_title_center_offset_pt"] = round(abs(y_title - (left.y0 + left.y1) / 2), 2)
                title_right = next(box[2] for text, _, box in runs if text == "Cumulative Z-score")
                observed["y_title_axis_gap_pt"] = round(left.x0 - title_right, 2)
    legend_entries = {
        "sroc": {"Confidence region", "Joint prediction region"},
        "trial_sequential": {"Cumulative Z-curve", "Monitoring boundary", "Futility region", "Conventional boundary"},
    }.get(kind, set())
    legend = [box for text, _, box in runs if text in legend_entries
              or (kind == "contour_funnel" and (" < P " in text or text.startswith(("P > ", "P ≤ "))))]
    if kind == "trial_sequential" and titles:
        legend_fonts = [size for text, size, _ in runs if text in legend_entries]
        if legend_fonts:
            observed["axis_to_legend_ratio"] = round(max(size for size, _ in titles) / min(legend_fonts), 2)
    if frame and legend:
        bounds = (min(box[0] for box in legend), min(box[1] for box in legend),
                  max(box[2] for box in legend), max(box[3] for box in legend))
        observed["legend_clearance_pt"] = round(min(
            max(bounds[0] - box[2], box[0] - bounds[2], bounds[1] - box[3], box[1] - bounds[3])
            for box in [frame, *(box for _, box in titles)]
        ), 2)
        observed["panel_aspect"] = round((frame[2] - frame[0]) / (frame[3] - frame[1]), 2)
    if kind == "contour_funnel":
        ticks = [float(text.replace(",", "")) for text, _, box in numbers
                 if frame and box[2] < frame[0] and box[3] >= frame[1]]
        observed["standard_error_ticks"] = sorted(ticks)
        observed["analysis_ci_note"] = any(text.startswith("Analysis CI") for text, _, _ in runs)
    if kind == "sroc":
        observed["vertical_numeric_labels"] = [text for text, size, box in numbers
                                               if box[3] - box[1] > max(box[2] - box[0], 1.05 * size)]
    return observed


def editorial_failures(kind, style, observed):
    failures = []
    if kind == "forest":
        if style != "revman" and observed["top_gap_mm"] > 4:
            failures.append("blank band above forest headers")
        if not re.search(r"\([^()]+ to [^()]+\)|\[[^\[\]]+, [^\[\]]+\]", observed["prediction_interval"]):
            failures.append("prediction interval is split")
    if kind in {"regression", "contour_funnel", "trial_sequential", "sroc"}:
        ratios = observed.get("axis_to_tick_ratio", [])
        if len(ratios) != 2 or observed["axis_font_ratio"] > 1.1 or not all(1 <= ratio <= 1.25 for ratio in ratios):
            failures.append("inconsistent axis title and tick hierarchy")
    if kind in {"contour_funnel", "trial_sequential", "sroc"} and observed.get("legend_clearance_pt", -1) <= 0:
        failures.append("legend intersects plot frame or title")
    if kind == "contour_funnel":
        ticks = observed["standard_error_ticks"]
        if len(ticks) < 2 or not all(math.isclose(tick * 10, round(tick * 10), abs_tol=1e-7) for tick in ticks):
            failures.append("standard error ticks are not round")
        if observed["analysis_ci_note"]:
            failures.append("unexplained analysis CI note")
    if kind == "trial_sequential":
        if (observed.get("panel_height_mm", 0) < 12 or observed.get("y_title_center_offset_pt", 10) > 1
                or not 0 < observed.get("y_title_axis_gap_pt", 0) <= 30):
            failures.append("TSA plot frame is squeezed or y title is detached")
        if not 1 <= observed.get("axis_to_legend_ratio", 0) <= 1.25:
            failures.append("inconsistent TSA axis and legend hierarchy")
    if kind == "sroc":
        if observed["vertical_numeric_labels"]:
            failures.append("rotated SROC tick labels")
    return failures


def _glyphs(container):
    for item in container:
        if isinstance(item, LTChar):
            yield item
        elif isinstance(item, LTContainer):
            yield from _glyphs(item)


def pdf_text_runs(page) -> list[tuple[str, float, tuple[float, float, float, float]]]:
    """Rebuild each label as (text, smallest point size, bounds) from glyph geometry.

    Cairo writes glyphs grouped by font subset rather than in reading order, so a label
    is every glyph sharing a direction, baseline and size, split at word-sized gaps.
    """
    lines: dict[tuple, list] = {}
    for char in _glyphs(page):
        a, b, _, _, x, y = char.matrix
        size = math.hypot(a, b)
        horizontal = abs(a) >= abs(b)
        sign = 1 if (a if horizontal else b) > 0 else -1
        low, high = (char.x0, char.x1) if horizontal else (char.y0, char.y1)
        start, end = (low, high) if sign > 0 else (-high, -low)
        key = (horizontal, sign, round(y if horizontal else x, 1), round(size, 1))
        lines.setdefault(key, []).append((start, end, char, size))
    runs = []
    for glyphs in lines.values():
        glyphs.sort(key=lambda glyph: glyph[0])
        groups, last_end = [[]], None
        for start, end, char, size in glyphs:
            if last_end is not None and start - last_end > .45 * size:
                groups.append([])
            groups[-1].append((char, size))
            last_end = end
        for group in groups:
            if text := "".join(char.get_text() for char, _ in group).strip():
                runs.append((text, min(size for char, size in group if char.get_text().strip()), (
                    min(char.x0 for char, _ in group), min(char.y0 for char, _ in group),
                    max(char.x1 for char, _ in group), max(char.y1 for char, _ in group))))
    return runs


def luminance(rgb):
    return sum(weight * (value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4)
               for weight, value in zip((.2126, .7152, .0722), rgb))


def publication_observations(kind, page, runs, png):
    labels = {text: box for text, _, box in runs}
    shapes = [item for item in page if isinstance(item, LTCurve)]

    def key(label, shape_type):
        x0, y0, _, y1 = labels[label]
        nearby = (item for item in shapes if isinstance(item, shape_type)
                  and 0 <= x0 - item.x1 < 2 * (y1 - y0) and y0 <= (item.y0 + item.y1) / 2 <= y1)
        return max(nearby, key=lambda item: item.x1, default=None)

    def key_gaps(keys):
        image = QImage(str(png))
        scale = 300 / 72
        gaps = []
        for item in keys:
            if item is None:
                continue
            y = round((page.height - item.y0) * scale)
            ink = [image.pixelColor(x, y).lightness() < 245
                   for x in range(math.ceil(item.x0 * scale), math.floor(item.x1 * scale))]
            painted = [index for index, value in enumerate(ink) if value]
            if painted:
                gaps.append(ink[painted[0]:painted[-1] + 1].count(False))
        return gaps

    if kind == "regression":
        keys = [key(label, LTLine) for label in ("Regression line", "95% CI") if label in labels]
        return {"line_dashes": [None if item is None else list(item.dashing_style[0]) if item.dashing_style else []
                                for item in keys], "white_key_pixels": key_gaps(keys)}
    if kind == "contour_funnel":
        bands = ("P > 0.10", "0.05 < P ≤ 0.10", "0.01 < P ≤ 0.05", "P ≤ 0.01")
        keys = [key(label, LTRect) for label in bands if label in labels]
        fills = [item.non_stroking_color for item in keys if item and item.fill]
        panel_fills = {item.non_stroking_color for item in shapes if item.fill and item.height > 10}
        image = QImage(str(png))
        scale = 300 / 72
        pixels = [image.pixelColor(round((item.x0 + item.x1) / 2 * scale),
                                   round((page.height - (item.y0 + item.y1) / 2) * scale)).getRgbF()[:3]
                  for item in keys if item and item.fill]
        guides = [key(label, LTLine) for label in ("No effect", "Common-effect estimate") if label in labels]
        frame = max((item for item in shapes if isinstance(item, LTRect) and item.fill
                     and .25 * page.width < item.width < page.width - 2 and item.height > .25 * page.height),
                    key=lambda item: item.width * item.height)
        grids = [item.y0 for item in shapes if isinstance(item, LTLine) and item.height < .05
                 and abs(item.x0 - frame.x0) < .25 and abs(item.x1 - frame.x1) < .25
                 and frame.y0 + .25 < item.y0 < frame.y1 - .25]
        tick_lines = [item.y0 for item in shapes if isinstance(item, LTLine)
                      and item.height < .05 and 0 < item.width < 3 and abs(item.x1 - frame.x0) < .25]
        return {"band_luminance": [round(luminance(color), 4) for color in pixels],
                "bands_match_panel": all(color in panel_fills for color in fills),
                "guide_dashed": [bool(item.dashing_style and item.dashing_style[0]) for item in guides if item],
                "gridline_count": len(grids),
                "off_tick_gridlines": [y for y in grids if not any(abs(y - tick) <= .25 for tick in tick_lines)],
                "band_key_gaps_pt": [round(labels[label][0] - item.x1, 2)
                                     for label, item in zip(bands, keys) if item],
                "white_key_pixels": key_gaps(guides)}
    if kind == "forest":
        title_y = min((box[1] for text, _, box in runs if text == "Risk ratio"), default=0)
        starts = sorted((box[0], box, text, size) for text, size, box in runs if text.startswith("Favours"))
        directions = []
        for _, box, text, size in starts:
            readings = [text]
            for edge in (0, 2):
                lines = sorted(((other[1], line) for line, _, other in runs
                                if other[1] < box[1] and abs(box[edge] - other[edge]) < .5), reverse=True)
                y, joined = box[1], text
                for next_y, line in lines:
                    if y - next_y >= 1.8 * size:
                        break
                    y, joined = next_y, f"{joined} {line}"
                    readings.append(joined)
            directions.append(readings)
        null = next(((box[0] + box[2]) / 2 for text, _, box in runs if text == "1" and box[1] > title_y), None)
        centers = [(box[0] + box[2]) / 2 for _, box, _, _ in starts]
        return {"directions": directions, "directions_below_axis": all(box[3] <= title_y for _, box, _, _ in starts),
                "direction_centers_pt": centers, "null_tick_pt": null,
                "direction_span_pt": [value for first, box, _, _ in starts for value in (first, box[2])]}
    if kind == "trial_sequential":
        image = QImage(str(png))
        scale = 300 / 72
        contrast = {}
        for label, (x0, y0, x1, y1) in labels.items():
            if not re.fullmatch(r"[+−-]?1\.96", label):
                continue
            pixels = [image.pixelColor(x, y).getRgbF()[:3]
                      for x in range(math.ceil(x0 * scale), math.floor(x1 * scale))
                      for y in range(max(0, math.ceil((page.height - y1) * scale)),
                                     min(image.height(), math.floor((page.height - y0) * scale)))]
            if pixels:
                dark, light = min(map(luminance, pixels)), max(map(luminance, pixels))
                contrast[label] = round((light + .05) / (dark + .05), 2)
        tick_boxes = [box for label, _, box in runs if re.fullmatch(r"[−-]?\d+(?:,\d{3})*", label)]
        fonts = sorted({char.fontname.split("+")[-1] for char in _glyphs(page)
                        if any(box[0] <= char.x0 and char.x1 <= box[2] and box[1] <= char.y0 and char.y1 <= box[3]
                               for box in tick_boxes)})
        return {"conventional_contrast": contrast, "tick_fonts": fonts}
    return {}


def pdf_observations(path: Path, width: float, height: float, kind: str = "") -> dict:
    pages = list(extract_pages(path, laparams=None))
    assert len(pages) == 1
    page, = pages
    assert abs(page.width - 72 * width) <= .5
    assert abs(page.height - 72 * height) <= .5
    runs = pdf_text_runs(page)
    outside = [text for text, _, (x0, y0, x1, y1) in runs
               if x0 < -.5 or y0 < -.5 or x1 > page.width + .5 or y1 > page.height + .5]

    def area(box):
        return (box[2] - box[0]) * (box[3] - box[1])

    overlaps = []
    for (first, _, a), (second, _, b) in combinations(runs, 2):
        intersection = (max(0, min(a[2], b[2]) - max(a[0], b[0]))
                        * max(0, min(a[3], b[3]) - max(a[1], b[1])))
        if intersection > .2 * min(area(a), area(b)):
            overlaps.append([first, second])
    return {
        "min_font_pt": round(min((size for _, size, _ in runs), default=0), 3),
        "labels": [text for text, _, _ in runs],
        "outside": outside,
        "overlaps": overlaps,
        "page_pt": [page.width, page.height],
        "editorial": editorial_observations(kind, runs, page),
        "publication": publication_observations(kind, page, runs, path.with_suffix(".png")),
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

    failures: list[tuple[object, ...]] = []
    default_sizes: dict[tuple[str, str], list[float]] = {}
    directions = []

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
        if isinstance(editor, EditPlotDialog) and editor.show_weight.isVisible():
            editor.show_weight.setChecked(False)
            editor.show_raw_counts.setChecked(False)
        editor.accept()
        assert not editor.isVisible()

    def export(view, kind, style, width, *, blocked=False, prefix=""):
        name = f"{prefix}{kind}-{style}"
        size_name = "proposed" if width is None else f"{width}mm"
        destination = work / f"{name}-{size_name}.pdf"
        dimensions = []

        def configure(dialog):
            dialog.format_control.setCurrentIndex(dialog.format_control.findData("pdf"))
            dialog.units.setCurrentText("mm")
            if width is not None:
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
            png = destination.with_suffix(".png")
            subprocess.run([desktop_tool_executable("pdftoppm"), "-r", "300", "-singlefile",
                            "-png", str(destination), str(png.with_suffix(""))], check=True, capture_output=True)
            assert png.is_file()
            observed = pdf_observations(destination, *dimensions, kind)
            record("print-export-pdf", figure=name, width=width,
                   exports={"pdf": str(destination), "png": str(png)}, **observed)
            if observed["min_font_pt"] < 6 or observed["outside"] or observed["overlaps"]:
                failures.append((name, width, observed))
            if missing := EXPECTED_LABELS[kind] - set(observed["labels"]):
                failures.append((name, width, "missing labels", sorted(missing)))
            if defects := editorial_failures(kind, style, observed["editorial"]):
                failures.append((name, width, defects, observed["editorial"]))
            publication = observed["publication"]
            valid = True
            if kind == "regression":
                dashes = publication["line_dashes"]
                gaps = publication["white_key_pixels"]
                valid = len(dashes) == 2 and dashes[0] == [] and bool(dashes[1]) and len(gaps) == 2 and gaps[1] > gaps[0] + 3
            elif kind == "contour_funnel":
                bands = publication["band_luminance"]
                gaps = publication["white_key_pixels"]
                valid = (len(bands) == 4 and all(a > b for a, b in zip(bands, bands[1:]))
                         and len(gaps) == 2 and gaps[0] == 0 and gaps[1] > 3
                         and not publication["off_tick_gridlines"]
                         and len(publication["band_key_gaps_pt"]) == 4
                         and max(publication["band_key_gaps_pt"]) <= 6
                         and publication["bands_match_panel"] and publication["guide_dashed"] == [False, True])
            elif kind == "forest":
                labels = publication["directions"]
                valid = (len(labels) == len(directions) and publication["directions_below_axis"]
                         and all(expected in found for expected, found in zip(directions, labels)))
                if valid and len(directions) == 2:
                    left, right = publication["direction_centers_pt"]
                    null = publication["null_tick_pt"]
                    if width == 66:
                        left, _, _, right = publication["direction_span_pt"]
                    valid = null is not None and left < null < right
            elif kind == "trial_sequential":
                contrast = publication["conventional_contrast"]
                fonts = publication["tick_fonts"]
                valid = len(contrast) == 2 and min(contrast.values()) >= 4.5 and len(fonts) == 1 and "Bold" not in fonts[0]
            if not valid:
                failures.append((name, width, publication))
            if width is None and "tick_pt" in observed["editorial"]:
                editorial = observed["editorial"]
                default_sizes[style, kind] = [editorial["tick_pt"], *editorial["axis_title_pt"]]

    def check_plots(view, kinds):
        for kind in kinds:
            matches = [entry for entry in view._plots.values() if entry.artifact.plot_kind == kind]
            assert len(matches) == 1, (kind, tuple(view.results.images), view.texts)
            entry, = matches
            view.nav_tree.setCurrentItem(entry.navigation_item)
            editor = FunnelPlotEditorDialog if "funnel" in kind else EditPlotDialog
            styles = ("default", "revman", "bmj") if kind in {
                "forest", "regression", "contour_funnel", "trial_sequential"
            } else ("default", "bmj")
            for style in styles:
                modal(app, editor, lambda dialog: pick_style(dialog, style), view.edit_plot_action.trigger)
                for width in (66, 137, None):
                    export(view, kind, style, width)
            if kind == "forest":
                def edit_directions(dialog):
                    left = dialog.direction_fields["fp_direction_left"]
                    right = dialog.direction_fields["fp_direction_right"]
                    assert [left.text(), right.text()] == directions
                    left.setText("Favours placebo")
                    right.clear()
                    dialog.accept()
                    assert not dialog.isVisible()
                modal(app, editor, edit_directions, view.edit_plot_action.trigger)
                directions[:] = ["Favours placebo"]
                export(view, kind, "edited", None)
            if kind == "sroc":
                export(view, kind, "bmj", 19, blocked=True)
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
    directions[:] = ["Favours BCG vaccine", "Favours Unvaccinated control"]
    check_plots(analyze(app, window, "binary.random"), ("forest",))
    window.action_meta_regression.trigger()
    setup = visible(AnalysisSetupDialog)
    for covariate, checkbox in setup.covs_and_check_boxes:
        checkbox.setChecked(covariate["name"] == "Absolute latitude")
    required(setup.buttonBox.button(QDialogButtonBox.StandardButton.Ok)).click()
    check_plots(visible(ResultsWindow), ("regression",))
    metric_action(window.menuMetric, "OR").trigger()
    funnels(("trimfill_funnel",))

    source, = (root / "sample_projects").glob("*Colditz*.rcms")
    project = load_project(source)
    sheets = project.project["sheets"]
    assert isinstance(sheets, list)
    sheet, = sheets
    assert isinstance(sheet, dict)
    sheet["name"] = "Free of tuberculosis"
    settings, rows = sheet["settings"], sheet["rows"]
    assert isinstance(settings, dict) and isinstance(rows, list)
    settings["effect_direction"] = "above"
    for row in rows:
        assert isinstance(row, dict)
        arms = row["raw_data"]
        assert isinstance(arms, dict)
        for arm, counts in arms.items():
            assert isinstance(counts, list)
            events, total = counts
            assert isinstance(events, int) and isinstance(total, int)
            arms[arm] = [total - events, total]
    beneficial = work / "colditz-tuberculosis-free.rcms"
    save_project(beneficial, project.project, project.state)
    window.workspace.mark_saved()
    assert window.open(str(beneficial), raise_on_error=True)
    record("print-beneficial-outcome", window, exports={"project": str(beneficial)})
    metric_action(window.menuMetric, "RR").trigger()
    directions[:] = ["Favours Unvaccinated control", "Favours BCG vaccine"]
    result = analyze(app, window, "binary.random")
    entry, = [entry for entry in result._plots.values() if entry.artifact.plot_kind == "forest"]
    result.nav_tree.setCurrentItem(entry.navigation_item)
    for style in ("default", "revman", "bmj"):
        modal(app, EditPlotDialog, lambda dialog: pick_style(dialog, style), result.edit_plot_action.trigger)
        export(result, "forest", style, None, prefix="beneficial-")
    result.close()

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
    for style in ("default", "bmj"):
        typography = {kind: default_sizes.get((style, kind))
                      for kind in ("regression", "contour_funnel", "sroc", "trial_sequential")}
        record("proposed-export-typography", style=style, axis_and_tick_pt=typography)
        if not all(sizes and all(8.75 <= size <= 9.25 for size in sizes) for sizes in typography.values()):
            failures.append((style, "proposed sizes lack a shared 9 pt axis scale", typography))
    assert not failures, failures
