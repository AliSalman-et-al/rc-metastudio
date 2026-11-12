"""Rendered plot captions, interval caps, row alignment and axis geometry."""

import json
import math
import re
from xml.etree import ElementTree as ET
from tests.python.gui.qt_test_support import required


def check_caption(path, identity):
    """Check the actual figure text, including wrapping, rather than its params."""
    nodes = list(ET.parse(path).iter("{http://www.w3.org/2000/svg}text"))
    text = " ".join("".join(node.itertext()) for node in nodes)
    expected = " ".join(identity.replace("\n", " · ").split())
    assert expected in " ".join(text.split()), (expected, text)
    caption = nodes[-1]
    size = float(required(re.search(r"font-size:\s*([\d.]+)px", caption.attrib["style"]))[1])
    assert size >= 12.9, ("unreadable caption", caption.attrib)


def check_interval_caps(path):
    """Match actual interval caps to horizontal whiskers, independent of style."""
    from statistics import median
    lines = []
    for node in ET.parse(path).iter("{http://www.w3.org/2000/svg}line"):
        lines.append(tuple(float(node.attrib[key]) for key in ("x1", "y1", "x2", "y2")))
    vertical = [line for line in lines if abs(line[0]-line[2]) < .02 and abs(line[1]-line[3]) > .1]
    caps = []
    for x1,y1,x2,y2 in lines:
        if abs(y1-y2) > .02 or abs(x1-x2) < 2:
            continue
        for cap in vertical:
            if min(abs(cap[0]-x1), abs(cap[0]-x2)) < .02 and abs((cap[1]+cap[3])/2-y1) < .02:
                caps.append((y1, abs(cap[1]-cap[3])))
    rows = sorted(set(round(y, 2) for y, _ in caps))
    spacing = [b-a for a,b in zip(rows, rows[1:]) if b-a > 2]
    assert len(spacing) >= 2, ("expected at least three capped interval rows", path, caps)
    row_height = median(spacing)
    assert all(height <= row_height*.45+.03 for _,height in caps), ("CI caps cross row bands", path, row_height, caps)


