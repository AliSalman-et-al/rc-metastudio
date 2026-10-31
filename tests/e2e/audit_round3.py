"""Round-three report and sequential figure contracts through real Qt and R."""

import json
import math
import re
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
from tests.python.gui.test_types import required


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
    if len(spacing) > 1:
        row_height = median(spacing)
        assert all(height <= row_height*.45+.03 for _,height in caps), ("CI caps cross row bands", path, row_height, caps)


def check_report(app, view, work, record):
    from rc_metastudio import results_window

    assert "Model configuration\n" in view.report_text.toPlainText()
    scene_text = [item.toPlainText() for item in view.scene.items() if hasattr(item, "toPlainText")]
    for section in view.results.sections:
        if section.source_key == "Weights":
            assert section.value not in scene_text, "legacy scene weights remain"

    view.copy_report_action.trigger()
    copied = app.clipboard().text()
    assert copied.startswith(view.results.identity + "\n"), copied
    for section in view.results.sections:
        for table in section.tables:
            assert "\t".join(table.headers) in copied, (table.title, copied)
            for row in table.rows:
                assert "\t".join(row) in copied, (table.title, row, copied)
    output = work / "round3-report.pdf"
    with patch.object(results_window.QFileDialog, "getSaveFileName", return_value=(str(output), "PDF (*.pdf)")):
        view.export_report_action.trigger()
    assert output.read_bytes().startswith(b"%PDF")
    assert app.clipboard().mimeData().hasHtml()
    if "Omission-only fits:" in view.results.details:
        assert copied.count("Omission-only fits:") == 1, copied
        assert "\nleave-one-out\n" not in copied, copied
    if "\nSensitivity\n" in view.results.details:
        for line in view.results.details.splitlines():
            if line.startswith(("Order:", "Each row", "Subgroups by", "Moderators:")):
                assert view.results.details.index(line) < view.results.details.index("\nSensitivity\n"), view.results.details
                assert line in copied and "Methods\n" in copied, copied
    view.report_action.setChecked(True)
    app.processEvents()
    record("round3-report-copy-export", view, identity=view.results.identity,
           text=copied, tables=[dict(title=t.title, headers=t.headers, rows=t.rows)
                               for s in view.results.sections for t in s.tables])


def check_annotation_spacing(view):
    assert "Overall-effect null:" not in view.report_text.toPlainText(), view.report_text.toPlainText()
    for path in view.results.display_images.values():
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


def check_fixed_references(view, record, method="IV"):
    report = view.report_text.toPlainText()
    assert "Random-effects meta-analysis:" not in report, report
    assert "Random-effects meta-regression:" not in report, report
    expected = {"IV": "Fixed-effect inverse-variance meta-analysis:",
                "MH": "Mantel-Haenszel meta-analysis:", "PETO": "Peto one-step odds-ratio method:"}[method]
    assert expected in report, report
    previous = view.report_action.isChecked()
    view.report_action.setChecked(True)
    view.report_text.verticalScrollBar().setValue(view.report_text.verticalScrollBar().maximum())
    record("round3-fixed-references", view, method=method, identity=view.results.identity, text=report)
    view.report_text.verticalScrollBar().setValue(0)
    view.report_action.setChecked(previous)


def check_standard_heterogeneity(view, record):
    from rc_metastudio import r_bridge
    tables = [t for s in view.results.sections for t in s.tables if t.title.endswith("Heterogeneity")]
    for table, (title, path) in zip(tables, view.results.display_images.items(), strict=True):
        r_bridge.load_in_r(str(view.params_paths[title]) + ".plotdata")
        expected = json.loads(str(r_bridge.r_iterable_to_list(r_bridge.ro.r('''jsonlite::toJSON(local({
          fit <- plot.data$res
          direct <- metafor::rma.uni(yi=fit$yi, vi=fit$vi, method=fit$method, test=fit$test, level=fit$level)
          list(data_type=plot.data$data_type, Q=direct$QE, df=direct$k-direct$p, p=direct$QEp, I2=direct$I2, tau2=direct$tau2,
               random=!direct$method %in% c("FE", "EE", "CE"))
        }), auto_unbox=TRUE, digits=16)'''))[0]))
        assert table.headers == ("Q", "df", "p-value", "I²") + (("τ²",) if expected["random"] else ()), table
        for cell, key in zip(table.rows[0], ("Q", "df", "p", "I2", "tau2")):
            if cell.startswith("<"):
                assert expected[key] < float(cell[1:]), (cell, expected)
            else:
                assert abs(float(cell.rstrip("%"))-expected[key]) <= (.05001 if key == "I2" else 5.01e-7), (cell, expected)
        if expected["data_type"] in {"binary", "continuous"}:
            weights = next(t for section in view.results.sections for t in section.tables if t.title == "Study weights")
            assert weights.headers == ("Study", "Weight (%)"), weights
            assert len(weights.rows) > 0 and all(row[1].endswith("%") for row in weights.rows), weights
        assert "Pooled " in view.report_text.toPlainText(), view.report_text.toPlainText()
        assert "Calculation scale: log - estimate" not in view.report_text.toPlainText()
        record("round3-standard-heterogeneity-public-reference", view, expected=expected,
               headers=table.headers, rows=table.rows, plots={title: path})


def check_sequential(view, workflow, record):
    from rc_metastudio import r_bridge

    tables = [t for s in view.results.sections for t in s.tables if t.title == "Model Results"]
    for index, (title, path) in enumerate(view.results.display_images.items()):
        params = view.params_paths[title]
        r_bridge.load_in_r(str(params) + ".plotdata")
        data = json.loads(str(r_bridge.r_iterable_to_list(r_bridge.ro.r('jsonlite::toJSON(list(slab=plot.data$slab, labels=RCMetaR:::rcmetar.metafor.effect.labels(plot.data), has_overall=plot.data$has_overall, estimates=plot.data$effect_display$y.disp, measure=plot.data$params$measure, range=RCMetaR:::rcmetar.forest.layout.preflight(plot.data)$x$alim), auto_unbox=TRUE, digits=16)'))[0]))
        svg = ET.parse(path)
        nodes = [("".join(node.itertext()), float(node.attrib.get("y", 0)))
                 for node in svg.iter("{http://www.w3.org/2000/svg}text")]
        table = tables[index]
        assert len(table.rows) == len(data["slab"]), (title, table, data)
        assert table.headers[0] == ("Study added (k)" if workflow == "cumulative" else "Study omitted"), table
        for row, name, effect in zip(table.rows, data["slab"], data["labels"], strict=True):
            label_y = [y for text, y in nodes if text == name]
            effect_y = [y for text, y in nodes if text == effect]
            assert label_y and any(abs(a-b) < .01 for a in label_y for b in effect_y), (title, name, effect, nodes)
            assert row[0] == name, (title, row, name)
            report_effect = row[1] if row[1] == "Not estimable" else f"{row[1]} [{row[2]}, {row[3]}]"
            assert report_effect == effect, (title, row, effect)
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


