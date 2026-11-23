"""Verify RCMetaR as Full R Stack Evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

if __package__:
    from scripts import r_verification_support as r_support
    from scripts.desktop_partition import DESKTOP_SHARDS
    from scripts.verification_evidence import TYPING_RECEIPT_ENV, configured_build_root, file_digest, run_typing, tree_digest
else:
    import r_verification_support as r_support
    from desktop_partition import DESKTOP_SHARDS
    from verification_evidence import TYPING_RECEIPT_ENV, configured_build_root, file_digest, run_typing, tree_digest


RCMetaR_PACKAGE = Path("r") / "RCMetaR"
R_DEP_INSTALLER = Path("scripts") / "install-r-deps.R"
R_REITSMA_VISUAL_QA = Path("scripts") / "verify_reitsma_visual_qa.R"
R_MANIFEST_VALIDATOR = Path("scripts") / "validate_rcmetar_r_manifests.py"
REITSMA_VISUAL_CASE_COUNT = 21
REITSMA_VISUAL_DETERMINISTIC_EXTENSIONS = {"svg", "svgz", "png", "tif", "tiff"}


class VerificationError(Exception):
    pass


def step(message: str) -> None:
    print(f"[RCMetaR-r-stack] {message}", flush=True)




def run(
    command: list[str | Path], *, cwd: Path, env: dict[str, str] | None = None
) -> None:
    printable = " ".join(str(part) for part in command)
    step(printable)
    result = subprocess.run(
        [str(part) for part in command],
        cwd=cwd,
        env=env,
        text=True,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise VerificationError(
            f"command failed with exit code {result.returncode}: {printable}"
        )


def run_json(
    command: list[str | Path], *, cwd: Path, env: dict[str, str] | None = None
) -> dict:
    printable = " ".join(str(part) for part in command)
    step(printable)
    result = subprocess.run(
        [str(part) for part in command],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        output = result.stderr.strip() or result.stdout.strip()
        raise VerificationError(
            f"command failed with exit code {result.returncode}: {printable}\n{output}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise VerificationError(
            f"command did not emit JSON: {printable}\n{result.stdout}"
        ) from exc


def resolve_rscript(name: str, env: dict[str, str] | None = None) -> Path:
    resolved = r_support.resolve_rscript(name, env)
    if resolved is None:
        raise VerificationError(f"Rscript was not found: {name}")
    return resolved


def isolated_r_env(
    base_env: dict[str, str], library: Path, r_home: Path | None = None
) -> dict[str, str]:
    env = dict(base_env)
    env["R_LIBS"] = str(library)
    env["R_LIBS_USER"] = str(library)
    env["RCMS_R_LIBS"] = str(library)
    if r_home is not None:
        env["R_HOME"] = str(r_home)
        env["RCMS_R_HOME"] = str(r_home)
        r_path_entries = [r_home / "bin"]
        if os.name == "nt":
            r_path_entries.insert(0, r_home / "bin" / "x64")
        env["PATH"] = os.pathsep.join(
            [*(str(path) for path in r_path_entries), env.get("PATH", "")]
        )
    env.setdefault("_R_CHECK_FORCE_SUGGESTS_", "false")
    return env


def copy_library(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def ensure_dependency_library(
    root: Path,
    rscript: Path,
    env: dict[str, str],
    python: str,
    cran_repo: str,
    cache_root: Path,
    work_dir: Path,
) -> Path:
    cache_library = (
        cache_root
        / r_support.dependency_cache_key(root, rscript, env, cran_repo, R_DEP_INSTALLER, "rdeps")
        / "library"
    )
    if cache_library.exists():
        try:
            cache_env = isolated_r_env(env, cache_library)
            cache_env["RCMS_CRAN_REPO"] = cran_repo
            cache_env["RCMS_POLICY_PYTHON"] = python
            verify_manifest_versions(root, python, rscript, cache_env)
            verify_dependency_closure(root, rscript, cache_env)
            step(f"Using cached R dependency library at {cache_library}")
        except (VerificationError, r_support.RVerificationSupportError):
            shutil.rmtree(cache_library)
        else:
            r_library = work_dir / "library"
            copy_library(cache_library, r_library)
            return r_library

    cache_library.mkdir(parents=True, exist_ok=True)
    cache_env = isolated_r_env(env, cache_library)
    cache_env["RCMS_CRAN_REPO"] = cran_repo
    cache_env["RCMS_POLICY_PYTHON"] = python
    step(f"Installing R dependencies into cache library at {cache_library}")
    run([rscript, R_DEP_INSTALLER], cwd=root, env=cache_env)
    verify_manifest_versions(root, python, rscript, cache_env)

    r_library = work_dir / "library"
    copy_library(cache_library, r_library)
    return r_library


def verify_dependency_closure(root: Path, rscript: Path, env: dict[str, str]) -> None:
    # Search only the target and the selected R's own runtime packages. Never
    # let an ambient site library fill a hole in the copied dependency cache.
    expression = """
    target <- Sys.getenv("R_LIBS")
    .libPaths(c(target, .Library), include.site=FALSE)
    local <- installed.packages(lib.loc=target)
    runtime <- installed.packages(lib.loc=.Library)
    runtime <- runtime[!is.na(runtime[, "Priority"]), , drop=FALSE]
    db <- rbind(local, runtime[!rownames(runtime) %in% rownames(local), , drop=FALSE])
    roots <- commandArgs(trailingOnly=TRUE)
    closure <- unique(c(roots, unlist(tools::package_dependencies(
      roots, db=db, which=c("Depends", "Imports", "LinkingTo"), recursive=TRUE))))
    missing <- setdiff(closure, c(rownames(local), rownames(runtime), "R"))
    if (length(missing)) stop(paste("Target-local closure missing:", paste(missing, collapse=", ")))
    for (package in roots) loadNamespace(package, lib.loc=c(target, .Library))
    cat("Target-local dependency closure verified:", length(closure), "packages\n")
    """
    with tempfile.TemporaryDirectory(prefix="rcms-closure-") as temporary:
        script = Path(temporary) / "closure.R"
        script.write_text(expression, encoding="utf-8")
        run([rscript, "--vanilla", script, *r_support.load_binary_dependency_policy(root)["normal_packages"]], cwd=root, env=env)


def built_RCMetaR_tarball(work_dir: Path) -> Path:
    tarballs = sorted(
        work_dir.glob("RCMetaR_*.tar.gz"), key=lambda path: path.stat().st_mtime
    )
    if not tarballs:
        raise VerificationError(
            f"R CMD build did not create an RCMetaR tarball in {work_dir}"
        )
    return tarballs[-1]


def verify_manifest_versions(
    root: Path, python: str, rscript: Path, env: dict[str, str]
) -> None:
    report = run_json(
        [
            python,
            R_MANIFEST_VALIDATOR,
            "--root",
            root,
            "--report-installed-versions",
            "--rscript",
            rscript,
        ],
        cwd=root,
        env=env,
    )
    missing = sorted(
        name for name, version in report["packages"].items() if version is None
    )
    if missing:
        raise VerificationError(
            "manifest dependency packages are not installed: " + ", ".join(missing)
        )
    manifest = json.loads(
        (root / "config/r-dependencies.json").read_text(encoding="utf-8")
    )
    if report.get("r_version") != manifest["target_runtime"]["r"]:
        raise VerificationError(
            f"R runtime mismatch: expected {manifest['target_runtime']['r']}, observed {report.get('r_version')}"
        )
    exact_versions = {
        dependency["name"]: dependency["installed_version"]
        for dependency in manifest["direct_RCMetaR_dependencies"]
        if dependency.get("source") in {"cran", "cran-archive"}
        and dependency.get("installed_version") not in {None, "latest-compatible"}
    }
    wrong_versions = {
        name: {"expected": expected, "actual": report["packages"].get(name)}
        for name, expected in exact_versions.items()
        if report["packages"].get(name) != expected
    }
    if wrong_versions:
        raise VerificationError(
            "manifest dependency versions do not match: "
            + json.dumps(wrong_versions, sort_keys=True)
        )
    step(
        "Manifest dependency versions are installed: "
        + json.dumps(report, sort_keys=True)
    )


def _read_reitsma_visual_manifest(root: Path) -> tuple[list[dict[str, str]], dict]:
    manifest_path = root / "manifest.csv"
    descriptor_path = root / "descriptor-contract.json"
    if not manifest_path.is_file() or not descriptor_path.is_file():
        raise VerificationError(
            "Reitsma visual QA did not produce its manifest and descriptor contract"
        )
    with manifest_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    try:
        descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VerificationError("Reitsma descriptor contract is not valid JSON") from exc
    if len(rows) != REITSMA_VISUAL_CASE_COUNT:
        raise VerificationError(
            f"Reitsma visual QA expected {REITSMA_VISUAL_CASE_COUNT} cases, observed {len(rows)}"
        )
    if len({row.get("case", "") for row in rows}) != REITSMA_VISUAL_CASE_COUNT:
        raise VerificationError("Reitsma visual QA manifest contains duplicate case identifiers")
    required = {
        "case", "family", "kind", "workflow", "style", "scenario", "extension",
        "image", "bytes", "sha256", "pdf_contract", "error",
    }
    if any(not required.issubset(row) for row in rows):
        raise VerificationError("Reitsma visual QA manifest is missing release contract columns")
    failures = [
        row["case"]
        for row in rows
        if row.get("error", "").strip() not in {"", "NA"}
    ]
    if failures:
        raise VerificationError("Reitsma visual QA failures: " + ", ".join(failures))
    for row in rows:
        image = Path(row["image"])
        if not image.is_file() or int(float(row["bytes"])) <= 1000:
            raise VerificationError(f"Reitsma visual QA artifact is missing or empty: {row['case']}")
        extension = row["extension"].lower()
        if extension in REITSMA_VISUAL_DETERMINISTIC_EXTENSIONS and len(row["sha256"]) != 64:
            raise VerificationError(f"Missing deterministic hash for Reitsma case: {row['case']}")
        if extension == "pdf":
            try:
                contract = json.loads(row["pdf_contract"])
            except json.JSONDecodeError as exc:
                raise VerificationError(f"Invalid PDF contract for Reitsma case: {row['case']}") from exc
            if (
                contract.get("signature") != "%PDF-"
                or contract.get("pages") != 1
                or contract.get("has_xref_or_xref_stream") is not True
                or contract.get("has_eof") is not True
            ):
                raise VerificationError(f"PDF semantic contract failed for Reitsma case: {row['case']}")
    if descriptor.get("schema_version") != 1 or set(descriptor.get("descriptors", {})) != {
        "sroc", "coefficient_forest"
    }:
        raise VerificationError("Reitsma descriptor contract has unexpected coverage")
    return rows, descriptor


def verify_reitsma_visual_evidence(
    root: Path, rscript: Path, env: dict[str, str], work_dir: Path
) -> None:
    """Run and compare the maintained 21-case visual release harness twice.

    Raster/SVG outputs are deterministic release artifacts and must retain
    stable SHA-256 values. PDFs are intentionally checked through their
    normalized semantic contract because producers may embed timestamps.
    """
    # The release gate must exercise the package that was just built and
    # installed above.  The visual script deliberately supports a source mode
    # for local development, but this integrated gate must never silently fall
    # back to pkgload::load_all() from the workspace.
    visual_env = dict(env)
    visual_env["RCMS_REITSMA_VISUAL_QA_MODE"] = "installed"
    visual_env["RCMS_REITSMA_VISUAL_QA_LIBRARY"] = env["R_LIBS"]
    evidence = []
    for index in (1, 2):
        output = work_dir / f"reitsma-visual-qa-{index}"
        output.mkdir(parents=True, exist_ok=True)
        run([rscript, R_REITSMA_VISUAL_QA, output], cwd=root, env=visual_env)
        evidence.append(_read_reitsma_visual_manifest(output))
    first_rows, first_descriptor = evidence[0]
    second_rows, second_descriptor = evidence[1]
    if first_descriptor != second_descriptor:
        raise VerificationError("Reitsma normalized descriptor contract is not deterministic")
    first_by_case = {row["case"]: row for row in first_rows}
    second_by_case = {row["case"]: row for row in second_rows}
    if set(first_by_case) != set(second_by_case):
        raise VerificationError("Reitsma visual QA case inventory changed between runs")
    for case, first in first_by_case.items():
        second = second_by_case[case]
        extension = first["extension"].lower()
        if extension in REITSMA_VISUAL_DETERMINISTIC_EXTENSIONS and first["sha256"] != second["sha256"]:
            raise VerificationError(f"Reitsma deterministic visual hash drifted: {case}")
        if extension == "pdf" and first["pdf_contract"] != second["pdf_contract"]:
            raise VerificationError(f"Reitsma PDF semantic contract drifted: {case}")
    step("Reitsma visual release evidence verified: 21 cases, deterministic hashes and normalized PDF/descriptor contracts")


def verify_analysis_authorities(root: Path, rscript: Path, env: dict[str, str]) -> None:
    report = root / "artifacts/verification/rcms/authorities.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.unlink(missing_ok=True)
    started = time.monotonic()
    run(
        [rscript, root / ".agents/skills/verify-rcms/scripts/analysis_authorities.R",
         report, "--installed"],
        cwd=root, env=env,
    )
    result = json.loads(report.read_text(encoding="utf-8"))
    cases = result["cases"]
    if not cases or not all(case["passed"] for case in cases):
        raise VerificationError("Statistical authority matrix contains failed or missing cases")
    step(f"Statistical authorities verified: {len(cases)} cases passed "
         f"in {time.monotonic() - started:.2f}s")


def build_stack_source(
    source: Path, r_exe: Path, env: dict[str, str], work_dir: Path
) -> Path:
    run([r_exe, "CMD", "build", "--no-build-vignettes", source], cwd=work_dir, env=env)
    return built_RCMetaR_tarball(work_dir)


def source_install_key(source: Path, env: dict[str, str]) -> str:
    startup_files = [source.parent.parent / name for name in (".Renviron", ".Rprofile")]
    for variable, default in (("R_ENVIRON_USER", ".Renviron"), ("R_PROFILE_USER", ".Rprofile")):
        startup_files.append(Path(env.get(variable) or Path.home() / default))
    startup_files.extend(Path(env[name]) for name in ("R_ENVIRON", "R_PROFILE") if env.get(name))
    # The dependency library is a private copy. Its bytes, not its path, identify it.
    settings = {
        name: value for name, value in env.items()
        if name not in {"R_LIBS", "R_LIBS_USER"}
        and (name.startswith(("R_", "_R_", "LC_")) or name in {"LANG", "PATH", "TZ"})
    }
    inputs = (
        tree_digest(source),
        tree_digest(Path(env["R_HOME"])),
        tree_digest(Path(env["R_LIBS"])),
        file_digest(Path(__file__)),
        {str(path): file_digest(path) for path in startup_files if path.is_file()},
        settings,
    )
    return hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()


def install_stack_source(
    root: Path, r_exe: Path, env: dict[str, str], work_dir: Path, cache_root: Path
) -> Path:
    source = root / RCMetaR_PACKAGE
    library = Path(env["R_LIBS"])
    # A package with build hooks or native code also depends on the host compiler
    # and tools. RCMetaR is pure R, so keep those builds on the uncached path.
    if any((source / name).exists() for name in ("src", "configure", "configure.win", "cleanup", "cleanup.win")):
        tarball = build_stack_source(source, r_exe, env, work_dir)
        run([r_exe, "CMD", "INSTALL", f"--library={library}", tarball], cwd=root, env=env)
        return tarball

    source_cache = cache_root / "source"
    source_cache.mkdir(parents=True, exist_ok=True)
    key = source_install_key(source, env)
    entry = source_cache / key
    if not entry.is_dir():
        with tempfile.TemporaryDirectory(prefix="install-", dir=source_cache) as temporary:
            staging = Path(temporary) / "entry"
            staging.mkdir()
            tarball = build_stack_source(source, r_exe, env, staging)
            run([r_exe, "CMD", "INSTALL", f"--library={staging}", tarball], cwd=root, env=env)
            if source_install_key(source, env) != key:
                raise VerificationError("RCMetaR installation inputs changed during the build")
            try:
                staging.rename(entry)
            except OSError:
                if not entry.is_dir():
                    raise
    else:
        step(f"Using cached RCMetaR installation at {entry}")
    copy_library(entry / "RCMetaR", library / "RCMetaR")
    return built_RCMetaR_tarball(entry)


def prepare_stack_library(
    args: argparse.Namespace, root: Path, rscript: Path, base_env: dict[str, str],
    python: str, cran_repo: str, work_dir: Path,
) -> dict[str, str]:
    bootstrap_library = work_dir / "bootstrap-library"
    bootstrap_library.mkdir(parents=True)
    env = isolated_r_env(base_env, bootstrap_library)
    r_home = r_support.resolve_r_home(rscript, root, env)
    env = isolated_r_env(base_env, bootstrap_library, r_home)
    r_exe = r_support.resolve_r_exe(rscript, root, env)
    cache_root = (args.r_library_cache_root or root / "artifacts/r-library-cache").resolve()
    prepared = args.prepared_r_library.resolve() if args.prepared_r_library else None
    if prepared is None:
        r_library = ensure_dependency_library(
            root, rscript, env, python, cran_repo, cache_root, work_dir
        )
    else:
        r_library = prepared / "dependencies/library"
        copy_library(prepared / "source/RCMetaR", r_library / "RCMetaR")
    env = isolated_r_env(base_env, r_library, r_home)
    env["RCMS_CRAN_REPO"] = cran_repo

    step(f"Using isolated R verification library at {r_library}")

    if prepared is None:
        tarball = install_stack_source(root, r_exe, env, work_dir, cache_root)
    else:
        tarball = built_RCMetaR_tarball(prepared / "source")
        verify_manifest_versions(root, python, rscript, env)
        verify_dependency_closure(root, rscript, env)
    if args.desktop_shard is None:
        run(
            [
                r_exe,
                "CMD",
                "check",
                "--no-manual",
                "--no-build-vignettes",
                f"--library={r_library}",
                tarball,
            ],
            cwd=work_dir,
            env=env,
        )
    return env


def verify(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    if __package__:
        from scripts import verify as source_verifier
    else:
        import verify as source_verifier
    build_root = configured_build_root(dict(os.environ))
    prepared_env = source_verifier.prepare_qt_environment(build_root)
    receipt = run_typing(build_root)
    python = (
        str(Path(args.python).absolute()) if Path(args.python).exists() else args.python
    )
    rscript = resolve_rscript(args.rscript)
    base_env = r_support.verification_base_env(prepared_env)
    base_env[TYPING_RECEIPT_ENV] = str(receipt)
    base_env["RCMS_RSCRIPT"] = str(rscript)
    cran_repo = r_support.configure_binary_repository(root, base_env, python, args.cran_repo)


    run([python, R_MANIFEST_VALIDATOR, "--root", root], cwd=root, env=base_env)

    work_dir_parent = args.work_dir.resolve() if args.work_dir else None
    if work_dir_parent is not None:
        work_dir_parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="RCMetaR-r-stack-", dir=work_dir_parent
    ) as temp_name:
        work_dir = Path(temp_name)
        env = prepare_stack_library(args, root, rscript, base_env, python, cran_repo, work_dir)

        env["RCMS_R_STACK_REQUIRED"] = "1"
        if args.desktop_shard is None:
            verify_analysis_authorities(root, rscript, env)
            verify_manifest_versions(root, python, rscript, env)
            verify_reitsma_visual_evidence(root, rscript, env, work_dir)

            run([python, "-m", "pytest", "tests/r_stack",
                 "tests/python/fast/test_packaged_summary_identity.py"], cwd=root, env=env)
        # Fresh offscreen children can overlap within the measured memory budget.
        # The E2E hook reserves host capacity; native drives remain separate/serial.
        desktop_command = [
            python, "-m", "pytest", "tests/e2e", "-n", args.desktop_workers,
            "-q", "--durations=10",
        ]
        if args.fresh:
            desktop_command.append("--fresh")
        if args.desktop_shard is not None:
            desktop_command += [
                "--desktop-shard", str(args.desktop_shard),
                "--shard-report", "artifacts/verification/desktop-partition.json",
                "--junitxml=artifacts/verification/desktop-results.xml",
            ]
        if args.desktop_scenarios:
            desktop_command += ["--desktop-scenarios", args.desktop_scenarios]
        if not args.skip_desktop:
            run(desktop_command, cwd=root, env=env)
        if args.desktop_shard is None:
            run(
                [
                    python,
                    "scripts/verify_golden_compatibility.py",
                    "--root",
                    root,
                    "--output-root",
                    "build/qt6-verification/golden-compatibility-r-stack-v2",
                ],
                cwd=root,
                env=env,
            )
        if args.doctor:
            run([python, "scripts/verify_rcms.py", "doctor"], cwd=root, env=env)

    step("RCMetaR R Stack Slice verification complete")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doctor", action="store_true", help="check app startup with the verified R library")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument("--desktop-workers", default="auto")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--skip-desktop", action="store_true")
    selection.add_argument("--desktop-shard", type=int, choices=DESKTOP_SHARDS)
    parser.add_argument("--desktop-scenarios", help="comma-separated selection within a desktop shard")
    parser.add_argument("--fresh", action="store_true", help="Do not reuse passed desktop evidence")
    parser.add_argument("--work-dir", type=Path, default=None)
    parser.add_argument("--r-library-cache-root", type=Path, default=None)
    parser.add_argument("--prepared-r-library", type=Path)
    parser.add_argument("--cran-repo", default=None)
    args = parser.parse_args(argv)
    if args.desktop_scenarios and args.desktop_shard is None:
        parser.error("--desktop-scenarios requires --desktop-shard")
    return args


def main(argv: list[str] | None = None) -> int:
    try:
        verify(parse_args(argv))
    except (VerificationError, r_support.RVerificationSupportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
