# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Frozen subgroup input preparation and conservative result parsing."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
import math
import re
from typing import Literal, TypeAlias, TypeGuard, cast

from rc_metastudio.analysis_adapter import AnalysisRequest, make_analysis_request
from rc_metastudio.analysis_results import AnalysisResult
from rc_metastudio.analysis_snapshot import BinaryInputSnapshot
from rc_metastudio.continuous_analysis_snapshot import ContinuousInputSnapshot
from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot


MissingCovariatePolicy = Literal["exclude", "missing_category"]
SubgroupFamily = Literal["binary", "continuous"]
StudyStatus = Literal["included", "excluded_missing"]
ResultStatus = Literal["available", "not_available"]
Scalar: TypeAlias = str | int | float | bool | None


def _is_string_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping) and all(isinstance(key, str) for key in value)

_MISSING_CODE = "__RCMS_MISSING__"
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
        if not _is_string_mapping(value):
            raise ValueError("subgroup plan must be an object")
        fields = {
            "version", "family", "metric", "covariate_name", "missing_policy",
            "assignments", "levels",
        }
        if set(value) != fields:
            raise ValueError("subgroup plan has unknown or missing fields")
        if type(value["version"]) is not int or value["version"] != 1:
            raise ValueError("unsupported subgroup plan version")
        family = value["family"]
        policy = value["missing_policy"]
        if family not in ("binary", "continuous"):
            raise ValueError("subgroup plan family is unsupported")
        if policy not in ("exclude", "missing_category"):
            raise ValueError("subgroup plan needs an explicit missing-value policy")
        if not isinstance(value["metric"], str) or not value["metric"]:
            raise ValueError("subgroup plan metric must be non-empty text")
        if not isinstance(value["covariate_name"], str) or not value["covariate_name"]:
            raise ValueError("subgroup plan covariate name must be non-empty text")
        raw_assignments = value["assignments"]
        raw_levels = value["levels"]
        if not isinstance(raw_assignments, (list, tuple)) or not isinstance(raw_levels, (list, tuple)):
            raise ValueError("subgroup plan assignments and levels must be lists")
        plan = cls(
            1,
            cast(SubgroupFamily, family),
            value["metric"],
            value["covariate_name"],
            cast(MissingCovariatePolicy, policy),
            tuple(_assignment_from_mapping(row) for row in raw_assignments),
            tuple(_level_from_mapping(row) for row in raw_levels),
        )
        _validate_plan_shape(plan)
        return plan


Snapshot: TypeAlias = (
    BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot
)


def create_subgroup_plan(
    snapshot: Snapshot,
    covariate_name: str,
    *,
    missing_policy: MissingCovariatePolicy,
) -> SubgroupPlan:
    """Freeze factor levels and an explicit decision for every missing value."""
    if isinstance(snapshot, DiagnosticInputSnapshot):
        raise ValueError(
            "the pinned RCMetaR method matrix does not support diagnostic subgroup analyses"
        )
    if not isinstance(snapshot, (BinaryInputSnapshot, ContinuousInputSnapshot)):
        raise TypeError("subgroup analysis requires a frozen binary or continuous input")
    family: SubgroupFamily = "binary" if isinstance(snapshot, BinaryInputSnapshot) else "continuous"
    if missing_policy not in ("exclude", "missing_category"):
        raise ValueError("choose whether studies with missing covariates are excluded or grouped")
    if not isinstance(covariate_name, str) or not covariate_name:
        raise ValueError("select a covariate for subgroup analysis")
    covariates = snapshot.covariates
    covariate = next((row for row in covariates if row.name == covariate_name), None)
    if covariate is None:
        raise ValueError(f"subgroup covariate {covariate_name!r} is not in the frozen input")
    if covariate.data_type != "factor":
        raise ValueError("subgroup analysis requires a categorical covariate")
    if len(covariate.values) != len(snapshot.studies):
        raise ValueError("subgroup covariate values do not match frozen study rows")

    if isinstance(snapshot, BinaryInputSnapshot):
        study_ids = tuple(study.id for study in snapshot.studies)
    else:
        study_ids = tuple(study.study_id for study in snapshot.studies)
    study_names = tuple(study.name for study in snapshot.studies)
    known_codes = {str(value) for value in covariate.values if not _is_missing(value)}
    missing_code = _fresh_missing_code(known_codes)
    assignments: list[SubgroupStudyAssignment] = []
    level_values: dict[str, Scalar] = {}
    level_ids: dict[str, list[int]] = {}
    missing_ids: list[int] = []

    for study_id, study_name, value in zip(study_ids, study_names, covariate.values, strict=True):
        if _is_missing(value):
            if missing_policy == "exclude":
                assignments.append(
                    SubgroupStudyAssignment(study_id, study_name, value, "excluded_missing", None)
                )
                continue
            backend_value = missing_code
            missing_ids.append(study_id)
        else:
            backend_value = str(value)
            previous = level_values.get(backend_value, value)
            if previous != value or type(previous) is not type(value):
                raise ValueError(
                    "categorical covariate values collapse to the same RCMetaR label; "
                    "rename or recode those levels before subgroup analysis"
                )
            level_values[backend_value] = value
        assignments.append(
            SubgroupStudyAssignment(study_id, study_name, value, "included", backend_value)
        )
        level_ids.setdefault(backend_value, []).append(study_id)

    levels = [
        SubgroupLevel(value, code, code, tuple(ids))
        for code, ids in level_ids.items()
        if code != missing_code
        for value in (level_values[code],)
    ]
    if missing_ids:
        levels.append(
            SubgroupLevel(None, "Missing values", missing_code, tuple(missing_ids), True)
        )
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


