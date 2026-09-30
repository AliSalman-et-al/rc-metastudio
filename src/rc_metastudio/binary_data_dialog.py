# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Binary outcome data entry dialog."""

import copy
from contextlib import ExitStack
from functools import partial
from typing import TYPE_CHECKING, TypeGuard, cast

from PyQt6.QtCore import QEvent, QObject, QSignalBlocker, QTimer, Qt
from PyQt6.QtGui import QAction, QBrush, QColor, QKeySequence, QPalette
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QHeaderView,
    QSizePolicy,
    QStyle,
    QTableWidgetItem,
    QWidget,
    QWIDGETSIZE_MAX,
)

from rc_metastudio import tabular_data
from rc_metastudio.calculator_service import (
    BinaryImputationOption,
    CalculatorService,
    execute_calculator_calls,
)
from rc_metastudio.calculator_dialog_worker import install_calculator_dialog_worker
from rc_metastudio.meta_globals import (
    BINARY_METRIC_NAMES,
    BINARY_ONE_ARM_METRICS,
    BINARY_TWO_ARM_METRICS,
    EMPTY_VALS,
    is_nan,
    is_empty,
)
from rc_metastudio import calculator_routines as calc_fncs

from rc_metastudio import app_error_handler
from rc_metastudio import adaptive_window
from rc_metastudio.runtime_types import required

if TYPE_CHECKING:
    import ui_binary_back_calculation_dialog as _ui_binary_back_calculation_dialog
    import ui_binary_data_dialog as _ui_binary_data_dialog
else:
    from rc_metastudio.forms import (
        ui_binary_back_calculation_dialog as _ui_binary_back_calculation_dialog,
    )
    from rc_metastudio.forms import ui_binary_data_dialog as _ui_binary_data_dialog

# this is the maximum size of a residual that we're willing to accept
# when computing 2x2 data
THRESHOLD = 1e-5
BINARY_RAW_COUNT_CELLS = frozenset(((0, 0), (0, 1), (1, 0), (1, 1)))
BINARY_ARM_TOTAL_CELLS = frozenset(((0, 2), (1, 2)))


def _calculator_results_by_id(value: object) -> dict[str, object]:
    if not isinstance(value, list):
        raise ValueError("calculator returned an invalid call result list")
    results: dict[str, object] = {}
    for item in value:
        if not _is_string_object_dict(item):
            raise ValueError("calculator returned an invalid call result")
        call_id = item.get("id")
        if not isinstance(call_id, str):
            raise ValueError("calculator returned a result without an identity")
        results[call_id] = item.get("result")
    return results


def _is_string_object_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


