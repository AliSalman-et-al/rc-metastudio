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
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from uuid import uuid4

if __package__:
    from scripts import r_verification_support as r_support
    from scripts.desktop_partition import DESKTOP_SHARDS
    from scripts.verification_evidence import source_digest, typing_command, verified_typing
else:
    import r_verification_support as r_support
    from desktop_partition import DESKTOP_SHARDS
    from verification_evidence import source_digest, typing_command, verified_typing


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
PRE_PUSH_RECEIPT = REPO_ROOT / "artifacts" / "verification" / "pre-push.json"
TYPING_RECEIPT_ENV = "RCMS_TYPING_RECEIPT"
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


def configured_build_root(env: dict[str, str]) -> Path:
    return Path(env.get("RCMS_QT6_BUILD_ROOT", DEFAULT_BUILD_ROOT)).resolve()


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
        raise VerificationError(
            f"Rscript was not found in selected R runtime at '{args.r_runtime_root}'."
        )
    resolved = r_support.resolve_rscript(requested or "Rscript")
    if resolved is not None:
        return str(resolved)
    if requested and requested != "Rscript":
        raise VerificationError(f"Rscript was not found at '{requested}'.")
    return "Rscript"


def run_default_r_evidence(args: argparse.Namespace, rscript: str, env: dict[str, str]) -> None:
    command = [
        sys.executable,
        "scripts/verify_rcmetar_r_default.py",
        "--rscript",
        rscript,
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
    run(command, env=env)


def run_source_lane(args: argparse.Namespace, *, smoke: bool) -> None:
    if args.sync:
        sync_environment()
    else:
        write_step("Skipping dependency sync for warm local verification")
    build_root = (REPO_ROOT / args.build_root).resolve()
    env = prepare_qt_environment(build_root)
    rscript = selected_rscript(args)
    if rscript != "Rscript":
        env["RCMS_RSCRIPT"] = rscript
    run_typing(build_root)
    run_source_tests(env, smoke=smoke, fast_workers=0 if smoke else args.fast_workers)
    if not args.skip_r_evidence:
        run_default_r_evidence(args, rscript, env)


def run_source_tests(env: dict[str, str], *, smoke: bool, fast_workers: int) -> None:
    preflight(env)
    if smoke:
        write_step("Running smoke pytest nodes")
        run_pytest(list(SMOKE_TESTS), env=env)
    else:
        write_step("Running fast and golden pytest lanes")
        run_pytest(
            ["tests/python/fast", "tests/analysis_regression/golden"],
            env=env,
            workers=fast_workers,
        )


def run_full_r_stack(args: argparse.Namespace) -> None:
    if args.sync:
        sync_environment()
    else:
        write_step("Skipping dependency sync for warm local R verification")
    build_root = (REPO_ROOT / args.build_root).resolve()
    env = os.environ | {"RCMS_QT6_BUILD_ROOT": str(build_root)}
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


def run_typing(build_root: Path) -> Path:
    source_before = source_digest(build_root)
    command = typing_command(build_root)
    evidence = REPO_ROOT / "artifacts/verification/typing" / (datetime.now().strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:8])
    evidence.mkdir(parents=True)
    write_step("$ " + " ".join(command))
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    (evidence / "stdout.log").write_text(result.stdout, encoding="utf-8")
    (evidence / "stderr.log").write_text(result.stderr, encoding="utf-8")
    receipt = evidence / "command.json"
    source_after = source_digest(build_root)
    receipt.write_text(json.dumps({
        "command": command,
        "python_platform": "win32",
        "exit_code": result.returncode,
        "build_root": str(build_root.resolve()),
        "source_sha256": source_before,
        "source_unchanged": source_before == source_after,
    }, indent=2), encoding="utf-8")
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    print(f"Typing evidence: {evidence}", flush=True)
    if result.returncode:
        raise VerificationError(f"strict typing failed; inspect {evidence}")
    if source_before != source_after:
        raise VerificationError(f"verification inputs changed during strict typing; inspect {evidence}")
    return receipt


