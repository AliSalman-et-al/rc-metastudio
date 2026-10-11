# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fresh-process desktop workflows with the production Qt and R stack."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.verify_rcms import SCENARIOS

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "scenario",
    [scenario for scenario in SCENARIOS if scenario != "doctor"],
)
def test_desktop_workflow(scenario, tmp_path):
    env = os.environ | {
        "PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(ROOT))),
        "RCMS_REQUIRE_IN_PROCESS_RPY2": "1",
        "RCMS_QT6_BUILD_ROOT": os.environ.get(
            "RCMS_QT6_BUILD_ROOT", str(ROOT / "build/qt6-verification")
        ),
        "RCMS_ANALYSIS_SCRATCH_DIR": str(tmp_path / "analysis"),
    }
    result = subprocess.run(
        [
            sys.executable,
            "-X",
            "faulthandler",
            str(Path(__file__).with_name("desktop_driver.py")),
            scenario,
            str(tmp_path),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        check=False,
        text=True,
        timeout=240 if scenario.startswith("plot-workflow-") else 120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "WORKFLOW PASSED" in result.stdout
