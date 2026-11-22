"""Resource-bounded concurrency; each case retains its fresh Qt/R process."""

import json
import os
from pathlib import Path

import pytest

from scripts.desktop_partition import DESKTOP_SHARDS, partition
from scripts.desktop_worker_capacity import desktop_resources
from scripts.verification_evidence import desktop_environment, verification_context, verification_launch_inputs


_DESKTOP_ENV = pytest.StashKey[dict[str, str]]()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--desktop-shard", type=int, choices=DESKTOP_SHARDS, default=None)
    parser.addoption("--desktop-scenarios", default=None)
    parser.addoption("--shard-report", default=None)
    parser.addoption("--fresh", action="store_true", help="Run every desktop case without evidence reuse")


def pytest_configure(config: pytest.Config) -> None:
    if config.option.collectonly:
        return
    if hasattr(config, "workerinput"):
        config.stash[_DESKTOP_ENV] = dict(os.environ) | config.workerinput["desktop_launch"]
        return
    from scripts.verify import ensure_typing

    env = desktop_environment()
    receipt = ensure_typing(Path(env["RCMS_QT6_BUILD_ROOT"]), env)
    context = verification_context(env) if env.get("RCMS_R_HOME") else None
    os.environ["RCMS_E2E_CONTEXT"] = json.dumps({
        "typing": str(receipt),
        "verification": context,
        "launch_inputs": verification_launch_inputs(env),
    })
    fresh = config.getoption("--fresh") or os.environ.get("RCMS_E2E_FRESH") == "1"
    os.environ["RCMS_E2E_REUSE_PASSED"] = "0" if fresh else "1"
    config.stash[_DESKTOP_ENV] = dict(os.environ)


@pytest.hookimpl(optionalhook=True)
def pytest_configure_node(node) -> None:
    environment = node.config.stash[_DESKTOP_ENV]
    names = verification_launch_inputs(desktop_environment()) | {
        "RCMS_E2E_CONTEXT": None, "RCMS_E2E_REUSE_PASSED": None,
    }
    node.workerinput["desktop_launch"] = {name: environment[name] for name in names if name in environment}


@pytest.fixture(scope="session")
def desktop_launch_environment(pytestconfig: pytest.Config) -> dict[str, str]:
    # Collection can import Qt, whose Windows bootstrap prepends to PATH.
    return pytestconfig.stash[_DESKTOP_ENV]


def pytest_xdist_auto_num_workers(config: pytest.Config) -> int:
    return desktop_resources()["workers"]


def pytest_report_header(config: pytest.Config) -> str:
    context = json.loads(os.environ.get("RCMS_E2E_CONTEXT", "{}"))
    signature = (context.get("verification") or {}).get("sha256")
    return f"Desktop resource budget: {desktop_resources()} (override with -n 1); input signature: {signature}"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    shard = config.getoption("--desktop-shard")
    scenarios = config.getoption("--desktop-scenarios")
    if shard is None:
        if scenarios:
            raise pytest.UsageError("--desktop-scenarios requires --desktop-shard")
        return
    durations = json.loads(
        (Path(__file__).resolve().parents[2] / "config/desktop-durations.json").read_text()
    )
    nodes = [item.nodeid for item in items]
    bins, loads = partition(nodes, durations)
    selected = bins[shard - 1]
    if scenarios:
        requested = set(scenarios.split(","))
        by_scenario = {node.rsplit("[", 1)[-1].removesuffix("]"): node for node in selected}
        if missing := requested - by_scenario.keys():
            raise pytest.UsageError(f"Desktop scenarios outside shard {shard}: {', '.join(sorted(missing))}")
        selected = [node for scenario, node in by_scenario.items() if scenario in requested]
    report = config.getoption("--shard-report")
    if report:
        path = Path(report)
        if hasattr(config, "workerinput"):
            path = path.with_name(f"{path.stem}-{config.workerinput['workerid']}{path.suffix}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "collected": nodes, "shards": bins, "estimated_seconds": loads, "selected": selected,
        }, indent=2))
    by_node = {item.nodeid: item for item in items}
    items[:] = [by_node.pop(node) for node in selected]
    deselected = list(by_node.values())
    config.hook.pytest_deselected(items=deselected)