def check_subgroup(view, record):
    from rc_metastudio import r_bridge

    def compare(cell, expected, tolerance):
        if expected is None:
            assert cell == "", cell
        elif cell.startswith("<"):
            assert expected < float(cell[1:]), (cell, expected)
        else:
            assert abs(float(cell.rstrip("%")) - expected) <= tolerance, (cell, expected)

    sections = [s for s in view.results.sections if any(t.title == "Heterogeneity" for t in s.tables)]
    for index, (title, path) in enumerate(view.results.display_images.items()):
        nodes = list(ET.parse(path).iter('{http://www.w3.org/2000/svg}text'))
        y = lambda prefix: max(float(node.attrib['y']) for node in nodes if ''.join(node.itertext()).startswith(prefix))
        if any(''.join(node.itertext()).startswith('Test for subgroup differences') for node in nodes) and any(''.join(node.itertext()).startswith('95% prediction interval') for node in nodes):
            assert y('Heterogeneity:') < y('Test for overall effect') < y('Test for subgroup differences') < y('95% prediction interval'), title
            from PyQt6.QtCore import Qt
            previous = view.report_action.isChecked()
            heading = next(section.title for section in view.results.sections if section.kind == 'image' and section.source_key == title)
            item = view.nav_tree.findItems(heading, Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive)[0]
            view.nav_tree.setCurrentItem(item)
            view.report_action.setChecked(False)
            selected = view._selected_plot()
            assert selected is not None, title
            bottom = selected[1].sceneBoundingRect().bottom() * view.graphics_view.transform().m22()
            view.graphics_view.verticalScrollBar().setValue(round(bottom - view.graphics_view.viewport().height() + 30))
            record('review1-subgroup-footer-order', view, title=title, plots={title:path})
            view.report_action.setChecked(previous)
        r_bridge.load_in_r(str(view.params_paths[title]) + ".plotdata")
        reference = json.loads(str(r_bridge.r_iterable_to_list(r_bridge.ro.r('''jsonlite::toJSON(local({
          fits <- plot.data$regeneration_state$subgroup_data$results
          lapply(fits, function(fit) {
            direct <- metafor::rma.uni(yi=fit$yi, vi=fit$vi, method=fit$method, test=fit$test, level=fit$level)
            pi <- if (!direct$method %in% c("FE", "EE", "CE") && direct$k > 2) stats::predict(direct) else NULL
            list(k=direct$k, Q=direct$QE, df=direct$k-direct$p, p=direct$QEp, I2=direct$I2,
                 tau2=direct$tau2, z=direct$zval, lower=pi$pi.lb, upper=pi$pi.ub, measure=plot.data$params$measure)
          })
        }), auto_unbox=TRUE, digits=16, null="null")'''))[0]))
        weights = json.loads(str(r_bridge.r_iterable_to_list(r_bridge.ro.r('''jsonlite::toJSON(local({
          state <- plot.data$regeneration_state$subgroup_data
          original <- tail(state$grouped.data, 1)[[1]]
          measure <- plot.data$params$measure
          if (is(original, "RatioData") && measure == "IRR") {
            es <- metafor::escalc(measure="IRR", x1i=original@x1, t1i=original@t1,
                                  x2i=original@x2, t2i=original@t2)
          } else if (is(original, "BinaryData") && measure == "OR") {
            es <- metafor::escalc(measure="OR", ai=original@g1O1, bi=original@g1O2,
                                 ci=original@g2O1, di=original@g2O2)
          } else if (is(original, "ContinuousData") && measure %in% c("MD", "SMD")) {
            es <- metafor::escalc(measure=measure, m1i=original@mean1, sd1i=original@sd1, n1i=original@N1,
                                 m2i=original@mean2, sd2i=original@sd2, n2i=original@N2)
          } else es <- data.frame(yi=original@y, vi=original@SE^2)
          fit <- tail(state$results, 1)[[1]]
          direct <- metafor::rma.uni(yi=es$yi, vi=es$vi, method=fit$method, test=fit$test, level=fit$level)
          order <- unlist(state$row.indices, use.names=FALSE)
          list(expected=as.numeric(weights(direct))[order], actual=plot.data$weights,
               order=order, names=plot.data$slab, total=sum(plot.data$weights),
               inputs=list(names=original@study.names, yi=es$yi, vi=es$vi))
        }), auto_unbox=TRUE, digits=16)'''))[0]))
        assert len(weights["expected"]) == len(weights["actual"]), weights
        assert all(abs(a-b) < 1e-8 for a,b in zip(weights["expected"], weights["actual"], strict=True)), weights
        assert abs(weights["total"] - 100) < 1e-8, weights
        record("round4-subgroup-weights", view, title=title, weights=weights, plots={title: path})
        tables = {t.title: t for t in sections[index].tables}
        model, heterogeneity = tables["Model Results"], tables["Heterogeneity"]
        assert "k" in model.headers
        assert all(h in heterogeneity.headers for h in ("Q", "df", "p-value", "I²"))
        for row, het, expected in zip(model.rows, heterogeneity.rows, reference, strict=True):
            compare(row[1], expected["k"], 0)
            compare(row[7], expected["z"], 5.01e-7)
            for column, key, tolerance in ((1, "Q", 5.01e-7), (2, "df", 0), (3, "p", 5.01e-7), (4, "I2", .05001)):
                compare(het[column], expected[key], tolerance)
            if "τ²" in heterogeneity.headers:
                compare(het[5], expected["tau2"], 5.01e-7)
        if "Prediction interval" in tables:
            for row, expected in zip(tables["Prediction interval"].rows, reference, strict=True):
                if expected["lower"] is None:
                    assert not row[1] and not row[2]
                    continue
                transform = (math.exp if expected["measure"] in {"OR", "RR", "HR", "IRR", "DOR", "PLR", "NLR"}
                             else lambda x: 1 / (1 + math.exp(-x)) if expected["measure"] in {"PLO", "Sens", "Spec"} else x)
                compare(row[1], transform(expected["lower"]), 5.01e-7)
                compare(row[2], transform(expected["upper"]), 5.01e-7)
        record("round3-subgroup-public-reference", view, title=title, expected=reference,
               tables={name: dict(headers=t.headers, rows=t.rows) for name, t in tables.items()}, plots={title: path})


