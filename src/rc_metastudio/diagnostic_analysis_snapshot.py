# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Immutable inputs for one univariate diagnostic analysis."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from typing import Literal, Protocol, TypeAlias, TypeGuard, cast


DiagnosticMetric: TypeAlias = Literal["Sens", "Spec", "PLR", "NLR", "DOR"]
DiagnosticInputSource: TypeAlias = Literal["counts", "entered_effects"]
DIAGNOSTIC_METRICS = frozenset({"Sens", "Spec", "PLR", "NLR", "DOR"})
_STUDY_FIELDS = {
    "id",
    "name",
    "year",
    "tp",
    "fn",
    "fp",
    "tn",
    "estimate",
    "standard_error",
}
_SNAPSHOT_FIELDS = {
    "version",
    "outcome",
    "time_point",
    "groups",
    "metric",
    "input_source",
    "confidence_level",
    "studies",
}


class _DiagnosticStudy(Protocol):
    id: int
    name: str
    year: object


class _DiagnosticInputModel(Protocol):
    current_effect: str | None
    current_outcome_name: str | None

    def get_current_follow_up_name(self) -> str | None: ...

    def get_current_groups(self) -> Sequence[object]: ...

    def get_studies(self, *, only_if_included: bool = False) -> Sequence[_DiagnosticStudy]: ...

    def get_current_estimates_and_standard_errors(
        self,
        *,
        only_if_included: bool = False,
        only_these_studies: Sequence[int] | None = None,
        effect: str | None = None,
    ) -> tuple[Sequence[object], Sequence[object]]: ...

    def get_current_raw_data(
        self,
        *,
        only_if_included: bool = False,
        only_these_studies: Sequence[int] | None = None,
    ) -> Sequence[Sequence[object]]: ...

    def get_confidence_level(self) -> float: ...


def _is_string_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping) and all(isinstance(key, str) for key in value)


@dataclass(frozen=True, slots=True)
class DiagnosticStudyInput:
    id: int
    name: str
    year: int | None
    tp: int | None
    fn: int | None
    fp: int | None
    tn: int | None
    estimate: float | None
    standard_error: float | None

    def __post_init__(self) -> None:
        if type(self.id) is not int or self.id < 0:
            raise ValueError("diagnostic study identity must be a non-negative integer")
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("diagnostic study name must be non-empty text")
        if self.year is not None and type(self.year) is not int:
            raise ValueError("diagnostic study year must be an integer or unavailable")
        for field_name in ("tp", "fn", "fp", "tn"):
            value = getattr(self, field_name)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError("diagnostic raw counts must be non-negative integers")
        _finite_or_none(self.estimate, "diagnostic estimate")
        _finite_or_none(self.standard_error, "diagnostic standard error")
        if self.standard_error is not None and self.standard_error < 0:
            raise ValueError("diagnostic standard error cannot be negative")

    def to_mapping(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "year": self.year,
            "tp": self.tp,
            "fn": self.fn,
            "fp": self.fp,
            "tn": self.tn,
            "estimate": self.estimate,
            "standard_error": self.standard_error,
        }


