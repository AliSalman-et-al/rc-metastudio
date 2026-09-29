# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import qualify_worker_journey


def test_qualifier_requires_the_packaged_worker_journey(tmp_path, monkeypatch):
    observed = {
        "worker_completed": True,
        "event_loop_responsive": True,
        "stop_acknowledged": True,
        "stopped_settings_retained": True,
        "saved_analysis_status": "complete",
        "reopened_analysis_count": 1,
        "reopened_draft_count": 1,
        "offline_export_bytes": 1024,
    }
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        Path(command[2]).write_text(json.dumps(observed), encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(qualify_worker_journey.subprocess, "run", run)
    artifact = tmp_path / "package.tar.gz"
    artifact.write_bytes(b"package")
    output = tmp_path / "qualification" / "worker.json"
    destination = tmp_path / "qualification" / "saved.rcms"
    result = qualify_worker_journey.qualify(
        tmp_path / "launcher", tmp_path / "amino.rcms", destination, output,
        artifact=artifact,
        r_home=tmp_path / "R", r_libs=tmp_path / "R" / "library",
    )

    assert calls[0][0][1] == "--automation-package-worker-journey"
    assert "R_HOME" not in calls[0][1]["env"]
    assert calls[0][1]["env"]["RCMS_R_HOME"] == str(tmp_path / "R")
    assert result["passed"] is True
    assert result["package_sha256"] == qualify_worker_journey._sha256_file(artifact)
    assert json.loads(output.read_text(encoding="utf-8")) == result

    observed["stop_acknowledged"] = False
    with pytest.raises(RuntimeError, match="did not meet its contract"):
        qualify_worker_journey.qualify(
            tmp_path / "launcher", tmp_path / "amino.rcms", destination, output,
        )
