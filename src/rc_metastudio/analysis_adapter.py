# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Typed, Qt-independent requests at the Analysis Adapter boundary."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
import hashlib
import json
from types import MappingProxyType
from typing import Literal, Protocol, TypeAlias, cast, runtime_checkable

from rc_metastudio.qt_object_guard import required
from rc_metastudio import r_bridge
from rc_metastudio import analysis_dataset
from rc_metastudio import result_formatting
from rc_metastudio.analysis_catalog import AnalysisFamily, FAMILY_METRICS
from rc_metastudio.analysis_results import AnalysisResult, ResultSection, parse_analysis_result
from rc_metastudio.analysis_errors import DiagnosticExecutionError
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


@runtime_checkable
class DiagnosticExecutionModel(Protocol):
    """Model queries required before diagnostic execution."""

    def included_studies_have_raw_data(self) -> bool: ...

    def included_studies_have_point_estimates(self, effect: str) -> bool: ...


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


@dataclass(frozen=True)
class StudySelectionResult:
    """Included studies that have values for every selected covariate."""

    studies: tuple[analysis_dataset.StudyRow, ...]
    has_missing_values: bool
    excluded_study_names: tuple[str, ...] = ()


class AnalysisService:
    """Own the process-global R boundary used by analysis configuration UI."""

    def prepare_method_dataset(self, model: object, data_type: str):
        if data_type == "binary":
            return _require_backend(lambda: r_bridge.dataset_to_simple_binary_r_object(model))
        if data_type == "continuous":
            return _require_backend(lambda: r_bridge.dataset_to_simple_continuous_r_object(model))
        if data_type == "diagnostic":
            return _require_backend(lambda: r_bridge.dataset_to_simple_diagnostic_r_object(model))
        if data_type in ("time_to_event", "event_rates"):
            return _require_backend(lambda: r_bridge.dataset_to_simple_ratio_r_object(model))
        raise ValueError(f"unsupported analysis data family: {data_type!r}")

    def available_methods(self, **query: object) -> Mapping[str, str]:
        return _require_backend(lambda: r_bridge.get_available_methods(**query))

    def parameters(self, method: str):
        return _require_backend(lambda: r_bridge.get_params(method))


    def plot_capabilities(
        self, data_type: str, method: str, *, workflow: str
    ) -> list[Mapping[str, object]]:
        return _require_backend(
            lambda: r_bridge.get_analysis_plot_capabilities(
                data_type, method, workflow=workflow
            )
        )

    def select_studies_for_covariates(
        self,
        model: CovariateSelectionModel,
        selected_covariates: Sequence[dict],
    ) -> StudySelectionResult:
        return select_studies_for_covariates(model, selected_covariates)

    def make_request(
        self,
        *,
        data_type: str,
        workflow: str | None,
        method: str,
        metric: str,
        parameters: Mapping[str, object],
    ) -> AnalysisRequest:
        return make_analysis_request(
            data_type=data_type,
            workflow=workflow,
            method=method,
            metric=metric,
            parameters=parameters,
        )

    def execute(
        self,
        model: object,
        requests: Sequence[AnalysisRequest],
        selected_covariates: Sequence[dict] = (),
    ) -> AnalysisResult:
        return execute_analysis_requests(model, requests, selected_covariates)

    def execute_meta_regression(
        self,
        model: MetaRegressionModel,
        studies: Sequence[analysis_dataset.StudyRow],
        selected_covariates: Sequence[dict],
        request: AnalysisRequest,
        fixed_effects: bool,
        default_confidence_level: AnalysisValue,
    ) -> AnalysisResult:
        return execute_meta_regression_request(
            model,
            studies,
            selected_covariates,
            request,
            fixed_effects,
            default_confidence_level,
        )


def _require_backend(operation):
    try:
        return operation()
    except KeyError as error:
        raise AnalysisBackendUnavailableError(
            "The embedded RCMetaR function registry is unavailable."
        ) from error


