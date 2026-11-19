# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Set up trial sequential analysis on the active sheet."""

from collections.abc import Callable
from dataclasses import replace
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory

from PyQt6.QtCore import QProcess, QSignalBlocker, Qt, QTimer
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QToolButton, QVBoxLayout, QWidget,
)

from rc_metastudio import adaptive_window, app_error_handler, progress_dialog, qt_layout
from rc_metastudio.analysis_identity import dataset_identity
from rc_metastudio.analysis_results import AnalysisResult
from rc_metastudio.dataset_table_model import DatasetTableModel
from rc_metastudio.manuscript_report import ManuscriptReport, trial_sequential_report
from rc_metastudio.qt_object_guard import required
from rc_metastudio.settings import make_r_tmp
from rc_metastudio.trial_sequential_analysis import (
    EFFECT_SOURCES, HKSJ_NOTE, TSA_TITLE, TsaOptions, TsaPreview, TsaRequest, TsaService, preview_conclusion,
)

TOOLTIPS = {
    "Type I error (α)": "Overall chance of a false-positive conclusion, controlled across all looks at the accumulating data.",
    "Power": "Chance of detecting the anticipated effect once the required information size is reached.",
    "Anticipated intervention effect": "The smallest effect the analysis should be able to detect. The default is the confidence limit of the pooled estimate closest to no effect.",
    "Control event proportion": "Expected risk of the outcome in the control group. The default is the unweighted mean of the trials' control arms.",
    "Participant variance": "Variance of the outcome among participants, used to convert the mean difference into a required number of participants.",
    "Heterogeneity adjustment": "Inflates the required information size for between-trial variation. D² (diversity) is recommended; I² usually underestimates it.",
    "Add studies in": "The order in which trials enter the cumulative analysis. Publication year reproduces how evidence accumulated.",
    "Test": "Two-sided tests look for benefit or harm. One-sided tests monitor a single direction.",
    "Boundaries": "O'Brien-Fleming boundaries are strict early and relax as information accrues. Pocock boundaries are equally strict at every look.",
    "Futility boundaries": "Shows the region where the anticipated effect becomes unlikely. Non-binding: crossing it does not stop the analysis.",
    "Penalised Z-curve": "An alternative to monitoring boundaries that penalises the Z-score for repeated testing (law of the iterated logarithm). Binary measures only.",
}
CHECKING_BOUNDARIES = "Checking boundary crossings…"


class _DesignPercent(QDoubleSpinBox):
    def textFromValue(self, value: float) -> str:
        # Preserve the original endpoints and any saved hundredths.
        decimals = 1 if value == round(value, 1) else 2
        return self.locale().toString(value, "f", decimals)


def _muted_label(text: str = "") -> QLabel:
    label = QLabel(text)
    qt_layout.configure_context_label(label)
    label.setForegroundRole(QPalette.ColorRole.PlaceholderText)
    return label


