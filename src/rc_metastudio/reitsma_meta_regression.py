# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Typed numerical results for RCMetaR's joint Reitsma meta-regression."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal


REQUIRED_MADA_VERSION = "0.5.12"
_CONDITIONAL_OUTPUT_REASON = (
    "RCMetaR does not provide conditional Reitsma predictions for this fit; "
    "no moderator profile and prediction implementation were supplied."
)

ModelSide = Literal["sensitivity", "false_positive_rate"]
EffectDirection = Literal["sensitivity", "specificity"]
UnavailableOutputName = Literal[
    "conditional_summary_operating_point", "adjusted_sroc", "sroc_auc"
]


@dataclass(frozen=True, slots=True)
class ExcludedStudy:
    """A researcher-approved exclusion retained with the fitted study set."""

    study_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class ModeratorCoding:
    """RCMetaR's effective coding for one selected moderator."""

    name: str
    kind: Literal["continuous", "factor"]
    levels: tuple[str, ...] = ()
    reference_level: str | None = None
    observed_range: tuple[float, float] | None = None


@dataclass(frozen=True, slots=True)
class ReitsmaCoefficient:
    """One authority-reported moderator coefficient on its modeled scale.

    The specificity odds-ratio table is the exact sign-reversed view of the
    false-positive-rate coefficients produced by RCMetaR. ``model_estimate``
    and its interval restore the native FPR model direction, while
    ``reported_odds_ratio`` preserves the clinical-scale display direction.
    """

    term: str
    model_side: ModelSide
    effect_direction: EffectDirection
    model_estimate: float
    standard_error: float
    model_statistic: float
    p_value: float
    model_ci_lower: float
    model_ci_upper: float
    reported_odds_ratio: float
    odds_ratio_ci_lower: float
    odds_ratio_ci_upper: float
    is_reference: bool


@dataclass(frozen=True, slots=True)
class LikelihoodRatioTest:
    """A likelihood-ratio comparison fitted with ML on the frozen study set."""

    label: str
    comparison: str
    statistic: float
    degrees_of_freedom: int
    p_value: float
    included_study_ids: tuple[str, ...]
    fit_estimator: Literal["ML"] = "ML"


@dataclass(frozen=True, slots=True)
class UnavailableOutput:
    """An intentionally omitted conditional output with its reason."""

    name: UnavailableOutputName
    reason: str = _CONDITIONAL_OUTPUT_REASON


@dataclass(frozen=True, slots=True)
class ReitsmaMetaRegressionResult:
    """Validated, portable summary of a joint Reitsma meta-regression."""

    formula: str
    estimator: Literal["REML", "ML"]
    correction_policy: str
    correction_factor: float
    package_version: str
    converged: bool
    eligible_study_ids: tuple[str, ...]
    exclusions: tuple[ExcludedStudy, ...]
    moderator_coding: tuple[ModeratorCoding, ...]
    sensitivity_coefficients: tuple[ReitsmaCoefficient, ...]
    false_positive_rate_coefficients: tuple[ReitsmaCoefficient, ...]
    overall_test: LikelihoodRatioTest
    moderator_tests: tuple[LikelihoodRatioTest, ...]
    unavailable_outputs: tuple[UnavailableOutput, ...]

    def to_mapping(self) -> dict[str, object]:
        """Return JSON-compatible data for saved results and offline reopen."""
        return {
            "schema": "reitsma-meta-regression-v1",
            "formula": self.formula,
            "estimator": self.estimator,
            "correction": {
                "policy": self.correction_policy,
                "factor": self.correction_factor,
            },
            "package_version": self.package_version,
            "converged": self.converged,
            "eligible_study_ids": list(self.eligible_study_ids),
            "exclusions": [
                {"study_id": item.study_id, "reason": item.reason}
                for item in self.exclusions
            ],
            "moderator_coding": [
                {
                    "name": item.name,
                    "kind": item.kind,
                    "levels": list(item.levels),
                    "reference_level": item.reference_level,
                    "observed_range": (
                        None
                        if item.observed_range is None
                        else list(item.observed_range)
                    ),
                }
                for item in self.moderator_coding
            ],
            "sensitivity_coefficients": [
                _coefficient_mapping(item)
                for item in self.sensitivity_coefficients
            ],
            "false_positive_rate_coefficients": [
                _coefficient_mapping(item)
                for item in self.false_positive_rate_coefficients
            ],
            "overall_ml_likelihood_ratio_test": _test_mapping(self.overall_test),
            "moderator_block_ml_tests": [
                _test_mapping(item) for item in self.moderator_tests
            ],
            "unavailable_outputs": [
                {"name": item.name, "reason": item.reason}
                for item in self.unavailable_outputs
            ],
        }


