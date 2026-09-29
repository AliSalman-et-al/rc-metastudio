# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Immutable inputs for one univariate diagnostic analysis."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from typing import Literal, Protocol, TypeAlias, TypeGuard, cast

from rc_metastudio.meta_globals import CONTINUOUS


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
_SNAPSHOT_FIELDS_WITH_COVARIATES = _SNAPSHOT_FIELDS | {"covariates"}


class _DiagnosticStudy(Protocol):
    id: int
    name: str
    year: object


class _DiagnosticCovariate(Protocol):
    name: str
    data_type: int


class _DiagnosticDataset(Protocol):
    covariates: Sequence[_DiagnosticCovariate]

    def get_covariate_values(
        self, name: str, *, ids_for_keys: bool = False
    ) -> Mapping[int, object]: ...


class _DiagnosticInputModel(Protocol):
    current_effect: str | None
    current_outcome_name: str | None
    dataset: _DiagnosticDataset

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
        _validate_study_identity(self.id, self.name)
        _validate_study_year(self.year)
        _validate_study_counts((self.tp, self.fn, self.fp, self.tn))
        _validate_study_effects(self.estimate, self.standard_error)

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


DiagnosticCovariateValue: TypeAlias = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class DiagnosticCovariateInput:
    name: str
    data_type: Literal["continuous", "factor"]
    values: tuple[DiagnosticCovariateValue, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("diagnostic covariate name must be non-empty text")
        if self.data_type not in ("continuous", "factor"):
            raise ValueError("diagnostic covariate type is invalid")
        for value in self.values:
            _covariate_value(value)

    def to_mapping(self) -> dict[str, object]:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "values": list(self.values),
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
    covariates: tuple[DiagnosticCovariateInput, ...] = ()

    def __post_init__(self) -> None:
        _validate_snapshot_version(self.version, self.covariates)
        _validate_snapshot_context(
            self.outcome,
            self.time_point,
            self.metric,
            self.groups,
            self.input_source,
            self.confidence_level,
        )
        _validate_snapshot_studies(self.studies)
        _validate_snapshot_covariates(self.covariates, len(self.studies))
        _validate_snapshot_source_rows(self.input_source, self.studies)

    def to_mapping(self) -> dict[str, object]:
        mapping = {
            "version": self.version,
            "outcome": self.outcome,
            "time_point": self.time_point,
            "groups": list(self.groups),
            "metric": self.metric,
            "input_source": self.input_source,
            "confidence_level": self.confidence_level,
            "studies": [study.to_mapping() for study in self.studies],
        }
        if self.version == 2:
            mapping["covariates"] = [covariate.to_mapping() for covariate in self.covariates]
        return mapping

    @classmethod
    def from_mapping(cls, value: object) -> DiagnosticInputSnapshot:
        mapping = _diagnostic_snapshot_mapping(value)
        version, has_covariates = _snapshot_mapping_version(mapping)
        _validate_mapping_version_and_covariates(version, has_covariates)
        groups = _snapshot_groups(mapping["groups"])
        studies = _snapshot_sequence(mapping["studies"], "studies")
        raw_covariates = _snapshot_sequence(mapping.get("covariates", []), "covariates")
        metric = _snapshot_metric(mapping["metric"])
        input_source = _snapshot_source(mapping["input_source"])
        return cls(
            version=version,
            outcome=_required_text(mapping["outcome"], "outcome"),
            time_point=_required_text(mapping["time_point"], "time point"),
            groups=groups,
            metric=metric,
            input_source=input_source,
            confidence_level=_required_number(mapping["confidence_level"], "confidence level"),
            studies=tuple(_study_from_mapping(study) for study in studies),
            covariates=tuple(_covariate_from_mapping(row) for row in raw_covariates),
        )


def _diagnostic_snapshot_mapping(value: object) -> Mapping[str, object]:
    if not _is_string_mapping(value) or set(value) not in (
        _SNAPSHOT_FIELDS,
        _SNAPSHOT_FIELDS_WITH_COVARIATES,
    ):
        raise ValueError("diagnostic input snapshot has unknown or missing fields")
    return value


def _snapshot_mapping_version(mapping: Mapping[str, object]) -> tuple[int, bool]:
    return (
        _required_int(mapping["version"], "snapshot version"),
        set(mapping) == _SNAPSHOT_FIELDS_WITH_COVARIATES,
    )


def _validate_mapping_version_and_covariates(version: int, has_covariates: bool) -> None:
    if (version == 1 and has_covariates) or (version == 2 and not has_covariates):
        raise ValueError("diagnostic input snapshot version and covariates disagree")


def _snapshot_groups(value: object) -> tuple[str]:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != 1
        or any(not isinstance(group, str) for group in value)
    ):
        raise ValueError("diagnostic input snapshot groups are invalid")
    return cast(tuple[str], tuple(value))