class TrialSequentialAnalysisDialog(QDialog):
    def __init__(
        self, model: DatasetTableModel, parent: QWidget, *,
        saved: TsaOptions, on_result: Callable[[AnalysisResult, ManuscriptReport], None],
        on_settings_saved: Callable[[TsaOptions], None],
        service: TsaService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(TSA_TITLE)
        self.setModal(True)
        self.model = model
        self.on_result = on_result
        self.on_settings_saved = on_settings_saved
        self.service = service or TsaService()
        self.base_request = TsaRequest.from_sheet(model, saved)
        self.default_inputs: dict[QLineEdit, tuple[QLabel, QPushButton]] = {}
        self.entered_inputs: set[QLineEdit] = set()
        self.binary = self.base_request.family == "binary"
        self.hr = self.base_request.metric == "HR"
        outer = QVBoxLayout(self)
        summary = QLabel(f"Measure: {self.base_request.measure} · Model: {self.base_request.model_label} · Wald z")
        qt_layout.configure_context_label(summary)
        outer.addWidget(summary)
        if self.base_request.inference in {"knha", "adhoc"}:
            outer.addWidget(_muted_label(HKSJ_NOTE))

        fields = QFormLayout()
        outer.addLayout(fields)
        self._setup_design_fields(fields, saved)

        self._section(fields, "Monitoring")
        self.order = self._choice("Add studies in", [("Publication year", "year"), ("Table order", "table")], saved.order)
        for widget in (self.order, self.test):
            self._row(fields, widget.accessibleName(), widget)
        self.spending = self._choice("Boundaries", [("O'Brien-Fleming", "obf"), ("Pocock", "pocock")], saved.spending)
        self._row(fields, "Boundaries", self.spending)
        self.futility = self._check("Futility boundaries", saved.futility)
        self.lil = self._check("Penalised Z-curve", saved.lil and self.binary)
        self.lil.setEnabled(self.binary)
        for check in (self.futility, self.lil):
            check.setToolTip(TOOLTIPS[check.text()])
            fields.addRow("", check)

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
        self.status.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        outer.addWidget(self.status)
        self.conclusion = _muted_label()
        self.conclusion.setAccessibleName("Trial sequential analysis preview conclusion")
        self.conclusion.setMinimumHeight(self.conclusion.fontMetrics().lineSpacing())
        outer.addWidget(self.conclusion)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.run_button = required(buttons.button(QDialogButtonBox.StandardButton.Ok), "Run analysis button")
        self.run_button.setText("Run analysis")
        self.run_button.setAccessibleName("Run analysis")
        outer.addWidget(buttons)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self._run)

        self._connect_preview()
        controller = adaptive_window.register_adaptive_window(self, adaptive_window.WindowRole.TRANSACTIONAL)
        adaptive_window.set_content_preferred_width(self, 560, 700)
        self._preview()
        self.conclusion_timer.start()
        controller.request_content_refit()

    def _setup_design_fields(self, fields: QFormLayout, saved: TsaOptions) -> None:
        self._section(fields, "Design assumptions")
        left, right = self.base_request.favoured_labels()
        self.test = self._choice("Test", [("Two-sided", "two-sided"),
                                          (f"One-sided (favours {left})", "benefit"),
                                          (f"One-sided (favours {right})", "harm")], saved.test)
        self.alpha = self._percent("Type I error (α)", .01, 49.99, 100 * saved.alpha)
        self.power = self._percent("Power", 50.01, 99.99, 100 * saved.power)
        self.initial_alpha = self.alpha.value()
        self.initial_power = self.power.value()
        for widget in (self.alpha, self.power):
            self._row(fields, widget.accessibleName(), widget)

        self.effect = self._default_input(fields, f"Anticipated intervention effect ({self.base_request.measure})",
                                          saved.anticipated_effect)
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
        self.fixed_effect_notice = _muted_label()
        fields.addRow(self.fixed_effect_notice)
        self.fixed_effect_notice.hide()

    def _connect_preview(self) -> None:
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(120)
        self.preview_timer.timeout.connect(self._preview)
        self.conclusion_timer = QTimer(self)
        self.conclusion_timer.setSingleShot(True)
        self.conclusion_timer.setInterval(600)
        self.conclusion_timer.timeout.connect(self._start_conclusion)
        self.conclusion_process = QProcess(self)
        self.conclusion_process.finished.connect(self._conclusion_finished)
        self.conclusion_process.errorOccurred.connect(self._conclusion_error)
        self.conclusion_dir: TemporaryDirectory[str] | None = None
        self.ready_preview: tuple[TsaRequest, float, float] | None = None
        self.active_preview: tuple[TsaRequest, float, float] | None = None
        self.finished.connect(self._stop_conclusion)
        self.finished.connect(self.preview_timer.stop)
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

    def _choice(self, name: str, choices: list[tuple[str, str]], selected: str) -> QComboBox:
        widget = QComboBox(self)
        widget.setAccessibleName(name)
        for label, value in choices:
            widget.addItem(label, value)
        widget.setCurrentIndex(max(0, widget.findData(selected)))
        return widget

    def _percent(self, name: str, lower: float, upper: float, value: float) -> QDoubleSpinBox:
        widget = _DesignPercent(self)
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
            line.setText(str(value).removesuffix(".0"))
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
    def _section(fields: QFormLayout, title: str) -> None:
        heading = QLabel(title)
        font = heading.font()
        font.setBold(True)
        heading.setFont(font)
        fields.addRow(heading)

    @staticmethod
    def _row(layout: QFormLayout, name: str, editor: QWidget, source: QLabel | None = None, reset: QPushButton | None = None) -> None:
        label = QLabel(name)
        label.setBuddy(editor)
        tooltip = TOOLTIPS.get(name, TOOLTIPS.get(name.partition(" (")[0]))
        if tooltip is not None:
            editor.setToolTip(tooltip)
            label.setToolTip(tooltip)
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
        saved = self.base_request.options
        alpha, power = self.alpha.value(), self.power.value()
        control = self._value(self.control) if self.control in self.entered_inputs else None
        if control is not None:
            control = (saved.control_proportion if saved.control_proportion is not None
                       and control == 100 * saved.control_proportion else control / 100)
        manual_ris = self._value(self.manual_ris) if self.manual.isChecked() else None
        if self.manual.isChecked() and manual_ris is None:
            raise ValueError("Enter the required information size.")
        return replace(self.base_request, options=TsaOptions(
            str(self.order.currentData()), test,
            saved.alpha if alpha == self.initial_alpha else alpha / 100,
            saved.power if power == self.initial_power else power / 100,
            self._value(self.effect) if self.effect in self.entered_inputs else None,
            control, self._value(self.variance),
            str(self.heterogeneity.currentData()), str(self.spending.currentData()),
            self.futility.isChecked() and test == "two-sided", self.lil.isChecked(), manual_ris,
        ))

    def _schedule_preview(self) -> None:
        self.run_button.setEnabled(False)
        self._stop_conclusion()
        self.preview_timer.start()
        self.conclusion_timer.start()

    def _stop_conclusion(self) -> None:
        self.conclusion_timer.stop()
        self.conclusion.clear()
        self.ready_preview = None
        self.active_preview = None
        if self.conclusion_process.state() != QProcess.ProcessState.NotRunning:
            self.conclusion_process.kill()

    def _start_conclusion(self) -> None:
        if self.ready_preview is None or self.conclusion_dir is not None:
            return
        self.active_preview = self.ready_preview
        request, _, _ = self.active_preview
        try:
            self.conclusion_dir = TemporaryDirectory(prefix="tsa-conclusion-", dir=make_r_tmp())
            program, arguments = self.service.conclusion_command(self.model, request, Path(self.conclusion_dir.name))
            self.conclusion_process.start(program, arguments)
        except Exception as error:
            self._release_conclusion_files()
            self.conclusion.clear()
            app_error_handler.log_exception(type(error), error, error.__traceback__)

    def _release_conclusion_files(self) -> None:
        if self.conclusion_dir is not None:
            self.conclusion_dir.cleanup()
            self.conclusion_dir = None
        self.active_preview = None

    def _conclusion_finished(self, code: int, status: QProcess.ExitStatus) -> None:
        active = self.active_preview
        text = ""
        try:
            if (code != 0 or status != QProcess.ExitStatus.NormalExit
                    or active is None or self.conclusion_dir is None):
                return
            outcome = Path(self.conclusion_dir.name) / "outcome.txt"
            if outcome.is_file():
                category, look, study = outcome.read_text(encoding="utf-8").split("\n", 2)
                _, accrued, ris = active
                text = preview_conclusion(category, look, study, accrued, ris)
        except (OSError, ValueError) as error:
            app_error_handler.log_exception(type(error), error, error.__traceback__)
        finally:
            self._release_conclusion_files()
            if active is not None:
                self.conclusion.setText(text)
            elif self.ready_preview is not None and not self.conclusion_timer.isActive():
                self._start_conclusion()

    def _conclusion_error(self, error: QProcess.ProcessError) -> None:
        if error == QProcess.ProcessError.FailedToStart:
            self._release_conclusion_files()
            self.conclusion.clear()

    def _preview(self) -> None:
        two_sided = self.test.currentData() == "two-sided"
        self.futility.setEnabled(two_sided)
        try:
            request = self._request()
            preview = self.service.preview(self.model, request)
            self._show_preview(request, preview)
        except Exception as error:
            self.ready_preview = None
            self.conclusion.clear()
            self.run_button.setEnabled(False)
            self.fixed_effect_notice.hide()
            self.status.setText(str(error).strip())

    def _effect_equivalent(self, options: TsaOptions, defaults: TsaOptions) -> str:
        effect = options.anticipated_effect if options.anticipated_effect is not None else defaults.anticipated_effect
        metric = self.base_request.metric
        if effect is None or metric == "MD":
            return ""
        if metric == "RD":
            precision = 1 if abs(effect) < .1 else 0
            return f"{100 * effect:.{precision}f} percentage points".replace("-", "−")
        pc = options.control_proportion if options.control_proportion is not None else defaults.control_proportion
        at_control = ""
        if metric == "OR":
            if pc is None or not 0 < pc < 1:
                return ""
            effect = effect / (1 - pc + pc * effect)
            at_control = f" at {pc:.2%} control risk"
        change = effect - 1
        precision = 1 if round(abs(change), 12) < .1 else 0
        direction = "reduction" if change < 0 else "increase"
        measure = "hazard" if self.hr else "risk"
        return f"≈ {abs(change):.{precision}%} relative {measure} {direction}{at_control}"

    def _show_design_defaults(self, options: TsaOptions, preview: TsaPreview) -> None:
        defaults = preview.defaults
        self._show_default(
            self.effect, "" if defaults.anticipated_effect is None else f"{defaults.anticipated_effect:.4g}",
            EFFECT_SOURCES.get(preview.effect_source, ""),
        )
        equivalent = self._effect_equivalent(options, defaults)
        if equivalent:
            source = self.default_inputs[self.effect][0]
            source.setText(f"{source.text()} · {equivalent}")
        if self.control is not None:
            pc = defaults.control_proportion
            self._show_default(self.control, "" if pc is None else f"{100 * pc:.2f}",
                               "Unweighted mean of control arms")
        if self.variance is not None:
            self.variance.setPlaceholderText("" if defaults.variance is None else f"{defaults.variance:.6g}")
            self.variance_source.setText("Entered" if options.variance is not None else "Fixed-effect-weighted pooled arm variance")

    def _show_heterogeneity(self, options: TsaOptions, preview: TsaPreview) -> None:
        if self.heterogeneity.isEnabled():
            measure, value = ("I²", preview.i2) if options.heterogeneity == "i2" else ("D²", preview.d2)
            label = "" if value is None else f"{measure} = {value:.0%}"
            if options.heterogeneity != "none" and value is not None:
                percent = f"{value:.1%}"
                remainder = 100 - float(percent.removesuffix("%"))
                label = f"{measure} = {percent}"
                if remainder > 0:
                    label += f" (size ×{100 / remainder:.1f})"
            self.heterogeneity_value.setText(label)
        note = preview.fixed_effect_note
        size, units = ("required information", "units of information") if self.hr else (
            "required information size", "participants")
        notice = ""
        if note is not None:
            ris = f"{note.ris:,.1f}" if self.hr else f"{note.ris:,.0f}"
            notice = (f"Fixed-effect model: the {size} ignores heterogeneity. "
                      f"With random effects, D² = {note.d2:.0%} and it would be {ris} {units}.")
        elif preview.fixed_effect_zero:
            notice = "Fixed-effect model: random effects estimate D² = 0%, so the size is unchanged."
        self.fixed_effect_notice.setText(notice)
        self.fixed_effect_notice.setVisible(bool(notice))

    def _show_preview(self, request: TsaRequest, preview: TsaPreview) -> None:
        self._show_design_defaults(request.options, preview)
        self._show_heterogeneity(request.options, preview)
        ris, accrued = preview.ris, preview.accrued
        ready = preview.ready and ris is not None and isfinite(ris) and ris > 0 and accrued is not None
        self.run_button.setEnabled(ready)
        self.ready_preview = None
        if not ready or ris is None or accrued is None:
            self.status.setText(preview.reason or "The required information size must be finite and positive.")
        elif self.hr:
            self.status.setText(f"Required statistical information: {ris:,.4g} · accrued {accrued:,.4g} ({accrued / ris:.0%})")
        else:
            self.status.setText(f"Required information size: {ris:,.0f} participants · accrued {accrued:,.0f} ({accrued / ris:.0%})")
        if ready and ris is not None and accrued is not None:
            self.ready_preview = request, accrued, ris
            self.conclusion.setText(CHECKING_BOUNDARIES)
        else:
            self.conclusion.clear()

    def _run(self) -> None:
        self._stop_conclusion()
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
            options = replace(request.options, futility=self.futility.isChecked())
            self.on_result(result, manuscript)
            self.on_settings_saved(options)
            self.accept()
        except Exception as error:
            app_error_handler.log_exception(type(error), error, error.__traceback__)
            self.status.setText(str(error).strip())
            self.run_button.setEnabled(True)
        finally:
            progress_dialog.dispose(progress)
