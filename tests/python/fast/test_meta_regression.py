# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import pytest

from rc_metastudio.meta_regression import (
    AvailableNumber,
    ContinuousModerator,
    FactorModerator,
    MetaRegressionRequest,
    MetaRegressionStudy,
    UnavailableNumber,
    parse_meta_regression_result,
    prepare_meta_regression,
)


def _request(*, missing_policy="reject", inference="z"):
    studies = (
        MetaRegressionStudy(1, "Study A", 0.2, 0.1),
        MetaRegressionStudy(2, "Study B", 0.1, 0.12),
        MetaRegressionStudy(3, "Study C", 0.4, 0.08),
        MetaRegressionStudy(4, "Study D", 0.5, 0.15),
        MetaRegressionStudy(5, "Study E", 0.6, 0.11),
    )
    return MetaRegressionRequest(
        studies=studies,
        moderators=(
            ContinuousModerator("dose", "mg", (0, 10, 20, 30, 40), unit_step=10),
            FactorModerator(
                "region",
                "B",
                ("A", "B", "C"),
                ("B", "A", "C", "A", ""),
            ),
        ),
        heterogeneity_method="REML",
        inference_method=inference,
        confidence_level=95,
        missing_moderator_policy=missing_policy,
        metric="SMD",
    )


def test_plan_freezes_formula_coding_units_and_selected_study_set():
    request = _request(missing_policy="exclude")

    plan = prepare_meta_regression(request)

    assert plan.formula == "yi ~ 1 + dose + region"
    assert [term.key for term in plan.coefficient_terms] == [
        "intercept",
        "moderator:dose",
        "moderator:region:level:A",
        "moderator:region:level:C",
    ]
    assert plan.moderators[0].unit == "mg"
    assert plan.moderators[0].unit_step == 10
    assert plan.coefficient_terms[1].label == "dose (per 10 mg)"
    assert plan.coefficient_terms[1].unit_step == 10
    assert plan.moderators[1].reference_level == "B"
    assert plan.moderators[1].levels == ("A", "B", "C")
    assert plan.eligible_study_count == 4
    assert plan.residual_degrees_of_freedom == 0
    assert [study.id for study in plan.studies] == [1, 2, 3, 4]
    assert plan.studies[0].design_row == (1.0, 0.0, 0.0, 0.0)
    assert plan.studies[1].design_row == (1.0, 1.0, 1.0, 0.0)
    assert plan.studies[2].design_row == (1.0, 2.0, 0.0, 1.0)
    assert plan.excluded_studies[0].missing_moderators == ("region",)


def test_plan_requires_explicit_missing_moderator_decision():
    with pytest.raises(ValueError, match="correct them or explicitly choose exclusion"):
        prepare_meta_regression(_request(missing_policy="reject"))


def test_formula_quotes_non_syntactic_R_moderator_names():
    request = MetaRegressionRequest(
        studies=(
            MetaRegressionStudy(1, "A", 0.2, 0.1),
            MetaRegressionStudy(2, "B", 0.3, 0.1),
        ),
        moderators=(ContinuousModerator("dose mg", "mg", (1, 2)),),
        heterogeneity_method="REML",
        inference_method="z",
        confidence_level=95,
        missing_moderator_policy="reject",
        metric="SMD",
    )

    plan = prepare_meta_regression(request)

    assert plan.formula == "yi ~ 1 + `dose mg`"


def test_non_normal_inference_requires_positive_authority_residual_df():
    with pytest.raises(ValueError, match="requires positive residual degrees of freedom"):
        prepare_meta_regression(_request(missing_policy="exclude", inference="knha"))


def test_plan_rejects_absent_categorical_reference_in_eligible_studies():
    request = _request(missing_policy="exclude")
    moderator = request.moderators[1]
    changed = MetaRegressionRequest(
        studies=request.studies,
        moderators=(request.moderators[0], FactorModerator(
            moderator.name,
            "C",
            moderator.levels,
            ("B", "A", "B", "", ""),
        )),
        heterogeneity_method=request.heterogeneity_method,
        inference_method=request.inference_method,
        confidence_level=request.confidence_level,
        missing_moderator_policy=request.missing_moderator_policy,
        metric=request.metric,
    )

    with pytest.raises(ValueError, match="reference level 'C'.*absent"):
        prepare_meta_regression(changed)


