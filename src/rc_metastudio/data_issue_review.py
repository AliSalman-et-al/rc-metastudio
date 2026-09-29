# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only review of studies in the currently selected analysis context."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Sequence
from typing import Literal, Protocol, SupportsFloat, cast
import uuid

from rc_metastudio import analysis_dataset, meta_globals
from rc_metastudio.workspace_column_identity import WorkspaceColumnIdentity

ReviewStatus = Literal["included", "excluded", "missing", "invalid"]
IssueKind = Literal["missing-required", "invalid-value", "exclusion-review"]
InputSource = Literal["raw", "entered-effect"]


@dataclass(frozen=True, slots=True)
class StudyCellTarget:
    """Stable address for returning a review issue to its source cell."""

    study_id: int
    study_identity: str
    outcome_identity: str | None
    follow_up_identity: str | None
    group_identity: str | None
    field_identity: WorkspaceColumnIdentity
    editor_id: str | None = None


@dataclass(frozen=True, slots=True)
class DataIssue:
    id: str
    study_id: int
    study_identity: str
    study_name: str
    kind: IssueKind
    field: str
    value: object
    problem: str
    correction_action: str
    target: StudyCellTarget | None
    blocking: bool = True


@dataclass(frozen=True, slots=True)
class MethodExclusionDecision:
    """An explicit, run-local decision; it never changes dataset inclusion."""

    study_id: int
    method_id: str
    reason: str
    permitted_by_method: bool
    confirmed: bool

    def __post_init__(self) -> None:
        if not self.method_id.strip() or not self.reason.strip():
            raise ValueError("method exclusions need a method and a reason")

    def to_mapping(self) -> dict[str, object]:
        return {
            "study_id": self.study_id,
            "method_id": self.method_id,
            "reason": self.reason,
            "permitted_by_method": self.permitted_by_method,
            "confirmed": self.confirmed,
        }


@dataclass(frozen=True, slots=True)
class StudyReview:
    study_id: int
    study_identity: str
    name: str
    status: ReviewStatus
    reasons: tuple[str, ...]
    issues: tuple[DataIssue, ...]
    method_exclusion: MethodExclusionDecision | None = None


@dataclass(frozen=True, slots=True)
class DataIssueReview:
    outcome: str | None
    time_point: str | None
    groups: tuple[str, ...]
    method_id: str | None
    metric: str | None
    input_source: InputSource
    studies: tuple[StudyReview, ...]

    @property
    def issues(self) -> tuple[DataIssue, ...]:
        return tuple(issue for study in self.studies for issue in study.issues)

    @property
    def blocking_issues(self) -> tuple[DataIssue, ...]:
        return tuple(
            issue
            for study in self.studies
            if study.status != "excluded"
            for issue in study.issues
            if issue.blocking
        )

    @property
    def is_ready(self) -> bool:
        return not self.blocking_issues and any(
            study.status == "included" for study in self.studies
        )

    def for_study(self, study_id: int) -> StudyReview:
        return next(study for study in self.studies if study.study_id == study_id)

    @property
    def confirmed_method_exclusions(self) -> tuple[dict[str, object], ...]:
        return tuple(
            study.method_exclusion.to_mapping()
            for study in self.studies
            if study.method_exclusion is not None
            and study.method_exclusion.permitted_by_method
            and study.method_exclusion.confirmed
        )


@dataclass(frozen=True, slots=True)
class _Field:
    key: str
    label: str
    column_kind: str
    column_index: int
    validator: Literal["count", "total", "number", "nonnegative-number"]
    identity: WorkspaceColumnIdentity | None = None
    editor_id: str | None = None


class _AnalysisContextModel(Protocol):
    dataset: analysis_dataset.Dataset
    current_outcome_name: str | None
    current_effect: str | None

    def get_current_follow_up_name(self) -> str | None: ...
    def get_current_groups(self) -> Sequence[str]: ...


@dataclass(frozen=True, slots=True)
class _ReviewContext:
    dataset: analysis_dataset.Dataset
    outcome_name: str | None
    time_point: str | None
    groups: tuple[str, ...]
    method_id: str | None
    outcome_identity: str | None
    follow_up_identity: str | None
    data_type: str | None
    subtype: str | None
    metric: str | None
    input_source: InputSource
    fields: tuple[_Field, ...]
    confidence_multiplier: object


