# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Method-selection dialog and analysis specification builder."""

from rc_metastudio.qt_layout import DisclosureButton, configure_context_label, style_inline_error, add_color_swatch, align_field_columns
from PyQt6 import QtCore, QtWidgets, sip
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QResizeEvent, QCloseEvent, QHideEvent, QShowEvent, QPalette
from PyQt6.QtWidgets import (
    QComboBox,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QDoubleSpinBox,
    QSizePolicy,
    QSpinBox,
)

import copy
import math
import re
from uuid import uuid4
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Literal

from rc_metastudio import adaptive_controls, adaptive_window, app_error_handler, qt_text
from rc_metastudio.analysis import (
    catalog as analysis_catalog,
    identity as analysis_identity,
    requests as analysis_adapter,
    progress_dialog,
)
from rc_metastudio.results import plot_capabilities
from rc_metastudio.project.model import PooledAnalysis
from rc_metastudio.results.contract import AnalysisResult, normalize_analysis_result
from rc_metastudio.analysis.method_labels import (
    diagnostic_metric_group_display_label,
    parameter_description,
    parameter_display_label,
    parameter_value_display_label,
)
from rc_metastudio.results.plot_defaults import apply_default_forest_arm_labels
from rc_metastudio.results.plot_style_controls import (
    configure_plot_style, load_plot_style, selected_plot_style,
)
from rc_metastudio.analysis.study_selection import fit_raw_rows, raw_data_is_complete
from rc_metastudio.results.plot_text import (
    configure_plot_text_inputs,
    plot_axis_label_params,
    plot_text_value,
    set_plot_text_value,
)
from rc_metastudio.analysis.catalog import (
    ALL_METRIC_NAMES, CONTINUOUS, DIAGNOSTIC_METRIC_GROUPS, ONE_ARM_METRICS,
    RATIO_DATA_TYPES, RAW_COUNT_METHODS, REITSMA_METHOD,
    TWO_ARM_METRICS,
)
from rc_metastudio.analysis.validation import ANALYSIS_DIGITS_MAX, ANALYSIS_DIGITS_MIN, ANALYSIS_NON_NEGATIVE_FLOAT_PARAMS, ANALYSIS_NUMERIC_MAX, ANALYSIS_NUMERIC_MIN, CONFIDENCE_LEVEL_DISPLAY_MAX, parse_plot_bound, is_valid_plot_tick_list, validate_analysis_digits, validate_analysis_float, validate_confidence_level, validate_correction_factor
from rc_metastudio.settings import analysis_output_path
from rc_metastudio.qt_object_guard import required

if TYPE_CHECKING:
    from rc_metastudio.domain_ids import RowId
    from rc_metastudio.project.model import Sheet, StudyRow
    from rc_metastudio.workspace.columns import RawColumn
    from rc_metastudio.results.report import AnalysisResultHandler
    from ui_analysis_setup_dialog import Ui_AnalysisSetupDialog
else:
    from rc_metastudio.forms.ui_analysis_setup_dialog import Ui_AnalysisSetupDialog

SHARED_DIAGNOSTIC_PARAMS = (
    "conf.level",
    "digits",
    "adjust",
    "correction.policy",
)

ParameterKind = Literal["enum", "float", "int", "string"]


@dataclass(frozen=True)
class _ParameterDefinition:
    name: str
    kind: ParameterKind
    default: object
    metadata: object
    values: tuple[object, ...] = ()


def _normalize_parameter_definition(
    name: str, definition: object, default: object, metadata: object
) -> _ParameterDefinition:
    if isinstance(definition, list):
        return _ParameterDefinition(name, "enum", default, metadata, tuple(definition))
    if _is_integer_analysis_param(name) or str(definition).lower() == "int":
        kind: ParameterKind = "int"
    elif str(definition).lower() == "string":
        kind = "string"
    else:
        kind = "float"
    return _ParameterDefinition(name, kind, default, metadata)


def _shared_diagnostic_specs(confidence_level):
    return {
        "conf.level": _normalize_parameter_definition(
            "conf.level", "float", confidence_level, None
        ),
        "digits": _normalize_parameter_definition("digits", "int", 2, None),
        "adjust": _normalize_parameter_definition("adjust", "float", 0.5, None),
        "correction.policy": _normalize_parameter_definition(
            "correction.policy",
            ["Studies with any zero cell", "All studies if any zero exists", "None"],
            "All studies if any zero exists",
            None,
        ),
    }


def _present_values(names, source):
    return {name: source[name] for name in names if name in source}


def _plot_parameter_values(values):
    return {
        name: value for name, value in values.items() if name.startswith(("fp_", "bp_"))
    }


class _DiagnosticMethodPanel(object):
    """A group-specific method editor used by the unified diagnostic dialog."""

    def __init__(self, owner, label, label_widget, combo, param_box):
        self.owner = owner
        self.params = {}
        self.widgets = []
        self.definitions = {}
        self.label = label_widget
        self.label.setText(label + " method")
        self.combo = combo
        owner._configure_method_selector(self.combo)
        self.layout = QGridLayout(param_box)
        param_box.setTitle("")
        param_box.setFlat(True)
        self.combo.currentIndexChanged.connect(
            app_error_handler.safe_slot(
                lambda _text: self._method_changed(), parent=owner
            )
        )

    @property
    def method(self):
        return required(self.combo.currentData(), "diagnostic method")

    def populate(self):
        metrics = [metric for group in self.owner.diagnostic_metrics if group in ('lr', 'dor')
                   for metric in DIAGNOSTIC_METRIC_GROUPS[group]]
        methods = self.owner._methods_for_metrics(metrics)
        methods.pop(REITSMA_METHOD, None)
        self.owner._populate_method_combo(
            self.combo, sorted(methods.items(), key=lambda item: item[1], reverse=True)
        )
        self._method_changed()

    def _method_changed(self, saved=None):
        definitions, defaults, order, metadata = self.owner.analysis_service.parameters(
            self.method
        )
        self.definitions = definitions
        if saved is not None:
            defaults.update(saved)
        specs = [
            _normalize_parameter_definition(name, definitions[name], defaults.get(name), metadata.get(name))
            for name in order or definitions
        ]
        self.owner._remove_parameter_widgets(self.widgets)
        self.params = {}
        self.widgets = self.owner._render_parameters(
            self.layout, self.owner._local_diagnostic_parameters(specs), self.params, defaults
        )
        self.owner._rebuild_shared_diagnostic_params()
        self.owner._set_analysis_tab_order()
        self.owner._schedule_local_reflow()


class _CompactDoubleSpinBox(QDoubleSpinBox):
    def textFromValue(self, v: float) -> str:
        return super().textFromValue(v).rstrip("0").rstrip(self.locale().decimalPoint())


