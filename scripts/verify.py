# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
#!/usr/bin/env python3
"""Run the maintained source verification lanes."""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from uuid import uuid4

if __package__:
    from scripts import package_input_policy, r_verification_support as r_support
    from scripts.desktop_partition import DESKTOP_SHARDS
    from scripts.verification_evidence import DEFAULT_BUILD_ROOT, PDF_TOOLS, VerificationError, configured_build_root, file_digest, run_typing
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts import package_input_policy
    import r_verification_support as r_support
    from desktop_partition import DESKTOP_SHARDS
    from verification_evidence import DEFAULT_BUILD_ROOT, PDF_TOOLS, VerificationError, configured_build_root, file_digest, run_typing


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
DEFAULT_R_LIBRARY_CACHE = REPO_ROOT / "artifacts" / "r-default-library-cache"
FULL_R_LIBRARY_CACHE = REPO_ROOT / "artifacts" / "r-library-cache"
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


def run_code_health(
    base: str, head: str = "HEAD", *, baseline: Path | None = None,
) -> None:
    command = [
        sys.executable, "scripts/code_health.py", "--base", base, "--head", head,
        "--output", "artifacts/code-health/final.json",
        "--report", "artifacts/code-health/final.txt",
    ]
    if baseline is not None:
        command.extend(("--baseline", str(baseline)))
    run(command)


def run_code_health_with_trend(
    base: str, head: str, baseline_revision: str, *, reuse_baseline: bool,
) -> None:
    baseline = Path("artifacts/code-health/baseline.json")
    report = baseline.with_suffix(".txt")
    cached = False
    if reuse_baseline and (REPO_ROOT / report).is_file():
        if __package__:
            from scripts.code_health import CodeHealthError, load_baseline
        else:
            from code_health import CodeHealthError, load_baseline

        try:
            cached = load_baseline(REPO_ROOT / baseline).get("head") == baseline_revision
        except CodeHealthError:
            pass
    if not cached:
        run(
            [
                sys.executable,
                "scripts/code_health.py",
                "--base",
                baseline_revision,
                "--head",
                baseline_revision,
                "--allow-fail",
                "--output",
                str(baseline),
                "--report",
                str(report),
            ]
        )
    run_code_health(base, head, baseline=baseline)


def run_packaging_contracts(env: dict[str, str] | None = None) -> None:
    run([sys.executable, "-m", "pytest", "-q", "tests/packaging/contract"], env=env)


def run_macos_packaging_contracts() -> None:
    run([
        sys.executable, "-m", "pytest", "-q",
        "tests/packaging/contract/test_macos_native_pipeline_contract.py",
        "tests/packaging/contract/test_macos_staple_retry_model.py",
    ])


def run_linux_source() -> None:
    env = prepare_qt_environment(REPO_ROOT / "build/qt6")
    run(["xvfb-run", "-a", sys.executable, "scripts/build_qt6.py", "native-smoke"], env=env)
    env["PYTHONPATH"] = str(REPO_ROOT)
    run([
        sys.executable, "-m", "pytest", "--strict-markers", "--confcutdir=tests/python/fast",
        "tests/python/fast/test_r_runtime.py::test_frozen_linux_r_home_requires_private_shared_library",
        "tests/python/fast/test_qt6_build_slice.py::test_linux_rcc_is_pinned_to_official_pyside6_version",
        "tests/python/fast/test_qt6_build_slice.py::test_linux_rcc_resolution_checks_selected_pyside_environment",
        "tests/python/fast/test_qt6_build_slice.py::test_native_linux_smoke_requires_xcb_and_x86_64",
        "tests/python/fast/test_qt6_build_slice.py::test_native_linux_smoke_selects_xcb",
    ], env=env)
    run([
        sys.executable, "-m", "pytest", "--strict-markers", "--confcutdir=tests/packaging/contract",
        "tests/packaging/contract/test_delivery_state_machine.py",
        "tests/packaging/contract/test_linux_distributable_contract.py",
    ], env=env)


def run_quick() -> None:
    build_root = configured_build_root(dict(os.environ))
    env = prepare_qt_environment(build_root)
    run_typing(build_root)
    preflight(env)
    run_pytest(
        ["-m", "not r_packages", "tests/python/fast"], env=env,
        workers=int(os.environ.get("RCMS_FAST_WORKERS", "4")),
    )
    run_packaging_contracts(env)
    run(["node", "--test", "tests/packaging/contract/release_actions.test.cjs"], env=env)


def ready_actions() -> dict[str, Callable[[], None]]:
    def verify(*args: str) -> None:
        run([sys.executable, "scripts/verify.py", *args])

    if sys.platform == "win32":
        return {
            package_input_policy.QT[0]: lambda: run(["powershell", "-File", "scripts/verify-qt6.ps1", "-Section", "Core"]),
            package_input_policy.QT[1]: lambda: run(["powershell", "-File", "scripts/verify-qt6.ps1", "-Section", "RemainingSurfaces"]),
            package_input_policy.SOURCE: lambda: verify("fast", "--skip-r-evidence"),
            package_input_policy.WINDOWS_PACKAGE: lambda: run(["powershell", "-File", "scripts/package-windows.ps1"]),
        }
    if sys.platform == "darwin":
        return {
            package_input_policy.SOURCE: lambda: verify("smoke", "--require-r-evidence"),
            "macos-package-qualification": lambda: run(["bash", "scripts/package-macos.sh", "--architecture", "arm64"]),
            "packaging-contract-macos": run_macos_packaging_contracts,
        }
    return {
        package_input_policy.SOURCE: run_linux_source,
        "linux-package-qualification": lambda: run(["bash", "scripts/package-linux.sh"]),
    }