_RAW_FIELDS = {
    meta_globals.BINARY: (
        _Field("events", "events", "raw", 0, "count"),
        _Field("total", "total", "raw", 1, "total"),
    ),
    meta_globals.CONTINUOUS: (
        _Field("n", "N", "raw", 0, "total"),
        _Field("mean", "mean", "raw", 1, "number"),
        _Field("sd", "SD", "raw", 2, "nonnegative-number"),
    ),
    meta_globals.DIAGNOSTIC: (
        _Field("tp", "TP", "raw", 0, "count"),
        _Field("fn", "FN", "raw", 1, "count"),
        _Field("fp", "FP", "raw", 2, "count"),
        _Field("tn", "TN", "raw", 3, "count"),
    ),
}


def review_analysis_data(
    model: object,
    *,
    method_id: str | None = None,
    required_covariates: Sequence[object] = (),
    input_source: InputSource | None = None,
    method_exclusions: Sequence[MethodExclusionDecision] = (),
) -> DataIssueReview:
    """Describe selected studies and their required inputs without mutating data.

    ``method_exclusions`` contains only decisions made for this selected method.
    A study is excluded by a method only when its reason is permitted and the
    user explicitly confirmed it. Global dataset exclusions remain separate.
    """
    if getattr(model, "dataset", None) is None:
        raise TypeError("analysis review requires a model with a dataset")
    context_model = cast(_AnalysisContextModel, model)
    context = _review_context(context_model, method_id, input_source)
    by_study = _method_decisions(method_id, method_exclusions)
    unknown_exclusions = set(by_study) - {
        int(study.id) for study in context.dataset.studies
    }
    if unknown_exclusions:
        raise ValueError("method exclusions reference a study that is no longer present")
    result = tuple(
        _review_study(
            study,
            context,
            required_covariates,
            by_study.get(int(study.id)),
        )
        for study in context.dataset.studies
        if _is_reviewable(
            study, context.outcome_name, context.time_point, context.groups
        )
    )
    return DataIssueReview(
        context.outcome_name,
        context.time_point,
        context.groups,
        method_id,
        context.metric,
        context.input_source,
        result,
    )


def _review_context(
    model: _AnalysisContextModel,
    method_id: str | None,
    input_source: InputSource | None,
) -> _ReviewContext:
    dataset = model.dataset
    outcome_name = model.current_outcome_name
    time_point = model.get_current_follow_up_name()
    groups = tuple(model.get_current_groups())
    outcome = dataset.get_outcome_obj(outcome_name) if outcome_name else None
    subtype = getattr(outcome, "sub_type", None)
    source = input_source or (
        "entered-effect" if subtype == "generic_effect" else "raw"
    )
    data_type = getattr(outcome, "data_type", None)
    metric = model.current_effect
    return _ReviewContext(
        dataset=dataset,
        outcome_name=outcome_name,
        time_point=time_point,
        groups=groups,
        method_id=method_id,
        outcome_identity=getattr(outcome, "stable_id", None),
        follow_up_identity=_follow_up_identity(dataset, outcome_name, time_point),
        data_type=data_type,
        subtype=subtype,
        metric=metric,
        input_source=source,
        fields=_fields_for_context(data_type, subtype, metric, groups, source),
        confidence_multiplier=getattr(model, "confidence_multiplier", None),
    )


def _follow_up_identity(
    dataset: analysis_dataset.Dataset,
    outcome_name: str | None,
    time_point: str | None,
) -> str | None:
    if outcome_name is None or time_point is None:
        return None
    return dataset.follow_up_stable_ids_by_outcome.get(outcome_name, {}).get(time_point)


def _review_study(
    study: analysis_dataset.Study,
    context: _ReviewContext,
    required_covariates: Sequence[object],
    decision: MethodExclusionDecision | None,
) -> StudyReview:
    identity = f"study:{study.id}"
    issues = list(_study_name_issues(study, context, identity))
    if context.outcome_name and context.time_point:
        issues.extend(_input_issues(study, identity, context))
    issues.extend(_covariate_issues(study, context, identity, required_covariates))
    if bool(getattr(study, "manually_excluded", False)):
        decision = None
    status, reasons = _study_status(study, issues, decision)
    if decision is not None and not _is_confirmed_exclusion(decision):
        reason = _exclusion_review_reason(decision)
        issues.append(
            _issue(
                study,
                identity,
                kind="exclusion-review",
                field="Study exclusion",
                value=decision.reason,
                problem=reason,
                target=None,
                method_id=context.method_id,
            )
        )
        reasons.append(reason)
        if status == "included":
            status = "invalid"
    return StudyReview(
        int(study.id), identity, str(study.name), status, tuple(reasons), tuple(issues), decision
    )


