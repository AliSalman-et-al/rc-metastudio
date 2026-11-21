# SPDX-License-Identifier: GPL-3.0-or-later
"""Publication export controls with proportional physical dimensions."""

import math

from PyQt6.QtCore import QSettings, QSignalBlocker
from rc_metastudio.qt_object_guard import required
from PyQt6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLabel, QPushButton, QSpinBox

from rc_metastudio.results.plot_service import RASTER_MAX_DIMENSION, RASTER_MAX_PIXELS
from rc_metastudio.settings import load_plot_export_format, save_plot_export_format


class PlotExportDialog(QDialog):
    def __init__(self, formats, width: float, height: float, parent=None, *, resizable: bool = True, native_dpi: int = 96, text_per_inch: tuple[float, float] = (0, 0)):
        super().__init__(parent)
        self.setWindowTitle('Export plot')
        self.setMinimumWidth(360)
        self.ratio = height / width
        self.resizable = resizable
        self.text_per_inch = text_per_inch
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
        if resizable:
            self._width_inches = self.width_control.value() / self.unit_factor()
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
        self.raster_limit = QLabel(self)
        self.raster_limit.setWordWrap(True)
        layout.addRow(self.raster_limit)
        self.use_max_dpi = QPushButton(self)
        self.use_max_dpi.clicked.connect(lambda: self.dpi.setValue(self._largest_dpi(self._width_inches)))
        layout.addRow(self.use_max_dpi)
        self.use_vector = QPushButton("Switch to PDF (vector)", self)
        self.use_vector.clicked.connect(lambda: self.format_control.setCurrentIndex(self.format_control.findData("pdf")))
        layout.addRow(self.use_vector)
        self.paginate_pdf = QCheckBox("Use A4 pages for tall PDF figures", self)
        self.paginate_pdf.setChecked(str(QSettings().value("export/paginate_pdf", True)).lower() == "true")
        layout.addRow(self.paginate_pdf)
        self.legibility_warning = QLabel(self)
        self.legibility_warning.setWordWrap(True)
        layout.addRow(self.legibility_warning)
        self.use_readable_width = QPushButton(self)
        self.use_readable_width.clicked.connect(self._set_readable_width)
        layout.addRow(self.use_readable_width)
        self.include_title = QCheckBox("Include title line", self)
        self.include_title.toggled.connect(self._refresh)
        if resizable:
            layout.addRow(self.include_title)
        else:
            self.include_title.hide()
        if not resizable:
            layout.addRow(QLabel("This image keeps its original size and resolution.", self))
        self.units.currentIndexChanged.connect(self._change_units)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, self)
        self.save_button = required(buttons.button(QDialogButtonBox.StandardButton.Save), "Save plot")
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
        if self.resizable:
            self._width_inches = self.width_control.value() / self.unit_factor()
        self._refresh()

    def _readable_width_mm(self) -> int:
        rate = self.text_per_inch[self.include_title.isChecked()]
        return math.ceil(6 * 25.4 / rate) if rate else 0

    def _readable_width_value(self) -> float:
        return math.ceil(self._readable_width_mm() / 25.4 * self.unit_factor() * 100 - 1e-9) / 100

    def _set_readable_width(self):
        self.width_control.setValue(self._readable_width_value())

    def _largest_dpi(self, width: float) -> int:
        height = width * self.ratio
        dpi = min(self.dpi.maximum(), math.floor(min(
            RASTER_MAX_DIMENSION / max(width, height),
            math.sqrt(RASTER_MAX_PIXELS / (width * height)),
        )))
        while dpi > 0 and math.ceil(width * dpi) * math.ceil(height * dpi) > RASTER_MAX_PIXELS:
            dpi -= 1
        return dpi

    def _refresh(self):
        self.height_label.setText(f'{self.width_control.value() * self.ratio:.2f} {self.units.currentText()}')
        raster = self.format_control.currentData() in ('png', 'tiff')
        max_dpi = self._largest_dpi(self._width_inches)
        oversized = self.resizable and raster and self.dpi.value() > max_dpi
        self.save_button.setEnabled(not oversized)
        self.raster_limit.setVisible(oversized)
        self.raster_limit.setText("This image is too large at the selected DPI. Use a lower DPI or export a vector PDF or SVG.")
        self.use_max_dpi.setVisible(oversized and max_dpi >= self.dpi.minimum())
        self.use_max_dpi.setText(f"Use {max_dpi} DPI")
        self.use_vector.setVisible(oversized and self.format_control.findData("pdf") >= 0)
        self.paginate_pdf.setVisible(self.resizable and self.format_control.currentData() == "pdf"
                                     and self._width_inches * self.ratio > 267 / 25.4)
        self.dpi.setEnabled(self.resizable and raster)
        self.pixel_label.setVisible(raster)
        smallest = self._width_inches * self.text_per_inch[self.include_title.isChecked()]
        warn = self.resizable and 0 < smallest < 6
        self.legibility_warning.setVisible(warn)
        target_width = self._readable_width_value()
        self.use_readable_width.setVisible(warn and target_width <= self.width_control.maximum()
            and (not raster or self.dpi.value() <= self._largest_dpi(target_width / self.unit_factor())))
        if warn:
            target = self._readable_width_mm()
            self.legibility_warning.setText(
                f"Smallest text would be {smallest:.2f}".rstrip("0") +
                f" pt at {self._width_inches * 25.4:.3g} mm. "
                f"This figure needs at least {target} mm wide for 6 pt text."
            )
            self.use_readable_width.setText(f"Use {target} mm")
        self.pixel_label.setText(f'{math.ceil(self._width_inches * self.dpi.value())} × {math.ceil(self._width_inches * self.ratio * self.dpi.value())} pixels')

    def dimensions(self) -> tuple[float, float, int]:
        width = self._width_inches
        return width, width * self.ratio, self.dpi.value()

    def accept(self):
        if not self.save_button.isEnabled():
            return
        save_plot_export_format(self.format_control.currentData())
        QSettings().setValue('export/units', self.units.currentText())
        if self.resizable:
            QSettings().setValue('export/dpi', self.dpi.value())
            if self.format_control.currentData() == "pdf":
                QSettings().setValue("export/paginate_pdf", self.paginate_pdf.isChecked())
            QSettings().setValue('export/width_inches', self.dimensions()[0])
        super().accept()
