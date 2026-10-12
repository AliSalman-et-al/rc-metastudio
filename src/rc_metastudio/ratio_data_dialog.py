"""Edit one ratio comparison without discarding its inactive input source."""

from dataclasses import replace
import math

from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QMessageBox, QVBoxLayout,
)

from rc_metastudio import adaptive_window


class RatioDataDialog(QDialog):
    def __init__(self, analysis_unit, groups, metric, parent=None):
        super().__init__(parent)
        self.analysis_unit = analysis_unit
        self.groups = groups
        self.effect_metric = metric
        self.setWindowTitle(f"{metric} study data")
        layout = QVBoxLayout(self)
        self.help_text = QLabel()
        self.help_text.setWordWrap(True)
        layout.addWidget(self.help_text)
        self.form = QFormLayout()
        layout.addLayout(self.form)
        record = analysis_unit.ratio_input(groups)
        self.fields = {}
        self.raw_fields = []
        if metric == "IRR":
            self._add_rate_fields(record)
        self._add_reported_fields(record)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        for field in (*self.raw_fields, *self.fields.values()):
            field.setMinimumWidth(230)
        self.fields["confidence"].setToolTip("Confidence level of the published interval. Analysis confidence is selected separately.")
        self._input_scale = record.scale
        self.fields["scale"].currentIndexChanged.connect(self._change_format)
        if metric == "IRR":
            self.fields["source"].currentIndexChanged.connect(self._update_fields)
        self._update_fields()
        adaptive_window.register_adaptive_window(self, adaptive_window.WindowRole.TRANSACTIONAL)

    def _add_rate_fields(self, record):
        source = QComboBox()
        source.addItem("Choose study data", "")
        source.addItem("Events and person-time", "raw")
        source.addItem("Reported IRR", "reported")
        try:
            selected = record.selected_source(self.analysis_unit.get_raw_data_for_groups(self.groups), metric=self.effect_metric)
        except ValueError:
            selected = ""
        if not any(value not in (None, "") for value in self.analysis_unit.get_raw_data_for_groups(self.groups)) and record.estimate is None:
            selected = "raw"
        source.setCurrentIndex(source.findData(selected))
        self.fields["source"] = source
        self.form.addRow("Study data", source)
        for group in self.groups:
            for label, value in zip(("Events", "Person-time"), self.analysis_unit.get_raw_data_for_group(group)):
                field = QLineEdit("" if value in (None, "") else str(value))
                self.form.addRow(f"{group}: {label}", field)
                self.raw_fields.append(field)

    def _add_reported_fields(self, record):
        labels = {"scale": "Input format", "estimate": self.effect_metric, "lower": "Lower bound",
                  "upper": "Upper bound", "confidence": "Original CI (%)", "se": "Standard error (log scale)",
                  "unit": "Person-time unit"}
        for name, label in labels.items():
            if self.effect_metric == "HR" and name == "unit":
                continue
            if name == "scale":
                field = QComboBox()
                field.addItem("Ratio and confidence interval", "ratio")
                field.addItem("Log ratio and standard error", "log")
                field.setCurrentIndex(field.findData(record.scale))
            else:
                value = getattr(record, name)
                field = QLineEdit("" if value is None else str(value))
            field.setObjectName(f"ratio_{name}")
            self.fields[name] = field
            self.form.addRow(label, field)

    def _change_format(self):
        scale = self.fields["scale"].currentData()
        field = self.fields["estimate"]
        text = field.text().strip()
        if text and scale != self._input_scale:
            try:
                value = float(text)
                field.setText(str(math.log(value) if scale == "log" else math.exp(value)))
            except (ValueError, OverflowError):
                field.clear()
        self._input_scale = scale
        self._update_fields()

    def _update_fields(self):
        raw = self.effect_metric == "IRR" and self.fields["source"].currentData() == "raw"
        reported = self.effect_metric == "HR" or self.fields["source"].currentData() == "reported"
        log = self.fields["scale"].currentData() == "log"
        for field in self.raw_fields:
            self.form.setRowVisible(field, raw)
        visibility = {"unit": raw, "lower": reported and not log,
                      "upper": reported and not log, "confidence": reported and not log,
                      "se": reported and log}
        for name, field in self.fields.items():
            if name == "source":
                continue
            self.form.setRowVisible(field, visibility.get(name, reported))
        label = self.form.labelForField(self.fields["estimate"])
        if isinstance(label, QLabel):
            label.setText(f"Log {self.effect_metric}" if log else self.effect_metric)
        self.help_text.setText(self._input_help(raw, reported, log))
        self.adjustSize()

    @staticmethod
    def _input_help(raw, reported, log):
        return (
            "Enter events and person-time for both groups in the same unit. Recurrent events are allowed."
            if raw else "Enter the reported log ratio and its standard error."
            if reported and log else "Enter the reported ratio and the bounds of its original confidence interval."
            if reported else "Both input sources are present. Choose which study data to use."
        )

    def accept(self):
        try:
            record = replace(self.analysis_unit.ratio_input(self.groups), **self._read_reported_inputs())
            if record.scale == "log" and (self.effect_metric == "HR" or record.source == "reported"):
                if record.se is None:
                    raise ValueError("Enter the standard error of the log ratio.")
                record = replace(record, lower=None, upper=None)
            record.validate()
            raw = self._read_raw_inputs()
            record.selected_source(raw, metric=self.effect_metric)
        except (ValueError, TypeError) as error:
            QMessageBox.warning(self, "Invalid study input", str(error))
            return
        self.analysis_unit.set_ratio_input(self.groups, record)
        if self.effect_metric == "IRR":
            self.analysis_unit.set_raw_data_for_groups(self.groups, [raw[:2], raw[2:]])
        super().accept()

    def _read_reported_inputs(self):
        values = {}
        for name, field in self.fields.items():
            text = field.currentData() if isinstance(field, QComboBox) else field.text().strip()
            values[name] = (float(text) if text else None) if name in ("estimate", "lower", "upper", "se", "confidence") else text
        return values

    def _read_raw_inputs(self):
        raw = [float(field.text()) if field.text().strip() else "" for field in self.raw_fields]
        for i, value in enumerate(raw):
            if isinstance(value, str):
                continue
            if not math.isfinite(value):
                raise ValueError("Raw inputs must be finite.")
            if i % 2 == 0 and (value < 0 or value % 1 != 0):
                raise ValueError("Events must be nonnegative integers.")
            if i % 2 == 1 and value <= 0:
                raise ValueError("Person-time must be positive.")
        return raw