def _study_name_issues(
    study: analysis_dataset.Study, context: _ReviewContext, identity: str
) -> tuple[DataIssue, ...]:
    if str(study.name).strip():
        return ()
    field = _Field(
        "study-name",
        "Study name",
        "fixed",
        1,
        "number",
        WorkspaceColumnIdentity("fixed", ("study-name",)),
    )
    return (
        _issue_for_field(
            study,
            identity,
            context.outcome_identity,
            context.follow_up_identity,
            None,
            field,
            study.name,
            "missing-required",
            "A study name is required to identify this row in the analysis.",
        ),
    )


def _study_status(
    study: analysis_dataset.Study,
    issues: Sequence[DataIssue],
    decision: MethodExclusionDecision | None,
) -> tuple[ReviewStatus, list[str]]:
    if decision is not None and _is_confirmed_exclusion(decision):
        return "excluded", [f"Excluded from {decision.method_id}: {decision.reason}"]
    if bool(getattr(study, "manually_excluded", False)):
        return "excluded", ["Manually excluded from the working dataset."]
    if issues:
        return _issues_status(issues)
    if not bool(getattr(study, "include", True)):
        return "excluded", ["Not included in the working dataset."]
    return "included", ["Included in the selected analysis context."]


def _issues_status(issues: Sequence[DataIssue]) -> tuple[ReviewStatus, list[str]]:
    has_invalid_value = any(issue.kind == "invalid-value" for issue in issues)
    status: ReviewStatus = "invalid" if has_invalid_value else "missing"
    return status, [issue.problem for issue in issues]


def _is_confirmed_exclusion(decision: MethodExclusionDecision) -> bool:
    return decision.permitted_by_method and decision.confirmed


def _exclusion_review_reason(decision: MethodExclusionDecision) -> str:
    if not decision.permitted_by_method:
        return "This method does not permit the requested study exclusion."
    return "Confirm this method-specific exclusion before running."


def _method_decisions(
    method_id: str | None,
    decisions: Sequence[MethodExclusionDecision],
) -> dict[int, MethodExclusionDecision]:
    if method_id is None:
        return {}
    matching = {
        item.study_id: item
        for item in decisions
        if item.method_id == method_id
    }
    if len(matching) != sum(item.method_id == method_id for item in decisions):
        raise ValueError("a method can have only one exclusion decision per study")
    return matching


def _is_reviewable(study, outcome_name, time_point, groups) -> bool:
    if _has_dataset_selection(study) or _has_study_identity(study):
        return True
    if _has_covariate_data(study):
        return True
    if outcome_name is None or time_point is None:
        return False
    return _has_raw_context_data(study, outcome_name, time_point, groups)


def _has_dataset_selection(study) -> bool:
    return bool(getattr(study, "include", False)) or bool(
        getattr(study, "manually_excluded", False)
    )


def _has_study_identity(study) -> bool:
    return bool(str(getattr(study, "name", "")).strip() or getattr(study, "year", None))


def _has_covariate_data(study) -> bool:
    return any(value not in (None, "") for value in study.covariate_values.values())


def _has_raw_context_data(study, outcome_name, time_point, groups) -> bool:
    try:
        unit = study.get_analysis_unit(outcome_name, time_point)
    except KeyError:
        return False
    if any(
        value not in (None, "")
        for group_name in groups
        if group_name in unit.groups
        for value in unit.get_raw_data_for_group(group_name)
    ):
        return True
    return False


def _fields_for_context(data_type, subtype, metric, groups, input_source):
    if subtype == "generic_effect" or input_source == "entered-effect":
        return _entered_effect_fields(data_type, subtype)
    return _raw_context_fields(data_type, subtype, metric, groups)


def _entered_effect_fields(data_type, subtype) -> tuple[_Field, _Field]:
    outcome_type = meta_globals.TYPE_TO_STR_DICT.get(data_type, "none")
    outcome_subtype = subtype or "none"
    editor_id = "effect-editor" if subtype != "generic_effect" else None
    return (
        _Field(
            "estimate", "Effect estimate", "outcome", 0, "number",
            WorkspaceColumnIdentity("outcome", (outcome_type, outcome_subtype, 0)),
            editor_id,
        ),
        _Field(
            "standard_error", "Standard error", "outcome", 1, "nonnegative-number",
            WorkspaceColumnIdentity("outcome", (outcome_type, outcome_subtype, 1)),
            editor_id,
        ),
    )