def check_annotation_spacing(view, *, style="default"):
    assert "Overall-effect null:" not in view.report_text.toPlainText(), view.report_text.toPlainText()
    for path in view.results.display_images.values():
        if style != "bmj":
            check_interval_caps(path)
        nodes = list(ET.parse(path).iter("{http://www.w3.org/2000/svg}text"))
        for weight in (node for node in nodes if re.fullmatch(r"[\d.]+%", "".join(node.itertext()))):
            row = [node for node in nodes if "[" in "".join(node.itertext())
                   and abs(float(node.attrib["y"]) - float(weight.attrib["y"])) < 2]
            if not row:
                continue
            assert len(row) == 1, row
            estimate = row[0]
            def bounds(node):
                x, width = float(node.attrib["x"]), float(node.attrib["textLength"].removesuffix("px"))
                anchor = node.attrib.get("text-anchor", "start")
                return (x-width, x) if anchor == "end" else (x-width/2, x+width/2) if anchor == "middle" else (x, x+width)
            a,b = sorted((bounds(weight), bounds(estimate)))
            assert b[0]-a[1] >= 4, ("weight/estimate gap", b[0]-a[1], weight.attrib, estimate.attrib)
        for estimate in nodes:
            text = "".join(estimate.itertext())
            if not re.fullmatch(r"[+\-\d.eE]+ (?:\[.*\]|\(.* to .*\))", text):
                continue
            row = [node for node in nodes if node is estimate or
                   (re.fullmatch(r"[+\-−\d.][\d.eE+\-−%/() ]*", "".join(node.itertext()))
                    and abs(float(node.attrib.get("y", 0)) - float(estimate.attrib["y"])) < 2)]
            boxes = []
            for node in row:
                x, width = float(node.attrib["x"]), float(node.attrib["textLength"].removesuffix("px"))
                anchor = node.attrib.get("text-anchor", "start")
                boxes.append((x-width, x) if anchor == "end" else (x-width/2, x+width/2) if anchor == "middle" else (x, x+width))
            boxes.sort()
            assert all(b[0]-a[1] >= 4 for a,b in zip(boxes, boxes[1:])), ("raw annotation gap", text, boxes)
        # Include the pooled label and footer, not only numeric annotation cells.
        def text_box(node):
            x, y = float(node.attrib["x"]), float(node.attrib["y"])
            width = float(node.attrib["textLength"].removesuffix("px"))
            height = float(required(re.search(r"font-size: ([\d.]+)px", node.attrib["style"]))[1])
            anchor = node.attrib.get("text-anchor", "start")
            left = x-width if anchor == "end" else x-width/2 if anchor == "middle" else x
            return left, left+width, y-height, y
        for node in nodes:
            text = "".join(node.itertext())
            if not (text.startswith(("Random-effects model", "Fixed-effect model", "(", "Test for overall effect", "Heterogeneity:"))):
                continue
            a = text_box(node)
            for other in nodes:
                if other is node or not re.fullmatch(r"[+\-−\d.][\d.eE+\-−%/() ]*", "".join(other.itertext())):
                    continue
                b = text_box(other)
                if min(a[3], b[3])-max(a[2], b[2]) > 1:
                    assert b[0]-a[1] >= 4 or a[0]-b[1] >= 4, ("model/footer collision", text, "".join(other.itertext()), a, b)
        study_rows = [float(node.attrib['y']) for node in nodes if ''.join(node.itertext()).startswith('Fixture ')]
        if study_rows:
            svg = ET.parse(path)
            paper_width = float(svg.getroot().attrib['viewBox'].split()[2])
            for rule in svg.iter('{http://www.w3.org/2000/svg}polyline'):
                points = [float(value) for value in re.findall(r'[+\-]?[\d.]+', rule.attrib['points'])]
                if len(points) != 4 or abs(points[1]-points[3]) > .01 or abs(points[2]-points[0]) < paper_width/2:
                    continue
                for header in (node for node in nodes if float(node.attrib['y']) < min(study_rows)):
                    box = text_box(header)
                    assert not box[2] < points[1] < box[3], ('rule over header', ''.join(header.itertext()), points, box)
        footers = [node for node in nodes if ''.join(node.itertext()).startswith(('Heterogeneity:', 'Test for overall effect', 'Test for subgroup differences', '95% prediction interval'))]
        for line in ET.parse(path).iter('{http://www.w3.org/2000/svg}line'):
            points = [float(line.attrib[key]) for key in ('x1','y1','x2','y2')]
            if abs(points[0]-points[2]) > .01 or abs(points[1]-points[3]) < 30:
                continue
            for footer in footers:
                box = text_box(footer)
                if box[0] <= points[0] <= box[1]:
                    assert min(points[1],points[3]) >= box[3]+2 or max(points[1],points[3]) <= box[2]-2, ('reference over footer', ''.join(footer.itertext()), points, box)
        captions = ["".join(node.itertext()) for node in nodes]
        assert not any(" · None" in caption for caption in captions), captions
        tests = [caption for caption in captions if caption.startswith("Test for overall effect")]
        comparative = any(caption.casefold().startswith(("odds ratio", "hazard ratio", "incidence rate ratio", "mean difference", "standardized mean difference")) for caption in captions)
        assert tests, captions
        assert all(("H₀:" not in caption) if comparative else ("H₀:" in caption) for caption in tests), tests
        for method in (node for node in nodes if "".join(node.itertext()) in {"IV, Random,", "IV, Fixed,"}):
            box = text_box(method)
            assert box[2] >= 4, ("header outside paper", box)
            for other in nodes:
                if other is method or "".join(other.itertext()) not in {"Sensitivity", "Specificity", "95% CI"}:
                    continue
                other_box = text_box(other)
                assert other_box[2] >= 4, ("header outside paper", other_box)
                if min(box[1], other_box[1]) > max(box[0], other_box[0]):
                    assert box[2]-other_box[3] >= 2 or other_box[2]-box[3] >= 2, ("header leading", "".join(other.itertext()), box, other_box)
        for title in (node for node in nodes if "".join(node.itertext()) in {"Sensitivity", "Specificity"}):
            box = text_box(title)
            for tick in (node for node in nodes if re.fullmatch(r"0\.[\d]+", "".join(node.itertext()))):
                other = text_box(tick)
                if abs(other[3]-box[3]) < 30 and min(box[1], other[1]) > max(box[0], other[0]):
                    assert box[2]-other[3] >= 4 or other[2]-box[3] >= 4, ("axis title/tick gap", box, other)
        assert not any("1.110223" in caption for caption in captions), captions
        if any("Entered effect" in text or "Coefficient" in text for text in captions):
            assert "Mean" not in captions, captions