def parse_reitsma_meta_regression_result(
    summary: object,
    *,
    eligible_study_ids: Sequence[str],
    exclusions: Sequence[ExcludedStudy] = (),
) -> ReitsmaMetaRegressionResult:
    """Parse the structured ``Summary`` returned by pinned RCMetaR.

    ``summary`` is the RCMetaR summary mapping after converting data frames to
    row mappings at the R boundary.  Every reported estimate and test is
    passed through from that authority; this parser only validates shape and
    restores the native FPR sign after RCMetaR's specificity display transform.
    """
    source = _mapping(summary, "Reitsma meta-regression Summary")
    unsupported = {
        "Summary operating point",
        "SROC AUC",
        "Adjusted SROC",
    }.intersection(source)
    if unsupported:
        raise ValueError(
            "Conditional Reitsma outputs are unsupported for meta-regression: "
            + ", ".join(sorted(unsupported))
        )

    model = _mapping(source.get("Model information"), "Model information")
    formula, estimator, package_version = _model_identity(model)
    study_ids = _unique_ids(eligible_study_ids, "eligible study IDs")
    excluded = _exclusions(exclusions)
    _validate_fitted_study_ids(model, study_ids, excluded)
    moderator_coding = _moderator_coding(source.get("Moderator coding"))
    _validate_formula(formula, moderator_coding)
    sensitivity = _coefficients(
        source.get("Sensitivity coefficients"),
        "Sensitivity coefficients",
        model_side="sensitivity",
    )
    false_positive_rate = _coefficients(
        source.get("Specificity coefficients"),
        "Specificity coefficients",
        model_side="false_positive_rate",
    )
    _validate_reference_rows(sensitivity, moderator_coding)
    _validate_reference_rows(false_positive_rate, moderator_coding)
    overall, blocks = _moderator_tests(source, moderator_coding, study_ids)
    correction_policy, correction_factor, converged = _fit_status(model)

    return ReitsmaMetaRegressionResult(
        formula=formula,
        estimator=estimator,
        correction_policy=correction_policy,
        correction_factor=correction_factor,
        package_version=package_version,
        converged=converged,
        eligible_study_ids=study_ids,
        exclusions=excluded,
        moderator_coding=moderator_coding,
        sensitivity_coefficients=sensitivity,
        false_positive_rate_coefficients=false_positive_rate,
        overall_test=overall,
        moderator_tests=blocks,
        unavailable_outputs=(
            UnavailableOutput("conditional_summary_operating_point"),
            UnavailableOutput("adjusted_sroc"),
            UnavailableOutput("sroc_auc"),
        ),
    )


def _model_identity(model: Mapping[str, object]) -> tuple[str, Literal["REML", "ML"], str]:
    estimator_value = _choice(model.get("estimator"), {"REML", "ML"}, "estimator")
    estimator: Literal["REML", "ML"] = (
        "REML" if estimator_value == "REML" else "ML"
    )
    package_version = _text(model.get("package.version"), "mada package version")
    if package_version != REQUIRED_MADA_VERSION:
        raise ValueError(
            "Reitsma meta-regression requires pinned mada %s; received %s."
            % (REQUIRED_MADA_VERSION, package_version)
        )
    return _text(model.get("formula"), "model formula"), estimator, package_version


def _validate_fitted_study_ids(
    model: Mapping[str, object],
    study_ids: tuple[str, ...],
    exclusions: tuple[ExcludedStudy, ...],
) -> None:
    excluded_ids = {item.study_id for item in exclusions}
    if excluded_ids.intersection(study_ids):
        raise ValueError("an excluded study cannot also be eligible")
    if len(study_ids) != _integer(model.get("studies.used"), "studies used"):
        raise ValueError("eligible study IDs do not match the fitted study count")


