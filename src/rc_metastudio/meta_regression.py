# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validated, immutable inputs and numeric results for univariate meta-regression.

RCMetaR 0.4.1 fits the study-level moderator matrix with ``metafor::rma.uni``.
This module freezes that matrix's meaning before execution and parses numerical
fields returned by the fitted model. It does not calculate predictions.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
import re
from typing import Literal, TypeAlias


MissingModeratorPolicy = Literal["reject", "exclude"]
InferenceMethod = Literal["z", "t", "knha", "adhoc"]
HeterogeneityMethod = Literal[
    "FE", "HE", "DL", "HS", "HSk", "SJ", "ML", "REML", "EB", "PM", "PMM"
]
ModeratorKind = Literal["continuous", "factor"]

_INFERENCE_METHODS = frozenset(("z", "t", "knha", "adhoc"))
_HETEROGENEITY_METHODS = frozenset(
    ("FE", "HE", "DL", "HS", "HSk", "SJ", "ML", "REML", "EB", "PM", "PMM")
)
_R_RESERVED_NAMES = frozenset(
    {
        "if", "else", "repeat", "while", "function", "for", "in", "next",
        "break", "TRUE", "FALSE", "NULL", "Inf", "NaN", "NA", "NA_integer_",
        "NA_real_", "NA_complex_", "NA_character_",
    }
)


@dataclass(frozen=True, slots=True)
class MetaRegressionStudy:
    """An included study's effect estimate and sampling standard error."""

    id: int
    label: str
    estimate: float
    standard_error: float


@dataclass(frozen=True, slots=True)
class ContinuousModerator:
    """A selected numeric moderator, with a disclosed coefficient unit.

    ``unit_step`` is the amount of the source value represented by one
    coefficient unit. For example, 10 and ``"10 years"`` fit a slope per
    decade when source values are recorded in years.
    """

    name: str
    unit: str
    values: tuple[object, ...]
    unit_step: float = 1.0


@dataclass(frozen=True, slots=True)
class FactorModerator:
    """A selected categorical moderator with an explicit treatment reference.

    ``levels`` is the level order supplied by the statistical authority. The
    pinned RCMetaR release sorts observed factor levels before applying
    treatment contrasts; callers must carry that order into the frozen plan.
    """

    name: str
    reference_level: str
    levels: tuple[str, ...]
    values: tuple[object, ...]


Moderator: TypeAlias = ContinuousModerator | FactorModerator


