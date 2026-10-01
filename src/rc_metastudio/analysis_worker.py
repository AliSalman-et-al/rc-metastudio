# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Line-oriented child process for analyses, study calculations, and plot operations."""

from __future__ import annotations

import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
import traceback
from uuid import uuid4
import warnings
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, fields, is_dataclass
from typing import TYPE_CHECKING, Any, Protocol, TypeGuard, cast

from rc_metastudio.analysis_contracts import AnalysisResult, PlotRegenerator
from rc_metastudio.analysis_worker_support import _create_binary_data, _wire_result
from rc_metastudio.plot_render_state import (
    MAX_RENDER_STATE_BYTES,
    MAX_TOTAL_RENDER_STATE_BYTES,
    is_plot_presentation,
    is_render_state,
    render_state_size,
    render_state_matches_capability,
)
from rc_metastudio.analysis_snapshot import (
    BinaryCovariateInput,
    BinaryInputSnapshot,
    BinaryStudyInput,
    SingleArmBinaryStudyInput,
)
from rc_metastudio.meta_globals import BINARY_ONE_ARM_METRICS

if TYPE_CHECKING:
    from rc_metastudio.continuous_analysis_snapshot import ContinuousInputSnapshot
    from rc_metastudio.cumulative_analysis import (
        CumulativeAnalysisSnapshot,
        CumulativeInputSnapshot,
    )
    from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot
    from rc_metastudio.analysis_contracts import AnalysisRequest
    from rc_metastudio.subgroup_analysis import SubgroupPlan
    from rc_metastudio.plot_service import PlotService
    from rc_metastudio.small_study_effects_core import (
        SmallStudyEffectsInput,
        SmallStudyEffectsService,
    )


_PLOT_OPERATIONS = frozenset(
    ("plot_parameters", "plot_export", "plot_edit", "saved_plot_render")
)
_PLOT_REGENERATORS = frozenset(("forest", "regression", "funnel", "sroc"))
_PLOT_EXTENSIONS = frozenset(("pdf", "png", "tif", "tiff", "svg"))


@dataclass(frozen=True)
class _SavedPlotRenderRequest:
    identity: dict[str, object]
    figure_key: str
    stage: Path
    output_path: Path
    display_path: Path | None
    renderer_state: dict[str, object]
    presentation: Mapping[str, object]


class _RContext(Protocol):
    globalenv: MutableMapping[str, object]


class _RObject(Protocol):
    def rx2(self, name: str) -> object: ...


class _LibraryLoader(Protocol):
    def load_metafor(self) -> object: ...

    def load_rcmetar(self) -> object: ...

    def load_grid(self) -> object: ...


class _WorkerBridge(Protocol):
    ro: _RContext

    def _r_numeric_vector(self, values: object) -> object: ...

    def _r_character_vector(self, values: object) -> object: ...

    def _r_year_vector(self, values: object) -> object: ...

    def execute_r_function(
        self, function_name: str, *args: object, **kwargs: object
    ) -> object: ...

    def r_object_to_python(self, value: object) -> object: ...

    def binary_convert_scale(
        self,
        value: object,
        metric: str,
        *,
        convert_to: str,
        n1: object = None,
    ) -> object: ...

    def get_r_version_string(self) -> str: ...

    def get_r_package_version(self, package: str) -> str: ...

    def get_available_methods(self, **query: object) -> Mapping[str, str]: ...

    def get_params(
        self, method: str
    ) -> tuple[object, object, object, object]: ...

    def get_method_description(self, method: str) -> object: ...

    def get_analysis_plot_capabilities(
        self, data_type: str, method: str, *, workflow: str
    ) -> object: ...

    def RLibraryLoader(self) -> _LibraryLoader: ...

    def run_versioned_analysis_request(
        self, request: Mapping[str, object]
    ) -> AnalysisResult: ...

    def load_vars_for_plot(
        self, params_path: str, return_params_dict: bool = False
    ) -> object: ...

    def update_plot_params(
        self,
        plot_params: Mapping[str, object],
        plot_params_name: str = "params",
        write_them_out: bool = False,
        outpath: str | None = None,
    ) -> object: ...

    def regenerate_plot_data(self) -> object: ...

    def regenerate_regression_plot_data(self) -> object: ...

    def regenerate_small_study_effects_funnel(
        self, params_path: str, output_path: str | None = None
    ) -> object: ...

    def load_in_r(self, path: str) -> object: ...

    def generate_forest_plot(self, path: str) -> object: ...

    def generate_reg_plot(self, path: str) -> object: ...

    def generate_sroc_plot(self, path: str) -> object: ...

    def generate_small_study_effects_funnel(self, path: str) -> object: ...

    def write_out_plot_data(
        self, params_out_path: str, plot_data_name: str = "plot.data"
    ) -> object: ...

    def project_plot_render_state(
        self,
        source_base: str,
        figure_key: str,
        plot_kind: str,
        regenerator: str,
    ) -> object: ...

    def render_saved_plot_state(
        self,
        state: Mapping[str, object],
        presentation: Mapping[str, object],
        figure_key: str,
        output_path: str,
        display_path: str | None = None,
    ) -> object: ...


def _is_string_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping) and all(isinstance(key, str) for key in value)


def _is_string_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _is_r_object(value: object) -> TypeGuard[_RObject]:
    return callable(getattr(value, "rx2", None))


def _required_row_int(row: Mapping[str, object], field: str) -> int:
    value = row.get(field)
    if type(value) is not int:
        raise ValueError("binary input study row has an invalid integer field")
    return value


def _optional_row_int(row: Mapping[str, object], field: str) -> int | None:
    value = row.get(field)
    if value is None or type(value) is int:
        return value
    raise ValueError("binary input study row has an invalid integer field")


def _optional_row_number(row: Mapping[str, object], field: str) -> float | None:
    value = row.get(field)
    if value is None or (
        isinstance(value, (int, float)) and not isinstance(value, bool)
    ):
        return value
    raise ValueError("binary input study row has an invalid numeric field")


def _required_row_text(row: Mapping[str, object], field: str) -> str:
    value = row.get(field)
    if isinstance(value, str):
        return value
    raise ValueError("binary input study row has an invalid text field")


def _snapshot_value(value: object) -> str | int | float | bool | None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ValueError("binary covariate values must be scalar")


def _is_plot_regenerator(value: object) -> TypeGuard[PlotRegenerator]:
    return isinstance(value, str) and (
        value in _PLOT_REGENERATORS or value == "none"
    )


def _analysis_snapshot(
    data_type: str, value: object
) -> BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot:
    if data_type == "binary":
        return _snapshot_from_mapping(value)
    if data_type == "continuous":
        from rc_metastudio.continuous_analysis_snapshot import ContinuousInputSnapshot

        return ContinuousInputSnapshot.from_mapping(value)
    if data_type == "diagnostic":
        from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot

        return DiagnosticInputSnapshot.from_mapping(value)
    raise ValueError("unsupported analysis worker data family")