def select_studies_for_covariates(
    model: CovariateSelectionModel,
    selected_covariates: Sequence[dict],
) -> StudySelectionResult:
    """Select included studies with complete values for selected covariates."""
    sheet = required(model.current_sheet, "active sheet")
    covariate_values = {
        covariate['name']: {row.id:row.covariate_values[covariate['id']] for row in sheet.rows if row.covariate_values.get(covariate['id']) is not None and str(row.covariate_values[covariate['id']]).strip()}
        for covariate in selected_covariates
    }
    studies = []
    excluded_study_names = []
    has_missing_values = False
    for study in model.get_studies(only_if_included=True):
        if all(
            study.id in covariate_values[covariate['name']]
            for covariate in selected_covariates
        ):
            studies.append(study)
        else:
            has_missing_values = True
            excluded_study_names.append(str(study.label))
    return StudySelectionResult(
        tuple(studies), has_missing_values, tuple(excluded_study_names)
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
    normalized_metric = _required_text("metric", metric)
    if normalized_metric not in FAMILY_METRICS[normalized_data_type]:
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
    """Parse raw boundary data once; R bridge results are already typed."""
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
        return _execute_diagnostic_request(model, requests)
    if len(requests) != 1:
        raise ValueError("Standard execution requires exactly one request.")
    return _typed_result(r_bridge.run_model_analysis(
        model, requests[0].to_mapping(), **_conversion_kwargs(selected_covariates)
    ))


def _execute_diagnostic_request(
    model: object, requests: Sequence[AnalysisRequest]
) -> AnalysisResult:
    if not isinstance(model, DiagnosticExecutionModel):
        raise TypeError("Diagnostic execution requires the diagnostic model queries.")
    return _run_diagnostic_analysis_isolating_metric_failures(model, requests)


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
    return _typed_result(r_bridge.run_model_analysis(
        model, regression_request.to_mapping(), **conversion_kwargs,
    ))


def _run_diagnostic_backend(requests: Sequence[AnalysisRequest], data: object):
    wire_requests: list[Mapping[str, object]] = [
        request.to_mapping() for request in requests
    ]
    return r_bridge.run_versioned_analysis_requests(wire_requests, data)


def _diagnostic_direct_effects_need_metric_specific_data(model, requests):
    if model.included_studies_have_raw_data():
        return False

    joint_methods = [
        request for request in requests if request.method == "diagnostic.reitsma"
    ]
    if joint_methods:
        raise ValueError(
            "Reitsma bivariate model requires complete TP/FN/FP/TN counts; "
            "entered diagnostic effects cannot be used for this method."
        )

    missing_metrics = [
        request.metric
        for request in requests
        if not model.included_studies_have_point_estimates(effect=request.metric)
    ]
    if missing_metrics:
        raise ValueError(
            "Diagnostic analysis requires complete TP/FN/FP/TN counts or "
            "complete entered effect estimates and confidence intervals for "
            "each selected metric. Missing entered estimates for: %s."
            % ", ".join(missing_metrics)
        )

    return True


def _run_diagnostic_analysis_isolating_metric_failures(
    model: DiagnosticExecutionModel, requests: Sequence[AnalysisRequest],
) -> AnalysisResult:
    if _diagnostic_direct_effects_need_metric_specific_data(model, requests):
        return _run_diagnostic_with_metric_specific_data(model, requests)

    data = r_bridge.dataset_to_simple_diagnostic_r_object(model)
    try:
        return _typed_result(_run_diagnostic_backend(requests, data))
    except DiagnosticExecutionError as error:
        if len(requests) == 1:
            raise RuntimeError(_format_diagnostic_failures([(requests[0].metric, error)])) from error
        return _run_diagnostic_methods_per_metric(
            requests, lambda request: _run_diagnostic_backend((request,), data),
        )


def _run_diagnostic_with_metric_specific_data(model, requests):
    def run_metric(request: AnalysisRequest):
        data = r_bridge.dataset_to_simple_diagnostic_r_object(model, metric=request.metric)
        return _run_diagnostic_backend((request,), data)

    return _run_diagnostic_methods_per_metric(requests, run_metric)


def _run_diagnostic_methods_per_metric(requests, run_metric):
    results: list[AnalysisResult | ResultSection] = []
    failures = []
    for request in requests:
        metric = request.metric
        try:
            results.append(_typed_result(run_metric(request)))
        except DiagnosticExecutionError as error:
            failures.append((metric, error))
            title = f"{metric} Error"
            results.append(ResultSection(
                f"diagnostic.{metric.lower()}.error", "text", 0, title, str(error), title,
            ))

    successes = [result for result in results if isinstance(result, AnalysisResult)]
    if failures and not any(result.sections for result in successes):
        raise RuntimeError(_format_diagnostic_failures(failures))
    return _combine_diagnostic_results(results, successes)


def _combine_diagnostic_results(
    results: Sequence[AnalysisResult | ResultSection], successes: Sequence[AnalysisResult],
) -> AnalysisResult:
    return AnalysisResult(
        version=1,
        image_var_names=MappingProxyType({
            key: value for result in successes for key, value in result.image_var_names.items()
        }),
        image_order=tuple(key for result in successes for key in result.image_order or ()) or None,
        sections=_merge_diagnostic_sections(results),
        software=", ".join(dict.fromkeys(
            filter(None, (package for result in successes for package in result.software.split(", ")))
        )),
        inference_methods=tuple(dict.fromkeys(
            code for result in successes for code in result.inference_methods
        )),
    )


def _merge_diagnostic_sections(results: Sequence[AnalysisResult | ResultSection]) -> tuple[ResultSection, ...]:
    sections: list[ResultSection] = []
    references_index: int | None = None
    references = ""
    for result in results:
        if isinstance(result, ResultSection):
            sections.append(result)
            continue
        metric_sections = [s for s in result.sections if (s.kind, s.source_key) != ("text", "References")]
        sections.extend(metric_sections)
        reference_section = next((s for s in result.sections if (s.kind, s.source_key) == ("text", "References")), None)
        if reference_section is None or not reference_section.value.strip():
            continue
        references = _merge_reference_texts(references, reference_section.value)
        if references_index is None:
            references_index = len(sections)
            sections.append(reference_section)

    if references_index is not None:
        sections[references_index] = replace(sections[references_index], value=references)
    return tuple(replace(section, order=index) for index, section in enumerate(sections))


def _format_diagnostic_failures(failures):
    return "\n".join("%s failed: %s" % (metric, error) for metric, error in failures)


def _merge_reference_texts(existing, incoming):
    """Combine already-formatted reference sections without losing citations."""
    references = _reference_entries(existing) + _reference_entries(incoming)
    if not references:
        return ""
    return result_formatting.format_references(
        result_formatting.dedupe_references_preserving_order(references)
    )


def _reference_entries(value):
    if not value:
        return []
    if not isinstance(value, str):
        return [str(value)]
    entries = []
    for line in value.splitlines():
        line = line.strip()
        if not line:
            continue
        # parse_out_results numbers references for display.  Remove that
        # presentation detail before applying stable de-duplication.
        if ". " in line and line.split(". ", 1)[0].isdigit():
            line = line.split(". ", 1)[1]
        entries.append(line)
    return entries
