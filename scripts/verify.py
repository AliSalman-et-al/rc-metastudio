# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
#!/usr/bin/env python3
"""Run the maintained source verification lanes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

if __package__:
    from scripts import r_verification_support as r_support
else:
    import r_verification_support as r_support


class VerificationError(RuntimeError):
    """A command-line or verification setup error."""


def discover_repo_root(start: Path | None = None) -> Path:
    """Find the repository containing both ``pyproject.toml`` and ``scripts``."""
    current = (start or Path(__file__).resolve()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "scripts"
        ).is_dir():
            return candidate
    raise VerificationError(f"could not discover repository root from {current}")


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = discover_repo_root(SCRIPT_DIR)
DEFAULT_BUILD_ROOT = REPO_ROOT / "build" / "qt6-verification"
DEFAULT_R_LIBRARY_CACHE = REPO_ROOT / "artifacts" / "r-default-library-cache"
FULL_R_LIBRARY_CACHE = REPO_ROOT / "artifacts" / "r-library-cache"
STABLE_BASELINE = "8b7796bcc840c3505c5fb0a1328cdd7682880e48"
SMOKE_TESTS = (
    "tests/analysis_regression/golden/test_analysis_regression_compare.py::"
    "test_golden_summary_parser_reads_current_RCMetaR_summary_display",
    "tests/python/fast/test_project_format.py::"
    "test_failed_atomic_replace_preserves_the_previous_project",
    "tests/python/fast/test_qt6_build_slice.py::"
    "test_minimal_qt6_window_reports_resources_and_exits_cleanly",
)


def write_step(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    """Run one child command and stop at the first failure."""
    write_step("$ " + " ".join(command))
    try:
        subprocess.run(command, cwd=REPO_ROOT, env=env, check=True)
    except FileNotFoundError as exc:
        raise VerificationError(f"command not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise VerificationError(
            f"command failed with exit code {exc.returncode}: {' '.join(command)}"
        ) from exc


def sync_environment() -> None:
    write_step("Syncing locked verification environment with uv")
    run(["uv", "sync", "--locked"])


def prepare_qt_environment(build_root: Path) -> dict[str, str]:
    run(
        [
            sys.executable,
            "scripts/build_qt6.py",
            "generate",
            "--build-root",
            str(build_root),
        ]
    )
    env = dict(os.environ)
    env["RCMS_QT6_BUILD_ROOT"] = str(build_root)
    # ``rc_metastudio.qt6_ui`` extends the installed package paths with the
    # generated tree. Keeping generated directories off ``PYTHONPATH`` avoids
    # importing a second, marker-only rc_metastudio package.
    path_entries = []
    if env.get("PYTHONPATH"):
        path_entries.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(path_entries)
    return env


def preflight(env: dict[str, str]) -> None:
    write_step("Collecting pytest nodes with strict marker validation")
    run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--strict-markers",
            "tests",
            "--collect-only",
            "-qq",
        ],
        env=env,
    )


def bounded_workers(requested: int) -> int:
    if requested < 0:
        raise VerificationError("--fast-workers must be zero or greater")
    return min(requested, max(1, os.cpu_count() or 1), 8)


def run_pytest(nodes: list[str], *, env: dict[str, str], workers: int = 0) -> None:
    command = [sys.executable, "-m", "pytest", "--strict-markers", *nodes]
    worker_count = bounded_workers(workers)
    if worker_count > 1:
        command += ["--dist", "loadfile", "-n", str(worker_count)]
    run(command, env=env)


def selected_rscript(args: argparse.Namespace) -> str:
    requested = args.rscript
    if args.r_runtime_root:
        candidates = r_support.rscript_paths_for_r_home(args.r_runtime_root)
        if requested:
            explicit = r_support.resolve_rscript(requested)
            if explicit is None or explicit.resolve() not in {p.resolve() for p in candidates}:
                raise VerificationError("explicit Rscript conflicts with selected R runtime root")
            return str(explicit.resolve())
        for candidate in candidates:
            if candidate.exists():
                return str(candidate.resolve())
        if requested and requested != "Rscript":
            raise VerificationError(f"Rscript was not found at '{requested}'.")
        raise VerificationError(
            f"Rscript was not found in selected R runtime at '{args.r_runtime_root}'."
        )
    resolved = r_support.resolve_rscript(requested or "Rscript")
    if resolved is not None:
        return str(resolved)
    if requested and requested != "Rscript":
        raise VerificationError(f"Rscript was not found at '{requested}'.")
    return "Rscript"


def run_default_r_evidence(args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        "scripts/verify_rcmetar_r_default.py",
        "--rscript",
        selected_rscript(args),
    ]
    if args.require_r_evidence:
        command += [
            "--require-r",
            "--require-installed-packages",
            "--install-missing",
            "--r-library-cache-root",
            str(args.r_library_cache_root or DEFAULT_R_LIBRARY_CACHE),
        ]
    write_step("Verifying Default R Evidence")
    run(command)


def run_source_lane(args: argparse.Namespace, *, smoke: bool) -> None:
    if args.sync:
        sync_environment()
    else:
        write_step("Skipping dependency sync for warm local verification")
    build_root = (REPO_ROOT / args.build_root).resolve()
    env = prepare_qt_environment(build_root)
    run_typing(build_root)
    preflight(env)
    if smoke:
        write_step("Running smoke pytest nodes")
        run_pytest(list(SMOKE_TESTS), env=env)
        if not args.skip_r_evidence:
            run_default_r_evidence(args)
    else:
        write_step("Running fast and golden pytest lanes")
        run_pytest(
            ["tests/python/fast", "tests/analysis_regression/golden"],
            env=env,
            workers=args.fast_workers,
        )
        if not args.skip_r_evidence:
            run_default_r_evidence(args)


def run_full_r_stack(args: argparse.Namespace) -> None:
    if args.sync:
        sync_environment()
    else:
        write_step("Skipping dependency sync for warm local R verification")
    build_root = (REPO_ROOT / args.build_root).resolve()
    env = prepare_qt_environment(build_root)
    command = [
        sys.executable,
        "scripts/verify_rcmetar_r_stack.py",
        "--rscript",
        selected_rscript(args),
        "--r-library-cache-root",
        str(args.r_library_cache_root or FULL_R_LIBRARY_CACHE),
    ]
    if args.skip_desktop:
        command.append("--skip-desktop")
    if args.desktop_shard is not None:
        command += ["--desktop-shard", str(args.desktop_shard)]
    write_step("Delegating Full R Stack Evidence")
    run(command, env=env)


def run_typing(build_root: Path) -> None:
    command = [
        sys.executable,
        "-m",
        "ty",
        "check",
        "--python",
        sys.executable,
        "--python-platform",
        "win32",
    ]
    for path in (
        str(build_root / "generated/rc_metastudio"),
        str(build_root / "generated/rc_metastudio/forms"),
        ".",
        "src/rc_metastudio",
        "src",
        "scripts",
        "tests/python/gui",
    ):
        command += ["--extra-search-path", path]
    command += ["src/rc_metastudio", "scripts", "tests", "r/RCMetaR/inst/qa",
                ".agents/skills/verify-rcms/scripts"]
    evidence = REPO_ROOT / "artifacts/verification/typing" / (datetime.now().strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:8])
    evidence.mkdir(parents=True)
    write_step("$ " + " ".join(command))
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    (evidence / "stdout.log").write_text(result.stdout, encoding="utf-8")
    (evidence / "stderr.log").write_text(result.stderr, encoding="utf-8")
    (evidence / "command.json").write_text(json.dumps({"command": command, "python_platform": "win32", "exit_code": result.returncode}, indent=2), encoding="utf-8")
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    print(f"Typing evidence: {evidence}", flush=True)
    if result.returncode:
        raise VerificationError(f"strict typing failed; inspect {evidence}")


def run_code_health(base: str = "origin/master", head: str = "HEAD") -> None:
    run(
        [
            sys.executable,
            "scripts/code_health.py",
            "--base",
            STABLE_BASELINE,
            "--head",
            STABLE_BASELINE,
            "--allow-fail",
            "--output",
            "artifacts/code-health/baseline.json",
            "--report",
            "artifacts/code-health/baseline.txt",
        ]
    )
    # shortcut: local code health measures committed HEAD, upgrade if dirty-tree qualification is needed.
    run(
        [
            sys.executable,
            "scripts/code_health.py",
            "--base",
            base,
            "--head",
            head,
            "--baseline",
            "artifacts/code-health/baseline.json",
            "--output",
            "artifacts/code-health/final.json",
            "--report",
            "artifacts/code-health/final.txt",
        ]
    )


def run_packaging_contracts() -> None:
    run([sys.executable, "-m", "pytest", "-q", "tests/packaging/contract"])


def run_pre_push() -> None:
    build = Path(
        os.environ.get("RCMS_QT6_BUILD_ROOT", str(DEFAULT_BUILD_ROOT))
    ).resolve()
    os.environ["RCMS_QT6_BUILD_ROOT"] = str(build)
    fast = parser().parse_args(
        ["fast", "--skip-r-evidence", "--build-root", str(build)]
    )
    steps = [
        ("prepare", lambda: prepare_qt_environment(build)),
        ("typing (win32)", lambda: run_typing(build)),
        ("code health", run_code_health),
        ("Python fast and golden", lambda: run_source_lane(fast, smoke=False)),
        (
            "GUI",
            lambda: run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-W",
                    "error",
                    "--strict-markers",
                    "tests/python/gui",
                ]
            ),
        ),
        ("packaging contracts", run_packaging_contracts),
    ]
    rows = [{"step": name, "seconds": 0.0, "status": "not run"} for name, _ in steps]
    # shortcut: native platform qualification stays in CI, upgrade when local native setup is owned here.
    rows += [
        {"step": name, "seconds": 0.0, "status": "CI only"}
        for name in (
            "R stack, authorities and desktop E2E (local: python scripts/verify.py r-stack)",
            "Windows native Qt and package qualification",
            "macOS native smoke and packaging",
            "Linux native xcb smoke",
        )
    ]
    try:
        for row, (_, action) in zip(rows, steps):
            started = time.monotonic()
            row["status"] = "fail"
            try:
                action()
                row["status"] = "pass"
            finally:
                row["seconds"] = round(time.monotonic() - started, 2)
    finally:
        output = REPO_ROOT / "artifacts/verification/pre-push.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        print("\n| Step | Seconds | Result |\n| --- | ---: | --- |")
        for row in rows:
            print(f"| {row['step']} | {row['seconds']} | {row['status']} |")


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    subparsers = cli.add_subparsers(dest="lane", required=True)

    def add_rscript_options(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--rscript")
        subparser.add_argument("--r-runtime-root")
        subparser.add_argument(
            "--r-library-cache-root",
            "--r-package-cache-root",
            dest="r_library_cache_root",
            type=Path,
        )

    def add_source_options(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--sync", action="store_true")
        r_evidence = subparser.add_mutually_exclusive_group()
        r_evidence.add_argument("--require-r-evidence", action="store_true")
        r_evidence.add_argument("--skip-r-evidence", action="store_true")
        add_rscript_options(subparser)

    smoke = subparsers.add_parser("smoke", help="run the representative smoke lane")
    add_source_options(smoke)
    smoke.add_argument("--build-root", default=DEFAULT_BUILD_ROOT, type=Path)

    fast = subparsers.add_parser(
        "fast", help="run fast, golden, and Default R Evidence"
    )
    add_source_options(fast)
    fast.add_argument(
        "--fast-workers",
        default=os.environ.get("RCMS_FAST_WORKERS", "4"),
        type=int,
    )
    fast.add_argument("--build-root", default=DEFAULT_BUILD_ROOT, type=Path)

    r_stack = subparsers.add_parser("r-stack", help="run Full R Stack Evidence")
    selection = r_stack.add_mutually_exclusive_group()
    selection.add_argument("--skip-desktop", action="store_true")
    selection.add_argument("--desktop-shard", type=int, choices=(1, 2, 3))
    r_stack.add_argument("--sync", action="store_true")
    add_rscript_options(r_stack)
    r_stack.add_argument("--build-root", default=DEFAULT_BUILD_ROOT, type=Path)
    subparsers.add_parser("pre-push", help="run required local CI checks, failing fast")
    return cli


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.lane == "smoke":
            run_source_lane(args, smoke=True)
        elif args.lane == "fast":
            run_source_lane(args, smoke=False)
        elif args.lane == "pre-push":
            run_pre_push()
        else:
            run_full_r_stack(args)
    except VerificationError as exc:
        print(f"verification failed: {exc}", file=sys.stderr)
        return 1
    write_step(f"{args.lane} verification complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
