# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import math

import pytest

from rc_metastudio.reitsma_meta_regression import (
    ExcludedStudy,
    parse_reitsma_meta_regression_result,
)


def _coefficient(
    term: str,
    estimate: float,
    lower: float,
    upper: float,
    *,
    standard_error: float,
    statistic: float,
    p_value: float,
) -> dict[str, object]:
    return {
        "term": term,
        "Estimate": estimate,
        "Std. Error": standard_error,
        "z": statistic,
        "Pr(>|z|)": p_value,
        "95%ci.lb": lower,
        "95%ci.ub": upper,
        "Odds Ratio": math.exp(estimate),
        "Odds Ratio lower": math.exp(lower),
        "Odds Ratio upper": math.exp(upper),
    }


def _summary() -> dict[str, object]:
    return {
        "Sensitivity coefficients": [
            _coefficient(
                "quality = B",
                0.60650751,
                0.02715423,
                1.1858608,
                standard_error=0.29559384,
                statistic=2.0518273,
                p_value=0.04018645,
            ),
            _coefficient(
                "threshold",
                -0.012322216361123,
                -0.1409612,
                0.1163168,
                standard_error=0.06563334,
                statistic=-0.1877432,
                p_value=0.85107793,
            ),
            _coefficient(
                "quality = A (reference)",
                0,
                0,
                0,
                standard_error=0,
                statistic=0,
                p_value=1,
            ),
        ],
        "Specificity coefficients": [
            _coefficient(
                "quality = B",
                0.9111392,
                -1.2464796,
                3.068758,
                standard_error=1.1008462,
                statistic=0.8276717,
                p_value=0.4078565,
            ),
            _coefficient(
                "threshold",
                -0.117323225590236,
                -0.5902263,
                0.3555799,
                standard_error=0.2412815,
                statistic=-0.4862503,
                p_value=0.6267897,
            ),
            _coefficient(
                "quality = A (reference)",
                0,
                0,
                0,
                standard_error=0,
                statistic=0,
                p_value=1,
            ),
        ],
        "Moderator coding": {
            "quality": {
                "type": "factor",
                "levels": ["A", "B"],
                "reference": "A",
            },
            "threshold": {
                "type": "continuous",
                "range": [1, 8],
            },
        },
        "Overall ML likelihood-ratio test": {
            "moderator": "All moderators",
            "statistic": 3.82673612230366,
            "df": 4,
            "p.value": 0.429962088732508,
        },
        "Moderator block tests": {
            "quality": {
                "moderator": "quality",
                "statistic": 3.61678963156885,
                "df": 2,
                "p.value": 0.163917042789733,
            },
            "threshold": {
                "moderator": "threshold",
                "statistic": 0.185175769205564,
                "df": 2,
                "p.value": 0.91156909455623,
            }
        },
        "Model information": {
            "formula": "cbind(tsens, tfpr) ~ `quality` + `threshold`",
            "estimator": "REML",
            "studies.used": 8,
            "correction.policy": "All studies if any zero exists",
            "correction.factor": 0.5,
            "converged": True,
            "package.version": "0.5.12",
        },
    }


def test_result_preserves_joint_scales_ml_tests_and_unsupported_outputs():
    result = parse_reitsma_meta_regression_result(
        _summary(),
        eligible_study_ids=tuple("abcdefgh"),
        exclusions=(ExcludedStudy("i", "Moderator value missing; excluded by user"),),
    )

    assert result.formula == "cbind(tsens, tfpr) ~ `quality` + `threshold`"
    assert result.moderator_coding[0].levels == ("A", "B")
    assert result.moderator_coding[0].reference_level == "A"
    assert result.overall_test.statistic == pytest.approx(3.82673612230366)
    assert result.overall_test.fit_estimator == "ML"
    assert result.overall_test.comparison == "full model vs intercept-only model"
    assert result.overall_test.included_study_ids == tuple("abcdefgh")
    assert result.moderator_tests[0].label == "quality"
    assert result.exclusions == (
        ExcludedStudy("i", "Moderator value missing; excluded by user"),
    )
    assert [item.name for item in result.unavailable_outputs] == [
        "conditional_summary_operating_point",
        "adjusted_sroc",
        "sroc_auc",
    ]
    assert all("no moderator profile" in item.reason for item in result.unavailable_outputs)

    saved = result.to_mapping()
    assert saved["eligible_study_ids"] == list("abcdefgh")
    assert saved["exclusions"] == [
        {"study_id": "i", "reason": "Moderator value missing; excluded by user"}
    ]
    overall_test = _mapping(saved["overall_ml_likelihood_ratio_test"])
    assert overall_test["fit_estimator"] == "ML"


def test_specificity_display_is_restored_to_false_positive_rate_model_scale():
    summary = _summary()
    specificity_rows = _coefficient_rows(summary, "Specificity coefficients")
    specificity_rows[0]["Estimate"] = -0.5
    specificity_rows[0]["z"] = -1.25
    specificity_rows[0]["95%ci.lb"] = -0.9
    specificity_rows[0]["95%ci.ub"] = -0.1
    specificity_rows[0]["Odds Ratio"] = math.exp(-0.5)
    specificity_rows[0]["Odds Ratio lower"] = math.exp(-0.9)
    specificity_rows[0]["Odds Ratio upper"] = math.exp(-0.1)
    summary["Specificity coefficients"] = specificity_rows

    result = parse_reitsma_meta_regression_result(
        summary, eligible_study_ids=tuple("abcdefgh")
    )
    coefficient = result.false_positive_rate_coefficients[0]

    assert coefficient.model_side == "false_positive_rate"
    assert coefficient.effect_direction == "specificity"
    assert coefficient.model_estimate == pytest.approx(0.5)
    assert coefficient.model_statistic == pytest.approx(1.25)
    assert coefficient.model_ci_lower == pytest.approx(0.1)
    assert coefficient.model_ci_upper == pytest.approx(0.9)
    assert coefficient.reported_odds_ratio == pytest.approx(math.exp(-0.5))


def test_rejects_study_set_drift_inconsistent_odds_ratio_and_conditional_points():
    summary = _summary()
    with pytest.raises(ValueError, match="fitted study count"):
        parse_reitsma_meta_regression_result(
            summary, eligible_study_ids=("a", "b")
        )

    summary = _summary()
    sensitivity_rows = _coefficient_rows(summary, "Sensitivity coefficients")
    sensitivity_rows[0]["Odds Ratio"] = 99
    summary["Sensitivity coefficients"] = sensitivity_rows
    with pytest.raises(ValueError, match="log-odds estimate"):
        parse_reitsma_meta_regression_result(
            summary, eligible_study_ids=tuple("abcdefgh")
        )

    summary = _summary()
    summary["Summary operating point"] = {"sensitivity": 0.8}
    with pytest.raises(ValueError, match="Conditional Reitsma outputs are unsupported"):
        parse_reitsma_meta_regression_result(
            summary, eligible_study_ids=tuple("abcdefgh")
        )


def _coefficient_rows(summary: dict[str, object], name: str) -> list[dict[str, object]]:
    rows = summary[name]
    assert isinstance(rows, list)
    return [_mapping(row) for row in rows]


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    result: dict[str, object] = {}
    for key, item in value.items():
        assert isinstance(key, str)
        result[key] = item
    return result
