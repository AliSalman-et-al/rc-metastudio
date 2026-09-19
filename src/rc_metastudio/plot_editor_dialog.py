# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Edit the presentation and output path of a generated plot."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QWidget,
)
from typing import TYPE_CHECKING

from rc_metastudio import adaptive_window, app_error_handler, plot_capabilities, qt_text
from rc_metastudio.plot_defaults import FOREST_ARM_LABELS
from rc_metastudio.plot_text import (
    apply_plot_text_input_limits,
    plot_parameter_text_value,
    plot_text_value,
    set_plot_text_value,
)

if TYPE_CHECKING:
    from ui_edit_plot_dialog import Ui_EditPlotDialog
else:
    from rc_metastudio.forms.ui_edit_plot_dialog import Ui_EditPlotDialog


PLOT_EDITOR_SAVE_FILTER = "Plot images (*.pdf *.png *.tif *.tiff *.svg);;All files (*)"
FOREST_STYLE_LABELS = {
    "default": "Default (metafor)",
    "revman": "RevMan",
    "bmj": "BMJ",
}
FOREST_STYLE_VALUES = {label: value for value, label in FOREST_STYLE_LABELS.items()}
FOREST_STYLE_DEFAULT_COLORS = {
    "default": "#2f5597",
    "revman": "#000000",
    "bmj": "#6b58a6",
}


