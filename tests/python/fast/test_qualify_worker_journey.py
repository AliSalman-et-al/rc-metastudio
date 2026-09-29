# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import qualify_worker_journey


_RUNS = {
    "binary.standard": ("binary", "standard", "OR", "binary.random"),
    "binary.cumulative": ("binary", "cumulative", "OR", "binary.random"),
    "binary.leave-one-out": (
        "binary",
        "leave-one-out",
        "OR",
        "binary.random",
    ),
    "continuous.standard": ("continuous", "standard", "SMD", "continuous.random"),
    "diagnostic.standard": ("diagnostic", "standard", "Sens", "diagnostic.random"),
}


def _observation(route):
    data_type, workflow, metric, method = _RUNS[route]
    value = {
        "route": route,
        "worker_completed": True,
        "event_loop_responsive": True,
        "saved_analysis_status": "complete",
        "reopened_analysis_count": 1,
        "main_process_r_bridge_absent": True,
        "analysis_runs": [
            {
                "data_type": data_type,
                "workflow": workflow,
                "metric": metric,
                "method": method,
                "status": "complete",
                "saved_reopened": True,
                "input_identity": "a" * 64,
                "result_text_sha256": "b" * 64,
                "study_order": ["Study 1", "Study 2"],
                "warnings": [],
            }
        ],
    }
    if route.startswith("binary."):
        value.update(
            stop_acknowledged=True,
            stopped_settings_retained=True,
            reopened_draft_count=1,
            offline_export_bytes=1024,
        )
    return value


def _inputs(tmp_path):
    artifact = tmp_path / "package.tar.gz"
    artifact.write_bytes(b"package")
    sample_root = tmp_path / "sample_projects"
    sample_root.mkdir()
    sample = sample_root / "amino.rcms"
    sample.write_bytes(b"binary sample")
    for name in ("continuous.rcms", "lymph.rcms"):
        (sample_root / name).write_bytes(name.encode())
    return artifact, sample


def test_qualifier_runs_each_route_in_a_fresh_bounded_process(tmp_path, monkeypatch):
    artifact, sample = _inputs(tmp_path)
    calls = []

    def run(command, *, timeout, environment):
        calls.append((command, timeout, environment))
        Path(command[2]).write_text(json.dumps(_observation(command[5])), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="route stdout", stderr="route stderr")

    monkeypatch.setattr(qualify_worker_journey, "_run_package", run)
    output = tmp_path / "qualification" / "worker.json"
    destination = tmp_path / "qualification" / "saved.rcms"
    result = qualify_worker_journey.qualify(
        tmp_path / "launcher",
        sample,
        destination,
        output,
        artifact=artifact,
        r_home=tmp_path / "R",
        r_libs=tmp_path / "R" / "library",
        route_timeout=90,
    )

    assert [call[0][5] for call in calls] == list(_RUNS)
    assert all(call[1] == 90 for call in calls)
    assert all(call[0][1] == "--automation-package-worker-journey" for call in calls)
    assert all(call[2]["RCMS_R_HOME"] == str(tmp_path / "R") for call in calls)
    assert all("R_HOME" not in call[2] for call in calls)
    assert result["passed"] is True
    assert result["gate"] == "bounded-core-worker"
    assert result["requested_routes"] == list(_RUNS)
    assert result["package_sha256"] == qualify_worker_journey._sha256_file(artifact)
    assert result["sample_project_sha256"] == qualify_worker_journey._sha256_file(sample)
    assert [route["status"] for route in result["routes"]] == ["complete"] * 5
    assert len(result["analysis_runs"]) == 5
    assert result["host"]["system"] == qualify_worker_journey.platform.system()
    assert json.loads(output.read_text(encoding="utf-8")) == result


