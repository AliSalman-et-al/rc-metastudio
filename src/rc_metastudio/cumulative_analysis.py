# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Immutable cumulative ordering and isolated prefix-result contracts."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
import math
from typing import Literal, Protocol, TypeAlias, cast

from rc_metastudio.analysis_contracts import AnalysisRequest
from rc_metastudio.analysis_snapshot import (
    BinaryCovariateInput,
    BinaryInputSnapshot,
    BinaryStudyInput,
    SingleArmBinaryStudyInput,
)
from rc_metastudio.continuous_analysis_snapshot import ContinuousInputSnapshot
from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot
from rc_metastudio.meta_globals import BINARY_ONE_ARM_METRICS


CumulativeInputSnapshot: TypeAlias = (
    BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot
)
CumulativeOrderField: TypeAlias = Literal["project_order", "year"]
CumulativeDirection: TypeAlias = Literal["ascending", "descending"]
MissingYearPolicy: TypeAlias = Literal["first", "last"]
OrderingValue: TypeAlias = str | int | float | bool | None
NumericStatus: TypeAlias = Literal["available", "not_estimable", "not_available"]
CumulativeStepStatus: TypeAlias = Literal["complete", "partial", "not_estimable", "failed"]


class _StudyOrderInput(Protocol):
    name: str
    year: int | None


@dataclass(frozen=True, slots=True)
class CumulativeOrderSpec:
    """The declared order. Ties always retain their project order."""

    field: CumulativeOrderField
    direction: CumulativeDirection
    missing_year_policy: MissingYearPolicy | None = None

    def __post_init__(self) -> None:
        if self.field not in ("project_order", "year"):
            raise ValueError("cumulative ordering field must be project_order or year")
        if self.direction not in ("ascending", "descending"):
            raise ValueError("cumulative ordering direction must be ascending or descending")
        if self.field == "project_order" and self.missing_year_policy is not None:
            raise ValueError("project order has no missing-year policy")
        if self.missing_year_policy not in (None, "first", "last"):
            raise ValueError("missing-year policy must be first, last, or unset")

    def to_mapping(self) -> dict[str, object]:
        return {
            "field": self.field,
            "direction": self.direction,
            "missing_year_policy": self.missing_year_policy,
            "tie_policy": "original_project_order",
        }

    @classmethod
    def from_mapping(cls, value: object) -> CumulativeOrderSpec:
        mapping = _string_mapping(value, "cumulative ordering")
        if set(mapping) != {"field", "direction", "missing_year_policy", "tie_policy"}:
            raise ValueError("cumulative ordering has unknown or missing fields")
        if mapping["tie_policy"] != "original_project_order":
            raise ValueError("unsupported cumulative tie policy")
        field = mapping["field"]
        direction = mapping["direction"]
        missing = mapping["missing_year_policy"]
        if field not in ("project_order", "year"):
            raise ValueError("cumulative ordering field is unsupported")
        if direction not in ("ascending", "descending"):
            raise ValueError("cumulative ordering direction is unsupported")
        if missing not in (None, "first", "last"):
            raise ValueError("cumulative missing-year policy is unsupported")
        return cls(
            cast(CumulativeOrderField, field),
            cast(CumulativeDirection, direction),
            cast(MissingYearPolicy | None, missing),
        )


@dataclass(frozen=True, slots=True)
class CumulativeStudyOrder:
    """One study's stable position, selected ordering value, and prefix size."""

    order: int
    source_order: int
    study_id: int
    study_name: str
    ordering_value: OrderingValue
    included_study_count: int

    def __post_init__(self) -> None:
        _validate_study_order_position(self)
        _validate_study_order_identity(self)
        _validate_ordering_value(self.ordering_value, "cumulative ordering value")

    def to_mapping(self) -> dict[str, object]:
        return {
            "order": self.order,
            "source_order": self.source_order,
            "study_id": self.study_id,
            "study_name": self.study_name,
            "ordering_value": self.ordering_value,
            "included_study_count": self.included_study_count,
        }


