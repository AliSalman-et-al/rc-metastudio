# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Effect source selection and calculator readout presentation."""

import math
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView, QLabel, QTableWidget, QTableWidgetItem
from rc_metastudio import r_bridge
from rc_metastudio.analysis_catalog import BINARY_ONE_ARM_METRICS, CONTINUOUS_ONE_ARM_METRICS
from rc_metastudio.analysis_validation import EMPTY_VALS
from rc_metastudio.calculator_controls import (
    fit_effect_ci_line_edits_to_contents,
    format_calculator_display_value,
    binary_effect_display_samples,
    continuous_effect_display_samples,
    diagnostic_effect_display_samples,
)


_ONE_ARM_REQUIRED_DATA = {
    **dict.fromkeys(BINARY_ONE_ARM_METRICS, 2),
    **dict.fromkeys(CONTINUOUS_ONE_ARM_METRICS, 3),
}


def calculator_effect_source(
    analysis_unit, groups, effect, arm_key, confidence_multiplier, *, input_mode=None
):
    """Return the active calculator effect authority.

    A partial raw-data edit does not produce a preview. Keep showing an
    entered effect in that state so back-calculation and direct editing remain
    usable; switch to the preview only after the active metric has one.
    """
    if input_mode == "estimate":
        return "entered"
    raw_data = analysis_unit.get_raw_data_for_arms(groups)
    if not any(value not in EMPTY_VALS for value in raw_data):
        return "entered"
    required_data = _ONE_ARM_REQUIRED_DATA.get(effect, len(raw_data))
    if any(value in EMPTY_VALS for value in raw_data[:required_data]):
        return "entered"
    preview = analysis_unit.get_effect_and_ci_for_source(
        "derived_preview", effect, arm_key, confidence_multiplier
    )
    return "derived_preview" if any(value is not None for value in preview) else "entered"


def _effect_values_on_display_scale(analysis_unit, current_effect, arm_key, data_type, converter, values):
    if data_type != "binary" or current_effect != "PFT":
        return [converter(value, current_effect, convert_to="display.scale") for value in values]
    converted = []
    for value in values:
        raw = analysis_unit.arms_by_id[arm_key[0]].raw_data
        n = raw[1] if len(raw) >= 2 and raw[1] not in EMPTY_VALS else None
        if value is not None and n is None:
            raise ValueError("PFT display requires the actual arm sample size.")
        converted.append(converter(value, current_effect, convert_to="display.scale", n1=n))
    return converted


