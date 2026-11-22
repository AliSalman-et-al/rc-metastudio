# SPDX-License-Identifier: GPL-3.0-or-later
"""Publication export controls and physical size validation."""

import math
from collections.abc import Callable

from PyQt6.QtCore import QSettings, QSignalBlocker, QTimer
from rc_metastudio.qt_object_guard import required
from rc_metastudio.r_runtime import AnalysisBackendUnavailableError
from PyQt6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLabel, QPushButton, QSpinBox

from rc_metastudio.results.plot_service import RASTER_MAX_DIMENSION, RASTER_MAX_PIXELS
from rc_metastudio.settings import load_plot_export_format, save_plot_export_format


class PlotExportDialog(QDialog):
    def __init__(self, formats, width: float, height: float, parent=None, *,
                 resizable: bool = True, native_dpi: int = 96,
                 text_per_inch: tuple[float, float] = (0, 0),
                 forest_geometry: Callable[[float, bool], tuple[float, float] | None] | None = None):
        super().__init__(parent)
        self.setWindowTitle('Export plot')
        self.setMinimumWidth(360)
        self.ratio = height / width
        self.resizable = resizable
        self.text_per_inch = text_per_inch
        self._forest_geometry = forest_geometry
        self.forest_dimensions: tuple[float, float] | None = None
        self._minimum_mm = 0.0
        self._layout_error = ""
        self._measuring = False
        self._measure_timer = QTimer(self)
        self._measure_timer.setSingleShot(True)
        self._measure_timer.setInterval(150)
        self._measure_timer.timeout.connect(self._measure_width)
        self._width_inches = width
        layout = QFormLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        self.format_control = QComboBox(self)
        for item in formats:
            self.format_control.addItem(item.label, item.extension)
        self.format_control.setCurrentIndex(max(0, self.format_control.findData(load_plot_export_format())))
        layout.addRow('Format', self.format_control)
        self.units = QComboBox(self)
        self.units.addItems(['cm', 'mm', 'in'])
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
        self.include_title = QCheckBox("Include figure caption", self)
        self.include_title.toggled.connect(self._width_changed)
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
        self._measure_width()
        if self._forest_geometry is not None and self._width_inches * 25.4 < self._minimum_mm:
            with QSignalBlocker(self.width_control):
                self.width_control.setValue(self._readable_width_value())
            self._width_inches = self.width_control.value() / self.unit_factor()
            self._measure_width()

    def unit_factor(self) -> float:
        return {'cm': 2.54, 'mm': 25.4, 'in': 1.0}[self.units.currentText()]

    def _change_width(self):
        self._width_inches = self.width_control.value() / self.unit_factor()
        self._width_changed()

    def _change_units(self):
        with QSignalBlocker(self.width_control):
            self.width_control.setRange(.1 * self.unit_factor(), 200 * self.unit_factor())
            self.width_control.setSuffix(' ' + self.units.currentText())
            self.width_control.setValue(self._width_inches * self.unit_factor())
        self._width_changed()

    def _width_changed(self):
        if self._forest_geometry is not None:
            self._measure_timer.start()
        self._refresh()

    def _measure_width(self):
        if self._measuring:
            self._measure_timer.start()
            return
        self._layout_error = ""
        self.forest_dimensions = None
        self._minimum_mm = 0.0
        if self._forest_geometry is not None:
            self._measuring = True
            self._refresh()
            try:
                dimensions = self._forest_geometry(self._width_inches, self.include_title.isChecked())
                if dimensions is None:
                    raise ValueError("Plot layout is unavailable.")
                self.forest_dimensions = dimensions
                self._minimum_mm = math.ceil(dimensions[1] * 254 - 1e-9) / 10
            except AnalysisBackendUnavailableError:
                self._layout_error = "Could not measure the forest plot because the analysis backend is unavailable."
            except Exception as error:
                self._layout_error = f"Could not measure the forest plot. {error}"
            finally:
                self._measuring = False
        self._refresh()

    def _readable_width_mm(self) -> float:
        if self._forest_geometry is not None:
            return self._minimum_mm
        rate = self.text_per_inch[self.include_title.isChecked()]
        return math.ceil(6 * 25.4 / rate) if rate else 0

    def _readable_width_value(self) -> float:
        return math.ceil(self._readable_width_mm() / 25.4 * self.unit_factor() * 100 - 1e-9) / 100

    def _set_readable_width(self):
        self.width_control.setValue(self._readable_width_value())

    def _largest_dpi(self, width: float) -> int:
        height = self.forest_dimensions[0] if self.forest_dimensions is not None else width * self.ratio
        dpi = min(self.dpi.maximum(), math.floor(min(
            RASTER_MAX_DIMENSION / max(width, height),
            math.sqrt(RASTER_MAX_PIXELS / (width * height)),
        )))
        while dpi > 0:
            w, h = math.ceil(width * dpi), math.ceil(height * dpi)
            if max(w, h) <= RASTER_MAX_DIMENSION and w * h <= RASTER_MAX_PIXELS:
                break
            dpi -= 1
        return dpi

    def _refresh(self):
        width, height, dpi = self.dimensions()
        pending = self._measuring or self._measure_timer.isActive()
        blocked = pending or bool(self._layout_error) or width * 25.4 + 1e-8 < self._minimum_mm
        self.height_label.setText("Measuring…" if pending else f'{height * self.unit_factor():.2f} {self.units.currentText()}')
        raster = self.format_control.currentData() in ('png', 'tiff')
        self._refresh_save_controls(dpi, blocked=blocked, raster=raster)
        self.paginate_pdf.setVisible(self.resizable and self.format_control.currentData() == "pdf"
                                     and not blocked and height > 267 / 25.4)
        self.dpi.setEnabled(self.resizable and raster)
        self.pixel_label.setVisible(raster and not blocked)
        self.pixel_label.setText(f'{math.ceil(width * dpi):,} × {math.ceil(height * dpi):,} pixels')
        self._refresh_legibility(width, pending=pending, raster=raster)

    def _refresh_save_controls(self, dpi: int, *, blocked: bool, raster: bool) -> None:
        max_dpi = self._largest_dpi(self._width_inches)
        oversized = not blocked and self.resizable and raster and dpi > max_dpi
        self.save_button.setEnabled(not blocked and not oversized)
        self.raster_limit.setVisible(oversized or bool(self._layout_error))
        self.raster_limit.setText(self._layout_error or "This image is too large at the selected DPI. Use a lower DPI or export a vector PDF or SVG.")
        self.use_max_dpi.setVisible(oversized and max_dpi >= self.dpi.minimum())
        self.use_max_dpi.setText(f"Use {max_dpi} DPI")
        self.use_vector.setVisible(oversized and self.format_control.findData("pdf") >= 0)

    def _refresh_legibility(self, width: float, *, pending: bool, raster: bool) -> None:
        units = self.units.currentText()
        target_width = self._readable_width_value()
        target = f"{target_width:.2f}".rstrip("0").rstrip(".") + f" {units}"
        if self._forest_geometry is not None:
            self.legibility_warning.setVisible(self._minimum_mm > 0)
            self.legibility_warning.setText(f"Minimum width for this figure: {target}")
            self.use_readable_width.setVisible(not pending and width * 25.4 + 1e-8 < self._minimum_mm)
            self.use_readable_width.setText(f"Use {target}")
            return
        smallest = self._width_inches * self.text_per_inch[self.include_title.isChecked()]
        warn = self.resizable and 0 < smallest < 6
        self.legibility_warning.setVisible(warn)
        self.use_readable_width.setVisible(warn and target_width <= self.width_control.maximum()
            and (not raster or self.dpi.value() <= self._largest_dpi(target_width / self.unit_factor())))
        if warn:
            text_size = f"{smallest:.2f}".rstrip("0").rstrip(".")
            self.legibility_warning.setText(
                f"Smallest text would be {text_size} pt at {self.width_control.text()}. "
                f"Use at least {target} for 6 pt text."
            )
            self.use_readable_width.setText(f"Use {target}")

    def dimensions(self) -> tuple[float, float, int]:
        width = self._width_inches
        height = self.forest_dimensions[0] if self.forest_dimensions is not None else width * self.ratio
        return width, height, self.dpi.value()

    def accept(self):
        if self._measure_timer.isActive():
            self._measure_timer.stop()
            self._measure_width()
        if not self.save_button.isEnabled():
            return
        save_plot_export_format(self.format_control.currentData())
        QSettings().setValue('export/units', self.units.currentText())
        if self.resizable:
            QSettings().setValue('export/dpi', self.dpi.value())
            if self.format_control.currentData() == "pdf":
                QSettings().setValue("export/paginate_pdf", self.paginate_pdf.isChecked())
        super().accept()