@dataclass(frozen=True, slots=True)
class CumulativeAnalysisSnapshot:
    """Original immutable inputs plus the exact analytical sequence."""

    version: int
    input_snapshot: CumulativeInputSnapshot
    ordering: CumulativeOrderSpec
    sequence: tuple[CumulativeStudyOrder, ...]

    def __post_init__(self) -> None:
        if type(self.version) is not int or self.version != 1:
            raise ValueError("unsupported cumulative analysis snapshot version")
        _validate_snapshot_studies(self)
        _validate_snapshot_sequence(self)

    @property
    def family(self) -> Literal["binary", "continuous", "diagnostic"]:
        if isinstance(self.input_snapshot, BinaryInputSnapshot):
            return "binary"
        if isinstance(self.input_snapshot, ContinuousInputSnapshot):
            return "continuous"
        return "diagnostic"

    @property
    def ordered_input_snapshot(self) -> CumulativeInputSnapshot:
        indexes = tuple(step.source_order for step in self.sequence)
        return _reorder_snapshot(self.input_snapshot, indexes)

    def prefix_input_snapshot(self, included_study_count: int) -> CumulativeInputSnapshot:
        if type(included_study_count) is not int or not 1 <= included_study_count <= len(self.sequence):
            raise ValueError("cumulative prefix count is outside the submitted study set")
        ordered = self.ordered_input_snapshot
        indexes = tuple(range(included_study_count))
        return _reorder_snapshot(ordered, indexes)

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "family": self.family,
            "input_snapshot": self.input_snapshot.to_mapping(),
            "ordering": self.ordering.to_mapping(),
            "sequence": [step.to_mapping() for step in self.sequence],
        }

    @classmethod
    def from_mapping(cls, value: object) -> CumulativeAnalysisSnapshot:
        mapping = _string_mapping(value, "cumulative analysis snapshot")
        if set(mapping) != {"version", "family", "input_snapshot", "ordering", "sequence"}:
            raise ValueError("cumulative analysis snapshot has unknown or missing fields")
        family = mapping["family"]
        if family not in ("binary", "continuous", "diagnostic"):
            raise ValueError("cumulative analysis snapshot family is unsupported")
        input_snapshot = _input_snapshot_from_mapping(
            family, mapping["input_snapshot"]
        )
        raw_sequence = mapping["sequence"]
        if not isinstance(raw_sequence, (list, tuple)):
            raise ValueError("cumulative sequence must be a list")
        return cls(
            version=_integer(mapping["version"], "cumulative snapshot version"),
            input_snapshot=input_snapshot,
            ordering=CumulativeOrderSpec.from_mapping(mapping["ordering"]),
            sequence=tuple(_cumulative_order_from_mapping(row) for row in raw_sequence),
        )


def freeze_cumulative_input(
    input_snapshot: CumulativeInputSnapshot,
    ordering: CumulativeOrderSpec,
) -> CumulativeAnalysisSnapshot:
    """Freeze an explicit project/year order without mutating the project snapshot."""
    return CumulativeAnalysisSnapshot(
        1, input_snapshot, ordering, _ordered_sequence(input_snapshot, ordering)
    )


def _ordered_sequence(
    input_snapshot: CumulativeInputSnapshot, ordering: CumulativeOrderSpec
) -> tuple[CumulativeStudyOrder, ...]:
    rows = _sequence_rows(input_snapshot, ordering)
    if ordering.field == "project_order":
        ordered_rows = _project_ordered_rows(rows, ordering)
    else:
        ordered_rows = _year_ordered_rows(rows, ordering)
    return _number_ordered_rows(ordered_rows)


def _sequence_rows(
    snapshot: CumulativeInputSnapshot, ordering: CumulativeOrderSpec
) -> list[CumulativeStudyOrder]:
    rows = []
    for source_order, study in enumerate(_input_studies(snapshot)):
        value = source_order + 1 if ordering.field == "project_order" else _study_year(study)
        rows.append(
            CumulativeStudyOrder(
                order=source_order,
                source_order=source_order,
                study_id=_study_id(study),
                study_name=cast(_StudyOrderInput, study).name,
                ordering_value=value,
                included_study_count=source_order + 1,
            )
        )
    return rows


def _project_ordered_rows(
    rows: list[CumulativeStudyOrder], ordering: CumulativeOrderSpec
) -> list[CumulativeStudyOrder]:
    return rows if ordering.direction == "ascending" else list(reversed(rows))


def _year_ordered_rows(
    rows: list[CumulativeStudyOrder], ordering: CumulativeOrderSpec
) -> list[CumulativeStudyOrder]:
    missing_rows, valued_rows = _partition_year_rows(rows)
    if missing_rows and ordering.missing_year_policy is None:
        raise ValueError("year ordering with missing years needs an explicit policy")
    sorted_valued_rows = sorted(
        valued_rows,
        key=lambda row: cast(int, row.ordering_value),
        reverse=ordering.direction == "descending",
    )
    return _place_missing_year_rows(missing_rows, sorted_valued_rows, ordering)


