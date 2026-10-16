"""Additional real desktop drives owned by the verification skill.

Fixtures may add covariates; analysis selection and execution always use widgets.
Frozen contracts prove numerics; other cases prove execution and rendered output.
"""

from pathlib import Path

GOLDEN = (
    "amino-binary-cumulative",
    "amino-binary-leave-one-out",
    "continuous-cumulative",
    "continuous-leave-one-out",
    "amino-binary-meta-regression",
    "continuous-meta-regression",
    "amino-binary-subgroup",
    "continuous-subgroup",
)
FIXED = (
    "binary.fixed.inv.var",
    "binary.fixed.mh",
    "binary.fixed.peto",
    "continuous.fixed",
    "diagnostic.fixed.inv.var",
    "diagnostic.fixed.mh",
    "diagnostic.fixed.peto",
)
DATA_TYPES = {
    "onearm-proportion": (
        "onearm_proportion_Button",
        "binary",
        "proportion",
        "PR",
        [4, 20],
    ),
    "onearm-mean": ("onearm_mean_Button", "continuous", "mean", "TX Mean", [20, 4, 2]),
    "reg-coef": (
        "onearm_single_reg_coef_Button",
        "continuous",
        "reg_coef",
        "TX Mean",
        None,
    ),
    "generic-effect": (
        "onearm_generic_effect_size_Button",
        "continuous",
        "generic_effect",
        "TX Mean",
        None,
    ),
    "twoarm-proportion": (
        "twoarm_proportions_Button",
        "binary",
        "proportions",
        "OR",
        [4, 20, 6, 22],
    ),
    "twoarm-mean": (
        "twoarm_means_Button",
        "continuous",
        "means",
        "MD",
        [20, 4, 2, 22, 3, 2.5],
    ),
    "twoarm-smd": (
        "twoarm_smds_Button",
        "continuous",
        "smd",
        "SMD",
        [20, 4, 2, 22, 3, 2.5],
    ),
    "diagnostic": ("diagnostic_Button", "diagnostic", None, None, [19, 10, 1, 81]),
}
SCENARIOS = (
    *("analysis-" + case for case in GOLDEN),
    *("analysis-" + method for method in FIXED),
    "analysis-diagnostic-joint",
    "analysis-diagnostic-combined",
    "analysis-diagnostic-cumulative",
    "analysis-diagnostic-leave-one-out",
    "analysis-diagnostic-subgroup",
    "analysis-diagnostic-regression-continuous",
    "analysis-diagnostic-regression-factor",
    "analysis-diagnostic-regression-multiple",
    *("analysis-data-" + name for name in DATA_TYPES),
    "small-study-binary-extended",
    "small-study-continuous-extended",
    "small-study-diagnostic",
)


