# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Plan verification from repository-relative paths, for CI and local ready."""

import argparse
from dataclasses import dataclass
from fnmatch import fnmatchcase
import json
import subprocess
import sys
from pathlib import Path

from scripts.desktop_partition import DESKTOP_SHARDS, partition
from tests.e2e.desktop_scenarios import QUALIFICATION_SCENARIOS

ROOT = Path(__file__).resolve().parents[1]
QT = ("qt6-verification", "remaining-surface-verification")
SOURCE = "source-fast-targets"
R = "full-r-stack"
WINDOWS_PACKAGE = "windows-package-qualification"
OTHER_PACKAGES = ("macos-package-qualification", "linux-package-qualification", "packaging-contract-macos")
PACKAGES = (WINDOWS_PACKAGE, *OTHER_PACKAGES)
JOBS = (*QT, SOURCE, R, *PACKAGES)
TARGETS = (
    {"target": "windows-x64", "runner": "windows-latest", "platform": "windows"},
    {"target": "macos-arm64", "runner": "macos-15", "platform": "macos"},
    {"target": "linux-x64", "runner": "ubuntu-24.04", "platform": "linux"},
)

BROAD = (
    "*.lock", "pyproject.toml", ".python-version", ".gitattributes",
    ".github/workflows/*", ".github/actions/*",
    "*/r_bridge.py", "*/rcmetar-core.R", "r/RCMetaR/DESCRIPTION", "r/RCMetaR/NAMESPACE",
    "config/*", "scripts/verify*", "scripts/ci_selection.py", "scripts/desktop_*",
    "scripts/*verification*", "scripts/code_health.py", "scripts/*qt6*",
    "scripts/*r-deps*", "scripts/install-rcmetar-source.R", "scripts/r_*policy.*",
    "scripts/local_r_test_backend.py", "tests/conftest.py",
    ".agents/skills/verify-rcms/scripts/*",
)
# These feature boundaries have explicit drives in the verify-rcms feature map.
# Shared shell, analysis, workspace and results code can affect many more drives.
FEATURES = (
    (("src/rc_metastudio/calculators/*", "src/rc_metastudio/forms/*calculation*.ui",
      "src/rc_metastudio/forms/*_data_dialog.ui"),
     ("calculator-*", "grid-entry", "polish-journeys", "hillclimb", "ui-fable-polish")),
    (("*/calculators/ratio_dialog.py", "*/calculators/controls.py", "*/calculators/effect_readout.py"),
     ("ratios-hr", "ratios-irr", "ui-design-direction")),
    (("src/rc_metastudio/importing/*", "src/rc_metastudio/forms/*import*.ui"),
     ("csv", "xlsx-import", "rm5-import", "polish-journeys", "ratios-hr", "ratios-irr")),
)
PACKAGE_SOURCE = ("*/automation.py", "*/r_runtime.py", "*/__main__.py", "src/rc_metastudio/__init__.py")
R_SOURCE = (
    "*/analysis/*", "*/results/*", "*/forms/*result*.ui", "*/forms/*plot*.ui",
    "*/r_runtime.py", "*/r_call_serialization.py", "*/rcmetar_identity.py", "*/r_backend*.py",
)


@dataclass(frozen=True)
class PathImpact:
    jobs: tuple[str, ...] = ()
    desktop: tuple[str, ...] = ()
    r_checks: bool = False


ALL = PathImpact((*QT, SOURCE, *PACKAGES), ("*",), True)


def matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatchcase(path, pattern) for pattern in patterns)


def source_impact(path: str) -> PathImpact:
    r_checks = matches(path, R_SOURCE)
    packages = PACKAGES if matches(path, PACKAGE_SOURCE) else ()
    desktop = tuple(scenario for paths, scenarios in FEATURES if matches(path, paths) for scenario in scenarios)
    return PathImpact((*QT, SOURCE, *packages), desktop or ("*",), r_checks)


