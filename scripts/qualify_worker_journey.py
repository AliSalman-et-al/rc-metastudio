#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qualify a packaged owned-worker result on the host that runs the package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess


def qualify(
    executable: Path,
    sample: Path,
    destination: Path,
    output: Path,
    *,
    artifact: Path | None = None,
    r_home: Path | None = None,
    r_libs: Path | None = None,
) -> dict[str, object]:
    """Run the actual package and retain its observed worker journey facts."""
    output.parent.mkdir(parents=True, exist_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    observation = output.with_name(output.stem + ".observation.json")
    environment = os.environ.copy()
    for name in (
        "R_HOME", "R_LIBS", "R_LIBS_USER", "RCMS_R_HOME", "RCMS_R_LIBS",
        "RCMS_REQUIRE_IN_PROCESS_RPY2",
    ):
        environment.pop(name, None)
    if r_home is not None:
        environment["RCMS_R_HOME"] = str(r_home)
    if r_libs is not None:
        environment["RCMS_R_LIBS"] = str(r_libs)
    command = [
        str(executable),
        "--automation-package-worker-journey",
        str(observation),
        str(sample),
        str(destination),
    ]
    subprocess.run(command, check=True, timeout=300, env=environment)
    journey = json.loads(observation.read_text(encoding="utf-8"))
    expected = (
        journey.get("worker_completed") is True
        and journey.get("event_loop_responsive") is True
        and journey.get("stop_acknowledged") is True
        and journey.get("stopped_settings_retained") is True
        and journey.get("saved_analysis_status") == "complete"
        and journey.get("reopened_analysis_count") == 1
        and journey.get("reopened_draft_count") == 1
        and isinstance(journey.get("offline_export_bytes"), int)
        and journey["offline_export_bytes"] > 0
    )
    if not expected:
        raise RuntimeError("packaged owned-worker journey did not meet its contract")
    result: dict[str, object] = {
        "schema_version": 1,
        "passed": True,
        "host": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "package_sha256": _sha256_file(artifact) if artifact else None,
        "observation": journey,
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


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
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--r-home", type=Path)
    parser.add_argument("--r-libs", type=Path)
    arguments = parser.parse_args()
    qualify(
        arguments.executable,
        arguments.sample,
        arguments.destination,
        arguments.output,
        artifact=arguments.artifact,
        r_home=arguments.r_home,
        r_libs=arguments.r_libs,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