class AnalysisSetupDialog(QDialog, Ui_AnalysisSetupDialog):
    def __init__(
        self,
        model,
        parent=None,
        analysis_type=None,
        external_params=None,
        diagnostic_metrics=None,
        diagnostic_analysis_details=None,
        confidence_level=None,
        analysis_service=None,
        initial_settings=None,
        *,
        on_result: "AnalysisResultHandler | None" = None,
        source_sheet: "Sheet | None" = None,
        replaces: QtWidgets.QWidget | None = None,
    ):

        super(AnalysisSetupDialog, self).__init__(parent)
        self.analysis_service = analysis_service or analysis_adapter.AnalysisService()
        self._on_result = on_result
        self._replaces = replaces
        self._rerun_source_sheet = source_sheet
        self.setupUi(self)
        self.outcome_label = QLabel(model.current_outcome_name, self)
        self.outcome_label.setTextFormat(Qt.TextFormat.PlainText)
        configure_context_label(self.outcome_label)
        self.content_scroll_layout.insertWidget(0, self.outcome_label)
        self._initialize_controls(external_params, analysis_type)
        self._initialize_analysis_state(
            model,
            confidence_level,
            diagnostic_metrics,
            diagnostic_analysis_details,
        )
        self._setup_advanced_parameters()
        self._connect_dialog_actions()
        self._configure_data_family()
        self.populate_parameter_controls()
        if self._combined_diagnostic:
            self._finish_combined_diagnostic_ui()
        self.content_scroll_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._setup_result_context()
        if self.data_type != "diagnostic" and not self.is_meta_regression:
            self.specs_tab.setTabText(self.specs_tab.indexOf(self.plot_tab), "Forest plot")
        self.specs_tab.currentChanged.connect(self._fit_active_tab_contents)
        self._fit_active_tab_contents(self.specs_tab.currentIndex())
        adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
        for field in self.findChildren(QLineEdit):
            if field.text() == "[default]":
                set_plot_text_value(field, "[default]")
                if field is self.col2_str_edit:
                    field.setToolTip("Automatic: " + self._result_metric_label())
                elif field is self.col3_str_edit and self.data_type == "diagnostic":
                    field.setToolTip("Automatic: diagnostic counts")
        if initial_settings is None and analysis_type is None and model.current_sheet:
            initial_settings = model.current_sheet.settings.get('analysis')
        if initial_settings is not None:
            self._restore_settings(initial_settings)

    def _setup_result_context(self):
        workflow = {"cumulative": "Cumulative meta-analysis", "leave-one-out": "Leave-one-out analysis", "subgroup": "Subgroup analysis", "meta-regression": "Meta-regression"}.get(self.analysis_type, "")
        prefix = f"{workflow} · " if workflow else ""
        self.setWindowTitle(f"{prefix}{self.model.current_outcome_name} · {self._result_metric_label()}")
        run_button = required(self.buttonBox.button(QDialogButtonBox.StandardButton.Ok), "Run analysis button")
        run_button.setText("Run analysis")
        run_button.setStyleSheet("QPushButton:focus { border: 2px solid palette(highlight); }")
        self.analysis_error_label = QLabel(self)
        self.analysis_error_label.setWordWrap(True)
        style_inline_error(self.analysis_error_label)
        self.analysis_error_label.setTextFormat(Qt.TextFormat.PlainText)
        self.analysis_error_label.setAccessibleName("Analysis error")
        self.analysis_error_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.analysis_error_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.analysis_error_label.hide()
        self.analysis_error_panel = QtWidgets.QWidget(self)
        error_layout = QtWidgets.QVBoxLayout(self.analysis_error_panel)
        error_layout.setContentsMargins(0, 0, 0, 0)
        error_layout.addWidget(self.analysis_error_label)
        self.analysis_error_toggle = DisclosureButton("Details", self.analysis_error_panel)
        error_layout.addWidget(self.analysis_error_toggle, 0, Qt.AlignmentFlag.AlignLeft)
        self.analysis_error_details = QtWidgets.QPlainTextEdit(self.analysis_error_panel)
        self.analysis_error_details.setReadOnly(True)
        self.analysis_error_details.setFixedHeight(
            self.analysis_error_details.fontMetrics().lineSpacing() * 8
            + 2 * self.analysis_error_details.frameWidth() + 8
        )
        self.analysis_error_details.setAccessibleName("Technical analysis error details")
        self.analysis_error_details.hide()
        error_layout.addWidget(self.analysis_error_details)
        self.analysis_error_toggle.toggled.connect(self._expand_error_details)
        self.analysis_error_panel.hide()
        self.content_scroll_layout.insertWidget(0, self.analysis_error_panel)
        if (
            not self.is_meta_regression
            and self.model.current_effect == "Mean"
            and analysis_catalog.canonical_metric_name(self.x_lbl_le.text()) in {"", "[default]", "Mean"}
        ):
            self.x_lbl_le.setText(analysis_identity.metric_label(self.model))
        if self.analysis_type in {"cumulative", "leave-one-out"}:
            self.col1_str_edit.setText("Study added" if self.analysis_type == "cumulative" else "Study omitted")
        elif self.analysis_type == "subgroup":
            self.col1_str_edit.setText("Subgroup")
        else:
            self.col1_str_edit.setText("Study")
        if self.data_type in {"binary", "continuous", "time_to_event", "event_rates"}:
            for field, name in zip((self.col3_str_edit, self.col4_str_edit), self.model.arm_names):
                set_plot_text_value(field, name)
        for checkbox, label in zip((self.show_1, self.show_2, self.show_3, self.show_4), ("study", "estimate", "first arm", "second arm")):
            checkbox.setAccessibleName(f"Show {label} column")

    def _restore_settings(self, saved):
        parameters = dict(saved["parameters"])
        self.current_param_vals.update(parameters)
        index = self.method_cbo_box.findData(saved["method"])
        if index < 0:
            raise ValueError("The result's analysis method is unavailable for its original dataset.")
        with QtCore.QSignalBlocker(self.method_cbo_box):
            self.method_cbo_box.setCurrentIndex(index)
        self.method_changed()
        if self._combined_diagnostic:
            method, values = saved["lr_dor"]
            index = self.lr_dor_panel.combo.findData(method)
            if index < 0:
                raise ValueError("The result's diagnostic method is unavailable for its original dataset.")
            with QtCore.QSignalBlocker(self.lr_dor_panel.combo):
                self.lr_dor_panel.combo.setCurrentIndex(index)
            self.lr_dor_panel._method_changed(values)
        if self.is_meta_regression:
            for covariate, checkbox in self.covs_and_check_boxes:
                checkbox.setChecked(covariate['name'] in saved["covariates"])
            self.fixed_effects_radio.setChecked(saved["fixed_effects"])
            self.random_effects_radio.setChecked(not saved["fixed_effects"])
        self._restore_plot_settings(parameters)

    def _restore_plot_settings(self, parameters):
        self._load_plot_params()
        self.study_order.setCurrentIndex(max(0, self.study_order.findData(parameters.get("cum_sequence" if self.analysis_type == "cumulative" else "fp_study_order", "table"))))
        prefix = "bp" if self.is_meta_regression else "fp"
        for field, name in ((self.col1_str_edit, "fp_col1_str"), (self.col2_str_edit, "fp_col2_str"),
                            (self.col3_str_edit, "fp_col3_str"), (self.col4_str_edit, "fp_col4_str"),
                            (self.x_lbl_le, "bp_xlabel" if self.is_meta_regression else "fp_xlabel"),
                            (self.plot_lb_le, f"{prefix}_plot_lb"), (self.plot_ub_le, f"{prefix}_plot_ub"), (self.x_ticks_le, f"{prefix}_xticks")):
            if parameters.get(name) is not None:
                if field in (self.col1_str_edit, self.col2_str_edit, self.col3_str_edit, self.col4_str_edit, self.x_lbl_le):
                    set_plot_text_value(
                        field, parameters[name],
                        literal=field is self.x_lbl_le and _bool_plot_param(parameters.get(f"{prefix}_xlabel_literal"), False),
                    )
                else:
                    field.setText(str(parameters[name]))
        self.show_i2.setChecked(_bool_plot_param(parameters.get("fp_show_i2"), True))
        for checkbox, name in ((self.show_1, "fp_show_col1"), (self.show_2, "fp_show_col2"),
                               (self.show_3, "fp_show_col3"), (self.show_4, "fp_show_col4"),
                               (self.show_summary_line, "fp_show_summary_line")):
            if name in parameters:
                checkbox.setChecked(_bool_plot_param(parameters[name], True))

    def _change_settings_callback(self, source_sheet: "Sheet | None"):
        from rc_metastudio.workspace.table_model import DatasetTableModel
        model = DatasetTableModel(dataset=copy.deepcopy(self.model.dataset), add_blank_study=False)
        model.set_current_sheet(self.model.current_sheet_id)
        saved_parameters = copy.deepcopy(self.current_param_vals)
        saved = dict(method=self.current_method, parameters=saved_parameters,
                     covariates=[cov['name'] for cov in self._selected_covariates()] if self.is_meta_regression else [],
                     fixed_effects=self.fixed_effects_radio.isChecked())
        if self._combined_diagnostic:
            saved["lr_dor"] = (self.lr_dor_panel.method, copy.deepcopy(self.lr_dor_panel.params))
        parent, service = self.parentWidget(), self.analysis_service
        on_result = self._on_result
        workflow, metrics = self.analysis_type, self.diagnostic_metrics
        details = copy.deepcopy(self.diagnostic_analysis_details)
        confidence = self.current_param_vals.get("conf.level", self.confidence_level)

        def reopen(plot_params: dict[str, object], origin: QtWidgets.QWidget):
            restored = copy.deepcopy(saved)
            parameters = copy.deepcopy(saved_parameters)
            if plot_params:
                parameters.update({key: value for key, value in plot_params.items()
                                   if key.startswith("fp_") and key not in {"fp_outpath", "fp_display_path"}})
            restored["parameters"] = parameters
            form = AnalysisSetupDialog(model, parent=parent, analysis_type=workflow,
                external_params=restored["parameters"], diagnostic_metrics=metrics,
                diagnostic_analysis_details=copy.deepcopy(details), confidence_level=confidence,
                analysis_service=service, initial_settings=restored, on_result=on_result,
                source_sheet=source_sheet, replaces=origin)
            form.show()

        return reopen

    def _initialize_controls(self, external_params, analysis_type):
        # Method controls must fit inside the adaptive viewport. An
        # outer horizontal scrollbar would hide the estimator control on
        # narrow first-use dialog sizes.
        self.content_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        # Preserve natural row heights, but let wrapping forms negotiate their
        # width down to the viewport instead of exporting unwrapped text widths.
        for widget in (self.content_scroll_area_widget, self.specs_tab,
                       self.methods_tab, self.parameter_grp_box):
            # layout-audit: allow=content-overflow-control; reason=scroll content retains vertical minima while fitting the viewport width
            widget.setMinimumWidth(0)
        self.parameter_grp_box.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            self.parameter_grp_box.sizePolicy().verticalPolicy(),
        )
        self.content_scroll_layout.setSizeConstraint(
            QtWidgets.QLayout.SizeConstraint.SetDefaultConstraint
        )
        self.method_lbl.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )
        self.gridLayout.removeWidget(self.method_lbl)
        self.gridLayout.removeWidget(self.method_cbo_box)
        self._method_row = QtWidgets.QWidget(self.methods_tab)
        self._method_layout = QtWidgets.QGridLayout(self._method_row)
        self._method_layout.setContentsMargins(0, 0, 0, 0)
        self._method_layout.setColumnStretch(1, 1)
        self._method_layout.addWidget(self.method_lbl, 0, 0)
        self._method_layout.addWidget(self.method_cbo_box, 0, 1)
        self.gridLayout.addWidget(self._method_row, 0, 0, 1, 2)
        self.gridLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.gridLayout.setColumnStretch(0, 0)
        self.gridLayout.setColumnStretch(1, 1)
        self._layout_reflow_pending = False
        self._resize_on_reflow = False
        self._layout_reflow_timer = QtCore.QTimer(self)
        self._layout_reflow_timer.setSingleShot(True)
        self._layout_reflow_timer.timeout.connect(self._apply_local_reflow)
        self._focus_reveal_connected = False
        for combo in self.findChildren(QComboBox):
            self._configure_value_control(combo)
        configure_plot_text_inputs(self)
        self.accent_color.setMaximumWidth(self.fontMetrics().height() * 6)
        self.color_btn.setText("Choose…")
        self.color_btn.setMaximumWidth(self.fontMetrics().height() * 12)
        apply_default_forest_arm_labels(self)
        self.current_param_vals: dict[str, object] = dict(external_params or {})
        self.analysis_type = analysis_type
        self.is_meta_regression = analysis_type == "meta-regression"
        plot_kind = "reg" if self.is_meta_regression else "forest"
        self._fit_output_stem = analysis_output_path(f"{uuid4().hex}-{plot_kind}")
        self._setup_plot_controls()
        self._load_plot_params()

    def _initialize_analysis_state(
        self, model, confidence_level, diagnostic_metrics, diagnostic_analysis_details
    ):
        self.model = model
        if confidence_level is None:
            raise ValueError("Specify a confidence level before running the analysis.")
        self.confidence_level = validate_confidence_level(confidence_level)
        self.data_type = self.model.get_current_data_type()
        self.current_widgets = []
        self.current_method = ""
        self.current_params: dict[str, object] = {}
        self.current_defaults: dict[str, object] = {}
        self.param_d: dict[str, object] = {}
        self.var_order: list[str] | None = None
        self.diagnostic_analysis_details: dict[str, tuple[str, dict[str, object]] | None] = diagnostic_analysis_details or {}
        self.diagnostic_metrics = tuple(diagnostic_metrics or ())
        self._combined_diagnostic = False
        self._shared_diagnostic_param_specs = _shared_diagnostic_specs(
            self.confidence_level
        )
        self._shared_diagnostic_widgets = []
        self._shared_diagnostic_layout: QGridLayout | None = None

    def _connect_dialog_actions(self):
        self._accepted_connection = None
        self._set_accepted_handler(
            self.run_meta_regression if self.is_meta_regression else self.run_ma
        )
        self.buttonBox.rejected.connect(
            app_error_handler.safe_slot(self.cancel, parent=self)
        )
        self._configure_method_selector(self.method_cbo_box)
        self.method_cbo_box.currentIndexChanged.connect(
            app_error_handler.safe_slot(
                lambda _text: self.method_changed(), parent=self
            )
        )

    def _configure_data_family(self):
        self._setup_covariates_tab()
        if self.data_type not in {"binary", "continuous"}:
            self.disable_bin_only_fields()
            if self.data_type == "diagnostic":
                self.enable_diagnostic_fields()

        if self.model.current_effect in ONE_ARM_METRICS:
            self.setup_fields_for_one_arm()

        if self.data_type == "diagnostic":
            self.sens_spec = any(
                metric in ("sens", "spec") for metric in self.diagnostic_metrics
            )
            self.lr_dor = any(
                metric in ("lr", "dor") for metric in self.diagnostic_metrics
            )
            self._combined_diagnostic = self.sens_spec and self.lr_dor
            self.setup_diagnostic_ui()

    def sizeHint(self):
        """Include the scroll body's content width in first-use negotiation."""
        hint = super(AnalysisSetupDialog, self).sizeHint()
        if not hasattr(self, "specs_tab"):
            return hint
        content_hint = self.specs_tab.minimumSizeHint()
        root_layout = self.layout()
        scrollbar = self.content_scroll_area.verticalScrollBar()
        if not content_hint.isValid() or root_layout is None or scrollbar is None:
            return hint
        margins = root_layout.contentsMargins()
        horizontal_margins = margins.left() + margins.right()
        width = max(content_hint.width(), self._method_width_hint())
        hint.setWidth(max(hint.width(), width + horizontal_margins + scrollbar.sizeHint().width(),
                          self._parameter_width_hint() + horizontal_margins + 80))
        hint.setHeight(
            self.content_scroll_area.minimumHeight() + self.buttonBox.sizeHint().height()
            + margins.top() + margins.bottom() + root_layout.spacing()
        )
        return hint

    def _method_width_hint(self):
        if not hasattr(self, "method_cbo_box"):
            return 0
        width = self.method_cbo_box.sizeHint().width()
        if hasattr(self, "method_lbl"):
            width += self.method_lbl.sizeHint().width()
        if hasattr(self, "gridLayout"):
            width += self.gridLayout.horizontalSpacing()
        # The selector lives inside a tab page and its layout, not directly
        # inside the scroll viewport. Include those in first-use sizing.
        margins = self.horizontalLayout.contentsMargins()
        width += margins.left() + margins.right()
        width += self.specs_tab.sizeHint().width() - self.methods_tab.sizeHint().width()
        return width

    def _parameter_width_hint(self):
        if self.parameter_grp_box.layout() is None:
            return -80
        label_width = max((label.sizeHint().width() for label in self.parameter_grp_box.findChildren(QLabel)
                           if label.buddy() is not None), default=0)
        value_width = max((combo.sizeHint().width() for combo in self.parameter_grp_box.findChildren(QComboBox)), default=0)
        return label_width + value_width

    def _set_scroll_body_height(self, content_height):
        layout = self.layout()
        assert layout is not None
        frame_height = max(0, self.frameGeometry().height() - self.height())
        policy = adaptive_window.WINDOW_POLICIES[adaptive_window.WindowRole.TRANSACTIONAL]
        available = int(adaptive_window.available_geometry_for_window(self).height() * policy.maximum_screen_fraction)
        self.content_scroll_area.setMinimumHeight(0)
        layout.invalidate()
        overhead = layout.minimumSize().height() - self.content_scroll_area.minimumSizeHint().height()
        body_height = available - frame_height - overhead
        self.content_scroll_area.setMinimumHeight(max(0, min(content_height + 2, body_height)))
        layout.activate()

    def _active_content_height(self):
        # QTabWidget's hint includes hidden pages, even when their size policy
        # is Ignored. Measure the selected layout instead of the entire stack.
        page = required(self.specs_tab.currentWidget(), "active analysis tab")
        layout = required(page.layout(), "active analysis layout")
        height = (layout.totalHeightForWidth(page.width()) if layout.hasHeightForWidth()
                  else layout.totalSizeHint().height())
        height += required(self.specs_tab.tabBar(), "analysis tabs").sizeHint().height()
        height += 2 * required(self.specs_tab.style(), "analysis tab style").pixelMetric(QtWidgets.QStyle.PixelMetric.PM_DefaultFrameWidth)
        height += self.outcome_label.heightForWidth(self.specs_tab.width()) + self.content_scroll_layout.spacing()
        if hasattr(self, "analysis_error_panel") and not self.analysis_error_panel.isHidden():
            height += self.analysis_error_panel.sizeHint().height() + self.content_scroll_layout.spacing()
        return height

    def _fit_active_tab_contents(self, current):
        for index in range(self.specs_tab.count()):
            page = self.specs_tab.widget(index)
            if page is not None:
                policy = QSizePolicy.Policy.Preferred if index == current else QSizePolicy.Policy.Ignored
                page.setSizePolicy(policy, policy)
        self.specs_tab.updateGeometry()
        active_page = self.specs_tab.currentWidget()
        assert active_page is not None
        self._set_scroll_body_height(self._active_content_height())
        position = self.pos()
        self.adjustSize()
        self.move(position)

    def showEvent(
        self, event: QShowEvent | None
    ) -> None:
        super(AnalysisSetupDialog, self).showEvent(event)
        policy = adaptive_window.WINDOW_POLICIES[adaptive_window.WindowRole.TRANSACTIONAL]
        available = adaptive_window.available_geometry_for_window(self)
        frame_width = max(0, self.frameGeometry().width() - self.width())
        width = min(self.sizeHint().width(),
                    int(available.width() * policy.maximum_screen_fraction) - frame_width)
        self.resize(max(self.width(), width), self.height())
        self._resize_on_reflow = True
        self._schedule_local_reflow()
        app = QtWidgets.QApplication.instance()
        if isinstance(app, QtWidgets.QApplication) and not self._focus_reveal_connected:
            app.focusChanged.connect(self._reveal_focused_control)
            self._focus_reveal_connected = True

    def hideEvent(
        self, event: QHideEvent | None
    ) -> None:
        self._disconnect_focus_reveal()
        super(AnalysisSetupDialog, self).hideEvent(event)

    def closeEvent(
        self, event: QCloseEvent | None
    ) -> None:
        self._release_owned_connections()
        super(AnalysisSetupDialog, self).closeEvent(event)
        self.deleteLater()

    def _disconnect_focus_reveal(self):
        if not self._focus_reveal_connected:
            return
        app = QtWidgets.QApplication.instance()
        if isinstance(app, QtWidgets.QApplication):
            try:
                app.focusChanged.disconnect(self._reveal_focused_control)
            except (TypeError, RuntimeError):
                pass
        self._focus_reveal_connected = False

    def cancel(self):
        self.reject()

    def _setup_covariates_tab(self):
        if not self.is_meta_regression:
            self.specs_tab.removeTab(self.specs_tab.indexOf(self.covariates_tab))
            self.regression_group.hide()
            return

        self.covs_and_check_boxes = []
        for row, covariate in enumerate(self.model.current_sheet.covariates):
            checkbox = QtWidgets.QCheckBox(covariate['name'], self.covariate_group_box)
            checkbox.setChecked(row == 0)
            checkbox.toggled.connect(
                app_error_handler.safe_slot(
                    self._update_meta_regression_ok, parent=self
                )
            )
            checkbox.toggled.connect(
                app_error_handler.safe_slot(
                    self._update_meta_regression_plot_availability, parent=self
                )
            )
            self.covariates_layout.addWidget(checkbox, row, 0)
            self.covs_and_check_boxes.append((covariate, checkbox))
        self.moderator_values_note = QLabel(self.covariate_group_box)
        self.moderator_values_note.setWordWrap(True)
        self.covariates_layout.addWidget(self.moderator_values_note, len(self.covs_and_check_boxes), 0)
        self._update_meta_regression_ok()
        self._update_meta_regression_plot_availability()

    def _selected_covariates(self):
        return [
            covariate
            for covariate, checkbox in self.covs_and_check_boxes
            if checkbox.isChecked()
        ]

    def _update_meta_regression_ok(self):
        selected = self._selected_covariates()
        button = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if button is not None:
            button.setEnabled(bool(selected))
        selection = analysis_adapter.select_studies_for_covariates(self.model, selected)
        self.moderator_values_note.setText(
            "Missing moderator values: " + ", ".join(selection.excluded_study_names)
            if selection.has_missing_values else "" if selected else "Select at least one covariate."
        )

    def _update_meta_regression_plot_availability(self):
        if not self.is_meta_regression:
            return
        selected = self._selected_covariates()
        bubble_available = len(selected) == 1 and selected[0]['data_type'] == CONTINUOUS
        self.plot_tab.setEnabled(bubble_available)
        self.plot_tab.setToolTip(
            ""
            if bubble_available
            else "Bubble plot options require exactly one numeric covariate."
        )

    def _set_accepted_handler(self, handler):
        if self._accepted_connection is None:
            self._accepted_connection = app_error_handler.connect_safely(
                self.buttonBox.accepted, handler, parent=self
            )
        else:
            self._accepted_connection.replace(handler, parent=self)

    def _setup_plot_controls(self):
        if self.analysis_type == "subgroup":
            note = QLabel("Subgroup figures use the default layout. RevMan and BMJ apply their accent colors; their standard-forest layouts are unavailable for subgroups.", self)
            note.setWordWrap(True)
            self.style_layout.addWidget(note, self.style_layout.rowCount(), 0, 1, 2)
        self.study_order = QComboBox(self)
        self.study_order.setAccessibleName("Forest study order")
        cumulative = self.analysis_type == "cumulative"
        options = analysis_identity.CUMULATIVE_SEQUENCES if cumulative else analysis_identity.LOO_ROW_ORDERS if self.analysis_type == "leave-one-out" else analysis_identity.FOREST_STUDY_ORDERS
        for label, key in options:
            self.study_order.addItem(label, key)
        key = "cum_sequence" if cumulative else "fp_study_order"
        self.study_order.setCurrentIndex(max(0, self.study_order.findData(self.current_param_vals.get(key, "table"))))
        self.study_order.setToolTip("Sets which studies each cumulative fit includes. A different sequence gives different intermediate results." if cumulative else "Reorders rows only. Every fit and its estimates stay the same.")
        self.study_order_label = QLabel("Add studies in" if cumulative else "Row order" if self.analysis_type == "leave-one-out" else "Study order", self)
        self.study_order_label.setBuddy(self.study_order)
        self.study_order.setAccessibleName(self.study_order_label.text())
        layout = self.style_layout
        if cumulative:
            self._sequence_row = QtWidgets.QWidget(self)
            self._sequence_layout = QGridLayout(self._sequence_row)
            layout = self._sequence_layout
            self.gridLayout.addWidget(self._sequence_row, self.gridLayout.rowCount(), 0, 1, 4)
        row = layout.rowCount()
        layout.addWidget(self.study_order_label, row, 0)
        layout.addWidget(self.study_order, row, 1)
        if cumulative:
            note = QLabel(self.study_order.toolTip(), self)
            note.setWordWrap(True)
            note.setForegroundRole(QPalette.ColorRole.PlaceholderText)
            layout.addWidget(note, row + 1, 1)
        self.show_i2 = QCheckBox("Show I² column", self)
        self.show_i2.setChecked(_bool_plot_param(self.current_param_vals.get("fp_show_i2"), True))
        self.show_i2.setToolTip("Show heterogeneity from each fitted subset. Tables and reports always retain I².")
        self.default_layout.addWidget(self.show_i2, self.default_layout.rowCount(), 0, 1, 2)
        self.show_i2.setVisible(self.analysis_type in {"cumulative", "leave-one-out"})
        add_color_swatch(self.accent_color, self.accent_color_layout)
        configure_plot_style(self.style_cbo, self.accent_color, self.color_btn)

        align_field_columns((self.style_layout, self.appearance_layout, self.gridLayout_2, self.default_layout, self.gridLayout_3, self.regression_layout))

    def _configure_plot_option_groups(self):
        workflow = self.analysis_type or "standard"
        capabilities = self.analysis_service.plot_capabilities(
            self.data_type, self.current_method, workflow=workflow
        )
        plot_kinds = [str(capability["plot_kind"]) for capability in capabilities]
        groups = frozenset().union(
            *(plot_capabilities.option_groups(plot_kind) for plot_kind in plot_kinds)
        )
        self.style_group.setVisible("style" in groups)
        self.appearance_group.setVisible("appearance" in groups)
        self.groupBox.setVisible("columns" in groups)
        self.default_panel.setVisible("forest" in groups)
        self.regression_group.setVisible("regression" in groups)
        self.label_11.setVisible("summary" in groups)
        self.show_summary_line.setVisible("summary" in groups)
        self.study_order.setVisible(self.analysis_type == "cumulative" or "forest" in groups)
        self.study_order_label.setVisible(self.analysis_type == "cumulative" or "forest" in groups)
        self.plot_tab.setEnabled(
            any(capability["styleable"] for capability in capabilities)
        )
        self._update_meta_regression_plot_availability()

    def run_meta_regression(self):
        selected_covariates = self._selected_covariates()
        if not selected_covariates:
            QMessageBox.warning(
                self,
                "No covariates selected",
                "Select at least one covariate before running meta-regression.",
            )
            return

        selection = analysis_adapter.select_studies_for_covariates(
            self.model, selected_covariates
        )
        if selection.has_missing_values and not self._confirm_excluded_studies(
            selection.excluded_study_names
        ):
            return
        self._executed_studies = selection.studies
        request = self._meta_regression_request()
        fixed_effects = self.fixed_effects_radio.isChecked()
        def execute_regression() -> AnalysisResult:
            result = analysis_adapter.execute_meta_regression_request(
                self.model,
                selection.studies,
                tuple(selected_covariates),
                request,
                fixed_effects,
                self.confidence_level,
            )
            return self._prepare_analysis_result(result)

        self._run_analysis(execute_regression, regression_request=request)

    def _confirm_excluded_studies(self, names):
        excluded = ", ".join(names)
        excluded_text = ""
        if excluded:
            excluded_text = f"\nThe following studies will be excluded: {excluded}"
        choice = QMessageBox.warning(
            self,
            "Missing covariate values",
            "Some studies do not have values for the selected covariates. "
            f"{excluded_text}\nRun the regression without those studies?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return choice != QMessageBox.StandardButton.No

    def _meta_regression_metric(self):
        return "Sens" if self.data_type == "diagnostic" else self.model.current_effect

    def _meta_regression_request(self):
        metric = self._meta_regression_metric()
        add_plot_params(self)
        parameters = copy.deepcopy(self.current_param_vals)
        parameters.pop("measure", None)
        parameters["metric.label"] = self._result_metric_label()
        method = "meta.regression"
        if self.data_type == "diagnostic":
            method = REITSMA_METHOD
            parameters["fp_outpath"] = f"{self._fit_output_stem}.svg"
            parameters["fp_display_path"] = parameters["fp_outpath"]
            parameters["joint.metrics"] = "Sens,Spec"
        return analysis_adapter.make_analysis_request(
            data_type=self.data_type,
            workflow="meta-regression",
            method=method,
            metric=metric,
            parameters=parameters,
        )

    def _load_plot_params(self):
        prefix = "bp" if self.is_meta_regression else "fp"
        load_plot_style(
            self.style_cbo,
            self.accent_color,
            self.current_param_vals.get(f"{prefix}_style"),
            self.current_param_vals.get(f"{prefix}_accent_color"),
        )
        self.point_size_multiplier.setValue(
            _float_plot_param(
                self.current_param_vals.get("%s_point_size_multiplier" % prefix),
                1.0,
            )
        )
        if self.is_meta_regression:
            self.show_regression_line.setChecked(
                _bool_plot_param(
                    self.current_param_vals.get("bp_show_regression_line"), True
                )
            )
            self.show_confidence_band.setChecked(
                _bool_plot_param(
                    self.current_param_vals.get("bp_show_confidence_band"), True
                )
            )
            self.show_prediction_interval.setChecked(
                _bool_plot_param(
                    self.current_param_vals.get("bp_show_prediction_interval"),
                    False,
                )
            )
            self.show_legend.setChecked(
                _bool_plot_param(
                    self.current_param_vals.get("bp_show_legend"), True
                )
            )
        self.show_raw_counts.setChecked(
            _bool_plot_param(
                self.current_param_vals.get("fp_show_raw_counts"), True
            )
        )
        self.show_headers.setChecked(
            _bool_plot_param(self.current_param_vals.get("fp_show_headers"), True)
        )
        self.show_annotation.setChecked(
            _bool_plot_param(
                self.current_param_vals.get("fp_show_annotation"), True
            )
        )

    def run_ma(self):
        self._run_analysis()

    def execute_configured_analysis(self) -> AnalysisResult:
        """Execute the current settings and prepare the result for presentation."""
        return self._execute_requests(self.analysis_requests())

    def _execute_requests(self, requests: Sequence[analysis_adapter.AnalysisRequest]) -> AnalysisResult:
        sheet = self.model.current_sheet
        direction = ("", "")
        if (sheet is not None and requests and requests[0].data_type != "diagnostic"
                and requests[0].metric in TWO_ARM_METRICS):
            direction = sheet.effect_direction_arms()
        result = analysis_adapter.execute_analysis_requests(self.model, requests)
        return self._prepare_analysis_result(result, direction)

    def _prepare_analysis_result(
        self, result: AnalysisResult, direction: tuple[str, str] = ("", ""),
    ) -> AnalysisResult:
        result = normalize_analysis_result(self._with_result_identity(result))
        if all(direction) and any(
            section.plot_kind in {"forest", "cumulative_forest", "leave_one_out_forest", "subgroup_forest"}
            for section in result.sections
        ):
            return replace(result, manuscript_favours=direction)
        return result

    def _run_analysis(
        self, regression: Callable[[], AnalysisResult] | None = None, *,
        regression_request: analysis_adapter.AnalysisRequest | None = None,
    ):
        run_button = required(self.buttonBox.button(QDialogButtonBox.StandardButton.Ok), "Run analysis button")
        if not run_button.isEnabled():
            return
        run_button.setEnabled(False)
        self.analysis_error_label.hide()
        self.analysis_error_panel.hide()
        self.analysis_error_toggle.setChecked(False)
        bar = None
        try:
            from rc_metastudio.results.report import ManuscriptReport

            source_sheet = self._rerun_source_sheet or self.model.current_sheet
            requests = self.analysis_requests() if regression is None else ()
            missing_inputs = self._missing_analysis_inputs(
                (regression_request,) if regression_request is not None else requests
            )
            if missing_inputs:
                self._show_analysis_error(missing_inputs)
                return
            repeated = self.analysis_type in {"cumulative", "leave-one-out"}
            bar = progress_dialog.AnalysisProgressDialog(
                self, context=self.windowTitle(), blocking=not repeated, cancellable=repeated,
            )
            bar.show()
            bar.repaint()
            bar.start_tracking()
            result = self._execute_requests(requests) if regression is None else regression()
            if bar.cancelled:
                return
            pooled_fit = self._pooled_fit_for_sheet(requests, source_sheet)
            manuscript = ManuscriptReport.from_result(result)
            change_settings = self._change_settings_callback(source_sheet)
            on_result = self._on_result
            if on_result is None:
                raise RuntimeError("analysis configuration has no results owner")
        except Exception as error:
            if bar is not None and bar.cancelled:
                return
            self._show_execution_error(error)
            return
        finally:
            if bar is not None:
                progress_dialog.dispose(bar)
            run_button.setEnabled(True)
        if source_sheet is not None and pooled_fit is not None:
            source_sheet.last_meta_analysis = pooled_fit
        self.done(QDialog.DialogCode.Accepted.value)
        shown = on_result(result, source_sheet=source_sheet, change_settings=change_settings, manuscript=manuscript)
        self._close_replaced_result(shown)

    def _close_replaced_result(self, shown) -> None:
        if shown is not None and self._replaces is not None and not sip.isdeleted(self._replaces):
            self._replaces.close()

    def _show_execution_error(self, error: Exception) -> None:
        app_error_handler.log_exception(type(error), error, error.__traceback__)
        message = re.sub(r"^Error in .*?:\s*", "", str(error).strip(), count=1, flags=re.DOTALL)
        message = re.sub(r"(?m)^\w*(?:Error|Exception):\s*", "", message).strip()
        # The input precheck should make this fallback unreachable for missing inputs.
        if "Processing terminated since k = 0" in message:
            message = "No study could contribute to this analysis. Check the study values and selected method."
        self._show_analysis_error(message or "The analysis could not be completed.",
                                  f"{error}")

    def _show_analysis_error(self, message: str, details: str = "") -> None:
        self.analysis_error_label.setText(message)
        self.analysis_error_details.setPlainText(details)
        self.analysis_error_toggle.setVisible(bool(details))
        self.analysis_error_panel.show()
        self.analysis_error_label.show()
        self._resize_on_reflow = True
        self._schedule_local_reflow()
        self.activateWindow()
        if details:
            self.analysis_error_toggle.setFocus()

    def _missing_analysis_inputs(self, requests: Sequence[analysis_adapter.AnalysisRequest]) -> str:
        studies = self._manuscript_studies()
        if not studies:
            return ("No studies are included. Select Include for at least one study with complete data."
                    if not self.model.get_studies() else "No included study has values for the selected covariates.")
        selected_ids = {study.id for study in studies}
        ratio_input = self.model.get_current_data_type(get_str=False) in RATIO_DATA_TYPES
        arm_inputs = {
            "binary": "events and totals",
            "continuous": "sample size, mean, and standard deviation",
            "event_rates": "events and person-time",
        }.get(self.data_type)
        for request in requests:
            missing = self._describe_missing_request_inputs(request, selected_ids, ratio_input, arm_inputs)
            if missing is None:
                continue
            if len(studies) > len(missing):
                missing.append(f"and {len(studies) - len(missing):,} more.")
            metric = request.metric
            prefix = f"{ALL_METRIC_NAMES.get(metric, metric)} — " if len(requests) > 1 else ""
            return "No study has enough data to analyze. " + prefix + " ".join(missing)
        return ""

    def _describe_missing_request_inputs(
        self, request: analysis_adapter.AnalysisRequest, selected_ids: set["RowId"],
        ratio_input: bool, arm_inputs: str | None,
    ) -> list[str] | None:
        fields = [column for column in self.model.columns.raw if not column.hidden]
        if request.metric in ONE_ARM_METRICS:
            fields = [column for column in fields if column.arm_index in (None, 0)]
        missing = []
        for index, study in enumerate(self.model.current_sheet.rows):
            if study.id not in selected_ids:
                continue
            absent = self._missing_study_fields(index, study, fields, request, ratio_input)
            if absent is None:
                return None
            if len(missing) < 3:
                inputs = self._describe_study_fields(fields, absent, arm_inputs, request, ratio_input)
                name = f"{study.label} ({study.year})" if study.year else study.label
                missing.append(f"{name} needs {inputs}.")
        return missing

    def _missing_study_fields(
        self, index: int, study: "StudyRow", fields: list["RawColumn"],
        request: analysis_adapter.AnalysisRequest, ratio_input: bool,
    ) -> list["RawColumn"] | None:
        raw = self.model.get_current_raw_data_for_study(index)
        absent = [column for position, column in enumerate(fields)
                  if position >= len(raw) or raw[position] in (None, "")]
        has_raw = bool(fields) and not absent
        has_effect = self.model.study_has_point_est(index, effect=request.metric)
        if ratio_input:
            has_raw = (
                has_raw and has_effect
                and study.analysis_unit.ratio_input(self.model.arm_names).selected_source(raw, metric=request.metric) == "raw"
            )
        if has_raw or (has_effect and request.method not in RAW_COUNT_METHODS):
            return None
        return absent

    def _describe_study_fields(
        self, fields: list["RawColumn"], absent: list["RawColumn"], arm_inputs: str | None,
        request: analysis_adapter.AnalysisRequest, ratio_input: bool,
    ) -> str:
        if arm_inputs and absent and absent == fields and {column.arm_index for column in fields} == {0, 1}:
            parts = [f"{arm_inputs} for both arms"]
        else:
            parts = self._describe_missing_arm_fields(fields, absent, arm_inputs)
        inputs = ", ".join(parts)
        if request.method not in RAW_COUNT_METHODS:
            estimate = "an estimate with its confidence interval or standard error"
            return f"{inputs}, or {estimate}" if inputs else estimate
        if not inputs and ratio_input:
            return "events and person-time selected as the effect source"
        return inputs or "valid study inputs"

    def _describe_missing_arm_fields(
        self, fields: list["RawColumn"], absent: list["RawColumn"], arm_inputs: str | None,
    ) -> list[str]:
        parts = []
        for arm, arm_name in enumerate(self.model.arm_names):
            arm_fields = [column for column in fields if column.arm_index == arm]
            arm_missing = [column for column in absent if column.arm_index == arm]
            if arm_inputs and arm_missing and arm_missing == arm_fields:
                parts.append(f"{arm_inputs} for {arm_name}")
            else:
                parts.extend(f"{column.field.label} ({arm_name})" for column in arm_missing)
        parts.extend(column.field.label for column in absent if column.arm_index is None)
        return parts

    def _pooled_fit_for_sheet(
        self, requests: Sequence[analysis_adapter.AnalysisRequest],
        source_sheet: "Sheet | None",
    ) -> PooledAnalysis | None:
        if (
            len(requests) != 1 or source_sheet is None or self._rerun_source_sheet is not None
            or self.analysis_type is not None or requests[0].data_type == "diagnostic"
        ):
            return None
        request = requests[0]
        return PooledAnalysis.from_method(request.method, request.parameter_values())

    def _expand_error_details(self, expanded):
        self.analysis_error_details.setVisible(expanded)
        self._resize_on_reflow = True
        self._schedule_local_reflow()

    def done(
        self, result: int
    ) -> None:
        self._release_owned_connections()
        super().done(result)
        self.deleteLater()

    def _release_owned_connections(self) -> None:
        self._disconnect_focus_reveal()
        self._layout_reflow_timer.stop()
        try:
            self._layout_reflow_timer.timeout.disconnect(self._apply_local_reflow)
        except (TypeError, RuntimeError):
            pass

    def _with_result_identity(self, result):
        model_label = self.method_cbo_box.currentText()
        if self.is_meta_regression and self.data_type != "diagnostic":
            model_label = "Fixed-effect meta-regression" if self.fixed_effects_radio.isChecked() else "Random-effects meta-regression"
        fits = self._diagnostic_fit_details()
        applied_parameters = self._applied_parameters()
        moderators = [cov['name'] for cov in self._selected_covariates()] if self.is_meta_regression else []
        identity, details = analysis_identity.result_identity(
            self.model, self.analysis_type, self._result_metric_label(),
            model_label, applied_parameters, self.confidence_level,
            moderators,
            fits=fits,
        )
        context = self._result_context(applied_parameters)
        from rc_metastudio.results.report import methods_prose
        metric = self._result_metric_label()
        if self.model.current_effect not in {"PFT", "YUQ", "YUY"}:
            metric = metric[:1].lower() + metric[1:]
        model = self._manuscript_model_label(model_label)
        outcome = self.model.current_sheet.name
        title = f"{outcome[:1].upper() + outcome[1:]}: {model} meta-analysis ({metric})"
        methods = methods_prose(metric, model, applied_parameters,
                                applied_parameters.get("conf.level", self.confidence_level),
                                self.analysis_type, moderators, fits, result.inference_methods,
                                missing_years=any(not study.year for study in self._manuscript_studies()))
        correction = context.partition(". ")[2]
        if correction:
            methods += " " + correction
            details += "\n" + correction
        model_info = self._manuscript_model_info()
        contributing = result.contributing_studies
        included = len(self._manuscript_studies())
        if contributing is not None and contributing < included:
            model_info[:1] = [("Studies included", str(included)), ("Studies contributing", str(contributing))]
        summary = context.split(". ")[0].rstrip(".") + "."
        if contributing is not None and contributing < included:
            summary += (f" {contributing} study contributed to the pooled estimate." if contributing == 1
                        else f" {contributing} studies contributed to the pooled estimate.")
        arms = self._manuscript_arms()
        return replace(result, identity=identity, details=details,
                       analysis_method=self.current_method,
                       manuscript_context=summary,
                       manuscript_title=title, manuscript_methods=methods,
                       manuscript_metric=metric, manuscript_arms=tuple(arms),
                       manuscript_model_info=tuple(model_info),
                       manuscript_comparison=self._manuscript_comparison(arms))

    def _manuscript_model_label(self, model_label):
        if "random" in model_label.lower():
            return "random-effects"
        if "fixed" in model_label.lower():
            return "fixed-effect"
        return model_label

    def _manuscript_comparison(self, arms):
        if self.data_type == "diagnostic":
            return "" if arms == ["Index test"] else "Index test: " + " / ".join(arms)
        prefix = "Arm: " if self.model.current_effect in ONE_ARM_METRICS else "Comparison: "
        return prefix + " / ".join(arms)

    def _manuscript_arms(self) -> list[str]:
        names = self.model.arm_names
        return names[:1] if self.model.current_effect in ONE_ARM_METRICS else names

    def _manuscript_studies(self):
        return getattr(self, "_executed_studies", self.model.get_studies())

    def _manuscript_raw_data(self):
        studies = getattr(self, "_executed_studies", None)
        if studies is None:
            return self.model.get_current_raw_data()
        return self.model.get_current_raw_data(only_these_studies=[study.id for study in studies])

    def _manuscript_model_info(self):
        model_info = [("Studies (k)", str(len(self._manuscript_studies())))]
        for name, total in self._manuscript_participants():
            label = (
                "Participants" if self.model.current_effect in ONE_ARM_METRICS else f"Participants in {name}"
            )
            model_info.append((label, f"{total:g}"))
        if self.data_type == "diagnostic":
            model_info.extend(self._diagnostic_participants(self._manuscript_raw_data()))
        return model_info

    def _manuscript_participants(self) -> list[tuple[str, float]]:
        if self.data_type not in ("binary", "continuous"):
            return []
        arms = self._manuscript_arms()
        raw = self._manuscript_raw_data()
        if not arms or not raw:
            return []
        indices = ((1, 3) if self.data_type == "binary" else (0, 3))[:len(arms)]
        if any(len(row) <= index or not isinstance(row[index], (int, float))
               or not math.isfinite(row[index]) for row in raw for index in indices):
            return []
        return [(name, sum(row[index] for row in raw))
                for name, index in zip(arms, indices, strict=True)]

    @staticmethod
    def _diagnostic_participants(raw):
        complete = [row for row in raw if len(row) == 4 and all(
            isinstance(v, (int, float)) and math.isfinite(v) for v in row
        )]
        return [("Participants", f"{sum(sum(row) for row in complete):g}")] if complete and len(complete) == len(raw) else []


    def _applied_parameters(self):
        applied_parameters = {key: value for key, value in self.current_param_vals.items()
                              if key in self.current_params or key in {"cov_name", "cum_sequence"}}
        if self.is_meta_regression and self.data_type != "diagnostic" and self.fixed_effects_radio.isChecked():
            applied_parameters.pop("rm.method", None)
        return applied_parameters

    def _result_context(self, applied_parameters):
        included = len(self._manuscript_studies())
        excluded = len(self.model.get_studies(only_if_included=False)) - included
        context = f"In total, {included:,} " + ("study was included" if included == 1 else "studies were included")
        participants = self._manuscript_participants()
        if participants:
            (name, total), *others = participants
            if self.model.current_effect in ONE_ARM_METRICS:
                context += f" ({total:,g} participants)"
            else:
                context += f" ({total:,g} participants in {name}"
                context += "".join(f", {total:,g} in {name}" for name, total in others) + ")"
        if excluded:
            context += f"; {excluded:,} " + ("study was excluded" if excluded == 1 else "studies were excluded")
        context += "."
        return context + self._correction_context(applied_parameters)

    def _correction_raw_data(self):
        raw = self._manuscript_raw_data()
        if self.data_type == "binary":
            return fit_raw_rows(
                self._manuscript_studies(), raw, self.model.current_effect,
                self.model.get_current_arm_key(),
            ) or []
        return raw if all(raw_data_is_complete(row) for row in raw) else []

    def _correction_context(self, applied_parameters):
        if self.data_type not in ("binary", "diagnostic") or not applied_parameters.get("adjust"):
            return ""
        raw = self._correction_raw_data()
        if not raw:
            return ""
        policy = applied_parameters.get("correction.policy", applied_parameters.get("to", "only0"))
        zero = self._has_zero_cell(raw)
        if policy in ("none", "None") or not (zero or policy in ("all", "All studies")):
            return ""
        label = {"only0": "studies with at least one zero cell", "all": "all studies",
                 "if0all": "all studies because at least one study had a zero cell"}.get(policy, policy[:1].lower() + policy[1:])
        if self.data_type == "binary":
            from rc_metastudio.results.report import binary_correction_prose
            double_zero = sum(len(row) == 4 and row[0] == 0 and row[2] == 0 for row in raw)
            return " " + binary_correction_prose(self.current_method, applied_parameters['adjust'], label, double_zero)
        return f" A continuity correction of {applied_parameters['adjust']} was applied to {label}."

    def _has_zero_cell(self, raw):
        if any(value == 0 for row in raw for value in row):
            return True
        return self.data_type == "binary" and any(
            row[i] == row[i + 1] for row in raw for i in range(0, len(row) - 1, 2))

    def _diagnostic_fit_details(self):
        if self.data_type != "diagnostic" or self.is_meta_regression:
            return []
        definitions = {self.current_method: self.current_params}
        if self._combined_diagnostic:
            definitions[self.lr_dor_panel.method] = self.lr_dor_panel.definitions
        fits = []
        for metric, configuration in self.diagnostic_analysis_details.items():
            if configuration is None:
                continue
            method, parameters = configuration
            fits.append((ALL_METRIC_NAMES.get(metric, metric), method,
                         _present_values(definitions[method], parameters)))
        return fits

    def _result_metric_label(self):
        if self.data_type != "diagnostic":
            return analysis_identity.metric_label(self.model)
        if self.is_meta_regression:
            return "Sensitivity and specificity"
        labels = {"sens": "Sensitivity", "spec": "Specificity", "lr": "Positive and negative likelihood ratios", "dor": "Diagnostic odds ratio"}
        return ", ".join(labels[metric] for metric in self.diagnostic_metrics).capitalize()

    def analysis_requests(self):
        """Return typed requests represented by the current user configuration."""
        add_plot_params(self)
        workflow = self.analysis_type or "standard"
        if self.data_type != "diagnostic":
            metric = str(self.model.current_effect)
            self.current_param_vals["measure"] = metric
            self.current_param_vals["metric.label"] = self._result_metric_label()
            parameters = copy.deepcopy(self.current_param_vals)
            return (
                analysis_adapter.make_analysis_request(
                    data_type=self.data_type,
                    workflow=workflow,
                    method=self.current_method,
                    metric=metric,
                    parameters=parameters,
                ),
            )

        self.add_current_analysis_details()
        return _diagnostic_analysis_requests(self, workflow)

    def enable_diagnostic_fields(self):
        set_plot_text_value(self.col3_str_edit, "[default]")
        self.show_3.setEnabled(True)
        self.show_3.setChecked(True)

    def disable_bin_only_fields(self):
        self.col3_str_edit.setEnabled(False)
        self.col4_str_edit.setEnabled(False)
        self.show_3.setChecked(False)
        self.show_3.setEnabled(False)
        self.show_4.setChecked(False)
        self.show_4.setEnabled(False)

    def setup_fields_for_one_arm(self):
        self.show_4.setChecked(False)
        self.show_4.setEnabled(False)

    def method_changed(self):
        self.current_method = required(self.method_cbo_box.currentData(), "analysis method")
        self.setup_params()
        self._rebuild_primary_parameters()

    def populate_parameter_controls(self):
        self.parameter_grp_box.setTitle("")
        self.parameter_grp_box.setFlat(True)
        metrics = self._method_query_metrics()
        metric = metrics[0]
        methods = self._methods_for_metrics(metrics)
        if self.data_type == "continuous" and metric == "Mean":
            family = analysis_identity.metric_label(self.model)
            methods = {method: label.replace("Continuous", family, 1) for method, label in methods.items()}
        elif self.data_type == "binary" and metric in ONE_ARM_METRICS:
            methods = {method: label.replace("Binary", "Proportion", 1) for method, label in methods.items()}
        joint = None
        if self.data_type == "diagnostic" and not self.is_meta_regression:
            label = methods.pop(REITSMA_METHOD, None)
            if label is not None and self._joint_diagnostic_available(metric):
                joint = (REITSMA_METHOD, label)
        ordered = sorted(methods.items(), key=lambda item: item[1], reverse=True)
        if joint is not None:
            ordered.insert(0, joint)
        self._populate_method_combo(self.method_cbo_box, ordered)
        self.method_changed()

    def _methods_for_metrics(self, metrics):
        return dict(self.analysis_service.available_methods(
            model=self.model, for_data_type=self.data_type, metrics=metrics,
            workflow=self.analysis_type,
        ))

    def _method_query_metrics(self):
        if self.data_type != "diagnostic":
            return (self.model.current_effect,)
        groups = [group for group in self.diagnostic_metrics
                  if not self._combined_diagnostic or group in ('sens', 'spec')]
        return tuple(metric for group in groups for metric in DIAGNOSTIC_METRIC_GROUPS[group])

    def _joint_diagnostic_available(self, metric):
        return (
            metric == "Sens" and self.analysis_type is None
            and {"sens", "spec"}.issubset(self.diagnostic_metrics)
            and self.model.included_studies_have_raw_data()
        )

    @staticmethod
    def _populate_method_combo(cbo_box, methods):
        with QtCore.QSignalBlocker(cbo_box):
            cbo_box.clear()
            for method, label in methods:
                cbo_box.addItem(label, method)

    def _remove_parameter_widgets(self, widgets):
        self._advanced_entries = [entry for entry in self._advanced_entries if entry[1] not in widgets]
        for widget in widgets:
            widget.setParent(None)
            widget.deleteLater()

    def _rebuild_primary_parameters(self):
        self._remove_parameter_widgets(self.current_widgets)
        self._configure_plot_option_groups()
        parameter_layout = self._parameter_layout()
        self.current_widgets = self._add_effect_measure(parameter_layout)
        definitions = self._ordered_parameter_definitions()
        if self._combined_diagnostic:
            definitions = self._local_diagnostic_parameters(definitions)
        self.current_widgets.extend(
            self._render_parameters(
                parameter_layout, definitions, self.current_param_vals, self._method_defaults, first_row=1
            )
        )
        if self.data_type == "diagnostic" and self.sens_spec:
            reason = ""
            if self.analysis_type in {"cumulative", "leave-one-out", "subgroup"}:
                reason = "The joint Reitsma model is unavailable for this workflow; sensitivity and specificity are fitted separately."
            elif not {"sens", "spec"}.issubset(self.diagnostic_metrics):
                reason = "The joint Reitsma model requires both sensitivity and specificity."
            elif not self.model.included_studies_have_raw_data():
                reason = "The joint Reitsma model requires complete TP/FN/FP/TN counts for every included study. Entered estimates use separate univariate fits."
            if reason:
                note = QLabel(reason)
                note.setWordWrap(True)
                note.setAccessibleName("Joint model availability")
                parameter_layout.addWidget(note, parameter_layout.rowCount(), 0, 1, 2)
                self.current_widgets.append(note)
        self._rebuild_shared_diagnostic_params()
        self._set_analysis_tab_order()
        self._schedule_local_reflow()

    def _set_analysis_tab_order(self):
        """Dynamic fields are created after the buttons; restore their visual order."""
        controls = [self.method_cbo_box]
        controls.extend(widget for widget in self.current_widgets if widget.focusPolicy() & Qt.FocusPolicy.TabFocus)
        if self._shared_diagnostic_layout is not None:
            panel = self.lr_dor_panel
            controls.append(panel.combo)
            controls.extend(widget for widget in panel.widgets if widget.focusPolicy() & Qt.FocusPolicy.TabFocus)
        controls.extend(widget for widget in self._shared_diagnostic_widgets if widget.focusPolicy() & Qt.FocusPolicy.TabFocus)
        controls.append(self.advanced_toggle)
        controls.extend(control for _, control, _, _ in self._advanced_entries)
        controls.extend(button for button in (self.buttonBox.button(QDialogButtonBox.StandardButton.Ok),
                                              self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel)) if button is not None)
        for before, after in zip(controls, controls[1:]):
            self.setTabOrder(before, after)

    def _parameter_layout(self):
        parameter_layout = self.parameter_grp_box.layout()
        if parameter_layout is None:
            parameter_layout = QGridLayout()
            parameter_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.parameter_grp_box.setLayout(parameter_layout)
        if not isinstance(parameter_layout, QGridLayout):
            raise TypeError("Analysis parameters require a grid layout")
        # Labels keep their natural width; value editors consume the remaining
        # method-panel width instead of forcing the panel wider than its
        # adaptive viewport.
        parameter_layout.setColumnStretch(0, 0)
        parameter_layout.setColumnStretch(1, 1)
        return parameter_layout

    def _ordered_parameter_definitions(self):
        definitions = [
            _normalize_parameter_definition(
                name,
                self.current_params[name],
                self.current_defaults.get(name),
                self.param_d.get(name),
            )
            for name in self.current_params
        ]
        if self.var_order is not None:
            by_name = {spec.name: spec for spec in definitions}
            return [by_name[name] for name in self.var_order]
        return [
            spec
            for kind in ("enum", "float", "int", "string")
            for spec in definitions
            if spec.kind == kind
        ]

    def _refresh_advanced_summary(self):
        changes = []
        for spec, control, target, default in self._advanced_entries:
            value = target.get(spec.name)
            if str(value) == str(default):
                continue
            if isinstance(control, QComboBox):
                text = control.currentText()
            elif isinstance(control, (QSpinBox, QDoubleSpinBox)):
                text = f"{value:g}"
            else:
                text = str(value)
            changes.append(f"{parameter_display_label(spec.name, spec.metadata)} {text}")
        self.advanced_toggle.setText("Advanced" + (f" · {len(changes)} changed" if changes else ""))
        self.advanced_toggle.setToolTip("\n".join(changes) or "Additional method options")

    def _place_parameter(self, layout, row, spec, label, control, target, default):
        if spec.name in {"measure", "rm.method", "estimator", "conf.level"}:
            layout.addWidget(label, row, 0)
            layout.addWidget(control, row, 1)
            return row + 1
        advanced = self.advanced_panel.layout()
        assert isinstance(advanced, QGridLayout)
        advanced_row = advanced.rowCount()
        advanced.addWidget(label, advanced_row, 0)
        advanced.addWidget(control, advanced_row, 1)
        self._advanced_entries.append((spec, control, target, default))
        if isinstance(control, QComboBox):
            control.currentIndexChanged.connect(self._refresh_advanced_summary)
        elif isinstance(control, (QSpinBox, QDoubleSpinBox)):
            control.valueChanged.connect(self._refresh_advanced_summary)
        elif isinstance(control, QCheckBox):
            control.toggled.connect(self._refresh_advanced_summary)
        else:
            control.textChanged.connect(self._refresh_advanced_summary)
        return row

    def _setup_advanced_parameters(self):
        self._advanced_entries = []
        self.advanced_toggle = DisclosureButton("Advanced", self)
        self.advanced_toggle.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed)
        self.advanced_panel = QtWidgets.QWidget()
        QGridLayout(self.advanced_panel)
        self.advanced_toggle.toggled.connect(self._expand_advanced)
        expanded = QtCore.QSettings().value("analysis/advancedExpanded", False, type=bool)
        self.advanced_toggle.setChecked(expanded)
        self.advanced_panel.setVisible(expanded)
        self.gridLayout.addWidget(self.advanced_toggle, 20, 0, 1, 4, Qt.AlignmentFlag.AlignLeft)
        self.gridLayout.addWidget(self.advanced_panel, 21, 0, 1, 4)

    def _add_effect_measure(self, layout):
        effect_label = QLabel("Effect measure")
        layout.addWidget(effect_label, 0, 0)
        metric_label = QLabel(", ".join({"sens": "Sensitivity", "spec": "specificity"}[group]
                                       for group in self.diagnostic_metrics if group in ("sens", "spec")).capitalize()
                              if self._combined_diagnostic else self._result_metric_label().capitalize())
        metric_label.setWordWrap(True)
        metric_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(metric_label, 0, 1)
        self._configure_parameter_accessibility(effect_label, metric_label)
        return [effect_label, metric_label]

    def _render_parameters(self, layout, definitions, target, defaults, *, first_row=0):
        widgets = []
        row = first_row
        for spec in definitions:
            label = self._parameter_label(spec)
            control = self._create_parameter_control(spec, target)
            self._configure_parameter_accessibility(label, control)
            widgets.extend((label, control))
            row = self._place_parameter(layout, row, spec, label, control, target, defaults.get(spec.name))
        self._refresh_advanced_summary()
        return widgets

    def _expand_advanced(self, checked):
        self.advanced_panel.setVisible(checked)
        self._refresh_advanced_summary()
        QtCore.QSettings().setValue("analysis/advancedExpanded", checked)
        self._resize_on_reflow = True
        self._schedule_local_reflow()

    def _parameter_label(self, spec):
        label = QLabel(parameter_display_label(spec.name, spec.metadata))
        label.setWordWrap(True)
        description = parameter_description(spec.name, spec.metadata)
        label.setToolTip(description)
        return label

    @staticmethod
    def _configure_parameter_accessibility(label, control):
        """Associate each generated value editor with its visible label."""
        description = label.toolTip() or label.text()
        label.setBuddy(control)
        label.setAccessibleName(label.text())
        label.setAccessibleDescription(description)
        control.setAccessibleName(label.text())
        control.setAccessibleDescription(description)
        control.setToolTip(description)

    def _create_parameter_control(self, spec, target):
        if spec.kind == "enum" and set(spec.values) == {"TRUE", "FALSE"}:
            control = QCheckBox(self)
            control.setChecked(str(spec.default).upper() == "TRUE")
            target[spec.name] = "TRUE" if control.isChecked() else "FALSE"
            control.toggled.connect(lambda checked: target.__setitem__(spec.name, "TRUE" if checked else "FALSE"))
            return control
        elif spec.kind == "enum":
            control = self._enum_parameter_control(spec, target)
        elif spec.kind == "int":
            control = self._integer_parameter_control(spec, target)
        elif spec.kind == "float":
            control = self._float_parameter_control(spec, target)
        else:
            control = QLineEdit()
            if spec.default is not None:
                control.setText(str(spec.default))
                target[spec.name] = spec.default
            adaptive_controls.configure_text_value_control(control)
            control.textChanged.connect(
                app_error_handler.safe_slot(
                    lambda value: target.__setitem__(spec.name, str(value)), parent=self
                )
            )
            return control

        if isinstance(control, QComboBox):
            self._configure_value_control(control)
        else:
            adaptive_controls.configure_numeric_value_control(control)
        return control

    def _enum_parameter_control(self, spec, target):
        control = adaptive_controls.AdaptiveComboBox()
        for value in spec.values:
            control.addItem(
                parameter_value_display_label(spec.name, value, spec.metadata),
                value,
            )
        if spec.default is not None:
            index = self._find_enum_item_index(control, spec.default)
            if index >= 0:
                control.setCurrentIndex(index)
            target[spec.name] = qt_text.to_native_text(control.currentData())
        combo = control
        control.currentIndexChanged[int].connect(
            app_error_handler.safe_slot(
                lambda index: target.__setitem__(
                    spec.name, qt_text.to_native_text(combo.itemData(index))
                ),
                parent=self,
            )
        )
        return control

    def _integer_parameter_control(self, spec, target):
        control = QSpinBox()
        if spec.name == "digits":
            control.setRange(ANALYSIS_DIGITS_MIN, ANALYSIS_DIGITS_MAX)
        else:
            control.setRange(-2147483648, 2147483647)
        control.setCorrectionMode(
            QtWidgets.QAbstractSpinBox.CorrectionMode.CorrectToPreviousValue
        )
        if spec.default is not None:
            value = (
                validate_analysis_digits(spec.default)
                if spec.name == "digits"
                else (
                    _coerce_integer_default(spec.name, spec.default)
                )
            )
            control.setValue(value)
            target[spec.name] = value
        control.valueChanged[int].connect(
            app_error_handler.safe_slot(
                lambda value: target.__setitem__(spec.name, value), parent=self
            )
        )
        return control

    def _float_parameter_control(self, spec, target):
        control = _CompactDoubleSpinBox()
        control.setDecimals(1 if spec.name == "conf.level" else 6)
        if spec.name == "conf.level":
            control.setRange(50, CONFIDENCE_LEVEL_DISPLAY_MAX)
            control.setSingleStep(0.1)
            control.setSuffix("%")
        elif spec.name in ANALYSIS_NON_NEGATIVE_FLOAT_PARAMS:
            control.setRange(0, ANALYSIS_NUMERIC_MAX)
        else:
            control.setRange(ANALYSIS_NUMERIC_MIN, ANALYSIS_NUMERIC_MAX)
        control.setCorrectionMode(
            QtWidgets.QAbstractSpinBox.CorrectionMode.CorrectToPreviousValue
        )
        if spec.default is not None:
            value = (
                validate_confidence_level(spec.default)
                if spec.name == "conf.level"
                else (
                    validate_correction_factor(spec.default)
                    if spec.name in ANALYSIS_NON_NEGATIVE_FLOAT_PARAMS
                    else validate_analysis_float(spec.name, spec.default)
                )
            )
            control.setValue(value)
            target[spec.name] = value
        control.valueChanged[float].connect(
            app_error_handler.safe_slot(
                lambda value: target.__setitem__(spec.name, value), parent=self
            )
        )
        return control

    def _find_enum_item_index(self, cbo_box, value):
        for index in range(cbo_box.count()):
            if qt_text.to_native_text(cbo_box.itemData(index)) == str(value):
                return index
        return -1



    def _configure_value_control(self, widget):
        adaptive_controls.configure_choice_control(widget, visible_characters=42)
        # Screen-bounded dialogs may still shrink, but complete choices contribute
        # to the initial size rather than being discarded by an Ignored policy.
        widget.setMinimumWidth(0)
        widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, widget.sizePolicy().verticalPolicy()
        )

    def _configure_method_selector(self, widget):
        adaptive_controls.configure_choice_control(widget, visible_characters=48)
        # Unlike parameter editors, the primary method selector determines the
        # dialog's useful preferred width and must keep its readable size hint.
        widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, widget.sizePolicy().verticalPolicy()
        )

    def _schedule_local_reflow(self):
        """Coalesce dynamic content negotiation."""
        if self._layout_reflow_pending:
            return
        self._layout_reflow_pending = True
        self._layout_reflow_timer.start(0)

    def _apply_local_reflow(self):
        self._layout_reflow_pending = False
        resize_window = self._resize_on_reflow
        self._resize_on_reflow = False
        for combo in self.content_scroll_area.findChildren(QComboBox):
            adaptive_controls.refresh_choice_popup_width(combo)
        for layout in (
            self.parameter_grp_box.layout(),
            self.shared_diagnostic_params_box.layout(),
            self.content_scroll_layout,
        ):
            if layout is not None:
                layout.invalidate()
        self.content_scroll_area_widget.updateGeometry()
        self.specs_tab.updateGeometry()
        active_page = self.specs_tab.currentWidget()
        assert active_page is not None
        content_height = self._active_content_height()
        # Method changes stay inside the scroll body. Explicit disclosure of
        # Advanced controls may grow the dialog while preserving its placement.
        if not self.isVisible() or resize_window:
            position = self.pos()
            previous_size = self.size()
            self._set_scroll_body_height(content_height)
            if self.isVisible():
                policy = adaptive_window.WINDOW_POLICIES[adaptive_window.WindowRole.TRANSACTIONAL]
                available_height = int(adaptive_window.available_geometry_for_window(self).height() * policy.maximum_screen_fraction)
                frame_height = max(0, self.frameGeometry().height() - self.height())
                self.resize(previous_size.width(), min(available_height - frame_height,
                            self.sizeHint().height()))
            else:
                self.adjustSize()
            self.move(position)
        if self.isVisible():
            self._fit_method_text()
        self._reveal_focused_control(None, QtWidgets.QApplication.focusWidget())

    def _fit_method_text(self):
        rows = [(self._method_row, self._method_layout, self.method_lbl, self.method_cbo_box)]
        if self.analysis_type == 'cumulative':
            rows.append((self._sequence_row, self._sequence_layout, self.study_order_label, self.study_order))
        if self._shared_diagnostic_layout is not None:
            rows.append((self._lr_dor_method_row, self._lr_dor_method_layout,
                         self.lr_dor_method_lbl, self.lr_dor_method_cbo_box))
        panels = [self.parameter_grp_box, self.advanced_panel]
        if self._shared_diagnostic_layout is not None:
            panels.extend((self.lr_dor_parameter_grp_box, self.shared_diagnostic_params_box))
        grids = [(panel, grid) for panel in panels if isinstance(grid := panel.layout(), QGridLayout)]
        labels = _grid_field_labels(grids)
        label_cap = self.fontMetrics().height() * 18
        label_width = min(label_cap, max([field.sizeHint().width() for field in labels]
                                        + [label.minimumSizeHint().width() for _, _, label, _ in rows]))
        leading = max(panel.mapTo(self.methods_tab, QtCore.QPoint()).x()
                      + panel.contentsMargins().left() + grid.contentsMargins().left()
                      for panel, grid in grids)
        for panel, grid in grids:
            margins = grid.contentsMargins()
            left = leading - panel.mapTo(self.methods_tab, QtCore.QPoint()).x() - panel.contentsMargins().left()
            grid.setContentsMargins(left, margins.top(), margins.right(), margins.bottom())
            grid.setColumnMinimumWidth(0, label_width)
            grid.setColumnStretch(1, 1)
        for field in labels:
            field.setMaximumWidth(label_cap)
        self._fit_method_rows(rows, leading, label_width)

    def _fit_method_rows(self, rows, leading, label_width):
        for row_widget, layout, label, combo in rows:
            label.setWordWrap(label.fontMetrics().horizontalAdvance(label.text()) > label_width)
            label.setMaximumWidth(label_width)
            label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            left = leading - row_widget.mapTo(self.methods_tab, QtCore.QPoint()).x() - row_widget.contentsMargins().left()
            layout.setContentsMargins(left, 0, 0, 0)
            layout.setColumnMinimumWidth(0, label_width)
            layout.activate()
            option = QtWidgets.QStyleOptionComboBox()
            combo.initStyleOption(option)
            style = combo.style()
            assert style is not None
            field = style.subControlRect(
                QtWidgets.QStyle.ComplexControl.CC_ComboBox, option,
                QtWidgets.QStyle.SubControl.SC_ComboBoxEditField, combo,
            )
            text_width = combo.fontMetrics().horizontalAdvance(combo.currentText())
            needed = max(
                label_width + text_width + combo.width() - field.width(),
                label.minimumSizeHint().width() + combo.minimumSizeHint().width(),
            )
            # The scroll body may already have expanded to this row's unwrapped
            # minimum. Fit against the viewport rather than that expanded width.
            viewport = required(self.content_scroll_area.viewport(), "analysis viewport")
            page_margins = self.content_scroll_area_widget.width() - row_widget.width()
            available_width = min(layout.contentsRect().width(), viewport.width() - page_margins)
            stacked = needed + layout.horizontalSpacing() > available_width
            combo_row = 1 if stacked else 0
            if layout.getItemPosition(layout.indexOf(combo))[0] == combo_row:
                continue
            layout.removeWidget(label)
            layout.removeWidget(combo)
            layout.addWidget(label, 0, 0, 1, 2 if stacked else 1)
            layout.addWidget(combo, combo_row, 0 if stacked else 1, 1, 2 if stacked else 1)
            layout.activate()

    def resizeEvent(
        self, event: QResizeEvent | None
    ) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_layout_reflow_timer"):
            self._schedule_local_reflow()

    def changeEvent(
        self, event: QtCore.QEvent | None
    ) -> None:
        super(AnalysisSetupDialog, self).changeEvent(event)
        if event is not None and event.type() == QtCore.QEvent.Type.FontChange and hasattr(self, "_layout_reflow_timer"):
            self._schedule_local_reflow()


    def _reveal_focused_control(self, _old, focused):
        if focused is not None and self.content_scroll_area.isAncestorOf(focused):
            self.content_scroll_area.ensureWidgetVisible(focused)

    def setup_params(self):
        self.current_params, self.current_defaults, self.var_order, self.param_d = (
            self.analysis_service.parameters(self.current_method)
        )

        self._method_defaults = dict(self.current_defaults)
        for name, definition in self.current_params.items():
            if name not in self.current_param_vals:
                continue
            saved_value = self.current_param_vals[name]
            if isinstance(definition, list) and str(saved_value) not in {
                str(option) for option in definition
            }:
                continue
            self.current_defaults[name] = saved_value

        # The application-level confidence setting overrides method defaults.
        self.current_defaults["conf.level"] = self.confidence_level

    def _local_diagnostic_parameters(self, specs):
        local = []
        for spec in specs:
            existing = self._shared_diagnostic_param_specs.get(spec.name)
            if existing is None:
                local.append(spec)
            elif spec.metadata:
                self._shared_diagnostic_param_specs[spec.name] = replace(existing, metadata=spec.metadata)
        return local

    def _finish_combined_diagnostic_ui(self):
        self.setWindowTitle("Method and parameters")
        self.method_lbl.setText(diagnostic_metric_group_display_label("sens_spec") + " method")

        # Stack the method panels while keeping labels beside their selectors.
        for widget in (self.lr_dor_method_lbl, self.lr_dor_method_cbo_box,
                       self.lr_dor_parameter_grp_box, self.shared_diagnostic_params_box):
            self.gridLayout.removeWidget(widget)
        self._lr_dor_method_row = QtWidgets.QWidget(self.methods_tab)
        self._lr_dor_method_layout = QGridLayout(self._lr_dor_method_row)
        self._lr_dor_method_layout.setContentsMargins(0, 0, 0, 0)
        self._lr_dor_method_layout.setColumnStretch(1, 1)
        self._lr_dor_method_layout.addWidget(self.lr_dor_method_lbl, 0, 0)
        self._lr_dor_method_layout.addWidget(self.lr_dor_method_cbo_box, 0, 1)
        self.gridLayout.addWidget(self._lr_dor_method_row, 2, 0, 1, 2)
        self.gridLayout.addWidget(self.lr_dor_parameter_grp_box, 3, 0, 1, 2)
        self.gridLayout.addWidget(self.shared_diagnostic_params_box, 4, 0, 1, 2)
        self.lr_dor_method_lbl.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.shared_diagnostic_params_box.show()

        lr_label = ("Likelihood ratios and DOR" if {"lr", "dor"}.issubset(self.diagnostic_metrics)
                    else "Positive and negative likelihood ratios" if "lr" in self.diagnostic_metrics
                    else "Diagnostic odds ratio")
        self.lr_dor_method_lbl.setWordWrap(True)
        self.lr_dor_method_lbl.show()
        self.lr_dor_method_cbo_box.show()
        self.lr_dor_parameter_grp_box.show()
        self.lr_dor_panel = _DiagnosticMethodPanel(
            self,
            lr_label,
            self.lr_dor_method_lbl,
            self.lr_dor_method_cbo_box,
            self.lr_dor_parameter_grp_box,
        )
        for widget in (self.lr_dor_parameter_grp_box, self.shared_diagnostic_params_box):
            widget.setSizePolicy(QSizePolicy.Policy.Ignored, widget.sizePolicy().verticalPolicy())
        self._shared_diagnostic_layout = QGridLayout(self.shared_diagnostic_params_box)
        self.lr_dor_panel.populate()

    def _rebuild_shared_diagnostic_params(self):
        layout = self._shared_diagnostic_layout
        if layout is None:
            return
        self._remove_parameter_widgets(self._shared_diagnostic_widgets)
        active = self.current_params.keys() | self.lr_dor_panel.definitions.keys()
        definitions = []
        defaults = {}
        for name, spec in self._shared_diagnostic_param_specs.items():
            if name not in active:
                continue
            defaults[name] = spec.default
            definitions.append(replace(spec, default=self.current_param_vals.get(name, spec.default)))
        self._shared_diagnostic_widgets = self._render_parameters(
            layout, definitions, self.current_param_vals, defaults
        )

    def add_current_analysis_details(self):
        """This method only applicable for diagnostic data, wherein
        we have multiple metrics. here the parameters/method for
        these metrics are added to a dictionary.
        """
        metrics_to_run = list(self.diagnostic_analysis_details.keys())

        if self._combined_diagnostic:
            first_params = self._diagnostic_params_for_method(
                self.current_params, self.current_param_vals
            )
            second_params = self._diagnostic_params_for_method(
                self.lr_dor_panel.definitions, self.lr_dor_panel.params
            )
            for metric in [m for m in ("Sens", "Spec") if m in metrics_to_run]:
                self.diagnostic_analysis_details[metric] = (
                    self.current_method,
                    copy.deepcopy(first_params),
                )
            for metric in [m for m in ("DOR", "PLR", "NLR") if m in metrics_to_run]:
                self.diagnostic_analysis_details[metric] = (
                    self.lr_dor_panel.method,
                    copy.deepcopy(second_params),
                )
        elif self.sens_spec:
            for metric in [m for m in ("Sens", "Spec") if m in metrics_to_run]:
                self.diagnostic_analysis_details[metric] = (
                    self.current_method,
                    self.current_param_vals,
                )
        else:
            for metric in [m for m in ("DOR", "PLR", "NLR") if m in metrics_to_run]:
                self.diagnostic_analysis_details[metric] = (
                    self.current_method,
                    self.current_param_vals,
                )

    def _diagnostic_params_for_method(self, definitions, local_params):
        params = _plot_parameter_values(self.current_param_vals)
        shared = set(definitions).intersection(SHARED_DIAGNOSTIC_PARAMS)
        params.update(_present_values(shared, self.current_param_vals))
        local_names = set(definitions).difference(SHARED_DIAGNOSTIC_PARAMS)
        params.update(_present_values(local_names, local_params))
        # Subgroup selection is workflow state, not a method parameter. Keep it
        # on each filtered request so combined diagnostic panels use the same
        # subgroup while retaining per-method parameter filtering above.
        for key in ("cov_name", "cum_sequence"):
            if key in self.current_param_vals:
                params[key] = self.current_param_vals[key]
        return params

    def setup_diagnostic_ui(self):
        if len(self.diagnostic_analysis_details) == 0:
            metrics_to_run = []
            for m in self.diagnostic_metrics:
                metrics_to_run.extend(DIAGNOSTIC_METRIC_GROUPS[m])

            self.diagnostic_analysis_details = dict(
                list(zip(metrics_to_run, [None for m in metrics_to_run]))
            )

        window_title = ""
        if self.is_meta_regression:
            # Reitsma estimates the joint random-effects model directly.
            self.regression_model_group.hide()
            window_title = "Reitsma meta-regression"
        elif self._combined_diagnostic:
            window_title = "Method and parameters"
        elif self.sens_spec:
            metric_group_label = diagnostic_metric_group_display_label("sens_spec")
            window_title = "Method and parameters for %s" % metric_group_label
        else:
            metric_group_label = diagnostic_metric_group_display_label("lr_dor")
            window_title = "Method and parameters for %s" % metric_group_label

        self.setWindowTitle(QtCore.QCoreApplication.translate("Dialog", window_title))
        self.method_lbl.setText("Analysis method")
        self.method_lbl.setWordWrap(False)


