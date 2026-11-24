# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Calculator input controls, validation and field sizing."""

import sys
from collections.abc import Callable, Iterable
from weakref import WeakKeyDictionary
from PyQt6.QtCore import QSignalBlocker, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPaintEvent
from PyQt6.QtWidgets import (
    QBoxLayout,
    QDialog,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QStyle,
    QStyleOptionFrame,
    QStyledItemDelegate,
    QWIDGETSIZE_MAX,
)
from rc_metastudio.analysis.validation import EMPTY_VALS, validate_confidence_interval_order
from rc_metastudio import input_text
from rc_metastudio.qt_layout import configure_context_label


CALC_NUM_DIGITS = 4


def add_study_context(dialog: QDialog, layout: QBoxLayout, study_name: str) -> None:
    if study_name:
        dialog.setWindowTitle(f"Study data — {study_name}")
        label = QLabel(study_name, dialog)
        label.setTextFormat(Qt.TextFormat.PlainText)
        configure_context_label(label)
        layout.insertWidget(0, label)






_EFFECT_CI_BASE_MINIMUM_WIDTHS = WeakKeyDictionary()


class NumericSummaryDelegate(QStyledItemDelegate):
    """Compact table painting; the editor and item retain round-trip-safe text."""

    def displayText(self, value, locale):
        number, valid = input_text.parse_decimal(value)
        return format(number, ".6g") if valid else str(value)

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if index.data(Qt.ItemDataRole.UserRole) is False and input_text.parse_decimal(index.data())[1]:
            option.backgroundBrush = QBrush(QColor(214, 169, 58, 80))
        header = index.model().headerData(index.column(), Qt.Orientation.Horizontal)
        if header in {"SE", "Variance", "Lower", "Upper"}:
            number, valid = input_text.parse_decimal(index.data())
            if valid:
                option.text = format_calculator_display_value(number)


class PrevalenceEdit(QLineEdit):
    """Round only the unfocused readout; editing and calculations use exact text."""

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        event = a0
        number, valid = input_text.parse_decimal(self.text())
        if self.hasFocus() or not valid:
            return super().paintEvent(event)
        option = QStyleOptionFrame()
        self.initStyleOption(option)
        painter = QPainter(self)
        style = self.style()
        assert style is not None
        style.drawPrimitive(QStyle.PrimitiveElement.PE_PanelLineEdit, option, painter, self)
        rect = style.subElementRect(QStyle.SubElement.SE_LineEditContents, option, self)
        rect.adjust(2, 0, -2, 0)
        painter.setPen(self.palette().text().color())
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         format_calculator_display_value(number))


def numeric_value(value):
    """Return finite interface numeric input using explicit decimal rules."""
    number, valid = input_text.parse_decimal(value)
    if not valid:
        raise ValueError(
            "Enter a finite number using a decimal point or decimal comma."
        )
    return number




def count_cell_error(text: object) -> str | None:
    if input_text.is_blank(text):
        return None
    try:
        value = numeric_value(text)
    except ValueError:
        return "Enter a number."
    if not value.is_integer():
        return "Counts must be whole numbers."
    if value < 0:
        return "Counts cannot be negative."
    return None


COUNT_TABLE_CELLS = {
    "c11": (0, 0), "c12": (0, 1), "c21": (1, 0), "c22": (1, 1),
    "r1sum": (0, 2), "r2sum": (1, 2),
    "c1sum": (2, 0), "c2sum": (2, 1), "total": (2, 2),
}


def read_count_table(read_count):
    return {key: read_count(*cell) for key, cell in COUNT_TABLE_CELLS.items()}


