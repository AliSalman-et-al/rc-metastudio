# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared execution and bootstrap helpers for direct RCMetaR R drivers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
import tempfile
from pathlib import Path
from uuid import uuid4
import json

import pytest


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_REQUIRED = os.getenv("RCMS_R_STACK_REQUIRED") == "1"

RCMETAR_BOOTSTRAP = textwrap.dedent(
    r"""
    repo <- normalizePath(__REPO_ROOT__, winslash = "/")
    suppressPackageStartupMessages(source(file.path(repo, "r/RCMetaR/R/classes.R")))
    suppressPackageStartupMessages(source(file.path(repo, "r/RCMetaR/R/analysis_contracts.R")))
    suppressPackageStartupMessages(source(file.path(repo, "r/RCMetaR/R/analysis_output.R")))
    suppressPackageStartupMessages(source(file.path(repo, "r/RCMetaR/R/display.R")))
    suppressPackageStartupMessages(source(file.path(repo, "r/RCMetaR/R/results_display.R")))
    suppressPackageStartupMessages(source(file.path(repo, "r/RCMetaR/R/rcmetar-core.R")))
    suppressPackageStartupMessages(source(file.path(repo, "r/RCMetaR/R/diagnostic_methods.R")))
    """
).strip()


def build_r_driver(driver: str) -> str:
    """Expand the canonical direct-source bootstrap into an R driver."""

    bootstrap = RCMETAR_BOOTSTRAP.replace(
        "__REPO_ROOT__", repr(REPO_ROOT).replace("\\", "/")
    )
    return textwrap.dedent(driver).replace("__RCMETAR_BOOTSTRAP__", bootstrap)


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


def run_python_driver(
    driver: str, *, env: dict[str, str], source_install: bool = False
) -> subprocess.CompletedProcess:
    """Run an embedded-Python driver with the same required-lane policy."""

    evidence = Path(REPO_ROOT) / "artifacts/verification/r-drivers" / uuid4().hex
    evidence.mkdir(parents=True)
    (evidence / "driver.py").write_text(driver, encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="rcms-driver-") as work:
        owned_env = dict(env)
        owned_env["PYTHONPATH"] = os.pathsep.join(filter(None, (REPO_ROOT, env.get("PYTHONPATH"))))
        owned_env["RCMS_DRIVER_OWNED_CWD"] = work
        owned_env["RCMS_SUMMARY_OWNED_LIBRARY"] = str(Path(work) / "r-library")
        library = Path(owned_env["RCMS_SUMMARY_OWNED_LIBRARY"])
        library.mkdir()
        if source_install:
            roots = env.get("R_LIBS", "").split(os.pathsep)
            for root in roots:
                if not root or not Path(root).is_dir():
                    continue
                for package in Path(root).iterdir():
                    if package.is_dir() and package.name != "RCMetaR" and not package.name.startswith("00LOCK") and not (library / package.name).exists():
                        shutil.copytree(package, library / package.name)
        result = subprocess.run(
            [sys.executable, str(evidence / "driver.py")],
            cwd=work, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            encoding="utf-8", errors="replace", env=owned_env,
        )
    (evidence / "stdout.log").write_text(result.stdout, encoding="utf-8")
    (evidence / "stderr.log").write_text(result.stderr, encoding="utf-8")
    (evidence / "command.json").write_text(json.dumps({"command": result.args, "exit_code": result.returncode, "owned_cwd": work, "cleanup": not Path(work).exists()}), encoding="utf-8")
    if result.returncode == 42:
        message = (
            result.stdout.strip() or "Python/R bridge prerequisites are unavailable"
        )
        if _REQUIRED:
            pytest.fail(message)
        pytest.skip(message)

    assert result.returncode == 0, "driver failed (rc=%s)\nSTDOUT:\n%s\nSTDERR:\n%s" % (
        result.returncode,
        result.stdout[-2000:],
        result.stderr[-2000:],
    )
    assert "OK" in result.stdout
    return result
