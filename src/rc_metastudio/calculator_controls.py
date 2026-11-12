# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Calculator input controls, validation and field sizing."""

import sys
from functools import partial
from weakref import WeakKeyDictionary
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPaintEvent
from PyQt6.QtWidgets import (
    QLineEdit,
    QMessageBox,
    QSizePolicy,
    QStyle,
    QStyleOptionFrame,
    QStyledItemDelegate,
    QWIDGETSIZE_MAX,
)
from rc_metastudio.analysis_validation import EMPTY_VALS
from rc_metastudio import qt_text


CALC_NUM_DIGITS = 4






_EFFECT_CI_BASE_MINIMUM_WIDTHS = WeakKeyDictionary()


class NumericSummaryDelegate(QStyledItemDelegate):
    """Compact table painting; the editor and item retain round-trip-safe text."""

    def displayText(self, value, locale):
        number, valid = qt_text.parse_decimal(value)
        return format(number, ".6g") if valid else str(value)

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        header = index.model().headerData(index.column(), Qt.Orientation.Horizontal)
        if header in {"SE", "Variance", "Lower", "Upper"}:
            number, valid = qt_text.parse_decimal(index.data())
            if valid:
                option.text = format_calculator_display_value(number)


class PrevalenceEdit(QLineEdit):
    """Round only the unfocused readout; editing and calculations use exact text."""

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        event = a0
        number, valid = qt_text.parse_decimal(self.text())
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


def cell_text_is_blank(value):
    """Return whether Qt item text is blank."""
    return qt_text.is_blank(value)


def numeric_value(value):
    """Return finite interface numeric input using explicit decimal rules."""
    number, valid = qt_text.parse_decimal(value)
    if not valid:
        raise ValueError(
            "Enter an unambiguous finite number using '.' or ',' as decimal separator."
        )
    return number




def validate_confidence_interval_order(est=None, low=None, high=None):
    def less_than_if_numeric(left, right):
        try:
            return numeric_value(left) < numeric_value(right)
        except ValueError:
            return None

    comparison_result = less_than_if_numeric(low, est)
    comparison_is_available = True if comparison_result is not None else False
    if comparison_is_available and not comparison_result:
        error_message = "The lower CI must be less than the point estimate!"
        return False, error_message

    comparison_result = less_than_if_numeric(est, high)
    comparison_is_available = True if comparison_result is not None else False
    if comparison_is_available and not comparison_result:
        error_message = "The higher CI must be greater than the point estimate!"
        return False, error_message

    comparison_result = less_than_if_numeric(low, high)
    comparison_is_available = True if comparison_result is not None else False
    if comparison_is_available and not comparison_result:
        error_message = "The lower CI must be less than the higher CI!"
        return False, error_message

    return True, None


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
        # Keep a signed-unit value in the semantic sample set. It is inside the
        # arcsine domain and prevents native proportional fonts from making the
        # field narrower than the signed-unit metrics when users switch scales.
        return ("-1.5708", "-1.0000", "1.5708")
    if metric in positive_ratio_metrics:
        # Ratios are positive and unbounded, so use the exact text produced by
        # the renderer at the largest accepted finite binary64 value.
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
    # Diagnostic ratios are positive and unbounded. Keep common values visible;
    # larger entries remain reachable through native line-edit navigation.
    return (precision, "9999." + ("9" * digits))


def commit_calculator_edits(dialog):
    """Commit drafts before a mode change replaces the shared effect editors."""
    for name, field in (("est", dialog.effect_text_box), ("lower", dialog.lower_text_box), ("upper", dialog.upper_text_box)):
        if field.text() != field.property("calculatorValue"):
            dialog.val_changed(name)
    return not getattr(dialog, "_validation_failed", False)


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


def validate_calculator_input(
    new_text,
    analysis_unit,
    current_effect,
    arm_key,
    to_display_scale,
    confidence_bound=None,
    parent=None,
    additional_validator=None,
    validation_message=None,
    confidence_multiplier=None,
    *,
    source="entered",
):
    """Validate display-scale input against interval order or a field constraint."""
    if confidence_multiplier is None:
        raise ValueError("confidence multiplier must be specified")

    est, lower, upper = analysis_unit.get_effect_and_ci_for_source(
        source, current_effect, arm_key, confidence_multiplier
    )  # calc scale
    display_estimate, display_lower, display_upper = [
        to_display_scale(x) for x in (est, lower, upper)
    ]
    validate_updated_interval = partial(
        validate_confidence_interval_order, est=display_estimate, low=display_lower, high=display_upper
    )
    try:
        parsed_value = numeric_value(new_text)
    except ValueError:
        QMessageBox.warning(parent, "Warning", "Must be numeric!")
        raise Exception("error")
    if not additional_validator:  # est, lower, upper
        if confidence_bound is None:
            raise ValueError("confidence_bound is required for confidence-bound validation")
        (interval_is_valid, error_message) = validate_updated_interval(**{confidence_bound: new_text})
        if not interval_is_valid:
            QMessageBox.warning(parent, "Warning", error_message)
            raise Exception("error")
    else:  # something other than est, lower, upper (like correlation or prevalence)
        if not additional_validator(new_text):
            QMessageBox.warning(parent, "Warning", validation_message)
            raise Exception("error")
    return parsed_value  # display_scale_val
