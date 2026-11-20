# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Attach the shared style and accent fields to the plot controls."""

from collections.abc import Mapping
import re

from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QAbstractButton, QColorDialog, QComboBox, QLineEdit

from rc_metastudio.app_error_handler import safe_slot
from rc_metastudio.results.plot_defaults import PLOT_STYLE_ACCENTS, PLOT_STYLE_LABELS


def configure_tsa_x_axis(selector: QComboBox, saved_units: object, *, statistical: bool) -> None:
    selector.setAccessibleName("X-axis")
    selector.addItem("Statistical information" if statistical else "Participants", "participants")
    selector.addItem("% of required information size", "percent")
    selector.setCurrentIndex(max(0, selector.findData(saved_units)))


def selected_plot_style(selector: QComboBox) -> str:
    return str(selector.currentData() or "default")

def plot_color(text: str) -> str:
    """Accept named Qt colours and R hex colours, or an unset field."""
    text = text.strip()
    if not text or re.fullmatch(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?", text):
        return text
    color = QColor(text)
    if color.isValid():
        return color.name(QColor.NameFormat.HexRgb)
    raise ValueError("Enter a color name or a hex color such as #2F5597, or leave it blank for the preset default.")


def configure_plot_style(
    selector: QComboBox, accent: QLineEdit, color_button: QAbstractButton,
    *, accents: Mapping[str, str] = PLOT_STYLE_ACCENTS,
) -> None:
    for style, label in PLOT_STYLE_LABELS.items():
        selector.addItem(label, style)
    selector.setCurrentIndex(selector.findData("default"))
    accent.setText(accents["default"])

    def update_accent() -> None:
        accent.setText(accents[selected_plot_style(selector)])

    def choose_color() -> None:
        color = QColorDialog.getColor(QColor(accent.text()), selector.window(), "Plot accent color")
        if color.isValid():
            accent.setText(color.name())

    selector.currentIndexChanged.connect(safe_slot(update_accent, parent=selector.window()))
    color_button.clicked.connect(safe_slot(choose_color, parent=selector.window()))


def load_plot_style(
    selector: QComboBox, accent: QLineEdit, saved_style: object, saved_accent: object,
    *, accents: Mapping[str, str] = PLOT_STYLE_ACCENTS,
) -> None:
    if isinstance(saved_style, (list, tuple)) and saved_style:
        saved_style = saved_style[0]
    style = str(saved_style or "default").strip().lower()
    if style not in PLOT_STYLE_LABELS:
        style = "default"
    with QSignalBlocker(selector):
        selector.setCurrentIndex(selector.findData(style))
    accent.setText(str(saved_accent or accents[style]))
