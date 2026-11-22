# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Typed, Qt-independent requests at the Analysis Adapter boundary."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Literal, Protocol, TypeAlias, cast

from rc_metastudio.qt_object_guard import required
from rc_metastudio import r_operations
from rc_metastudio.project import model as analysis_dataset
from rc_metastudio.analysis.catalog import AnalysisFamily, FAMILY_METRICS
from rc_metastudio.results.contract import AnalysisResult, parse_analysis_result
from rc_metastudio.r_runtime import AnalysisBackendUnavailableError


AnalysisValue: TypeAlias = bool | int | float | str | None
AnalysisWorkflow: TypeAlias = Literal[
    "standard",
    "cumulative",
    "leave-one-out",
    "subgroup",
    "bootstrap",
    "meta-regression",
]

class CovariateSelectionModel(Protocol):
    """Model operations required by covariate-qualified study selection."""

    @property
    def current_sheet(self) -> analysis_dataset.Sheet | None: ...

    def get_studies(
        self, only_if_included: bool = True
    ) -> list[analysis_dataset.StudyRow]: ...


class MetaRegressionModel(Protocol):
    """Model operation required by meta-regression conversion."""

    dataset: analysis_dataset.Dataset


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


@dataclass(frozen=True)
class StudySelectionResult:
    """Included studies that have values for every selected covariate."""

    studies: tuple[analysis_dataset.StudyRow, ...]
    has_missing_values: bool
    excluded_study_names: tuple[str, ...] = ()


class AnalysisService:
    """Query the R method registry for the analysis configuration UI."""

    def available_methods(
        self, *, model: object, for_data_type: str, metrics: Sequence[str],
        workflow: str | None,
    ) -> Mapping[str, str]:
        return _require_backend(lambda: r_operations.available_model_methods(
            model, for_data_type, metrics, workflow=workflow or "standard"
        ))

    def parameters(self, method: str):
        return _require_backend(lambda: r_operations.get_params(method))


    def plot_capabilities(
        self, data_type: str, method: str, *, workflow: str
    ) -> list[Mapping[str, object]]:
        return _require_backend(
            lambda: r_operations.get_analysis_plot_capabilities(
                data_type, method, workflow=workflow
            )
        )
def _require_backend(operation):
    try:
        return operation()
    except KeyError as error:
        raise AnalysisBackendUnavailableError(
            "The RCMetaR method registry is unavailable."
        ) from error


def select_studies_for_covariates(
    model: CovariateSelectionModel,
    selected_covariates: Sequence[dict],
) -> StudySelectionResult:
    """Select included studies with complete values for selected covariates."""
    required(model.current_sheet, "active sheet")
    covariate_ids = [covariate["id"] for covariate in selected_covariates]
    studies = []
    excluded_study_names = []
    for study in model.get_studies(only_if_included=True):
        values = (study.covariate_values.get(covariate_id) for covariate_id in covariate_ids)
        if all(value is not None and str(value).strip() for value in values):
            studies.append(study)
        else:
            excluded_study_names.append(str(study.label))
    return StudySelectionResult(
        tuple(studies), bool(excluded_study_names), tuple(excluded_study_names)
    )


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


def _typed_result(value: object) -> AnalysisResult:
    """Parse raw boundary data once; R worker results are already typed."""
    if isinstance(value, AnalysisResult):
        return value
    return parse_analysis_result(value)


def execute_analysis_requests(
    model: object,
    requests: Sequence[AnalysisRequest],
    selected_covariates: Sequence[dict] = (),
) -> AnalysisResult:
    """Execute a frozen set of analysis requests through the R backend."""
    if not requests:
        raise ValueError("No analysis requests were configured.")
    data_types = {request.data_type for request in requests}
    if len(data_types) != 1:
        raise ValueError("One execution cannot mix analysis data families.")
    data_type = requests[0].data_type
    if data_type == "diagnostic":
        return _typed_result(r_operations.run_model_diagnostic_analysis(
            model, [request.to_mapping() for request in requests]
        ))
    if len(requests) != 1:
        raise ValueError("Standard execution requires exactly one request.")
    return _typed_result(r_operations.run_model_analysis(
        model, requests[0].to_mapping(), **_conversion_kwargs(selected_covariates)
    ))


def _conversion_kwargs(
    selected_covariates: Sequence[dict],
) -> dict[str, object]:
    if not selected_covariates:
        return {}
    return {"covs_to_include": selected_covariates}


def execute_meta_regression_request(
    model: MetaRegressionModel,
    studies: Sequence[analysis_dataset.StudyRow],
    selected_covariates: Sequence[dict],
    request: AnalysisRequest,
    fixed_effects: bool,
    default_confidence_level: AnalysisValue,
) -> AnalysisResult:
    """Convert the dataset and execute one frozen meta-regression request."""
    conversion_kwargs = {
        "covs_to_include": selected_covariates,
        "studies": studies,
    }
    parameters = request.parameter_values()
    if request.data_type == "binary":
        parameters.setdefault("to", "only0")
        parameters.setdefault("adjust", 0.5)
    parameters.setdefault("conf.level", default_confidence_level)
    parameters["rm.method"] = (
        "FE" if fixed_effects else parameters.get("rm.method", "REML")
    )
    regression_request = replace(
        request,
        workflow="meta-regression",
        parameters=tuple(AnalysisParameter(name, value) for name, value in parameters.items()),
    )
    return _typed_result(r_operations.run_model_analysis(
        model, regression_request.to_mapping(), **conversion_kwargs,
    ))
