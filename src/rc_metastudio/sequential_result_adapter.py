# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read RCMetaR's sequential numeric table with the frozen study identities."""

from __future__ import annotations

import math
from typing import Any

from rc_metastudio.analysis_adapter import AnalysisRequest
from rc_metastudio.cumulative_analysis import (
    CumulativeAnalysisResult,
    CumulativeAnalysisSnapshot,
    cumulative_step_from_backend,
)
from rc_metastudio.leave_one_out import (
    LeaveOneOutEstimate,
    LeaveOneOutNumber,
    LeaveOneOutReport,
    NamedHeterogeneity,
    run_leave_one_out,
)


def _numeric_rows(bridge: Any, expected: int) -> tuple[dict[str, object], ...]:
    raw = bridge.ro.globalenv["result"]
    numeric_section = "res.summary" if "res.summary" in tuple(raw.names) else "res"
    table = raw.rx2(numeric_section).rx2("summary.table")
    columns = {
        str(name): tuple(table.rx2(str(name)))
        for name in tuple(table.names)
    }
    if not columns or any(len(values) != expected for values in columns.values()):
        raise ValueError("RCMetaR sequential result does not match the frozen study sequence")
    return tuple(
        {name: values[index] for name, values in columns.items()}
        for index in range(expected)
    )


def cumulative_result_from_backend(
    snapshot: CumulativeAnalysisSnapshot, bridge: Any
) -> CumulativeAnalysisResult:
    rows = _numeric_rows(bridge, len(snapshot.sequence))
    steps = tuple(
        cumulative_step_from_backend(
            order,
            {"res": {**row, "b": row.get("estimate")}},
        )
        for order, row in zip(snapshot.sequence, rows)
    )
    status = "complete" if all(step.status == "complete" for step in steps) else "partial"
    return CumulativeAnalysisResult(1, status, snapshot.ordering, steps)


def leave_one_out_result_from_backend(
    snapshot: object, request: AnalysisRequest, bridge: Any
) -> LeaveOneOutReport:
    studies = getattr(snapshot, "studies")
    rows = _numeric_rows(bridge, len(studies) + 1)
    native_scale = effect_scale_for_request(snapshot, request)
    source_ids = tuple(getattr(study, "id", getattr(study, "study_id", None)) for study in studies)
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("leave-one-out inputs have duplicate study identities")

    def fit(subset: object) -> LeaveOneOutEstimate:
        remaining = {getattr(study, "id", getattr(study, "study_id", None)) for study in getattr(subset, "studies")}
        omitted = set(source_ids) - remaining
        if len(omitted) > 1:
            raise ValueError("leave-one-out subset omits multiple studies")
        index = 0 if not omitted else source_ids.index(next(iter(omitted))) + 1
        return leave_one_out_estimate_from_model(rows[index], native_scale)

    return run_leave_one_out(
        snapshot,
        fit,
        data_type=request.data_type,
        method=request.method,
        effect_scale=native_scale,
    )


def effect_scale_for_request(snapshot: object, request: AnalysisRequest) -> str:
    return {
        "OR": "log odds ratio",
        "RR": "log risk ratio",
        "RD": "risk difference",
        "AS": "arcsine difference",
        "YUQ": "Yule's Q",
        "YUY": "Yule's Y",
        "Sens": "logit sensitivity",
        "Spec": "logit specificity",
        "PLR": "log positive likelihood ratio",
        "NLR": "log negative likelihood ratio",
        "DOR": "log diagnostic odds ratio",
    }.get(request.metric, getattr(snapshot, "effect_scale", f"{request.metric} calculation scale"))


def leave_one_out_estimate_from_model(
    model: dict[str, object], effect_scale: str
) -> LeaveOneOutEstimate:
    def value(name: str) -> LeaveOneOutNumber:
        number = _finite_scalar(model.get(name))
        if number is None:
            return LeaveOneOutNumber.unavailable("not_estimable", f"RCMetaR did not return finite {name}.")
        return LeaveOneOutNumber.available(number)

    heterogeneity_values = []
    for name in ("Q", "tau2", "I2", "H2"):
        number = _finite_scalar(model.get(name))
        if number is not None:
            heterogeneity_values.append(NamedHeterogeneity(name, number))
    return LeaveOneOutEstimate(
        effect_scale,
        value("estimate"),
        value("ci.lb"),
        value("ci.ub"),
        tuple(heterogeneity_values),
    )


def _finite_scalar(raw: object) -> float | None:
    if isinstance(raw, (list, tuple)) and len(raw) == 1:
        raw = raw[0]
    if isinstance(raw, bool) or not isinstance(raw, (float, int)):
        return None
    number = float(raw)
    return number if math.isfinite(number) else None
