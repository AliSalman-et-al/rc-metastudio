# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Method-selection dialog and analysis specification builder."""

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QColor, QHideEvent, QShowEvent
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QDoubleSpinBox,
    QSizePolicy,
    QSpinBox,
)

import copy
import hashlib
import os
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Literal

from rc_metastudio import (
    adaptive_controls,
    adaptive_window,
    analysis_adapter,
    app_error_handler,
    plot_capabilities,
    progress_dialog,
    qt_text,
    data_issue_review,
)
from rc_metastudio.analysis_method_labels import (
    diagnostic_metric_group_display_label,
    normalize_available_method_labels,
    parameter_description,
    parameter_display_label,
    parameter_value_display_label,
)
from rc_metastudio.analysis_errors import PrimaryDiagnosticFitError
from rc_metastudio.plot_defaults import apply_default_forest_arm_labels
from rc_metastudio.plot_text import (
    apply_plot_text_input_limits,
    plot_parameter_text_value,
)
from rc_metastudio.meta_globals import (
    ANALYSIS_DIGITS_MAX,
    ANALYSIS_DIGITS_MIN,
    ANALYSIS_NON_NEGATIVE_FLOAT_PARAMS,
    ANALYSIS_NUMERIC_MAX,
    ANALYSIS_NUMERIC_MIN,
    CONFIDENCE_LEVEL_DISPLAY_MAX,
    CONTINUOUS,
    DIAGNOSTIC_METRIC_LABELS,
    DIAGNOSTIC_METRIC_GROUPS,
    ONE_ARM_METRICS,
    check_plot_bound,
    seems_sane,
    validate_analysis_digits,
    validate_analysis_float,
    validate_confidence_level,
    validate_correction_factor,
)
from rc_metastudio.settings import analysis_output_path

if TYPE_CHECKING:
    from ui_analysis_setup_dialog import Ui_AnalysisSetupDialog
else:
    from rc_metastudio.forms.ui_analysis_setup_dialog import Ui_AnalysisSetupDialog

PLOT_STYLE_LABELS = {
    "default": "Default (metafor)",
    "revman": "RevMan",
    "bmj": "BMJ",
}
PLOT_STYLE_VALUES = {label: value for value, label in PLOT_STYLE_LABELS.items()}
PLOT_STYLE_DEFAULT_COLORS = {
    "default": "#2f5597",
    "revman": "#000000",
    "bmj": "#6b58a6",
}

COUNT_BASED_DIAGNOSTIC_METHODS = {
    "diagnostic.reitsma",
}

