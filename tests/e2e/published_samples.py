"""Compare bundled project results with direct fits of the retained source rows."""

from tests.e2e import r_oracle

import hashlib
import json
from pathlib import Path
import re
from unittest.mock import patch
from xml.etree import ElementTree

from PyQt6 import QtCore, QtWidgets
from rc_metastudio.analysis.diagnostic_metrics_dialog import DiagnosticMetricsDialog
from rc_metastudio.analysis.setup_dialog import AnalysisSetupDialog
from rc_metastudio.analysis.small_study_effects_dialog import SmallStudyEffectsDialog
from rc_metastudio.analysis.subgroup_dialog import SubgroupAnalysisDialog
from rc_metastudio.analysis.trial_sequential_dialog import TrialSequentialAnalysisDialog

from rc_metastudio.results.window import ResultsWindow
from tests.analysis_regression.golden.support.golden_analysis import parsed_numeric_sections
from tests.python.gui.qt_test_support import metric_action, required, wait


def run(app, window, work, root, record, analyze, *, example):
    from tests.e2e.dialog_interaction import modal
    from tests.e2e.dialog_interaction import set_parameter

    samples = root / "sample_projects"
    manifest = json.loads((samples / "manifest.json").read_text(encoding="utf-8"))
    entry = next(item for item in manifest["projects"] if f", {example.title()} " in item["file"])
    filename = entry["file"]
    source = samples / entry["source_file"]
    path = samples / filename
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == entry["source_sha256"]
    next(action for action in window.sample_menu.actions() if action.data() == filename).trigger()
    assert window.workspace.path == path
    assert len(window.model.current_sheet.rows) == entry["study_count"]
    record("published-sample-opened", window, sample=filename, exports={"project": str(path), "source": str(source)})
    from rc_metastudio.project.archive import load_project
    canonical = json.dumps(load_project(path).project, ensure_ascii=False, allow_nan=False,
                           sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256((canonical + "\n").encode()).hexdigest() == entry["semantic_sha256"]
    authority = (root / "tests/e2e/published_sample_authority.R").read_text(encoding="utf-8")

    def expected_fit(metric, method, estimator, inference="z", sheet=0, correction="only0",
                     workflow="standard", moderators=""):
        return json.loads(str(r_oracle.apply(authority, str(source), example, metric, method, estimator,
                                        inference, sheet, .5, correction, workflow, moderators)[0]))

    def select_metric(metric):
        if window.model.current_effect != metric:
            metric_action(window.menuMetric, metric).trigger()
            assert window.model.current_effect == metric

    def visible(kind):
        app.processEvents()
        widgets = [widget for widget in app.topLevelWidgets()
                   if isinstance(widget, kind) and widget.isVisible()]
        assert len(widgets) == 1, (kind.__name__, widgets)
        return widgets[0]

    def accept(dialog, buttons):
        button = required(buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
        assert button.isEnabled(), dialog.windowTitle()
        button.click()
        app.processEvents()

    def record_results(view, workflow, observed, expected, **context):
        if workflow not in {"deeks", "small-study", "reitsma"}:
            view.report_action.trigger()
        app.processEvents()
        record("published-" + workflow + "-reference", view, sample=filename, observed=observed,
               expected=expected, plots=dict(view.results.display_images), **context)
        view.close()
        app.processEvents()

    def pooled(metric, method, *, estimator="FE", inference="z", sheet=0, correction="only0"):
        diagnostic = example == "kearon"
        if not diagnostic:
            select_metric(metric)
        parameters = {}
        if inference != "z":
            parameters["inference.method"] = inference
        if correction != "only0":
            parameters["to"] = correction
        likelihood = diagnostic and metric == "LR"
        metrics = ("PLR", "NLR") if likelihood else (metric,)
        references = {measure: expected_fit(measure, method, estimator, inference, sheet, correction)
                      for measure in metrics}
        view = analyze(app, window, method, digits=4, estimator=estimator if method.endswith(".random") else None,
                       diagnostic_metrics=(("lr" if likelihood else metric.lower()),) if diagnostic else None,
                       parameters=parameters)
        sections = parsed_numeric_sections(view.results)
        observed = {}
        for measure, expected in references.items():
            prefix = {"PLR": "positive likelihood ratio", "NLR": "negative likelihood ratio"}.get(measure, "")
            summary = next(value for title, value in sections.items()
                           if "estimate" in value and title.casefold().startswith(prefix))
            for field in ("estimate", "lower_bound", "upper_bound"):
                assert abs(summary[field] - expected[field]) <= 0.000051, (measure, method, summary, expected)
            if not likelihood and expected["contributing"] < entry["study_count"]:
                assert view.results.contributing_studies == expected["contributing"], expected
            observed[measure] = summary
        record_results(view, "pooled", observed, references, metric=metric, method=method, estimator=estimator,
                       inference=inference, correction=correction)

    def repeated(workflow, metric, method, *, factor="", moderators=(), formula="", estimator="REML",
                 check_plot=None):
        diagnostic = example == "kearon"
        regression = workflow == "meta-regression"
        if not diagnostic:
            select_metric(metric)
        expected = expected_fit(metric, method, estimator, workflow=workflow, moderators=formula)
        action = {"cumulative": window.action_cum_ma, "leave-one-out": window.action_loo_ma,
                  "subgroup": window.action_subgroup_ma, "meta-regression": window.action_meta_regression}[workflow]
        assert action.isEnabled()
        action.trigger()
        if factor:
            chooser = visible(SubgroupAnalysisDialog)
            chooser.covariate_combo_box.setCurrentText(factor)
            accept(chooser, chooser.buttonBox)
        if diagnostic and not regression:
            chooser = visible(DiagnosticMetricsDialog)
            for key in chooser.SELECTABLE_METRICS:
                chooser._metric_checkbox(key).setChecked(key == metric.lower())
            chooser.btn_ok.click()
        setup = visible(AnalysisSetupDialog)
        if regression:
            if estimator == "FE":
                setup.fixed_effects_radio.setChecked(True)
            for cov, checkbox in setup.covs_and_check_boxes:
                checkbox.setChecked(cov["name"] in moderators)
        else:
            index = setup.method_cbo_box.findData(method)
            assert index >= 0, method
            setup.method_cbo_box.setCurrentIndex(index)
        if method == "diagnostic.reitsma":
            set_parameter(app, setup, "estimator", estimator)
        elif estimator != "FE":
            set_parameter(app, setup, "rm.method", estimator)
        set_parameter(app, setup, "digits", 4)
        record("published-workflow-configured", setup, sample=filename, workflow=workflow,
               metric=metric, estimator=estimator, factor=factor, moderators=moderators)
        accept(setup, setup.buttonBox)
        view = visible(ResultsWindow)
        if check_plot is not None:
            check_plot(view)
        roles = {"estimate": "estimate", "lower_bound": "ci_lower", "upper_bound": "ci_upper"}
        if regression and diagnostic:
            actual = {}
            for side, references in expected.items():
                lines = view.texts[f"{side} coefficients"].replace("−", "-").splitlines()
                head = next(i for i, line in enumerate(lines) if "odds ratio" in line.casefold())
                columns = ["term", *re.split(r"\s{2,}", lines[head].strip().casefold())]
                indexes = [columns.index(label) for label in ("odds ratio", "odds ratio lower", "odds ratio upper")]
                values = []
                for line in lines[head + 1:]:
                    cells = re.split(r"\s{2,}", line.strip())
                    if len(cells) == len(columns) and any(name in cells[0] for name in moderators) and "(reference)" not in cells[0]:
                        values.append([float(cells[index]) for index in indexes])
                actual[side] = values
                for observed, ref in zip(values, references, strict=True):
                    for value, bound in zip(observed, ref, strict=True):
                        assert abs(value - bound) <= .00051, (side, values, references, lines)
        elif regression:
            table = next(table for section in view.results.sections for table in section.tables
                         if table.role == "coefficients")
            actual = [
                {q.role: q.value for cell in row for q in cell}
                for row in table.quantities if any(q.role == "estimate" for cell in row for q in cell)
            ]
            for field, role in roles.items():
                for value, ref in zip(actual, expected[field], strict=True):
                    assert abs(value[role] - ref) <= .000051, (field, actual, expected)
        elif factor:
            table = next(table for section in view.results.sections for table in section.tables
                         if table.title == "Model results" and len(table.rows) == len(expected))
            actual = {
                row[0].removeprefix("Subgroup ").casefold(): {q.role: q.value for cell in cells for q in cell}
                for row, cells in zip(table.rows, table.quantities, strict=True)
            }
            for name, ref in expected.items():
                for field, role in roles.items():
                    assert abs(actual[name.casefold()][role] - ref[field]) <= .000051, (name, actual, expected)
        else:
            title = "Cumulative results" if workflow == "cumulative" else "Leave-one-out results"
            table = next(table for section in view.results.sections for table in section.tables if table.title == title)
            actual = [{q.role: q.value for cell in row for q in cell} for row in table.quantities]
            for value, ref in zip(actual, expected, strict=True):
                for field, role in roles.items():
                    assert abs(value[role] - ref[field]) <= .000051, (field, value, ref)
        record_results(view, workflow, actual, expected, metric=metric, estimator=estimator, moderators=moderators)

    def joint(estimator):
        expected = expected_fit("Sens", "diagnostic.reitsma", estimator)
        view = analyze(app, window, "diagnostic.reitsma", digits=4, diagnostic_metrics=("sens", "spec", "dor", "lr"),
                       parameters={"estimator": estimator})
        point = view.texts["Summary operating point"].split("False-positive rate:", 1)[0]
        actual = [float(value) / 100 if percent else float(value)
                  for value, percent in re.findall(
                      r"(?:Estimate|Lower bound(?:\s*\([^)]*\))?|Upper bound(?:\s*\([^)]*\))?):\s+([0-9.]+)\s*(%)?",
                      point)]
        for value, ref in zip(actual, sum(expected, []), strict=True):
            assert abs(value - ref) <= .000051, (actual, expected, point)
        assert any("sroc" in name.casefold() for name in view.results.images)
        record_results(view, "reitsma", actual, expected, estimator=estimator)

    def small_study(metric, side=""):
        diagnostic = example == "kearon"
        trim_fill = example != "feng" and not diagnostic
        if not diagnostic:
            select_metric(metric)
        expected = expected_fit(metric, "", "REML", workflow="deeks" if diagnostic else "small-study",
                                moderators=side)

        def configure(dialog):
            if diagnostic:
                assert dialog.deeks_funnel_check.isChecked()
            else:
                dialog.ordinary_funnel_check.setChecked(True)
                dialog.contour_funnel_check.setChecked(True)
                dialog.trim_fill_check.setChecked(trim_fill)
                dialog.trim_fill_side_combo.setCurrentText(side.capitalize() if side else "Automatic")
                dialog.extrapolation_check.setChecked(trim_fill)
            record("published-small-study-configured", dialog, sample=filename, metric=metric, side=side)
            accept(dialog, dialog.button_box)
            assert not dialog.failure_label.isVisible(), dialog.failure_label.text()

        modal(app, SmallStudyEffectsDialog, configure, window.action_publication_bias.trigger)
        view = visible(ResultsWindow)
        tests = view.texts["small-study.tests"].replace("−", "-")
        record("published-small-study-result", view, sample=filename, metric=metric,
               texts=dict(view.texts), plots=dict(view.results.display_images))
        if diagnostic:
            assert any("deeks" in name.casefold() for name in view.results.images)
            actual = compare_p_value(tests, "Deeks", expected["p"])
        else:
            for plot in ("ordinary", "contour"):
                assert any(plot in Path(path).name for path in view.results.images.values()), view.results.images
            actual = {label: compare_p_value(tests, label, p) for label, p in expected["tests"].items()}
            if trim_fill:
                assert any("trimfill" in Path(path).name for path in view.results.images.values()), view.results.images
                assert "small-study.extrapolation" in view.texts
                trim = next(text for key, text in view.texts.items() if "trim-and-fill" in key.casefold())
                assert f"Estimated missing studies: {expected['imputed']}" in trim, (trim, expected)
                assert f"Side: {expected['side'].capitalize()}" in trim, (trim, expected)
                line = next(line for line in trim.splitlines() if line.startswith("Estimate after imputation:"))
                estimate = [float(token) for token in re.findall(r"-?\d+(?:\.\d+)?", line.replace("−", "-"))]
                for value, ref in zip((estimate[0], *estimate[-2:]), expected["trim"], strict=True):
                    assert abs(value - ref) <= .00051, (estimate, expected, line)
            else:
                assert "the funnel plot is descriptive" in "\n".join(view.texts.values())
        record_results(view, "deeks" if diagnostic else "small-study", actual, expected, tests=tests,
                       side=side, metric=metric)

    def tsa(metric, method, required_information_size):
        select_metric(metric)
        view = analyze(app, window, method)
        view.close()
        expected = expected_fit(metric, method, "FE")

        def configure(dialog):
            dialog.order.setCurrentIndex(dialog.order.findData("table"))
            dialog.manual.setChecked(True)
            dialog.manual_ris.setText(str(required_information_size))
            if metric == "MD":
                dialog.effect.setText("-0.15")
            wait(400)
            assert dialog.run_button.isEnabled(), dialog.status.text()
            record("published-tsa-configured", dialog, sample=filename, metric=metric,
                   status=dialog.status.text(), required_information_size=required_information_size)
            dialog.run_button.click()
            assert dialog.result() == dialog.DialogCode.Accepted, dialog.status.text()

        modal(app, TrialSequentialAnalysisDialog, configure, window.action_trial_sequential_analysis.trigger)
        view = visible(ResultsWindow)
        table = view._report_tables[0]
        measure = "Peto OR" if method.endswith(".peto") else metric
        column = next(index for index, title in enumerate(table.headers) if title.startswith(measure + " ("))
        fits = {q.role: q.value for q in table.quantities[-1][column]}
        for field, role in (("estimate", "estimate"), ("lower_bound", "ci_lower"), ("upper_bound", "ci_upper")):
            assert abs(fits[role] - expected[field]) <= .000051, (metric, method, fits, expected, table.headers)
        record_results(view, "tsa", fits, expected, metric=metric, method=method, steps=len(table.rows),
                       required_information_size=required_information_size)

    if example == "colditz":
        def check_figure_3a(view):
            title, = view.results.display_images
            artifact = view.plot_artifact(title)
            png = work / "figure-3a-regression.png"
            with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(png), "")):
                view.save_image_as(artifact, format="png")
            assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
            svg = ElementTree.parse(artifact.image_path)
            lines = svg.findall(".//{http://www.w3.org/2000/svg}line")
            grid = [line for line in lines if "stroke-dasharray:" in line.get("style", "")
                    and "stroke: #CCCCCC;" in line.get("style", "")]
            horizontal = [line for line in grid if line.attrib["y1"] == line.attrib["y2"]]
            vertical = [line for line in grid if line.attrib["x1"] == line.attrib["x2"]]
            assert horizontal and vertical, "Default regression plot is missing its grid"
            left, bottom = horizontal[0].attrib["x1"], vertical[0].attrib["y1"]
            y_ticks = sorted(float(line.attrib["y1"]) for line in lines
                             if line.attrib["x1"] == left and float(line.attrib["x2"]) < float(left)
                             and line.attrib["y1"] == line.attrib["y2"])
            x_ticks = sorted(float(line.attrib["x1"]) for line in lines
                             if line.attrib["y1"] == bottom and float(line.attrib["y2"]) > float(bottom)
                             and line.attrib["x1"] == line.attrib["x2"])
            y_grid = sorted(float(line.attrib["y1"]) for line in horizontal)
            x_grid = sorted(float(line.attrib["x1"]) for line in vertical)
            labels = [label.text for label in svg.findall(".//{http://www.w3.org/2000/svg}text")
                      if label.get("text-anchor") == "end"]
            record("published-bcg-rr-regression", view, sample=filename,
                   plots=dict(view.results.display_images), exports={"Figure 3A": str(png)},
                   labels=labels, y_ticks=y_ticks, y_grid=y_grid, x_ticks=x_ticks, x_grid=x_grid)
            assert labels == ["0.2", "0.5", "1"]
            assert x_ticks and x_grid == x_ticks, (x_grid, x_ticks)
            assert len(y_ticks) == len(labels) and y_grid == y_ticks, (y_grid, y_ticks)

        repeated("meta-regression", "RR", "binary.random", moderators=["Absolute latitude"],
                 formula="latitude", check_plot=check_figure_3a)
        for metric in ("OR", "RR", "RD", "AS", "YUQ", "YUY"):
            pooled(metric, "binary.fixed.inv.var")
            pooled(metric, "binary.random", estimator="REML")
        for estimator in ("HE", "DL", "HS", "HSk", "SJ", "ML", "EB", "PM", "PMM"):
            pooled("OR", "binary.random", estimator=estimator)
        for inference in ("t", "knha", "adhoc"):
            pooled("OR", "binary.random", estimator="REML", inference=inference)
        repeated("cumulative", "OR", "binary.fixed.inv.var", estimator="FE")
        repeated("leave-one-out", "OR", "binary.random")
        repeated("subgroup", "OR", "binary.random", factor="Allocation method")
        for formula, names in (("latitude", ["Absolute latitude"]),
                               ("category", ["Allocation method"]),
                               ("latitude + category", ["Absolute latitude", "Allocation method"])):
            repeated("meta-regression", "OR", "binary.random", moderators=names, formula=formula)
        small_study("OR")
        small_study("RR")
        small_study("RD")
        for metric, method in (("RR", "binary.fixed.inv.var"), ("RD", "binary.fixed.inv.var"),
                               ("OR", "binary.fixed.peto")):
            tsa(metric, method, 120000)
    elif example == "barza":
        for sheet in range(2):
            window.sheet_tabs.setCurrentIndex(sheet)
            for metric in ("OR", "RR", "RD"):
                pooled(metric, "binary.fixed.mh", sheet=sheet)
            pooled("OR", "binary.fixed.peto", sheet=sheet)
        pooled("OR", "binary.fixed.mh", sheet=1, correction="all")
        window.sheet_tabs.setCurrentIndex(0)
        repeated("cumulative", "OR", "binary.fixed.mh", estimator="FE")
        repeated("leave-one-out", "OR", "binary.fixed.peto", estimator="FE")
        tsa("RR", "binary.fixed.mh", 3000)
    elif example == "poole":
        for metric in ("MD", "SMD"):
            pooled(metric, "continuous.fixed")
            pooled(metric, "continuous.random", estimator="REML")
        repeated("cumulative", "MD", "continuous.fixed", estimator="FE")
        repeated("leave-one-out", "SMD", "continuous.random")
        repeated("subgroup", "MD", "continuous.random", factor="Trial duration")
        for formula, names in (("year", ["Publication year"]), ("category", ["Trial duration"]),
                               ("year + category", ["Trial duration", "Publication year"])):
            for estimator in ("FE", "REML"):
                repeated("meta-regression", "MD", "continuous.random", moderators=names, formula=formula,
                         estimator=estimator)
        for side in ("", "left", "right"):
            small_study("MD", side)
        small_study("SMD")
        tsa("MD", "continuous.fixed", 10000)
        select_metric("SMD")
        assert not window.action_trial_sequential_analysis.isEnabled()
        record("published-tsa-ineligible-smd", window, reason=window.action_trial_sequential_analysis.toolTip())
    elif example == "kearon":
        for metric in ("Sens", "Spec", "DOR", "LR"):
            pooled(metric, "diagnostic.fixed.inv.var")
            pooled(metric, "diagnostic.random", estimator="REML")
        for metric in ("DOR", "LR"):
            pooled(metric, "diagnostic.fixed.mh")
        pooled("DOR", "diagnostic.fixed.peto")
        for estimator in ("REML", "ML"):
            joint(estimator)
        repeated("cumulative", "DOR", "diagnostic.fixed.inv.var", estimator="FE")
        repeated("leave-one-out", "DOR", "diagnostic.random")
        repeated("subgroup", "DOR", "diagnostic.random", factor="Patient group")
        for formula, names in (("year", ["Publication year"]), ("category", ["Patient group"]),
                               ("category + year", ["Patient group", "Publication year"])):
            repeated("meta-regression", "Sens", "diagnostic.reitsma", moderators=names, formula=formula)
        group = window.model.current_sheet.covariates[0]["id"]
        model = window.model
        for row, study in enumerate(model.current_sheet.rows):
            if study.covariate_values[group] == "Symptomatic":
                assert model.setData(model.index(row, model.INCLUDE_STUDY), QtCore.Qt.CheckState.Unchecked.value,
                                     QtCore.Qt.ItemDataRole.CheckStateRole)
        small_study("DOR")
    elif example == "greenland":
        for sheet in range(2):
            window.sheet_tabs.setCurrentIndex(sheet)
            pooled("Mean", "continuous.fixed", sheet=sheet)
            pooled("Mean", "continuous.random", estimator="REML", sheet=sheet)
    elif example == "abe":
        pooled("Mean", "continuous.fixed")
        pooled("Mean", "continuous.random", estimator="REML")
    elif example == "feng":
        for metric in ("PR", "PLN", "PLO", "PAS", "PFT"):
            pooled(metric, "binary.fixed.inv.var")
            pooled(metric, "binary.random", estimator="REML")
        small_study("PR")


def compare_p_value(tests, label, expected):
    section = next(block for block in tests.split("\n\n") if block.startswith(label))
    match = re.search(r"\bp(?:-value)?\s*([=<:])\s*(\d+(?:\.\d+)?)", section, re.IGNORECASE)
    assert match, section
    value = float(match[2])
    if match[1] == "<":
        assert expected < value, (label, expected, section)
        return f"< {value}"
    assert abs(value - expected) <= .00051, (label, expected, section)
    return value
