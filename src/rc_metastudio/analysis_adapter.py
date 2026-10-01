# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Typed, Qt-independent requests at the Analysis Adapter boundary."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import copy
from dataclasses import dataclass
from typing import Protocol, cast, runtime_checkable

from rc_metastudio import r_bridge
from rc_metastudio import analysis_dataset
from rc_metastudio import result_sections
from rc_metastudio.analysis_contracts import (
    AnalysisResult,
    AnalysisFamily,
    AnalysisRequest,
    AnalysisValue,
    AnalysisWorkflow,
    make_analysis_request,
)
from rc_metastudio.analysis_results import parse_analysis_result
from rc_metastudio.analysis_errors import (
    DiagnosticExecutionError,
    PrimaryDiagnosticFitError,
)
from rc_metastudio import r_backend
from rc_metastudio.r_backend import AnalysisBackendUnavailableError


class CovariateDataset(Protocol):
    """Dataset operation required by covariate-qualified study selection."""

    def get_covariate_values(
        self, covariate: str, ids_for_keys: bool = False
    ) -> Mapping[int, object]: ...


class CovariateSelectionModel(Protocol):
    """Model operations required by covariate-qualified study selection."""

    dataset: CovariateDataset

    def get_studies(
        self, only_if_included: bool = True
    ) -> list[analysis_dataset.Study]: ...


class MetaRegressionModel(Protocol):
    """Model operation required by meta-regression conversion."""

    dataset: analysis_dataset.Dataset


@runtime_checkable
class DiagnosticExecutionModel(Protocol):
    """Model queries required before diagnostic execution."""

    def included_studies_have_raw_data(self) -> bool: ...

    def included_studies_have_point_estimates(self, effect: str) -> bool: ...


@dataclass(frozen=True)
class StudySelectionResult:
    """Included studies that have values for every selected covariate."""

    studies: tuple[analysis_dataset.Study, ...]
    has_missing_values: bool
    excluded_study_names: tuple[str, ...] = ()


class AnalysisService:
    """Own the process-global R boundary used by analysis configuration UI."""

    def prepare_method_dataset(
        self, model: object, data_type: str, *, var_name: str = "tmp_obj"
    ) -> None:
        bridge = r_backend.install_r_backend()
        if data_type == "binary":
            _require_backend(
                lambda: bridge.dataset_to_simple_binary_r_object(
                    model, var_name=var_name
                )
            )
            return
        if data_type == "continuous":
            _require_backend(
                lambda: bridge.dataset_to_simple_continuous_r_object(
                    model, var_name=var_name
                )
            )
            return
        if data_type == "diagnostic":
            _require_backend(
                lambda: bridge.dataset_to_simple_diagnostic_r_object(
                    model, var_name=var_name
                )
            )
            return
        raise ValueError(f"unsupported analysis data family: {data_type!r}")

    def available_methods(self, **query: object) -> Mapping[str, str]:
        bridge = r_backend.install_r_backend()
        return _require_backend(lambda: bridge.get_available_methods(**query))

    def parameters(self, method: str):
        bridge = r_backend.install_r_backend()
        return _require_backend(lambda: bridge.get_params(method))

    def method_description(self, method: str) -> str:
        bridge = r_backend.install_r_backend()
        return _require_backend(lambda: bridge.get_method_description(method))

    def plot_capabilities(
        self, data_type: str, method: str, *, workflow: str
    ) -> list[Mapping[str, object]]:
        bridge = r_backend.install_r_backend()
        return _require_backend(
            lambda: bridge.get_analysis_plot_capabilities(
                data_type, method, workflow=workflow
            )
        )

    def select_studies_for_covariates(
        self,
        model: CovariateSelectionModel,
        selected_covariates: Sequence[analysis_dataset.Covariate],
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
        selected_covariates: Sequence[analysis_dataset.Covariate] = (),
    ) -> AnalysisResult:
        r_backend.install_r_backend()
        return execute_analysis_requests(model, requests, selected_covariates)

    def execute_meta_regression(
        self,
        model: MetaRegressionModel,
        studies: Sequence[analysis_dataset.Study],
        selected_covariates: Sequence[analysis_dataset.Covariate],
        request: AnalysisRequest,
        fixed_effects: bool,
        default_confidence_level: AnalysisValue,
    ) -> AnalysisResult:
        r_backend.install_r_backend()
        return execute_meta_regression_request(
            model,
            studies,
            selected_covariates,
            request,
            fixed_effects,
            default_confidence_level,
        )

    def reset_working_directory(self) -> None:
        bridge = r_backend.install_r_backend()
        bridge.reset_r_working_directory()


