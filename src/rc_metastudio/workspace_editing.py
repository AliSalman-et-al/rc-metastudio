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

import math

from collections.abc import Mapping
from dataclasses import dataclass, replace
import uuid
from typing import Literal, Protocol

from rc_metastudio import name_validation, qt_text
from rc_metastudio import r_runtime, r_bridge
from rc_metastudio.analysis_catalog import RATIO_DATA_TYPES, EVENT_RATES
from rc_metastudio.ratio_data import RATIO_FIELDS

from rc_metastudio.analysis_dataset import Dataset, StudyRow
from rc_metastudio.analysis_unit import AnalysisUnit, EffectEstimate
from rc_metastudio.dataset_analysis_domain import (
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
from rc_metastudio.analysis_catalog import BINARY_ONE_ARM_METRICS, CONTINUOUS_ONE_ARM_METRICS, DIAGNOSTIC_METRICS, FACTOR
from rc_metastudio.analysis_validation import (
    is_float_convertible, is_an_int, is_empty,
    normal_confidence_multiplier, validate_confidence_interval_order, validate_confidence_level,
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
    data_type: object
    outcome_subtype: str | None
    arm_key: tuple[str, ...]
    confidence_level: float
    confidence_multiplier: float


@dataclass(slots=True)
class WorkspaceViewState:
    """Serializable selection and confidence state for the workspace."""

    current_sheet_id: SheetId | None = None
    current_effect: str | None = None
    confidence_level: float = 95.0
    confidence_multiplier: float = 1.96


@dataclass(frozen=True, slots=True)
class RawCell:
    position: int


@dataclass(frozen=True, slots=True)
class OutcomeCell:
    position: int


@dataclass(frozen=True, slots=True)
class CovariateCell:
    identity: str
    data_type: int


EditableField = Literal["name", "year", "include"] | RawCell | OutcomeCell | CovariateCell


@dataclass(frozen=True, slots=True)
class CellRejection:
    message: str
    kind: Literal["value", "number", "backend"] = "value"


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
    ) -> CellRejection | None:
        if context.sheet_id is None or row < 0:
            return CellRejection("Cannot edit that cell.")
        sheet = dataset.sheet(context.sheet_id)
        if field == "name":
            return self._edit_study_name(sheet, row, value)
        if row >= len(sheet.rows):
            return CellRejection("Enter a study name first.")
        study = sheet.rows[row]
        if field == "year":
            return self._edit_year(study, value)
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
    def _edit_study_name(sheet, row: int, value: object) -> CellRejection | None:
        try:
            name = name_validation.validate_required_name("study", value)
        except ValueError as error:
            return CellRejection(str(error))
        if any(index != row and name_validation.normalize_name(study.label) == name
               for index, study in enumerate(sheet.rows)):
            return CellRejection(f"Study name ‘{name}’ already exists. Use a unique name before pasting.")
        while len(sheet.rows) <= row:
            unit = AnalysisUnit(
                sheet,
                arm_names=[arm.name for arm in sheet.arms],
                arm_stable_ids=[arm.id for arm in sheet.arms],
            )
            sheet.rows.append(StudyRow(RowId(uuid.uuid4().hex), "", unit, include=False))
        study = sheet.rows[row]
        if not study.manually_excluded and not has_study_entered_data(study):
            study.include = True
        study.label = name
        return None

    @staticmethod
    def _edit_year(study: StudyRow, value: object) -> CellRejection | None:
        text = qt_text.to_native_text(value)
        if not qt_text.is_blank(text) and not is_an_int(text):
            return CellRejection("Enter the year as a whole number, for example 2019.", kind="number")
        try:
            study.year = int(float(text)) if not qt_text.is_blank(text) else 0
        except (TypeError, ValueError):
            return CellRejection("Enter the year as a whole number, for example 2019.", kind="number")
        return None

    def _raw_data(self, study: StudyRow, context: WorkspaceEditingContext):
        return study.analysis_unit.get_raw_data_for_arms(
            context.arm_names
        )

    def _verify_raw_data(
        self, study: StudyRow, position: int, context: WorkspaceEditingContext, value: object
    ) -> CellRejection | None:
        text, numeric_valid = qt_text.normalize_decimal_text(value)
        if not numeric_valid:
            return CellRejection("Enter a number.", kind="number")
        if qt_text.is_blank(text):
            return None
        if not is_float_convertible(text):
            return CellRejection("Enter a number.", kind="number")
        if context.data_type == EVENT_RATES:
            number = float(text)
            if not math.isfinite(number):
                return CellRejection("Raw inputs must be finite.")
            if position % 2 == 0 and (number < 0 or not number.is_integer()):
                return CellRejection("Events must be nonnegative integers.", kind="number")
            if position % 2 == 1 and number <= 0:
                return CellRejection("Person-time must be positive.")
            return None
        error = self._verify_raw_number(text, context.data_type)
        if error:
            return error
        raw_data = self._raw_data(study, context)
        return self._verify_raw_bounds(text, raw_data, position, context.data_type)

    @staticmethod
    def _verify_raw_number(text: str, data_type: object) -> CellRejection | None:
        if data_type not in (BINARY, DIAGNOSTIC):
            return None
        if not is_an_int(text):
            return CellRejection("Counts must be whole numbers.", kind="number")
        if int(float(text)) < 0:
            return CellRejection("Counts cannot be negative.")
        return None

    @staticmethod
    def _verify_raw_bounds(
        text: str, raw_data, position: int, data_type: object
    ) -> CellRejection | None:
        if data_type == BINARY:
            return WorkspaceEditingService._verify_binary_bounds(text, raw_data, position)
        if data_type == CONTINUOUS:
            return WorkspaceEditingService._verify_continuous_bounds(text, position)
        if data_type == DIAGNOSTIC:
            return WorkspaceEditingService._verify_diagnostic_bounds(
                text, raw_data, position
            )
        return None

    @staticmethod
    def _verify_binary_bounds(text, raw_data, position: int) -> CellRejection | None:
        if position in (0, 2):
            sample = raw_data[position + 1]
            if is_an_int(sample) and int(float(text)) > int(float(sample)):
                return CellRejection("Events cannot exceed the arm total.")
        if position in (1, 3):
            event = raw_data[position - 1]
            if is_an_int(event) and int(float(text)) < int(float(event)):
                return CellRejection("Events cannot exceed the arm total.")
        return None

    @staticmethod
    def _verify_continuous_bounds(text, position: int) -> CellRejection | None:
        if float(text) > 0:
            return None
        if position in (0, 3):
            return CellRejection("Participants must be a positive whole number.", kind="number")
        if position in (2, 5):
            return CellRejection("Standard deviation must be greater than zero.")
        return None

    @staticmethod
    def _verify_diagnostic_bounds(text, raw_data, position: int) -> CellRejection | None:
        """Reject an empty diagnostic study while allowing individual zero cells."""
        candidate = list(raw_data)
        if position >= len(candidate):
            return None
        candidate[position] = text
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
        self, study: StudyRow, position: int, context: WorkspaceEditingContext, value: object, allow_raw_and_entered: bool
    ) -> CellRejection | None:
        text, numeric_valid = qt_text.normalize_decimal_text(value)
        if not numeric_valid:
            return CellRejection("Enter a number.", kind="number")
        if qt_text.is_blank(text):
            return None
        if not is_float_convertible(text):
            return CellRejection("Enter a number.", kind="number")
        unit = study.analysis_unit
        previous_display = self._previous_display_outcome(
            study, position, context, unit
        )
        raw_data = self._raw_data(study, context)
        if not allow_raw_and_entered and not all(is_empty(item) for item in raw_data):
            error = self._verify_raw_override(text, previous_display, position)
            if error:
                return error
        return self._verify_outcome_value(text, previous_display, position, context)

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
    def _verify_raw_override(text, previous_display, position) -> CellRejection | None:
        outcome_index = position % 3
        previous = previous_display[outcome_index]
        delta = abs(float(text) - previous) if previous is not None else float("-inf")
        if delta > 10e-6:
            return CellRejection("You have already entered raw data for this study. If you want to enter the outcome directly, delete the raw data first.")
        return None

    @staticmethod
    def _verify_outcome_value(text, previous_display, position, context) -> CellRejection | None:
        number = float(text)
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
        error = self._verify_raw_data(study, position, context, value)
        if error:
            return error
        unit = study.analysis_unit
        per_group = len(unit.get_raw_data_for_arm(context.arm_names[0]))
        group = context.arm_names[position // per_group]
        unit.get_raw_data_for_arm(group)[position % per_group] = (
            "" if qt_text.is_blank(value) else float(qt_text.normalize_decimal_text(value)[0])
        )
        self.update_effect_previews_if_possible(study, context)
        return None

    def _edit_outcome(
        self, study: StudyRow, position: int, context: WorkspaceEditingContext, value: object, allow_raw_and_entered: bool
    ) -> CellRejection | None:
        error = self._verify_outcome_data(study, position, context, value, allow_raw_and_entered)
        if error:
            return error
        unit = study.analysis_unit
        normalized_value, _ = qt_text.normalize_decimal_text(value)
        display_value = None if qt_text.is_blank(value) else float(normalized_value)
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