def analyze_existing(app, window, workflow, method, record, parameters=None):
    from PyQt6 import QtCore, QtWidgets
    from rc_metastudio import analysis_setup_dialog, results_window
    from rc_metastudio.subgroup_analysis_dialog import SubgroupAnalysisDialog
    from analysis_matrix import set_parameter
    from tests.python.gui.test_types import mouse_click

    def visible(kind):
        return next(w for w in app.topLevelWidgets() if isinstance(w, kind) and w.isVisible())

    action = {"standard": window.action_go, "cumulative": window.action_cum_ma,
              "leave-one-out": window.action_loo_ma, "subgroup": window.action_subgroup_ma,
              "meta-regression": window.action_meta_regression}[workflow]
    action.trigger()
    app.processEvents()
    if workflow == "subgroup":
        subgroup = visible(SubgroupAnalysisDialog)
        subgroup.covariate_combo_box.setCurrentIndex(subgroup.covariate_combo_box.findText("Group"))
        mouse_click(subgroup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok), QtCore.Qt.MouseButton.LeftButton)
    dialog = visible(analysis_setup_dialog.AnalysisSetupDialog)
    if workflow == "meta-regression":
        for covariate, checkbox in dialog.covs_and_check_boxes:
            checkbox.setChecked(covariate["name"] == "Dose")
    else:
        dialog.method_cbo_box.setCurrentText(next(label for label, key in dialog.available_method_d.items() if key == method))
    app.processEvents()
    for key, value in {"digits": 6, **(parameters or {})}.items():
        set_parameter(app, dialog, key, value)
    from tests.e2e.review1_design import keyboard_traversal
    parameter_controls = [control for control in dialog.current_widgets if control.focusPolicy() & QtCore.Qt.FocusPolicy.TabFocus]
    keyboard_traversal(app, dialog, [dialog.method_cbo_box, *parameter_controls,
                       dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok),
                       dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel)], record, "setup")
    if workflow == "meta-regression":
        from tests.e2e.review1_design import keyboard_dialog_pages
        keyboard_dialog_pages(app, dialog, record)
    record("round3-configured", dialog, workflow=workflow, method=method, parameters=dialog.current_param_vals)
    mouse_click(dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok), QtCore.Qt.MouseButton.LeftButton)
    app.processEvents()
    view = visible(results_window.ResultsWindow)
    view.resize(1500, 850)
    app.processEvents()
    return view


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