def _partition_year_rows(
    rows: list[CumulativeStudyOrder],
) -> tuple[list[CumulativeStudyOrder], list[CumulativeStudyOrder]]:
    missing = [row for row in rows if row.ordering_value is None]
    valued = [row for row in rows if row.ordering_value is not None]
    return missing, valued


def _place_missing_year_rows(
    missing: list[CumulativeStudyOrder],
    valued: list[CumulativeStudyOrder],
    ordering: CumulativeOrderSpec,
) -> list[CumulativeStudyOrder]:
    if ordering.missing_year_policy == "first":
        return missing + valued
    return valued + missing


def _number_ordered_rows(
    rows: list[CumulativeStudyOrder],
) -> tuple[CumulativeStudyOrder, ...]:
    return tuple(
        replace(row, order=index, included_study_count=index + 1)
        for index, row in enumerate(rows)
    )


@dataclass(frozen=True, slots=True)
class CumulativeValue:
    status: NumericStatus
    value: float | int | None
    reason: str | None

    def __post_init__(self) -> None:
        if self.status == "available":
            _validate_available_cumulative_value(self)
        elif self.status in ("not_estimable", "not_available"):
            _validate_unavailable_cumulative_value(self)
        else:
            raise ValueError("cumulative numeric status is invalid")

    def to_mapping(self) -> dict[str, object]:
        return {"status": self.status, "value": self.value, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class CumulativeStepResult:
    order: int
    source_order: int
    study_id: int
    study_name: str
    ordering_value: OrderingValue
    included_study_count: int
    analyzed_study_count: CumulativeValue
    estimate: CumulativeValue
    lower_bound: CumulativeValue
    upper_bound: CumulativeValue
    standard_error: CumulativeValue
    p_value: CumulativeValue
    status: CumulativeStepStatus
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        _validate_result_step_identity(self)
        _validate_result_step_status(self)
        _validate_result_step_values(self)

    def to_mapping(self, *, final_step: bool) -> dict[str, object]:
        return {
            "order": self.order,
            "source_order": self.source_order,
            "study_id": self.study_id,
            "study_name": self.study_name,
            "ordering_value": self.ordering_value,
            "included_study_count": self.included_study_count,
            "analyzed_study_count": self.analyzed_study_count.to_mapping(),
            "estimate": self.estimate.to_mapping(),
            "lower_bound": self.lower_bound.to_mapping(),
            "upper_bound": self.upper_bound.to_mapping(),
            "standard_error": self.standard_error.to_mapping(),
            "p_value": self.p_value.to_mapping(),
            "status": self.status,
            "failure_reason": self.failure_reason,
            "is_final": final_step,
        }


@dataclass(frozen=True, slots=True)
class CumulativeAnalysisResult:
    version: int
    status: Literal["complete", "partial"]
    ordering: CumulativeOrderSpec
    steps: tuple[CumulativeStepResult, ...]

    def __post_init__(self) -> None:
        if type(self.version) is not int or self.version != 1:
            raise ValueError("unsupported cumulative result version")
        _validate_result_sequence(self)

    @property
    def final_step(self) -> CumulativeStepResult:
        """The last prefix is the all-included result, even when it failed."""
        return self.steps[-1]

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "status": self.status,
            "ordering": self.ordering.to_mapping(),
            "steps": [
                step.to_mapping(final_step=index == len(self.steps) - 1)
                for index, step in enumerate(self.steps)
            ],
        }

    @classmethod
    def from_mapping(cls, value: object) -> CumulativeAnalysisResult:
        mapping = _string_mapping(value, "cumulative analysis result")
        if set(mapping) != {"version", "status", "ordering", "steps"}:
            raise ValueError("cumulative analysis result has unknown or missing fields")
        status = mapping["status"]
        if status not in ("complete", "partial"):
            raise ValueError("cumulative analysis result status is unsupported")
        rows = mapping["steps"]
        if not isinstance(rows, (list, tuple)):
            raise ValueError("cumulative result steps must be a list")
        for index, row in enumerate(rows):
            step = _string_mapping(row, "cumulative result step")
            if step.get("is_final") is not (index == len(rows) - 1):
                raise ValueError("cumulative final-step marker does not match its sequence")
        return cls(
            version=_integer(mapping["version"], "cumulative result version"),
            status=cast(Literal["complete", "partial"], status),
            ordering=CumulativeOrderSpec.from_mapping(mapping["ordering"]),
            steps=tuple(_cumulative_step_from_mapping(row) for row in rows),
        )


