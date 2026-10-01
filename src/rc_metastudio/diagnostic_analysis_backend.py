# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Isolated producer for one diagnostic univariate backend request."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
import re
from typing import Protocol, TypeAlias, TypeGuard, cast

from rc_metastudio.analysis_results import AnalysisResult
from rc_metastudio.diagnostic_analysis_results import (
    DiagnosticAnalysisNumerics,
    DiagnosticResultError,
    UNIVARIATE_DIAGNOSTIC_METHODS,
    diagnostic_numerics_from_authority_model,
)
from rc_metastudio.diagnostic_analysis_snapshot import (
    DIAGNOSTIC_METRICS,
    DiagnosticInputSnapshot,
    DiagnosticMetric,
)


AnalysisScalar: TypeAlias = str | int | float | bool | None
_REQUEST_FIELDS = {"version", "data_type", "workflow", "method", "metric", "params"}
_R_SYMBOL = re.compile(r"^[A-Za-z][A-Za-z0-9_.]*$")


class _RGlobalEnvironment(Protocol):
    def __getitem__(self, key: str) -> object: ...

    def __setitem__(self, key: str, value: object) -> None: ...


def _is_string_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping) and all(isinstance(key, str) for key in value)


class DiagnosticBackend(Protocol):
    ro: object

    def _r_numeric_vector(self, values: object) -> object: ...

    def _r_character_vector(self, values: object) -> object: ...

    def _r_year_vector(self, values: object) -> object: ...

    def execute_r_function(self, name: str, *args: object, **kwargs: object) -> object: ...

    def get_available_methods(self, **kwargs: object) -> Mapping[str, str]: ...

    def get_params(self, method: str) -> tuple[object, object, object, object]: ...

    def get_method_description(self, method: str) -> str: ...

    def get_analysis_plot_capabilities(
        self, data_type: str, method: str, workflow: str = "standard"
    ) -> object: ...

    def run_versioned_analysis_request(
        self, request: Mapping[str, object], res_name: str, data_name: str
    ) -> AnalysisResult: ...

    def r_object_to_python(self, value: object) -> object: ...

    def diagnostic_convert_scale(
        self,
        value: list[float | None],
        metric: str,
        convert_to: str = "display.scale",
    ) -> list[object]: ...


@dataclass(frozen=True, slots=True)
class DiagnosticAnalysisRequest:
    version: int
    method: str
    metric: DiagnosticMetric
    parameters: tuple[tuple[str, AnalysisScalar], ...]

    def __post_init__(self) -> None:
        _validate_request_header(self)
        _validate_request_parameters(self.parameters)

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "data_type": "diagnostic",
            "workflow": "standard",
            "method": self.method,
            "metric": self.metric,
            "params": dict(self.parameters),
        }


def _validate_request_header(request: DiagnosticAnalysisRequest) -> None:
    if type(request.version) is not int or request.version != 1:
        raise ValueError("unsupported diagnostic analysis request version")
    if not isinstance(request.method, str) or request.method not in UNIVARIATE_DIAGNOSTIC_METHODS:
        raise ValueError("diagnostic request must select a supported univariate method")
    if not isinstance(request.metric, str) or request.metric not in DIAGNOSTIC_METRICS:
        raise ValueError("diagnostic request metric is unsupported")
    _validate_measure(request)


def _validate_measure(request: DiagnosticAnalysisRequest) -> None:
    if not any(
        name == "measure" and value == request.metric
        for name, value in request.parameters
    ):
        raise ValueError("diagnostic request measure must match its frozen input")


def _validate_request_parameters(parameters: tuple[tuple[str, AnalysisScalar], ...]) -> None:
    names = [name for name, _ in parameters]
    if any(not isinstance(name, str) or not name for name in names):
        raise ValueError("diagnostic request parameter names must be non-empty text")
    if len(set(names)) != len(parameters):
        raise ValueError("diagnostic request parameter names must be unique")
    for name, value in parameters:
        _validated_parameter_value(name, value)


def _validated_parameter_value(name: str, value: object) -> AnalysisScalar:
    if value is not None and not isinstance(value, (str, int, float, bool)):
        raise ValueError(f"diagnostic parameter {name!r} must be a scalar")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"diagnostic parameter {name!r} must be finite")
    return value


