# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Effect source selection and calculator readout presentation."""

import math
from typing import cast
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from rc_metastudio.analysis.catalog import BINARY_ONE_ARM_METRICS, CONTINUOUS_ONE_ARM_METRICS
from rc_metastudio.project.study import EffectSource
from rc_metastudio.analysis.validation import EMPTY_VALS
from rc_metastudio.calculators.service import CalculatorService, Numeric
from rc_metastudio.analysis.study_selection import raw_data_is_complete
from rc_metastudio.calculators.controls import (
    CalculatorEffectFields,
    parse_calculator_value,
    validate_calculator_interval,
    fit_effect_ci_line_edits_to_contents,
    format_calculator_display_value,
    binary_effect_display_samples,
    continuous_effect_display_samples,
    diagnostic_effect_display_samples,
)


_ONE_ARM_REQUIRED_VALUE_COUNTS = {
    **dict.fromkeys(BINARY_ONE_ARM_METRICS, 2),
    **dict.fromkeys(CONTINUOUS_ONE_ARM_METRICS, 3),
}


def calculator_effect_source(
    analysis_unit, arm_names, effect, arm_key, confidence_multiplier, *, input_mode=None
) -> EffectSource:
    """Return the active calculator effect authority.

    A partial raw-data edit does not produce a preview. Keep showing an
    entered effect in that state so back-calculation and direct editing remain
    usable; switch to the preview only after the active metric has one.
    """
    if input_mode == "estimate":
        return "entered"
    raw_data = analysis_unit.get_raw_data_for_arms(arm_names)
    if not any(value not in EMPTY_VALS for value in raw_data):
        return "entered"
    required_value_count = _ONE_ARM_REQUIRED_VALUE_COUNTS.get(effect, len(raw_data))
    required = raw_data[:required_value_count]
    if effect in {"Sens", "Spec"}:
        required = raw_data[:2] if effect == "Sens" else raw_data[2:4]
    if any(value in EMPTY_VALS for value in required):
        return "entered"
    preview = analysis_unit.get_effect_and_ci_for_source(
        "derived_preview", effect, arm_key, confidence_multiplier
    )
    return "derived_preview" if any(value is not None for value in preview) else "entered"


def effect_values_on_display_scale(analysis_unit, current_effect, arm_key, data_type, calculator, values):
    converter = {
        "binary": calculator.binary_convert_scale,
        "continuous": calculator.continuous_convert_scale,
        "diagnostic": calculator.diagnostic_convert_scale,
    }[data_type]
    if current_effect == "PFT" and data_type == "binary":
        raw = analysis_unit.arms_by_id[arm_key[0]].raw_data
        n = raw[1] if len(raw) >= 2 and raw[1] not in EMPTY_VALS else None
        if n is None and any(value is not None for value in values):
            raise ValueError("PFT display requires the actual arm sample size.")
        return calculator.binary_convert_scale(tuple(values), current_effect, n1=n)
    return converter(tuple(values), current_effect)


def parse_effect_draft(
    text: str, field: str, analysis_unit, effect, arm_key, data_type,
    confidence_multiplier, source: EffectSource, calculator: CalculatorService,
) -> float | None:
    value = parse_calculator_value(text)
    if value is not None:
        current = analysis_unit.get_effect_and_ci_for_source(
            source, effect, arm_key, confidence_multiplier
        )
        displayed = effect_values_on_display_scale(
            analysis_unit, effect, arm_key, data_type, calculator, current
        )
        validate_calculator_interval(field, value, displayed)
    return value


def populate_effect_ci_fields(
    analysis_unit,
    effect_fields: CalculatorEffectFields,
    current_effect,
    arm_key,
    data_type,
    confidence_multiplier=None,
    *,
    source: EffectSource = "entered",
    calculator: CalculatorService | None = None,
):
    """Populate calculator fields from an analysis unit."""
    if confidence_multiplier is None:
        raise ValueError("confidence multiplier must be specified")

    if data_type in {"binary", "continuous"} and source == "entered":
        values = analysis_unit.get_entered_effect_and_ci(current_effect, arm_key)
    else:
        values = analysis_unit.get_effect_and_ci_for_source(
            source, current_effect, arm_key, confidence_multiplier
        )
    display_values = effect_values_on_display_scale(
        analysis_unit, current_effect, arm_key, data_type, calculator or CalculatorService(), values
    )
    effect_fields.display(display_values)
    semantic_samples = {
        "binary": binary_effect_display_samples,
        "continuous": continuous_effect_display_samples,
        "diagnostic": diagnostic_effect_display_samples,
    }[data_type](current_effect)
    fit_effect_ci_line_edits_to_contents(
        list(effect_fields.editors.values()),
        semantic_samples=semantic_samples,
    )