def run(app, window, work, record, scenario):
    from analysis_matrix import DATA_TYPES, run as matrix

    def prepare(target):
        studies = target.model.get_studies(only_if_included=True)
        target.model.add_covariate("Group", "factor",
                                          {s.label: "A" if i % 2 else "B" for i, s in enumerate(studies)})
        target.model.reset_model()
        target.enable_menu_options_that_require_dataset()

    def duplicate_names(target):
        studies = target.model.get_studies(only_if_included=True)
        studies[1].label = studies[0].label
        group = target.model.add_covariate("Group", "factor")
        for i, study in enumerate(studies):
            study.covariate_values[group["id"]] = "A" if i % 2 else "B"
        target.model.reset_model()
        target.enable_menu_options_that_require_dataset()

    family_name = scenario.removeprefix("audit-round3-")
    if family_name == "arm-names":
        from tests.e2e.arm_names import run as naming
        return naming(app, window, work, record)
    if family_name == "irr-context":
        return run_irr_context(app, window, record)
    if family_name in {"round5", "bubble-metrics"}:
        return run_round5(app, window, work, record, prepare, only_bubbles=family_name == "bubble-metrics")
    if family_name.startswith("presentation-"):
        from PyQt6 import QtCore
        selected_family = family_name.removeprefix("presentation-")
        cases = [] if selected_family == "sequential" else [(selected_family, None)]
        if selected_family == "transforms":
            cases = [("onearm-proportion", metric) for metric in ("PLN", "PLO", "PAS", "PFT")]
        for family, metric in cases:
            def select_metric(target):
                if metric:
                    next(action for action in target.oneArmMetricMenu.actions() if action.data() == metric).trigger()
                    app.processEvents()
            for digits in ((3,) if metric else (3, 6)):
                for style in ("default", "revman", "bmj"):
                    window.workspace.mark_saved()
                    view = matrix(app, window, "analysis-data-" + family, record, keep_results=True,
                                  parameters={"digits": digits, "fp_style": style}, prepare=select_metric)
                    check_annotation_spacing(view)
                    if metric:
                        from rc_metastudio import r_bridge
                        for title, path in view.results.display_images.items():
                            r_bridge.load_in_r(str(view.params_paths[title]) + ".plotdata")
                            axis = json.loads(str(r_bridge.r_iterable_to_list(r_bridge.ro.r('jsonlite::toJSON(local({plan <- RCMetaR:::rcmetar.forest.layout.preflight(plot.data); ticks <- RCMetaR:::rcmetar.metafor.axis.ticks(plot.data, plan$x$alim); list(metric=plot.data$params$measure, ticks=ticks, labels=RCMetaR:::rcmetar.revman.axis.labels(plot.data, ticks))}), auto_unbox=TRUE, digits=16)'))[0]))
                            raw = [[float(window.model.data(window.model.index(row, column))) for column in window.model.RAW_DATA[:2]] for row in range(6)]
                            assert raw == [[4.0+i, 20.0+i] for i in range(6)], raw
                            counts = ",".join(str(row[0]) for row in raw)
                            totals = ",".join(str(row[1]) for row in raw)
                            reference = json.loads(str(r_bridge.r_iterable_to_list(r_bridge.ro.r(f'''jsonlite::toJSON(local({{
                                n <- c({totals}); es <- metafor::escalc(measure="{metric}", xi=c({counts}), ni=n)
                                fit <- metafor::rma.uni(es$yi, es$vi, method="DL", level=95)
                                display <- function(x, n) switch("{metric}", PLN=exp(x), PLO=stats::plogis(x), PAS=metafor::transf.iarcsin(x), PFT=metafor::transf.ipft(x, ni=n))
                                pooled <- function(x) if ("{metric}" == "PFT") metafor::transf.ipft.hm(x, targs=list(ni=n)) else display(x, n)
                                margin <- stats::qnorm(.975) * sqrt(es$vi)
                                list(studies=cbind(display(es$yi,n),display(es$yi-margin,n),display(es$yi+margin,n)),
                                     pooled=vapply(c(fit$b,fit$ci.lb,fit$ci.ub), pooled, numeric(1)))
                            }}), auto_unbox=TRUE, digits=16)'''))[0]))
                            table = next(table for section in view.results.sections for table in section.tables if table.title == "Model Results")
                            assert all(abs(float(cell)-expected) < .000501 for cell, expected in zip(table.rows[0][:3], reference["pooled"], strict=True)), (table, reference)
                            nodes = list(ET.parse(path).iter("{http://www.w3.org/2000/svg}text"))
                            expected_null = {"PLN": "proportion = 1", "PLO": "proportion = 0.5", "PAS": "proportion = 0", "PFT": "Freeman–Tukey transformed proportion = 0"}[metric]
                            assert any("H₀: " + expected_null in "".join(node.itertext()) for node in nodes), (metric, ["".join(node.itertext()) for node in nodes])
                            assert "Pooled Proportion:" in view.report_text.toPlainText()
                            last_study_y = max(float(node.attrib["y"]) for node in nodes if "".join(node.itertext()).startswith("Fixture "))
                            axis_labels = ["".join(node.itertext()) for node in nodes if float(node.attrib["y"]) > last_study_y]
                            assert any(label.startswith("Proportion") for label in axis_labels), (metric, axis_labels)
                            assert not any("transformed Proportion" in label for label in axis_labels), metric
                            annotations = [node for node in nodes if re.fullmatch(r"[+\-\d.eE]+ (?:\[.*\]|\(.* to .*\))", "".join(node.itertext()))]
                            for index, expected in enumerate(reference["studies"]):
                                name = next(node for node in nodes if "".join(node.itertext()) == "Fixture " + str(index+1))
                                row = next(node for node in annotations if abs(float(node.attrib["y"])-float(name.attrib["y"])) < 2)
                                values = [float(value) for value in re.findall(r"[+\-]?\d+(?:\.\d+)?(?:e[+\-]?\d+)?", "".join(row.itertext()))]
                                assert all(abs(value-ref) < .000501 for value, ref in zip(values, expected, strict=True)), (metric, style, index, values, expected)
                            record("review1-transformed-public-reference", view, metric=metric, style=style, inputs=raw, reference=reference)
                            labels = [float(label) for label in axis["labels"]]
                            assert len(labels) >= 2, axis
                            assert labels[0] == 0 and labels[-1] == 1, axis
                            assert all(abs(value*10-round(value*10)) < 1e-7 for value in labels), axis
                            record("review1-transformed-forest-axis", view, axis=axis, plots={title: path})
                    from PyQt6.QtCore import Qt
                    for title, path in view.results.display_images.items():
                        heading = next(section.title for section in view.results.sections
                                       if section.kind == "image" and section.source_key == title)
                        items = view.nav_tree.findItems(heading, Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive)
                        assert len(items) == 1, (title, items)
                        view.nav_tree.setCurrentItem(items[0])
                        if digits in (3, 6):
                            from advanced_workflows import export_formats
                            export_formats(app, view, work, family + "-" + style + "-" + str(digits) + "-" + title, record)
                        record("round4-annotations", view, family=family, digits=digits, style=style,
                               title=title, metric=metric, plots={title: path})
                        selected = view._selected_plot()
                        bottom = selected[1].sceneBoundingRect().bottom() * view.graphics_view.transform().m22()
                        view.graphics_view.verticalScrollBar().setValue(round(bottom - view.graphics_view.viewport().height() + 30))
                        record("round4-annotations-bottom", view, family=family, digits=digits, style=style, title=title)
                    view.close()
                    view.deleteLater()
                    app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        if selected_family in {"generic-effect", "reg-coef"}:
            from advanced_workflows import modal
            from rc_metastudio.continuous_data_dialog import ContinuousDataDialog
            def inspect_calculator(dialog):
                label = "Entered effect" if selected_family == "generic-effect" else "Coefficient"
                assert dialog.effect_combo_box.currentText() == label, dialog.effect_combo_box.currentText()
                assert dialog.input_mode_combo.currentData() == "estimate"
                assert not dialog.simple_group.isVisible()
                record("round4-contextual-calculator", dialog, family=selected_family)
                dialog.reject()
            modal(app, ContinuousDataDialog, inspect_calculator,
                  lambda: window.tableView.row_header_clicked(0))
        if selected_family == "generic-effect":
            import csv
            from unittest.mock import patch
            from rc_metastudio import main_wizard
            from PyQt6 import QtWidgets
            from advanced_workflows import click
            wizard = main_wizard.MainWizard(path="csv_import")
            wizard.set_dataset_info(dict(arms="one", data_type="continuous", sub_type="generic_effect",
                                         effect="TX Mean", metric_choices=[], name="Entered estimates"))
            wizard.setStartId(main_wizard.Page_CsvImport)
            wizard.restart()
            wizard.show()
            app.processEvents()
            page = wizard.currentPage()
            assert isinstance(page, main_wizard.CsvImportPage)
            assert "Estimate" in page.required_header_labels and "TX Mean" not in page.required_header_labels, page.required_header_labels
            source = work / "entered-estimate-alias.csv"
            with source.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["Study", "Year", "TX Mean", "SE"])
                writer.writerow(["Entered row", 2026, .2, .1])
            with patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=(str(source), "")):
                click(app, page.select_file_btn)
            assert page.isComplete(), page.import_status.text()
            headers = [required(page.preview_table.horizontalHeaderItem(i)).text() for i in range(page.preview_table.columnCount())]
            assert "Estimate" in headers and "TX Mean" not in headers, headers
            record("round4-contextual-csv", wizard, headers=headers, input_headers=page.required_header_labels,
                   exports={"csv": str(source)})
            wizard.reject()
            wizard.deleteLater()
            app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        for family in ([selected_family] if selected_family in {"twoarm-proportion", "twoarm-mean"} else []):
            window.workspace.mark_saved()
            view = matrix(app, window, "analysis-data-" + family, record, keep_results=True,
                          workflow_override="subgroup", parameters={"digits": 6}, prepare=duplicate_names)
            check_subgroup(view, record)
            view.close()
            view.deleteLater()
            app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        for workflow in (("cumulative", "leave-one-out") if selected_family == "sequential" else ()):
            for style in ("default", "revman", "bmj"):
                window.workspace.mark_saved()
                view = matrix(app, window, "analysis-data-twoarm-mean", record, keep_results=True,
                              workflow_override=workflow, parameters={"digits": 6, "fp_style": style})
                check_sequential(view, workflow, record)
                from advanced_workflows import export_formats
                export_formats(app, view, work, workflow + "-" + style, record)
                if workflow == "cumulative":
                    check_excluding_null(app, view, record)
                view.close()
                view.deleteLater()
                app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        return

    if family_name == "precision":
        from rc_metastudio import r_bridge
        def entered(target, values):
            model = target.model
            for row in range(6):
                for column in model.OUTCOMES:
                    assert model.setData(model.index(row, column), "")
                for column, value in zip(model.OUTCOMES, values, strict=True):
                    assert model.setData(model.index(row, column), str(value))
        view = matrix(app, window, "analysis-data-reg-coef", record, keep_results=True,
                      parameters={"digits": 6}, prepare=lambda target: entered(target, (.2, 0, .4)))
        for path in view.results.display_images.values():
            nodes = list(ET.parse(path).iter("{http://www.w3.org/2000/svg}text"))
            captions = ["".join(node.itertext()) for node in nodes]
            assert not any(" · None" in caption for caption in captions), captions
            assert any("[0.000000, 0.400000]" in caption for caption in captions), captions
            assert not any("e-16" in caption or "e-17" in caption for caption in captions), captions
            for weight in (node for node in nodes if re.fullmatch(r"[\d.]+%", "".join(node.itertext()))):
                row = [node for node in nodes if "[" in "".join(node.itertext())
                       and abs(float(node.attrib["y"]) - float(weight.attrib["y"])) < 2]
                assert len(row) == 1, row
                estimate = row[0]
                right = float(weight.attrib["x"]) + float(weight.attrib["textLength"].removesuffix("px")) / 2
                left = float(estimate.attrib["x"]) - float(estimate.attrib["textLength"].removesuffix("px"))
                assert left - right >= 4, ("weight/estimate gap", left - right)
        record("round3-zero-bound-presentation", view, entered_bounds=[0, .4], plots=dict(view.results.display_images))
        view.close()
        window.workspace.mark_saved()
        view = matrix(app, window, "analysis-data-generic-effect", record, keep_results=True,
                      parameters={"digits": 6}, prepare=lambda target: entered(target, (1e-10, 1e-11)))
        reference = json.loads(str(r_bridge.r_iterable_to_list(r_bridge.ro.r('local({f <- metafor::rma.uni(yi=rep(1e-10,6), sei=rep(1e-11,6), method="DL"); jsonlite::toJSON(list(estimate=as.numeric(f$b),lower=f$ci.lb,upper=f$ci.ub,se=f$se),auto_unbox=TRUE,digits=16)})'))[0]))
        row = next(t for s in view.results.sections for t in s.tables if t.title == "Model Results").rows[0]
        for cell, expected in zip(row[:4], reference.values(), strict=True):
            assert float(cell) != 0 and math.isclose(float(cell), expected, rel_tol=1e-6), (cell, expected)
        check_report(app, view, work, record)
        view.report_action.setChecked(False)
        app.processEvents()
        for path in view.results.display_images.values():
            svg = ET.parse(path)
            captions = ["".join(node.itertext()) for node in svg.iter("{http://www.w3.org/2000/svg}text")]
            ticks = {caption for caption in captions if re.fullmatch(r"[-+\d.]+e[-+]\d+", caption)}
            assert len(ticks) >= 2, ticks
            width = float(svg.getroot().attrib["width"].removesuffix("pt"))
            intervals = [node.attrib for node in svg.iter("{http://www.w3.org/2000/svg}line")
                         if abs(float(node.attrib["y1"]) - float(node.attrib["y2"])) < .01
                         and abs(float(node.attrib["x1"]) - float(node.attrib["x2"])) > width * .01]
            assert len(intervals) >= 6, intervals
        record("round3-small-effects-preserved", view, expected=reference, actual=row, plots=dict(view.results.display_images))
        view.close()
        window.workspace.mark_saved()
        for style in ("default", "revman", "bmj"):
            view = matrix(app, window, "analysis-data-generic-effect", record, keep_results=True,
                          parameters={"digits": 6, "fp_style": style},
                          prepare=lambda target: entered(target, (1, 1e-20)))
            assert view.results.display_images, "missing degenerate-axis figures"
            bounds, ticks = [], set()
            for title, path in view.results.display_images.items():
                r_bridge.load_in_r(str(view.params_paths[title]) + ".plotdata")
                bounds = r_bridge.r_iterable_to_list(r_bridge.execute_r_string('RCMetaR:::rcmetar.forest.layout.preflight(plot.data)$x$alim'))
                assert all(math.isfinite(x) for x in bounds) and bounds[1] > bounds[0], bounds
                nodes = list(ET.parse(path).iter("{http://www.w3.org/2000/svg}text"))
                numeric = [n for n in nodes if n.attrib.get("text-anchor") == "middle"
                           and re.fullmatch(r"[\d.]+", "".join(n.itertext()))]
                axis_y = max(float(n.attrib["y"]) for n in numeric)
                labels = ["".join(n.itertext()) for n in numeric if abs(float(n.attrib["y"])-axis_y) < .01]
                ticks = set(labels)
                assert len(ticks) >= 2, ticks
                assert len(labels) == len(ticks), ("duplicate collapsed-axis labels", style, labels)
            record("round3-degenerate-axis", view, style=style, entered=[1, 1e-20], bounds=bounds,
                   ticks=sorted(ticks), plots=dict(view.results.display_images))
            if style == "default":
                view.graphics_view.verticalScrollBar().setValue(view.graphics_view.verticalScrollBar().maximum())
                record("round3-degenerate-axis-bottom", view, style=style, bounds=bounds)
            view.close()
            window.workspace.mark_saved()
        for metric in ("OR", "PLO", "linear"):
            window.workspace.mark_saved()
            def select_metric(target):
                if metric == "PLO":
                    for row, events in enumerate((3, 15, 30, 50, 70, 90)):
                        for column, value in zip(reversed(target.model.RAW_DATA[:2]), (100, events), strict=True):
                            assert target.model.setData(target.model.index(row, column), str(value))
                    next(action for action in target.oneArmMetricMenu.actions() if action.data() == "PLO").trigger()
                    app.processEvents()
                    from PyQt6.QtCore import Qt
                    for row in range(6):
                        assert target.model.setData(target.model.index(row, target.model.INCLUDE_STUDY),
                                                    Qt.CheckState.Checked, Qt.ItemDataRole.CheckStateRole)
                if metric in {"PLO", "linear"}:
                    studies = target.model.get_studies(only_if_included=True)
                    assert len(studies) == 6, studies
                    target.model.add_covariate("Dose", "continuous",
                                                      {s.label: float(i) for i, s in enumerate(studies)})
                    target.model.reset_model()
                    target.enable_menu_options_that_require_dataset()
                    record("round3-proportion-input", target, metric=target.model.current_effect,
                           raw=target.model.get_current_raw_data(),
                           effects=target.model.get_current_estimates_and_standard_errors(),
                           raw_complete=target.model.included_studies_have_raw_data())
            view = matrix(app, window, "analysis-amino-binary-meta-regression" if metric == "OR" else "analysis-data-onearm-proportion" if metric == "PLO" else "analysis-data-generic-effect",
                          record, keep_results=True, workflow_override="meta-regression",
                          parameters={"digits": 6}, prepare=select_metric)
            check_bubble_ticks(view, metric, record)
            view.close()
        return

    names = [family_name] if family_name in DATA_TYPES else []
    for name in names:
        for workflow in ("cumulative", "leave-one-out", "subgroup"):
            window.workspace.mark_saved()
            view = matrix(app, window, "analysis-data-" + name, record,
                          keep_results=True, workflow_override=workflow,
                          parameters={"digits": 6}, prepare=prepare if workflow == "subgroup" else None)
            check_report(app, view, work, record)
            if workflow != "subgroup":
                check_sequential(view, workflow, record)
                if name == "twoarm-mean" and workflow == "cumulative":
                    check_excluding_null(app, view, record)
            else:
                check_subgroup(view, record)
            view.close()
            app.processEvents()

    if names:
        return
    from PyQt6 import QtCore
    root = Path(__file__).resolve().parents[2]
    samples = {"hr": ("time_to_event", "Pignon2000-HR"), "irr": ("event_rates", "NielWeise2008-IRR")}
    for family, sample in ([samples[family_name]] if family_name in samples else []):
        window.workspace.mark_saved()
        assert window.open(str(root / "sample_projects" / (sample + ".rcms")), raise_on_error=True)
        duplicate_names(window)
        model = window.model
        assert model.setData(model.index(1, model.INCLUDE_STUDY), QtCore.Qt.CheckState.Unchecked, QtCore.Qt.ItemDataRole.CheckStateRole)
        record("round3-ratio-excluded-study", window, family=family, excluded=model.get_studies(False)[1].label)
        for workflow in ("cumulative", "leave-one-out", "subgroup"):
            view = analyze_existing(app, window, workflow, family + ".random", record)
            check_report(app, view, work, record)
            if workflow == "subgroup":
                check_subgroup(view, record)
            else:
                check_sequential(view, workflow, record)
                if workflow == "leave-one-out":
                    assert "Omission-only fits" in view.report_text.toPlainText()
                    assert "All studies" not in next(t for s in view.results.sections for t in s.tables if t.title == "Model Results").rows[0][0]
            view.close()
        if family == "event_rates":
            # Only one included study has treated events. Omitting it leaves a
            # non-estimable MH fit while all other omission identities remain.
            for row in range(len(model.get_studies(False))):
                assert model.setData(model.index(row, model.RAW_DATA[0]), "3" if row == 0 else "0")
            view = analyze_existing(app, window, "leave-one-out", "event_rates.mh", record)
            check_report(app, view, work, record)
            check_sequential(view, "leave-one-out", record)
            assert "Non-estimable" in view.report_text.toPlainText()
            view.close()
        window.workspace.mark_saved()
        assert window.open(str(root / "sample_projects" / (sample + ".rcms")), raise_on_error=True)
        duplicate_names(window)
        for workflow in ("cumulative", "leave-one-out", "subgroup"):
            view = analyze_existing(app, window, workflow, family + ".fixed", record)
            check_report(app, view, work, record)
            check_fixed_references(view, record)
            if workflow == "subgroup":
                check_subgroup(view, record)
            else:
                check_sequential(view, workflow, record)
            view.close()
        view = analyze_existing(app, window, "standard", family + ".fixed", record)
        check_fixed_references(view, record)
        check_standard_heterogeneity(view, record)
        assert "Estimator:" not in view.results.details, view.results.details
        for path in view.results.display_images.values():
            captions = "\n".join("".join(node.itertext()) for node in ET.parse(path).iter("{http://www.w3.org/2000/svg}text"))
            assert "τ²" not in captions and all(label in captions for label in ("Q =", "df =", "I² =")), captions
        record("round3-fixed-footer", view, details=view.results.details, plots=dict(view.results.display_images))
        view.graphics_view.verticalScrollBar().setValue(view.graphics_view.verticalScrollBar().maximum())
        record("round3-fixed-footer-bottom", view, details=view.results.details)
        original_identity = view.results.identity
        window.workspace.mark_saved()
        assert window.open(str(root / "sample_projects/continuous.rcms"), raise_on_error=True)
        check_report(app, view, work, record)
        assert view.results.identity == original_identity
        from PyQt6 import QtWidgets
        from rc_metastudio import analysis_setup_dialog, results_window
        from tests.python.gui.test_types import mouse_click
        for suffix in ("random", "fixed"):
            view.change_settings_action.trigger()
            app.processEvents()
            dialog = next(w for w in app.topLevelWidgets() if isinstance(w, analysis_setup_dialog.AnalysisSetupDialog) and w.isVisible())
            assert dialog.data_type == family
            dialog.method_cbo_box.setCurrentText(next(label for label, key in dialog.available_method_d.items() if key == family + "." + suffix))
            app.processEvents()
            previous = {id(w) for w in app.topLevelWidgets() if isinstance(w, results_window.ResultsWindow)}
            mouse_click(dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok), QtCore.Qt.MouseButton.LeftButton)
            app.processEvents()
            changed = next(w for w in app.topLevelWidgets() if isinstance(w, results_window.ResultsWindow) and w.isVisible() and id(w) not in previous)
            assert ("Estimator:" in changed.results.details) == (suffix == "random"), changed.results.details
            assert changed.results.identity == original_identity
            record("round3-fixed-random-rerun", changed, method=suffix, details=changed.results.details, plots=dict(changed.results.display_images))
            view.close()
            view = changed
        view.close()

    if family_name != "references":
        return
    for scenario, method in (("analysis-binary.fixed.mh", "MH"), ("analysis-binary.fixed.peto", "PETO"),
                             ("analysis-diagnostic.fixed.mh", "MH"), ("analysis-diagnostic.fixed.peto", "PETO")):
        window.workspace.mark_saved()
        view = matrix(app, window, scenario, record, keep_results=True)
        check_report(app, view, work, record)
        check_fixed_references(view, record, method)
        view.close()
    for scenario in ("analysis-binary.fixed.inv.var", "analysis-continuous.fixed", "analysis-diagnostic.fixed.inv.var"):
        for workflow in ("standard", "cumulative", "leave-one-out", "subgroup"):
            window.workspace.mark_saved()
            view = matrix(app, window, scenario, record, keep_results=True, workflow_override=workflow,
                          parameters={"digits": 6}, prepare=prepare if workflow == "subgroup" else None)
            check_report(app, view, work, record)
            check_fixed_references(view, record)
            if workflow == "standard":
                check_standard_heterogeneity(view, record)
            view.close()
    for family in ("amino-binary", "continuous"):
        window.workspace.mark_saved()
        view = matrix(app, window, "analysis-" + family + "-meta-regression", record,
                      keep_results=True, parameters={"digits": 6}, fixed_effects=True)
        check_report(app, view, work, record)
        check_fixed_references(view, record)
        view.close()
    for scenario in ("analysis-amino-binary-subgroup", "analysis-continuous-subgroup", "analysis-diagnostic-combined"):
        window.workspace.mark_saved()
        view = matrix(app, window, scenario, record, keep_results=True, parameters={"digits": 6})
        check_report(app, view, work, record)
        if scenario.endswith("subgroup"):
            check_subgroup(view, record)
        else:
            assert view.results.details.count("Estimator:") == 5, view.results.details
        view.close()


