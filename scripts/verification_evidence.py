"""Reuse passed desktop evidence only for identical inputs and intact artifacts."""

import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

if __package__:
    from scripts.r_verification_support import resolve_rscript
else:
    from r_verification_support import resolve_rscript

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "artifacts/verification/rcms/cache"
R_PATH_VARIABLES = ("R_HOME", "R_LIBS", "R_LIBS_USER", "R_LIBS_SITE", "LD_LIBRARY_PATH")
PDF_TOOLS = ("pdfimages", "pdfinfo", "pdftohtml", "pdftoppm", "pdftotext")
EVIDENCE_ENVIRONMENT = (
    "QT_SCALE_FACTOR", "QT_FONT_DPI", "QT_QPA_FONTDIR", "QT_QPA_PLATFORM",
    "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "FONTCONFIG_FILE", "FONTCONFIG_PATH",
    "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "LANG", "LANGUAGE",
    "RCMS_AXIS_BASELINE", "RCMS_REVIEWER_BASELINE", "RCMS_UI_DESIGN_PHASE",
    "RCMS_UI_CRAWL_SECTIONS", "RCMS_PROFILE_STARTUP", "RCMS_REPORT_AUDIT_DIR",
)


def file_digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_digest(build_root: Path) -> str:
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
    resource = build_root / "resources/icons.rcc"
    for path in sorted([*(build_root / "generated").rglob("*.py"), resource]):
        if path.is_file():
            digest.update(path.relative_to(build_root).as_posix().encode())
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


def desktop_environment(*, native: bool = False) -> dict[str, str]:
    env = os.environ | {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(ROOT))),
        "RCMS_REQUIRE_IN_PROCESS_RPY2": "1",
        "RCMS_QT6_BUILD_ROOT": str(Path(os.environ.get(
            "RCMS_QT6_BUILD_ROOT", ROOT / "build/qt6-verification"
        )).resolve()),
    }
    for variable in ("RCMS_R_HOME", "RCMS_R_LIBS", "QT_QPA_FONTDIR"):
        if env.get(variable):
            env[variable] = str(Path(env[variable]).resolve())
    if native:
        env.pop("QT_QPA_PLATFORM", None)
    else:
        env["QT_QPA_PLATFORM"] = "offscreen"
        if sys.platform == "win32":
            env.setdefault("QT_QPA_FONTDIR", str(Path(env["WINDIR"]) / "Fonts"))
    return env


def typing_command(build_root: Path) -> list[str]:
    command = [sys.executable, "-m", "ty", "check", "--python", sys.executable, "--python-platform", "win32"]
    for path in (
        build_root / "generated/rc_metastudio",
        build_root / "generated/rc_metastudio/forms",
        ".",
        "src/rc_metastudio",
        "src",
        "scripts",
        "tests/python/gui",
    ):
        command += ["--extra-search-path", str(path)]
    return command + ["src/rc_metastudio", "scripts", "tests", "r/RCMetaR/inst/qa",
                      ".agents/skills/verify-rcms/scripts"]


def verified_typing(path: object, build_root: Path, source: str) -> bool:
    if not isinstance(path, str):
        return False
    try:
        receipt = Path(path).resolve()
        if receipt.name != "command.json" or receipt.parent.parent != ROOT / "artifacts/verification/typing":
            return False
        record = json.loads(receipt.read_text(encoding="utf-8"))
        return (
            record["exit_code"] == 0 and record["python_platform"] == "win32"
            and record["build_root"] == str(build_root)
            and record["command"] == typing_command(build_root)
            and record["source_sha256"] == source and record["source_unchanged"] is True
            and (receipt.parent / "stdout.log").is_file() and (receipt.parent / "stderr.log").is_file()
        )
    except (OSError, ValueError, KeyError, TypeError):
        return False


def evidence_environment(env: dict[str, str]) -> dict[str, str | None]:
    return {name: env.get(name) for name in EVIDENCE_ENVIRONMENT} | {
        name: value for name, value in env.items() if name.startswith("LC_")
    }