def compute_2x2_table_from_inner_counts(params):
    """Derive 2x2 margins from the four independent inner count cells."""
    c11 = params["c11"]
    c12 = params["c12"]
    c21 = params["c21"]
    c22 = params["c22"]

    def add_if_present(left, right):
        if left in EMPTY_VALS or right in EMPTY_VALS:
            return None
        return left + right

    r1sum = add_if_present(c11, c12)
    r2sum = add_if_present(c21, c22)
    c1sum = add_if_present(c11, c21)
    c2sum = add_if_present(c12, c22)
    total = add_if_present(r1sum, r2sum)
    if total in EMPTY_VALS:
        total = add_if_present(c1sum, c2sum)

    return {
        "c11": c11,
        "c12": c12,
        "r1sum": r1sum,
        "c21": c21,
        "c22": c22,
        "r2sum": r2sum,
        "c1sum": c1sum,
        "c2sum": c2sum,
        "total": total,
    }


def set_table_item_editable(item, editable):
    if item is None:
        return
    flags = item.flags()
    if editable:
        flags = flags | Qt.ItemFlag.ItemIsEditable
    else:
        flags = flags & ~Qt.ItemFlag.ItemIsEditable
    item.setFlags(flags)


def set_table_cells_editable(table, editable_cells):
    table.blockSignals(True)
    try:
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                set_table_item_editable(
                    table.item(row, col), (row, col) in editable_cells
                )
    finally:
        table.blockSignals(False)


def fit_effect_ci_line_edits_to_contents(
    line_edits, digits=CALC_NUM_DIGITS, semantic_samples=None
):
    """Size calculator values from a semantic contract when one is supplied."""
    if semantic_samples is None:
        semantic_samples = ()
    for line_edit in line_edits:
        if line_edit is None:
            continue

        policy = line_edit.sizePolicy()

        if semantic_samples:
            content_width = max(
                line_edit.fontMetrics().horizontalAdvance(sample)
                for sample in (*semantic_samples, line_edit.text())
            )
            text_margins = line_edit.textMargins()
            frame_width = line_edit.style().pixelMetric(
                QStyle.PixelMetric.PM_DefaultFrameWidth, None, line_edit
            )
            required_width = (
                content_width
                + text_margins.left()
                + text_margins.right()
                + (2 * frame_width)
                + 12
            )
        else:
            signed_precision_sample = "-0." + ("8" * digits)
            base_minimum_width = _EFFECT_CI_BASE_MINIMUM_WIDTHS.get(line_edit)
            if base_minimum_width is None:
                base_minimum_width = line_edit.minimumWidth()
                _EFFECT_CI_BASE_MINIMUM_WIDTHS[line_edit] = base_minimum_width
            content_width = max(
                line_edit.fontMetrics().horizontalAdvance(value)
                for value in (signed_precision_sample, str(line_edit.text()))
            )
            required_width = max(base_minimum_width, content_width + 12)
        # layout-audit: allow=numeric-domain-control; reason=editor width follows representative values from its numeric domain
        line_edit.setMinimumWidth(required_width)
        # layout-audit: allow=numeric-domain-control; reason=editor width follows representative values from its numeric domain
        line_edit.setMaximumWidth(QWIDGETSIZE_MAX)
        line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, policy.verticalPolicy())
        if not line_edit.hasFocus():
            line_edit.setCursorPosition(0)


def format_calculator_display_value(value, digits=CALC_NUM_DIGITS):
    """Format presentation only; the analysis unit retains the exact value."""
    if value and (abs(value) < 10 ** -digits or abs(value) >= 1e8):
        return format(value, f".{digits}g")
    return format(value, f".{digits}f")


def binary_effect_display_samples(metric, digits=CALC_NUM_DIGITS):
    """Return semantic display-domain samples for a binary calculator metric."""
    precision = "0." + ("0" * digits)
    proportion_metrics = {"PR", "PLN", "PLO", "PAS", "PFT"}
    signed_unit_metrics = {"RD", "YUQ", "YUY"}
    positive_ratio_metrics = {"OR", "RR"}

    if metric in proportion_metrics:
        return (precision, "1." + ("0" * digits))
    if metric in signed_unit_metrics:
        return ("-1." + ("0" * digits), "1." + ("0" * digits))
    if metric == "AS":
        return ("-1.5708", "-1.0000", "1.5708")
    if metric in positive_ratio_metrics:
        return (
            precision,
            format_calculator_display_value(sys.float_info.max, digits),
        )
    return ("-" + precision, precision)


