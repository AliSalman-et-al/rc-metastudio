# SPDX-License-Identifier: GPL-3.0-or-later
"""Publication export controls with proportional physical dimensions."""

import math

from PyQt6.QtCore import QSettings, QSignalBlocker
from PyQt6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLabel, QSpinBox

from rc_metastudio.settings import load_plot_export_format, save_plot_export_format


class PlotExportDialog(QDialog):
    def __init__(self, formats, width: float, height: float, parent=None, *, resizable: bool = True, native_dpi: int = 96, minimum_width: float = 0):
        super().__init__(parent)
        self.setWindowTitle('Export plot')
        self.setMinimumWidth(360)
        self.ratio = height / width
        self.resizable = resizable
        self.minimum_width = minimum_width
        self._width_inches = width
        if resizable:
            try:
                saved_width = float(str(QSettings().value('export/width_inches', width)))
            except ValueError:
                saved_width = width
            self._width_inches = min(200., max(.1, saved_width)) if math.isfinite(saved_width) else width
        layout = QFormLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        self.format_control = QComboBox(self)
        for item in formats:
            self.format_control.addItem(item.label, item.extension)
        self.format_control.setCurrentIndex(max(0, self.format_control.findData(load_plot_export_format())))
        layout.addRow('Format', self.format_control)
        self.units = QComboBox(self)
        self.units.addItems(['cm', 'in'])
        self.units.setCurrentText(str(QSettings().value('export/units', 'cm')))
        layout.addRow('Units', self.units)
        self.width_control = QDoubleSpinBox(self)
        self.width_control.setDecimals(2)
        self.width_control.setRange(.1 * self.unit_factor(), 200 * self.unit_factor())
        self.width_control.setSuffix(' ' + self.units.currentText())
        self.width_control.setValue(self._width_inches * self.unit_factor())
        self.width_control.setEnabled(resizable)
        layout.addRow('Width', self.width_control)
        self.height_label = QLabel(self)
        layout.addRow('Height', self.height_label)
        self.dpi = QSpinBox(self)
        self.dpi.setRange(72 if resizable else 1, max(1200, native_dpi))
        try:
            saved_dpi = int(float(str(QSettings().value('export/dpi', 600))))
        except (ValueError, OverflowError):
            saved_dpi = 600
        self.dpi.setValue(saved_dpi if resizable else native_dpi)
        layout.addRow('Resolution (DPI)', self.dpi)
        self.dpi.valueChanged.connect(self._refresh)
        self.format_control.currentIndexChanged.connect(self._refresh)
        self.width_control.valueChanged.connect(self._change_width)
        self.pixel_label = QLabel(self)
        layout.addRow(self.pixel_label)
        self.legibility_warning = QLabel(
            "At this width, some figure text will be smaller than 6 pt. "
            "Increase the width or simplify the figure in Edit plot.", self)
        self.legibility_warning.setWordWrap(True)
        layout.addRow(self.legibility_warning)
        self.include_title = QCheckBox("Include title line", self)
        if resizable:
            layout.addRow(self.include_title)
        else:
            self.include_title.hide()
        if not resizable:
            layout.addRow(QLabel("This image keeps its original size and resolution.", self))
        self.units.currentIndexChanged.connect(self._change_units)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        self._refresh()

    def unit_factor(self) -> float:
        return 2.54 if self.units.currentText() == 'cm' else 1.0

    def _change_width(self):
        self._width_inches = self.width_control.value() / self.unit_factor()
        self._refresh()

    def _change_units(self):
        with QSignalBlocker(self.width_control):
            self.width_control.setRange(.1 * self.unit_factor(), 200 * self.unit_factor())
            self.width_control.setSuffix(' ' + self.units.currentText())
            self.width_control.setValue(self._width_inches * self.unit_factor())
        self._refresh()

    def _refresh(self):
        self.height_label.setText(f'{self.width_control.value() * self.ratio:.2f} {self.units.currentText()}')
        raster = self.format_control.currentData() in ('png', 'tiff')
        self.dpi.setEnabled(self.resizable and raster)
        self.pixel_label.setVisible(raster)
        self.legibility_warning.setVisible(self._width_inches < self.minimum_width)
        self.pixel_label.setText(f'{round(self._width_inches * self.dpi.value())} × {round(self._width_inches * self.ratio * self.dpi.value())} pixels')

    def dimensions(self) -> tuple[float, float, int]:
        width = self._width_inches
        return width, width * self.ratio, self.dpi.value()

    def accept(self):
        save_plot_export_format(self.format_control.currentData())
        QSettings().setValue('export/units', self.units.currentText())
        if self.resizable:
            QSettings().setValue('export/dpi', self.dpi.value())
            QSettings().setValue('export/width_inches', self.dimensions()[0])
        super().accept()