@dataclass(frozen=True, slots=True)
class DiagnosticInputSnapshot:
    """The selected diagnostic data and included study order at submit time."""

    version: int
    outcome: str
    time_point: str
    groups: tuple[str]
    metric: DiagnosticMetric
    input_source: DiagnosticInputSource
    confidence_level: float
    studies: tuple[DiagnosticStudyInput, ...]

    def __post_init__(self) -> None:
        if type(self.version) is not int or self.version != 1:
            raise ValueError(f"unsupported diagnostic input snapshot version: {self.version}")
        if (
            not isinstance(self.outcome, str)
            or not self.outcome
            or not isinstance(self.time_point, str)
            or not self.time_point
        ):
            raise ValueError("diagnostic analysis requires an outcome and time point")
        if not isinstance(self.metric, str) or self.metric not in DIAGNOSTIC_METRICS:
            raise ValueError("univariate diagnostic analysis requires Sens, Spec, PLR, NLR, or DOR")
        if (
            not isinstance(self.groups, tuple)
            or len(self.groups) != 1
            or any(not isinstance(group, str) or not group for group in self.groups)
        ):
            raise ValueError("diagnostic analysis requires one selected study group")
        if not isinstance(self.input_source, str) or self.input_source not in {
            "counts",
            "entered_effects",
        }:
            raise ValueError("diagnostic input source must be counts or entered effects")
        if (
            isinstance(self.confidence_level, bool)
            or not isinstance(self.confidence_level, (int, float))
            or not math.isfinite(self.confidence_level)
            or not 0 < self.confidence_level < 100
        ):
            raise ValueError("diagnostic confidence level must be between 0 and 100")
        if not isinstance(self.studies, tuple) or not self.studies:
            raise ValueError("include at least one diagnostic study before running")
        if len({study.id for study in self.studies}) != len(self.studies):
            raise ValueError("diagnostic input snapshot contains duplicate study identities")
        if self.input_source == "counts" and not all(
            None not in (study.tp, study.fn, study.fp, study.tn)
            for study in self.studies
        ):
            raise ValueError(
                "count-based diagnostic analysis requires TP, FN, FP, and TN "
                "for every included study"
            )
        if self.input_source == "entered_effects" and not all(
            study.estimate is not None and study.standard_error is not None
            for study in self.studies
        ):
            raise ValueError(
                "entered-effect diagnostic analysis requires an estimate and "
                "standard error for every included study"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "outcome": self.outcome,
            "time_point": self.time_point,
            "groups": list(self.groups),
            "metric": self.metric,
            "input_source": self.input_source,
            "confidence_level": self.confidence_level,
            "studies": [study.to_mapping() for study in self.studies],
        }

    @classmethod
    def from_mapping(cls, value: object) -> DiagnosticInputSnapshot:
        if not _is_string_mapping(value) or set(value) != _SNAPSHOT_FIELDS:
            raise ValueError("diagnostic input snapshot has unknown or missing fields")
        groups = value["groups"]
        studies = value["studies"]
        if (
            not isinstance(groups, (list, tuple))
            or len(groups) != 1
            or any(not isinstance(group, str) for group in groups)
        ):
            raise ValueError("diagnostic input snapshot groups are invalid")
        if not isinstance(studies, (list, tuple)):
            raise ValueError("diagnostic input snapshot studies must be a list")
        metric = value["metric"]
        source = value["input_source"]
        if not isinstance(metric, str) or metric not in DIAGNOSTIC_METRICS:
            raise ValueError("diagnostic input snapshot metric is unsupported")
        if not isinstance(source, str) or source not in {"counts", "entered_effects"}:
            raise ValueError("diagnostic input snapshot source is unsupported")
        return cls(
            version=_required_int(value["version"], "snapshot version"),
            outcome=_required_text(value["outcome"], "outcome"),
            time_point=_required_text(value["time_point"], "time point"),
            groups=cast(tuple[str], tuple(groups)),
            metric=cast(DiagnosticMetric, metric),
            input_source=cast(DiagnosticInputSource, source),
            confidence_level=_required_number(value["confidence_level"], "confidence level"),
            studies=tuple(_study_from_mapping(study) for study in studies),
        )