def check_sequential(view, workflow, record):
    from rc_metastudio import r_bridge

    tables = [t for s in view.results.sections for t in s.tables if t.title == "Model Results"]
    for index, (title, path) in enumerate(view.results.display_images.items()):
        params = view.params_paths[title]
        r_bridge.load_in_r(str(params) + ".plotdata")
        data = json.loads(str(r_bridge.r_iterable_to_list(r_bridge.ro.r('jsonlite::toJSON(list(slab=plot.data$slab, has_overall=plot.data$has_overall, estimates=plot.data$effect_display$y.disp, measure=plot.data$params$measure, range=RCMetaR:::rcmetar.forest.layout.preflight(plot.data)$x$alim), auto_unbox=TRUE, digits=16)'))[0]))
        svg = ET.parse(path)
        nodes = [("".join(node.itertext()), float(node.attrib.get("y", 0)))
                 for node in svg.iter("{http://www.w3.org/2000/svg}text")]
        table = tables[index]
        assert len(table.rows) == len(data["slab"]), (title, table, data)
        assert table.headers[0] == ("Study added (k)" if workflow == "cumulative" else "Study omitted"), table
        for row, name in zip(table.rows, data["slab"], strict=True):
            effect = row[1] if row[1] == "Not estimable" else f"{row[1]} [{row[2]}, {row[3]}]"
            label_y = [y for text, y in nodes if text == name]
            effect_y = [y for text, y in nodes if text == effect]
            assert label_y and any(abs(a-b) < .01 for a in label_y for b in effect_y), (title, name, effect, nodes)
            assert row[0] == name, (title, row, name)
        if workflow == "leave-one-out":
            assert isinstance(data.get("has_overall"), bool), data
            assert (data["slab"][0] == "All studies") == data["has_overall"], data
        ticks = []
        lines = []
        if data["measure"] in {"OR", "RR", "HR", "IRR", "MD", "SMD"} and data["range"][0] <= 0 <= data["range"][1]:
            null = 1 if data["measure"] in {"OR", "RR", "HR", "IRR"} else 0
            ticks = [float(node.attrib["x"]) for node in svg.iter("{http://www.w3.org/2000/svg}text")
                     if node.attrib.get("text-anchor") == "middle" and "".join(node.itertext()).strip() in {str(null), f"{null:.1f}", f"{null:.2f}"}]
            lines = [node.attrib for node in svg.iter("{http://www.w3.org/2000/svg}line")]
            assert ticks and any(abs(float(line["x1"]) - float(line["x2"])) < .01
                                 and abs(float(line["y1"]) - float(line["y2"])) > 50
                                 and any(abs(float(line["x1"]) - tick) < .02 for tick in ticks)
                                 for line in lines), (title, null, ticks, lines)
        if workflow in {"cumulative", "leave-one-out"}:
            row_y = [y for text, y in nodes if text in data["slab"]]
            for line in lines if data["measure"] in {"OR", "RR", "HR", "IRR", "MD", "SMD"} and data["range"][0] <= 0 <= data["range"][1] else []:
                if (abs(float(line["x1"]) - float(line["x2"])) < .01
                    and abs(float(line["y1"]) - float(line["y2"])) > 50
                    and any(abs(float(line["x1"]) - tick) < .02 for tick in ticks)):
                    assert max(float(line["y1"]), float(line["y2"])) <= max(row_y) + 15, ("null reaches footer", line, row_y)
        view.report_action.setChecked(False)
        from PyQt6.QtCore import Qt
        heading = next(s.title for s in view.results.sections if s.kind == "image" and s.source_key == title)
        items = view.nav_tree.findItems(heading, Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive)
        assert len(items) == 1, (title, items)
        view.nav_tree.setCurrentItem(items[0])
        record("round3-sequential-rows", view, title=title, workflow=workflow,
               rows=table.rows, figure=data, plots={title: path})
        scroll = view.graphics_view.verticalScrollBar()
        position = scroll.value()
        scroll.setValue(scroll.maximum())
        record("round3-sequential-bottom", view, title=title, workflow=workflow)
        scroll.setValue(position)


