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
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.verification_evidence import (
    DESKTOP_TOOL_PATHS_ENV, desktop_environment, external_tools, passed_evidence, remember_evidence, source_digest,
    verification_launch_inputs, verified_typing,
)
from tests.e2e.desktop_scenarios import SCENARIOS


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
        "workflow_files_sha256": {
            path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((ROOT / "tests/e2e").iterdir())
            if path.is_file() and path.suffix in {".py", ".json"}
        },
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


def _reuse_evidence(context, args) -> bool:
    if args.compare_measures is not None:
        return False
    if context is not None and not args.native and os.environ.get("RCMS_E2E_REUSE_PASSED") == "1":
        reused = passed_evidence(context, args.scenario)
        if reused is not None:
            print(f"Evidence: {reused}", flush=True)
            print("Reused passed evidence: identical source/runtime/input signature; all artifact hashes verified", flush=True)
            return True
    return False


def _print_failure_transcripts(evidence: Path) -> None:
    encoding = sys.stdout.encoding or "utf-8"
    for name in ("stdout.log", "stderr.log"):
        transcript = (evidence / name).read_text(encoding="utf-8", errors="replace")
        display = f"{name} (last 20000 characters):\n{transcript[-20000:]}"
        print(display.encode(encoding, errors="backslashreplace").decode(encoding), flush=True)


def _desktop_environment(work: Path, evidence: Path, base: dict[str, str]) -> dict[str, str]:
    r_temporary = work / "tmp"
    r_temporary.mkdir()
    return base | {
        "RCMS_ANALYSIS_SCRATCH_DIR": str(work / "analysis"),
        "RCMS_E2E_EVIDENCE_DIR": str(evidence),
        "TMPDIR": str(r_temporary),
        "TMP": str(r_temporary),
        "TEMP": str(r_temporary),
    }


def _compare_hillclimb(passed, args, evidence):
    if not passed or args.scenario != "hillclimb":
        return passed
    measured = json.loads((evidence / "measures.json").read_text())
    if args.compare_measures:
        previous = json.loads(args.compare_measures.read_text())
        without_wall_times = lambda data: {task: {k: v for k, v in values.items() if k != "wall_seconds"} for task, values in data.items()}
        if without_wall_times(measured) != without_wall_times(previous):
            passed = False
            print("Hillclimb counts or numerical output changed", file=sys.stderr)
    print(json.dumps(measured, indent=2))
    return passed


def _desktop_command(scenario, work):
    timeout_seconds = SCENARIOS[scenario].timeout_seconds
    command = [
        sys.executable,
        str(ROOT / "scripts/run_with_timeout.py"),
        "--timeout-seconds",
        str(timeout_seconds),
        "--label",
        "RCMS " + scenario,
        "--",
        sys.executable,
        "-X",
        "faulthandler",
        str(ROOT / "tests/e2e/desktop_driver.py"),
        scenario,
        str(work),
    ]
    return command


def _desktop_typing(build_root: Path, source: str, env: dict[str, str], *, native: bool):
    try:
        controller = json.loads(os.environ.get("RCMS_E2E_CONTEXT", "{}"))
    except ValueError:
        controller = {}
    typing_evidence = controller.get("typing") if isinstance(controller, dict) else None
    if not native and verified_typing(typing_evidence, build_root, source):
        context = controller.get("verification")
        if context is not None and source != context["source_sha256"]:
            raise RuntimeError("Verification inputs changed after desktop collection; restart the run")
        if controller.get("launch_inputs") != verification_launch_inputs(env):
            context = None
        if context is not None and context.get("external_tools") != external_tools(env):
            raise RuntimeError("Verification tools changed after desktop collection; restart the run")
        return typing_evidence, context
    from scripts.verify import run_typing
    return str(run_typing(build_root)), None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=SCENARIOS)
    parser.add_argument(
        "--native",
        action="store_true",
        help="Use the host Qt platform instead of offscreen",
    )
    parser.add_argument("--compare-measures", type=Path, help="Compare hillclimb counts and numerical output with a previous measures.json")
    args = parser.parse_args()
    env = desktop_environment(native=args.native)
    build_root = Path(env["RCMS_QT6_BUILD_ROOT"])
    source = source_digest(build_root)
    typing_evidence, context = _desktop_typing(build_root, source, env, native=args.native)
    if _reuse_evidence(context, args):
        return 0
    tools = context["external_tools"] if context is not None else external_tools(env)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    evidence = ROOT / "artifacts/verification/rcms" / (run_id + "-" + args.scenario)
    evidence.mkdir(parents=True, exist_ok=False)
    scratch_root = ROOT / "build/verification/rcms"
    scratch_root.mkdir(parents=True, exist_ok=True)
    record = run_metadata(args.scenario, args.native)
    record["typing_evidence"] = typing_evidence
    record["external_tools"] = tools
    if context is not None:
        record["verification_context"] = context
    try:
        with tempfile.TemporaryDirectory(
            prefix="desktop-", dir=scratch_root
        ) as temporary:
            work = Path(temporary)
            child_environment = _desktop_environment(work, evidence, env)
            child_environment[DESKTOP_TOOL_PATHS_ENV] = json.dumps({
                name: tool["path"] if tool else None for name, tool in tools.items()
            })
            command = _desktop_command(args.scenario, work)
            record["command"] = command
            print(f"Evidence: {evidence}", flush=True)
            try:
                child_environment["RCMS_DRIVE_STARTED"] = str(time.time())
                with (
                    (evidence / "stdout.log").open("wb") as stdout,
                    (evidence / "stderr.log").open("wb") as stderr,
                ):
                    result = subprocess.run(
                        command,
                        cwd=work,
                        env=child_environment,
                        stdout=stdout,
                        stderr=stderr,
                        check=False,
                    )
                record["exit_code"] = result.returncode
                passed = result.returncode == 0 and "WORKFLOW PASSED" in (
                    evidence / "stdout.log"
                ).read_text(encoding="utf-8", errors="replace")
                passed = _compare_hillclimb(passed, args, evidence)
            finally:
                # Move the finished workspace so the evidence keeps its settings and R scratch files.
                shutil.move(work, evidence / "workflow")
        if passed and tools != external_tools(env):
            raise RuntimeError("Verification tools changed during desktop driving; restart the run")
        record["passed"] = passed
        if not passed:
            _print_failure_transcripts(evidence)
        return 0 if passed else 1
    finally:
        if source_digest(build_root) != source:
            record["passed"] = False
            write_manifest(evidence, record)
            raise RuntimeError("Verification inputs changed during desktop driving; restart the run")
        write_manifest(evidence, record)
        if context is not None and record["passed"] and not args.native:
            remember_evidence(context, args.scenario, evidence)


if __name__ == "__main__":
    raise SystemExit(main())
