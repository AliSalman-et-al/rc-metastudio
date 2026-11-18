# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Set up trial sequential analysis on the active sheet."""

from collections.abc import Callable
from dataclasses import replace
from math import isfinite

from PyQt6.QtCore import QSignalBlocker, Qt, QTimer
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QToolButton, QVBoxLayout, QWidget,
)

from rc_metastudio import adaptive_window, app_error_handler, progress_dialog, qt_layout
from rc_metastudio.analysis_identity import dataset_identity
from rc_metastudio.dataset_table_model import DatasetTableModel
from rc_metastudio.manuscript_report import AnalysisResultHandler, trial_sequential_report
from rc_metastudio.qt_object_guard import required
from rc_metastudio.trial_sequential_analysis import (
    EFFECT_SOURCES, HKSJ_NOTE, TSA_SETTINGS, TSA_TITLE, TsaOptions, TsaPreview, TsaRequest, TsaService,
)

def _muted_label(text: str = "") -> QLabel:
    label = QLabel(text)
    qt_layout.configure_context_label(label)
    label.setForegroundRole(QPalette.ColorRole.PlaceholderText)
    return label


class TrialSequentialAnalysisDialog(QDialog):
    def __init__(
        self, model: DatasetTableModel, parent: QWidget, *,
        on_result: AnalysisResultHandler, on_settings_saved: Callable[[], None],
        service: TsaService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(TSA_TITLE)
        self.setModal(True)
        self.model = model
        self.sheet = required(model.current_sheet, "active sheet")
        self.on_result = on_result
        self.on_settings_saved = on_settings_saved
        self.service = service or TsaService()
        saved = TsaOptions.from_mapping(self.sheet.settings.get(TSA_SETTINGS, {}))
        self.base_request = TsaRequest.from_sheet(model, saved)
        self.default_inputs: dict[QLineEdit, tuple[QLabel, QPushButton]] = {}
        self.entered_inputs: set[QLineEdit] = set()
        self.binary = self.base_request.family == "binary"
        self.hr = self.base_request.metric == "HR"
        outer = QVBoxLayout(self)
        summary = QLabel(f"Measure: {self.base_request.metric} · Model: {self.base_request.model_label} · Wald z")
        qt_layout.configure_context_label(summary)
        outer.addWidget(summary)
        if self.base_request.inference in {"knha", "adhoc"}:
            outer.addWidget(_muted_label(HKSJ_NOTE))

        fields = QFormLayout()
        outer.addLayout(fields)
        self.order = self._choice("Add studies in", [("Publication year", "year"), ("Table order", "table")], saved.order)
        left, right = self.base_request.favoured_labels()
        self.test = self._choice("Test", [("Two-sided", "two-sided"),
                                          (f"One-sided (favours {left})", "benefit"),
                                          (f"One-sided (favours {right})", "harm")], saved.test)
        self.alpha = self._percent("Type I error (α)", .01, 49.99, 100 * saved.alpha)
        self.power = self._percent("Power", 50.01, 99.99, 100 * saved.power)
        for widget in (self.order, self.test, self.alpha, self.power):
            self._row(fields, widget.accessibleName(), widget)

        self.effect = self._default_input(fields, "Anticipated intervention effect", saved.anticipated_effect)
        if self.binary:
            self.control = self._default_input(
                fields, "Control event proportion (%)",
                None if saved.control_proportion is None else 100 * saved.control_proportion,
            )
        else:
            self.control = None
        self.variance = None
        if self.base_request.metric == "MD":
            self.variance, self.variance_source = self._input(fields, "Participant variance", saved.variance)
        self.heterogeneity = self._choice("Heterogeneity adjustment", [("D²", "d2"), ("I²", "i2"),
                                                                     ("None", "none")], saved.heterogeneity)
        self.heterogeneity_value = _muted_label()
        self._row(fields, "Heterogeneity adjustment", self.heterogeneity, self.heterogeneity_value)
        if self.base_request.model != "random":
            self.heterogeneity.setEnabled(False)
            self.heterogeneity.setToolTip("Not applicable to fixed-effect models")
            self.heterogeneity_value.setText(self.heterogeneity.toolTip())
        self.spending = self._choice("Boundaries", [("O'Brien-Fleming", "obf"), ("Pocock", "pocock")], saved.spending)
        self._row(fields, "Boundaries", self.spending)
        self.futility = self._check("Futility boundaries", saved.futility)
        self.lil = self._check("Penalised Z-curve (law of the iterated logarithm)", saved.lil and self.binary)
        self.lil.setEnabled(self.binary)
        if not self.binary:
            self.lil.setToolTip("The penalised Z-curve is available only for binary measures.")
        fields.addRow("", self.futility)
        fields.addRow("", self.lil)

        advanced = QToolButton(self)
        advanced.setText("Advanced")
        advanced.setAccessibleName("Advanced")
        advanced.setCheckable(True)
        advanced.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        advanced.setArrowType(Qt.ArrowType.RightArrow)
        outer.addWidget(advanced, 0, Qt.AlignmentFlag.AlignLeft)
        advanced_fields = QWidget(self)
        advanced_layout = QFormLayout(advanced_fields)
        self.manual = self._check("Enter required information size manually", saved.manual_ris is not None)
        self.manual_ris = self._line("Required information size", saved.manual_ris)
        self.manual_ris.setEnabled(self.manual.isChecked())
        advanced_layout.addRow(self.manual, self.manual_ris)
        outer.addWidget(advanced_fields)
        advanced_fields.hide()
        advanced.toggled.connect(advanced_fields.setVisible)
        advanced.toggled.connect(lambda opened: advanced.setArrowType(
            Qt.ArrowType.DownArrow if opened else Qt.ArrowType.RightArrow))

        self.status = QLabel()
        self.status.setAccessibleName("Trial sequential analysis preview")
        qt_layout.configure_context_label(self.status)
        outer.addWidget(self.status)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.run_button = required(buttons.button(QDialogButtonBox.StandardButton.Ok), "Run analysis button")
        self.run_button.setText("Run analysis")
        self.run_button.setAccessibleName("Run analysis")
        outer.addWidget(buttons)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self._run)

        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(120)
        self.preview_timer.timeout.connect(self._preview)
        for combo in (self.order, self.test, self.heterogeneity, self.spending):
            combo.currentIndexChanged.connect(self._schedule_preview)
        for spin in (self.alpha, self.power):
            spin.valueChanged.connect(self._schedule_preview)
        for field in (self.effect, self.control, self.variance, self.manual_ris):
            if field is not None:
                field.textChanged.connect(self._schedule_preview)
        for check in (self.futility, self.lil, self.manual):
            check.toggled.connect(self._schedule_preview)
        self.manual.toggled.connect(self.manual_ris.setEnabled)
        controller = adaptive_window.register_adaptive_window(self, adaptive_window.WindowRole.TRANSACTIONAL)
        adaptive_window.set_content_preferred_width(self, 560, 700)
        self._preview()
        controller.request_content_refit()

    def _choice(self, name: str, choices: list[tuple[str, str]], selected: str) -> QComboBox:
        widget = QComboBox(self)
        widget.setAccessibleName(name)
        for label, value in choices:
            widget.addItem(label, value)
        widget.setCurrentIndex(max(0, widget.findData(selected)))
        return widget

    def _percent(self, name: str, lower: float, upper: float, value: float) -> QDoubleSpinBox:
        widget = QDoubleSpinBox(self)
        widget.setAccessibleName(name)
        widget.setRange(lower, upper)
        widget.setSuffix("%")
        widget.setValue(value)
        return widget

    def _check(self, name: str, checked: bool) -> QCheckBox:
        widget = QCheckBox(name, self)
        widget.setAccessibleName(name)
        widget.setChecked(checked)
        return widget

    def _line(self, name: str, value: float | None) -> QLineEdit:
        line = QLineEdit(self)
        line.setAccessibleName(name)
        if value is not None:
            line.setText(format(value, ".15g"))
        return line

    def _input(self, layout: QFormLayout, name: str, value: float | None) -> tuple[QLineEdit, QLabel]:
        line = self._line(name, value)
        source = _muted_label()
        self._row(layout, name, line, source)
        return line, source

    def _default_input(self, layout: QFormLayout, name: str, value: float | None) -> QLineEdit:
        line = self._line(name, value)
        source = _muted_label()
        reset = QPushButton("Use default", self)
        reset.setAccessibleName(f"Use default for {name.lower()}")
        reset.setFlat(True)
        reset.setForegroundRole(QPalette.ColorRole.Link)
        self.default_inputs[line] = source, reset
        if value is not None:
            self.entered_inputs.add(line)
        reset.setVisible(value is not None)
        reset.clicked.connect(lambda: self._restore_default(line))
        line.textChanged.connect(lambda: self._mark_entered(line))
        self._row(layout, name, line, source, reset)
        return line

    def _mark_entered(self, line: QLineEdit) -> None:
        self.entered_inputs.add(line)
        source, reset = self.default_inputs[line]
        source.setText("Entered")
        reset.show()

    def _restore_default(self, line: QLineEdit) -> None:
        self.entered_inputs.discard(line)
        with QSignalBlocker(line):
            line.clear()
        self._schedule_preview()

    def _show_default(self, line: QLineEdit, value: str, description: str) -> None:
        source, reset = self.default_inputs[line]
        entered = line in self.entered_inputs
        if not entered:
            with QSignalBlocker(line):
                line.setText(value)
        source.setText("Entered" if entered else description)
        reset.setVisible(entered)

    @staticmethod
    def _row(layout: QFormLayout, name: str, editor: QWidget, source: QLabel | None = None, reset: QPushButton | None = None) -> None:
        label = QLabel(name)
        label.setBuddy(editor)
        if source is None:
            layout.addRow(label, editor)
        else:
            contents = QHBoxLayout()
            contents.addWidget(editor, 1)
            contents.addWidget(source, 2)
            if reset is not None:
                contents.addWidget(reset)
            layout.addRow(label, contents)

    @staticmethod
    def _value(widget: QLineEdit | None) -> float | None:
        if widget is None or not widget.text().strip():
            return None
        try:
            value = float(widget.text())
        except ValueError:
            raise ValueError(f"Enter a number for {widget.accessibleName().lower()}.") from None
        if not isfinite(value):
            raise ValueError(f"Enter a finite number for {widget.accessibleName().lower()}.")
        return value

    def _request(self) -> TsaRequest:
        test = str(self.test.currentData())
        control = self._value(self.control) if self.control in self.entered_inputs else None
        manual_ris = self._value(self.manual_ris) if self.manual.isChecked() else None
        if self.manual.isChecked() and manual_ris is None:
            raise ValueError("Enter the required information size.")
        return replace(self.base_request, options=TsaOptions(
            str(self.order.currentData()), test, self.alpha.value() / 100, self.power.value() / 100,
            self._value(self.effect) if self.effect in self.entered_inputs else None,
            None if control is None else control / 100, self._value(self.variance),
            str(self.heterogeneity.currentData()), str(self.spending.currentData()),
            self.futility.isChecked() and test == "two-sided", self.lil.isChecked(), manual_ris,
        ))

    def _schedule_preview(self) -> None:
        self.run_button.setEnabled(False)
        self.preview_timer.start()

    def _preview(self) -> None:
        two_sided = self.test.currentData() == "two-sided"
        self.futility.setEnabled(two_sided)
        self.futility.setToolTip("" if two_sided else "Futility boundaries are available only for two-sided tests.")
        try:
            request = self._request()
            preview = self.service.preview(self.model, request)
            self._show_preview(request.options, preview)
        except Exception as error:
            self.run_button.setEnabled(False)
            self.status.setText(str(error).strip())

    def _show_preview(self, options: TsaOptions, preview: TsaPreview) -> None:
        defaults = preview.defaults
        self._show_default(
            self.effect, "" if defaults.anticipated_effect is None else f"{defaults.anticipated_effect:.4g}",
            EFFECT_SOURCES.get(preview.effect_source, ""),
        )
        if self.control is not None:
            pc = defaults.control_proportion
            self._show_default(self.control, "" if pc is None else f"{100 * pc:.2f}",
                               "Unweighted mean of control arms")
        if self.variance is not None:
            self.variance.setPlaceholderText("" if defaults.variance is None else f"{defaults.variance:.6g}")
            self.variance_source.setText("Entered" if options.variance is not None else "Fixed-effect-weighted pooled arm variance")
        if self.heterogeneity.isEnabled():
            value = preview.i2 if options.heterogeneity == "i2" else preview.d2
            self.heterogeneity_value.setText(
                f"{self.heterogeneity.currentText()} = {value:.0%}"
                if options.heterogeneity != "none" and value is not None else "")
        ris, accrued = preview.ris, preview.accrued
        ready = preview.ready and ris is not None and isfinite(ris) and ris > 0 and accrued is not None
        self.run_button.setEnabled(ready)
        if not ready or ris is None or accrued is None:
            self.status.setText(preview.reason or "The required information size must be finite and positive.")
        elif self.hr:
            self.status.setText(f"Required statistical information: {ris:,.4g} · accrued {accrued:,.4g} ({accrued / ris:.0%})")
        else:
            self.status.setText(f"Required information size: {ris:,.0f} participants · accrued {accrued:,.0f} ({accrued / ris:.0%})")

    def _run(self) -> None:
        self.run_button.setEnabled(False)
        progress = progress_dialog.AnalysisProgressDialog(self, operation="Running trial sequential analysis…")
        progress.show()
        progress.repaint()
        try:
            request = self._request()
            run = self.service.run(self.model, request)
            context = dataset_identity(self.model)
            result = replace(run.result, identity=f"{TSA_TITLE} — {context}", manuscript_title=TSA_TITLE)
            manuscript = trial_sequential_report(run, request, context)
            self.on_result(result, source_sheet=self.sheet, manuscript=manuscript)
            options = replace(request.options, futility=self.futility.isChecked())
            saved = TsaOptions.from_mapping(self.sheet.settings.get(TSA_SETTINGS, {}))
            if saved != options:
                self.sheet.settings[TSA_SETTINGS] = options.to_mapping()
                self.on_settings_saved()
            self.accept()
        except Exception as error:
            app_error_handler.log_exception(type(error), error, error.__traceback__)
            self.status.setText(str(error).strip())
            self.run_button.setEnabled(True)
        finally:
            progress_dialog.dispose(progress)