def check_excluding_null(app, view, record):
    from advanced_workflows import click, modal
    from PyQt6 import QtWidgets
    from rc_metastudio import r_bridge
    from rc_metastudio.plot_editor_dialog import EditPlotDialog

    def exclude_null(dialog):
        dialog.plot_lb_le.setText("0.5")
        dialog.plot_ub_le.setText("2")
        record("round3-null-excluded-controls", dialog)
        click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Apply))
        click(app, dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel))

    modal(app, EditPlotDialog, exclude_null, view.edit_plot_action.trigger)
    for title, path in view.results.display_images.items():
        r_bridge.load_in_r(str(view.params_paths[title]) + ".plotdata")
        observed = json.loads(str(r_bridge.r_iterable_to_list(r_bridge.ro.r('local({ limits <- RCMetaR:::rcmetar.forest.layout.preflight(plot.data)$x$alim; jsonlite::toJSON(list(range=limits, null=RCMetaR:::rcmetar.metafor.refline(plot.data, limits)),auto_unbox=TRUE,na="null") })'))[0]))
        assert observed == {"range": [.5, 2], "null": None}, observed
        lines = [node.attrib for node in ET.parse(path).iter("{http://www.w3.org/2000/svg}line")]
        assert not any(abs(float(line["x1"]) - float(line["x2"])) < .01
                       and abs(float(line["y1"]) - float(line["y2"])) > 50 for line in lines), lines
        record("round3-null-excluded-rendered", view, observed=observed, plots={title: path})


def check_bubble_ticks(view, metric, record):
    for path in view.results.display_images.values():
        svg = ET.parse(path)
        ticks = []
        tick_nodes = []
        for node in svg.iter("{http://www.w3.org/2000/svg}text"):
            if node.attrib.get("text-anchor") != "end":
                continue
            try:
                label = "".join(node.itertext())
                value = float(label)
                assert not ("." in label and label.endswith("0")), ("padded bubble tick", label)
                if metric == "OR":
                    mantissa = value / 10 ** math.floor(math.log10(value))
                    assert any(math.isclose(mantissa, round_value) for round_value in (1, 2, 5)), ("non-round ratio tick", label)
                elif metric == "PLO":
                    assert value in {.001, .005, .01, .05, .1, .25, .5, .75, .9, .95, .99, .995, .999}, ("non-round proportion tick", label)
                ticks.append((value, float(node.attrib["y"])))
                tick_nodes.append(node)
            except ValueError:
                pass
        if metric == "linear":
            title = next(node for node in svg.iter("{http://www.w3.org/2000/svg}text")
                         if "Entered effect" in "".join(node.itertext()))
            title_x = float(title.attrib.get("x", required(re.search(r"translate\(([-\d.]+)", title.attrib.get("transform", "translate(0")))[1]))
            title_right = title_x + float(required(re.search(r"font-size:\s*([\d.]+)px", title.attrib["style"]))[1])
            tick_left = min(float(node.attrib["x"]) - float(node.attrib["textLength"].removesuffix("px")) for node in tick_nodes)
            assert tick_left - title_right >= 4, ("tick/title gap", tick_left, title.attrib)
        assert 3 <= len(ticks) <= 8, ticks
        bubble_group = next(group for group in svg.iter("{http://www.w3.org/2000/svg}g")
                            if group.find("{http://www.w3.org/2000/svg}circle") is not None)
        clip_id = bubble_group.attrib["clip-path"].removeprefix("url(#").removesuffix(")")
        frames = [rect.attrib for clip in svg.iter("{http://www.w3.org/2000/svg}clipPath")
                  if clip.attrib["id"] == clip_id for rect in clip]
        assert len(frames) == 1, frames
        # Full-width dashed guides must stay inside the actual panel.
        frame = frames[0]
        top, bottom = float(frame["y"]), float(frame["y"]) + float(frame["height"])
        for node in svg.iter("{http://www.w3.org/2000/svg}line"):
            if "stroke-dasharray" not in node.attrib.get("style", ""):
                continue
            if abs(float(node.attrib["y1"]) - float(node.attrib["y2"])) < .01:
                assert top <= float(node.attrib["y1"]) <= bottom, ("guide outside bubble panel", node.attrib, frame)
        height = float(frames[0]["height"])
        coverage = (max(y for _, y in ticks) - min(y for _, y in ticks)) / height
        assert coverage >= .55, (ticks, frames[0], coverage)
        positions = sorted(y for _, y in ticks)
        assert min(b-a for a, b in zip(positions, positions[1:])) >= 12, ticks
        record("round3-bubble-tick-coverage", view, ticks=ticks, plot_frame=frames[0], coverage=coverage,
               metric=metric, plots=dict(view.results.display_images))