def _validate_result_sequence(result: CumulativeAnalysisResult) -> None:
    if not result.steps:
        raise ValueError("cumulative result must retain at least one step")
    if tuple(step.order for step in result.steps) != tuple(range(len(result.steps))):
        raise ValueError("cumulative result step order must be contiguous and ordered")
    expected = "complete" if all(step.status == "complete" for step in result.steps) else "partial"
    if result.status != expected:
        raise ValueError("cumulative result status does not match its steps")


def _validate_snapshot_studies(snapshot: CumulativeAnalysisSnapshot) -> None:
    if not snapshot.sequence:
        raise ValueError("cumulative analysis needs at least one included study")
    source_studies = _input_studies(snapshot.input_snapshot)
    if len(source_studies) != len(snapshot.sequence):
        raise ValueError("cumulative sequence does not match submitted study rows")
    source_ids = tuple(_study_id(study) for study in source_studies)
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("cumulative inputs contain duplicate study identities")
    if {step.study_id for step in snapshot.sequence} != set(source_ids):
        raise ValueError("cumulative sequence must contain every input study exactly once")


def _validate_snapshot_sequence(snapshot: CumulativeAnalysisSnapshot) -> None:
    sequence = snapshot.sequence
    positions = range(len(sequence))
    if tuple(step.order for step in sequence) != tuple(positions):
        raise ValueError("cumulative step order must be contiguous and ordered")
    if {step.source_order for step in sequence} != set(positions):
        raise ValueError("cumulative source order must identify each input row once")
    if any(step.included_study_count != step.order + 1 for step in sequence):
        raise ValueError("cumulative prefix counts must be contiguous")
    if sequence != _ordered_sequence(snapshot.input_snapshot, snapshot.ordering):
        raise ValueError("cumulative sequence does not match its declared ordering")


def _validate_study_order_position(order: CumulativeStudyOrder) -> None:
    if type(order.order) is not int or order.order < 0:
        raise ValueError("cumulative step order must be a non-negative integer")
    if type(order.source_order) is not int or order.source_order < 0:
        raise ValueError("cumulative source order must be a non-negative integer")
    if type(order.included_study_count) is not int or order.included_study_count != order.order + 1:
        raise ValueError("cumulative included-study count must match its step")


def _validate_study_order_identity(order: CumulativeStudyOrder) -> None:
    if type(order.study_id) is not int or order.study_id < 0:
        raise ValueError("cumulative study identity must be a non-negative integer")
    if not isinstance(order.study_name, str) or not order.study_name:
        raise ValueError("cumulative study name must be non-empty text")