def prepare_subgroup_snapshot(snapshot: Snapshot, plan: SubgroupPlan) -> Snapshot:
    """Apply the saved missing policy while keeping all frozen rows aligned."""
    expected = create_subgroup_plan(
        snapshot, plan.covariate_name, missing_policy=plan.missing_policy
    )
    if expected != plan:
        raise ValueError("subgroup plan does not match the frozen analysis input")
    if plan.family == "binary" and isinstance(snapshot, BinaryInputSnapshot):
        included_ids = {row.study_id for row in plan.assignments if row.status == "included"}
        rows = tuple(study for study in snapshot.studies if study.id in included_ids)
        assignments = {row.study_id: row for row in plan.assignments}
        covariates = tuple(
            replace(
                covariate,
                values=tuple(
                    assignments[study.id].backend_value
                    if covariate.name == plan.covariate_name
                    else covariate.values[index]
                    for index, study in enumerate(snapshot.studies)
                    if study.id in included_ids
                ),
            )
            for covariate in snapshot.covariates
        )
        return replace(snapshot, studies=rows, covariates=covariates)
    if plan.family == "continuous" and isinstance(snapshot, ContinuousInputSnapshot):
        included_ids = {row.study_id for row in plan.assignments if row.status == "included"}
        rows = tuple(study for study in snapshot.studies if study.study_id in included_ids)
        assignments = {row.study_id: row for row in plan.assignments}
        covariates = tuple(
            replace(
                covariate,
                values=tuple(
                    assignments[study.study_id].backend_value
                    if covariate.name == plan.covariate_name
                    else covariate.values[index]
                    for index, study in enumerate(snapshot.studies)
                    if study.study_id in included_ids
                ),
            )
            for covariate in snapshot.covariates
        )
        return replace(snapshot, studies=rows, covariates=covariates)
    raise ValueError("subgroup plan family does not match its frozen input")