def ensure_typing(build_root: Path, env: dict[str, str]) -> Path:
    inherited = env.get(TYPING_RECEIPT_ENV)
    if inherited and verified_typing(inherited, build_root, source_digest(build_root)):
        return Path(inherited)
    return run_typing(build_root)


def run_code_health(
    base: str = "origin/master", head: str = "HEAD", *, reuse_baseline: bool = False
) -> None:
    baseline = Path("artifacts/code-health/baseline.json")
    report = baseline.with_suffix(".txt")
    cached = False
    if reuse_baseline and (REPO_ROOT / report).is_file():
        from scripts.code_health import CodeHealthError, load_baseline

        try:
            cached = load_baseline(REPO_ROOT / baseline).get("head") == STABLE_BASELINE
        except CodeHealthError:
            pass
    if not cached:
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
                str(baseline),
                "--report",
                str(report),
            ]
        )
    run(
        [
            sys.executable,
            "scripts/code_health.py",
            "--base",
            base,
            "--head",
            head,
            "--baseline",
            str(baseline),
            "--output",
            "artifacts/code-health/final.json",
            "--report",
            "artifacts/code-health/final.txt",
        ]
    )


def run_packaging_contracts(env: dict[str, str] | None = None) -> None:
    run([sys.executable, "-m", "pytest", "-q", "tests/packaging/contract"], env=env)


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def clean_checkout() -> bool:
    return not git_output("status", "--porcelain", "--untracked-files=all", "--ignore-submodules=none")


def pinned_r_environment(env: dict[str, str]) -> None:
    selected_home = env.get("RCMS_R_HOME")
    if selected_home:
        rscript = next(
            (path for path in r_support.rscript_paths_for_r_home(selected_home) if path.is_file()),
            None,
        )
    else:
        rscript = r_support.resolve_rscript("Rscript", env)
    if rscript is None:
        raise VerificationError("Rscript not found; set RCMS_R_HOME to the manifest-pinned installation")
    # Let the selected Rscript resolve its own home, independently of ambient R_HOME.
    env.pop("R_HOME", None)
    manifest = json.loads((REPO_ROOT / "config/r-dependencies.json").read_text(encoding="utf-8"))
    expected = manifest["target_runtime"]["r"]
    actual = subprocess.check_output(
        [str(rscript), "--vanilla", "-e", "cat(as.character(getRversion()))"],
        cwd=REPO_ROOT, env=env, text=True,
    ).strip()
    if actual != expected:
        raise VerificationError(f"{rscript} is R {actual}; expected R {expected}. Set RCMS_R_HOME.")
    home = str(r_support.resolve_r_home(rscript, REPO_ROOT, env))
    write_step(f"Using pinned R {actual} at {home}")
    env.update(
        RCMS_RSCRIPT=str(rscript),
        RCMS_R_HOME=home,
        R_HOME=home,
        PATH=os.pathsep.join((str(rscript.parent), env.get("PATH", ""))),
    )


def pre_push_steps() -> dict[str, Callable[[], object]]:
    build = configured_build_root(dict(os.environ))
    env: dict[str, str] = {}

    def qt(section: str) -> None:
        run([
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
            "scripts/verify-qt6.ps1", "-Section", section, "-BuildRoot", str(build),
        ], env=env)

    return {
        "prepare": lambda: env.update(prepare_qt_environment(build)),
        "typing (win32)": lambda: run_typing(build),
        "pinned R runtime": lambda: pinned_r_environment(env),
        "code health": run_code_health,
        "fast-verification/source-fast-targets": lambda: run_source_tests(
            env, smoke=False, fast_workers=int(os.environ.get("RCMS_FAST_WORKERS", "4"))
        ),
        "GUI": lambda: run_pytest(["-W", "error", "tests/python/gui"], env=env),
        "fast-verification/packaging-contract": lambda: run_packaging_contracts(env),
        "JavaScript release tests": lambda: run(
            ["node", "--test", "tests/packaging/contract/release_actions.test.cjs"], env=env
        ),
        "fast-verification/qt6-verification": lambda: qt("Core"),
        "fast-verification/remaining-surface-verification": lambda: qt("RemainingSurfaces"),
        "fast-verification/full-r-stack": lambda: run([
            sys.executable, "scripts/verify_rcmetar_r_stack.py",
            "--rscript", env["RCMS_RSCRIPT"], "--r-library-cache-root",
            str(FULL_R_LIBRARY_CACHE), "--fresh", "--doctor",
        ], env=env),
    }


