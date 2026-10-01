# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Frozen subgroup input preparation and conservative result parsing."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
import math
import re
from typing import Literal, TypeAlias, TypeGuard, TypeVar, cast

from rc_metastudio.analysis_contracts import (
    AnalysisRequest,
    AnalysisResult,
    make_analysis_request,
)
from rc_metastudio.analysis_snapshot import BinaryCovariateInput, BinaryInputSnapshot
from rc_metastudio.continuous_analysis_snapshot import (
    ContinuousCovariateInput,
    ContinuousInputSnapshot,
)
from rc_metastudio.diagnostic_analysis_snapshot import (
    DiagnosticCovariateInput,
    DiagnosticInputSnapshot,
)


MissingCovariatePolicy = Literal["exclude", "missing_category"]
SubgroupFamily = Literal["binary", "continuous", "diagnostic"]
StudyStatus = Literal["included", "excluded_missing"]
ResultStatus = Literal["available", "not_available"]
Scalar: TypeAlias = str | int | float | bool | None
ModelValues: TypeAlias = tuple[tuple[float, str], ...]


def _is_string_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping) and all(isinstance(key, str) for key in value)

_MISSING_CODE = "__RCMS_MISSING__"
_PLAN_FIELDS = frozenset(
    {
        "version",
        "family",
        "metric",
        "covariate_name",
        "missing_policy",
        "assignments",
        "levels",
    }
)
_NUMBER = re.compile(r"[<>]?\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_HETEROGENEITY = re.compile(
    r"^\s*(?P<q>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*"
    r"\(\s*(?P<df>\d+)\s*\)\s+(?P<p>[<>]?\s*"
    r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s+"
    r"(?P<i2>[+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*%\s*$"
)


@dataclass(frozen=True, slots=True)
class SubgroupStudyAssignment:
    study_id: int
    study_name: str
    value: Scalar
    status: StudyStatus
    backend_value: str | None

    def to_mapping(self) -> dict[str, object]:
        return {
            "study_id": self.study_id,
            "study_name": self.study_name,
            "value": self.value,
            "status": self.status,
            "backend_value": self.backend_value,
        }


@dataclass(frozen=True, slots=True)
class SubgroupLevel:
    value: Scalar
    label: str
    backend_value: str
    study_ids: tuple[int, ...]
    is_missing_category: bool = False

    @property
    def included_count(self) -> int:
        return len(self.study_ids)

    def to_mapping(self) -> dict[str, object]:
        return {
            "value": self.value,
            "label": self.label,
            "backend_value": self.backend_value,
            "study_ids": list(self.study_ids),
            "is_missing_category": self.is_missing_category,
        }


@dataclass(frozen=True, slots=True)
class SubgroupPlan:
    """Saved covariate choice and per-study missing-value decisions."""

    version: int
    family: SubgroupFamily
    metric: str
    covariate_name: str
    missing_policy: MissingCovariatePolicy
    assignments: tuple[SubgroupStudyAssignment, ...]
    levels: tuple[SubgroupLevel, ...]

    @property
    def included_count(self) -> int:
        return sum(assignment.status == "included" for assignment in self.assignments)

    @property
    def missing_count(self) -> int:
        return sum(assignment.value is None or assignment.value == "" for assignment in self.assignments)

    @property
    def excluded_count(self) -> int:
        return sum(assignment.status == "excluded_missing" for assignment in self.assignments)

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": self.version,
            "family": self.family,
            "metric": self.metric,
            "covariate_name": self.covariate_name,
            "missing_policy": self.missing_policy,
            "assignments": [row.to_mapping() for row in self.assignments],
            "levels": [level.to_mapping() for level in self.levels],
        }

    @classmethod
    def from_mapping(cls, value: object) -> SubgroupPlan:
        mapping = _plan_mapping(value)
        _validate_plan_version(mapping["version"])
        family = _plan_family(mapping["family"])
        policy = _plan_missing_policy(mapping["missing_policy"])
        metric = _plan_text(mapping["metric"], "metric")
        covariate_name = _plan_text(mapping["covariate_name"], "covariate name")
        assignments = _plan_rows(mapping["assignments"])
        levels = _plan_rows(mapping["levels"])
        plan = cls(
            1,
            family,
            metric,
            covariate_name,
            policy,
            tuple(_assignment_from_mapping(row) for row in assignments),
            tuple(_level_from_mapping(row) for row in levels),
        )
        _validate_plan_shape(plan)
        return plan


Snapshot: TypeAlias = (
    BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot
)
_Covariate = TypeVar(
    "_Covariate",
    BinaryCovariateInput,
    ContinuousCovariateInput,
    DiagnosticCovariateInput,
)


def _plan_mapping(value: object) -> Mapping[str, object]:
    if not _is_string_mapping(value):
        raise ValueError("subgroup plan must be an object")
    if set(value) != _PLAN_FIELDS:
        raise ValueError("subgroup plan has unknown or missing fields")
    return value