def _coerce_integer_default(name: str, value: object) -> int:
    """Convert a persisted integer default after validating its concrete type."""
    if not isinstance(value, (str, bytes, bytearray, int, float)):
        raise TypeError(f"Invalid integer default for {name}: {value!r}")
    return int(value)


def _is_integer_analysis_param(name):
    return name == "digits"


def add_plot_params(specs_form: AnalysisSetupDialog) -> None:
    specs_form.current_param_vals["plot_caption"] = analysis_identity.plot_caption(
        specs_form.model, specs_form.current_param_vals.get("plot_caption")
    )
    output_stem = specs_form._fit_output_stem
    if specs_form.is_meta_regression:
        specs_form.current_param_vals.update(
            {
                "bp_style": selected_plot_style(specs_form.style_cbo),
                "bp_accent_color": _text_value(specs_form.accent_color),
                "bp_point_size_multiplier": specs_form.point_size_multiplier.value(),
                **plot_axis_label_params(specs_form.x_lbl_le, "bp"),
                "bp_xticks": _validated_plot_ticks(specs_form.x_ticks_le),
                "bp_plot_lb": _validated_plot_bound(specs_form.plot_lb_le),
                "bp_plot_ub": _validated_plot_bound(specs_form.plot_ub_le),
                "bp_outpath": f"{output_stem}.svg",
                "bp_display_path": f"{output_stem}.svg",
                "bp_show_regression_line": specs_form.show_regression_line.isChecked(),
                "bp_show_confidence_band": specs_form.show_confidence_band.isChecked(),
                "bp_show_prediction_interval": specs_form.show_prediction_interval.isChecked(),
                "bp_show_legend": specs_form.show_legend.isChecked(),
            }
        )
        return

    if specs_form.analysis_type == "cumulative":
        specs_form.current_param_vals["cum_sequence"] = specs_form.study_order.currentData()
    specs_form.current_param_vals["fp_show_i2"] = specs_form.show_i2.isChecked()
    specs_form.current_param_vals["fp_study_order"] = specs_form.study_order.currentData() if specs_form.analysis_type != "cumulative" else "table"
    specs_form.current_param_vals["fp_style"] = selected_plot_style(specs_form.style_cbo)
    specs_form.current_param_vals["fp_show_col1"] = specs_form.show_1.isChecked()
    specs_form.current_param_vals["fp_col1_str"] = _text_value(specs_form.col1_str_edit)
    specs_form.current_param_vals["fp_show_col2"] = specs_form.show_2.isChecked()
    specs_form.current_param_vals["fp_col2_str"] = _text_value(specs_form.col2_str_edit)
    specs_form.current_param_vals["fp_show_col3"] = specs_form.show_3.isChecked()
    specs_form.current_param_vals["fp_col3_str"] = _text_value(specs_form.col3_str_edit)
    specs_form.current_param_vals["fp_show_col4"] = specs_form.show_4.isChecked()
    specs_form.current_param_vals["fp_col4_str"] = _text_value(specs_form.col4_str_edit)
    specs_form.current_param_vals.update(plot_axis_label_params(specs_form.x_lbl_le, "fp"))
    specs_form.current_param_vals["fp_outpath"] = f"{output_stem}.svg"
    specs_form.current_param_vals["fp_display_path"] = specs_form.current_param_vals["fp_outpath"]

    specs_form.current_param_vals["fp_plot_lb"] = _validated_plot_bound(specs_form.plot_lb_le)
    specs_form.current_param_vals["fp_plot_ub"] = _validated_plot_bound(specs_form.plot_ub_le)
    specs_form.current_param_vals["fp_xticks"] = _validated_plot_ticks(specs_form.x_ticks_le)

    specs_form.current_param_vals["fp_show_summary_line"] = (
        specs_form.show_summary_line.isChecked()
    )
    specs_form.current_param_vals["fp_show_raw_counts"] = (
        specs_form.show_raw_counts.isChecked()
    )
    specs_form.current_param_vals["fp_show_headers"] = (
        specs_form.show_headers.isChecked()
    )
    specs_form.current_param_vals["fp_show_annotation"] = (
        specs_form.show_annotation.isChecked()
    )
    specs_form.current_param_vals["fp_accent_color"] = _text_value(
        specs_form.accent_color
    )
    specs_form.current_param_vals["fp_point_size_multiplier"] = (
        specs_form.point_size_multiplier.value()
    )


