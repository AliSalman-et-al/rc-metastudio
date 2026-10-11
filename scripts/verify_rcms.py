#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Capture durable evidence from the existing real Qt/R desktop driver."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents/skills/verify-rcms/scripts"))
from advanced_workflows import SCENARIOS as ADVANCED_SCENARIOS
from analysis_matrix import SCENARIOS as ANALYSIS_SCENARIOS

SCENARIOS = (
    "doctor",
    "amino",
    "continuous",
    "lymph",
    "editing",
    "csv",
    "plot-edit",
    "small-study-effects",
    "calculator-binary",
    "calculator-continuous",
    "calculator-diagnostic",
    *ANALYSIS_SCENARIOS,
    *ADVANCED_SCENARIOS,
)


def git_output(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.strip()


def run_metadata(scenario: str, native: bool) -> dict[str, object]:
    return {
        "scenario": scenario,
        "started_utc": datetime.now(UTC).isoformat(),
        "head": git_output("rev-parse", "HEAD"),
        "worktree_status": git_output("status", "--short"),
        "tracked_diff_sha256": hashlib.sha256(
            git_output("diff", "HEAD", "--binary").encode()
        ).hexdigest(),
        "driver_sha256": hashlib.sha256(
            (ROOT / "tests/e2e/desktop_driver.py").read_bytes()
        ).hexdigest(),
        "skill_files_sha256": {
            path.relative_to(ROOT).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted((ROOT / ".agents/skills/verify-rcms").rglob("*"))
            if path.is_file() and path.suffix in {".py", ".R", ".md", ".yaml"}
        },
        "python": sys.executable,
        "native_requested": native,
        "passed": False,
    }


def write_manifest(evidence: Path, record: dict[str, object]) -> None:
    record["finished_utc"] = datetime.now(UTC).isoformat()
    record["worktree_status_after"] = git_output("status", "--short")
    record["files"] = [
        {
            "path": path.relative_to(evidence).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in sorted(evidence.rglob("*"))
        if path.is_file()
    ]
    (evidence / "manifest.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=SCENARIOS)
    parser.add_argument(
        "--native",
        action="store_true",
        help="Use the host Qt platform instead of offscreen",
    )
    args = parser.parse_args()
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    evidence = ROOT / "artifacts/verification/rcms" / (run_id + "-" + args.scenario)
    evidence.mkdir(parents=True, exist_ok=False)
    scratch_root = ROOT / "build/verification/rcms"
    scratch_root.mkdir(parents=True, exist_ok=True)
    record = run_metadata(args.scenario, args.native)
    try:
        with tempfile.TemporaryDirectory(
            prefix="desktop-", dir=scratch_root
        ) as temporary:
            work = Path(temporary)
            r_temporary = work / "tmp"
            r_temporary.mkdir()
            env = os.environ | {
                "PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(ROOT))),
                "RCMS_REQUIRE_IN_PROCESS_RPY2": "1",
                "RCMS_QT6_BUILD_ROOT": os.environ.get(
                    "RCMS_QT6_BUILD_ROOT", str(ROOT / "build/qt6-verification")
                ),
                "RCMS_ANALYSIS_SCRATCH_DIR": str(work / "analysis"),
                "RCMS_E2E_EVIDENCE_DIR": str(evidence),
                "TMPDIR": str(r_temporary),
                "TMP": str(r_temporary),
                "TEMP": str(r_temporary),
            }
            if args.native:
                env.pop("QT_QPA_PLATFORM", None)
            else:
                env["QT_QPA_PLATFORM"] = "offscreen"
            command = [
                sys.executable,
                str(ROOT / "scripts/run_with_timeout.py"),
                "--timeout-seconds",
                "240" if args.scenario.startswith("plot-workflow-") else "120",
                "--label",
                "RCMS " + args.scenario,
                "--",
                sys.executable,
                "-X",
                "faulthandler",
                str(ROOT / "tests/e2e/desktop_driver.py"),
                args.scenario,
                str(work),
            ]
            record["command"] = command
            print(f"Evidence: {evidence}", flush=True)
            try:
                with (
                    (evidence / "stdout.log").open("wb") as stdout,
                    (evidence / "stderr.log").open("wb") as stderr,
                ):
                    result = subprocess.run(
                        command,
                        cwd=work,
                        env=env,
                        stdout=stdout,
                        stderr=stderr,
                        check=False,
                    )
                record["exit_code"] = result.returncode
                passed = result.returncode == 0 and "WORKFLOW PASSED" in (
                    evidence / "stdout.log"
                ).read_text(encoding="utf-8", errors="replace")
                record["passed"] = passed
            finally:
                # Copy before TemporaryDirectory removes settings and R scratch files.
                shutil.copytree(work, evidence / "workflow")
        return 0 if passed else 1
    finally:
        write_manifest(evidence, record)


if __name__ == "__main__":
    raise SystemExit(main())