def _validate_formula(formula: str, moderator_coding: tuple[ModeratorCoding, ...]) -> None:
    if not moderator_coding:
        raise ValueError("Reitsma meta-regression requires selected moderators")
    expected_formula = "cbind(tsens, tfpr) ~ " + " + ".join(
        "`%s`" % item.name.replace("`", "``") for item in moderator_coding
    )
    if formula != expected_formula:
        raise ValueError("model formula must match the selected joint moderators")


def _moderator_tests(
    source: Mapping[str, object],
    moderator_coding: tuple[ModeratorCoding, ...],
    study_ids: tuple[str, ...],
) -> tuple[LikelihoodRatioTest, tuple[LikelihoodRatioTest, ...]]:
    overall = _likelihood_test(
        source.get("Overall ML likelihood-ratio test"),
        label="All moderators",
        comparison="full model vs intercept-only model",
        study_ids=study_ids,
    )
    block_source = _mapping(
        source.get("Moderator block tests"), "Moderator block tests"
    )
    moderator_names = tuple(item.name for item in moderator_coding)
    if tuple(block_source) != moderator_names:
        raise ValueError("moderator block tests must match selected moderator order")
    blocks = tuple(
        _likelihood_test(
            block_source[name],
            label=name,
            comparison="full model vs model without moderator '%s'" % name,
            study_ids=study_ids,
        )
        for name in moderator_names
    )
    _validate_test_degrees(overall, blocks, moderator_coding)
    return overall, blocks


def _validate_test_degrees(
    overall: LikelihoodRatioTest,
    blocks: tuple[LikelihoodRatioTest, ...],
    moderator_coding: tuple[ModeratorCoding, ...],
) -> None:
    parameter_counts = tuple(
        len(item.levels) - 1 if item.kind == "factor" else 1
        for item in moderator_coding
    )
    if overall.degrees_of_freedom != 2 * sum(parameter_counts):
        raise ValueError("overall test df must cover both modeled sides")
    if any(
        test.degrees_of_freedom != 2 * parameter_count
        for test, parameter_count in zip(blocks, parameter_counts, strict=True)
    ):
        raise ValueError("moderator block test df must cover both modeled sides")


def _fit_status(model: Mapping[str, object]) -> tuple[str, float, bool]:
    correction_policy = _text(
        model.get("correction.policy"), "correction policy"
    )
    correction_factor = _finite_number(
        model.get("correction.factor"), "correction factor"
    )
    if correction_factor < 0:
        raise ValueError("correction factor must be non-negative")
    converged = model.get("converged")
    if type(converged) is not bool:
        raise ValueError("model convergence state must be boolean")
    return correction_policy, correction_factor, converged


def _coefficients(
    value: object,
    label: str,
    *,
    model_side: ModelSide,
) -> tuple[ReitsmaCoefficient, ...]:
    rows = _sequence(value, label)
    result: list[ReitsmaCoefficient] = []
    seen_terms: set[str] = set()
    effect_direction: EffectDirection = (
        "sensitivity" if model_side == "sensitivity" else "specificity"
    )
    for row_value in rows:
        row = _mapping(row_value, label + " row")
        term = _text(row.get("term"), label + " term")
        if term in seen_terms:
            raise ValueError("coefficient terms must be unique")
        seen_terms.add(term)
        estimate = _finite_number(row.get("Estimate"), label + " estimate")
        standard_error = _finite_number(
            row.get("Std. Error"), label + " standard error"
        )
        statistic = _finite_number(row.get("z"), label + " z statistic")
        p_value = _probability(row.get("Pr(>|z|)"), label + " p-value")
        lower_key, upper_key = _confidence_interval_columns(row)
        displayed_lower = _finite_number(row.get(lower_key), label + " CI lower")
        displayed_upper = _finite_number(row.get(upper_key), label + " CI upper")
        if displayed_lower > displayed_upper:
            raise ValueError("coefficient confidence interval bounds are reversed")
        odds_ratio = _positive_number(row.get("Odds Ratio"), label + " odds ratio")
        odds_ratio_lower = _positive_number(
            row.get("Odds Ratio lower"), label + " odds-ratio CI lower"
        )
        odds_ratio_upper = _positive_number(
            row.get("Odds Ratio upper"), label + " odds-ratio CI upper"
        )
        if odds_ratio_lower > odds_ratio_upper:
            raise ValueError("odds-ratio confidence interval bounds are reversed")
        _check_exp_transform(estimate, odds_ratio, label + " odds ratio")
        _check_exp_transform(displayed_lower, odds_ratio_lower, label + " lower bound")
        _check_exp_transform(displayed_upper, odds_ratio_upper, label + " upper bound")
        is_reference = term.endswith(" (reference)")
        if model_side == "false_positive_rate":
            model_estimate = -estimate
            model_lower = -displayed_upper
            model_upper = -displayed_lower
            model_statistic = -statistic
        else:
            model_estimate = estimate
            model_lower = displayed_lower
            model_upper = displayed_upper
            model_statistic = statistic
        result.append(
            ReitsmaCoefficient(
                term=term,
                model_side=model_side,
                effect_direction=effect_direction,
                model_estimate=model_estimate,
                standard_error=standard_error,
                model_statistic=model_statistic,
                p_value=p_value,
                model_ci_lower=model_lower,
                model_ci_upper=model_upper,
                reported_odds_ratio=odds_ratio,
                odds_ratio_ci_lower=odds_ratio_lower,
                odds_ratio_ci_upper=odds_ratio_upper,
                is_reference=is_reference,
            )
        )
    if not result:
        raise ValueError(label + " must contain moderator coefficients")
    return tuple(result)