def _raw_context_fields(data_type, subtype, metric, groups) -> tuple[_Field, ...]:
    all_fields = _RAW_FIELDS.get(data_type, ())
    if data_type in (meta_globals.BINARY, meta_globals.CONTINUOUS) and metric in meta_globals.ONE_ARM_METRICS:
        groups = groups[:1]
    if data_type == meta_globals.DIAGNOSTIC:
        groups = groups[:1]
    return tuple(
        _Field(
            f"{group_index}.{field.key}",
            f"{groups[group_index]} {field.label}".strip(),
            field.column_kind,
            group_index * len(all_fields) + field.column_index,
            field.validator,
            WorkspaceColumnIdentity(
                "raw",
                (
                    meta_globals.TYPE_TO_STR_DICT.get(data_type, "none"),
                    subtype or "none",
                    group_index * len(all_fields) + field.column_index,
                ),
            ),
        )
        for group_index in range(len(groups))
        for field in all_fields
    )


def _input_issues(
    study,
    study_identity,
    context: _ReviewContext,
):
    outcome_name = context.outcome_name
    time_point = context.time_point
    assert outcome_name is not None and time_point is not None
    try:
        unit = study.get_analysis_unit(outcome_name, time_point)
    except (KeyError, ValueError):
        unit = None
    if unit is None:
        return _missing_input_issues(study, study_identity, context)
    values = _input_values(unit, context)
    return tuple(
        issue
        for field in context.fields
        if (issue := _field_input_issue(study, study_identity, unit, context, field, values))
        is not None
    )


def _missing_input_issues(study, study_identity, context: _ReviewContext):
    return tuple(
        _issue_for_field(
            study,
            study_identity,
            context.outcome_identity,
            context.follow_up_identity,
            None,
            field,
            None,
            "missing-required",
            f"Required {field.label} is missing.",
        )
        for field in context.fields
    )


def _input_values(unit, context: _ReviewContext) -> tuple[object, ...]:
    if context.input_source == "entered-effect" or context.subtype == "generic_effect":
        return _entered_effect_values(unit, context)
    return _raw_input_values(unit, context)


def _entered_effect_values(unit, context: _ReviewContext) -> tuple[object, object]:
    effect_groups = (
        context.groups[:1]
        if context.metric in meta_globals.ONE_ARM_METRICS
        else context.groups
    )
    comparison = "-".join(effect_groups)
    entry = unit.entered_effects.get(context.metric, {}).get(comparison, {})
    standard_error = entry.get("SE")
    if standard_error is None:
        standard_error = _standard_error_from_interval(
            entry, context.confidence_multiplier
        )
    return entry.get("est"), standard_error


def _raw_input_values(unit, context: _ReviewContext) -> tuple[object, ...]:
    raw_groups = context.groups
    if (
        context.data_type in (meta_globals.BINARY, meta_globals.CONTINUOUS)
        and context.metric in meta_globals.ONE_ARM_METRICS
    ):
        raw_groups = raw_groups[:1]
    field_count = len(_RAW_FIELDS.get(context.data_type, ()))
    return tuple(
        value
        for group_name in raw_groups
        for value in (
            unit.get_raw_data_for_group(group_name)
            if group_name in unit.groups
            else (None,) * field_count
        )
    )


def _field_input_issue(study, study_identity, unit, context, field, values):
    value = values[field.column_index] if field.column_index < len(values) else None
    problem_kind, problem = _validate(field, value, values)
    if problem_kind is None:
        return None
    group = _field_group(unit, context, field)
    return _issue_for_field(
        study,
        study_identity,
        context.outcome_identity,
        context.follow_up_identity,
        getattr(group, "stable_id", None),
        field,
        value,
        problem_kind,
        problem,
    )


def _field_group(unit, context: _ReviewContext, field: _Field):
    if not context.groups or context.input_source != "raw":
        return None
    field_count = max(1, len(_RAW_FIELDS.get(context.data_type, ())))
    target_group_index = field.column_index // field_count
    group_name = context.groups[min(target_group_index, len(context.groups) - 1)]
    return unit.groups.get(group_name)


def _standard_error_from_interval(entry, confidence_multiplier):
    if not isinstance(confidence_multiplier, (int, float)) or confidence_multiplier <= 0:
        return None
    estimate = entry.get("est")
    if estimate is None:
        return None
    lower, upper = entry.get("lower"), entry.get("upper")
    try:
        estimate = float(estimate)
        if upper is not None:
            return (float(upper) - estimate) / confidence_multiplier
        if lower is not None:
            return (estimate - float(lower)) / confidence_multiplier
    except (TypeError, ValueError):
        return None
    return None