def _validated_plot_bound(widget):
    value = _text_value(widget)
    return value if value != "[default]" and parse_plot_bound(value) is not False else "[default]"


def _validated_plot_ticks(widget):
    value = _text_value(widget)
    return value if value != "[default]" and is_valid_plot_tick_list(value) else "[default]"


def _scalar_plot_param(value):
    if isinstance(value, (list, tuple)) and value:
        return value[0]
    return value


def _bool_plot_param(value, default):
    value = _scalar_plot_param(default if value is None else value)
    if isinstance(value, str):
        return value.lower() in ("true", "t", "1", "yes")
    return bool(value)


def _float_plot_param(value, default):
    try:
        return float(_scalar_plot_param(default if value is None else value))
    except (TypeError, ValueError):
        return default


def _diagnostic_analysis_requests(
    specs_form: AnalysisSetupDialog, workflow: str,
) -> tuple[analysis_adapter.AnalysisRequest, ...]:
    requests = []
    missing_metrics = []

    joint, pending = _diagnostic_pending_requests(specs_form)
    for diagnostic_metric, details in pending:
        if details is None:
            missing_metrics.append(diagnostic_metric)
            continue

        try:
            method, param_vals = details
        except (TypeError, ValueError):
            raise ValueError(
                "Invalid method and parameter selection for: %s." % diagnostic_metric
            )

        if method is None or param_vals is None:
            missing_metrics.append(diagnostic_metric)
            continue

        param_vals = copy.deepcopy(param_vals)
        param_vals["plot_caption"] = specs_form.current_param_vals.get("plot_caption", "")

        output_stem = f"{specs_form._fit_output_stem}_{diagnostic_metric.lower()}"
        param_vals["fp_outpath"] = f"{output_stem}.svg"
        param_vals["fp_display_path"] = param_vals["fp_outpath"]
        param_vals.pop("measure", None)
        if joint is not None and diagnostic_metric == "Sens":
            param_vals["joint.metrics"] = "Sens,Spec"

        requests.append(analysis_adapter.make_analysis_request(
            data_type=specs_form.data_type,
            workflow=workflow,
            method=method,
            metric=diagnostic_metric,
            parameters=param_vals,
        ))

    if missing_metrics:
        raise ValueError(
            "No method and parameters were selected for: %s. "
            "Complete all diagnostic method screens before running analysis."
            % ", ".join(missing_metrics)
        )

    if not requests:
        raise ValueError("No diagnostic effect measures were selected for analysis.")

    return tuple(requests)


