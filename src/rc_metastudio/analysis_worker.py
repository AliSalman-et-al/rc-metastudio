# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Line-oriented child process for analyses and typed plot operations."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
import json
from pathlib import Path
import shutil
import sys
import tempfile
import traceback
import warnings
from collections.abc import Mapping

from rc_metastudio.analysis_results import ResultSection
from rc_metastudio.analysis_snapshot import (
    BinaryCovariateInput,
    BinaryInputSnapshot,
    BinaryStudyInput,
)


_PLOT_OPERATIONS = frozenset(("plot_parameters", "plot_export", "plot_edit"))
_PLOT_REGENERATORS = frozenset(("forest", "regression", "funnel", "sroc"))
_PLOT_EXTENSIONS = frozenset(("pdf", "png", "tif", "tiff", "svg"))


def _send(message: Mapping[str, object]) -> None:
    sys.stdout.write(json.dumps(message, allow_nan=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _snapshot_from_mapping(value: object) -> BinaryInputSnapshot:
    if not isinstance(value, Mapping) or value.get("version") != 1:
        raise ValueError("unsupported binary input snapshot")
    studies = value.get("studies")
    covariates = value.get("covariates")
    groups = value.get("groups")
    if not isinstance(studies, list) or not isinstance(covariates, list):
        raise ValueError("binary input snapshot rows are missing")
    if not isinstance(groups, list) or len(groups) != 2:
        raise ValueError("binary input snapshot needs two group names")
    study_rows = []
    for row in studies:
        if not isinstance(row, Mapping):
            raise ValueError("binary input study rows must be objects")
        study_rows.append(BinaryStudyInput(**{field.name: row.get(field.name) for field in fields(BinaryStudyInput)}))
    covariate_rows = []
    for row in covariates:
        if not isinstance(row, Mapping) or not isinstance(row.get("values"), list):
            raise ValueError("binary covariate rows must include values")
        covariate_rows.append(
            BinaryCovariateInput(
                str(row.get("name", "")),
                str(row.get("data_type", "")),
                tuple(row["values"]),
            )
        )
    return BinaryInputSnapshot(
        version=1,
        outcome=str(value.get("outcome", "")),
        time_point=str(value.get("time_point", "")),
        groups=(str(groups[0]), str(groups[1])),
        metric=str(value.get("metric", "")),
        raw_counts_available=value.get("raw_counts_available") is True,
        studies=tuple(study_rows),
        covariates=tuple(covariate_rows),
    )


def _create_binary_data(snapshot: BinaryInputSnapshot, bridge: object) -> object:
    import rpy2.robjects as ro

    studies = snapshot.studies
    ids = [study.id for study in studies]
    covariate_values = []
    for covariate in snapshot.covariates:
        values = covariate.values
        if covariate.data_type == "continuous":
            r_values = bridge._r_numeric_vector(values)
        elif covariate.data_type == "factor":
            r_values = bridge._r_character_vector(values)
        else:
            raise ValueError("unsupported covariate type in binary input snapshot")
        reference = next((str(item) for item in values if item not in (None, "")), "")
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
    covariates = bridge.execute_r_function("list", *covariate_values)
    kwargs: dict[str, object] = {
        "y": bridge._r_numeric_vector([study.estimate for study in studies]),
        "SE": bridge._r_numeric_vector([study.standard_error for study in studies]),
        "study.names": bridge._r_character_vector([study.name for study in studies]),
        "years": bridge._r_year_vector([study.year for study in studies]),
        "covariates": covariates,
    }
    if snapshot.raw_counts_available:
        treatment_events = [study.treatment_events for study in studies]
        treatment_totals = [study.treatment_total for study in studies]
        control_events = [study.control_events for study in studies]
        control_totals = [study.control_total for study in studies]
        kwargs.update(
            {
                "g1O1": bridge._r_numeric_vector(treatment_events),
                "g1O2": bridge._r_numeric_vector(
                    [total - events for total, events in zip(treatment_totals, treatment_events)]
                ),
                "g2O1": bridge._r_numeric_vector(control_events),
                "g2O2": bridge._r_numeric_vector(
                    [total - events for total, events in zip(control_totals, control_events)]
                ),
            }
        )
    r_data = bridge.execute_r_function("rcmetar.create.binary.data", **kwargs)
    ro.globalenv["tmp_obj"] = r_data
    return r_data


def _wire_result(result: object) -> dict[str, object]:
    def plain(value: object) -> object:
        if is_dataclass(value):
            return {item.name: plain(getattr(value, item.name)) for item in fields(value)}
        if isinstance(value, Mapping):
            return {str(key): plain(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            return [plain(item) for item in value]
        return value

    return {
        "version": result.version,
        "texts": plain(result.texts),
        "images": plain(result.images),
        "display_images": plain(result.display_images),
        "image_var_names": plain(result.image_var_names),
        "image_params_paths": plain(result.image_params_paths),
        "image_order": plain(result.image_order),
        "plot_capabilities": plain(result.plot_capabilities),
        "sections": [_wire_section(section) for section in result.sections],
        "binary_numerics": plain(result.binary_numerics),
    }


def _wire_section(section: object) -> dict[str, object]:
    if not isinstance(section, ResultSection):
        raise TypeError("analysis result contains an invalid result section")
    return {
        "id": section.semantic_id,
        "kind": section.kind,
        "order": section.order,
        "title": section.title,
        "source_key": section.source_key,
    }


def _wire_methods(bridge: object, metric: str, workflow: str) -> dict[str, object]:
    methods = bridge.get_available_methods(
        for_data_type="binary",
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
                "binary", method, workflow=workflow
            ),
        }
    return {"available_methods": methods, "details": details}


def _wire_json(value: object) -> object:
    if is_dataclass(value):
        return {item.name: _wire_json(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _wire_json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_wire_json(item) for item in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError("analysis metadata contains a non-JSON value: %s" % type(value).__name__)


def _initialize_backend():
    from rc_metastudio import r_backend

    bridge = r_backend.install_r_backend()
    loader = bridge.RLibraryLoader()
    loader.load_metafor()
    loader.load_rcmetar()
    loader.load_grid()
    return bridge


def _plot_identity_from_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("plot worker request needs an artifact identity")
    analysis_id = value.get("analysis_id")
    figure_key = value.get("figure_key")
    generation = value.get("generation")
    if (
        not isinstance(analysis_id, str)
        or not analysis_id
        or not isinstance(figure_key, str)
        or not figure_key
        or not isinstance(generation, int)
        or isinstance(generation, bool)
        or generation < 0
        or set(value) != {"analysis_id", "figure_key", "generation"}
    ):
        raise ValueError("plot artifact identity is invalid")
    return {
        "analysis_id": analysis_id,
        "figure_key": figure_key,
        "generation": generation,
    }


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


def _plot_parameter_paths(regenerator: str) -> tuple[str, str | None]:
    if regenerator in ("forest", "sroc"):
        return "fp_outpath", "fp_display_path"
    if regenerator == "regression":
        return "bp_outpath", "bp_display_path"
    if regenerator == "funnel":
        return "funnel.outpath", None
    raise ValueError("unsupported plot regenerator: %s" % regenerator)


def _execute_plot(payload: Mapping[str, object], operation: str, run_id: str) -> None:
    from rc_metastudio.plot_service import PlotService

    identity = _plot_identity_from_mapping(payload.get("artifact_identity"))
    regenerator = payload.get("regenerator")
    if not isinstance(regenerator, str) or regenerator not in _PLOT_REGENERATORS:
        raise ValueError("unsupported plot regenerator: %s" % regenerator)
    params_value = payload.get("params_path")
    stage_value = payload.get("staging_dir")
    if not isinstance(params_value, str) or not params_value:
        raise ValueError("plot worker request needs a parameter path")
    if not isinstance(stage_value, str) or not stage_value:
        raise ValueError("plot worker request needs a staging directory")
    source_base = Path(params_value).expanduser().resolve()
    staging_root = Path(stage_value).expanduser().resolve()
    if not staging_root.is_dir():
        raise ValueError("plot staging directory does not exist")

    output_extension = None
    if operation in ("plot_export", "plot_edit"):
        output_extension = _plot_extension(payload.get("output_extension"))
    stage = Path(
        tempfile.mkdtemp(prefix=f"rcms-{operation}-", dir=str(staging_root))
    )
    input_dir = stage / "input"
    candidate_dir = stage / "candidate"
    input_dir.mkdir()
    candidate_dir.mkdir()
    staged_base = input_dir / "plot"
    _copy_plot_sidecars(
        source_base,
        staged_base,
        _plot_source_sidecars(operation, regenerator),
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

    if operation == "plot_parameters":
        params = service.load_params(str(staged_base))
        if params is None:
            raise ValueError("stored plot parameters are unavailable")
        result: dict[str, object] = {
            "params": _wire_json(params),
            "staging_path": str(stage),
        }
    elif operation == "plot_export":
        candidate_image = candidate_dir / ("figure." + str(output_extension))
        service.export(
            regenerator=regenerator,
            params_path=str(staged_base),
            output_path=str(candidate_image),
        )
        _require_candidate(candidate_image, stage)
        result = {
            "staging_path": str(stage),
            "candidate": {"image_path": str(candidate_image)},
        }
    elif operation == "plot_edit":
        result = _execute_plot_edit(
            payload,
            regenerator,
            str(output_extension),
            staged_base,
            candidate_dir,
            stage,
            bridge,
            service,
        )
    else:
        raise ValueError("unsupported plot worker operation")

    _send(
        {
            "type": "plot_result",
            "run_id": run_id,
            "operation": operation,
            "artifact_identity": identity,
            "result": result,
        }
    )


def _execute_plot_edit(
    payload: Mapping[str, object],
    regenerator: str,
    extension: str,
    staged_base: Path,
    candidate_dir: Path,
    stage: Path,
    bridge: object,
    service: object,
) -> dict[str, object]:
    updated_value = payload.get("updated_params")
    if not isinstance(updated_value, Mapping) or any(
        not isinstance(key, str) for key in updated_value
    ):
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

    output_param, display_param = _plot_parameter_paths(regenerator)
    updated_params = dict(updated_value)
    candidate_image = candidate_dir / ("figure." + extension)
    candidate_display: Path | None = None
    if display_param is not None and display_param in updated_params:
        if display_path is None and updated_params.get(display_param):
            raise ValueError("plot edit request needs a display destination")
        if display_path is not None:
            candidate_display = candidate_dir / "display.svg"
    elif display_path is not None:
        raise ValueError("plot edit request has no display parameter")

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
    return {"staging_path": str(stage), "candidate": candidate}


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


def _execute(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("analysis worker request must be an object")
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("analysis worker request needs a run identity")
    operation = payload.get("operation", "analysis")
    if isinstance(operation, str) and operation in _PLOT_OPERATIONS:
        _execute_plot(payload, str(operation), run_id)
        return
    if operation not in ("methods", "analysis"):
        raise ValueError("unsupported analysis worker operation")
    _send({"type": "progress", "run_id": run_id, "stage": "Starting analysis engine"})
    bridge = _initialize_backend()
    backend_versions = {
        "R": bridge.get_r_version_string(),
        "metafor": bridge.get_r_package_version("metafor"),
        "RCMetaR": bridge.get_r_package_version("RCMetaR"),
    }
    snapshot = _snapshot_from_mapping(payload.get("input"))
    _send({"type": "progress", "run_id": run_id, "stage": "Preparing study data"})
    _create_binary_data(snapshot, bridge)
    if operation == "methods":
        query = payload.get("query")
        if not isinstance(query, Mapping):
            raise ValueError("analysis worker method request needs a query")
        if query.get("data_type") != "binary" or query.get("workflow") != "standard":
            raise ValueError("worker only provides standard binary method metadata")
        if query.get("metric") != snapshot.metric:
            raise ValueError("method query metric does not match its input snapshot")
        catalogue = _wire_json(
            _wire_methods(bridge, str(query["metric"]), str(query["workflow"]))
        )
        _send(
            {
                "type": "methods",
                "run_id": run_id,
                "catalogue": catalogue,
                "backend_versions": backend_versions,
            }
        )
        return

    if operation != "analysis":
        raise ValueError("unsupported analysis worker operation")
    request = payload.get("request")
    if not isinstance(request, Mapping):
        raise ValueError("analysis worker request needs an analysis specification")
    if (
        request.get("version") != 1
        or request.get("data_type") != "binary"
        or request.get("workflow") != "standard"
        or request.get("metric") != snapshot.metric
    ):
        raise ValueError("worker only accepts a matching standard binary request")
    _send(
        {
            "type": "progress",
            "run_id": run_id,
            "stage": "Running the statistical method",
        }
    )
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        result = bridge.run_versioned_analysis_request(request)
    _send(
        {
            "type": "result",
            "run_id": run_id,
            "result": _wire_result(result),
            "warnings": [str(item.message) for item in observed],
            "backend_versions": backend_versions,
        }
    )


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
        message: dict[str, object] = {
            "type": "failure",
            "run_id": request.get("run_id", "") if isinstance(request, Mapping) else "",
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "details": traceback.format_exc(),
            },
            "warnings": [],
        }
        operation = request.get("operation") if isinstance(request, Mapping) else None
        if isinstance(operation, str) and operation in _PLOT_OPERATIONS:
            message["operation"] = request.get("operation")
            message["artifact_identity"] = request.get("artifact_identity")
        _send(message)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
