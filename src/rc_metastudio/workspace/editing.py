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

from collections.abc import Buffer, Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, replace
import math
import uuid
from typing import Literal, Protocol, SupportsFloat, SupportsIndex, cast

from rc_metastudio import name_validation, input_text
from rc_metastudio import r_runtime, r_operations
from rc_metastudio.analysis.catalog import (
    BINARY, BINARY_ONE_ARM_METRICS, CONTINUOUS, CONTINUOUS_ONE_ARM_METRICS, DIAGNOSTIC,
    DIAGNOSTIC_METRICS, EVENT_RATES, FACTOR, RATIO_DATA_TYPES, TIME_TO_EVENT, TYPE_TO_STR_DICT,
)
from rc_metastudio.ratio_data import RATIO_FIELDS

from rc_metastudio.project.model import Sheet, StudyRow
from rc_metastudio.project.study import AnalysisUnit, EffectEstimate
from rc_metastudio.analysis.study_selection import (
    has_study_entered_data,
    comparison_key,
    display_effect_source,
    raw_data_is_complete,
    raw_data_is_empty,
)
from rc_metastudio.analysis.validation import (
    is_an_int, is_empty,
    normal_confidence_multiplier, validate_confidence_interval_order, validate_confidence_level,
)
from rc_metastudio.workspace.columns import (
    CovariateCell, EditableField, OutcomeCell,
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

    arm_names: tuple[str, ...]
    current_effect: str | None
    data_type: int | None
    outcome_subtype: str | None
    arm_key: tuple[str, ...]
    confidence_level: float
    confidence_multiplier: float
    preserve_entered_effects_with_raw: bool = False

    @classmethod
    def for_sheet(cls, sheet: Sheet | None, metric: str | None, confidence: ConfidenceSettings):
        return cls(
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


def ratio_effect_is_editable(unit: AnalysisUnit, arm_names: Sequence[str], metric: str | None) -> bool:
    record = unit.ratio_input(arm_names)
    try:
        raw_source = record.selected_source(unit.get_raw_data_for_arms(arm_names), metric=metric or "") == "raw"
    except ValueError:
        raw_source = False
    return not raw_source and record.scale != "log"


def selected_metric(sheet: Sheet | None) -> str | None:
    if sheet is None:
        return None
    defaults = {BINARY: "OR", CONTINUOUS: "SMD", TIME_TO_EVENT: "HR", EVENT_RATES: "IRR"}
    return sheet.settings.get("metric") or sheet.settings.get("active_effect") or defaults.get(sheet.data_type)



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
    text = input_text.to_native_text(value)
    if input_text.is_blank(text):
        return 0
    try:
        return int(text)
    except ValueError:
        return int(float(text)) if is_an_int(text) else None


def _convert_effect_scale(
    value: object, data_type: object, effect: str | None,
    direction: Literal["calc.scale", "display.scale"], n1: object,
) -> object:
    if data_type in RATIO_DATA_TYPES:
        if value in (None, ""):
            return None
        if direction == "display.scale":
            return math.exp(float(cast(str | Buffer | SupportsFloat | SupportsIndex, value)))
        if not isinstance(value, (str, int, float)):
            raise TypeError("A numerical ratio is required.")
        return math.log(float(value))
    if data_type == BINARY:
        return r_operations.binary_convert_scale(value, effect, convert_to=direction, n1=n1)
    if data_type == CONTINUOUS:
        return r_operations.continuous_convert_scale(value, effect, convert_to=direction)
    if data_type == DIAGNOSTIC:
        return r_operations.diagnostic_convert_scale(value, effect, convert_to=direction)
    raise ValueError(f"Unsupported outcome type: {data_type!r}")


class WorkspaceEditingService:
    """Validate edits and calculate their workspace effects."""

    @staticmethod
    def backend_ready() -> bool:
        return r_runtime.is_ready()

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

    def display_scale_converter(
        self,
        data_type: object,
        effect: str | None,
        n1: object = None,
    ) -> Callable[[object], object]:
        if not self.backend_ready():
            return lambda value: None
        return lambda value: _convert_effect_scale(value, data_type, effect, "display.scale", n1)

    def recalculate_display_scale(
        self, studies: Sequence[StudyRow], context: WorkspaceEditingContext,
    ) -> None:
        if context.data_type in RATIO_DATA_TYPES or not self.backend_ready():
            return
        metrics = ("Sens", "Spec") if context.data_type == DIAGNOSTIC else (context.current_effect,)
        for metric in metrics:
            if metric is None:
                continue
            for study in studies:
                unit = study.analysis_unit
                raw = unit.get_raw_data_for_arms(context.arm_names) if metric == "PFT" else ()
                n1 = raw[1] if len(raw) > 1 else None
                unit.calculate_display_effect_and_ci(
                    metric, context.arm_key,
                    self.display_scale_converter(context.data_type, metric, n1),
                    confidence_level=context.confidence_level,
                    confidence_multiplier=context.confidence_multiplier,
                    check_if_necessary=True,
                    source=display_effect_source(unit, context.current_effect, context.arm_key, context.arm_names),
                )

    def apply_edit(
        self,
        sheet: Sheet | None,
        row: int,
        field: EditableField,
        context: WorkspaceEditingContext,
        value: object,
        *,
        row_order: Sequence[int] | None = None,
    ) -> CellRejection | None:
        if sheet is None or row < 0:
            return CellRejection("Select an outcome and a study row before editing.")
        if field in ("name", "year"):
            rejection, _ = self.edit_study_identities(sheet, {row: {field: value}}, row_order=row_order)
            return rejection
        if row >= len(sheet.rows):
            return CellRejection("Enter a study name first.")
        study = sheet.rows[row]
        if not study.label.strip() and not input_text.is_blank(value):
            return CellRejection("Enter a study name first.")
        if isinstance(field, (RawCell, OutcomeCell)):
            return self._edit_measurement(study, field, context, value)
        if field == "include":
            if type(value) is not bool:
                return CellRejection("Study inclusion must be checked or unchecked.")
            self.set_inclusion(study, value)
            return None
        return self._edit_covariate(study, field, value)

    def prepare_paste(
        self, sheet: Sheet, context: WorkspaceEditingContext, visible_order: Sequence[int],
        first_row: int, fields: Sequence[EditableField | None], values: Sequence[Sequence[object]],
    ) -> tuple[list[StudyRow], list[int], int]:
        """Prepare a rectangular edit before publishing anything to the workspace."""
        staged = deepcopy(sheet)
        old_count = len(staged.rows)
        indexed = [(visible_order[row] if row < len(visible_order) else row, cells)
                   for row, cells in enumerate(values, start=first_row)]
        identities: dict[int, Mapping[str, object]] = {
            row: {field: value for field, value in zip(fields, cells, strict=True) if field in ("name", "year")}
            for row, cells in indexed
        }
        rejection, skipped = self.edit_study_identities(
            staged, identities, row_order=visible_order, skip_invalid_year=True,
        )
        if rejection is not None:
            raise ValueError(rejection.message)
        for row, cells in indexed:
            skipped += self._paste_measurements(staged, row, fields, cells, context)
        self.recalculate_display_scale(staged.rows, context)
        order = [*visible_order, *range(old_count, len(staged.rows))]
        return staged.rows, order, skipped

    def _paste_measurements(
        self, sheet: Sheet, row: int, fields: Sequence[EditableField | None], cells: Sequence[object],
        context: WorkspaceEditingContext,
    ) -> int:
        skipped = 0
        for field, value in zip(fields, cells, strict=True):
            if field in ("name", "year"):
                continue
            if field is None:
                raise ValueError("This cell is read-only.")
            if self._paste_is_overwriting_ratio(sheet, row, field, context):
                raise ValueError("Calculated ratios cannot be pasted over. Click the study row number to edit its original inputs.")
            rejection = self.apply_edit(sheet, row, field, context, value)
            if rejection is not None:
                if rejection.kind != "number":
                    raise ValueError(rejection.message)
                skipped += 1
        return skipped

    def _paste_is_overwriting_ratio(
        self, sheet: Sheet, row: int, field: EditableField, context: WorkspaceEditingContext,
    ) -> bool:
        if context.data_type not in RATIO_DATA_TYPES or not isinstance(field, OutcomeCell) or field.position >= 3:
            return False
        if not self.backend_ready():
            return True
        return row < len(sheet.rows) and not ratio_effect_is_editable(
            sheet.rows[row].analysis_unit, context.arm_names, context.current_effect,
        )

    def _edit_measurement(
        self, study: StudyRow, field: RawCell | OutcomeCell, context: WorkspaceEditingContext,
        value: object,
    ) -> CellRejection | None:
        draft = replace(study, analysis_unit=study.analysis_unit.copy_for_edit())
        try:
            rejection = self._apply_measurement(draft, field, context, value)
            if rejection is not None:
                return rejection
            self._update_inclusion(draft, context)
        except Exception as error:
            edited = "raw data" if isinstance(field, RawCell) else "outcome data"
            return CellRejection(f"Could not compute study effects from the edited {edited}: {error}", kind="backend")
        study.analysis_unit.adopt_calculated_state(draft.analysis_unit)
        study.include = draft.include
        return None

    def _apply_measurement(self, study, field: RawCell | OutcomeCell, context, value):
        if isinstance(field, RawCell):
            return self._edit_raw_data(study, field.position, context, value)
        if context.data_type in RATIO_DATA_TYPES:
            return self._edit_ratio_input(study, field.position, context, value)
        return self._edit_outcome(study, field.position, context, value)

    def _edit_ratio_input(self, study, position: int, context, value):
        unit = study.analysis_unit
        field = RATIO_FIELDS[position]
        text = input_text.to_native_text(value).strip()
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
    ) -> None:
        if (
            context.data_type == DIAGNOSTIC
            or (context.preserve_entered_effects_with_raw and not raw_data_is_empty(self._raw_data(study, context)))
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
                unit = AnalysisUnit(sheet)
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
                "Diagnostic 2 × 2 table must contain at least one participant; "
                "enter at least one count greater than zero."
            )
        return None

    def _verify_outcome_data(
        self, study: StudyRow, position: int, context: WorkspaceEditingContext, number: float,
    ) -> CellRejection | None:
        unit = study.analysis_unit
        previous_display = self._previous_display_outcome(
            study, position, context, unit
        )
        raw_data = self._raw_data(study, context)
        if not context.preserve_entered_effects_with_raw and not all(is_empty(item) for item in raw_data):
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
        estimate, lower, upper = effect
        return converter(estimate), converter(lower), converter(upper)

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
        number, valid = input_text.parse_optional_decimal(value)
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
        self.update_effect_previews((study,), context, update_inclusion=True)
        return None

    def _edit_outcome(
        self, study: StudyRow, position: int, context: WorkspaceEditingContext, value: object,
    ) -> CellRejection | None:
        display_value, valid = input_text.parse_optional_decimal(value)
        if not valid:
            return CellRejection("Enter a number.", kind="number")
        if display_value is not None:
            error = self._verify_outcome_data(study, position, context, display_value)
            if error is not None:
                return error
        unit = study.analysis_unit
        metric, outcome_index = self._outcome_metric(position, context)
        if metric is None:
            return CellRejection("Choose an effect measure first.")
        n1 = self._outcome_sample_size(study, context)
        calculation_value = _convert_effect_scale(
            display_value, context.data_type, metric, "calc.scale", n1,
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
            converted = input_text.to_native_text(value)
        elif input_text.is_blank(value):
            converted = None
        else:
            converted, valid = self._number(value)
            if not valid:
                return CellRejection("Numeric covariates require numbers.", kind="number")
        study.covariate_values[field.identity] = converted
        return None

    @staticmethod
    def _number(value: object) -> tuple[float | None, bool]:
        text, valid = input_text.normalize_decimal_text(value)
        if not valid or input_text.is_blank(text):
            return None, False
        try:
            return float(text), True
        except ValueError:
            return None, False

    def update_effect_previews(
        self, studies: Sequence[StudyRow], context: WorkspaceEditingContext, *,
        update_inclusion: bool,
    ) -> None:
        pending = []
        runtime_ready = self.backend_ready()
        if not runtime_ready and not update_inclusion:
            return
        for study in studies:
            raw_data = self._raw_data(study, context)
            if self._prepare_effect_preview(study, raw_data, context, update_inclusion) and runtime_ready:
                pending.append((study, raw_data))
        if not pending or context.data_type is None:
            return
        requested = DIAGNOSTIC_METRICS if context.data_type == DIAGNOSTIC else (context.current_effect,)
        metrics = tuple(metric for metric in requested if metric is not None)
        previews = r_operations.study_effect_previews(
            [raw for _, raw in pending], TYPE_TO_STR_DICT[context.data_type], context.current_effect,
            metrics, context.confidence_level,
        )
        for (study, _), row in zip(pending, previews, strict=True):
            for metric, values in zip(metrics, row, strict=True):
                estimate, lower, upper, display_estimate, display_lower, display_upper = values
                self._store_derived_effect_preview(
                    study.analysis_unit, metric, context, estimate, lower, upper,
                    display=(display_estimate, display_lower, display_upper),
                )

    def _prepare_effect_preview(self, study, raw_data, context, update_inclusion) -> bool:
        unit = study.analysis_unit
        if context.data_type in RATIO_DATA_TYPES:
            self._clear_effect_and_display_ci(unit, context.current_effect, context)
            record = unit.ratio_input(context.arm_names)
            ready = record.ready(raw_data, metric=context.current_effect)
            if update_inclusion:
                study.include = not study.manually_excluded and ready
            return ready and record.selected_source(raw_data, metric=context.current_effect) == "raw"
        complete = self._raw_data_is_complete_for_context(raw_data, context)
        if update_inclusion and (complete or self._should_clear_inclusion(unit, context)):
            study.include = complete and not study.manually_excluded
        if not complete and not raw_data_is_empty(raw_data):
            self._clear_incomplete_effect_previews(unit, context)
        return complete


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

    @staticmethod
    def _store_derived_effect_preview(
        unit: AnalysisUnit, metric: str, context: WorkspaceEditingContext,
        estimate: object, lower: object, upper: object, *,
        display: tuple[float | None, float | None, float | None],
    ) -> None:
        unit.set_derived_effect_preview(metric, context.arm_key, estimate, lower, upper, confidence_multiplier=context.confidence_multiplier)
        standard_error = unit.get_se("derived_preview", metric, context.arm_key, context.confidence_multiplier)
        unit.set_display_effect_and_ci(
            "derived_preview", metric, context.arm_key,
            *(display if estimate is not None else (None, None, None)),
            standard_error if estimate is not None else None, confidence_level=context.confidence_level,
        )

    @staticmethod
    def _clear_effect_and_display_ci(unit: AnalysisUnit, metric: str | None, context: WorkspaceEditingContext) -> None:
        if metric is None:
            return
        unit.set_effect_for_source("derived_preview", metric, context.arm_key, None, None, None, None)
        unit.set_display_effect_and_ci(
            "derived_preview", metric, context.arm_key,
            None, None, None, None, confidence_level=None,
        )