def run_pre_push() -> None:
    steps = pre_push_steps()
    PRE_PUSH_RECEIPT.unlink(missing_ok=True)
    head = git_output("rev-parse", "HEAD")
    clean_at_start = clean_checkout()
    rows = [{"step": name, "seconds": 0.0, "status": "not run"} for name in steps]
    rows += [
        {"step": name, "seconds": 0.0, "status": "CI only"}
        for name in (
            "macOS native smoke and packaging",
            "Linux native xcb smoke",
        )
    ]
    try:
        if sys.platform != "win32":
            raise VerificationError("pre-push requires Windows and a native Qt desktop")
        if not clean_at_start:
            raise VerificationError("commit your changes before running pre-push")
        for row, action in zip(rows, steps.values()):
            started = time.monotonic()
            write_step(f"Starting {row['step']}")
            row["status"] = "fail"
            try:
                action()
                row["status"] = "pass"
            finally:
                row["seconds"] = round(time.monotonic() - started, 2)
    finally:
        clean = clean_at_start and git_output("rev-parse", "HEAD") == head and clean_checkout()
        PRE_PUSH_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        temporary = PRE_PUSH_RECEIPT.with_suffix(f".{uuid4().hex}.tmp")
        temporary.write_text(
            json.dumps({"head": head, "clean": clean, "steps": rows}, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(PRE_PUSH_RECEIPT)
        print("\n| Step | Seconds | Result |\n| --- | ---: | --- |")
        for row in rows:
            print(f"| {row['step']} | {row['seconds']} | {row['status']} |")
    if not clean:
        raise VerificationError("HEAD or the worktree changed during pre-push")


def check_pre_push() -> None:
    # Git supplies local ref, local object, remote ref and remote object for every update.
    updates = [line.split() for line in sys.stdin]
    commits = {local for ref, local, _, _ in updates if ref != "(delete)"}
    if not commits:
        return
    try:
        receipt = json.loads(PRE_PUSH_RECEIPT.read_text(encoding="utf-8"))
        statuses = {row["step"]: row["status"] for row in receipt["steps"]}
        valid = (
            receipt["clean"] is True
            and commits == {receipt["head"]}
            and len(statuses) == len(receipt["steps"])
            and all(statuses.get(step) == "pass" for step in pre_push_steps())
        )
    except (OSError, ValueError, KeyError, TypeError):
        valid = False
    if not valid or not clean_checkout():
        raise VerificationError(
            "No clean passing pre-push receipt for the object(s) being pushed. "
            "See docs/maintaining.md#pre-push-gate."
        )


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
    selection.add_argument("--desktop-shard", type=int, choices=DESKTOP_SHARDS)
    r_stack.add_argument("--sync", action="store_true")
    add_rscript_options(r_stack)
    r_stack.add_argument("--build-root", default=DEFAULT_BUILD_ROOT, type=Path)
    subparsers.add_parser("pre-push", help="run required local CI checks, failing fast")
    subparsers.add_parser("check-pre-push", help="validate a push against the local receipt")
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
        elif args.lane == "check-pre-push":
            check_pre_push()
        else:
            run_full_r_stack(args)
    except (VerificationError, r_support.RVerificationSupportError, subprocess.CalledProcessError) as exc:
        print(f"verification failed: {exc}", file=sys.stderr)
        return 1
    write_step(f"{args.lane} verification complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