def _snapshot_sequence(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"diagnostic input snapshot {label} must be a list")
    return value


def _snapshot_metric(value: object) -> DiagnosticMetric:
    if not isinstance(value, str) or value not in DIAGNOSTIC_METRICS:
        raise ValueError("diagnostic input snapshot metric is unsupported")
    return cast(DiagnosticMetric, value)


def _snapshot_source(value: object) -> DiagnosticInputSource:
    if not isinstance(value, str) or value not in {"counts", "entered_effects"}:
        raise ValueError("diagnostic input snapshot source is unsupported")
    return cast(DiagnosticInputSource, value)


def _validate_snapshot_version(
    version: int, covariates: Sequence[DiagnosticCovariateInput]
) -> None:
    if type(version) is not int or version not in (1, 2):
        raise ValueError(f"unsupported diagnostic input snapshot version: {version}")
    if version == 1 and covariates:
        raise ValueError("diagnostic input snapshot v1 cannot contain covariates")


def _validate_snapshot_context(
    outcome: str,
    time_point: str,
    metric: DiagnosticMetric,
    groups: tuple[str],
    input_source: DiagnosticInputSource,
    confidence_level: float,
) -> None:
    _validate_outcome_and_time_point(outcome, time_point)
    _validate_metric(metric)
    _validate_groups(groups)
    _validate_input_source(input_source)
    _validate_confidence_level(confidence_level)


def _validate_outcome_and_time_point(outcome: str, time_point: str) -> None:
    if (
        not isinstance(outcome, str)
        or not outcome
        or not isinstance(time_point, str)
        or not time_point
    ):
        raise ValueError("diagnostic analysis requires an outcome and time point")


def _validate_metric(metric: str) -> None:
    if not isinstance(metric, str) or metric not in DIAGNOSTIC_METRICS:
        raise ValueError("univariate diagnostic analysis requires Sens, Spec, PLR, NLR, or DOR")


def _validate_groups(groups: tuple[str]) -> None:
    if (
        not isinstance(groups, tuple)
        or len(groups) != 1
        or any(not isinstance(group, str) or not group for group in groups)
    ):
        raise ValueError("diagnostic analysis requires one selected study group")


def _validate_input_source(input_source: str) -> None:
    if not isinstance(input_source, str) or input_source not in {
        "counts",
        "entered_effects",
    }:
        raise ValueError("diagnostic input source must be counts or entered effects")


def _validate_confidence_level(confidence_level: float) -> None:
    if (
        isinstance(confidence_level, bool)
        or not isinstance(confidence_level, (int, float))
        or not math.isfinite(confidence_level)
        or not 0 < confidence_level < 100
    ):
        raise ValueError("diagnostic confidence level must be between 0 and 100")


def _validate_snapshot_studies(studies: tuple[DiagnosticStudyInput, ...]) -> None:
    if not isinstance(studies, tuple) or not studies:
        raise ValueError("include at least one diagnostic study before running")
    if len({study.id for study in studies}) != len(studies):
        raise ValueError("diagnostic input snapshot contains duplicate study identities")


def _validate_snapshot_covariates(
    covariates: tuple[DiagnosticCovariateInput, ...], study_count: int
) -> None:
    if len({covariate.name for covariate in covariates}) != len(covariates):
        raise ValueError("diagnostic input snapshot contains duplicate covariates")
    if any(len(covariate.values) != study_count for covariate in covariates):
        raise ValueError("diagnostic covariate values do not match the study rows")


def _validate_snapshot_source_rows(
    input_source: str, studies: Sequence[DiagnosticStudyInput]
) -> None:
    if input_source == "counts" and not _all_studies_have_counts(studies):
        raise ValueError(
            "count-based diagnostic analysis requires TP, FN, FP, and TN "
            "for every included study"
        )
    if input_source == "entered_effects" and not _all_studies_have_effects(studies):
        raise ValueError(
            "entered-effect diagnostic analysis requires an estimate and "
            "standard error for every included study"
        )


