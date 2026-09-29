# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Retain independently fitted sequential steps when a native sequence aborts."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace

from rc_metastudio.analysis_adapter import AnalysisRequest
from rc_metastudio.cumulative_analysis import (
    CumulativeAnalysisSnapshot,
    CumulativeInputSnapshot,
    run_cumulative_analysis,
)
from rc_metastudio.leave_one_out import run_leave_one_out
from rc_metastudio.sequential_result_adapter import (
    effect_scale_for_request,
    leave_one_out_estimate_from_model,
)


StandardFit = Callable[[CumulativeInputSnapshot, AnalysisRequest], Mapping[str, object]]


def recover_sequential_steps(
    snapshot: CumulativeInputSnapshot | CumulativeAnalysisSnapshot,
    request: AnalysisRequest,
    fit_standard: StandardFit,
) -> dict[str, object]:
    """Use ordinary authority fits without replacing failed rows with estimates."""
    if request.workflow == "cumulative":
        if not isinstance(snapshot, CumulativeAnalysisSnapshot):
            raise ValueError("cumulative recovery needs the frozen analytical sequence")
        result = run_cumulative_analysis(
            snapshot,
            request,
            lambda prefix, standard: {"res": fit_standard(prefix, standard)},
        )
        return {"cumulative_numerics": result.to_mapping()}
    if request.workflow != "leave-one-out" or isinstance(snapshot, CumulativeAnalysisSnapshot):
        raise ValueError("unsupported sequential recovery request")
    scale = effect_scale_for_request(snapshot, request)
    standard = replace(request, workflow="standard")
    report = run_leave_one_out(
        snapshot,
        lambda subset: leave_one_out_estimate_from_model(
            dict(fit_standard(subset, standard)), scale
        ),
        data_type=request.data_type,
        method=request.method,
        effect_scale=scale,
    )
    return {"leave_one_out_numerics": report.to_mapping()}
