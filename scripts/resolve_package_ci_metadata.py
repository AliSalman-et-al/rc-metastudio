#!/usr/bin/env python3
"""Resolve cross-platform package metadata for GitHub Actions."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

if __package__:
    from scripts.dependency_lock import ROOT, locked_python_versions, project_version
else:
    from dependency_lock import ROOT, locked_python_versions, project_version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--r-policy", action="store_true", help="Emit the pinned R version and snapshot.")
    source.add_argument("--qt-sdk", action="store_true", help="Emit the locked Qt SDK and downloader versions.")
    args = parser.parse_args()
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        raise SystemExit("GITHUB_OUTPUT is required.")
    if args.r_policy:
        if __package__:
            from scripts.r_dependency_policy import load_policy
        else:
            from r_dependency_policy import load_policy
        policy = load_policy(ROOT / "config/r-dependencies.json")
        fields = {"r-version": policy["r_version"], "r-snapshot": policy["snapshot"]}
    elif args.qt_sdk:
        versions = locked_python_versions("pyqt6-qt6", "aqtinstall")
        fields = {"qt-version": versions["pyqt6-qt6"], "aqt-version": versions["aqtinstall"]}
    else:
        fields = {"version": project_version()}
    with Path(output_path).open("a", encoding="utf-8") as output:
        for key, value in fields.items():
            output.write(f"{key}={value}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
