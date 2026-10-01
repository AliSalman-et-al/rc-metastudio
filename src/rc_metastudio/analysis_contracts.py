# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Low-level request and result contracts shared across analysis boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
from typing import Literal, TypeAlias


AnalysisValue: TypeAlias = bool | int | float | str | None
AnalysisFamily: TypeAlias = Literal["binary", "continuous", "diagnostic"]
AnalysisWorkflow: TypeAlias = Literal[
    "standard",
    "cumulative",
    "leave-one-out",
    "subgroup",
    "bootstrap",
    "meta-regression",
]


@dataclass(frozen=True)
class AnalysisParameter:
    """One normalized value passed to the R analysis boundary."""

    name: str
    value: AnalysisValue


@dataclass(frozen=True)
class AnalysisRequest:
    """A complete, locale-independent analysis invocation."""

    data_type: AnalysisFamily
    workflow: AnalysisWorkflow
    method: str
    metric: str
    parameters: tuple[AnalysisParameter, ...]
    version: int = 1

    def __post_init__(self) -> None:
        if self.version != 1:
            raise ValueError(f"unsupported analysis request version: {self.version}")
        _required_text("metric", self.metric)

    @property
    def semantic_id(self) -> str:
        """Stable identity for this request's meaning, excluding presentation."""
        payload = {
            "data_type": self.data_type,
            "metric": self.metric,
            "method": self.method,
            "parameters": [(item.name, item.value) for item in self.parameters],
            "version": self.version,
            "workflow": self.workflow,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def to_mapping(self) -> dict[str, object]:
        """Return the explicit wire representation consumed by RCMetaR."""
        parameters = self.parameter_values()
        parameters.setdefault("measure", self.metric)
        return {
            "version": self.version,
            "data_type": self.data_type,
            "workflow": self.workflow,
            "method": self.method,
            "metric": self.metric,
            "params": parameters,
        }

    def parameter_values(self) -> dict[str, AnalysisValue]:
        return {parameter.name: parameter.value for parameter in self.parameters}


PlotKind = Literal[
    "forest",
    "cumulative_forest",
    "leave_one_out_forest",
    "subgroup_forest",
    "regression",
    "roc",
    "sroc",
    "funnel",
    "contour_funnel",
    "deeks_funnel",
    "trimfill_funnel",
    "other",
]
PlotComposition = Literal["single"]
PlotRegenerator = Literal["forest", "regression", "funnel", "sroc", "none"]


@dataclass(frozen=True, slots=True)
class PlotCapability:
    """Immutable capability data attached to one semantic plot artifact."""

    plot_kind: PlotKind
    editable: bool
    styleable: bool
    composition: PlotComposition
    regenerator: PlotRegenerator


@dataclass(frozen=True, slots=True)
class ResultSection:
    """Stable result identity and stored display/regeneration data."""

    semantic_id: str
    kind: Literal["text", "image"]
    order: int
    title: str
    value: str
    source_key: str
    plot_kind: PlotKind | None = None
    plot_data: str | None = None
    capability: PlotCapability | None = None


@dataclass(frozen=True, slots=True)
class BinaryNumericValue:
    """A numerical result with an explicit availability state."""

    status: Literal["available", "not_estimable", "not_available"]
    value: float | int | None
    reason: str | None


@dataclass(frozen=True, slots=True)
class BinaryEstimate:
    estimate: BinaryNumericValue
    lower: BinaryNumericValue
    upper: BinaryNumericValue


@dataclass(frozen=True, slots=True)
class BinaryStudyNumerics:
    order: int
    label: str
    treatment_events: BinaryNumericValue
    treatment_total: BinaryNumericValue
    control_events: BinaryNumericValue
    control_total: BinaryNumericValue
    weight: BinaryNumericValue
    p_value: BinaryNumericValue
    calculation: BinaryEstimate
    display: BinaryEstimate


@dataclass(frozen=True, slots=True)
class BinaryPooledNumerics:
    calculation: BinaryEstimate
    display: BinaryEstimate
    study_count: BinaryNumericValue
    p_value: BinaryNumericValue


@dataclass(frozen=True, slots=True)
class BinaryNumerics:
    """Typed two-arm binary values returned by the statistical backend."""

    version: int
    metric: str
    calculation_scale: str
    display_scale: str
    weight_scale: Literal["percent"]
    calculation_null_value: float
    display_null_value: float
    pooled: BinaryPooledNumerics
    studies: tuple[BinaryStudyNumerics, ...]


@dataclass(frozen=True, slots=True)
class BinaryProportionStudyNumerics:
    order: int
    label: str
    events: BinaryNumericValue
    total: BinaryNumericValue
    calculation: BinaryEstimate
    display: BinaryEstimate


@dataclass(frozen=True, slots=True)
class BinaryProportionPooledNumerics:
    calculation: BinaryEstimate
    display: BinaryEstimate
    study_count: BinaryNumericValue
    back_transformation_denominators: tuple[int, ...] | None


@dataclass(frozen=True, slots=True)
class BinaryProportionNumerics:
    """Typed one-arm proportion values returned by RCMetaR."""

    version: int
    metric: str
    arm_label: str
    calculation_scale: str
    display_scale: Literal["proportion"]
    pooled: BinaryProportionPooledNumerics
    studies: tuple[BinaryProportionStudyNumerics, ...]


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Validated immutable result contract consumed by application adapters."""

    version: int
    texts: Mapping[str, str]
    images: Mapping[str, str]
    display_images: Mapping[str, str]
    image_var_names: Mapping[str, str]
    image_params_paths: Mapping[str, str]
    image_order: tuple[str, ...] | None
    plot_capabilities: Mapping[str, PlotCapability]
    sections: tuple[ResultSection, ...]
    binary_numerics: BinaryNumerics | None = None
    binary_proportion_numerics: BinaryProportionNumerics | None = None
    continuous_numerics: Mapping[str, object] | None = None
    diagnostic_numerics: Mapping[str, object] | None = None
    cumulative_numerics: Mapping[str, object] | None = None
    leave_one_out_numerics: Mapping[str, object] | None = None
    meta_regression_numerics: Mapping[str, object] | None = None
    reitsma_meta_regression_numerics: Mapping[str, object] | None = None
    reitsma_report: Mapping[str, object] | None = None
    subgroup_numerics: Mapping[str, object] | None = None
    subgroup_plan: Mapping[str, object] | None = None


_FAMILY_METRICS: Mapping[AnalysisFamily, frozenset[str]] = {
    "binary": frozenset(
        {"OR", "RD", "RR", "AS", "YUQ", "YUY", "PR", "PLN", "PLO", "PAS", "PFT"}
    ),
    "continuous": frozenset({"MD", "SMD", "TX Mean"}),
    "diagnostic": frozenset({"Sens", "Spec", "PLR", "NLR", "DOR"}),
}


def make_analysis_request(
    *,
    data_type: str,
    workflow: str | None,
    method: str,
    metric: str,
    parameters: Mapping[str, object],
) -> AnalysisRequest:
    """Validate and freeze values selected by a user-facing configuration."""
    normalized_data_type = _analysis_family(data_type)
    normalized_method = _required_text("analysis method", method)
    normalized_workflow = _analysis_workflow(workflow or "standard")
    normalized_metric = _required_text("metric", metric)
    if normalized_metric not in _FAMILY_METRICS[normalized_data_type]:
        raise ValueError(
            f"metric {normalized_metric!r} is not valid for {normalized_data_type} analysis"
        )
    normalized_parameters = tuple(
        AnalysisParameter(_required_text("parameter name", name), _native_value(value))
        for name, value in sorted(parameters.items())
    )
    return AnalysisRequest(
        data_type=normalized_data_type,
        workflow=normalized_workflow,
        method=normalized_method,
        metric=normalized_metric,
        parameters=normalized_parameters,
    )


def _required_text(label: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _analysis_family(value: object) -> AnalysisFamily:
    if value == "binary":
        return "binary"
    if value == "continuous":
        return "continuous"
    if value == "diagnostic":
        return "diagnostic"
    raise ValueError(f"unsupported analysis data family: {value!r}")


def _analysis_workflow(value: object) -> AnalysisWorkflow:
    if value == "standard":
        return "standard"
    if value == "cumulative":
        return "cumulative"
    if value == "leave-one-out":
        return "leave-one-out"
    if value == "subgroup":
        return "subgroup"
    if value == "bootstrap":
        return "bootstrap"
    if value == "meta-regression":
        return "meta-regression"
    raise ValueError(f"unsupported analysis workflow: {value!r}")


def _native_value(value: object) -> AnalysisValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError(
        "analysis parameters must be native bool, int, float, str, or None values; "
        f"received {type(value).__name__}"
    )
