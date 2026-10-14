"""Resource-bounded concurrency; each case retains its fresh Qt/R process."""

import json
import os

import pytest

from scripts.verification_resources import desktop_resources
from scripts.verification_evidence import verification_context


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--fresh", action="store_true", help="Run every desktop case without evidence reuse")


def pytest_configure(config: pytest.Config) -> None:
    if not hasattr(config, "workerinput") and not config.option.collectonly and os.environ.get("RCMS_R_HOME"):
        os.environ["RCMS_E2E_CONTEXT"] = json.dumps(verification_context())
        fresh = config.getoption("--fresh") or os.environ.get("RCMS_E2E_FRESH") == "1"
        os.environ["RCMS_E2E_REUSE_PASSED"] = "0" if fresh else "1"


def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:
    return desktop_resources()["workers"]


def pytest_report_header(config: pytest.Config) -> str:
    context = json.loads(os.environ.get("RCMS_E2E_CONTEXT", "{}"))
    return f"Desktop resource budget: {desktop_resources()} (override with -n 1); input signature: {context.get('sha256')}"