def _validate_plan_version(value: object) -> None:
    if type(value) is not int or value != 1:
        raise ValueError("unsupported subgroup plan version")


def _plan_family(value: object) -> SubgroupFamily:
    if value not in ("binary", "continuous", "diagnostic"):
        raise ValueError("subgroup plan family is unsupported")
    return cast(SubgroupFamily, value)


def _plan_missing_policy(value: object) -> MissingCovariatePolicy:
    if value not in ("exclude", "missing_category"):
        raise ValueError("subgroup plan needs an explicit missing-value policy")
    return cast(MissingCovariatePolicy, value)


def _plan_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"subgroup plan {label} must be non-empty text")
    return value


def _plan_rows(value: object) -> tuple[object, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError("subgroup plan assignments and levels must be lists")
    return tuple(value)


def create_subgroup_plan(
    snapshot: Snapshot,
    covariate_name: str,
    *,
    missing_policy: MissingCovariatePolicy,
) -> SubgroupPlan:
    """Freeze factor levels and an explicit decision for every missing value."""
    family = _validated_snapshot_family(snapshot)
    _validate_subgroup_selection(covariate_name, missing_policy)
    values = _selected_factor_values(snapshot, covariate_name)
    study_rows = _subgroup_study_identities(snapshot)
    if len(values) != len(study_rows):
        raise ValueError("subgroup covariate values do not match frozen study rows")

    known_codes = {str(value) for value in values if not _is_missing(value)}
    missing_code = _fresh_missing_code(known_codes)
    assignments, level_values, level_ids, missing_ids = _assign_studies(
        study_rows, values, missing_policy, missing_code
    )
    levels = _subgroup_levels(level_values, level_ids, missing_ids, missing_code)
    if len(levels) < 2:
        raise ValueError("subgroup analysis needs at least two non-empty subgroup levels")
    plan = SubgroupPlan(
        version=1,
        family=family,
        metric=snapshot.metric,
        covariate_name=covariate_name,
        missing_policy=missing_policy,
        assignments=tuple(assignments),
        levels=tuple(levels),
    )
    _validate_plan_shape(plan)
    return plan


def _validated_snapshot_family(snapshot: Snapshot) -> SubgroupFamily:
    family = _snapshot_family(snapshot)
    if isinstance(snapshot, DiagnosticInputSnapshot) and snapshot.version < 2:
        raise ValueError(
            "diagnostic subgroup analysis requires a frozen snapshot with covariates"
        )
    return family


def _snapshot_family(snapshot: Snapshot) -> SubgroupFamily:
    if not isinstance(
        snapshot,
        (BinaryInputSnapshot, ContinuousInputSnapshot, DiagnosticInputSnapshot),
    ):
        raise TypeError("subgroup analysis requires a frozen analysis input")
    if isinstance(snapshot, BinaryInputSnapshot):
        return "binary"
    if isinstance(snapshot, ContinuousInputSnapshot):
        return "continuous"
    return "diagnostic"


def _validate_subgroup_selection(
    covariate_name: str, missing_policy: MissingCovariatePolicy
) -> None:
    if missing_policy not in ("exclude", "missing_category"):
        raise ValueError("choose whether studies with missing covariates are excluded or grouped")
    if not isinstance(covariate_name, str) or not covariate_name:
        raise ValueError("select a covariate for subgroup analysis")


def _selected_factor_values(snapshot: Snapshot, covariate_name: str) -> tuple[Scalar, ...]:
    covariate = next(
        (row for row in snapshot.covariates if row.name == covariate_name), None
    )
    if covariate is None:
        raise ValueError(f"subgroup covariate {covariate_name!r} is not in the frozen input")
    if covariate.data_type != "factor":
        raise ValueError("subgroup analysis requires a categorical covariate")
    return covariate.values


def _subgroup_study_identities(snapshot: Snapshot) -> tuple[tuple[int, str], ...]:
    if isinstance(snapshot, (BinaryInputSnapshot, DiagnosticInputSnapshot)):
        return tuple((study.id, study.name) for study in snapshot.studies)
    return tuple((study.study_id, study.name) for study in snapshot.studies)


def _assign_studies(
    study_rows: tuple[tuple[int, str], ...],
    values: tuple[Scalar, ...],
    missing_policy: MissingCovariatePolicy,
    missing_code: str,
) -> tuple[
    tuple[SubgroupStudyAssignment, ...],
    dict[str, Scalar],
    dict[str, list[int]],
    tuple[int, ...],
]:
    assignments: list[SubgroupStudyAssignment] = []
    level_values: dict[str, Scalar] = {}
    level_ids: dict[str, list[int]] = {}
    missing_ids: list[int] = []
    for (study_id, study_name), value in zip(study_rows, values, strict=True):
        assignment, backend_value = _assignment_for_value(
            study_id, study_name, value, missing_policy, missing_code, level_values
        )
        assignments.append(assignment)
        if assignment.status == "excluded_missing":
            continue
        if _is_missing(value):
            missing_ids.append(study_id)
        level_ids.setdefault(cast(str, backend_value), []).append(study_id)
    return tuple(assignments), level_values, level_ids, tuple(missing_ids)


def _assignment_for_value(
    study_id: int,
    study_name: str,
    value: Scalar,
    missing_policy: MissingCovariatePolicy,
    missing_code: str,
    level_values: dict[str, Scalar],
) -> tuple[SubgroupStudyAssignment, str | None]:
    if _is_missing(value):
        if missing_policy == "exclude":
            return (
                SubgroupStudyAssignment(
                    study_id, study_name, value, "excluded_missing", None
                ),
                None,
            )
        backend_value = missing_code
    else:
        backend_value = str(value)
        previous = level_values.get(backend_value, value)
        if previous != value or type(previous) is not type(value):
            raise ValueError(
                "categorical covariate values collapse to the same RCMetaR label; "
                "rename or recode those levels before subgroup analysis"
            )
        level_values[backend_value] = value
    return (
        SubgroupStudyAssignment(study_id, study_name, value, "included", backend_value),
        backend_value,
    )


def _subgroup_levels(
    level_values: Mapping[str, Scalar],
    level_ids: Mapping[str, Sequence[int]],
    missing_ids: tuple[int, ...],
    missing_code: str,
) -> tuple[SubgroupLevel, ...]:
    levels = [
        SubgroupLevel(value, code, code, tuple(level_ids[code]))
        for code, value in level_values.items()
        if code != missing_code
    ]
    if missing_ids:
        levels.append(
            SubgroupLevel(None, "Missing values", missing_code, missing_ids, True)
        )
    return tuple(levels)


def prepare_subgroup_snapshot(snapshot: Snapshot, plan: SubgroupPlan) -> Snapshot:
    """Apply the saved missing policy while keeping all frozen rows aligned."""
    expected = create_subgroup_plan(
        snapshot, plan.covariate_name, missing_policy=plan.missing_policy
    )
    if expected != plan:
        raise ValueError("subgroup plan does not match the frozen analysis input")
    if plan.family == "binary" and isinstance(snapshot, BinaryInputSnapshot):
        return _prepare_binary_subgroup_snapshot(snapshot, plan)
    if plan.family == "continuous" and isinstance(snapshot, ContinuousInputSnapshot):
        return _prepare_continuous_subgroup_snapshot(snapshot, plan)
    if plan.family == "diagnostic" and isinstance(snapshot, DiagnosticInputSnapshot):
        return _prepare_diagnostic_subgroup_snapshot(snapshot, plan)
    raise ValueError("subgroup plan family does not match its frozen input")


def _included_study_ids(plan: SubgroupPlan) -> set[int]:
    return {
        row.study_id for row in plan.assignments if row.status == "included"
    }


def _prepared_covariates(
    covariates: tuple[_Covariate, ...],
    plan: SubgroupPlan,
    study_ids: tuple[int, ...],
    included_ids: set[int],
) -> tuple[_Covariate, ...]:
    assignments = {row.study_id: row for row in plan.assignments}
    return tuple(
        replace(
            covariate,
            values=tuple(
                assignments[study_id].backend_value
                if covariate.name == plan.covariate_name
                else covariate.values[index]
                for index, study_id in enumerate(study_ids)
                if study_id in included_ids
            ),
        )
        for covariate in covariates
    )


def _prepare_binary_subgroup_snapshot(
    snapshot: BinaryInputSnapshot, plan: SubgroupPlan
) -> BinaryInputSnapshot:
    included_ids = _included_study_ids(plan)
    study_ids = tuple(study.id for study in snapshot.studies)
    rows = tuple(study for study in snapshot.studies if study.id in included_ids)
    covariates = _prepared_covariates(snapshot.covariates, plan, study_ids, included_ids)
    return replace(snapshot, studies=rows, covariates=covariates)


def _prepare_continuous_subgroup_snapshot(
    snapshot: ContinuousInputSnapshot, plan: SubgroupPlan
) -> ContinuousInputSnapshot:
    included_ids = _included_study_ids(plan)
    study_ids = tuple(study.study_id for study in snapshot.studies)
    rows = tuple(study for study in snapshot.studies if study.study_id in included_ids)
    covariates = _prepared_covariates(snapshot.covariates, plan, study_ids, included_ids)
    return replace(snapshot, studies=rows, covariates=covariates)


def _prepare_diagnostic_subgroup_snapshot(
    snapshot: DiagnosticInputSnapshot, plan: SubgroupPlan
) -> DiagnosticInputSnapshot:
    included_ids = _included_study_ids(plan)
    study_ids = tuple(study.id for study in snapshot.studies)
    rows = tuple(study for study in snapshot.studies if study.id in included_ids)
    covariates = _prepared_covariates(snapshot.covariates, plan, study_ids, included_ids)
    return replace(snapshot, studies=rows, covariates=covariates)


def create_subgroup_request(
    snapshot: Snapshot,
    plan: SubgroupPlan,
    *,
    method: str,
    parameters: Mapping[str, object],
) -> AnalysisRequest:
    """Build a subgroup request from the frozen family and selected moderator."""
    snapshot_family = _snapshot_family(snapshot)
    if plan.family != snapshot_family:
        raise ValueError("subgroup plan family does not match its frozen input")
    if plan.metric != snapshot.metric:
        raise ValueError("subgroup plan metric does not match its frozen input")
    if create_subgroup_plan(
        snapshot, plan.covariate_name, missing_policy=plan.missing_policy
    ) != plan:
        raise ValueError("subgroup plan does not match the frozen analysis input")
    values = dict(parameters)
    if "cov_name" in values and values["cov_name"] != plan.covariate_name:
        raise ValueError("subgroup request cov_name must match the frozen subgroup plan")
    values["cov_name"] = plan.covariate_name
    return make_analysis_request(
        data_type=plan.family,
        workflow="subgroup",
        method=method,
        metric=plan.metric,
        parameters=values,
    )


@dataclass(frozen=True, slots=True)
class SubgroupModelResult:
    label: str
    included_count: int
    status: ResultStatus
    reason: str | None
    estimate: float | None = None
    lower_bound: float | None = None
    upper_bound: float | None = None
    standard_error: float | None = None
    p_value: float | None = None
    p_value_text: str | None = None
    z_value: float | None = None

    def to_mapping(self) -> dict[str, object]:
        return {
            "label": self.label,
            "included_count": self.included_count,
            "status": self.status,
            "reason": self.reason,
            "estimate": self.estimate,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "standard_error": self.standard_error,
            "p_value": self.p_value,
            "p_value_text": self.p_value_text,
            "z_value": self.z_value,
        }


@dataclass(frozen=True, slots=True)
class SubgroupHeterogeneity:
    label: str
    status: ResultStatus
    reason: str | None
    q: float | None = None
    degrees_of_freedom: int | None = None
    p_value: float | None = None
    p_value_text: str | None = None
    i_squared: float | None = None

    def to_mapping(self) -> dict[str, object]:
        return {
            "label": self.label,
            "status": self.status,
            "reason": self.reason,
            "q": self.q,
            "degrees_of_freedom": self.degrees_of_freedom,
            "p_value": self.p_value,
            "p_value_text": self.p_value_text,
            "i_squared": self.i_squared,
        }


@dataclass(frozen=True, slots=True)
class BetweenSubgroupTest:
    status: Literal["available", "not_calculated"]
    reason: str | None
    statistic: float | None = None
    degrees_of_freedom: float | None = None
    p_value: float | None = None

    def to_mapping(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "statistic": self.statistic,
            "degrees_of_freedom": self.degrees_of_freedom,
            "p_value": self.p_value,
        }


@dataclass(frozen=True, slots=True)
class SubgroupAnalysisResult:
    covariate_name: str
    missing_policy: MissingCovariatePolicy
    included_count: int
    missing_count: int
    excluded_count: int
    levels: tuple[SubgroupModelResult, ...]
    overall: SubgroupModelResult
    heterogeneity: tuple[SubgroupHeterogeneity, ...]
    between_subgroup_test: BetweenSubgroupTest
    figure_status: Literal["available", "not_available"]

    def to_mapping(self) -> dict[str, object]:
        return {
            "version": 1,
            "covariate_name": self.covariate_name,
            "missing_policy": self.missing_policy,
            "included_count": self.included_count,
            "missing_count": self.missing_count,
            "excluded_count": self.excluded_count,
            "levels": [level.to_mapping() for level in self.levels],
            "overall": self.overall.to_mapping(),
            "heterogeneity": [row.to_mapping() for row in self.heterogeneity],
            "between_subgroup_test": self.between_subgroup_test.to_mapping(),
            "figure_status": self.figure_status,
        }


def parse_subgroup_result(
    summary: str,
    plan: SubgroupPlan,
    *,
    figure_available: bool = False,
    between_subgroup_test: Mapping[str, object] | None = None,
) -> SubgroupAnalysisResult:
    """Parse only backend-reported subgroup values; never compare p-values."""
    if not isinstance(summary, str) or "Model Results" not in summary:
        raise ValueError("RCMetaR did not return a subgroup model summary")
    binary = plan.family in ("binary", "diagnostic")
    model_lines = _section_lines(summary, "Model Results", "Heterogeneity")
    heterogeneity_lines = _section_lines(summary, "Heterogeneity", None)
    model_rows, overall_values = _parse_model_rows(model_lines, plan.levels, binary)
    results = tuple(
        _level_model_result(level, model_rows[level.backend_value], binary)
        for level in plan.levels
    )
    overall = _overall_model_result(plan, overall_values, binary)
    heterogeneity = _parse_heterogeneity(heterogeneity_lines, plan.levels)
    between = _between_result(between_subgroup_test)
    return SubgroupAnalysisResult(
        covariate_name=plan.covariate_name,
        missing_policy=plan.missing_policy,
        included_count=plan.included_count,
        missing_count=plan.missing_count,
        excluded_count=plan.excluded_count,
        levels=results,
        overall=overall,
        heterogeneity=heterogeneity,
        between_subgroup_test=between,
        figure_status="available" if figure_available else "not_available",
    )


def _parse_model_rows(
    lines: Sequence[str], levels: Sequence[SubgroupLevel], binary: bool
) -> tuple[dict[str, ModelValues | None], ModelValues | None]:
    rows: dict[str, ModelValues | None] = {
        level.backend_value: None for level in levels
    }
    prefixes = tuple((level, f"Subgroup {level.backend_value}") for level in levels)
    _record_model_rows(lines, prefixes, rows, binary)
    return rows, _overall_model_values(lines, binary)


def _record_model_rows(
    lines: Sequence[str],
    prefixes: Sequence[tuple[SubgroupLevel, str]],
    rows: dict[str, ModelValues | None],
    binary: bool,
) -> None:
    for line in lines:
        match = _matching_model_row(line, prefixes, binary)
        if match is None:
            continue
        level, _prefix, values = match
        if rows[level.backend_value] is not None:
            raise ValueError(
                f"RCMetaR returned duplicate model rows for subgroup {level.label!r}"
            )
        rows[level.backend_value] = values


def _overall_model_values(lines: Sequence[str], binary: bool) -> ModelValues | None:
    overall_line = next(
        (line for line in lines if _row_has_prefix(line, "Overall")), None
    )
    if overall_line is None:
        return None
    return _model_row(overall_line, "Overall", binary)


def _matching_model_row(
    line: str,
    prefixes: Sequence[tuple[SubgroupLevel, str]],
    binary: bool,
) -> tuple[SubgroupLevel, str, ModelValues] | None:
    candidates = _model_row_candidates(line, prefixes, binary)
    if not candidates:
        return None
    longest = max(len(prefix) for _level, prefix, _values in candidates)
    most_specific = [item for item in candidates if len(item[1]) == longest]
    if len(most_specific) != 1:
        raise ValueError("RCMetaR returned an ambiguous subgroup model row")
    return most_specific[0]


def _model_row_candidates(
    line: str,
    prefixes: Sequence[tuple[SubgroupLevel, str]],
    binary: bool,
) -> tuple[tuple[SubgroupLevel, str, ModelValues], ...]:
    matches = []
    for level, prefix in prefixes:
        if not _row_has_prefix(line, prefix):
            continue
        try:
            values = _model_row(line, prefix, binary)
        except ValueError:
            continue
        if binary and values[0][0] != level.included_count:
            continue
        matches.append((level, prefix, values))
    return tuple(matches)


def _level_model_result(
    level: SubgroupLevel, values: ModelValues | None, binary: bool
) -> SubgroupModelResult:
    if values is None:
        return SubgroupModelResult(
            label=level.label,
            included_count=level.included_count,
            status="not_available",
            reason="RCMetaR returned no model row for this subgroup level",
        )
    return _model_result(level.label, level.included_count, values, binary)


def _overall_model_result(
    plan: SubgroupPlan, values: ModelValues | None, binary: bool
) -> SubgroupModelResult:
    if values is None:
        return SubgroupModelResult(
            "Overall",
            plan.included_count,
            "not_available",
            "RCMetaR returned no overall model row",
        )
    return _model_result("Overall", plan.included_count, values, binary)


def _between_result(
    value: Mapping[str, object] | None,
) -> BetweenSubgroupTest:
    if value is not None:
        return _between_group_test_from_backend(value)
    return BetweenSubgroupTest(
        "not_calculated",
        "RCMetaR's subgroup result provides within-subgroup heterogeneity only; "
        "it returned no between-subgroup test.",
    )


def subgroup_figure_available(result: AnalysisResult) -> bool:
    return any(
        section.kind == "image" and section.plot_kind == "subgroup_forest"
        for section in result.sections
    )


def render_subgroup_result(
    result: SubgroupAnalysisResult, plan: SubgroupPlan
) -> str:
    """Render the saved typed subgroup values without recomputing any statistic."""
    _validate_render_plan(result, plan)
    lines = _subgroup_summary_lines(result)
    lines.extend(_missing_assignment_lines(plan))
    lines.extend(_render_model_result(model) for model in (*result.levels, result.overall))
    if result.heterogeneity:
        lines.extend(("", "Within-subgroup heterogeneity:"))
        lines.extend(_render_heterogeneity(row) for row in result.heterogeneity)
    lines.extend(_between_test_lines(result.between_subgroup_test))
    lines.append(
        "Within-subgroup p-values do not test differences between subgroup levels."
    )
    return "\n".join(lines)


def _validate_render_plan(result: SubgroupAnalysisResult, plan: SubgroupPlan) -> None:
    if (
        result.covariate_name != plan.covariate_name
        or result.missing_policy != plan.missing_policy
        or result.included_count != plan.included_count
        or result.missing_count != plan.missing_count
        or result.excluded_count != plan.excluded_count
    ):
        raise ValueError("subgroup result does not match its frozen inclusion plan")


def _subgroup_summary_lines(result: SubgroupAnalysisResult) -> list[str]:
    missing_policy = (
        "exclude studies with missing values"
        if result.missing_policy == "exclude"
        else "include missing values as a subgroup"
    )
    lines = [
        f"Grouping variable: {result.covariate_name}",
        f"Missing-value policy: {missing_policy}",
        (
            f"Studies: {result.included_count} analyzed; {result.missing_count} missing; "
            f"{result.excluded_count} excluded."
        ),
        "",
        "Subgroup results (as returned by RCMetaR):",
    ]
    return lines


def _missing_assignment_lines(plan: SubgroupPlan) -> tuple[str, ...]:
    changed_assignments = [
        row
        for row in plan.assignments
        if row.status == "excluded_missing"
        or row.value is None
        or row.value == ""
    ]
    if not changed_assignments:
        return ()
    decision = (
        "Excluded for missing subgroup values"
        if plan.missing_policy == "exclude"
        else "Assigned to Missing values subgroup"
    )
    return (
        "",
        f"{decision}: "
        + ", ".join(row.study_name for row in changed_assignments),
    )


def _between_test_lines(test: BetweenSubgroupTest) -> tuple[str, str]:
    if test.status == "available":
        return (
            "",
            "Between-subgroup test: "
            f"statistic {_format_number(test.statistic)}, "
            f"df {_format_number(test.degrees_of_freedom)}, "
            f"p {_format_number(test.p_value)}.",
        )
    return (
        "",
        "Between-subgroup test: Not calculated. "
        f"{test.reason or 'The backend did not return a test.'}",
    )


def _render_model_result(model: SubgroupModelResult) -> str:
    if model.status != "available":
        return (
            f"{model.label} (n={model.included_count}): Not available. "
            f"{model.reason or ''}"
        ).rstrip()
    return (
        f"{model.label} (n={model.included_count}): "
        f"estimate {_format_number(model.estimate)} "
        f"[{_format_number(model.lower_bound)}, {_format_number(model.upper_bound)}], "
        f"p {model.p_value_text or _format_number(model.p_value)}."
    )


def _render_heterogeneity(row: SubgroupHeterogeneity) -> str:
    if row.status != "available":
        return f"{row.label}: Not available. {row.reason or ''}".rstrip()
    return (
        f"{row.label}: Q={_format_number(row.q)} "
        f"(df={_format_number(row.degrees_of_freedom)}), "
        f"p={row.p_value_text or _format_number(row.p_value)}, "
        f"I²={_format_number(row.i_squared)}%."
    )


def _format_number(value: float | int | None) -> str:
    return "not available" if value is None else f"{value:.5g}"


def _model_row(line: str, prefix: str, binary: bool) -> tuple[tuple[float, str], ...]:
    stripped = line.strip()
    if not stripped.startswith(prefix):
        raise ValueError("subgroup summary row label does not match its frozen level")
    return _model_values(stripped[len(prefix):], binary)


def _model_values(tail: str, binary: bool) -> ModelValues:
    tokens = [match.group(0).strip() for match in _NUMBER.finditer(tail)]
    expected = 7 if binary else 5
    if len(tokens) != expected:
        raise ValueError(f"subgroup model row needs {expected} reported numeric values")
    values = tuple((_numeric_token(token), token) for token in tokens)
    _validate_model_row_count(values, binary)
    return values


def _validate_model_row_count(values: ModelValues, binary: bool) -> None:
    if not binary:
        return
    count = values[0][0]
    if count < 0 or int(count) != count:
        raise ValueError("subgroup study count must be a non-negative integer")


def _model_result(
    label: str, planned_count: int, values: tuple[tuple[float, str], ...], binary: bool
) -> SubgroupModelResult:
    if binary:
        returned_count = int(values[0][0])
        if returned_count != planned_count:
            raise ValueError(
                f"RCMetaR subgroup count for {label!r} is {returned_count}, "
                f"but the frozen plan includes {planned_count}"
            )
        offset = 1
    else:
        offset = 0
    return SubgroupModelResult(
        label=label,
        included_count=planned_count,
        status="available",
        reason=None,
        estimate=values[offset][0],
        lower_bound=values[offset + 1][0],
        upper_bound=values[offset + 2][0],
        standard_error=values[offset + 3][0],
        p_value=values[offset + 4][0],
        p_value_text=values[offset + 4][1],
        z_value=values[offset + 5][0] if binary else None,
    )


def _parse_heterogeneity(
    lines: Sequence[str], levels: Sequence[SubgroupLevel]
) -> tuple[SubgroupHeterogeneity, ...]:
    if not lines:
        return ()
    labels = _heterogeneity_labels(levels)
    found: dict[str, SubgroupHeterogeneity] = {}
    for line in lines:
        row = _heterogeneity_row(line, labels)
        if row is not None:
            found[row.label] = row
    return tuple(
        found.get(
            label,
            SubgroupHeterogeneity(
                label, "not_available", "RCMetaR returned no heterogeneity row for this level"
            ),
        )
        for _, label in labels
    )


def _heterogeneity_labels(
    levels: Sequence[SubgroupLevel],
) -> list[tuple[str, str]]:
    labels = [(f"Subgroup {level.backend_value}", level.label) for level in levels]
    labels.sort(key=lambda pair: len(pair[0]), reverse=True)
    labels.append(("Overall", "Overall"))
    return labels


def _heterogeneity_row(
    line: str, labels: Sequence[tuple[str, str]]
) -> SubgroupHeterogeneity | None:
    matched = next(
        ((prefix, label) for prefix, label in labels if _row_has_prefix(line, prefix)),
        None,
    )
    if matched is None:
        return None
    prefix, label = matched
    remainder = line.strip()[len(prefix):].strip()
    match = _HETEROGENEITY.match(remainder)
    if match is None:
        return None
    p_text = match.group("p").strip()
    return SubgroupHeterogeneity(
        label=label,
        status="available",
        reason=None,
        q=float(match.group("q")),
        degrees_of_freedom=int(match.group("df")),
        p_value=_numeric_token(p_text),
        p_value_text=p_text,
        i_squared=float(match.group("i2")),
    )


def _between_group_test_from_backend(value: Mapping[str, object]) -> BetweenSubgroupTest:
    fields = {"statistic", "degrees_of_freedom", "p_value"}
    if set(value) != fields:
        raise ValueError("backend between-subgroup test must return statistic, df, and p-value")
    statistic = _finite_number(value["statistic"], "between-subgroup statistic")
    degrees = _finite_number(value["degrees_of_freedom"], "between-subgroup degrees of freedom")
    p_value = _finite_number(value["p_value"], "between-subgroup p-value")
    if degrees <= 0 or not 0 <= p_value <= 1:
        raise ValueError("backend between-subgroup test returned invalid degrees of freedom or p-value")
    return BetweenSubgroupTest("available", None, statistic, degrees, p_value)


def _section_lines(summary: str, start_title: str, end_title: str | None) -> list[str]:
    lines = summary.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == start_title)
    except StopIteration:
        return []
    end = len(lines)
    if end_title is not None:
        end = next(
            (index for index in range(start + 1, len(lines)) if lines[index].strip() == end_title),
            len(lines),
        )
    return lines[start + 1:end]


