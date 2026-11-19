# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Edit the presentation of a generated plot."""

import math
from collections.abc import Callable
from typing import TYPE_CHECKING

from rc_metastudio.qt_layout import style_inline_error, align_field_columns, add_color_swatch
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from rc_metastudio import adaptive_window, analysis_identity, app_error_handler, plot_capabilities, qt_text
from rc_metastudio.plot_defaults import BUBBLE_STYLE_ACCENTS, FOREST_ARM_LABELS, PLOT_STYLE_ACCENTS
from rc_metastudio.qt_object_guard import required
from rc_metastudio.plot_style_controls import (
    configure_plot_style,
    configure_tsa_x_axis, load_plot_style, selected_plot_style,
)
from rc_metastudio.plot_text import (
    configure_plot_text_inputs,
    size_plot_text_editor,
    plot_axis_label_params,
    plot_text_value,
    set_plot_text_value,
)
from rc_metastudio.small_study_effects import FUNNEL_STYLE_PRESETS, FunnelStyle

if TYPE_CHECKING:
    from ui_edit_plot_dialog import Ui_EditPlotDialog
else:
    from rc_metastudio.forms.ui_edit_plot_dialog import Ui_EditPlotDialog


class EditPlotDialog(QDialog, Ui_EditPlotDialog):
    rerun_requested = pyqtSignal()

    def __init__(
        self, plot_params, image_path, parent=None, plot_type="forest",
        *, on_commit: Callable[[dict[str, object]], None] | None = None,
    ):
        super(EditPlotDialog, self).__init__(parent)
        self.setupUi(self)
        self._on_commit = on_commit
        self._configure_accessibility()
        configure_plot_text_inputs(self)
        self._params = dict(plot_params or {})
        self.plot_type = plot_type
        self._style_accents = BUBBLE_STYLE_ACCENTS if plot_type == "trial_sequential" else PLOT_STYLE_ACCENTS
        if plot_type == "subgroup_forest":
            note = QLabel("Subgroup figures use the default layout. RevMan and BMJ apply their accent colors; their standard-forest layouts are unavailable for subgroups.", self)
            note.setWordWrap(True)
            self.style_layout.addWidget(note, self.style_layout.rowCount(), 0, 1, 2)
        self._is_reitsma_coefficient = plot_type == "reitsma_coefficient"
        self._option_groups = plot_capabilities.option_groups(plot_type)
        self._setup_study_order()
        self._setup_axis_scale()
        self.tsa_x_axis = QComboBox(self.axis_group)
        if "tsa_axis" in self._option_groups:
            self._setup_tsa_x_axis()
        else:
            self.tsa_x_axis.hide()
        self.default_panel.setTitle("Forest options")
        self._setup_direction_labels()
        self.show_weight = QCheckBox("Show weight column", self)
        self.show_weight.setChecked(self._bool_param("fp_show_weight", True))
        self.show_weight.setVisible(plot_type in {"forest", "subgroup_forest"})
        self.default_layout.addWidget(self.show_weight, self.default_layout.rowCount(), 0, 1, 2)
        self.figure_caption = QLineEdit(self)
        self.figure_caption.setText(str(self._scalar(self._params.get("plot_caption", "")) or "").replace("\n", " · "))
        self.figure_caption.setAccessibleName("Figure caption")
        self.figure_caption.setToolTip("Sheet and arm comparison for standalone figures. Edit or clear to remove.")
        self.figure_caption.setMaxLength(1000)
        caption_label = QLabel("Figure caption", self)
        caption_label.setBuddy(self.figure_caption)
        caption_row = self.style_layout.rowCount()
        caption_columns = self.style_layout.columnCount()
        self.style_layout.addWidget(caption_label, caption_row, 0)
        self.style_layout.addWidget(self.figure_caption, caption_row, 1, 1, caption_columns - 1)
        self._sroc_group = None
        if self.plot_type == "sroc":
            self._build_sroc_controls()
            configure_plot_text_inputs(self)

        self.x_ticks_le.textChanged.connect(self._ticks_changed)
        if self.plot_type == "sroc":
            self.sroc_y_ticks.textChanged.connect(self._ticks_changed)

        self.accent_color.setMaximumWidth(self.accent_color.fontMetrics().height() * 6)
        self.color_btn.setText("Choose…")
        self.color_btn.setMaximumWidth(self.fontMetrics().height() * 12)
        configure_plot_style(self.style_cbo, self.accent_color, self.color_btn, accents=self._style_accents)
        apply_button = required(self.buttonBox.button(QDialogButtonBox.StandardButton.Apply), "plot Apply button")
        apply_button.clicked.connect(self._commit)

        add_color_swatch(self.accent_color, self.accent_color_layout)
        self._load_params(image_path)
        self.setTabOrder(self.style_cbo, self.figure_caption)
        self.setTabOrder(self.figure_caption, self.show_1)
        self._configure_option_groups()
        layouts = [self.style_layout, self.appearance_layout, self.gridLayout_2, self.default_layout, self.regression_layout, self.gridLayout_4]
        if self._sroc_group is not None:
            layouts.append(self._sroc_group.layout())
        align_field_columns(layouts)
        size_plot_text_editor(self)
        adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )

    def _setup_study_order(self):
        self.study_order = QComboBox(self)
        self.study_order.setAccessibleName("Forest study order")
        cumulative = self.plot_type == "cumulative_forest"
        options = analysis_identity.CUMULATIVE_SEQUENCES if cumulative else analysis_identity.LOO_ROW_ORDERS if self.plot_type == "leave_one_out_forest" else analysis_identity.FOREST_STUDY_ORDERS
        for label, key in options:
            self.study_order.addItem(label, key)
        order = self._params.get("cum_sequence" if cumulative else "fp_study_order", "table")
        self.study_order.setCurrentIndex(max(0, self.study_order.findData(self._scalar(order))))
        self.study_order.setEnabled(not cumulative)
        self.study_order.setToolTip("Changing the addition sequence requires rerunning the analysis." if cumulative else "Reorders rows only. Every fit and its estimates stay the same.")
        self.study_order_label = QLabel("Studies added in" if cumulative else "Row order" if self.plot_type == "leave_one_out_forest" else "Study order", self)
        self.study_order_label.setBuddy(self.study_order)
        self.study_order.setAccessibleName(self.study_order_label.text())
        row = self.style_layout.rowCount()
        self.style_layout.addWidget(self.study_order_label, row, 0)
        self.style_layout.addWidget(self.study_order, row, 1)
        self.sequence_rerun = QPushButton("Change sequence and rerun…", self)
        self.sequence_rerun.setVisible(cumulative)
        self.sequence_rerun.setEnabled(False)
        self.sequence_rerun.clicked.connect(self._request_sequence_rerun)
        if cumulative:
            note = QLabel("Changing the addition sequence requires rerunning the analysis.", self)
            note.setWordWrap(True)
            self.style_layout.addWidget(note, row + 1, 0, 1, 2)
            self.style_layout.addWidget(self.sequence_rerun, row + 2, 1)
        self.show_i2 = QCheckBox("Show I² column", self)
        self.show_i2.setChecked(self._bool_param("fp_show_i2", True))
        self.show_i2.setVisible(self.plot_type in {"cumulative_forest", "leave_one_out_forest"})
        self.show_i2.setToolTip("Tables and reports always retain I² from each fitted subset.")
        self.default_layout.addWidget(self.show_i2, self.default_layout.rowCount(), 0, 1, 2)

    def _setup_direction_labels(self):
        self.favours_left = QLineEdit(str(self._params.get("fp_favours_left") or ""), self)
        self.favours_right = QLineEdit(str(self._params.get("fp_favours_right") or ""), self)
        for row, (field, label) in enumerate(((self.favours_left, "Left direction label"), (self.favours_right, "Right direction label")), start=self.default_layout.rowCount()):
            field.setAccessibleName(label)
            field.setPlaceholderText("Optional: Favours …")
            field.setToolTip("Leave empty unless the outcome's clinical direction is known.")
            field.setMaxLength(120)
            caption = QLabel(label, self)
            caption.setBuddy(field)
            self.default_layout.addWidget(caption, row, 0)
            self.default_layout.addWidget(field, row, 1)

    def _request_sequence_rerun(self):
        # Draft appearance goes into the new setup; Cancel leaves this result intact.
        self.reject()
        self.rerun_requested.emit()

    def _setup_axis_scale(self):
        self.axis_scale = QComboBox(self)
        self.axis_scale.setAccessibleName("Effect axis scale")
        self.axis_scale.setToolTip("Change axis spacing only. Fitted effects, confidence intervals and weights stay the same.")
        measure = str(self._scalar(self._params.get("measure", "")))
        proportion = not self._is_reitsma_coefficient and measure in {"PR", "PLN", "PLO", "PAS", "PFT", "Sens", "Spec"}
        ratio = self._is_reitsma_coefficient or measure in {"OR", "RR", "HR", "IRR", "DOR", "PLR", "NLR"}
        self.axis_scale.addItem("Linear, natural units", "natural")
        self.axis_scale.addItem("Logarithmic, natural labels" if ratio else "Fitted transformation", "transformed")
        default_scale = "natural" if proportion else "transformed"
        self.axis_scale.setCurrentIndex(max(0, self.axis_scale.findData(self._scalar(self._params.get("fp_axis_scale", default_scale)))))
        axis_label = QLabel("Effect axis scale", self)
        axis_label.setBuddy(self.axis_scale)
        row = self.style_layout.rowCount()
        self.style_layout.addWidget(axis_label, row, 0)
        self.style_layout.addWidget(self.axis_scale, row, 1)
        axis_label.setVisible((ratio or proportion) and self.plot_type not in {"regression", "sroc", "trial_sequential"})
        self.axis_scale.setVisible(not axis_label.isHidden())

    def _setup_tsa_x_axis(self):
        configure_tsa_x_axis(
            self.tsa_x_axis, self._scalar(self._params.get("tsa_x_axis", "participants")),
            statistical=self._scalar(self._params.get("metric")) == "HR",
        )
        for field in (self.label_12, self.x_lbl_le, self.label_13, self.x_ticks_le,
                      self.label_14, self.plot_lb_le, self.label_15, self.plot_ub_le):
            field.hide()
        label = QLabel("X-axis", self.axis_group)
        label.setBuddy(self.tsa_x_axis)
        row = self.gridLayout_4.rowCount()
        self.gridLayout_4.addWidget(label, row, 0)
        self.gridLayout_4.addWidget(self.tsa_x_axis, row, 1)

    def _configure_accessibility(self):
        """Name static controls and expose an inline commit error region."""
        self._commit_error = QLabel(self)
        self._commit_error.setObjectName("plot_commit_error")
        self._commit_error.setWordWrap(True)
        style_inline_error(self._commit_error)
        self._commit_error.setAccessibleName("Could not update plot")
        self._commit_error.setAccessibleDescription(
            "The change could not be drawn. The previous plot is still shown."
        )
        self._commit_error.hide()
        self.verticalLayout.insertWidget(
            self.verticalLayout.indexOf(self.buttonBox), self._commit_error
        )
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

    def _show_commit_error(self, message: str) -> None:
        self._commit_error.setText(message)
        self._commit_error.show()

    def _commit(self) -> bool:
        axes = [("X-axis", self.plot_lb_le, self.plot_ub_le)]
        if self.plot_type == "sroc":
            axes.append(("Y-axis", self.sroc_y_lower, self.sroc_y_upper))
        for axis, lower, upper in axes:
            values: list[float | None] = []
            for widget, label in ((lower, "lower"), (upper, "upper")):
                text = widget.text().strip()
                if not text or text == "[default]":
                    values.append(None)
                    continue
                try:
                    value = float(text)
                except ValueError:
                    value = math.nan
                if not math.isfinite(value):
                    self._show_commit_error(f"{axis} {label} bound must be a finite number, or leave it blank for automatic limits.")
                    widget.setFocus()
                    return False
                values.append(value)
            low, high = values
            if low is not None and high is not None and low >= high:
                self._show_commit_error(f"{axis} lower bound must be less than the upper bound.")
                lower.setFocus()
                return False
        if not self._validate_ticks():
            return False
        try:
            params = self.plot_params()
            if self._on_commit is not None:
                self._on_commit(params)
        except Exception as error:
            self._show_commit_error(str(error))
            app_error_handler.handle_exception(type(error), error, error.__traceback__, parent=self)
            return False
        self._params.update(params)
        self._commit_error.clear()
        self._commit_error.hide()
        return True

    def _ticks_changed(self):
        if self._validate_ticks(focus=False):
            self._commit_error.clear()
            self._commit_error.hide()

    def _validate_ticks(self, *, focus=True):
        fields = [(self.x_ticks_le, "X")]
        if self.plot_type == "sroc":
            fields.append((self.sroc_y_ticks, "Y"))
        for field, axis in fields:
            ticks = field.text().strip()
            if not ticks or ticks == "[default]":
                continue
            message = self._tick_error(ticks, axis)
            if message:
                self._show_commit_error(message)
                if focus:
                    field.setFocus()
                return False
        return True

    def _tick_error(self, ticks, axis):
        try:
            values = [float(token.strip()) for token in ticks.split(",")]
            valid = all(math.isfinite(value) for value in values)
        except ValueError:
            valid = False
        if not valid:
            return f"{axis}-axis ticks must be comma-separated finite numbers, or leave blank for automatic ticks."
        if self.plot_type == "sroc":
            if any(value < 0 or value > 1 for value in values):
                return f"{axis}-axis SROC ticks must lie between 0 and 1."
            return ""
        measure = str(self._scalar(self._params.get("measure", "")))
        logarithmic = (self.plot_type != "regression" and
                       measure in {"OR", "RR", "HR", "IRR", "DOR", "PLR", "NLR"} and
                       self.axis_scale.currentData() != "natural")
        if logarithmic and any(value <= 0 for value in values):
            return "X-axis ticks must be positive for a logarithmic effect axis."
        return ""

    def accept(self) -> None:
        if self._commit():
            super().accept()


    def _configure_option_groups(self):
        self.study_order.setVisible("forest" in self._option_groups)
        self.study_order_label.setVisible("forest" in self._option_groups)
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
        for field in (self.sroc_curve_color, self.sroc_confidence_color, self.sroc_prediction_color):
            field.setMaximumWidth(field.fontMetrics().height() * 6)
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
        self.sroc_show_auc = QCheckBox("Show normalized partial AUC annotation", self._sroc_group)
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
            (self.sroc_show_auc, "Show normalized partial AUC annotation", "Show or hide the normalized partial area-under-the-curve annotation."),
            (self.sroc_show_curve_legend, "Show SROC curve legend", "Show or hide the curve legend."),
            (self.sroc_show_marker_legend, "Show SROC marker-size legend", "Show or hide the marker-size legend."),
        ):
            control.setAccessibleName(name)
            control.setAccessibleDescription(description)
            control.setToolTip(description)

        def add_field(label_text, control):
            label = QLabel(label_text, self._sroc_group)
            label.setBuddy(control)
            field = self._sroc_color_row(control) if control in (self.sroc_curve_color, self.sroc_confidence_color, self.sroc_prediction_color) else control
            layout.addRow(label, field)

        add_field("Y-axis label", self.sroc_ylabel)
        add_field("Y-axis lower bound", self.sroc_y_lower)
        add_field("Y-axis upper bound", self.sroc_y_upper)
        add_field("Y-axis ticks", self.sroc_y_ticks)
        add_field("Marker area", self.sroc_marker_area)
        layout.addRow('', self.sroc_show_labels)
        layout.addRow('', self.sroc_extrapolate)
        add_field("Curve color", self.sroc_curve_color)
        add_field("Confidence color", self.sroc_confidence_color)
        add_field("Prediction color", self.sroc_prediction_color)
        add_field("Curve line style", self.sroc_curve_lty)
        add_field("Confidence line style", self.sroc_confidence_lty)
        add_field("Prediction line style", self.sroc_prediction_lty)
        add_field("Text size", self.sroc_text_cex)
        layout.addRow('', self.sroc_show_confidence)
        layout.addRow('', self.sroc_show_prediction)
        layout.addRow('', self.sroc_show_summary)
        layout.addRow('', self.sroc_show_auc)
        layout.addRow('', self.sroc_show_curve_legend)
        layout.addRow('', self.sroc_show_marker_legend)
        self.content_layout.addWidget(self._sroc_group)

    def _sroc_color_row(self, edit):
        row = QWidget(self._sroc_group)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edit)
        button = QPushButton('Choose…', row)
        button.setAccessibleName('Choose ' + edit.accessibleName())
        button.clicked.connect(app_error_handler.safe_slot(
            lambda checked=False: self._choose_sroc_color(edit), parent=self))
        layout.addWidget(button)
        add_color_swatch(edit, layout)
        return row

    def _choose_sroc_color(self, edit):
        color = QColorDialog.getColor(QColor(edit.text()), self, edit.accessibleName())
        if color.isValid():
            edit.setText(color.name())

    def _load_params(self, image_path):
        load_plot_style(
            self.style_cbo,
            self.accent_color,
            self._params.get(self._param_name("style")),
            self._params.get(self._param_name("accent_color")),
            accents=self._style_accents,
        )
        self._set_text(
            self.col1_str_edit, self._params.get("fp_col1_str", "Study")
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
        xlabel = self._params.get(self._param_name("xlabel"))
        if self._bool_param(self._param_name("xlabel_literal"), False):
            set_plot_text_value(self.x_lbl_le, self._scalar(xlabel), literal=True)
        else:
            self._set_text(self.x_lbl_le, xlabel)
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
        self._image_path = qt_text.to_native_text(self._scalar(image_path or self._params.get(self._param_name("outpath"), "")))
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
            self._set_text(self.sroc_curve_color, self._params.get("fp_curve_color") or self._params.get("fp_accent_color") or "#2f5597")
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

    def _set_text(self, widget, value):
        value = self._scalar(value)
        automatic = widget in (self.col2_str_edit, self.x_lbl_le, self.plot_lb_le,
                               self.plot_ub_le, self.x_ticks_le)
        if automatic and value in (None, "", "[default]"):
            set_plot_text_value(widget, "")
            widget.setPlaceholderText("Automatic")
            keys = {self.col2_str_edit: "effect", self.x_lbl_le: "xlabel",
                    self.plot_lb_le: "lower", self.plot_ub_le: "upper", self.x_ticks_le: "ticks"}
            resolved = self._params.get("resolved.defaults", {}).get(keys[widget])
            if isinstance(resolved, (list, tuple)):
                resolved = ", ".join(str(item) for item in resolved)
            widget.setToolTip("Automatic: " + str(resolved if resolved is not None else "determined by the plotted data"))
        else:
            set_plot_text_value(widget, value)

    @staticmethod
    def _automatic_value(widget):
        return qt_text.to_native_text(widget.text()) or "[default]"

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

    def _param_name(self, suffix):
        return "%s_%s" % ("bp" if self.plot_type == "regression" else "fp", suffix)

    def plot_params(self):
        style = selected_plot_style(self.style_cbo)
        params = {
            "fp_style": style,
            "fp_axis_scale": self.axis_scale.currentData(),
            "fp_show_i2": self.show_i2.isChecked(),
            "fp_study_order": self.study_order.currentData() if self.plot_type != "cumulative_forest" else "table",
            "fp_favours_left": self.favours_left.text().strip(),
            "fp_favours_right": self.favours_right.text().strip(),
            "fp_show_col1": self.show_1.isChecked(),
            "fp_col1_str": qt_text.to_native_text(plot_text_value(self.col1_str_edit)),
            "fp_show_col2": self.show_2.isChecked(),
            "fp_col2_str": qt_text.to_native_text(plot_text_value(self.col2_str_edit)) or "[default]",
            "fp_show_col3": self.show_3.isChecked(),
            "fp_col3_str": qt_text.to_native_text(plot_text_value(self.col3_str_edit)),
            "fp_show_col4": self.show_4.isChecked(),
            "fp_col4_str": qt_text.to_native_text(plot_text_value(self.col4_str_edit)),
            "fp_show_raw_counts": self.show_raw_counts.isChecked(),
            "fp_show_weight": self.show_weight.isChecked(),
            "fp_show_headers": self.show_headers.isChecked(),
            "fp_show_annotation": self.show_annotation.isChecked(),
            "fp_accent_color": qt_text.to_native_text(self.accent_color.text()),
            "fp_point_size_multiplier": self.point_size_multiplier.value(),
            **plot_axis_label_params(self.x_lbl_le, "fp"),
            "fp_plot_lb": self._automatic_value(self.plot_lb_le),
            "fp_plot_ub": self._automatic_value(self.plot_ub_le),
            "fp_xticks": self._automatic_value(self.x_ticks_le),
            "fp_show_summary_line": self.show_summary_line.isChecked(),
            "fp_outpath": self._image_path,
        }
        forest_display_path = self._scalar(self._params.get("fp_display_path", ""))
        if forest_display_path:
            params["fp_display_path"] = forest_display_path
        if "tsa_axis" in self._option_groups:
            params["tsa_x_axis"] = self.tsa_x_axis.currentData()
            params["funnel.region.color"] = FUNNEL_STYLE_PRESETS[FunnelStyle(style)]["region_color"]
        if self.plot_type == "regression":
            params = {
                "bp_style": style,
                "bp_accent_color": qt_text.to_native_text(self.accent_color.text()),
                "bp_point_size_multiplier": self.point_size_multiplier.value(),
                **plot_axis_label_params(self.x_lbl_le, "bp"),
                "bp_plot_lb": self._automatic_value(self.plot_lb_le),
                "bp_plot_ub": self._automatic_value(self.plot_ub_le),
                "bp_xticks": self._automatic_value(self.x_ticks_le),
                "bp_show_regression_line": self.show_regression_line.isChecked(),
                "bp_show_confidence_band": self.show_confidence_band.isChecked(),
                "bp_show_prediction_interval": self.show_prediction_interval.isChecked(),
                "bp_show_legend": self.show_legend.isChecked(),
                "bp_outpath": self._image_path,
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
                    "fp_sroc_plot_lb": self._automatic_value(self.sroc_y_lower),
                    "fp_sroc_plot_ub": self._automatic_value(self.sroc_y_upper),
                    "fp_sroc_yticks": self._automatic_value(self.sroc_y_ticks),
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
        params["plot_caption"] = self.figure_caption.text().strip()
        return params