def test_result_parser_keeps_authority_missing_values_unavailable_with_reasons():
    request = MetaRegressionRequest(
        studies=(
            MetaRegressionStudy(1, "A", 0.2, 0.1),
            MetaRegressionStudy(2, "B", 0.3, 0.1),
            MetaRegressionStudy(3, "C", 0.4, 0.1),
        ),
        moderators=(ContinuousModerator("dose", "mg", (1, 2, 3)),),
        heterogeneity_method="REML",
        inference_method="z",
        confidence_level=95,
        missing_moderator_policy="reject",
        metric="SMD",
    )
    plan = prepare_meta_regression(request)
    fit = {
        "k": 3,
        "p": 2,
        "method": "REML",
        "b": [0.2, None],
        "se": [0.1, 0.2],
        "ci.lb": [0.004, None],
        "ci.ub": [0.396, None],
        "zval": [2.0, None],
        "pval": [0.0455, None],
        "QM": 4.0,
        "m": 1,
        "QMp": 0.0455,
        "QE": 1.2,
        "QEp": 0.27,
        "tau2": None,
    }

    result = parse_meta_regression_result(plan, fit)

    assert result.formula == "yi ~ 1 + dose"
    assert result.eligible_study_ids == (1, 2, 3)
    assert result.coefficients[0].estimate == AvailableNumber(0.2)
    assert isinstance(result.coefficients[1].estimate, UnavailableNumber)
    assert result.coefficients[1].estimate.reason
    assert result.overall_test.statistic == AvailableNumber(4.0)
    assert isinstance(result.overall_test.denominator_degrees_of_freedom, UnavailableNumber)
    assert result.residual_heterogeneity.tau_squared == UnavailableNumber(
        "RCMetaR returned no finite 'tau2' value.", "not_estimable"
    )
    mapping = result.to_mapping()
    coefficient_rows = mapping["coefficients"]
    assert isinstance(coefficient_rows, list)
    second_coefficient = coefficient_rows[1]
    assert isinstance(second_coefficient, dict)
    coefficient_fields = {str(key): value for key, value in second_coefficient.items()}
    assert coefficient_fields["estimate"] == {
        "status": "not_estimable",
        "value": None,
        "reason": "RCMetaR did not return an estimable coefficient b value.",
    }
    assert "predictions" not in mapping


def test_parser_refuses_backend_silent_study_exclusion():
    request = MetaRegressionRequest(
        studies=(
            MetaRegressionStudy(1, "A", 0.2, 0.1),
            MetaRegressionStudy(2, "B", 0.3, 0.1),
        ),
        moderators=(ContinuousModerator("dose", "mg", (1, 2)),),
        heterogeneity_method="REML",
        inference_method="z",
        confidence_level=95,
        missing_moderator_policy="reject",
        metric="SMD",
    )
    plan = prepare_meta_regression(request)

    with pytest.raises(ValueError, match="fitted study count does not match"):
        parse_meta_regression_result(plan, {"k": 1, "p": 2})


