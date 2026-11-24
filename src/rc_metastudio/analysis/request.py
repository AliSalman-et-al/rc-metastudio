"""Immutable analysis requests and their RCMetaR wire representation."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from rc_metastudio.analysis.catalog import AnalysisFamily, AnalysisWorkflow, FAMILY_METRICS, analysis_workflow

type AnalysisValue = bool | int | float | str | None


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
        if type(self.version) is not int or self.version != 1:
            raise ValueError(f"unsupported analysis request version: {self.version}")
        _required_text("analysis method", self.method)
        _required_text("metric", self.metric)

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
    normalized_workflow = analysis_workflow(workflow or None)
    normalized_metric = _required_text("effect measure", metric)
    if normalized_metric not in FAMILY_METRICS[normalized_data_type]:
        raise ValueError(
            f"Effect measure {normalized_metric!r} is not valid for {normalized_data_type} analysis"
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
    if isinstance(value, str) and value in FAMILY_METRICS:
        return cast(AnalysisFamily, value)
    raise ValueError(f"unsupported analysis data family: {value!r}")


def _native_value(value: object) -> AnalysisValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError(
        "analysis parameters must be native bool, int, float, str, or None values; "
        f"received {type(value).__name__}"
    )
