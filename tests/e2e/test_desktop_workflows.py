# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fresh-process desktop workflows with the production Qt and R stack."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "scenario",
    [
        "amino",
        "continuous",
        "lymph",
        "editing",
        "csv",
        "plot-edit",
        "small-study-effects",
        "calculator-binary",
        "calculator-continuous",
        "calculator-diagnostic",
    ],
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
        cwd=ROOT,
        env=env,
        capture_output=True,
        check=False,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "WORKFLOW PASSED" in result.stdout