@dataclass(frozen=True, slots=True)
class MetaRegressionRequest:
    """One complete request for the supported generic regression core."""

    studies: tuple[MetaRegressionStudy, ...]
    moderators: tuple[Moderator, ...]
    heterogeneity_method: HeterogeneityMethod
    inference_method: InferenceMethod
    confidence_level: float
    missing_moderator_policy: MissingModeratorPolicy
    metric: str
    version: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.studies, tuple) or not isinstance(self.moderators, tuple):
            raise TypeError("meta-regression studies and moderators must be frozen tuples")
        if self.version != 1:
            raise ValueError(f"unsupported meta-regression request version: {self.version}")
        if not isinstance(self.metric, str) or not self.metric.strip():
            raise ValueError("meta-regression requires an effect measure")
        if self.heterogeneity_method not in _HETEROGENEITY_METHODS:
            raise ValueError("unsupported meta-regression heterogeneity method")
        if self.inference_method not in _INFERENCE_METHODS:
            raise ValueError("unsupported meta-regression inference method")
        if (
            isinstance(self.confidence_level, bool)
            or not isinstance(self.confidence_level, (int, float))
            or not math.isfinite(self.confidence_level)
            or not 0 < self.confidence_level < 100
        ):
            raise ValueError("confidence level must be greater than zero and less than 100")
        if self.missing_moderator_policy not in ("reject", "exclude"):
            raise ValueError("missing moderator policy must be 'reject' or 'exclude'")
        if not self.studies:
            raise ValueError("meta-regression requires at least one included study")
        if not self.moderators:
            raise ValueError("select at least one moderator before running meta-regression")
        if len({study.id for study in self.studies}) != len(self.studies):
            raise ValueError("meta-regression study identities must be unique")
        if len({moderator.name for moderator in self.moderators}) != len(self.moderators):
            raise ValueError("meta-regression moderator names must be unique")
        if any(not isinstance(study, MetaRegressionStudy) for study in self.studies):
            raise TypeError("meta-regression rows must be MetaRegressionStudy values")
        if any(
            not isinstance(moderator, (ContinuousModerator, FactorModerator))
            for moderator in self.moderators
        ):
            raise TypeError("meta-regression moderators must be typed selections")
        for study in self.studies:
            _required_text(study.label, "study label")
            _finite(study.estimate, "study effect estimate")
            standard_error = _finite(study.standard_error, "study standard error")
            if standard_error < 0:
                raise ValueError("study standard error cannot be negative")
        for moderator in self.moderators:
            _required_text(moderator.name, "moderator name")
            if not isinstance(moderator.values, tuple):
                raise TypeError("moderator values must be frozen tuples")
            if len(moderator.values) != len(self.studies):
                raise ValueError(
                    f"moderator '{moderator.name}' values do not match the included studies"
                )
            if isinstance(moderator, ContinuousModerator):
                _required_text(moderator.unit, f"unit for moderator '{moderator.name}'")
                step = _finite(moderator.unit_step, "moderator unit step")
                if step <= 0:
                    raise ValueError("moderator unit step must be greater than zero")
                _r_identifier(moderator.name)
            elif isinstance(moderator, FactorModerator):
                _required_text(moderator.reference_level, "factor reference level")
                _r_identifier(moderator.name)
                if (
                    not moderator.levels
                    or any(not isinstance(level, str) or not level for level in moderator.levels)
                    or len(set(moderator.levels)) != len(moderator.levels)
                ):
                    raise ValueError(
                        f"factor moderator '{moderator.name}' needs unique non-empty levels"
                    )
                if moderator.reference_level not in moderator.levels:
                    raise ValueError(
                        f"reference level '{moderator.reference_level}' is not a level of "
                        f"moderator '{moderator.name}'"
                    )
                if len(moderator.levels) < 2:
                    raise ValueError(
                        f"factor moderator '{moderator.name}' needs at least two levels"
                    )
            else:
                raise TypeError("unsupported meta-regression moderator type")


@dataclass(frozen=True, slots=True)
class CoefficientTerm:
    key: str
    label: str
    kind: Literal["intercept", "continuous", "factor_level"]
    moderator_name: str | None
    unit: str | None
    unit_step: float | None
    level: str | None
    reference_level: str | None


@dataclass(frozen=True, slots=True)
class ExcludedStudy:
    id: int
    label: str
    missing_moderators: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PlannedStudy:
    id: int
    label: str
    estimate: float
    standard_error: float
    moderator_values: tuple[float | str, ...]
    design_row: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class ModeratorCoding:
    name: str
    kind: ModeratorKind
    unit: str | None
    unit_step: float | None
    levels: tuple[str, ...]
    reference_level: str | None
    coefficient_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MetaRegressionPlan:
    request: MetaRegressionRequest
    formula: str
    moderators: tuple[ModeratorCoding, ...]
    coefficient_terms: tuple[CoefficientTerm, ...]
    studies: tuple[PlannedStudy, ...]
    excluded_studies: tuple[ExcludedStudy, ...]
    eligible_study_count: int
    coefficient_count: int
    residual_degrees_of_freedom: int