def set_parameter(app, dialog, key, value):
    from PyQt6 import QtWidgets

    from rc_metastudio.analysis_method_labels import parameter_display_label

    if key == "fp_style":
        from rc_metastudio.analysis_setup_dialog import PLOT_STYLE_LABELS
        dialog.style_cbo.setCurrentText(PLOT_STYLE_LABELS[value])
        app.processEvents()
        return

    plot_controls = {"bp_plot_lb": dialog.plot_lb_le, "bp_plot_ub": dialog.plot_ub_le,
                     "fp_plot_lb": dialog.plot_lb_le, "fp_plot_ub": dialog.plot_ub_le}
    if key in plot_controls:
        plot_controls[key].setText(str(value))
        app.processEvents()
        return
    label = parameter_display_label(key, dialog.param_d.get(key))
    controls = [
        w.buddy()
        for w in dialog.findChildren(QtWidgets.QLabel)
        if w.text().casefold() == label.casefold() and w.buddy() is not None
    ]
    assert controls, (key, label)
    control = controls[0]
    if isinstance(control, QtWidgets.QComboBox):
        index = control.findData(value)
        assert index >= 0, (key, value)
        control.setCurrentIndex(index)
    elif isinstance(control, QtWidgets.QCheckBox):
        control.setChecked(str(value).upper() == "TRUE")
    elif isinstance(control, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
        control.setValue(value)
    else:
        control.setText(str(value))
    app.processEvents()


def run(
    app,
    window,
    scenario,
    record,
    *,
    keep_results=False,
    parameters=None,
    workflow_override=None,
    metrics_override=None,
    metric_override=None,
    prepare=None,
    fixed_effects=False,
    group_names=None,
):
    import json
    import re

    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtSvg import QSvgRenderer
    from PyQt6.QtTest import QTest

    from rc_metastudio import analysis_dataset, analysis_setup_dialog, results_window
    from rc_metastudio.diagnostic_metrics_dialog import DiagnosticMetricsDialog
    from tests.analysis_regression.golden.support.golden_analysis import (
        curated_golden_bundles,
        parsed_numeric_sections,
    )

    root = Path(__file__).resolve().parents[4]
    work = Path(__import__("sys").argv[2])

    def click(widget):
        assert widget.isEnabled(), widget.objectName()
        QTest.mouseClick(widget, QtCore.Qt.MouseButton.LeftButton)
        app.processEvents()

    def visible(kind):
        found = [
            w for w in app.topLevelWidgets() if isinstance(w, kind) and w.isVisible()
        ]
        assert len(found) == 1, (kind, found)
        return found[0]

    def observe():
        view = visible(results_window.ResultsWindow)
        app.processEvents()
        app.processEvents()
        clinical = any(section.plot_kind == "sroc" for section in view.results.sections)
        if clinical:
            assert any(section.semantic_id.startswith("diagnostic.reitsma.summary")
                       for section in view.results.sections), [section.semantic_id for section in view.results.sections]
            report = view.report_text.toPlainText()
            first_section = min(view.results.sections, key=lambda section: section.order)
            assert first_section.source_key == "Clinical interpretation", first_section
            assert report.startswith(first_section.title + "\n"), report
            assert report.index(first_section.value.splitlines()[0]) < report.index("Model configuration"), report
        assert view.content_stack.currentWidget() is (view.report_text if clinical else view.figure_page)
        if clinical:
            assert view.nav_tree.currentItem().text(0) == "Text report"
            view.nav_tree.setCurrentItem(view._last_plot_item)
            app.processEvents()
        selected = view._selected_plot()
        assert selected is not None
        viewport = view.graphics_view.viewport()
        # Native resize delivery can finish a loop turn before its queued refit.
        # Observe the settled result, with a bound that still fails a missing fit.
        for _ in range(40):
            app.processEvents()
            bounds = view.graphics_view.mapFromScene(selected[1].sceneBoundingRect()).boundingRect()
            if not view._viewport_refit_pending and bounds.right() >= viewport.width() - 100:
                break
            QTest.qWait(25)
        plot_bounds = view.graphics_view.mapFromScene(selected[1].sceneBoundingRect()).boundingRect()
        assert 0 <= plot_bounds.left() and plot_bounds.right() < viewport.width(), plot_bounds
        if plot_bounds.right() < viewport.width() - 100:
            record("matrix-incomplete-initial-fit", view, plot_bounds=str(plot_bounds), viewport=str(viewport.size()),
                   fit_active=view._fit_width_active, transform=view.graphics_view.transform().m11(),
                   item_scale=selected[1].scale(), item_bounds=str(selected[1].boundingRect()),
                   visible=view.isVisible(), plots=dict(view.results.display_images))
        assert plot_bounds.right() >= viewport.width() - 100, (plot_bounds, viewport.size())
        assert view.scene.items()
        rendered = "\n".join(
            w.toPlainText()
            for w in view.scene.items()
            if isinstance(w, QtWidgets.QGraphicsTextItem)
        )
        # Figure pages contain figures; full structured text remains in the
        # report, table view and exports, without duplicated scene printouts.
        for section in view.results.sections:
            if section.kind == "text" and section.source_key == "Weights":
                assert section.value.strip() not in rendered
        report = view._plain_text_report()
        for section in view.results.sections:
            for table in section.tables:
                assert "\t".join(table.headers) in report
                assert all("\t".join(row) in report for row in table.rows)
        if scenario.startswith("analysis-diagnostic-regression"):
            assert "Image Order" not in view.texts
            assert "diagnostic.reitsma.sensitivity.coefficients" not in view.report_text.toPlainText()
            assert "diagnostic.reitsma.specificity.coefficients" not in view.report_text.toPlainText()
            if scenario == "analysis-diagnostic-regression-multiple":
                assert view.report_text.toPlainText().count("Overall ML likelihood-ratio test") == 1
                assert view._plain_text_report().count("Overall ML likelihood-ratio test") == 1
        assert view.results.images, dict(view.texts)
        if scenario == "analysis-data-twoarm-mean" and workflow == "standard":
            from rc_metastudio import r_bridge
            r_bridge.load_in_r(str(next(iter(view.params_paths.values()))) + ".plotdata")
            headers = r_bridge.r_object_to_python(r_bridge.ro.r("plot.data$ilab$headers"))
            style = (parameters or {}).get("fp_style", "revman")
            expected_headers = (["Mean", "SD", "N", "Mean", "SD", "N"] if style == "default" else
                                ["Total", "Mean", "SD", "Total", "Mean", "SD", "Weight (%)"] if style == "bmj" else
                                ["Mean", "SD", "Total", "Mean", "SD", "Total", "Weight"])
            assert headers == expected_headers, headers
        if any(section.plot_kind == "subgroup_forest" for section in view.results.sections):
            assert any(table.title == "Test of subgroup differences"
                       for section in view.results.sections for table in section.tables), dict(view.texts)
            assert "Test of subgroup differences" in view.report_text.toPlainText()
        for path in (view.results.display_images or view.results.images).values():
            assert (
                QSvgRenderer(str(path)).isValid()
                if Path(path).suffix == ".svg"
                else not QtGui.QImage(str(path)).isNull()
            ), path
        if clinical:
            view.report_action.trigger()
        record(
            "matrix-results",
            view,
            texts=dict(view.texts),
            plots=dict(view.results.display_images or view.results.images),
        )
        if clinical:
            assert view.report_action.isChecked()
            assert view.nav_tree.currentItem().text(0) == "Text report"
            assert view.report_text.horizontalScrollBar().maximum() == 0
            record("clinical-report", view, report=view.report_text.toPlainText())
            view.report_action.trigger()
            app.processEvents()
        return view

    def compare(view, expected, case):
        actual = parsed_numeric_sections(view.results)
        policy = json.loads(
            (
                root / "tests/analysis_regression/baseline/numeric-contract.json"
            ).read_text()
        )["tolerance_policy"]
        for section, values in expected.items():
            assert section in actual, (section, actual.keys())
            for key, value in values.items():
                tolerance = max(policy["absolute"], policy["relative"] * abs(value))
                assert key in actual[section], (section, key)
                assert abs(actual[section][key] - value) <= tolerance + 1e-12, (
                    case,
                    section,
                    key,
                    actual[section][key],
                    value,
                )
        record(
            "matrix-oracle",
            view,
            case=case,
            actual=actual,
            expected=expected,
            oracle="frozen contract",
            tolerance_policy=policy,
        )

    def covariate(name, kind, values):
        window.model.dataset.add_covariate(
            analysis_dataset.Covariate(name, kind), values
        )
        window.model.reset_model()
        window.enable_menu_options_that_require_dataset()

    if scenario.startswith("analysis-data-"):
        from rc_metastudio import main_wizard

        name = scenario.removeprefix("analysis-data-")
        button, family, subtype, metric, raw = DATA_TYPES[name]
        metric = metric_override or metric
        callback_errors = []

        def create():
            wizard = app.activeModalWidget()
            if not isinstance(wizard, main_wizard.MainWizard):
                QtCore.QTimer.singleShot(10, create)
                return
            try:
                page = wizard.currentPage()
                assert isinstance(page, main_wizard.DataTypePage), type(page)
                click(getattr(page, button))
                record("data-type-selected", wizard, data_type=name)
                click(wizard.button(QtWidgets.QWizard.WizardButton.NextButton))
                if isinstance(wizard.currentPage(), main_wizard.ChooseMetricPage):
                    combo = wizard.currentPage().metric_cbo_box
                    index = combo.findData(metric)
                    assert index >= 0, (
                        metric,
                        [combo.itemData(i) for i in range(combo.count())],
                    )
                    combo.setCurrentIndex(index)
                    click(wizard.button(QtWidgets.QWizard.WizardButton.NextButton))
                wizard.currentPage().outcome_name_LineEdit.setText(
                    "Verification outcome"
                )
                page = wizard.currentPage()
                record("data-outcome-naming", wizard, data_type=name)
                if group_names is not None:
                    assert page.first_group_name.isVisible()
                    if len(group_names) == 2:
                        page.first_group_name.setText(" Same ")
                        page.second_group_name.setText("Same")
                        assert not page.isComplete() and page.validation_label.text()
                        record("round5-arm-duplicate", wizard)
                    page.first_group_name.setText(group_names[0])
                    if len(group_names) == 2:
                        page.second_group_name.setText(group_names[1])
                    assert page.isComplete(), page.validation_label.text()
                    record("round5-arm-wizard", wizard, names=group_names)
                click(wizard.button(QtWidgets.QWizard.WizardButton.FinishButton))
            except Exception as error:  # noqa: BLE001 - propagate modal callback failures after exec.
                callback_errors.append(error)
                wizard.reject()

        QtCore.QTimer.singleShot(0, create)
        window.action_new_dataset.trigger()
        assert not callback_errors, callback_errors
        assert window.model.get_current_outcome_type() == family
        assert window.model.get_current_outcome_subtype() == subtype
        assert window.model.current_effect == metric
        model = window.model
        for row in range(6):
            assert model.setData(model.index(row, model.NAME), f"Fixture {row + 1}")
            if raw is not None:
                columns = list(model.RAW_DATA)
                if name.startswith("onearm-"):
                    # Workspace keeps both groups; a one-arm metric consumes the first.
                    assert len(columns) == 2 * len(raw), (columns, raw)
                    columns = columns[: len(raw)]
                else:
                    assert len(columns) == len(raw), (columns, raw)
                for column, value in zip(columns, raw):
                    assert model.setData(model.index(row, column), str(value + row))
            else:
                values = (
                    (0.2 + row / 10, 0.1 + row / 100)
                    if len(model.OUTCOMES) == 2
                    else (0.2 + row / 10, -0.1 + row / 10, 0.5 + row / 10)
                )
                for column, value in zip(model.OUTCOMES, values):
                    assert model.setData(model.index(row, column), str(value))
            assert model.setData(
                model.index(row, model.INCLUDE_STUDY),
                QtCore.Qt.CheckState.Checked,
                QtCore.Qt.ItemDataRole.CheckStateRole,
            )
        record(
            "data-populated",
            window,
            data_type=name,
            metric=metric,
            included=sum(s.include for s in model.dataset.studies),
        )
        window.out_path = str(work / "typed.rcms")
        columns = [model.NAME, *model.RAW_DATA, *model.OUTCOMES]
        before = [
            [str(model.data(model.index(row, column))) for column in columns]
            for row in range(6)
        ]
        assert window.save()
        assert window.open(window.out_path, raise_on_error=True)
        assert window.model.current_effect == metric
        assert window.model.get_current_outcome_type() == family
        assert window.model.get_current_outcome_subtype() == subtype
        assert sum(s.include for s in window.model.dataset.studies) == 6
        after = [
            [
                str(window.model.data(window.model.index(row, column)))
                for column in columns
            ]
            for row in range(6)
        ]
        assert after == before, (after, before)
        record("data-reopened", window, data_type=name, metric=metric, cells=after)
        workflow = "standard"
        method = family + ".random"
        metrics = ("sens", "spec") if family == "diagnostic" else ()
        expected = None
    elif scenario.startswith("small-study-"):
        from rc_metastudio.publication_bias_dialog import PublicationBiasDialog

        sample = {
            "small-study-binary-extended": "amino",
            "small-study-continuous-extended": "continuous",
            "small-study-diagnostic": "lymph",
        }[scenario]
        assert window.open(
            str(root / f"sample_projects/{sample}.rcms"), raise_on_error=True
        )
        if sample == "continuous":
            import copy

            for study in list(window.model.dataset.studies):
                duplicate = copy.deepcopy(study)
                duplicate.id = window.model.dataset.max_study_id() + 1
                duplicate.name += " replicate"
                window.model.dataset.add_study(duplicate)
            window.model.set_state(window.model.get_state())
        callback_errors = []

        def configure():
            dialog = app.activeModalWidget()
            if not isinstance(dialog, PublicationBiasDialog):
                QtCore.QTimer.singleShot(10, configure)
                return
            try:
                if sample == "lymph":
                    assert dialog.deeks_funnel_check.isChecked()
                    assert not dialog.sensitivity_group.isVisible()
                    assert not dialog.trim_fill_check.isChecked()
                    assert not dialog.extrapolation_check.isEnabled()
                else:
                    dialog.ordinary_funnel_check.setChecked(True)
                    dialog.contour_funnel_check.setChecked(True)
                    dialog.trim_fill_check.setChecked(True)
                    dialog.extrapolation_check.setChecked(True)
                record(
                    "small-study-matrix-configured",
                    dialog,
                    context=dialog.context_label.text(),
                    selected=scenario,
                )
                click(
                    dialog.button_box.button(
                        QtWidgets.QDialogButtonBox.StandardButton.Ok
                    )
                )
                assert not dialog.failure_label.isVisible(), dialog.failure_label.text()
            except Exception as error:  # noqa: BLE001 - propagate modal callback failures after exec.
                callback_errors.append(error)
                dialog.reject()

        QtCore.QTimer.singleShot(0, configure)
        window.action_publication_bias.trigger()
        assert not callback_errors, callback_errors
        view = observe()
        texts = "\n".join(view.texts.values())
        if sample == "lymph":
            assert "Deeks" in texts
            assert any("deeks" in key for key in view.results.images)
        else:
            assert any("contour" in key for key in view.results.images)
            assert any("trim-and-fill" in key for key in view.texts)
            assert "small-study.extrapolation" in view.texts
        if keep_results:
            return view
        view.close()
        return
    else:
        case = scenario.removeprefix("analysis-")
        expected = None
        metrics = ("dor",)
        if case in GOLDEN:
            bundle = next(
                b for b in curated_golden_bundles(str(root)) if b["id"] == case
            )
            assert window.open(
                str(root / "sample_projects" / bundle["dataset"]), raise_on_error=True
            )
            workflow = bundle["case"].analysis_type.replace("_", "-")
            method = bundle["method"]
            for cov in bundle["case"].covariates:
                covariate(cov["name"], cov["type"], cov["values"])
            expected = next(
                c
                for c in json.loads(
                    (
                        root
                        / "tests/analysis_regression/baseline/numeric-contract.json"
                    ).read_text()
                )["cases"]
                if c["id"] == case
            )["sections"]
        else:
            family = case.split(".")[0] if case in FIXED else "diagnostic"
            sample = {
                "binary": "amino",
                "continuous": "continuous",
                "diagnostic": "lymph",
            }[family]
            assert window.open(
                str(root / f"sample_projects/{sample}.rcms"), raise_on_error=True
            )
            workflow = "standard"
            method = case if case in FIXED else "diagnostic.random"
            if case == "diagnostic-joint":
                method, metrics = "diagnostic.reitsma", ("sens", "spec")
            elif case == "diagnostic-combined":
                metrics = ("sens", "spec", "lr", "dor")
            elif case.startswith("diagnostic-regression-"):
                workflow = "meta-regression"
                method = "diagnostic.reitsma"
            elif case.startswith("diagnostic-") and case not in FIXED:
                workflow = case.removeprefix("diagnostic-")
            if workflow in ("subgroup", "meta-regression"):
                studies = window.model.get_studies(only_if_included=True)
                if workflow == "subgroup" or case.endswith(("factor", "multiple")):
                    covariate(
                        "Group",
                        "factor",
                        {s.name: "A" if i % 2 else "B" for i, s in enumerate(studies)},
                    )
                if workflow == "meta-regression" and case.endswith(
                    ("continuous", "multiple")
                ):
                    covariate(
                        "Dose",
                        "continuous",
                        {s.name: float(i + 1) for i, s in enumerate(studies)},
                    )

    if workflow_override:
        workflow = workflow_override
    if metrics_override:
        metrics = metrics_override
    if prepare:
        prepare(window)
    action = {
        "standard": window.action_go,
        "cumulative": window.action_cum_ma,
        "leave-one-out": window.action_loo_ma,
        "subgroup": window.action_subgroup_ma,
        "meta-regression": window.action_meta_regression,
    }[workflow]
    assert action.isEnabled(), (scenario, workflow)
    record("matrix-action", window, scenario=scenario, workflow=workflow, method=method)
    action.trigger()
    app.processEvents()
    if workflow == "subgroup":
        from rc_metastudio.subgroup_analysis_dialog import SubgroupAnalysisDialog

        subgroup = visible(SubgroupAnalysisDialog)
        assert subgroup.covariate_combo_box.count() == 1
        click(subgroup.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
    if (
        window.model.get_current_outcome_type() == "diagnostic"
        and workflow != "meta-regression"
    ):
        dialog = visible(DiagnosticMetricsDialog)
        for key in dialog.SELECTABLE_METRICS:
            dialog._metric_checkbox(key).setChecked(key in metrics)
        record("diagnostic-metrics", dialog, metrics=metrics)
        click(dialog.btn_ok)
    dialog = visible(analysis_setup_dialog.AnalysisSetupDialog)
    if workflow == "meta-regression" and fixed_effects:
        dialog.fixed_effects_radio.setChecked(True)
        expected = None
    if workflow != "meta-regression":
        label = next(
            label for label, key in dialog.available_method_d.items() if key == method
        )
        dialog.method_cbo_box.setCurrentText(label)
        app.processEvents()
        if scenario == "analysis-diagnostic-combined":
            panel = dialog.lr_dor_panel
            label = next(
                label
                for label, key in panel.methods.items()
                if key == "diagnostic.random"
            )
            panel.combo.setCurrentText(label)
            app.processEvents()
            assert panel.method == "diagnostic.random"
            estimator = next(control for control in panel.widgets
                             if isinstance(control, QtWidgets.QComboBox) and control.findData("REML") >= 0)
            estimator.setCurrentIndex(estimator.findData("REML"))
            app.processEvents()
            assert panel.params["rm.method"] == "REML"
            assert dialog.current_param_vals["rm.method"] == "DL"
    else:
        for _, checkbox in dialog.covs_and_check_boxes:
            checkbox.setChecked(False)
        assert not dialog.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).isEnabled()
        for _, checkbox in dialog.covs_and_check_boxes:
            checkbox.setChecked(True)
    set_parameter(
        app,
        dialog,
        "digits",
        2 if expected is not None and workflow == "meta-regression" else 3,
    )
    if expected is not None:
        set_parameter(app, dialog, "rm.method", "DL")
    for key, value in (parameters or {}).items():
        set_parameter(app, dialog, key, value)
    lr_dor_method = dialog.lr_dor_panel.method if dialog._combined_diagnostic else None
    lr_dor_parameters = dict(dialog.lr_dor_panel.params) if dialog._combined_diagnostic else None
    record(
        "matrix-configured",
        dialog,
        workflow=workflow,
        method=method,
        parameters=dict(dialog.current_param_vals),
        lr_dor_method=lr_dor_method,
        lr_dor_parameters=lr_dor_parameters,
    )
    click(dialog.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok))
    view = observe()
    view.change_settings_action.trigger()
    app.processEvents()
    properties = visible(analysis_setup_dialog.AnalysisSetupDialog)
    assert properties.current_method == dialog.current_method
    assert properties.analysis_type == dialog.analysis_type
    assert properties.model.current_effect == dialog.model.current_effect
    assert properties.model.current_outcome_name == dialog.model.current_outcome_name
    assert properties.diagnostic_metrics == dialog.diagnostic_metrics
    for key in ("rm.method", "inference.method", "conf.level", "digits", "cov_name"):
        if key in dialog.current_param_vals:
            assert properties.current_param_vals[key] == dialog.current_param_vals[key], key
    if properties._combined_diagnostic:
        assert properties.lr_dor_panel.method == lr_dor_method
        assert properties.lr_dor_panel.params == lr_dor_parameters
    if properties.is_meta_regression:
        assert [cov.name for cov in properties._selected_covariates()] == [cov.name for cov in window.model.dataset.covariates]
    record("properties-prefilled", properties, workflow=properties.analysis_type,
           method=properties.current_method, parameters=dict(properties.current_param_vals))
    properties.reject()
    app.processEvents()
    if scenario == "analysis-diagnostic-regression-multiple":
        assert "Group = A vs B" in view.report_text.toPlainText(), view.report_text.toPlainText()
    if scenario == "analysis-diagnostic-combined":
        assert view.results.details.count("Estimator: DerSimonian-Laird") == 2, view.results.details
        assert view.results.details.count("Estimator: Restricted Maximum Likelihood") == 3, view.results.details
        report = view.report_text.toPlainText()
        assert report.startswith("Sensitivity results\n"), report
        assert "Sensitivity — Heterogeneity\n" in report, report
        assert view.table_selector.findText("Sensitivity — Heterogeneity") >= 0
        assert report.index("Sensitivity results") < report.index("Model configuration"), report
    if scenario == "analysis-diagnostic-joint":
        point = view.texts["Summary operating point"]
        assert all(
            label in point for label in ("Sensitivity", "Lower bound", "Upper bound")
        ), point
        ratios = view.texts["Sampling-based summary ratios"]
        assert "posLR" not in ratios and "DOR" not in ratios, ratios
        assert "95% interval" in ratios or ("2.5%" in ratios and "97.5%" in ratios), (
            ratios
        )
        import re

        rows = re.findall(
            r"(?im)^\s*(positive likelihood ratio|negative likelihood ratio|"
            r"inverse negative likelihood ratio|diagnostic odds ratio)\s+"
            r"([0-9]+(?:\.[0-9]+)?)\s+([0-9]+(?:\.[0-9]+)?)\s+"
            r"([0-9]+(?:\.[0-9]+)?)\s+([0-9]+(?:\.[0-9]+)?)\s*$",
            ratios,
        )
        assert len(rows) == 4 and len({row[0].casefold() for row in rows}) == 4, ratios
        assert all(float(value) >= 0 for row in rows for value in row[1:]), ratios
        i_squared = "\n".join(
            text
            for name, text in view.texts.items()
            if name.startswith("Diagnostic I-squared")
        )
        assert i_squared and ("Zhou" in i_squared or "I-squared" in i_squared), (
            i_squared
        )
    if expected is not None and not parameters:
        compare(view, expected, case)
    else:
        assert any(text.strip() for text in view.texts.values())
        if method == "diagnostic.reitsma":
            assert "Reitsma" in "\n".join(view.texts.values())
        if scenario == "analysis-diagnostic-combined":
            text = "\n".join(view.texts.values()).lower()
            assert all(
                word in text
                for word in ("sensitivity", "specificity", "likelihood", "odds")
            )
        record(
            "matrix-routing-proof",
            view,
            method=method,
            workflow=workflow,
            scope="UI execution/rendering; numerical authority requires R-stack lane",
        )
    if keep_results:
        return view
    view.close()