def set_current_effect_from_value(
    analysis_unit,
    txt_boxes,
    current_effect,
    arm_key,
    data_type,
    confidence_multiplier=None,
    *,
    source="entered",
):
    """Populate calculator fields from an analysis unit."""
    if confidence_multiplier is None:
        raise ValueError("confidence multiplier must be specified")

    converters = {
        "binary": r_bridge.binary_convert_scale,
        "continuous": r_bridge.continuous_convert_scale,
        "diagnostic": r_bridge.diagnostic_convert_scale,
    }
    try:
        converter = converters[data_type]
    except KeyError as exc:
        raise ValueError("data_type unrecognized") from exc
    effect_tbox, lower_tbox, upper_tbox = [
        txt_boxes[box_name] for box_name in ("effect", "lower", "upper")
    ]

    (est, lower, upper) = analysis_unit.get_effect_and_ci_for_source(
        source, current_effect, arm_key, confidence_multiplier
    )
    if data_type in {"binary", "continuous"} and source == "entered":
        est, lower, upper = analysis_unit.get_entered_effect_and_ci(current_effect, arm_key)
    display_estimate, display_lower, display_upper = _effect_values_on_display_scale(
        analysis_unit, current_effect, arm_key, data_type, converter, (est, lower, upper)
    )
    for val, txt_box in zip(
        (display_estimate, display_lower, display_upper),
        [effect_tbox, lower_tbox, upper_tbox],
    ):
        txt_box.blockSignals(True)
        if val is not None:
            txt_box.setText(format_calculator_display_value(val))
        else:
            txt_box.setText("")
        txt_box.setProperty("calculatorValue", txt_box.text())
        txt_box.blockSignals(False)
    semantic_samples = {
        "binary": binary_effect_display_samples,
        "continuous": continuous_effect_display_samples,
        "diagnostic": diagnostic_effect_display_samples,
    }[data_type](current_effect)
    fit_effect_ci_line_edits_to_contents(
        [effect_tbox, lower_tbox, upper_tbox],
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
    summary = f"SE{scale}: {se:.4f}"
    if data_type != "diagnostic" and se > 0:
        z = est / se
        p = math.erfc(abs(z) / math.sqrt(2))
        p_text = "<0.001" if p < 0.001 else f"{p:.3f}"
        summary += f"    Z: {z:.4f}    Two-sided P: {p_text}"
    return summary


def _update_binary_metric_table(dialog, raw) -> None:
    if not hasattr(dialog, "metric_readout"):
        table = QTableWidget(3, 4, dialog)
        dialog.metric_readout = table
        table.setObjectName("calculator_metrics")
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setHorizontalHeaderLabels(["Metric", "Estimate", "Lower CI", "Upper CI"])
        vertical_header = table.verticalHeader()
        assert vertical_header is not None
        vertical_header.hide()
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        horizontal_header = table.horizontalHeader()
        assert horizontal_header is not None
        horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        dialog.content_layout.addWidget(table)
        def select_metric(row, column):
            index = dialog.effect_combo_box.findData(("OR", "RR", "RD")[row])
            if index < 0:
                index = dialog.effect_combo_box.findText(("OR", "RR", "RD")[row])
            dialog.effect_combo_box.setCurrentIndex(index)
        table.cellClicked.connect(select_metric)
    for row, metric in enumerate(("OR", "RR", "RD")):
        result = dialog.calculator.effect_for_study(
            *raw, metric=metric, confidence_level=dialog.confidence_level
        )
        values = dialog.calculator.effect_triplet(result)
        display = [r_bridge.binary_convert_scale(v, metric, convert_to="display.scale") for v in values]
        for column, value in enumerate([metric] + display):
            text = value if isinstance(value, str) else (
                "" if value is None else format_calculator_display_value(value)
            )
            dialog.metric_readout.setItem(row, column, QTableWidgetItem(text))
    table = dialog.metric_readout
    table.resizeColumnsToContents()
    table.resizeRowsToContents()
    header = table.horizontalHeader()
    assert header is not None
    table.setFixedHeight(header.height()
                         + sum(table.rowHeight(row) for row in range(table.rowCount()))
                         + 2 * table.frameWidth())
    table.setMinimumWidth(sum(table.columnWidth(col) for col in range(table.columnCount()))
                          + 2 * table.frameWidth())


def update_calculator_readout(dialog, data_type):
    """Refresh read-only statistics without replacing the user's editable text."""
    if getattr(dialog, "_raw_data_invalid", False):
        return
    analysis_unit = dialog.analysis_unit
    current_effect = dialog.current_effect
    arm_key = dialog.arm_key
    confidence_multiplier = dialog.confidence_multiplier
    source = calculator_effect_source(
        analysis_unit, dialog.arm_names, current_effect, arm_key, confidence_multiplier,
        input_mode=getattr(dialog, "_active_input_mode", None) if data_type == "binary" else None,
    )
    if data_type == "continuous":
        source = "entered" if getattr(dialog, "_active_input_mode", "estimate") == "estimate" else "derived_preview"
    est, lower, upper = analysis_unit.get_effect_and_ci_for_source(
        source, current_effect, arm_key, confidence_multiplier
    )
    if not hasattr(dialog, "wald_readout"):
        dialog.wald_readout = QLabel(dialog)
        dialog.wald_readout.setObjectName("calculator_wald")
        dialog.wald_readout.setWordWrap(True)
        for field in (dialog.effect_text_box, dialog.lower_text_box, dialog.upper_text_box):
            field.editingFinished.connect(lambda: update_calculator_readout(dialog, data_type))
        if data_type == "diagnostic":
            dialog.effect_layout.addWidget(dialog.wald_readout, 2, 0, 1, 6)
        else:
            dialog.dialog_layout.insertWidget(dialog.dialog_layout.indexOf(dialog.buttonBox), dialog.wald_readout)
    se = analysis_unit.get_se(source, current_effect, arm_key, confidence_multiplier)
    summary = _wald_summary(data_type, current_effect, est, se)
    dialog.wald_readout.setText(summary)
    dialog.wald_readout.show()
    raw = analysis_unit.get_raw_data_for_arms(dialog.arm_names)
    complete_binary = (
        data_type == "binary" and len(raw) == 4
        and all(v not in EMPTY_VALS for v in raw)
    )
    if complete_binary:
        _update_binary_metric_table(dialog, raw)
    if hasattr(dialog, "metric_readout"):
        dialog.metric_readout.setVisible(complete_binary)
