"""Analysis report, method reference, heterogeneity and subgroup checks."""

import json
import math
from unittest.mock import patch
from xml.etree import ElementTree as ET


def check_report(app, view, work, record):
    from rc_metastudio import results_window

    assert "Model configuration\n" in view.report_text.toPlainText()
    scene_text = [item.toPlainText() for item in view.scene.items() if hasattr(item, "toPlainText")]
    for section in view.results.sections:
        if section.source_key == "Weights":
            assert section.value not in scene_text, "legacy scene weights remain"

    view.copy_report_action.trigger()
    copied = app.clipboard().text()
    assert copied.startswith(view.manuscript.title + "\n"), copied
    assert view.manuscript.methods in copied and view.manuscript.results in copied
    from tests.e2e.manuscript_export import assert_manuscript_tables
    assert_manuscript_tables(view)

    if "Omission-only fits:" in view.results.details:
        assert copied.count("Omission-only fits:") == 1, copied
    for line in view.results.details.splitlines():
        if line.startswith(("Order:", "Each row", "Subgroups by", "Moderators:")):
            assert line in copied, (line, copied)
    output = work / "round3-report.pdf"
    with patch.object(results_window.QFileDialog, "getSaveFileName", return_value=(str(output), "PDF (*.pdf)")):
        view.export_report_action.trigger()
    assert output.read_bytes().startswith(b"%PDF")
    assert app.clipboard().mimeData().hasHtml()
    view.report_action.setChecked(True)
    app.processEvents()
    record("round3-report-copy-export", view, identity=view.results.identity,
           text=copied, tables=[dict(title=t.title, headers=t.headers, rows=t.rows)
                               for s in view.results.sections for t in s.tables])


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
            assert weights.headers == ("Study", "Effect", "Lower bound", "Upper bound", "Weight (%)"), weights
            assert weights.rows and all(len(row) == 5 and row[0] and row[4].endswith("%") for row in weights.rows), weights
            assert all(float(row[2]) <= float(row[1]) <= float(row[3]) for row in weights.rows), weights
        assert "Pooled " in view.report_text.toPlainText(), view.report_text.toPlainText()
        assert "Calculation scale: log - estimate" not in view.report_text.toPlainText()
        record("round3-standard-heterogeneity-public-reference", view, expected=expected,
               headers=table.headers, rows=table.rows, plots={title: path})


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