def prepare_meta_regression(request: MetaRegressionRequest) -> MetaRegressionPlan:
    """Freeze eligible rows and the exact coefficient columns before fitting."""
    moderator_by_study: dict[int, tuple[float | str, ...]] = {}
    excluded: list[ExcludedStudy] = []
    eligible_indices: list[int] = []
    for study_index, study in enumerate(request.studies):
        normalized: list[float | str] = []
        missing: list[str] = []
        for moderator in request.moderators:
            value = moderator.values[study_index]
            if _is_missing(value):
                missing.append(moderator.name)
                continue
            if isinstance(moderator, ContinuousModerator):
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError(
                        f"continuous moderator '{moderator.name}' must be numeric for "
                        f"study '{study.label}'"
                    )
                normalized.append(_finite(value, f"moderator '{moderator.name}' value") / moderator.unit_step)
            else:
                if not isinstance(value, str) or not value:
                    raise ValueError(
                        f"factor moderator '{moderator.name}' must be non-empty text for "
                        f"study '{study.label}'"
                    )
                if value not in moderator.levels:
                    raise ValueError(
                        f"factor value '{value}' for moderator '{moderator.name}' is not "
                        "in the declared authority level order"
                    )
                normalized.append(value)
        if missing:
            if request.missing_moderator_policy == "reject":
                names = ", ".join(missing)
                raise ValueError(
                    f"study '{study.label}' has missing selected moderator values: {names}; "
                    "correct them or explicitly choose exclusion"
                )
            excluded.append(ExcludedStudy(study.id, study.label, tuple(missing)))
            continue
        moderator_by_study[study_index] = tuple(normalized)
        eligible_indices.append(study_index)

    if not eligible_indices:
        raise ValueError("no included studies remain eligible for the selected moderators")

    codings: list[ModeratorCoding] = []
    terms: list[CoefficientTerm] = [
        CoefficientTerm(
            "intercept", "Intercept", "intercept", None, None, None, None, None
        )
    ]

    for moderator_index, moderator in enumerate(request.moderators):
        values = tuple(
            moderator_by_study[index][moderator_index]
            for index in eligible_indices
        )
        if isinstance(moderator, ContinuousModerator):
            key = f"moderator:{moderator.name}"
            codings.append(
                ModeratorCoding(
                    moderator.name,
                    "continuous",
                    moderator.unit,
                    moderator.unit_step,
                    (),
                    None,
                    (key,),
                )
            )
            terms.append(
                CoefficientTerm(
                    key,
                    f"{moderator.name} (per {_coefficient_unit(moderator)})",
                    "continuous",
                    moderator.name,
                    moderator.unit,
                    moderator.unit_step,
                    None,
                    None,
                )
            )
        else:
            observed = {str(value) for value in values}
            active_levels = tuple(
                level for level in moderator.levels if level in observed
            )
            if moderator.reference_level not in active_levels:
                raise ValueError(
                    f"factor reference level '{moderator.reference_level}' for "
                    f"'{moderator.name}' is absent from eligible studies"
                )
            if len(active_levels) < 2:
                raise ValueError(
                    f"factor moderator '{moderator.name}' has fewer than two observed "
                    "levels among eligible studies"
                )
            keys = tuple(
                f"moderator:{moderator.name}:level:{level}"
                for level in active_levels
                if level != moderator.reference_level
            )
            codings.append(
                ModeratorCoding(
                    moderator.name,
                    "factor",
                    None,
                    None,
                    active_levels,
                    moderator.reference_level,
                    keys,
                )
            )
            for level, key in zip(
                (level for level in active_levels if level != moderator.reference_level),
                keys,
                strict=True,
            ):
                terms.append(
                    CoefficientTerm(
                        key,
                        f"{moderator.name}: {level} vs {moderator.reference_level}",
                        "factor_level",
                        moderator.name,
                        None,
                        None,
                        level,
                        moderator.reference_level,
                    )
                )

    # RCMetaR's extract.cov.data forms all continuous columns first, then the
    # factor indicator columns in the authority-provided level order.
    terms = [terms[0]] + [term for term in terms[1:] if term.kind == "continuous"] + [
        term for term in terms[1:] if term.kind == "factor_level"
    ]
    formula_terms = [
        _r_identifier(moderator.name)
        for moderator in request.moderators
        if isinstance(moderator, ContinuousModerator)
    ] + [
        _r_identifier(moderator.name)
        for moderator in request.moderators
        if isinstance(moderator, FactorModerator)
    ]
    formula = "yi ~ 1 + " + " + ".join(formula_terms)

    planned_studies: list[PlannedStudy] = []
    for study_index in eligible_indices:
        values = moderator_by_study[study_index]
        design = [1.0]
        for term in terms[1:]:
            moderator_index = next(
                index
                for index, moderator in enumerate(request.moderators)
                if moderator.name == term.moderator_name
            )
            value = values[moderator_index]
            if term.kind == "continuous":
                if not isinstance(value, float):
                    value = float(value)
                design.append(value)
            elif term.kind == "factor_level":
                design.append(1.0 if value == term.level else 0.0)
        study = request.studies[study_index]
        planned_studies.append(
            PlannedStudy(
                study.id,
                study.label,
                study.estimate,
                study.standard_error,
                values,
                tuple(design),
            )
        )

    coefficient_count = len(terms)
    eligible_count = len(planned_studies)
    residual_df = eligible_count - coefficient_count
    if request.inference_method != "z" and residual_df <= 0:
        raise ValueError(
            "The selected inference method requires positive residual degrees of "
            f"freedom (studies: {eligible_count}, fitted coefficients: {coefficient_count})."
        )
    return MetaRegressionPlan(
        request,
        formula,
        tuple(codings),
        tuple(terms),
        tuple(planned_studies),
        tuple(excluded),
        eligible_count,
        coefficient_count,
        residual_df,
    )


