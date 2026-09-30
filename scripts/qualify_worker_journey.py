#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qualify a packaged owned-worker result on the host that runs the package."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import signal
import subprocess
import time
import uuid
from collections.abc import Mapping, Sequence
from typing import Literal, TypeGuard


JsonObject = dict[str, object]
WorkerProcessState = Literal["terminated", "cleanup_unconfirmed"]


class _WorkerTimeoutExpired(subprocess.TimeoutExpired):
    """A timeout with the worker cleanup outcome retained as typed fields."""

    worker_pid: int | None
    worker_returncode: int | None
    worker_process_state: WorkerProcessState

    def __init__(
        self,
        command: Sequence[str],
        timeout: float,
        *,
        output: str | bytes | None,
        stderr: str | bytes | None,
        worker_pid: int | None,
        worker_returncode: int | None,
    ) -> None:
        super().__init__(command, timeout, output=output, stderr=stderr)
        self.worker_pid = worker_pid
        self.worker_returncode = worker_returncode
        self.worker_process_state = (
            "terminated" if worker_returncode is not None else "cleanup_unconfirmed"
        )


_CORE_ROUTES = (
    "binary.standard",
    "binary.cumulative",
    "binary.leave-one-out",
    "continuous.standard",
    "diagnostic.standard",
)

_ROUTES = {
    "binary.standard": ("amino.rcms", ("binary", "standard", "OR", "binary.random")),
    "binary.cumulative": (
        "amino.rcms",
        ("binary", "cumulative", "OR", "binary.random"),
    ),
    "binary.leave-one-out": (
        "amino.rcms",
        ("binary", "leave-one-out", "OR", "binary.random"),
    ),
    "continuous.standard": (
        "continuous.rcms",
        ("continuous", "standard", "SMD", "continuous.random"),
    ),
    "diagnostic.standard": (
        "lymph.rcms",
        ("diagnostic", "standard", "Sens", "diagnostic.random"),
    ),
    "binary.one-arm": ("amino.rcms", ("binary", "standard", "PLO", "binary.random")),
    "continuous.entered-effect": (
        "continuous.rcms",
        ("continuous", "standard", "SMD", "continuous.random"),
    ),
    "binary.meta-regression": (
        "amino.rcms",
        ("binary", "meta-regression", "OR", "meta.regression"),
    ),
    "continuous.meta-regression": (
        "continuous.rcms",
        ("continuous", "meta-regression", "SMD", "meta.regression"),
    ),
    "diagnostic.reitsma-meta-regression": (
        "lymph.rcms",
        (
            "diagnostic",
            "meta-regression",
            "Sensitivity and specificity",
            "diagnostic.reitsma",
        ),
    ),
    "diagnostic.reitsma": (
        "lymph.rcms",
        ("diagnostic", "standard", "Sensitivity and specificity", "diagnostic.reitsma"),
    ),
    "binary.small-study-effects": (
        "amino.rcms",
        ("binary", "small-study-effects", "OR", "small.study.effects"),
    ),
    "binary.plot-edit": (
        "amino.rcms",
        ("binary", "standard", "OR", "binary.random"),
    ),
    "diagnostic.subgroup": (
        "lymph.rcms",
        ("diagnostic", "subgroup", "Sens", "diagnostic.random"),
    ),
    "binary.subgroup": (
        "amino.rcms", ("binary", "subgroup", "OR", "binary.random")
    ),
    "continuous.subgroup": (
        "continuous.rcms", ("continuous", "subgroup", "SMD", "continuous.random")
    ),
    "continuous.cumulative": (
        "continuous.rcms", ("continuous", "cumulative", "SMD", "continuous.random")
    ),
    "diagnostic.cumulative": (
        "lymph.rcms", ("diagnostic", "cumulative", "Sens", "diagnostic.random")
    ),
    "continuous.leave-one-out": (
        "continuous.rcms", ("continuous", "leave-one-out", "SMD", "continuous.random")
    ),
    "diagnostic.leave-one-out": (
        "lymph.rcms", ("diagnostic", "leave-one-out", "Sens", "diagnostic.random")
    ),
}

_METHOD_VARIANT_ROUTE_SPECS = tuple(
    (family, workflow, metric, method, sample)
    for family, workflows, metric, methods, sample in (
        (
            "binary",
            ("standard", "cumulative", "leave-one-out", "subgroup"),
            "OR",
            (
                "binary.fixed.inv.var",
                "binary.fixed.mh",
                "binary.fixed.peto",
            ),
            "amino.rcms",
        ),
        (
            "continuous",
            ("standard", "cumulative", "leave-one-out", "subgroup"),
            "SMD",
            ("continuous.fixed",),
            "continuous.rcms",
        ),
        (
            "diagnostic",
            ("standard", "cumulative", "leave-one-out", "subgroup"),
            "Sens",
            ("diagnostic.fixed.inv.var",),
            "lymph.rcms",
        ),
        (
            "diagnostic",
            ("standard", "cumulative", "leave-one-out", "subgroup"),
            "DOR",
            ("diagnostic.fixed.mh", "diagnostic.fixed.peto"),
            "lymph.rcms",
        ),
    )
    for workflow in workflows
    for method in methods
)
_METHOD_VARIANT_ROUTES = {
    "%s.%s.%s" % (family, method, workflow): (
        sample,
        (family, workflow, metric, method),
    )
    for family, workflow, metric, method, sample in _METHOD_VARIANT_ROUTE_SPECS
}
_ROUTES.update(_METHOD_VARIANT_ROUTES)

_SUBGROUP_ROUTES = frozenset(
    {"binary.subgroup", "continuous.subgroup", "diagnostic.subgroup"}
    | {
        route
        for route, (_sample, (_family, workflow, _metric, _method))
        in _METHOD_VARIANT_ROUTES.items()
        if workflow == "subgroup"
    }
)
_SEQUENTIAL_ROUTES = frozenset(
    {
        "continuous.cumulative",
        "diagnostic.cumulative",
        "continuous.leave-one-out",
        "diagnostic.leave-one-out",
    }
    | {
        route
        for route, (_sample, (_family, workflow, _metric, _method))
        in _METHOD_VARIANT_ROUTES.items()
        if workflow in {"cumulative", "leave-one-out"}
    }
)
_BINARY_METHOD_WORKFLOW_ROUTES = frozenset(
    {
        "binary.standard",
        "binary.cumulative",
        "binary.leave-one-out",
    }
    | {
        route
        for route, (_sample, (family, workflow, _metric, _method))
        in _METHOD_VARIANT_ROUTES.items()
        if family == "binary"
        and workflow in {"standard", "cumulative", "leave-one-out"}
    }
)


def qualify(
    executable: Path,
    sample: Path,
    destination: Path,
    output: Path,
    *,
    artifact: Path,
    r_home: Path | None = None,
    r_libs: Path | None = None,
    route_timeout: int = 120,
    routes: tuple[str, ...] | None = None,
) -> dict[str, object]:
    """Run each route in a fresh package process and retain its evidence."""
    selected_routes = _validate_qualification_request(
        artifact, sample, route_timeout, routes
    )
    executable = executable.expanduser().resolve()
    sample = sample.expanduser().resolve()
    destination = destination.expanduser().resolve()
    output = output.expanduser().resolve()
    artifact = artifact.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    environment = _package_environment(r_home, r_libs)
    analysis_runs: list[object] = []
    route_results: list[JsonObject] = []
    result: dict[str, object] = {
        "schema_version": 2,
        "gate": (
            "bounded-core-worker"
            if selected_routes == _CORE_ROUTES
            else "selected-routes"
        ),
        "requested_routes": list(selected_routes),
        "passed": False,
        "host": _host_identity(),
        "package_sha256": _sha256_file(artifact),
        "sample_project_sha256": _sha256_file(sample),
        "analysis_runs": analysis_runs,
        "routes": route_results,
    }
    _write_result(output, result)
    for route in selected_routes:
        _qualify_route(
            route,
            executable=executable,
            sample_root=sample.parent,
            destination=destination,
            output=output,
            result=result,
            route_results=route_results,
            analysis_runs=analysis_runs,
            timeout=route_timeout,
            environment=environment,
        )
    result["passed"] = _qualification_passed(
        route_results, analysis_runs, selected_routes
    )
    _write_result(output, result)
    return result