def run_round5(app, window, work, record, prepare, only_bubbles=False):
    """Retain actual long figures and panel geometry through normal Qt/R routes."""
    from PyQt6 import QtCore
    from analysis_matrix import DATA_TYPES, run as matrix
    from rc_metastudio import r_bridge
    root = Path(__file__).resolve().parents[2]
    measurements = []
    for style in (() if only_bubbles else ("default", "revman", "bmj")):
        window.workspace.mark_saved()
        assert window.open(str(root / "sample_projects/Pignon2000-HR.rcms"), raise_on_error=True)
        prepare(window)
        for workflow in ("standard", "subgroup"):
            view = analyze_existing(app, window, workflow, "time_to_event.random", record,
                                    parameters={"fp_style": style})
            check_report(app, view, work, record)
            title, path = next(iter(view.results.display_images.items()))
            r_bridge.load_in_r(str(view.params_paths[title]) + ".plotdata")
            layout = json.loads(str(r_bridge.r_iterable_to_list(r_bridge.ro.r('jsonlite::toJSON(local({p <- RCMetaR:::rcmetar.forest.layout.preflight(plot.data); list(cex=p$typography$cex,height=p$metrics$height,rows=length(plot.data$slab))}),auto_unbox=TRUE)'))[0]))
            assert layout["rows"] == 65 and layout["cex"] >= 1.08, layout
            assert layout["height"] > 18, layout
            nodes = list(ET.parse(path).iter("{http://www.w3.org/2000/svg}text"))
            captions = ["".join(n.itertext()) for n in nodes]
            assert any(window.model.current_sheet.name in text for text in captions), captions[-5:]
            if workflow == "subgroup":
                for node in nodes:
                    if "".join(node.itertext()) not in {"A", "B"}:
                        continue
                    y = float(node.attrib["y"])
                    height = float(required(re.search(r"font-size:\s*([\d.]+)px", node.attrib["style"]))[1])
                    for rule in ET.parse(path).iter("{http://www.w3.org/2000/svg}line"):
                        if abs(float(rule.attrib["x2"]) - float(rule.attrib["x1"])) < 500 or abs(float(rule.attrib["y2"]) - float(rule.attrib["y1"])) > .01:
                            continue
                        assert not y-height < float(rule.attrib["y1"]) < y+height*.25, ("rule crosses subgroup heading", style, node.attrib, rule.attrib)
            study_names = {study.label for study in window.model.get_studies(only_if_included=True)}
            study_y = sorted({float(node.attrib["y"]) for node in nodes if "".join(node.itertext()) in study_names})
            row_gap = min(b-a for a, b in zip(study_y, study_y[1:]))
            polygon_heights = []
            for polygon in ET.parse(path).iter("{http://www.w3.org/2000/svg}polygon"):
                points = [float(value) for value in re.findall(r"[-+]?[\d.]+", polygon.attrib["points"])]
                polygon_heights.append(max(points[1::2])-min(points[1::2]))
            layout.update(row_spacing_px=row_gap, max_polygon_height_px=max(polygon_heights))
            assert max(polygon_heights) <= row_gap * .8, ("pooled polygon exceeds study row", style, workflow, layout)
            heading = next(s.title for s in view.results.sections if s.kind == "image" and s.source_key == title)
            view.nav_tree.setCurrentItem(view.nav_tree.findItems(heading, QtCore.Qt.MatchFlag.MatchExactly)[0])
            view.report_action.setChecked(False)
            view._show_report(False)
            app.processEvents()
            assert view.graphics_view.verticalScrollBar().maximum() > 0
            record("round5-long-figure", view, style=style, workflow=workflow, layout=layout, plots={title:path})
            view.graphics_view.verticalScrollBar().setValue(view.graphics_view.verticalScrollBar().maximum())
            record("round5-long-figure-bottom", view, style=style, workflow=workflow)
            destination = work / ("long-" + style + "-" + workflow + ".svg")
            view.plot_service.export(regenerator="forest", params_path=view.params_paths[title], output_path=str(destination))
            assert destination.is_file()
            check_interval_caps(destination)
            measurements.append(dict(style=style, workflow=workflow, **layout))
            view.close()
    if not only_bubbles:
        window.workspace.mark_saved()
        view = matrix(app, window, "analysis-data-twoarm-proportion", record, keep_results=True,
                      workflow_override="subgroup", parameters={"fp_style":"bmj", "digits":6}, prepare=prepare)
        check_report(app, view, work, record)
        check_subgroup(view, record)
        check_annotation_spacing(view)
        view.report_action.setChecked(False)
        view._show_report(False)
        view.graphics_view.verticalScrollBar().setValue(0)
        record("round5-bmj-binary-subgroup", view, plots=dict(view.results.display_images))
        view.close()
        record("round5-readable-type-matrix", window, measurements=measurements)
        return
    from rc_metastudio import meta_globals
    def add_dose(target):
        studies = target.model.get_studies(only_if_included=True)
        target.model.add_covariate("Dose", "continuous",
                                          {study.label: float(i) for i, study in enumerate(studies)})
        target.model.reset_model()
        target.enable_menu_options_that_require_dataset()
    def check_panel(view, family, metric):
        assert not re.search(r"(?<![\d.eE])-0\.0+(?![\d.eE])", view.report_text.toPlainText()), view.report_text.toPlainText()
        paths = list(view.results.display_images.items())
        exported = {}
        for title, _path in paths.copy():
            destination = work / ("bubble-" + family + "-" + str(metric).replace(" ", "-") + ".svg")
            view.plot_service.export(regenerator="regression", params_path=view.params_paths[title], output_path=str(destination))
            paths.append((title, str(destination)))
            exported[title] = str(destination)
        for title, path in paths:
            svg = ET.parse(path)
            point_group = next(group for group in svg.iter("{http://www.w3.org/2000/svg}g")
                               if group.find("{http://www.w3.org/2000/svg}circle") is not None)
            clip_id = point_group.attrib["clip-path"].removeprefix("url(#").removesuffix(")")
            frame = next(rect for clip in svg.iter("{http://www.w3.org/2000/svg}clipPath")
                         if clip.attrib["id"] == clip_id for rect in clip)
            top = float(frame.attrib["y"])
            bottom = top + float(frame.attrib["height"])
            for group in svg.iter("{http://www.w3.org/2000/svg}g"):
                for shape in list(group):
                    if shape.tag.rsplit("}",1)[-1] not in {"polyline", "polygon"} or "#2F5597" not in shape.attrib.get("style", "").upper():
                        continue
                    points = [float(value) for value in re.findall(r"[-+]?[\d.]+", shape.attrib["points"])]
                    if max(points[::2])-min(points[::2]) > float(frame.attrib["width"]) / 2:
                        assert group.attrib.get("clip-path") == point_group.attrib["clip-path"], ("bubble data layer lacks panel clipping", shape.attrib)
                        left = float(frame.attrib["x"])
                        assert min(points[::2]) >= left-.1 and max(points[::2]) <= left+float(frame.attrib["width"])+.1, ("bubble prediction outside selected range", metric, min(points[::2]), max(points[::2]), frame.attrib)
                for line in group.findall("{http://www.w3.org/2000/svg}line"):
                    style = line.attrib.get("style", "").upper()
                    if abs(float(line.attrib["y1"]) - float(line.attrib["y2"])) > .01:
                        continue
                    if any(color in style for color in ("#7F7F7F", "#808080", "#BEBEBE")):
                        assert top <= float(line.attrib["y1"]) <= bottom, ("null outside panel", line.attrib, frame.attrib)
                        assert group.attrib.get("clip-path") == point_group.attrib["clip-path"], ("null guide lacks panel clipping", line.attrib)
            assert any(window.model.current_sheet.name in "".join(n.itertext()) for n in svg.iter("{http://www.w3.org/2000/svg}text"))
        record("round5-bubble-bounds", view, family=family, metric=metric,
               explicit_x=[1,4], plots=dict(view.results.display_images), exports=exported)
    cases = [(family, None) for family in DATA_TYPES if family != "diagnostic"]
    cases += [("onearm-proportion", metric) for metric in meta_globals.BINARY_ONE_ARM_METRICS if metric != "PR"]
    cases += [("twoarm-proportion", metric) for metric in meta_globals.BINARY_TWO_ARM_METRICS if metric != "OR"]
    for family, metric in cases:
        window.workspace.mark_saved()
        def prepare_metric(target):
            if metric:
                menu = target.oneArmMetricMenu if family == "onearm-proportion" else target.twoArmMetricMenu
                next(action for action in menu.actions() if action.data() == metric).trigger()
                app.processEvents()
            add_dose(target)
        view = matrix(app, window, "analysis-data-" + family, record, keep_results=True,
                      workflow_override="meta-regression", parameters={"digits":6, "bp_plot_lb":"1", "bp_plot_ub":"4"},
                      prepare=prepare_metric)
        check_panel(view, family, metric or window.model.current_effect)
        view.close()
    for family, sample in (("time_to_event", "Pignon2000-HR"), ("event_rates", "NielWeise2008-IRR")):
        window.workspace.mark_saved()
        assert window.open(str(root / "sample_projects" / (sample + ".rcms")), raise_on_error=True)
        add_dose(window)
        view = analyze_existing(app, window, "meta-regression", family + ".random", record,
                                parameters={"bp_plot_lb":"1", "bp_plot_ub":"4"})
        view.report_action.setChecked(False)
        view._show_report(False)
        check_panel(view, family, window.model.current_effect)
        view.close()
    record("round5-bubble-metric-matrix", window, cases=len(cases)+2)