@dataclass(frozen=True, slots=True)
class AvailableNumber:
    value: float
    status: Literal["available"] = "available"

    def __post_init__(self) -> None:
        if (
            isinstance(self.value, bool)
            or not isinstance(self.value, (int, float))
            or not math.isfinite(self.value)
        ):
            raise ValueError("available regression results must be finite numbers")

    def to_mapping(self) -> dict[str, object]:
        return {"status": self.status, "value": self.value, "reason": None}


@dataclass(frozen=True, slots=True)
class UnavailableNumber:
    reason: str
    status: Literal["not_estimable", "not_available"] = "not_available"

    def __post_init__(self) -> None:
        if (
            self.status not in {"not_estimable", "not_available"}
            or not isinstance(self.reason, str)
            or not self.reason.strip()
        ):
            raise ValueError("unavailable regression results need a reason and status")

    def to_mapping(self) -> dict[str, object]:
        return {"status": self.status, "value": None, "reason": self.reason}


NumericOutput: TypeAlias = AvailableNumber | UnavailableNumber


@dataclass(frozen=True, slots=True)
class CoefficientResult:
    term: CoefficientTerm
    estimate: NumericOutput
    standard_error: NumericOutput
    lower: NumericOutput
    upper: NumericOutput
    statistic_name: str
    statistic: NumericOutput
    degrees_of_freedom: NumericOutput
    p_value: NumericOutput

    def to_mapping(self) -> dict[str, object]:
        return {
            "term": _coefficient_term_mapping(self.term),
            "estimate": self.estimate.to_mapping(),
            "standard_error": self.standard_error.to_mapping(),
            "lower": self.lower.to_mapping(),
            "upper": self.upper.to_mapping(),
            "statistic_name": self.statistic_name,
            "statistic": self.statistic.to_mapping(),
            "degrees_of_freedom": self.degrees_of_freedom.to_mapping(),
            "p_value": self.p_value.to_mapping(),
        }


@dataclass(frozen=True, slots=True)
class RegressionTest:
    key: str
    label: str
    statistic_name: str
    statistic: NumericOutput
    numerator_degrees_of_freedom: NumericOutput
    denominator_degrees_of_freedom: NumericOutput
    p_value: NumericOutput

    def to_mapping(self) -> dict[str, object]:
        return {
            "key": self.key,
            "label": self.label,
            "statistic_name": self.statistic_name,
            "statistic": self.statistic.to_mapping(),
            "numerator_degrees_of_freedom": self.numerator_degrees_of_freedom.to_mapping(),
            "denominator_degrees_of_freedom": self.denominator_degrees_of_freedom.to_mapping(),
            "p_value": self.p_value.to_mapping(),
        }


