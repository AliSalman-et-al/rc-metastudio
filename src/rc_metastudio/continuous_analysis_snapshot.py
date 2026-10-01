# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Immutable input snapshots and an isolated RCMetaR adapter for continuous analyses."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass, replace
import math
from typing import Literal, Protocol, cast

from rc_metastudio.analysis_contracts import AnalysisRequest, AnalysisResult
from rc_metastudio.meta_globals import (
    CONTINUOUS,
    CONTINUOUS_ONE_ARM_METRICS,
    CONTINUOUS_TWO_ARM_METRICS,
)


ContinuousMetric = Literal["MD", "SMD", "TX Mean"]
EffectProvenance = Literal["entered", "raw_reconstructed"]
CovariateValue = str | int | float | bool | None
StringMapping = Mapping[str, object]


class _Study(Protocol):
    id: int
    name: str
    year: int | str | None


class _Covariate(Protocol):
    name: str
    data_type: int


class _Dataset(Protocol):
    studies: Sequence[_Study]
    covariates: Sequence[_Covariate]

    def get_covariate_values(
        self, covariate: str, ids_for_keys: bool = False
    ) -> Mapping[object, object]: ...


class _EnteredEffect(Protocol):
    lower: object
    upper: object


class _AnalysisUnit(Protocol):
    def get_effect_for_source(
        self, source: str, effect: str, group_comparison: str
    ) -> _EnteredEffect: ...


class _DatasetModel(Protocol):
    current_effect: str | None
    current_outcome_name: str | None
    dataset: _Dataset

    def get_current_follow_up_name(self) -> str | None: ...

    def get_current_groups(self) -> Sequence[str]: ...

    def get_current_outcome_subtype(self) -> str | None: ...

    def get_studies(self, only_if_included: bool = True) -> list[_Study]: ...

    def get_current_estimates_and_standard_errors(
        self,
        only_if_included: bool = True,
        only_these_studies: Sequence[int] | None = None,
    ) -> tuple[Sequence[object], Sequence[object]]: ...

    def get_current_raw_data(
        self,
        only_if_included: bool = True,
        only_these_studies: Sequence[int] | None = None,
    ) -> Sequence[Sequence[object]]: ...

    def _get_canonical_analysis_unit(self, study_index: int) -> _AnalysisUnit: ...

    def get_current_group_comparison(self) -> str: ...

    def get_confidence_level(self) -> float: ...


class _RNamespace(Protocol):
    globalenv: MutableMapping[str, object]


class _ContinuousBridge(Protocol):
    ro: _RNamespace

    def _r_numeric_vector(self, values: Sequence[object]) -> object: ...

    def _r_character_vector(self, values: Sequence[object]) -> object: ...

    def _r_year_vector(self, values: Sequence[object]) -> object: ...

    def execute_r_function(
        self, function_name: str, *args: object, **kwargs: object
    ) -> object: ...

    def run_versioned_analysis_request(self, request: Mapping[str, object]) -> AnalysisResult: ...

    def r_object_to_python(self, value: object) -> object: ...