class EditPlotDialog(QDialog, Ui_EditPlotDialog):
    applied = pyqtSignal()

    def __init__(self, plot_params, image_path, parent=None, plot_type="forest"):
        super(EditPlotDialog, self).__init__(parent)
        self.setupUi(self)
        self._pending_ok = False
        self._allow_close = True
        self._commit_outcome = None
        self._configure_accessibility()
        self._hide_internal_plot_path_controls()
        apply_plot_text_input_limits(self)
        self._loading_style = False
        self._params = dict(plot_params or {})
        self.plot_type = plot_type
        self._is_reitsma_coefficient = bool(
            self._params.get("reitsma.coefficient.scale")
        )
        option_kind = (
            "reitsma_coefficient" if self._is_reitsma_coefficient else plot_type
        )
        self._option_groups = plot_capabilities.option_groups(option_kind)
        self._sroc_group = None
        if self.plot_type == "sroc":
            self._build_sroc_controls()
            apply_plot_text_input_limits(self)

        self.color_btn.clicked.connect(
            app_error_handler.safe_slot(self._choose_color, parent=self)
        )
        self.save_btn.clicked.connect(
            app_error_handler.safe_slot(self._browse_image_path, parent=self)
        )
        self.style_cbo.currentTextChanged.connect(
            app_error_handler.safe_slot(self._style_changed, parent=self)
        )
        # The generated form connects accepted() directly to accept(). Route
        # both Apply and OK through the transactional commit boundary first.
        try:
            self.buttonBox.accepted.disconnect(self.accept)
        except TypeError:
            pass
        self.buttonBox.clicked.connect(self._button_clicked)

        self._load_params(image_path)
        self._configure_option_groups()
        adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )

    def _configure_accessibility(self):
        """Name static controls and expose an inline commit error region."""
        self._commit_error = QLabel(self.content_scroll_contents)
        self._commit_error.setObjectName("plot_commit_error")
        self._commit_error.setWordWrap(True)
        self._commit_error.setStyleSheet("color: #b00020;")
        self._commit_error.setAccessibleName("Plot edit error")
        self._commit_error.setAccessibleDescription(
            "A plot edit could not be rendered. The last successful plot remains active."
        )
        self._commit_error.hide()
        self.content_layout.addWidget(self._commit_error)
        controls = {
            self.style_cbo: ("Plot style", "Choose the visual style used to draw the plot."),
            self.color_btn: ("Choose plot accent color", "Open a color picker for the plot accent color."),
            self.point_size_multiplier: ("Plot point size", "Scale study points in the plot."),
            self.x_lbl_le: ("Plot X-axis label", "Set the X-axis label or leave it at the default."),
            self.plot_lb_le: ("Plot lower bound", "Set an optional lower bound for the plot axis."),
            self.plot_ub_le: ("Plot upper bound", "Set an optional upper bound for the plot axis."),
            self.x_ticks_le: ("Plot X-axis ticks", "Set optional comma-separated X-axis tick values."),
            self.show_summary_line: ("Show summary line", "Show or hide the summary line."),
            self.show_regression_line: ("Show regression line", "Show or hide the fitted regression line."),
            self.show_confidence_band: ("Show confidence band", "Show or hide the confidence band."),
            self.show_prediction_interval: ("Show prediction interval", "Show or hide the prediction interval."),
            self.show_legend: ("Show legend", "Show or hide the plot legend."),
        }
        for control, (name, description) in controls.items():
            control.setAccessibleName(name)
            control.setAccessibleDescription(description)
            control.setToolTip(description)
        self.color_btn.setToolTip("Choose the plot accent color")

    def mark_commit_succeeded(self):
        """Allow an OK commit to close only after rendering succeeds."""
        self._params = self.plot_params()
        self._allow_close = True
        self._commit_outcome = True
        self._commit_error.clear()
        self._commit_error.hide()
        if self._pending_ok:
            super().accept()

    def mark_commit_failed(self, message):
        """Keep the editor open and show the rendering failure inline."""
        self._allow_close = False
        self._commit_outcome = False
        self._commit_error.setText(str(message))
        self._commit_error.show()

    def _commit(self):
        self._commit_outcome = None
        self.applied.emit()
        # Preserve the signal-only API for callers that use the dialog without
        # ResultsWindow. The real integration explicitly marks success/failure.
        if self._commit_outcome is None:
            self.mark_commit_succeeded()

    def _button_clicked(self, button):
        button_type = self.buttonBox.standardButton(button)
        if button_type == QDialogButtonBox.StandardButton.Apply:
            self._pending_ok = False
            self._commit()
        elif button_type == QDialogButtonBox.StandardButton.Ok:
            self._pending_ok = True
            self._allow_close = False
            self._commit()

    def accept(self):
        if getattr(self, "_pending_ok", False) and not getattr(
            self, "_allow_close", True
        ):
            return
        super().accept()

    def _hide_internal_plot_path_controls(self):
        """Keep the generated artifact path as implementation state only."""
        for widget in (self.label_3, self.image_path, self.save_btn):
            widget.hide()

    def _configure_option_groups(self):
        self.groupBox.setVisible("columns" in self._option_groups)
        self.default_panel.setVisible("forest" in self._option_groups)
        self.label_16.setVisible("summary" in self._option_groups)
        self.show_summary_line.setVisible("summary" in self._option_groups)
        self.regression_group.setVisible("regression" in self._option_groups)
        if self._sroc_group is not None:
            self._sroc_group.setVisible(True)

    def _build_sroc_controls(self):
        self._sroc_group = QWidget(self.content_scroll_contents)
        self._sroc_group.setObjectName("sroc_options")
        layout = QFormLayout(self._sroc_group)
        self.sroc_ylabel = QLineEdit(self._sroc_group)
        self.sroc_marker_area = QComboBox(self._sroc_group)
        self.sroc_marker_area.addItem("Uniform", "uniform")
        self.sroc_marker_area.addItem("Sample-size area", "sample-size")
        self.sroc_show_labels = QCheckBox("Show study labels", self._sroc_group)
        self.sroc_extrapolate = QCheckBox("Extrapolate curve to 0–1", self._sroc_group)
        self.sroc_curve_color = QLineEdit(self._sroc_group)
        self.sroc_confidence_color = QLineEdit(self._sroc_group)
        self.sroc_prediction_color = QLineEdit(self._sroc_group)
        self.sroc_curve_lty = QComboBox(self._sroc_group)
        self.sroc_confidence_lty = QComboBox(self._sroc_group)
        self.sroc_prediction_lty = QComboBox(self._sroc_group)
        for combo in (self.sroc_curve_lty, self.sroc_confidence_lty, self.sroc_prediction_lty):
            combo.addItems(["Solid", "Dashed", "Dotted", "Dot-dash"])
        self.sroc_text_cex = QDoubleSpinBox(self._sroc_group)
        self.sroc_text_cex.setRange(.2, 3.)
        self.sroc_text_cex.setSingleStep(.1)
        self.sroc_show_confidence = QCheckBox("Show confidence region", self._sroc_group)
        self.sroc_show_prediction = QCheckBox("Show joint prediction region", self._sroc_group)
        self.sroc_show_summary = QCheckBox("Show summary point", self._sroc_group)
        self.sroc_show_auc = QCheckBox("Show normalized pAUC annotation", self._sroc_group)
        self.sroc_show_curve_legend = QCheckBox(
            "Show curve legend", self._sroc_group
        )
        self.sroc_show_marker_legend = QCheckBox(
            "Show marker-size legend", self._sroc_group
        )
        self.sroc_y_lower = QLineEdit(self._sroc_group)
        self.sroc_y_upper = QLineEdit(self._sroc_group)
        self.sroc_y_ticks = QLineEdit(self._sroc_group)
        self.sroc_marker_area.currentIndexChanged.connect(
            self._sync_sroc_marker_legend
        )
        for control, name, description in (
            (self.sroc_ylabel, "SROC Y-axis label", "Set the SROC Y-axis label."),
            (self.sroc_y_lower, "SROC Y-axis lower bound", "Set an optional lower bound for the SROC Y-axis."),
            (self.sroc_y_upper, "SROC Y-axis upper bound", "Set an optional upper bound for the SROC Y-axis."),
            (self.sroc_y_ticks, "SROC Y-axis ticks", "Set optional comma-separated SROC Y-axis tick values."),
            (self.sroc_marker_area, "SROC marker area", "Choose whether marker area is uniform or represents study sample size."),
            (self.sroc_curve_color, "SROC curve color", "Set the color of the SROC curve."),
            (self.sroc_confidence_color, "SROC confidence color", "Set the color of the confidence region."),
            (self.sroc_prediction_color, "SROC prediction color", "Set the color of the prediction region."),
            (self.sroc_curve_lty, "SROC curve line style", "Choose the SROC curve line style."),
            (self.sroc_confidence_lty, "SROC confidence line style", "Choose the confidence-region line style."),
            (self.sroc_prediction_lty, "SROC prediction line style", "Choose the prediction-region line style."),
            (self.sroc_text_cex, "SROC text size", "Set the SROC annotation text size."),
            (self.sroc_show_labels, "Show SROC study labels", "Show or hide study labels on the SROC plot."),
            (self.sroc_extrapolate, "Extrapolate SROC curve", "Extend the SROC curve to the full 0–1 range."),
            (self.sroc_show_confidence, "Show SROC confidence region", "Show or hide the confidence region."),
            (self.sroc_show_prediction, "Show SROC prediction region", "Show or hide the joint prediction region."),
            (self.sroc_show_summary, "Show SROC summary point", "Show or hide the summary point."),
            (self.sroc_show_auc, "Show normalized pAUC annotation", "Show or hide the normalized partial area-under-the-curve annotation."),
            (self.sroc_show_curve_legend, "Show SROC curve legend", "Show or hide the curve legend."),
            (self.sroc_show_marker_legend, "Show SROC marker-size legend", "Show or hide the marker-size legend."),
        ):
            control.setAccessibleName(name)
            control.setAccessibleDescription(description)
            control.setToolTip(description)

        def add_field(label_text, control):
            label = QLabel(label_text, self._sroc_group)
            label.setBuddy(control)
            layout.addRow(label, control)

        add_field("Y-axis label:", self.sroc_ylabel)
        add_field("Y-axis lower bound:", self.sroc_y_lower)
        add_field("Y-axis upper bound:", self.sroc_y_upper)
        add_field("Y-axis ticks:", self.sroc_y_ticks)
        add_field("Marker area:", self.sroc_marker_area)
        layout.addRow(self.sroc_show_labels)
        layout.addRow(self.sroc_extrapolate)
        add_field("Curve color:", self.sroc_curve_color)
        add_field("Confidence color:", self.sroc_confidence_color)
        add_field("Prediction color:", self.sroc_prediction_color)
        add_field("Curve line style:", self.sroc_curve_lty)
        add_field("Confidence line style:", self.sroc_confidence_lty)
        add_field("Prediction line style:", self.sroc_prediction_lty)
        add_field("Text size:", self.sroc_text_cex)
        layout.addRow(self.sroc_show_confidence)
        layout.addRow(self.sroc_show_prediction)
        layout.addRow(self.sroc_show_summary)
        layout.addRow(self.sroc_show_auc)
        layout.addRow(self.sroc_show_curve_legend)
        layout.addRow(self.sroc_show_marker_legend)
        self.content_layout.addWidget(self._sroc_group)

    def _load_params(self, image_path):
        self._loading_style = True
        try:
            style = self._normalized_style(
                self._params.get(self._param_name("style"), "default")
            )
            self.style_cbo.setCurrentText(FOREST_STYLE_LABELS[style])
            self._set_text(
                self.col1_str_edit, self._params.get("fp_col1_str", "Study or Subgroup")
            )
            self._set_text(
                self.col2_str_edit, self._params.get("fp_col2_str", "[default]")
            )
            self._set_text(
                self.col3_str_edit,
                self._params.get("fp_col3_str", FOREST_ARM_LABELS[0]),
            )
            self._set_text(
                self.col4_str_edit,
                self._params.get("fp_col4_str", FOREST_ARM_LABELS[1]),
            )
            self.show_1.setChecked(self._bool_param("fp_show_col1", True))
            self.show_2.setChecked(self._bool_param("fp_show_col2", True))
            self.show_3.setChecked(self._bool_param("fp_show_col3", True))
            self.show_4.setChecked(self._bool_param("fp_show_col4", True))
            self.show_raw_counts.setChecked(
                self._bool_param("fp_show_raw_counts", True)
            )
            self.show_headers.setChecked(self._bool_param("fp_show_headers", True))
            self.show_annotation.setChecked(
                self._bool_param("fp_show_annotation", True)
            )
            self._set_text(
                self.x_lbl_le, self._axis_label_input()
            )
            self._set_text(
                self.plot_lb_le,
                self._params.get(self._param_name("plot_lb"), "[default]"),
            )
            self._set_text(
                self.plot_ub_le,
                self._params.get(self._param_name("plot_ub"), "[default]"),
            )
            ticks_name = "bp_xticks" if self.plot_type == "regression" else "fp_xticks"
            self._set_text(self.x_ticks_le, self._params.get(ticks_name, "[default]"))
            self.show_summary_line.setChecked(
                self._bool_param("fp_show_summary_line", True)
            )
            self._set_text(
                self.image_path,
                image_path or self._params.get(self._param_name("outpath"), ""),
            )
            color = (
                self._params.get(self._param_name("accent_color"))
                or FOREST_STYLE_DEFAULT_COLORS[style]
            )
            self._set_accent_color(color)
            self.point_size_multiplier.setValue(
                self._float_param(self._param_name("point_size_multiplier"), 1.0)
            )
            self.show_regression_line.setChecked(
                self._bool_param("bp_show_regression_line", True)
            )
            self.show_confidence_band.setChecked(
                self._bool_param("bp_show_confidence_band", True)
            )
            self.show_prediction_interval.setChecked(
                self._bool_param(
                    "bp_show_prediction_interval", self.plot_type == "sroc"
                )
            )
            self.show_legend.setChecked(self._bool_param("bp_show_legend", False))
            if self.plot_type == "sroc":
                self._set_text(self.sroc_ylabel, self._params.get("fp_ylabel", "Sensitivity"))
                self._set_text(
                    self.sroc_y_lower,
                    self._params.get("fp_sroc_plot_lb", "[default]"),
                )
                self._set_text(
                    self.sroc_y_upper,
                    self._params.get("fp_sroc_plot_ub", "[default]"),
                )
                self._set_text(
                    self.sroc_y_ticks,
                    self._params.get("fp_sroc_yticks", "[default]"),
                )
                marker = self._params.get("fp_marker_area", "uniform")
                self.sroc_marker_area.setCurrentIndex(1 if marker == "sample-size" else 0)
                self.sroc_show_labels.setChecked(self._bool_param("fp_show_labels", False))
                self.sroc_extrapolate.setChecked(self._bool_param("fp_extrapolate", False))
                self._set_text(self.sroc_curve_color, self._params.get("fp_curve_color", "#2f5597"))
                self._set_text(self.sroc_confidence_color, self._params.get("fp_confidence_color", "#2f5597"))
                self._set_text(self.sroc_prediction_color, self._params.get("fp_prediction_color", "#b45f06"))
                self.sroc_curve_lty.setCurrentIndex(max(0, self._int_param("fp_curve_lty", 1) - 1))
                self.sroc_confidence_lty.setCurrentIndex(max(0, self._int_param("fp_confidence_lty", 2) - 1))
                self.sroc_prediction_lty.setCurrentIndex(max(0, self._int_param("fp_prediction_lty", 3) - 1))
                self.sroc_text_cex.setValue(self._float_param("fp_text_cex", .8))
                self.sroc_show_confidence.setChecked(self._bool_param("fp_show_confidence", True))
                self.sroc_show_prediction.setChecked(self._bool_param("fp_show_prediction", True))
                self.sroc_show_summary.setChecked(self._bool_param("fp_show_summary", True))
                self.sroc_show_auc.setChecked(self._bool_param("fp_show_auc", True))
                self.sroc_show_curve_legend.setChecked(
                    self._bool_param("fp_show_legend", True)
                )
                self.sroc_show_marker_legend.setChecked(
                    self._bool_param(
                        "fp_show_marker_legend", marker == "sample-size"
                    )
                )
                self._sync_sroc_marker_legend()
        finally:
            self._loading_style = False

    def _sync_sroc_marker_legend(self, *_args):
        """Expose marker-size legend only when marker size conveys sample size."""
        if self._sroc_group is None:
            return
        scaled = self.sroc_marker_area.currentData() == "sample-size"
        self.sroc_show_marker_legend.setEnabled(scaled)
        if not scaled:
            self.sroc_show_marker_legend.setChecked(False)
            self.sroc_show_marker_legend.setToolTip(
                "Available when marker area represents study sample size."
            )
        else:
            self.sroc_show_marker_legend.setToolTip(
                "Show the study sample-size examples used to scale markers."
            )

    def _style_changed(self, label):
        if self._loading_style:
            return
        style = FOREST_STYLE_VALUES.get(str(label), "default")
        self._set_accent_color(FOREST_STYLE_DEFAULT_COLORS[style])

    def _choose_color(self):
        current = QColor(self.accent_color.text())
        color = QColorDialog.getColor(current, self, "Plot Accent Color")
        if color.isValid():
            self._set_accent_color(color.name())

    def _browse_image_path(self):
        plot_label = "SROC" if self.plot_type == "sroc" else self.plot_type.title()
        selected_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save %s Plot Image" % plot_label,
            qt_text.to_native_text(self.image_path.text()),
            PLOT_EDITOR_SAVE_FILTER,
        )
        if selected_path:
            self.image_path.setText(selected_path)

    def _set_accent_color(self, color):
        text = str(color or FOREST_STYLE_DEFAULT_COLORS["default"])
        self.accent_color.setText(text)
        self.color_btn.setStyleSheet("background-color: %s;" % text)

    def _set_text(self, widget, value):
        set_plot_text_value(widget, self._scalar(value))

    def _axis_label_input(self):
        value = self._scalar(self._params.get(self._param_name("xlabel")))
        return "" if value in (None, "[default]") else value

    def _axis_label_value(self):
        value = plot_parameter_text_value(self.x_lbl_le)
        return None if value is None else qt_text.to_native_text(value)

    def _scalar(self, value):
        if isinstance(value, (list, tuple)) and value:
            return value[0]
        return value

    def _bool_param(self, name, default):
        value = self._scalar(self._params.get(name, default))
        if isinstance(value, str):
            return value.lower() in ("true", "t", "1", "yes")
        return bool(value)

    def _float_param(self, name, default):
        try:
            return float(self._scalar(self._params.get(name, default)))
        except (TypeError, ValueError):
            return default

    def _int_param(self, name, default):
        try:
            return int(self._scalar(self._params.get(name, default)))
        except (TypeError, ValueError):
            return default

    def _normalized_style(self, style):
        style = str(self._scalar(style) or "default").strip().lower()
        return style if style in FOREST_STYLE_LABELS else "default"

    def _param_name(self, suffix):
        return "%s_%s" % ("bp" if self.plot_type == "regression" else "fp", suffix)

    def plot_params(self):
        style = FOREST_STYLE_VALUES.get(str(self.style_cbo.currentText()), "default")
        params = {
            "fp_style": style,
            "fp_show_col1": self.show_1.isChecked(),
            "fp_col1_str": qt_text.to_native_text(plot_text_value(self.col1_str_edit)),
            "fp_show_col2": self.show_2.isChecked(),
            "fp_col2_str": qt_text.to_native_text(plot_text_value(self.col2_str_edit)),
            "fp_show_col3": self.show_3.isChecked(),
            "fp_col3_str": qt_text.to_native_text(plot_text_value(self.col3_str_edit)),
            "fp_show_col4": self.show_4.isChecked(),
            "fp_col4_str": qt_text.to_native_text(plot_text_value(self.col4_str_edit)),
            "fp_show_raw_counts": self.show_raw_counts.isChecked(),
            "fp_show_headers": self.show_headers.isChecked(),
            "fp_show_annotation": self.show_annotation.isChecked(),
            "fp_accent_color": qt_text.to_native_text(self.accent_color.text()),
            "fp_point_size_multiplier": self.point_size_multiplier.value(),
            "fp_xlabel": self._axis_label_value(),
            "fp_plot_lb": qt_text.to_native_text(self.plot_lb_le.text()),
            "fp_plot_ub": qt_text.to_native_text(self.plot_ub_le.text()),
            "fp_xticks": qt_text.to_native_text(self.x_ticks_le.text()),
            "fp_show_summary_line": self.show_summary_line.isChecked(),
            "fp_outpath": qt_text.to_native_text(self.image_path.text()),
        }
        forest_display_path = self._scalar(self._params.get("fp_display_path", ""))
        if forest_display_path:
            params["fp_display_path"] = forest_display_path
        if self.plot_type == "regression":
            params = {
                "bp_style": style,
                "bp_accent_color": qt_text.to_native_text(self.accent_color.text()),
                "bp_point_size_multiplier": self.point_size_multiplier.value(),
                "bp_xlabel": self._axis_label_value(),
                "bp_plot_lb": qt_text.to_native_text(self.plot_lb_le.text()),
                "bp_plot_ub": qt_text.to_native_text(self.plot_ub_le.text()),
                "bp_xticks": qt_text.to_native_text(self.x_ticks_le.text()),
                "bp_show_regression_line": self.show_regression_line.isChecked(),
                "bp_show_confidence_band": self.show_confidence_band.isChecked(),
                "bp_show_prediction_interval": self.show_prediction_interval.isChecked(),
                "bp_show_legend": self.show_legend.isChecked(),
                "bp_outpath": qt_text.to_native_text(self.image_path.text()),
            }
            regression_display_path = self._scalar(
                self._params.get("bp_display_path", "")
            )
            if regression_display_path:
                params["bp_display_path"] = regression_display_path
        elif self.plot_type == "sroc":
            self._sync_sroc_marker_legend()
            params.update(
                {
                    "fp_ylabel": qt_text.to_native_text(plot_text_value(self.sroc_ylabel)),
                    "fp_sroc_plot_lb": qt_text.to_native_text(self.sroc_y_lower.text()),
                    "fp_sroc_plot_ub": qt_text.to_native_text(self.sroc_y_upper.text()),
                    "fp_sroc_yticks": qt_text.to_native_text(self.sroc_y_ticks.text()),
                    "fp_marker_area": self.sroc_marker_area.currentData(),
                    "fp_show_labels": self.sroc_show_labels.isChecked(),
                    "fp_extrapolate": self.sroc_extrapolate.isChecked(),
                    "fp_curve_color": qt_text.to_native_text(self.sroc_curve_color.text()),
                    "fp_confidence_color": qt_text.to_native_text(self.sroc_confidence_color.text()),
                    "fp_prediction_color": qt_text.to_native_text(self.sroc_prediction_color.text()),
                    "fp_curve_lty": self.sroc_curve_lty.currentIndex() + 1,
                    "fp_confidence_lty": self.sroc_confidence_lty.currentIndex() + 1,
                    "fp_prediction_lty": self.sroc_prediction_lty.currentIndex() + 1,
                    "fp_text_cex": self.sroc_text_cex.value(),
                    "fp_show_confidence": self.sroc_show_confidence.isChecked(),
                    "fp_show_prediction": self.sroc_show_prediction.isChecked(),
                    "fp_show_summary": self.sroc_show_summary.isChecked(),
                    "fp_show_auc": self.sroc_show_auc.isChecked(),
                    "fp_show_legend": self.sroc_show_curve_legend.isChecked(),
                    "fp_show_marker_legend": self.sroc_show_marker_legend.isChecked(),
                }
            )
        elif self._is_reitsma_coefficient:
            params["reitsma.coefficient.scale"] = self._params.get(
                "reitsma.coefficient.scale"
            )
            params["reitsma.moderator.coding"] = self._params.get(
                "reitsma.moderator.coding", {}
            )
        return params
