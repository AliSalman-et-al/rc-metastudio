# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Schedule desktop verification scenarios across CI shards."""

from collections.abc import Mapping, Sequence


DESKTOP_SHARDS = (1, 2, 3)


def partition(
    nodes: Sequence[str], measured_seconds: Mapping[str, float]
) -> tuple[list[list[str]], list[float]]:
    bins: list[list[str]] = [[] for _ in DESKTOP_SHARDS]
    loads = [0.0 for _ in DESKTOP_SHARDS]

    def duration(node: str) -> float:
        scenario = node.rsplit("[", 1)[-1].removesuffix("]")
        return float(measured_seconds.get(scenario, 60.0))

    for node in sorted(nodes, key=lambda node: (-duration(node), node)):
        index = min(range(len(bins)), key=lambda index: (loads[index], index))
        bins[index].append(node)
        loads[index] += duration(node)
    return bins, loads