def _text_value(widget):
    return qt_text.to_native_text(plot_text_value(widget))


def _diagnostic_pending_requests(specs_form):
    ordered_metrics = ["Sens", "Spec", "NLR", "PLR", "DOR"]
    configured = [
        metric
        for metric in ordered_metrics
        if metric in specs_form.diagnostic_analysis_details
    ]
    # Sensitivity and specificity are one Reitsma request.  The pair is a
    # request-only joint metric and is never persisted as a project effect.
    joint = None
    if "Sens" in configured and "Spec" in configured:
        sens_details = specs_form.diagnostic_analysis_details["Sens"]
        spec_details = specs_form.diagnostic_analysis_details["Spec"]
        if sens_details and spec_details and sens_details[0] == spec_details[0] == REITSMA_METHOD:
            joint = (sens_details[0], sens_details[1])
            configured = [metric for metric in configured if metric not in ("Sens", "Spec")]

    pending = [("Sens", joint)] if joint is not None else []
    pending.extend((metric, specs_form.diagnostic_analysis_details[metric]) for metric in configured)
    return joint, pending




def _grid_field_labels(grids):
    labels = []
    for _, grid in grids:
        for index in range(grid.count()):
            item = grid.itemAt(index)
            _, column, _, span = grid.getItemPosition(index)
            if item is None or column != 0 or span != 1:
                continue
            field = item.widget()
            if isinstance(field, QLabel):
                labels.append(field)
    return labels