def verification_launch_inputs(env: dict[str, str]) -> dict[str, str | None]:
    return evidence_environment(env) | {name: env.get(name) for name in (
        *R_PATH_VARIABLES, "RCMS_R_HOME", "RCMS_R_LIBS", "RCMS_RSCRIPT", "RCMS_QT6_BUILD_ROOT", "PATH", "PATHEXT",
    )}


def _runtime_environment(env: dict[str, str]) -> dict[str, str | None]:
    return json.loads(subprocess.check_output(
        [sys.executable, "-c", """
import json, os
from rc_metastudio.r_runtime import configure_bundled_r_environment

configure_bundled_r_environment()
names = (
    "R_HOME", "R_LIBS", "R_LIBS_USER", "R_LIBS_SITE", "LD_LIBRARY_PATH",
    "R_ENVIRON", "R_ENVIRON_USER", "R_PROFILE", "R_PROFILE_USER",
    "RPY2_CFFI_MODE", "LANG", "LC_ALL", "LC_COLLATE", "LC_CTYPE", "LC_NUMERIC", "PATH",
)
print(json.dumps({name: os.environ.get(name) for name in names}))
"""],
        cwd=ROOT, env=env, text=True, encoding="utf-8",
    ))


def external_tools(env: dict[str, str], runtime: dict[str, str | None] | None = None) -> dict[str, dict[str, str] | None]:
    if runtime is None:
        runtime = _runtime_environment(env)
    effective_env = env | {name: value for name, value in runtime.items() if value is not None}
    commands: dict[str, str | Path | None] = {
        name: shutil.which(name, path=effective_env.get("PATH")) for name in PDF_TOOLS
    }
    commands["Rscript"] = resolve_rscript("Rscript", effective_env)
    identities: dict[str, dict[str, str] | None] = {}
    for name, command in commands.items():
        path = Path(command).resolve() if command else None
        identities[name] = {"path": str(path), "sha256": file_digest(path)} if path and path.is_file() else None
    return identities


def verification_context(env: dict[str, str]) -> dict[str, object]:
    runtime = _runtime_environment(env)
    startup = {name: runtime.pop(name) for name in ("R_ENVIRON", "R_ENVIRON_USER", "R_PROFILE", "R_PROFILE_USER")}
    runtime_roots = _runtime_roots(env, runtime)
    record = {
        "source_sha256": source_digest(Path(env["RCMS_QT6_BUILD_ROOT"])),
        "python": sys.version,
        "platform": platform.platform(),
        "libc": platform.libc_ver(),
        "r_environment": {key: value for key, value in runtime.items() if key not in (*R_PATH_VARIABLES, "PATH")},
        "r_startup_files": {
            name: file_digest(Path(value)) if value and Path(value).is_file() else None
            for name, value in startup.items()
        },
        "runtime_trees": [tree_digest(path) for path in runtime_roots],
        "external_tools": external_tools(env, runtime),
        "distributions": sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions()),
        "environment": evidence_environment(env),
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
    except (OSError, ValueError, KeyError, TypeError):
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


def _runtime_roots(env: dict[str, str], runtime: dict[str, str | None]) -> list[Path]:
    runtime_roots = [
        Path(sys.prefix),
        *(Path(name) for variable in R_PATH_VARIABLES
          for name in (runtime.get(variable) or "").split(os.pathsep) if name),
    ]
    font_roots = [Path("/usr/share/fonts"), Path.home() / ".local/share/fonts", Path.home() / ".fonts"]
    if sys.platform == "win32":
        font_roots = [Path(env["WINDIR"]) / "Fonts"]
    elif sys.platform == "darwin":
        font_roots = [Path("/System/Library/Fonts"), Path("/Library/Fonts"), Path.home() / "Library/Fonts"]
    if configured_fonts := env.get("QT_QPA_FONTDIR"):
        font_roots.append(Path(configured_fonts))
    runtime_roots.extend(path for path in font_roots if path.is_dir())
    return list(dict.fromkeys(path.resolve() for path in runtime_roots if path.is_dir()))
