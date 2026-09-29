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
        if type(self.version) is not int or self.version != 1:
            raise ValueError("unsupported diagnostic analysis request version")
        if not isinstance(self.method, str) or self.method not in UNIVARIATE_DIAGNOSTIC_METHODS:
            raise ValueError("diagnostic request must select a supported univariate method")
        if not isinstance(self.metric, str) or self.metric not in DIAGNOSTIC_METRICS:
            raise ValueError("diagnostic request metric is unsupported")
        if not any(name == "measure" and value == self.metric for name, value in self.parameters):
            raise ValueError("diagnostic request measure must match its frozen input")
        names = [name for name, _ in self.parameters]
        if any(not isinstance(name, str) or not name for name in names):
            raise ValueError("diagnostic request parameter names must be non-empty text")
        if len(set(names)) != len(self.parameters):
            raise ValueError("diagnostic request parameter names must be unique")
        for name, value in self.parameters:
            if value is not None and not isinstance(value, (str, int, float, bool)):
                raise ValueError(f"diagnostic parameter {name!r} must be a scalar")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f"diagnostic parameter {name!r} must be finite")

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "data_type": "diagnostic",
            "workflow": "standard",
            "method": self.method,
            "metric": self.metric,
            "params": dict(self.parameters),
        }


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
        if value is not None and not isinstance(value, (str, int, float, bool)):
            raise ValueError(f"diagnostic parameter {name!r} must be a scalar")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"diagnostic parameter {name!r} must be finite")
        values[name] = value
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
    if (
        type(value["version"]) is not int
        or value["version"] != 1
        or value["data_type"] != "diagnostic"
        or value["workflow"] != "standard"
    ):
        raise ValueError("only standard univariate diagnostic requests are supported")
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


def create_diagnostic_r_data(
    input_snapshot: DiagnosticInputSnapshot,
    bridge: DiagnosticBackend,
    *,
    data_name: str = "tmp_obj",
) -> object:
    """Build one RCMetaR DiagnosticData object from the immutable snapshot."""
    _validate_r_symbol(data_name)
    studies = input_snapshot.studies
    kwargs: dict[str, object] = {
        "y": bridge._r_numeric_vector([study.estimate for study in studies]),
        "SE": bridge._r_numeric_vector(
            [study.standard_error for study in studies]
        ),
        "study.names": bridge._r_character_vector([study.name for study in studies]),
        "years": bridge._r_year_vector([study.year for study in studies]),
        "covariates": bridge.execute_r_function("list"),
    }
    if input_snapshot.input_source == "counts":
        kwargs.update(
            {
                "TP": bridge._r_numeric_vector([study.tp for study in studies]),
                "FN": bridge._r_numeric_vector([study.fn for study in studies]),
                "FP": bridge._r_numeric_vector([study.fp for study in studies]),
                "TN": bridge._r_numeric_vector([study.tn for study in studies]),
            }
        )
    diagnostic_data = bridge.execute_r_function(
        "rcmetar.create.diagnostic.data", **kwargs
    )
    _global_environment(bridge)[data_name] = diagnostic_data
    return diagnostic_data


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
