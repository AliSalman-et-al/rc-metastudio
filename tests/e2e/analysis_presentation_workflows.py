"""Real analysis setup and presentation workflows across data families."""

import json
import math
import re
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
from tests.python.gui.qt_test_support import required
from tests.e2e.analysis_result_checks import (
    check_fixed_references,
    check_report,
    check_standard_heterogeneity,
    check_subgroup,
)
from tests.e2e.plot_geometry_checks import (
    check_annotation_spacing,
    check_bubble_ticks,
    check_caption,
    check_excluding_null,
    check_interval_caps,
    check_sequential,
)


def analyze_existing(app, window, workflow, method, record, parameters=None):
    from PyQt6 import QtCore, QtWidgets
    from rc_metastudio import analysis_setup_dialog, results_window
    from rc_metastudio.subgroup_analysis_dialog import SubgroupAnalysisDialog
    from analysis_matrix import set_parameter
    from tests.python.gui.qt_test_support import mouse_click

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
    from tests.e2e.keyboard_navigation import keyboard_traversal
    parameter_controls = [control for control in dialog.current_widgets if control.focusPolicy() & QtCore.Qt.FocusPolicy.TabFocus]
    keyboard_traversal(app, dialog, [dialog.method_cbo_box, *parameter_controls,
                       dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok),
                       dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel)], record, "setup")
    if workflow == "meta-regression":
        from tests.e2e.keyboard_navigation import keyboard_dialog_pages
        keyboard_dialog_pages(app, dialog, record)
    record("round3-configured", dialog, workflow=workflow, method=method, parameters=dialog.current_param_vals)
    mouse_click(dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok), QtCore.Qt.MouseButton.LeftButton)
    app.processEvents()
    view = visible(results_window.ResultsWindow)
    view.resize(1500, 850)
    app.processEvents()
    return view


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
                    check_annotation_spacing(view, style=style)
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
                            from tests.e2e.report_retention import assert_report
                            pooled, _fit = assert_report(view)
                            assert len(pooled.rows) == 1 and pooled.rows[0][0] == 'Proportion'
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
            numeric = [node for node in svg.iter("{http://www.w3.org/2000/svg}text")
                       if node.attrib.get("text-anchor") == "middle"
                       and re.fullmatch(r"[-+\d.]+(?:e[-+]\d+)?", "".join(node.itertext()))]
            axis_y = max(float(node.attrib["y"]) for node in numeric)
            axis = [node for node in numeric if abs(float(node.attrib["y"]) - axis_y) < .01]
            ticks = {float("".join(node.itertext())) for node in axis}
            assert len(ticks) >= 2 and len(ticks) == len(axis), (ticks, axis)
            assert all(value != 0 and math.isfinite(value) for value in ticks), ticks
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
        from tests.python.gui.qt_test_support import mouse_click
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
            if style != "bmj":
                check_interval_caps(destination)
            measurements.append(dict(style=style, workflow=workflow, **layout))
            view.close()
    if not only_bubbles:
        window.workspace.mark_saved()
        view = matrix(app, window, "analysis-data-twoarm-proportion", record, keep_results=True,
                      workflow_override="subgroup", parameters={"fp_style":"bmj", "digits":6}, prepare=prepare)
        check_report(app, view, work, record)
        check_subgroup(view, record)
        check_annotation_spacing(view, style="bmj")
        view.report_action.setChecked(False)
        view._show_report(False)
        view.graphics_view.verticalScrollBar().setValue(0)
        record("round5-bmj-binary-subgroup", view, plots=dict(view.results.display_images))
        view.close()
        record("round5-readable-type-matrix", window, measurements=measurements)
        return
    from rc_metastudio import analysis_catalog
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
    cases += [("onearm-proportion", metric) for metric in analysis_catalog.BINARY_ONE_ARM_METRICS if metric != "PR"]
    cases += [("twoarm-proportion", metric) for metric in analysis_catalog.BINARY_TWO_ARM_METRICS if metric != "OR"]
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
        view = analyze_existing(app, window, "standard", "event_rates.random", record,
                                parameters={"fp_style":style, "fp_show_col3":True, "fp_show_col4":True})
        check_annotation_spacing(view, style=style)
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