@dataclass(frozen=True, slots=True)
class DiagnosticAnalysisRun:
    input_snapshot: DiagnosticInputSnapshot
    request: DiagnosticAnalysisRequest
    result: AnalysisResult
    numerics: DiagnosticAnalysisNumerics


def create_diagnostic_request(
    input_snapshot: DiagnosticInputSnapshot,
    method: str,
    parameters: Mapping[str, object],
) -> DiagnosticAnalysisRequest:
    """Freeze a standard diagnostic request and its method settings."""
    if not isinstance(method, str) or method not in UNIVARIATE_DIAGNOSTIC_METHODS:
        raise ValueError("only supported univariate diagnostic methods can be run here")
    values: dict[str, AnalysisScalar] = {}
    for name, value in parameters.items():
        if not isinstance(name, str) or not name:
            raise ValueError("diagnostic parameter names must be non-empty text")
        values[name] = _validated_parameter_value(name, value)
    measure = values.get("measure")
    if measure is not None and measure != input_snapshot.metric:
        raise ValueError("diagnostic request measure does not match its input snapshot")
    values["measure"] = input_snapshot.metric
    return DiagnosticAnalysisRequest(
        1,
        method,
        input_snapshot.metric,
        tuple(sorted(values.items())),
    )


def diagnostic_request_from_mapping(
    value: object, input_snapshot: DiagnosticInputSnapshot
) -> DiagnosticAnalysisRequest:
    """Validate the explicit JSON request before it crosses the R boundary."""
    if not _is_string_mapping(value) or set(value) != _REQUEST_FIELDS:
        raise ValueError("diagnostic analysis request has unknown or missing fields")
    _validate_request_envelope(value)
    method = value["method"]
    metric = value["metric"]
    parameters = value["params"]
    if not isinstance(method, str) or not isinstance(metric, str):
        raise ValueError("diagnostic analysis method and metric must be text")
    if metric != input_snapshot.metric:
        raise ValueError("diagnostic request metric does not match its input snapshot")
    if not _is_string_mapping(parameters):
        raise ValueError("diagnostic request parameters must be an object")
    return create_diagnostic_request(input_snapshot, method, parameters)


def _validate_request_envelope(value: Mapping[str, object]) -> None:
    if (
        type(value["version"]) is not int
        or value["version"] != 1
        or value["data_type"] != "diagnostic"
        or value["workflow"] != "standard"
    ):
        raise ValueError("only standard univariate diagnostic requests are supported")


def create_diagnostic_r_data(
    input_snapshot: DiagnosticInputSnapshot,
    bridge: DiagnosticBackend,
    *,
    data_name: str = "tmp_obj",
) -> object:
    """Build one RCMetaR DiagnosticData object from the immutable snapshot."""
    _validate_r_symbol(data_name)
    studies = input_snapshot.studies
    covariates = _diagnostic_covariates(input_snapshot, bridge)
    kwargs: dict[str, object] = {
        "y": bridge._r_numeric_vector([study.estimate for study in studies]),
        "SE": bridge._r_numeric_vector(
            [study.standard_error for study in studies]
        ),
        "study.names": bridge._r_character_vector([study.name for study in studies]),
        "years": bridge._r_year_vector([study.year for study in studies]),
        "covariates": covariates,
    }
    if input_snapshot.input_source == "counts":
        kwargs.update(_diagnostic_count_vectors(input_snapshot, bridge))
    diagnostic_data = bridge.execute_r_function(
        "rcmetar.create.diagnostic.data", **kwargs
    )
    _global_environment(bridge)[data_name] = diagnostic_data
    return diagnostic_data


def _diagnostic_count_vectors(
    input_snapshot: DiagnosticInputSnapshot, bridge: DiagnosticBackend
) -> dict[str, object]:
    studies = input_snapshot.studies
    return {
        "TP": bridge._r_numeric_vector([study.tp for study in studies]),
        "FN": bridge._r_numeric_vector([study.fn for study in studies]),
        "FP": bridge._r_numeric_vector([study.fp for study in studies]),
        "TN": bridge._r_numeric_vector([study.tn for study in studies]),
    }