def _validate_ordering_value(value: OrderingValue, label: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{label} must be finite or missing")
    if value is not None and not isinstance(value, (str, int, float, bool)):
        raise ValueError(f"{label} must be a scalar or missing")


def _validate_available_cumulative_value(value: CumulativeValue) -> None:
    if isinstance(value.value, bool) or not isinstance(value.value, (int, float)):
        raise ValueError("available cumulative values must be numeric")
    if not math.isfinite(value.value):
        raise ValueError("available cumulative values must be finite")
    if value.reason is not None:
        raise ValueError("available cumulative values cannot have a missing reason")


def _validate_unavailable_cumulative_value(value: CumulativeValue) -> None:
    if value.value is not None or not value.reason:
        raise ValueError("unavailable cumulative values need a reason and no value")


def _validate_result_step_identity(step: CumulativeStepResult) -> None:
    _validate_result_step_position(step)
    _validate_result_step_study(step)
    _validate_ordering_value(step.ordering_value, "cumulative ordering value")


def _validate_result_step_position(step: CumulativeStepResult) -> None:
    if type(step.order) is not int or step.order < 0:
        raise ValueError("cumulative result order must be a non-negative integer")
    if type(step.source_order) is not int or step.source_order < 0:
        raise ValueError("cumulative source order must be a non-negative integer")


def _validate_result_step_study(step: CumulativeStepResult) -> None:
    if type(step.study_id) is not int or step.study_id < 0:
        raise ValueError("cumulative study identity must be a non-negative integer")
    if not step.study_name:
        raise ValueError("cumulative study name must be non-empty")
    if step.included_study_count != step.order + 1:
        raise ValueError("cumulative prefix count must match its step order")


def _validate_result_step_status(step: CumulativeStepResult) -> None:
    if step.status not in ("complete", "partial", "not_estimable", "failed"):
        raise ValueError("cumulative step status is invalid")
    if step.status == "failed" and not step.failure_reason:
        raise ValueError("failed cumulative steps need a reason")
    if step.status != "failed" and step.failure_reason is not None:
        raise ValueError("only failed cumulative steps have a failure reason")


def _validate_result_step_values(step: CumulativeStepResult) -> None:
    if step.status == "complete":
        _validate_complete_step_values(step)
    if step.status == "not_estimable":
        _validate_nonestimable_step_value(step)
    if step.status == "failed":
        _validate_failed_step_values(step)


def _validate_complete_step_values(step: CumulativeStepResult) -> None:
    if any(
        value.status != "available"
        for value in (step.estimate, step.lower_bound, step.upper_bound)
    ):
        raise ValueError("complete cumulative steps need an estimate and interval")


def _validate_nonestimable_step_value(step: CumulativeStepResult) -> None:
    if step.estimate.status != "not_estimable":
        raise ValueError("not-estimable steps need a backend non-estimable estimate")


def _validate_failed_step_values(step: CumulativeStepResult) -> None:
    if any(value.status != "not_available" for value in _step_numeric_values(step)):
        raise ValueError("failed cumulative steps cannot contain backend values")


def _step_numeric_values(step: CumulativeStepResult) -> tuple[CumulativeValue, ...]:
    return (
        step.estimate,
        step.lower_bound,
        step.upper_bound,
        step.standard_error,
        step.p_value,
        step.analyzed_study_count,
    )


PrefixAnalyzer: TypeAlias = Callable[
    [CumulativeInputSnapshot, AnalysisRequest], object
]


def run_cumulative_analysis(
    snapshot: CumulativeAnalysisSnapshot,
    request: AnalysisRequest,
    analyze_prefix: PrefixAnalyzer,
) -> CumulativeAnalysisResult:
    """Fit every ordered prefix separately and retain a failed prefix in place."""
    if request.workflow != "cumulative":
        raise ValueError("cumulative analysis needs a cumulative request")
    if request.data_type != snapshot.family or request.metric != snapshot.input_snapshot.metric:
        raise ValueError("cumulative request does not match its frozen inputs")
    standard_request = replace(request, workflow="standard")
    results = []
    for order in snapshot.sequence:
        prefix = snapshot.prefix_input_snapshot(order.included_study_count)
        try:
            backend_result = analyze_prefix(prefix, standard_request)
            step = cumulative_step_from_backend(order, backend_result)
        except Exception as error:
            step = _failed_step(order, f"{type(error).__name__}: {error}")
        results.append(step)
    steps = tuple(results)
    status: Literal["complete", "partial"] = (
        "complete" if all(step.status == "complete" for step in steps) else "partial"
    )
    return CumulativeAnalysisResult(1, status, snapshot.ordering, steps)


def cumulative_step_from_backend(
    order: CumulativeStudyOrder, backend_result: object
) -> CumulativeStepResult:
    """Read one RCMetaR standard-fit model result without using display text."""
    backend = _string_mapping(backend_result, "cumulative backend result")
    model_value = backend.get("res", backend)
    model = _string_mapping(model_value, "cumulative backend model values")
    estimate = _backend_number(model, "b", "cumulative estimate")
    lower = _backend_number(model, "ci.lb", "cumulative lower bound")
    upper = _backend_number(model, "ci.ub", "cumulative upper bound")
    standard_error = _backend_number(model, "se", "cumulative standard error")
    p_value = _backend_number(model, "pval", "cumulative p-value")
    count = _validated_analyzed_count(
        _backend_number(model, "k", "analyzed study count"),
        order.included_study_count,
    )
    if estimate.status == "not_estimable":
        status: CumulativeStepStatus = "not_estimable"
    elif estimate.status != "available" or lower.status != "available" or upper.status != "available":
        status = "partial"
    else:
        status = "complete"
    return CumulativeStepResult(
        order=order.order,
        source_order=order.source_order,
        study_id=order.study_id,
        study_name=order.study_name,
        ordering_value=order.ordering_value,
        included_study_count=order.included_study_count,
        analyzed_study_count=count,
        estimate=estimate,
        lower_bound=lower,
        upper_bound=upper,
        standard_error=standard_error,
        p_value=p_value,
        status=status,
    )


def _failed_step(order: CumulativeStudyOrder, reason: str) -> CumulativeStepResult:
    unavailable = CumulativeValue("not_available", None, reason)
    return CumulativeStepResult(
        order.order,
        order.source_order,
        order.study_id,
        order.study_name,
        order.ordering_value,
        order.included_study_count,
        unavailable,
        unavailable,
        unavailable,
        unavailable,
        unavailable,
        unavailable,
        "failed",
        reason,
    )


def _backend_number(
    model: Mapping[str, object], key: str, label: str
) -> CumulativeValue:
    if key not in model:
        return CumulativeValue("not_available", None, f"The backend did not return {label}.")
    number = _scalar_number(model[key])
    if number is None:
        return CumulativeValue("not_estimable", None, f"The backend returned no finite {label}.")
    return CumulativeValue("available", number, None)


def _scalar_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (list, tuple)):
        return _single_finite_number(value)
    return None