@dataclass(frozen=True, slots=True)
class ResidualHeterogeneity:
    tau_squared: NumericOutput
    tau_squared_standard_error: NumericOutput
    i_squared_percent: NumericOutput
    h_squared: NumericOutput
    explained_percent: NumericOutput
    q: NumericOutput
    q_degrees_of_freedom: NumericOutput
    q_p_value: NumericOutput

    def to_mapping(self) -> dict[str, object]:
        return {
            "tau_squared": self.tau_squared.to_mapping(),
            "tau_squared_standard_error": self.tau_squared_standard_error.to_mapping(),
            "i_squared_percent": self.i_squared_percent.to_mapping(),
            "h_squared": self.h_squared.to_mapping(),
            "explained_percent": self.explained_percent.to_mapping(),
            "q": self.q.to_mapping(),
            "q_degrees_of_freedom": self.q_degrees_of_freedom.to_mapping(),
            "q_p_value": self.q_p_value.to_mapping(),
        }


@dataclass(frozen=True, slots=True)
class MetaRegressionNumerics:
    version: int
    formula: str
    metric: str
    heterogeneity_method: str
    inference_method: str
    confidence_level: float
    missing_moderator_policy: MissingModeratorPolicy
    moderators: tuple[ModeratorCoding, ...]
    eligible_study_ids: tuple[int, ...]
    excluded_studies: tuple[ExcludedStudy, ...]
    coefficient_count: int
    residual_degrees_of_freedom: int
    coefficients: tuple[CoefficientResult, ...]
    overall_test: RegressionTest
    moderator_tests: tuple[RegressionTest, ...]
    residual_heterogeneity: ResidualHeterogeneity

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "formula": self.formula,
            "metric": self.metric,
            "heterogeneity_method": self.heterogeneity_method,
            "inference_method": self.inference_method,
            "confidence_level": self.confidence_level,
            "missing_moderator_policy": self.missing_moderator_policy,
            "moderators": [_moderator_coding_mapping(value) for value in self.moderators],
            "eligible_study_ids": list(self.eligible_study_ids),
            "excluded_studies": [
                {
                    "id": study.id,
                    "label": study.label,
                    "missing_moderators": list(study.missing_moderators),
                }
                for study in self.excluded_studies
            ],
            "coefficient_count": self.coefficient_count,
            "residual_degrees_of_freedom": self.residual_degrees_of_freedom,
            "coefficients": [value.to_mapping() for value in self.coefficients],
            "overall_test": self.overall_test.to_mapping(),
            "moderator_tests": [value.to_mapping() for value in self.moderator_tests],
            "residual_heterogeneity": self.residual_heterogeneity.to_mapping(),
        }


