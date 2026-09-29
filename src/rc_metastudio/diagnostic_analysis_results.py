# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Typed, data-only numerical results for univariate diagnostic models."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Callable, Mapping, Sequence
from typing import Literal, TypeAlias, TypeGuard, cast

from rc_metastudio.diagnostic_analysis_snapshot import (
    DIAGNOSTIC_METRICS,
    DiagnosticInputSnapshot,
    DiagnosticMetric,
    DiagnosticStudyInput,
)


NumericStatus: TypeAlias = Literal["available", "not_estimable", "not_available"]
_VALUE_FIELDS = {"status", "value", "reason"}
_EFFECT_FIELDS = {"estimate", "lower", "upper"}
_POOLED_FIELDS = {
    "calculation",
    "display",
    "standard_error",
    "p_value",
    "study_count",
    "tau_squared",
    "q",
    "q_df",
    "q_p_value",
    "i_squared",
}
_STUDY_FIELDS = {
    "order",
    "label",
    "tp",
    "fn",
    "fp",
    "tn",
    "calculation",
    "display",
    "variance",
    "weight_fraction",
}
_RESULT_FIELDS = {
    "version",
    "scope",
    "method",
    "metric",
    "calculation_scale",
    "display_scale",
    "pooled",
    "studies",
}
_SCALE_BY_METRIC = {
    "Sens": ("logit", "proportion"),
    "Spec": ("logit", "proportion"),
    "PLR": ("log", "ratio"),
    "NLR": ("log", "ratio"),
    "DOR": ("log", "ratio"),
}
UNIVARIATE_DIAGNOSTIC_METHODS = frozenset(
    {
        "diagnostic.fixed.inv.var",
        "diagnostic.fixed.mh",
        "diagnostic.fixed.peto",
        "diagnostic.random",
    }
)


def _is_string_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping) and all(isinstance(key, str) for key in value)


class DiagnosticResultError(ValueError):
    """A diagnostic numerical result violates its public contract."""


