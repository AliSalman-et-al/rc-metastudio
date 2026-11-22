# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared execution and bootstrap helpers for direct RCMetaR R drivers."""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_REQUIRED = os.getenv("RCMS_R_STACK_REQUIRED") == "1"


def run_r_driver(driver: str) -> None:
    """Run a direct R driver, skipping locally but failing in the required lane."""

    rscript = shutil.which("Rscript")
    if not rscript:
        message = "Rscript executable not found"
        if _REQUIRED:
            pytest.fail(message)
        pytest.skip(message)

    result = subprocess.run(
        [rscript, "-"],
        cwd=REPO_ROOT,
        input=driver,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if result.returncode == 42:
        message = result.stdout.strip() or "R driver prerequisites are unavailable"
        if _REQUIRED:
            pytest.fail(message)
        pytest.skip(message)

    assert result.returncode == 0, "driver failed (rc=%s)\nSTDOUT:\n%s\nSTDERR:\n%s" % (
        result.returncode,
        result.stdout[-2000:],
        result.stderr[-2000:],
    )
    assert "OK" in result.stdout