def _all_studies_have_counts(studies: Sequence[DiagnosticStudyInput]) -> bool:
    return all(None not in (study.tp, study.fn, study.fp, study.tn) for study in studies)


def _all_studies_have_effects(studies: Sequence[DiagnosticStudyInput]) -> bool:
    return all(
        study.estimate is not None and study.standard_error is not None
        for study in studies
    )


def freeze_diagnostic_input(
    model: _DiagnosticInputModel,
    metric: str | None = None,
    *,
    include_covariates: bool = False,
) -> DiagnosticInputSnapshot:
    """Freeze only the included diagnostic rows for the selected single metric."""
    selected_metric = _selected_metric(model, metric)
    outcome = _selected_outcome(model)
    time_point = _selected_time_point(model)
    groups = _selected_groups(model)
    included = _included_studies(model)
    study_ids = [study.id for study in included]
    counts = _included_raw_counts(model, included, study_ids)
    estimates, standard_errors = _included_effects(
        model, selected_metric, included, study_ids, counts
    )
    studies = _diagnostic_study_inputs(included, counts, estimates, standard_errors)
    source = _diagnostic_input_source(studies)
    covariates = _diagnostic_covariates(model, study_ids) if include_covariates else ()
    return DiagnosticInputSnapshot(
        version=2 if include_covariates else 1,
        outcome=outcome,
        time_point=time_point,
        groups=groups,
        metric=selected_metric,
        input_source=source,
        confidence_level=float(model.get_confidence_level()),
        studies=studies,
        covariates=covariates,
    )


def _selected_metric(
    model: _DiagnosticInputModel, metric: str | None
) -> DiagnosticMetric:
    selected = getattr(model, "current_effect", None) if metric is None else metric
    if not isinstance(selected, str) or selected not in DIAGNOSTIC_METRICS:
        raise ValueError("select one supported diagnostic measure before running")
    return cast(DiagnosticMetric, selected)


def _selected_outcome(model: _DiagnosticInputModel) -> str:
    outcome = getattr(model, "current_outcome_name", None)
    if not isinstance(outcome, str) or not outcome:
        raise ValueError("select an outcome before running a diagnostic analysis")
    return outcome


def _selected_time_point(model: _DiagnosticInputModel) -> str:
    time_point = model.get_current_follow_up_name()
    if not isinstance(time_point, str) or not time_point:
        raise ValueError("select a time point before running a diagnostic analysis")
    return time_point


def _selected_groups(model: _DiagnosticInputModel) -> tuple[str]:
    groups = model.get_current_groups()
    if len(groups) != 1 or any(not isinstance(group, str) or not group for group in groups):
        raise ValueError("select one study group before running a diagnostic analysis")
    return cast(tuple[str], tuple(groups))


def _included_studies(model: _DiagnosticInputModel) -> tuple[_DiagnosticStudy, ...]:
    studies = tuple(model.get_studies(only_if_included=True))
    if not studies:
        raise ValueError("include at least one diagnostic study before running")
    return studies


_DiagnosticCountRow: TypeAlias = tuple[int | None, int | None, int | None, int | None]


def _included_raw_counts(
    model: _DiagnosticInputModel,
    studies: Sequence[_DiagnosticStudy],
    study_ids: Sequence[int],
) -> tuple[_DiagnosticCountRow, ...]:
    raw_rows = model.get_current_raw_data(
        only_if_included=True, only_these_studies=study_ids
    )
    if len(raw_rows) != len(studies):
        raise ValueError("diagnostic raw counts do not match the included study rows")
    return tuple(_parse_count_row(row) for row in raw_rows)


def _parse_count_row(raw_row: Sequence[object]) -> _DiagnosticCountRow:
    values = list(raw_row)
    values.extend([None] * max(0, 4 - len(values)))
    if len(values) != 4:
        raise ValueError("diagnostic study data must contain TP, FN, FP, and TN")
    return (
        _parse_count(values[0], "TP"),
        _parse_count(values[1], "FN"),
        _parse_count(values[2], "FP"),
        _parse_count(values[3], "TN"),
    )