class BinaryDataDialog(QDialog, _ui_binary_data_dialog.Ui_BinaryDataDialog):
    def __init__(
        self,
        analysis_unit,
        current_groups,
        group_comparison,
        current_effect,
        confidence_level=None,
        calculator: CalculatorService | None = None,
        worker_client=None,
        parent=None,
    ):
        super(BinaryDataDialog, self).__init__(parent)
        self.setupUi(self)
        self.study_context_label.hide()
        self.calculated_values_group.hide()
        self._pending_back_calculation: tuple[
            tuple[int, int, int], tuple[int, int, int]
        ] | None = None
        self._prepared_back_calculation = None
        self._configure_raw_data_table()
        self._configure_focus_revelation()
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        self._initialize_calculator(calculator, worker_client, confidence_level)
        self._setup_signals_and_slots()
        self._initialize_study_fields(
            analysis_unit, current_groups, group_comparison, current_effect
        )
        self._initialize_form_state()
        self._initialize_data_view()
        self._configure_apply_button()
        self._request_content_refit()
        if self._calculator_async:
            self._request_calculator(
                [
                    {
                        "id": "multiplier",
                        "operation": "get_confidence_multiplier",
                        "args": {"confidence_level": self.confidence_level},
                    }
                ],
                self._calculator_initialized,
            )

    def _initialize_calculator(self, calculator, worker_client, confidence_level):
        if confidence_level is None:
            raise ValueError("Confidence level must be specified")
        self.confidence_level = confidence_level
        self.worker_client = worker_client
        self._calculator_async = worker_client is not None and calculator is None
        if self._calculator_async:
            calculator_service = None
        elif calculator is not None:
            calculator_service = calculator
        else:
            calculator_service = CalculatorService()
        self.calculator = calculator_service
        self._calculator_requests = None
        self._worker_status_label = None
        if self._calculator_async:
            self._worker_status_label, self._calculator_requests = (
                install_calculator_dialog_worker(self, worker_client)
            )
        self.confidence_multiplier = (
            calculator_service.get_confidence_multiplier(self.confidence_level)
            if calculator_service is not None
            else None
        )
        self.current_item_data: int | None = None

    def _initialize_study_fields(
        self, analysis_unit, current_groups, group_comparison, current_effect
    ):
        self.analysis_unit = analysis_unit
        self.current_groups = current_groups
        self.group_comparison = group_comparison
        self.current_effect = current_effect
        self.entry_widgets = [
            self.raw_data_table,
            self.lower_text_box,
            self.upper_text_box,
            self.effect_text_box,
        ]
        self.text_boxes = [
            self.lower_text_box,
            self.upper_text_box,
            self.effect_text_box,
        ]
        if self._calculator_async:
            for text_box in self.text_boxes:
                text_box.textChanged.connect(self._invalidate_calculator_responses)

    def _initialize_form_state(self):
        self.ci_label.setText(
            "{0:.1f}% Confidence Interval".format(self.confidence_level)
        )
        self._configure_readable_ci_label()
        self.initialize_form()  # initialize all cell to empty items
        self.setup_back_calculation_feedback()
        self._field_history = calc_fncs.TransientEditHistory()

    def _initialize_data_view(self):
        self._update_raw_data()  # analysis_unit --> table
        self._populate_effect_data()  # make combo boxes for effects
        if not self._calculator_async:
            self.set_current_effect()  # fill in current effect data in line edits
        self._update_data_table()  # fill in 2x2
        self._fit_raw_data_columns_for_first_display()
        if not self._calculator_async:
            self.update_back_calculation_button()
        self._set_content_preferred_width()
        self.raw_data_table.setCurrentCell(0, 0)
        self.raw_data_table.setFocus()

    def _configure_apply_button(self):
        apply_button = required(
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok),
            "binary calculator OK button",
        )
        apply_button.setText("Apply to study")
        apply_button.setAccessibleName("Apply study data changes")
        apply_button.setDefault(True)
        if self._calculator_async:
            for widget in self.entry_widgets:
                widget.setEnabled(False)
            apply_button.setEnabled(False)

    def _request_calculator(self, calls, on_result, on_error=None):
        if self._calculator_requests is not None:
            return self._calculator_requests.submit(calls, on_result, on_error)
        result = execute_calculator_calls(calls, service=self.calculator)
        on_result(_calculator_results_by_id(result.get("calls")))
        return 0

    def _invalidate_calculator_responses(self, *_args):
        if self._calculator_requests is not None:
            self._calculator_requests.invalidate()

    def _synchronous_calculator(self) -> CalculatorService:
        if self.calculator is None:
            raise RuntimeError("Synchronous calculator service is unavailable.")
        return self.calculator

    def _calculator_initialized(self, results):
        self.confidence_multiplier = float(results["multiplier"])
        for widget in self.entry_widgets:
            widget.setEnabled(True)
        apply_button = required(
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok),
            "binary calculator OK button",
        )
        apply_button.setEnabled(True)
        self._update_raw_data()
        self._update_data_table()
        if not self.update_effect_from_raw_data():
            self.set_current_effect(after=self.update_back_calculation_button)
        self.raw_data_table.setFocus()

    def _configure_raw_data_table(self):
        # The adaptive contract sizes the dialog; the scroll area owns overflow.
        self.content_scroll.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding
        )
        table = self.raw_data_table
        table.setHorizontalHeaderLabels(["Event", "No Event", "Total"])
        table.setVerticalHeaderLabels(["Group 1", "Group 2", "Total"])
        horizontal_header = required(table.horizontalHeader(), "binary table header")
        vertical_header = required(table.verticalHeader(), "binary row header")
        horizontal_header.setVisible(True)
        vertical_header.setVisible(True)
        horizontal_header.setHighlightSections(False)
        vertical_header.setHighlightSections(False)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # layout-audit: allow=compact-table-overflow; reason=compact table keeps rows visible and owns excess overflow
        table.setMinimumWidth(0)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        horizontal_header.setStretchLastSection(False)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        table_height = (
            horizontal_header.sizeHint().height()
            + sum(table.rowHeight(row) for row in range(table.rowCount()))
            + 2 * table.frameWidth()
        )
        # layout-audit: allow=compact-table-overflow; reason=compact table keeps rows visible and owns excess overflow
        table.setMinimumHeight(table_height)
        # layout-audit: allow=compact-table-overflow; reason=compact table keeps rows visible and owns excess overflow
        table.setMaximumHeight(table_height)
        for label in (
            self.event_lbl_3,
            self.label_18,
            self.label_19,
            self.label_20,
            self.label_21,
            self.label_22,
        ):
            label.setVisible(False)

    def _configure_readable_ci_label(self):
        """Keep the confidence heading on one line at normal scaling."""
        self.ci_label.setWordWrap(False)
        # layout-audit: allow=content-overflow-control; reason=confidence heading remains readable inside the scrollable dialog content
        self.ci_label.setMinimumWidth(self.ci_label.sizeHint().width())

    def _set_content_preferred_width(self):
        """Give dense content room before the outer policy applies its cap."""
        layout = required(self.content_layout, "binary content layout")
        layout.activate()
        content_width = layout.sizeHint().width()
        content_width = max(content_width, self.raw_data_table.minimumWidth() + 44)
        margins = required(self.layout(), "binary dialog layout").contentsMargins()
        scrollbar = required(
            self.content_scroll.verticalScrollBar(), "binary content scrollbar"
        )
        preferred_width = (
            content_width
            + margins.left()
            + margins.right()
            + 2 * self.content_scroll.frameWidth()
            + scrollbar.sizeHint().width()
        )
        minimum_width = (
            self.clear_button.sizeHint().width()
            + self.back_calculate_button.sizeHint().width()
            + 40
            + margins.left()
            + margins.right()
            + 2 * self.content_scroll.frameWidth()
            + scrollbar.sizeHint().width()
        )
        adaptive_window.set_content_preferred_width(
            self, minimum_width, preferred_width
        )

    def _fit_raw_data_columns_for_first_display(self):
        """Choose sensible initial widths, then leave sections user-adjustable."""
        for column in range(self.raw_data_table.columnCount()):
            self._grow_raw_data_column_to_contents(column)
        header = required(self.raw_data_table.horizontalHeader(), "binary table header")
        table_width = sum(
            header.sectionSize(column)
            for column in range(self.raw_data_table.columnCount())
        )
        table_width += required(
            self.raw_data_table.verticalHeader(), "binary row header"
        ).sizeHint().width()
        table_width += 2 * self.raw_data_table.frameWidth()
        # layout-audit: allow=compact-table-overflow; reason=wide numeric cells keep their contents and the table owns horizontal overflow
        self.raw_data_table.setMinimumWidth(
            max(self.raw_data_table.minimumWidth(), table_width)
        )

    def _grow_raw_data_column_to_contents(self, column):
        table = self.raw_data_table
        header = required(table.horizontalHeader(), "binary table header")
        required_width = max(
            header.sectionSizeHint(column),
            table.sizeHintForColumn(column),
        )
        if required_width > table.columnWidth(column):
            header.resizeSection(column, required_width)

    def _configure_focus_revelation(self):
        """Reveal focused calculator controls within this dialog's overflow."""
        for widget in self.content_widget.findChildren(QWidget):
            widget.installEventFilter(self)

    def eventFilter(  # ty: ignore[invalid-method-override] -- PyQt6's QDialog stub rejects this runtime-supported QObject override.
        self, watched: QObject | None, event: QEvent | None
    ) -> bool:
        if (
            isinstance(watched, QWidget)
            and event is not None
            and event.type() == QEvent.Type.FocusIn
            and self.content_widget.isAncestorOf(watched)
        ):
            self.content_scroll.ensureWidgetVisible(watched)
        return super(BinaryDataDialog, self).eventFilter(watched, event)

    def _request_content_refit(self):
        controller = getattr(self, "_layout_controller", None)
        if controller is not None:
            controller.request_content_refit()

    def initialize_form(self):
        """Initialize every input field to an empty value."""
        nrows = self.raw_data_table.rowCount()
        ncols = self.raw_data_table.columnCount()

        for row in range(nrows):
            for col in range(ncols):
                self._set_val(row, col, None)

        for txt_box in self.text_boxes:
            txt_box.setText("")

    def update_back_calculation_button(self, engage=False):
        if not engage:
            self._clear_back_calculation_preview()
        if not self._prepare_back_calculation_button():
            return None
        if self._calculator_async:
            if self.confidence_multiplier is None:
                self.back_calculate_button.setEnabled(False)
                return None
            if self._prepared_back_calculation is None:
                self._request_binary_back_calculation(engage)
                return None
            bin_data, imputed = self._prepared_back_calculation
            self._prepared_back_calculation = None
        else:
            bin_data = self._build_back_calculation_args()
            imputed = self._synchronous_calculator().impute_binary_data(
                bin_data.copy()
            )

        # Leave if nothing was imputed
        if "FAIL" in imputed:
            self.back_calculate_button.setEnabled(False)
            return None

        self.back_calculate_button.setEnabled(
            self._back_calculation_adds_missing_counts(bin_data, imputed)
        )
        if not engage:
            return None
        self._show_back_calculation_preview(imputed)

    def _clear_back_calculation_preview(self):
        self._pending_back_calculation = None
        self.calculated_values_group.hide()
        self.calculated_values_label.clear()

    def _prepare_back_calculation_button(self):
        supported = self.current_effect in ("OR", "RR", "RD")
        self.back_calculate_button.setVisible(supported)
        self._request_content_refit()
        if not supported:
            self._clear_back_calculation_preview()
        return supported

    def _build_back_calculation_args(self):
        entered_values = self.analysis_unit.get_effect_and_ci_for_source(
            "entered",
            self.current_effect,
            self.group_comparison,
            self.confidence_multiplier,
        )
        display_values = [
            self._synchronous_calculator().binary_convert_scale(
                value, self.current_effect, convert_to="display.scale"
            )
            for value in entered_values
        ]
        args = {"metric": str(self.current_effect)}
        for key, value in zip(("estimate", "lower", "upper"), display_values):
            try:
                args[key] = float(value)
            except (TypeError, ValueError):
                args[key] = None
        args["conf.level"] = self.confidence_level
        for key, row, column in (
            ("Ev_A", 0, 0),
            ("N_A", 0, 2),
            ("Ev_B", 1, 0),
            ("N_B", 1, 2),
        ):
            args[key] = self._table_count_as_float(row, column)
        return args

    def _table_count_as_float(self, row, column):
        return float(self._get_int(row, column)) if not self._is_empty(row, column) else None

    def _back_calculation_adds_missing_counts(self, bin_data, imputed):
        old_counts = tuple(
            bin_data[key] for key in ("Ev_A", "N_A", "Ev_B", "N_B")
        )
        option1 = self._rounded_imputed_counts(imputed["op1"])
        if not self._option_adds_missing_count(old_counts, option1):
            return False
        if "op2" not in imputed:
            return True
        option2 = self._rounded_imputed_counts(imputed["op2"])
        return self._option_adds_missing_count(old_counts, option2)

    @staticmethod
    def _rounded_imputed_counts(option):
        return tuple(int(round(option[key])) for key in ("a", "b", "c", "d"))

    @staticmethod
    def _option_adds_missing_count(old_counts, new_counts):
        return any(
            old in EMPTY_VALS and new not in EMPTY_VALS
            for old, new in zip(old_counts, new_counts)
        )

    def _show_back_calculation_preview(self, imputed):
        try:
            choice = self._choose_back_calculation_option(imputed)
            if choice is None:
                return
            candidate = self._candidate_from_imputation(imputed[choice])
            changes = self._back_calculation_changes(candidate)
            if not changes:
                self._clear_back_calculation_preview()
                return
            self._pending_back_calculation = candidate
            assumption = self._back_calculation_assumption(choice, len(imputed))
            self.calculated_values_label.setText(
                calc_fncs.format_calculated_values_preview(assumption, changes)
            )
            self.calculated_values_group.show()
            self._request_content_refit()
        except Exception as error:
            self._pending_back_calculation = None
            self.calculated_values_group.hide()
            self._mark_table_invalid(f"Could not prepare calculated values: {error}")
            self.back_calculate_button.setFocus()

    def _choose_back_calculation_option(self, imputed):
        if len(imputed) == 1:
            return "op1"
        dialog = BinaryBackCalculationDialog(imputed, parent=self)
        if not dialog.exec():
            return None
        return dialog.get_choice()

    @staticmethod
    def _candidate_from_imputation(option):
        counts = BinaryDataDialog._rounded_imputed_counts(
            cast(BinaryImputationOption, option)
        )
        group_1_events, group_1_total, group_2_events, group_2_total = counts
        return (
            (
                group_1_events,
                group_1_total - group_1_events,
                group_1_total,
            ),
            (
                group_2_events,
                group_2_total - group_2_events,
                group_2_total,
            ),
        )

    def _back_calculation_changes(self, candidate):
        changes = []
        fields = ("events", "non-events", "total")
        for row, group in enumerate(self.current_groups[:2]):
            for column, field_name in enumerate(fields):
                old_value = self._get_int(row, column)
                new_value = candidate[row][column]
                if old_value != new_value:
                    changes.append((f"{group} {field_name}", old_value, new_value))
        return changes

    def _back_calculation_assumption(self, choice, option_count):
        assumption = (
            f"RCMetaR calculated these counts from the entered {self.current_effect} "
            f"estimate and confidence interval at {self.confidence_level:g}% confidence."
        )
        if option_count > 1:
            alternatives = option_count - 1
            assumption += (
                f" Previewing {choice}; {alternatives} alternative compatible "
                f"count set{'s' if alternatives != 1 else ''} available."
            )
        return assumption

    def _request_binary_back_calculation(self, engage):
        estimate = self.analysis_unit.get_effect_and_ci_for_source(
            "entered",
            self.current_effect,
            self.group_comparison,
            self.confidence_multiplier,
        )
        calls = [
            {
                "id": key,
                "operation": "binary_convert_scale",
                "args": {
                    "x": value,
                    "metric_name": self.current_effect,
                    "convert_to": "display.scale",
                },
            }
            for key, value in zip(("estimate", "lower", "upper"), estimate)
        ]

        def impute(results):
            data = {
                "metric": str(self.current_effect),
                "conf.level": self.confidence_level,
                "Ev_A": float(self._get_int(0, 0)) if not self._is_empty(0, 0) else None,
                "N_A": float(self._get_int(0, 2)) if not self._is_empty(0, 2) else None,
                "Ev_B": float(self._get_int(1, 0)) if not self._is_empty(1, 0) else None,
                "N_B": float(self._get_int(1, 2)) if not self._is_empty(1, 2) else None,
            }
            for key in ("estimate", "lower", "upper"):
                try:
                    data[key] = float(results[key])
                except (TypeError, ValueError):
                    data[key] = None

            self._request_calculator(
                [
                    {
                        "id": "imputed",
                        "operation": "impute_binary_data",
                        "args": {"binary_data": data},
                    }
                ],
                lambda imputed_results: self._binary_back_calculation_ready(
                    engage, data, imputed_results["imputed"]
                ),
            )

        self._request_calculator(calls, impute)

    def _binary_back_calculation_ready(self, engage, data, imputed):
        self._prepared_back_calculation = (data, imputed)
        self.update_back_calculation_button(engage=engage)

    def accept(self):
        """Publish entered and previewed values only on explicit application."""
        candidate = self._pending_back_calculation
        if candidate is not None and not self._apply_back_calculation(candidate):
            return
        super().accept()

    def _apply_back_calculation(self, candidate):
        if not self._validate_back_calculation_candidate(candidate):
            return False

        old_analysis_unit, old_table = self._save_analysis_unit_and_table_state(
            table=self.raw_data_table,
            analysis_unit=self.analysis_unit,
            use_old_value=False,
        )
        try:
            self._publish_back_calculation_candidate(candidate)
        except Exception as error:
            self.restore_analysis_unit_and_table(old_analysis_unit, old_table)
            self._mark_table_invalid(f"Could not apply calculated values: {error}")
            self.back_calculate_button.setFocus()
            return False

        self._record_back_calculation_edit(old_analysis_unit, old_table)
        self._pending_back_calculation = None
        self.calculated_values_group.hide()
        return True

    def _validate_back_calculation_candidate(self, candidate):
        for row, values in enumerate(candidate):
            for column, value in enumerate(values):
                error = self._cell_data_not_valid(str(value))
                if error:
                    self._mark_table_invalid(error)
                    self.raw_data_table.setCurrentCell(row, column)
                    self.raw_data_table.setFocus()
                    return False
        return True

    def _publish_back_calculation_candidate(self, candidate):
        for column in range(3):
            self.clear_column(column)
        with QSignalBlocker(self.raw_data_table):
            for row, values in enumerate(candidate):
                for column, value in enumerate(values):
                    if column < 2:
                        self._set_val(row, column, value)
        self._update_data_table()
        self._update_analysis_unit()

    def _record_back_calculation_edit(self, old_analysis_unit, old_table):
        new_analysis_unit, new_table = self._save_analysis_unit_and_table_state(
            table=self.raw_data_table,
            analysis_unit=self.analysis_unit,
            use_old_value=False,
        )
        calc_fncs.push_field_edit(
            self._field_history,
            owner=self,
            restore_state=self.restore_analysis_unit_and_table,
            old_state=(old_analysis_unit, old_table),
            new_state=(new_analysis_unit, new_table),
            description="Apply calculated binary values",
            refresh_on_initial_redo=False,
        )

    def setup_back_calculation_feedback(self):
        inconsistency_palette = QPalette()
        inconsistency_palette.setColor(
            QPalette.ColorRole.WindowText, Qt.GlobalColor.red
        )
        self.inconsistencyLabel.setPalette(inconsistency_palette)
        self.inconsistencyLabel.setVisible(False)
        self._request_content_refit()

    def _mark_table_consistent(self):
        self.inconsistencyLabel.setVisible(False)
        required(
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok),
            "binary calculator OK button",
        ).setEnabled(True)
        self._request_content_refit()

    def _mark_table_invalid(self, message):
        self.inconsistencyLabel.setText(str(message))
        self.inconsistencyLabel.setVisible(True)
        required(
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok),
            "binary calculator OK button",
        ).setEnabled(False)
        self._request_content_refit()
        self.inconsistencyLabel.updateGeometry()
        content_layout = self.content_widget.layout()
        if content_layout is not None:
            content_layout.activate()
        self._reveal_validation_message()
        QTimer.singleShot(
            0,
            self._reveal_validation_message,
        )

    def _reveal_validation_message(self):
        self.content_scroll.ensureWidgetVisible(self.inconsistencyLabel, 12, 12)
        center = self.inconsistencyLabel.mapTo(
            self.content_widget, self.inconsistencyLabel.rect().center()
        )
        self.content_scroll.ensureVisible(center.x(), center.y(), 12, 12)

    def _raw_count_cell_is_editable(self, row, col):
        if (row, col) in BINARY_RAW_COUNT_CELLS:
            return True
        if (row, col) in BINARY_ARM_TOTAL_CELLS:
            return any(self._is_empty(row, inner_col) for inner_col in (0, 1))
        return False

    def _refresh_raw_data_editability(self):
        with QSignalBlocker(self.raw_data_table):
            for row in range(self.raw_data_table.rowCount()):
                for col in range(self.raw_data_table.columnCount()):
                    calc_fncs.set_table_item_editable(
                        self.raw_data_table.item(row, col),
                        self._raw_count_cell_is_editable(row, col),
                    )

    def on_raw_data_table_currentCellChanged(
        self, currentRow, currentColumn, previousRow, previousColumn
    ):
        self.current_item_data = self._get_int(currentRow, currentColumn)

    def _setup_signals_and_slots(self):
        self.raw_data_table.cellChanged.connect(
            app_error_handler.safe_slot(self.cell_changed, parent=self)
        )
        self.raw_data_table.currentCellChanged.connect(
            app_error_handler.safe_slot(
                self.on_raw_data_table_currentCellChanged, parent=self
            )
        )

        self.effect_combo_box.currentTextChanged.connect(
            app_error_handler.safe_slot(
                lambda _text: self.effect_changed(), parent=self
            )
        )
        self.clear_button.clicked.connect(
            app_error_handler.safe_slot(self.clear_form, parent=self)
        )
        self.back_calculate_button.clicked.connect(
            app_error_handler.safe_slot(
                lambda: self.update_back_calculation_button(engage=True), parent=self
            )
        )

        self.effect_text_box.editingFinished.connect(
            app_error_handler.safe_slot(lambda: self.val_changed("est"), parent=self)
        )
        self.lower_text_box.editingFinished.connect(
            app_error_handler.safe_slot(lambda: self.val_changed("lower"), parent=self)
        )
        self.upper_text_box.editingFinished.connect(
            app_error_handler.safe_slot(lambda: self.val_changed("upper"), parent=self)
        )

        undo = QAction(self)
        redo = QAction(self)
        undo.setShortcut(QKeySequence.StandardKey.Undo)
        redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.addAction(undo)
        self.addAction(redo)
        undo.triggered.connect(
            app_error_handler.safe_slot(lambda _checked=False: self.undo(), parent=self)
        )
        redo.triggered.connect(
            app_error_handler.safe_slot(lambda _checked=False: self.redo(), parent=self)
        )

    def _populate_effect_data(self):
        available_effects = {str(effect) for effect in self.analysis_unit.get_effect_names()}
        metric_family = (
            BINARY_ONE_ARM_METRICS
            if self.current_effect in BINARY_ONE_ARM_METRICS
            else BINARY_TWO_ARM_METRICS
        )
        q_effects = [effect for effect in metric_family if effect in available_effects]
        if self.current_effect not in q_effects:
            q_effects.append(str(self.current_effect))
        with QSignalBlocker(self.effect_combo_box):
            self.effect_combo_box.clear()
            for effect in q_effects:
                self.effect_combo_box.addItem(
                    self._effect_display_label(effect), userData=effect
                )
            # layout-audit: allow=content-overflow-control; reason=required content may consume available layout width
            self.effect_combo_box.setMinimumWidth(0)
            # layout-audit: allow=content-overflow-control; reason=required content may consume available layout width
            self.effect_combo_box.setMaximumWidth(QWIDGETSIZE_MAX)
            self.effect_combo_box.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            self.effect_combo_box.setCurrentIndex(
                q_effects.index(str(self.current_effect))
            )
        self._update_effect_choice_accessibility()
        self._request_content_refit()

    def _update_effect_choice_accessibility(self):
        combo = self.effect_combo_box
        if combo.count() == 0:
            return
        full_text = combo.currentText()
        combo.setToolTip(full_text)
        text_width = max(
            combo.fontMetrics().horizontalAdvance(combo.itemText(index))
            for index in range(combo.count())
        )
        scrollbar_width = required(
            combo.style(), "binary metric combo style"
        ).pixelMetric(QStyle.PixelMetric.PM_ScrollBarExtent, None, combo)
        # layout-audit: allow=bounded-native-popup; reason=native choice popup is bounded to the owning screen
        required(combo.view(), "binary metric combo popup").setMinimumWidth(
            text_width + scrollbar_width + 24
        )

    def get_effect_names(self):
        return self.analysis_unit.get_effect_names()

    def _effect_display_label(self, effect):
        return "%s (%s)" % (BINARY_METRIC_NAMES.get(effect, effect), effect)

    def _selected_effect(self):
        effect = self.effect_combo_box.currentData()
        if effect is None:
            effect = self.effect_combo_box.currentText()
        return str(effect)

    def set_current_effect(self, *, after=None):
        """Populate fields from a meta-analysis unit."""
        if self.confidence_multiplier is None:
            return
        txt_boxes = dict(
            effect=self.effect_text_box,
            lower=self.lower_text_box,
            upper=self.upper_text_box,
        )
        source = calc_fncs.calculator_effect_source(
            self.analysis_unit,
            self.current_groups,
            self.current_effect,
            self.group_comparison,
            self.confidence_multiplier,
        )
        self.groupBox.setTitle(
            "Calculated effect"
            if source == "derived_preview"
            else "Entered effect"
        )
        if self._calculator_async:
            values = self.analysis_unit.get_effect_and_ci_for_source(
                source,
                self.current_effect,
                self.group_comparison,
                self.confidence_multiplier,
            )
            calls = [
                {
                    "id": key,
                    "operation": "binary_convert_scale",
                    "args": {
                        "x": value,
                        "metric_name": self.current_effect,
                        "convert_to": "display.scale",
                    },
                }
                for key, value in zip(("effect", "lower", "upper"), values)
            ]

            def rendered(results):
                calc_fncs.set_display_effect_values(
                    txt_boxes,
                    self.current_effect,
                    "binary",
                    (results["effect"], results["lower"], results["upper"]),
                )
                self.change_row_color_according_to_metric()
                if after is not None:
                    after()

            self._request_calculator(calls, rendered)
            return
        calc_fncs.set_current_effect_from_value(
            analysis_unit=self.analysis_unit,
            txt_boxes=txt_boxes,
            current_effect=self.current_effect,
            group_comparison=self.group_comparison,
            data_type="binary",
            confidence_multiplier=self.confidence_multiplier,
            source=source,
        )

        self.change_row_color_according_to_metric()
        if after is not None:
            after()

    def change_row_color_according_to_metric(self):
        # Change color of bottom rows of table according one or two-arm metric
        current_effect_is_one_arm = self.current_effect in BINARY_ONE_ARM_METRICS
        for row in (1, 2):
            for col in range(3):
                item = self.raw_data_table.item(row, col)
                item = required(item, f"binary table cell ({row}, {col})")
                if current_effect_is_one_arm:
                    item.setBackground(QBrush(QColor(Qt.GlobalColor.gray)))
                else:
                    text = item.text()
                    with QSignalBlocker(self.raw_data_table):
                        popped_item = self.raw_data_table.takeItem(row, col)
                    del popped_item
                    self._set_val(row, col, text)

    def effect_changed(self):
        """Called when a new effect is selected in the combo box"""
        self.current_effect = self._selected_effect()
        self.group_comparison = self.get_current_group_comparison()

        self._update_effect_choice_accessibility()
        if self._calculator_async:
            if not self.update_effect_from_raw_data():
                self.set_current_effect(after=self.update_back_calculation_button)
            return

        self.update_effect_from_raw_data()
        self.set_current_effect()
        self.update_back_calculation_button()

    def _text_box_value_is_between_bounds(self, val_str, new_text):
        if is_empty(new_text):
            return True, ""
        ci_param = {"est": "est", "lower": "low", "upper": "high"}.get(val_str)
        if ci_param is None:
            return True, ""
        if self._calculator_async:
            try:
                display_value = calc_fncs.numeric_value(new_text)
            except ValueError:
                QMessageBox.warning(self, "Warning", "Must be numeric!")
                return False, False
            values = {
                "est": self.effect_text_box.text(),
                "low": self.lower_text_box.text(),
                "high": self.upper_text_box.text(),
            }
            values[ci_param] = new_text
            good, message = calc_fncs.between_bounds(
                est=values["est"], low=values["low"], high=values["high"]
            )
            if not good:
                QMessageBox.warning(self, "Warning", message)
                return False, False
            return True, display_value
        try:
            with ExitStack() as signal_blockers:
                for widget in self.entry_widgets:
                    signal_blockers.enter_context(QSignalBlocker(widget))
                display_scale_val = calc_fncs.evaluate(
                    new_text=new_text,
                    analysis_unit=self.analysis_unit,
                    current_effect=self.current_effect,
                    group_comparison=self.group_comparison,
                    conv_to_disp_scale=partial(
                        self._synchronous_calculator().binary_convert_scale,
                        metric_name=self.current_effect,
                        convert_to="display.scale",
                    ),
                    parent=self,
                    confidence_multiplier=self.confidence_multiplier,
                    ci_param=ci_param,
                    source=calc_fncs.calculator_effect_source(
                        self.analysis_unit,
                        self.current_groups,
                        self.current_effect,
                        self.group_comparison,
                        self.confidence_multiplier,
                    ),
                )
        except Exception:
            return False, False
        return True, display_scale_val

    def _text_from_value(self, value):
        if value == "est":
            return str(self.effect_text_box.text())
        elif value == "lower":
            return str(self.lower_text_box.text())
        elif value == "upper":
            return str(self.upper_text_box.text())
        return None  # Unknown value key.

    def val_changed(self, val_str):
        # Backup form state
        old_analysis_unit, old_table = self._save_analysis_unit_and_table_state(
            table=self.raw_data_table,
            analysis_unit=self.analysis_unit,
            use_old_value=False,
        )

        new_text = self._text_from_value(val_str)

        no_errors, display_scale_val = self._text_box_value_is_between_bounds(
            val_str, new_text
        )
        if no_errors is False:  # There are errors
            self._restore_invalid_effect_edit(
                val_str, old_analysis_unit, old_table
            )
            return

        # If we got to this point it means everything is ok so far
        try:
            if display_scale_val not in EMPTY_VALS:
                display_scale_val = float(display_scale_val)
            else:
                display_scale_val = None
        except ValueError:
            # Ignore incomplete numeric input while the user is still editing.
            return None

        if self._calculator_async:
            self._request_calculation_scale(
                val_str, display_scale_val, old_analysis_unit, old_table
            )
            return

        calculation_scale_value = self._synchronous_calculator().binary_convert_scale(
            display_scale_val, self.current_effect, convert_to="calc.scale"
        )
        self._commit_effect_value(
            val_str, calculation_scale_value, old_analysis_unit, old_table
        )

    def _restore_invalid_effect_edit(self, val_str, old_analysis_unit, old_table):
        self.restore_analysis_unit_and_table(old_analysis_unit, old_table)
        with ExitStack() as signal_blockers:
            for widget in self.entry_widgets:
                signal_blockers.enter_context(QSignalBlocker(widget))
            self._focus_effect_entry(val_str)

    def _focus_effect_entry(self, val_str):
        effect_entries = {
            "est": self.effect_text_box,
            "lower": self.lower_text_box,
            "upper": self.upper_text_box,
        }
        entry = effect_entries.get(val_str)
        if entry is not None:
            entry.setFocus()

    def _request_calculation_scale(
        self, val_str, display_scale_val, old_analysis_unit, old_table
    ):
        apply_button = required(
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok),
            "binary calculator OK button",
        )
        apply_button.setEnabled(False)

        def commit(results):
            self._commit_effect_value(
                val_str,
                results["calculation-scale"],
                old_analysis_unit,
                old_table,
            )
            apply_button.setEnabled(True)

        def failed(_error):
            apply_button.setEnabled(False)
            self._focus_effect_entry(val_str)

        self._request_calculator(
            [
                {
                    "id": "calculation-scale",
                    "operation": "binary_convert_scale",
                    "args": {
                        "x": display_scale_val,
                        "metric_name": self.current_effect,
                        "convert_to": "calc.scale",
                    },
                }
            ],
            commit,
            failed,
        )

    def _commit_effect_value(
        self, val_str, calculation_scale_value, old_analysis_unit, old_table
    ):

        if val_str == "est":
            self.analysis_unit.set_effect(
                self.current_effect, self.group_comparison, calculation_scale_value
            )
        elif val_str == "lower":
            self.analysis_unit.set_lower(
                self.current_effect, self.group_comparison, calculation_scale_value
            )
        elif val_str == "upper":
            self.analysis_unit.set_upper(
                self.current_effect, self.group_comparison, calculation_scale_value
            )

        new_analysis_unit, new_table = self._save_analysis_unit_and_table_state(
            table=self.raw_data_table,
            analysis_unit=self.analysis_unit,
            use_old_value=False,
        )

        calc_fncs.push_field_edit(
            self._field_history,
            owner=self,
            restore_state=self.restore_analysis_unit_and_table,
            old_state=(old_analysis_unit, old_table),
            new_state=(new_analysis_unit, new_table),
        )

    def _update_raw_data(self):
        """Sets events and non-events from stored events and arm totals."""

        for row, group in enumerate(self.current_groups):
            events, total = self.analysis_unit.get_raw_data_for_group(group)
            no_events = None
            if events not in EMPTY_VALS and total not in EMPTY_VALS:
                no_events = total - events
            self._set_val(row, 0, events)
            self._set_val(row, 1, no_events)
            self._set_val(row, 2, total)

    def _update_analysis_unit(self):
        """Copy the potentially imputed table values into the analysis unit."""
        for row in range(2):
            events = self._get_int(row, 0)
            no_events = self._get_int(row, 1)
            total = self._get_int(row, 2)
            if events not in EMPTY_VALS and no_events not in EMPTY_VALS:
                total = events + no_events
            raw_data = self.analysis_unit.get_raw_data_for_group(
                self.current_groups[row]
            )
            raw_data[0] = events
            raw_data[1] = total

    def _cell_data_not_valid(self, celldata_string):
        # ignore blank entries
        if calc_fncs.cell_text_is_blank(celldata_string):
            return None

        try:
            value = calc_fncs.numeric_value(celldata_string)
        except ValueError:
            return "Raw data needs to be numeric."

        if not value.is_integer():
            return "Expected a whole number (count), but a decimal value was entered."

        if value < 0:
            return "Counts cannot be negative."
        return None

    def restore_analysis_unit(self, old_analysis_unit):
        """Restores the analysis_unit data and resets the form"""
        self.analysis_unit = copy.deepcopy(old_analysis_unit)

        self.initialize_form()  # clear form first
        self._update_raw_data()
        self.set_current_effect()
        self._update_data_table()
        self.update_back_calculation_button()

    def restore_table(self, old_table):
        old_table = tabular_data.normalize_rows(old_table)
        if not old_table:
            return
        nrows = min(len(old_table), self.raw_data_table.rowCount())
        ncols = min(len(old_table[0]), self.raw_data_table.columnCount())

        for row in range(nrows):
            for col in range(ncols):
                self._set_val(row, col, old_table[row][col])
        self._update_data_table()
        self._mark_table_consistent()

    def restore_analysis_unit_and_table(self, old_analysis_unit, old_table):
        self.restore_analysis_unit(old_analysis_unit)
        self.restore_table(old_table)

    def _save_analysis_unit_and_table_state(
        self,
        table,
        analysis_unit,
        row=None,
        col=None,
        old_value=None,
        use_old_value=True,
    ):
        old_table = calc_fncs.save_table_data(table)
        if use_old_value:
            old_table[row][col] = old_value

        old_analysis_unit = copy.deepcopy(analysis_unit)
        return old_analysis_unit, old_table

    def cell_changed(self, row, col):
        # tries to make sense of user input before passing
        # on to the R routine

        if not self._raw_count_cell_is_editable(row, col):
            self._update_data_table()
            self._mark_table_consistent()
            return

        self._grow_raw_data_column_to_contents(col)

        old_analysis_unit, old_table = self._save_analysis_unit_and_table_state(
            table=self.raw_data_table,
            analysis_unit=self.analysis_unit,
            old_value=self.current_item_data,
            row=row,
            col=col,
            use_old_value=True,
        )

        try:
            # Test if entered data is valid (a number)
            warning_msg = self._cell_data_not_valid(
                required(
                    self.raw_data_table.item(row, col),
                    f"binary table cell ({row}, {col})",
                ).text()
            )
            if warning_msg:
                raise ValueError(warning_msg)

            self._update_data_table()  # calculate derived margins from raw counts
            self._mark_table_consistent()
        except Exception as e:
            msg = e.args[0]
            QMessageBox.warning(self, "Warning", msg)  # popup warning
            self.restore_analysis_unit_and_table(
                old_analysis_unit, old_table
            )  # brings things back to the way they were
            self._mark_table_invalid(msg)
            return  # and leave

        try:
            self._update_analysis_unit()  # table widget --> analysis_unit
            self.update_effect_from_raw_data()  # update metric in analysis_unit and in table
        except Exception as e:
            msg = "Could not compute study effects from the edited raw data: %s" % e
            QMessageBox.warning(self, "Warning", msg)
            self.restore_analysis_unit_and_table(old_analysis_unit, old_table)
            return

        new_analysis_unit, new_table = self._save_analysis_unit_and_table_state(
            table=self.raw_data_table,
            analysis_unit=self.analysis_unit,
            row=row,
            col=col,
            use_old_value=False,
        )

        calc_fncs.push_field_edit(
            self._field_history,
            owner=self,
            restore_state=self.restore_analysis_unit_and_table,
            old_state=(old_analysis_unit, old_table),
            new_state=(new_analysis_unit, new_table),
        )

    def _get_table_values(self):
        """Package table from 2x2 table in to a dictionary"""
        vals_d = {}
        vals_d["c11"] = self._get_int(0, 0)
        vals_d["c12"] = self._get_int(0, 1)
        vals_d["c21"] = self._get_int(1, 0)
        vals_d["c22"] = self._get_int(1, 1)
        vals_d["r1sum"] = self._get_int(0, 2)
        vals_d["r2sum"] = self._get_int(1, 2)
        vals_d["c1sum"] = self._get_int(2, 0)
        vals_d["c2sum"] = self._get_int(2, 1)
        vals_d["total"] = self._get_int(2, 2)
        return vals_d

    def clear_column(self, col):
        """Clears out column in table and analysis_unit"""
        for row in range(3):
            self._set_val(row, col, None)

        self._update_analysis_unit()

    def _set_vals(self, computed_d):
        """Sets values in table widget"""
        with QSignalBlocker(self.raw_data_table):
            self._set_val(0, 0, computed_d["c11"])
            self._set_val(0, 1, computed_d["c12"])
            self._set_val(1, 0, computed_d["c21"])
            self._set_val(1, 1, computed_d["c22"])
            self._set_val(0, 2, computed_d["r1sum"])
            self._set_val(1, 2, computed_d["r2sum"])
            self._set_val(2, 0, computed_d["c1sum"])
            self._set_val(2, 1, computed_d["c2sum"])
            self._set_val(2, 2, computed_d["total"])

    def _set_val(self, row, col, val):
        if is_nan(val):  # get out quick
            return

        with QSignalBlocker(self.raw_data_table):
            str_val = "" if val in EMPTY_VALS else str(int(val))
            if self.raw_data_table.item(row, col) is None:
                self.raw_data_table.setItem(row, col, QTableWidgetItem(str_val))
            else:
                required(
                    self.raw_data_table.item(row, col),
                    f"binary table cell ({row}, {col})",
                ).setText(str_val)
            calc_fncs.set_table_item_editable(
                self.raw_data_table.item(row, col),
                self._raw_count_cell_is_editable(row, col),
            )

    def _update_data_table(self):
        """Fill in 2x2 table from other entries in the table"""
        with QSignalBlocker(self.raw_data_table):
            params = self._get_table_values()
            computed_params = calc_fncs.compute_2x2_table_from_inner_counts(params)
            for total_name in ("r1sum", "r2sum"):
                if computed_params[total_name] in EMPTY_VALS:
                    computed_params[total_name] = params[total_name]
            if (
                computed_params["total"] in EMPTY_VALS
                and computed_params["r1sum"] not in EMPTY_VALS
                and computed_params["r2sum"] not in EMPTY_VALS
            ):
                computed_params["total"] = (
                    computed_params["r1sum"] + computed_params["r2sum"]
                )
            if computed_params:
                self._set_vals(computed_params)  # computed --> table widget

    def _is_empty(self, i, j):
        val = self.raw_data_table.item(i, j)
        return val is None or val.text() == ""

    def _get_int(self, i, j):
        """Get value from cell specified by row=i, col=j as an integer"""
        if not self._is_empty(i, j):
            text = required(
                self.raw_data_table.item(i, j), f"binary table cell ({i}, {j})"
            ).text()
            try:
                val = int(text)
            except ValueError:
                val = int(calc_fncs.numeric_value(text))
            return val
        else:
            return None  # its good to be explicit

    def _is_blank(self, x):
        return x is None or x == ""

    def update_effect_from_raw_data(self):
        e1, n1, e2, n2 = self.analysis_unit.get_raw_data_for_groups(self.current_groups)

        two_arm_raw_data_ok = not any([self._is_blank(x) for x in [e1, n1, e2, n2]])
        one_arm_raw_data_ok = not any([self._is_blank(x) for x in [e1, n1]])
        current_effect_is_one_arm = self.current_effect in BINARY_ONE_ARM_METRICS
        current_effect_is_two_arm = self.current_effect in BINARY_TWO_ARM_METRICS

        # Leave current effects untouched when raw data are incomplete.
        if two_arm_raw_data_ok or (current_effect_is_one_arm and one_arm_raw_data_ok):
            if self._calculator_async:
                self._request_calculator(
                    [
                        {
                            "id": "raw-effect",
                            "operation": "calculate_raw_effects",
                            "args": {
                                "data_type": "binary",
                                "effect": self.current_effect,
                                "raw_data": [e1, n1, e2, n2],
                                "confidence_level": self.confidence_level,
                            },
                        }
                    ],
                    self._binary_raw_effect_ready,
                )
                return True
            if current_effect_is_two_arm:
                est_and_ci_d = self._synchronous_calculator().effect_for_study(
                    e1,
                    n1,
                    e2,
                    n2,
                    metric=self.current_effect,
                    confidence_level=self.confidence_level,
                )
            else:
                # binary, one-arm
                est_and_ci_d = self._synchronous_calculator().effect_for_study(
                    e1,
                    n1,
                    two_arm=False,
                    metric=self.current_effect,
                    confidence_level=self.confidence_level,
                )

            est, low, high = self._synchronous_calculator().effect_triplet(
                est_and_ci_d,
                "calc_scale",
                metric=self.current_effect,
            )
            self.analysis_unit.set_effect_and_ci(
                self.current_effect,
                self.group_comparison,
                est,
                low,
                high,
                confidence_multiplier=self.confidence_multiplier,
            )
            self.set_current_effect()
            return True
        return False

    def _binary_raw_effect_ready(self, results):
        estimate, lower, upper = results["raw-effect"][0]
        self.analysis_unit.set_effect_and_ci(
            self.current_effect,
            self.group_comparison,
            estimate,
            lower,
            upper,
            confidence_multiplier=self.confidence_multiplier,
        )
        self.set_current_effect(after=self.update_back_calculation_button)

    def clear_form(self):
        self._pending_back_calculation = None
        self.calculated_values_group.hide()
        self.calculated_values_label.clear()

        # For undo/redo
        old_analysis_unit, old_table = self._save_analysis_unit_and_table_state(
            table=self.raw_data_table,
            analysis_unit=self.analysis_unit,
            use_old_value=False,
        )

        blank_vals = {
            "c11": "",
            "c12": "",
            "r1sum": "",
            "c21": "",
            "c22": "",
            "r2sum": "",
            "c1sum": "",
            "c2sum": "",
            "total": "",
        }

        self._set_vals(blank_vals)
        self._update_analysis_unit()

        for metric in BINARY_ONE_ARM_METRICS + BINARY_TWO_ARM_METRICS:
            if (
                self.current_effect in BINARY_TWO_ARM_METRICS
                and metric in BINARY_TWO_ARM_METRICS
            ) or (
                self.current_effect in BINARY_ONE_ARM_METRICS
                and metric in BINARY_ONE_ARM_METRICS
            ):
                self.analysis_unit.set_effect_for_source(
                    "entered", metric, self.group_comparison, None, None, None
                )
        # clear line edits
        self.set_current_effect()
        self._refresh_raw_data_editability()

        new_analysis_unit, new_table = self._save_analysis_unit_and_table_state(
            table=self.raw_data_table,
            analysis_unit=self.analysis_unit,
            use_old_value=False,
        )

        calc_fncs.push_field_edit(
            self._field_history,
            owner=self,
            restore_state=self.restore_analysis_unit_and_table,
            old_state=(old_analysis_unit, old_table),
            new_state=(new_analysis_unit, new_table),
        )

    def get_current_group_comparison(self):

        if self.current_effect in BINARY_ONE_ARM_METRICS:
            group_comparison = self.current_groups[0]
        else:
            group_comparison = "-".join(self.current_groups)
        return group_comparison

    def undo(self):
        self._field_history.undo()

    def redo(self):
        self._field_history.redo()


