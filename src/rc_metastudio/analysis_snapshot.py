# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Immutable, JSON-safe inputs for isolated analysis workers."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, SupportsFloat, TypeAlias, TypedDict

from rc_metastudio.meta_globals import (
    BINARY_ONE_ARM_METRICS,
    BINARY_TWO_ARM_METRICS,
    CONTINUOUS,
)


SnapshotValue: TypeAlias = str | int | float | bool | None


class _BinaryStudyModel(Protocol):
    id: int
    name: str
    year: int | str | None


class _BinaryCovariate(Protocol):
    name: str
    data_type: int


class _BinaryDataset(Protocol):
    covariates: Sequence[_BinaryCovariate]

    def get_covariate_values(
        self, name: str, ids_for_keys: bool = False
    ) -> Mapping[int, object]: ...


class _BinaryInputModel(Protocol):
    current_effect: str | None
    current_outcome_name: str | None
    dataset: _BinaryDataset

    def get_current_follow_up_name(self) -> str | None: ...

    def get_current_groups(self) -> Sequence[str]: ...

    def get_studies(self, only_if_included: bool) -> Sequence[_BinaryStudyModel]: ...

    def get_current_raw_data(
        self, only_if_included: bool, only_these_studies: Sequence[int]
    ) -> Sequence[Sequence[object]]: ...

    def get_current_estimates_and_standard_errors(
        self, only_if_included: bool, only_these_studies: Sequence[int]
    ) -> tuple[Sequence[object], Sequence[object]]: ...