def freeze_diagnostic_input(
    model: _DiagnosticInputModel, metric: str | None = None
) -> DiagnosticInputSnapshot:
    """Freeze only the included diagnostic rows for the selected single metric."""
    selected_metric = getattr(model, "current_effect", None) if metric is None else metric
    if not isinstance(selected_metric, str) or selected_metric not in DIAGNOSTIC_METRICS:
        raise ValueError("select one supported diagnostic measure before running")
    outcome = getattr(model, "current_outcome_name", None)
    time_point = model.get_current_follow_up_name()
    raw_groups = model.get_current_groups()
    if not isinstance(outcome, str) or not outcome:
        raise ValueError("select an outcome before running a diagnostic analysis")
    if not isinstance(time_point, str) or not time_point:
        raise ValueError("select a time point before running a diagnostic analysis")
    if len(raw_groups) != 1 or any(
        not isinstance(group, str) or not group for group in raw_groups
    ):
        raise ValueError("select one study group before running a diagnostic analysis")
    groups = cast(tuple[str], tuple(raw_groups))
    included = tuple(model.get_studies(only_if_included=True))
    if not included:
        raise ValueError("include at least one diagnostic study before running")
    study_ids = [study.id for study in included]
    raw_rows = model.get_current_raw_data(
        only_if_included=True, only_these_studies=study_ids
    )
    if len(raw_rows) != len(included):
        raise ValueError("diagnostic raw counts do not match the included study rows")

    parsed_rows: list[tuple[int | None, int | None, int | None, int | None]] = []
    for row in raw_rows:
        raw = list(row)
        raw.extend([None] * max(0, 4 - len(raw)))
        if len(raw) != 4:
            raise ValueError("diagnostic study data must contain TP, FN, FP, and TN")
        parsed_rows.append(
            (
                _parse_count(raw[0], "TP"),
                _parse_count(raw[1], "FN"),
                _parse_count(raw[2], "FP"),
                _parse_count(raw[3], "TN"),
            )
        )
    counts_complete = all(None not in row for row in parsed_rows)
    if counts_complete:
        # Raw rows already contain the authoritative input. Querying effect previews
        # here can initialize embedded R in the GUI process; the worker derives them
        # from these frozen counts instead.
        estimates: Sequence[object] = [None] * len(included)
        standard_errors: Sequence[object] = [None] * len(included)
    else:
        estimates, standard_errors = model.get_current_estimates_and_standard_errors(
            only_if_included=True,
            only_these_studies=study_ids,
            effect=selected_metric,
        )
    if len(estimates) != len(included) or len(standard_errors) != len(included):
        raise ValueError("diagnostic effects do not match the included study rows")

    rows: list[DiagnosticStudyInput] = []
    for index, study in enumerate(included):
        tp, fn, fp, tn = parsed_rows[index]
        rows.append(
            DiagnosticStudyInput(
                id=study.id,
                name=study.name,
                year=_parse_year(study.year),
                tp=tp,
                fn=fn,
                fp=fp,
                tn=tn,
                estimate=_parse_number(estimates[index], "diagnostic estimate"),
                standard_error=_parse_number(standard_errors[index], "diagnostic standard error"),
            )
        )

    source: DiagnosticInputSource = (
        "counts"
        if all(None not in (study.tp, study.fn, study.fp, study.tn) for study in rows)
        else "entered_effects"
    )
    return DiagnosticInputSnapshot(
        version=1,
        outcome=outcome,
        time_point=time_point,
        groups=groups,
        metric=cast(DiagnosticMetric, selected_metric),
        input_source=source,
        confidence_level=float(model.get_confidence_level()),
        studies=tuple(rows),
    )


def _study_from_mapping(value: object) -> DiagnosticStudyInput:
    if not _is_string_mapping(value) or set(value) != _STUDY_FIELDS:
        raise ValueError("diagnostic input study has unknown or missing fields")
    return DiagnosticStudyInput(
        id=_required_int(value["id"], "study id"),
        name=_required_text(value["name"], "study name"),
        year=_optional_int(value["year"], "study year"),
        tp=_optional_int(value["tp"], "TP"),
        fn=_optional_int(value["fn"], "FN"),
        fp=_optional_int(value["fp"], "FP"),
        tn=_optional_int(value["tn"], "TN"),
        estimate=_optional_number(value["estimate"], "diagnostic estimate"),
        standard_error=_optional_number(value["standard_error"], "diagnostic standard error"),
    )


def _parse_count(value: object, label: str) -> int | None:
    if value in (None, ""):
        return None
    number = _parse_number(value, f"{label} count")
    if number is None:
        return None
    if number % 1 != 0:
        raise ValueError(f"{label} count must be a whole number")
    if number < 0:
        raise ValueError(f"{label} count cannot be negative")
    return int(number)


def _parse_year(value: object) -> int | None:
    if value in (None, ""):
        return None
    number = _parse_number(value, "study year")
    if number is None or number % 1 != 0:
        raise ValueError("study year must be a whole number")
    return int(number)


def _parse_number(value: object, label: str) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    if not isinstance(value, (str, int, float)):
        raise ValueError(f"{label} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _finite_or_none(value: float | None, label: str) -> None:
    if value is not None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{label} must be numeric")
        if not math.isfinite(value):
            raise ValueError(f"{label} must be finite")


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty text")
    return value


def _required_int(value: object, label: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{label} must be an integer")
    return value


def _optional_int(value: object, label: str) -> int | None:
    if value is None:
        return None
    return _required_int(value, label)


def _required_number(value: object, label: str) -> float:
    number = _optional_number(value, label)
    if number is None:
        raise ValueError(f"{label} is required")
    return number


def _optional_number(value: object, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric or unavailable")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number
