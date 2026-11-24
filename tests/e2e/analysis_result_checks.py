"""Analysis report, method reference, heterogeneity and subgroup checks."""

from tests.e2e import r_oracle

import json
import math
from unittest.mock import patch
from xml.etree import ElementTree as ET
from tests.e2e.plot_observations import load_serialized_object


def _display_number(cell):
    return float(cell.replace("−", "-").replace(",", "").rstrip("%"))


def check_report(app, view, work, record):
    from rc_metastudio.results import window as results_window
    from rc_metastudio.results.formatting import report_numbers

    assert "Model configuration\n" in view.manuscript_text.toPlainText()
    scene_text = [item.toPlainText() for item in view.scene.items() if hasattr(item, "toPlainText")]
    for section in view.results.sections:
        if section.source_key == "Weights":
            assert section.value not in scene_text, "legacy scene weights remain"

    view.manuscript_text.selectAll()
    view.manuscript_text.copy()
    copied = app.clipboard().text()
    assert copied.startswith("Methods\n"), copied
    for paragraph in (view.manuscript.methods, view.manuscript.results):
        assert report_numbers(paragraph).replace("\u00a0", " ") in copied.replace("\u00a0", " ")
    from tests.e2e.report_retention import assert_report
    assert_report(view)

    if "Omission-only fits:" in view.results.details:
        assert copied.count("Omission-only fits:") == 1, copied
    for line in view.results.details.splitlines():
        if line.startswith(("Order:", "Each row", "Subgroups defined by", "Moderators:")):
            assert line in copied, (line, copied)
    output = work / "round3-report.pdf"
    with patch.object(results_window.QFileDialog, "getSaveFileName", return_value=(str(output), "PDF (*.pdf)")):
        view.export_report_action.trigger()
    assert output.read_bytes().startswith(b"%PDF")
    assert app.clipboard().mimeData().hasHtml()
    cursor = view.manuscript_text.textCursor()
    cursor.clearSelection()
    view.manuscript_text.setTextCursor(cursor)
    view.report_action.setChecked(True)
    app.processEvents()
    record("round3-report-copy-export", view, identity=view.results.identity,
           text=copied, tables=[dict(title=t.title, headers=t.headers, rows=t.rows)
                               for s in view.results.sections for t in s.tables])


def check_fixed_references(view, record, method="IV"):
    report = view.manuscript_text.toPlainText()
    assert "Random-effects meta-analysis:" not in report, report
    assert "Random-effects meta-regression:" not in report, report
    expected = {"IV": "Cochran, W. G. (1954).",
                "MH": "Mantel, N., & Haenszel, W. (1959).", "PETO": "Yusuf, S., Peto, R., Lewis, J., Collins, R., & Sleight, P. (1985)."}[method]
    assert expected in report, report
    previous = view.report_action.isChecked()
    view.report_action.setChecked(True)
    view.manuscript_text.verticalScrollBar().setValue(view.manuscript_text.verticalScrollBar().maximum())
    record("round3-fixed-references", view, method=method, identity=view.results.identity, text=report)
    view.manuscript_text.verticalScrollBar().setValue(0)
    view.report_action.setChecked(previous)


def check_standard_heterogeneity(view, record):
    tables = [t for s in view.results.sections for t in s.tables if t.title.endswith("Heterogeneity")]
    assert tables, "Expected heterogeneity tables for standard analysis"
    for table, (title, path) in zip(tables, view.results.display_images.items(), strict=True):
        load_serialized_object(str(view.params_paths[title]) + ".plotdata")
        expected = json.loads(str(list(r_oracle.evaluate('''jsonlite::toJSON(local({
          fit <- plot.data$res
          direct <- metafor::rma.uni(yi=fit$yi, vi=fit$vi, method=fit$method, test=fit$test, level=fit$level)
          list(data_type=plot.data$data_type, Q=direct$QE, df=direct$k-direct$p, p=direct$QEp, I2=direct$I2, tau2=direct$tau2,
               random=!direct$method %in% c("FE", "EE", "CE"))
        }), auto_unbox=TRUE, digits=16)'''))[0]))
        assert table.headers == ("Q", "df", "P value", "I²") + (("τ²",) if expected["random"] else ()), table
        keys = ("Q", "df", "p", "I2") + (("tau2",) if expected["random"] else ())
        for cell, key in zip(table.rows[0], keys, strict=True):
            if cell.startswith("<"):
                assert expected[key] < _display_number(cell[1:]), (cell, expected)
            else:
                assert abs(_display_number(cell)-expected[key]) <= (.05001 if key == "I2" else 5.01e-7), (cell, expected)
        if expected["data_type"] in {"binary", "continuous"}:
            weights = next(t for section in view.results.sections for t in section.tables if t.title == "Study weights")
            assert weights.headers == ("Study", "Effect", "Lower bound", "Upper bound", "Weight (%)"), weights
            assert weights.rows and all(len(row) == 5 and row[0] and row[4].endswith("%") for row in weights.rows), weights
            assert all(_display_number(row[2]) <= _display_number(row[1]) <= _display_number(row[3]) for row in weights.rows), weights
        assert "Pooled " in view.manuscript_text.toPlainText(), view.manuscript_text.toPlainText()
        assert "Calculation scale: log - estimate" not in view.manuscript_text.toPlainText()
        record("round3-standard-heterogeneity-public-reference", view, expected=expected,
               headers=table.headers, rows=table.rows, plots={title: path})