class _StudyMetadata(TypedDict):
    id: int
    name: str
    year: int | None
    estimate: float | None
    standard_error: float | None


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
class SingleArmBinaryStudyInput:
    id: int
    name: str
    year: int | None
    estimate: float | None
    standard_error: float | None
    events: int | None
    total: int | None

    def to_mapping(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "year": self.year,
            "estimate": self.estimate,
            "standard_error": self.standard_error,
            "events": self.events,
            "total": self.total,
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
    groups: tuple[str, ...]
    metric: str
    raw_counts_available: bool
    studies: tuple[BinaryStudyInput | SingleArmBinaryStudyInput, ...]
    covariates: tuple[BinaryCovariateInput, ...]

    def __post_init__(self) -> None:
        one_arm = _validate_binary_snapshot_identity(self)
        _validate_binary_snapshot_rows(self, one_arm)

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


def _validate_binary_snapshot_identity(snapshot: BinaryInputSnapshot) -> bool:
    _validate_binary_snapshot_header(snapshot)
    one_arm = _binary_metric_mode(snapshot.metric)[1]
    _validate_binary_groups(snapshot.groups, one_arm)
    return one_arm


def _validate_binary_snapshot_header(snapshot: BinaryInputSnapshot) -> None:
    if snapshot.version != 1:
        raise ValueError(f"unsupported binary input snapshot version: {snapshot.version}")
    if not snapshot.outcome or not snapshot.time_point:
        raise ValueError("binary analysis requires a selected outcome and time point")


def _binary_metric_mode(metric: str | None) -> tuple[str, bool]:
    if metric in BINARY_ONE_ARM_METRICS:
        return metric, True
    if metric in BINARY_TWO_ARM_METRICS:
        return metric, False
    raise ValueError("isolated standard analysis requires a supported binary measure")


def _validate_binary_groups(groups: tuple[str, ...], one_arm: bool) -> None:
    expected_groups = 1 if one_arm else 2
    if len(groups) != expected_groups or not all(groups):
        label = "one" if one_arm else "two"
        raise ValueError(f"binary analysis requires {label} selected study arm(s)")


def _validate_binary_snapshot_rows(
    snapshot: BinaryInputSnapshot, one_arm: bool
) -> None:
    if not snapshot.studies:
        raise ValueError("include at least one study before running the analysis")
    _validate_binary_study_identities(snapshot.studies)
    _validate_binary_covariates(snapshot.covariates, len(snapshot.studies))
    for study in snapshot.studies:
        _validate_binary_study_input(
            study, one_arm, snapshot.raw_counts_available, snapshot.groups
        )


def _validate_binary_study_identities(
    studies: tuple[BinaryStudyInput | SingleArmBinaryStudyInput, ...]
) -> None:
    if len({study.id for study in studies}) != len(studies):
        raise ValueError("binary input snapshot contains duplicate study identities")


def _validate_binary_covariates(
    covariates: tuple[BinaryCovariateInput, ...], study_count: int
) -> None:
    if len({covariate.name for covariate in covariates}) != len(covariates):
        raise ValueError("binary input snapshot contains duplicate covariates")
    if any(len(covariate.values) != study_count for covariate in covariates):
        raise ValueError("binary covariate values do not match the study rows")


def _validate_binary_study_input(
    study: BinaryStudyInput | SingleArmBinaryStudyInput,
    one_arm: bool,
    raw_counts_available: bool,
    groups: tuple[str, ...],
) -> None:
    _validate_binary_study_type(study, one_arm)
    _validate_binary_study_effects(study)
    _validate_binary_study_source(study, one_arm, raw_counts_available, groups)


def _validate_binary_study_type(
    study: BinaryStudyInput | SingleArmBinaryStudyInput, one_arm: bool
) -> None:
    if one_arm and not isinstance(study, SingleArmBinaryStudyInput):
        raise ValueError("single-arm binary data must use one-arm study rows")
    if not one_arm and not isinstance(study, BinaryStudyInput):
        raise ValueError("two-arm binary data must use two-arm study rows")


def _validate_binary_study_effects(
    study: BinaryStudyInput | SingleArmBinaryStudyInput,
) -> None:
    for number, label in (
        (study.estimate, "study estimate"),
        (study.standard_error, "study standard error"),
    ):
        if number is not None and not math.isfinite(number):
            raise ValueError(f"{label} must be finite")
    if study.standard_error is not None and study.standard_error < 0:
        raise ValueError("study standard error cannot be negative")


def _validate_binary_study_source(
    study: BinaryStudyInput | SingleArmBinaryStudyInput,
    one_arm: bool,
    raw_counts_available: bool,
    groups: tuple[str, ...],
) -> None:
    if raw_counts_available:
        _validate_binary_study_counts(study, groups)
        return
    if one_arm and isinstance(study, SingleArmBinaryStudyInput):
        if study.events is not None or study.total is not None:
            raise ValueError(
                "single-arm snapshots with raw counts must declare them as the input source"
            )


def _validate_binary_study_counts(
    study: BinaryStudyInput | SingleArmBinaryStudyInput, groups: tuple[str, ...]
) -> None:
    if isinstance(study, SingleArmBinaryStudyInput):
        _validate_arm(study.events, study.total, groups[0])
        return
    _validate_arm(study.treatment_events, study.treatment_total, "treatment")
    _validate_arm(study.control_events, study.control_total, "control")


def _validate_arm(events: int | None, total: int | None, label: str) -> None:
    if events is None or total is None:
        raise ValueError(f"included studies need complete {label} event counts")
    if events < 0 or total < 0 or events > total:
        raise ValueError(f"{label} events must be between zero and the arm total")


def freeze_binary_input(model: _BinaryInputModel) -> BinaryInputSnapshot:
    """Copy the selected included binary rows into a validated snapshot."""
    metric, one_arm = _binary_metric_mode(model.current_effect)
    outcome = model.current_outcome_name
    follow_up = model.get_current_follow_up_name()
    groups = _selected_binary_groups(model.get_current_groups(), one_arm)
    studies = tuple(model.get_studies(only_if_included=True))
    rows, raw_available = _freeze_binary_studies(model, studies, one_arm)
    study_ids = tuple(study.id for study in studies)
    snapshot_covariates = _freeze_binary_covariates(model.dataset, study_ids)
    return BinaryInputSnapshot(
        1,
        str(outcome or ""),
        str(follow_up or ""),
        groups,
        str(metric),
        raw_available,
        rows,
        snapshot_covariates,
    )


def _selected_binary_groups(groups: Sequence[str], one_arm: bool) -> tuple[str, ...]:
    if one_arm:
        return tuple(str(group) for group in groups[:1])
    return tuple(str(group) for group in groups)


def _freeze_binary_studies(
    model: _BinaryInputModel,
    studies: Sequence[_BinaryStudyModel],
    one_arm: bool,
) -> tuple[tuple[BinaryStudyInput | SingleArmBinaryStudyInput, ...], bool]:
    study_ids = [study.id for study in studies]
    raw_rows = model.get_current_raw_data(
        only_if_included=True, only_these_studies=study_ids
    )
    raw_available = _has_complete_raw_counts(raw_rows, len(studies), one_arm)
    if raw_available:
        # RCMetaR reconstructs study effects from the frozen counts in its own
        # process. Asking the live model for derived previews would start R here.
        estimates = (None,) * len(studies)
        standard_errors = (None,) * len(studies)
    else:
        estimates, standard_errors = model.get_current_estimates_and_standard_errors(
            only_if_included=True, only_these_studies=study_ids
        )
    if len(estimates) != len(studies) or len(standard_errors) != len(studies):
        raise ValueError("binary estimates do not match the included study rows")
    if len(raw_rows) != len(studies):
        raise ValueError("binary raw data do not match the included study rows")
    rows = tuple(
        _freeze_binary_study(
            study,
            raw_rows[index],
            estimates[index],
            standard_errors[index],
            one_arm,
        )
        for index, study in enumerate(studies)
    )
    return rows, raw_available


def _has_complete_raw_counts(
    rows: Sequence[Sequence[object]], study_count: int, one_arm: bool
) -> bool:
    width = 2 if one_arm else 4
    complete = tuple(_raw_counts_complete(row, width) for row in rows)
    available = bool(study_count) and all(complete)
    if not available and any(_raw_counts_present(row, width) for row in rows):
        arm_label = "single-arm" if one_arm else "two-arm"
        raise ValueError(
            f"{arm_label} included studies must all have complete event counts, "
            "or all use entered estimates"
        )
    return available


def _raw_counts_complete(row: Sequence[object], width: int) -> bool:
    return len(row) >= width and all(value not in (None, "") for value in row[:width])


def _raw_counts_present(row: Sequence[object], width: int) -> bool:
    return any(value not in (None, "") for value in row[:width])


def _freeze_binary_study(
    study: _BinaryStudyModel,
    raw_row: Sequence[object],
    estimate: object,
    standard_error: object,
    one_arm: bool,
) -> BinaryStudyInput | SingleArmBinaryStudyInput:
    width = 2 if one_arm else 4
    raw = list(raw_row)
    raw.extend([None] * max(0, width - len(raw)))
    common: _StudyMetadata = {
        "id": int(study.id),
        "name": str(study.name),
        "year": None if study.year in (None, "") else int(study.year),
        "estimate": _snapshot_number(estimate, "study estimate"),
        "standard_error": _snapshot_number(standard_error, "study standard error"),
    }
    if one_arm:
        return SingleArmBinaryStudyInput(
            **common,
            events=_snapshot_count(raw[0], "events"),
            total=_snapshot_count(raw[1], "total"),
        )
    return BinaryStudyInput(
        **common,
        treatment_events=_snapshot_count(raw[0], "treatment events"),
        treatment_total=_snapshot_count(raw[1], "treatment total"),
        control_events=_snapshot_count(raw[2], "control events"),
        control_total=_snapshot_count(raw[3], "control total"),
    )


def _snapshot_number(value: object, label: str) -> float | None:
    if value is None or (isinstance(value, str) and not value):
        return None
    if isinstance(value, bool) or not isinstance(value, (str, bytes, SupportsFloat)):
        raise ValueError(f"{label} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be numeric") from error
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _snapshot_count(value: object, label: str) -> int | None:
    parsed = _snapshot_number(value, label)
    if parsed is None:
        return None
    if parsed % 1 != 0:
        raise ValueError(f"{label} must be a whole number")
    return int(parsed)


def _freeze_binary_covariates(
    dataset: _BinaryDataset, study_ids: Sequence[int]
) -> tuple[BinaryCovariateInput, ...]:
    covariates = []
    for covariate in dataset.covariates:
        values_by_id = dataset.get_covariate_values(
            covariate.name, ids_for_keys=True
        )
        values = tuple(
            _snapshot_value(values_by_id.get(study_id)) for study_id in study_ids
        )
        covariates.append(
            BinaryCovariateInput(
                covariate.name,
                "continuous" if covariate.data_type == CONTINUOUS else "factor",
                values,
            )
        )
    return tuple(covariates)


def _snapshot_value(value: object) -> SnapshotValue:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise TypeError("covariate values must be finite JSON-safe values")
