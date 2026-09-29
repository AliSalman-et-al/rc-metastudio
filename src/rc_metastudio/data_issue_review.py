# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only review of studies in the currently selected analysis context."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Sequence
from typing import Literal, Protocol, cast
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
    dataset = context_model.dataset

    outcome_name = context_model.current_outcome_name
    time_point = context_model.get_current_follow_up_name()
    groups = tuple(context_model.get_current_groups())
    outcome = dataset.get_outcome_obj(outcome_name) if outcome_name else None
    outcome_identity = getattr(outcome, "stable_id", None)
    follow_up_identity = (
        dataset.follow_up_stable_ids_by_outcome.get(outcome_name, {}).get(time_point)
        if outcome_name and time_point
        else None
    )
    data_type = getattr(outcome, "data_type", None)
    subtype = getattr(outcome, "sub_type", None)
    metric = context_model.current_effect
    if input_source is None:
        input_source = "entered-effect" if subtype == "generic_effect" else "raw"
    fields = _fields_for_context(data_type, subtype, metric, groups, input_source)

    by_study = _method_decisions(method_id, method_exclusions)
    unknown_exclusions = set(by_study) - {int(study.id) for study in dataset.studies}
    if unknown_exclusions:
        raise ValueError("method exclusions reference a study that is no longer present")
    result = []
    for study in dataset.studies:
        if not _is_reviewable(study, outcome_name, time_point, groups):
            continue

        identity = f"study:{study.id}"
        study_issues: list[DataIssue] = []
        reasons: list[str] = []
        if not str(study.name).strip():
            study_issues.append(
                _issue_for_field(
                    study,
                    identity,
                    outcome_identity,
                    follow_up_identity,
                    None,
                    _Field(
                        "study-name",
                        "Study name",
                        "fixed",
                        1,
                        "number",
                        WorkspaceColumnIdentity("fixed", ("study-name",)),
                    ),
                    study.name,
                    "missing-required",
                    "A study name is required to identify this row in the analysis.",
                )
            )
        if outcome_name and time_point:
            study_issues.extend(
                _input_issues(
                    study,
                    identity,
                    outcome_name,
                    time_point,
                    outcome_identity,
                    follow_up_identity,
                    groups,
                    data_type,
                    subtype,
                    metric,
                    fields,
                    input_source,
                    getattr(context_model, "confidence_multiplier", None),
                )
            )
        study_issues.extend(
            _covariate_issues(
                study,
                identity,
                required_covariates,
                outcome_identity,
                follow_up_identity,
            )
        )

        decision = by_study.get(int(study.id))
        if bool(getattr(study, "manually_excluded", False)):
            decision = None
        if decision is not None and decision.permitted_by_method and decision.confirmed:
            status: ReviewStatus = "excluded"
            reasons.append(f"Excluded from {decision.method_id}: {decision.reason}")
        elif bool(getattr(study, "manually_excluded", False)):
            status = "excluded"
            reasons.append("Manually excluded from the working dataset.")
        elif study_issues:
            status = "invalid" if any(
                issue.kind == "invalid-value" for issue in study_issues
            ) else "missing"
            reasons.extend(issue.problem for issue in study_issues)
        elif not bool(getattr(study, "include", True)):
            status = "excluded"
            reasons.append("Not included in the working dataset.")
        else:
            status = "included"
            reasons.append("Included in the selected analysis context.")

        if decision is not None and not (
            decision.permitted_by_method and decision.confirmed
        ):
            reason = (
                "This method does not permit the requested study exclusion."
                if not decision.permitted_by_method
                else "Confirm this method-specific exclusion before running."
            )
            study_issues.append(
                _issue(
                    study,
                    identity,
                    kind="exclusion-review",
                    field="Study exclusion",
                    value=decision.reason,
                    problem=reason,
                    target=None,
                    method_id=method_id,
                )
            )
            reasons.append(reason)
            if status == "included":
                status = "invalid"

        result.append(
            StudyReview(
                int(study.id),
                identity,
                str(study.name),
                status,
                tuple(reasons),
                tuple(study_issues),
                decision,
            )
        )

    return DataIssueReview(
        str(outcome_name) if outcome_name is not None else None,
        str(time_point) if time_point is not None else None,
        groups,
        method_id,
        str(metric) if metric is not None else None,
        input_source,
        tuple(result),
    )


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
    if bool(getattr(study, "include", False)) or bool(
        getattr(study, "manually_excluded", False)
    ):
        return True
    if str(getattr(study, "name", "")).strip() or getattr(study, "year", None):
        return True
    if any(value not in (None, "") for value in study.covariate_values.values()):
        return True
    if not outcome_name or not time_point:
        return False
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
    outcome_name,
    time_point,
    outcome_identity,
    follow_up_identity,
    groups,
    data_type,
    subtype,
    metric,
    fields,
    input_source,
    confidence_multiplier,
):
    try:
        unit = study.get_analysis_unit(outcome_name, time_point)
    except (KeyError, ValueError):
        unit = None
    if unit is None:
        return tuple(
            _issue_for_field(
                study,
                study_identity,
                outcome_identity,
                follow_up_identity,
                None,
                field,
                None,
                "missing-required",
                f"Required {field.label} is missing.",
            )
            for field in fields
        )

    if input_source == "entered-effect" or subtype == "generic_effect":
        effect_groups = groups[:1] if metric in meta_globals.ONE_ARM_METRICS else groups
        comparison = "-".join(effect_groups)
        entry = unit.entered_effects.get(metric, {}).get(comparison, {})
        standard_error = entry.get("SE")
        if standard_error is None:
            standard_error = _standard_error_from_interval(entry, confidence_multiplier)
        values = (entry.get("est"), standard_error)
    else:
        raw_groups = groups[:1] if data_type in (meta_globals.BINARY, meta_globals.CONTINUOUS) and metric in meta_globals.ONE_ARM_METRICS else groups
        values = tuple(
            value
            for group_name in raw_groups
            for value in (
                unit.get_raw_data_for_group(group_name)
                if group_name in unit.groups
                else (None,) * len(_RAW_FIELDS.get(data_type, ()))
            )
        )

    issues = []
    for field in fields:
        value = values[field.column_index] if field.column_index < len(values) else None
        target_group_index = field.column_index // max(1, len(_RAW_FIELDS.get(data_type, ())))
        group_name = (
            groups[min(target_group_index, len(groups) - 1)]
            if groups and input_source == "raw"
            else None
        )
        group = unit.groups.get(group_name) if group_name else None
        problem_kind, problem = _validate(field, value, values)
        if problem:
            issues.append(
                _issue_for_field(
                    study,
                    study_identity,
                    outcome_identity,
                    follow_up_identity,
                    getattr(group, "stable_id", None),
                    field,
                    value,
                    problem_kind,
                    problem,
                )
            )
    return tuple(issues)


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
    if isinstance(value, bool):
        return "invalid-value", f"{field.label} must be numeric."
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "invalid-value", f"{field.label} must be numeric."
    if not math.isfinite(number):
        return "invalid-value", f"{field.label} must be finite."
    if field.validator in ("count", "total") and not number.is_integer():
        return "invalid-value", f"{field.label} must be a whole number."
    if field.validator == "count" and number < 0:
        return "invalid-value", f"{field.label} cannot be negative."
    if field.validator == "total" and number <= 0:
        return "invalid-value", f"{field.label} must be greater than zero."
    if field.validator == "nonnegative-number" and number < 0:
        return "invalid-value", f"{field.label} cannot be negative."
    if field.key.endswith(".events"):
        total_index = field.column_index + 1
        if total_index < len(values) and values[total_index] not in (None, ""):
            try:
                if number > float(values[total_index]):
                    return "invalid-value", "Events cannot exceed the total."
            except (TypeError, ValueError):
                pass
    return None, ""


