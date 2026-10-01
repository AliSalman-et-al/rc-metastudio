#!/usr/bin/env python3
"""Capture direct RCMetaR package API outputs against a pinned R library."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import sys
from zipfile import ZipFile, ZipInfo

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from tests.analysis_regression.golden.support.release_source_v031_package import (  # noqa: E402
    AUTHORITY_SCOPE,
    CAPTURE_KIND,
    CASE_SPEC_PATH,
    HISTORICAL_EXE_EXPECTED_SUMMARY_SHA256,
    HISTORICAL_EXE_SAMPLE,
    HISTORICAL_EXE_SMOKE_SCOPE,
    RELEASE,
    VERSIONS,
    _artifact_identity,
    canonical_sha256,
    load_case_specs,
    _validate_historical_exe_smoke,
    validate_package_manifest,
)

R_CAPTURE = REPOSITORY_ROOT / "scripts/capture_v031_package_reference.R"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=("release-reference", "candidate-replay"))
    parser.add_argument("--rscript", required=True, type=Path)
    parser.add_argument("--library", required=True, type=Path, help="R library containing RCMetaR")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--case-spec", type=Path, default=CASE_SPEC_PATH)
    parser.add_argument("--archive-root", type=Path, help="Extracted RCMetaStudio-0.3.1-windows-x64 directory")
    parser.add_argument("--archive", type=Path, help="Downloaded published release ZIP")
    parser.add_argument(
        "--historical-executable-smoke",
        dest="automation_smoke",
        action="store_true",
        help="Also run the verified published RCMetaStudio.exe --automation-smoke entry point.",
    )
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left.resolve())) == os.path.normcase(str(right.resolve()))


def contained_path(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def verify_release_inputs(args):
    if args.role == "release-reference":
        return _verify_release_archive_inputs(args)
    if args.archive is not None or args.archive_root is not None:
        raise ValueError("Archive inputs are only valid for a release-reference capture.")
    return None


def _verify_release_archive_inputs(args):
    if args.archive is None or args.archive_root is None:
        raise ValueError("Release-reference capture requires the archive and extracted archive root.")
    archive = args.archive.resolve(strict=True)
    app_root = args.archive_root.resolve(strict=True)
    _validate_release_archive_identity(archive, app_root)
    _verify_extracted_runtime(archive, app_root)

    r_home, rscript, library = _embedded_runtime_paths(app_root)
    if not same_path(args.rscript, rscript) or not same_path(args.library, library):
        raise ValueError("Rscript and RCMetaR library must be the ones embedded in the verified archive.")
    _require_embedded_files((app_root / "RCMetaStudio.exe", rscript, library / "RCMetaR" / "DESCRIPTION"))
    return r_home.resolve()


def _validate_release_archive_identity(archive: Path, app_root: Path):
    if not archive.is_file():
        raise ValueError("The pinned release archive path is not a file.")
    if app_root.name != RELEASE["archive_internal_root"]:
        raise ValueError("The extracted archive root does not match the pinned archive layout.")
    observed = file_sha256(archive)
    if observed != RELEASE["asset_sha256"]:
        raise ValueError(
            "Published archive SHA-256 mismatch: expected %s, got %s."
            % (RELEASE["asset_sha256"], observed)
        )


def _verify_extracted_runtime(archive: Path, app_root: Path):
    archive_prefix = app_root.name + "/"
    runtime_prefix = archive_prefix + "R/"
    with ZipFile(archive) as zip_file:
        expected = _runtime_archive_members(zip_file, runtime_prefix, archive_prefix)
        extracted = _runtime_files(app_root)
        if set(expected) != set(extracted):
            raise ValueError("Extracted embedded R tree does not match the pinned ZIP file inventory.")
        for relative, member in expected.items():
            if not _zip_member_matches(zip_file, member, extracted[relative]):
                raise ValueError("Extracted embedded R file differs from pinned ZIP: %s" % relative)


def _verify_extracted_archive_file(archive: Path, app_root: Path, relative_path: str):
    relative = PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Pinned archive member path must remain inside the archive root.")
    archive_name = app_root.name + "/" + relative.as_posix()
    path = app_root.joinpath(*relative.parts)
    if not path.is_file():
        raise ValueError("Published archive is missing required file: %s" % relative_path)
    with ZipFile(archive) as zip_file:
        member = _required_archive_file(zip_file, archive_name)
        if not _zip_member_matches(zip_file, member, path):
            raise ValueError("Extracted file differs from pinned ZIP: %s" % relative_path)


def _required_archive_file(zip_file: ZipFile, archive_name: str) -> ZipInfo:
    matching = [item for item in zip_file.infolist() if item.filename == archive_name]
    if len(matching) != 1 or matching[0].is_dir():
        raise ValueError("Pinned archive does not contain one file at %s." % archive_name)
    return matching[0]


def _runtime_archive_members(zip_file: ZipFile, runtime_prefix: str, archive_prefix: str):
    expected = {}
    for member in zip_file.infolist():
        if member.is_dir() or not member.filename.startswith(runtime_prefix):
            continue
        relative = PurePosixPath(member.filename[len(archive_prefix):])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Pinned archive contains an invalid embedded R path.")
        name = relative.as_posix()
        if name in expected:
            raise ValueError("Pinned archive repeats an embedded R path: %s" % name)
        expected[name] = member
    if not expected:
        raise ValueError("Pinned archive contains no embedded R runtime files.")
    return expected


def _runtime_files(app_root: Path):
    runtime_root = app_root / "R"
    files = {}
    for path in runtime_root.rglob("*"):
        if path.is_symlink():
            raise ValueError("Extracted embedded R tree contains a symbolic link.")
        if path.is_file():
            files[path.relative_to(app_root).as_posix()] = path
    return files


def _zip_member_matches(zip_file: ZipFile, member: ZipInfo, path: Path):
    if path.stat().st_size != member.file_size:
        return False
    with zip_file.open(member) as archived, path.open("rb") as extracted:
        while True:
            expected = archived.read(1024 * 1024)
            observed = extracted.read(1024 * 1024)
            if expected != observed:
                return False
            if not expected:
                return True


def _embedded_runtime_paths(app_root: Path):
    r_home = app_root / "R"
    rscript = r_home / "bin" / "Rscript.exe"
    library = r_home / "library"
    return r_home, rscript, library


def _require_embedded_files(paths):
    for required in paths:
        if not required.is_file():
            raise ValueError("Published archive is missing required file: %s" % required)


def read_raw_capture(path: Path, role: str):
    raw = json.loads(path.read_text(encoding="utf-8"))
    _validate_raw_envelope(raw, role)
    _validate_raw_versions(raw, role)
    _validate_raw_runtime(raw)
    return raw


def _validate_raw_envelope(raw, role):
    if not isinstance(raw, dict) or set(raw) != {
        "schema_version", "capture_role", "versions", "runtime", "cases"
    }:
        raise ValueError("R capture output fields do not match schema v1.")
    if raw["schema_version"] != 1 or raw["capture_role"] != role:
        raise ValueError("R capture output version or role changed.")


def _validate_raw_versions(raw, role):
    if not isinstance(raw["versions"], dict) or set(raw["versions"]) != set(VERSIONS):
        raise ValueError("R capture did not report the pinned package-version tuple fields.")
    if role == "release-reference" and raw["versions"] != VERSIONS:
        raise ValueError("R capture package versions do not match the published release pins.")


def _validate_raw_runtime(raw):
    if not isinstance(raw["runtime"], dict) or set(raw["runtime"]) != {
        "r_home", "rcmetar_path", "runner_os", "runner_arch"
    }:
        raise ValueError("R capture runtime provenance fields changed.")


def artifact_descriptors(raw_artifacts, spec, output_dir: Path):
    if not isinstance(raw_artifacts, list):
        raise ValueError("R capture artifacts must be an ordered list.")
    artifacts = [_capture_artifact(raw, output_dir) for raw in raw_artifacts]
    identities = [_artifact_identity_fields(item) for item in artifacts]
    if identities != _artifact_identity(spec["id"], spec):
        raise ValueError("R capture artifact inventory did not match the requested case.")
    return artifacts


def _capture_artifact(raw, output_dir: Path):
    fields = {"name", "plot_kind", "format", "relative_path"}
    if not isinstance(raw, dict) or set(raw) != fields:
        raise ValueError("R capture artifact descriptor fields changed.")
    relative = PurePosixPath(raw["relative_path"])
    path = _resolve_capture_artifact(relative, output_dir)
    size = path.stat().st_size
    if size <= 0:
        raise ValueError("R capture artifact is empty: %s" % relative.as_posix())
    return {
        **{key: raw[key] for key in ("name", "plot_kind", "format", "relative_path")},
        "sha256": file_sha256(path),
        "size_bytes": size,
    }


def _resolve_capture_artifact(relative: PurePosixPath, output_dir: Path):
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("R capture artifact path must remain inside its output directory.")
    path = output_dir.joinpath(*relative.parts).resolve(strict=True)
    if not contained_path(path, output_dir) or not path.is_file():
        raise ValueError("R capture artifact escaped its output directory.")
    return path


def _artifact_identity_fields(item):
    return {key: item[key] for key in ("name", "plot_kind", "format", "relative_path")}


def build_manifest(raw, specs, role, output_dir, archive_root=None, historical_exe_smoke=None):
    raw_cases = raw["cases"]
    _validate_capture_case_order(raw_cases, specs)
    cases = [
        _build_case_manifest(item, spec, output_dir)
        for spec, item in zip(specs["cases"], raw_cases)
    ]
    environment = _manifest_environment(raw["runtime"], role, archive_root)

    repository = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    run_url = (
        "%s/%s/actions/runs/%s"
        % (os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/"), repository, run_id)
        if repository and run_id
        else None
    )
    manifest = {
        "schema_version": 2,
        "capture_kind": CAPTURE_KIND,
        "authority_scope": AUTHORITY_SCOPE,
        "capture_role": role,
        "release": RELEASE,
        "versions": raw["versions"],
        "environment": environment,
        "workflow": {
            "repository": repository,
            "workflow_ref": os.environ.get("GITHUB_WORKFLOW_REF"),
            "source_sha": os.environ.get("GITHUB_SHA"),
            "run_id": run_id,
            "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
            "run_url": run_url,
        },
        "case_ids": specs["case_ids"],
        "cases": cases,
        "historical_exe_smoke": historical_exe_smoke,
    }
    validate_package_manifest(manifest)
    return manifest


def _validate_capture_case_order(raw_cases, specs):
    if not isinstance(raw_cases, list):
        raise ValueError("R capture case inventory is missing, duplicated, or out of order.")
    observed_ids = [item.get("id") for item in raw_cases if isinstance(item, dict)]
    if len(observed_ids) != len(raw_cases) or observed_ids != specs["case_ids"]:
        raise ValueError("R capture case inventory is missing, duplicated, or out of order.")


def _build_case_manifest(item, spec, output_dir):
    fields = {
        "id", "status", "effective_request", "eligibility", "warnings", "outputs", "artifacts"
    }
    if not isinstance(item, dict) or set(item) != fields:
        raise ValueError("R capture case output fields changed.")
    request = {key: spec[key] for key in ("family", "metric", "method", "workflow")}
    request["params"] = spec["params"]
    if item["status"] != "success":
        raise ValueError("R package API case did not complete successfully: %s" % spec["id"])
    result = {
        "id": spec["id"],
        "family": spec["family"],
        "metric": spec["metric"],
        "method": spec["method"],
        "workflow": spec["workflow"],
        "request": request,
        "effective_request": item["effective_request"],
        "input": spec["input"],
        "input_sha256": canonical_sha256(spec["input"]),
        "request_sha256": canonical_sha256(request),
        "ordered_input_studies": spec["input"]["study_names"],
        "status": item["status"],
        "eligibility": item["eligibility"],
        "warnings": item["warnings"],
        "outputs": item["outputs"],
        "artifacts": artifact_descriptors(item["artifacts"], spec, output_dir),
    }
    if "journey" in spec:
        result["journey"] = spec["journey"]
    return result


def _manifest_environment(runtime, role, archive_root):
    confirmed = _embedded_runtime_confirmed(runtime, role, archive_root)
    return {
        "runner_os": runtime["runner_os"] or platform.system(),
        "runner_arch": runtime["runner_arch"] or os.environ.get("PROCESSOR_ARCHITECTURE") or platform.machine(),
        "embedded_r_home_confirmed": confirmed,
        "embedded_rcmetar_library_confirmed": confirmed,
        "release_archive_sha256_verified": confirmed,
    }


def _embedded_runtime_confirmed(runtime, role, archive_root):
    if role != "release-reference":
        return False
    if archive_root is None:
        raise ValueError("Release-reference manifest requires the verified archive root.")
    r_home = archive_root.resolve(strict=True) / "R"
    if not same_path(Path(runtime["r_home"]), r_home):
        raise ValueError("R resolved an R_HOME outside the verified archive.")
    if not same_path(Path(runtime["rcmetar_path"]), r_home / "library" / "RCMetaR"):
        raise ValueError("R loaded RCMetaR from outside the verified archive library.")
    return True


def capture(args):
    archive_r_home = verify_release_inputs(args)
    _validate_capture_options(args)
    rscript, library, case_spec, output_dir = _capture_paths(args)
    _prepare_capture_output(output_dir)
    smoke = _capture_optional_exe_smoke(args, output_dir)
    specs = _load_capture_specs(case_spec)
    raw = _run_package_capture(
        rscript, library, case_spec, output_dir, args.role, archive_r_home
    )
    manifest = build_manifest(
        raw,
        specs,
        args.role,
        output_dir,
        args.archive_root if args.role == "release-reference" else None,
        smoke,
    )
    return _write_capture_manifest(manifest, output_dir)


def _validate_capture_options(args):
    if args.automation_smoke and args.role != "release-reference":
        raise ValueError("The historical executable smoke is only available for a release-reference capture.")


def _capture_paths(args):
    rscript = args.rscript.resolve(strict=True)
    library = args.library.resolve(strict=True)
    case_spec = args.case_spec.resolve(strict=True)
    output_dir = args.output_dir.resolve()
    return rscript, library, case_spec, output_dir


def _prepare_capture_output(output_dir: Path):
    if output_dir.exists():
        raise ValueError("Capture output directory already exists: %s" % output_dir)
    output_dir.mkdir(parents=True)
    (output_dir / "artifacts").mkdir()


def _load_capture_specs(case_spec: Path):
    specs = json.loads(case_spec.read_text(encoding="utf-8"))
    if not isinstance(specs, dict) or specs != load_case_specs():
        raise ValueError("Case specification schema mismatch.")
    return specs


def _run_package_capture(rscript, library, case_spec, output_dir, role, archive_r_home):
    environment = os.environ.copy()
    environment["RCMS_PACKAGE_LIBRARY"] = str(library)
    environment["RCMS_CAPTURE_ROLE"] = role
    environment["RCMS_CAPTURE_CASE_SPEC"] = str(case_spec)
    environment["RCMS_CAPTURE_OUTPUT_DIR"] = str(output_dir)
    if archive_r_home is not None:
        environment["RCMS_EXPECTED_R_HOME"] = str(archive_r_home)
        environment["R_HOME"] = str(archive_r_home)
        environment["R_LIBS"] = str(library)
        environment["R_LIBS_USER"] = str(library)

    command = [str(rscript), "--vanilla", str(R_CAPTURE.resolve())]
    result = subprocess.run(command, env=environment, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            "R package API capture failed (exit %d).\n%s\n%s"
            % (result.returncode, result.stdout, result.stderr)
        )
    return read_raw_capture(output_dir / "capture-raw.json", role)


def _capture_optional_exe_smoke(args, output_dir):
    if not args.automation_smoke:
        return None
    smoke = capture_historical_exe_smoke(
        args.archive.resolve(strict=True),
        args.archive_root.resolve(strict=True),
        output_dir,
    )
    _validate_historical_exe_smoke(smoke, windows_provenance=True)
    result_path = output_dir / "historical-exe-smoke" / "result.json"
    result_path.write_text(
        json.dumps(smoke, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return smoke


def _write_capture_manifest(manifest, output_dir):
    destination = output_dir / "manifest.json"
    temporary = output_dir / "manifest.json.tmp"
    temporary.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)
    (output_dir / "capture-raw.json").unlink()
    return destination


def capture_historical_exe_smoke(
    archive: Path,
    archive_root: Path,
    output_dir: Path,
    *,
    timeout_seconds: int = 900,
):
    """Record the pinned executable's existing automation entry point without patching it."""
    executable, sample = _verified_smoke_inputs(archive, archive_root)
    smoke_dir = output_dir / "historical-exe-smoke"
    smoke_dir.mkdir(parents=True, exist_ok=False)
    evidence_path = smoke_dir / "smoke-evidence.json"
    log_path = smoke_dir / "automation.log"
    stdout_path = smoke_dir / "stdout.bin"
    stderr_path = smoke_dir / "stderr.bin"
    command = [str(executable.resolve()), "--automation-smoke", str(sample.resolve())]
    stdout, stderr, exit_code, status = _run_historical_exe(
        command, archive_root, evidence_path, log_path, timeout_seconds
    )
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    status, observed_summary = _historical_smoke_summary(
        evidence_path, log_path, stdout, stderr, status
    )
    files = {
        name: _smoke_file_descriptor(path, output_dir)
        for name, path in (
            ("stdout", stdout_path),
            ("stderr", stderr_path),
            ("automation_log", log_path),
            ("smoke_evidence", evidence_path),
        )
    }
    return {
        "scope": HISTORICAL_EXE_SMOKE_SCOPE,
        "status": status,
        "command": command,
        "working_directory": str(archive_root.resolve()),
        "timeout_seconds": timeout_seconds,
        "executable_sha256": file_sha256(executable),
        "sample_project": HISTORICAL_EXE_SAMPLE,
        "sample_project_sha256": file_sha256(sample),
        "exit_code": exit_code,
        "expected_normalized_summary_sha256": HISTORICAL_EXE_EXPECTED_SUMMARY_SHA256,
        "observed_normalized_summary_sha256": observed_summary,
        "files": files,
    }