def test_current_RCMetaR_meta_regression_coefficients_and_tests(tmp_path):
    from rc_metastudio import __version__
    from rc_metastudio.analysis_worker import _initialize_backend

    try:
        bridge = _initialize_backend()
        version = bridge.get_r_package_version("RCMetaR")
    except Exception as error:
        pytest.skip(f"the configured R runtime is unavailable: {error}")
    if version != __version__:
        pytest.skip(
            f"configured RCMetaR version {version} does not match app version {__version__}"
        )

    estimates = (0.2, 0.1, 0.4, 0.5, 0.8, 0.6, 0.9)
    standard_errors = (0.1, 0.12, 0.08, 0.15, 0.09, 0.11, 0.13)
    dose = (0, 10, 20, 30, 40, 50, 60)
    regions = ("B", "A", "C", "A", "B", "C", "A")
    request = MetaRegressionRequest(
        studies=tuple(
            MetaRegressionStudy(index + 1, f"S{index + 1}", estimate, standard_errors[index])
            for index, estimate in enumerate(estimates)
        ),
        moderators=(
            ContinuousModerator("dose", "mg", dose, unit_step=10),
            FactorModerator("region", "B", ("A", "B", "C"), regions),
        ),
        heterogeneity_method="REML",
        inference_method="z",
        confidence_level=95,
        missing_moderator_policy="reject",
        metric="SMD",
    )
    plan = prepare_meta_regression(request)

    continuous = bridge.execute_r_function(
        "rcmetar.create.covariate.values",
        **{
            "cov.name": "dose",
            "cov.vals": bridge._r_numeric_vector(
                [row.moderator_values[0] for row in plan.studies]
            ),
            "cov.type": "continuous",
            "ref.var": "",
        },
    )
    factor = bridge.execute_r_function(
        "rcmetar.create.covariate.values",
        **{
            "cov.name": "region",
            "cov.vals": bridge._r_character_vector(regions),
            "cov.type": "factor",
            "ref.var": "B",
        },
    )
    covariates = bridge.execute_r_function("list", continuous, factor)
    data = bridge.execute_r_function(
        "rcmetar.create.continuous.data",
        y=bridge._r_numeric_vector(estimates),
        SE=bridge._r_numeric_vector(standard_errors),
        **{
            "study.names": bridge._r_character_vector(
                [study.label for study in request.studies]
            ),
            "years": bridge._r_year_vector([2020 + index for index in range(7)]),
            "covariates": covariates,
        },
    )
    bridge.ro.globalenv["tmp_obj"] = data
    bridge.run_versioned_analysis_request(
        {
            "version": 1,
            "data_type": "continuous",
            "workflow": "meta-regression",
            "method": "meta.regression",
            "metric": "SMD",
            "params": {
                "measure": "SMD",
                "rm.method": "REML",
                "inference.method": "z",
                "conf.level": 95,
                "digits": 3,
                "bp_outpath": str(tmp_path / "meta-regression.svg"),
            },
        }
    )
    raw = bridge.ro.globalenv["result"]
    fit_r = raw.rx2("res")
    fit = bridge.r_object_to_python(fit_r)
    factor_fit = bridge.r_object_to_python(
        bridge.execute_r_function(
            "anova", fit_r, btt=bridge.ro.IntVector([3, 4])
        )
    )
    statistic = factor_fit.get("QM")
    if statistic is None:
        statistic = factor_fit.get("F")
    factor_test = {
        "statistic": statistic,
        "degrees_of_freedom": len(plan.moderators[1].coefficient_keys),
        "denominator_degrees_of_freedom": None,
        "p_value": factor_fit.get("QMp"),
    }

    result = parse_meta_regression_result(
        plan, fit, moderator_tests={"region": factor_test}
    )

    assert result.missing_moderator_policy == "reject"
    assert result.moderators[0].unit == "mg"
    assert result.moderators[0].unit_step == 10
    assert result.moderators[1].reference_level == "B"
    assert result.eligible_study_ids == tuple(range(1, 8))
    assert [term.key for term in (coefficient.term for coefficient in result.coefficients)] == [
        "intercept",
        "moderator:dose",
        "moderator:region:level:A",
        "moderator:region:level:C",
    ]
    coefficient_estimates = [
        coefficient.estimate for coefficient in result.coefficients
    ]
    available_estimates = [
        value.value
        for value in coefficient_estimates
        if isinstance(value, AvailableNumber)
    ]
    assert len(available_estimates) == len(coefficient_estimates)
    assert available_estimates == pytest.approx(
        [0.23154158166960281, 0.1354261156126064, -0.19066351091613482, -0.1805534095654478],
        abs=1e-12,
    )
    assert result.coefficients[0].standard_error == AvailableNumber(
        0.0916419200997576
    )
    assert result.coefficients[0].lower == AvailableNumber(
        0.05192671879998065
    )
    assert result.coefficients[0].upper == AvailableNumber(
        0.41115644453922495
    )
    assert result.coefficients[0].statistic == AvailableNumber(
        2.526590248409857
    )
    assert result.coefficients[0].p_value == AvailableNumber(
        0.011517579225682851
    )
    assert isinstance(result.coefficients[0].degrees_of_freedom, UnavailableNumber)
    assert result.overall_test.statistic == AvailableNumber(32.62802036676466)
    assert isinstance(result.overall_test.p_value, AvailableNumber)
    assert result.overall_test.p_value.value == pytest.approx(3.8583106897674923e-07)
    assert isinstance(result.residual_heterogeneity.tau_squared, AvailableNumber)
    assert result.residual_heterogeneity.tau_squared.value == pytest.approx(
        0.002517478977167429
    )
    assert isinstance(result.residual_heterogeneity.q, AvailableNumber)
    assert result.residual_heterogeneity.q.value == pytest.approx(3.143047614964721)
    assert isinstance(result.moderator_tests[0].statistic, AvailableNumber)
    assert result.moderator_tests[0].numerator_degrees_of_freedom == AvailableNumber(2)
    assert isinstance(result.moderator_tests[0].p_value, AvailableNumber)
    assert result.moderator_tests[0].p_value.value == pytest.approx(
        0.15950097841676492, abs=1e-12
    )