@dataclass(frozen=True, slots=True)
class DiagnosticNumericValue:
    status: NumericStatus
    value: float | int | None
    reason: str | None

    def __post_init__(self) -> None:
        _validate_numeric_value(self.to_mapping(), "numeric value")

    def to_mapping(self) -> dict[str, object]:
        return {"status": self.status, "value": self.value, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class DiagnosticEffectEstimate:
    estimate: DiagnosticNumericValue
    lower: DiagnosticNumericValue
    upper: DiagnosticNumericValue

    def to_mapping(self) -> dict[str, object]:
        return {
            "estimate": self.estimate.to_mapping(),
            "lower": self.lower.to_mapping(),
            "upper": self.upper.to_mapping(),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticPooledNumerics:
    calculation: DiagnosticEffectEstimate
    display: DiagnosticEffectEstimate
    standard_error: DiagnosticNumericValue
    p_value: DiagnosticNumericValue
    study_count: DiagnosticNumericValue
    tau_squared: DiagnosticNumericValue
    q: DiagnosticNumericValue
    q_df: DiagnosticNumericValue
    q_p_value: DiagnosticNumericValue
    i_squared: DiagnosticNumericValue

    def to_mapping(self) -> dict[str, object]:
        return {
            "calculation": self.calculation.to_mapping(),
            "display": self.display.to_mapping(),
            "standard_error": self.standard_error.to_mapping(),
            "p_value": self.p_value.to_mapping(),
            "study_count": self.study_count.to_mapping(),
            "tau_squared": self.tau_squared.to_mapping(),
            "q": self.q.to_mapping(),
            "q_df": self.q_df.to_mapping(),
            "q_p_value": self.q_p_value.to_mapping(),
            "i_squared": self.i_squared.to_mapping(),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticStudyNumerics:
    order: int
    label: str
    tp: DiagnosticNumericValue
    fn: DiagnosticNumericValue
    fp: DiagnosticNumericValue
    tn: DiagnosticNumericValue
    calculation: DiagnosticEffectEstimate
    display: DiagnosticEffectEstimate
    variance: DiagnosticNumericValue
    weight_fraction: DiagnosticNumericValue

    def to_mapping(self) -> dict[str, object]:
        return {
            "order": self.order,
            "label": self.label,
            "tp": self.tp.to_mapping(),
            "fn": self.fn.to_mapping(),
            "fp": self.fp.to_mapping(),
            "tn": self.tn.to_mapping(),
            "calculation": self.calculation.to_mapping(),
            "display": self.display.to_mapping(),
            "variance": self.variance.to_mapping(),
            "weight_fraction": self.weight_fraction.to_mapping(),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticAnalysisNumerics:
    version: int
    scope: Literal["univariate"]
    method: str
    metric: DiagnosticMetric
    calculation_scale: str
    display_scale: str
    pooled: DiagnosticPooledNumerics
    studies: tuple[DiagnosticStudyNumerics, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "scope": self.scope,
            "method": self.method,
            "metric": self.metric,
            "calculation_scale": self.calculation_scale,
            "display_scale": self.display_scale,
            "pooled": self.pooled.to_mapping(),
            "studies": [study.to_mapping() for study in self.studies],
        }


def parse_diagnostic_numerics(
    value: object,
    *,
    input_snapshot: DiagnosticInputSnapshot,
    method: str,
) -> DiagnosticAnalysisNumerics:
    """Validate authority-supplied values and align them to the frozen study order."""
    if not _is_string_mapping(value) or set(value) != _RESULT_FIELDS:
        raise DiagnosticResultError("diagnostic numerics have unknown or missing fields")
    if type(value["version"]) is not int or value["version"] != 1:
        raise DiagnosticResultError("unsupported diagnostic numerics version")
    if value["scope"] != "univariate":
        raise DiagnosticResultError("diagnostic result must identify a univariate model")
    if (
        not isinstance(method, str)
        or method not in UNIVARIATE_DIAGNOSTIC_METHODS
        or value["method"] != method
    ):
        raise DiagnosticResultError("diagnostic result method is not a supported univariate method")
    metric = value["metric"]
    if (
        not isinstance(metric, str)
        or metric not in DIAGNOSTIC_METRICS
        or metric != input_snapshot.metric
    ):
        raise DiagnosticResultError("diagnostic result metric does not match its input snapshot")
    calculation_scale, display_scale = _SCALE_BY_METRIC[metric]
    if (
        value["calculation_scale"] != calculation_scale
        or value["display_scale"] != display_scale
    ):
        raise DiagnosticResultError("diagnostic result scale does not match its measure")
    pooled = _pooled(value["pooled"])
    raw_studies = value["studies"]
    if (
        not isinstance(raw_studies, (list, tuple))
        or len(raw_studies) != len(input_snapshot.studies)
    ):
        raise DiagnosticResultError("diagnostic result must align with every included study")
    studies = tuple(
        _study(item, order=index, expected_study=source)
        for index, (item, source) in enumerate(zip(raw_studies, input_snapshot.studies))
    )
    if (
        pooled.study_count.status == "available"
        and cast(int, pooled.study_count.value) > len(studies)
    ):
        raise DiagnosticResultError("diagnostic pooled study count exceeds included rows")
    _check_interval(pooled.calculation, "pooled calculation interval")
    _check_interval(pooled.display, "pooled display interval")
    for index, study in enumerate(studies):
        _check_interval(study.calculation, f"study {index + 1} calculation interval")
        _check_interval(study.display, f"study {index + 1} display interval")
    return DiagnosticAnalysisNumerics(
        1,
        "univariate",
        method,
        cast(DiagnosticMetric, metric),
        calculation_scale,
        display_scale,
        pooled,
        studies,
    )


def _pooled(value: object) -> DiagnosticPooledNumerics:
    if not _is_string_mapping(value) or set(value) != _POOLED_FIELDS:
        raise DiagnosticResultError("diagnostic pooled numerics have unknown or missing fields")
    return DiagnosticPooledNumerics(
        _effect(value["calculation"], "pooled calculation"),
        _effect(value["display"], "pooled display"),
        _value(value["standard_error"], "pooled standard error", nonnegative=True),
        _value(value["p_value"], "pooled p-value", probability=True),
        _value(value["study_count"], "pooled study count", integer=True, nonnegative=True),
        _value(value["tau_squared"], "tau-squared", nonnegative=True),
        _value(value["q"], "Q statistic", nonnegative=True),
        _value(value["q_df"], "Q degrees of freedom", integer=True, nonnegative=True),
        _value(value["q_p_value"], "Q p-value", probability=True),
        _value(value["i_squared"], "I-squared", percentage=True),
    )


def _study(
    value: object,
    *,
    order: int,
    expected_study: DiagnosticStudyInput,
) -> DiagnosticStudyNumerics:
    if not _is_string_mapping(value) or set(value) != _STUDY_FIELDS:
        raise DiagnosticResultError("diagnostic study numerics have unknown or missing fields")
    if type(value["order"]) is not int or value["order"] != order:
        raise DiagnosticResultError("diagnostic study order must match the frozen input order")
    if value["label"] != expected_study.name:
        raise DiagnosticResultError("diagnostic study label does not match the frozen input order")
    counts = {
        field_name: _value(
            value[field_name],
            f"study {field_name.upper()} count",
            integer=True,
            nonnegative=True,
        )
        for field_name in ("tp", "fn", "fp", "tn")
    }
    for field_name, count in counts.items():
        expected_count = getattr(expected_study, field_name)
        if expected_count is None:
            if count.status != "not_available":
                raise DiagnosticResultError(
                    f"diagnostic study {field_name.upper()} availability "
                    "does not match its frozen input"
                )
        elif count.status != "available" or expected_count != count.value:
            raise DiagnosticResultError(
                f"diagnostic study {field_name.upper()} does not match its frozen input"
            )
    return DiagnosticStudyNumerics(
        order,
        expected_study.name,
        counts["tp"],
        counts["fn"],
        counts["fp"],
        counts["tn"],
        _effect(value["calculation"], "study calculation"),
        _effect(value["display"], "study display"),
        _value(value["variance"], "study variance", nonnegative=True),
        _value(value["weight_fraction"], "study weight", nonnegative=True, proportion=True),
    )


def _effect(value: object, label: str) -> DiagnosticEffectEstimate:
    if not _is_string_mapping(value) or set(value) != _EFFECT_FIELDS:
        raise DiagnosticResultError(f"{label} must contain estimate, lower, and upper")
    return DiagnosticEffectEstimate(
        _value(value["estimate"], f"{label} estimate"),
        _value(value["lower"], f"{label} lower bound"),
        _value(value["upper"], f"{label} upper bound"),
    )


def _value(
    value: object,
    label: str,
    *,
    integer: bool = False,
    nonnegative: bool = False,
    probability: bool = False,
    percentage: bool = False,
    proportion: bool = False,
) -> DiagnosticNumericValue:
    _validate_numeric_value(value, label)
    assert _is_string_mapping(value)
    number = value["value"]
    status = value["status"]
    if status == "available":
        assert isinstance(number, (int, float)) and not isinstance(number, bool)
        if integer and type(number) is not int:
            raise DiagnosticResultError(f"{label} must be an integer")
        if nonnegative and number < 0:
            raise DiagnosticResultError(f"{label} cannot be negative")
        if probability and not 0 <= number <= 1:
            raise DiagnosticResultError(f"{label} must be between zero and one")
        if percentage and not 0 <= number <= 100:
            raise DiagnosticResultError(f"{label} must be a percentage")
        if proportion and not 0 <= number <= 1:
            raise DiagnosticResultError(f"{label} must be a proportion")
    return DiagnosticNumericValue(
        cast(NumericStatus, status),
        cast(float | int | None, number),
        cast(str | None, value["reason"]),
    )


def _validate_numeric_value(value: object, label: str) -> None:
    if not _is_string_mapping(value) or set(value) != _VALUE_FIELDS:
        raise DiagnosticResultError(f"{label} has unknown or missing fields")
    status = value["status"]
    number = value["value"]
    reason = value["reason"]
    if not isinstance(status, str) or status not in {
        "available",
        "not_estimable",
        "not_available",
    }:
        raise DiagnosticResultError(f"{label} status is invalid")
    if status == "available":
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            raise DiagnosticResultError(f"{label} must be numeric when available")
        if not math.isfinite(float(number)):
            raise DiagnosticResultError(f"{label} must be finite")
        if reason is not None:
            raise DiagnosticResultError(f"{label} cannot include a reason when available")
    elif number is not None or not isinstance(reason, str) or not reason.strip():
        raise DiagnosticResultError(f"{label} unavailable values need a reason and no number")


def _check_interval(interval: DiagnosticEffectEstimate, label: str) -> None:
    values = (
        interval.lower.value,
        interval.estimate.value,
        interval.upper.value,
    )
    statuses = (
        interval.lower.status,
        interval.estimate.status,
        interval.upper.status,
    )
    if all(status == "available" for status in statuses):
        lower, estimate, upper = cast(tuple[float, float, float], values)
        if not lower <= estimate <= upper:
            raise DiagnosticResultError(f"{label} must contain its estimate")


def diagnostic_numerics_from_authority_model(
    input_snapshot: DiagnosticInputSnapshot,
    method: str,
    model: Mapping[str, object],
    convert_to_display: Callable[[Sequence[float | None]], Sequence[object]],
) -> DiagnosticAnalysisNumerics:
    """Normalize authority-returned model values without estimating missing values."""
    if not isinstance(method, str) or method not in UNIVARIATE_DIAGNOSTIC_METHODS:
        raise DiagnosticResultError("only supported univariate diagnostic methods have numerics")
    metric = input_snapshot.metric
    calculation = _effect_from_model(model)
    display = _display_effect(calculation, metric, convert_to_display)
    pooled = {
        "calculation": calculation,
        "display": display,
        "standard_error": _model_value(
            model, "se", "The statistical authority did not return a pooled standard error."
        ),
        "p_value": _model_value(
            model, "pval", "The statistical authority did not return a pooled p-value."
        ),
        "study_count": _model_value(
            model,
            "k",
            "The statistical authority did not return a pooled study count.",
        ),
        "tau_squared": _model_value(
            model, "tau2", "This method does not return between-study variance."
        ),
        "q": _model_value(
            model, "QE", "This method does not return a Q heterogeneity statistic."
        ),
        "q_df": _model_value(
            model,
            "QE.df",
            "The statistical authority did not return Q degrees of freedom.",
        ),
        "q_p_value": _model_value(
            model,
            "QEp",
            "This method does not return a Q heterogeneity p-value.",
        ),
        "i_squared": _model_value(
            model, "I2", "This method does not return an I-squared estimate."
        ),
    }
    model_studies = _study_vectors(model, len(input_snapshot.studies))
    try:
        calculation_estimates = [
            _available_number(value) for value in model_studies["estimates"]
        ]
        display_estimates = list(convert_to_display(calculation_estimates))
    except (ArithmeticError, TypeError, ValueError):
        display_estimates = [None] * len(input_snapshot.studies)
    if len(display_estimates) != len(input_snapshot.studies):
        display_estimates = [None] * len(input_snapshot.studies)

    rows = []
    for index, study in enumerate(input_snapshot.studies):
        calculation_estimate = model_studies["estimates"][index]
        display_estimate = _value_from_authority(
            display_estimates[index],
            "The statistical authority could not convert this study's estimate "
            "to its display scale.",
        )
        unavailable_interval = _missing(
            "The statistical authority did not return study-specific confidence limits."
        )
        rows.append(
            {
                "order": index,
                "label": study.name,
                "tp": _input_count(study.tp),
                "fn": _input_count(study.fn),
                "fp": _input_count(study.fp),
                "tn": _input_count(study.tn),
                "calculation": {
                    "estimate": calculation_estimate,
                    "lower": unavailable_interval,
                    "upper": unavailable_interval,
                },
                "display": {
                    "estimate": display_estimate,
                    "lower": unavailable_interval,
                    "upper": unavailable_interval,
                },
                "variance": model_studies["variances"][index],
                "weight_fraction": model_studies["weights"][index],
            }
        )
    return parse_diagnostic_numerics(
        {
            "version": 1,
            "scope": "univariate",
            "method": method,
            "metric": metric,
            "calculation_scale": _SCALE_BY_METRIC[metric][0],
            "display_scale": _SCALE_BY_METRIC[metric][1],
            "pooled": pooled,
            "studies": rows,
        },
        input_snapshot=input_snapshot,
        method=method,
    )


def _effect_from_model(model: Mapping[str, object]) -> dict[str, object]:
    return {
        "estimate": _model_value(
            model, "b", "The statistical authority did not return a pooled estimate."
        ),
        "lower": _model_value(
            model,
            "ci.lb",
            "The statistical authority did not return a lower confidence bound.",
        ),
        "upper": _model_value(
            model,
            "ci.ub",
            "The statistical authority did not return an upper confidence bound.",
        ),
    }


def _display_effect(
    calculation: Mapping[str, object],
    metric: str,
    convert_to_display: Callable[[Sequence[float | None]], Sequence[object]],
) -> dict[str, object]:
    numbers = [
        _available_number(calculation.get(key))
        for key in ("estimate", "lower", "upper")
    ]
    try:
        converted = list(convert_to_display(numbers))
    except (ArithmeticError, TypeError, ValueError):
        converted = [None, None, None]
    if len(converted) != 3:
        converted = [None, None, None]
    reason = (
        f"The statistical authority could not convert the {metric} estimate "
        "to its display scale."
    )
    return {
        key: _value_from_authority(value, reason)
        for key, value in zip(("estimate", "lower", "upper"), converted)
    }


def _study_vectors(model: Mapping[str, object], count: int) -> dict[str, list[dict[str, object]]]:
    return {
        "estimates": [
            _value_from_authority(
                value,
                "The statistical authority did not return this study's calculation-scale estimate.",
            )
            for value in _aligned_model_vector(model, ("yi.f", "yi"), count)
        ],
        "variances": [
            _value_from_authority(
                value,
                "The statistical authority did not return this study's variance.",
            )
            for value in _aligned_model_vector(model, ("vi.f", "vi"), count)
        ],
        "weights": [
            _value_from_authority(
                value,
                "The statistical authority did not return this study's weight.",
            )
            for value in _aligned_model_vector(model, ("study.weights",), count)
        ],
    }


def _aligned_model_vector(
    model: Mapping[str, object], keys: tuple[str, ...], count: int
) -> list[object]:
    for key in keys:
        if key not in model:
            continue
        value = model[key]
        if count == 1 and not isinstance(value, (list, tuple)):
            return [value]
        if isinstance(value, (list, tuple)) and len(value) == count:
            return list(value)
    return [None] * count


def _model_value(
    model: Mapping[str, object], key: str, missing_reason: str
) -> dict[str, object]:
    if key not in model:
        return _missing(missing_reason)
    return _value_from_authority(model[key], missing_reason)


def _value_from_authority(value: object, missing_reason: str) -> dict[str, object]:
    if value is None:
        return _missing(missing_reason)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return _unestimable("The statistical authority did not return a finite numeric value.")
    if not math.isfinite(float(value)):
        return _unestimable("The statistical authority did not return a finite numeric value.")
    return {"status": "available", "value": value, "reason": None}


def _available_number(value: object) -> float | None:
    if not _is_string_mapping(value) or value.get("status") != "available":
        return None
    number = value.get("value")
    if isinstance(number, bool) or not isinstance(number, (int, float)):
        return None
    return float(number)


def _input_count(value: int | None) -> dict[str, object]:
    if value is None:
        return _missing("Raw count data were not available for this study.")
    return {"status": "available", "value": value, "reason": None}


def _missing(reason: str) -> dict[str, object]:
    return {"status": "not_available", "value": None, "reason": reason}


def _unestimable(reason: str) -> dict[str, object]:
    return {"status": "not_estimable", "value": None, "reason": reason}
