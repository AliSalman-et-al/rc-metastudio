# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Leave-one-out orchestration over immutable input snapshots."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, is_dataclass, replace
import math
from typing import Any, Literal, TypeVar, cast


SnapshotT = TypeVar("SnapshotT")
NumberStatus = Literal["available", "not_estimable", "not_available"]
RowStatus = Literal["available", "not_estimable", "failed"]
StudyIdentity = int | str


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value


def _study_id(value: object) -> StudyIdentity:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("study identity must be integer or text")
    if isinstance(value, str) and not value:
        raise ValueError("study identity must be non-empty")
    return value


@dataclass(frozen=True, slots=True)
class LeaveOneOutNumber:
    status: NumberStatus
    value: float | None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.status == "available":
            _number(self.value, "available result")
            if self.reason is not None:
                raise ValueError("available results cannot have a reason")
        elif (
            self.status not in {"not_estimable", "not_available"}
            or self.value is not None
            or not isinstance(self.reason, str)
            or not self.reason.strip()
        ):
            raise ValueError("unavailable results need a reason and no value")

    @classmethod
    def available(cls, value: int | float) -> LeaveOneOutNumber:
        return cls("available", _number(value, "result"))

    @classmethod
    def unavailable(
        cls, status: Literal["not_estimable", "not_available"], reason: str
    ) -> LeaveOneOutNumber:
        return cls(status, None, _text(reason, "result reason"))

    def to_mapping(self) -> dict[str, object]:
        return {"status": self.status, "value": self.value, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class NamedHeterogeneity:
    name: str
    value: float

    def __post_init__(self) -> None:
        _text(self.name, "heterogeneity name")
        _number(self.value, f"heterogeneity {self.name}")

    def to_mapping(self) -> dict[str, object]:
        return {"name": self.name, "value": self.value}


@dataclass(frozen=True, slots=True)
class LeaveOneOutEstimate:
    """One ordinary authority fit's pooled values on a named scale."""

    effect_scale: str
    estimate: LeaveOneOutNumber
    lower_bound: LeaveOneOutNumber
    upper_bound: LeaveOneOutNumber
    heterogeneity: tuple[NamedHeterogeneity, ...] = ()

    def __post_init__(self) -> None:
        _text(self.effect_scale, "effect scale")
        if len({value.name for value in self.heterogeneity}) != len(self.heterogeneity):
            raise ValueError("heterogeneity names must be unique")
        if all(
            value.status == "available"
            for value in (self.lower_bound, self.estimate, self.upper_bound)
        ):
            lower, estimate, upper = cast(
                tuple[float, float, float],
                (self.lower_bound.value, self.estimate.value, self.upper_bound.value),
            )
            if not lower <= estimate <= upper:
                raise ValueError("interval must contain its estimate")

    @classmethod
    def not_estimable(cls, reason: str, *, effect_scale: str) -> LeaveOneOutEstimate:
        value = LeaveOneOutNumber.unavailable("not_estimable", reason)
        return cls(effect_scale, value, value, value)


@dataclass(frozen=True, slots=True)
class LeaveOneOutRow:
    kind: Literal["baseline", "omission"]
    label: str
    study_id: StudyIdentity | None
    remaining_study_count: int
    status: RowStatus
    estimate: LeaveOneOutNumber
    lower_bound: LeaveOneOutNumber
    upper_bound: LeaveOneOutNumber
    heterogeneity: tuple[NamedHeterogeneity, ...]
    change_from_baseline: LeaveOneOutNumber
    change_scale: str
    reason: str | None

    def __post_init__(self) -> None:
        _text(self.label, "row label")
        _text(self.change_scale, "change scale")
        if self.kind not in {"baseline", "omission"}:
            raise ValueError("row kind is invalid")
        if (self.kind == "baseline") != (self.study_id is None):
            raise ValueError("only omission rows have a study identity")
        if self.study_id is not None:
            _study_id(self.study_id)
        if type(self.remaining_study_count) is not int or self.remaining_study_count < 0:
            raise ValueError("remaining study count must be a non-negative integer")
        if self.status not in {"available", "not_estimable", "failed"}:
            raise ValueError("row status is invalid")
        if self.status == "available" and self.estimate.status != "available":
            raise ValueError("available rows need an estimate")
        if self.status != "available" and not self.reason:
            raise ValueError("failed or non-estimable rows need a reason")

    def to_mapping(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "label": self.label,
            "study_id": self.study_id,
            "remaining_study_count": self.remaining_study_count,
            "status": self.status,
            "estimate": self.estimate.to_mapping(),
            "lower_bound": self.lower_bound.to_mapping(),
            "upper_bound": self.upper_bound.to_mapping(),
            "heterogeneity": [value.to_mapping() for value in self.heterogeneity],
            "change_from_baseline": self.change_from_baseline.to_mapping(),
            "change_scale": self.change_scale,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class LeaveOneOutReport:
    data_type: str
    method: str
    metric: str
    effect_scale: str
    outcome: str
    time_point: str
    rows: tuple[LeaveOneOutRow, ...]

    def __post_init__(self) -> None:
        for label, value in (
            ("data type", self.data_type),
            ("method", self.method),
            ("metric", self.metric),
            ("effect scale", self.effect_scale),
            ("outcome", self.outcome),
            ("time point", self.time_point),
        ):
            _text(value, label)
        if self.data_type not in {"binary", "continuous", "diagnostic"}:
            raise ValueError("data type is invalid")
        if len(self.rows) < 2 or self.rows[0].kind != "baseline":
            raise ValueError("report must start with a baseline and include omission rows")
        if self.rows[0].label != "All included studies":
            raise ValueError("baseline label is invalid")
        omissions = self.rows[1:]
        if any(row.kind != "omission" for row in omissions):
            raise ValueError("remaining report rows must be omissions")
        if self.rows[0].remaining_study_count != len(omissions):
            raise ValueError("baseline count must match the omission rows")
        if any(row.remaining_study_count != len(omissions) - 1 for row in omissions):
            raise ValueError("omission counts must match the included study count")
        ids = [row.study_id for row in omissions]
        if len(ids) != len(set(ids)):
            raise ValueError("omission study identities must be unique")

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": 1,
            "data_type": self.data_type,
            "method": self.method,
            "metric": self.metric,
            "effect_scale": self.effect_scale,
            "change_convention": "omitted_minus_baseline",
            "outcome": self.outcome,
            "time_point": self.time_point,
            "rows": [row.to_mapping() for row in self.rows],
        }


def run_leave_one_out(
    snapshot: SnapshotT,
    fit_standard: Callable[[SnapshotT], LeaveOneOutEstimate],
    *,
    data_type: str,
    method: str,
    effect_scale: str,
) -> LeaveOneOutReport:
    """Fit all included studies and each omission without changing the snapshot."""
    studies = _snapshot_studies(snapshot)
    study_ids = [_study_identity(study) for study in studies]
    if len(study_ids) != len(set(study_ids)):
        raise ValueError("snapshot study identities must be unique")
    outcome = _text(getattr(snapshot, "outcome", None), "outcome")
    time_point = _text(
        getattr(snapshot, "time_point", getattr(snapshot, "follow_up", None)),
        "time point",
    )
    metric = _text(getattr(snapshot, "metric", None), "metric")
    for label, value in (("data type", data_type), ("method", method), ("effect scale", effect_scale)):
        _text(value, label)
    if data_type not in {"binary", "continuous", "diagnostic"}:
        raise ValueError("data type is invalid")

    baseline, baseline_error = _fit(fit_standard, snapshot, effect_scale)
    rows = [
        _row(
            "baseline",
            "All included studies",
            None,
            len(studies),
            baseline,
            baseline,
            effect_scale,
            baseline_error,
        )
    ]
    for index, study in enumerate(studies):
        study_id, name = _study_identity(study), _study_name(study)
        if len(studies) == 1:
            reason = "No studies remain after omitting this study."
            omission = LeaveOneOutEstimate.not_estimable(reason, effect_scale=effect_scale)
            error = None
        else:
            try:
                subset = _snapshot_without(snapshot, index)
                omission, error = _fit(fit_standard, subset, effect_scale)
            except Exception as failure:
                error = str(failure).strip() or type(failure).__name__
                omission = LeaveOneOutEstimate.not_estimable(error, effect_scale=effect_scale)
        rows.append(
            _row(
                "omission",
                f"Omitting {name}",
                study_id,
                len(studies) - 1,
                omission,
                baseline,
                effect_scale,
                error,
            )
        )

    return LeaveOneOutReport(
        data_type, method, metric, effect_scale, outcome, time_point, tuple(rows)
    )


def _snapshot_studies(snapshot: object) -> tuple[object, ...]:
    if not is_dataclass(snapshot) or isinstance(snapshot, type):
        raise ValueError("leave-one-out requires a frozen dataclass snapshot")
    params = getattr(type(snapshot), "__dataclass_params__", None)
    studies = getattr(snapshot, "studies", None)
    if params is None or not params.frozen or not isinstance(studies, tuple) or not studies:
        raise ValueError("leave-one-out requires a non-empty frozen study snapshot")
    covariates = getattr(snapshot, "covariates", ())
    if not isinstance(covariates, tuple) or any(
        not isinstance(getattr(item, "values", None), tuple)
        or len(item.values) != len(studies)
        for item in covariates
    ):
        raise ValueError("snapshot covariates must align with its study rows")
    return studies


def _study_identity(study: object) -> StudyIdentity:
    raw = getattr(study, "id", getattr(study, "study_id", None))
    return _study_id(raw)


def _study_name(study: object) -> str:
    return _text(getattr(study, "name", None), "study name")


def _snapshot_without(snapshot: SnapshotT, omitted_index: int) -> SnapshotT:
    studies = cast(tuple[object, ...], getattr(snapshot, "studies"))
    keep = tuple(index for index in range(len(studies)) if index != omitted_index)
    updates: dict[str, object] = {
        "studies": tuple(studies[index] for index in keep)
    }
    if hasattr(snapshot, "covariates"):
        covariates = getattr(snapshot, "covariates")
        updates["covariates"] = tuple(
            replace(item, values=tuple(item.values[index] for index in keep))
            for item in covariates
        )
    return cast(SnapshotT, replace(cast(Any, snapshot), **updates))


def _fit(
    fit_standard: Callable[[SnapshotT], LeaveOneOutEstimate],
    snapshot: SnapshotT,
    effect_scale: str,
) -> tuple[LeaveOneOutEstimate, str | None]:
    try:
        result = fit_standard(snapshot)
        if not isinstance(result, LeaveOneOutEstimate):
            raise TypeError("standard fit did not return LeaveOneOutEstimate")
        if result.effect_scale != effect_scale:
            raise ValueError("standard fit returned a different effect scale")
        return result, None
    except Exception as error:
        reason = str(error).strip() or type(error).__name__
        return LeaveOneOutEstimate.not_estimable(reason, effect_scale=effect_scale), reason


def _row(
    kind: Literal["baseline", "omission"],
    label: str,
    study_id: StudyIdentity | None,
    remaining_count: int,
    result: LeaveOneOutEstimate,
    baseline: LeaveOneOutEstimate,
    effect_scale: str,
    error: str | None,
) -> LeaveOneOutRow:
    if error is not None:
        unavailable = LeaveOneOutNumber.unavailable("not_available", error)
        return LeaveOneOutRow(
            kind,
            label,
            study_id,
            remaining_count,
            "failed",
            unavailable,
            unavailable,
            unavailable,
            (),
            unavailable,
            effect_scale,
            error,
        )

    status: RowStatus = (
        "available" if result.estimate.status == "available" else "not_estimable"
    )
    change = _change(result.estimate, baseline.estimate, kind)
    return LeaveOneOutRow(
        kind,
        label,
        study_id,
        remaining_count,
        status,
        result.estimate,
        result.lower_bound,
        result.upper_bound,
        result.heterogeneity,
        change,
        effect_scale,
        result.estimate.reason,
    )


def _change(
    estimate: LeaveOneOutNumber,
    baseline: LeaveOneOutNumber,
    kind: Literal["baseline", "omission"],
) -> LeaveOneOutNumber:
    if kind == "baseline" and estimate.status == "available":
        return LeaveOneOutNumber.available(0)
    if estimate.status != "available":
        return LeaveOneOutNumber.unavailable(
            "not_available", "The fit has no available estimate for comparison."
        )
    if baseline.status != "available":
        return LeaveOneOutNumber.unavailable(
            "not_available", "The all-included baseline estimate is unavailable."
        )
    return LeaveOneOutNumber.available(
        cast(float, estimate.value) - cast(float, baseline.value)
    )