def _moderator_coding(value: object) -> tuple[ModeratorCoding, ...]:
    source = _mapping(value, "Moderator coding")
    result: list[ModeratorCoding] = []
    for name, value in source.items():
        if not name:
            raise ValueError("moderator names must be non-empty")
        coding = _mapping(value, "coding for " + name)
        kind = _choice(
            coding.get("type"), {"continuous", "factor"}, name + " coding type"
        )
        result.append(
            _factor_coding(name, coding)
            if kind == "factor"
            else _continuous_coding(name, coding)
        )
    return tuple(result)


def _factor_coding(name: str, coding: Mapping[str, object]) -> ModeratorCoding:
    levels = tuple(
        _text(item, name + " level")
        for item in _sequence(coding.get("levels"), name + " levels")
    )
    if len(levels) < 2 or len(set(levels)) != len(levels):
        raise ValueError(name + " factor levels must be distinct")
    reference = _text(coding.get("reference"), name + " reference level")
    if reference not in levels:
        raise ValueError(name + " reference level must be one of its levels")
    return ModeratorCoding(
        name=name, kind="factor", levels=levels, reference_level=reference
    )


def _continuous_coding(name: str, coding: Mapping[str, object]) -> ModeratorCoding:
    range_value = coding.get("range")
    if range_value is None:
        return ModeratorCoding(name=name, kind="continuous")
    bounds = _sequence(range_value, name + " observed range")
    if len(bounds) != 2:
        raise ValueError(name + " observed range must have two bounds")
    lower = _finite_number(bounds[0], name + " observed range lower")
    upper = _finite_number(bounds[1], name + " observed range upper")
    if lower > upper:
        raise ValueError(name + " observed range bounds are reversed")
    return ModeratorCoding(name=name, kind="continuous", observed_range=(lower, upper))


def _validate_reference_rows(
    coefficients: tuple[ReitsmaCoefficient, ...],
    moderators: tuple[ModeratorCoding, ...],
) -> None:
    labels = [item.term for item in coefficients]
    for moderator in moderators:
        if moderator.kind != "factor":
            continue
        reference_label = "%s = %s (reference)" % (
            moderator.name,
            moderator.reference_level,
        )
        if labels.count(reference_label) != 1:
            raise ValueError(
                "factor reference coefficient row missing or duplicated: "
                + reference_label
            )


