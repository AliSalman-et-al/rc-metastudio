# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from rc_metastudio.analysis_results import parse_analysis_result


def _number(value, status="available", reason=None):
    return {"status": status, "value": value, "reason": reason}


def _estimate(value, lower, upper):
    return {
        "estimate": _number(value),
        "lower": _number(lower),
        "upper": _number(upper),
    }


def _binary_numerics():
    return {
        "version": 1,
        "metric": "OR",
        "calculation_scale": "log",
        "display_scale": "ratio",
        "weight_scale": "percent",
        "calculation_null_value": 0,
        "display_null_value": 1,
        "pooled": {
            "calculation": _estimate(-0.4, -0.8, 0.0),
            "display": _estimate(0.670320046, 0.449328964, 1.0),
            "study_count": _number(2),
            "p_value": _number(0.23),
        },
        "studies": [
            {
                "order": 0,
                "label": "Study A",
                "treatment_events": _number(2),
                "treatment_total": _number(20),
                "control_events": _number(5),
                "control_total": _number(20),
                "weight": _number(62.5),
                "p_value": _number(None, "not_available", "The model does not return per-study p-values."),
                "calculation": _estimate(-1.098612289, -2.59, 0.39),
                "display": _estimate(0.333333333, 0.075, 1.477),
            },
            {
                "order": 1,
                "label": "Study B",
                "treatment_events": _number(6),
                "treatment_total": _number(30),
                "control_events": _number(8),
                "control_total": _number(30),
                "weight": _number(37.5),
                "p_value": _number(None, "not_available", "The model does not return per-study p-values."),
                "calculation": _estimate(-0.344840486, -1.37, 0.68),
                "display": _estimate(0.708333333, 0.254, 1.974),
            },
        ],
    }


def _result(binary_numerics=None):
    result = {"version": 1, "texts": {}, "sections": []}
    if binary_numerics is not None:
        result["binary_numerics"] = binary_numerics
    return result


def test_binary_numerics_is_validated_as_immutable_typed_values():
    typed = parse_analysis_result(_result(_binary_numerics())).binary_numerics

    assert typed is not None
    assert (typed.metric, typed.calculation_scale, typed.display_scale) == (
        "OR",
        "log",
        "ratio",
    )
    assert typed.weight_scale == "percent"
    assert (typed.calculation_null_value, typed.display_null_value) == (0, 1)
    assert typed.pooled.study_count.value == 2
    assert typed.pooled.p_value.value == pytest.approx(0.23)
    assert typed.pooled.display.estimate.value == pytest.approx(0.670320046)
    assert [study.label for study in typed.studies] == ["Study A", "Study B"]
    assert typed.studies[0].treatment_total.value == 20
    assert typed.studies[0].weight.value == pytest.approx(62.5)
    assert typed.studies[0].p_value.status == "not_available"
    assert typed.studies[1].calculation.estimate.value == pytest.approx(-0.344840486)
    with pytest.raises((AttributeError, TypeError)):
        setattr(typed.studies[0], "label", "changed")


def test_binary_numerics_keeps_unavailable_model_values_explicit():
    value = _binary_numerics()
    value["pooled"]["calculation"]["estimate"] = _number(
        None, "not_estimable", "The model did not return a finite value."
    )

    typed = parse_analysis_result(_result(value)).binary_numerics

    assert typed is not None
    assert typed.pooled.calculation.estimate.status == "not_estimable"
    assert typed.pooled.calculation.estimate.value is None
    assert typed.pooled.calculation.estimate.reason


def test_binary_numerics_is_optional_for_other_result_families():
    assert parse_analysis_result(_result()).binary_numerics is None


@pytest.mark.parametrize(
    ("metric", "calculation_scale", "display_scale", "calculation_null", "display_null"),
    [
        ("OR", "log", "ratio", 0, 1),
        ("RR", "log", "ratio", 0, 1),
        ("RD", "risk_difference", "risk_difference", 0, 0),
        ("AS", "arcsine_difference", "arcsine_difference", 0, 0),
        ("YUQ", "yule_q", "yule_q", 0, 0),
        ("YUY", "yule_y", "yule_y", 0, 0),
    ],
)
def test_binary_metric_scales_and_null_values_are_validated(
    metric, calculation_scale, display_scale, calculation_null, display_null
):
    value = _binary_numerics()
    value.update(
        metric=metric,
        calculation_scale=calculation_scale,
        display_scale=display_scale,
        calculation_null_value=calculation_null,
        display_null_value=display_null,
    )

    typed = parse_analysis_result(_result(value)).binary_numerics

    assert typed is not None
    assert (typed.metric, typed.calculation_scale, typed.display_scale) == (
        metric,
        calculation_scale,
        display_scale,
    )
    assert (typed.calculation_null_value, typed.display_null_value) == (
        calculation_null,
        display_null,
    )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda data: data.update(metric="PR"), "metric is unsupported"),
        (
            lambda data: data.update(calculation_scale="ratio"),
            "calculation scale does not match",
        ),
        (
            lambda data: data["studies"][1].update(order=0),
            "study order must be contiguous",
        ),
        (
            lambda data: data["studies"][0].update(treatment_events=_number(None)),
            "numeric value|must be numeric",
        ),
        (
            lambda data: data["studies"][0].update(treatment_events=_number(-1)),
            "raw counts cannot be negative",
        ),
        (
            lambda data: data["pooled"]["calculation"].update(
                estimate={"status": "not_estimable", "value": None, "reason": " "}
            ),
            "need a reason",
        ),
        (
            lambda data: data["pooled"].update(study_count=_number(3)),
            "study count exceeds the study rows",
        ),
        (
            lambda data: data["pooled"].update(p_value=_number(1.1)),
            "p-value must be between zero and one",
        ),
        (
            lambda data: data["studies"][0].update(weight=_number(101)),
            "study weight must be a percentage",
        ),
    ],
)
def test_binary_numerics_rejects_malformed_contract(change, message):
    value = _binary_numerics()
    change(value)

    with pytest.raises(ValueError, match=message):
        parse_analysis_result(_result(value))