def run_irr_context(app, window, record):
    root = Path(__file__).resolve().parents[2]
    for style in ("default", "revman", "bmj"):
        window.workspace.mark_saved()
        assert window.open(str(root / "sample_projects/NielWeise2008-IRR.rcms")), style
        view = analyze_existing(app, window, "standard", "event_rates.random", record, parameters={"fp_style":style})
        check_annotation_spacing(view)
        title, path = next(iter(view.results.display_images.items()))
        from rc_metastudio.analysis_identity import dataset_identity
        check_caption(path, dataset_identity(window.model))
        labels = ["".join(node.itertext()) for node in ET.parse(path).iter("{http://www.w3.org/2000/svg}text")]
        assert all(label == label.strip() for label in labels if re.fullmatch(r"\s*[-+\d.]+\s*", label)), labels
        assert "Events" in labels and any("Person-time" in label for label in labels), labels
        unit = window.model.get_current_analysis_unit_for_study(0).ratio_input(window.model.arm_names).unit
        assert any(unit in label for label in labels), (unit, labels)
        svg = ET.parse(path)
        nodes = list(svg.iter("{http://www.w3.org/2000/svg}text"))
        first_study = min(float(node.attrib["y"]) for node in nodes if "Bong" in "".join(node.itertext()))
        headers = [node for node in nodes if float(node.attrib["y"]) < first_study - 5]
        def header_box(node):
            x, y = float(node.attrib["x"]), float(node.attrib["y"])
            width = float(node.attrib["textLength"].removesuffix("px"))
            height = float(required(re.search(r"font-size:\s*([\d.]+)px", node.attrib["style"]))[1]) * .8
            anchor = node.attrib.get("text-anchor", "start")
            left = x - (width if anchor == "end" else width/2 if anchor == "middle" else 0)
            return left, left+width, y-height, y
        for index, node in enumerate(headers):
            a = header_box(node)
            for other in headers[index+1:]:
                b = header_box(other)
                if min(a[1],b[1])-max(a[0],b[0]) > 1:
                    assert a[2]-b[3] >= 1 or b[2]-a[3] >= 1, ("IRR header collision", style, "".join(node.itertext()), "".join(other.itertext()), a, b)
        for node in nodes:
            if "Heterogeneity:" in "".join(node.itertext()) or "Test for overall effect" in "".join(node.itertext()) or "prediction interval:" in "".join(node.itertext()):
                assert "font-weight: bold" not in node.attrib["style"], node.attrib
        for node in svg.iter("{http://www.w3.org/2000/svg}text"):
            if "Person-time" not in "".join(node.itertext()):
                continue
            x, y = float(node.attrib["x"]), float(node.attrib["y"])
            height = float(required(re.search(r"font-size:\s*([\d.]+)px", node.attrib["style"]))[1])
            for line in svg.iter("{http://www.w3.org/2000/svg}line"):
                if abs(float(line.attrib["y1"]) - float(line.attrib["y2"])) < .01:
                    left, right = sorted((float(line.attrib["x1"]), float(line.attrib["x2"])))
                    assert not (left <= x <= right and y-height < float(line.attrib["y1"]) < y + height * .25), ("rule crosses exposure header", node.attrib, line.attrib)
        raw = window.model.get_current_raw_data()
        totals = [str(sum(column)) for column in zip(*raw, strict=True)]
        weight = next(node for node in nodes if "".join(node.itertext()) in {"100.0%", "100.0"})
        pooled = [node for node in nodes if abs(float(node.attrib["y"]) - float(weight.attrib["y"])) < 3]
        pooled_text = ["".join(node.itertext()) for node in pooled]
        assert all(total in pooled_text for total in totals), (style, totals, pooled_text)
        assert all("font-weight: bold" in node.attrib["style"] for node in pooled if "".join(node.itertext()) in totals), pooled_text
        destination = Path(path).parent / ("irr-context-" + style + ".svg")
        view.plot_service.export(regenerator="forest", params_path=view.params_paths[title], output_path=str(destination))
        assert unit in destination.read_text()
        check_caption(destination, dataset_identity(window.model))
        view.report_action.setChecked(False)
        view._show_report(False)
        record("round5-irr-context", view, style=style, unit=unit, raw=window.model.get_current_raw_data(), plots={title:path}, exports={"svg":str(destination)})
        view.close()