def _covariate_issues(
    study,
    study_identity,
    covariates,
    outcome_identity,
    follow_up_identity,
):
    issues = []
    for covariate in covariates:
        name = str(getattr(covariate, "name", covariate))
        value = study.covariate_values.get(name)
        if value in (None, ""):
            identity = str(getattr(covariate, "stable_id", name))
            field = _Field(name, name, "covariate", 0, "number")
            issues.append(
                _issue_for_field(
                    study,
                    study_identity,
                    outcome_identity,
                    follow_up_identity,
                    None,
                    field,
                    value,
                    "missing-required",
                    f"Required covariate {name} is missing.",
                    covariate_identity=identity,
                )
            )
        elif getattr(covariate, "data_type", None) == meta_globals.CONTINUOUS:
            if isinstance(value, bool):
                numeric = math.nan
            else:
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    numeric = math.nan
            if not math.isfinite(numeric):
                identity = str(getattr(covariate, "stable_id", name))
                field = _Field(name, name, "covariate", 0, "number")
                issues.append(
                    _issue_for_field(
                        study,
                        study_identity,
                        outcome_identity,
                        follow_up_identity,
                        None,
                        field,
                        value,
                        "invalid-value",
                        f"Covariate {name} must be numeric and finite.",
                        covariate_identity=identity,
                    )
                )
    return tuple(issues)


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
