"""Round-three report and sequential figure contracts through real Qt and R."""

import json
import math
import re
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET


def check_report(app, view, work, record):
    from rc_metastudio import results_window

    assert view.report_text.toPlainText().startswith("Model configuration\n")
    view.copy_report_action.trigger()
    copied = app.clipboard().text()
    assert copied.startswith(view.results.identity + "\n"), copied
    for section in view.results.sections:
        for table in section.tables:
            assert "\t".join(table.headers) in copied, (table.title, copied)
            for row in table.rows:
                assert "\t".join(row) in copied, (table.title, row, copied)
    output = work / "round3-report.txt"
    with patch.object(results_window.QFileDialog, "getSaveFileName", return_value=(str(output), "Text report (*.txt)")):
        view.export_report_action.trigger()
    assert output.read_text(encoding="utf-8") == copied
    if "Omission-only fits:" in view.results.details:
        assert copied.count("Omission-only fits:") == 1, copied
        assert "\nleave-one-out\n" not in copied, copied
    if "\nSensitivity\n" in view.results.details:
        for line in view.results.details.splitlines():
            if line.startswith(("Order:", "Each row", "Subgroups by", "Moderators:")):
                assert view.results.details.index(line) < view.results.details.index("\nSensitivity\n"), view.results.details
                assert copied.index(line) < copied.index("\nSensitivity\n"), copied
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
          list(Q=direct$QE, df=direct$k-direct$p, p=direct$QEp, I2=direct$I2, tau2=direct$tau2,
               random=!direct$method %in% c("FE", "EE", "CE"))
        }), auto_unbox=TRUE, digits=16)'''))[0]))
        assert table.headers == ("Q", "df", "p-value", "I²") + (("τ²",) if expected["random"] else ()), table
        for cell, key in zip(table.rows[0], ("Q", "df", "p", "I2", "tau2")):
            if cell.startswith("<"):
                assert expected[key] < float(cell[1:]), (cell, expected)
            else:
                assert abs(float(cell.rstrip("%"))-expected[key]) <= (.05001 if key == "I2" else 5.01e-7), (cell, expected)
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
        if data["measure"] in {"OR", "RR", "HR", "IRR", "MD", "SMD"} and data["range"][0] <= 0 <= data["range"][1]:
            null = 1 if data["measure"] in {"OR", "RR", "HR", "IRR"} else 0
            ticks = [float(node.attrib["x"]) for node in svg.iter("{http://www.w3.org/2000/svg}text")
                     if node.attrib.get("text-anchor") == "middle" and "".join(node.itertext()).strip() in {str(null), f"{null:.1f}", f"{null:.2f}"}]
            lines = [node.attrib for node in svg.iter("{http://www.w3.org/2000/svg}line")]
            assert ticks and any(abs(float(line["x1"]) - float(line["x2"])) < .01
                                 and abs(float(line["y1"]) - float(line["y2"])) > 50
                                 and any(abs(float(line["x1"]) - tick) < .02 for tick in ticks)
                                 for line in lines), (title, null, ticks, lines)
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
              "leave-one-out": window.action_loo_ma, "subgroup": window.action_subgroup_ma}[workflow]
    action.trigger()
    app.processEvents()
    if workflow == "subgroup":
        subgroup = visible(SubgroupAnalysisDialog)
        subgroup.covariate_combo_box.setCurrentIndex(subgroup.covariate_combo_box.findText("Group"))
        mouse_click(subgroup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok), QtCore.Qt.MouseButton.LeftButton)
    dialog = visible(analysis_setup_dialog.AnalysisSetupDialog)
    dialog.method_cbo_box.setCurrentText(next(label for label, key in dialog.available_method_d.items() if key == method))
    app.processEvents()
    for key, value in {"digits": 6, **(parameters or {})}.items():
        set_parameter(app, dialog, key, value)
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
                else:
                    assert value in {.001, .005, .01, .05, .1, .25, .5, .75, .9, .95, .99, .995, .999}, ("non-round proportion tick", label)
                ticks.append((value, float(node.attrib["y"])))
            except ValueError:
                pass
        assert 3 <= len(ticks) <= 8, ticks
        bubble_group = next(group for group in svg.iter("{http://www.w3.org/2000/svg}g")
                            if group.find("{http://www.w3.org/2000/svg}circle") is not None)
        clip_id = bubble_group.attrib["clip-path"].removeprefix("url(#").removesuffix(")")
        frames = [rect.attrib for clip in svg.iter("{http://www.w3.org/2000/svg}clipPath")
                  if clip.attrib["id"] == clip_id for rect in clip]
        assert len(frames) == 1, frames
        height = float(frames[0]["height"])
        coverage = (max(y for _, y in ticks) - min(y for _, y in ticks)) / height
        assert coverage >= .55, (ticks, frames[0], coverage)
        positions = sorted(y for _, y in ticks)
        assert min(b-a for a, b in zip(positions, positions[1:])) >= 12, ticks
        record("round3-bubble-tick-coverage", view, ticks=ticks, plot_frame=frames[0], coverage=coverage,
               metric=metric, plots=dict(view.results.display_images))



def run(app, window, work, record, scenario):
    from analysis_matrix import DATA_TYPES, run as matrix
    from rc_metastudio.analysis_dataset import Covariate

    def prepare(target):
        studies = target.model.get_studies(only_if_included=True)
        target.model.dataset.add_covariate(Covariate("Group", "factor"),
                                          {s.name: "A" if i % 2 else "B" for i, s in enumerate(studies)})
        target.model.reset_model()
        target.enable_menu_options_that_require_dataset()

    family_name = scenario.removeprefix("audit-round3-")
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
            for title, path in view.results.display_images.items():
                r_bridge.load_in_r(str(view.params_paths[title]) + ".plotdata")
                bounds = list(r_bridge.ro.r('RCMetaR:::rcmetar.forest.layout.preflight(plot.data)$x$alim'))
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
        for metric in ("OR", "PLO"):
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
                    studies = target.model.get_studies(only_if_included=True)
                    assert len(studies) == 6, studies
                    target.model.dataset.add_covariate(Covariate("Dose", "continuous"),
                                                      {s.name: float(i) for i, s in enumerate(studies)})
                    target.model.reset_model()
                    target.enable_menu_options_that_require_dataset()
                    record("round3-proportion-input", target, metric=target.model.current_effect,
                           raw=target.model.get_current_raw_data(),
                           effects=target.model.get_current_estimates_and_standard_errors(),
                           raw_complete=target.model.included_studies_have_raw_data())
            view = matrix(app, window, "analysis-amino-binary-meta-regression" if metric == "OR" else "analysis-data-onearm-proportion",
                          record, keep_results=True, workflow_override="meta-regression",
                          parameters={"digits": 3}, prepare=select_metric)
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
        prepare(window)
        model = window.model
        assert model.setData(model.index(1, model.INCLUDE_STUDY), QtCore.Qt.CheckState.Unchecked, QtCore.Qt.ItemDataRole.CheckStateRole)
        record("round3-ratio-excluded-study", window, family=family, excluded=model.dataset.studies[1].name)
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
            for row in range(len(model.dataset.studies)):
                assert model.setData(model.index(row, model.RAW_DATA[0]), "3" if row == 0 else "0")
            view = analyze_existing(app, window, "leave-one-out", "event_rates.mh", record)
            check_report(app, view, work, record)
            check_sequential(view, "leave-one-out", record)
            assert "Non-estimable" in view.report_text.toPlainText()
            view.close()
        window.workspace.mark_saved()
        assert window.open(str(root / "sample_projects" / (sample + ".rcms")), raise_on_error=True)
        prepare(window)
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
