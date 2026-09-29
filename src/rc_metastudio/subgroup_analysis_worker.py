# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Attach the frozen subgroup report to an ordinary RCMetaR result."""

from __future__ import annotations

from dataclasses import replace
from types import MappingProxyType

from rc_metastudio.analysis_results import AnalysisResult, ResultSection
from rc_metastudio.subgroup_analysis import (
    SubgroupAnalysisResult,
    SubgroupPlan,
    parse_subgroup_result,
    render_subgroup_result,
    subgroup_figure_available,
)


def attach_subgroup_report(
    result: AnalysisResult, plan: SubgroupPlan
) -> tuple[AnalysisResult, SubgroupAnalysisResult]:
    """Parse authority output and add an offline-visible subgroup summary."""
    summary = result.texts.get("Subgroup Summary")
    if summary is None:
        raise ValueError("RCMetaR did not return a Subgroup Summary section")
    numerics = parse_subgroup_result(
        summary,
        plan,
        figure_available=subgroup_figure_available(result),
    )
    summary_key = "subgroup_analysis_summary"
    if summary_key in result.texts or any(
        section.semantic_id == "subgroup.summary" for section in result.sections
    ):
        raise ValueError("RCMetaR subgroup result conflicts with the saved summary section")
    texts = dict(result.texts)
    texts[summary_key] = render_subgroup_result(numerics, plan)
    next_order = max((section.order for section in result.sections), default=-1) + 1
    section = ResultSection(
        semantic_id="subgroup.summary",
        kind="text",
        order=next_order,
        title="Subgroup analysis summary",
        value=texts[summary_key],
        source_key=summary_key,
    )
    return (
        replace(
            result,
            texts=MappingProxyType(texts),
            sections=(*result.sections, section),
            subgroup_numerics=MappingProxyType(numerics.to_mapping()),
            subgroup_plan=MappingProxyType(plan.to_mapping()),
        ),
        numerics,
    )