def impact(path: str) -> PathImpact:
    if matches(path, BROAD):
        return ALL
    if matches(path, ("*.md", "*.rst", "LICENSE*", "CITATION.cff", "docs/*", "artifacts/*")):
        return PathImpact()
    if matches(path, ("src/*", "*.ui")):
        return source_impact(path)
    if matches(path, ("scripts/*", "packaging/*", "delivery/*", "tests/packaging/*")):
        return PathImpact(PACKAGES)
    if matches(path, ("r/*", "tests/r_stack/*", "tests/analysis_regression/*")):
        return PathImpact((SOURCE,), ("*",), True)
    if matches(path, ("tests/e2e/*", "tests/fixtures/*", "sample_projects/*")):
        return PathImpact(desktop=("*",))
    if matches(path, ("tests/python/gui/*",)):
        return PathImpact(QT)
    if matches(path, ("tests/python/fast/*",)):
        return PathImpact()
    return ALL


def desktop_parts(patterns: set[str]) -> dict[str, str]:
    if "*" in patterns:
        return {str(shard): "" for shard in DESKTOP_SHARDS}
    if not patterns:
        return {}
    # Same ordering and duration lookup as the pytest collection hook.
    durations = json.loads((ROOT / "config/desktop-durations.json").read_text(encoding="utf-8"))
    nodes = [f"[{scenario}]" for scenario in QUALIFICATION_SCENARIOS]
    bins, _ = partition(nodes, durations)
    return {
        str(shard): ",".join(selected)
        for shard, nodes_in_shard in zip(DESKTOP_SHARDS, bins, strict=True)
        if (selected := [node[1:-1] for node in nodes_in_shard if matches(node[1:-1], tuple(patterns))])
    }


@dataclass(frozen=True)
class Plan:
    reasons: dict[str, list[str]]
    parts: dict[str, str]

    @property
    def jobs(self) -> list[str]:
        jobs = [job for job in JOBS if job in self.reasons]
        if self.parts:
            jobs.append(R)
        return jobs


def plan(paths: list[str], *, full: str = "", draft: bool = False) -> Plan:
    reasons: dict[str, list[str]] = {}
    desktop: set[str] = set()
    inputs = {full: ALL} if full else {path: impact(path) for path in sorted(set(paths))}
    for path, affected in inputs.items():
        for job in affected.jobs:
            if not draft or job not in OTHER_PACKAGES:
                reasons.setdefault(job, []).append(path)
        if affected.r_checks:
            reasons.setdefault("checks", []).append(path)
        if affected.desktop:
            desktop.update(affected.desktop)
            reasons.setdefault("desktop", []).append(path)
    parts = {"checks": ""} if "checks" in reasons else {}
    parts.update(desktop_parts(desktop))
    return Plan(reasons, parts)


def git_paths(*args: str) -> list[str]:
    output = subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8")
    return [path for path in output.split("\0") if path]


def changed_paths(base: str, *, working_tree: bool = False) -> list[str]:
    target = [] if working_tree else ["HEAD"]
    # Treat renames as deletion plus addition so both boundaries are selected.
    return git_paths("diff", "--no-renames", "--name-only", "-z", base, *target, "--")


def lane_reads(path: str, lane: str) -> bool:
    if lane == "quick":
        return not path.startswith("artifacts/")
    if lane == "code-health":
        return matches(path, ("scripts/verify.py", "scripts/code_health.py", "config/code-health.json"))
    affected = impact(path)
    if lane in PACKAGES:
        return bool(affected.jobs or affected.desktop or affected.r_checks)
    shared = matches(path, ("src/*", "r/*", "tests/fixtures/*", "tests/python/fixtures/*"))
    if lane == "checks":
        return affected.r_checks or shared or matches(path, ("tests/python/fast/test_packaged_summary_identity.py",))
    if lane.startswith("desktop-"):
        return bool(affected.desktop) or shared
    return lane in affected.jobs or shared or (
        lane == SOURCE and path.startswith(("tests/python/fast/", "tests/packaging/contract/"))
    )


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--full")
    cli.add_argument("--draft", action="store_true")
    args = cli.parse_args()
    if args.full:
        selected = plan([], full=args.full, draft=args.draft)
    else:
        paths = sys.stdin.buffer.read().decode("utf-8").split("\0")
        selected = plan([path for path in paths if path], draft=args.draft)
    for name, value in (
        ("lanes", selected.jobs),
        ("targets", TARGETS[:1] if args.draft else TARGETS),
        ("r-stack-parts", [{"part": part, "scenarios": scenarios} for part, scenarios in selected.parts.items()]),
    ):
        print(f"{name}={json.dumps(value, separators=(',', ':'))}")
    print(json.dumps(selected.reasons, ensure_ascii=True), file=sys.stderr)


if __name__ == "__main__":
    main()
