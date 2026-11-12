"""Resource-bounded concurrency; each case retains its fresh Qt/R process."""

import json
import os
from pathlib import Path

import pytest

from scripts.desktop_worker_capacity import desktop_resources
from scripts.verification_evidence import verification_context


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--desktop-shard", type=int, choices=(1, 2, 3), default=None)
    parser.addoption("--shard-report", default=None)
    parser.addoption("--fresh", action="store_true", help="Run every desktop case without evidence reuse")


def pytest_configure(config: pytest.Config) -> None:
    if not hasattr(config, "workerinput") and not config.option.collectonly:
        from scripts.verify import DEFAULT_BUILD_ROOT, run_typing
        run_typing(Path(os.environ.get("RCMS_QT6_BUILD_ROOT", str(DEFAULT_BUILD_ROOT))).resolve())
    if not hasattr(config, "workerinput") and not config.option.collectonly and os.environ.get("RCMS_R_HOME"):
        os.environ["RCMS_E2E_CONTEXT"] = json.dumps(verification_context())
        fresh = config.getoption("--fresh") or os.environ.get("RCMS_E2E_FRESH") == "1"
        os.environ["RCMS_E2E_REUSE_PASSED"] = "0" if fresh else "1"


def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:
    return desktop_resources()["workers"]


def pytest_report_header(config: pytest.Config) -> str:
    context = json.loads(os.environ.get("RCMS_E2E_CONTEXT", "{}"))
    return f"Desktop resource budget: {desktop_resources()} (override with -n 1); input signature: {context.get('sha256')}"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    shard = config.getoption("--desktop-shard")
    if shard is None:
        return
    durations = json.loads(
        (Path(__file__).resolve().parents[2] / "config/desktop-durations.json").read_text()
    )
    bins: list[list[str]] = [[], [], []]
    loads = [0.0, 0.0, 0.0]
    nodes = [item.nodeid for item in items]
    def duration(node: str) -> float:
        # shortcut: unmeasured scenarios count as 60 s, refresh config/desktop-durations.json from shard JUnit when shards drift apart.
        return float(durations.get(node.rsplit("[", 1)[-1].removesuffix("]"), 60.0))
    for node in sorted(nodes, key=lambda node: (-duration(node), node)):
        index = min(range(3), key=lambda index: (loads[index], index))
        bins[index].append(node)
        loads[index] += duration(node)
    report = config.getoption("--shard-report")
    if report:
        path = Path(report)
        if hasattr(config, "workerinput"):
            path = path.with_name(f"{path.stem}-{config.workerinput['workerid']}{path.suffix}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"collected": nodes, "shards": bins, "estimated_seconds": loads}, indent=2))
    selected = set(bins[shard - 1])
    deselected = [item for item in items if item.nodeid not in selected]
    items[:] = [item for item in items if item.nodeid in selected]
    config.hook.pytest_deselected(items=deselected)