def _likelihood_test(
    value: object,
    *,
    label: str,
    comparison: str,
    study_ids: tuple[str, ...],
) -> LikelihoodRatioTest:
    source = _mapping(value, label + " likelihood-ratio test")
    if _text(source.get("moderator"), label + " moderator label") != label:
        raise ValueError(label + " likelihood-ratio test label does not match")
    statistic = _finite_number(source.get("statistic"), label + " statistic")
    if statistic < 0:
        raise ValueError(label + " likelihood-ratio statistic must be non-negative")
    degrees = _integer(source.get("df"), label + " degrees of freedom")
    if degrees < 1:
        raise ValueError(label + " degrees of freedom must be positive")
    return LikelihoodRatioTest(
        label=label,
        comparison=comparison,
        statistic=statistic,
        degrees_of_freedom=degrees,
        p_value=_probability(source.get("p.value"), label + " p-value"),
        included_study_ids=study_ids,
    )


def _confidence_interval_columns(row: Mapping[str, object]) -> tuple[str, str]:
    lower = sorted(key for key in row if key.endswith("%ci.lb"))
    upper = sorted(key for key in row if key.endswith("%ci.ub"))
    if len(lower) != 1 or len(upper) != 1:
        raise ValueError("coefficient row must contain one confidence interval")
    if lower[0].removesuffix(".lb") != upper[0].removesuffix(".ub"):
        raise ValueError("coefficient confidence interval levels do not match")
    return lower[0], upper[0]


def _check_exp_transform(value: float, expected: float, label: str) -> None:
    actual = math.exp(value)
    if not math.isclose(actual, expected, rel_tol=1e-7, abs_tol=1e-12):
        raise ValueError(label + " does not match the authority's log-odds estimate")


def _coefficient_mapping(value: ReitsmaCoefficient) -> dict[str, object]:
    return {
        "term": value.term,
        "model_side": value.model_side,
        "effect_direction": value.effect_direction,
        "model_estimate": value.model_estimate,
        "standard_error": value.standard_error,
        "model_statistic": value.model_statistic,
        "p_value": value.p_value,
        "model_ci_lower": value.model_ci_lower,
        "model_ci_upper": value.model_ci_upper,
        "reported_odds_ratio": value.reported_odds_ratio,
        "odds_ratio_ci_lower": value.odds_ratio_ci_lower,
        "odds_ratio_ci_upper": value.odds_ratio_ci_upper,
        "is_reference": value.is_reference,
    }


def _test_mapping(value: LikelihoodRatioTest) -> dict[str, object]:
    return {
        "label": value.label,
        "comparison": value.comparison,
        "statistic": value.statistic,
        "degrees_of_freedom": value.degrees_of_freedom,
        "p_value": value.p_value,
        "fit_estimator": value.fit_estimator,
        "included_study_ids": list(value.included_study_ids),
    }


def _mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(label + " must be a mapping")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(label + " keys must be text")
        result[key] = item
    return result


def _sequence(value: object, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(label + " must be a sequence")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + " must be non-empty text")
    return value


def _choice(value: object, choices: set[str], label: str) -> str:
    if not isinstance(value, str) or value not in choices:
        raise ValueError(label + " must be one of " + ", ".join(sorted(choices)))
    return value


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(label + " must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(label + " must be finite")
    return numeric


def _positive_number(value: object, label: str) -> float:
    numeric = _finite_number(value, label)
    if numeric <= 0:
        raise ValueError(label + " must be positive")
    return numeric


def _probability(value: object, label: str) -> float:
    numeric = _finite_number(value, label)
    if not 0 <= numeric <= 1:
        raise ValueError(label + " must be between 0 and 1")
    return numeric


def _integer(value: object, label: str) -> int:
    if type(value) is not int:
        raise ValueError(label + " must be an integer")
    return value


def _unique_ids(values: Sequence[str], label: str) -> tuple[str, ...]:
    result = tuple(_text(value, label) for value in values)
    if len(result) != len(set(result)):
        raise ValueError(label + " must be unique")
    return result


def _exclusions(values: Sequence[ExcludedStudy]) -> tuple[ExcludedStudy, ...]:
    result: list[ExcludedStudy] = []
    for item in values:
        if not isinstance(item, ExcludedStudy):
            raise ValueError("exclusions must be ExcludedStudy values")
        result.append(
            ExcludedStudy(
                _text(item.study_id, "excluded study ID"),
                _text(item.reason, "exclusion reason"),
            )
        )
    ids = [item.study_id for item in result]
    if len(ids) != len(set(ids)):
        raise ValueError("excluded study IDs must be non-empty and unique")
    return tuple(result)