def _validate_qualification_request(
    artifact: Path,
    sample: Path,
    route_timeout: int,
    routes: tuple[str, ...] | None,
) -> tuple[str, ...]:
    if not artifact.is_file():
        raise FileNotFoundError("the qualified package artifact is unavailable")
    if not sample.is_file():
        raise FileNotFoundError("the packaged sample project is unavailable")
    if route_timeout <= 0:
        raise ValueError("route timeout must be a positive number of seconds")
    selected_routes = _CORE_ROUTES if routes is None else routes
    if not selected_routes:
        raise ValueError("at least one qualification route is required")
    if len(set(selected_routes)) != len(selected_routes):
        raise ValueError("qualification routes must not be repeated")
    unknown_routes = set(selected_routes).difference(_ROUTES)
    if unknown_routes:
        raise ValueError("unknown qualification route: %s" % ", ".join(sorted(unknown_routes)))

    return selected_routes


def _package_environment(
    r_home: Path | None, r_libs: Path | None
) -> dict[str, str]:
    environment: dict[str, str] = os.environ.copy()
    for name in (
        "R_HOME", "R_LIBS", "R_LIBS_USER", "RCMS_R_HOME", "RCMS_R_LIBS",
        "RCMS_REQUIRE_IN_PROCESS_RPY2",
    ):
        environment.pop(name, None)
    if r_home is not None:
        environment["RCMS_R_HOME"] = str(r_home)
    if r_libs is not None:
        environment["RCMS_R_LIBS"] = str(r_libs)
    return environment


def _qualify_route(
    route: str,
    *,
    executable: Path,
    sample_root: Path,
    destination: Path,
    output: Path,
    result: dict[str, object],
    route_results: list[JsonObject],
    analysis_runs: list[object],
    timeout: int,
    environment: Mapping[str, str],
) -> None:
    route_sample = sample_root / _ROUTES[route][0]
    observation_path = _observation_path(output, route)
    route_destination = _route_destination(destination, route)
    route_result: JsonObject = {
        "route": route,
        "status": "running",
        "timeout_seconds": timeout,
        "sample_project": str(route_sample),
    }
    route_results.append(route_result)
    _write_result(output, result)
    if not route_sample.is_file():
        _finish_route(output, result, route_result, "unavailable", "packaged sample project is missing")
        return
    completed = _run_route_process(
        route,
        executable,
        route_sample,
        route_destination,
        observation_path,
        route_result,
        result,
        output,
        timeout,
        environment,
    )
    if completed is None:
        return
    route_result["sample_project_sha256"] = _sha256_file(route_sample)
    route_result["stdout"] = _tail(completed.stdout)
    route_result["stderr"] = _tail(completed.stderr)
    journey = _read_route_observation(observation_path, route_result)
    if journey is None:
        _write_result(output, result)
        return
    _accept_route_observation(
        route, journey, route_result, result, analysis_runs, output
    )


def _observation_path(output: Path, route: str) -> Path:
    slug = route.replace(".", "-")
    return output.with_name(
        "%s.%s.%s.observation.json" % (output.stem, slug, uuid.uuid4().hex)
    )


def _route_destination(destination: Path, route: str) -> Path:
    slug = route.replace(".", "-")
    return destination.with_name(
        "%s-%s%s" % (destination.stem, slug, destination.suffix)
    )


def _run_route_process(
    route: str,
    executable: Path,
    route_sample: Path,
    route_destination: Path,
    observation_path: Path,
    route_result: JsonObject,
    result: dict[str, object],
    output: Path,
    timeout: int,
    environment: Mapping[str, str],
) -> subprocess.CompletedProcess[str] | None:
    command = [
        str(executable),
        "--automation-package-worker-journey",
        str(observation_path),
        str(route_sample),
        str(route_destination),
        route,
    ]
    started = time.monotonic()
    try:
        completed = _run_package(command, timeout=timeout, environment=environment)
    except subprocess.TimeoutExpired as error:
        _record_timeout(route_result, error, timeout)
    except subprocess.CalledProcessError as error:
        _record_process_failure(route_result, error, started)
    else:
        route_result["elapsed_seconds"] = round(time.monotonic() - started, 2)
        return completed
    _write_result(output, result)
    return None


def _record_timeout(
    route_result: JsonObject, error: subprocess.TimeoutExpired, timeout: int
) -> None:
    route_result.update(
        status="timed_out",
        elapsed_seconds=timeout,
        worker_pid=getattr(error, "worker_pid", None),
        worker_returncode=getattr(error, "worker_returncode", None),
        worker_process_state=getattr(error, "worker_process_state", "unknown"),
        stdout=_output_text(error.stdout),
        stderr=_output_text(error.stderr),
    )


def _record_process_failure(
    route_result: JsonObject,
    error: subprocess.CalledProcessError,
    started: float,
) -> None:
    route_result.update(
        status="failed",
        elapsed_seconds=round(time.monotonic() - started, 2),
        return_code=error.returncode,
        stdout=_output_text(error.stdout),
        stderr=_output_text(error.stderr),
    )


def _read_route_observation(path: Path, route_result: JsonObject) -> JsonObject | None:
    try:
        journey: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        route_result.update(
            status="failed",
            details="worker process did not write valid evidence: %s" % error,
        )
        return None
    if not _is_json_object(journey):
        route_result.update(
            status="failed",
            details="packaged worker evidence must be a JSON object",
        )
        return None
    route_result["observation"] = journey
    return journey


def _accept_route_observation(
    route: str,
    journey: JsonObject,
    route_result: JsonObject,
    result: dict[str, object],
    analysis_runs: list[object],
    output: Path,
) -> None:
    qualification_status = journey.get("qualification_status", "complete")
    if qualification_status in {"unsupported", "unqualified"}:
        status = (
            "unsupported" if qualification_status == "unsupported" else "unqualified"
        )
        _finish_route(
            output,
            result,
            route_result,
            status,
            journey.get("details", "route did not meet its qualification contract"),
        )
        return
    if not _route_observation_valid(route, journey):
        _finish_route(
            output,
            result,
            route_result,
            "failed",
            "packaged route did not meet its evidence contract",
        )
        return
    route_runs = _json_objects(journey.get("analysis_runs"))
    if route_runs is None:
        _finish_route(
            output,
            result,
            route_result,
            "failed",
            "packaged worker evidence has invalid analysis runs",
        )
        return
    route_result["status"] = "complete"
    analysis_runs.extend(route_runs)
    _write_result(output, result)


def _finish_route(
    output: Path,
    result: dict[str, object],
    route_result: JsonObject,
    status: str,
    details: object,
) -> None:
    route_result.update(status=status, details=details)
    _write_result(output, result)


def _qualification_passed(
    route_results: list[JsonObject],
    analysis_runs: list[object],
    routes: tuple[str, ...],
) -> bool:
    return all(route.get("status") == "complete" for route in route_results) and _analysis_runs_valid(
        analysis_runs, routes
    )


