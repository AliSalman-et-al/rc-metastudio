# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
import re
import subprocess
import tomllib


ROOT = Path(__file__).resolve().parents[3]


def test_linux_package_checks_installed_rcmetar_against_current_source_version():
    script = (ROOT / "scripts/build-linux-package.sh").read_text(encoding="utf-8")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    app_version = project["project"]["version"]
    package_description = (ROOT / "r/RCMetaR/DESCRIPTION").read_text(
        encoding="utf-8"
    )
    description_version = re.search(r"(?m)^Version:\s*(\S+)\s*$", package_description)
    assert description_version is not None
    assert description_version.group(1) == app_version

    assert 'project.get("project", {}).get("version")' in script
    assert 'RCMS_EXPECTED_RCMETAR_VERSION="$application_version"' in script
    assert 'Sys.getenv("RCMS_EXPECTED_RCMETAR_VERSION", unset = "")' in script
    assert 'version("RCMetaR") == expected' in script
    assert 'version("RCMetaR") == "0.4.1"' not in script
    assert 'version("mada") == "0.5.12"' in script
    assert 'version("meta") == "8.5-0"' in script

    subprocess.run(
        ["bash", "-n", str(ROOT / "scripts/build-linux-package.sh")],
        check=True,
        capture_output=True,
        text=True,
    )