def _wald_summary(data_type, current_effect, est, se) -> str:
    if est is None or se is None:
        return ""
    scale = ""
    if current_effect in {"OR", "RR", "HR", "IRR", "DOR", "PLR", "NLR", "PLN"}:
        scale = " (log scale)"
    elif current_effect in {"Sens", "Spec", "PLO"}:
        scale = " (logit scale)"
    summary = f"SE{scale} {se:.4f}"
    if data_type != "diagnostic" and se > 0:
        z = est / se
        p = math.erfc(abs(z) / math.sqrt(2))
        p_text = "< 0.001" if p < 0.001 else f"= {p:.3f}"
        summary += f"  ·  z = {z:.4f}  ·  two-sided P {p_text}"
    return summary


COMPARATIVE_BINARY_METRICS = ("OR", "RR", "RD")


def update_binary_metric_table(
    table: QTableWidget, raw: list[Numeric | None], calculator: CalculatorService,
    confidence_level: float,
) -> None:
    if len(raw) != 4 or not raw_data_is_complete(raw):
        table.hide()
        return
    e1, n1, e2, n2 = cast(list[Numeric], raw)
    table.show()
    for row, metric in enumerate(COMPARATIVE_BINARY_METRICS):
        result = calculator.effect_for_study(e1, n1, e2, n2, metric=metric, confidence_level=confidence_level)
        values = calculator.effect_triplet(result)
        display = [calculator.binary_convert_scale(value, metric) for value in values]
        for column, value in enumerate((metric, *display)):
            text = value if isinstance(value, str) else (
                "" if value is None else format_calculator_display_value(value)
            )
            item = QTableWidgetItem(text)
            item.setTextAlignment((Qt.AlignmentFlag.AlignLeft if column == 0 else Qt.AlignmentFlag.AlignRight) | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, column, item)
    table.resizeColumnsToContents()
    table.resizeRowsToContents()
    header = table.horizontalHeader()
    assert header is not None
    table.setFixedHeight(header.height()
                         + sum(table.rowHeight(row) for row in range(table.rowCount()))
                         + 2 * table.frameWidth())
    table.setMinimumWidth(sum(table.columnWidth(col) for col in range(table.columnCount()))
                          + 2 * table.frameWidth())


def update_wald_readout(
    label: QLabel, analysis_unit, current_effect, arm_key, confidence_multiplier,
    data_type, source: EffectSource,
) -> None:
    est = analysis_unit.get_effect_and_ci_for_source(
        source, current_effect, arm_key, confidence_multiplier
    )[0]
    se = analysis_unit.get_se(source, current_effect, arm_key, confidence_multiplier)
    label.setText(_wald_summary(data_type, current_effect, est, se))
    label.show()


def make_wald_readout(layout: QVBoxLayout, button_box: QWidget) -> QLabel:
    label = QLabel(button_box.parentWidget())
    label.setObjectName("calculator_wald")
    label.setWordWrap(True)
    label.hide()
    layout.insertWidget(layout.indexOf(button_box), label)
    return label


def make_binary_metric_table(layout: QVBoxLayout, parent: QWidget) -> QTableWidget:
    table = QTableWidget(len(COMPARATIVE_BINARY_METRICS), 4, parent)
    table.setObjectName("calculator_metrics")
    table.setShowGrid(False)
    table.setAlternatingRowColors(True)
    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.setHorizontalHeaderLabels(["Effect measure", "Estimate", "Lower CI", "Upper CI"])
    vertical_header = table.verticalHeader()
    assert vertical_header is not None
    vertical_header.hide()
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    horizontal_header = table.horizontalHeader()
    assert horizontal_header is not None
    horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    font = QFont(horizontal_header.font())
    font.setBold(True)
    horizontal_header.setFont(font)
    horizontal_header.setStyleSheet("QHeaderView::section { border: 0; border-bottom: 1px solid palette(mid); padding: 0 0.5em; }")
    for column in range(4):
        item = table.horizontalHeaderItem(column)
        assert item is not None
        item.setTextAlignment((Qt.AlignmentFlag.AlignLeft if column == 0 else Qt.AlignmentFlag.AlignRight) | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(table)
    table.hide()
    return table