def check_subgroup(view, record):

    def compare(cell, expected, tolerance):
        if expected is None:
            assert cell == "", cell
        elif cell.startswith("<"):
            assert expected < _display_number(cell[1:]), (cell, expected)
        else:
            assert abs(_display_number(cell) - expected) <= tolerance, (cell, expected)

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
        load_serialized_object(str(view.params_paths[title]) + ".plotdata")
        reference = json.loads(str(list(r_oracle.evaluate('''jsonlite::toJSON(local({
          fits <- plot.data$regeneration_state$subgroup_data$results
          lapply(fits, function(fit) {
            direct <- metafor::rma.uni(yi=fit$yi, vi=fit$vi, method=fit$method, test=fit$test, level=fit$level)
            pi <- if (!direct$method %in% c("FE", "EE", "CE") && direct$k > 2) stats::predict(direct) else NULL
            list(k=direct$k, Q=direct$QE, df=direct$k-direct$p, p=direct$QEp, I2=direct$I2,
                 tau2=direct$tau2, z=direct$zval, lower=pi$pi.lb, upper=pi$pi.ub, measure=plot.data$params$measure)
          })
        }), auto_unbox=TRUE, digits=16, null="null")'''))[0]))
        weights = json.loads(str(list(r_oracle.evaluate('''jsonlite::toJSON(local({
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
        model, heterogeneity = tables["Model results"], tables["Heterogeneity"]
        assert "k" in model.headers
        assert all(h in heterogeneity.headers for h in ("Q", "df", "P value", "I²"))
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


def authority(
    window,
    family,
    estimator,
    inference,
    confidence,
    correction="only0",
    entered=None,
    metric=None,
):
    """Public metafor reconstruction uses observed input, never RCMS preparation."""

    rows = window.model.get_current_raw_data()
    vector = lambda i: (
        "c("
        + ",".join("NA_real_" if row[i] in (None, "") else str(row[i]) for row in rows)
        + ")"
    )
    metric = metric or window.model.current_effect
    if family == "binary":
        expression = (
            f'metafor::escalc("{metric}", xi={vector(0)}, ni={vector(1)}, add=.5, to="{correction}")'
            if metric in {"PR", "PLN", "PLO", "PAS", "PFT"}
            else f'metafor::escalc("{metric}", ai={vector(0)}, n1i={vector(1)}, ci={vector(2)}, n2i={vector(3)}, add=.5, to="{correction}", drop00=FALSE)'
        )
    elif family == "continuous":
        expression = (
            f'metafor::escalc("MN", ni={vector(0)}, mi={vector(1)}, sdi={vector(2)})'
            if metric == "Mean"
            else f'metafor::escalc("{metric}", n1i={vector(0)}, m1i={vector(1)}, sd1i={vector(2)}, n2i={vector(3)}, m2i={vector(4)}, sd2i={vector(5)})'
        )
    elif metric in {"Sens", "Spec"}:
        events, other = (0, 1) if metric == "Sens" else (3, 2)
        correction_mask = f"({vector(0)}*{vector(1)}*{vector(2)}*{vector(3)} == 0)"
        expression = f'metafor::escalc("PLO", xi={vector(events)}+.5*{correction_mask}, ni={vector(events)}+{vector(other)}+{correction_mask}, add=0)'
    else:
        expression = f'metafor::escalc("OR", ai={vector(0)}, bi={vector(1)}, ci={vector(2)}, di={vector(3)}, add=.5, to="only0", drop00=FALSE)'
    override = (
        ""
        if entered is None
        else f"e$yi[1] <- {entered[0]}; e$vi[1] <- {entered[1] ** 2}; "
    )
    point, lower, upper = "as.numeric(f$b)", "f$ci.lb", "f$ci.ub"
    if metric == "PFT":
        point, lower, upper = (
            f"metafor::transf.ipft.hm({value}, targs=list(ni={vector(1)}))"
            for value in (point, lower, upper)
        )
    result = r_oracle.evaluate(
        "{ e <- "
        + expression
        + "; "
        + override
        + 'f <- metafor::rma.uni(e$yi, vi=e$vi, method="'
        + estimator
        + '", test="'
        + inference
        + '", level='
        + str(confidence)
        + f"); jsonlite::toJSON(list(estimate={point}, lower_bound={lower}, upper_bound={upper}, standard_error=f$se, p_value=f$pval, q=f$QE, heterogeneity_p_value=f$QEp, tau_squared=f$tau2), auto_unbox=TRUE, digits=16) }}"
    )
    return json.loads(str(result[0]))


def compare_authority(view, expected, family, record, metric=None):
    from tests.analysis_regression.golden.support.golden_analysis import (
        parsed_numeric_sections,
    )

    sections = parsed_numeric_sections(view.results)
    diagnostic_summaries = {
        "Sens": "Sensitivity summary", "Spec": "Specificity summary",
        "DOR": "Diagnostic odds ratio summary",
    }
    actual = sections[diagnostic_summaries[metric or "DOR"] if family == "diagnostic" else "Summary"]
    for key, value in expected.items():
        observed_key = (
            "calculation_scale." + key
            if (family == "diagnostic" or (family == "binary" and metric not in {"PR", "PFT"}))
            and key in ("estimate", "lower_bound", "upper_bound", "standard_error")
            else key
        )
        assert observed_key in actual, (observed_key, actual)
        assert abs(actual[observed_key] - value) <= 1e-6 + 1e-12, (
            key,
            actual[observed_key],
            value,
        )
    record(
        "nondefault-public-authority",
        view,
        actual=actual,
        expected=expected,
        oracle="metafor::escalc + rma.uni",
        tolerance=1e-6,
    )
