"""Reuse passed desktop evidence only for identical inputs and intact artifacts."""

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "artifacts/verification/rcms/cache"


def file_digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_digest() -> str:
    paths = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
    ).decode().split("\0")
    digest = hashlib.sha256()
    for name in sorted(set(paths)):
        path = ROOT / name
        if not name or name.startswith("docs/") or path.suffix == ".md" or not path.is_file():
            continue
        digest.update(name.encode())
        digest.update(file_digest(path).encode())
    generated = Path(os.environ.get("RCMS_QT6_BUILD_ROOT", ROOT / "build/qt6-verification")) / "generated"
    for path in sorted(generated.rglob("*.py")):
        digest.update(path.relative_to(generated).as_posix().encode())
        digest.update(file_digest(path).encode())
    return digest.hexdigest()


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        name = path.relative_to(root).as_posix()
        # INSTALL metadata embeds the temporary directory and build timestamp.
        # Executable R code, data, native libraries and DESCRIPTION remain bound.
        if name == "RCMetaR/Meta/package.rds":
            continue
        digest.update(name.encode())
        digest.update(file_digest(path).encode())
    return digest.hexdigest()


def verification_context() -> dict[str, object]:
    runtime_roots = _runtime_roots()
    record = {
        "source_sha256": source_digest(),
        "python": sys.version,
        "platform": platform.platform(),
        "libc": platform.libc_ver(),
        "effective_cffi_mode": "API",  # Production r_runtime forces this mode.
        "r_startup_files": {
            name: file_digest(path) if path.is_file() else None
            for name, path in {
                "profile": Path(os.environ.get("R_PROFILE_USER", Path.home() / ".Rprofile")),
                "environ": Path(os.environ.get("R_ENVIRON_USER", Path.home() / ".Renviron")),
            }.items()
        },
        "runtime_trees": [tree_digest(path) for path in runtime_roots],
        "distributions": sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions()),
        "environment": {name: os.environ.get(name) for name in (
            "QT_SCALE_FACTOR", "QT_FONT_DPI", "LANG", "LC_ALL",
            "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
        )},
    }
    record["sha256"] = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
    return record


def passed_evidence(context: dict[str, object], scenario: str) -> Path | None:
    index = CACHE / str(context["sha256"]) / (scenario + ".json")
    try:
        entry = json.loads(index.read_text())
        evidence = ROOT / entry["evidence"]
        manifest_path = evidence / "manifest.json"
        if file_digest(manifest_path) != entry["manifest_sha256"]:
            return None
        manifest = json.loads(manifest_path.read_text())
        if not manifest["passed"] or manifest.get("exit_code") != 0 or manifest.get("verification_context") != context:
            return None
        for artifact in manifest["files"]:
            path = evidence / artifact["path"]
            if file_digest(path) != artifact["sha256"]:
                return None
        return evidence
    except (OSError, ValueError, KeyError):
        return None


def remember_evidence(context: dict[str, object], scenario: str, evidence: Path) -> None:
    directory = CACHE / str(context["sha256"])
    directory.mkdir(parents=True, exist_ok=True)
    index = directory / (scenario + ".json")
    temporary = index.with_suffix("." + uuid4().hex + ".tmp")
    temporary.write_text(json.dumps({
        "evidence": evidence.relative_to(ROOT).as_posix(),
        "manifest_sha256": file_digest(evidence / "manifest.json"),
    }) + "\n")
    temporary.replace(index)


def _runtime_roots() -> list[Path]:
    libraries = dict.fromkeys(
        name for variable in ("RCMS_R_LIBS", "R_LIBS", "R_LIBS_USER")
        for name in os.environ.get(variable, "").split(os.pathsep) if name
    )
    runtime_roots = [Path(sys.prefix), Path(os.environ["RCMS_R_HOME"])]
    runtime_roots.extend(Path(name) for name in libraries)
    runtime_roots.extend(Path(name) for name in os.environ.get("LD_LIBRARY_PATH", "").split(os.pathsep) if name)
    font_roots = [Path("/usr/share/fonts"), Path.home() / ".local/share/fonts", Path.home() / ".fonts"]
    if sys.platform == "win32":
        font_roots = [Path(os.environ["WINDIR"]) / "Fonts"]
    elif sys.platform == "darwin":
        font_roots = [Path("/System/Library/Fonts"), Path("/Library/Fonts"), Path.home() / "Library/Fonts"]
    runtime_roots.extend(path for path in font_roots if path.is_dir())
    return runtime_roots
