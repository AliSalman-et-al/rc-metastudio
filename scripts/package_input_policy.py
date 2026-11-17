#!/usr/bin/env python3
"""Classify changed paths for source and packaged verification."""

import argparse
import sys


PACKAGE_DIRECTORIES = (
    ".agents/skills/verify-rcms/scripts/",
    "delivery/",
    "packaging/",
    "r/",
    "sample_projects/",
    "scripts/",
    "src/",
    "tests/e2e/",
    "tests/packaging/",
)
PACKAGE_FILES = {
    ".github/workflows/candidate.yml",
    ".github/workflows/community-release-candidate.yml",
    ".github/workflows/fast-verification.yml",
    ".github/workflows/macos-trusted-release-candidate.yml",
    ".github/workflows/notarization-status.yml",
    ".github/workflows/package-linux.yml",
    ".github/workflows/package-target.yml",
    ".github/workflows/package-verification.yml",
    ".github/workflows/package-windows.yml",
    ".github/workflows/promote.yml",
    ".python-version",
    "config/macos-package-targets.json",
    "config/r-dependencies.json",
    "pyproject.toml",
    "tests/python/fast/test_project_format.py",
    "tests/python/fast/test_qt6_build_slice.py",
    "tests/python/gui/test_main_window_automation_launch.py",
    "uv.lock",
}
SOURCE_DIRECTORIES = (".github/workflows/", "config/", "tests/")


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    paths = [line.rstrip("\r\n").replace("\\", "/") for line in sys.stdin]
    package_inputs = [
        path for path in paths
        if path.startswith(PACKAGE_DIRECTORIES) or path in PACKAGE_FILES
    ]
    source_inputs = [path for path in paths if path.startswith(SOURCE_DIRECTORIES)]
    matches = package_inputs or source_inputs
    source_required = str(bool(matches)).lower()
    print(f"run-windows={source_required}")
    print(f"run-linux={source_required}")
    print(f"run-windows-package={str(bool(package_inputs)).lower()}")
    reason = f"matched {matches[0]}" if matches else "no Qt6 integration verification inputs changed"
    print(f"reason={reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