SHARED_DIAGNOSTIC_PARAMS = (
    "conf.level",
    "digits",
    "adjust",
    "correction.policy",
    "estimator",
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
        "estimator": _normalize_parameter_definition(
            "estimator", ["REML", "ML"], "REML", None
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

    def __init__(self, owner, label, metric, label_widget, combo, param_box):
        self.owner = owner
        self.metric = metric
        self.params = {}
        self.widgets = []
        self.label = label_widget
        self.label.setText(label)
        self.combo = combo
        self.param_box = param_box
        owner._configure_method_selector(self.combo)
        self.param_box.setLayout(QGridLayout())
        self.combo.currentTextChanged.connect(
            app_error_handler.safe_slot(
                lambda _text: self._method_changed(), parent=owner
            )
        )

    @property
    def method(self):
        return self.methods[str(self.combo.currentText())]

    def populate(self):
        self.owner.analysis_service.prepare_method_dataset(
            self.owner.model, "diagnostic", var_name="tmp_obj"
        )
        self.methods = normalize_available_method_labels(
            self.owner.analysis_service.available_methods(
                for_data_type="diagnostic",
                data_obj_name="tmp_obj",
                metric=self.metric,
            )
        )
        names = [
            name
            for name in self.methods
            if self.methods[name] not in COUNT_BASED_DIAGNOSTIC_METHODS
        ]
        if "Diagnostic Fixed-Effect Peto" in names:
            names.remove("Diagnostic Fixed-Effect Peto")
        names.sort(reverse=True)
        blocked = self.combo.blockSignals(True)
        try:
            self.combo.clear()
            self.combo.addItems(names)
        finally:
            self.combo.blockSignals(blocked)
        self._method_changed()

    def _method_changed(self):
        for widget in self.widgets:
            self.param_box.layout().removeWidget(widget)
            widget.deleteLater()
        self.widgets = []
        self.params = {}
        method = self.method
        definitions, defaults, order, metadata = self.owner.analysis_service.parameters(
            method
        )
        self.param_box.setTitle(str(self.combo.currentText()))
        description = QLabel(
            "Description: %s" % self.owner.analysis_service.method_description(method)
        )
        description.setWordWrap(True)
        self.param_box.layout().addWidget(description, 0, 0, 1, 2)
        self.widgets.append(description)
        row = 1
        for name in order or definitions:
            spec = _normalize_parameter_definition(
                name, definitions[name], defaults.get(name), metadata.get(name)
            )
            if name in SHARED_DIAGNOSTIC_PARAMS:
                self.owner._register_shared_diagnostic_param(
                    spec,
                )
                continue
            label = self.owner._parameter_label(spec)
            control = self.owner._create_parameter_control(spec, self.params)
            self.owner._configure_parameter_accessibility(label, control)
            self.param_box.layout().addWidget(label, row, 0)
            self.param_box.layout().addWidget(control, row, 1)
            self.widgets.extend((label, control))
            row += 1
        self.owner._schedule_local_reflow()


class AnalysisSetupDialog(QDialog, Ui_AnalysisSetupDialog):
    correction_requested = QtCore.pyqtSignal(object)
    draft_changed = QtCore.pyqtSignal(object)

    def __init__(
        self,
        model,
        parent=None,
        analysis_type=None,
        external_params=None,
        diagnostic_metrics=None,
        diagnostic_analysis_details=None,
        fp_specs_only=False,
        confidence_level=None,
        analysis_service=None,
        analysis_worker=None,
        frozen_snapshot=None,
    ):

        super(AnalysisSetupDialog, self).__init__(parent)
        self.analysis_service = analysis_service or analysis_adapter.AnalysisService()
        self.analysis_worker = analysis_worker
        self._frozen_snapshot = frozen_snapshot
        self._worker_run_id = None
        self._worker_progress_dialog = None
        self.setupUi(self)
        self.setModal(False)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self._initialize_controls(external_params, analysis_type)
        self._initialize_analysis_state(
            model,
            confidence_level,
            diagnostic_metrics,
            diagnostic_analysis_details,
        )
        self._connect_dialog_actions()
        self._configure_data_family()
        self.populate_parameter_controls()
        if self._combined_diagnostic:
            self._finish_combined_diagnostic_ui()
        self._install_review_context()
        self._install_draft_tracking()
        adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )

    def _install_review_context(self):
        self.context_label = QLabel(self)
        self.context_label.setObjectName("analysisContextSummary")
        self.context_label.setAccessibleName("Analysis context")
        self.context_label.setWordWrap(True)
        self.context_label.setTextFormat(Qt.TextFormat.PlainText)
        self.verticalLayout.insertWidget(0, self.context_label)
        self._refresh_context_summary()
        self.worker_feedback = QLabel("Ready to review and run.", self)
        self.worker_feedback.setObjectName("analysisWorkerFeedback")
        self.worker_feedback.setAccessibleName("Analysis status")
        self.worker_feedback.setWordWrap(True)
        self.verticalLayout.insertWidget(1, self.worker_feedback)

        self.review_page = QtWidgets.QWidget(self)
        review_layout = QtWidgets.QVBoxLayout(self.review_page)
        self.review_text = QtWidgets.QTextBrowser(self.review_page)
        self.review_text.setObjectName("analysisScientificReview")
        self.review_text.setAccessibleName("Effective scientific settings before run")
        self.review_text.setOpenExternalLinks(False)
        self.review_text.setMaximumHeight(150)
        review_layout.addWidget(self.review_text)
        if self.analysis_type == "cumulative" and self._frozen_snapshot is not None:
            self._install_cumulative_order_controls(review_layout)
        self.review_issues_table = QtWidgets.QTableWidget(0, 5, self.review_page)
        self.review_issues_table.setObjectName("analysisDataIssues")
        self.review_issues_table.setAccessibleName("Data issues before analysis")
        self.review_issues_table.setHorizontalHeaderLabels(
            ("Study", "Field", "Value", "Problem", "Correction")
        )
        header = self.review_issues_table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
        review_layout.addWidget(self.review_issues_table)
        self.specs_tab.addTab(self.review_page, "Review")
        self.specs_tab.currentChanged.connect(self._review_tab_selected)
        run_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if run_button is not None:
            run_button.setText("Run analysis")
            run_button.setAccessibleName("Run analysis with the reviewed settings")
        cancel_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button is not None:
            cancel_button.setAccessibleName("Close setup and keep an unfinished draft")

    def _install_cumulative_order_controls(self, review_layout):
        controls = QtWidgets.QWidget(self.review_page)
        grid = QGridLayout(controls)
        grid.setContentsMargins(0, 0, 0, 0)
        self.cumulative_order_field = QComboBox(controls)
        self.cumulative_order_field.setAccessibleName("Cumulative study ordering field")
        self.cumulative_order_field.addItem("Project order", "project_order")
        self.cumulative_order_field.addItem("Study year", "year")
        self.cumulative_direction = QComboBox(controls)
        self.cumulative_direction.setAccessibleName("Cumulative study ordering direction")
        self.cumulative_direction.addItem("Ascending", "ascending")
        self.cumulative_direction.addItem("Descending", "descending")
        self.cumulative_missing_year = QComboBox(controls)
        self.cumulative_missing_year.setAccessibleName("Missing study year policy")
        self.cumulative_missing_year.addItem("Choose missing-year placement", None)
        self.cumulative_missing_year.addItem("Missing years first", "first")
        self.cumulative_missing_year.addItem("Missing years last", "last")
        grid.addWidget(QLabel("Order studies by", controls), 0, 0)
        grid.addWidget(self.cumulative_order_field, 0, 1)
        grid.addWidget(QLabel("Direction", controls), 1, 0)
        grid.addWidget(self.cumulative_direction, 1, 1)
        self.cumulative_missing_label = QLabel("Missing years", controls)
        grid.addWidget(self.cumulative_missing_label, 2, 0)
        grid.addWidget(self.cumulative_missing_year, 2, 1)
        self.verticalLayout.insertWidget(1, controls)
        self.cumulative_sequence_preview = QtWidgets.QTextBrowser(self.review_page)
        self.cumulative_sequence_preview.setAccessibleName("Cumulative analytical sequence")
        self.cumulative_sequence_preview.setMaximumHeight(140)
        review_layout.addWidget(self.cumulative_sequence_preview)
        for selector in (
            self.cumulative_order_field,
            self.cumulative_direction,
            self.cumulative_missing_year,
        ):
            selector.currentIndexChanged.connect(self._refresh_cumulative_sequence_preview)
        self._refresh_cumulative_sequence_preview()

    def _cumulative_snapshot(self):
        from rc_metastudio.cumulative_analysis import (
            CumulativeOrderSpec,
            freeze_cumulative_input,
        )

        field = self.cumulative_order_field.currentData()
        direction = self.cumulative_direction.currentData()
        missing = self.cumulative_missing_year.currentData() if field == "year" else None
        return freeze_cumulative_input(
            self._frozen_snapshot, CumulativeOrderSpec(field, direction, missing)
        )

    def _refresh_cumulative_sequence_preview(self):
        field = self.cumulative_order_field.currentData()
        has_missing_years = any(
            study.year is None for study in self._frozen_snapshot.studies
        )
        show_missing = field == "year" and has_missing_years
        self.cumulative_missing_label.setVisible(show_missing)
        self.cumulative_missing_year.setVisible(show_missing)
        try:
            snapshot = self._cumulative_snapshot()
        except ValueError as error:
            self.cumulative_sequence_preview.setPlainText(str(error))
            return
        lines = [
            "%d. %s · %s · %d included"
            % (
                step.order + 1,
                step.study_name,
                step.ordering_value if step.ordering_value is not None else "year missing",
                step.included_study_count,
            )
            for step in snapshot.sequence
        ]
        self.cumulative_sequence_preview.setPlainText("\n".join(lines))

    def _install_draft_tracking(self):
        self._draft_change_timer = QtCore.QTimer(self)
        self._draft_change_timer.setSingleShot(True)
        self._draft_change_timer.timeout.connect(self._emit_draft_change)
        for control_type in (
            QComboBox,
            QLineEdit,
            QSpinBox,
            QDoubleSpinBox,
            QtWidgets.QCheckBox,
            QtWidgets.QRadioButton,
        ):
            for control in self.findChildren(control_type):
                self._track_draft_control(control)

    def _track_draft_control(self, control):
        if getattr(control, "_rcms_draft_tracked", False):
            return
        control._rcms_draft_tracked = True
        if isinstance(control, QComboBox):
            control.currentIndexChanged.connect(self._queue_draft_change)
        elif isinstance(control, QLineEdit):
            control.textChanged.connect(self._queue_draft_change)
        elif isinstance(control, (QSpinBox, QDoubleSpinBox)):
            control.valueChanged.connect(self._queue_draft_change)
        elif isinstance(control, (QtWidgets.QCheckBox, QtWidgets.QRadioButton)):
            control.toggled.connect(self._queue_draft_change)

    def _queue_draft_change(self, *_args):
        self._draft_change_timer.start(250)

    def _emit_draft_change(self):
        self.draft_changed.emit(self.draft_payload())

    def draft_payload(self):
        """Return data-only editor state without machine-local plot output paths."""
        get_groups = getattr(self.model, "get_current_groups", None)
        get_follow_up = getattr(self.model, "get_current_follow_up_name", None)
        groups = list(get_groups()) if callable(get_groups) else []
        follow_up = get_follow_up() if callable(get_follow_up) else None
        try:
            add_plot_params(self)
        except ValueError:
            # Preserve the entered method controls even when figure settings
            # need correction before a run.
            pass
        parameters = {
            key: value
            for key, value in self.current_param_vals.items()
            if key not in {"fp_outpath", "fp_display_path", "bp_outpath", "bp_display_path"}
        }
        settings = {
            "analysis_type": self.analysis_type,
            "method": self.current_method or None,
            "parameters": parameters,
        }
        if self.analysis_type == "cumulative":
            from rc_metastudio.cumulative_analysis import CumulativeOrderSpec

            field = self.cumulative_order_field.currentData()
            settings["ordering"] = CumulativeOrderSpec(
                field,
                self.cumulative_direction.currentData(),
                self.cumulative_missing_year.currentData() if field == "year" else None,
            ).to_mapping()
        return {
            "selection": {
                "outcome": getattr(self.model, "current_outcome_name", None),
                "follow_up": follow_up,
                "groups": groups[:2],
                "effect": getattr(self.model, "current_effect", None),
            },
            "settings": settings,
        }

    def _refresh_context_summary(self):
        get_groups = getattr(self.model, "get_current_groups", None)
        groups = list(get_groups()) if callable(get_groups) else []
        get_follow_up = getattr(self.model, "get_current_follow_up_name", None)
        follow_up = get_follow_up() if callable(get_follow_up) else None
        direction = " versus ".join(str(group) for group in groups)
        self.context_label.setText(
            "Outcome: %s  ·  Time point: %s  ·  Direction: %s  ·  "
            "Measure: %s  ·  Analysis: %s"
            % (
                getattr(self.model, "current_outcome_name", None) or "Not selected",
                follow_up or "Not selected",
                direction or "Not selected",
                self.model.current_effect or "Not selected",
                (self.analysis_type or "standard").replace("-", " ").title(),
            )
        )

    def _review_tab_selected(self, index):
        if self.specs_tab.widget(index) is not self.review_page:
            return
        self._refresh_context_summary()
        try:
            requests = self.analysis_requests()
        except Exception as error:
            self.review_text.setPlainText(
                "The current analysis settings need attention: %s" % error
            )
            return
        study_count = len(self.model.get_studies(only_if_included=True))
        blocks = []
        for request in requests:
            parameters = {
                name: value
                for name, value in request.parameter_values().items()
                if not name.startswith(("fp_", "bp_"))
            }
            lines = [
                "Analysis: %s" % request.workflow.replace("-", " ").title(),
                "Method: %s" % request.method,
                "Measure: %s" % request.metric,
                "Included studies: %s" % study_count,
            ]
            lines.extend(
                "%s: %s" % (name, parameters[name])
                for name in sorted(parameters)
            )
            subgroup_plan = getattr(self, "_subgroup_plan", None)
            if request.workflow == "subgroup" and subgroup_plan is not None:
                lines.extend(
                    (
                        "Grouping variable: %s" % subgroup_plan.covariate_name,
                        "Missing-value policy: %s" % subgroup_plan.missing_policy,
                    )
                )
                affected = [
                    assignment
                    for assignment in subgroup_plan.assignments
                    if assignment.status == "excluded_missing"
                    or assignment.value is None
                    or assignment.value == ""
                ]
                if affected:
                    decision = (
                        "Excluded studies"
                        if subgroup_plan.missing_policy == "exclude"
                        else "Studies assigned to Missing values subgroup"
                    )
                    lines.append(
                        "%s: %s"
                        % (decision, ", ".join(row.study_name for row in affected))
                    )
                lines.append(
                    "Subgroup levels: %s"
                    % "; ".join(
                        "%s (%d)" % (level.label, level.included_count)
                        for level in subgroup_plan.levels
                    )
                )
            blocks.append("\n".join(lines))
        self.review_text.setPlainText("\n\n".join(blocks))
        self._refresh_data_issue_review(requests)

    def _refresh_data_issue_review(self, requests):
        table = self.review_issues_table
        table.setRowCount(0)
        if len(requests) != 1:
            return
        try:
            source = (
                "raw"
                if self.model.included_studies_have_raw_data()
                else "entered-effect"
            )
            review = data_issue_review.review_analysis_data(
                self.model, method_id=requests[0].method, input_source=source
            )
        except (AttributeError, KeyError, TypeError, ValueError):
            return
        self._latest_data_issue_review = review
        counts = {
            status: sum(study.status == status for study in review.studies)
            for status in ("included", "excluded", "missing", "invalid")
        }
        self.review_text.append(
            "\nData review: %d included · %d excluded · %d missing · %d invalid"
            % (
                counts["included"],
                counts["excluded"],
                counts["missing"],
                counts["invalid"],
            )
        )
        for study in review.studies:
            if study.status == "excluded":
                self.review_text.append(
                    "%s: %s" % (study.name, "; ".join(study.reasons))
                )
        for study in review.studies:
            for issue in study.issues:
                row = table.rowCount()
                table.insertRow(row)
                for column, value in enumerate(
                    (study.name, issue.field, issue.value, issue.problem)
                ):
                    table.setItem(
                        row,
                        column,
                        QtWidgets.QTableWidgetItem("" if value is None else str(value)),
                    )
                if issue.target is not None:
                    button = QtWidgets.QPushButton("Go to data", table)
                    button.clicked.connect(
                        lambda _checked=False, target=issue.target: self.correction_requested.emit(
                            target
                        )
                    )
                    table.setCellWidget(row, 4, button)
        if not review.issues:
            self.review_text.append("No unresolved data issues in included studies.")

    def _initialize_controls(self, external_params, analysis_type):
        self._hide_internal_plot_path_controls()
        # Method descriptions must reflow inside the adaptive viewport. An
        # outer horizontal scrollbar would hide the estimator control on
        # narrow first-use dialog sizes.
        self.content_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        # Keep nested content from exporting its unwrapped preferred width to
        # the outer scroll area. The controls still expand to the viewport.
        for widget in (
            self.content_scroll_area_widget,
            self.specs_tab,
            self.methods_tab,
            self.parameter_grp_box,
        ):
            # layout-audit: allow=content-overflow-control; reason=nested scroll content must negotiate down to its viewport
            widget.setMinimumWidth(0)
        # The parameter group contains the dynamic, wrapping content. Keep its
        # unwrapped size hint from widening the whole tab, while leaving the
        # method selector's own preferred width available to the outer grid.
        self.parameter_grp_box.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            self.parameter_grp_box.sizePolicy().verticalPolicy(),
        )
        self.gridLayout.setColumnStretch(0, 0)
        self.gridLayout.setColumnStretch(1, 1)
        self._layout_reflow_pending = False
        self._layout_reflow_timer = QtCore.QTimer(self)
        self._layout_reflow_timer.setSingleShot(True)
        self._layout_reflow_timer.timeout.connect(self._apply_local_reflow)
        self._focus_reveal_connected = False
        for combo in self.findChildren(QComboBox):
            self._configure_value_control(combo)
        apply_plot_text_input_limits(self)
        apply_default_forest_arm_labels(self)
        if _text_value(self.image_path) == "":
            self.image_path.setText(analysis_output_path("forest.png"))
        self.current_param_vals: dict[str, object] = dict(external_params or {})
        self.analysis_type = analysis_type
        self.is_meta_regression = analysis_type == "meta-regression"
        self._loading_plot_style = False
        self._setup_plot_controls()
        self._load_plot_params()

    def _initialize_analysis_state(
        self, model, confidence_level, diagnostic_metrics, diagnostic_analysis_details
    ):
        self.model = model
        if confidence_level is None:
            raise ValueError("CONFIDENCE LEVEL MUST BE SPECIFIED")
        self.confidence_level = validate_confidence_level(confidence_level)
        self.data_type = self.model.get_current_outcome_type()
        self.current_widgets = []
        self.current_method = ""
        self.current_params: dict[str, object] = {}
        self.current_defaults: dict[str, object] = {}
        self.param_d: dict[str, object] = {}
        self.var_order: list[str] | None = None
        self.diagnostic_analysis_details = diagnostic_analysis_details or {}
        self.diagnostic_metrics = tuple(diagnostic_metrics or ())
        self._combined_diagnostic = False
        self._shared_diagnostic_param_specs = _shared_diagnostic_specs(
            self.confidence_level
        )
        self._shared_diagnostic_widgets = []

    def _connect_dialog_actions(self):
        self._accepted_connection = None
        self._set_accepted_handler(
            self.run_meta_regression if self.is_meta_regression else self.run_ma
        )
        self.buttonBox.rejected.connect(
            app_error_handler.safe_slot(self.cancel, parent=self)
        )
        self.save_btn.pressed.connect(
            app_error_handler.safe_slot(self.select_out_path, parent=self)
        )
        self._configure_method_selector(self.method_cbo_box)
        self.method_cbo_box.currentTextChanged.connect(
            app_error_handler.safe_slot(
                lambda _text: self.method_changed(), parent=self
            )
        )

    def _configure_data_family(self):
        self._setup_covariates_tab()
        if self.data_type != "binary":
            self.disable_bin_only_fields()
            if self.data_type == "diagnostic":
                self.enable_diagnostic_fields()

        # disable second arm display for one-arm analyses
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

    def _hide_internal_plot_path_controls(self):
        """Keep generated output paths out of the researcher-facing form."""
        for widget in (self.label_3, self.image_path, self.save_btn):
            widget.hide()

    def sizeHint(self):
        """Include the scroll body's content width in first-use negotiation."""
        hint = super(AnalysisSetupDialog, self).sizeHint()
        if hasattr(self, "specs_tab"):
            content_hint = self.specs_tab.minimumSizeHint()
            if content_hint.isValid():
                root_layout = self.layout()
                if root_layout is None:
                    return hint
                margins = root_layout.contentsMargins()
                scrollbar = self.content_scroll_area.verticalScrollBar()
                if scrollbar is None:
                    return hint
                scrollbar_width = scrollbar.sizeHint().width()
                method_width = 0
                if hasattr(self, "method_cbo_box"):
                    method_width = self.method_cbo_box.sizeHint().width()
                    if hasattr(self, "method_lbl"):
                        method_width += self.method_lbl.sizeHint().width()
                    if hasattr(self, "gridLayout"):
                        method_width += self.gridLayout.horizontalSpacing()
                hint.setWidth(
                    max(
                        hint.width(),
                        max(content_hint.width(), method_width)
                        + margins.left()
                        + margins.right()
                        + scrollbar_width,
                    )
                )
        return hint

    def showEvent(  # ty: ignore[invalid-method-override] -- PyQt6 multiple-inheritance stub mismatch
        self, event: QShowEvent | None
    ) -> None:
        super(AnalysisSetupDialog, self).showEvent(event)
        self._refresh_context_summary()
        app = QtWidgets.QApplication.instance()
        if isinstance(app, QtWidgets.QApplication) and not self._focus_reveal_connected:
            app.focusChanged.connect(self._reveal_focused_control)
            self._focus_reveal_connected = True

    def hideEvent(  # ty: ignore[invalid-method-override] -- PyQt6 multiple-inheritance stub mismatch
        self, event: QHideEvent | None
    ) -> None:
        self._disconnect_focus_reveal()
        super(AnalysisSetupDialog, self).hideEvent(event)

    def closeEvent(  # ty: ignore[invalid-method-override] -- PyQt6 multiple-inheritance stub mismatch
        self, event: QCloseEvent | None
    ) -> None:
        if self._worker_run_id is not None and event is not None:
            event.ignore()
            return
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
        if self._worker_run_id is not None:
            return
        self.reject()

    def _setup_covariates_tab(self):
        if not self.is_meta_regression:
            self.specs_tab.removeTab(self.specs_tab.indexOf(self.covariates_tab))
            self.regression_group.hide()
            return

        self.covs_and_check_boxes = []
        for row, covariate in enumerate(self.model.dataset.covariates):
            checkbox = QtWidgets.QCheckBox(covariate.name, self.covariate_group_box)
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
        self.diagnostic_regression_group.setVisible(self.data_type == "diagnostic")
        self.image_path.setText(analysis_output_path("reg.png"))
        self._update_meta_regression_ok()
        self._update_meta_regression_plot_availability()

    def _selected_covariates(self):
        return [
            covariate
            for covariate, checkbox in self.covs_and_check_boxes
            if checkbox.isChecked()
        ]

    def _update_meta_regression_ok(self):
        button = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if button is not None:
            button.setEnabled(bool(self._selected_covariates()))

    def _update_meta_regression_plot_availability(self):
        if not self.is_meta_regression:
            return
        selected = self._selected_covariates()
        bubble_available = len(selected) == 1 and selected[0].data_type == CONTINUOUS
        self.plot_tab.setEnabled(bubble_available)
        self.plot_tab.setToolTip(
            ""
            if bubble_available
            else "Bubble plot options require exactly one continuous covariate."
        )

    def _set_accepted_handler(self, handler):
        if self._accepted_connection is None:
            self._accepted_connection = app_error_handler.connect_safely(
                self.buttonBox.accepted, handler, parent=self
            )
        else:
            self._accepted_connection.replace(handler, parent=self)

    def select_out_path(self):
        out_f = "."
        out_f, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "RCMetaStudio - Plot Path",
            out_f,
            "png image files: (.png)",
        )
        if out_f == "" or out_f is None:
            return None
        else:
            self.image_path.setText(out_f)

    def _setup_plot_controls(self):
        self.color_btn.clicked.connect(
            app_error_handler.safe_slot(self._choose_plot_color, parent=self)
        )
        self.style_cbo.currentTextChanged.connect(
            app_error_handler.safe_slot(self._plot_style_changed, parent=self)
        )

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
        self.plot_tab.setEnabled(
            any(capability["styleable"] for capability in capabilities)
        )
        self._update_meta_regression_plot_availability()

    def run_meta_regression(self):
        try:
            selected_covariates = self._selected_covariates()
            if not selected_covariates:
                QMessageBox.warning(
                    self,
                    "No Covariates Selected",
                    "Select at least one covariate before running meta-regression.",
                )
                return

            selection = self.analysis_service.select_studies_for_covariates(
                self.model, selected_covariates
            )
            if selection.has_missing_values and not self._confirm_excluded_studies(
                selection.excluded_study_names
            ):
                return
            request = self._meta_regression_request()
            fixed_effects = self.fixed_effects_radio.isChecked()
        except Exception as error:
            self._show_analysis_failure(error)
            return

        self._run_analysis(
            lambda: self.analysis_service.execute_meta_regression(
                self.model,
                selection.studies,
                tuple(selected_covariates),
                request,
                fixed_effects,
                self.confidence_level,
            ),
            string_result_is_failure=True,
            requests=(request,),
        )

    def _confirm_excluded_studies(self, names):
        excluded = ", ".join(names)
        excluded_text = ""
        if excluded:
            excluded_text = f"\nThe following studies will be excluded: {excluded}"
        choice = QMessageBox.warning(
            self,
            "Missing Covariate Values",
            "Some studies do not have values for the selected covariates. "
            f"{excluded_text}\nRun the regression without those studies?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return choice != QMessageBox.StandardButton.No

    def _meta_regression_metric(self):
        if self.data_type != "diagnostic":
            return self.model.current_effect
        if self.is_meta_regression or self.sensitivity_radio.isChecked():
            return "Sens"
        return "Spec" if self.specificity_radio.isChecked() else "DOR"

    def _meta_regression_request(self):
        metric = self._meta_regression_metric()
        add_plot_params(self)
        parameters = copy.deepcopy(self.current_param_vals)
        parameters["measure"] = metric
        if self.data_type == "diagnostic" and self.is_meta_regression:
            parameters["joint.metrics"] = "Sens,Spec"
        method = (
            "diagnostic.reitsma"
            if self.data_type == "diagnostic"
            else "meta.regression"
        )
        return self.analysis_service.make_request(
            data_type=self.data_type,
            workflow="meta-regression",
            method=method,
            metric=metric,
            parameters=parameters,
        )

    def _load_plot_params(self):
        self._loading_plot_style = True
        try:
            prefix = "bp" if self.is_meta_regression else "fp"
            style = _normalized_plot_style(
                self.current_param_vals.get("%s_style" % prefix, "default")
            )
            self.style_cbo.setCurrentText(PLOT_STYLE_LABELS[style])
            self._set_plot_accent_color(
                self.current_param_vals.get("%s_accent_color" % prefix)
                or PLOT_STYLE_DEFAULT_COLORS[style]
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
                        self.current_param_vals.get("bp_show_legend"), False
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
        finally:
            self._loading_plot_style = False

    def _plot_style_changed(self, label):
        if self._loading_plot_style:
            return
        style = PLOT_STYLE_VALUES.get(str(label), "default")
        self._set_plot_accent_color(PLOT_STYLE_DEFAULT_COLORS[style])

    def _choose_plot_color(self):
        current = QColor(self.accent_color.text())
        color = QtWidgets.QColorDialog.getColor(current, self, "Plot Accent Color")
        if color.isValid():
            self._set_plot_accent_color(color.name())

    def _set_plot_accent_color(self, color):
        text = str(color or PLOT_STYLE_DEFAULT_COLORS["default"])
        self.accent_color.setText(text)
        self.color_btn.setStyleSheet("background-color: %s;" % text)

    def run_ma(self):
        try:
            requests = self.analysis_requests()
        except Exception as error:
            self._show_analysis_failure(error)
            return

        self._run_analysis(
            lambda: self.analysis_service.execute(self.model, requests),
            requests=requests,
        )

    def _run_analysis(
        self,
        operation,
        string_result_is_failure=False,
        requests=(),
    ):
        if (
            self.analysis_worker is not None
            and len(requests) == 1
            and requests[0].data_type in ("binary", "continuous", "diagnostic")
            and requests[0].workflow
            in ("standard", "cumulative", "leave-one-out", "subgroup")
        ):
            self._run_isolated_standard_analysis(requests[0])
            return

        bar = progress_dialog.AnalysisProgressDialog(self)
        bar.show()
        result = None
        primary_failure_metric = None
        primary_failure_detail = None
        failed = False
        try:
            result = operation()
            if string_result_is_failure and isinstance(result, str):
                raise RuntimeError(result)
            primary_failure = _primary_reitsma_fit_failure(result, requests)
            if primary_failure is not None:
                primary_failure_metric, primary_failure_detail = primary_failure
                raise RuntimeError(primary_failure_detail)
        except Exception as error:
            failed = True
            app_error_handler.log_exception(type(error), error, error.__traceback__)
            if isinstance(error, PrimaryDiagnosticFitError):
                primary_failure_metric = error.metric
            self._show_analysis_failure(
                error,
                requests=requests,
                primary_failure_metric=primary_failure_metric,
            )
            self._reset_working_dir_safely()
        finally:
            _dispose_progress(bar)

        if failed:
            return

        try:
            delivered = self._deliver_result(result)
        except Exception as error:
            app_error_handler.log_exception(type(error), error, error.__traceback__)
            self._show_analysis_failure(
                error, requests=requests, result_delivery_failed=True
            )
            self._reset_working_dir_safely()
            return
        if not delivered:
            return

        self.done(QDialog.DialogCode.Accepted.value)

    def _run_isolated_standard_analysis(self, request):
        try:
            base_snapshot = self._frozen_snapshot
            if request.metric != base_snapshot.metric:
                raise ValueError("The selected measure changed. Reopen analysis setup to review its inputs.")
            snapshot = (
                self._cumulative_snapshot()
                if request.workflow == "cumulative"
                else base_snapshot
            )
            if request.data_type == "binary":
                input_source = "raw" if base_snapshot.raw_counts_available else "entered-effect"
            elif request.data_type == "continuous":
                input_source = "raw" if base_snapshot.raw_measurements_complete else "entered-effect"
            else:
                input_source = "raw" if base_snapshot.input_source == "counts" else "entered-effect"
            review = data_issue_review.review_analysis_data(
                self.model,
                method_id=request.method,
                input_source=input_source,
            )
            if not review.is_ready:
                self.specs_tab.setCurrentWidget(self.review_page)
                self.review_text.append(
                    "Resolve the listed data issues before running this analysis."
                )
                self.worker_feedback.setText("Data issues require correction before this analysis can run.")
                (self.review_issues_table if review.issues else self.review_text).setFocus()
                return
            run_id = self.parentWidget().submit_standard_analysis(
                self, snapshot, request
            )
            if run_id is None:
                return
        except Exception as error:
            self._show_analysis_failure(error, requests=(request,))
            return
        self._worker_run_id = run_id
        self.worker_feedback.setText("Analysis running. Use Stop analysis to keep these settings.")
        self._worker_progress_dialog = progress_dialog.AnalysisProgressDialog(self)
        self._worker_progress_dialog.set_stage("Starting analysis engine")
        self._worker_progress_dialog.stop_requested.connect(
            self._stop_isolated_analysis
        )
        self._worker_progress_dialog.show()
        self._worker_progress_dialog.stop_button.setFocus()

    def _stop_isolated_analysis(self):
        if self._worker_run_id is not None and self.analysis_worker is not None:
            self.analysis_worker.stop()

    def _worker_progress(self, run_id, stage):
        if run_id != self._worker_run_id or self._worker_progress_dialog is None:
            return
        self._worker_progress_dialog.set_stage(stage)

    def _worker_failed(self, run_id, error):
        if run_id != self._worker_run_id:
            return
        if self._worker_progress_dialog is not None:
            self._worker_progress_dialog.hide()
            self._worker_progress_dialog.deleteLater()
            self._worker_progress_dialog = None
        self._worker_run_id = None
        if error.get("type") != "AnalysisStoppedError":
            self.worker_feedback.setText("Analysis failed. Settings remain open for correction and retry.")
            self._show_worker_failure(error)
        else:
            self.worker_feedback.setText("Analysis stopped. Settings remain open for retry.")
            run_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
            if run_button is not None:
                run_button.setFocus()

    def _show_worker_failure(self, error):
        message = QMessageBox(self)
        message.setIcon(QMessageBox.Icon.Critical)
        message.setWindowTitle("Analysis Engine Unavailable")
        message.setText(str(error.get("message", "The analysis could not be completed.")))
        message.setInformativeText(
            "Your settings and selected inputs are still open. Check the analysis "
            "engine installation, then select OK to retry."
        )
        details = "{}: {}".format(error.get("type", "AnalysisWorkerError"), error.get("message", ""))
        if error.get("details"):
            details += "\n\n" + str(error["details"])
        message.setDetailedText("Technical details:\n" + details)
        message.setStandardButtons(QMessageBox.StandardButton.Ok)
        message.exec()
        run_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if run_button is not None:
            run_button.setFocus()

    def _worker_completed(self, run_id, delivered, warnings=()):
        if run_id != self._worker_run_id:
            return
        if self._worker_progress_dialog is not None:
            self._worker_progress_dialog.hide()
            self._worker_progress_dialog.deleteLater()
            self._worker_progress_dialog = None
        self._worker_run_id = None
        if not delivered:
            self.worker_feedback.setText(
                "The result could not be delivered. Settings remain open for review and retry."
            )
            run_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
            if run_button is not None:
                run_button.setFocus()
            return
        self.worker_feedback.setText("Analysis completed. The result is in the workspace history.")
        if warnings:
            QMessageBox.warning(
                self,
                "Analysis Completed with Warnings",
                "The analysis completed with these warnings:\n\n%s"
                % "\n".join(str(item) for item in warnings),
            )
        self.done(QDialog.DialogCode.Accepted.value)

    def _show_analysis_failure(
        self,
        error,
        *,
        requests=(),
        primary_failure_metric=None,
        result_delivery_failed=False,
    ):
        details = [f"{type(error).__name__}: {error}"]
        if isinstance(error, PrimaryDiagnosticFitError):
            details.append(
                "Primary fit: %s / %s / %s"
                % (error.workflow, error.method, error.metric)
            )
        if requests:
            details.append("Effective analysis requests:")
            for request in requests:
                details.append(
                    "%s / %s / %s / %s\nSettings: %r"
                    % (
                        request.data_type,
                        request.workflow,
                        request.method,
                        request.metric,
                        request.parameter_values(),
                    )
                )

        if primary_failure_metric is not None:
            title = f"The requested {primary_failure_metric} Reitsma fit failed."
            informative = (
                "No alternate estimator was fitted. Your selected measures and settings "
                "are still here. Review the Reitsma estimator and zero-cell correction "
                "settings, then close this message and select OK to retry."
            )
        elif result_delivery_failed:
            title = "The analysis completed, but its results could not be displayed."
            informative = (
                "Your selected measures and settings are still here. Close this message, "
                "review the technical details, and select OK to retry."
            )
        else:
            title = "The analysis could not be completed."
            informative = (
                "Your selected measures and settings are still here. Check the method "
                "and input data, then close this message and select OK to retry."
            )

        message = QMessageBox(self)
        message.setIcon(QMessageBox.Icon.Critical)
        message.setWindowTitle("Analysis Failed")
        message.setText(title)
        message.setInformativeText(informative)
        message.setDetailedText("Technical details:\n" + "\n".join(details))
        message.setStandardButtons(QMessageBox.StandardButton.Ok)
        message.exec()
        run_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if run_button is not None:
            run_button.setFocus()

    def done(  # ty: ignore[invalid-method-override] -- PyQt6 generated-form multiple inheritance
        self, result: int
    ) -> None:
        self._release_owned_connections()
        super().done(result)
        self.deleteLater()

    def _reset_working_dir_safely(self):
        try:
            self.analysis_service.reset_working_directory()
        except Exception:
            pass

    def _release_owned_connections(self) -> None:
        self._disconnect_focus_reveal()
        self._layout_reflow_timer.stop()
        try:
            self._layout_reflow_timer.timeout.disconnect(self._apply_local_reflow)
        except (TypeError, RuntimeError):
            pass

    def _deliver_result(self, result, *, context=None, edit_copy_spec=None):
        parent = self.parentWidget()
        callback = getattr(parent, "analysis", None)
        if not callable(callback):
            raise RuntimeError("analysis configuration has no results owner")
        if context is None and edit_copy_spec is None:
            return callback(result) is not False
        return callback(
            result, context=context, edit_copy_spec=edit_copy_spec
        ) is not False

    def analysis_requests(self):
        """Return typed requests represented by the current user configuration."""
        add_plot_params(self)
        workflow = self.analysis_type or "standard"
        if self.data_type != "diagnostic":
            metric = str(self.model.current_effect)
            self.current_param_vals["measure"] = metric
            parameters = copy.deepcopy(self.current_param_vals)
            return (
                self.analysis_service.make_request(
                    data_type=self.data_type,
                    workflow=workflow,
                    method=self.current_method,
                    metric=metric,
                    parameters=parameters,
                ),
            )

        if self.analysis_worker is not None and self._frozen_snapshot is not None:
            metric = self._frozen_snapshot.metric
            self.current_param_vals["measure"] = metric
            return (
                self.analysis_service.make_request(
                    data_type="diagnostic",
                    workflow=workflow,
                    method=self.current_method,
                    metric=metric,
                    parameters=copy.deepcopy(self.current_param_vals),
                ),
            )

        self.add_current_analysis_details()
        method_names, parameter_values = _diagnostic_analysis_requests(self)
        return tuple(
            self.analysis_service.make_request(
                data_type=self.data_type,
                workflow=workflow,
                method=method,
                metric=str(parameters["measure"]),
                parameters=parameters,
            )
            for method, parameters in zip(method_names, parameter_values)
        )

    def enable_diagnostic_fields(self):
        self.col3_str_edit.setText("[default]")
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
        self.clear_param_ui()
        self.current_widgets = []
        if self.available_method_d is None:
            raise RuntimeError("Analysis methods have not been initialized")
        self.current_method = self.available_method_d[
            str(self.method_cbo_box.currentText())
        ]
        self.setup_params()
        self._set_parameter_box_title(self.method_cbo_box, self.parameter_grp_box)
        self.ui_for_params(
            excluded_names=SHARED_DIAGNOSTIC_PARAMS if self._combined_diagnostic else ()
        )
        self._schedule_local_reflow()

    def _set_parameter_box_title(self, cbo_box, param_box):
        param_box.setTitle(str(cbo_box.currentText()))

    def populate_parameter_controls(self, cbo_box=None, param_box=None):
        if cbo_box is None:
            cbo_box = self.method_cbo_box
            param_box = self.parameter_grp_box

        tmp_obj_name = "tmp_obj"
        self.analysis_service.prepare_method_dataset(
            self.model, self.data_type, var_name=tmp_obj_name
        )
        metric = self._method_query_metric()
        method_query = {
            "for_data_type": self.data_type,
            "data_obj_name": tmp_obj_name,
            "metric": metric,
        }
        if self.analysis_type is not None:
            method_query["workflow"] = self.analysis_type
        self.available_method_d = self.analysis_service.available_methods(
            **method_query
        )
        self.available_method_d = normalize_available_method_labels(
            self.available_method_d
        )
        method_names = self._available_method_names(metric)
        self._populate_method_combo(cbo_box, method_names)
        self.current_method = self.available_method_d[str(cbo_box.currentText())]
        self.setup_params()
        self._set_parameter_box_title(cbo_box, param_box)
        if cbo_box is self.method_cbo_box:
            excluded = SHARED_DIAGNOSTIC_PARAMS if self._combined_diagnostic else ()
            self.ui_for_params(excluded_names=excluded)

    def _method_query_metric(self):
        if self.data_type != "diagnostic":
            return self.model.current_effect
        if self.analysis_type is not None or self.sens_spec:
            return "Sens"
        return "DOR"

    def _available_method_names(self, metric):
        method_names = list(self.available_method_d.keys())
        reitsma_name = "Reitsma bivariate model"
        if self.data_type == "diagnostic" and not self.is_meta_regression:
            self._remove_unavailable_diagnostic_methods(
                method_names, metric, reitsma_name
            )
        method_names.sort(reverse=True)
        if self._reitsma_is_available(method_names, reitsma_name):
            method_names.remove(reitsma_name)
            method_names.insert(0, reitsma_name)
        return method_names

    def _remove_unavailable_diagnostic_methods(
        self, method_names, metric, reitsma_name
    ):
        if self._hide_reitsma(metric) and reitsma_name in method_names:
            method_names.remove(reitsma_name)
        peto_method = "Diagnostic Fixed-Effect Peto"
        has_required_metrics = all(
            name in self.diagnostic_metrics for name in ("lr", "dor")
        )
        if has_required_metrics and peto_method in method_names:
            method_names.remove(peto_method)

    def _reitsma_is_available(self, method_names, reitsma_name):
        return (
            self.data_type == "diagnostic"
            and not self.is_meta_regression
            and reitsma_name in method_names
        )

    def _hide_reitsma(self, metric):
        if metric != "Sens" or self.analysis_type is not None:
            return True
        if not {"sens", "spec"}.issubset(self.diagnostic_metrics):
            return True
        method = self.available_method_d.get("Reitsma bivariate model")
        return method in COUNT_BASED_DIAGNOSTIC_METHODS and not (
            self.model.included_studies_have_raw_data()
        )

    @staticmethod
    def _populate_method_combo(cbo_box, method_names):
        signals_were_blocked = cbo_box.blockSignals(True)
        try:
            for method in method_names:
                cbo_box.addItem(method)
        finally:
            cbo_box.blockSignals(signals_were_blocked)

    def clear_param_ui(self):
        parameter_layout = self.parameter_grp_box.layout()
        for widget in self.current_widgets:
            if parameter_layout is not None:
                parameter_layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()
            widget = None

    def ui_for_params(self, adjust_root=True, excluded_names=()):
        self._configure_plot_option_groups()
        parameter_layout = self._parameter_layout()
        method_description = self.analysis_service.method_description(
            self.current_method
        )
        self.add_method_description(
            parameter_layout, 0, "Description: %s" % method_description
        )
        self._add_parameter_controls(
            parameter_layout, self._ordered_parameter_definitions(), excluded_names
        )
        self._schedule_local_reflow()

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

    def _add_parameter_controls(self, layout, definitions, excluded_names):
        row = 1
        for spec in definitions:
            if spec.name in excluded_names:
                self._register_shared_diagnostic_param(spec)
                continue
            label = self._parameter_label(spec)
            control = self._create_parameter_control(spec, self.current_param_vals)
            self._configure_parameter_accessibility(label, control)
            self.current_widgets.extend((label, control))
            layout.addWidget(label, row, 0)
            layout.addWidget(control, row, 1)
            row += 1

    def _parameter_label(self, spec):
        label = QLabel(parameter_display_label(spec.name, spec.metadata))
        description = parameter_description(spec.name, spec.metadata)
        if spec.name == "estimator" and description == "No description provided.":
            description = "REML: restricted maximum likelihood; ML: maximum likelihood."
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
        if spec.kind == "enum":
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
                target[spec.name] = self._enum_item_value(control.currentData())
            combo = control
            control.currentIndexChanged[int].connect(
                app_error_handler.safe_slot(
                    lambda index: target.__setitem__(
                        spec.name, self._enum_item_value(combo.itemData(index))
                    ),
                    parent=self,
                )
            )
        elif spec.kind == "int":
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
        elif spec.kind == "float":
            control = QDoubleSpinBox()
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
            if hasattr(self, "_draft_change_timer"):
                self._track_draft_control(control)
            return control

        if isinstance(control, QComboBox):
            self._configure_value_control(control)
        else:
            adaptive_controls.configure_numeric_value_control(control)
        if hasattr(self, "_draft_change_timer"):
            self._track_draft_control(control)
        return control

    def _find_enum_item_index(self, cbo_box, value):
        for index in range(cbo_box.count()):
            if self._enum_item_value(cbo_box.itemData(index)) == str(value):
                return index
        return -1

    def _enum_item_value(self, item_data):
        if hasattr(item_data, "value"):
            item_data = item_data.value()
        return qt_text.to_native_text(item_data)

    def add_method_description(self, layout, current_grid_row, text):
        lbl = QLabel(text, self.parameter_grp_box)
        lbl.setWordWrap(True)
        # layout-audit: allow=content-overflow-control; reason=required content may consume available layout width
        lbl.setMinimumWidth(0)
        # QLabel's preferred width is the unwrapped text width. Ignored keeps
        # that width out of QGridLayout's minimum while retaining word-wrap.
        lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.current_widgets.append(lbl)
        layout.addWidget(lbl, current_grid_row, 0, 1, 2)

    def _configure_value_control(self, widget):
        adaptive_controls.configure_choice_control(widget)
        # The popup keeps complete enum values; the inline editor must still
        # negotiate down to the method panel's available width.
        # layout-audit: allow=content-overflow-control; reason=choice popup preserves complete values while the inline editor reflows
        widget.setMinimumWidth(0)
        widget.setSizePolicy(
            QSizePolicy.Policy.Ignored, widget.sizePolicy().verticalPolicy()
        )

    def _configure_method_selector(self, widget):
        adaptive_controls.configure_choice_control(widget, visible_characters=28)
        # Unlike parameter editors, the primary method selector determines the
        # dialog's useful preferred width and must keep its readable size hint.
        widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, widget.sizePolicy().verticalPolicy()
        )

    def _schedule_local_reflow(self):
        """Coalesce dynamic content negotiation without resizing the root window."""
        if self._layout_reflow_pending:
            return
        self._layout_reflow_pending = True
        self._layout_reflow_timer.start(0)

    def _apply_local_reflow(self):
        self._layout_reflow_pending = False
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
        self._reveal_focused_control(None, QtWidgets.QApplication.focusWidget())

    def _reveal_focused_control(self, _old, focused):
        if focused is not None and self.content_scroll_area.isAncestorOf(focused):
            self.content_scroll_area.ensureWidgetVisible(focused)

    def setup_params(self):
        # parses out information about the parameters of the current method
        # param_d holds (meta) information about the parameter -- it's a each param
        # itself maps to a dictionary with a pretty name and description (assuming
        # they were provided for the given param)
        self.current_params, self.current_defaults, self.var_order, self.param_d = (
            self.analysis_service.parameters(self.current_method)
        )

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

    def _register_shared_diagnostic_param(self, spec):
        if spec.name not in SHARED_DIAGNOSTIC_PARAMS:
            return
        existing = self._shared_diagnostic_param_specs[spec.name]
        self._shared_diagnostic_param_specs[spec.name] = replace(
            existing, metadata=spec.metadata or existing.metadata
        )
        if (
            hasattr(self, "shared_diagnostic_params_box")
            and self.shared_diagnostic_params_box.layout() is not None
        ):
            self._rebuild_shared_diagnostic_params()

    def _finish_combined_diagnostic_ui(self):
        self.setWindowTitle("Method & Parameters")
        self.method_lbl.setText(diagnostic_metric_group_display_label("sens_spec"))

        self.shared_diagnostic_params_box.show()
        self.shared_diagnostic_params_box.setLayout(QGridLayout())

        lr_label = diagnostic_metric_group_display_label("lr_dor")
        self.lr_dor_method_lbl.show()
        self.lr_dor_method_cbo_box.show()
        self.lr_dor_parameter_grp_box.show()
        self.lr_dor_panel = _DiagnosticMethodPanel(
            self,
            lr_label,
            "DOR",
            self.lr_dor_method_lbl,
            self.lr_dor_method_cbo_box,
            self.lr_dor_parameter_grp_box,
        )
        self.lr_dor_panel.populate()
        self._rebuild_shared_diagnostic_params()

    def _rebuild_shared_diagnostic_params(self):
        layout = self.shared_diagnostic_params_box.layout()
        if not isinstance(layout, QGridLayout):
            raise RuntimeError("Shared diagnostic parameters require a grid layout")
        for widget in self._shared_diagnostic_widgets:
            layout.removeWidget(widget)
            widget.deleteLater()
        self._shared_diagnostic_widgets = []

        for row, name in enumerate(SHARED_DIAGNOSTIC_PARAMS):
            spec = self._shared_diagnostic_param_specs.get(name)
            if spec is None:
                continue
            value = self.current_param_vals.get(name, spec.default)
            spec = replace(spec, default=value)
            label = self._parameter_label(spec)
            control = self._create_parameter_control(spec, self.current_param_vals)
            self._configure_parameter_accessibility(label, control)
            layout.addWidget(label, row, 0)
            layout.addWidget(control, row, 1)
            self._shared_diagnostic_widgets.extend((label, control))

    def add_current_analysis_details(self):
        """This method only applicable for diagnostic data, wherein
        we have multiple metrics. here the parameters/method for
        these metrics are added to a dictionary.
        """
        # this was extracted earlier, ultimately from the checkboxes
        # selected by the user
        metrics_to_run = list(self.diagnostic_analysis_details.keys())

        if self._combined_diagnostic:
            first_params = self._diagnostic_params_for_method(
                self.current_method, self.current_param_vals
            )
            second_params = self._diagnostic_params_for_method(
                self.lr_dor_panel.method, self.lr_dor_panel.params
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

    def _diagnostic_params_for_method(self, method, local_params):
        definitions, _defaults, _order, _metadata = self.analysis_service.parameters(
            method
        )
        params = _plot_parameter_values(self.current_param_vals)
        shared = set(definitions).intersection(SHARED_DIAGNOSTIC_PARAMS)
        params.update(_present_values(shared, self.current_param_vals))
        local_names = set(definitions).difference(SHARED_DIAGNOSTIC_PARAMS)
        params.update(_present_values(local_names, local_params))
        # Subgroup selection is workflow state, not a method parameter. Keep it
        # on each filtered request so combined diagnostic panels use the same
        # subgroup while retaining per-method parameter filtering above.
        if "cov_name" in self.current_param_vals:
            params["cov_name"] = self.current_param_vals["cov_name"]
        return params

    def setup_diagnostic_ui(self):
        if len(self.diagnostic_analysis_details) == 0:
            metrics_to_run = []
            for m in self.diagnostic_metrics:
                metrics_to_run.extend(DIAGNOSTIC_METRIC_GROUPS[m])

            self.diagnostic_analysis_details = dict(
                list(zip(metrics_to_run, [None for m in metrics_to_run]))
            )

        # Reflect the selected method in the dialog labels.
        window_title, method_label = "", ""
        if self.is_meta_regression:
            # Diagnostic Reitsma meta-regression always models both sides.
            # The legacy univariate effect radios would otherwise advertise a
            # DOR request that still dispatches to the joint model.
            self.diagnostic_regression_group.hide()
            # Reitsma meta-regression estimates its joint random-effects model
            # directly.  The legacy fixed/random-effects selector is not a
            # parameter of this model and must not remain visible or imply
            # that fixed effects can be requested.
            self.regression_model_group.hide()
            window_title = "Reitsma Meta-Regression"
            method_label = "Reitsma bivariate model"
        elif self.analysis_worker is not None and self._frozen_snapshot is not None:
            metric_label = DIAGNOSTIC_METRIC_LABELS[
                self._frozen_snapshot.metric
            ]
            window_title = "Method & Parameters for %s" % metric_label
            method_label = "Method for %s" % metric_label
        elif self._combined_diagnostic:
            window_title = "Method & Parameters"
            method_label = diagnostic_metric_group_display_label("sens_spec")
        elif self.sens_spec:
            metric_group_label = diagnostic_metric_group_display_label("sens_spec")
            window_title = "Method & Parameters for %s" % metric_group_label
            method_label = "Method for %s" % metric_group_label
        else:
            metric_group_label = diagnostic_metric_group_display_label("lr_dor")
            window_title = "Method & Parameters for %s" % metric_group_label
            method_label = "Method for %s" % metric_group_label

        self.setWindowTitle(QtCore.QCoreApplication.translate("Dialog", window_title))
        self.method_lbl.setText(method_label)
        if self.data_type == "diagnostic" and not self._combined_diagnostic:
            # Keep the truthful diagnostic label visible without letting its
            # preferred width starve the method selector on narrow screens.
            self.method_lbl.setWordWrap(True)
            self.method_lbl.setSizePolicy(
                QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
            )


def _dispose_progress(progress):
    progress_dialog.hide_once(progress)
    progress.close()
    progress.deleteLater()


def _coerce_integer_default(name: str, value: object) -> int:
    """Convert a persisted integer default after validating its concrete type."""
    if not isinstance(value, (str, bytes, bytearray, int, float)):
        raise TypeError(f"Invalid integer default for {name}: {value!r}")
    return int(value)


def _is_integer_analysis_param(name):
    return name == "digits"


def _display_svg_path(output_path):
    root, _extension = os.path.splitext(str(output_path))
    normalized_path = os.path.normcase(os.path.abspath(str(output_path)))
    path_digest = hashlib.sha256(normalized_path.encode("utf-8")).hexdigest()[:12]
    plot_name = os.path.basename(root) or "plot"
    return analysis_output_path("%s-%s.display.svg" % (plot_name, path_digest))


def add_plot_params(specs_form):
    if getattr(specs_form, "analysis_type", None) == "meta-regression":
        bubble_outpath = _text_value(specs_form.image_path)
        specs_form.current_param_vals.update(
            {
                "bp_style": PLOT_STYLE_VALUES.get(
                    str(specs_form.style_cbo.currentText()), "default"
                ),
                "bp_accent_color": _text_value(specs_form.accent_color),
                "bp_point_size_multiplier": specs_form.point_size_multiplier.value(),
                "bp_xlabel": _plot_axis_label_value(specs_form.x_lbl_le),
                "bp_xticks": _validated_plot_ticks(specs_form.x_ticks_le),
                "bp_plot_lb": _validated_plot_bound(specs_form.plot_lb_le),
                "bp_plot_ub": _validated_plot_bound(specs_form.plot_ub_le),
                "bp_outpath": bubble_outpath,
                "bp_display_path": _display_svg_path(bubble_outpath),
                "bp_show_regression_line": specs_form.show_regression_line.isChecked(),
                "bp_show_confidence_band": specs_form.show_confidence_band.isChecked(),
                "bp_show_prediction_interval": specs_form.show_prediction_interval.isChecked(),
                "bp_show_legend": specs_form.show_legend.isChecked(),
            }
        )
        return

    specs_form.current_param_vals["fp_style"] = PLOT_STYLE_VALUES.get(
        str(specs_form.style_cbo.currentText()), "default"
    )
    specs_form.current_param_vals["fp_show_col1"] = specs_form.show_1.isChecked()
    specs_form.current_param_vals["fp_col1_str"] = _text_value(specs_form.col1_str_edit)
    specs_form.current_param_vals["fp_show_col2"] = specs_form.show_2.isChecked()
    specs_form.current_param_vals["fp_col2_str"] = _text_value(specs_form.col2_str_edit)
    specs_form.current_param_vals["fp_show_col3"] = specs_form.show_3.isChecked()
    specs_form.current_param_vals["fp_col3_str"] = _text_value(specs_form.col3_str_edit)
    specs_form.current_param_vals["fp_show_col4"] = specs_form.show_4.isChecked()
    specs_form.current_param_vals["fp_col4_str"] = _text_value(specs_form.col4_str_edit)
    specs_form.current_param_vals["fp_xlabel"] = _plot_axis_label_value(
        specs_form.x_lbl_le
    )
    forest_outpath = _text_value(specs_form.image_path)
    specs_form.current_param_vals["fp_outpath"] = forest_outpath
    specs_form.current_param_vals["fp_display_path"] = _display_svg_path(forest_outpath)

    plot_lb = _text_value(specs_form.plot_lb_le)
    specs_form.current_param_vals["fp_plot_lb"] = "[default]"
    if plot_lb != "[default]" and check_plot_bound(plot_lb):
        specs_form.current_param_vals["fp_plot_lb"] = plot_lb

    plot_ub = _text_value(specs_form.plot_ub_le)
    specs_form.current_param_vals["fp_plot_ub"] = "[default]"
    if plot_ub != "[default]" and check_plot_bound(plot_ub):
        specs_form.current_param_vals["fp_plot_ub"] = plot_ub

    xticks = _text_value(specs_form.x_ticks_le)
    specs_form.current_param_vals["fp_xticks"] = "[default]"
    if xticks != "[default]" and seems_sane(xticks):
        specs_form.current_param_vals["fp_xticks"] = xticks

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
    return value if value != "[default]" and check_plot_bound(value) else "[default]"


def _validated_plot_ticks(widget):
    value = _text_value(widget)
    return value if value != "[default]" and seems_sane(value) else "[default]"


def _plot_axis_label_value(widget):
    """Return an axis label without leaking an untouched form placeholder."""
    value = plot_parameter_text_value(widget)
    return None if value is None else qt_text.to_native_text(value)


def _normalized_plot_style(style):
    style = str(_scalar_plot_param(style) or "default").strip().lower()
    return style if style in PLOT_STYLE_LABELS else "default"


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


def _diagnostic_analysis_requests(specs_form):
    method_names, list_of_param_vals = [], []
    missing_metrics = []

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
        if sens_details and spec_details and sens_details[0] == spec_details[0] == "diagnostic.reitsma":
            joint = (sens_details[0], sens_details[1])
            configured = [metric for metric in configured if metric not in ("Sens", "Spec")]

    pending = [("Sens", joint)] if joint is not None else []
    pending.extend((metric, specs_form.diagnostic_analysis_details[metric]) for metric in configured)
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

        # update the forest plot path
        split_fp_path = specs_form.current_param_vals["fp_outpath"].split(".")
        new_str = (
            split_fp_path[0]
            if len(split_fp_path) == 1
            else ".".join(split_fp_path[:-1])
        )
        new_str = new_str + "_%s" % diagnostic_metric.lower() + ".png"
        param_vals["fp_outpath"] = new_str
        param_vals["fp_display_path"] = _display_svg_path(new_str)

        # update the metric
        param_vals["measure"] = diagnostic_metric
        if joint is not None and diagnostic_metric == "Sens":
            param_vals["joint.metrics"] = "Sens,Spec"

        method_names.append(method)
        list_of_param_vals.append(param_vals)

    if missing_metrics:
        raise ValueError(
            "No method and parameters were selected for: %s. "
            "Complete all diagnostic method screens before running analysis."
            % ", ".join(missing_metrics)
        )

    if not method_names:
        raise ValueError("No diagnostic metrics were configured for analysis.")

    return method_names, list_of_param_vals


def _primary_reitsma_fit_failure(result, requests):
    sections = getattr(result, "sections", ())
    for request in requests:
        if (
            request.data_type != "diagnostic"
            or request.method != "diagnostic.reitsma"
        ):
            continue
        error_section_id = "diagnostic.%s.error" % request.metric.lower()
        for section in sections:
            if section.semantic_id == error_section_id:
                return request.metric, section.value
    return None


def _text_value(widget):
    return qt_text.to_native_text(widget.text())