def parse_meta_regression_result(
    plan: MetaRegressionPlan,
    fit: object,
    *,
    moderator_tests: Mapping[str, object] | None = None,
) -> MetaRegressionNumerics:
    """Parse actual ``metafor::rma.uni`` fields; never derive predictions.

    RCMetaR 0.4.1 returns categorical moderator block tests in its summary
    display, not in the model object. A caller may supply those exact test
    records from that display; omitted factor tests remain explicitly
    unavailable rather than being approximated from their coefficients.
    """
    if not isinstance(fit, Mapping):
        raise ValueError("meta-regression fit result must be a mapping")
    fit_values: dict[str, object] = {}
    for key, value in fit.items():
        if not isinstance(key, str):
            raise ValueError("meta-regression fit field names must be text")
        fit_values[key] = value
    k = _fit_number(fit_values.get("k"))
    p = _fit_number(fit_values.get("p"))
    if k is None or k != plan.eligible_study_count:
        raise ValueError(
            "RCMetaR fitted study count does not match the explicitly eligible study set"
        )
    if p is None or p != plan.coefficient_count:
        raise ValueError(
            "RCMetaR fitted coefficient count does not match the explicit moderator coding"
        )

    field_values = {
        name: _fit_vector(fit_values.get(name), expected=plan.coefficient_count, field=name)
        for name in ("b", "se", "ci.lb", "ci.ub", "zval", "pval")
    }
    statistic_name = "z" if plan.request.inference_method == "z" else "t"
    if plan.request.inference_method == "z":
        df_values = [
            UnavailableNumber("Normal-approximation coefficient tests do not use degrees of freedom.")
            for _ in plan.coefficient_terms
        ]
    else:
        df = _fit_number(fit_values.get("ddf"))
        if df is None:
            df = _fit_number(fit_values.get("k"))
            if df is not None:
                df -= _fit_number(fit_values.get("p")) or 0
        df_values = [
            _available(df)
            if df is not None and df > 0
            else _unavailable("RCMetaR did not return coefficient degrees of freedom.")
            for _ in plan.coefficient_terms
        ]

    coefficients = tuple(
        CoefficientResult(
            term,
            field_values["b"][index],
            field_values["se"][index],
            field_values["ci.lb"][index],
            field_values["ci.ub"][index],
            statistic_name,
            field_values["zval"][index],
            df_values[index],
            field_values["pval"][index],
        )
        for index, term in enumerate(plan.coefficient_terms)
    )

    residual_df = _available(plan.residual_degrees_of_freedom)
    t_inference = plan.request.inference_method != "z"
    overall_test = _test(
        "moderators.overall",
        "Overall moderators",
        "F" if t_inference else "QM",
        fit_values.get("QM"),
        fit_values.get("m"),
        plan.residual_degrees_of_freedom if t_inference else None,
        fit_values.get("QMp"),
        numerator_reason="RCMetaR did not return the moderator degrees of freedom.",
        denominator_reason="Normal-approximation omnibus tests do not use denominator degrees of freedom.",
    )
    parsed_moderator_tests = []
    provided_tests = moderator_tests or {}
    for coding in plan.moderators:
        if coding.kind != "factor":
            continue
        raw_test = provided_tests.get(coding.name)
        if raw_test is None:
            statistic = _unavailable(
                "RCMetaR 0.4.1 returns categorical moderator block tests in the summary, "
                "not in the fitted model object."
            )
            numerator_df = _unavailable(
                "The categorical block test was not available as structured output."
            )
            p_value = _unavailable(
                "The categorical block test was not available as structured output."
            )
            parsed_moderator_tests.append(
                RegressionTest(
                    f"moderator.{coding.name}",
                    f"{coding.name} (joint)",
                    "F" if t_inference else "QM",
                    statistic,
                    numerator_df,
                    residual_df if t_inference else _unavailable(
                        "Normal-approximation tests do not use denominator degrees of freedom."
                    ),
                    p_value,
                )
            )
            continue
        if not isinstance(raw_test, Mapping):
            raise ValueError(f"moderator test for '{coding.name}' must be a mapping")
        test_values: dict[str, object] = {}
        for key, value in raw_test.items():
            if not isinstance(key, str):
                raise ValueError("moderator test field names must be text")
            test_values[key] = value
        parsed_moderator_tests.append(
            _test(
                f"moderator.{coding.name}",
                f"{coding.name} (joint)",
                "F" if t_inference else "QM",
                test_values.get("statistic"),
                test_values.get("degrees_of_freedom"),
                test_values.get("denominator_degrees_of_freedom"),
                test_values.get("p_value"),
                numerator_reason="The authority did not return this moderator block's degrees of freedom.",
                denominator_reason="The authority did not return this moderator block's denominator degrees of freedom.",
            )
        )

    heterogeneity = ResidualHeterogeneity(
        tau_squared=_fit_output(fit_values, "tau2"),
        tau_squared_standard_error=_fit_output(fit_values, "se.tau2"),
        i_squared_percent=_fit_output(fit_values, "I2"),
        h_squared=_fit_output(fit_values, "H2"),
        explained_percent=_fit_output(fit_values, "R2"),
        q=_fit_output(fit_values, "QE"),
        q_degrees_of_freedom=residual_df,
        q_p_value=_fit_output(fit_values, "QEp"),
    )
    method = fit_values.get("method")
    if isinstance(method, (list, tuple)):
        method = method[0] if len(method) == 1 else None
    if method is not None and str(method) != plan.request.heterogeneity_method:
        raise ValueError("RCMetaR heterogeneity method does not match the frozen request")
    return MetaRegressionNumerics(
        version=1,
        formula=plan.formula,
        metric=plan.request.metric,
        heterogeneity_method=plan.request.heterogeneity_method,
        inference_method=plan.request.inference_method,
        confidence_level=float(plan.request.confidence_level),
        missing_moderator_policy=plan.request.missing_moderator_policy,
        moderators=plan.moderators,
        eligible_study_ids=tuple(study.id for study in plan.studies),
        excluded_studies=plan.excluded_studies,
        coefficient_count=plan.coefficient_count,
        residual_degrees_of_freedom=plan.residual_degrees_of_freedom,
        coefficients=coefficients,
        overall_test=overall_test,
        moderator_tests=tuple(parsed_moderator_tests),
        residual_heterogeneity=heterogeneity,
    )