def _single_finite_number(values: Sequence[object]) -> float | None:
    found: float | None = None
    for value in values:
        number = _scalar_number(value)
        if number is None:
            continue
        if found is not None:
            return None
        found = number
    return found


def _input_studies(snapshot: CumulativeInputSnapshot) -> tuple[object, ...]:
    return snapshot.studies


def _study_id(study: object) -> int:
    value = getattr(study, "study_id", None)
    if value is None:
        value = getattr(study, "id", None)
    if type(value) is not int or value < 0:
        raise ValueError("cumulative input study identity must be a non-negative integer")
    return value


def _study_year(study: object) -> int | None:
    value = getattr(study, "year", None)
    if value in (None, "", 0):
        return None
    if type(value) is not int:
        raise ValueError("cumulative study years must be integers or missing")
    return value


def _reorder_snapshot(
    snapshot: CumulativeInputSnapshot, indexes: tuple[int, ...]
) -> CumulativeInputSnapshot:
    studies = _input_studies(snapshot)
    _validate_reorder_indexes(studies, indexes)
    ordered_studies = tuple(studies[index] for index in indexes)
    if isinstance(snapshot, BinaryInputSnapshot):
        return _reorder_binary_snapshot(snapshot, ordered_studies, indexes)
    if isinstance(snapshot, ContinuousInputSnapshot):
        return _reorder_continuous_snapshot(snapshot, ordered_studies, indexes)
    return replace(snapshot, studies=ordered_studies)


def _validate_reorder_indexes(studies: tuple[object, ...], indexes: tuple[int, ...]) -> None:
    if len(set(indexes)) != len(indexes):
        raise ValueError("cumulative snapshot order references invalid source rows")
    if any(not 0 <= index < len(studies) for index in indexes):
        raise ValueError("cumulative snapshot order references invalid source rows")


def _reorder_binary_snapshot(
    snapshot: BinaryInputSnapshot,
    studies: tuple[object, ...],
    indexes: tuple[int, ...],
) -> BinaryInputSnapshot:
    covariates = tuple(
        replace(covariate, values=tuple(covariate.values[index] for index in indexes))
        for covariate in snapshot.covariates
    )
    return replace(snapshot, studies=studies, covariates=covariates)


def _reorder_continuous_snapshot(
    snapshot: ContinuousInputSnapshot,
    studies: tuple[object, ...],
    indexes: tuple[int, ...],
) -> ContinuousInputSnapshot:
    covariates = tuple(
        replace(covariate, values=tuple(covariate.values[index] for index in indexes))
        for covariate in snapshot.covariates
    )
    return replace(snapshot, studies=studies, covariates=covariates)


def _string_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{label} must be a string-keyed object")
    return cast(Mapping[str, object], value)


def _input_snapshot_from_mapping(family: object, value: object) -> CumulativeInputSnapshot:
    if family == "continuous":
        return ContinuousInputSnapshot.from_mapping(value)
    if family == "diagnostic":
        return DiagnosticInputSnapshot.from_mapping(value)
    if family != "binary":
        raise ValueError("cumulative analysis snapshot family is unsupported")
    return _binary_input_snapshot_from_mapping(value)


