# SPDX-License-Identifier: GPL-3.0-or-later
"""Identify the RCMetaR source used with this application build."""

import hashlib
import json
from importlib.resources import files
from pathlib import Path
import sys

from rc_metastudio import __version__


STAMP_COMMAND = "uv run --locked python -m rc_metastudio.rcmetar_identity"
_ROOT = Path(__file__).resolve().parents[2]


def source_sha(package: Path, *, description: bytes | None = None) -> str:
    digest = hashlib.sha256()
    sources = ["DESCRIPTION", "NAMESPACE", *sorted(
        path.relative_to(package).as_posix()
        for path in (package / "R").iterdir() if path.is_file() and path.suffix.lower() == ".r"
    )]
    for name in sources:
        contents = description if name == "DESCRIPTION" and description is not None else (package / name).read_bytes()
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(contents.replace(b"\r\n", b"\n") + b"\0")
    return digest.hexdigest()


def expected_source() -> tuple[str, str]:
    if getattr(sys, "frozen", False):
        fingerprint = files("rc_metastudio").joinpath("source.sha256").read_text(encoding="ascii").strip()
    else:
        package = _ROOT / "r" / "RCMetaR"
        if not (package / "DESCRIPTION").is_file():
            raise RuntimeError("The analysis backend requires an editable RC MetaStudio source checkout "
                               "or the packaged application.")
        fingerprint = source_sha(package)
    return __version__, fingerprint


def runtime_versions() -> dict[str, str]:
    manifest = (files("rc_metastudio").joinpath("r-dependencies.json") if getattr(sys, "frozen", False)
                else _ROOT / "config" / "r-dependencies.json")
    dependencies = json.loads(manifest.read_text(encoding="utf-8"))["direct_RCMetaR_dependencies"]
    return {item["name"]: item["installed_version"] for item in dependencies if "runtime" in item["scope"]}


if __name__ == "__main__":
    package = _ROOT / "r" / "RCMetaR"
    (package / "inst" / "source.sha256").write_text(source_sha(package) + "\n", encoding="ascii")