def _test(
    key: str,
    label: str,
    statistic_name: str,
    statistic: object,
    numerator_df: object,
    denominator_df: object,
    p_value: object,
    *,
    numerator_reason: str,
    denominator_reason: str,
) -> RegressionTest:
    return RegressionTest(
        key,
        label,
        statistic_name,
        _optional_fit_output(
            statistic,
            f"{label} statistic was not returned.",
            unavailable_status="not_available",
        ),
        _optional_fit_output(
            numerator_df, numerator_reason, unavailable_status="not_available"
        ),
        _optional_fit_output(
            denominator_df, denominator_reason, unavailable_status="not_available"
        ),
        _optional_fit_output(
            p_value,
            f"{label} p-value was not returned.",
            unavailable_status="not_available",
        ),
    )


def _fit_vector(
    value: object, *, expected: int, field: str
) -> tuple[NumericOutput, ...]:
    if value is None:
        unavailable = _unavailable(
            f"RCMetaR did not return coefficient {field} values."
        )
        return tuple(unavailable for _ in range(expected))
    values = value if isinstance(value, (list, tuple)) else (value,)
    if len(values) != expected:
        raise ValueError(
            f"RCMetaR coefficient field '{field}' does not match the fitted coefficient count"
        )
    return tuple(
        _optional_fit_output(
            item, f"RCMetaR did not return an estimable coefficient {field} value."
        )
        for item in values
    )


def _fit_output(fit: Mapping[str, object], field: str) -> NumericOutput:
    if field not in fit:
        return _unavailable(f"RCMetaR did not return '{field}'.")
    return _optional_fit_output(fit.get(field), f"RCMetaR returned no finite '{field}' value.")


def _optional_fit_output(
    value: object,
    reason: str,
    *,
    unavailable_status: Literal["not_estimable", "not_available"] = "not_estimable",
) -> NumericOutput:
    number = _fit_number(value)
    return (
        _available(number)
        if number is not None
        else _unavailable(reason, status=unavailable_status)
    )


def _fit_number(value: object) -> float | None:
    if isinstance(value, (list, tuple)):
        if len(value) != 1:
            return None
        value = value[0]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _available(value: float | int) -> AvailableNumber:
    return AvailableNumber(float(value))


def _unavailable(
    reason: str,
    *,
    status: Literal["not_estimable", "not_available"] = "not_available",
) -> UnavailableNumber:
    return UnavailableNumber(reason, status)


def _coefficient_term_mapping(term: CoefficientTerm) -> dict[str, object]:
    return {
        "key": term.key,
        "label": term.label,
        "kind": term.kind,
        "moderator_name": term.moderator_name,
        "unit": term.unit,
        "unit_step": term.unit_step,
        "level": term.level,
        "reference_level": term.reference_level,
    }


def _moderator_coding_mapping(moderator: ModeratorCoding) -> dict[str, object]:
    return {
        "name": moderator.name,
        "kind": moderator.kind,
        "unit": moderator.unit,
        "unit_step": moderator.unit_step,
        "levels": list(moderator.levels),
        "reference_level": moderator.reference_level,
        "coefficient_keys": list(moderator.coefficient_keys),
    }


def _coefficient_unit(moderator: ContinuousModerator) -> str:
    step = moderator.unit_step
    if step == 1:
        return moderator.unit
    return f"{step:g} {moderator.unit}"


def _finite(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _is_missing(value: object) -> bool:
    return value is None or value == ""


def _required_text(value: object, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")


def _r_identifier(name: str) -> str:
    if "`" in name:
        raise ValueError("moderator names cannot contain a backtick")
    if (
        name not in _R_RESERVED_NAMES
        and re.fullmatch(r"[A-Za-z.][A-Za-z0-9._]*", name)
        and not re.match(r"^\.(?:\d|$)", name)
    ):
        return name
    return f"`{name}`"
