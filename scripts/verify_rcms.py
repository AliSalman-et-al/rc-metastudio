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
from scripts.verification_evidence import passed_evidence, remember_evidence, source_digest
sys.path.insert(0, str(ROOT / ".agents/skills/verify-rcms/scripts"))
from advanced_workflows import SCENARIOS as ADVANCED_SCENARIOS
from analysis_matrix import SCENARIOS as ANALYSIS_SCENARIOS
from ratio_workflows import SCENARIOS as RATIO_SCENARIOS

SCENARIOS = (
    *("audit-round3-" + family for family in ("onearm-proportion", "onearm-mean", "reg-coef", "generic-effect", "twoarm-proportion", "twoarm-mean", "twoarm-smd", "diagnostic", "hr", "irr", "references", "precision", "round5", "bubble-metrics", "irr-context", "arm-names", *("presentation-" + family for family in ("diagnostic", "onearm-proportion", "twoarm-proportion", "twoarm-mean", "twoarm-smd", "reg-coef", "generic-effect", "sequential", "transforms")))),
    "review1-design",
    "review-workflows",
    "doctor",
    "hillclimb",
    "analysis-dialog",
    "grid-entry",
    "ux-improvements",
    "results-window",
    "summary-of-findings",
    "manuscript-export-direct",
    "manuscript-export",
    "amino",
    "sheets",
    "ui-crawl",
    "rm5-import",
    "sheets-legacy",
    "sheets-edges",
    "sheets-persist",
    "sheets-swap",
    "continuous",
    "lymph",
    "editing",
    "csv",
    "xlsx-import",
    "plot-edit",
    "small-study-effects",
    "calculator-binary",
    "calculator-continuous",
    "calculator-diagnostic",
    *ANALYSIS_SCENARIOS,
    *ADVANCED_SCENARIOS,
    *RATIO_SCENARIOS,
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


def _scenario_timeout(scenario: str) -> int:
    if scenario == "ui-crawl":
        return 600
    timeout_seconds = 120
    if scenario in {"sheets-legacy", "sheets-swap"}:
        return 600
    if scenario in {"sheets-baseline", "hillclimb", "manuscript-export", "manuscript-export-direct", "summary-of-findings", "results-window", "ux-improvements"}:
        return 600
    if scenario in {"ratios-hr", "ratios-irr", "project-display-labels", "project-round6-polish", "project-release-coefficients", "project-reviewer-predictions", "project-reviewer-groups", "project-reviewer-colours", "calculator-ratio-precision", "project-axis-proportions", "project-axis-others", "project-axis-sequential"}:
        timeout_seconds = 600
    elif scenario.startswith("audit-round3-"):
        timeout_seconds = 600
    elif scenario.startswith("plot-workflow-"):
        timeout_seconds = 240
    return timeout_seconds


def _reuse_evidence(context, args) -> bool:
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


def _desktop_environment(work: Path, evidence: Path, native: bool) -> dict[str, str]:
    r_temporary = work / "tmp"
    r_temporary.mkdir()
    env = os.environ | {
        "PYTHONIOENCODING": "utf-8",
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
    if native:
        env.pop("QT_QPA_PLATFORM", None)
    else:
        env["QT_QPA_PLATFORM"] = "offscreen"
        if sys.platform == "win32":
            env.setdefault("QT_QPA_FONTDIR", str(Path(env["WINDIR"]) / "Fonts"))
    return env


def _compare_hillclimb(passed, args, evidence):
    if not passed or args.scenario != "hillclimb":
        return passed
    measured = json.loads((evidence / "measures.json").read_text())
    if args.compare_measures:
        previous = json.loads(args.compare_measures.read_text())
        stable = lambda data: {task: {k: v for k, v in values.items() if k != "wall_seconds"} for task, values in data.items()}
        if stable(measured) != stable(previous):
            passed = False
            print("Hillclimb counts or numerical output changed", file=sys.stderr)
    print(json.dumps(measured, indent=2))
    return passed


def _desktop_command(scenario, work):
    timeout_seconds = _scenario_timeout(scenario)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=(*SCENARIOS, "sheets-baseline"))
    parser.add_argument(
        "--native",
        action="store_true",
        help="Use the host Qt platform instead of offscreen",
    )
    parser.add_argument("--compare-measures", type=Path, help="Compare hillclimb counts and numerical output with a previous measures.json")
    args = parser.parse_args()
    context = json.loads(os.environ["RCMS_E2E_CONTEXT"]) if os.environ.get("RCMS_E2E_CONTEXT") else None
    if context is not None and source_digest() != context["source_sha256"]:
        raise RuntimeError("Verification inputs changed after desktop collection; restart the run")
    if _reuse_evidence(context, args):
        return 0
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    evidence = ROOT / "artifacts/verification/rcms" / (run_id + "-" + args.scenario)
    evidence.mkdir(parents=True, exist_ok=False)
    scratch_root = ROOT / "build/verification/rcms"
    scratch_root.mkdir(parents=True, exist_ok=True)
    record = run_metadata(args.scenario, args.native)
    if context is not None:
        record["verification_context"] = context
    try:
        with tempfile.TemporaryDirectory(
            prefix="desktop-", dir=scratch_root
        ) as temporary:
            work = Path(temporary)
            env = _desktop_environment(work, evidence, args.native)
            command = _desktop_command(args.scenario, work)
            record["command"] = command
            print(f"Evidence: {evidence}", flush=True)
            try:
                env["RCMS_DRIVE_STARTED"] = str(time.time())
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
                passed = _compare_hillclimb(passed, args, evidence)
                record["passed"] = passed
            finally:
                # Copy before TemporaryDirectory removes settings and R scratch files.
                shutil.copytree(work, evidence / "workflow")
        if not passed:
            _print_failure_transcripts(evidence)
        return 0 if passed else 1
    finally:
        if context is not None and source_digest() != context["source_sha256"]:
            record["passed"] = False
            write_manifest(evidence, record)
            raise RuntimeError("Verification inputs changed during desktop driving; restart the run")
        write_manifest(evidence, record)
        if context is not None and record["passed"] and not args.native:
            remember_evidence(context, args.scenario, evidence)


if __name__ == "__main__":
    raise SystemExit(main())