class BinaryBackCalculationDialog(
    QDialog, _ui_binary_back_calculation_dialog.Ui_BinaryBackCalculationDialog
):
    def __init__(self, imputed_data, parent=None):
        super(BinaryBackCalculationDialog, self).__init__(parent)
        self.setupUi(self)
        for widget in self.content_widget.findChildren(QWidget):
            widget.installEventFilter(self)
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )

        op1 = imputed_data["op1"]  # option 1 data
        a, b, c, d = op1["a"], op1["b"], op1["c"], op1["d"]
        a, b, c, d = int(round(a)), int(round(b)), int(round(c)), int(round(d))
        option1_txt = (
            "Group 1:\n  #events: %d\n  Total: %d\n\nGroup 2:\n  #events: %d\n  Total: %d"
            % (a, b, c, d)
        )

        op2 = imputed_data["op2"]
        a, b, c, d = op2["a"], op2["b"], op2["c"], op2["d"]
        a, b, c, d = int(round(a)), int(round(b)), int(round(c)), int(round(d))
        option2_txt = (
            "Group 1:\n  #events: %d\n  Total: %d\n\nGroup 2:\n  #events: %d\n  Total: %d"
            % (a, b, c, d)
        )

        self.choice1_btn.setText(option1_txt)
        self.choice2_btn.setText(option2_txt)
        self.info_label.setText(
            "The back-calculation has resulted in two "
            "possible sets of choices for the counts. Please"
            " choose one from below. These choices do not "
            "reflect possible corrections for zero counts."
        )

        self._layout_controller.request_content_refit()

    def eventFilter(  # ty: ignore[invalid-method-override] -- PyQt6's QDialog stub rejects this runtime-supported QObject override.
        self, watched: QObject | None, event: QEvent | None
    ) -> bool:
        if (
            isinstance(watched, QWidget)
            and event is not None
            and event.type() == QEvent.Type.FocusIn
            and self.content_widget.isAncestorOf(watched)
        ):
            self.content_scroll.ensureWidgetVisible(watched)
        return super(BinaryBackCalculationDialog, self).eventFilter(watched, event)

    def get_choice(self):
        choices = ["op1", "op2"]

        if self.choice1_btn.isChecked():
            return choices[0]  # op1
        else:
            return choices[1]  # op2
