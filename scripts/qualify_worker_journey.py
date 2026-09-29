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
    "diagnostic.reitsma": (
        "lymph.rcms",
        ("diagnostic", "standard", "Sensitivity and specificity", "diagnostic.reitsma"),
    ),
    "binary.small-study-effects": (
        "amino.rcms",
        ("binary", "small-study-effects", "OR", "small.study.effects"),
    ),
    "diagnostic.subgroup": (
        "lymph.rcms",
        ("diagnostic", "subgroup", "Sens", "diagnostic.random"),
    ),
}


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
    executable = executable.expanduser().resolve()
    sample = sample.expanduser().resolve()
    destination = destination.expanduser().resolve()
    output = output.expanduser().resolve()
    artifact = artifact.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
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
        "analysis_runs": [],
        "routes": [],
    }
    analysis_runs: list[object] = []
    route_results: list[JsonObject] = []
    result["analysis_runs"] = analysis_runs
    result["routes"] = route_results
    _write_result(output, result)
    sample_root = sample.parent
    for route in selected_routes:
        sample_name, _expected = _ROUTES[route]
        route_sample = sample_root / sample_name
        slug = route.replace(".", "-")
        observation_path = output.with_name(
            "%s.%s.observation.json" % (output.stem, slug)
        )
        route_destination = destination.with_name(
            "%s-%s%s" % (destination.stem, slug, destination.suffix)
        )
        route_result: dict[str, object] = {
            "route": route,
            "status": "running",
            "timeout_seconds": route_timeout,
            "sample_project": str(route_sample),
        }
        route_results.append(route_result)
        _write_result(output, result)
        if not route_sample.is_file():
            route_result.update(
                status="unavailable",
                details="packaged sample project is missing",
            )
            _write_result(output, result)
            continue
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
            completed = _run_package(command, timeout=route_timeout, environment=environment)
        except subprocess.TimeoutExpired as error:
            route_result.update(
                status="timed_out",
                elapsed_seconds=route_timeout,
                worker_pid=getattr(error, "worker_pid", None),
                worker_returncode=getattr(error, "worker_returncode", None),
                worker_process_state=getattr(error, "worker_process_state", "unknown"),
                stdout=_output_text(error.stdout),
                stderr=_output_text(error.stderr),
            )
            _write_result(output, result)
            continue
        except subprocess.CalledProcessError as error:
            route_result.update(
                status="failed",
                elapsed_seconds=round(time.monotonic() - started, 2),
                return_code=error.returncode,
                stdout=_output_text(error.stdout),
                stderr=_output_text(error.stderr),
            )
            _write_result(output, result)
            continue

        elapsed = round(time.monotonic() - started, 2)
        route_result["elapsed_seconds"] = elapsed
        route_result["sample_project_sha256"] = _sha256_file(route_sample)
        route_result["stdout"] = _tail(completed.stdout)
        route_result["stderr"] = _tail(completed.stderr)
        try:
            journey: object = json.loads(
                observation_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as error:
            route_result.update(
                status="failed",
                details="worker process did not write valid evidence: %s" % error,
            )
            _write_result(output, result)
            continue
        if not _is_json_object(journey):
            route_result.update(
                status="failed",
                details="packaged worker evidence must be a JSON object",
            )
            _write_result(output, result)
            continue
        route_result["observation"] = journey
        qualification_status = journey.get("qualification_status", "complete")
        if qualification_status in {"unsupported", "unqualified"}:
            route_result.update(
                status=qualification_status,
                details=journey.get("details", "route did not meet its qualification contract"),
            )
            _write_result(output, result)
            continue
        if not _route_observation_valid(route, journey):
            route_result.update(
                status="failed",
                details="packaged route did not meet its evidence contract",
            )
            _write_result(output, result)
            continue
        route_result["status"] = "complete"
        route_runs = _json_objects(journey.get("analysis_runs"))
        if route_runs is None:
            route_result.update(
                status="failed",
                details="packaged worker evidence has invalid analysis runs",
            )
            _write_result(output, result)
            continue
        analysis_runs.extend(route_runs)
        _write_result(output, result)

    result["passed"] = (
        all(route["status"] == "complete" for route in route_results)
        and _analysis_runs_valid(analysis_runs, selected_routes)
    )
    _write_result(output, result)
    return result


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
        _terminate_process_tree(process)
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired as cleanup_error:
            if process.poll() is None:
                process.kill()
            for pipe in (process.stdout, process.stderr):
                if pipe is not None:
                    pipe.close()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            stdout = error.output or cleanup_error.output
            stderr = error.stderr or cleanup_error.stderr
        timeout_error = _WorkerTimeoutExpired(
            command,
            timeout,
            output=stdout or error.output,
            stderr=stderr or error.stderr,
            worker_pid=process.pid,
            worker_returncode=process.poll(),
        )
        raise timeout_error from error
    if process.returncode:
        raise subprocess.CalledProcessError(
            process.returncode, command, output=stdout, stderr=stderr
        )
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


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
    route_spec = _ROUTES.get(route)
    expected = route_spec[1] if route_spec else None
    if expected is None or not _is_json_object(journey):
        return False
    runs = journey.get("analysis_runs")
    required_run_count = 2 if route == "diagnostic.subgroup" else 1
    if (
        journey.get("route") != route
        or journey.get("worker_completed") is not True
        or journey.get("main_process_r_bridge_absent") is not True
        or journey.get("event_loop_responsive") is not True
        or not isinstance(runs, list)
        or len(runs) != required_run_count
    ):
        return False
    valid_runs: list[JsonObject] = []
    for run in runs:
        if not _is_json_object(run) or not _analysis_run_valid(run):
            return False
        valid_runs.append(run)
    if any(
        (run["data_type"], run["workflow"], run["metric"], run["method"]) != expected
        for run in valid_runs
    ):
        return False
    reopened_count = journey.get("reopened_analysis_count")
    if (
        journey.get("saved_analysis_status") != "complete"
        or not _is_integer(reopened_count)
        or reopened_count < required_run_count
    ):
        return False
    if route == "diagnostic.subgroup":
        if (
            journey.get("saved_edit_copy_opened") is not True
            or journey.get("live_project_confidence_level") != 95.0
            or journey.get("saved_edit_copy_confidence_level") != 90.0
            or journey.get("saved_edit_copy_missing_policy") != "exclude"
        ):
            return False
        policies: set[str] = set()
        study_orders: list[tuple[str, ...]] = []
        for run in valid_runs:
            result_evidence = run.get("result_evidence")
            if not _is_json_object(result_evidence) or not _route_result_evidence_valid(
                route, result_evidence
            ):
                return False
            policy = result_evidence.get("missing_policy")
            if not isinstance(policy, str):
                return False
            policies.add(policy)
            study_order = run.get("study_order")
            assignments = _json_objects(result_evidence.get("assignments"))
            if (
                not _string_list(study_order)
                or assignments is None
                or result_evidence.get("input_study_count") != len(study_order)
                or [row.get("study_name") for row in assignments] != study_order
            ):
                return False
            study_orders.append(tuple(study_order))
            figure_bytes = run.get("figure_export_bytes")
            if result_evidence["figure_status"] == "available":
                if (
                    run.get("figure_status") != "exported"
                    or not _is_integer(figure_bytes)
                    or figure_bytes <= 0
                ):
                    return False
            elif run.get("figure_status") != "not_available":
                return False
        return policies == {"exclude", "missing_category"} and len(set(study_orders)) == 1

    run = valid_runs[0]
    if route in _CORE_ROUTES and route.startswith("binary."):
        export_bytes = journey.get("offline_export_bytes")
        extra = (
            journey.get("stop_acknowledged") is True
            and journey.get("stopped_settings_retained") is True
            and journey.get("reopened_draft_count") == 1
            and _is_integer(export_bytes)
            and export_bytes > 0
        )
    else:
        extra = True
    if not extra:
        return False
    if route not in _CORE_ROUTES:
        result_evidence = run.get("result_evidence")
        if not _route_result_evidence_valid(route, result_evidence):
            return False
        if not _is_json_object(result_evidence):
            return False
        study_order = run.get("study_order")
        if route.endswith("meta-regression"):
            eligible_order = result_evidence.get("eligible_study_order")
            if not _string_list(study_order) or not _string_list(eligible_order):
                return False
            if [name for name in study_order if name in eligible_order] != eligible_order:
                return False
        elif route == "binary.small-study-effects":
            report_order = result_evidence.get("report_study_order")
            if not _string_list(study_order) or not _string_list(report_order):
                return False
            if [name for name in study_order if name in report_order] != report_order:
                return False
        if result_evidence["figure_status"] == "available":
            figure_bytes = run.get("figure_export_bytes")
            return (
                run.get("figure_status") == "exported"
                and _is_integer(figure_bytes)
                and figure_bytes > 0
            )
        return run.get("figure_status") == "not_available"
    return True


def _route_result_evidence_valid(route: str, value: object) -> bool:
    if not _is_json_object(value):
        return False
    if (
        value.get("status") != "available"
        or value.get("numeric_oracle")
        != "observed_only_no_independent_expected_value"
    ):
        return False
    if route == "binary.one-arm":
        pooled = value.get("pooled_proportion")
        study_count = value.get("study_count")
        raw_arm_totals = value.get("raw_arm_totals")
        return (
            value.get("kind") == "one-arm-proportion"
            and value.get("metric") == "PLO"
            and isinstance(value.get("arm_label"), str)
            and _finite_number(pooled)
            and 0 <= pooled <= 1
            and _is_integer(study_count)
            and study_count >= 2
            and _is_integer(raw_arm_totals)
            and raw_arm_totals > 0
            and value.get("input_study_count") == study_count
            and value.get("figure_status") in {"available", "not_available"}
        )
    if route == "continuous.entered-effect":
        study_count = value.get("study_count")
        return (
            value.get("kind") == "entered-effect-continuous"
            and value.get("input_source") == "entered"
            and value.get("metric") == "SMD"
            and _finite_number(value.get("pooled_estimate"))
            and _is_integer(study_count)
            and study_count >= 2
            and value.get("input_study_count") == study_count
            and value.get("figure_status") in {"available", "not_available"}
        )
    if route.endswith("meta-regression"):
        formula = value.get("formula")
        moderators = value.get("moderators")
        coefficient_count = value.get("coefficient_count")
        eligible_study_count = value.get("eligible_study_count")
        eligible_study_order = value.get("eligible_study_order")
        coefficients = _json_objects(value.get("coefficients"))
        if (
            not isinstance(formula, str)
            or not isinstance(moderators, list)
            or not _is_integer(coefficient_count)
            or not _is_integer(eligible_study_count)
            or not _string_list(eligible_study_order)
            or coefficients is None
        ):
            return False
        return (
            value.get("kind") == "generic-meta-regression"
            and bool(formula)
            and bool(moderators)
            and coefficient_count >= 2
            and eligible_study_count >= 3
            and len(eligible_study_order) == eligible_study_count
            and all(eligible_study_order)
            and len(set(eligible_study_order)) == len(eligible_study_order)
            and value.get("figure_status") in {"available", "not_available"}
            and len(coefficients) == coefficient_count
            and all(
                isinstance(coefficient.get("label"), str)
                and bool(coefficient.get("label"))
                and _finite_number(coefficient.get("estimate"))
                for coefficient in coefficients
            )
        )
    if route == "diagnostic.reitsma":
        section_statuses = value.get("section_statuses")
        if not _is_json_object(section_statuses):
            return False
        summary = value.get("summary")
        return (
            value.get("kind") == "joint-reitsma"
            and value.get("measures") == ["Sensitivity", "Specificity"]
            and isinstance(summary, str)
            and bool(summary)
            and section_statuses.get("Summary operating point") == "available"
            and section_statuses.get("SROC") in {"available", "not_available"}
            and value.get("figure_status") in {"available", "not_available"}
        )
    if route == "binary.small-study-effects":
        usable_studies = value.get("usable_studies")
        primary_test_method = value.get("primary_test_method")
        section_statuses = value.get("section_statuses")
        report_study_order = value.get("report_study_order")
        return (
            value.get("kind") == "small-study-effects"
            and value.get("report_status") == "complete"
            and _is_integer(usable_studies)
            and usable_studies >= 3
            and value.get("primary_test_status") == "available"
            and isinstance(primary_test_method, str)
            and bool(primary_test_method)
            and _is_json_object(section_statuses)
            and _string_list(report_study_order)
            and len(report_study_order) == usable_studies
            and all(report_study_order)
            and isinstance(value.get("report_warnings"), list)
            and value.get("figure_status") in {"available", "not_available"}
        )
    if route == "diagnostic.subgroup":
        input_count = value.get("input_study_count")
        included_count = value.get("included_count")
        missing_count = value.get("missing_count")
        excluded_count = value.get("excluded_count")
        policy = value.get("missing_policy")
        assignments = _json_objects(value.get("assignments"))
        levels = _json_objects(value.get("levels"))
        total_included_count = included_count
        if (
            value.get("kind") != "diagnostic-subgroup"
            or value.get("covariate_name") != "Qualification region"
            or policy not in {"exclude", "missing_category"}
            or value.get("confidence_level") != 90.0
            or not _is_integer(input_count)
            or not _is_integer(included_count)
            or not _is_integer(missing_count)
            or not _is_integer(excluded_count)
            or min(input_count, included_count, missing_count, excluded_count) < 0
            or input_count < 2
            or missing_count < 1
            or assignments is None
            or len(assignments) != input_count
            or levels is None
            or len(levels) < 2
            or value.get("overall") != {
                "included_count": included_count,
                "status": "available",
            }
            or value.get("between_subgroup_test_status") != "not_calculated"
            or value.get("figure_status") not in {"available", "not_available"}
        ):
            return False
        if (
            excluded_count != (missing_count if policy == "exclude" else 0)
            or included_count != input_count - excluded_count
        ):
            return False
        names: list[str] = []
        expected_groups: dict[str, list[str]] = {}
        missing_category_names: list[str] = []
        observed_missing = 0
        for assignment in assignments:
            study_name = assignment.get("study_name")
            study_id = assignment.get("study_id")
            assigned_value = assignment.get("value")
            if (
                not isinstance(study_name, str)
                or not study_name
                or not _is_exact_integer(study_id)
                or study_id < 0
                or assigned_value is not None
                and not isinstance(assigned_value, str)
            ):
                return False
            name = study_name
            if name in names:
                return False
            names.append(name)
            is_missing = assigned_value is None or assigned_value == ""
            observed_missing += int(is_missing)
            expected_status = (
                "excluded_missing"
                if is_missing and policy == "exclude"
                else "included"
            )
            if assignment.get("status") != expected_status:
                return False
            if expected_status == "included":
                if is_missing:
                    missing_category_names.append(name)
                elif isinstance(assigned_value, str):
                    expected_groups.setdefault(assigned_value, []).append(name)
                else:
                    return False
        if observed_missing != missing_count:
            return False
        if missing_category_names:
            expected_groups["Missing values"] = missing_category_names
        actual_groups: list[tuple[str, list[object]]] = []
        summed_level_count = 0
        for level in levels:
            label = level.get("label")
            study_order = level.get("study_order")
            level_count = level.get("included_count")
            if (
                not isinstance(label, str)
                or not isinstance(study_order, list)
                or not _is_integer(level_count)
                or level.get("status") != "available"
                or level_count != len(study_order)
                or not study_order
            ):
                return False
            actual_groups.append((label, list(study_order)))
            summed_level_count += level_count
        if (
            actual_groups != list(expected_groups.items())
            or summed_level_count != total_included_count
        ):
            return False
        return True
    return False


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
    parser.add_argument(
        "--route",
        action="append",
        choices=tuple(_ROUTES),
        help=(
            "qualify only this registered route (repeatable); without this option, "
            "run the bounded core worker gate"
        ),
    )
    parser.add_argument("--r-home", type=Path)
    parser.add_argument("--r-libs", type=Path)
    arguments = parser.parse_args()
    result = qualify(
        arguments.executable,
        arguments.sample,
        arguments.destination,
        arguments.output,
        artifact=arguments.artifact,
        r_home=arguments.r_home,
        r_libs=arguments.r_libs,
        route_timeout=arguments.route_timeout,
        routes=tuple(arguments.route) if arguments.route else None,
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
    required = [
        identity
        for route in selected_routes
        for identity in (
            [_ROUTES[route][1], _ROUTES[route][1]]
            if route == "diagnostic.subgroup"
            else [_ROUTES[route][1]]
        )
    ]
    runs = _json_objects(value)
    if runs is None or len(runs) != len(required):
        return False
    actual: list[tuple[object, object, object, object]] = []
    for run in runs:
        if not _analysis_run_valid(run):
            return False
        identity = (
            run.get("data_type"),
            run.get("workflow"),
            run.get("metric"),
            run.get("method"),
        )
        if identity not in required:
            return False
        actual.append(identity)
    return sorted(actual) == sorted(required)


def _analysis_run_valid(run: object) -> bool:
    if not _is_json_object(run):
        return False
    studies = run.get("study_order")
    return (
        run.get("status") == "complete"
        and run.get("saved_reopened") is True
        and _is_sha256(run.get("input_identity"))
        and _is_sha256(run.get("result_text_sha256"))
        and _string_list(studies)
        and bool(studies)
        and all(studies)
        and isinstance(run.get("warnings"), list)
    )


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


if __name__ == "__main__":
    raise SystemExit(main())
