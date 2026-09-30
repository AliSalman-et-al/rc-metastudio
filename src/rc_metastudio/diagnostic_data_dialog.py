# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Diagnostic outcome data entry dialog."""

import copy
from contextlib import ExitStack
from functools import partial
from typing import TYPE_CHECKING

from PyQt6.QtCore import QEvent, QObject, QSignalBlocker, QTimer, Qt
from PyQt6.QtGui import QAction, QKeySequence, QPalette
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

from rc_metastudio.calculator_service import (
    CalculatorService,
    execute_calculator_calls,
)
from rc_metastudio.calculator_dialog_worker import install_calculator_dialog_worker
from rc_metastudio import app_error_handler
from rc_metastudio import adaptive_window
from rc_metastudio import tabular_data
from rc_metastudio.meta_globals import (
    DIAGNOSTIC,
    DIAGNOSTIC_METRICS,
    DIAG_FIELDS_TO_RAW_INDICES,
    EMPTY_VALS,
    is_nan,
    is_a_float,
    is_empty,
)
from rc_metastudio import calculator_routines as calc_fncs
from rc_metastudio.runtime_types import required

if TYPE_CHECKING:
    import ui_diagnostic_data_dialog as _ui_diagnostic_data_dialog
else:
    from rc_metastudio.forms import (
        ui_diagnostic_data_dialog as _ui_diagnostic_data_dialog,
    )

BACK_CALCULATABLE_DIAGNOSTIC_EFFECTS = ["Sens", "Spec"]
DIAGNOSTIC_RAW_COUNT_CELLS = frozenset(((0, 0), (0, 1), (1, 0), (1, 1)))


def _local_calculator_result_fields(value: object) -> tuple[str, object]:
    if not isinstance(value, dict):
        raise RuntimeError("The local calculator returned an invalid call result.")
    fields: dict[str, object] = {}
    for key, field_value in value.items():
        if not isinstance(key, str):
            raise RuntimeError("The local calculator returned an invalid call result.")
        fields[key] = field_value
    call_id = fields.get("id")
    if not isinstance(call_id, str) or "result" not in fields:
        raise RuntimeError("The local calculator returned an invalid call result.")
    return call_id, fields["result"]


def _local_calculator_results(response: dict[str, object]) -> dict[str, object]:
    raw_results = response.get("calls")
    if not isinstance(raw_results, list):
        raise RuntimeError("The local calculator returned an invalid result batch.")
    results: dict[str, object] = {}
    for raw_item in raw_results:
        call_id, result = _local_calculator_result_fields(raw_item)
        results[call_id] = result
    return results


