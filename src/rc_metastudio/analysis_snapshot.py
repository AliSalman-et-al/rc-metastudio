# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Immutable, JSON-safe inputs for isolated analysis workers."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TypeAlias

from rc_metastudio.meta_globals import BINARY_TWO_ARM_METRICS, CONTINUOUS


SnapshotValue: TypeAlias = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class BinaryStudyInput:
    id: int
    name: str
    year: int | None
    estimate: float | None
    standard_error: float | None
    treatment_events: int | None
    treatment_total: int | None
    control_events: int | None
    control_total: int | None

    def to_mapping(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "year": self.year,
            "estimate": self.estimate,
            "standard_error": self.standard_error,
            "treatment_events": self.treatment_events,
            "treatment_total": self.treatment_total,
            "control_events": self.control_events,
            "control_total": self.control_total,
        }


@dataclass(frozen=True, slots=True)
class BinaryCovariateInput:
    name: str
    data_type: str
    values: tuple[SnapshotValue, ...]

    def to_mapping(self) -> dict[str, object]:
        return {"name": self.name, "data_type": self.data_type, "values": list(self.values)}


@dataclass(frozen=True, slots=True)
class BinaryInputSnapshot:
    """The selected binary data state as it existed at submit time."""

    version: int
    outcome: str
    time_point: str
    groups: tuple[str, str]
    metric: str
    raw_counts_available: bool
    studies: tuple[BinaryStudyInput, ...]
    covariates: tuple[BinaryCovariateInput, ...]

    def __post_init__(self) -> None:
        if self.version != 1:
            raise ValueError(f"unsupported binary input snapshot version: {self.version}")
        if not self.outcome or not self.time_point:
            raise ValueError("binary analysis requires a selected outcome and time point")
        if self.metric not in BINARY_TWO_ARM_METRICS:
            raise ValueError("isolated standard analysis requires a two-arm binary measure")
        if len(self.groups) != 2 or not all(self.groups):
            raise ValueError("binary analysis requires two selected study arms")
        if not self.studies:
            raise ValueError("include at least one study before running the analysis")
        if len({study.id for study in self.studies}) != len(self.studies):
            raise ValueError("binary input snapshot contains duplicate study identities")
        if len({covariate.name for covariate in self.covariates}) != len(self.covariates):
            raise ValueError("binary input snapshot contains duplicate covariates")
        for covariate in self.covariates:
            if len(covariate.values) != len(self.studies):
                raise ValueError("binary covariate values do not match the study rows")
        for study in self.studies:
            for number, label in (
                (study.estimate, "study estimate"),
                (study.standard_error, "study standard error"),
            ):
                if number is not None and not math.isfinite(number):
                    raise ValueError(f"{label} must be finite")
            if study.standard_error is not None and study.standard_error < 0:
                raise ValueError("study standard error cannot be negative")
            if self.raw_counts_available:
                _validate_arm(study.treatment_events, study.treatment_total, "treatment")
                _validate_arm(study.control_events, study.control_total, "control")

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "outcome": self.outcome,
            "time_point": self.time_point,
            "groups": list(self.groups),
            "metric": self.metric,
            "raw_counts_available": self.raw_counts_available,
            "studies": [study.to_mapping() for study in self.studies],
            "covariates": [covariate.to_mapping() for covariate in self.covariates],
        }


@dataclass(frozen=True, slots=True)
class BinaryAnalysisEditCopy:
    """Run-owned inputs and effective request retained by ResultsWindow."""

    input_snapshot: BinaryInputSnapshot
    effective_request: object


def _validate_arm(events: int | None, total: int | None, label: str) -> None:
    if events is None or total is None:
        raise ValueError(f"included studies need complete {label} event counts")
    if events < 0 or total < 0 or events > total:
        raise ValueError(f"{label} events must be between zero and the arm total")


def freeze_binary_input(model: object) -> BinaryInputSnapshot:
    """Copy the current included two-arm binary rows into a validated snapshot."""
    if getattr(model, "current_effect", None) not in BINARY_TWO_ARM_METRICS:
        raise ValueError("isolated standard analysis requires a two-arm binary measure")
    outcome = getattr(model, "current_outcome_name", None)
    follow_up = model.get_current_follow_up_name()
    groups = tuple(model.get_current_groups())
    studies = tuple(model.get_studies(only_if_included=True))
    study_ids = [study.id for study in studies]
    estimates, standard_errors = model.get_current_estimates_and_standard_errors(
        only_if_included=True, only_these_studies=study_ids
    )
    raw_rows = model.get_current_raw_data(
        only_if_included=True, only_these_studies=study_ids
    )
    raw_available = bool(studies) and all(
        len(row) >= 4 and all(value not in (None, "") for value in row[:4])
        for row in raw_rows
    )
    if len(estimates) != len(studies) or len(standard_errors) != len(studies):
        raise ValueError("binary estimates do not match the included study rows")
    if len(raw_rows) != len(studies):
        raise ValueError("binary raw data do not match the included study rows")

    def number(value: object, label: str) -> float | None:
        if value in (None, ""):
            return None
        if isinstance(value, bool):
            raise ValueError(f"{label} must be numeric")
        try:
            result = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{label} must be numeric") from error
        if not math.isfinite(result):
            raise ValueError(f"{label} must be finite")
        return result

    def count(value: object, label: str) -> int | None:
        parsed = number(value, label)
        if parsed is None:
            return None
        if not parsed.is_integer():
            raise ValueError(f"{label} must be a whole number")
        return int(parsed)

    rows = []
    for index, study in enumerate(studies):
        raw = list(raw_rows[index])
        raw.extend([None] * max(0, 4 - len(raw)))
        rows.append(
            BinaryStudyInput(
                id=int(study.id),
                name=str(study.name),
                year=None if study.year in (None, "") else int(study.year),
                estimate=number(estimates[index], "study estimate"),
                standard_error=number(standard_errors[index], "study standard error"),
                treatment_events=count(raw[0], "treatment events"),
                treatment_total=count(raw[1], "treatment total"),
                control_events=count(raw[2], "control events"),
                control_total=count(raw[3], "control total"),
            )
        )

    snapshot_covariates = []
    for covariate in model.dataset.covariates:
        by_id = model.dataset.get_covariate_values(covariate.name, ids_for_keys=True)
        values = tuple(_snapshot_value(by_id.get(study_id)) for study_id in study_ids)
        snapshot_covariates.append(
            BinaryCovariateInput(
                str(covariate.name),
                "continuous" if covariate.data_type == CONTINUOUS else "factor",
                values,
            )
        )
    return BinaryInputSnapshot(
        1,
        str(outcome or ""),
        str(follow_up or ""),
        (str(groups[0]), str(groups[1])),
        str(model.current_effect),
        raw_available,
        tuple(rows),
        tuple(snapshot_covariates),
    )


def _snapshot_value(value: object) -> SnapshotValue:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise TypeError("covariate values must be finite JSON-safe values")
