# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fresh-process desktop workflows with the production Qt and R stack."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.verify_rcms import QUALIFICATION_SCENARIOS

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "scenario",
    QUALIFICATION_SCENARIOS,
)
def test_desktop_workflow(scenario):
    # The same launcher owns timeouts, isolation and durable evidence in CI.
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/verify_rcms.py"),
            scenario,
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    evidence_lines = [line.removeprefix("Evidence: ") for line in result.stdout.splitlines() if line.startswith("Evidence: ")]
    assert len(evidence_lines) == 1, result.stdout + result.stderr
    evidence = Path(evidence_lines[0])
    manifest = json.loads((evidence / "manifest.json").read_text(encoding="utf-8"))
    assert result.returncode == 0, result.stdout + result.stderr
    assert manifest["passed"], evidence