def _included_effects(
    model: _DiagnosticInputModel,
    metric: DiagnosticMetric,
    studies: Sequence[_DiagnosticStudy],
    study_ids: Sequence[int],
    counts: Sequence[_DiagnosticCountRow],
) -> tuple[Sequence[object], Sequence[object]]:
    if _all_count_rows_complete(counts):
        # Raw counts are authoritative, and the worker derives their effects.
        return [None] * len(studies), [None] * len(studies)
    estimates, standard_errors = model.get_current_estimates_and_standard_errors(
        only_if_included=True,
        only_these_studies=study_ids,
        effect=metric,
    )
    if len(estimates) != len(studies) or len(standard_errors) != len(studies):
        raise ValueError("diagnostic effects do not match the included study rows")
    return estimates, standard_errors


def _all_count_rows_complete(counts: Sequence[_DiagnosticCountRow]) -> bool:
    return all(None not in row for row in counts)


def _diagnostic_study_inputs(
    studies: Sequence[_DiagnosticStudy],
    counts: Sequence[_DiagnosticCountRow],
    estimates: Sequence[object],
    standard_errors: Sequence[object],
) -> tuple[DiagnosticStudyInput, ...]:
    return tuple(
        _diagnostic_study_input(study, counts[index], estimates[index], standard_errors[index])
        for index, study in enumerate(studies)
    )


def _diagnostic_study_input(
    study: _DiagnosticStudy,
    counts: _DiagnosticCountRow,
    estimate: object,
    standard_error: object,
) -> DiagnosticStudyInput:
    tp, fn, fp, tn = counts
    return DiagnosticStudyInput(
        id=study.id,
        name=study.name,
        year=_parse_year(study.year),
        tp=tp,
        fn=fn,
        fp=fp,
        tn=tn,
        estimate=_parse_number(estimate, "diagnostic estimate"),
        standard_error=_parse_number(standard_error, "diagnostic standard error"),
    )


def _diagnostic_input_source(
    studies: Sequence[DiagnosticStudyInput],
) -> DiagnosticInputSource:
    if _all_studies_have_counts(studies):
        return "counts"
    return "entered_effects"


def _diagnostic_covariates(
    model: _DiagnosticInputModel, study_ids: Sequence[int]
) -> tuple[DiagnosticCovariateInput, ...]:
    covariates = []
    for covariate in model.dataset.covariates:
        by_id = model.dataset.get_covariate_values(covariate.name, ids_for_keys=True)
        covariates.append(
            DiagnosticCovariateInput(
                str(covariate.name),
                "continuous" if covariate.data_type == CONTINUOUS else "factor",
                tuple(_covariate_value(by_id.get(study_id)) for study_id in study_ids),
            )
        )
    return tuple(covariates)


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


def _covariate_from_mapping(value: object) -> DiagnosticCovariateInput:
    if not _is_string_mapping(value) or set(value) != {"name", "data_type", "values"}:
        raise ValueError("diagnostic covariate has unknown or missing fields")
    name = _required_text(value["name"], "covariate name")
    data_type = value["data_type"]
    values = value["values"]
    if data_type not in ("continuous", "factor") or not isinstance(values, (list, tuple)):
        raise ValueError("diagnostic covariate is invalid")
    return DiagnosticCovariateInput(
        name,
        cast(Literal["continuous", "factor"], data_type),
        tuple(_covariate_value(item) for item in values),
    )


def _covariate_value(value: object) -> DiagnosticCovariateValue:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise ValueError("diagnostic covariate values must be finite JSON scalars")


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


def _validate_study_identity(study_id: int, name: str) -> None:
    if type(study_id) is not int or study_id < 0:
        raise ValueError("diagnostic study identity must be a non-negative integer")
    if not isinstance(name, str) or not name:
        raise ValueError("diagnostic study name must be non-empty text")


def _validate_study_year(year: int | None) -> None:
    if year is not None and type(year) is not int:
        raise ValueError("diagnostic study year must be an integer or unavailable")


def _validate_study_counts(counts: Sequence[int | None]) -> None:
    for value in counts:
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError("diagnostic raw counts must be non-negative integers")


def _validate_study_effects(estimate: float | None, standard_error: float | None) -> None:
    _finite_or_none(estimate, "diagnostic estimate")
    _finite_or_none(standard_error, "diagnostic standard error")
    if standard_error is not None and standard_error < 0:
        raise ValueError("diagnostic standard error cannot be negative")


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