def _validate(field, value, values) -> tuple[IssueKind | None, str]:
    if value in (None, ""):
        return "missing-required", f"Required {field.label} is missing."
    number = _numeric_value(value)
    if number is None:
        return "invalid-value", f"{field.label} must be numeric."
    if not math.isfinite(number):
        return "invalid-value", f"{field.label} must be finite."
    problem = _validator_problem(field, number)
    if problem:
        return "invalid-value", problem
    if field.key.endswith(".events") and _events_exceed_total(field, number, values):
        return "invalid-value", "Events cannot exceed the total."
    return None, ""


def _numeric_value(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, SupportsFloat):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _validator_problem(field: _Field, number: float) -> str:
    if field.validator in ("count", "total"):
        return _count_or_total_problem(field, number)
    if field.validator == "nonnegative-number" and number < 0:
        return f"{field.label} cannot be negative."
    return ""


def _count_or_total_problem(field: _Field, number: float) -> str:
    if number % 1 != 0:
        return f"{field.label} must be a whole number."
    if field.validator == "count" and number < 0:
        return f"{field.label} cannot be negative."
    if field.validator == "total" and number <= 0:
        return f"{field.label} must be greater than zero."
    return ""


def _events_exceed_total(field: _Field, events: float, values: Sequence[object]) -> bool:
    total_index = field.column_index + 1
    if total_index >= len(values) or values[total_index] in (None, ""):
        return False
    total = _numeric_value(values[total_index])
    return total is not None and events > total


def _covariate_issues(
    study,
    context: _ReviewContext,
    study_identity: str,
    covariates: Sequence[object],
):
    return tuple(
        issue
        for covariate in covariates
        if (issue := _covariate_issue(study, context, study_identity, covariate))
        is not None
    )


def _covariate_issue(study, context, study_identity, covariate):
    name = str(getattr(covariate, "name", covariate))
    value = study.covariate_values.get(name)
    if value in (None, ""):
        kind: IssueKind = "missing-required"
        problem = f"Required covariate {name} is missing."
    elif getattr(covariate, "data_type", None) == meta_globals.CONTINUOUS:
        problem = _continuous_covariate_problem(name, value)
        if not problem:
            return None
        kind = "invalid-value"
    else:
        return None
    identity = str(getattr(covariate, "stable_id", name))
    field = _Field(name, name, "covariate", 0, "number")
    return _issue_for_field(
        study,
        study_identity,
        context.outcome_identity,
        context.follow_up_identity,
        None,
        field,
        value,
        kind,
        problem,
        covariate_identity=identity,
    )


def _continuous_covariate_problem(name: str, value: object) -> str:
    number = _numeric_value(value)
    if number is None or not math.isfinite(number):
        return f"Covariate {name} must be numeric and finite."
    return ""


def _issue_for_field(
    study,
    study_identity,
    outcome_identity,
    follow_up_identity,
    group_identity,
    field,
    value,
    kind,
    problem,
    *,
    covariate_identity=None,
):
    if field.column_kind == "covariate":
        column = WorkspaceColumnIdentity("covariate", (covariate_identity or field.key,))
    else:
        column = field.identity or WorkspaceColumnIdentity(
            field.column_kind, (field.column_index,)
        )
    target = StudyCellTarget(
        int(study.id),
        study_identity,
        outcome_identity,
        follow_up_identity,
        group_identity,
        column,
        field.editor_id,
    )
    return _issue(
        study,
        study_identity,
        kind=kind,
        field=field.label,
        value=value,
        problem=problem,
        target=target,
    )


def _issue(
    study,
    study_identity,
    *,
    kind,
    field,
    value,
    problem,
    target,
    method_id=None,
):
    target_identity = (
        repr(target)
        if target is not None
        else f"method:{method_id}:{field}"
    )
    issue_id = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"rc-metastudio/data-issue/v1/{study_identity}/{target_identity}/{kind}/{method_id or ''}",
    ).hex
    return DataIssue(
        issue_id,
        int(study.id),
        study_identity,
        str(study.name),
        kind,
        field,
        value,
        problem,
        f"Edit {field} for this study in the current data table."
        if target is not None
        else "Review the selected method's exclusion setting.",
        target,
        True,
    )