class AnalysisMethodCatalogue:
    """Read-only method metadata returned by the isolated R worker."""

    def __init__(self, catalogue: Mapping[str, object]):
        self._data_type = catalogue.get("data_type", "binary")
        self._workflow = catalogue.get("workflow", "standard")
        if self._data_type not in ("binary", "continuous", "diagnostic"):
            raise ValueError("The analysis worker returned an unsupported data family.")
        if self._workflow not in ("standard", "cumulative", "leave-one-out", "subgroup"):
            raise ValueError("The analysis worker returned an unsupported workflow.")
        methods = catalogue.get("available_methods")
        details = catalogue.get("details")
        if not isinstance(methods, Mapping) or not isinstance(details, Mapping):
            raise ValueError("The analysis worker returned incomplete method metadata.")
        self._methods = copy.deepcopy(dict(methods))
        self._details = copy.deepcopy(dict(details))

    def prepare_method_dataset(
        self, _model: object, data_type: str, *, var_name: str = "tmp_obj"
    ) -> None:
        if data_type != self._data_type or var_name != "tmp_obj":
            raise ValueError("This method catalogue does not match the selected data.")

    def available_methods(self, **_query: object) -> Mapping[str, str]:
        return copy.deepcopy(self._methods)

    def parameters(self, method: str):
        detail = self._details.get(method)
        if not isinstance(detail, Mapping):
            raise KeyError(method)
        return (
            copy.deepcopy(detail["parameters"]),
            copy.deepcopy(detail["defaults"]),
            copy.deepcopy(detail["order"]),
            copy.deepcopy(detail["metadata"]),
        )

    def method_description(self, method: str) -> str:
        detail = self._details.get(method)
        if not isinstance(detail, Mapping):
            raise KeyError(method)
        return str(detail["description"])

    def plot_capabilities(
        self, data_type: str, method: str, *, workflow: str
    ) -> list[Mapping[str, object]]:
        if data_type != self._data_type or workflow != self._workflow:
            raise ValueError("This method catalogue does not match the selected data.")
        detail = self._details.get(method)
        if not isinstance(detail, Mapping):
            raise KeyError(method)
        return copy.deepcopy(detail["plot_capabilities"])

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


def _require_backend(operation):
    try:
        return operation()
    except KeyError as error:
        raise AnalysisBackendUnavailableError(
            "The embedded RCMetaR function registry is unavailable."
        ) from error


def select_studies_for_covariates(
    model: CovariateSelectionModel,
    selected_covariates: Sequence[analysis_dataset.Covariate],
) -> StudySelectionResult:
    """Select included studies with complete values for selected covariates."""
    covariate_values = {
        covariate.name: model.dataset.get_covariate_values(
            covariate.name, ids_for_keys=True
        )
        for covariate in selected_covariates
    }
    studies = []
    excluded_study_names = []
    has_missing_values = False
    for study in model.get_studies(only_if_included=True):
        if all(
            study.id in covariate_values[covariate.name]
            for covariate in selected_covariates
        ):
            studies.append(study)
        else:
            has_missing_values = True
            excluded_study_names.append(str(study.name))
    return StudySelectionResult(
        tuple(studies), has_missing_values, tuple(excluded_study_names)
    )


def _typed_result(value: object) -> AnalysisResult:
    """Parse raw boundary data once; R bridge results are already typed."""
    if isinstance(value, AnalysisResult):
        return value
    return parse_analysis_result(value)