def _row_has_prefix(line: str, prefix: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith(prefix):
        return False
    remainder = stripped[len(prefix):]
    if not remainder or not remainder[0].isspace():
        return False
    tail = remainder.lstrip()
    return bool(tail) and (tail[0].isdigit() or tail[0] in "+-<>")


def _numeric_token(value: str) -> float:
    text = value.strip().replace(" ", "")
    if text.startswith(("<", ">")):
        text = text[1:]
    try:
        number = float(text)
    except ValueError as error:
        raise ValueError("subgroup result contains an invalid numeric value") from error
    if not math.isfinite(number):
        raise ValueError("subgroup result contains a non-finite numeric value")
    return number


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _is_missing(value: object) -> bool:
    return value is None or value == ""


def _fresh_missing_code(used: set[str]) -> str:
    candidate = _MISSING_CODE
    suffix = 2
    while candidate in used:
        candidate = f"{_MISSING_CODE}_{suffix}"
        suffix += 1
    return candidate


def _assignment_from_mapping(value: object) -> SubgroupStudyAssignment:
    mapping = _mapping_with_fields(
        value,
        {"study_id", "study_name", "value", "status", "backend_value"},
        "subgroup study assignment has unknown or missing fields",
    )
    study_id, name = _assignment_identity(mapping["study_id"], mapping["study_name"])
    raw_value = _validated_scalar(mapping["value"], "subgroup value")
    status = _assignment_status(mapping["status"])
    backend_value = _assignment_backend_value(mapping["backend_value"])
    _validate_assignment_backend(status, backend_value)
    return SubgroupStudyAssignment(
        study_id, name, raw_value, status, backend_value
    )


def _mapping_with_fields(
    value: object, fields: set[str], message: str
) -> Mapping[str, object]:
    if not _is_string_mapping(value) or set(value) != fields:
        raise ValueError(message)
    return value


def _assignment_identity(study_id: object, name: object) -> tuple[int, str]:
    if type(study_id) is not int or study_id < 0:
        raise ValueError("subgroup study id must be a non-negative integer")
    if not isinstance(name, str) or not name:
        raise ValueError("subgroup study name must be non-empty text")
    return study_id, name


def _validated_scalar(value: object, label: str) -> Scalar:
    _scalar(value, label)
    return cast(Scalar, value)


def _assignment_status(value: object) -> StudyStatus:
    if value not in ("included", "excluded_missing"):
        raise ValueError("subgroup study status is invalid")
    return cast(StudyStatus, value)


def _assignment_backend_value(value: object) -> str | None:
    if value is not None and not isinstance(value, str):
        raise ValueError("subgroup backend value must be text or missing")
    return value


def _validate_assignment_backend(status: StudyStatus, backend_value: str | None) -> None:
    if (status == "included") != (backend_value is not None):
        raise ValueError("subgroup included status and backend value disagree")


def _level_from_mapping(value: object) -> SubgroupLevel:
    mapping = _mapping_with_fields(
        value,
        {"value", "label", "backend_value", "study_ids", "is_missing_category"},
        "subgroup level has unknown or missing fields",
    )
    raw_value = _validated_scalar(mapping["value"], "subgroup level value")
    label, code = _level_identity(mapping["label"], mapping["backend_value"])
    ids = _level_study_ids(mapping["study_ids"])
    missing = _level_missing_flag(mapping["is_missing_category"], raw_value)
    return SubgroupLevel(raw_value, label, code, ids, missing)


def _level_identity(label: object, code: object) -> tuple[str, str]:
    if not isinstance(label, str) or not label or not isinstance(code, str) or not code:
        raise ValueError("subgroup level label and backend value must be non-empty text")
    return label, code


def _level_study_ids(value: object) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple)) or not value or any(type(item) is not int for item in value):
        raise ValueError("subgroup level must contain study identities")
    return tuple(cast(int, study_id) for study_id in value)