def _binary_input_snapshot_from_mapping(value: object) -> BinaryInputSnapshot:
    mapping = _string_mapping(value, "binary input snapshot")
    _validate_binary_snapshot_fields(mapping)
    metric = _required_string(mapping["metric"], "binary input snapshot metric")
    groups = _string_sequence(mapping["groups"], "binary input snapshot groups")
    raw_studies = _mapping_sequence(mapping["studies"], "binary input snapshot studies")
    raw_covariates = _mapping_sequence(mapping["covariates"], "binary input snapshot covariates")
    raw_counts_available = _required_bool(
        mapping["raw_counts_available"], "binary raw-count availability"
    )
    one_arm = metric in BINARY_ONE_ARM_METRICS
    studies = _binary_studies_from_mapping(raw_studies, one_arm)
    covariates = _binary_covariates_from_mapping(raw_covariates)
    return BinaryInputSnapshot(
        _integer(mapping["version"], "binary snapshot version"),
        _text(mapping["outcome"], "binary outcome"),
        _text(mapping["time_point"], "binary time point"),
        groups,
        metric,
        raw_counts_available,
        tuple(studies),
        tuple(covariates),
    )


def _validate_binary_snapshot_fields(mapping: Mapping[str, object]) -> None:
    expected = {
        "version", "outcome", "time_point", "groups", "metric",
        "raw_counts_available", "studies", "covariates",
    }
    if set(mapping) != expected:
        raise ValueError("binary input snapshot has unknown or missing fields")