def execute_analysis_requests(
    model: object,
    requests: Sequence[AnalysisRequest],
    selected_covariates: Sequence[analysis_dataset.Covariate] = (),
) -> AnalysisResult:
    """Execute a frozen set of analysis requests through the R backend."""
    if not requests:
        raise ValueError("No analysis requests were configured.")
    data_types = {request.data_type for request in requests}
    if len(data_types) != 1:
        raise ValueError("One execution cannot mix analysis data families.")
    data_type = requests[0].data_type
    if data_type == "binary":
        return _execute_binary_request(model, requests, selected_covariates)
    if data_type == "continuous":
        return _execute_continuous_request(model, requests, selected_covariates)
    if data_type == "diagnostic":
        return _execute_diagnostic_request(model, requests)
    raise ValueError("Unsupported analysis data family: %s" % data_type)


def _execute_binary_request(
    model: object,
    requests: Sequence[AnalysisRequest],
    selected_covariates: Sequence[analysis_dataset.Covariate],
) -> AnalysisResult:
    if len(requests) != 1:
        raise ValueError("Binary execution requires exactly one request.")
    r_bridge.dataset_to_simple_binary_r_object(
        model, **_conversion_kwargs(selected_covariates)
    )
    return _typed_result(r_bridge.run_versioned_analysis_request(requests[0].to_mapping()))


def _execute_continuous_request(
    model: object,
    requests: Sequence[AnalysisRequest],
    selected_covariates: Sequence[analysis_dataset.Covariate],
) -> AnalysisResult:
    if len(requests) != 1:
        raise ValueError("Continuous execution requires exactly one request.")
    r_bridge.dataset_to_simple_continuous_r_object(
        model, **_conversion_kwargs(selected_covariates)
    )
    return _typed_result(
        r_bridge.run_versioned_analysis_request(requests[0].to_mapping())
    )


def _execute_diagnostic_request(
    model: object, requests: Sequence[AnalysisRequest]
) -> AnalysisResult:
    if not isinstance(model, DiagnosticExecutionModel):
        raise TypeError("Diagnostic execution requires the diagnostic model queries.")
    return _run_diagnostic_analysis_isolating_metric_failures(model, requests)


def execute_small_study_effects_request(model, request):
    """Execute the dedicated immutable small-study effects request boundary."""
    from rc_metastudio.publication_bias import execute_small_study_effects

    return execute_small_study_effects(model, request)


def _conversion_kwargs(
    selected_covariates: Sequence[analysis_dataset.Covariate],
) -> dict[str, object]:
    if not selected_covariates:
        return {}
    return {"covs_to_include": selected_covariates}


def execute_meta_regression_request(
    model: MetaRegressionModel,
    studies: Sequence[analysis_dataset.Study],
    selected_covariates: Sequence[analysis_dataset.Covariate],
    request: AnalysisRequest,
    fixed_effects: bool,
    default_confidence_level: AnalysisValue,
) -> AnalysisResult:
    """Convert the dataset and execute one frozen meta-regression request."""
    _convert_meta_regression_dataset(model, studies, selected_covariates, request)
    parameters = request.parameter_values()
    if request.data_type == "binary":
        parameters.setdefault("to", "only0")
        parameters.setdefault("adjust", 0.5)
    parameters.setdefault("conf.level", default_confidence_level)
    parameters["rm.method"] = (
        "FE" if fixed_effects else parameters.get("rm.method", "DL")
    )
    versioned = dict(request.to_mapping())
    versioned["workflow"] = "meta-regression"
    versioned["params"] = parameters
    return _typed_result(_run_meta_regression_backend(request, versioned))


def _convert_meta_regression_dataset(
    model: MetaRegressionModel,
    studies: Sequence[analysis_dataset.Study],
    selected_covariates: Sequence[analysis_dataset.Covariate],
    request: AnalysisRequest,
) -> None:
    conversion_kwargs = {
        "covs_to_include": selected_covariates,
        "studies": studies,
    }
    if request.data_type == "diagnostic":
        r_bridge.dataset_to_simple_diagnostic_r_object(
            model, metric=request.metric, **conversion_kwargs
        )
    elif request.data_type == "continuous":
        r_bridge.dataset_to_simple_continuous_r_object(model, **conversion_kwargs)
    elif request.data_type == "binary":
        r_bridge.dataset_to_simple_binary_r_object(
            model, **conversion_kwargs
        )
    else:
        raise ValueError(
            "Unsupported meta-regression data family: %s" % request.data_type
        )