def create_subgroup_request(
    snapshot: Snapshot,
    plan: SubgroupPlan,
    *,
    method: str,
    parameters: Mapping[str, object],
) -> AnalysisRequest:
    """Build a subgroup request from the frozen family and selected moderator."""
    if isinstance(snapshot, DiagnosticInputSnapshot):
        raise ValueError(
            "the pinned RCMetaR method matrix does not support diagnostic subgroup analyses"
        )
    if plan.family != ("binary" if isinstance(snapshot, BinaryInputSnapshot) else "continuous"):
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
    binary = plan.family == "binary"
    model_lines = _section_lines(summary, "Model Results", "Heterogeneity")
    heterogeneity_lines = _section_lines(summary, "Heterogeneity", None)
    row_prefixes = [(level, f"Subgroup {level.backend_value}") for level in plan.levels]
    row_prefixes.sort(key=lambda pair: len(pair[1]), reverse=True)
    model_rows: dict[str, tuple[tuple[float, str], ...] | None] = {}
    for level, prefix in row_prefixes:
        line = next((line for line in model_lines if _row_has_prefix(line, prefix)), None)
        model_rows[level.backend_value] = None if line is None else _model_row(line, prefix, binary)
    overall_line = next((line for line in model_lines if _row_has_prefix(line, "Overall")), None)
    overall_values = None if overall_line is None else _model_row(overall_line, "Overall", binary)

    results: list[SubgroupModelResult] = []
    for level in plan.levels:
        values = model_rows[level.backend_value]
        if values is None:
            results.append(
                SubgroupModelResult(
                    label=level.label,
                    included_count=level.included_count,
                    status="not_available",
                    reason="RCMetaR returned no model row for this subgroup level",
                )
            )
            continue
        results.append(_model_result(level.label, level.included_count, values, binary))
    overall_count = plan.included_count
    overall = (
        SubgroupModelResult(
            "Overall", overall_count, "not_available", "RCMetaR returned no overall model row"
        )
        if overall_values is None
        else _model_result("Overall", overall_count, overall_values, binary)
    )
    heterogeneity = _parse_heterogeneity(heterogeneity_lines, plan.levels)
    between = (
        _between_group_test_from_backend(between_subgroup_test)
        if between_subgroup_test is not None
        else BetweenSubgroupTest(
            "not_calculated",
            "RCMetaR's subgroup result provides within-subgroup heterogeneity only; "
            "it returned no between-subgroup test.",
        )
    )
    return SubgroupAnalysisResult(
        covariate_name=plan.covariate_name,
        missing_policy=plan.missing_policy,
        included_count=plan.included_count,
        missing_count=plan.missing_count,
        excluded_count=plan.excluded_count,
        levels=tuple(results),
        overall=overall,
        heterogeneity=heterogeneity,
        between_subgroup_test=between,
        figure_status="available" if figure_available else "not_available",
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
    if (
        result.covariate_name != plan.covariate_name
        or result.missing_policy != plan.missing_policy
        or result.included_count != plan.included_count
        or result.missing_count != plan.missing_count
        or result.excluded_count != plan.excluded_count
    ):
        raise ValueError("subgroup result does not match its frozen inclusion plan")
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
    changed_assignments = [
        row
        for row in plan.assignments
        if row.status == "excluded_missing"
        or row.value is None
        or row.value == ""
    ]
    if changed_assignments:
        decision = (
            "Excluded for missing subgroup values"
            if plan.missing_policy == "exclude"
            else "Assigned to Missing values subgroup"
        )
        lines.extend(
            (
                "",
                f"{decision}: "
                + ", ".join(row.study_name for row in changed_assignments),
            )
        )
    for model in (*result.levels, result.overall):
        lines.append(_render_model_result(model))
    if result.heterogeneity:
        lines.extend(("", "Within-subgroup heterogeneity:"))
        lines.extend(_render_heterogeneity(row) for row in result.heterogeneity)
    test = result.between_subgroup_test
    if test.status == "available":
        lines.extend(
            (
                "",
                "Between-subgroup test: "
                f"statistic {_format_number(test.statistic)}, "
                f"df {_format_number(test.degrees_of_freedom)}, "
                f"p {_format_number(test.p_value)}.",
            )
        )
    else:
        lines.extend(
            (
                "",
                "Between-subgroup test: Not calculated. "
                f"{test.reason or 'The backend did not return a test.'}",
            )
        )
    lines.append(
        "Within-subgroup p-values do not test differences between subgroup levels."
    )
    return "\n".join(lines)


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
    tail = stripped[len(prefix):]
    tokens = [match.group(0).strip() for match in _NUMBER.finditer(tail)]
    expected = 7 if binary else 5
    if len(tokens) != expected:
        raise ValueError(f"subgroup model row needs {expected} reported numeric values")
    values = tuple((_numeric_token(token), token) for token in tokens)
    if binary:
        count = values[0][0]
        if count < 0 or int(count) != count:
            raise ValueError("subgroup study count must be a non-negative integer")
    return values


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
    labels = [(f"Subgroup {level.backend_value}", level.label) for level in levels]
    labels.sort(key=lambda pair: len(pair[0]), reverse=True)
    labels.append(("Overall", "Overall"))
    found: dict[str, SubgroupHeterogeneity] = {}
    for line in lines:
        matched = next(
            ((prefix, label) for prefix, label in labels if _row_has_prefix(line, prefix)),
            None,
        )
        if matched is None:
            continue
        prefix, label = matched
        stripped = line.strip()
        remainder = stripped[len(prefix):].strip()
        match = _HETEROGENEITY.match(remainder)
        if match is None:
            continue
        p_text = match.group("p").strip()
        found[label] = SubgroupHeterogeneity(
            label=label,
            status="available",
            reason=None,
            q=float(match.group("q")),
            degrees_of_freedom=int(match.group("df")),
            p_value=_numeric_token(p_text),
            p_value_text=p_text,
            i_squared=float(match.group("i2")),
        )
    return tuple(
        found.get(
            label,
            SubgroupHeterogeneity(
                label, "not_available", "RCMetaR returned no heterogeneity row for this level"
            ),
        )
        for _, label in labels
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
    if not _is_string_mapping(value) or set(value) != {
        "study_id", "study_name", "value", "status", "backend_value"
    }:
        raise ValueError("subgroup study assignment has unknown or missing fields")
    study_id = value["study_id"]
    name = value["study_name"]
    raw_value = value["value"]
    status = value["status"]
    backend_value = value["backend_value"]
    if type(study_id) is not int or study_id < 0:
        raise ValueError("subgroup study id must be a non-negative integer")
    if not isinstance(name, str) or not name:
        raise ValueError("subgroup study name must be non-empty text")
    _scalar(raw_value, "subgroup value")
    if status not in ("included", "excluded_missing"):
        raise ValueError("subgroup study status is invalid")
    if backend_value is not None and not isinstance(backend_value, str):
        raise ValueError("subgroup backend value must be text or missing")
    if (status == "included") != (backend_value is not None):
        raise ValueError("subgroup included status and backend value disagree")
    return SubgroupStudyAssignment(
        study_id, name, cast(Scalar, raw_value), cast(StudyStatus, status), backend_value
    )


def _level_from_mapping(value: object) -> SubgroupLevel:
    if not _is_string_mapping(value) or set(value) != {
        "value", "label", "backend_value", "study_ids", "is_missing_category"
    }:
        raise ValueError("subgroup level has unknown or missing fields")
    raw_value = value["value"]
    _scalar(raw_value, "subgroup level value")
    label = value["label"]
    code = value["backend_value"]
    ids = value["study_ids"]
    missing = value["is_missing_category"]
    if not isinstance(label, str) or not label or not isinstance(code, str) or not code:
        raise ValueError("subgroup level label and backend value must be non-empty text")
    if not isinstance(ids, (list, tuple)) or not ids or any(type(item) is not int for item in ids):
        raise ValueError("subgroup level must contain study identities")
    if type(missing) is not bool:
        raise ValueError("subgroup missing-category flag must be boolean")
    if missing != (raw_value is None):
        raise ValueError("subgroup missing-category value is inconsistent")
    return SubgroupLevel(
        cast(Scalar, raw_value),
        label,
        code,
        tuple(cast(int, study_id) for study_id in ids),
        missing,
    )


def _validate_plan_shape(plan: SubgroupPlan) -> None:
    if not plan.assignments or len({row.study_id for row in plan.assignments}) != len(plan.assignments):
        raise ValueError("subgroup plan assignments must have unique study identities")
    if len(plan.levels) < 2 or len({level.backend_value for level in plan.levels}) != len(plan.levels):
        raise ValueError("subgroup plan needs at least two distinct levels")
    assignment_ids = {row.study_id for row in plan.assignments if row.status == "included"}
    level_ids = [study_id for level in plan.levels for study_id in level.study_ids]
    if len(level_ids) != len(set(level_ids)) or set(level_ids) != assignment_ids:
        raise ValueError("subgroup plan level membership does not match included studies")
    backend_members: dict[str, set[int]] = {}
    for assignment in plan.assignments:
        missing = _is_missing(assignment.value)
        if plan.missing_policy == "exclude" and missing:
            if assignment.status != "excluded_missing":
                raise ValueError("subgroup plan does not exclude every missing value")
        elif assignment.status != "included":
            raise ValueError("subgroup plan excludes a non-missing covariate value")
        if assignment.status == "included":
            expected_code = (
                next((level.backend_value for level in plan.levels if level.is_missing_category), None)
                if missing
                else str(assignment.value)
            )
            if expected_code is None or assignment.backend_value != expected_code:
                raise ValueError("subgroup assignment backend value does not match its level")
            backend_members.setdefault(expected_code, set()).add(assignment.study_id)
    missing_levels = [level for level in plan.levels if level.is_missing_category]
    if plan.missing_policy == "exclude" and missing_levels:
        raise ValueError("excluded missing values cannot also form a subgroup level")
    if len(missing_levels) > 1:
        raise ValueError("subgroup plan can contain only one missing-value category")
    for level in plan.levels:
        if backend_members.get(level.backend_value) != set(level.study_ids):
            raise ValueError("subgroup level membership does not match assigned values")


def _scalar(value: object, label: str) -> None:
    if value is None or isinstance(value, (str, int, bool)):
        return
    if isinstance(value, float) and math.isfinite(value):
        return
    raise ValueError(f"{label} must be a finite JSON scalar")