class DiagnosticDataDialog(QDialog, _ui_diagnostic_data_dialog.Ui_DiagnosticDataDialog):
    def __init__(
        self,
        analysis_unit,
        current_groups,
        group_comparison,
        confidence_level=None,
        calculator: CalculatorService | None = None,
        worker_client=None,
        parent=None,
    ):
        super(DiagnosticDataDialog, self).__init__(parent)
        self.setupUi(self)
        self.study_context_label.hide()
        self.calculated_values_group.hide()
        self._pending_back_calculation = None
        self._configure_raw_data_table()
        self._configure_semantic_fields()
        self._configure_focus_revelation()
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )

        if confidence_level is None:
            raise ValueError("Confidence level must be specified")
        self.confidence_level = confidence_level
        self.worker_client = worker_client
        self._calculator_async = worker_client is not None and calculator is None
        self.calculator: CalculatorService | None = calculator if calculator is not None else (
            None if self._calculator_async else CalculatorService()
        )
        self._calculator_requests = None
        self._worker_status_label = None
        if self._calculator_async:
            self._worker_status_label, self._calculator_requests = (
                install_calculator_dialog_worker(self, worker_client)
            )
        self.confidence_multiplier = (
            None
            if self._calculator_async
            else self._calculator_service().get_confidence_multiplier(
                self.confidence_level
            )
        )
        self.current_item_data: int | None = None

        self.setup_signals_and_slots()

        self._initialize_entry_state(analysis_unit, current_groups, group_comparison)

    def _calculator_service(self) -> CalculatorService:
        calculator = self.calculator
        if calculator is None:
            raise RuntimeError("The calculator is unavailable for worker-backed input.")
        return calculator

    def _initialize_entry_state(self, analysis_unit, current_groups, group_comparison):
        self.analysis_unit = analysis_unit
        self.current_groups = current_groups
        self.group_comparison = group_comparison
        self.current_effect = "Sens"
        self._configure_entry_widgets()
        self._configure_entry_labels()
        self._populate_entry_data()
        self._configure_apply_button()
        if self._calculator_async:
            self._request_initial_multiplier()
        self._request_initial_content_refit()

    def _configure_entry_widgets(self) -> None:
        self.entry_widgets = [
            self.two_by_two_table,
            self.prevalence_text_box,
            self.lower_text_box,
            self.upper_text_box,
            self.effect_text_box,
        ]
        self.text_boxes = [
            self.lower_text_box,
            self.upper_text_box,
            self.effect_text_box,
            self.prevalence_text_box,
        ]
        if self._calculator_async:
            for text_box in self.text_boxes:
                text_box.textChanged.connect(self._calculator_input_changed)

    def _configure_entry_labels(self) -> None:
        self.ci_label.setText(
            "{0:.1f}% Confidence Interval".format(self.confidence_level)
        )
        self._configure_readable_ci_label()

    def _populate_entry_data(self) -> None:
        self.initialize_form()
        self.setup_back_calculation_feedback()
        self._field_history = calc_fncs.TransientEditHistory()
        self._update_raw_data()
        self._populate_effect_cmbo_box()
        if not self._calculator_async:
            self.set_current_effect()
        self._update_data_table()
        self._fit_raw_data_columns_for_first_display()
        if not self._calculator_async:
            self.update_back_calculation_button()
        self._set_content_preferred_width()

    def _configure_apply_button(self) -> None:
        self.current_prevalence = self._get_prevalence_str()
        self.two_by_two_table.setCurrentCell(0, 0)
        self.two_by_two_table.setFocus()
        apply_button = required(
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok),
            "diagnostic calculator OK button",
        )
        apply_button.setText("Apply to study")
        apply_button.setAccessibleName("Apply study data changes")
        apply_button.setDefault(True)
        if self._calculator_async:
            for widget in self.entry_widgets:
                widget.setEnabled(False)
            apply_button.setEnabled(False)

    def _request_initial_multiplier(self) -> None:
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

    def _request_calculator(self, calls, on_result, on_error=None):
        if self._calculator_requests is not None:
            return self._calculator_requests.submit(calls, on_result, on_error)
        response = execute_calculator_calls(
            calls, service=self._calculator_service()
        )
        on_result(_local_calculator_results(response))
        return 0

    def _invalidate_calculator_responses(self, *_args):
        if self._calculator_requests is not None:
            self._calculator_requests.invalidate()

    def _calculator_input_changed(self, *_args):
        self._invalidate_calculator_responses()
        self._pending_back_calculation = None
        self.calculated_values_group.hide()
        self.calculated_values_label.clear()
        self.back_calculate_button.setEnabled(False)
        apply_button = required(
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok),
            "diagnostic calculator OK button",
        )
        apply_button.setEnabled(False)

    def _calculator_initialized(self, results):
        self.confidence_multiplier = float(results["multiplier"])
        for widget in self.entry_widgets:
            widget.setEnabled(True)
        apply_button = required(
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok),
            "diagnostic calculator OK button",
        )
        apply_button.setEnabled(True)
        self._update_raw_data()
        self._update_data_table()
        self.impute_effects_in_analysis_unit(
            after=lambda: self.set_current_effect(
                after=self.update_back_calculation_button
            )
        )
        self.two_by_two_table.setFocus()

    def _configure_raw_data_table(self):
        """Give the diagnostic grid internal overflow and semantic row height."""
        # The adaptive contract sizes the dialog; the scroll area owns overflow.
        self.content_scroll.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding
        )
        table = self.two_by_two_table
        # layout-audit: allow=compact-table-overflow; reason=compact table keeps rows visible and owns excess overflow
        table.setMinimumWidth(0)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        header = required(table.horizontalHeader(), "diagnostic table header")
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        height = (
            header.sizeHint().height()
            + sum(table.rowHeight(row) for row in range(table.rowCount()))
            + 2 * table.frameWidth()
            + required(table.horizontalScrollBar(), "diagnostic table scrollbar")
            .sizeHint()
            .height()
        )
        # layout-audit: allow=compact-table-overflow; reason=compact table keeps rows visible and owns excess overflow
        table.setMinimumHeight(height)
        # layout-audit: allow=compact-table-overflow; reason=compact table keeps rows visible and owns excess overflow
        table.setMaximumHeight(height)

    def _configure_readable_ci_label(self):
        """Keep the confidence heading on one line at normal scaling."""
        self.ci_label.setWordWrap(False)
        # layout-audit: allow=content-overflow-control; reason=confidence heading remains readable inside the scrollable dialog content
        self.ci_label.setMinimumWidth(self.ci_label.sizeHint().width())

    def _set_content_preferred_width(self):
        """Give dense content room before the outer policy applies its cap."""
        layout = required(self.content_layout, "diagnostic content layout")
        layout.activate()
        content_width = layout.sizeHint().width()
        content_width = max(content_width, self.two_by_two_table.minimumWidth() + 44)
        margins = required(self.layout(), "diagnostic dialog layout").contentsMargins()
        scrollbar = required(
            self.content_scroll.verticalScrollBar(), "diagnostic content scrollbar"
        )
        preferred_width = (
            content_width
            + margins.left()
            + margins.right()
            + 2 * self.content_scroll.frameWidth()
            + scrollbar.sizeHint().width()
        )
        # Only the footer sits outside the scroll area and must set the dialog minimum.
        footer = required(self.buttonBox, "diagnostic action footer")
        minimum_width = (
            max(footer.minimumWidth(), footer.minimumSizeHint().width())
            + margins.left()
            + margins.right()
        )
        adaptive_window.set_content_preferred_width(
            self, minimum_width, preferred_width
        )

    def _configure_semantic_fields(self):
        # layout-audit: allow=content-overflow-control; reason=required content may consume available layout width
        self.effect_combo_box.setMinimumWidth(0)
        # layout-audit: allow=content-overflow-control; reason=required content may consume available layout width
        self.effect_combo_box.setMaximumWidth(QWIDGETSIZE_MAX)
        self.effect_combo_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._size_line_edit_for_samples(self.prevalence_text_box, ("0.0000", "1.0000"))

    @staticmethod
    def _size_line_edit_for_samples(line_edit, samples):
        margins = line_edit.textMargins()
        frame = required(line_edit.style(), "diagnostic field style").pixelMetric(
            QStyle.PixelMetric.PM_DefaultFrameWidth, None, line_edit
        )
        required_width = (
            max(line_edit.fontMetrics().horizontalAdvance(value) for value in samples)
            + margins.left()
            + margins.right()
            + 2 * frame
            + 12
        )
        # layout-audit: allow=numeric-domain-control; reason=editor width follows representative values from its numeric domain
        line_edit.setMinimumWidth(required_width)
        # layout-audit: allow=numeric-domain-control; reason=editor width follows representative values from its numeric domain
        line_edit.setMaximumWidth(required_width)
        line_edit.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def _configure_focus_revelation(self):
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
        return super(DiagnosticDataDialog, self).eventFilter(watched, event)

    def _fit_raw_data_columns_for_first_display(self):
        self._grow_all_raw_data_columns_to_contents()
        header = required(self.two_by_two_table.horizontalHeader(), "diagnostic table header")
        table_width = sum(
            header.sectionSize(column)
            for column in range(self.two_by_two_table.columnCount())
        )
        table_width += required(
            self.two_by_two_table.verticalHeader(), "diagnostic row header"
        ).sizeHint().width()
        table_width += 2 * self.two_by_two_table.frameWidth()
        # layout-audit: allow=compact-table-overflow; reason=wide diagnostic cells keep their contents and the table owns horizontal overflow
        self.two_by_two_table.setMinimumWidth(
            max(self.two_by_two_table.minimumWidth(), table_width)
        )

    def _grow_all_raw_data_columns_to_contents(self):
        for column in range(self.two_by_two_table.columnCount()):
            self._grow_raw_data_column_to_contents(column)

    def _grow_raw_data_column_to_contents(self, column):
        table = self.two_by_two_table
        header = required(table.horizontalHeader(), "diagnostic table header")
        required_width = max(
            header.sectionSizeHint(column), table.sizeHintForColumn(column)
        )
        if required_width > table.columnWidth(column):
            header.resizeSection(column, required_width)

    def _request_initial_content_refit(self):
        controller = self.__dict__.get("_layout_controller")
        if controller is not None and not self.isVisible():
            controller.request_content_refit()

    def initialize_form(self):
        """Initialize all cells to empty items"""
        nrows = self.two_by_two_table.rowCount()
        ncols = self.two_by_two_table.columnCount()

        for row in range(nrows):
            for col in range(ncols):
                self._set_val(row, col, None)

        for txt_box in self.text_boxes:
            txt_box.setText("")

    def setup_signals_and_slots(self):
        self.two_by_two_table.cellChanged.connect(
            app_error_handler.safe_slot(self.cell_changed, parent=self)
        )
        self.two_by_two_table.currentCellChanged.connect(
            app_error_handler.safe_slot(
                self.on_two_by_two_table_currentCellChanged, parent=self
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
        self.prevalence_text_box.editingFinished.connect(
            app_error_handler.safe_slot(
                lambda: self.val_changed("prevalence"), parent=self
            )
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

    def on_two_by_two_table_currentCellChanged(
        self, currentRow, currentColumn, previousRow, previousColumn
    ):
        self.current_item_data = self._get_int(currentRow, currentColumn)

    def setup_back_calculation_feedback(self):
        inconsistency_palette = QPalette()
        inconsistency_palette.setColor(
            QPalette.ColorRole.WindowText, Qt.GlobalColor.red
        )
        self.inconsistencyLabel.setPalette(inconsistency_palette)
        self.inconsistencyLabel.setVisible(False)

    def _mark_table_consistent(self):
        self.inconsistencyLabel.setVisible(False)
        required(
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok),
            "diagnostic calculator OK button",
        ).setEnabled(True)

    def _mark_table_invalid(self, message):
        self.inconsistencyLabel.setText(str(message))
        self.inconsistencyLabel.setVisible(True)
        # The rejected edit has already been rolled back to a valid state, so
        # acceptance must remain available while the inline guidance is shown.
        required(
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok),
            "diagnostic calculator OK button",
        ).setEnabled(True)
        self.content_layout.invalidate()
        self.content_widget.updateGeometry()
        self.content_scroll.ensureWidgetVisible(self.inconsistencyLabel)
        QTimer.singleShot(
            0,
            lambda: self._ensure_content_widget_visible(self.inconsistencyLabel),
        )

    def _ensure_content_widget_visible(self, widget):
        try:
            self.content_scroll.ensureWidgetVisible(widget)
            center = widget.mapTo(self.content_widget, widget.rect().center())
            self.content_scroll.ensureVisible(center.x(), center.y(), 12, 12)
        except RuntimeError:
            pass

    def _raw_count_cell_is_editable(self, row, col):
        return (row, col) in DIAGNOSTIC_RAW_COUNT_CELLS

    def _get_int(self, i, j):
        try:
            if not self._is_empty(i, j):
                text = required(
                    self.two_by_two_table.item(i, j),
                    f"diagnostic table cell ({i}, {j})",
                ).text()
                try:
                    int_val = int(text)
                except ValueError:
                    int_val = int(calc_fncs.numeric_value(text))
                return int_val
        except (ArithmeticError, TypeError, ValueError) as exc:
            msg = "Could not convert %s to integer" % self.two_by_two_table.item(i, j)
            QMessageBox.warning(self, "Warning", msg)
            raise ValueError(
                "Could not convert %s to int" % self.two_by_two_table.item(i, j)
            ) from exc

    def cell_data_invalid(self, celldata_string):
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

    def _is_empty(self, i, j):
        val = self.two_by_two_table.item(i, j)
        return val is None or val.text() == "" or val.text() is None

    def _set_val(self, row, col, val):
        if is_nan(val):  # get out quick
            return

        str_val = "" if val in EMPTY_VALS else str(int(val))
        with QSignalBlocker(self.two_by_two_table):
            if self.two_by_two_table.item(row, col) is None:
                self.two_by_two_table.setItem(row, col, QTableWidgetItem(str_val))
            else:
                required(
                    self.two_by_two_table.item(row, col),
                    f"diagnostic table cell ({row}, {col})",
                ).setText(str_val)
            calc_fncs.set_table_item_editable(
                self.two_by_two_table.item(row, col),
                self._raw_count_cell_is_editable(row, col),
            )

    def _set_vals(self, computed_d):
        """Sets values in table widget"""
        with QSignalBlocker(self.two_by_two_table):
            self._set_val(0, 0, computed_d["c11"])
            self._set_val(0, 1, computed_d["c12"])
            self._set_val(1, 0, computed_d["c21"])
            self._set_val(1, 1, computed_d["c22"])
            self._set_val(0, 2, computed_d["r1sum"])
            self._set_val(1, 2, computed_d["r2sum"])
            self._set_val(2, 0, computed_d["c1sum"])
            self._set_val(2, 1, computed_d["c2sum"])
            self._set_val(2, 2, computed_d["total"])

    def _get_prevalence_str(self):
        return str(self.prevalence_text_box.text())

    def cell_changed(self, row, col):
        if self._calculator_async:
            self._invalidate_calculator_responses()
        if not self._raw_count_cell_is_editable(row, col):
            self._update_data_table()
            self._mark_table_consistent()
            return

        old_analysis_unit, old_table = self._save_analysis_unit_and_table_state(
            table=self.two_by_two_table,
            analysis_unit=self.analysis_unit,
            old_value=self.current_item_data,
            row=row,
            col=col,
            use_old_value=True,
        )
        old_prevalence = self._get_prevalence_str()

        if not self._validate_raw_count_cell_edit(
            row, col, old_analysis_unit, old_table, old_prevalence
        ):
            return

        try:
            self._update_analysis_unit()  # 2x2 table --> analysis_unit
            if self._calculator_async:
                self._finish_worker_raw_count_edit(
                    row, col, old_analysis_unit, old_table, old_prevalence
                )
                return
            self.impute_effects_in_analysis_unit()  # effects   --> analysis_unit
            self.set_current_effect()  # analysis_unit   --> effects
        except Exception as e:
            self._report_raw_effect_update_failure(
                e, old_analysis_unit, old_table, old_prevalence
            )
            return

        self._record_raw_count_edit(row, col, old_analysis_unit, old_table, old_prevalence)

    def _validate_raw_count_cell_edit(
        self, row, col, old_analysis_unit, old_table, old_prevalence
    ) -> bool:
        try:
            cell = required(
                self.two_by_two_table.item(row, col),
                f"diagnostic table cell ({row}, {col})",
            )
            warning = self.cell_data_invalid(cell.text())
            if warning:
                raise ValueError(warning)
            if self._raw_count_table_is_all_zero():
                raise ValueError(
                    "Diagnostic 2x2 table must contain at least one participant; "
                    "enter at least one count greater than zero."
                )
            self._update_data_table()
            self._mark_table_consistent()
        except Exception as error:
            message = error.args[0]
            QMessageBox.warning(self, "Warning", message)
            self.restore_analysis_unit_and_table(
                old_analysis_unit, old_table, old_prevalence
            )
            self._mark_table_invalid(message)
            return False
        return True

    def _finish_worker_raw_count_edit(
        self, row, col, old_analysis_unit, old_table, old_prevalence
    ) -> None:
        self._clear_derived_effect_previews()
        self._pending_back_calculation = None
        self.calculated_values_group.hide()
        self.calculated_values_label.clear()
        self.effect_group.setTitle("Entered effect")
        with ExitStack() as signal_blockers:
            for widget in self.text_boxes[:3]:
                signal_blockers.enter_context(QSignalBlocker(widget))
            self.effect_text_box.clear()
            self.lower_text_box.clear()
            self.upper_text_box.clear()
        self._record_raw_count_edit(
            row, col, old_analysis_unit, old_table, old_prevalence
        )
        self.current_prevalence = self._get_prevalence_str()
        self.impute_effects_in_analysis_unit(
            after=self._restore_current_effect_after_raw_imputation
        )

    def _restore_current_effect_after_raw_imputation(self) -> None:
        self.set_current_effect(after=self.update_back_calculation_button)

    def _record_raw_count_edit(
        self, row, col, old_analysis_unit, old_table, old_prevalence
    ) -> None:
        new_analysis_unit, new_table = self._save_analysis_unit_and_table_state(
            table=self.two_by_two_table,
            analysis_unit=self.analysis_unit,
            row=row,
            col=col,
            use_old_value=False,
        )
        new_prevalence = self._get_prevalence_str()
        calc_fncs.push_field_edit(
            self._field_history,
            owner=self,
            restore_state=self.restore_analysis_unit_and_table,
            old_state=(old_analysis_unit, old_table, old_prevalence),
            new_state=(new_analysis_unit, new_table, new_prevalence),
        )

    def _report_raw_effect_update_failure(
        self, error, old_analysis_unit, old_table, old_prevalence
    ) -> None:
        message = "Could not compute study effects from the edited raw data: %s" % error
        QMessageBox.warning(self, "Warning", message)
        self.restore_analysis_unit_and_table(
            old_analysis_unit, old_table, old_prevalence
        )

    def restore_analysis_unit(self, old_analysis_unit):
        self.analysis_unit = copy.deepcopy(old_analysis_unit)

        self.initialize_form()
        self._update_raw_data()
        self._update_data_table()
        if self._calculator_async:
            self.set_current_effect(after=self.update_back_calculation_button)
        else:
            self.set_current_effect()
            self.update_back_calculation_button()

    def restore_table(self, old_table_data):
        old_table_data = tabular_data.normalize_rows(old_table_data)
        if not old_table_data:
            return
        nrows = min(len(old_table_data), self.two_by_two_table.rowCount())
        ncols = min(len(old_table_data[0]), self.two_by_two_table.columnCount())

        for row in range(nrows):
            for col in range(ncols):
                self._set_val(row, col, old_table_data[row][col])
        self._update_data_table()
        self._mark_table_consistent()

    def restore_analysis_unit_and_table(
        self, old_analysis_unit, old_table, old_prevalence
    ):
        self.restore_analysis_unit(old_analysis_unit)
        self.restore_table(old_table)
        self.prevalence_text_box.setText(old_prevalence)

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

    def get_total_subjects(self):
        return self._get_int(2, 2)

    def _get_table_values(self):
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

    def _clear_derived_effect_previews(self):
        for metric in DIAGNOSTIC_METRICS:
            self.analysis_unit.set_effect_for_source(
                "derived_preview", metric, self.group_comparison, None, None, None
            )

    def impute_effects_in_analysis_unit(self, *, after=None):
        counts = self.get_raw_diagnostic_data()
        tp, fn, fp, tn = counts["TP"], counts["FN"], counts["FP"], counts["TN"]
        can_calculate_sens = tp is not None and fn is not None
        can_calculate_spec = tn is not None and fp is not None
        if not can_calculate_sens:
            tp, fn = 0, 0
        if not can_calculate_spec:
            tn, fp = 0, 0

        if self._calculator_async:
            self._request_diagnostic_raw_effects(
                [tp, fn, fp, tn], can_calculate_sens, can_calculate_spec, after
            )
            return

        self._impute_local_diagnostic_effects(
            tp, fn, fp, tn, can_calculate_sens, can_calculate_spec
        )

    def _request_diagnostic_raw_effects(
        self, raw_counts, can_calculate_sens, can_calculate_spec, after
    ) -> None:
        if not can_calculate_sens and not can_calculate_spec:
            if after is not None:
                after()
            return
        eligible_metrics = self._eligible_diagnostic_effects(
            can_calculate_sens, can_calculate_spec
        )

        def apply(results):
            self._apply_worker_diagnostic_effects(results, eligible_metrics)
            if after is not None:
                after()

        self._request_calculator(
            [
                {
                    "id": "raw-effects",
                    "operation": "calculate_raw_effects",
                    "args": {
                        "data_type": DIAGNOSTIC,
                        "effect": None,
                        "raw_data": raw_counts,
                        "confidence_level": self.confidence_level,
                    },
                }
            ],
            apply,
            lambda _error: self.back_calculate_button.setEnabled(False),
        )

    def _eligible_diagnostic_effects(self, can_calculate_sens, can_calculate_spec):
        metrics = set()
        if can_calculate_sens:
            metrics.add("Sens")
        if can_calculate_spec:
            metrics.add("Spec")
        entered_counts = self.get_raw_diagnostic_data()
        if all(value is not None for value in entered_counts.values()):
            metrics.update(DIAGNOSTIC_METRICS)
        return metrics

    def _apply_worker_diagnostic_effects(self, results, eligible_metrics) -> None:
        effect_results = results.get("raw-effects")
        if isinstance(effect_results, dict):
            for metric in eligible_metrics:
                values = effect_results.get(metric)
                if isinstance(values, (list, tuple)) and len(values) == 3:
                    self.analysis_unit.set_effect_and_ci(
                        metric,
                        self.group_comparison,
                        values[0],
                        values[1],
                        values[2],
                        confidence_multiplier=self.confidence_multiplier,
                    )

    def _impute_local_diagnostic_effects(
        self, tp, fn, fp, tn, can_calculate_sens, can_calculate_spec
    ) -> None:
        ests_and_cis = self._calculator_service().diagnostic_effects_for_study(
            tp,
            fn,
            fp,
            tn,
            metrics=DIAGNOSTIC_METRICS,
            confidence_level=self.confidence_level,
        )
        for metric in DIAGNOSTIC_METRICS:
            if metric.lower() == "sens" and not can_calculate_sens:
                continue
            elif metric.lower() == "spec" and not can_calculate_spec:
                continue

            est, lower, upper = self._calculator_service().effect_triplet(
                ests_and_cis[metric],
                "calc_scale",
                metric=metric,
            )
            self.analysis_unit.set_effect_and_ci(
                metric,
                self.group_comparison,
                est,
                lower,
                upper,
                confidence_multiplier=self.confidence_multiplier,
            )

    def _get_row_col(self, field):
        row = 0 if field in ("FP", "TP") else 1
        col = 1 if field in ("FP", "TN") else 0
        return (row, col)

    def update_2x2_table(self, imputed_dict):
        """Fill in entries in 2x2 table and add data to analysis_unit"""
        # reset relevant column and sums column if we have new data
        if imputed_dict["TP"] and imputed_dict["FN"]:
            self.clear_column(0)
            self.clear_column(2)
        if imputed_dict["TN"] and imputed_dict["FP"]:
            self.clear_column(1)
            self.clear_column(2)

        for field in ["FP", "TP", "TN", "FN"]:
            if (field in imputed_dict) and (imputed_dict[field] is not None):
                row, col = self._get_row_col(field)
                self._set_val(row, col, imputed_dict[field])
                raw_data_index = DIAG_FIELDS_TO_RAW_INDICES[field]

                # Preserve blanks while storing the imputed count.
                self.analysis_unit.groups[self.group_comparison].raw_data[
                    raw_data_index
                ] = (
                    None
                    if not is_a_float(imputed_dict[field])
                    else float(imputed_dict[field])
                )

    def _update_analysis_unit(self):
        """Copy the table values to the analysis unit."""
        raw_dict = self.get_raw_diagnostic_data()  # values are floats or None
        for field in raw_dict.keys():
            i = DIAG_FIELDS_TO_RAW_INDICES[field]
            self.analysis_unit.groups[self.group_comparison].raw_data[i] = raw_dict[
                field
            ]

    def get_raw_diagnostic_data(self, convert_none_to_na_string=False):
        """Return TP, FN, FP, and TN values from the table."""
        empty_value = "NA" if convert_none_to_na_string else None

        d = {}
        d["TP"] = (
            float(self._get_int(0, 0)) if not self._is_empty(0, 0) else empty_value
        )
        d["FN"] = (
            float(self._get_int(1, 0)) if not self._is_empty(1, 0) else empty_value
        )
        d["FP"] = (
            float(self._get_int(0, 1)) if not self._is_empty(0, 1) else empty_value
        )
        d["TN"] = (
            float(self._get_int(1, 1)) if not self._is_empty(1, 1) else empty_value
        )
        return d

    def _raw_count_table_is_all_zero(self):
        counts = self.get_raw_diagnostic_data()
        return all(value is not None and value == 0 for value in counts.values())

    def _text_box_value_is_between_bounds(self, val_str, new_text):
        if is_empty(new_text):
            return True, ""
        if self._calculator_async:
            return self._validate_worker_effect_value(val_str, new_text)
        ci_param = {"est": "est", "lower": "low", "upper": "high"}.get(val_str)
        is_prevalence = val_str == "prevalence"
        if ci_param is None and not is_prevalence:
            return True, ""
        return self._evaluate_local_effect_value(new_text, ci_param, is_prevalence)

    def _validate_worker_effect_value(self, val_str, new_text):
        try:
            display_value = calc_fncs.numeric_value(new_text)
            if val_str == "prevalence":
                return 0 <= display_value <= 1, display_value
            if val_str not in {"est", "lower", "upper"}:
                return True, ""
            values = {
                "est": self.effect_text_box.text(),
                "lower": self.lower_text_box.text(),
                "upper": self.upper_text_box.text(),
            }
            values[val_str] = new_text
            good, _message = calc_fncs.between_bounds(
                est=values["est"], low=values["lower"], high=values["upper"]
            )
            return good, display_value
        except ValueError:
            return False, False

    def _evaluate_local_effect_value(self, new_text, ci_param, is_prevalence):
        try:
            with ExitStack() as signal_blockers:
                for widget in self.entry_widgets:
                    signal_blockers.enter_context(QSignalBlocker(widget))
                options = {}
                if is_prevalence:
                    options = {
                        "opt_cmp_fn": lambda x: 0 <= calc_fncs.numeric_value(x) <= 1,
                        "opt_cmp_msg": "Prevalence must be between 0 and 1.",
                    }
                display_scale_val = calc_fncs.evaluate(
                    new_text=new_text,
                    analysis_unit=self.analysis_unit,
                    current_effect=self.current_effect,
                    group_comparison=self.group_comparison,
                    conv_to_disp_scale=partial(
                        self._calculator_service().diagnostic_convert_scale,
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
                    **options,
                )
        except Exception:
            return False, False
        return True, "" if is_prevalence else display_scale_val

    def _text_from_value(self, value):
        if value == "est":
            return str(self.effect_text_box.text())
        elif value == "lower":
            return str(self.lower_text_box.text())
        elif value == "upper":
            return str(self.upper_text_box.text())
        elif value == "prevalence":
            return str(self.prevalence_text_box.text())
        return None  # Unknown value key.

    def val_changed(self, val_str):
        # Backup form state
        old_analysis_unit, old_table = self._save_analysis_unit_and_table_state(
            table=self.two_by_two_table,
            analysis_unit=self.analysis_unit,
            use_old_value=False,
        )
        old_prevalence = self.current_prevalence

        new_text = self._text_from_value(val_str)

        no_errors, display_scale_val = self._text_box_value_is_between_bounds(
            val_str, new_text
        )
        if self._calculator_async:
            if not no_errors:
                self._mark_table_invalid(self._validation_guidance(val_str, new_text))
                self._focus_value_field(val_str)
                required(
                    self.buttonBox.button(QDialogButtonBox.StandardButton.Ok),
                    "diagnostic calculator OK button",
                ).setEnabled(False)
                return
            if val_str == "prevalence":
                new_analysis_unit, new_table = self._save_analysis_unit_and_table_state(
                    table=self.two_by_two_table,
                    analysis_unit=self.analysis_unit,
                    use_old_value=False,
                )
                new_prevalence = self._get_prevalence_str()
                calc_fncs.push_field_edit(
                    self._field_history,
                    owner=self,
                    restore_state=self.restore_analysis_unit_and_table,
                    old_state=(old_analysis_unit, old_table, old_prevalence),
                    new_state=(new_analysis_unit, new_table, new_prevalence),
                )
                self.current_prevalence = new_prevalence
                self.update_back_calculation_button()
                required(
                    self.buttonBox.button(QDialogButtonBox.StandardButton.Ok),
                    "diagnostic calculator OK button",
                ).setEnabled(True)
                self._mark_table_consistent()
                return

            calculation_value = (
                None
                if is_empty(new_text)
                else float(display_scale_val)
            )

            def store_value(results):
                value = results["calculation-value"]
                if val_str == "est":
                    self.analysis_unit.set_effect(
                        self.current_effect, self.group_comparison, value
                    )
                elif val_str == "lower":
                    self.analysis_unit.set_lower(
                        self.current_effect, self.group_comparison, value
                    )
                else:
                    self.analysis_unit.set_upper(
                        self.current_effect, self.group_comparison, value
                    )
                new_analysis_unit, new_table = self._save_analysis_unit_and_table_state(
                    table=self.two_by_two_table,
                    analysis_unit=self.analysis_unit,
                    use_old_value=False,
                )
                new_prevalence = self._get_prevalence_str()
                calc_fncs.push_field_edit(
                    self._field_history,
                    owner=self,
                    restore_state=self.restore_analysis_unit_and_table,
                    old_state=(old_analysis_unit, old_table, old_prevalence),
                    new_state=(new_analysis_unit, new_table, new_prevalence),
                )
                self.current_prevalence = new_prevalence
                self.update_back_calculation_button()
                required(
                    self.buttonBox.button(QDialogButtonBox.StandardButton.Ok),
                    "diagnostic calculator OK button",
                ).setEnabled(True)
                self._mark_table_consistent()

            def conversion_failed(_error):
                self._focus_value_field(val_str)

            self._request_calculator(
                [
                    {
                        "id": "calculation-value",
                        "operation": "diagnostic_convert_scale",
                        "args": {
                            "x": calculation_value,
                            "metric_name": self.current_effect,
                            "convert_to": "calc.scale",
                        },
                    }
                ],
                store_value,
                conversion_failed,
            )
            return
        if no_errors is False:  # There are errors
            guidance = self._validation_guidance(val_str, new_text)
            self.restore_analysis_unit_and_table(
                old_analysis_unit, old_table, old_prevalence
            )
            with ExitStack() as signal_blockers:
                for widget in self.entry_widgets:
                    signal_blockers.enter_context(QSignalBlocker(widget))
                if val_str == "est":
                    self.effect_text_box.setFocus()
                elif val_str == "lower":
                    self.lower_text_box.setFocus()
                elif val_str == "upper":
                    self.upper_text_box.setFocus()
                elif val_str == "prevalence":
                    self.prevalence_text_box.setFocus()
            self._mark_table_invalid(guidance)
            return

        try:
            if display_scale_val not in EMPTY_VALS:
                display_scale_val = float(display_scale_val)
            else:
                display_scale_val = None
        except ValueError:
            # Ignore incomplete numeric input while the user is still editing.
            return None

        calculation_scale_value = self._calculator_service().diagnostic_convert_scale(
            display_scale_val, self.current_effect, convert_to="calc.scale"
        )

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
        elif val_str == "prevalence":
            pass

        new_analysis_unit, new_table = self._save_analysis_unit_and_table_state(
            table=self.two_by_two_table,
            analysis_unit=self.analysis_unit,
            use_old_value=False,
        )
        new_prevalence = self._get_prevalence_str()

        calc_fncs.push_field_edit(
            self._field_history,
            owner=self,
            restore_state=self.restore_analysis_unit_and_table,
            old_state=(old_analysis_unit, old_table, old_prevalence),
            new_state=(new_analysis_unit, new_table, new_prevalence),
        )

        self.current_prevalence = new_prevalence
        self._mark_table_consistent()

    def _focus_value_field(self, val_str):
        field = {
            "est": self.effect_text_box,
            "lower": self.lower_text_box,
            "upper": self.upper_text_box,
            "prevalence": self.prevalence_text_box,
        }.get(val_str)
        if field is not None:
            field.setFocus()

    def _validation_guidance(self, val_str, new_text):
        labels = {
            "est": "Effect estimate",
            "lower": "Lower confidence limit",
            "upper": "Upper confidence limit",
            "prevalence": "Prevalence",
        }
        label = labels.get(val_str, "Entered value")
        try:
            value = calc_fncs.numeric_value(new_text)
        except ValueError:
            return "{} must be numeric.".format(label)
        if val_str == "prevalence" and not 0 <= value <= 1:
            return "Prevalence must be between 0 and 1."

        values = {
            "est": self.effect_text_box.text(),
            "lower": self.lower_text_box.text(),
            "upper": self.upper_text_box.text(),
        }
        good, message = calc_fncs.between_bounds(
            est=values["est"], low=values["lower"], high=values["upper"]
        )
        if not good and message:
            return str(message).replace("!", ".")
        return "Enter a valid diagnostic effect estimate and confidence interval."

    def effect_changed(self):
        self.current_effect = str(self.effect_combo_box.currentText())
        self._invalidate_calculator_responses()
        if self._calculator_async:
            self.set_current_effect(after=self.update_back_calculation_button)
        else:
            self.set_current_effect()
            self.update_back_calculation_button()
        self._mark_table_consistent()

    def _update_raw_data(self):
        """Populates the 2x2 table with whatever parametric data was provided"""
        with QSignalBlocker(self.two_by_two_table):
            field_index = 0
            for col in (0, 1):
                for row in (0, 1):
                    val = self.analysis_unit.get_raw_data_for_group(
                        self.group_comparison
                    )[field_index]
                    if val is not None:
                        try:
                            val = str(int(val))
                        except (TypeError, ValueError, OverflowError):
                            val = str(val)
                        item = QTableWidgetItem(val)
                        self.two_by_two_table.setItem(row, col, item)
                    field_index += 1

    def _populate_effect_cmbo_box(self):
        # Back-calculation is currently supported for sensitivity/specificity.
        effects = BACK_CALCULATABLE_DIAGNOSTIC_EFFECTS
        with QSignalBlocker(self.effect_combo_box):
            self.effect_combo_box.addItems(effects)
            self.effect_combo_box.setCurrentIndex(0)

    def set_current_effect(self, *, after=None):
        """Fill in effect text boxes with data from analysis_unit"""
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
        self.effect_group.setTitle(
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
                    "operation": "diagnostic_convert_scale",
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
                    "diagnostic",
                    (results["effect"], results["lower"], results["upper"]),
                )
                if after is not None:
                    after()

            self._request_calculator(calls, rendered)
            return
        calc_fncs.set_current_effect_from_value(
            analysis_unit=self.analysis_unit,
            txt_boxes=txt_boxes,
            current_effect=self.current_effect,
            group_comparison=self.group_comparison,
            data_type="diagnostic",
            confidence_multiplier=self.confidence_multiplier,
            source=source,
        )

    def _update_data_table(self):
        """Try to calculate rest of 2x2 table from existing cells"""
        with ExitStack() as signal_blockers:
            for widget in self.entry_widgets:
                signal_blockers.enter_context(QSignalBlocker(widget))
            params = self._get_table_values()
            computed_params = calc_fncs.compute_2x2_table_from_inner_counts(params)
            if computed_params:
                self._set_vals(computed_params)  # computed --> table widget

            # Compute prevalence if possible
            if (computed_params["c1sum"] not in EMPTY_VALS) and (
                computed_params["total"] not in EMPTY_VALS
            ):
                prevalence = float(computed_params["c1sum"]) / float(
                    computed_params["total"]
                )
                prev_str = str(prevalence)[:7]
                self.prevalence_text_box.setText("%s" % prev_str)
        self._grow_all_raw_data_columns_to_contents()

    def clear_column(self, col):
        """Clears out column in table and analysis_unit"""
        for row in range(3):
            self._set_val(row, col, None)

        self._update_analysis_unit()

    def clear_form(self):
        self._pending_back_calculation = None
        self.calculated_values_group.hide()
        self.calculated_values_label.clear()

        # For undo/redo
        old_analysis_unit, old_table = self._save_analysis_unit_and_table_state(
            table=self.two_by_two_table,
            analysis_unit=self.analysis_unit,
            use_old_value=False,
        )
        old_prevalence = self._get_prevalence_str()

        keys = ["c11", "c12", "r1sum", "c21", "c22", "r2sum", "c1sum", "c2sum", "total"]
        blank_vals = dict(list(zip(keys, [""] * len(keys))))

        self._set_vals(blank_vals)
        self._update_analysis_unit()

        for metric in DIAGNOSTIC_METRICS:
            self.analysis_unit.set_effect_for_source(
                "entered", metric, self.group_comparison, None, None, None
            )

        # clear line edits
        self.set_current_effect()
        with QSignalBlocker(self.prevalence_text_box):
            self.prevalence_text_box.setText("")

        calc_fncs.set_table_cells_editable(
            self.two_by_two_table, DIAGNOSTIC_RAW_COUNT_CELLS
        )

        new_analysis_unit, new_table = self._save_analysis_unit_and_table_state(
            table=self.two_by_two_table,
            analysis_unit=self.analysis_unit,
            use_old_value=False,
        )
        new_prevalence = self._get_prevalence_str()

        calc_fncs.push_field_edit(
            self._field_history,
            owner=self,
            restore_state=self.restore_analysis_unit_and_table,
            old_state=(old_analysis_unit, old_table, old_prevalence),
            new_state=(new_analysis_unit, new_table, new_prevalence),
        )

    def update_back_calculation_button(self, engage=False):
        if not engage:
            self._pending_back_calculation = None
            self.calculated_values_group.hide()
            self.calculated_values_label.clear()

        if self.confidence_multiplier is None:
            self.back_calculate_button.setEnabled(False)
            return

        if self._calculator_async:
            self._update_back_calculation_async(engage)
            return

        try:
            diagnostic_data = self._local_back_calculation_data()
            imputed = self._calculator_service().impute_diagnostic_data(diagnostic_data)
            self._apply_local_back_calculation_result(imputed, engage)
        except Exception as error:
            self._show_back_calculation_error(error)

    def _local_back_calculation_data(self):
        diagnostic_data = self._local_back_calculation_effects()
        total = self.get_total_subjects()
        diagnostic_data["total"] = float(total) if is_a_float(total) else None
        try:
            diagnostic_data["prev"] = calc_fncs.numeric_value(
                self.prevalence_text_box.text()
            )
        except ValueError:
            diagnostic_data["prev"] = None
        diagnostic_data["conf.level"] = self.confidence_level
        diagnostic_data.update(self.get_raw_diagnostic_data())
        return diagnostic_data

    def _local_back_calculation_effects(self):
        diagnostic_data = {}
        for effect in BACK_CALCULATABLE_DIAGNOSTIC_EFFECTS:
            estimate, lower, upper = self.analysis_unit.get_effect_and_ci_for_source(
                "entered", effect, self.group_comparison, self.confidence_multiplier
            )
            converted = [
                self._calculator_service().diagnostic_convert_scale(
                    value, effect, convert_to="display.scale"
                )
                for value in (estimate, lower, upper)
            ]
            for suffix, value in zip(("", ".lb", ".ub"), converted):
                try:
                    diagnostic_data[f"{effect.lower()}{suffix}"] = float(value)
                except (TypeError, ValueError):
                    pass
        return diagnostic_data

    def _apply_local_back_calculation_result(self, imputed, engage):
        if imputed.get("FAIL") or not any(
            imputed.get(field) is not None for field in ("TP", "TN", "FP", "FN")
        ):
            self.back_calculate_button.setEnabled(False)
            return
        can_apply = self._local_back_calculation_can_apply(imputed)
        self.back_calculate_button.setEnabled(can_apply)
        if engage and can_apply:
            self._show_back_calculation_preview(imputed)

    def _local_back_calculation_can_apply(self, imputed):
        new_data = (imputed["TP"], imputed["FP"], imputed["FN"], imputed["TN"])
        old_data = (
            self._get_int(0, 0),
            self._get_int(0, 1),
            self._get_int(1, 0),
            self._get_int(1, 1),
        )
        return any(
            old in EMPTY_VALS and new not in EMPTY_VALS
            for old, new in zip(old_data, new_data)
        )

    def _show_back_calculation_error(self, error):
        self._pending_back_calculation = None
        self.calculated_values_label.setText(
            f"Could not prepare calculated values: {error}"
        )
        self.calculated_values_group.show()
        self.back_calculate_button.setFocus()
        self._request_initial_content_refit()

    def _update_back_calculation_async(self, engage):
        self._request_calculator(
            self._back_calculation_conversion_calls(),
            lambda converted: self._request_diagnostic_imputation(converted, engage),
        )

    def _back_calculation_conversion_calls(self):
        calls = []
        for effect in BACK_CALCULATABLE_DIAGNOSTIC_EFFECTS:
            values = self.analysis_unit.get_effect_and_ci_for_source(
                "entered", effect, self.group_comparison, self.confidence_multiplier
            )
            for suffix, value in zip(("est", "lower", "upper"), values):
                calls.append(
                    {
                        "id": f"{effect}-{suffix}",
                        "operation": "diagnostic_convert_scale",
                        "args": {
                            "x": value,
                            "metric_name": effect,
                            "convert_to": "display.scale",
                        },
                    }
                )
        return calls

    def _request_diagnostic_imputation(self, converted, engage) -> None:
        diagnostic_data = self._diagnostic_imputation_data(converted)
        self._request_calculator(
            [
                {
                    "id": "imputed",
                    "operation": "impute_diagnostic_data",
                    "args": {"diagnostic_data": diagnostic_data},
                }
            ],
            lambda results: self._update_worker_back_calculation_preview(
                results, engage
            ),
        )

    def _diagnostic_imputation_data(self, converted):
        diagnostic_data = {}
        for effect in BACK_CALCULATABLE_DIAGNOSTIC_EFFECTS:
            for suffix, key in zip(("est", "lower", "upper"), ("", ".lb", ".ub")):
                value = converted[f"{effect}-{suffix}"]
                if value is not None:
                    diagnostic_data[f"{effect.lower()}{key}"] = float(value)
        total = self.get_total_subjects()
        diagnostic_data["total"] = float(total) if is_a_float(total) else None
        try:
            diagnostic_data["prev"] = calc_fncs.numeric_value(
                self.prevalence_text_box.text()
            )
        except ValueError:
            diagnostic_data["prev"] = None
        diagnostic_data["conf.level"] = self.confidence_level
        diagnostic_data.update(self.get_raw_diagnostic_data())
        return diagnostic_data

    def _update_worker_back_calculation_preview(self, results, engage) -> None:
        imputed = results.get("imputed")
        if not self._has_imputed_diagnostic_counts(imputed):
            self.back_calculate_button.setEnabled(False)
            return
        can_apply = self._worker_back_calculation_can_apply(imputed)
        self.back_calculate_button.setEnabled(can_apply)
        if engage and can_apply:
            self._show_back_calculation_preview(imputed)

    def _has_imputed_diagnostic_counts(self, value) -> bool:
        return (
            isinstance(value, dict)
            and not value.get("FAIL")
            and any(value.get(field) is not None for field in ("TP", "TN", "FP", "FN"))
        )

    def _worker_back_calculation_can_apply(self, imputed) -> bool:
        old_data = (
            self._get_int(0, 0),
            self._get_int(0, 1),
            self._get_int(1, 0),
            self._get_int(1, 1),
        )
        new_data = (
            imputed.get("TP"),
            imputed.get("FP"),
            imputed.get("FN"),
            imputed.get("TN"),
        )
        return any(old in EMPTY_VALS and new not in EMPTY_VALS for old, new in zip(old_data, new_data))

    def _show_back_calculation_preview(self, imputed) -> None:
        changes = self._diagnostic_back_calculation_changes(imputed)
        if not changes:
            self.back_calculate_button.setEnabled(False)
            return
        self._pending_back_calculation = dict(imputed)
        assumptions = (
            "RCMetaR reconstructed missing diagnostic counts from the entered "
            "sensitivity and specificity intervals, prevalence, and total sample "
            f"size using {self.confidence_level:g}% confidence."
        )
        self.calculated_values_label.setText(
            calc_fncs.format_calculated_values_preview(assumptions, changes)
        )
        self.calculated_values_group.show()
        self._request_initial_content_refit()

    def _diagnostic_back_calculation_changes(self, imputed):
        counts = self.get_raw_diagnostic_data()
        changes = self._diagnostic_count_changes(imputed, counts)
        margins = calc_fncs.compute_2x2_table_from_inner_counts(
            {
                "c11": counts["TP"],
                "c12": counts["FP"],
                "c21": counts["FN"],
                "c22": counts["TN"],
                **{key: None for key in ("r1sum", "r2sum", "c1sum", "c2sum", "total")},
            }
        )
        changes.extend(self._diagnostic_margin_changes(margins))
        prevalence_change = self._diagnostic_prevalence_change(margins)
        if prevalence_change is not None:
            changes.append(prevalence_change)
        return changes

    def _diagnostic_count_changes(self, imputed, counts):
        count_cells = {
            "TP": (0, 0, "True positives"),
            "FP": (0, 1, "False positives"),
            "FN": (1, 0, "False negatives"),
            "TN": (1, 1, "True negatives"),
        }
        counts = self.get_raw_diagnostic_data()
        changes = []
        for field, (row, column, label) in count_cells.items():
            value = imputed.get(field)
            if value is None:
                continue
            try:
                displayed_value = int(calc_fncs.numeric_value(value))
            except ValueError:
                displayed_value = value
            old_value = self._get_int(row, column)
            if old_value != displayed_value:
                changes.append((label, old_value, displayed_value))
                counts[field] = displayed_value
        return changes

    def _diagnostic_margin_changes(self, margins):
        changes = []
        margin_cells = (
            (0, 2, "r1sum", "Test-positive total"),
            (1, 2, "r2sum", "Test-negative total"),
            (2, 0, "c1sum", "Disease-positive total"),
            (2, 1, "c2sum", "Disease-negative total"),
            (2, 2, "total", "All participants"),
        )
        for row, column, key, label in margin_cells:
            old_value = self._get_int(row, column)
            new_value = margins[key]
            if old_value != new_value:
                changes.append((label, old_value, new_value))
        return changes

    def _diagnostic_prevalence_change(self, margins):
        total = margins["total"]
        disease_positive = margins["c1sum"]
        old_prevalence = self._get_prevalence_str()
        new_prevalence = (
            str(float(disease_positive) / float(total))[:7]
            if total not in EMPTY_VALS and total != 0 and disease_positive not in EMPTY_VALS
            else ""
        )
        if old_prevalence != new_prevalence:
            return "Prevalence", old_prevalence, new_prevalence
        return None

    def accept(self):
        candidate = self._pending_back_calculation
        if candidate is not None and not self._apply_back_calculation(candidate):
            return
        super().accept()

    def _apply_back_calculation(self, candidate):
        count_cells = {
            "TP": (0, 0),
            "FP": (0, 1),
            "FN": (1, 0),
            "TN": (1, 1),
        }
        for field, (row, column) in count_cells.items():
            value = candidate.get(field)
            if value is None:
                continue
            message = self.cell_data_invalid(str(value))
            if message:
                self._mark_table_invalid(message)
                self.two_by_two_table.setCurrentCell(row, column)
                self.two_by_two_table.setFocus()
                return False

        old_analysis_unit, old_table = self._save_analysis_unit_and_table_state(
            table=self.two_by_two_table,
            analysis_unit=self.analysis_unit,
            use_old_value=False,
        )
        old_prevalence = self._get_prevalence_str()
        try:
            self.update_2x2_table(candidate)
            self._update_data_table()
            self._update_analysis_unit()
        except Exception as error:
            self.restore_analysis_unit_and_table(
                old_analysis_unit, old_table, old_prevalence
            )
            self._mark_table_invalid(f"Could not apply calculated values: {error}")
            self.back_calculate_button.setFocus()
            return False

        new_analysis_unit, new_table = self._save_analysis_unit_and_table_state(
            table=self.two_by_two_table,
            analysis_unit=self.analysis_unit,
            use_old_value=False,
        )
        new_prevalence = self._get_prevalence_str()
        calc_fncs.push_field_edit(
            self._field_history,
            owner=self,
            restore_state=self.restore_analysis_unit_and_table,
            old_state=(old_analysis_unit, old_table, old_prevalence),
            new_state=(new_analysis_unit, new_table, new_prevalence),
            description="Apply calculated diagnostic values",
        )
        self._pending_back_calculation = None
        self.calculated_values_group.hide()
        return True

    def undo(self):
        self._field_history.undo()

    def redo(self):
        self._field_history.redo()