def _run_meta_regression_backend(
    request: AnalysisRequest, versioned: Mapping[str, object]
) -> object:
    try:
        result = r_bridge.run_versioned_analysis_request(versioned)
    except Exception as error:
        if not (
            isinstance(error, DiagnosticExecutionError)
            or r_bridge.is_r_runtime_error(error)
        ):
            raise
        if request.method == "diagnostic.reitsma":
            raise _primary_diagnostic_fit_error(request, error) from error
        raise
    return result


def _run_diagnostic_backend(workflow, method_names, parameter_values):
    requests = [
        {
            "version": 1,
            "data_type": "diagnostic",
            "workflow": workflow,
            "method": method,
            "metric": params.get("measure", "DOR"),
            "params": params,
        }
        for method, params in zip(method_names, parameter_values, strict=True)
    ]
    return r_bridge.run_versioned_analysis_requests(requests)


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


def _run_diagnostic_analysis_isolating_metric_failures(model, requests):
    if _diagnostic_direct_effects_need_metric_specific_data(model, requests):
        return _run_diagnostic_with_metric_specific_data(model, requests)

    r_bridge.dataset_to_simple_diagnostic_r_object(model)
    if len(requests) == 1 and requests[0].method == "diagnostic.reitsma":
        return _typed_result(_run_diagnostic_request(requests[0]))

    try:
        method_names = [request.method for request in requests]
        parameter_values = [request.parameter_values() for request in requests]
        workflow = requests[0].workflow
        return _typed_result(
            _run_diagnostic_backend(workflow, method_names, parameter_values)
        )
    except DiagnosticExecutionError:
        return _run_diagnostic_with_shared_data_per_metric(requests)


def _run_diagnostic_with_shared_data_per_metric(requests):
    return _run_diagnostic_methods_per_metric(requests, _run_diagnostic_request)


def _run_diagnostic_with_metric_specific_data(model, requests):
    def run_metric(request):
        r_bridge.dataset_to_simple_diagnostic_r_object(model, metric=request.metric)
        return _run_diagnostic_request(request)

    return _run_diagnostic_methods_per_metric(requests, run_metric)


def _run_diagnostic_request(request):
    try:
        return _run_diagnostic_backend(
            request.workflow, [request.method], [request.parameter_values()]
        )
    except DiagnosticExecutionError as error:
        if request.method == "diagnostic.reitsma":
            raise _primary_diagnostic_fit_error(request, error) from error
        raise


def _primary_diagnostic_fit_error(request, error):
    return PrimaryDiagnosticFitError(
        metric=request.metric,
        workflow=request.workflow,
        detail=str(error),
    )


def _run_diagnostic_methods_per_metric(requests, run_metric):
    merged_result = _empty_diagnostic_result()
    failures = []
    primary_fit_failures = []
    for request in requests:
        metric = request.metric
        try:
            metric_result = _typed_result(run_metric(request))
        except DiagnosticExecutionError as e:
            failures.append((metric, e))
            if isinstance(e, PrimaryDiagnosticFitError):
                primary_fit_failures.append(e)
            _record_diagnostic_metric_failure(merged_result, metric, e)
        else:
            _merge_diagnostic_result(merged_result, metric_result)

    return _finish_diagnostic_metric_results(
        merged_result, failures, primary_fit_failures
    )


def _finish_diagnostic_metric_results(
    merged_result: dict[str, object],
    failures: list[tuple[str, DiagnosticExecutionError]],
    primary_fit_failures: list[PrimaryDiagnosticFitError],
) -> AnalysisResult:
    if primary_fit_failures:
        raise primary_fit_failures[0]

    if failures and not _diagnostic_result_has_successes(_typed_result(merged_result)):
        raise RuntimeError(_format_diagnostic_failures(failures))

    if not merged_result["image_order"]:
        merged_result["image_order"] = None
    return _typed_result(merged_result)