def _verified_smoke_inputs(archive: Path, archive_root: Path):
    _validate_release_archive_identity(archive, archive_root)
    _verify_extracted_archive_file(archive, archive_root, "RCMetaStudio.exe")
    executable = archive_root / "RCMetaStudio.exe"
    sample = archive_root / "sample_projects" / HISTORICAL_EXE_SAMPLE
    _verify_extracted_archive_file(
        archive,
        archive_root,
        "sample_projects/%s" % HISTORICAL_EXE_SAMPLE,
    )
    return executable, sample


def _run_historical_exe(command, archive_root, evidence_path, log_path, timeout_seconds):
    environment = os.environ.copy()
    environment["RCMS_PACKAGE_SMOKE_EVIDENCE"] = str(evidence_path.resolve())
    environment["RCMS_AUTOMATION_SMOKE_LOG"] = str(log_path.resolve())

    try:
        result = subprocess.run(
            command,
            cwd=str(archive_root),
            env=environment,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        return error.stdout or b"", error.stderr or b"", None, "timeout"
    except OSError as error:
        return b"", str(error).encode("utf-8", errors="replace"), None, "failure"
    return _completed_historical_exe(result, evidence_path)


def _completed_historical_exe(result, evidence_path):
    stdout_bytes = result.stdout or b""
    stderr_bytes = result.stderr or b""
    exit_code = result.returncode
    if exit_code != 0:
        return stdout_bytes, stderr_bytes, exit_code, "failure"
    status = "success" if evidence_path.is_file() else "incomplete"
    return stdout_bytes, stderr_bytes, exit_code, status


def _historical_smoke_summary(evidence_path, log_path, stdout_bytes, stderr_bytes, status):
    evidence, status = _read_historical_smoke_evidence(evidence_path, status)
    status, observed_summary = _historical_evidence_summary(evidence, status)
    if observed_summary is not None:
        return status, observed_summary
    return _historical_log_summary(log_path, stdout_bytes, stderr_bytes, status)


def _read_historical_smoke_evidence(evidence_path, status):
    if not evidence_path.is_file():
        return None, status
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "failure"
    return evidence, status


def _historical_evidence_summary(evidence, status):
    if not isinstance(evidence, dict):
        return status, None
    workflow = _historical_evidence_workflow(evidence)
    if workflow is None:
        return "failure", None
    observed = _historical_observed_summary(workflow)
    if observed is None:
        return "failure", None
    if observed != HISTORICAL_EXE_EXPECTED_SUMMARY_SHA256:
        return "failure", observed
    return status, observed


def _historical_evidence_workflow(evidence):
    workflow = evidence.get("workflows", {})
    valid = (
        evidence.get("schema_version") == 1
        and evidence.get("passed") is True
        and isinstance(workflow, dict)
        and workflow.get("expected_normalized_summary_sha256")
        == HISTORICAL_EXE_EXPECTED_SUMMARY_SHA256
    )
    return workflow if valid else None


def _historical_observed_summary(workflow):
    observed = workflow.get("normalized_summary_sha256")
    if not isinstance(observed, str) or not re.fullmatch(r"[0-9a-f]{64}", observed):
        return None
    return observed


def _historical_log_summary(log_path, stdout_bytes, stderr_bytes, status):
    mismatch = _summary_mismatch_from_log(log_path, stdout_bytes, stderr_bytes)
    if mismatch is None:
        return status, None
    observed = mismatch.group(1)
    if mismatch.group(2) != HISTORICAL_EXE_EXPECTED_SUMMARY_SHA256:
        status = "failure"
    return status, observed


def _summary_mismatch_from_log(log_path, stdout_bytes, stderr_bytes):
    combined_log = b"\n".join(
        (
            stdout_bytes,
            stderr_bytes,
            log_path.read_bytes() if log_path.is_file() else b"",
        )
    ).decode("utf-8", errors="replace")
    return re.search(
        r"Packaged summary identity mismatch: ([0-9a-f]{64}) != ([0-9a-f]{64})",
        combined_log,
    )


def _smoke_file_descriptor(path: Path, output_dir: Path):
    if not path.is_file():
        return None
    return {
        "relative_path": path.relative_to(output_dir).as_posix(),
        "sha256": file_sha256(path),
        "size_bytes": path.stat().st_size,
    }


def main():
    args = parse_args()
    try:
        path = capture(args)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print("Package API capture failed: %s" % error, file=sys.stderr)
        return 1
    manifest = json.loads(path.read_text(encoding="utf-8"))
    print("Captured %d published v0.3.1 package API cases: %s" % (len(manifest["case_ids"]), path))
    smoke = manifest["historical_exe_smoke"]
    if smoke is not None and smoke["status"] != "success":
        print(
            "Published executable --automation-smoke %s (evidence retained in %s)."
            % (smoke["status"], path.parent / "historical-exe-smoke"),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
