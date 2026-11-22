# SPDX-License-Identifier: GPL-3.0-or-later
"""Identify the RCMetaR source used with this application build."""

import hashlib
from pathlib import Path
import sys

from rc_metastudio import __version__


def source_sha(package: Path) -> str:
    digest = hashlib.sha256()
    files = [package / "DESCRIPTION", package / "NAMESPACE", *sorted((package / "R").glob("*.R"))]
    for path in files:
        digest.update(path.relative_to(package).as_posix().encode("utf-8") + b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return digest.hexdigest()


def expected_source() -> tuple[str, str]:
    if getattr(sys, "frozen", False):
        fingerprint = Path(__file__).with_name("source.sha256").read_text(encoding="ascii").strip()
    else:
        fingerprint = source_sha(Path(__file__).resolve().parents[2] / "r" / "RCMetaR")
    return __version__, fingerprint


if __name__ == "__main__":
    package = Path(__file__).resolve().parents[2] / "r" / "RCMetaR"
    (package / "inst" / "source.sha256").write_text(source_sha(package) + "\n", encoding="ascii")