def _record_diagnostic_metric_failure(
    merged_result: dict[str, object], metric: str, error: DiagnosticExecutionError
) -> None:
    title = "%s Error" % metric
    cast(dict[str, str], merged_result["texts"])[title] = str(error)
    sections = cast(list[dict[str, object]], merged_result["sections"])
    sections.append(
        {
            "id": "diagnostic.%s.error" % metric.lower(),
            "kind": "text",
            "order": len(sections),
            "title": title,
            "source_key": title,
        }
    )


def _empty_diagnostic_result() -> dict[str, object]:
    return {
        "version": 1,
        "texts": {},
        "images": {},
        "display_images": {},
        "image_var_names": {},
        "image_params_paths": {},
        "plot_capabilities": {},
        "image_order": [],
        "sections": [],
    }


def _merge_diagnostic_result(
    merged_result: dict[str, object], metric_result: AnalysisResult
) -> None:
    _merge_diagnostic_texts(merged_result, metric_result)
    _merge_diagnostic_artifacts(merged_result, metric_result)
    _merge_diagnostic_image_order(merged_result, metric_result)
    _merge_diagnostic_sections(merged_result, metric_result)


def _merge_diagnostic_texts(
    merged_result: dict[str, object], metric_result: AnalysisResult
) -> None:
    merged_texts = cast(dict[str, str], merged_result["texts"])
    metric_texts = metric_result.texts
    merged_references = _merge_reference_texts(
        merged_texts.get("References"), metric_texts.get("References")
    )
    if merged_references:
        merged_texts["References"] = merged_references
    merged_texts.update(
        {name: value for name, value in metric_texts.items() if name != "References"}
    )


def _merge_diagnostic_artifacts(
    merged_result: dict[str, object], metric_result: AnalysisResult
) -> None:
    for key, values in (
        ("images", metric_result.images),
        ("display_images", metric_result.display_images),
        ("image_var_names", metric_result.image_var_names),
        ("image_params_paths", metric_result.image_params_paths),
        (
            "plot_capabilities",
            {
                key: {
                    "plot_kind": capability.plot_kind,
                    "editable": capability.editable,
                    "styleable": capability.styleable,
                    "composition": capability.composition,
                    "regenerator": capability.regenerator,
                }
                for key, capability in metric_result.plot_capabilities.items()
            },
        ),
    ):
        cast(dict[str, object], merged_result[key]).update(values)


def _merge_diagnostic_image_order(
    merged_result: dict[str, object], metric_result: AnalysisResult
) -> None:
    image_order = metric_result.image_order
    if not image_order:
        return
    merged_order = cast(list[str] | None, merged_result["image_order"])
    if merged_order is None:
        merged_result["image_order"] = list(image_order)
        return
    merged_order.extend(image_order)


def _merge_diagnostic_sections(
    merged_result: dict[str, object], metric_result: AnalysisResult
) -> None:
    merged_texts = cast(dict[str, str], merged_result["texts"])
    merged_sections = cast(list[dict[str, object]], merged_result["sections"])
    reference_id = None
    for section in metric_result.sections:
        if section.kind == "text" and section.source_key == "References":
            reference_id = section.semantic_id
            continue
        merged_sections.append(
            {
                "id": section.semantic_id,
                "kind": section.kind,
                "order": len(merged_sections),
                "title": section.title,
                "source_key": section.source_key,
            }
        )
    if "References" in merged_texts and not any(
        section["source_key"] == "References" for section in merged_sections
    ):
        merged_sections.append(
            {
                "id": reference_id or "diagnostic.references",
                "kind": "text",
                "order": len(merged_sections),
                "title": "References",
                "source_key": "References",
            }
        )


def _diagnostic_result_has_successes(result: AnalysisResult) -> bool:
    return bool(
        result.images or any(not key.endswith(" Error") for key in result.texts)
    )


def _format_diagnostic_failures(failures):
    return "\n".join("%s failed: %s" % (metric, error) for metric, error in failures)


def _merge_reference_texts(existing, incoming):
    """Combine already-formatted reference sections without losing citations."""
    references = _reference_entries(existing) + _reference_entries(incoming)
    if not references:
        return ""
    return result_sections.format_references(
        result_sections.dedupe_references_preserving_order(references)
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
