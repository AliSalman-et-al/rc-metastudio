# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Attach the shared style and accent fields to the plot controls."""

from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QAbstractButton, QColorDialog, QComboBox, QLineEdit

from rc_metastudio.app_error_handler import safe_slot
from rc_metastudio.plot_defaults import PLOT_STYLE_ACCENTS, PLOT_STYLE_LABELS


def selected_plot_style(selector: QComboBox) -> str:
    return str(selector.currentData() or "default")


def configure_plot_style(
    selector: QComboBox, accent: QLineEdit, color_button: QAbstractButton
) -> None:
    for style, label in PLOT_STYLE_LABELS.items():
        selector.addItem(label, style)
    selector.setCurrentIndex(selector.findData("default"))
    accent.setText(PLOT_STYLE_ACCENTS["default"])

    def update_accent() -> None:
        accent.setText(PLOT_STYLE_ACCENTS[selected_plot_style(selector)])

    def choose_color() -> None:
        color = QColorDialog.getColor(QColor(accent.text()), selector.window(), "Plot accent color")
        if color.isValid():
            accent.setText(color.name())

    selector.currentIndexChanged.connect(safe_slot(update_accent, parent=selector.window()))
    color_button.clicked.connect(safe_slot(choose_color, parent=selector.window()))


def load_plot_style(
    selector: QComboBox, accent: QLineEdit, saved_style: object, saved_accent: object
) -> None:
    if isinstance(saved_style, (list, tuple)) and saved_style:
        saved_style = saved_style[0]
    style = str(saved_style or "default").strip().lower()
    if style not in PLOT_STYLE_LABELS:
        style = "default"
    with QSignalBlocker(selector):
        selector.setCurrentIndex(selector.findData(style))
    accent.setText(str(saved_accent or PLOT_STYLE_ACCENTS[style]))
