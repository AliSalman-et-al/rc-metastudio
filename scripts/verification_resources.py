"""Bound independent offscreen desktop workers by observed host capacity."""

import os
from pathlib import Path

import psutil


def desktop_resources() -> dict[str, int]:
    try:
        cpus = os.cpu_count() or 1
        process = psutil.Process()
        if hasattr(process, "cpu_affinity"):
            cpus = min(cpus, len(process.cpu_affinity()))
        available = psutil.virtual_memory().available
    except (OSError, psutil.Error):
        return {"cpus": 1, "available_bytes": 0, "workers": 1}
    for group in _cgroup_ancestors():
        cpus, available = _cgroup_limits(group, cpus, available)
    # Packed publication TIFF peaks at 1.2 GiB; leave headroom per child and host.
    workers = max(1, min(3, cpus - 1, (available - 1024**3) // (2 * 1024**3)))
    return {"cpus": cpus, "available_bytes": available, "workers": workers}


def _cgroup_ancestors():
    membership = Path("/proc/self/cgroup")
    if not membership.exists():
        return
    for line in membership.read_text().splitlines():
        if not line.startswith("0::"):
            continue
        group = Path("/sys/fs/cgroup") / line.removeprefix("0::").lstrip("/")
        while group.is_relative_to("/sys/fs/cgroup"):
            yield group
            group = group.parent


def _cgroup_limits(group: Path, cpus: int, available: int) -> tuple[int, int]:
    cpu_limit = group / "cpu.max"
    memory_limit = group / "memory.max"
    if cpu_limit.is_file():
        quota, period = cpu_limit.read_text().split()
        if quota != "max":
            cpus = min(cpus, max(1, int(quota) // int(period)))
    if memory_limit.is_file() and memory_limit.read_text().strip() != "max":
        stats = dict(line.split() for line in (group / "memory.stat").read_text().splitlines())
        # Inactive file pages are reclaimable, including bytes read to
        # validate cached evidence. Count resident working memory.
        working = int((group / "memory.current").read_text()) - int(stats.get("inactive_file", "0"))
        remaining = int(memory_limit.read_text()) - working
        available = min(available, max(0, remaining))
    return cpus, available