def ready_desktop(part: str, scenarios: str, args: argparse.Namespace) -> None:
    command = [
        sys.executable, "scripts/verify_rcmetar_r_stack.py",
        "--rscript", selected_rscript(args),
        "--r-library-cache-root", str(args.r_library_cache_root or FULL_R_LIBRARY_CACHE),
    ]
    if part == "checks":
        command.append("--skip-desktop")
    else:
        command += ["--desktop-shard", part]
    if scenarios:
        command += ["--desktop-scenarios", scenarios]
    run(command)


def ready_toolchain(args: argparse.Namespace) -> dict[str, object]:
    env = dict(os.environ)
    rscript = r_support.resolve_rscript(selected_rscript(args))
    tools = [shutil.which(name) for name in ("git", "uv", "node", "bash", "powershell", "rcc", "xvfb-run", *PDF_TOOLS)]
    executables = {Path(path).resolve() for path in tools if path} | {Path(sys.executable).resolve()}
    if rscript:
        executables.add(rscript.resolve())
    return {
        "platform": platform.platform(),
        "python": sys.version,
        "distributions": sorted((d.metadata["Name"], d.version) for d in metadata.distributions()),
        "executables": {str(path): file_digest(path) for path in sorted(executables)},
        "r_version": subprocess.check_output([str(rscript), "--version"], stderr=subprocess.STDOUT, text=True).strip() if rscript else None,
        "environment": {key: value for key, value in env.items() if key.startswith(("RCMS_", "QT_", "R_", "LC_")) or key in {"PATH", "PYTHONPATH", "LANG"}},
    }


def ready_key(lane: str, selection: str, toolchain: dict[str, object]) -> str:
    identity = hashlib.sha256(json.dumps([lane, selection, toolchain], sort_keys=True).encode())
    if lane == "code-health" or lane in package_input_policy.PACKAGES:
        identity.update(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT))
    paths = package_input_policy.git_paths("ls-files", "-z", "--cached", "--others", "--exclude-standard")
    for name in sorted(set(paths)):
        path = REPO_ROOT / name
        if package_input_policy.lane_reads(name, lane) and path.is_file():
            identity.update(json.dumps([name, file_digest(path)]).encode())
    return identity.hexdigest()


def run_ready_lane(lane: str, selection: str, action: Callable[[], None], args: argparse.Namespace) -> None:
    if lane.startswith("desktop-"):
        action()
        return
    toolchain = ready_toolchain(args)
    key = ready_key(lane, selection, toolchain)
    cache = REPO_ROOT / "artifacts/verification/ready" / lane
    receipt = cache / f"{key}.json"
    record = json.dumps({"lane": lane, "inputs_sha256": key}) + "\n"
    if not args.full and receipt.is_file() and receipt.read_text(encoding="utf-8") == record:
        write_step(f"Reusing passed {lane}: {receipt}")
        return
    action()
    if ready_key(lane, selection, ready_toolchain(args)) == key:
        cache.mkdir(parents=True, exist_ok=True)
        temp = cache / f"{uuid4().hex}.tmp"
        temp.write_text(record, encoding="utf-8")
        temp.replace(receipt)
    else:
        write_step(f"Inputs changed while running {lane}. Result was not cached.")


def run_ready(args: argparse.Namespace) -> None:
    base = subprocess.check_output(["git", "merge-base", "origin/master", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    paths = package_input_policy.changed_paths(base, working_tree=True)
    paths += package_input_policy.git_paths("ls-files", "-z", "--others", "--exclude-standard")
    selected = package_input_policy.plan(paths, full="--full" if args.full else "")
    local = ready_actions()
    actions = [
        ("quick", "", "always", run_quick),
        ("code-health", base, "always, compares committed HEAD", lambda: run_code_health(base)),
    ]
    for job in selected.jobs:
        if job in local:
            actions.append((job, "", ", ".join(selected.reasons[job]), local[job]))
        elif job != package_input_policy.R:
            write_step(f"CI only on this host: {job} ({', '.join(selected.reasons[job])})")
    for part, scenarios in selected.parts.items():
        lane = "checks" if part == "checks" else f"desktop-{part}"
        reason = ", ".join(selected.reasons["checks" if part == "checks" else "desktop"])
        actions.append((lane, scenarios, reason, lambda part=part, scenarios=scenarios: ready_desktop(part, scenarios, args)))
    write_step(f"Ready plan against merge base {base}")
    for lane, selection, reason, _ in actions:
        detail = f" [{selection}]" if lane.startswith("desktop-") and selection else ""
        print(f"  {lane}{detail} - {reason}", flush=True)
    if not args.dry_run:
        for lane, selection, _, action in actions:
            run_ready_lane(lane, selection, action, args)


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
    subparsers.add_parser("quick", help="run the Windows quick CI checks")
    ready = subparsers.add_parser("ready", help="run quick checks and the lanes selected for your changes")
    ready.add_argument("--dry-run", action="store_true")
    ready.add_argument("--full", action="store_true")
    add_rscript_options(ready)
    return cli


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.lane == "smoke":
            run_source_lane(args, smoke=True)
        elif args.lane == "fast":
            run_source_lane(args, smoke=False)
        elif args.lane == "quick":
            run_quick()
        elif args.lane == "ready":
            run_ready(args)
        else:
            run_full_r_stack(args)
    except (VerificationError, r_support.RVerificationSupportError, subprocess.CalledProcessError) as exc:
        print(f"verification failed: {exc}", file=sys.stderr)
        return 1
    write_step(f"{args.lane} verification complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