def _send(message: Mapping[str, object]) -> None:
    sys.stdout.write(json.dumps(message, allow_nan=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _snapshot_from_mapping(value: object) -> BinaryInputSnapshot:
    if not _is_string_mapping(value) or value.get("version") != 1:
        raise ValueError("unsupported binary input snapshot")
    studies = value.get("studies")
    covariates = value.get("covariates")
    groups = value.get("groups")
    metric = value.get("metric")
    if not isinstance(studies, list) or not isinstance(covariates, list):
        raise ValueError("binary input snapshot rows are missing")
    one_arm = metric in BINARY_ONE_ARM_METRICS
    normalized_groups = _binary_snapshot_groups(groups, one_arm)
    study_rows = tuple(_binary_study_from_mapping(row, one_arm) for row in studies)
    covariate_rows = tuple(_binary_covariate_from_mapping(row) for row in covariates)
    return BinaryInputSnapshot(
        version=1,
        outcome=str(value.get("outcome", "")),
        time_point=str(value.get("time_point", "")),
        groups=normalized_groups,
        metric=str(metric or ""),
        raw_counts_available=value.get("raw_counts_available") is True,
        studies=study_rows,
        covariates=covariate_rows,
    )


def _binary_snapshot_groups(value: object, one_arm: bool) -> tuple[str, ...]:
    expected = 1 if one_arm else 2
    if not isinstance(value, list) or len(value) != expected:
        label = "one" if one_arm else "two"
        raise ValueError(f"binary input snapshot needs {label} group name(s)")
    return tuple(str(group) for group in value)


def _binary_study_from_mapping(
    value: object, one_arm: bool
) -> BinaryStudyInput | SingleArmBinaryStudyInput:
    if not _is_string_mapping(value):
        raise ValueError("binary input study rows must be objects")
    study_id = _required_row_int(value, "id")
    name = _required_row_text(value, "name")
    year = _optional_row_int(value, "year")
    estimate = _optional_row_number(value, "estimate")
    standard_error = _optional_row_number(value, "standard_error")
    if one_arm:
        return SingleArmBinaryStudyInput(
            id=study_id,
            name=name,
            year=year,
            estimate=estimate,
            standard_error=standard_error,
            events=_optional_row_int(value, "events"),
            total=_optional_row_int(value, "total"),
        )
    return BinaryStudyInput(
        id=study_id,
        name=name,
        year=year,
        estimate=estimate,
        standard_error=standard_error,
        treatment_events=_optional_row_int(value, "treatment_events"),
        treatment_total=_optional_row_int(value, "treatment_total"),
        control_events=_optional_row_int(value, "control_events"),
        control_total=_optional_row_int(value, "control_total"),
    )


def _binary_covariate_from_mapping(value: object) -> BinaryCovariateInput:
    if not _is_string_mapping(value):
        raise ValueError("binary covariate rows must include values")
    values = value.get("values")
    if not isinstance(values, list):
        raise ValueError("binary covariate rows must include values")
    return BinaryCovariateInput(
        str(value.get("name", "")),
        str(value.get("data_type", "")),
        tuple(_snapshot_value(item) for item in values),
    )


def _one_arm_binary_numerics(
    snapshot: BinaryInputSnapshot,
    request: Mapping[str, object],
    bridge: _WorkerBridge,
) -> dict[str, object]:
    """Attach raw and proportion-scale values from the RCMetaR fit object."""
    raw_result = bridge.ro.globalenv["result"]
    if not _is_r_object(raw_result):
        raise ValueError("RCMetaR did not return a proportion model result")
    fit_value = bridge.r_object_to_python(raw_result.rx2("res"))
    if not _is_string_mapping(fit_value):
        raise ValueError("RCMetaR did not return a proportion model result")

    calculation = _backend_estimate(fit_value, "b", "ci.lb", "ci.ub")
    denominators = (
        _study_denominators(snapshot)
        if snapshot.metric == "PFT" and snapshot.raw_counts_available
        else None
    )
    display = _display_estimate(
        bridge, snapshot.metric, calculation, denominators=denominators
    )
    fit_count = _fit_number(fit_value.get("k"))
    study_count = len(snapshot.studies) if fit_count is None else int(fit_count)
    multiplier = _confidence_multiplier(bridge, request)
    study_calculations = _study_estimates(fit_value, snapshot, multiplier)
    study_rows = _one_arm_study_rows(
        snapshot, study_calculations, bridge
    )

    return {
        "version": 1,
        "metric": snapshot.metric,
        "arm_label": snapshot.groups[0],
        "calculation_scale": _binary_proportion_scale(snapshot.metric),
        "display_scale": "proportion",
        "pooled": {
            "calculation": calculation,
            "display": display,
            "study_count": _available_integer(study_count),
            "back_transformation_denominators": (
                list(denominators) if denominators is not None else None
            ),
        },
        "studies": study_rows,
    }


def _one_arm_study_rows(
    snapshot: BinaryInputSnapshot,
    calculations: list[dict[str, dict[str, object]]],
    bridge: _WorkerBridge,
) -> list[dict[str, object]]:
    rows = []
    for index, study in enumerate(snapshot.studies):
        if not isinstance(study, SingleArmBinaryStudyInput):
            raise ValueError("single-arm result contains a two-arm study row")
        calculation = calculations[index]
        denominators = (study.total,) if study.total is not None else None
        rows.append(
            {
                "order": index,
                "label": study.name,
                "events": _available_integer(study.events),
                "total": _available_integer(study.total),
                "calculation": calculation,
                "display": _display_estimate(
                    bridge,
                    snapshot.metric,
                    calculation,
                    denominators=denominators,
                ),
            }
        )
    return rows


def _backend_estimate(
    fit: Mapping[str, object], estimate_name: str, lower_name: str, upper_name: str
) -> dict[str, dict[str, object]]:
    return {
        "estimate": _available_number(_fit_number(fit.get(estimate_name))),
        "lower": _available_number(_fit_number(fit.get(lower_name))),
        "upper": _available_number(_fit_number(fit.get(upper_name))),
    }


def _display_estimate(
    bridge: _WorkerBridge,
    metric: str,
    calculation: Mapping[str, Mapping[str, object]],
    *,
    denominators: tuple[int, ...] | None,
) -> dict[str, dict[str, object]]:
    return {
        key: _display_value(bridge, metric, value, denominators=denominators)
        for key, value in calculation.items()
    }


def _display_value(
    bridge: _WorkerBridge,
    metric: str,
    calculation: Mapping[str, object],
    *,
    denominators: tuple[int, ...] | None,
) -> dict[str, object]:
    if calculation.get("status") != "available":
        return dict(calculation)
    value = calculation.get("value")
    if metric == "PFT" and (denominators is None or not denominators):
        return _unavailable_number(
            "RCMetaR needs the included arm denominators to back-transform PFT."
        )
    try:
        display = bridge.binary_convert_scale(
            value,
            metric,
            convert_to="display.scale",
            n1=(
                bridge._r_numeric_vector(denominators)
                if denominators is not None
                else None
            ),
        )
    except Exception:
        return _unavailable_number(
            "RCMetaR could not back-transform this value."
        )
    number = _fit_number(display)
    if number is None:
        return _unavailable_number("RCMetaR did not return a finite proportion value.")
    return _available_number(number)


def _study_denominators(snapshot: BinaryInputSnapshot) -> tuple[int, ...] | None:
    totals = _single_arm_totals(snapshot)
    if len(totals) != len(snapshot.studies) or not _positive_totals(totals):
        return None
    return tuple(total for total in totals if total is not None)


def _single_arm_totals(snapshot: BinaryInputSnapshot) -> list[int | None]:
    return [
        study.total
        for study in snapshot.studies
        if isinstance(study, SingleArmBinaryStudyInput)
    ]


def _positive_totals(totals: list[int | None]) -> bool:
    return all(total is not None and total > 0 for total in totals)


def _study_estimates(
    fit: Mapping[str, object],
    snapshot: BinaryInputSnapshot,
    multiplier: float | None,
) -> list[dict[str, dict[str, object]]]:
    count = len(snapshot.studies)
    estimates, variances = _study_effect_vectors(fit, count)
    if len(estimates) != count or len(variances) != count or multiplier is None:
        return [_unavailable_estimate() for _ in snapshot.studies]
    return [
        _study_estimate(estimate, variance, multiplier)
        for estimate, variance in zip(estimates, variances, strict=True)
    ]


def _study_effect_vectors(
    fit: Mapping[str, object], count: int
) -> tuple[list[float | None], list[float | None]]:
    estimates = _number_list(fit.get("yi.f"))
    variances = _number_list(fit.get("vi.f"))
    if len(estimates) != count or len(variances) != count:
        estimates = _number_list(fit.get("yi"))
        variances = _number_list(fit.get("vi"))
    if count == 1 and (len(estimates) != 1 or len(variances) != 1):
        estimates = [_fit_number(fit.get("b"))]
        standard_error = _fit_number(fit.get("se"))
        variances = [standard_error * standard_error if standard_error is not None else None]
    return estimates, variances


def _study_estimate(
    estimate: float | None, variance: float | None, multiplier: float
) -> dict[str, dict[str, object]]:
    if estimate is None or variance is None or variance < 0:
        return _unavailable_estimate()
    standard_error = math.sqrt(variance)
    return {
        "estimate": _available_number(estimate),
        "lower": _available_number(estimate - multiplier * standard_error),
        "upper": _available_number(estimate + multiplier * standard_error),
    }


def _unavailable_estimate() -> dict[str, dict[str, object]]:
    unavailable = _unavailable_number("RCMetaR did not return an estimable value.")
    return {"estimate": unavailable, "lower": dict(unavailable), "upper": dict(unavailable)}


def _confidence_multiplier(
    bridge: _WorkerBridge, request: Mapping[str, object]
) -> float | None:
    params = request.get("params")
    conf_level = params.get("conf.level") if _is_string_mapping(params) else None
    if conf_level is None:
        multiplier = bridge.execute_r_function("rcmetar.get.mult.from.conf.level")
    else:
        if not isinstance(conf_level, (str, int, float)):
            raise TypeError("confidence level must be numeric")
        multiplier = bridge.execute_r_function(
            "rcmetar.get.mult.from.conf.level", float(conf_level)
        )
    return _fit_number(bridge.r_object_to_python(multiplier))


def _number_list(value: object) -> list[float | None]:
    if value is None:
        return []
    values = value if isinstance(value, (list, tuple)) else [value]
    return [_fit_number(item) for item in values]


def _fit_number(value: object) -> float | None:
    if isinstance(value, (list, tuple)):
        if len(value) != 1:
            return None
        value = value[0]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def _available_number(value: float | None) -> dict[str, object]:
    if value is None:
        return _unavailable_number("RCMetaR did not return an estimable value.")
    return {"status": "available", "value": value, "reason": None}


def _available_integer(value: int | None) -> dict[str, object]:
    if value is None:
        return _unavailable_number("Raw event counts are unavailable for this study.")
    return {"status": "available", "value": value, "reason": None}


def _unavailable_number(reason: str) -> dict[str, object]:
    return {"status": "not_available", "value": None, "reason": reason}


def _binary_proportion_scale(metric: str) -> str:
    return {
        "PR": "proportion",
        "PLN": "log",
        "PLO": "logit",
        "PAS": "arcsine",
        "PFT": "freeman_tukey",
    }[metric]


def _wire_methods(
    bridge: _WorkerBridge, data_type: str, metric: str, workflow: str
) -> dict[str, object]:
    methods = bridge.get_available_methods(
        for_data_type=data_type,
        data_obj_name="tmp_obj",
        metric=metric,
        workflow=workflow,
    )
    details = {}
    for method in methods.values():
        method = str(method)
        definitions, defaults, order, metadata = bridge.get_params(method)
        details[method] = {
            "parameters": definitions,
            "defaults": defaults,
            "order": order,
            "metadata": metadata,
            "description": str(bridge.get_method_description(method)),
            "plot_capabilities": bridge.get_analysis_plot_capabilities(
                data_type, method, workflow=workflow
            ),
        }
    return {
        "data_type": data_type,
        "workflow": workflow,
        "available_methods": methods,
        "details": details,
    }


def _wire_json(value: object) -> object:
    if is_dataclass(value):
        return _wire_dataclass(value)
    if isinstance(value, Mapping):
        return _wire_mapping(cast(Mapping[object, object], value))
    if isinstance(value, (tuple, list)):
        return _wire_sequence(cast(tuple[object, ...] | list[object], value))
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError("analysis metadata contains a non-JSON value: %s" % type(value).__name__)


def _wire_dataclass(value: object) -> dict[str, object]:
    return {
        item.name: _wire_json(getattr(value, item.name))
        for item in fields(cast(Any, value))
    }


def _wire_mapping(value: Mapping[object, object]) -> dict[str, object]:
    return {str(key): _wire_json(item) for key, item in value.items()}


def _wire_sequence(value: tuple[object, ...] | list[object]) -> list[object]:
    return [_wire_json(item) for item in value]


def _initialize_backend():
    from rc_metastudio import r_backend

    bridge = cast(_WorkerBridge, r_backend.install_r_backend())
    loader = bridge.RLibraryLoader()
    loader.load_metafor()
    loader.load_rcmetar()
    loader.load_grid()
    return bridge


def _plot_identity_from_mapping(value: object) -> dict[str, object]:
    if not _is_string_mapping(value):
        raise ValueError("plot worker request needs an artifact identity")
    if set(value) != {"analysis_id", "figure_key", "generation"}:
        raise ValueError("plot artifact identity is invalid")
    return {
        "analysis_id": _plot_identity_text(value, "analysis_id"),
        "figure_key": _plot_identity_text(value, "figure_key"),
        "generation": _plot_generation(value.get("generation")),
    }


def _plot_identity_text(value: Mapping[str, object], field: str) -> str:
    item = value.get(field)
    if not isinstance(item, str) or not item:
        raise ValueError("plot artifact identity is invalid")
    return item


def _plot_generation(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("plot artifact identity is invalid")
    return value


def _plot_source_sidecars(operation: str, regenerator: str) -> tuple[str, ...]:
    if operation == "plot_export" and regenerator != "funnel":
        return ("plotdata",)
    return ("data", "params", "res")


def _copy_plot_sidecars(
    source_base: Path, staged_base: Path, sidecars: tuple[str, ...]
) -> None:
    for suffix in sidecars:
        source = Path(f"{source_base}.{suffix}")
        if not source.is_file():
            raise FileNotFoundError("required plot data is missing: %s" % source)
        shutil.copyfile(source, f"{staged_base}.{suffix}")


def _plot_extension(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("plot output format must be text")
    extension = value.lower().lstrip(".")
    if extension not in _PLOT_EXTENSIONS:
        raise ValueError("unsupported plot output format: %s" % value)
    return extension


def _plot_parameter_paths(regenerator: PlotRegenerator) -> tuple[str, str | None]:
    if regenerator in ("forest", "sroc"):
        return "fp_outpath", "fp_display_path"
    if regenerator == "regression":
        return "bp_outpath", "bp_display_path"
    if regenerator == "funnel":
        return "funnel.outpath", None
    raise ValueError("unsupported plot regenerator: %s" % regenerator)


def _execute_plot(payload: Mapping[str, object], operation: str, run_id: str) -> None:
    if operation == "saved_plot_render":
        _execute_saved_plot_render(payload, run_id)
        return
    from rc_metastudio.plot_service import PlotService

    identity, regenerator, source_base, staging_root, output_extension = (
        _plot_request_context(payload, operation)
    )
    stage, staged_base, candidate_dir = _prepare_plot_staging(
        operation, regenerator, source_base, staging_root
    )
    _send(
        {
            "type": "progress",
            "run_id": run_id,
            "operation": operation,
            "artifact_identity": identity,
            "stage": "Starting plot engine",
        }
    )
    bridge = _initialize_backend()
    service = PlotService(bridge)
    result = _plot_operation_result(
        payload,
        operation,
        regenerator,
        output_extension,
        staged_base,
        candidate_dir,
        stage,
        bridge,
        service,
    )

    _send(
        {
            "type": "plot_result",
            "run_id": run_id,
            "operation": operation,
            "artifact_identity": identity,
            "result": result,
        }
    )


def _execute_saved_plot_render(payload: Mapping[str, object], run_id: str) -> None:
    request = _saved_plot_render_request(payload)
    _send_plot_progress(
        run_id, request.identity, "Preparing the frozen plot renderer"
    )
    bridge = _initialize_backend()
    bridge.render_saved_plot_state(
        request.renderer_state,
        request.presentation,
        request.figure_key,
        str(request.output_path),
        None if request.display_path is None else str(request.display_path),
    )
    candidate = _saved_plot_render_candidate(request)
    _send(
        {
            "type": "plot_result",
            "run_id": run_id,
            "operation": "saved_plot_render",
            "artifact_identity": request.identity,
            "result": {"candidate": candidate},
        }
    )


def _saved_plot_render_request(
    payload: Mapping[str, object],
) -> _SavedPlotRenderRequest:
    identity, figure_key = _saved_plot_identity(payload)
    regenerator, plot_kind = _saved_plot_renderer(payload)
    stage, output_path, display_path = _saved_plot_paths(payload)
    state, presentation = _saved_plot_inputs(
        payload, figure_key, plot_kind, regenerator
    )
    return _SavedPlotRenderRequest(
        identity=identity,
        figure_key=figure_key,
        stage=stage,
        output_path=output_path,
        display_path=display_path,
        renderer_state=state,
        presentation=presentation,
    )


def _saved_plot_identity(
    payload: Mapping[str, object],
) -> tuple[dict[str, object], str]:
    identity = _plot_identity_from_mapping(payload.get("artifact_identity"))
    figure_key = payload.get("figure_key")
    if (
        not isinstance(figure_key, str)
        or not figure_key
        or identity["figure_key"] != figure_key
    ):
        raise ValueError("saved plot request needs a figure key")
    return identity, figure_key


def _saved_plot_renderer(payload: Mapping[str, object]) -> tuple[str, str]:
    regenerator = payload.get("regenerator")
    plot_kind = payload.get("plot_kind")
    if not isinstance(regenerator, str) or not isinstance(plot_kind, str):
        raise ValueError("saved plot request needs a supported renderer")
    return regenerator, plot_kind


def _saved_plot_paths(
    payload: Mapping[str, object],
) -> tuple[Path, Path, Path | None]:
    stage = _required_plot_path(payload.get("staging_dir"), "staging directory")
    if not stage.is_dir():
        raise ValueError("saved plot staging directory does not exist")
    output_path = _staged_saved_plot_path(payload.get("output_path"), stage)
    display_value = payload.get("display_path")
    display_path = (
        _staged_saved_plot_path(display_value, stage)
        if display_value is not None
        else None
    )
    if display_path is not None and display_path.suffix.lower() != ".svg":
        raise ValueError("saved plot display output must be SVG")
    return stage, output_path, display_path


def _saved_plot_inputs(
    payload: Mapping[str, object],
    figure_key: str,
    plot_kind: str,
    regenerator: str,
) -> tuple[dict[str, object], Mapping[str, object]]:
    state = payload.get("renderer_state")
    if (
        not isinstance(state, dict)
        or not is_render_state(state, figure_key)
        or not render_state_matches_capability(state, plot_kind, regenerator)
    ):
        raise ValueError("saved figure has missing or malformed frozen renderer data")
    presentation = payload.get("presentation")
    renderer = state.get("renderer")
    if not is_plot_presentation(presentation, renderer):
        raise ValueError("saved plot appearance settings are malformed")
    return (
        state,
        cast(Mapping[str, object], presentation),
    )


def _saved_plot_render_candidate(
    request: _SavedPlotRenderRequest,
) -> dict[str, object]:
    _require_candidate(request.output_path, request.stage)
    candidate: dict[str, object] = {"image_path": str(request.output_path)}
    if request.display_path is not None:
        _require_candidate(request.display_path, request.stage)
        candidate["display_path"] = str(request.display_path)
    return candidate


def _staged_saved_plot_path(value: object, stage: Path) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("saved plot request needs a candidate path")
    path = Path(value).expanduser().resolve()
    try:
        path.relative_to(stage.resolve())
    except ValueError as error:
        raise ValueError("saved plot candidate escaped its staging directory") from error
    return path


def _send_plot_progress(run_id: str, identity: Mapping[str, object], stage: str) -> None:
    _send(
        {
            "type": "progress",
            "run_id": run_id,
            "operation": "saved_plot_render",
            "artifact_identity": dict(identity),
            "stage": stage,
        }
    )


def _plot_request_context(
    payload: Mapping[str, object], operation: str
) -> tuple[dict[str, object], PlotRegenerator, Path, Path, str | None]:
    identity = _plot_identity_from_mapping(payload.get("artifact_identity"))
    regenerator_value = payload.get("regenerator")
    if not _is_plot_regenerator(regenerator_value) or regenerator_value == "none":
        raise ValueError("unsupported plot regenerator: %s" % regenerator_value)
    source_base = _required_plot_path(payload.get("params_path"), "parameter path")
    staging_root = _required_plot_path(payload.get("staging_dir"), "staging directory")
    if not staging_root.is_dir():
        raise ValueError("plot staging directory does not exist")
    extension = (
        _plot_extension(payload.get("output_extension"))
        if operation in ("plot_export", "plot_edit")
        else None
    )
    return identity, regenerator_value, source_base, staging_root, extension


def _required_plot_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"plot worker request needs a {label}")
    return Path(value).expanduser().resolve()


def _prepare_plot_staging(
    operation: str,
    regenerator: PlotRegenerator,
    source_base: Path,
    staging_root: Path,
) -> tuple[Path, Path, Path]:
    stage = Path(tempfile.mkdtemp(prefix=f"rcms-{operation}-", dir=str(staging_root)))
    input_dir = stage / "input"
    candidate_dir = stage / "candidate"
    input_dir.mkdir()
    candidate_dir.mkdir()
    staged_base = input_dir / "plot"
    _copy_plot_sidecars(
        source_base, staged_base, _plot_source_sidecars(operation, regenerator)
    )
    return stage, staged_base, candidate_dir


def _plot_operation_result(
    payload: Mapping[str, object],
    operation: str,
    regenerator: PlotRegenerator,
    extension: str | None,
    staged_base: Path,
    candidate_dir: Path,
    stage: Path,
    bridge: _WorkerBridge,
    service: PlotService,
) -> dict[str, object]:
    if operation == "plot_parameters":
        return _read_plot_parameters(service, staged_base, stage)
    if operation == "plot_export":
        return _export_plot(service, regenerator, extension, staged_base, candidate_dir, stage)
    if operation == "plot_edit":
        return _execute_plot_edit(
            payload,
            regenerator,
            str(extension),
            staged_base,
            candidate_dir,
            stage,
            bridge,
            service,
        )
    raise ValueError("unsupported plot worker operation")


def _read_plot_parameters(
    service: PlotService, staged_base: Path, stage: Path
) -> dict[str, object]:
    params = service.load_params(str(staged_base))
    if params is None:
        raise ValueError("stored plot parameters are unavailable")
    return {"params": _wire_json(params), "staging_path": str(stage)}


def _export_plot(
    service: PlotService,
    regenerator: PlotRegenerator,
    extension: str | None,
    staged_base: Path,
    candidate_dir: Path,
    stage: Path,
) -> dict[str, object]:
    candidate_image = candidate_dir / ("figure." + str(extension))
    service.export(
        regenerator=regenerator,
        params_path=str(staged_base),
        output_path=str(candidate_image),
    )
    _require_candidate(candidate_image, stage)
    return {
        "staging_path": str(stage),
        "candidate": {"image_path": str(candidate_image)},
    }


def _execute_plot_edit(
    payload: Mapping[str, object],
    regenerator: PlotRegenerator,
    extension: str,
    staged_base: Path,
    candidate_dir: Path,
    stage: Path,
    bridge: _WorkerBridge,
    service: PlotService,
) -> dict[str, object]:
    updated_params, output_path, display_path = _plot_edit_inputs(payload)
    output_param, display_param = _plot_parameter_paths(regenerator)
    candidate_image = candidate_dir / ("figure." + extension)
    candidate_display = _candidate_display_path(
        display_param, updated_params, display_path, candidate_dir
    )
    _render_plot_edit(
        service,
        regenerator,
        staged_base,
        updated_params,
        output_param,
        display_param,
        candidate_image,
        candidate_display,
        stage,
    )
    _save_plot_edit_params(
        bridge,
        regenerator,
        staged_base,
        updated_params,
        output_param,
        display_param,
        output_path,
        display_path,
    )
    candidate = _plot_edit_candidate(
        regenerator,
        candidate_image,
        candidate_display,
        staged_base,
        stage,
    )
    return {"staging_path": str(stage), "candidate": candidate}


def _plot_edit_inputs(
    payload: Mapping[str, object],
) -> tuple[dict[str, object], str, str | None]:
    updated_value = payload.get("updated_params")
    if not _is_string_mapping(updated_value):
        raise ValueError("plot edit request needs a parameter mapping")
    output_path = payload.get("output_path")
    if not isinstance(output_path, str) or not output_path:
        raise ValueError("plot edit request needs a destination path")
    output_path = str(Path(output_path).expanduser().resolve())
    display_path_value = payload.get("display_path")
    if display_path_value is not None and (
        not isinstance(display_path_value, str) or not display_path_value
    ):
        raise ValueError("plot display destination must be a path")
    display_path = (
        str(Path(display_path_value).expanduser().resolve())
        if isinstance(display_path_value, str)
        else None
    )
    return dict(updated_value), output_path, display_path


def _candidate_display_path(
    display_param: str | None,
    updated_params: Mapping[str, object],
    display_path: str | None,
    candidate_dir: Path,
) -> Path | None:
    if display_param is not None and display_param in updated_params:
        if display_path is None and updated_params.get(display_param):
            raise ValueError("plot edit request needs a display destination")
        if display_path is not None:
            return candidate_dir / "display.svg"
    elif display_path is not None:
        raise ValueError("plot edit request has no display parameter")
    return None


def _render_plot_edit(
    service: PlotService,
    regenerator: PlotRegenerator,
    staged_base: Path,
    updated_params: Mapping[str, object],
    output_param: str,
    display_param: str | None,
    candidate_image: Path,
    candidate_display: Path | None,
    stage: Path,
) -> None:
    render_params = dict(updated_params)
    render_params[output_param] = str(candidate_image)
    if display_param is not None and candidate_display is not None:
        render_params[display_param] = str(candidate_display)
    service.apply_edits(
        regenerator=regenerator,
        params_path=str(staged_base),
        updated_params=render_params,
        output_path=str(candidate_image),
    )
    _require_candidate(candidate_image, stage)
    if candidate_display is not None:
        _require_candidate(candidate_display, stage)


def _save_plot_edit_params(
    bridge: _WorkerBridge,
    regenerator: PlotRegenerator,
    staged_base: Path,
    updated_params: Mapping[str, object],
    output_param: str,
    display_param: str | None,
    output_path: str,
    display_path: str | None,
) -> None:
    # The candidate files stay in staging, but their saved parameters must
    # refer to the eventual destination paths after the caller promotes them.
    committed_params = dict(updated_params)
    committed_params[output_param] = output_path
    if display_param is not None and display_path is not None:
        committed_params[display_param] = display_path
    bridge.update_plot_params(
        committed_params,
        write_them_out=True,
        outpath=f"{staged_base}.params",
    )
    if regenerator != "funnel":
        if regenerator == "regression":
            bridge.regenerate_regression_plot_data()
        else:
            bridge.regenerate_plot_data()
        bridge.write_out_plot_data(str(staged_base))


def _plot_edit_candidate(
    regenerator: PlotRegenerator,
    candidate_image: Path,
    candidate_display: Path | None,
    staged_base: Path,
    stage: Path,
) -> dict[str, object]:
    candidate: dict[str, object] = {
        "image_path": str(candidate_image),
        "params_path": f"{staged_base}.params",
    }
    plotdata_path = Path(f"{staged_base}.plotdata")
    if regenerator != "funnel":
        _require_candidate(plotdata_path, stage)
        candidate["plotdata_path"] = str(plotdata_path)
    if candidate_display is not None:
        candidate["display_path"] = str(candidate_display)
    for candidate_path in candidate.values():
        if isinstance(candidate_path, str):
            _require_candidate(Path(candidate_path), stage)
    return candidate


def _require_candidate(path: Path, stage: Path) -> None:
    resolved = path.resolve()
    try:
        resolved.relative_to(stage.resolve())
    except ValueError as error:
        raise ValueError(
            "plot worker candidate escaped its staging directory"
        ) from error
    if not resolved.is_file() or resolved.stat().st_size == 0:
        raise ValueError("plot worker produced no candidate file: %s" % path)


def _small_study_effects_snapshot(
    value: object, data_type: str
) -> SmallStudyEffectsInput:
    if data_type == "binary":
        return _snapshot_from_mapping(value)
    if data_type == "continuous":
        from rc_metastudio.continuous_analysis_snapshot import ContinuousInputSnapshot

        return ContinuousInputSnapshot.from_mapping(value)
    if data_type == "diagnostic":
        from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot

        return DiagnosticInputSnapshot.from_mapping(value)
    raise ValueError("unsupported small-study effects data family")


def _execute_small_study_effects(
    payload: Mapping[str, object], operation: str, run_id: str
) -> None:
    from rc_metastudio import publication_bias

    request_value = payload.get("request")
    if not _is_string_mapping(request_value):
        raise ValueError("small-study effects worker request needs a specification")
    request_mapping = request_value
    request = publication_bias.SmallStudyEffectsRequest.from_mapping(request_mapping)
    snapshot = _small_study_effects_snapshot(payload.get("input"), request.data_type)
    if getattr(snapshot, "metric", None) != request.metric:
        raise ValueError("small-study effects input measure does not match its request")

    _send({"type": "progress", "run_id": run_id, "stage": "Starting analysis engine"})
    bridge = _initialize_backend()
    backend_versions = _small_study_backend_versions(request.data_type, bridge)
    service = publication_bias.SmallStudyEffectsService()
    _send({"type": "progress", "run_id": run_id, "stage": "Preparing study data"})
    is_preview = operation == "small_study_effects_preview"
    result, observed = _run_small_study_request(
        is_preview, snapshot, request_mapping, service, run_id
    )
    if not is_preview:
        _capture_small_study_render_states(result, payload, bridge)
    _send(
        {
            "type": "result",
            "run_id": run_id,
            "result": result,
            "warnings": [str(item.message) for item in observed],
            "backend_versions": backend_versions,
        }
    )


def _small_study_backend_versions(
    data_type: str, bridge: _WorkerBridge
) -> dict[str, str]:
    versions = {
        "R": bridge.get_r_version_string(),
        "metafor": bridge.get_r_package_version("metafor"),
        "RCMetaR": bridge.get_r_package_version("RCMetaR"),
    }
    if data_type == "diagnostic":
        versions["mada"] = bridge.get_r_package_version("mada")
    return versions


def _run_small_study_request(
    is_preview: bool,
    snapshot: SmallStudyEffectsInput,
    request: Mapping[str, object],
    service: SmallStudyEffectsService,
    run_id: str,
) -> tuple[object, list[warnings.WarningMessage]]:
    from rc_metastudio.small_study_effects_worker import (
        preview_request,
        run_request,
    )

    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        _send(
            {
                "type": "progress",
                "run_id": run_id,
                "stage": (
                    "Checking method eligibility"
                    if is_preview
                    else "Running small-study effects analysis"
                ),
            }
        )
        result = (
            preview_request(snapshot, request, service)
            if is_preview
            else run_request(snapshot, request, service)
        )
    return result, list(observed)


def _capture_small_study_render_states(
    result: object, payload: Mapping[str, object], bridge: _WorkerBridge
) -> None:
    _stage_small_study_effects_figures(result, payload.get("staging_dir"))
    if not _is_string_dict(result):
        raise ValueError("small-study effects result must be an object")
    staging = _small_study_staging_directory(payload.get("staging_dir"))
    _retain_plot_sidecars(
        result, {"params": {"fp_outpath": str(staging / "capture.png")}}
    )
    _attach_plot_render_states(result, bridge)


def _stage_small_study_effects_figures(result: object, staging_value: object) -> None:
    """Copy R temporary figures into the caller-owned run directory before exit."""
    if not _is_string_dict(result):
        raise ValueError("small-study effects result must be an object")
    staging = _small_study_staging_directory(staging_value)
    copied: dict[str, str] = {}
    image_number = 0
    for field in ("images", "display_images"):
        paths = _small_study_figure_paths(result, field)
        for key, raw_path in paths.items():
            image_number = _stage_small_study_figure(
                paths, key, raw_path, staging, copied, image_number, field
            )


def _small_study_staging_directory(value: object) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("small-study effects worker needs a run staging directory")
    staging = Path(value).expanduser().resolve()
    if not staging.is_dir():
        raise ValueError("small-study effects run staging directory is unavailable")
    return staging


def _small_study_figure_paths(
    result: dict[str, object], field: str
) -> dict[str, object]:
    paths = result.get(field, {})
    if not _is_string_dict(paths):
        raise ValueError(f"small-study effects {field} must be a mapping")
    return paths


def _stage_small_study_figure(
    paths: dict[str, object],
    key: str,
    value: object,
    staging: Path,
    copied: dict[str, str],
    image_number: int,
    field: str,
) -> int:
    if not isinstance(key, str) or not isinstance(value, str):
        raise ValueError(f"small-study effects {field} needs text paths")
    if not value:
        return image_number
    if value in copied:
        paths[key] = copied[value]
        return image_number
    source = Path(value).expanduser()
    suffix = source.suffix.lower()
    if not _is_small_study_figure_file(source, suffix):
        paths[key] = ""
        return image_number
    source_path = source.resolve()
    if _path_is_within(source_path, staging):
        copied[value] = str(source_path)
        paths[key] = copied[value]
        return image_number
    target = staging / f"small-study-figure-{image_number}{suffix}"
    try:
        shutil.copyfile(source_path, target)
    except OSError:
        paths[key] = ""
        return image_number + 1
    copied[value] = str(target)
    paths[key] = str(target)
    return image_number + 1


def _is_small_study_figure_file(source: Path, suffix: str) -> bool:
    return suffix in {".svg", ".png", ".jpg", ".jpeg"} and source.is_file()


def _path_is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True


def _execute_reitsma(payload: Mapping[str, object], run_id: str) -> None:
    from rc_metastudio.reitsma_analysis import (
        ReitsmaInputSnapshot,
        ReitsmaRequest,
        run_reitsma_analysis,
    )

    snapshot = ReitsmaInputSnapshot.from_mapping(payload.get("input"))
    request_value = payload.get("request")
    if not _is_string_mapping(request_value):
        raise ValueError("joint Reitsma worker request needs a specification")
    request = ReitsmaRequest.from_mapping(request_value)
    plot_output_path = None
    if request.create_plot:
        staging_value = payload.get("staging_dir")
        if not isinstance(staging_value, str) or not staging_value.strip():
            raise ValueError("joint Reitsma SROC request needs a run staging directory")
        staging_dir = Path(staging_value).resolve()
        if not staging_dir.is_dir():
            raise ValueError("joint Reitsma run staging directory is unavailable")
        plot_output_path = str(staging_dir / "reitsma-sroc.svg")

    _send({"type": "progress", "run_id": run_id, "stage": "Starting analysis engine"})
    bridge = _initialize_backend()
    backend_versions = {
        "R": bridge.get_r_version_string(),
        "mada": bridge.get_r_package_version("mada"),
        "RCMetaR": bridge.get_r_package_version("RCMetaR"),
    }
    _send({"type": "progress", "run_id": run_id, "stage": "Checking joint count eligibility"})
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        _send({"type": "progress", "run_id": run_id, "stage": "Running the joint Reitsma model"})
        execution = run_reitsma_analysis(
            snapshot, request, bridge, plot_output_path=plot_output_path
        )
    result_wire = _wire_result(execution.result)
    result_wire["reitsma_report"] = execution.report.to_mapping()
    if plot_output_path is not None:
        _retain_plot_sidecars(
            result_wire, {"params": {"fp_outpath": plot_output_path}}
        )
        _attach_plot_render_states(result_wire, bridge)
    _send(
        {
            "type": "result",
            "run_id": run_id,
            "result": result_wire,
            "warnings": [str(item.message) for item in observed],
            "backend_versions": backend_versions,
        }
    )


def _execute_subgroup(payload: Mapping[str, object], run_id: str) -> None:
    from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot
    from rc_metastudio.subgroup_analysis_worker import attach_subgroup_report

    request_mapping, plan_mapping = _subgroup_request_mappings(payload)
    snapshot = _subgroup_snapshot(request_mapping.get("data_type"), payload.get("input"))
    plan, request, prepared = _prepare_subgroup_run(
        request_mapping, plan_mapping, snapshot
    )

    _send({"type": "progress", "run_id": run_id, "stage": "Starting analysis engine"})
    bridge = _initialize_backend()
    backend_versions = _subgroup_backend_versions(bridge, prepared)
    _send({"type": "progress", "run_id": run_id, "stage": "Preparing subgroup study data"})
    _prepare_subgroup_backend(prepared, bridge)
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        _send({"type": "progress", "run_id": run_id, "stage": "Running subgroup analysis"})
        native_result = bridge.run_versioned_analysis_request(request.to_mapping())
    result, numerics = attach_subgroup_report(native_result, plan)
    result_wire = _wire_result(result)
    result_wire["subgroup_numerics"] = numerics.to_mapping()
    result_wire["subgroup_plan"] = plan.to_mapping()
    request_mapping = request.to_mapping()
    _retain_plot_sidecars(result_wire, request_mapping)
    _attach_plot_render_states(result_wire, bridge)
    _send(
        {
            "type": "result",
            "run_id": run_id,
            "result": result_wire,
            "warnings": [str(item.message) for item in observed],
            "backend_versions": backend_versions,
        }
    )


def _subgroup_request_mappings(
    payload: Mapping[str, object],
) -> tuple[Mapping[str, object], Mapping[str, object]]:
    request = payload.get("request")
    plan = payload.get("subgroup_plan")
    if not _is_string_mapping(request) or not _is_string_mapping(plan):
        raise ValueError("subgroup worker request needs a request and frozen plan")
    return request, plan


def _subgroup_snapshot(
    data_type: object, value: object
) -> BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot:
    if data_type == "binary":
        return _snapshot_from_mapping(value)
    if data_type == "continuous":
        from rc_metastudio.continuous_analysis_snapshot import ContinuousInputSnapshot

        return ContinuousInputSnapshot.from_mapping(value)
    if data_type == "diagnostic":
        from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot

        return DiagnosticInputSnapshot.from_mapping(value)
    raise ValueError("subgroup analysis received an unsupported input family")


def _prepare_subgroup_run(
    request_value: Mapping[str, object],
    plan_value: Mapping[str, object],
    snapshot: BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot,
) -> tuple[
    SubgroupPlan,
    AnalysisRequest,
    BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot,
]:
    from rc_metastudio.analysis_adapter import make_analysis_request
    from rc_metastudio.subgroup_analysis import (
        SubgroupPlan,
        create_subgroup_request,
        prepare_subgroup_snapshot,
    )

    plan = SubgroupPlan.from_mapping(plan_value)
    raw_params = request_value.get("params")
    if not _is_string_mapping(raw_params):
        raise ValueError("subgroup worker request needs analysis parameters")
    request = make_analysis_request(
        data_type=str(request_value.get("data_type", "")),
        workflow=str(request_value.get("workflow", "")),
        method=str(request_value.get("method", "")),
        metric=str(request_value.get("metric", "")),
        parameters=raw_params,
    )
    if request_value.get("version") != 1:
        raise ValueError("subgroup worker needs a versioned request")
    expected = create_subgroup_request(
        snapshot, plan, method=request.method, parameters=request.parameter_values()
    )
    if request.semantic_id != expected.semantic_id:
        raise ValueError("subgroup request does not match its frozen plan")
    return plan, request, prepare_subgroup_snapshot(snapshot, plan)


def _subgroup_backend_versions(bridge: _WorkerBridge, prepared: object) -> dict[str, str]:
    from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot

    versions = {
        "R": bridge.get_r_version_string(),
        "metafor": bridge.get_r_package_version("metafor"),
        "RCMetaR": bridge.get_r_package_version("RCMetaR"),
    }
    if isinstance(prepared, DiagnosticInputSnapshot):
        versions["mada"] = bridge.get_r_package_version("mada")
    return versions


def _prepare_subgroup_backend(prepared: object, bridge: _WorkerBridge) -> None:
    from rc_metastudio.continuous_analysis_snapshot import (
        ContinuousInputSnapshot,
        create_continuous_backend_data,
    )
    from rc_metastudio.diagnostic_analysis_backend import create_diagnostic_r_data
    from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot

    if isinstance(prepared, BinaryInputSnapshot):
        _create_binary_data(prepared, bridge)
    elif isinstance(prepared, ContinuousInputSnapshot):
        bridge.ro.globalenv["tmp_obj"] = create_continuous_backend_data(prepared, bridge)
    elif isinstance(prepared, DiagnosticInputSnapshot):
        from rc_metastudio.diagnostic_analysis_backend import DiagnosticBackend

        create_diagnostic_r_data(prepared, cast(DiagnosticBackend, bridge))
    else:
        raise ValueError("subgroup plan produced an unsupported prepared input family")


def _execute_calculator(payload: Mapping[str, object], run_id: str) -> None:
    _send({"type": "progress", "run_id": run_id, "stage": "Starting study calculation"})
    bridge = _initialize_backend()
    backend_versions = {
        "R": bridge.get_r_version_string(),
        "metafor": bridge.get_r_package_version("metafor"),
        "RCMetaR": bridge.get_r_package_version("RCMetaR"),
    }
    from rc_metastudio.calculator_service import execute_calculator_calls

    result = execute_calculator_calls(payload.get("calls"))
    _send(
        {
            "type": "result",
            "run_id": run_id,
            "result": _wire_json(result),
            "warnings": [],
            "backend_versions": backend_versions,
        }
    )


def _execute(payload: object) -> None:
    if not _is_string_mapping(payload):
        raise ValueError("analysis worker request must be an object")
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("analysis worker request needs a run identity")
    operation = payload.get("operation", "analysis")
    if _dispatch_special_operation(payload, operation, run_id):
        return
    if operation not in ("methods", "analysis", "meta_regression"):
        raise ValueError("unsupported analysis worker operation")
    _execute_generic_operation(payload, str(operation), run_id)


def _dispatch_special_operation(
    payload: Mapping[str, object], operation: object, run_id: str
) -> bool:
    if isinstance(operation, str) and operation in _PLOT_OPERATIONS:
        _execute_plot(payload, operation, run_id)
        return True
    if operation in ("small_study_effects_preview", "small_study_effects"):
        _execute_small_study_effects(payload, str(operation), run_id)
        return True
    if operation == "reitsma":
        _execute_reitsma(payload, run_id)
        return True
    if operation == "subgroup":
        _execute_subgroup(payload, run_id)
        return True
    if operation == "calculator":
        _execute_calculator(payload, run_id)
        return True
    return False


def _generic_worker_context(
    payload: Mapping[str, object], operation: str, run_id: str
) -> tuple[_WorkerBridge, dict[str, str], Mapping[str, object]]:
    _send({"type": "progress", "run_id": run_id, "stage": "Starting analysis engine"})
    bridge = _initialize_backend()
    versions = {
        "R": bridge.get_r_version_string(),
        "metafor": bridge.get_r_package_version("metafor"),
        "RCMetaR": bridge.get_r_package_version("RCMetaR"),
    }
    value = payload.get("query" if operation == "methods" else "request")
    if not _is_string_mapping(value):
        raise ValueError("analysis worker request needs a method query or specification")
    return bridge, versions, value


def _execute_generic_operation(
    payload: Mapping[str, object], operation: str, run_id: str
) -> None:
    bridge, versions, specification = _generic_worker_context(
        payload, operation, run_id
    )
    if operation == "meta_regression":
        _execute_meta_regression(payload, specification, bridge, versions, run_id)
        return
    data_type, workflow, snapshot, cumulative_snapshot = _analysis_input_context(
        payload, operation, specification
    )
    _send({"type": "progress", "run_id": run_id, "stage": "Preparing study data"})
    if operation == "methods":
        _execute_methods(snapshot, data_type, workflow, bridge, versions, run_id)
        return
    _execute_analysis(
        snapshot,
        data_type,
        workflow,
        specification,
        cumulative_snapshot,
        bridge,
        versions,
        run_id,
    )


def _execute_meta_regression(
    payload: Mapping[str, object],
    specification: Mapping[str, object],
    bridge: _WorkerBridge,
    versions: dict[str, str],
    run_id: str,
) -> None:
    from rc_metastudio.meta_regression_analysis import (
        MetaRegressionInputSnapshot,
        MetaRegressionRunRequest,
        execute_meta_regression,
    )

    snapshot = MetaRegressionInputSnapshot.from_mapping(payload.get("input"))
    request = MetaRegressionRunRequest.from_mapping(specification)
    if request.data_type != snapshot.data_type:
        raise ValueError("meta-regression input family does not match its request")
    if snapshot.data_type == "diagnostic":
        versions["mada"] = bridge.get_r_package_version("mada")
    _send({"type": "progress", "run_id": run_id, "stage": "Preparing study data"})
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        _send({"type": "progress", "run_id": run_id, "stage": "Running the meta-regression"})
        from rc_metastudio.meta_regression_analysis import MetaRegressionBridge

        execution = execute_meta_regression(
            snapshot, request, cast(MetaRegressionBridge, bridge)
        )
    result_wire = _wire_result(execution.result)
    _retain_plot_sidecars(result_wire, request.to_mapping())
    _attach_plot_render_states(result_wire, bridge)
    _send(
        {
            "type": "result",
            "run_id": run_id,
            "result": result_wire,
            "warnings": [str(item.message) for item in observed],
            "backend_versions": versions,
        }
    )


def _analysis_input_context(
    payload: Mapping[str, object],
    operation: str,
    specification: Mapping[str, object],
) -> tuple[
    str,
    str,
    BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot,
    CumulativeAnalysisSnapshot | None,
]:
    data_type = specification.get("data_type")
    workflow = specification.get("workflow")
    if not isinstance(data_type, str):
        raise ValueError("analysis worker request needs a data family")
    cumulative_snapshot: CumulativeAnalysisSnapshot | None = None
    if operation == "analysis" and workflow == "cumulative":
        from rc_metastudio.cumulative_analysis import CumulativeAnalysisSnapshot

        cumulative_snapshot = CumulativeAnalysisSnapshot.from_mapping(payload.get("input"))
        snapshot = cumulative_snapshot.ordered_input_snapshot
        if cumulative_snapshot.family != data_type:
            raise ValueError("cumulative input family does not match its request")
    else:
        snapshot = _analysis_snapshot(data_type, payload.get("input"))
    supported = (
        ("standard", "cumulative", "leave-one-out", "subgroup")
        if operation == "methods"
        else ("standard", "cumulative", "leave-one-out")
    )
    if workflow not in supported or specification.get("metric") != snapshot.metric:
        raise ValueError("worker needs a matching supported analysis request")
    return data_type, str(workflow), snapshot, cumulative_snapshot


def _execute_methods(
    snapshot: BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot,
    data_type: str,
    workflow: str,
    bridge: _WorkerBridge,
    versions: dict[str, str],
    run_id: str,
) -> None:
    catalogue = _method_catalogue(snapshot, data_type, workflow, bridge)
    _send(
        {
            "type": "methods",
            "run_id": run_id,
            "catalogue": _wire_json(catalogue),
            "backend_versions": versions,
        }
    )


def _method_catalogue(
    snapshot: BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot,
    data_type: str,
    workflow: str,
    bridge: _WorkerBridge,
) -> dict[str, object]:
    from rc_metastudio.diagnostic_analysis_backend import diagnostic_method_catalogue
    from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot

    if isinstance(snapshot, DiagnosticInputSnapshot) and workflow == "standard":
        from rc_metastudio.diagnostic_analysis_backend import DiagnosticBackend

        methods = diagnostic_method_catalogue(
            snapshot, cast(DiagnosticBackend, bridge)
        )
        return {
            "data_type": "diagnostic",
            "available_methods": {
                detail["label"]: method for method, detail in methods.items()
            },
            "details": {
                method: {key: value for key, value in detail.items() if key != "label"}
                for method, detail in methods.items()
            },
        }
    _prepare_method_data(snapshot, bridge)
    return _wire_methods(bridge, data_type, snapshot.metric, workflow)


def _prepare_method_data(
    snapshot: BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot,
    bridge: _WorkerBridge,
) -> None:
    from rc_metastudio.continuous_analysis_snapshot import (
        ContinuousInputSnapshot,
        create_continuous_backend_data,
    )
    from rc_metastudio.diagnostic_analysis_backend import create_diagnostic_r_data
    from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot

    if isinstance(snapshot, BinaryInputSnapshot):
        _create_binary_data(snapshot, bridge)
    elif isinstance(snapshot, ContinuousInputSnapshot):
        bridge.ro.globalenv["tmp_obj"] = create_continuous_backend_data(snapshot, bridge)
    elif isinstance(snapshot, DiagnosticInputSnapshot):
        from rc_metastudio.diagnostic_analysis_backend import DiagnosticBackend

        create_diagnostic_r_data(snapshot, cast(DiagnosticBackend, bridge))
    else:
        raise ValueError("unsupported analysis worker data family")


def _execute_analysis(
    snapshot: BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot,
    data_type: str,
    workflow: str,
    specification: Mapping[str, object],
    cumulative_snapshot: CumulativeAnalysisSnapshot | None,
    bridge: _WorkerBridge,
    versions: dict[str, str],
    run_id: str,
) -> None:
    if type(specification.get("version")) is not int or specification.get("version") != 1:
        raise ValueError("worker needs a versioned analysis specification")
    _send({"type": "progress", "run_id": run_id, "stage": "Running the statistical method"})
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        result_wire = _run_analysis(
            snapshot,
            data_type,
            workflow,
            specification,
            cumulative_snapshot,
            bridge,
            run_id,
        )
        _retain_plot_sidecars(result_wire, specification)
        _attach_plot_render_states(result_wire, bridge)
    _send(
        {
            "type": "result",
            "run_id": run_id,
            "result": result_wire,
            "warnings": [str(item.message) for item in observed],
            "backend_versions": versions,
        }
    )


def _retain_plot_sidecars(
    result_wire: dict[str, object], specification: Mapping[str, object]
) -> None:
    paths = _retained_plot_paths(result_wire)
    if paths is None:
        return
    missing_sources = {key for key, source_base in paths.items() if not source_base}
    paths = {key: source_base for key, source_base in paths.items() if source_base}
    if not paths:
        result_wire["image_params_paths"] = {}
        _mark_missing_plot_sources(result_wire, missing_sources)
        return
    retained = _copy_result_plot_sidecars(paths, result_wire, specification)
    result_wire["image_params_paths"] = retained
    _mark_missing_plot_sources(result_wire, missing_sources)


def _copy_result_plot_sidecars(
    paths: Mapping[str, str],
    result_wire: Mapping[str, object],
    specification: Mapping[str, object],
) -> dict[str, str]:
    destination_dir = _plot_output_directory(specification)
    retained: dict[str, str] = {}
    copied: list[Path] = []
    try:
        for index, (key, source_base) in enumerate(paths.items()):
            sidecars = _plot_sidecars_for_figure(result_wire, key)
            if sidecars:
                destination_base = destination_dir / (
                    "rcms-plot-%s-%d" % (uuid4().hex, index)
                )
                _copy_analysis_plot_sidecars(
                    source_base, destination_base, copied, sidecars
                )
                retained[key] = str(destination_base)
    except Exception:
        for path in copied:
            path.unlink(missing_ok=True)
        raise
    return retained


def _plot_sidecars_for_figure(
    result_wire: Mapping[str, object], figure_key: str
) -> tuple[str, ...]:
    capability = _plot_capability(result_wire.get("plot_capabilities"), figure_key)
    if capability is None:
        return "data", "params", "res", "plotdata"
    return _sidecars_for_regenerator(str(capability.get("regenerator")))


def _attach_plot_render_states(
    result_wire: dict[str, object], bridge: _WorkerBridge
) -> None:
    paths = _retained_plot_paths(result_wire)
    if paths is None:
        return
    capabilities = result_wire.get("plot_capabilities")
    states: dict[str, object] = {}
    unavailable = _plot_render_state_reasons(result_wire)
    total_size = 0
    for figure_key, source_base in paths.items():
        state, size, reason = _project_plot_render_state_for_figure(
            figure_key, source_base, capabilities, bridge
        )
        if reason is not None:
            unavailable[figure_key] = reason
            continue
        if total_size + size > MAX_TOTAL_RENDER_STATE_BYTES:
            unavailable[figure_key] = "Frozen renderer data exceed the 2 MB result limit."
            continue
        assert state is not None
        states[figure_key] = state
        total_size += size
    if states:
        result_wire["plot_render_state"] = states
    if unavailable:
        result_wire["plot_render_state_unavailable"] = unavailable


def _project_plot_render_state_for_figure(
    figure_key: str,
    source_base: str,
    capabilities: object,
    bridge: _WorkerBridge,
) -> tuple[dict[str, object] | None, int, str | None]:
    renderer = _frozen_renderer_capability(capabilities, figure_key)
    if renderer is None:
        return None, 0, "This figure has no supported renderer capability."
    plot_kind, regenerator = renderer
    if not _plot_render_sidecars_available(source_base, regenerator):
        return None, 0, "Frozen renderer data are missing for this figure."
    state = bridge.project_plot_render_state(
        source_base, figure_key, plot_kind, regenerator
    )
    if state is None:
        return None, 0, "This figure has no supported frozen renderer data."
    size = render_state_size(state, figure_key)
    if size is None:
        raise ValueError("R returned malformed frozen plot renderer data")
    if not render_state_matches_capability(state, plot_kind, regenerator):
        raise ValueError("R returned malformed frozen plot renderer data")
    if size > MAX_RENDER_STATE_BYTES:
        return None, size, "Frozen renderer data exceed the 1 MB per-figure limit."
    reason: str | None = None
    return cast(dict[str, object], state), size, reason


def _frozen_renderer_capability(
    capabilities: object, figure_key: str
) -> tuple[str, str] | None:
    capability = _plot_capability(capabilities, figure_key)
    if capability is None:
        return None
    plot_kind, regenerator = capability.get("plot_kind"), capability.get("regenerator")
    if not isinstance(plot_kind, str) or not isinstance(regenerator, str):
        return None
    if not _sidecars_for_regenerator(regenerator):
        return None
    return plot_kind, regenerator


def _plot_render_sidecars_available(source_base: str, regenerator: str) -> bool:
    sidecars = _sidecars_for_regenerator(regenerator)
    return bool(sidecars) and all(
        Path(source_base + "." + suffix).is_file() for suffix in sidecars
    )


def _plot_capability(value: object, figure_key: str) -> Mapping[str, object] | None:
    if not _is_string_mapping(value):
        return None
    capability = value.get(figure_key)
    return capability if _is_string_mapping(capability) else None


def _sidecars_for_regenerator(regenerator: str) -> tuple[str, ...]:
    if regenerator == "funnel":
        return "data", "params", "res"
    if regenerator in {"forest", "regression", "sroc"}:
        return "data", "params", "res", "plotdata"
    return ()


def _retained_plot_paths(result_wire: Mapping[str, object]) -> dict[str, str] | None:
    paths = result_wire.get("image_params_paths")
    if not _is_string_mapping(paths) or not paths:
        return None
    normalized: dict[str, str] = {}
    for key, value in paths.items():
        if not isinstance(value, str):
            raise ValueError("analysis plot parameter paths must be text")
        normalized[key] = value
    return normalized


def _mark_missing_plot_sources(
    result_wire: dict[str, object], figure_keys: set[str]
) -> None:
    if not figure_keys:
        return
    unavailable = _plot_render_state_reasons(result_wire)
    for figure_key in figure_keys:
        unavailable[figure_key] = (
            "Figure source data are unavailable, so appearance editing and "
            "regeneration are disabled."
        )
    result_wire["plot_render_state_unavailable"] = unavailable
    capabilities = result_wire.get("plot_capabilities")
    if _is_string_mapping(capabilities):
        for figure_key in figure_keys:
            capability = capabilities.get(figure_key)
            if isinstance(capability, MutableMapping):
                capability_fields = cast(MutableMapping[str, object], capability)
                capability_fields["editable"] = False
                capability_fields["styleable"] = False


def _plot_render_state_reasons(result_wire: Mapping[str, object]) -> dict[str, str]:
    value = result_wire.get("plot_render_state_unavailable")
    if value is None:
        return {}
    if not _is_string_mapping(value):
        raise ValueError("plot renderer availability reasons must be a mapping")
    reasons: dict[str, str] = {}
    for key, reason in value.items():
        if not isinstance(reason, str) or not reason:
            raise ValueError("plot renderer availability reasons must be non-empty text")
        reasons[key] = reason
    return reasons


def _plot_output_directory(specification: Mapping[str, object]) -> Path:
    parameters = specification.get("params")
    output_path = None
    if _is_string_mapping(parameters):
        output_path = parameters.get("fp_outpath") or parameters.get("bp_outpath")
    if not isinstance(output_path, str) or not output_path:
        raise ValueError("analysis plot data needs a managed output path")
    destination_dir = Path(output_path).expanduser().resolve().parent
    if not destination_dir.is_dir():
        raise ValueError("analysis plot output directory does not exist")
    return destination_dir


def _copy_analysis_plot_sidecars(
    source_base: str,
    destination_base: Path,
    copied: list[Path],
    suffixes: tuple[str, ...],
) -> None:
    for suffix in suffixes:
        source = Path("%s.%s" % (source_base, suffix)).expanduser()
        if not source.is_file():
            raise FileNotFoundError("required analysis plot data is missing: %s" % source)
        destination = Path("%s.%s" % (destination_base, suffix))
        shutil.copyfile(source, destination)
        copied.append(destination)


def _run_analysis(
    snapshot: BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot,
    data_type: str,
    workflow: str,
    specification: Mapping[str, object],
    cumulative_snapshot: CumulativeAnalysisSnapshot | None,
    bridge: _WorkerBridge,
    run_id: str,
) -> dict[str, object]:
    from rc_metastudio.continuous_analysis_snapshot import ContinuousInputSnapshot
    from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot

    if workflow != "standard":
        return _run_sequential_analysis(
            snapshot, data_type, workflow, specification, cumulative_snapshot, bridge, run_id
        )
    if isinstance(snapshot, BinaryInputSnapshot):
        return _run_binary_analysis(snapshot, specification, bridge)
    if isinstance(snapshot, ContinuousInputSnapshot):
        return _run_continuous_analysis(snapshot, specification, bridge)
    if isinstance(snapshot, DiagnosticInputSnapshot):
        return _run_diagnostic_analysis(snapshot, specification, bridge)
    raise ValueError("unsupported analysis worker data family")


def _run_binary_analysis(
    snapshot: BinaryInputSnapshot,
    specification: Mapping[str, object],
    bridge: _WorkerBridge,
) -> dict[str, object]:
    _create_binary_data(snapshot, bridge)
    result_wire = _wire_result(bridge.run_versioned_analysis_request(specification))
    if snapshot.metric in BINARY_ONE_ARM_METRICS:
        result_wire["binary_proportion_numerics"] = _one_arm_binary_numerics(
            snapshot, specification, bridge
        )
    return result_wire


def _run_continuous_analysis(
    snapshot: ContinuousInputSnapshot,
    specification: Mapping[str, object],
    bridge: _WorkerBridge,
) -> dict[str, object]:
    from rc_metastudio.analysis_adapter import make_analysis_request
    from rc_metastudio.continuous_analysis_snapshot import execute_continuous_snapshot

    parameters = specification.get("params")
    if not _is_string_mapping(parameters):
        raise ValueError("continuous analysis parameters must be an object")
    request = make_analysis_request(
        data_type="continuous",
        workflow="standard",
        method=str(specification.get("method", "")),
        metric=snapshot.metric,
        parameters=parameters,
    )
    execution = execute_continuous_snapshot(snapshot, request, bridge=bridge)
    result_wire = _wire_result(execution.result)
    result_wire["continuous_numerics"] = execution.numerics.to_mapping()
    return result_wire


def _run_diagnostic_analysis(
    snapshot: DiagnosticInputSnapshot,
    specification: Mapping[str, object],
    bridge: _WorkerBridge,
) -> dict[str, object]:
    from rc_metastudio.diagnostic_analysis_backend import (
        diagnostic_request_from_mapping,
        run_diagnostic_analysis,
    )

    request = diagnostic_request_from_mapping(specification, snapshot)
    from rc_metastudio.diagnostic_analysis_backend import DiagnosticBackend

    execution = run_diagnostic_analysis(
        snapshot, request, cast(DiagnosticBackend, bridge)
    )
    result_wire = _wire_result(execution.result)
    result_wire["diagnostic_numerics"] = execution.numerics.to_mapping()
    return result_wire


def _run_sequential_analysis(
    snapshot: BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot,
    data_type: str,
    workflow: str,
    specification: Mapping[str, object],
    cumulative_snapshot: CumulativeAnalysisSnapshot | None,
    bridge: _WorkerBridge,
    run_id: str,
) -> dict[str, object]:
    from rc_metastudio.analysis_adapter import make_analysis_request
    from rc_metastudio.sequential_result_adapter import (
        cumulative_result_from_backend,
        leave_one_out_result_from_backend,
    )

    parameters = specification.get("params")
    if not _is_string_mapping(parameters):
        raise ValueError("sequential analysis parameters must be an object")
    request = make_analysis_request(
        data_type=data_type,
        workflow=workflow,
        method=str(specification.get("method", "")),
        metric=snapshot.metric,
        parameters=parameters,
    )
    try:
        _prepare_step_data(snapshot, bridge)
        result_wire = _wire_result(bridge.run_versioned_analysis_request(specification))
        if workflow == "cumulative":
            if cumulative_snapshot is None:
                raise ValueError("cumulative analysis input is unavailable")
            result_wire["cumulative_numerics"] = cumulative_result_from_backend(
                cumulative_snapshot, bridge
            ).to_mapping()
        else:
            result_wire["leave_one_out_numerics"] = leave_one_out_result_from_backend(
                snapshot, request, bridge
            ).to_mapping()
        return result_wire
    except Exception as native_error:
        _send({
            "type": "progress",
            "run_id": run_id,
            "stage": "Checking each study step after the sequence failed",
        })
        return _recover_sequential_analysis(
            snapshot,
            data_type,
            workflow,
            cumulative_snapshot,
            request,
            bridge,
            native_error,
        )


def _prepare_step_data(snapshot: object, bridge: _WorkerBridge) -> None:
    from rc_metastudio.continuous_analysis_snapshot import (
        ContinuousInputSnapshot,
        create_continuous_backend_data,
    )
    from rc_metastudio.diagnostic_analysis_backend import create_diagnostic_r_data
    from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot

    if isinstance(snapshot, BinaryInputSnapshot):
        _create_binary_data(snapshot, bridge)
    elif isinstance(snapshot, ContinuousInputSnapshot):
        bridge.ro.globalenv["tmp_obj"] = create_continuous_backend_data(snapshot, bridge)
    elif isinstance(snapshot, DiagnosticInputSnapshot):
        from rc_metastudio.diagnostic_analysis_backend import DiagnosticBackend

        create_diagnostic_r_data(snapshot, cast(DiagnosticBackend, bridge))
    else:
        raise ValueError("unsupported sequential analysis data family")


def _recover_sequential_analysis(
    snapshot: BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot,
    data_type: str,
    workflow: str,
    cumulative_snapshot: CumulativeAnalysisSnapshot | None,
    request: AnalysisRequest,
    bridge: _WorkerBridge,
    native_error: Exception,
) -> dict[str, object]:
    from rc_metastudio.cumulative_analysis import CumulativeInputSnapshot
    from rc_metastudio.sequential_step_fallback import recover_sequential_steps

    def fit_standard(
        step_snapshot: object, standard_request: AnalysisRequest
    ) -> dict[str, object]:
        _prepare_step_data(step_snapshot, bridge)
        bridge.run_versioned_analysis_request(standard_request.to_mapping())
        raw = bridge.r_object_to_python(bridge.ro.globalenv["result"])
        return _standard_result_model(raw, data_type)

    recovery_snapshot: CumulativeInputSnapshot | CumulativeAnalysisSnapshot
    if workflow == "cumulative":
        if cumulative_snapshot is None:
            raise ValueError("cumulative analysis input is unavailable")
        recovery_snapshot = cumulative_snapshot
    else:
        recovery_snapshot = snapshot
    recovered = recover_sequential_steps(recovery_snapshot, request, fit_standard)
    detail = str(native_error).strip() or type(native_error).__name__
    return {
        "version": 1,
        "texts": {
            "sequential_recovery": (
                "The complete sequence could not be rendered by RCMetaR: "
                f"{detail}\nEach listed step was attempted independently with the selected "
                "method. Failed steps retain their reasons. The sequence figure "
                "is unavailable for this run."
            )
        },
        "sections": [{
            "id": "sequential-recovery", "kind": "text", "order": 0,
            "title": "Incomplete sequence", "source_key": "sequential_recovery",
        }],
        **recovered,
    }


def _standard_result_model(value: object, data_type: str) -> dict[str, object]:
    if not _is_string_mapping(value):
        raise ValueError("RCMetaR returned no standard model values")
    model = value.get("res")
    if data_type == "diagnostic":
        summary = value.get("Summary")
        model = summary.get("MAResults") if _is_string_mapping(summary) else None
    if not _is_string_mapping(model):
        raise ValueError("RCMetaR returned no standard model values")
    return dict(model)

def main() -> int:
    request: object = None
    try:
        line = sys.stdin.readline()
        if not line:
            raise ValueError("analysis worker request was empty")
        request = json.loads(line)
        _execute(request)
        return 0
    except BaseException as error:
        _send(_worker_failure_message(request, error))
        return 1


def _worker_failure_message(request: object, error: BaseException) -> dict[str, object]:
    request_mapping = request if _is_string_mapping(request) else None
    message: dict[str, object] = {
        "type": "failure",
        "run_id": request_mapping.get("run_id", "") if request_mapping else "",
        "error": {
            "type": type(error).__name__,
            "message": str(error),
            "details": traceback.format_exc(),
        },
        "warnings": [],
    }
    if request_mapping is not None:
        _attach_plot_failure_identity(message, request_mapping)
    return message


def _attach_plot_failure_identity(
    message: dict[str, object], request: Mapping[str, object]
) -> None:
    operation = request.get("operation")
    if isinstance(operation, str) and operation in _PLOT_OPERATIONS:
        message["operation"] = request.get("operation")
        message["artifact_identity"] = request.get("artifact_identity")


if __name__ == "__main__":
    raise SystemExit(main())