def _level_missing_flag(value: object, raw_value: Scalar) -> bool:
    if type(value) is not bool:
        raise ValueError("subgroup missing-category flag must be boolean")
    if value != (raw_value is None):
        raise ValueError("subgroup missing-category value is inconsistent")
    return value


def _validate_plan_shape(plan: SubgroupPlan) -> None:
    _validate_plan_identities(plan)
    backend_members = _assigned_backend_members(plan)
    _validate_missing_level_policy(plan)
    _validate_level_membership(plan.levels, backend_members)


def _validate_plan_identities(plan: SubgroupPlan) -> None:
    _validate_unique_assignment_ids(plan.assignments)
    _validate_unique_level_codes(plan.levels)
    _validate_level_assignment_ids(plan.assignments, plan.levels)


def _validate_unique_assignment_ids(assignments: Sequence[SubgroupStudyAssignment]) -> None:
    if not assignments or len({row.study_id for row in assignments}) != len(assignments):
        raise ValueError("subgroup plan assignments must have unique study identities")


def _validate_unique_level_codes(levels: Sequence[SubgroupLevel]) -> None:
    if len(levels) < 2 or len({level.backend_value for level in levels}) != len(levels):
        raise ValueError("subgroup plan needs at least two distinct levels")


def _validate_level_assignment_ids(
    assignments: Sequence[SubgroupStudyAssignment], levels: Sequence[SubgroupLevel]
) -> None:
    assignment_ids = {row.study_id for row in assignments if row.status == "included"}
    level_ids = [study_id for level in levels for study_id in level.study_ids]
    if len(level_ids) != len(set(level_ids)) or set(level_ids) != assignment_ids:
        raise ValueError("subgroup plan level membership does not match included studies")


