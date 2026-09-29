# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Line-oriented child-process entry point for standard binary analyses."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
import json
import math
import sys
import traceback
import warnings
from collections.abc import Mapping

from rc_metastudio.analysis_snapshot import BinaryInputSnapshot, BinaryStudyInput, BinaryCovariateInput


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
        "sections": plain(result.sections),
        "binary_numerics": plain(result.binary_numerics),
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


def _execute(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("analysis worker request must be an object")
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("analysis worker request needs a run identity")
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
    operation = payload.get("operation", "analysis")
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
    _send({"type": "progress", "run_id": run_id, "stage": "Running the statistical method"})
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
    try:
        line = sys.stdin.readline()
        if not line:
            raise ValueError("analysis worker request was empty")
        _execute(json.loads(line))
        return 0
    except BaseException as error:
        request_id = ""
        try:
            request_id = json.loads(line).get("run_id", "")
        except Exception:
            pass
        _send(
            {
                "type": "failure",
                "run_id": request_id,
                "error": {
                    "type": type(error).__name__,
                    "message": str(error),
                    "details": traceback.format_exc(),
                },
                "warnings": [],
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
