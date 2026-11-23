#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Select and verify the official macOS Qt resource compiler."""

import argparse
from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess

if __package__:
    from scripts.dependency_lock import locked_python_versions
else:
    from dependency_lock import locked_python_versions


QT_RCC_VERSION = locked_python_versions("pyqt6-qt6")["pyqt6-qt6"]


def discover_macos_rcc(sdk_root: Path) -> Path:
    """Resolve one recognized Qt macOS SDK ``rcc`` layout, fail closed otherwise."""
    root = sdk_root.resolve()
    relative_candidates = (
        Path("libexec/rcc"),
        Path("libexec/rcc.app/Contents/MacOS/rcc"),
        Path("bin/rcc"),
        Path("bin/rcc.app/Contents/MacOS/rcc"),
    )
    candidates = set()
    for relative in relative_candidates:
        candidate = root / relative
        if not candidate.is_file():
            continue
        resolved = candidate.resolve()
        if not resolved.is_relative_to(root):
            raise RuntimeError(
                f"Qt macOS SDK rcc escapes the declared SDK root: {candidate} -> "
                f"{resolved}"
            )
        candidates.add(resolved)
    if not candidates:
        searched = ", ".join(relative.as_posix() for relative in relative_candidates)
        raise RuntimeError(
            f"Qt macOS SDK contains no rcc in a recognized layout under {root}; "
            f"searched {searched}"
        )
    if len(candidates) != 1:
        raise RuntimeError(
            "Qt macOS SDK contains ambiguous distinct rcc executables: "
            + ", ".join(str(candidate) for candidate in sorted(candidates))
        )
    return candidates.pop()


def validate_macos_rcc(
    rcc: Path,
    *,
    expected_version: str = QT_RCC_VERSION,
    command_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    host_machine: Callable[[], str] = platform.machine,
) -> list[str]:
    """Validate an official macOS SDK rcc without importing Qt build dependencies."""
    completed = command_runner(
        [str(rcc), "--version"], check=True, capture_output=True, text=True
    )
    reported = completed.stdout.strip() or completed.stderr.strip()
    if reported != f"rcc {expected_version}":
        raise RuntimeError(
            f"rcc version mismatch: expected 'rcc {expected_version}', got {reported!r}"
        )
    architectures = command_runner(
        ["/usr/bin/lipo", "-archs", str(rcc)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    supported = {"arm64", "x86_64"}
    unique_architectures = set(architectures)
    if (
        not unique_architectures
        or len(architectures) != len(unique_architectures)
        or not unique_architectures <= supported
    ):
        raise RuntimeError(f"rcc has invalid architecture slices: {architectures!r}")
    host = host_machine().lower()
    if host != "arm64" or host not in architectures:
        raise RuntimeError(
            f"rcc architecture mismatch: host {host!r}, slices {architectures!r}"
        )
    return sorted(architectures)


def append_github_env(github_env: Path, name: str, value: str) -> None:
    """Append one safe, exact UTF-8 GitHub environment-file assignment."""
    if not re.fullmatch(r"[A-Z_][A-Z0-9_]*", name):
        raise RuntimeError(f"invalid GitHub environment variable name: {name!r}")
    if "\r" in value or "\n" in value:
        raise RuntimeError("GitHub environment variable value contains CR or LF")
    github_env.parent.mkdir(parents=True, exist_ok=True)
    with github_env.open("ab") as stream:
        stream.write(f"{name}={value}\n".encode("utf-8"))


def resolve_macos_rcc(
    sdk_root: Path,
    github_env: Path,
    diagnostic: Path,
    *,
    command_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    host_machine: Callable[[], str] = platform.machine,
) -> dict[str, object]:
    """Validate, record, and export the exact official SDK ``rcc`` executable."""
    rcc = discover_macos_rcc(sdk_root)
    architectures = validate_macos_rcc(
        rcc, command_runner=command_runner, host_machine=host_machine
    )
    with rcc.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    record: dict[str, object] = {
        "path": str(rcc),
        "version": QT_RCC_VERSION,
        "sha256": digest,
        "architectures": architectures,
    }
    diagnostic.parent.mkdir(parents=True, exist_ok=True)
    diagnostic.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    append_github_env(github_env, "RCMS_QT6_RCC", str(rcc))
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--github-env", type=Path, required=True)
    parser.add_argument("--diagnostic", type=Path, required=True)
    args = parser.parse_args()
    record = resolve_macos_rcc(
        args.sdk_root.resolve(), args.github_env.resolve(), args.diagnostic.resolve()
    )
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