def test_qualifier_records_timeout_and_continues_later_routes(tmp_path, monkeypatch):
    artifact, sample = _inputs(tmp_path)
    calls = []

    def run(command, *, timeout, environment):
        calls.append(command[5])
        if command[5] == "binary.cumulative":
            error = qualify_worker_journey.subprocess.TimeoutExpired(
                command, timeout, output=b"worker progress", stderr=b"last stderr"
            )
            error.worker_pid = 456
            error.worker_returncode = None
            error.worker_process_state = "cleanup_unconfirmed"
            raise error
        Path(command[2]).write_text(json.dumps(_observation(command[5])), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(qualify_worker_journey, "_run_package", run)
    output = tmp_path / "worker.json"
    result = qualify_worker_journey.qualify(
        tmp_path / "launcher",
        sample,
        tmp_path / "saved.rcms",
        output,
        artifact=artifact,
        route_timeout=30,
    )

    assert calls == list(_RUNS)
    assert result["passed"] is False
    assert [route["status"] for route in result["routes"]] == [
        "complete",
        "timed_out",
        "complete",
        "complete",
        "complete",
    ]
    timed_out = result["routes"][1]
    assert timed_out["elapsed_seconds"] == 30
    assert timed_out["stdout"] == "worker progress"
    assert timed_out["stderr"] == "last stderr"
    assert timed_out["worker_pid"] == 456
    assert timed_out["worker_process_state"] == "cleanup_unconfirmed"
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is False


def test_qualifier_marks_missing_sample_unavailable_and_continues(tmp_path, monkeypatch):
    artifact, sample = _inputs(tmp_path)
    (sample.parent / "continuous.rcms").unlink()
    calls = []

    def run(command, *, timeout, environment):
        calls.append(command[5])
        Path(command[2]).write_text(json.dumps(_observation(command[5])), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(qualify_worker_journey, "_run_package", run)
    result = qualify_worker_journey.qualify(
        tmp_path / "launcher",
        sample,
        tmp_path / "saved.rcms",
        tmp_path / "worker.json",
        artifact=artifact,
    )

    assert calls == [route for route in _RUNS if route != "continuous.standard"]
    assert result["passed"] is False
    assert result["routes"][3]["route"] == "continuous.standard"
    assert result["routes"][3]["status"] == "unavailable"
    assert "missing" in result["routes"][3]["details"]


def test_qualifier_selected_route_is_not_reported_as_core_gate(tmp_path, monkeypatch):
    artifact, sample = _inputs(tmp_path)

    def run(command, *, timeout, environment):
        Path(command[2]).write_text(json.dumps(_observation(command[5])), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(qualify_worker_journey, "_run_package", run)
    result = qualify_worker_journey.qualify(
        tmp_path / "launcher",
        sample,
        tmp_path / "saved.rcms",
        tmp_path / "worker.json",
        artifact=artifact,
        routes=("diagnostic.standard",),
    )

    assert result["passed"] is True
    assert result["gate"] == "selected-routes"
    assert result["requested_routes"] == ["diagnostic.standard"]
    assert len(result["analysis_runs"]) == 1


def test_route_evidence_must_match_requested_route():
    observation = _observation("binary.standard")

    assert qualify_worker_journey._route_observation_valid("binary.standard", observation)
    observation["route"] = "binary.leave-one-out"
    assert not qualify_worker_journey._route_observation_valid("binary.standard", observation)


def test_package_timeout_bounds_cleanup_when_a_child_holds_output_pipes(monkeypatch):
    class Pipe:
        closed = False

        def close(self):
            self.closed = True

    class HangingProcess:
        pid = 123
        returncode = None

        def __init__(self):
            self.stdout = Pipe()
            self.stderr = Pipe()
            self.communication_timeouts = []
            self.wait_timeout = None
            self.killed = False

        def communicate(self, timeout):
            self.communication_timeouts.append(timeout)
            raise qualify_worker_journey.subprocess.TimeoutExpired(
                ["app"], timeout, output=b"partial", stderr=b"pending"
            )

        def poll(self):
            return None

        def kill(self):
            self.killed = True

        def wait(self, timeout):
            self.wait_timeout = timeout
            raise qualify_worker_journey.subprocess.TimeoutExpired(["app"], timeout)

    process = HangingProcess()
    monkeypatch.setattr(
        qualify_worker_journey.subprocess, "Popen", lambda *args, **kwargs: process
    )
    monkeypatch.setattr(
        qualify_worker_journey, "_terminate_process_tree", lambda _process: None
    )

    with pytest.raises(qualify_worker_journey.subprocess.TimeoutExpired) as caught:
        qualify_worker_journey._run_package(["app"], timeout=1, environment={})

    assert process.communication_timeouts == [1, 10]
    assert process.wait_timeout == 2
    assert process.killed is True
    assert process.stdout.closed is True
    assert process.stderr.closed is True
    assert caught.value.worker_pid == 123
    assert caught.value.worker_returncode is None
    assert caught.value.worker_process_state == "cleanup_unconfirmed"


def test_qualifier_requires_positive_timeout(tmp_path):
    artifact, sample = _inputs(tmp_path)
    (sample.parent / "continuous.rcms").unlink()

    with pytest.raises(ValueError, match="positive"):
        qualify_worker_journey.qualify(
            tmp_path / "launcher",
            sample,
            tmp_path / "saved.rcms",
            tmp_path / "worker.json",
            artifact=artifact,
            route_timeout=0,
        )


def test_qualifier_records_linux_distribution_for_platform_identity(monkeypatch):
    monkeypatch.setattr(qualify_worker_journey.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        qualify_worker_journey.platform, "release", lambda: "6.8.0"
    )
    monkeypatch.setattr(
        qualify_worker_journey.platform, "version", lambda: "#1 SMP"
    )
    monkeypatch.setattr(
        qualify_worker_journey.platform, "machine", lambda: "x86_64"
    )
    monkeypatch.setattr(
        qualify_worker_journey.platform,
        "freedesktop_os_release",
        lambda: {"ID": "ubuntu", "VERSION_ID": "26.04"},
    )

    identity = qualify_worker_journey._host_identity()

    assert identity["os_release"] == {"ID": "ubuntu", "VERSION_ID": "26.04"}