def _diagnostic_covariates(
    input_snapshot: DiagnosticInputSnapshot, bridge: DiagnosticBackend
) -> object:
    covariate_values = []
    for covariate in input_snapshot.covariates:
        if covariate.data_type == "continuous":
            r_values = bridge._r_numeric_vector(covariate.values)
        else:
            r_values = bridge._r_character_vector(
                [None if value is None else str(value) for value in covariate.values]
            )
        reference = next(
            (str(value) for value in covariate.values if value not in (None, "")),
            "",
        )
        covariate_values.append(
            bridge.execute_r_function(
                "rcmetar.create.covariate.values",
                **{
                    "cov.name": covariate.name,
                    "cov.vals": r_values,
                    "cov.type": covariate.data_type,
                    "ref.var": reference,
                },
            )
        )
    return bridge.execute_r_function("list", *covariate_values)


def diagnostic_method_catalogue(
    input_snapshot: DiagnosticInputSnapshot,
    bridge: DiagnosticBackend,
    *,
    data_name: str = "tmp_obj",
) -> dict[str, dict[str, object]]:
    """Return only methods RCMetaR accepts for the selected metric and data."""
    create_diagnostic_r_data(input_snapshot, bridge, data_name=data_name)
    methods = bridge.get_available_methods(
        for_data_type="diagnostic",
        data_obj_name=data_name,
        metric=input_snapshot.metric,
        workflow="standard",
    )
    catalogue: dict[str, dict[str, object]] = {}
    for label, method in methods.items():
        if not isinstance(method, str) or method not in UNIVARIATE_DIAGNOSTIC_METHODS:
            continue
        definitions, defaults, order, metadata = bridge.get_params(method)
        catalogue[method] = {
            "label": label,
            "parameters": definitions,
            "defaults": defaults,
            "order": order,
            "metadata": metadata,
            "description": bridge.get_method_description(method),
            "plot_capabilities": bridge.get_analysis_plot_capabilities(
                "diagnostic", method, workflow="standard"
            ),
        }
    return catalogue


def run_diagnostic_analysis(
    input_snapshot: DiagnosticInputSnapshot,
    request: DiagnosticAnalysisRequest,
    bridge: DiagnosticBackend,
    *,
    data_name: str = "tmp_obj",
    result_name: str = "rcms_diagnostic_result",
) -> DiagnosticAnalysisRun:
    """Run a single univariate request and retain typed authority output."""
    if request.metric != input_snapshot.metric:
        raise ValueError("diagnostic request metric does not match its input snapshot")
    _validate_r_symbol(data_name)
    _validate_r_symbol(result_name)
    if data_name == result_name:
        raise ValueError("diagnostic data and result symbols must differ")
    create_diagnostic_r_data(input_snapshot, bridge, data_name=data_name)
    result = bridge.run_versioned_analysis_request(
        request.to_mapping(), res_name=result_name, data_name=data_name
    )
    raw_result = _global_environment(bridge)[result_name]
    model = _authority_model(raw_result, bridge)
    numerics = diagnostic_numerics_from_authority_model(
        input_snapshot,
        request.method,
        model,
        lambda values: bridge.diagnostic_convert_scale(values, request.metric),
    )
    return DiagnosticAnalysisRun(input_snapshot, request, result, numerics)


def _authority_model(
    raw_result: object, bridge: DiagnosticBackend
) -> Mapping[str, object]:
    if _is_string_mapping(raw_result):
        summary = raw_result.get("Summary")
        if _is_string_mapping(summary):
            model = summary.get("MAResults")
            if _is_string_mapping(model):
                return model
    rx2 = getattr(raw_result, "rx2", None)
    if callable(rx2):
        summary = rx2("Summary")
        model = summary.rx2("MAResults")
        converted = bridge.r_object_to_python(model)
        if _is_string_mapping(converted):
            return converted
    raise DiagnosticResultError(
        "RCMetaR did not return the univariate diagnostic model values"
    )


def _global_environment(bridge: DiagnosticBackend) -> _RGlobalEnvironment:
    environment = getattr(getattr(bridge, "ro", None), "globalenv", None)
    if environment is None:
        raise RuntimeError("diagnostic backend has no R global environment")
    return cast(_RGlobalEnvironment, environment)


def _validate_r_symbol(value: str) -> None:
    if not isinstance(value, str) or _R_SYMBOL.fullmatch(value) is None:
        raise ValueError("diagnostic backend symbol is invalid")
