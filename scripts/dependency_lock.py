# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read the source checkout's pinned runtime and distribution identities."""

import argparse
import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        version = tomllib.load(stream)["project"]["version"]
    if not isinstance(version, str) or not version:
        raise ValueError("pyproject.toml must declare a project version")
    return version


def locked_python_versions(*names: str) -> dict[str, str]:
    with (ROOT / "uv.lock").open("rb") as stream:
        packages = tomllib.load(stream)["package"]
    versions = {}
    for name in names:
        matches = {package["version"] for package in packages if package["name"] == name}
        if len(matches) != 1:
            raise ValueError(f"uv.lock must provide a single version of {name}")
        versions[name] = matches.pop()
    return versions


def packaged_stack() -> dict[str, str]:
    packages = locked_python_versions("pyqt6", "pyqt6-qt6", "pyqt6-sip", "pyinstaller")
    r_dependencies = json.loads((ROOT / "config/r-dependencies.json").read_text(encoding="utf-8"))
    return {
        "python": (ROOT / ".python-version").read_text(encoding="utf-8").strip(),
        "pyqt6": packages["pyqt6"],
        "qt": packages["pyqt6-qt6"],
        "sip": packages["pyqt6-sip"],
        "sip_runtime": "6.17.3",
        "r": r_dependencies["target_runtime"]["r"],
        "pyinstaller": packages["pyinstaller"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-version", action="store_true", help="Print only the project version.")
    args = parser.parse_args()
    print(project_version() if args.project_version else json.dumps(packaged_stack()))