def continuous_effect_display_samples(metric, digits=CALC_NUM_DIGITS):
    """Return formatter-derived semantic samples for continuous effect fields.

    Continuous effect domains are mathematically unbounded, so values beyond
    these common display magnitudes remain reachable through QLineEdit's native
    horizontal navigation rather than forcing the dialog to grow indefinitely.
    """
    magnitude = 10.9999 if metric == "SMD" else 9999.9999
    return tuple(
        format_calculator_display_value(value, digits)
        for value in (-magnitude, magnitude)
    )


def diagnostic_effect_display_samples(metric, digits=CALC_NUM_DIGITS):
    """Return valid display-domain samples for diagnostic effect fields."""
    precision = "0." + ("0" * digits)
    if metric in {"Sens", "Spec"}:
        return (precision, "1." + ("0" * digits))
    return (precision, "9999." + ("9" * digits))


class CalculatorEffectFields:
    """Track drafts separately from the rendered values of the effect editors."""

    def __init__(self, estimate: QLineEdit, lower: QLineEdit, upper: QLineEdit) -> None:
        self.editors = {"est": estimate, "lower": lower, "upper": upper}
        self._committed: dict[str, str] = {}

    def is_pending(self, name: str) -> bool:
        return self.editors[name].text() != self._committed.get(name)

    def mark_committed(self, name: str) -> None:
        self._committed[name] = self.editors[name].text()

    def display(self, values: Iterable[float | None]) -> None:
        for (name, editor), value in zip(self.editors.items(), values, strict=True):
            with QSignalBlocker(editor):
                editor.setText("" if value is None else format_calculator_display_value(value))
                self.mark_committed(name)

    def commit_pending(self, apply: Callable[[str], None]) -> None:
        for name in self.editors:
            if self.is_pending(name):
                apply(name)


def snapshot_table_text(table):
    row_count, column_count = table.rowCount(), table.columnCount()

    empty_row = [None] * column_count
    cell_texts = []
    for _ in range(row_count):
        cell_texts.append(empty_row[:])

    for row in range(row_count):
        for col in range(column_count):
            item = table.item(row, col)
            cell_text = "" if item is None else item.text()
            cell_texts[row][col] = cell_text
    return cell_texts


def calculator_inputs_disabled(table, text_boxes):
    table_is_read_only = table_has_no_editable_cells(table)
    text_fields_are_disabled = all_text_fields_disabled(text_boxes)

    if table_is_read_only and text_fields_are_disabled:
        return True
    return False


def table_has_no_editable_cells(table):
    no_editable_cells = True
    row_count = table.rowCount()
    column_count = table.columnCount()
    for row in range(row_count):
        for col in range(column_count):
            item = table.item(row, col)
            if item is None:
                continue
            if (
                item.flags() & Qt.ItemFlag.ItemIsEditable
            ) == Qt.ItemFlag.ItemIsEditable:
                no_editable_cells = False
    return no_editable_cells


def all_text_fields_disabled(text_boxes):
    return not any([box.isEnabled() for box in text_boxes])


class CalculatorInputError(ValueError):
    """The user's draft needs correction before it can be applied."""


class CalculatorNumberError(CalculatorInputError):
    """The draft does not represent a finite number."""


def parse_calculator_value(text: str) -> float | None:
    if not text:
        return None
    try:
        return numeric_value(text)
    except ValueError as error:
        raise CalculatorNumberError("Enter a number.") from error


def validate_calculator_interval(field: str, value: float, displayed) -> None:
    bounds = dict(zip(("est", "lower", "upper"), displayed, strict=True))
    bounds[field] = value
    valid, message = validate_confidence_interval_order(
        bounds["est"], bounds["lower"], bounds["upper"]
    )
    if not valid:
        raise CalculatorInputError(message)