def _assigned_backend_members(plan: SubgroupPlan) -> dict[str, set[int]]:
    missing_code = next(
        (level.backend_value for level in plan.levels if level.is_missing_category),
        None,
    )
    backend_members: dict[str, set[int]] = {}
    for assignment in plan.assignments:
        code = _validated_assignment_code(plan, assignment, missing_code)
        if code is not None:
            backend_members.setdefault(code, set()).add(assignment.study_id)
    return backend_members


def _validated_assignment_code(
    plan: SubgroupPlan,
    assignment: SubgroupStudyAssignment,
    missing_code: str | None,
) -> str | None:
    missing = _is_missing(assignment.value)
    if plan.missing_policy == "exclude" and missing:
        if assignment.status != "excluded_missing":
            raise ValueError("subgroup plan does not exclude every missing value")
        return None
    if assignment.status != "included":
        raise ValueError("subgroup plan excludes a non-missing covariate value")
    expected_code = missing_code if missing else str(assignment.value)
    if expected_code is None or assignment.backend_value != expected_code:
        raise ValueError("subgroup assignment backend value does not match its level")
    return expected_code


def _validate_missing_level_policy(plan: SubgroupPlan) -> None:
    missing_levels = [level for level in plan.levels if level.is_missing_category]
    if plan.missing_policy == "exclude" and missing_levels:
        raise ValueError("excluded missing values cannot also form a subgroup level")
    if len(missing_levels) > 1:
        raise ValueError("subgroup plan can contain only one missing-value category")


def _validate_level_membership(
    levels: Sequence[SubgroupLevel], backend_members: Mapping[str, set[int]]
) -> None:
    for level in levels:
        if backend_members.get(level.backend_value) != set(level.study_ids):
            raise ValueError("subgroup level membership does not match assigned values")


def _scalar(value: object, label: str) -> None:
    if value is None or isinstance(value, (str, int, bool)):
        return
    if isinstance(value, float) and math.isfinite(value):
        return
    raise ValueError(f"{label} must be a finite JSON scalar")