def _write_result(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _output_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return _tail(value or "")


def _tail(value: str, limit: int = 4000) -> str:
    return value[-limit:]


def _run_package(
    command: Sequence[str], *, timeout: int, environment: Mapping[str, str]
) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
        creationflags=(
            subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        ),
        start_new_session=os.name != "nt",
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise _worker_timeout_error(process, command, timeout, error) from error
    if process.returncode:
        raise subprocess.CalledProcessError(
            process.returncode, command, output=stdout, stderr=stderr
        )
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def _worker_timeout_error(
    process: subprocess.Popen[str],
    command: Sequence[str],
    timeout: int,
    error: subprocess.TimeoutExpired,
) -> _WorkerTimeoutExpired:
    _terminate_process_tree(process)
    stdout, stderr = _drain_timed_out_process(process, error)
    return _WorkerTimeoutExpired(
        command,
        timeout,
        output=stdout or error.output,
        stderr=stderr or error.stderr,
        worker_pid=process.pid,
        worker_returncode=process.poll(),
    )


def _drain_timed_out_process(
    process: subprocess.Popen[str], error: subprocess.TimeoutExpired
) -> tuple[str | bytes | None, str | bytes | None]:
    try:
        return process.communicate(timeout=10)
    except subprocess.TimeoutExpired as cleanup_error:
        _kill_unresponsive_process(process)
        return (
            error.output or cleanup_error.output,
            error.stderr or cleanup_error.stderr,
        )


def _kill_unresponsive_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.kill()
    for pipe in (process.stdout, process.stderr):
        if pipe is not None:
            pipe.close()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
        if process.poll() is None:
            process.kill()
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        if process.poll() is None:
            process.kill()
    except OSError:
        if process.poll() is None:
            process.kill()


def _route_observation_valid(route: str, journey: object) -> bool:
    if not _is_json_object(journey):
        return False
    route_spec = _ROUTES.get(route)
    if route_spec is None or not _journey_complete(route, journey):
        return False
    runs = _route_runs(route, route_spec[1], journey)
    if runs is None:
        return False
    if route in _SUBGROUP_ROUTES:
        return _subgroup_observation_valid(route, journey, runs)
    return _single_route_observation_valid(route, journey, runs[0])


def _journey_complete(route: str, journey: JsonObject) -> bool:
    reopened_count = journey.get("reopened_analysis_count")
    return (
        journey.get("route") == route
        and _journey_runtime_valid(journey)
        and _journey_analysis_status_valid(route, journey)
        and _journey_reopen_count_valid(route, reopened_count)
    )


def _journey_runtime_valid(journey: JsonObject) -> bool:
    return (
        journey.get("worker_completed") is True
        and journey.get("main_process_r_bridge_absent") is True
        and journey.get("event_loop_responsive") is True
    )


def _journey_analysis_status_valid(route: str, journey: JsonObject) -> bool:
    accepted = {"complete", "partial"} if route in _SEQUENTIAL_ROUTES else {"complete"}
    return journey.get("saved_analysis_status") in accepted


def _journey_reopen_count_valid(route: str, value: object) -> bool:
    required = 2 if route in _SUBGROUP_ROUTES else 1
    return _is_integer(value) and value >= required


def _route_runs(
    route: str, expected: tuple[str, ...], journey: JsonObject
) -> list[JsonObject] | None:
    runs = journey.get("analysis_runs")
    if not isinstance(runs, list) or len(runs) != _expected_run_count(route):
        return None
    valid_runs = _json_objects(runs)
    if valid_runs is None or not _route_runs_match(
        valid_runs, expected, allow_partial=route in _SEQUENTIAL_ROUTES
    ):
        return None
    return valid_runs


def _expected_run_count(route: str) -> int:
    return 2 if route in _SUBGROUP_ROUTES else 1


def _route_runs_match(
    runs: list[JsonObject], expected: tuple[str, ...], *, allow_partial: bool = False
) -> bool:
    return all(
        _analysis_run_valid(run, allow_partial=allow_partial)
        and _run_matches_identity(run, expected)
        for run in runs
    )


def _run_matches_identity(run: JsonObject, expected: tuple[str, ...]) -> bool:
    return (run.get("data_type"), run.get("workflow"), run.get("metric"), run.get("method")) == expected


def _subgroup_observation_valid(
    route: str, journey: JsonObject, runs: list[JsonObject]
) -> bool:
    if (
        journey.get("saved_edit_copy_opened") is not True
        or journey.get("live_project_confidence_level") != 95.0
        or journey.get("saved_edit_copy_confidence_level") != 90.0
        or journey.get("saved_edit_copy_missing_policy") != "exclude"
    ):
        return False
    policies: set[str] = set()
    study_orders: list[tuple[str, ...]] = []
    for run in runs:
        details = _subgroup_run_valid(route, run)
        if details is None:
            return False
        policy, study_order = details
        policies.add(policy)
        study_orders.append(study_order)
    return policies == {"exclude", "missing_category"} and len(set(study_orders)) == 1


def _subgroup_run_valid(
    route: str, run: JsonObject,
) -> tuple[str, tuple[str, ...]] | None:
    details = _subgroup_run_details(route, run)
    if details is None:
        return None
    policy, study_order, evidence = details
    if not _result_figure_export_valid(run, evidence):
        return None
    return policy, tuple(study_order)


def _subgroup_run_details(
    route: str, run: JsonObject,
) -> tuple[str, list[str], JsonObject] | None:
    evidence = _validated_subgroup_evidence(route, run.get("result_evidence"))
    if evidence is None:
        return None
    return _subgroup_run_fields(run, evidence)


def _subgroup_run_fields(
    run: JsonObject, evidence: JsonObject
) -> tuple[str, list[str], JsonObject] | None:
    policy = evidence.get("missing_policy")
    study_order = run.get("study_order")
    if not isinstance(policy, str):
        return None
    if not _string_list(study_order):
        return None
    if not _subgroup_assignments_match(evidence, study_order):
        return None
    return policy, study_order, evidence


def _subgroup_assignments_match(evidence: JsonObject, study_order: list[str]) -> bool:
    assignments = _json_objects(evidence.get("assignments"))
    return (
        assignments is not None
        and evidence.get("input_study_count") == len(study_order)
        and [row.get("study_name") for row in assignments] == study_order
    )


def _validated_subgroup_evidence(route: str, value: object) -> JsonObject | None:
    if not _is_json_object(value):
        return None
    return value if _route_result_evidence_valid(route, value) else None


def _single_route_observation_valid(
    route: str, journey: JsonObject, run: JsonObject
) -> bool:
    if not _core_route_confirmation_valid(route, journey):
        return False
    if route in _CORE_ROUTES:
        return True
    evidence = run.get("result_evidence")
    if not _is_json_object(evidence):
        return False
    if not _route_result_evidence_valid(route, evidence):
        return False
    if not _route_reopen_confirmation_valid(route, run):
        return False
    if not _route_study_order_valid(route, run, evidence):
        return False
    if not _route_plot_edit_valid(route, run):
        return False
    return _result_figure_export_valid(run, evidence)


def _route_reopen_confirmation_valid(route: str, run: JsonObject) -> bool:
    return (
        route != "diagnostic.reitsma-meta-regression"
        or run.get("report_view_after_reopen") is True
    )


def _route_plot_edit_valid(route: str, run: JsonObject) -> bool:
    return route != "binary.plot-edit" or _plot_edit_journey_valid(run)


def _plot_edit_journey_valid(run: JsonObject) -> bool:
    regeneration = run.get("saved_plot_regeneration")
    edit = run.get("saved_plot_edit")
    artifact = run.get("saved_edited_artifact")
    reopened = run.get("saved_edited_artifact_after_reopen")
    records = _plot_edit_records(regeneration, edit, artifact, reopened)
    if records is None:
        return False
    regeneration, edit, artifact, reopened = records
    regeneration_request = regeneration.get("worker_request")
    edit_request = edit.get("worker_request")
    result_evidence = run.get("result_evidence")
    return (
        _plot_edit_request_identity_valid(
            regeneration_request, edit_request, result_evidence, artifact
        )
        and _plot_edit_persistence_valid(regeneration, edit, artifact, reopened, run)
        and _plot_edit_style_valid(artifact, reopened)
        and _plot_edit_completion_valid(regeneration, edit, run)
    )


def _plot_edit_records(
    regeneration: object,
    edit: object,
    artifact: object,
    reopened: object,
) -> tuple[JsonObject, JsonObject, JsonObject, JsonObject] | None:
    if not _is_json_object(regeneration):
        return None
    if not _is_json_object(edit):
        return None
    if not _is_json_object(artifact):
        return None
    if not _is_json_object(reopened):
        return None
    if not _plot_operation_evidence_valid(regeneration, "saved_plot_render"):
        return None
    if not _plot_operation_evidence_valid(edit, "saved_plot_render"):
        return None
    return regeneration, edit, artifact, reopened


def _plot_edit_request_identity_valid(
    regeneration_request, edit_request, result_evidence, artifact
) -> bool:
    identities = _plot_edit_artifact_identities(
        regeneration_request, edit_request
    )
    if identities is None or not _is_json_object(result_evidence):
        return False
    regeneration_identity, edit_identity = identities
    return (
        result_evidence.get("figure_title") == "Forest Plot"
        and result_evidence.get("figure_key") == artifact.get("figure_key")
        and result_evidence.get("figure_key") == regeneration_identity.get("figure_key")
        and _plot_identities_share_figure(regeneration_identity, edit_identity)
    )


def _plot_edit_artifact_identities(regeneration_request, edit_request):
    if not _is_json_object(regeneration_request) or not _is_json_object(edit_request):
        return None
    regeneration = regeneration_request.get("artifact_identity")
    edit = edit_request.get("artifact_identity")
    if not _is_json_object(regeneration) or not _is_json_object(edit):
        return None
    return regeneration, edit


def _plot_edit_persistence_valid(regeneration, edit, artifact, reopened, run) -> bool:
    return (
        _plot_edit_revision_chain_valid(regeneration, edit, artifact, reopened)
        and _plot_edit_artifact_valid(artifact, reopened, run)
    )


def _plot_edit_revision_chain_valid(regeneration, edit, artifact, reopened) -> bool:
    return (
        artifact.get("record_revision") == reopened.get("record_revision")
        and artifact.get("record_revision") == edit.get("record_revision_after")
        and edit.get("record_revision_before") == regeneration.get("record_revision_after")
        and regeneration.get("record_revision_after") != edit.get("record_revision_after")
        and _all_sha256_text(
            artifact.get("record_revision"),
            regeneration.get("record_revision_before"),
            regeneration.get("record_revision_after"),
            regeneration.get("stored_image_sha256"),
            edit.get("record_revision_before"),
            edit.get("record_revision_after"),
            artifact.get("image_sha256"),
        )
    )


def _plot_edit_artifact_valid(artifact, reopened, run) -> bool:
    return (
        artifact.get("persistence") == "saved_record"
        and artifact.get("record_id") == run.get("analysis_id")
        and reopened.get("record_id") == run.get("analysis_id")
        and artifact.get("image_sha256") == reopened.get("image_sha256")
        and artifact.get("figure_key") == reopened.get("figure_key")
    )


def _plot_edit_style_valid(artifact, reopened) -> bool:
    style = artifact.get("style")
    reopened_style = reopened.get("style")
    return (
        _is_json_object(style)
        and style.get("fp_xlabel") == "Qualification effect direction"
        and _is_json_object(reopened_style)
        and reopened_style.get("fp_xlabel") == style.get("fp_xlabel")
    )


def _plot_edit_completion_valid(regeneration, edit, run) -> bool:
    return (
        regeneration.get("worker_completed") is True
        and edit.get("worker_completed") is True
        and run.get("source_result_unchanged") is True
        and run.get("saved_reopened") is True
        and run.get("saved_edited_reopened") is True
    )


def _all_sha256_text(*values: object) -> bool:
    return all(_sha256_text(value) for value in values)


def _plot_operation_evidence_valid(value: object, operation: str) -> bool:
    if not _is_json_object(value):
        return False
    request = value.get("worker_request")
    valid = (
        value.get("worker_completed") is True
        and _plot_request_identity_valid(request, operation)
    )
    if operation == "plot_export":
        output_bytes = value.get("output_bytes")
        return (
            valid
            and _is_integer(output_bytes)
            and output_bytes > 0
            and _sha256_text(value.get("output_sha256"))
        )
    return valid


def _plot_request_identity_valid(value: object, operation: str) -> bool:
    if not _is_json_object(value):
        return False
    identity = value.get("artifact_identity")
    if not _is_json_object(identity):
        return False
    return (
        value.get("operation") == operation
        and isinstance(value.get("run_id"), str)
        and bool(value["run_id"])
        and _plot_artifact_identity_valid(identity)
    )


def _plot_artifact_identity_valid(identity: JsonObject) -> bool:
    generation = identity.get("generation")
    return (
        isinstance(identity.get("analysis_id"), str)
        and bool(identity["analysis_id"])
        and isinstance(identity.get("figure_key"), str)
        and bool(identity["figure_key"])
        and _is_integer(generation)
        and generation > 0
    )


def _plot_identities_share_figure(left: object, right: object) -> bool:
    if not _is_json_object(left) or not _is_json_object(right):
        return False
    left_generation = left.get("generation")
    right_generation = right.get("generation")
    return (
        left.get("analysis_id") == right.get("analysis_id")
        and left.get("figure_key") == right.get("figure_key")
        and _is_integer(left_generation)
        and _is_integer(right_generation)
        and right_generation > left_generation
    )


def _sha256_text(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _core_route_confirmation_valid(route: str, journey: JsonObject) -> bool:
    if (
        route not in _CORE_ROUTES
        and route not in _BINARY_METHOD_WORKFLOW_ROUTES
    ) or not route.startswith("binary."):
        return True
    export_bytes = journey.get("offline_export_bytes")
    return (
        journey.get("stop_acknowledged") is True
        and journey.get("stopped_settings_retained") is True
        and journey.get("reopened_draft_count") == 1
        and _is_integer(export_bytes)
        and export_bytes > 0
    )


def _route_study_order_valid(
    route: str, run: JsonObject, evidence: JsonObject
) -> bool:
    if route in _SEQUENTIAL_ROUTES:
        return run.get("study_order") == evidence.get("study_order")
    if route.endswith("meta-regression"):
        expected = evidence.get("eligible_study_order")
    elif route == "binary.small-study-effects":
        expected = evidence.get("report_study_order")
    else:
        return True
    study_order = run.get("study_order")
    if not _string_list(study_order) or not _string_list(expected):
        return False
    return [name for name in study_order if name in expected] == expected


def _result_figure_export_valid(run: JsonObject, evidence: JsonObject) -> bool:
    if evidence.get("figure_status") != "available":
        return run.get("figure_status") == "not_available"
    export_bytes = run.get("figure_export_bytes")
    return (
        run.get("figure_status") == "exported"
        and _is_integer(export_bytes)
        and export_bytes > 0
    )


def _route_result_evidence_valid(route: str, value: object) -> bool:
    if not _is_json_object(value):
        return False
    if not _available_observation(value):
        return False
    validator = _ROUTE_EVIDENCE_VALIDATORS.get(route)
    return validator(value) if validator is not None else False


def _available_observation(value: JsonObject) -> bool:
    return (
        value.get("status") == "available"
        and value.get("numeric_oracle")
        == "observed_only_no_independent_expected_value"
    )


def _one_arm_evidence_valid(value: JsonObject) -> bool:
    pooled = value.get("pooled_proportion")
    studies = value.get("study_count")
    totals = value.get("raw_arm_totals")
    return (
        value.get("kind") == "one-arm-proportion"
        and value.get("metric") == "PLO"
        and isinstance(value.get("arm_label"), str)
        and _one_arm_summary_valid(pooled, studies, totals, value)
    )


def _one_arm_summary_valid(
    pooled: object, studies: object, totals: object, value: JsonObject
) -> bool:
    return (
        _finite_number(pooled)
        and 0 <= pooled <= 1
        and _is_integer(studies)
        and studies >= 2
        and _is_integer(totals)
        and totals > 0
        and value.get("input_study_count") == studies
        and _has_figure_status(value)
    )


def _continuous_entered_evidence_valid(value: JsonObject) -> bool:
    studies = value.get("study_count")
    return (
        value.get("kind") == "entered-effect-continuous"
        and value.get("input_source") == "entered"
        and value.get("metric") == "SMD"
        and _finite_number(value.get("pooled_estimate"))
        and _is_integer(studies)
        and studies >= 2
        and value.get("input_study_count") == studies
        and _has_figure_status(value)
    )


def _meta_regression_evidence_valid(value: JsonObject) -> bool:
    formula = value.get("formula")
    moderators = value.get("moderators")
    coefficient_count = value.get("coefficient_count")
    eligible_count = value.get("eligible_study_count")
    eligible_order = value.get("eligible_study_order")
    coefficients = _json_objects(value.get("coefficients"))
    if not (
        isinstance(formula, str)
        and isinstance(moderators, list)
        and _is_integer(coefficient_count)
        and _is_integer(eligible_count)
        and _string_list(eligible_order)
        and coefficients is not None
    ):
        return False
    return (
        _meta_regression_header_valid(
            value, formula, moderators, coefficient_count, eligible_count, eligible_order
        )
        and _meta_regression_coefficients_valid(coefficient_count, coefficients)
    )


def _meta_regression_header_valid(
    value: JsonObject,
    formula: object,
    moderators: object,
    coefficient_count: int,
    eligible_count: int,
    eligible_order: list[str],
) -> bool:
    return (
        value.get("kind") == "generic-meta-regression"
        and _formula_and_moderators_valid(formula, moderators)
        and coefficient_count >= 2
        and eligible_count >= 3
        and _eligible_order_valid(eligible_order, eligible_count)
        and _has_figure_status(value)
    )


def _formula_and_moderators_valid(formula: object, moderators: object) -> bool:
    return (
        isinstance(formula, str)
        and bool(formula)
        and isinstance(moderators, list)
        and bool(moderators)
    )


def _eligible_order_valid(order: list[str], count: int) -> bool:
    return len(order) == count and all(order) and len(set(order)) == len(order)


def _meta_regression_coefficients_valid(
    count: int, coefficients: list[JsonObject]
) -> bool:
    return (
        len(coefficients) == count
        and all(_coefficient_valid(row) for row in coefficients)
    )


def _coefficient_valid(coefficient: JsonObject) -> bool:
    label = coefficient.get("label")
    return (
        isinstance(label, str)
        and bool(label)
        and _finite_number(coefficient.get("estimate"))
    )


def _reitsma_meta_regression_evidence_valid(value: JsonObject) -> bool:
    if not _reitsma_meta_regression_header_valid(value):
        return False
    if not _reitsma_meta_regression_settings_valid(value.get("effective_settings")):
        return False
    if not _reitsma_moderator_valid(value.get("moderator")):
        return False
    details = _reitsma_evidence_details(value)
    if details is None:
        return False
    eligible, exclusions, sensitivity, false_positive_rate, overall, tests, unavailable = details
    return (
        _reitsma_evidence_studies_valid(value, exclusions, eligible)
        and _reitsma_evidence_coefficients_valid(sensitivity, false_positive_rate)
        and _reitsma_evidence_tests_valid(overall, tests, unavailable, eligible)
    )


def _reitsma_evidence_studies_valid(
    value: JsonObject, exclusions: list[JsonObject], eligible: list[str]
) -> bool:
    return (
        _reitsma_counts_from_evidence(value, exclusions)
        and _unique_nonempty(eligible)
        and _reitsma_exclusions_valid(exclusions, eligible)
    )


def _reitsma_evidence_coefficients_valid(
    sensitivity: object, false_positive_rate: object
) -> bool:
    return (
        _reitsma_coefficients_valid(sensitivity)
        and _reitsma_coefficients_valid(false_positive_rate)
    )


def _reitsma_evidence_tests_valid(
    overall: object,
    tests: list[JsonObject],
    unavailable: list[JsonObject],
    eligible: list[str],
) -> bool:
    return (
        _reitsma_test_valid(overall, "All moderators", eligible)
        and _reitsma_moderator_tests_valid(tests, eligible)
        and _reitsma_unavailable_outputs_valid(unavailable)
    )


def _reitsma_meta_regression_header_valid(value: JsonObject) -> bool:
    return (
        value.get("kind") == "joint-reitsma-meta-regression"
        and value.get("status") == "available"
        and value.get("report_status") == "available"
        and value.get("numeric_oracle") == "observed_only_no_independent_expected_value"
        and value.get("figure_status") in {"available", "not_available"}
    )


def _reitsma_evidence_details(value: JsonObject):
    eligible = value.get("eligible_study_order")
    exclusions = _json_objects(value.get("exclusions"))
    tests = _json_objects(value.get("moderator_ml_tests"))
    unavailable = _json_objects(value.get("unavailable_outputs"))
    if (
        not _string_list(eligible)
        or exclusions is None
        or tests is None
        or unavailable is None
    ):
        return None
    return (
        eligible,
        exclusions,
        value.get("sensitivity_coefficients"),
        value.get("false_positive_rate_coefficients"),
        value.get("overall_ml_test"),
        tests,
        unavailable,
    )


def _reitsma_counts_from_evidence(
    value: JsonObject, exclusions: list[JsonObject]
) -> bool:
    input_count = value.get("input_study_count")
    eligible_count = value.get("eligible_study_count")
    return (
        _is_integer(input_count)
        and _is_integer(eligible_count)
        and _reitsma_counts_valid(input_count, eligible_count, exclusions)
    )


def _reitsma_meta_regression_settings_valid(value: object) -> bool:
    if not _is_json_object(value):
        return False
    correction = value.get("correction_factor")
    confidence = value.get("confidence_level")
    policy = value.get("correction_policy")
    return _reitsma_setting_identity_valid(value, policy) and _reitsma_setting_ranges_valid(
        correction, confidence
    )


def _reitsma_setting_identity_valid(value: JsonObject, policy: object) -> bool:
    return (
        value.get("missing_moderator_policy") == "exclude"
        and value.get("joint_metrics") == "Sens,Spec"
        and value.get("estimator") in {"REML", "ML"}
        and isinstance(policy, str)
        and bool(policy)
    )


def _reitsma_setting_ranges_valid(correction: object, confidence: object) -> bool:
    return (
        _finite_number(correction)
        and correction >= 0
        and _finite_number(confidence)
        and 0 < confidence < 100
    )


def _reitsma_moderator_valid(value: object) -> bool:
    if not _is_json_object(value):
        return False
    step = value.get("unit_step")
    return (
        value.get("name") == "Qualification index"
        and value.get("kind") == "continuous"
        and value.get("unit") == "study index"
        and _finite_number(step)
        and step > 0
    )


def _reitsma_counts_valid(
    input_count: int, eligible_count: int, exclusions: list[JsonObject]
) -> bool:
    return (
        0 < eligible_count < input_count
        and len(exclusions) == input_count - eligible_count
    )


def _unique_nonempty(values: list[str]) -> bool:
    return bool(values) and all(values) and len(set(values)) == len(values)


def _reitsma_exclusions_valid(
    exclusions: list[JsonObject], eligible_order: list[str]
) -> bool:
    names: list[str] = []
    for exclusion in exclusions:
        name = exclusion.get("study_name")
        reason = exclusion.get("reason")
        if (
            not isinstance(name, str)
            or not name
            or name in eligible_order
            or not isinstance(reason, str)
            or "Qualification index" not in reason
        ):
            return False
        names.append(name)
    return len(set(names)) == len(names)


def _reitsma_coefficients_valid(value: object) -> bool:
    rows = _json_objects(value)
    if rows is None or not rows:
        return False
    return all(_reitsma_coefficient_valid(row) for row in rows)


def _reitsma_coefficient_valid(value: JsonObject) -> bool:
    term = value.get("term")
    estimate = value.get("model_estimate")
    p_value = value.get("p_value")
    return (
        isinstance(term, str)
        and bool(term)
        and _finite_number(estimate)
        and _finite_number(p_value)
        and 0 <= p_value <= 1
    )


def _reitsma_test_valid(
    value: object, label: str, eligible_order: list[str]
) -> bool:
    if not _is_json_object(value):
        return False
    statistic = value.get("statistic")
    degrees = value.get("degrees_of_freedom")
    p_value = value.get("p_value")
    return _reitsma_test_identity_valid(value, label, eligible_order) and (
        _finite_number(statistic)
        and _is_integer(degrees)
        and degrees > 0
        and _finite_number(p_value)
        and 0 <= p_value <= 1
    )


def _reitsma_test_identity_valid(
    value: JsonObject, label: str, eligible_order: list[str]
) -> bool:
    return (
        value.get("label") == label
        and value.get("fit_estimator") == "ML"
        and value.get("included_study_order") == eligible_order
    )


def _reitsma_moderator_tests_valid(
    tests: list[JsonObject] | None, eligible_order: list[str]
) -> bool:
    return (
        tests is not None
        and len(tests) == 1
        and _reitsma_test_valid(tests[0], "Qualification index", eligible_order)
    )


def _reitsma_unavailable_outputs_valid(
    outputs: list[JsonObject] | None,
) -> bool:
    if outputs is None:
        return False
    names: list[str] = []
    for output in outputs:
        name = output.get("name")
        reason = output.get("reason")
        if not isinstance(name, str) or not isinstance(reason, str) or not reason:
            return False
        names.append(name)
    return set(names) == {
        "conditional_summary_operating_point",
        "adjusted_sroc",
        "sroc_auc",
    }


def _reitsma_evidence_valid(value: JsonObject) -> bool:
    statuses = value.get("section_statuses")
    summary = value.get("summary")
    return (
        value.get("kind") == "joint-reitsma"
        and value.get("measures") == ["Sensitivity", "Specificity"]
        and isinstance(summary, str)
        and bool(summary)
        and _is_json_object(statuses)
        and statuses.get("Summary operating point") == "available"
        and statuses.get("SROC") in {"available", "not_available"}
        and _has_figure_status(value)
    )


def _small_study_evidence_valid(value: JsonObject) -> bool:
    usable = value.get("usable_studies")
    method = value.get("primary_test_method")
    statuses = value.get("section_statuses")
    order = value.get("report_study_order")
    return _small_study_summary_valid(value, usable, method, statuses) and (
        _small_study_order_valid(order, usable)
        and isinstance(value.get("report_warnings"), list)
    )


def _small_study_summary_valid(
    value: JsonObject, usable: object, method: object, statuses: object
) -> bool:
    return (
        value.get("kind") == "small-study-effects"
        and value.get("report_status") == "complete"
        and _small_study_eligibility_valid(usable)
        and _small_study_test_valid(value, method, statuses)
        and _has_figure_status(value)
    )


def _small_study_eligibility_valid(usable: object) -> bool:
    return _is_integer(usable) and usable >= 3


def _small_study_test_valid(
    value: JsonObject, method: object, statuses: object
) -> bool:
    return (
        value.get("primary_test_status") == "available"
        and isinstance(method, str)
        and bool(method)
        and _small_study_sections_valid(statuses)
    )


def _small_study_sections_valid(statuses: object) -> bool:
    return _is_json_object(statuses)


def _small_study_order_valid(order: object, usable: object) -> bool:
    return _string_list(order) and len(order) == usable and all(order)


def _subgroup_evidence_valid(route: str, value: JsonObject) -> bool:
    counts = _subgroup_counts(value)
    expected = _ROUTES[route][1]
    if (
        counts is None
        or value.get("family") != expected[0]
        or value.get("metric") != expected[2]
        or not _subgroup_metadata_valid(value, counts)
    ):
        return False
    return _subgroup_groups_valid(value, counts)


def _subgroup_groups_valid(
    value: JsonObject, counts: tuple[int, int, int, int]
) -> bool:
    input_count, included_count, missing_count, excluded_count = counts
    assignments = _json_objects(value.get("assignments"))
    levels = _json_objects(value.get("levels"))
    policy = value.get("missing_policy")
    if assignments is None or levels is None or not isinstance(policy, str):
        return False
    if not _subgroup_counts_match_policy(
        input_count, included_count, missing_count, excluded_count, policy
    ):
        return False
    expected_groups = _subgroup_assignment_groups(assignments, policy, missing_count)
    if expected_groups is None:
        return False
    actual_groups = _subgroup_level_groups(levels)
    return actual_groups is not None and _subgroup_observed_groups_match(
        actual_groups, expected_groups, assignments, included_count
    )


def _subgroup_observed_groups_match(actual, expected, assignments, included_count):
    group_order, summed_count = actual
    assignment_ids = {row["study_name"]: row["study_id"] for row in assignments}
    return (
        [label for label, _names, _ids in group_order] == list(expected)
        and all(
            names == expected[label]
            and ids == [assignment_ids[name] for name in names]
            for label, names, ids in group_order
        )
        and summed_count == included_count
    )


def _subgroup_counts(value: JsonObject) -> tuple[int, int, int, int] | None:
    input_count = value.get("input_study_count")
    included_count = value.get("included_count")
    missing_count = value.get("missing_count")
    excluded_count = value.get("excluded_count")
    if not (
        _is_integer(input_count)
        and _is_integer(included_count)
        and _is_integer(missing_count)
        and _is_integer(excluded_count)
    ):
        return None
    return input_count, included_count, missing_count, excluded_count


def _subgroup_metadata_valid(
    value: JsonObject, counts: tuple[int, int, int, int]
) -> bool:
    input_count, _included, missing_count, _excluded = counts
    assignments = value.get("assignments")
    levels = value.get("levels")
    return (
        value.get("kind") in {
            "binary-subgroup", "continuous-subgroup", "diagnostic-subgroup"
        }
        and value.get("covariate_name") == "Qualification region"
        and value.get("missing_policy") in {"exclude", "missing_category"}
        and value.get("confidence_level") == 90.0
        and _subgroup_shape_valid(input_count, missing_count, assignments, levels)
        and _subgroup_summary_valid(value, counts[1])
    )


def _subgroup_shape_valid(
    input_count: int,
    missing_count: int,
    assignments: object,
    levels: object,
) -> bool:
    return (
        input_count >= 2
        and missing_count >= 1
        and isinstance(assignments, list)
        and len(assignments) == input_count
        and isinstance(levels, list)
        and len(levels) >= 2
    )


def _subgroup_summary_valid(value: JsonObject, included_count: int) -> bool:
    overall = value.get("overall")
    return (
        _is_json_object(overall)
        and overall.get("included_count") == included_count
        and _subgroup_numeric_observation_valid(overall)
        and overall.get("status") == "available"
        and value.get("between_subgroup_test_status") == "not_calculated"
        and _has_figure_status(value)
    )


def _subgroup_counts_match_policy(
    input_count: int,
    included_count: int,
    missing_count: int,
    excluded_count: int,
    policy: str,
) -> bool:
    expected_excluded = missing_count if policy == "exclude" else 0
    return (
        excluded_count == expected_excluded
        and included_count == input_count - excluded_count
    )


def _subgroup_assignment_groups(
    assignments: list[JsonObject], policy: str, missing_count: int
) -> dict[str, list[str]] | None:
    names: set[str] = set()
    groups: dict[str, list[str]] = {}
    missing_names: list[str] = []
    observed_missing = 0
    study_ids: set[int] = set()
    for assignment in assignments:
        if not _record_subgroup_assignment(
            assignment, policy, names, study_ids, groups, missing_names
        ):
            return None
        observed_missing += int(
            assignment.get("value") is None or assignment.get("value") == ""
        )
    if observed_missing != missing_count:
        return None
    if missing_names:
        groups["Missing values"] = missing_names
    return groups


def _record_subgroup_assignment(
    assignment: JsonObject,
    policy: str,
    names: set[str],
    study_ids: set[int],
    groups: dict[str, list[str]],
    missing_names: list[str],
) -> bool:
    parsed = _parse_subgroup_assignment(assignment, policy)
    if parsed is None:
        return False
    name, study_id, value = parsed
    if name in names:
        return False
    if study_id in study_ids:
        return False
    names.add(name)
    study_ids.add(study_id)
    if value is None and policy == "missing_category":
        missing_names.append(name)
    elif value is not None:
        groups.setdefault(value, []).append(name)
    return True


def _parse_subgroup_assignment(
    assignment: JsonObject, policy: str
) -> tuple[str, int, str | None] | None:
    name = assignment.get("study_name")
    study_id = assignment.get("study_id")
    value = assignment.get("value")
    if not isinstance(name, str) or not name:
        return None
    if not _is_exact_integer(study_id) or study_id < 0:
        return None
    if value is not None and not isinstance(value, str):
        return None
    if not _subgroup_assignment_status_valid(assignment, policy, value):
        return None
    return name, study_id, _normalized_assignment_value(value)


def _subgroup_assignment_status_valid(
    assignment: JsonObject, policy: str, value: object
) -> bool:
    is_missing = value is None or value == ""
    expected = "excluded_missing" if is_missing and policy == "exclude" else "included"
    return assignment.get("status") == expected


def _normalized_assignment_value(value: str | None) -> str | None:
    return None if value is None or value == "" else value


def _subgroup_level_groups(
    levels: list[JsonObject],
) -> tuple[list[tuple[str, list[str], list[int]]], int] | None:
    groups: list[tuple[str, list[str], list[int], int]] = []
    total = 0
    for level in levels:
        group = _subgroup_level_group(level)
        if group is None:
            return None
        groups.append(group)
        total += group[3]
    return [(label, order, ids) for label, order, ids, _count in groups], total


def _subgroup_level_group(
    level: JsonObject,
) -> tuple[str, list[str], list[int], int] | None:
    label = level.get("label")
    order = level.get("study_order")
    included_count = level.get("included_count")
    if not isinstance(label, str) or not _string_list(order):
        return None
    study_ids = _subgroup_integer_list(level.get("study_ids"))
    if study_ids is None or not _is_integer(included_count):
        return None
    if not _subgroup_level_shape_valid(level):
        return None
    return label, list(order), list(study_ids), included_count


def _subgroup_integer_list(value: object) -> list[int] | None:
    if not isinstance(value, list):
        return None
    integers: list[int] = []
    for item in value:
        if not _is_exact_integer(item) or item < 0:
            return None
        integers.append(item)
    return integers


def _subgroup_level_shape_valid(level):
    if not isinstance(level.get("label"), str) or not _string_list(level.get("study_order")):
        return False
    order = level["study_order"]
    ids = level.get("study_ids")
    count = level.get("included_count")
    return (
        _subgroup_level_members_valid(order, ids)
        and _subgroup_level_count_valid(level, count, order, ids)
    )


def _subgroup_level_members_valid(order, study_ids):
    return (
        isinstance(study_ids, list)
        and all(_is_exact_integer(value) and value >= 0 for value in study_ids)
        and bool(order)
        and len(set(order)) == len(order)
        and len(set(study_ids)) == len(study_ids)
    )


def _subgroup_level_count_valid(level, count, order, study_ids):
    return (
        _is_integer(count)
        and level.get("status") in {"available", "not_available"}
        and count == len(order)
        and count == len(study_ids)
        and _subgroup_numeric_observation_valid(level)
    )


def _has_figure_status(value: JsonObject) -> bool:
    return value.get("figure_status") in {"available", "not_available"}


def _subgroup_numeric_observation_valid(value: JsonObject) -> bool:
    if value.get("status") == "available":
        return _available_subgroup_estimate_valid(value)
    return _unavailable_subgroup_estimate_valid(value)


def _available_subgroup_estimate_valid(value):
    estimate, lower, upper = (
        value.get(field) for field in ("estimate", "lower_bound", "upper_bound")
    )
    return (
        value.get("reason") is None
        and all(_finite_number(number) for number in (estimate, lower, upper))
        and lower <= estimate <= upper
    )


def _unavailable_subgroup_estimate_valid(value):
    return (
        value.get("status") == "not_available"
        and isinstance(value.get("reason"), str)
        and bool(value.get("reason"))
        and all(value.get(field) is None for field in ("estimate", "lower_bound", "upper_bound"))
    )


def _cumulative_evidence_valid(route: str, value: JsonObject) -> bool:
    parts = _cumulative_evidence_parts(route, value)
    if parts is None:
        return False
    count, input_ids, study_ids, study_order, steps, ordering = parts
    return (
        _cumulative_ordering_valid(ordering, count)
        and _cumulative_identities_valid(
            count, input_ids, study_ids, study_order, steps
        )
        and _cumulative_result_status_valid(value, steps)
    )


def _cumulative_evidence_parts(route, value):
    data_type, workflow, metric, _method = _ROUTES[route][1]
    count = value.get("input_study_count")
    input_ids = value.get("input_study_ids")
    study_ids = value.get("study_ids")
    study_order = value.get("study_order")
    steps = _json_objects(value.get("steps"))
    ordering = value.get("ordering")
    if not (
        _cumulative_evidence_identity_valid(value, data_type, metric)
        and _cumulative_evidence_lists_valid(
            count, input_ids, study_ids, study_order, steps, ordering
        )
    ):
        return None
    return count, input_ids, study_ids, study_order, steps, ordering


def _cumulative_evidence_identity_valid(value, data_type, metric):
    return (
        value.get("kind") == "cumulative-analysis"
        and value.get("data_type") == data_type
        and value.get("metric") == metric
    )


def _cumulative_evidence_lists_valid(count, input_ids, study_ids, study_order, steps, ordering):
    return (
        _is_integer(count)
        and isinstance(input_ids, list)
        and isinstance(study_ids, list)
        and _string_list(study_order)
        and steps is not None
        and _is_json_object(ordering)
    )


def _cumulative_result_status_valid(value, steps):
    statuses = [step.get("status") for step in steps]
    derived = "complete" if all(status == "complete" for status in statuses) else "partial"
    return (
        value.get("result_status") == derived
        and value.get("figure_status") in {"available", "not_available"}
    )


def _cumulative_ordering_valid(ordering: JsonObject, count: int) -> bool:
    return (
        ordering.get("field") == "project_order"
        and ordering.get("direction") == "descending"
        and ordering.get("missing_year_policy") is None
        and ordering.get("tie_policy") == "original_project_order"
        and count >= 2
    )


def _cumulative_identities_valid(count, input_ids, study_ids, study_order, steps):
    return (
        _cumulative_identity_lists_valid(count, input_ids, study_ids, study_order, steps)
        and all(
            _cumulative_step_valid(step, index, count, input_ids, study_ids, study_order)
            for index, step in enumerate(steps)
        )
    )


def _cumulative_identity_lists_valid(count, input_ids, study_ids, study_order, steps):
    return (
        _cumulative_identity_lengths_valid(
            count, input_ids, study_ids, study_order, steps
        )
        and _cumulative_identity_order_valid(input_ids, study_ids, study_order, count)
    )


def _cumulative_identity_lengths_valid(count, input_ids, study_ids, study_order, steps):
    return (
        len(input_ids) == count
        and len(study_ids) == count
        and len(study_order) == count
        and len(steps) == count
    )


def _cumulative_identity_order_valid(input_ids, study_ids, study_order, count):
    return (
        all(_is_exact_integer(study_id) and study_id >= 0 for study_id in input_ids)
        and len(set(input_ids)) == count
        and len(set(study_ids)) == count
        and len(set(study_order)) == count
        and study_ids == list(reversed(input_ids))
    )


def _cumulative_step_valid(step, index, count, input_ids, study_ids, study_order):
    source_order = count - index - 1
    return (
        step.get("order") == index
        and step.get("source_order") == source_order
        and step.get("study_id") == study_ids[index] == input_ids[source_order]
        and step.get("study_name") == study_order[index]
        and isinstance(step.get("study_name"), str)
        and bool(step.get("study_name"))
        and _cumulative_step_result_valid(step, index)
    )


def _cumulative_step_result_valid(step, index):
    numbers = step.get("numbers")
    return (
        _is_json_object(numbers)
        and step.get("included_study_count") == index + 1
        and step.get("status") in {"complete", "partial", "not_estimable", "failed"}
        and _cumulative_numbers_valid(numbers, index + 1)
    )


def _cumulative_numbers_valid(numbers: JsonObject, included_count: int) -> bool:
    fields = (
        "analyzed_study_count", "estimate", "lower_bound", "upper_bound",
        "standard_error", "p_value",
    )
    if not all(_numeric_observation_valid(numbers.get(field)) for field in fields):
        return False
    analyzed = numbers["analyzed_study_count"]
    return (
        _is_json_object(analyzed)
        and _cumulative_observed_count_valid(analyzed, included_count)
    )


def _cumulative_observed_count_valid(analyzed: JsonObject, included_count: int) -> bool:
    if analyzed.get("status") == "available":
        return analyzed.get("value") == included_count
    return analyzed.get("status") == "not_available"


def _numeric_observation_valid(value: object) -> bool:
    if not _is_json_object(value):
        return False
    status = value.get("status")
    number = value.get("value")
    reason = value.get("reason")
    if status == "available":
        return _finite_number(number) and reason is None
    return (
        status in {"not_estimable", "not_available"}
        and number is None
        and isinstance(reason, str)
        and bool(reason)
    )


def _leave_one_out_evidence_valid(route: str, value: JsonObject) -> bool:
    parts = _leave_one_out_evidence_parts(route, value)
    if parts is None:
        return False
    count, study_ids, study_order, rows = parts
    return (
        all(
            _leave_one_out_row_valid(row, index, count, study_ids, study_order)
            for index, row in enumerate(rows)
        )
        and _leave_one_out_result_status_valid(value, rows)
    )


def _leave_one_out_evidence_parts(route, value):
    data_type, _workflow, metric, _method = _ROUTES[route][1]
    count = value.get("input_study_count")
    study_ids = value.get("study_ids")
    study_order = value.get("study_order")
    rows = _json_objects(value.get("rows"))
    if not _leave_one_out_evidence_identity_valid(value, data_type, metric):
        return None
    if not _leave_one_out_evidence_shape_valid(count, study_ids, study_order, rows):
        return None
    return count, study_ids, study_order, rows


def _leave_one_out_evidence_identity_valid(value, data_type, metric):
    return (
        value.get("kind") == "leave-one-out-analysis"
        and value.get("data_type") == data_type
        and value.get("metric") == metric
    )


def _leave_one_out_evidence_shape_valid(count, study_ids, study_order, rows):
    if not _leave_one_out_count_valid(count):
        return False
    if not isinstance(study_ids, list) or not _string_list(study_order) or rows is None:
        return False
    return (
        _leave_one_out_row_lengths_valid(count, study_ids, study_order, rows)
        and _leave_one_out_identity_lists_valid(study_ids, study_order, count)
    )


def _leave_one_out_count_valid(count):
    return _is_integer(count) and count >= 2


def _leave_one_out_row_lengths_valid(count, study_ids, study_order, rows):
    return (
        len(study_ids) == count
        and len(study_order) == count
        and len(rows) == count + 1
    )


def _leave_one_out_identity_lists_valid(study_ids, study_order, count):
    return len(set(study_ids)) == count and len(set(study_order)) == count


def _leave_one_out_result_status_valid(value, rows):
    derived = "complete" if all(row.get("status") == "available" for row in rows) else "partial"
    return (
        value.get("result_status") == derived
        and value.get("row_status_result") == derived
        and value.get("figure_status") in {"available", "not_available"}
    )


def _leave_one_out_row_valid(row, index, count, study_ids, study_order):
    return (
        _leave_one_out_row_identity_valid(row, index, study_ids, study_order)
        and row.get("remaining_study_count") == (count if index == 0 else count - 1)
        and row.get("status") in {"available", "partial", "not_estimable", "failed"}
        and _leave_one_out_row_result_valid(row)
    )


def _leave_one_out_row_identity_valid(row, index, study_ids, study_order):
    if index == 0:
        return row.get("kind") == "baseline" and row.get("label") == "All included studies" and row.get("study_id") is None
    study_index = index - 1
    return (
        row.get("kind") == "omission"
        and row.get("study_id") == study_ids[study_index]
        and row.get("label") == "Omitting %s" % study_order[study_index]
    )


def _leave_one_out_row_result_valid(row):
    numbers = row.get("numbers")
    if not _is_json_object(numbers) or not _leave_one_out_numbers_valid(numbers):
        return False
    status = row.get("status")
    estimate = numbers["estimate"]
    return _leave_one_out_estimate_status_valid(status, estimate)


def _leave_one_out_numbers_valid(numbers):
    return all(
        _numeric_observation_valid(numbers.get(field))
        for field in ("estimate", "lower_bound", "upper_bound", "change_from_baseline")
    )


def _leave_one_out_estimate_status_valid(status, estimate):
    if not _is_json_object(estimate):
        return False
    if status in {"available", "partial"}:
        return estimate.get("status") == "available"
    return estimate.get("status") in {"not_estimable", "not_available"}


def _plot_edit_evidence_valid(value: JsonObject) -> bool:
    count = value.get("study_count")
    return (
        value.get("kind") == "binary-plot-edit"
        and _is_integer(count)
        and count >= 2
        and value.get("input_study_count") == count
        and value.get("figure_status") == "available"
        and isinstance(value.get("figure_key"), str)
        and bool(value.get("figure_key"))
        and value.get("figure_title") == "Forest Plot"
    )


def _method_variant_evidence_valid(route: str, value: JsonObject) -> bool:
    family, workflow, metric, method = _METHOD_VARIANT_ROUTES[route][1]
    identity = tuple(
        value.get(field) for field in ("family", "workflow", "metric", "method")
    )
    return (
        value.get("kind") == "method-variant"
        and identity == (family, workflow, metric, method)
        and _method_variant_summary_valid(value)
    )


def _method_variant_summary_valid(value: JsonObject) -> bool:
    study_count = value.get("study_count")
    input_count = value.get("input_study_count")
    return (
        _method_variant_counts_valid(study_count, input_count)
        and _finite_number(value.get("estimate"))
        and _method_variant_order_valid(value.get("study_order"), input_count)
        and value.get("figure_status") == "available"
    )


def _method_variant_counts_valid(study_count: object, input_count: object) -> bool:
    return (
        _is_integer(study_count)
        and study_count > 0
        and _is_integer(input_count)
        and input_count >= study_count
    )


def _method_variant_order_valid(order: object, input_count: object) -> bool:
    return (
        _string_list(order)
        and isinstance(input_count, int)
        and len(order) == input_count
        and all(order)
    )


def _method_variant_route_evidence_valid(route: str, value: JsonObject) -> bool:
    workflow = _METHOD_VARIANT_ROUTES[route][1][1]
    if workflow == "standard":
        return _method_variant_evidence_valid(route, value)
    if workflow == "subgroup":
        return _subgroup_evidence_valid(route, value)
    if workflow == "cumulative":
        return _cumulative_evidence_valid(route, value)
    return _leave_one_out_evidence_valid(route, value)


_ROUTE_EVIDENCE_VALIDATORS = {
    "binary.one-arm": _one_arm_evidence_valid,
    "continuous.entered-effect": _continuous_entered_evidence_valid,
    "binary.meta-regression": _meta_regression_evidence_valid,
    "continuous.meta-regression": _meta_regression_evidence_valid,
    "diagnostic.reitsma-meta-regression": _reitsma_meta_regression_evidence_valid,
    "diagnostic.reitsma": _reitsma_evidence_valid,
    "binary.small-study-effects": _small_study_evidence_valid,
    "binary.plot-edit": _plot_edit_evidence_valid,
    "binary.subgroup": lambda value: _subgroup_evidence_valid("binary.subgroup", value),
    "continuous.subgroup": lambda value: _subgroup_evidence_valid("continuous.subgroup", value),
    "diagnostic.subgroup": lambda value: _subgroup_evidence_valid("diagnostic.subgroup", value),
    "continuous.cumulative": lambda value: _cumulative_evidence_valid("continuous.cumulative", value),
    "diagnostic.cumulative": lambda value: _cumulative_evidence_valid("diagnostic.cumulative", value),
    "continuous.leave-one-out": lambda value: _leave_one_out_evidence_valid("continuous.leave-one-out", value),
    "diagnostic.leave-one-out": lambda value: _leave_one_out_evidence_valid("diagnostic.leave-one-out", value),
}
_ROUTE_EVIDENCE_VALIDATORS.update(
    {
        route: (
            lambda value, route=route:
            _method_variant_route_evidence_valid(route, value)
        )
        for route in _METHOD_VARIANT_ROUTES
    }
)


def _is_json_object(value: object) -> TypeGuard[JsonObject]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _json_objects(value: object) -> list[JsonObject] | None:
    if not isinstance(value, list):
        return None
    objects: list[JsonObject] = []
    for item in value:
        if not _is_json_object(item):
            return None
        objects.append(item)
    return objects


def _string_list(value: object) -> TypeGuard[list[str]]:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_integer(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_exact_integer(value: object) -> TypeGuard[int]:
    return type(value) is int


def _finite_number(value: object) -> TypeGuard[int | float]:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--route-timeout", type=int, default=120)
    route_selection = parser.add_mutually_exclusive_group()
    route_selection.add_argument(
        "--route",
        action="append",
        choices=tuple(_ROUTES),
        help=(
            "qualify only this registered route (repeatable); without this option, "
            "run the bounded core worker gate"
        ),
    )
    route_selection.add_argument(
        "--all-routes",
        action="store_true",
        help="qualify every registered worker route",
    )
    route_selection.add_argument(
        "--all-additional-routes",
        action="store_true",
        help="qualify every registered route except the five-route core gate",
    )
    parser.add_argument("--r-home", type=Path)
    parser.add_argument("--r-libs", type=Path)
    arguments = parser.parse_args()
    if arguments.all_routes:
        selected_routes = tuple(_ROUTES)
    elif arguments.all_additional_routes:
        selected_routes = tuple(
            route for route in _ROUTES if route not in _CORE_ROUTES
        )
    elif arguments.route:
        selected_routes = tuple(arguments.route)
    else:
        selected_routes = None
    result = qualify(
        arguments.executable,
        arguments.sample,
        arguments.destination,
        arguments.output,
        artifact=arguments.artifact,
        r_home=arguments.r_home,
        r_libs=arguments.r_libs,
        route_timeout=arguments.route_timeout,
        routes=selected_routes,
    )
    return 0 if result["passed"] else 1


def _host_identity() -> dict[str, object]:
    system = platform.system()
    identity: dict[str, object] = {
        "system": system,
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
    }
    if system == "Linux":
        try:
            identity["os_release"] = platform.freedesktop_os_release()
        except OSError:
            identity["os_release"] = None
    elif system == "Darwin":
        identity["macos_version"] = platform.mac_ver()[0]
    return identity


def _analysis_runs_valid(
    value: object,
    routes: tuple[str, ...] | None = None,
) -> bool:
    selected_routes = _CORE_ROUTES if routes is None else routes
    required = _required_analysis_identities(selected_routes)
    partial_identities = {
        _ROUTES[route][1] for route in selected_routes if route in _SEQUENTIAL_ROUTES
    }
    runs = _json_objects(value)
    if runs is None or len(runs) != len(required):
        return False
    return _analysis_runs_match(runs, required, partial_identities)


def _required_analysis_identities(
    routes: tuple[str, ...] | None,
) -> list[tuple[str, ...]]:
    selected_routes = _CORE_ROUTES if routes is None else routes
    required: list[tuple[str, ...]] = []
    for route in selected_routes:
        identity = _ROUTES[route][1]
        required.append(identity)
        if route in _SUBGROUP_ROUTES:
            required.append(identity)
    return required


def _analysis_runs_match(
    runs: list[JsonObject],
    required: list[tuple[str, ...]],
    partial_identities: set[tuple[str, ...]],
) -> bool:
    actual: list[tuple[object, object, object, object]] = []
    for run in runs:
        identity = (
            run.get("data_type"),
            run.get("workflow"),
            run.get("metric"),
            run.get("method"),
        )
        if not _analysis_run_valid(run, allow_partial=identity in partial_identities):
            return False
        if identity not in required:
            return False
        actual.append(identity)
    return sorted(actual) == sorted(required)


def _analysis_run_valid(run: object, *, allow_partial: bool = False) -> bool:
    if not _is_json_object(run):
        return False
    studies = run.get("study_order")
    return (
        run.get("status") in ({"complete", "partial"} if allow_partial else {"complete"})
        and run.get("saved_reopened") is True
        and _analysis_run_hashes_valid(run)
        and _analysis_studies_valid(studies)
        and isinstance(run.get("warnings"), list)
    )


def _analysis_run_hashes_valid(run: JsonObject) -> bool:
    return _is_sha256(run.get("input_identity")) and _is_sha256(
        run.get("result_text_sha256")
    )


def _analysis_studies_valid(studies: object) -> bool:
    return _string_list(studies) and bool(studies) and all(studies)


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


if __name__ == "__main__":
    raise SystemExit(main())