def _validate_arm_sample_size(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("continuous arm sample size must be a positive integer")


def _validate_nonnegative(value: float, label: str) -> None:
    if value < 0:
        raise ValueError(f"{label} cannot be negative")


def _validate_study_identity(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("continuous study identity must be a non-negative integer")


def _validate_study_year(value: object) -> None:
    if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
        raise ValueError("continuous study year must be an integer or missing")


def _validate_study_effect(
    estimate: float | None, standard_error: float | None
) -> None:
    if estimate is not None:
        _finite(estimate, "continuous study estimate")
    if standard_error is not None:
        standard_error = _finite(standard_error, "continuous study standard error")
    if (estimate is None) != (standard_error is None):
        raise ValueError("continuous study estimate and standard error must be paired")
    if standard_error is not None:
        _validate_nonnegative(standard_error, "continuous study standard error")


def _validate_entered_interval(
    lower_value: float | None,
    upper_value: float | None,
    confidence_value: float | None,
) -> None:
    interval = (lower_value, upper_value, confidence_value)
    if not any(value is not None for value in interval):
        return
    if any(value is None for value in interval):
        raise ValueError("entered intervals need both bounds and a confidence level")
    lower = _finite(lower_value, "entered lower bound")
    upper = _finite(upper_value, "entered upper bound")
    _confidence(confidence_value)
    if lower > upper:
        raise ValueError("entered lower bound cannot exceed its upper bound")


def _validate_study_provenance(
    provenance: EffectProvenance,
    estimate: float | None,
    arm_1: ContinuousArmInput | None,
    arm_2: ContinuousArmInput | None,
) -> None:
    if provenance == "entered" and estimate is None:
        raise ValueError("entered continuous rows need an estimate and standard error")
    if provenance == "entered" and (arm_1 is not None or arm_2 is not None):
        raise ValueError("entered-effect rows cannot claim raw arm measurements")
    if provenance == "raw_reconstructed" and arm_1 is None:
        raise ValueError("raw-derived continuous rows need the first arm measurements")


@dataclass(frozen=True, slots=True)
class ContinuousArmInput:
    """One arm's recorded sample size, mean, and standard deviation."""

    sample_size: int
    mean: float
    standard_deviation: float

    def __post_init__(self) -> None:
        _validate_arm_sample_size(self.sample_size)
        _finite(self.mean, "continuous arm mean")
        deviation = _finite(self.standard_deviation, "continuous arm standard deviation")
        _validate_nonnegative(deviation, "continuous arm standard deviation")

    def to_mapping(self) -> dict[str, object]:
        return {
            "sample_size": self.sample_size,
            "mean": self.mean,
            "standard_deviation": self.standard_deviation,
        }


@dataclass(frozen=True, slots=True)
class ContinuousCovariateInput:
    name: str
    data_type: Literal["continuous", "factor"]
    values: tuple[CovariateValue, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("continuous covariate name must be non-empty")
        if self.data_type not in ("continuous", "factor"):
            raise ValueError("continuous covariate type is invalid")
        for value in self.values:
            _covariate_value(value)

    def to_mapping(self) -> dict[str, object]:
        return {"name": self.name, "data_type": self.data_type, "values": list(self.values)}


@dataclass(frozen=True, slots=True)
class ContinuousStudyInput:
    study_id: int
    name: str
    year: int | None
    provenance: EffectProvenance
    estimate: float | None
    standard_error: float | None
    arm_1: ContinuousArmInput | None
    arm_2: ContinuousArmInput | None
    entered_lower: float | None = None
    entered_upper: float | None = None
    entered_confidence_level: float | None = None

    def __post_init__(self) -> None:
        _validate_study_identity(self.study_id)
        if not self.name:
            raise ValueError("continuous study name must be non-empty")
        if self.provenance not in ("entered", "raw_reconstructed"):
            raise ValueError("continuous study provenance is invalid")
        _validate_study_year(self.year)
        _validate_study_effect(self.estimate, self.standard_error)
        _validate_entered_interval(
            self.entered_lower,
            self.entered_upper,
            self.entered_confidence_level,
        )
        _validate_study_provenance(self.provenance, self.estimate, self.arm_1, self.arm_2)

    def to_mapping(self) -> dict[str, object]:
        return {
            "study_id": self.study_id,
            "name": self.name,
            "year": self.year,
            "provenance": self.provenance,
            "estimate": self.estimate,
            "standard_error": self.standard_error,
            "arm_1": None if self.arm_1 is None else self.arm_1.to_mapping(),
            "arm_2": None if self.arm_2 is None else self.arm_2.to_mapping(),
            "entered_lower": self.entered_lower,
            "entered_upper": self.entered_upper,
            "entered_confidence_level": self.entered_confidence_level,
        }


@dataclass(frozen=True, slots=True)
class ContinuousInputSnapshot:
    """Selected continuous inputs at submit time; no live model references."""

    version: int
    outcome: str
    follow_up: str
    groups: tuple[str, ...]
    metric: ContinuousMetric
    outcome_subtype: str | None
    outcome_unit: str | None
    studies: tuple[ContinuousStudyInput, ...]
    covariates: tuple[ContinuousCovariateInput, ...]

    def __post_init__(self) -> None:
        _validate_snapshot_version(self.version)
        _validate_snapshot_selection(self.outcome, self.follow_up)
        _continuous_snapshot_metric(self.metric)
        _validate_optional_snapshot_text(
            self.outcome_subtype, "continuous outcome subtype must be text or missing"
        )
        _validate_snapshot_groups(self.groups, self.metric)
        _validate_optional_snapshot_text(
            self.outcome_unit, "continuous outcome unit must be text or unrecorded"
        )
        _validate_snapshot_studies(self.studies)
        _validate_snapshot_covariates(self.covariates, len(self.studies))
        _validate_distinct_groups(self.groups)
        _validate_snapshot_study_arms(self.metric, self.studies)

    @property
    def raw_measurements_complete(self) -> bool:
        return all(study.provenance == "raw_reconstructed" for study in self.studies)

    @property
    def effect_scale(self) -> str:
        if self.metric == "SMD":
            return "standard_deviation_units"
        if self.metric == "TX Mean" and self.outcome_subtype in ("generic_effect", "reg_coef"):
            return "entered_effect_scale"
        return "outcome_units"

    @property
    def effect_convention(self) -> str:
        if self.metric == "TX Mean":
            if self.outcome_subtype in ("generic_effect", "reg_coef"):
                return "entered_effect_for_group_1"
            return "group_1_mean"
        return "group_1_minus_group_2"

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "outcome": self.outcome,
            "follow_up": self.follow_up,
            "groups": list(self.groups),
            "metric": self.metric,
            "outcome_subtype": self.outcome_subtype,
            "outcome_unit": self.outcome_unit,
            "studies": [study.to_mapping() for study in self.studies],
            "covariates": [covariate.to_mapping() for covariate in self.covariates],
        }

    @classmethod
    def from_mapping(cls, value: object) -> ContinuousInputSnapshot:
        source = _mapping(value, "continuous input snapshot")
        return cls(
            version=_continuous_snapshot_version(source.get("version")),
            outcome=_text(source.get("outcome"), "outcome"),
            follow_up=_text(source.get("follow_up"), "follow-up"),
            groups=_continuous_snapshot_groups(source.get("groups")),
            metric=_continuous_snapshot_metric(source.get("metric")),
            outcome_subtype=_optional_text(source.get("outcome_subtype"), "outcome subtype"),
            outcome_unit=_optional_text(source.get("outcome_unit"), "outcome unit"),
            studies=tuple(
                _study_from_mapping(row)
                for row in _continuous_snapshot_rows(source.get("studies"))
            ),
            covariates=tuple(
                _covariate_from_mapping(row)
                for row in _continuous_snapshot_rows(source.get("covariates"))
            ),
        )


def _validate_snapshot_version(version: int) -> None:
    if type(version) is not int or version != 1:
        raise ValueError(f"unsupported continuous input snapshot version: {version}")


def _validate_snapshot_selection(outcome: str, follow_up: str) -> None:
    if (
        not isinstance(outcome, str)
        or not outcome
        or not isinstance(follow_up, str)
        or not follow_up
    ):
        raise ValueError("continuous analysis needs a selected outcome and follow-up")


def _validate_snapshot_groups(
    groups: tuple[str, ...], metric: ContinuousMetric
) -> None:
    arm_count = 1 if metric in CONTINUOUS_ONE_ARM_METRICS else 2
    if len(groups) != arm_count or any(not isinstance(group, str) or not group for group in groups):
        raise ValueError("continuous snapshot group count does not match its metric")


def _validate_optional_snapshot_text(value: str | None, message: str) -> None:
    if value is not None and not isinstance(value, str):
        raise ValueError(message)


def _validate_snapshot_studies(studies: tuple[ContinuousStudyInput, ...]) -> None:
    if not studies:
        raise ValueError("include at least one study before running the analysis")
    _validate_unique_study_ids(studies)
    _validate_shared_study_provenance(studies)


def _validate_unique_study_ids(studies: tuple[ContinuousStudyInput, ...]) -> None:
    if len({study.study_id for study in studies}) != len(studies):
        raise ValueError("continuous snapshot contains duplicate study identities")


def _validate_shared_study_provenance(
    studies: tuple[ContinuousStudyInput, ...]
) -> None:
    if len({study.provenance for study in studies}) != 1:
        raise ValueError(
            "continuous analysis cannot mix entered effects and raw measurements"
        )


def _validate_snapshot_covariates(
    covariates: tuple[ContinuousCovariateInput, ...], study_count: int
) -> None:
    if len({covariate.name for covariate in covariates}) != len(covariates):
        raise ValueError("continuous snapshot contains duplicate covariates")
    if any(len(covariate.values) != study_count for covariate in covariates):
        raise ValueError("continuous covariate values do not match the study rows")


def _validate_distinct_groups(groups: tuple[str, ...]) -> None:
    if len(set(groups)) != len(groups):
        raise ValueError("continuous snapshot groups must be distinct")


def _validate_snapshot_study_arms(
    metric: ContinuousMetric, studies: tuple[ContinuousStudyInput, ...]
) -> None:
    for study in studies:
        if metric in CONTINUOUS_TWO_ARM_METRICS and study.provenance == "raw_reconstructed" and study.arm_2 is None:
            raise ValueError("two-arm continuous rows need both arm measurements")
        if metric in CONTINUOUS_ONE_ARM_METRICS and study.arm_2 is not None:
            raise ValueError("single-arm continuous rows cannot carry a comparator arm")


def _continuous_snapshot_version(value: object) -> int:
    if type(value) is not int or value != 1:
        raise ValueError("unsupported continuous input snapshot")
    return value


def _continuous_snapshot_groups(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("continuous snapshot groups must be text rows")
    return tuple(cast(list[str], value))


def _continuous_snapshot_metric(value: object) -> ContinuousMetric:
    if value not in CONTINUOUS_TWO_ARM_METRICS + CONTINUOUS_ONE_ARM_METRICS:
        raise ValueError("continuous input snapshot has an unsupported metric")
    return cast(ContinuousMetric, value)


def _continuous_snapshot_rows(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("continuous snapshot rows are missing")
    return cast(list[object], value)


@dataclass(frozen=True, slots=True)
class ContinuousAnalysisExecution:
    result: AnalysisResult
    numerics: ContinuousNumerics


@dataclass(frozen=True, slots=True)
class _ContinuousFreezeContext:
    metric: ContinuousMetric
    outcome: str
    follow_up: str
    groups: tuple[str, ...]
    studies: tuple[_Study, ...]
    study_ids: tuple[int, ...]
    canonical_index_by_id: Mapping[int, int]
    required_arms: int


@dataclass(frozen=True, slots=True)
class _ContinuousStudySource:
    provenance: EffectProvenance
    raw_rows: tuple[tuple[object, ...], ...]
    estimates: Sequence[object]
    standard_errors: Sequence[object]


def freeze_continuous_input(model: _DatasetModel) -> ContinuousInputSnapshot:
    """Copy the selected continuous studies, exact values, and source provenance."""
    context = _continuous_freeze_context(model)
    source = _continuous_study_source(model, context)
    studies = tuple(
        _freeze_continuous_study(index, study, context, source, model)
        for index, study in enumerate(context.studies)
    )
    covariates = _freeze_continuous_covariates(model, context.study_ids)
    return ContinuousInputSnapshot(
        version=1,
        outcome=context.outcome,
        follow_up=context.follow_up,
        groups=tuple(str(group) for group in context.groups),
        metric=context.metric,
        outcome_subtype=model.get_current_outcome_subtype(),
        outcome_unit=None,
        studies=studies,
        covariates=covariates,
    )


def _continuous_freeze_context(model: _DatasetModel) -> _ContinuousFreezeContext:
    metric = _selected_continuous_metric(model)
    outcome, follow_up = _selected_continuous_outcome(model)
    required_arms = 1 if metric in CONTINUOUS_ONE_ARM_METRICS else 2
    selected_groups = tuple(model.get_current_groups())
    if len(selected_groups) < required_arms:
        raise ValueError("selected continuous metric needs more study arms")
    studies = tuple(model.get_studies(only_if_included=True))
    if not studies:
        raise ValueError("include at least one study before running the analysis")
    study_ids = tuple(study.id for study in studies)
    canonical_index_by_id = {
        study.id: index for index, study in enumerate(model.dataset.studies)
    }
    return _ContinuousFreezeContext(
        metric=metric,
        outcome=outcome,
        follow_up=follow_up,
        groups=selected_groups[:required_arms],
        studies=studies,
        study_ids=study_ids,
        canonical_index_by_id=canonical_index_by_id,
        required_arms=required_arms,
    )


def _selected_continuous_metric(model: _DatasetModel) -> ContinuousMetric:
    metric = getattr(model, "current_effect", None)
    if metric not in CONTINUOUS_TWO_ARM_METRICS + CONTINUOUS_ONE_ARM_METRICS:
        raise ValueError(
            "isolated continuous analysis requires an RCMetaR continuous measure"
        )
    return cast(ContinuousMetric, metric)


def _selected_continuous_outcome(model: _DatasetModel) -> tuple[str, str]:
    outcome = getattr(model, "current_outcome_name", None)
    follow_up = model.get_current_follow_up_name()
    if not isinstance(outcome, str) or not outcome or not isinstance(follow_up, str) or not follow_up:
        raise ValueError("continuous analysis needs a selected outcome and follow-up")
    return outcome, follow_up


def _continuous_study_source(
    model: _DatasetModel, context: _ContinuousFreezeContext
) -> _ContinuousStudySource:
    required_width = 3 * context.required_arms
    raw_rows = model.get_current_raw_data(
        only_if_included=True, only_these_studies=list(context.study_ids)
    )
    normalized_rows, provenance = _normalize_continuous_raw_rows(
        raw_rows, context.studies, required_width
    )
    estimates, standard_errors = _continuous_effect_vectors(
        model, context, provenance
    )
    return _ContinuousStudySource(
        provenance, normalized_rows, estimates, standard_errors
    )


def _normalize_continuous_raw_rows(
    raw_rows: Sequence[Sequence[object]],
    studies: tuple[_Study, ...],
    required_width: int,
) -> tuple[tuple[tuple[object, ...], ...], EffectProvenance]:
    if len(raw_rows) != len(studies):
        raise ValueError("continuous raw data do not match the included study rows")
    rows: list[tuple[object, ...]] = []
    provenances: list[EffectProvenance] = []
    for index, _study in enumerate(studies):
        raw = list(raw_rows[index])
        raw.extend([None] * max(0, required_width - len(raw)))
        selected = raw[:required_width]
        has_raw = any(value not in (None, "") for value in selected)
        rows.append(tuple(selected))
        provenances.append("raw_reconstructed" if has_raw else "entered")
    if len(set(provenances)) > 1:
        raise ValueError(
            "continuous analysis cannot mix entered effects and raw measurements"
        )
    return tuple(rows), provenances[0]


def _continuous_effect_vectors(
    model: _DatasetModel,
    context: _ContinuousFreezeContext,
    provenance: EffectProvenance,
) -> tuple[Sequence[object], Sequence[object]]:
    if provenance == "raw_reconstructed":
        return [None] * len(context.studies), [None] * len(context.studies)
    estimates, standard_errors = model.get_current_estimates_and_standard_errors(
        only_if_included=True, only_these_studies=list(context.study_ids)
    )
    if len(estimates) != len(context.studies) or len(standard_errors) != len(context.studies):
        raise ValueError("continuous estimates do not match the included study rows")
    return estimates, standard_errors


def _freeze_continuous_study(
    index: int,
    study: _Study,
    context: _ContinuousFreezeContext,
    source: _ContinuousStudySource,
    model: _DatasetModel,
) -> ContinuousStudyInput:
    arms = _continuous_study_arms(
        source.raw_rows[index], source.provenance, context.required_arms, study.name
    )
    estimate, standard_error = _continuous_study_effect(
        index, study, context.metric, source
    )
    entered_interval = _entered_effect_interval(
        study, context, source.provenance, model
    )
    return ContinuousStudyInput(
        study_id=int(study.id),
        name=str(study.name),
        year=None if study.year in (None, "") else int(study.year),
        provenance=source.provenance,
        estimate=estimate,
        standard_error=standard_error,
        arm_1=arms[0],
        arm_2=arms[1] if context.required_arms == 2 else None,
        entered_lower=entered_interval[0],
        entered_upper=entered_interval[1],
        entered_confidence_level=entered_interval[2],
    )


def _continuous_study_arms(
    raw: tuple[object, ...],
    provenance: EffectProvenance,
    required_arms: int,
    study_name: str,
) -> tuple[ContinuousArmInput | None, ...]:
    arms = tuple(
        _arm_from_values(raw[offset : offset + 3])
        for offset in range(0, 3 * required_arms, 3)
    )
    if provenance == "raw_reconstructed" and any(arm is None for arm in arms):
        raise ValueError(
            f"included study {study_name!s} has partial raw continuous data; complete it or clear it"
        )
    return arms


def _continuous_study_effect(
    index: int,
    study: _Study,
    metric: ContinuousMetric,
    source: _ContinuousStudySource,
) -> tuple[float | None, float | None]:
    estimate = _model_number(source.estimates[index], "study estimate")
    standard_error = _model_number(
        source.standard_errors[index], "study standard error"
    )
    if estimate is None or standard_error is None:
        if source.provenance == "entered":
            raise ValueError(
                f"included study {study.name!s} has no complete {metric} estimate and uncertainty"
            )
        return None, None
    if standard_error < 0:
        raise ValueError(f"included study {study.name!s} has a negative standard error")
    return estimate, standard_error


def _entered_effect_interval(
    study: _Study,
    context: _ContinuousFreezeContext,
    provenance: EffectProvenance,
    model: _DatasetModel,
) -> tuple[float | None, float | None, float | None]:
    if provenance != "entered":
        return None, None, None
    canonical_index = context.canonical_index_by_id.get(study.id)
    if canonical_index is None:
        raise ValueError(f"included study {study.name!s} is missing from the dataset")
    unit = model._get_canonical_analysis_unit(canonical_index)
    entered = unit.get_effect_for_source(
        "entered", context.metric, model.get_current_group_comparison()
    )
    lower = _model_number(entered.lower, "entered lower bound")
    upper = _model_number(entered.upper, "entered upper bound")
    confidence = (
        None
        if lower is None and upper is None
        else _confidence(model.get_confidence_level())
    )
    return lower, upper, confidence


def _freeze_continuous_covariates(
    model: _DatasetModel, study_ids: tuple[int, ...]
) -> tuple[ContinuousCovariateInput, ...]:
    covariates = []
    for covariate in model.dataset.covariates:
        by_id = model.dataset.get_covariate_values(covariate.name, ids_for_keys=True)
        data_type = "continuous" if covariate.data_type == CONTINUOUS else "factor"
        covariates.append(
            ContinuousCovariateInput(
                str(covariate.name),
                data_type,
                tuple(_covariate_value(by_id.get(study_id)) for study_id in study_ids),
            )
        )
    return tuple(covariates)

def execute_continuous_snapshot(
    snapshot: ContinuousInputSnapshot,
    request: AnalysisRequest,
    *,
    bridge: _ContinuousBridge,
) -> ContinuousAnalysisExecution:
    """Build RCMetaR data from frozen inputs, run one request, and retain numerics."""
    if request.data_type != "continuous" or request.metric != snapshot.metric:
        raise ValueError("continuous request does not match its input snapshot")
    if request.workflow != "standard":
        raise ValueError("continuous snapshot adapter supports standard analyses only")
    backend_data = create_continuous_backend_data(snapshot, bridge)
    if snapshot.raw_measurements_complete:
        snapshot = _with_worker_reconstructed_effects(
            snapshot, request, backend_data, bridge
        )
    bridge.ro.globalenv["tmp_obj"] = backend_data
    result = bridge.run_versioned_analysis_request(request.to_mapping())
    raw_result = bridge.ro.globalenv["result"]
    raw_result = bridge.r_object_to_python(raw_result)
    numerics = continuous_numerics_from_backend(snapshot, request, raw_result)
    return ContinuousAnalysisExecution(result, numerics)


def create_continuous_backend_data(
    snapshot: ContinuousInputSnapshot, bridge: _ContinuousBridge
) -> object:
    """Create RCMetaR's ContinuousData S4 input without consulting live model state."""
    kwargs = _continuous_backend_effect_fields(snapshot, bridge)
    if snapshot.raw_measurements_complete:
        kwargs.update(_raw_arm_backend_fields(snapshot, bridge, 1))
        if snapshot.metric in CONTINUOUS_TWO_ARM_METRICS:
            kwargs.update(_raw_arm_backend_fields(snapshot, bridge, 2))
    return bridge.execute_r_function("rcmetar.create.continuous.data", **kwargs)


def _continuous_backend_effect_fields(
    snapshot: ContinuousInputSnapshot, bridge: _ContinuousBridge
) -> dict[str, object]:
    studies = snapshot.studies
    return {
        "y": bridge._r_numeric_vector(
            [
                None if study.provenance == "raw_reconstructed" else study.estimate
                for study in studies
            ]
        ),
        "SE": bridge._r_numeric_vector(
            [
                None
                if study.provenance == "raw_reconstructed"
                else study.standard_error
                for study in studies
            ]
        ),
        "study.names": bridge._r_character_vector(
            [study.name for study in studies]
        ),
        "years": bridge._r_year_vector([study.year for study in studies]),
        "covariates": _backend_covariates(snapshot, bridge),
    }


def _raw_arm_backend_fields(
    snapshot: ContinuousInputSnapshot,
    bridge: _ContinuousBridge,
    arm_number: Literal[1, 2],
) -> dict[str, object]:
    arms = tuple(
        _required_arm(study.arm_1 if arm_number == 1 else study.arm_2)
        for study in snapshot.studies
    )
    return {
        f"N{arm_number}": bridge._r_numeric_vector(
            [arm.sample_size for arm in arms]
        ),
        f"mean{arm_number}": bridge._r_numeric_vector([arm.mean for arm in arms]),
        f"sd{arm_number}": bridge._r_numeric_vector(
            [arm.standard_deviation for arm in arms]
        ),
    }


def _with_worker_reconstructed_effects(
    snapshot: ContinuousInputSnapshot,
    request: AnalysisRequest,
    backend_data: object,
    bridge: _ContinuousBridge,
) -> ContinuousInputSnapshot:
    """Ask RCMetaR to derive raw study effects inside the analysis worker."""
    parameters: dict[str, object] = {
        key: value
        for key, value in request.parameter_values().items()
        if value is not None
    }
    parameters["measure"] = _rcmetar_metric(snapshot.metric)
    r_parameters = bridge.execute_r_function("list", **parameters)
    prepared = bridge.execute_r_function(
        "rcmetar.prepare.analysis.data", backend_data, r_parameters
    )
    estimates = bridge.r_object_to_python(
        bridge.execute_r_function("slot", prepared, "y")
    )
    standard_errors = bridge.r_object_to_python(
        bridge.execute_r_function("slot", prepared, "SE")
    )
    estimate_values = _worker_effect_vector(estimates, len(snapshot.studies), "estimate")
    standard_error_values = _worker_effect_vector(
        standard_errors, len(snapshot.studies), "standard error"
    )
    return replace(
        snapshot,
        studies=tuple(
            replace(
                study,
                estimate=estimate_values[index],
                standard_error=standard_error_values[index],
            )
            for index, study in enumerate(snapshot.studies)
        ),
    )


def _worker_effect_vector(
    value: object, expected_count: int, label: str
) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != expected_count:
        raise ValueError(f"RCMetaR returned the wrong number of continuous {label} values")
    values = tuple(_finite(item, f"worker continuous {label}") for item in value)
    if label == "standard error" and any(item < 0 for item in values):
        raise ValueError("RCMetaR returned a negative continuous standard error")
    return values


def _rcmetar_metric(metric: ContinuousMetric) -> str:
    return "TXMean" if metric == "TX Mean" else metric


def _backend_covariates(
    snapshot: ContinuousInputSnapshot, bridge: _ContinuousBridge
) -> object:
    rows = []
    for covariate in snapshot.covariates:
        values = covariate.values
        vector = (
            bridge._r_numeric_vector(values)
            if covariate.data_type == "continuous"
            else bridge._r_character_vector(values)
        )
        reference = next((str(item) for item in values if item not in (None, "")), "")
        rows.append(
            bridge.execute_r_function(
                "rcmetar.create.covariate.values",
                **{
                    "cov.name": covariate.name,
                    "cov.vals": vector,
                    "cov.type": covariate.data_type,
                    "ref.var": reference,
                },
            )
        )
    return bridge.execute_r_function("list", *rows)


@dataclass(frozen=True, slots=True)
class ContinuousBackendValue:
    status: Literal["available", "not_estimable", "not_available"]
    value: float | None
    reason: str | None = None

    def to_mapping(self) -> dict[str, object]:
        return {"status": self.status, "value": self.value, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class ContinuousBackendEstimate:
    estimate: ContinuousBackendValue
    lower_bound: ContinuousBackendValue
    upper_bound: ContinuousBackendValue

    def to_mapping(self) -> dict[str, object]:
        return {
            "estimate": self.estimate.to_mapping(),
            "lower_bound": self.lower_bound.to_mapping(),
            "upper_bound": self.upper_bound.to_mapping(),
        }


@dataclass(frozen=True, slots=True)
class ContinuousStudyNumerics:
    order: int
    study_id: int
    label: str
    provenance: EffectProvenance
    estimate: float | None
    standard_error: float | None
    arm_1: ContinuousArmInput | None
    arm_2: ContinuousArmInput | None
    entered_lower: float | None
    entered_upper: float | None
    entered_confidence_level: float | None

    def to_mapping(self) -> dict[str, object]:
        return {
            "order": self.order,
            "study_id": self.study_id,
            "label": self.label,
            "provenance": self.provenance,
            "estimate": self.estimate,
            "standard_error": self.standard_error,
            "arm_1": None if self.arm_1 is None else self.arm_1.to_mapping(),
            "arm_2": None if self.arm_2 is None else self.arm_2.to_mapping(),
            "entered_lower": self.entered_lower,
            "entered_upper": self.entered_upper,
            "entered_confidence_level": self.entered_confidence_level,
        }


@dataclass(frozen=True, slots=True)
class ContinuousNumerics:
    version: int
    metric: ContinuousMetric
    effect_scale: str
    effect_convention: str
    groups: tuple[str, ...]
    outcome_subtype: str | None
    outcome_unit: str | None
    confidence_level: float | None
    pooled: ContinuousBackendEstimate
    standard_error: ContinuousBackendValue
    p_value: ContinuousBackendValue
    tau_squared: ContinuousBackendValue
    analyzed_study_count: ContinuousBackendValue
    submitted_study_count: int
    studies: tuple[ContinuousStudyNumerics, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "metric": self.metric,
            "effect_scale": self.effect_scale,
            "effect_convention": self.effect_convention,
            "groups": list(self.groups),
            "outcome_subtype": self.outcome_subtype,
            "outcome_unit": self.outcome_unit,
            "confidence_level": self.confidence_level,
            "pooled": self.pooled.to_mapping(),
            "standard_error": self.standard_error.to_mapping(),
            "p_value": self.p_value.to_mapping(),
            "tau_squared": self.tau_squared.to_mapping(),
            "analyzed_study_count": self.analyzed_study_count.to_mapping(),
            "submitted_study_count": self.submitted_study_count,
            "studies": [study.to_mapping() for study in self.studies],
        }


def continuous_numerics_from_backend(
    snapshot: ContinuousInputSnapshot,
    request: AnalysisRequest,
    backend_result: object,
) -> ContinuousNumerics:
    """Validate RCMetaR/metafor numerical fields without parsing display text."""
    backend = _mapping(backend_result, "continuous backend result")
    if request.data_type != "continuous" or request.metric != snapshot.metric:
        raise ValueError("continuous backend request does not match its snapshot")
    model = _mapping(backend.get("res"), "continuous pooled model values")
    confidence = _continuous_backend_confidence(backend, request)
    pooled = ContinuousBackendEstimate(
        _backend_value(model, "b", "pooled estimate"),
        _backend_value(model, "ci.lb", "pooled lower bound"),
        _backend_value(model, "ci.ub", "pooled upper bound"),
    )
    backend_studies = _continuous_analyzed_study_count(
        model.get("k"), len(snapshot.studies)
    )
    return ContinuousNumerics(
        version=1,
        metric=snapshot.metric,
        effect_scale=snapshot.effect_scale,
        effect_convention=snapshot.effect_convention,
        groups=snapshot.groups,
        outcome_subtype=snapshot.outcome_subtype,
        outcome_unit=snapshot.outcome_unit,
        confidence_level=confidence,
        pooled=pooled,
        standard_error=_backend_value(model, "se", "pooled standard error"),
        p_value=_backend_value(model, "pval", "pooled p-value"),
        tau_squared=_backend_value(model, "tau2", "tau-squared"),
        analyzed_study_count=backend_studies,
        submitted_study_count=len(snapshot.studies),
        studies=tuple(
            ContinuousStudyNumerics(
                order=index,
                study_id=study.study_id,
                label=study.name,
                provenance=study.provenance,
                estimate=study.estimate,
                standard_error=study.standard_error,
                arm_1=study.arm_1,
                arm_2=study.arm_2,
                entered_lower=study.entered_lower,
                entered_upper=study.entered_upper,
                entered_confidence_level=study.entered_confidence_level,
            )
            for index, study in enumerate(snapshot.studies)
        ),
    )


def _continuous_backend_confidence(
    backend: StringMapping, request: AnalysisRequest
) -> float | None:
    params = backend.get("input_params")
    param_confidence = (
        _mapping(params, "continuous backend input parameters").get("conf.level")
        if isinstance(params, Mapping)
        else None
    )
    confidence = _confidence(param_confidence)
    if confidence is not None:
        return confidence
    return _confidence(request.parameter_values().get("conf.level"))


def _continuous_analyzed_study_count(
    value: object, submitted_count: int
) -> ContinuousBackendValue:
    count = _backend_scalar(value)
    if count is None:
        return _unavailable("The backend did not return an analyzed study count.")
    if count < 0 or not float(count).is_integer():
        raise ValueError("continuous backend study count must be a non-negative integer")
    if count > submitted_count:
        raise ValueError("continuous backend study count exceeds submitted study rows")
    return ContinuousBackendValue("available", count)


def _backend_value(
    model: StringMapping, key: str, label: str
) -> ContinuousBackendValue:
    if key not in model:
        return _unavailable(f"The backend did not return {label}.")
    number = _backend_scalar(model[key])
    if number is None:
        return ContinuousBackendValue(
            "not_estimable", None, f"The backend returned no finite {label}."
        )
    return ContinuousBackendValue("available", number)


def _backend_scalar(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (list, tuple)):
        flattened = []
        for item in value:
            item_number = _backend_scalar(item)
            if item_number is not None:
                flattened.append(item_number)
        return flattened[0] if len(flattened) == 1 else None
    return None


def _unavailable(reason: str) -> ContinuousBackendValue:
    return ContinuousBackendValue("not_available", None, reason)


def _study_from_mapping(value: object) -> ContinuousStudyInput:
    row = _mapping(value, "continuous study row")
    provenance = row.get("provenance")
    if provenance not in ("entered", "raw_reconstructed"):
        raise ValueError("continuous study provenance is invalid")
    raw_study_id = row.get("study_id")
    if isinstance(raw_study_id, bool) or not isinstance(raw_study_id, int):
        raise ValueError("continuous study identity must be an integer")
    raw_year = row.get("year")
    if raw_year is not None and (isinstance(raw_year, bool) or not isinstance(raw_year, int)):
        raise ValueError("continuous study year must be an integer or missing")
    return ContinuousStudyInput(
        study_id=raw_study_id,
        name=_text(row.get("name"), "study name"),
        year=raw_year,
        provenance=cast(EffectProvenance, provenance),
        estimate=_optional_finite(row.get("estimate"), "continuous study estimate"),
        standard_error=_optional_finite(row.get("standard_error"), "continuous study standard error"),
        arm_1=_arm_from_mapping(row.get("arm_1")),
        arm_2=_arm_from_mapping(row.get("arm_2")),
        entered_lower=_optional_finite(row.get("entered_lower"), "entered lower bound"),
        entered_upper=_optional_finite(row.get("entered_upper"), "entered upper bound"),
        entered_confidence_level=_optional_confidence(row.get("entered_confidence_level")),
    )


def _arm_from_mapping(value: object) -> ContinuousArmInput | None:
    if value is None:
        return None
    arm = _mapping(value, "continuous arm input")
    size = arm.get("sample_size")
    if isinstance(size, bool) or not isinstance(size, int):
        raise ValueError("continuous arm sample size must be an integer")
    return ContinuousArmInput(
        size,
        _finite(arm.get("mean"), "continuous arm mean"),
        _finite(arm.get("standard_deviation"), "continuous arm standard deviation"),
    )


def _covariate_from_mapping(value: object) -> ContinuousCovariateInput:
    covariate = _mapping(value, "continuous covariate")
    name = _text(covariate.get("name"), "covariate name")
    data_type = covariate.get("data_type")
    raw_values = covariate.get("values")
    if data_type not in ("continuous", "factor") or not isinstance(raw_values, list):
        raise ValueError("continuous covariate data is invalid")
    values = tuple(_covariate_value(item) for item in raw_values)
    return ContinuousCovariateInput(
        name, cast(Literal["continuous", "factor"], data_type), values
    )


def _arm_from_values(values: Sequence[object]) -> ContinuousArmInput | None:
    if len(values) < 3 or any(value in (None, "") for value in values[:3]):
        return None
    number = _model_number(values[0], "continuous arm sample size")
    mean = _model_number(values[1], "continuous arm mean")
    deviation = _model_number(values[2], "continuous arm standard deviation")
    if number is None or mean is None or deviation is None or not float(number).is_integer():
        raise ValueError("continuous arm raw data must have a whole sample size and numeric moments")
    return ContinuousArmInput(int(number), mean, deviation)


def _required_arm(arm: ContinuousArmInput | None) -> ContinuousArmInput:
    if arm is None:
        raise ValueError("complete raw continuous measurements are required")
    return arm


def _model_number(value: object, label: str) -> float | None:
    if value in (None, ""):
        return None
    return _finite(value, label)


def _covariate_value(value: object) -> CovariateValue:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise ValueError("continuous covariates must contain finite JSON-safe values")


def _optional_text(value: object, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text or missing")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty text")
    return value


def _finite(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _optional_finite(value: object, label: str) -> float | None:
    return None if value is None else _finite(value, label)


def _confidence(value: object) -> float | None:
    if value is None:
        return None
    number = _finite(value, "confidence level")
    if not 0 < number < 100:
        raise ValueError("confidence level must be between zero and 100")
    return number


def _optional_confidence(value: object) -> float | None:
    return _confidence(value)


def _mapping(value: object, label: str) -> StringMapping:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise ValueError(f"{label} field names must be text")
    return cast(StringMapping, value)
