# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt-free editing operations for the dataset workspace.

The table model owns Qt roles, indexes, and presentation.  This module owns
the backend boundary used while an edit is being validated or previewed.
Keeping that boundary here also gives non-Qt callers a small, testable way to
calculate the same raw-data preview as the table.
"""

from __future__ import annotations
from rc_metastudio.domain_ids import RowId, SheetId

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
import uuid
from typing import Literal, Protocol

from rc_metastudio import name_validation, qt_text
from rc_metastudio import r_runtime, r_bridge
from rc_metastudio.analysis.catalog import RATIO_DATA_TYPES, EVENT_RATES, TIME_TO_EVENT, ONE_ARM_METRICS
from rc_metastudio.ratio_data import RATIO_FIELDS

from rc_metastudio.project.model import Dataset, Sheet, StudyRow
from rc_metastudio.project.study import AnalysisUnit, EffectEstimate
from rc_metastudio.analysis.study_selection import (
    has_study_entered_data,
    BINARY,
    CONTINUOUS,
    DIAGNOSTIC,
    ScaleBridge,
    calculate_raw_effects,
    raw_data_is_complete,
    raw_data_is_empty,
    make_display_scale_converter,
    to_calculation_scale,
)
from rc_metastudio.analysis.catalog import BINARY_ONE_ARM_METRICS, CONTINUOUS_ONE_ARM_METRICS, DIAGNOSTIC_METRICS, FACTOR
from rc_metastudio.analysis.validation import (
    DEFAULT_CONFIDENCE_LEVEL,
    is_an_int, is_empty,
    normal_confidence_multiplier, validate_confidence_interval_order, validate_confidence_level,
)
from rc_metastudio.workspace.columns import (
    FIRST_IMPORT_COLUMN, FIRST_RAW_COLUMN, CovariateCell, EditableField, OutcomeCell,
    RawCell, RawColumn, RawInputKind, sheet_columns,
)


@dataclass(frozen=True, slots=True)
class ConfidenceSettings:
    """Validated confidence level and multiplier used by one edit session."""

    level: float
    multiplier: float


class _InclusionTarget(Protocol):
    include: bool
    manually_excluded: bool


def _effect_value(effect: Mapping[str, object] | EffectEstimate, field: str):
    if isinstance(effect, EffectEstimate):
        return {
            "est": effect.estimate,
            "lower": effect.lower,
            "upper": effect.upper,
            "SE": effect.standard_error,
        }[field]
    return effect[field]


@dataclass(frozen=True, slots=True)
class WorkspaceEditingContext:
    """Domain values needed to edit one visible workspace."""

    sheet_id: SheetId | None
    arm_names: tuple[str, ...]
    current_effect: str | None
    data_type: int | None
    outcome_subtype: str | None
    arm_key: tuple[str, ...]
    confidence_level: float
    confidence_multiplier: float

    @classmethod
    def for_sheet(cls, sheet: Sheet | None, metric: str | None, confidence: ConfidenceSettings):
        return cls(
            sheet.id if sheet else None,
            tuple(arm.name for arm in sheet.arms) if sheet else (),
            metric,
            sheet.data_type if sheet else None,
            sheet.sub_type if sheet else None,
            comparison_key(sheet, metric),
            confidence.level,
            confidence.multiplier,
        )


@dataclass(slots=True)
class WorkspaceViewState:
    """Serializable selection and confidence state for the workspace."""

    current_sheet_id: SheetId | None = None
    current_effect: str | None = None
    confidence_level: float = 95.0
    confidence_multiplier: float = 1.96


def selected_metric(sheet: Sheet | None) -> str | None:
    if sheet is None:
        return None
    defaults = {BINARY: "OR", CONTINUOUS: "SMD", TIME_TO_EVENT: "HR", EVENT_RATES: "IRR"}
    return sheet.settings.get("metric") or sheet.settings.get("active_effect") or defaults.get(sheet.data_type)


def comparison_key(sheet: Sheet | None, metric: str | None) -> tuple[str, ...]:
    if sheet is None:
        return ()
    arms = sheet.arms[:1] if metric in ONE_ARM_METRICS else sheet.arms
    return tuple(arm.id for arm in arms)


def add_covariate(sheet: Sheet, name, data_type, *, values=None, stable_id=None):
    name = name_validation.validate_unique_name("covariate", name, [cov["name"] for cov in sheet.covariates])
    covariate = {
        "id": stable_id or uuid.uuid4().hex,
        "name": name,
        "data_type": {"factor": FACTOR, "continuous": CONTINUOUS}.get(data_type, data_type),
    }
    sheet.covariates.append(covariate)
    for row in sheet.rows:
        row.covariate_values[covariate["id"]] = (values or {}).get(row.label)
    return covariate


@dataclass(frozen=True, slots=True)
class CellRejection:
    message: str
    kind: Literal["value", "number", "backend"] = "value"


def _study_identity_at(sheet: Sheet, index: int) -> tuple[str, int | None]:
    if index >= len(sheet.rows):
        return "", 0
    study = sheet.rows[index]
    return study.label, study.year


def _edited_study_name(original: str, fields: Mapping[str, object]) -> str:
    if "name" in fields:
        return name_validation.validate_required_name("study", fields["name"])
    return original


def _parse_study_identity_year(value: object) -> int | None:
    text = qt_text.to_native_text(value)
    if qt_text.is_blank(text):
        return 0
    try:
        return int(text)
    except ValueError:
        return int(float(text)) if is_an_int(text) else None


class WorkspaceEditingService:
    """Perform backend-facing edit work without importing Qt.

    ``bridge`` is injectable for deterministic tests and for applications that
    provide another analysis backend.  The default remains the production
    RCMetaR bridge, preserving the existing statistical contract.
    """

    def __init__(self, bridge: ScaleBridge | None = None) -> None:
        self.bridge = r_bridge if bridge is None else bridge

    @staticmethod
    def update_inclusion_after_edit(
        study: _InclusionTarget,
        *,
        diagnostic: bool,
        inclusion_column: bool,
        outcome_selected: bool,
        effect: Mapping[str, object] | EffectEstimate,
        data_type: object,
        outcome_subtype: str | None,
    ) -> None:
        """Apply the durable inclusion rule after a successful cell edit."""
        if diagnostic:
            return
        if inclusion_column:
            return
        if not outcome_selected:
            return
        if not study.manually_excluded:
            study.include = True
        if not WorkspaceEditingService._effect_is_complete(
            effect, data_type, outcome_subtype
        ):
            study.include = False

    @staticmethod
    def _effect_is_complete(effect, data_type, outcome_subtype) -> bool:
        if data_type == CONTINUOUS and outcome_subtype == "generic_effect":
            return all(_effect_value(effect, key) is not None for key in ("est", "SE"))
        return all(
            _effect_value(effect, key) is not None
            for key in ("upper", "lower", "est")
        )

    def confidence_settings(self, level: object) -> ConfidenceSettings:
        validated = validate_confidence_level(level)
        return ConfidenceSettings(validated, normal_confidence_multiplier(validated))

    def preview_raw_effects(
        self,
        data_type: object,
        effect: str | None,
        raw_data: tuple[object, ...] | list[object],
        confidence_level: float,
    ):
        """Calculate raw effects for a candidate edit."""
        return calculate_raw_effects(
            self.bridge, data_type, effect, raw_data, confidence_level
        )

    def to_calculation_scale(
        self,
        value: object,
        data_type: object,
        effect: str | None,
        n1: object = None,
    ):
        return to_calculation_scale(self.bridge, value, data_type, effect, n1)

    def display_scale_converter(
        self,
        data_type: object,
        effect: str | None,
        n1: object = None,
    ):
        if not r_runtime.is_ready():
            return lambda value: None
        return make_display_scale_converter(self.bridge, data_type, effect, n1)

    def apply_edit(
        self,
        dataset: Dataset,
        row: int,
        field: EditableField,
        context: WorkspaceEditingContext,
        value: object,
        *,
        allow_raw_and_entered: bool = False,
        row_order: Sequence[int] | None = None,
    ) -> CellRejection | None:
        if context.sheet_id is None or row < 0:
            return CellRejection("Select an outcome and a study row before editing.")
        sheet = dataset.sheet(context.sheet_id)
        if field in ("name", "year"):
            rejection, _ = self.edit_study_identities(sheet, {row: {field: value}}, row_order=row_order)
            return rejection
        if row >= len(sheet.rows):
            return CellRejection("Enter a study name first.")
        study = sheet.rows[row]
        if not study.label.strip() and not qt_text.is_blank(value):
            return CellRejection("Enter a study name first.")
        if isinstance(field, (RawCell, OutcomeCell)):
            return self._edit_measurement(study, field, context, value, allow_raw_and_entered=allow_raw_and_entered)
        if field == "include":
            if type(value) is not bool:
                return CellRejection("Study inclusion must be checked or unchecked.")
            self.set_inclusion(study, value)
            return None
        return self._edit_covariate(study, field, value)

    def load_import_rows(
        self, dataset: Dataset, sheet: Sheet, rows: Sequence[Sequence[str]],
        on_row_loaded: Callable[[int], None],
    ) -> list[str]:
        """Apply normalized tabular input to a detached sheet before publishing it."""
        columns = sheet_columns(sheet.data_type, sheet.sub_type)
        sections = range(FIRST_IMPORT_COLUMN, columns.first_covariate + len(sheet.covariates))
        fields = [columns.editable_field(section, sheet.covariates) for section in sections]
        confidence = self.confidence_settings(sheet.settings.get("confidence_level", DEFAULT_CONFIDENCE_LEVEL))
        context = WorkspaceEditingContext.for_sheet(sheet, selected_metric(sheet), confidence)
        rejection, _ = self.edit_study_identities(
            sheet, {row: {"name": values[0], "year": values[1]} for row, values in enumerate(rows)},
        )
        if rejection is not None:
            raise ValueError(rejection.message)
        warnings = []
        for row, values in enumerate(rows):
            for section, field, value in zip(sections, fields, values):
                if section < FIRST_RAW_COLUMN:
                    continue
                if field is None:
                    raise ValueError(f"Study row {row + 1}, column {section} is calculated automatically and cannot be edited directly.")
                rejection = self.apply_edit(dataset, row, field, context, value, allow_raw_and_entered=True)
                if rejection is not None:
                    message = f"Study row {row + 1}, column {section}: {rejection.message}"
                    if rejection.kind == "backend":
                        raise ValueError(message)
                    warnings.append(message)
            on_row_loaded(row + 1)
        return warnings

    def _edit_measurement(
        self, study: StudyRow, field: RawCell | OutcomeCell, context: WorkspaceEditingContext,
        value: object, *, allow_raw_and_entered: bool,
    ) -> CellRejection | None:
        draft = replace(study, analysis_unit=study.analysis_unit.copy_for_edit())
        try:
            rejection = self._apply_measurement(draft, field, context, value, allow_raw_and_entered)
            if rejection is not None:
                return rejection
            self._update_inclusion(draft, context, allow_raw_and_entered=allow_raw_and_entered)
        except Exception as error:
            edited = "raw data" if isinstance(field, RawCell) else "outcome data"
            return CellRejection(f"Could not compute study effects from the edited {edited}: {error}", kind="backend")
        study.analysis_unit.adopt_calculated_state(draft.analysis_unit)
        study.include = draft.include
        return None

    def _apply_measurement(self, study, field: RawCell | OutcomeCell, context, value, allow_raw_and_entered):
        if isinstance(field, RawCell):
            return self._edit_raw_data(study, field.position, context, value)
        if context.data_type in RATIO_DATA_TYPES:
            return self._edit_ratio_input(study, field.position, context, value)
        return self._edit_outcome(study, field.position, context, value, allow_raw_and_entered)

    def _edit_ratio_input(self, study, position: int, context, value):
        unit = study.analysis_unit
        field = RATIO_FIELDS[position]
        text = qt_text.to_native_text(value).strip()
        try:
            parsed = text
            if field in ("estimate", "lower", "upper", "se", "confidence"):
                parsed = float(text) if text else (95.0 if field == "confidence" else None)
            candidate = replace(unit.ratio_input(context.arm_names), **{field: parsed})
            candidate.validate()
        except (TypeError, ValueError) as error:
            return CellRejection(str(error))
        unit.set_ratio_input(context.arm_names, candidate)
        return None

    @staticmethod
    def set_inclusion(study: StudyRow, included: bool) -> None:
        study.include = included
        study.manually_excluded = not included

    def _update_inclusion(
        self,
        study,
        context,
        *,
        allow_raw_and_entered: bool = False,
    ) -> None:
        if (
            context.data_type == DIAGNOSTIC
            or (allow_raw_and_entered and not raw_data_is_empty(self._raw_data(study, context)))
        ):
            return
        unit = study.analysis_unit
        if context.data_type in RATIO_DATA_TYPES:
            raw = unit.get_raw_data_for_arms(context.arm_names)
            study.include = not study.manually_excluded and unit.ratio_input(context.arm_names).ready(raw, metric=context.current_effect)
            return
        if self._raw_data_is_complete_for_context(self._raw_data(study, context), context):
            study.include = not study.manually_excluded
            return
        effect = unit.get_effect_for_source(
            "entered", context.current_effect or "", context.arm_key
        )
        self.update_inclusion_after_edit(
            study,
            diagnostic=context.data_type == DIAGNOSTIC,
            inclusion_column=False,
            outcome_selected=True,
            effect=effect,
            data_type=context.data_type,
            outcome_subtype=context.outcome_subtype,
        )

    @staticmethod
    def edit_study_identities(
        sheet: Sheet, edits: Mapping[int, Mapping[str, object]], *,
        row_order: Sequence[int] | None = None, skip_invalid_year: bool = False,
    ) -> tuple[CellRejection | None, int]:
        """Validate all proposed names and years together before applying them."""
        updates = {}
        skipped = 0
        for index, fields in edits.items():
            original = _study_identity_at(sheet, index)
            try:
                name = _edited_study_name(original[0], fields)
            except ValueError as error:
                return CellRejection(str(error)), skipped
            year = original[1]
            if "year" in fields:
                parsed_year = _parse_study_identity_year(fields["year"])
                if parsed_year is not None:
                    year = parsed_year
                elif skip_invalid_year:
                    skipped += 1
                else:
                    return CellRejection("Enter the year as a whole number, for example 2019.", kind="number"), skipped
            if (name, year) != original:
                updates[index] = (name, year)

        rejection = WorkspaceEditingService._study_identity_conflict(sheet, updates, row_order)
        if rejection is not None:
            return rejection, skipped
        WorkspaceEditingService._apply_study_identities(sheet, updates)
        return None, skipped

    @staticmethod
    def _study_identity_conflict(
        sheet: Sheet, updates: dict[int, tuple[str, int | None]], row_order: Sequence[int] | None,
    ) -> CellRejection | None:
        ordered = list(row_order) if row_order is not None else list(range(len(sheet.rows)))
        ordered.extend(range(len(sheet.rows), max(updates, default=len(sheet.rows) - 1) + 1))
        seen = {}
        for row_number, index in enumerate(ordered, start=1):
            name, year = updates.get(index, _study_identity_at(sheet, index))
            key = name_validation.study_identity(name, year)
            if not key[0]:
                continue
            previous = seen.get(key)
            if previous is not None:
                previous_index, previous_row = previous
                if index in updates or previous_index in updates:
                    conflict_row = row_number if index not in updates else previous_row
                    return CellRejection(name_validation.study_conflict(key, conflict_row))
            else:
                seen[key] = (index, row_number)

        return None

    @staticmethod
    def _apply_study_identities(sheet: Sheet, updates: dict[int, tuple[str, int | None]]) -> None:
        for index, (name, year) in sorted(updates.items()):
            while len(sheet.rows) <= index:
                unit = AnalysisUnit(sheet, arm_names=[arm.name for arm in sheet.arms],
                                    arm_stable_ids=[arm.id for arm in sheet.arms])
                sheet.rows.append(StudyRow(RowId(uuid.uuid4().hex), "", unit, include=False))
            study = sheet.rows[index]
            if name != study.label and not study.manually_excluded and not has_study_entered_data(study):
                study.include = True
            study.label, study.year = name, year

    def _raw_data(self, study: StudyRow, context: WorkspaceEditingContext):
        return study.analysis_unit.get_raw_data_for_arms(
            context.arm_names
        )

    @staticmethod
    def _verify_raw_data(
        number: float, column: RawColumn, raw_data, columns: Sequence[RawColumn],
    ) -> CellRejection | None:
        kind = column.field.kind
        binary_fields = (RawInputKind.BINARY_EVENTS, RawInputKind.BINARY_TOTAL)
        if kind in (*binary_fields, RawInputKind.DIAGNOSTIC_COUNT):
            if not number.is_integer():
                return CellRejection("Counts must be whole numbers.", kind="number")
            if number < 0:
                return CellRejection("Counts cannot be negative.")
        if kind in binary_fields:
            return WorkspaceEditingService._verify_binary_bounds(number, column, raw_data, columns)
        if kind is RawInputKind.DIAGNOSTIC_COUNT:
            return WorkspaceEditingService._verify_diagnostic_bounds(
                number, raw_data, column.field_index,
            )
        if kind is RawInputKind.SAMPLE_SIZE and number <= 0:
            return CellRejection("Participants must be a positive whole number.", kind="number")
        if kind is RawInputKind.STANDARD_DEVIATION and number <= 0:
            return CellRejection("Standard deviation must be greater than zero.")
        if kind is RawInputKind.RATE_EVENTS and (number < 0 or not number.is_integer()):
            return CellRejection("Events must be non-negative integers.", kind="number")
        if kind is RawInputKind.PERSON_TIME and number <= 0:
            return CellRejection("Person-time must be positive.")
        return None

    @staticmethod
    def _verify_binary_bounds(
        number: float, column: RawColumn, raw_data, columns: Sequence[RawColumn],
    ) -> CellRejection | None:
        editing_events = column.field.kind is RawInputKind.BINARY_EVENTS
        paired_kind = RawInputKind.BINARY_TOTAL if editing_events else RawInputKind.BINARY_EVENTS
        other = next(
            candidate for candidate in columns
            if candidate.arm_index == column.arm_index and candidate.field.kind is paired_kind
        )
        paired_value = raw_data[other.field_index]
        if not is_an_int(paired_value):
            return None
        paired_count = int(float(paired_value))
        events, total = (number, paired_count) if editing_events else (paired_count, number)
        if events > total:
            return CellRejection("Events cannot exceed the arm total.")
        return None

    @staticmethod
    def _verify_diagnostic_bounds(number: float, raw_data, position: int) -> CellRejection | None:
        """Reject an empty diagnostic study while allowing individual zero cells."""
        candidate = list(raw_data)
        if position >= len(candidate):
            return None
        candidate[position] = number
        if len(candidate) != 4 or any(is_empty(value) for value in candidate):
            return None
        try:
            all_zero = all(float(value) == 0 for value in candidate)
        except (TypeError, ValueError):
            return None
        if all_zero:
            return CellRejection(
                "Diagnostic 2x2 table must contain at least one participant; "
                "enter at least one count greater than zero."
            )
        return None

    def _verify_outcome_data(
        self, study: StudyRow, position: int, context: WorkspaceEditingContext, number: float, allow_raw_and_entered: bool
    ) -> CellRejection | None:
        unit = study.analysis_unit
        previous_display = self._previous_display_outcome(
            study, position, context, unit
        )
        raw_data = self._raw_data(study, context)
        if not allow_raw_and_entered and not all(is_empty(item) for item in raw_data):
            error = self._verify_raw_override(number, previous_display, position)
            if error:
                return error
        return self._verify_outcome_value(number, previous_display, position, context)

    def _previous_display_outcome(
        self, study, position, context, unit: AnalysisUnit
    ) -> tuple[object, object, object]:
        metric, _ = self._outcome_metric(position, context)
        effect = unit.get_effect_and_ci_for_source(
            "entered", metric or "", context.arm_key, context.confidence_multiplier
        )
        converter = self.display_scale_converter(
            context.data_type, metric, self._outcome_sample_size(study, context)
        )
        return tuple(converter(item) for item in effect)

    @staticmethod
    def _verify_raw_override(number: float, previous_display, position) -> CellRejection | None:
        outcome_index = position % 3
        previous = previous_display[outcome_index]
        delta = abs(number - previous) if previous is not None else float("-inf")
        if delta > 10e-6:
            return CellRejection("This study already has arm data. Clear the arm data before entering an effect estimate directly.")
        return None

    @staticmethod
    def _verify_outcome_value(number: float, previous_display, position, context) -> CellRejection | None:
        if context.current_effect in ("OR", "RR") and number < 0:
            return CellRejection("Ratios cannot be negative.")
        outcome_index = position % 3
        if context.outcome_subtype == "generic_effect":
            generic_index = position % 2
            if context.data_type == CONTINUOUS and generic_index == 1 and number < 0:
                return CellRejection("Standard error cannot be negative.")
            return None
        candidate = list(previous_display)
        candidate[outcome_index] = number
        ok, message = validate_confidence_interval_order(
            est=candidate[0], low=candidate[1], high=candidate[2]
        )
        return None if ok else CellRejection(message or "Invalid confidence interval.")

    def _edit_raw_data(
        self,
        study: StudyRow,
        position: int,
        context: WorkspaceEditingContext,
        value: object,
    ) -> CellRejection | None:
        number, valid = qt_text.parse_optional_decimal(value)
        if not valid:
            return CellRejection("Enter a number.", kind="number")
        columns = sheet_columns(context.data_type, context.outcome_subtype).raw
        column = columns[position]
        group = context.arm_names[column.arm_index or 0]
        raw_data = study.analysis_unit.get_raw_data_for_arm(group)
        if number is not None:
            error = self._verify_raw_data(number, column, raw_data, columns)
            if error is not None:
                return error
        raw_data[column.field_index] = "" if number is None else number
        self.update_effect_previews_if_possible(study, context)
        return None

    def _edit_outcome(
        self, study: StudyRow, position: int, context: WorkspaceEditingContext, value: object, allow_raw_and_entered: bool
    ) -> CellRejection | None:
        display_value, valid = qt_text.parse_optional_decimal(value)
        if not valid:
            return CellRejection("Enter a number.", kind="number")
        if display_value is not None:
            error = self._verify_outcome_data(study, position, context, display_value, allow_raw_and_entered)
            if error is not None:
                return error
        unit = study.analysis_unit
        metric, outcome_index = self._outcome_metric(position, context)
        if metric is None:
            return CellRejection("Choose an effect measure first.")
        n1 = self._outcome_sample_size(study, context)
        calculation_value = self.to_calculation_scale(
            display_value, context.data_type, metric, n1
        )
        self._set_entered_outcome(
            unit, metric, outcome_index, calculation_value, context
        )
        self._recalculate_entered_outcome(unit, metric, context)
        unit.calculate_display_effect_and_ci(
            metric,
            context.arm_key,
            self.display_scale_converter(context.data_type, metric, n1),
            confidence_level=context.confidence_level,
            confidence_multiplier=context.confidence_multiplier,
            source="entered",
        )
        return None

    @staticmethod
    def _outcome_metric(
        position: int, context: WorkspaceEditingContext
    ) -> tuple[str | None, int]:
        if context.data_type == DIAGNOSTIC:
            return ("Spec" if position >= 3 else "Sens", position % 3)
        return context.current_effect, position

    def _outcome_sample_size(self, study, context):
        if context.current_effect != "PFT":
            return None
        return self._raw_data(study, context)[1]

    @staticmethod
    def _set_entered_outcome(
        unit: AnalysisUnit,
        metric: str,
        outcome_index: int,
        calculation_value,
        context: WorkspaceEditingContext,
    ) -> None:
        entered = unit.get_effect_for_source("entered", metric, context.arm_key)
        if outcome_index == 0:
            values = (calculation_value, entered.lower, entered.upper, entered.standard_error)
        elif outcome_index == 1 and context.outcome_subtype == "generic_effect":
            values = (entered.estimate, entered.lower, entered.upper, calculation_value)
        elif outcome_index == 1:
            values = (entered.estimate, calculation_value, entered.upper, entered.standard_error)
        else:
            values = (entered.estimate, entered.lower, calculation_value, entered.standard_error)
        unit.set_effect_for_source("entered", metric, context.arm_key, *values)

    @staticmethod
    def _recalculate_entered_outcome(
        unit: AnalysisUnit, metric: str, context: WorkspaceEditingContext
    ) -> None:
        if context.outcome_subtype == "generic_effect":
            return
        entered = unit.get_effect_for_source("entered", metric, context.arm_key)
        values = (entered.estimate, entered.lower, entered.upper)
        se = unit.calculate_se_if_possible(
            metric,
            context.arm_key,
            confidence_multiplier=context.confidence_multiplier,
            source="entered",
        ) if None not in values else None
        unit.set_effect_for_source(
            "entered", metric, context.arm_key,
            entered.estimate, entered.lower, entered.upper, se,
        )

    def _edit_covariate(self, study: StudyRow, field: CovariateCell, value: object) -> CellRejection | None:
        if field.data_type == FACTOR:
            converted = qt_text.to_native_text(value)
        elif qt_text.is_blank(value):
            converted = None
        else:
            converted, valid = self._number(value)
            if not valid:
                return CellRejection("Numeric covariates require numbers.", kind="number")
        study.covariate_values[field.identity] = converted
        return None

    @staticmethod
    def _number(value: object) -> tuple[float | None, bool]:
        text, valid = qt_text.normalize_decimal_text(value)
        if not valid or qt_text.is_blank(text):
            return None, False
        try:
            return float(text), True
        except ValueError:
            return None, False

    def update_effect_previews_if_possible(
        self,
        study: StudyRow,
        context: WorkspaceEditingContext,
        *,
        update_inclusion: bool = True,
    ) -> None:
        unit = study.analysis_unit
        raw_data = self._raw_data(study, context)
        if context.data_type in RATIO_DATA_TYPES:
            self._update_ratio_outcome(study, unit, raw_data, context, update_inclusion)
            return
        complete = self._raw_data_is_complete_for_context(raw_data, context)
        if update_inclusion and self._should_clear_inclusion(unit, context):
            study.include = False
        if complete and not r_runtime.is_ready():
            if update_inclusion:
                study.include = not study.manually_excluded
            return
        if complete:
            self._calculate_complete_effect_previews(
                study, unit, raw_data, context, update_inclusion=update_inclusion
            )
        elif not raw_data_is_empty(raw_data):
            self._clear_incomplete_effect_previews(unit, context)

    def _update_ratio_outcome(self, study, unit, raw_data, context, update_inclusion):
        self._clear_effect_and_display_ci(unit, context.current_effect, context)
        record = unit.ratio_input(context.arm_names)
        ready = record.ready(raw_data, metric=context.current_effect)
        if ready and record.selected_source(raw_data, metric=context.current_effect) == "raw" and r_runtime.is_ready():
            est, lower, upper = r_bridge.incidence_rate_effect_preview(raw_data, context.confidence_level)
            self._store_derived_effect_preview(unit, context.current_effect, context, est, lower, upper)
        if update_inclusion:
            study.include = not study.manually_excluded and ready


    @staticmethod
    def _raw_data_is_complete_for_context(raw_data, context) -> bool:
        if raw_data_is_complete(raw_data):
            return True
        one_arm = context.current_effect in BINARY_ONE_ARM_METRICS + CONTINUOUS_ONE_ARM_METRICS
        return one_arm and raw_data_is_complete(raw_data[: len(raw_data) // 2])

    def _should_clear_inclusion(self, unit: AnalysisUnit, context) -> bool:
        if context.data_type == DIAGNOSTIC:
            if not raw_data_is_empty(unit.get_raw_data_for_arms(context.arm_names)):
                return True
            return not any(
                None not in unit.get_effect_and_se_for_source(
                    "entered",
                    metric,
                    context.arm_key,
                    context.confidence_multiplier,
                )
                for metric in DIAGNOSTIC_METRICS
            )
        return not self._has_point_estimate(unit, context)

    def _calculate_complete_effect_previews(
        self, study, unit, raw_data, context, *, update_inclusion=True
    ) -> None:
        if update_inclusion and not study.manually_excluded:
            study.include = True
        calculated = self.preview_raw_effects(
            context.data_type, context.current_effect, raw_data, context.confidence_level
        )
        if context.data_type == DIAGNOSTIC:
            if not isinstance(calculated, dict):
                raise TypeError("diagnostic effects must be a metric mapping")
            for metric, (est, lower, upper) in calculated.items():
                self._store_derived_effect_preview(unit, metric, context, est, lower, upper)
            return
        if not isinstance(calculated, tuple):
            raise TypeError("non-diagnostic effects must be a result tuple")
        (est, lower, upper), n1 = calculated
        self._store_derived_effect_preview(unit, context.current_effect, context, est, lower, upper, n1)

    def _clear_incomplete_effect_previews(self, unit, context) -> None:
        metrics = (
            DIAGNOSTIC_METRICS
            if context.data_type == DIAGNOSTIC
            else (context.current_effect,)
        )
        for metric in metrics:
            self._clear_effect_and_display_ci(unit, metric, context)

    @staticmethod
    def _has_point_estimate(unit: AnalysisUnit, context: WorkspaceEditingContext) -> bool:
        return None not in unit.get_effect_and_se_for_source(
            "entered",
            context.current_effect or "",
            context.arm_key,
            context.confidence_multiplier,
        )

    def _store_derived_effect_preview(
        self, unit: AnalysisUnit, metric: str | None, context: WorkspaceEditingContext,
        estimate: object, lower: object, upper: object, n1: object = None,
    ) -> None:
        if metric is None:
            return
        unit.set_derived_effect_preview(metric, context.arm_key, estimate, lower, upper, confidence_multiplier=context.confidence_multiplier)
        unit.calculate_display_effect_and_ci(
            metric,
            context.arm_key,
            self.display_scale_converter(context.data_type, metric, n1),
            confidence_level=context.confidence_level,
            confidence_multiplier=context.confidence_multiplier,
            source="derived_preview",
        )

    @staticmethod
    def _clear_effect_and_display_ci(unit: AnalysisUnit, metric: str | None, context: WorkspaceEditingContext) -> None:
        if metric is None:
            return
        unit.set_effect_for_source("derived_preview", metric, context.arm_key, None, None, None, None)
        unit.set_display_effect_for_source("derived_preview", metric, context.arm_key, None)
        unit.set_display_lower_for_source("derived_preview", metric, context.arm_key, None)
        unit.set_display_upper_for_source("derived_preview", metric, context.arm_key, None)
        unit.set_display_se_for_source("derived_preview", metric, context.arm_key, None)