def _required_string(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text")
    return value


def _string_sequence(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be a list")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{label} must contain text")
    return tuple(cast(str, item) for item in value)


def _mapping_sequence(value: object, label: str) -> tuple[object, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be a list")
    return tuple(value)


def _required_bool(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{label} must be boolean")
    return value


def _binary_studies_from_mapping(
    rows: tuple[object, ...], one_arm: bool
) -> list[BinaryStudyInput | SingleArmBinaryStudyInput]:
    return [_binary_study_from_mapping(row, one_arm) for row in rows]


def _binary_study_from_mapping(
    value: object, one_arm: bool
) -> BinaryStudyInput | SingleArmBinaryStudyInput:
    study = _string_mapping(value, "binary input study")
    expected = _binary_study_fields(one_arm)
    if set(study) != expected:
        raise ValueError("binary input study has unknown or missing fields")
    study_id = _integer(study["id"], "binary study id")
    study_name = _text(study["name"], "binary study name")
    study_year = _optional_integer(study["year"], "binary study year")
    estimate = _optional_number(study["estimate"], "binary study estimate")
    standard_error = _optional_number(
        study["standard_error"], "binary study standard error"
    )
    if one_arm:
        return SingleArmBinaryStudyInput(
            id=study_id,
            name=study_name,
            year=study_year,
            estimate=estimate,
            standard_error=standard_error,
            events=_optional_integer(study["events"], "events"),
            total=_optional_integer(study["total"], "total"),
        )
    return BinaryStudyInput(
        id=study_id,
        name=study_name,
        year=study_year,
        estimate=estimate,
        standard_error=standard_error,
        treatment_events=_optional_integer(study["treatment_events"], "treatment events"),
        treatment_total=_optional_integer(study["treatment_total"], "treatment total"),
        control_events=_optional_integer(study["control_events"], "control events"),
        control_total=_optional_integer(study["control_total"], "control total"),
    )


def _binary_study_fields(one_arm: bool) -> set[str]:
    if one_arm:
        return {"id", "name", "year", "estimate", "standard_error", "events", "total"}
    return {
        "id", "name", "year", "estimate", "standard_error",
        "treatment_events", "treatment_total", "control_events", "control_total",
    }


def _binary_covariates_from_mapping(
    rows: tuple[object, ...],
) -> list[BinaryCovariateInput]:
    return [_binary_covariate_from_mapping(row) for row in rows]


def _binary_covariate_from_mapping(value: object) -> BinaryCovariateInput:
    covariate = _string_mapping(value, "binary covariate")
    if set(covariate) != {"name", "data_type", "values"}:
        raise ValueError("binary covariate has unknown or missing fields")
    values = covariate["values"]
    if not isinstance(values, (list, tuple)):
        raise ValueError("binary covariate values must be a list")
    return BinaryCovariateInput(
        _text(covariate["name"], "binary covariate name"),
        _text(covariate["data_type"], "binary covariate type"),
        tuple(_json_scalar(item, "binary covariate value") for item in values),
    )


def _cumulative_order_from_mapping(value: object) -> CumulativeStudyOrder:
    row = _string_mapping(value, "cumulative sequence step")
    if set(row) != {
        "order", "source_order", "study_id", "study_name", "ordering_value",
        "included_study_count",
    }:
        raise ValueError("cumulative sequence step has unknown or missing fields")
    ordering_value = row["ordering_value"]
    if ordering_value is not None:
        ordering_value = _json_scalar(ordering_value, "cumulative ordering value")
    return CumulativeStudyOrder(
        _integer(row["order"], "cumulative order"),
        _integer(row["source_order"], "cumulative source order"),
        _integer(row["study_id"], "cumulative study id"),
        _text(row["study_name"], "cumulative study name"),
        ordering_value,
        _integer(row["included_study_count"], "cumulative prefix count"),
    )


def _cumulative_step_from_mapping(value: object) -> CumulativeStepResult:
    row = _string_mapping(value, "cumulative result step")
    fields = {
        "order", "source_order", "study_id", "study_name", "ordering_value",
        "included_study_count", "analyzed_study_count", "estimate", "lower_bound",
        "upper_bound", "standard_error", "p_value", "status", "failure_reason",
        "is_final",
    }
    if set(row) != fields or type(row["is_final"]) is not bool:
        raise ValueError("cumulative result step has unknown or missing fields")
    status = row["status"]
    if status not in ("complete", "partial", "not_estimable", "failed"):
        raise ValueError("cumulative result step status is unsupported")
    ordering_value = row["ordering_value"]
    if ordering_value is not None:
        ordering_value = _json_scalar(ordering_value, "cumulative ordering value")
    reason = row["failure_reason"]
    if reason is not None and not isinstance(reason, str):
        raise ValueError("cumulative failure reason must be text or missing")
    included_count = _integer(
        row["included_study_count"], "cumulative result prefix count"
    )
    analyzed_count = _validated_analyzed_count(
        _cumulative_value_from_mapping(row["analyzed_study_count"]), included_count
    )
    return CumulativeStepResult(
        order=_integer(row["order"], "cumulative result order"),
        source_order=_integer(row["source_order"], "cumulative result source order"),
        study_id=_integer(row["study_id"], "cumulative result study id"),
        study_name=_text(row["study_name"], "cumulative result study name"),
        ordering_value=ordering_value,
        included_study_count=included_count,
        analyzed_study_count=analyzed_count,
        estimate=_cumulative_value_from_mapping(row["estimate"]),
        lower_bound=_cumulative_value_from_mapping(row["lower_bound"]),
        upper_bound=_cumulative_value_from_mapping(row["upper_bound"]),
        standard_error=_cumulative_value_from_mapping(row["standard_error"]),
        p_value=_cumulative_value_from_mapping(row["p_value"]),
        status=cast(CumulativeStepStatus, status),
        failure_reason=reason,
    )


def _cumulative_value_from_mapping(value: object) -> CumulativeValue:
    row = _string_mapping(value, "cumulative numeric value")
    if set(row) != {"status", "value", "reason"}:
        raise ValueError("cumulative numeric value has unknown or missing fields")
    status = row["status"]
    if status not in ("available", "not_estimable", "not_available"):
        raise ValueError("cumulative numeric status is unsupported")
    numeric = row["value"]
    if numeric is not None:
        numeric = _optional_number(numeric, "cumulative numeric value")
    reason = row["reason"]
    if reason is not None and not isinstance(reason, str):
        raise ValueError("cumulative numeric reason must be text or missing")
    return CumulativeValue(cast(NumericStatus, status), numeric, reason)


def _validated_analyzed_count(
    count: CumulativeValue, included_study_count: int
) -> CumulativeValue:
    if count.status != "available":
        return count
    value = cast(float | int, count.value)
    if not float(value).is_integer():
        raise ValueError("analyzed study count must be a whole number")
    if value < 0:
        raise ValueError("analyzed study count cannot be negative")
    if value > included_study_count:
        raise ValueError("backend analyzed study count exceeds the cumulative prefix")
    return replace(count, value=int(value))


def _integer(value: object, label: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{label} must be an integer")
    return value


def _optional_integer(value: object, label: str) -> int | None:
    return None if value is None else _integer(value, label)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be non-empty text")
    return value


def _optional_number(value: object, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric or missing")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _json_scalar(value: object, label: str) -> OrderingValue:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise ValueError(f"{label} must be a finite JSON scalar")
