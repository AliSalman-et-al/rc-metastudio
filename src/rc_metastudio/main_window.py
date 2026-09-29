# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Main RC MetaStudio desktop window."""

from __future__ import annotations

import os
from collections.abc import Mapping
from functools import cmp_to_key
from typing import TYPE_CHECKING, TypeGuard, cast
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QAction,
    QCloseEvent,
    QKeyEvent,
    QKeySequence,
    QResizeEvent,
    QTextDocument,
)
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QLabel,
    QMessageBox,
    QTableView,
)
import copy
from dataclasses import replace
import tempfile
import uuid
from pathlib import Path

if TYPE_CHECKING:
    import ui_main_window as _ui_main_window
else:
    from rc_metastudio import ui_main_window as _ui_main_window
from rc_metastudio import dataset_table_view
from rc_metastudio import dataset_table_model
from rc_metastudio import meta_globals
from rc_metastudio.meta_globals import DEFAULT_DATASET_NAME
from rc_metastudio import analysis_dataset
from rc_metastudio import analysis_adapter
from rc_metastudio import analysis_worker_client
from rc_metastudio import app_error_handler
from rc_metastudio import r_backend
from rc_metastudio import qt_layout
from rc_metastudio import adaptive_window
from rc_metastudio import qt_text
from rc_metastudio import name_validation
from rc_metastudio import project_adapter
from rc_metastudio import project_format
from rc_metastudio import recovery_snapshot
from rc_metastudio import csv_import
from rc_metastudio import saved_result_adapter
from rc_metastudio import analysis_draft
from rc_metastudio import analysis_draft_records
from rc_metastudio import context_panel_widget, results_panel_widget
from rc_metastudio.settings import (
    add_file_to_recent_files,
    analysis_output_path,
    get_default_open_directory,
    get_base_path,
    get_recent_files,
    get_sample_projects_path,
    get_user_documents_path,
    load_main_column_widths,
    load_settings,
    recent_file_display_name,
    save_main_window_placement,
    save_settings,
)
from rc_metastudio.runtime_types import required

from rc_metastudio import add_new_dialogs
from rc_metastudio import results_window, analysis_setup_dialog
from rc_metastudio import publication_bias_dialog
from rc_metastudio import diagnostic_metrics_dialog
from rc_metastudio import meta_regression_dialog
from rc_metastudio import reitsma_analysis_dialog
from rc_metastudio import subgroup_analysis_dialog
from rc_metastudio import edit_dialog
from rc_metastudio import edit_name_dialogs
from rc_metastudio import covariate_type_dialog
from rc_metastudio import confidence_level_dialog
from rc_metastudio import main_wizard
from rc_metastudio import about_legal_dialog

from rc_metastudio.analysis_results import AnalysisResult
from rc_metastudio.workspace_session import WorkspaceSession


def _qt_item_text(value):
    return qt_text.to_native_text(value)


def _resolve_open_file_path(file_path):
    if file_path in [None, ""] or os.path.exists(file_path):
        return file_path

    normalized_path = os.path.normpath(file_path).replace("/", os.sep)
    path_parts = [part.lower() for part in normalized_path.split(os.sep)]
    if "sample_projects" not in path_parts:
        return file_path

    sample_file = os.path.basename(file_path)
    candidates = [
        os.path.join(get_sample_projects_path(), sample_file),
        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), os.pardir, "sample_projects", sample_file
            )
        ),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return file_path


def _format_open_project_error(file_path, exception):
    if isinstance(
        exception,
        (
            project_adapter.ProjectAdapterError,
            project_format.ProjectFormatError,
        ),
    ):
        return "Could not open %s.\n\n%s" % (file_path, exception)
    return "Could not open %s.\n\nDetails: %s: %s" % (
        file_path,
        exception.__class__.__name__,
        exception,
    )


def _qt_dialog_path(value):
    value = value[0] if isinstance(value, tuple) else value
    return qt_text.to_native_text(value)


def _qt_text(value):
    return qt_text.to_native_text(value)


def _connect_action(action, callback):
    parent = getattr(callback, "__self__", None)
    action.triggered[bool].connect(
        app_error_handler.safe_slot(lambda checked=False: callback(), parent=parent)
    )


def _format_confidence_level_status(confidence_level):
    if confidence_level is None:
        return "Confidence Level: not set"
    return "Confidence Level: {:.1%}".format(float(confidence_level) / 100.0)


def _request_with_run_output_paths(request, run_id):
    """Give each worker-owned forest plot a path unique to its run."""
    parameters = request.parameter_values()
    if "fp_outpath" in parameters:
        output_path = analysis_output_path("forest-%s.png" % run_id)
        parameters["fp_outpath"] = output_path
        parameters["fp_display_path"] = analysis_setup_dialog._display_svg_path(
            output_path
        )
    return analysis_adapter.make_analysis_request(
        data_type=request.data_type,
        workflow=request.workflow,
        method=request.method,
        metric=request.metric,
        parameters=parameters,
    )


def _cleanup_analysis_staging(run):
    staging = run.get("staging")
    cleanup = getattr(staging, "cleanup", None)
    if callable(cleanup):
        cleanup()


def _is_string_keyed_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping) and all(isinstance(key, str) for key in value)


def _is_string_list(value: object) -> TypeGuard[list[str]]:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _required_draft_text(value: object, message: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(message)
    return value


def _required_draft_groups(value: object) -> list[str]:
    if not _is_string_list(value):
        raise ValueError("The draft has invalid study groups")
    return value


def _optional_draft_text(value: object, message: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(message)
    return value


def _validated_raw_preview_calls(payload, requests):
    calls = payload["calls"]
    if (
        not isinstance(calls, list)
        or len(calls) != len(requests)
        or {item["id"] for item in calls} != requests.keys()
    ):
        raise ValueError("Study preview response does not match the request")
    return calls


def _is_analysis_stopped(error):
    return isinstance(error, dict) and error.get("type") == "AnalysisStoppedError"


def _analysis_engine_failure_detail(error):
    if not isinstance(error, dict):
        return str(error)
    detail = error.get("message") or "The method catalogue could not be loaded."
    technical = error.get("details") or ""
    if technical:
        return "%s\n\n%s" % (detail, technical)
    return detail


class ElidingStatusLabel(QLabel):
    """A status label whose content cannot claim window geometry."""

    def __init__(self, text="", parent=None):
        super(ElidingStatusLabel, self).__init__(parent)
        self._full_text = ""
        # layout-audit: allow=content-overflow-control; reason=required content may consume available layout width
        self.setMinimumWidth(0)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Preferred
        )
        self.setText(text)

    def setText(  # ty: ignore[invalid-method-override] -- PyQt6's QLabel overload stubs conflict with this semantic text override.
        self, text: str | None
    ) -> None:
        text = qt_text.to_native_text(text)
        if "<" in text and ">" in text:
            document = QTextDocument()
            document.setHtml(text)
            text = document.toPlainText()
        self._full_text = text
        self.setToolTip(self._full_text)
        self._refresh_elision()

    def text(self):
        """Return the semantic status text, not its width-dependent paint form."""
        return self._full_text

    def resizeEvent(  # ty: ignore[invalid-method-override] -- PyQt6's QLabel and QWidget stubs conflict for this runtime-supported override.
        self, event: QResizeEvent | None
    ) -> None:
        super(ElidingStatusLabel, self).resizeEvent(event)
        self._refresh_elision()

    def _refresh_elision(self):
        width = max(0, self.contentsRect().width())
        elided = self.fontMetrics().elidedText(
            self._full_text, Qt.TextElideMode.ElideRight, width
        )
        QLabel.setText(self, elided)


class MainWindow(QtWidgets.QMainWindow, _ui_main_window.Ui_MainWindow):
    model: dataset_table_model.DatasetTableModel
    tableView: dataset_table_view.DatasetTableView
    _recovery_path: Path | None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.analysis_service = analysis_adapter.AnalysisService()
        self.analysis_worker = analysis_worker_client.AnalysisWorkerClient(self)
        self.analysis_worker.progress.connect(self._analysis_worker_progress)
        self.analysis_worker.completed.connect(self._analysis_worker_completed)
        self.analysis_worker.methodsReady.connect(self._analysis_worker_methods_ready)
        self.analysis_worker.calculatorCompleted.connect(self._raw_previews_completed)
        self.analysis_worker.failed.connect(self._analysis_worker_failed)
        self.analysis_worker.busyChanged.connect(self._raw_preview_worker_busy_changed)
        self._analysis_worker_runs = {}
        self._raw_preview_timer = QtCore.QTimer(self)
        self._raw_preview_timer.setSingleShot(True)
        self._raw_preview_timer.timeout.connect(self._submit_raw_previews)
        self._raw_previews_paused = False
        self._document_generation = 0
        self._recovery_enabled = False
        self._recovery_path = None
        self._recovery_timer = QtCore.QTimer(self)
        self._recovery_timer.setSingleShot(True)
        self._recovery_timer.timeout.connect(self._write_recovery_snapshot)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setupUi(self)
        self.action_reitsma = QAction(
            "Joint Reitsma sensitivity and specificity…", self
        )
        self.action_reitsma.setObjectName("action_reitsma")
        self.action_reitsma.setStatusTip(
            "Fit one joint count-based Reitsma model for sensitivity and specificity."
        )
        self.menuAnalysis.insertAction(self.action_meta_regression, self.action_reitsma)
        qt_layout.configure_analysis_menu(self.menuAnalysis)
        for action, icon_name in (
            (self.action_go, "meta-analysis"),
            (self.action_cum_ma, "cumulative-analysis"),
            (self.action_loo_ma, "leave-one-out-analysis"),
            (self.action_subgroup_ma, "subgroup-analysis"),
            (self.action_meta_regression, "meta-regression"),
            (self.action_publication_bias, "publication-bias"),
        ):
            qt_layout.configure_analysis_action_icon(action, icon_name)
        qt_layout.configure_main_toolbar(self.toolBar)
        dataset_file_label = ElidingStatusLabel(
            self.dataset_file_lbl.text(), self.centralwidget
        )
        self.verticalLayout_3.replaceWidget(self.dataset_file_lbl, dataset_file_label)
        self.dataset_file_lbl.deleteLater()
        self.dataset_file_lbl = dataset_file_label
        qt_layout.configure_navigation_tool_buttons(
            (
                self.nav_left_btn,
                self.nav_up_btn,
                self.nav_down_btn,
                self.nav_right_btn,
                self.nav_add_btn,
            )
        )
        adaptive_window.register_adaptive_window(self, adaptive_window.WindowRole.MAIN)
        table_view = dataset_table_view.DatasetTableView(self.nav_frame)
        self.verticalLayout.replaceWidget(self.tableView, table_view)
        self.tableView.deleteLater()
        self.tableView = table_view
        self.tableView.restore_column_widths(load_main_column_widths())
        self._configure_workspace_destinations()

        self.cl_label = ElidingStatusLabel(
            _format_confidence_level_status(meta_globals.DEFAULT_CONFIDENCE_LEVEL)
        )
        self.cl_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.statusbar.addWidget(self.cl_label, 1)

        self.workspace = WorkspaceSession()
        self.new_dataset()

        self.tableView.setModel(self.model)
        self.tableView.setItemDelegate(dataset_table_view.StudyDelegate(self.tableView))

        self.dimensions = ["outcome", "follow-up", "group"]
        self.current_dimension_index = 0
        self.update_dimension()
        self._model_signal_connections = []
        self._setup_connections()
        self._connect_workspace_context()
        self._configure_standard_shortcuts()
        self.tableView.setSelectionMode(QTableView.SelectionMode.ContiguousSelection)
        self.model.reset_model()
        # The table view delegates window-owned actions through this reference.
        self.tableView.main_gui = cast(dataset_table_view.MainWindowProtocol, self)
        self.tableView.synchronize_column_widths()

        self.out_path = None
        self.metric_menu_is_set_for = None

        self.action_meta_regression.setEnabled(False)
        self.action_publication_bias.setEnabled(False)
        self.action_reitsma.setEnabled(False)

        load_settings()
        self.populate_open_recent_menu()

    def _configure_workspace_destinations(self):
        self.context_panel = context_panel_widget.ContextPanelWidget(
            self.centralwidget
        )
        self.workspace_tabs = QtWidgets.QTabWidget(self.centralwidget)
        self.workspace_tabs.setObjectName("workspaceTabs")
        self.workspace_tabs.setAccessibleName("Project destinations")
        self.results_panel = results_panel_widget.ResultsPanelWidget(
            self.workspace_tabs
        )
        self.verticalLayout_3.removeWidget(self.nav_frame)
        self.workspace_tabs.addTab(self.nav_frame, "Data")
        self.workspace_tabs.addTab(self.results_panel, "Results")
        self.frame.hide()
        self.verticalLayout_3.insertWidget(0, self.context_panel)
        self.verticalLayout_3.insertWidget(1, self.workspace_tabs, 1)

    def _connect_workspace_context(self):
        panel = self.context_panel
        panel.outcome_selected.connect(self._workspace_outcome_selected)
        panel.time_point_selected.connect(self._workspace_time_point_selected)
        panel.treatment_arm_selected.connect(self._workspace_treatment_arm_selected)
        panel.control_arm_selected.connect(self._workspace_control_arm_selected)
        panel.measure_selected.connect(self._workspace_measure_selected)
        panel.add_outcome_requested.connect(
            lambda: self._workspace_add_dimension("outcome")
        )
        panel.add_time_point_requested.connect(
            lambda: self._workspace_add_dimension("follow-up")
        )
        panel.add_study_arm_requested.connect(
            lambda: self._workspace_add_dimension("group")
        )
        self.results_panel.open_requested.connect(self._open_saved_analysis)
        self.results_panel.edit_copy_requested.connect(self._edit_saved_analysis_copy)
        self.results_panel.delete_requested.connect(self._delete_saved_analysis)
        self.results_panel.resume_draft_requested.connect(self._resume_analysis_draft)
        self.results_panel.delete_draft_requested.connect(self._delete_analysis_draft)
        panel.refresh(self.model)
        self._refresh_workspace_results()

    def _refresh_workspace_context(self):
        self.context_panel.refresh(self.model)
        self._enable_action_reitsma()

    def _bind_project_generation(self, dialog):
        dialog._document_generation = self._document_generation

    def _require_current_project_dialog(self, dialog):
        if getattr(dialog, "_document_generation", None) == self._document_generation:
            return True
        dialog._show_analysis_failure(
            "The project changed after this analysis setup opened. The request was "
            "not run. Open a new setup from the active project."
        )
        dialog.reject()
        return False

    def _refresh_workspace_results(self):
        self.results_panel.set_records(self.workspace.list_saved_analyses())
        self.results_panel.set_drafts(self.workspace.list_analysis_drafts())

    def _matching_analysis_draft(self, model, analysis_type):
        selection_values = self._draft_selection_values(model)
        for record in reversed(self.workspace.list_analysis_drafts()):
            selection = record["selection"]
            settings = record["settings"]
            if all(
                selection.get(key) == value
                for key, value in selection_values.items()
            ) and settings.get("analysis_type") == analysis_type:
                return record
        return None

    @staticmethod
    def _draft_selection_values(model):
        get_groups = getattr(model, "get_current_groups", None)
        get_follow_up = getattr(model, "get_current_follow_up_name", None)
        groups = list(get_groups())[:2] if callable(get_groups) else []
        follow_up = get_follow_up() if callable(get_follow_up) else None
        return {
            "outcome": model.current_outcome_name,
            "follow_up": follow_up,
            "groups": groups,
            "effect": model.current_effect,
        }

    def _attach_analysis_draft(self, form, record=None):
        form._analysis_draft_id = record["id"] if record is not None else None
        form._document_generation = self._document_generation
        form.draft_changed.connect(
            lambda payload, editor=form: self._save_analysis_draft_from_dialog(
                editor, payload
            )
        )
        form.finished.connect(
            lambda _result, editor=form: self._analysis_draft_editor_closed(editor)
        )

    def _analysis_draft_editor_closed(self, form):
        timer = form._draft_change_timer
        pending = timer.isActive()
        timer.stop()
        if pending and form._document_generation == self._document_generation:
            self._save_analysis_draft_from_dialog(form, form.draft_payload())

    @staticmethod
    def _restore_analysis_draft_method(form, record):
        ordering = record["settings"].get("ordering")
        if ordering is not None and form.analysis_type == "cumulative":
            from rc_metastudio.cumulative_analysis import CumulativeOrderSpec

            choice = CumulativeOrderSpec.from_mapping(ordering)
            for control, value in (
                (form.cumulative_order_field, choice.field),
                (form.cumulative_direction, choice.direction),
                (form.cumulative_missing_year, choice.missing_year_policy),
            ):
                index = control.findData(value)
                if index >= 0:
                    control.setCurrentIndex(index)
        method_id = record["settings"]["method"]
        if method_id is None:
            return
        for label, available_id in form.available_method_d.items():
            if available_id == method_id:
                form.method_cbo_box.setCurrentText(label)
                return
        QMessageBox.warning(
            form,
            "Draft Method Unavailable",
            "This draft's method is unavailable with the current data and analysis "
            "engine. Choose an available method before running.",
        )

    def _save_analysis_draft_from_dialog(self, form, payload):
        if form._document_generation != self._document_generation:
            return False
        try:
            record = analysis_draft_records.create_record(
                payload["selection"],
                payload["settings"],
                record_id=form._analysis_draft_id,
            )
            record_id = record.value["id"]
            if not isinstance(record_id, str):
                raise ValueError("analysis draft record has an invalid identifier")
            existing = self.workspace.get_analysis_draft(record_id)
            if existing is not None and all(
                existing.value[field] == record.value[field]
                for field in ("selection", "settings")
            ):
                return True
            self.workspace.save_analysis_draft(record)
        except Exception as error:
            QMessageBox.warning(
                self,
                "Could Not Save Analysis Draft",
                "The current analysis settings could not be kept in this project.\n\n"
                "Details: %s: %s" % (type(error).__name__, error),
            )
            return False
        form._analysis_draft_id = record_id
        self._notify_user_that_data_is_unsaved()
        self._refresh_workspace_results()
        return True

    def _resume_analysis_draft(self, record_id: str) -> None:
        record = self.workspace.get_analysis_draft(record_id)
        if record is None:
            return
        try:
            selection = self._validated_draft_selection(record.value["selection"])
            workflow = self._validated_draft_workflow(record.value["settings"])
            self._restore_draft_selection(selection)
            self._open_draft_workflow(workflow)
        except (KeyError, TypeError, ValueError) as error:
            QMessageBox.warning(
                self,
                "Draft Context Unavailable",
                "The draft's outcome, time point, arms, or measure is no longer "
                "available. The draft remains in this project.\n\nDetails: %s" % error,
            )

    @staticmethod
    def _validated_draft_selection(value):
        if not isinstance(value, dict):
            raise ValueError("analysis draft selection must be an object")
        outcome = _required_draft_text(value["outcome"], "The draft has no selected outcome")
        groups = _required_draft_groups(value["groups"])
        follow_up = _optional_draft_text(value["follow_up"], "The draft has an invalid follow-up")
        effect = _optional_draft_text(value["effect"], "The draft has an invalid measure")
        return outcome, groups, follow_up, effect

    @staticmethod
    def _validated_draft_workflow(value):
        if not isinstance(value, dict):
            raise ValueError("The draft has invalid analysis settings")
        workflow = value["analysis_type"]
        if workflow is not None and not isinstance(workflow, str):
            raise ValueError("The draft has an invalid analysis type")
        return workflow

    def _restore_draft_selection(self, selection):
        outcome, groups, follow_up, effect = selection
        self.display_outcome(
            outcome,
            group_names=groups or None,
            follow_up_name=follow_up,
        )
        if isinstance(effect, str):
            self._workspace_measure_selected(effect)
            if self.model.current_effect != effect:
                raise ValueError("The draft's measure is no longer available")

    def _open_draft_workflow(self, workflow):
        confidence_level = self.model.get_confidence_level()
        if workflow in (None, "cumulative", "leave-one-out"):
            self._request_standard_analysis_methods(
                confidence_level,
                workflow=workflow or "standard",
            )
            return
        form = self._build_analysis_specs_dialog(
            analysis_type=workflow,
            confidence_level=confidence_level,
        )
        if form is not None:
            form.show()

    def _delete_analysis_draft(self, record_id):
        if self.workspace.get_analysis_draft(record_id) is None:
            return
        choice = QMessageBox.question(
            self,
            "Delete Analysis Draft",
            "Delete this unfinished analysis from the project?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Yes:
            self.workspace.delete_analysis_draft(record_id)
            self._refresh_workspace_results()
            self._notify_user_that_data_is_unsaved()

    def _flush_analysis_drafts(self):
        for form in self.findChildren(analysis_setup_dialog.AnalysisSetupDialog):
            if (
                form.isVisible()
                and getattr(form, "_document_generation", None)
                == self._document_generation
                and not self._save_analysis_draft_from_dialog(form, form.draft_payload())
            ):
                return False
        return True

    def _open_saved_analysis(self, record_id):
        record = self.workspace.get_saved_analysis(record_id)
        if record is None:
            return
        temporary = tempfile.TemporaryDirectory(prefix="rcms-result-")
        try:
            result = saved_result_adapter.restore_result(
                record, Path(temporary.name)
            )
            snapshot = record.value["input_snapshot"]
            specification = record.value["specification"]
            if not _is_string_keyed_mapping(snapshot) or not _is_string_keyed_mapping(
                specification
            ):
                raise ValueError("saved analysis inputs are malformed")
            context_snapshot = snapshot.get("input_snapshot", snapshot)
            if not _is_string_keyed_mapping(context_snapshot):
                raise ValueError("saved analysis context is malformed")
            groups = context_snapshot.get("groups", [])
            if not _is_string_list(groups):
                raise ValueError("saved analysis study groups are malformed")
            parameters = specification.get("params", {})
            if not _is_string_keyed_mapping(parameters):
                raise ValueError("saved analysis parameters are malformed")
            effective_settings = dict(parameters)
            plan = result.subgroup_plan
            if plan is not None:
                from rc_metastudio.subgroup_analysis import SubgroupPlan

                subgroup_plan = SubgroupPlan.from_mapping(plan)
                effective_settings.update(
                    {
                        "covariate_name": subgroup_plan.covariate_name,
                        "missing_value_policy": subgroup_plan.missing_policy,
                        "included_study_count": subgroup_plan.included_count,
                        "excluded_study_count": subgroup_plan.excluded_count,
                    }
                )
            context = {
                "outcome": context_snapshot.get("outcome"),
                "time_point": context_snapshot.get("time_point", context_snapshot.get("follow_up")),
                "direction": " versus ".join(groups),
                "measure": specification.get("metric"),
                "workflow": (
                    "subgroup analysis"
                    if plan is not None
                    else specification.get("workflow")
                ),
                "method": specification.get("method"),
                "status": record.value["status"],
                "effective_settings": effective_settings,
            }
            form = self._show_analysis_result(
                result,
                context=context,
                edit_copy_spec=record.value,
            )
            form.destroyed.connect(lambda: temporary.cleanup())
        except Exception as error:
            temporary.cleanup()
            app_error_handler.log_exception(type(error), error, error.__traceback__)
            QMessageBox.critical(
                self,
                "Could Not Open Saved Analysis",
                "The saved analysis could not be displayed.\n\nDetails: %s: %s"
                % (type(error).__name__, error),
            )

    def _edit_saved_analysis_copy(self, record_id):
        record = self.workspace.get_saved_analysis(record_id)
        if record is not None:
            self._edit_analysis_copy(record.value)

    def _edit_analysis_copy(self, source):
        if self.analysis_worker.is_busy:
            QMessageBox.information(
                self,
                "Analysis in Progress",
                "Wait for the current analysis to finish before editing a copy.",
            )
            return
        run_id = None
        try:
            context = self._analysis_copy_context(source)
            if context is None:
                return
            snapshot, parameters, method, data_type, workflow = context
            draft_model = analysis_draft.model_for_snapshot(snapshot)
            from rc_metastudio.cumulative_analysis import CumulativeAnalysisSnapshot

            if isinstance(snapshot, CumulativeAnalysisSnapshot):
                base_snapshot = snapshot.input_snapshot
            else:
                base_snapshot = snapshot
            run_id = uuid.uuid4().hex
            self._analysis_worker_runs[run_id] = {
                "kind": "edit_methods",
                "draft_model": draft_model,
                "parameters": parameters,
                "method": method,
                "input_snapshot": snapshot,
                "workflow": workflow,
            }
            self.statusbar.showMessage("Loading analysis methods…")
            self.analysis_worker.request_methods(
                run_id,
                base_snapshot.to_mapping(),
                {
                    "data_type": data_type,
                    "metric": base_snapshot.metric,
                    "workflow": workflow,
                },
            )
        except Exception as error:
            if run_id is not None:
                self._analysis_worker_runs.pop(run_id, None)
            self.statusbar.clearMessage()
            self._show_analysis_specs_error(error)

    def _analysis_copy_context(self, source):
        if not isinstance(source, Mapping):
            request = source.effective_request
            return (
                source.input_snapshot,
                request.parameter_values(),
                request.method,
                request.data_type,
                request.workflow,
            )
        specification = source["specification"]
        if self._open_special_analysis_copy(source, specification):
            return None
        data_type = specification["data_type"]
        workflow = specification["workflow"]
        if workflow == "subgroup":
            self._open_subgroup_analysis_copy(source, specification, data_type)
            return None
        snapshot = self._saved_analysis_input_snapshot(
            source["input_snapshot"], data_type, workflow
        )
        parameters = dict(specification["params"])
        parameters.update(source.get("presentation", {}))
        return snapshot, parameters, specification["method"], data_type, workflow

    def _open_special_analysis_copy(self, source, specification):
        return (
            self._open_small_study_effects_copy(source, specification)
            or self._open_meta_regression_copy(source, specification)
            or self._open_reitsma_copy(source, specification)
        )

    def _open_small_study_effects_copy(self, source, specification):
        results = source.get("results")
        if not (
            isinstance(specification, Mapping)
            and "data.type" in specification
            and isinstance(results, Mapping)
            and isinstance(results.get("small_study_effects"), Mapping)
        ):
            return False
        from rc_metastudio.analysis_worker import _small_study_effects_snapshot
        from rc_metastudio.publication_bias import SmallStudyEffectsRequest

        request = SmallStudyEffectsRequest.from_mapping(specification)
        snapshot = _small_study_effects_snapshot(
            source["input_snapshot"], request.data_type
        )
        form = publication_bias_dialog.PublicationBiasDialog(
            self.model,
            parent=self,
            input_snapshot=snapshot,
            initial_request=request,
        )
        self._bind_project_generation(form)
        form.preview_requested.connect(
            lambda frozen, preview: self.submit_small_study_effects_preview(
                form, frozen, preview
            )
        )
        form.analysis_requested.connect(
            lambda frozen, updated: self.submit_small_study_effects(
                form, frozen, updated
            )
        )
        form.start_preview()
        form.show()
        return True

    def _open_meta_regression_copy(self, source, specification):
        if (
            specification.get("workflow") != "meta-regression"
            or specification.get("method")
            not in {"meta.regression", "diagnostic.reitsma"}
        ):
            return False
        from rc_metastudio.meta_regression_analysis import (
            MetaRegressionInputSnapshot,
            MetaRegressionRunRequest,
        )

        form = meta_regression_dialog.MetaRegressionDialog(
            self.model,
            worker_client=self.analysis_worker,
            frozen_snapshot=MetaRegressionInputSnapshot.from_mapping(
                source["input_snapshot"]
            ),
            initial_request=MetaRegressionRunRequest.from_mapping(specification),
            parent=self,
        )
        self._bind_project_generation(form)
        form.run_requested.connect(
            app_error_handler.safe_slot(
                lambda snapshot, request: self.submit_meta_regression_analysis(
                    form, snapshot, request
                ),
                parent=self,
            )
        )
        form.show()
        return True

    def _open_reitsma_copy(self, source, specification):
        if specification.get("method") != "diagnostic.reitsma":
            return False
        from rc_metastudio.reitsma_analysis import ReitsmaInputSnapshot, ReitsmaRequest

        form = reitsma_analysis_dialog.ReitsmaAnalysisDialog(
            self.model,
            worker_client=self.analysis_worker,
            frozen_snapshot=ReitsmaInputSnapshot.from_mapping(source["input_snapshot"]),
            initial_request=ReitsmaRequest.from_mapping(specification),
            parent=self,
        )
        self._bind_project_generation(form)
        form.run_requested.connect(
            app_error_handler.safe_slot(
                lambda snapshot, request: self.submit_reitsma_analysis(
                    form, snapshot, request
                ),
                parent=self,
            )
        )
        form.show()
        return True

    def _open_subgroup_analysis_copy(self, source, specification, data_type):
        from rc_metastudio.subgroup_analysis import SubgroupPlan

        snapshot = self._saved_analysis_input_snapshot(
            source["input_snapshot"], data_type, "standard"
        )
        plan = SubgroupPlan.from_mapping(source["results"].get("subgroup_plan"))
        saved_parameters = {
            name: value
            for name, value in specification["params"].items()
            if name
            not in {
                "fp_outpath",
                "fp_display_path",
                "bp_outpath",
                "bp_display_path",
            }
        }
        self._request_subgroup_analysis_methods(
            snapshot,
            plan,
            initial_parameters=saved_parameters,
            initial_method=specification["method"],
        )

    @staticmethod
    def _saved_analysis_input_snapshot(input_snapshot, data_type, workflow):
        if workflow == "cumulative":
            from rc_metastudio.cumulative_analysis import CumulativeAnalysisSnapshot

            return CumulativeAnalysisSnapshot.from_mapping(input_snapshot)
        if data_type == "binary":
            from rc_metastudio.analysis_worker import _snapshot_from_mapping

            return _snapshot_from_mapping(input_snapshot)
        if data_type == "continuous":
            from rc_metastudio.continuous_analysis_snapshot import ContinuousInputSnapshot

            return ContinuousInputSnapshot.from_mapping(input_snapshot)
        if data_type == "diagnostic":
            from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot

            return DiagnosticInputSnapshot.from_mapping(input_snapshot)
        raise ValueError("Unsupported saved analysis family")

    def _delete_saved_analysis(self, record_id):
        if self.workspace.get_saved_analysis(record_id) is None:
            return
        choice = QMessageBox.question(
            self,
            "Delete Saved Analysis",
            "Delete this saved analysis from the project?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Yes:
            self.workspace.delete_saved_analysis(record_id)
            self._refresh_workspace_results()
            self._notify_user_that_data_is_unsaved()

    def _workspace_outcome_selected(self, outcome):
        if outcome == self.model.current_outcome_name:
            return
        data_type = self.model.dataset.get_outcome_type(outcome)
        if data_type == meta_globals.BINARY:
            metrics = (
                meta_globals.BINARY_ONE_ARM_METRICS
                + meta_globals.BINARY_TWO_ARM_METRICS
            )
            if self.model.current_effect not in metrics:
                self.model.current_effect = meta_globals.BINARY_TWO_ARM_METRICS[0]
        elif data_type == meta_globals.CONTINUOUS:
            metrics = (
                meta_globals.CONTINUOUS_ONE_ARM_METRICS
                + meta_globals.CONTINUOUS_TWO_ARM_METRICS
            )
            if self.model.current_effect not in metrics:
                self.model.current_effect = meta_globals.CONTINUOUS_TWO_ARM_METRICS[0]
        elif data_type == meta_globals.DIAGNOSTIC:
            if self.model.current_effect not in meta_globals.DIAGNOSTIC_METRICS:
                self.model.current_effect = "Sens"
        self.display_outcome(outcome)

    def _workspace_time_point_selected(self, time_point):
        if time_point != self.model.get_current_follow_up_name():
            self.display_follow_up(self.model.get_t_point_for_follow_up_name(time_point))

    def _workspace_treatment_arm_selected(self, arm):
        self._workspace_arm_selected(arm, 0)

    def _workspace_control_arm_selected(self, arm):
        self._workspace_arm_selected(arm, 1)

    def _workspace_arm_selected(self, arm, position):
        groups = list(self.model.get_current_groups())
        if self.model.is_diagnostic():
            if groups and groups[0] == arm:
                return
            self.model.previous_groups = groups
            self.model.current_groups = [arm]
            self.model.group_index_a = self.model.dataset.get_group_names().index(arm)
            self.model.hydrate_derived_previews()
            self.model.reset_model()
            return
        if len(groups) < 2 or groups[position] == arm:
            return
        other = 1 - position
        if groups[other] == arm:
            groups[position], groups[other] = groups[other], groups[position]
        else:
            groups[position] = arm
        self.display_groups(groups)

    def _workspace_measure_selected(self, measure):
        if measure == self.model.current_effect:
            return
        if self.model.get_current_outcome_type() == "diagnostic":
            if measure not in meta_globals.DIAGNOSTIC_METRICS:
                return
            self.model.current_effect = measure
            self._refresh_workspace_context()
            return
        for menu_action in self.menuMetric.actions():
            submenu = menu_action.menu()
            if submenu is not None and any(
                _qt_item_text(action.data()) == measure for action in submenu.actions()
            ):
                self.metric_selected(measure, submenu)
                return

    def _workspace_add_dimension(self, dimension):
        previous_index = self.current_dimension_index
        self.current_dimension_index = self.dimensions.index(dimension)
        self.update_dimension()
        try:
            self.add_new()
        finally:
            self.current_dimension_index = previous_index
            self.update_dimension()

    def createPopupMenu(self):
        return None

    def start(self):
        # Enter the ordinary application event loop before opening the startup
        # workflow. QDialog.exec() creates a nested loop, which is not supported
        # uniformly by every windowing system (notably Cocoa during startup).
        self._startup_wizard = None
        self._recovery_path = recovery_snapshot.default_recovery_snapshot_path(
            get_base_path()
        )
        QtCore.QTimer.singleShot(0, self._offer_recovery_or_start)

    def _offer_recovery_or_start(self):
        path = self._recovery_path
        if path is None or not path.exists():
            self._recovery_enabled = True
            self._open_startup_wizard()
            return
        try:
            snapshot = recovery_snapshot.read_recovery_snapshot(path)
        except recovery_snapshot.RecoverySnapshotError as error:
            QMessageBox.warning(
                self,
                "Recovery Snapshot Unavailable",
                "The previous recovery snapshot could not be opened. It has been "
                "kept for inspection.\n\nDetails: %s" % error,
            )
            self._open_startup_wizard()
            return
        preview = snapshot.preview
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Recover Previous Work")
        dialog.setText("Restore the project from the previous session?")
        dialog.setInformativeText(
            "%s · %s studies · %s saved analyses · %s analysis drafts\n"
            "Snapshot: %s"
            % (
                preview.project_title,
                preview.study_count,
                preview.saved_analysis_count,
                preview.analysis_draft_count,
                preview.created_at.astimezone().strftime("%Y-%m-%d %H:%M"),
            )
        )
        restore_button = dialog.addButton(
            "Restore work", QMessageBox.ButtonRole.AcceptRole
        )
        discard_button = dialog.addButton(
            "Discard recovery", QMessageBox.ButtonRole.DestructiveRole
        )
        dialog.setDefaultButton(restore_button)
        self._recovery_prompt = dialog
        dialog.finished.connect(
            lambda _result: self._finish_recovery_prompt(
                dialog, snapshot, restore_button, discard_button
            )
        )
        dialog.open()

    def _finish_recovery_prompt(self, dialog, snapshot, restore_button, discard_button):
        clicked = dialog.clickedButton()
        dialog.deleteLater()
        self._recovery_prompt = None
        if clicked is restore_button:
            try:
                source = snapshot.preview.source_project_path
                recovered = WorkspaceSession(snapshot.document, path=source)
                self._install_open_document(recovered.runtime)
                self.workspace = recovered
                self.workspace.mark_dirty()
                self._document_generation += 1
                self.out_path = source
                self._notify_user_that_data_is_unsaved()
                self._refresh_workspace_results()
                self._recovery_enabled = True
                self._reactivate_after_startup_wizard()
                return
            except Exception as error:
                QMessageBox.critical(
                    self,
                    "Could Not Restore Work",
                    "The recovery snapshot was kept.\n\nDetails: %s: %s"
                    % (type(error).__name__, error),
                )
        elif clicked is discard_button:
            if self._invalidate_recovery_snapshot():
                self._recovery_enabled = True
        self._open_startup_wizard()

    def _schedule_recovery_snapshot(self):
        if self._recovery_enabled and self.workspace.is_dirty:
            self._recovery_timer.start(3000)

    def _write_recovery_snapshot(self):
        document = self.workspace.document
        if (
            not self._recovery_enabled
            or document is None
            or not self.workspace.is_dirty
            or self._recovery_path is None
        ):
            return
        try:
            recovery_snapshot.write_recovery_snapshot(
                self._recovery_path,
                document,
                source_project_path=self.out_path,
                workspace_was_dirty=True,
            )
        except recovery_snapshot.RecoverySnapshotError as error:
            self.statusbar.showMessage("Could not update recovery snapshot: %s" % error)

    def _invalidate_recovery_snapshot(self):
        self._recovery_timer.stop()
        if self._recovery_path is None:
            return True
        try:
            recovery_snapshot.invalidate_recovery_snapshot(self._recovery_path)
        except recovery_snapshot.RecoverySnapshotError as error:
            QMessageBox.warning(
                self,
                "Could Not Discard Recovery",
                "The recovery snapshot could not be removed.\n\nDetails: %s" % error,
            )
            return False
        return True

    def _open_startup_wizard(self):
        start_up_wizard = main_wizard.MainWizard(
            parent=self, recent_datasets=get_recent_files()
        )
        self._startup_wizard = start_up_wizard
        start_up_wizard.finished.connect(self._finish_startup_wizard)
        start_up_wizard.open()

    def _finish_startup_wizard(self, result):
        start_up_wizard = self._startup_wizard
        if start_up_wizard is None:
            return

        try:
            if result == int(QDialog.DialogCode.Accepted):
                wizard_data = start_up_wizard.get_results()
                self._handle_wizard_results(wizard_data)
        finally:
            start_up_wizard.deleteLater()
            self._startup_wizard = None
            self._reactivate_after_startup_wizard()

    def _reactivate_after_startup_wizard(self):
        if self.isMinimized():
            self.setWindowState(
                self.windowState() & ~QtCore.Qt.WindowState.WindowMinimized
            )
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(  # ty: ignore[invalid-method-override] -- PyQt6's QMainWindow and QWidget stubs conflict for this runtime-supported override.
        self, event: QCloseEvent | None
    ) -> None:
        if event is None:
            return
        self._pause_raw_previews()
        if not self._confirm_stop_running_analysis() or not self._confirm_close():
            self._resume_raw_previews()
            event.ignore()
            return
        self._disconnect_model_signals()
        save_main_window_placement(self, self.tableView.column_width_state())
        save_settings()
        event.accept()

    def _confirm_stop_running_analysis(self):
        if not self.analysis_worker.is_busy:
            return True
        if any(
            run.get("kind") == "raw_previews"
            for run in self._analysis_worker_runs.values()
        ):
            stopped = self.analysis_worker.stop_and_wait()
            self._raw_preview_timer.stop()
            return stopped
        choice = QMessageBox(self)
        choice.setWindowTitle("Analysis in Progress")
        choice.setText("An analysis is still running.")
        choice.setInformativeText(
            "Keep the project open, or stop the analysis and continue."
        )
        keep_button = choice.addButton(
            "Keep project open", QMessageBox.ButtonRole.RejectRole
        )
        stop_button = choice.addButton(
            "Stop analysis and continue", QMessageBox.ButtonRole.AcceptRole
        )
        choice.setDefaultButton(keep_button)
        choice.exec()
        if choice.clickedButton() is not stop_button:
            return False
        for run in self._analysis_worker_runs.values():
            dialog = run.get("dialog")
            progress = getattr(dialog, "_worker_progress_dialog", None)
            if progress is not None:
                progress.set_stage("Stopping analysis…")
                progress.stop_button.setEnabled(False)
        return self.analysis_worker.stop_and_wait()

    def _confirm_close(self):
        if not self._flush_analysis_drafts():
            return False
        if not self.workspace.is_dirty:
            return True
        choice = self.prompt_to_save_unsaved_data()
        if choice == QMessageBox.StandardButton.Yes:
            return self.save() is True
        return (
            self._invalidate_recovery_snapshot()
            if choice == QMessageBox.StandardButton.No
            else False
        )

    def _authorize_destructive_project_action(self):
        """Return whether New/Open/Import may replace the current project."""
        self._pause_raw_previews()
        authorized = False
        try:
            authorized = self._confirm_stop_running_analysis() and self._confirm_close()
            return authorized
        finally:
            if not authorized:
                self._resume_raw_previews()

    def _pause_raw_previews(self):
        self._raw_previews_paused = True
        self._raw_preview_timer.stop()

    def _resume_raw_previews(self):
        self._raw_previews_paused = False
        self._schedule_raw_previews()

    def _update_recent_project_nonfatal(self, path, operation):
        try:
            add_file_to_recent_files(path)
            self.populate_open_recent_menu()
        except Exception as exc:
            try:
                app_error_handler.log_exception(type(exc), exc, exc.__traceback__)
            except Exception:
                pass
            try:
                QMessageBox.warning(
                    self,
                    "Recent Projects Not Updated",
                    "The project was %s successfully, but RC MetaStudio could not "
                    "update the machine-local recent-project list.\n\nDetails: %s: %s"
                    % (operation, exc.__class__.__name__, exc),
                )
            except Exception:
                pass

    def _report_durability_uncertain_save(self, destination, exception):
        try:
            app_error_handler.log_exception(
                type(exception), exception, exception.__traceback__
            )
        except Exception:
            pass
        try:
            QMessageBox.warning(
                self,
                "Project Saved; Durability Uncertain",
                "RC MetaStudio installed the saved project at %s, but the operating "
                "system could not confirm final directory durability. The document "
                "is treated as saved so later actions do not discard work by retrying "
                "a replacement.\n\nDetails: %s" % (destination, exception),
            )
        except Exception:
            pass

    def _configure_standard_shortcuts(self):
        """Use platform-native shortcuts for the maintained shell actions."""
        for action, standard_key in (
            (self.action_new_dataset, QKeySequence.StandardKey.New),
            (self.action_open, QKeySequence.StandardKey.Open),
            (self.action_save, QKeySequence.StandardKey.Save),
            (self.action_quit, QKeySequence.StandardKey.Quit),
        ):
            action.setShortcut(QKeySequence(standard_key))

    def _model_about_to_be_reset(self):
        """Call all the functions here that should be called when the model is
        about to be reset
        """
        self._recalculate_display_scale_values()

    def _recalculate_display_scale_values(self):

        self.tableView.model().recalculate_display_scale()

    def create_new_dataset(self, use_undo_framework=True):
        if not self._authorize_destructive_project_action():
            return
        try:
            wizard = main_wizard.MainWizard(parent=self, path="new_dataset")
            if wizard.exec():
                wizard_data = wizard.get_results()
                self._handle_wizard_results(wizard_data)
        finally:
            self._resume_raw_previews()

    def new_dataset(
        self, name=DEFAULT_DATASET_NAME, is_diagnostic=False, use_undo_framework=True
    ):

        data_model = analysis_dataset.Dataset(title=name, is_diagnostic=is_diagnostic)
        # A new workspace needs one durable study for outcome setup. The table
        # model's editable trailing row remains presentation-only.
        data_model.add_study(analysis_dataset.Study(data_model.max_study_id() + 1))
        existing_model = getattr(self, "model", None)
        if existing_model is not None:
            if use_undo_framework:
                self._commit_model_operation(lambda: self.set_model(data_model))
            else:  # CSV import manages its own undo boundary.
                self.set_model(data_model)
        else:
            self.model = dataset_table_model.DatasetTableModel(dataset=data_model)
            self.model.enable_worker_raw_previews()
            self.disable_menu_options_that_require_dataset()
            self.workspace.update_live_state(
                project_adapter.RuntimeProject(
                    dataset=self.model.dataset,
                    model_state=self.model.get_state(),
                    restored_selection=False,
                )
            )
        self.out_path = None
        self._notify_user_that_data_is_unsaved()

    def _notify_user_that_data_is_unsaved(self):
        if self.out_path is None:
            self.dataset_file_lbl.setText(
                "<font color='red'>careful! your data isn't saved yet</font>"
            )
        else:
            self.dataset_file_lbl.setText(
                "Open Project: <font color='red'>%s</font>" % self.out_path
            )
        self._schedule_recovery_snapshot()

    def toggle_menu_options_that_require_dataset(self, enable):
        self.action_go.setEnabled(enable)
        self.action_cum_ma.setEnabled(enable)
        self.action_loo_ma.setEnabled(enable)
        self._enable_action_meta_regression(enable)
        self._enable_action_subgroup_ma(enable)
        self.action_publication_bias.setEnabled(enable)
        self._enable_action_reitsma(enable)

    def _enable_action_reitsma(self, dataset_analysis_enabled=None):
        if dataset_analysis_enabled is None:
            dataset_analysis_enabled = self.action_go.isEnabled()
        self.action_reitsma.setEnabled(
            dataset_analysis_enabled
            and bool(self.model and self.model.is_diagnostic())
        )

    def _enable_action_meta_regression(self, dataset_analysis_enabled=None):
        """Enables action_meta_regression if analysis can run and covariates exist."""
        if dataset_analysis_enabled is None:
            dataset_analysis_enabled = self.action_go.isEnabled()
        has_covariates = bool(self.model and self.model.dataset.covariates)
        self.action_meta_regression.setEnabled(
            dataset_analysis_enabled and has_covariates
        )

    def _enable_action_subgroup_ma(self, dataset_analysis_enabled=None):
        """Enables action_subgroup_ma if there are suitable covariate(s)
        i.e. of type Factor
        """
        if dataset_analysis_enabled is None:
            dataset_analysis_enabled = self.action_go.isEnabled()
        has_factor_covariates = bool(
            self.model
            and any(
                cov.get_data_type() == meta_globals.FACTOR
                for cov in self.model.dataset.covariates
            )
        )
        self.action_subgroup_ma.setEnabled(
            dataset_analysis_enabled and has_factor_covariates
        )

    def disable_menu_options_that_require_dataset(self):
        self.toggle_menu_options_that_require_dataset(False)

    def enable_menu_options_that_require_dataset(self):
        self.toggle_menu_options_that_require_dataset(True)

    def keyPressEvent(  # ty: ignore[invalid-method-override] -- PyQt6's QMainWindow and QWidget stubs conflict for this runtime-supported override.
        self, event: QKeyEvent | None
    ) -> None:
        if event is None:
            return
        if event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
            if event.key() == QtCore.Qt.Key.Key_S:
                self.save()
            elif event.key() == QtCore.Qt.Key.Key_O:
                self.open()

    def _disconnect_model_signals(self):
        """Disconnect signals owned by the current dataset model."""
        for connection in self._model_signal_connections:
            connection.disconnect()
        self._model_signal_connections = []

    def data_error(self, msg):
        QMessageBox.warning(self, "Warning", msg)

    def set_edit_focus(self, index):
        """Sets edit focus to the row,col specified by index."""
        if not index.isValid():
            return
        self.tableView.setCurrentIndex(index)
        if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
            return
        self.tableView.edit(index)

    def populate_open_recent_menu(self):
        recent_datasets = get_recent_files()
        self.action_open_recent_2.clear()
        for dataset in reversed(recent_datasets):
            action_item = QAction(
                recent_file_display_name(dataset), self.action_open_recent_2
            )
            action_item.setData(str(dataset))
            action_item.setToolTip(str(dataset))
            action_item.setStatusTip(str(dataset))
            self.action_open_recent_2.addAction(action_item)
            _connect_action(
                action_item, lambda dataset=dataset: self.dataset_selected(dataset)
            )

    def dataset_selected(self, dataset_path):
        self.open(file_path=dataset_path)

    def _change_global_ci(self):
        previous_confidence_level = self.model.get_confidence_level()

        dialog = confidence_level_dialog.ConfidenceLevelDialog(
            previous_confidence_level, self
        )
        if dialog.exec():
            new_confidence_level = dialog.get_value()
            change_cl_command = ChangeConfidenceLevelCommand(
                previous_confidence_level, new_confidence_level, mainform=self
            )
            self._commit_model_operation(change_cl_command.redo)

    def _import_csv(self):
        """Import data from csv file"""
        if not self._authorize_destructive_project_action():
            return
        try:
            wizard = main_wizard.MainWizard(parent=self, path="csv_import")
            if wizard.exec():
                wizard_data = wizard.get_results()
                self._handle_wizard_results(wizard_data)
        finally:
            self._resume_raw_previews()

    def _setup_connections(self, menu_actions=True):
        """Signals & slots"""
        model = self.tableView.model()
        self._model_signal_connections.append(
            app_error_handler.connect_safely(
                model.workspaceEditCommitted,
                self.tableView.cell_content_changed,
                parent=self,
            )
        )
        self._model_signal_connections.append(
            app_error_handler.connect_safely(
                model.workspaceEditCommitted,
                self._workspace_edit_committed,
                parent=self,
            )
        )

        # Model resets clear the active editor, so restore its index explicitly.
        self._model_signal_connections.append(
            app_error_handler.connect_safely(
                model.editFocusRequested, self.set_edit_focus, parent=self
            )
        )

        # Recalculate display-scale values before model resets.
        self._model_signal_connections.append(
            app_error_handler.connect_safely(
                model.modelAboutToBeReset, self._model_about_to_be_reset, parent=self
            )
        )
        self._model_signal_connections.append(
            app_error_handler.connect_safely(
                model.modelReset, self._refresh_workspace_context, parent=self
            )
        )

        self._model_signal_connections.append(
            app_error_handler.connect_safely(
                model.dataError, self.data_error, parent=self
            )
        )
        self._model_signal_connections.append(
            app_error_handler.connect_safely(
                model.rawPreviewRequested, self._schedule_raw_previews, parent=self
            )
        )

        self._model_signal_connections.append(
            app_error_handler.connect_safely(
                self.tableView.dataDirtied, self.data_dirtied, parent=self
            )
        )
        if menu_actions:
            self.nav_add_btn.pressed.connect(
                app_error_handler.safe_slot(self.add_new, parent=self)
            )
            self.nav_right_btn.pressed.connect(
                app_error_handler.safe_slot(self.next, parent=self)
            )
            self.nav_left_btn.pressed.connect(
                app_error_handler.safe_slot(self.previous, parent=self)
            )
            self.nav_up_btn.pressed.connect(
                app_error_handler.safe_slot(self.next_dimension, parent=self)
            )
            self.nav_down_btn.pressed.connect(
                app_error_handler.safe_slot(self.previous_dimension, parent=self)
            )

            _connect_action(self.action_save, self.save)
            _connect_action(self.action_save_as, self.save_as)
            _connect_action(self.action_open, self.open)
            _connect_action(self.action_new_dataset, self.create_new_dataset)
            _connect_action(self.action_quit, self.quit)
            _connect_action(self.action_go, self.go)
            _connect_action(self.action_cum_ma, self.cum_ma)
            _connect_action(self.action_loo_ma, self.loo_ma)

            _connect_action(self.action_undo, self.undo)
            _connect_action(self.action_redo, self.redo)
            _connect_action(self.action_copy, self.tableView.copy)
            _connect_action(self.action_paste, self.tableView.paste)
            _connect_action(
                self.action_auto_fit_columns, self.tableView.auto_fit_columns
            )

            _connect_action(self.action_edit, self.edit_dataset)
            _connect_action(self.action_add_covariate, self.add_covariate)

            _connect_action(self.action_meta_regression, self.meta_reg)
            _connect_action(self.action_reitsma, self.reitsma)
            _connect_action(self.action_publication_bias, self.publication_bias)
            _connect_action(self.action_subgroup_ma, self.meta_subgroup_get_cov)

            _connect_action(self.action_about_legal, self.show_about_legal)
            _connect_action(self.action_change_confidence_level, self._change_global_ci)
            _connect_action(self.action_import_csv, self._import_csv)

    def _update_confidence_level_label(self):
        confidence_level = self.model.get_confidence_level()
        self.cl_label.setText(_format_confidence_level_status(confidence_level))

    def go(self):
        form = None
        if self.model.get_current_outcome_type() in (
            "binary", "continuous", "diagnostic"
        ):
            self._request_standard_analysis_methods(
                self.model.get_confidence_level()
            )
            return
        form = self._build_analysis_specs_dialog(
            confidence_level=self.model.get_confidence_level()
        )
        if form is None:
            return
        form.show()

    def _request_binary_analysis_methods(self, confidence_level):
        self._request_standard_analysis_methods(confidence_level)

    def _request_standard_analysis_methods(self, confidence_level, workflow="standard"):
        if self.analysis_worker.is_busy:
            self._show_analysis_specs_error(
                RuntimeError(
                    "An analysis is already running. Wait for it to finish before opening another."
                )
            )
            return
        run_id = None
        try:
            data_type = self.model.get_current_outcome_type()
            self._ensure_supported_diagnostic_measure(data_type)
            snapshot = self._freeze_standard_analysis_input(data_type)
            run_id = uuid.uuid4().hex
            self._analysis_worker_runs[run_id] = {
                "kind": "methods",
                "input_snapshot": snapshot,
                "confidence_level": confidence_level,
                "workflow": workflow,
            }
            self.statusbar.showMessage("Loading analysis methods…")
            self.analysis_worker.request_methods(
                run_id,
                snapshot.to_mapping(),
                {
                    "data_type": data_type,
                    "metric": snapshot.metric,
                    "workflow": workflow,
                },
            )
        except Exception as error:
            if run_id is not None:
                self._analysis_worker_runs.pop(run_id, None)
            self.statusbar.clearMessage()
            self._show_analysis_specs_error(error)

    def _ensure_supported_diagnostic_measure(self, data_type):
        if data_type == "diagnostic" and self.model.current_effect not in (
            "Sens", "Spec", "PLR", "NLR", "DOR"
        ):
            self.model.current_effect = "Sens"
            self._refresh_workspace_context()

    def _freeze_standard_analysis_input(self, data_type):
        if data_type == "binary":
            from rc_metastudio.analysis_snapshot import (
                _BinaryInputModel,
                freeze_binary_input,
            )

            return freeze_binary_input(cast(_BinaryInputModel, self.model))
        if data_type == "continuous":
            from rc_metastudio.continuous_analysis_snapshot import (
                _DatasetModel,
                freeze_continuous_input,
            )

            return freeze_continuous_input(cast(_DatasetModel, self.model))
        if data_type == "diagnostic":
            from rc_metastudio.diagnostic_analysis_snapshot import (
                _DiagnosticInputModel,
                freeze_diagnostic_input,
            )

            return freeze_diagnostic_input(cast(_DiagnosticInputModel, self.model))
        raise ValueError("Choose a supported analysis outcome first.")

    def meta_reg(self):
        try:
            form = meta_regression_dialog.MetaRegressionDialog(
                self.model, worker_client=self.analysis_worker, parent=self
            )
            self._bind_project_generation(form)
            form.run_requested.connect(
                app_error_handler.safe_slot(
                    lambda snapshot, request: self.submit_meta_regression_analysis(
                        form, snapshot, request
                    ),
                    parent=self,
                )
            )
        except Exception as error:
            self._show_analysis_specs_error(error)
            return
        form.show()

    def reitsma(self):
        try:
            form = reitsma_analysis_dialog.ReitsmaAnalysisDialog(
                self.model, worker_client=self.analysis_worker, parent=self
            )
            self._bind_project_generation(form)
            form.run_requested.connect(
                app_error_handler.safe_slot(
                    lambda snapshot, request: self.submit_reitsma_analysis(
                        form, snapshot, request
                    ),
                    parent=self,
                )
            )
        except Exception as error:
            self._show_analysis_specs_error(error)
            return
        form.show()

    def submit_reitsma_analysis(self, dialog, snapshot, request):
        if not self._require_current_project_dialog(dialog):
            return None
        if self.analysis_worker.is_busy:
            dialog._show_worker_failure(
                {"message": "Wait for the current analysis to finish before running Reitsma."}
            )
            return None
        run_id = uuid.uuid4().hex
        request_mapping = request.to_mapping()
        parameters = request_mapping["params"]
        context = {
            "outcome": snapshot.outcome,
            "time_point": snapshot.time_point,
            "direction": snapshot.groups[0],
            "measure": "Sensitivity and specificity",
            "workflow": "joint Reitsma",
            "method": "diagnostic.reitsma",
            "effective_settings": dict(parameters),
        }
        staging = (
            tempfile.TemporaryDirectory(prefix="rcms-reitsma-%s-" % run_id)
            if request.create_plot
            else None
        )
        self._analysis_worker_runs[run_id] = {
            "kind": "reitsma",
            "dialog": dialog,
            "input_snapshot": snapshot,
            "context": context,
            "spec": None,
            "request": request,
            "staging": staging,
        }
        try:
            self.analysis_worker.submit_reitsma(
                run_id,
                snapshot.to_mapping(),
                request_mapping,
                staging_dir=staging.name if staging is not None else None,
            )
        except Exception:
            self._analysis_worker_runs.pop(run_id, None)
            if staging is not None:
                staging.cleanup()
            raise
        dialog._worker_started(run_id)
        return run_id

    def publication_bias(self):
        from rc_metastudio.small_study_effects_core import (
            freeze_small_study_effects_input,
        )

        form = publication_bias_dialog.PublicationBiasDialog(self.model, parent=self)
        try:
            snapshot = freeze_small_study_effects_input(
                self.model, form.preview_request()
            )
        except Exception as error:
            self._show_analysis_specs_error(error)
            return
        form.set_input_snapshot(snapshot)
        form.preview_requested.connect(
            lambda frozen, request: self.submit_small_study_effects_preview(
                form, frozen, request
            )
        )
        form.analysis_requested.connect(
            lambda frozen, request: self.submit_small_study_effects(
                form, frozen, request
            )
        )
        form.start_preview()
        form.exec()

    def data_dirtied(self):
        self._notify_user_that_data_is_unsaved()
        try:
            runtime = project_adapter.RuntimeProject(
                dataset=self.model.dataset,
                model_state=self.model.get_state(),
                restored_selection=self.model.current_outcome_name is not None,
            )
        except project_adapter.ProjectAdapterError:
            self.workspace.mark_dirty()
        else:
            self.workspace.update_live_state(runtime)
            self.workspace.checkpoint()

    def _workspace_edit_committed(self, _edit):
        self.data_dirtied()

    def _commit_model_operation(self, operation):
        """Run one already validated UI operation as one workspace change."""
        self.workspace.begin_change()
        try:
            operation()
        finally:
            self.workspace.end_change()

    def _undo_clean_changed(self, is_clean):
        """Keep project dirty state aligned with the active undo history."""
        if not is_clean:
            self._notify_user_that_data_is_unsaved()

    def meta_subgroup_get_cov(self):
        form = subgroup_analysis_dialog.SubgroupAnalysisDialog(self.model, parent=self)
        self._bind_project_generation(form)
        form.show()

    def cum_ma(self):
        self._request_standard_analysis_methods(
            self.model.get_confidence_level(), workflow="cumulative"
        )

    def loo_ma(self):
        self._request_standard_analysis_methods(
            self.model.get_confidence_level(), workflow="leave-one-out"
        )

    def show_about_legal(self):
        return about_legal_dialog.AboutLegalDialog(self).exec()

    def meta_subgroup(self, selected_covariate, missing_policy):
        from rc_metastudio.subgroup_analysis import (
            create_subgroup_plan,
        )

        try:
            data_type = self.model.get_current_outcome_type()
            if data_type == "binary":
                from rc_metastudio.analysis_snapshot import (
                    _BinaryInputModel,
                    freeze_binary_input,
                )

                snapshot = freeze_binary_input(cast(_BinaryInputModel, self.model))
            elif data_type == "continuous":
                from rc_metastudio.continuous_analysis_snapshot import (
                    _DatasetModel,
                    freeze_continuous_input,
                )

                snapshot = freeze_continuous_input(cast(_DatasetModel, self.model))
            elif data_type == "diagnostic":
                from rc_metastudio.diagnostic_analysis_snapshot import (
                    _DiagnosticInputModel,
                    freeze_diagnostic_input,
                )

                snapshot = freeze_diagnostic_input(
                    cast(_DiagnosticInputModel, self.model), include_covariates=True
                )
            else:
                raise ValueError(
                    "Subgroup analysis needs a binary, continuous, or diagnostic outcome."
                )
            plan = create_subgroup_plan(
                snapshot, selected_covariate, missing_policy=missing_policy
            )
            self._request_subgroup_analysis_methods(snapshot, plan)
        except Exception as error:
            self._show_analysis_specs_error(error)

    def _request_subgroup_analysis_methods(
        self, snapshot, plan, *, initial_parameters=None, initial_method=None
    ):
        from rc_metastudio.subgroup_analysis import prepare_subgroup_snapshot

        if self.analysis_worker.is_busy:
            self._show_analysis_specs_error(
                RuntimeError(
                    "An analysis is already running. Wait for it to finish before opening another."
                )
            )
            return
        run_id = None
        try:
            prepared = prepare_subgroup_snapshot(snapshot, plan)
            run_id = uuid.uuid4().hex
            self._analysis_worker_runs[run_id] = {
                "kind": "subgroup_methods",
                "input_snapshot": prepared,
                "original_snapshot": snapshot,
                "subgroup_plan": plan,
                "confidence_level": self.model.get_confidence_level(),
                "workflow": "subgroup",
                "document_generation": self._document_generation,
                "initial_parameters": initial_parameters,
                "initial_method": initial_method,
            }
            self.statusbar.showMessage("Loading subgroup analysis methods…")
            self.analysis_worker.request_methods(
                run_id,
                prepared.to_mapping(),
                {
                    "data_type": plan.family,
                    "metric": plan.metric,
                    "workflow": "subgroup",
                },
            )
        except Exception as error:
            if run_id is not None:
                self._analysis_worker_runs.pop(run_id, None)
            self.statusbar.clearMessage()
            self._show_analysis_specs_error(error)

    def _build_analysis_specs_dialog(
        self,
        analysis_type=None,
        external_params=None,
        diagnostic_metrics=None,
        confidence_level=None,
    ):
        try:
            draft = self._matching_analysis_draft(self.model, analysis_type)
            form = self._create_analysis_specs_dialog(
                analysis_type,
                external_params,
                diagnostic_metrics,
                confidence_level,
                draft,
            )
            form.correction_requested.connect(self._focus_issue_target)
            if draft is not None:
                self._restore_analysis_draft_method(form, draft)
            self._attach_analysis_draft(form, draft)
            return form
        except Exception as e:
            self._show_analysis_specs_error(e)
            return None

    def _create_analysis_specs_dialog(
        self,
        analysis_type,
        external_params,
        diagnostic_metrics,
        confidence_level,
        draft,
    ):
        saved_parameters = draft["settings"]["parameters"] if draft is not None else {}
        kwargs = {
            "analysis_type": analysis_type,
            "parent": self,
            "confidence_level": saved_parameters.get("conf.level", confidence_level),
        }
        if saved_parameters or external_params is not None:
            kwargs["external_params"] = {
                **saved_parameters,
                **(external_params or {}),
            }
        if diagnostic_metrics is not None:
            kwargs["diagnostic_metrics"] = diagnostic_metrics
        if analysis_type is None and self.model.get_current_outcome_type() == "binary":
            kwargs["analysis_worker"] = self.analysis_worker
        return analysis_setup_dialog.AnalysisSetupDialog(
            self.model, analysis_service=self.analysis_service, **kwargs
        )

    def _show_analysis_specs_error(self, exception):
        if isinstance(exception, r_backend.AnalysisBackendUnavailableError):
            self._show_analysis_backend_error(exception)
        else:
            self._show_analysis_preparation_error(exception)

    def _show_analysis_backend_error(self, exception):
        message = (
            "The analysis backend could not be reached, so "
            "RC MetaStudio cannot build the Method & Parameters dialog.\n\n"
            "Details: %s: %s" % (exception.__class__.__name__, exception)
        )
        QMessageBox.critical(self, "Analysis Backend Unavailable", message)

    def _show_analysis_preparation_error(self, exception):
        message = (
            "RC MetaStudio could not prepare the Method & Parameters dialog "
            "for this analysis.\n\n"
            "Details: %s: %s" % (exception.__class__.__name__, exception)
        )
        QMessageBox.critical(self, "Could Not Prepare Analysis", message)

    def undo(self):
        if self.workspace.undo():
            runtime = self.workspace.runtime
            if runtime is not None:
                self._install_workspace_runtime(runtime)

    def redo(self):
        if self.workspace.redo():
            runtime = self.workspace.runtime
            if runtime is not None:
                self._install_workspace_runtime(runtime)

    def _install_workspace_runtime(self, runtime):
        target_digest = self.workspace.runtime_digest
        current = self.tableView.currentIndex()
        position = (current.row(), current.column()) if current.isValid() else None
        self._set_model_adapter(
            runtime.dataset,
            runtime.model_state,
            preserve_state_selection=runtime.restored_selection,
            recalculate_outcomes=False,
        )
        self.workspace.update_live_state(runtime)
        self.workspace.checkpoint(expected_digest=target_digest)
        self.out_path = str(self.workspace.path) if self.workspace.path else None
        if position is not None:
            self.tableView.setCurrentIndex(self.model.index(*position))
        self._refresh_workspace_results()

    def edit_dataset(self):
        current_dataset = self.workspace.snapshot().dataset
        edit_window = edit_dialog.EditDialog(current_dataset, parent=self)

        if edit_window.exec():
            # if we edited the current dataset when there was no
            # outcome yet, then we want to default to an outcome
            # that was added.

            old_state_dict = self.tableView.model().get_state()
            new_state_dict = copy.deepcopy(old_state_dict)

            # update the new state dict to reflect the currently selected
            # outcomes, etc.
            outcome_model = edit_window.outcomes_model
            edited_outcomes = outcome_model.outcome_list
            if outcome_model.current_outcome_name is not None:
                new_state_dict["current_outcome_name"] = (
                    outcome_model.current_outcome_name
                )
            elif old_state_dict["current_outcome_name"] in edited_outcomes:
                new_state_dict["current_outcome_name"] = old_state_dict[
                    "current_outcome_name"
                ]
            elif edited_outcomes:
                # If the current outcome was removed, select the first remaining one.
                new_state_dict["current_outcome_name"] = edited_outcomes[0]
            else:
                new_state_dict["current_outcome_name"] = None

            new_state_dict["current_follow_up_index"] = max(
                edit_window.follow_up_list.currentIndex().row(), 0
            )
            group_names = edit_window.groups_model.group_list

            if len(group_names) >= 2:
                new_state_dict["current_groups"] = group_names[:2]
            else:
                new_state_dict["current_groups"] = meta_globals.DEFAULT_GROUP_NAMES
            modified_dataset = edit_window.dataset

            self._commit_model_operation(
                lambda: self.set_model(modified_dataset, new_state_dict)
            )

    def populate_metrics_menu(self, metric_to_check=None):
        """Populates the `metric` sub-menu with available metrics for the
        current datatype.
        """
        # Clearing a checked QAction emits ``toggled(False)`` while Qt tears the
        # old submenu down.  Those actions are connected to ``metric_selected``,
        # which would otherwise recalculate every study while a restored
        # project's menu is being rebuilt.  A document open must preserve the
        # persisted effects rather than treating menu destruction as a user edit.
        for menu_action in self.menuMetric.actions():
            menu_action.blockSignals(True)
            submenu = menu_action.menu()
            if submenu is not None:
                for action in submenu.actions():
                    action.blockSignals(True)
        self.menuMetric.clear()
        self.menuMetric.setDisabled(False)

        if self.model.get_current_outcome_type() == "binary":
            self.add_binary_metrics(metric_to_check=metric_to_check)
            self.metric_menu_is_set_for = meta_globals.BINARY

        elif self.model.get_current_outcome_type() == "continuous":
            self.add_continuous_metrics(metric_to_check=metric_to_check)
            self.metric_menu_is_set_for = meta_globals.CONTINUOUS

        else:
            # diagnostic data; deactive metrics option
            # we always show sens. + spec. for diag. data.
            self.menuMetric.setDisabled(True)
            self.metric_menu_is_set_for = meta_globals.DIAGNOSTIC

    def add_binary_metrics(self, metric_to_check=None):
        self.add_metrics(
            meta_globals.BINARY_ONE_ARM_METRICS,
            meta_globals.BINARY_TWO_ARM_METRICS,
            metric_to_check=metric_to_check,
        )

    def add_continuous_metrics(self, metric_to_check=None):
        self.add_metrics(
            meta_globals.CONTINUOUS_ONE_ARM_METRICS,
            meta_globals.CONTINUOUS_TWO_ARM_METRICS,
            metric_to_check=metric_to_check,
        )

    def add_metrics(self, one_arm_metrics, two_arm_metrics, metric_to_check=None):
        # we'll add sub-menus for two-arm and one-arm metrics
        self.twoArmMetricMenu = self.add_sub_metric_menu("Two-arm metrics")
        self.oneArmMetricMenu = self.add_sub_metric_menu("One-arm metrics")

        for i, metric in enumerate(two_arm_metrics):
            metric_action = self.add_metric_action(metric, self.twoArmMetricMenu)
            if metric == metric_to_check or (metric_to_check is None and i == 0):
                # arbitrarily check the first metric in the case that none
                # is specificied
                metric_action.blockSignals(True)
                metric_action.setChecked(True)
                metric_action.blockSignals(False)

        # now add the one-arm metrics
        for metric in one_arm_metrics:
            metric_action = self.add_metric_action(metric, self.oneArmMetricMenu)
            if metric == metric_to_check:
                metric_action.blockSignals(True)
                metric_action.setChecked(True)
                metric_action.blockSignals(False)

    def add_sub_metric_menu(self, name):
        sub_menu = QtWidgets.QMenu(str(name), self.menuMetric)
        sub_menu.setToolTip(
            "Choose a %s effect-size measure or calculator metric." % str(name).lower()
        )
        sub_menu.setStatusTip(sub_menu.toolTip())
        self.menuMetric.addAction(sub_menu.menuAction())
        return sub_menu

    def add_metric_action(self, metric, menu):
        metric_names = meta_globals.ALL_METRIC_NAMES

        metric_action = QAction(str(metric + ": " + metric_names[metric]), self)
        metric_action.setToolTip(metric_names[metric])
        metric_action.setStatusTip(metric_names[metric])
        metric_action.setData(metric)
        metric_action.setCheckable(True)
        metric_action.toggled.connect(
            app_error_handler.safe_slot(
                lambda checked=False, metric=metric, menu=menu: self.metric_selected(
                    metric, menu
                ),
                parent=self,
            )
        )
        menu.addAction(metric_action)
        return metric_action

    def deselect_all_metrics(self):
        data_type = self.tableView.model().get_current_outcome_type(get_str=False)
        if data_type in (meta_globals.BINARY, meta_globals.CONTINUOUS):
            for menu_action in self.menuMetric.actions():
                sub_menu = menu_action.menu()
                if sub_menu is None:
                    continue
                for action in sub_menu.actions():
                    action.blockSignals(True)
                    action.setChecked(False)
                    action.blockSignals(False)

    def metric_selected(self, metric_name, menu):
        self.deselect_all_metrics()

        for action in menu.actions():
            action_data = _qt_item_text(action.data())
            if action_data == metric_name:
                action.blockSignals(True)
                action.setChecked(True)
                action.blockSignals(False)

        self.tableView.model().set_current_metric(metric_name)
        self.model.hydrate_derived_previews()
        self.model.reset_model()
        self.tableView.synchronize_column_widths()

    def submit_binary_analysis(self, dialog, snapshot, request):
        return self.submit_standard_analysis(dialog, snapshot, request)

    def submit_meta_regression_analysis(self, dialog, snapshot, request):
        if not self._require_current_project_dialog(dialog):
            return None
        if self.analysis_worker.is_busy:
            raise RuntimeError(
                "An analysis is already running. Wait for it to finish before starting another."
            )
        run_id = uuid.uuid4().hex
        effective_request = self._meta_regression_request(snapshot, request, run_id)
        context = self._meta_regression_context(snapshot, effective_request)
        self._analysis_worker_runs[run_id] = {
            "kind": "meta_regression",
            "dialog": dialog,
            "input_snapshot": snapshot,
            "context": context,
            "spec": None,
            "request": effective_request,
        }
        try:
            self.analysis_worker.submit_meta_regression(
                run_id, snapshot.to_mapping(), effective_request.to_mapping()
            )
        except Exception:
            self._analysis_worker_runs.pop(run_id, None)
            raise
        dialog._worker_started(run_id)
        return run_id

    @staticmethod
    def _meta_regression_request(snapshot, request, run_id):
        plot_output_path = None
        plot_display_path = None
        if request.create_plot and snapshot.data_type == "diagnostic":
            plot_output_path = analysis_output_path(
                "meta-regression-%s.svg" % run_id
            )
        elif (
            request.create_plot
            and len(snapshot.moderators) == 1
            and snapshot.moderators[0].kind == "continuous"
        ):
            plot_output_path = analysis_output_path(
                "meta-regression-%s.png" % run_id
            )
            plot_display_path = analysis_setup_dialog._display_svg_path(
                plot_output_path
            )
        return replace(
            request,
            plot_output_path=plot_output_path,
            plot_display_path=plot_display_path,
        )

    @staticmethod
    def _meta_regression_context(snapshot, effective_request):
        request_mapping = effective_request.to_mapping()
        parameters = request_mapping.get("params", {})
        if not isinstance(parameters, Mapping):
            raise ValueError("meta-regression parameters must be a mapping")
        return {
            "outcome": snapshot.outcome,
            "time_point": snapshot.time_point,
            "direction": (
                snapshot.groups[0]
                if len(snapshot.groups) == 1
                else "%s versus %s" % snapshot.groups
            ),
            "measure": snapshot.metric,
            "workflow": "meta-regression",
            "method": effective_request.method,
            "effective_settings": {
                **{
                    key: value
                    for key, value in parameters.items()
                    if not key.endswith(("outpath", "display_path"))
                },
                "missing_moderator_policy": effective_request.missing_moderator_policy,
                "moderators": [
                    {
                        "name": moderator.name,
                        "kind": moderator.kind,
                        "unit": moderator.unit,
                        "unit_step": moderator.unit_step,
                        "reference_level": moderator.reference_level,
                    }
                    for moderator in snapshot.moderators
                ],
            },
        }

    def submit_small_study_effects_preview(self, dialog, snapshot, request):
        if self.analysis_worker.is_busy:
            dialog._show_request_failure(
                "An analysis is already running. Wait for it to finish before checking eligibility."
            )
            return None
        run_id = uuid.uuid4().hex
        self._analysis_worker_runs[run_id] = {
            "kind": "small_study_effects_preview",
            "dialog": dialog,
            "input_snapshot": snapshot,
            "request": request,
        }
        dialog.begin_worker_request(run_id, "preview")
        try:
            self.analysis_worker.request_small_study_effects_preview(
                run_id, snapshot.to_mapping(), request.to_mapping()
            )
        except Exception as error:
            self._analysis_worker_runs.pop(run_id, None)
            dialog._worker_failed(run_id, {"message": str(error)})
            return None
        return run_id

    def submit_small_study_effects(self, dialog, snapshot, request):
        if self.analysis_worker.is_busy:
            dialog._show_request_failure(
                "An analysis is already running. Wait for it to finish before running small-study effects."
            )
            return None
        run_id = uuid.uuid4().hex
        staging = tempfile.TemporaryDirectory(
            prefix="rcms-small-study-%s-" % run_id
        )
        groups = snapshot.groups
        context = {
            "outcome": snapshot.outcome,
            "time_point": getattr(snapshot, "time_point", getattr(snapshot, "follow_up", "")),
            "direction": groups[0] if len(groups) == 1 else "%s versus %s" % groups,
            "measure": snapshot.metric,
            "workflow": "small-study effects",
            "method": "RCMetaR small-study effects report",
            "effective_settings": request.to_mapping(),
        }
        self._analysis_worker_runs[run_id] = {
            "kind": "small_study_effects",
            "dialog": dialog,
            "input_snapshot": snapshot,
            "context": context,
            "spec": None,
            "request": request,
            "staging": staging,
        }
        dialog.begin_worker_request(run_id, "analysis")
        try:
            self.analysis_worker.submit_small_study_effects(
                run_id,
                snapshot.to_mapping(),
                request.to_mapping(),
                staging_dir=staging.name,
            )
        except Exception as error:
            self._analysis_worker_runs.pop(run_id, None)
            staging.cleanup()
            dialog._worker_failed(run_id, {"message": str(error)})
            return None
        return run_id

    def submit_standard_analysis(self, dialog, snapshot, request):
        if request.workflow == "subgroup":
            return self.submit_subgroup_analysis(dialog, snapshot, request)
        if self.analysis_worker.is_busy:
            raise RuntimeError(
                "An analysis is already running. Wait for it to finish before starting another."
            )
        run_id = uuid.uuid4().hex
        effective_request = _request_with_run_output_paths(request, run_id)
        base_snapshot = getattr(snapshot, "input_snapshot", snapshot)
        context = {
            "outcome": base_snapshot.outcome,
            "time_point": getattr(base_snapshot, "time_point", getattr(base_snapshot, "follow_up", "first")),
            "direction": (
                base_snapshot.groups[0]
                if len(base_snapshot.groups) == 1
                else "%s versus %s" % base_snapshot.groups
            ),
            "measure": effective_request.metric,
            "workflow": effective_request.workflow,
            "method": effective_request.method,
            "effective_settings": {
                key: value
                for key, value in effective_request.parameter_values().items()
                if not key.startswith(("fp_", "bp_"))
            },
        }
        edit_copy_spec = analysis_draft.AnalysisEditCopy(snapshot, effective_request)
        self._analysis_worker_runs[run_id] = {
            "dialog": dialog,
            "input_snapshot": snapshot,
            "context": context,
            "spec": edit_copy_spec,
            "request": effective_request,
        }
        try:
            self.analysis_worker.submit(
                run_id, snapshot.to_mapping(), effective_request.to_mapping()
            )
        except Exception:
            self._analysis_worker_runs.pop(run_id, None)
            raise
        return run_id

    def submit_subgroup_analysis(self, dialog, prepared_snapshot, request):
        if not self._require_current_project_dialog(dialog):
            return None
        if self.analysis_worker.is_busy:
            dialog._show_worker_failure(
                {"message": "Wait for the current analysis to finish before running this subgroup analysis."}
            )
            return None
        original_snapshot, plan = self._validate_subgroup_submission(
            dialog, prepared_snapshot, request
        )
        run_id = uuid.uuid4().hex
        effective_request = _request_with_run_output_paths(request, run_id)
        context = self._subgroup_analysis_context(
            original_snapshot, plan, effective_request
        )
        self._analysis_worker_runs[run_id] = {
            "kind": "subgroup",
            "dialog": dialog,
            "input_snapshot": original_snapshot,
            "prepared_snapshot": prepared_snapshot,
            "subgroup_plan": plan,
            "context": context,
            "spec": analysis_draft.AnalysisEditCopy(
                original_snapshot, effective_request
            ),
            "request": effective_request,
        }
        try:
            self.analysis_worker.submit_subgroup(
                run_id,
                original_snapshot.to_mapping(),
                effective_request.to_mapping(),
                plan.to_mapping(),
            )
        except Exception:
            self._analysis_worker_runs.pop(run_id, None)
            raise
        return run_id

    @staticmethod
    def _validate_subgroup_submission(dialog, prepared_snapshot, request):
        from rc_metastudio.subgroup_analysis import (
            create_subgroup_request,
            prepare_subgroup_snapshot,
        )
        original_snapshot = getattr(dialog, "_subgroup_original_snapshot", None)
        plan = getattr(dialog, "_subgroup_plan", None)
        if original_snapshot is None or plan is None:
            raise ValueError("Subgroup setup has no frozen input plan.")
        expected_prepared = prepare_subgroup_snapshot(original_snapshot, plan)
        if expected_prepared != prepared_snapshot:
            raise ValueError("Subgroup setup no longer matches its frozen study rows.")
        expected_request = create_subgroup_request(
            original_snapshot,
            plan,
            method=request.method,
            parameters=request.parameter_values(),
        )
        if expected_request.semantic_id != request.semantic_id:
            raise ValueError("Subgroup method settings do not match their frozen plan.")
        return original_snapshot, plan

    @staticmethod
    def _subgroup_analysis_context(original_snapshot, plan, effective_request):
        settings = MainWindow._subgroup_analysis_settings(plan, effective_request)
        groups = original_snapshot.groups
        return {
            "outcome": original_snapshot.outcome,
            "time_point": getattr(
                original_snapshot,
                "time_point",
                getattr(original_snapshot, "follow_up", "first"),
            ),
            "direction": " versus ".join(groups),
            "measure": effective_request.metric,
            "workflow": "subgroup analysis",
            "method": effective_request.method,
            "effective_settings": settings,
        }

    @staticmethod
    def _subgroup_analysis_settings(plan, effective_request):
        excluded_names, missing_category_names = MainWindow._subgroup_study_status_names(plan)
        settings = {
            key: value
            for key, value in effective_request.parameter_values().items()
            if not key.startswith(("fp_", "bp_"))
        }
        settings.update(
            {
                "covariate_name": plan.covariate_name,
                "missing_value_policy": plan.missing_policy,
                "included_study_count": plan.included_count,
                "excluded_studies": excluded_names,
                "missing_category_studies": missing_category_names,
            }
        )
        return settings

    @staticmethod
    def _subgroup_study_status_names(plan):
        excluded_names = []
        missing_category_names = []
        for assignment in plan.assignments:
            if assignment.status == "excluded_missing":
                excluded_names.append(assignment.study_name)
            if (
                assignment.value is None or assignment.value == ""
            ) and plan.missing_policy == "missing_category":
                missing_category_names.append(assignment.study_name)
        return excluded_names, missing_category_names

    def _analysis_worker_progress(self, run_id, stage):
        run = self._analysis_worker_runs.get(run_id)
        if run is not None:
            if run.get("kind") in ("methods", "edit_methods", "subgroup_methods", "raw_previews"):
                self.statusbar.showMessage(stage)
            else:
                run["dialog"]._worker_progress(run_id, stage)

    def _schedule_raw_previews(self):
        if not self._raw_previews_paused and not self.analysis_worker.is_busy:
            self._raw_preview_timer.start(200)

    def _raw_preview_worker_busy_changed(self, busy):
        if not busy:
            self._schedule_raw_previews()

    def _submit_raw_previews(self):
        if self._raw_previews_paused or self.analysis_worker.is_busy:
            return
        model = self.model
        requests = model.take_pending_raw_previews(limit=32)
        if not requests:
            return
        calls = [
            {
                "id": str(request.study_id),
                "operation": "calculate_raw_effects",
                "args": {
                    "data_type": request.context.data_type,
                    "effect": request.context.current_effect,
                    "raw_data": list(request.raw_data),
                    "confidence_level": request.context.confidence_level,
                },
            }
            for request in requests
        ]
        run_id = uuid.uuid4().hex
        self._analysis_worker_runs[run_id] = {
            "kind": "raw_previews",
            "model": model,
            "document_generation": self._document_generation,
            "requests": {str(request.study_id): request for request in requests},
        }
        try:
            self.analysis_worker.submit_calculator(run_id, calls)
        except Exception as error:
            self._analysis_worker_runs.pop(run_id, None)
            self.statusbar.showMessage(f"Study previews could not start: {error}", 8000)

    def _raw_previews_completed(self, run_id, payload):
        run = self._analysis_worker_runs.pop(run_id, None)
        if run is None or run.get("kind") != "raw_previews":
            return
        if run["model"] is not self.model or run["document_generation"] != self._document_generation:
            return
        try:
            requests = run["requests"]
            calls = _validated_raw_preview_calls(payload, requests)
            for item in calls:
                self.model.apply_worker_raw_preview(requests[item["id"]], item["result"])
        except (KeyError, TypeError, ValueError) as error:
            self.statusbar.showMessage(f"Study preview failed: {error}", 8000)
        else:
            self.statusbar.clearMessage()
        self._schedule_raw_previews()

    def _focus_issue_target(self, target):
        self._select_issue_target_context(target)
        row_column = self._issue_target_row_column(target)
        if row_column is None:
            return
        row, column = row_column
        self.workspace_tabs.setCurrentWidget(self.nav_frame)
        cell = self.model.index(row, column)
        self.tableView.setCurrentIndex(cell)
        self.tableView.scrollTo(cell)
        self.tableView.setFocus()

    def _select_issue_target_context(self, target):
        dataset = self.model.dataset
        outcome = dataset.outcomes_by_id.get(target.outcome_identity)
        if outcome is not None and outcome.name != self.model.current_outcome_name:
            self.display_outcome(outcome.name)
        if outcome is not None and target.follow_up_identity is not None:
            follow_up = dataset.follow_ups_by_outcome_id.get(outcome.stable_id, {}).get(
                target.follow_up_identity
            )
            if (
                follow_up is not None
                and follow_up.label != self.model.get_current_follow_up_name()
            ):
                self.display_follow_up(
                    self.model.get_t_point_for_follow_up_name(follow_up.label)
                )
        return outcome

    def _issue_target_row_column(self, target):
        ordered_ids = self.model.get_ordered_study_ids()
        if target.study_id not in ordered_ids:
            return None
        row = ordered_ids.index(target.study_id)
        column = next(
            (
                index
                for index in range(self.model.columnCount())
                if self.model.workspace_column_identity(index)
                == target.field_identity
            ),
            self.model.NAME,
        )
        return row, column

    def _analysis_worker_methods_ready(self, run_id, catalogue, _backend_versions):
        run = self._analysis_worker_runs.pop(run_id, None)
        self.statusbar.clearMessage()
        if run is None or run.get("kind") not in {"methods", "edit_methods", "subgroup_methods"}:
            return
        try:
            self._open_analysis_methods_form(run, catalogue)
        except Exception as error:
            self._show_analysis_specs_error(error)

    def _open_analysis_methods_form(self, run, catalogue):
        editing_copy = run["kind"] == "edit_methods"
        subgroup_setup = run["kind"] == "subgroup_methods"
        if subgroup_setup and run["document_generation"] != self._document_generation:
            return
        service = analysis_adapter.AnalysisMethodCatalogue(catalogue)
        draft_model = self._analysis_methods_draft_model(run, editing_copy)
        base_snapshot = getattr(
            run["input_snapshot"], "input_snapshot", run["input_snapshot"]
        )
        draft = self._analysis_methods_matching_draft(
            run, draft_model, editing_copy, subgroup_setup
        )
        parameters = self._analysis_methods_parameters(
            run, draft, editing_copy, subgroup_setup
        )
        confidence_level = self._analysis_methods_confidence(
            run, parameters, editing_copy
        )
        workflow = run["workflow"]
        form = analysis_setup_dialog.AnalysisSetupDialog(
            draft_model,
            analysis_service=service,
            analysis_worker=self.analysis_worker,
            frozen_snapshot=base_snapshot,
            confidence_level=confidence_level,
            external_params=parameters,
            analysis_type=workflow if workflow != "standard" else None,
            parent=self,
        )
        form.correction_requested.connect(self._focus_issue_target)
        self._configure_analysis_methods_form(
            form, run, draft, editing_copy, subgroup_setup
        )
        form.show()

    @staticmethod
    def _analysis_methods_draft_model(run, editing_copy):
        if editing_copy:
            return run["draft_model"]
        return analysis_draft.model_for_snapshot(run["input_snapshot"])

    def _analysis_methods_matching_draft(
        self, run, draft_model, editing_copy, subgroup_setup
    ):
        if editing_copy or subgroup_setup:
            return None
        workflow = run["workflow"]
        return self._matching_analysis_draft(
            draft_model, workflow if workflow != "standard" else None
        )

    @staticmethod
    def _analysis_methods_parameters(run, draft, editing_copy, subgroup_setup):
        if editing_copy:
            return run["parameters"]
        if subgroup_setup:
            return {
                **(run["initial_parameters"] or {}),
                "cov_name": run["subgroup_plan"].covariate_name,
            }
        return draft["settings"]["parameters"] if draft is not None else None

    @staticmethod
    def _analysis_methods_confidence(run, parameters, editing_copy):
        if editing_copy:
            return run["parameters"].get(
                "conf.level", meta_globals.DEFAULT_CONFIDENCE_LEVEL
            )
        if parameters is not None:
            return parameters.get("conf.level", run["confidence_level"])
        return run["confidence_level"]

    def _configure_analysis_methods_form(
        self, form, run, draft, editing_copy, subgroup_setup
    ):
        self._configure_subgroup_form(form, run, subgroup_setup)
        self._configure_cumulative_copy_form(form, run, editing_copy)
        self._restore_analysis_methods_selection(
            form, run, draft, editing_copy, subgroup_setup
        )
        self._attach_methods_form_draft(form, draft, subgroup_setup)

    def _configure_subgroup_form(self, form, run, subgroup_setup):
        if not subgroup_setup:
            return
        form._subgroup_original_snapshot = run["original_snapshot"]
        form._subgroup_plan = run["subgroup_plan"]
        self._bind_project_generation(form)

    def _configure_cumulative_copy_form(self, form, run, editing_copy):
        if editing_copy and run["workflow"] == "cumulative":
            self._restore_cumulative_ordering(form, run["input_snapshot"].ordering)

    def _restore_analysis_methods_selection(
        self, form, run, draft, editing_copy, subgroup_setup
    ):
        if editing_copy or (subgroup_setup and run["initial_method"]):
            selected_method = run["method"] if editing_copy else run["initial_method"]
            self._select_analysis_method(form, selected_method)
        elif draft is not None:
            self._restore_analysis_draft_method(form, draft)

    def _attach_methods_form_draft(self, form, draft, subgroup_setup):
        if subgroup_setup:
            form._analysis_draft_id = None
        else:
            self._attach_analysis_draft(form, draft)

    @staticmethod
    def _restore_cumulative_ordering(form, ordering):
        form.cumulative_order_field.setCurrentIndex(
            form.cumulative_order_field.findData(ordering.field)
        )
        form.cumulative_direction.setCurrentIndex(
            form.cumulative_direction.findData(ordering.direction)
        )
        if ordering.missing_year_policy is not None:
            form.cumulative_missing_year.setCurrentIndex(
                form.cumulative_missing_year.findData(ordering.missing_year_policy)
            )

    @staticmethod
    def _select_analysis_method(form, selected_method):
        for label, method in form.available_method_d.items():
            if method == selected_method:
                form.method_cbo_box.setCurrentText(label)
                return
        QMessageBox.warning(
            form,
            "Saved Method Unavailable",
            "The saved method is unavailable in this analysis engine. "
            "Choose a method before running the copy.",
        )

    def _analysis_worker_completed(
        self, run_id, result_payload, warnings, backend_versions
    ):
        run = self._analysis_worker_runs.pop(run_id, None)
        if run is None:
            return
        if run.get("kind") == "small_study_effects_preview":
            run["dialog"]._worker_preview_completed(run_id, result_payload)
            return
        result = self._parse_completed_worker_result(run_id, run, result_payload)
        if result is None:
            return
        saved = self._save_completed_worker_result(
            run_id, run, result, result_payload, warnings, backend_versions
        )
        if saved is None:
            return
        result, record, display_assets = saved
        delivered = self._deliver_completed_worker_result(
            run_id, run, result, record, display_assets
        )
        if delivered:
            self._finish_analysis_draft(run)
        run["dialog"]._worker_completed(run_id, delivered, warnings)

    def _parse_completed_worker_result(self, run_id, run, result_payload):
        try:
            from rc_metastudio.analysis_results import parse_analysis_result

            return parse_analysis_result(result_payload)
        except Exception as error:
            app_error_handler.log_exception(type(error), error, error.__traceback__)
            _cleanup_analysis_staging(run)
            if run.get("kind") == "small_study_effects":
                run["dialog"]._worker_failed(run_id, {"message": str(error)})
            else:
                run["dialog"]._show_analysis_failure(error, requests=(run["request"],))
                run["dialog"]._worker_completed(run_id, False)
            return None

    def _save_completed_worker_result(
        self, run_id, run, result, result_payload, warnings, backend_versions
    ):
        display_assets = None
        try:
            record = saved_result_adapter.capture_result(
                run["input_snapshot"].to_mapping(),
                run["request"].to_mapping(),
                result_payload,
                warnings=tuple(str(warning) for warning in warnings),
                backend_versions=backend_versions,
            )
            if run.get("kind") in {"reitsma", "small_study_effects"}:
                display_assets = tempfile.TemporaryDirectory(
                    prefix="rcms-%s-display-" % run["kind"]
                )
                result = saved_result_adapter.restore_result(
                    record, Path(display_assets.name)
                )
                _cleanup_analysis_staging(run)
            self.workspace.add_saved_analysis(record)
            self._refresh_workspace_results()
            self._notify_user_that_data_is_unsaved()
        except Exception as error:
            self._worker_result_save_failed(run_id, run, display_assets, error)
            return None
        return result, record, display_assets

    def _worker_result_save_failed(self, run_id, run, display_assets, error):
        app_error_handler.log_exception(type(error), error, error.__traceback__)
        _cleanup_analysis_staging(run)
        if display_assets is not None:
            display_assets.cleanup()
        dialog = QMessageBox(
            QMessageBox.Icon.Warning,
            "Analysis Was Not Saved",
            "The analysis completed, but its result could not be retained in "
            "this project. Keep the analysis settings open and retry after "
            "correcting the problem.\n\nDetails: %s: %s"
            % (type(error).__name__, error),
            QMessageBox.StandardButton.Ok,
            self,
        )
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.open()
        if run.get("kind") == "small_study_effects":
            run["dialog"]._worker_failed(
                run_id,
                {"message": "The result could not be saved. Settings remain open for retry."},
            )
        else:
            run["dialog"]._worker_completed(run_id, False)

    def _deliver_completed_worker_result(
        self, run_id, run, result, record, display_assets
    ):
        try:
            return self._present_completed_worker_result(
                run, result, record, display_assets
            )
        except Exception as error:
            self._worker_result_delivery_failed(run_id, run, display_assets, error)
            return False

    def _present_completed_worker_result(
        self, run, result, record, display_assets
    ) -> bool:
        kind = run.get("kind")
        if kind in {"reitsma", "small_study_effects"}:
            edit_copy_spec = run["spec"] if kind == "reitsma" else record.value
            form = self._show_analysis_result(
                result, context=run["context"], edit_copy_spec=edit_copy_spec
            )
            if display_assets is not None:
                form.destroyed.connect(lambda: display_assets.cleanup())
            self.workspace_tabs.setCurrentWidget(self.results_panel)
            return True
        edit_copy_spec = record.value if kind == "subgroup" else run["spec"]
        delivered = self.analysis(
            result,
            context=run["context"],
            edit_copy_spec=edit_copy_spec,
        )
        if delivered:
            self.workspace_tabs.setCurrentWidget(self.results_panel)
        return delivered

    def _worker_result_delivery_failed(self, run_id, run, display_assets, error):
        app_error_handler.log_exception(type(error), error, error.__traceback__)
        _cleanup_analysis_staging(run)
        if display_assets is not None:
            display_assets.cleanup()
        if run.get("kind") == "small_study_effects":
            run["dialog"]._worker_failed(run_id, {"message": str(error)})
            return
        run["dialog"]._show_analysis_failure(error, requests=(run["request"],))
        run["dialog"]._worker_completed(run_id, False)

    def _finish_analysis_draft(self, run):
        form = run["dialog"]
        timer = getattr(form, "_draft_change_timer", None)
        if timer is not None:
            timer.stop()
        record_id = getattr(form, "_analysis_draft_id", None)
        if record_id is not None:
            self.workspace.delete_analysis_draft(record_id)
            self._refresh_workspace_results()
            form._analysis_draft_id = None

    def _analysis_worker_failed(self, run_id, error):
        run = self._analysis_worker_runs.pop(run_id, None)
        if run is None:
            return
        if self._handle_raw_preview_failure(run, error):
            return
        _cleanup_analysis_staging(run)
        if self._handle_method_catalogue_failure(run, error):
            return
        run["dialog"]._worker_failed(run_id, error)

    def _handle_raw_preview_failure(self, run, error):
        if run.get("kind") != "raw_previews":
            return False
        current_document = (
            run["model"] is self.model
            and run["document_generation"] == self._document_generation
        )
        if current_document:
            if _is_analysis_stopped(error):
                self.model.requeue_raw_previews(run["requests"].values())
            else:
                detail = (
                    error.get("message", "Calculation failed")
                    if isinstance(error, dict)
                    else str(error)
                )
                self.statusbar.showMessage(f"Study preview failed: {detail}", 8000)
        self._schedule_raw_previews()
        return True

    def _handle_method_catalogue_failure(self, run, error):
        if run.get("kind") not in ("methods", "edit_methods", "subgroup_methods"):
            return False
        self.statusbar.clearMessage()
        if _is_analysis_stopped(error):
            return True
        self._show_analysis_engine_failure(error)
        return True

    def _show_analysis_engine_failure(self, error):
        detail = _analysis_engine_failure_detail(error)
        dialog = QMessageBox(
            QMessageBox.Icon.Critical,
            "Analysis Engine Unavailable",
            "RC MetaStudio could not start the isolated R analysis engine "
            "to load available methods. The project is still open and readable.\n\n"
            + detail,
            QMessageBox.StandardButton.Ok,
            self,
        )
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.open()

    def analysis(
        self,
        results: AnalysisResult,
        *,
        context=None,
        edit_copy_spec=None,
    ):
        try:
            self._show_analysis_result(
                results,
                context=context,
                edit_copy_spec=edit_copy_spec,
            )
        except Exception as e:
            app_error_handler.log_exception(type(e), e, e.__traceback__)
            QMessageBox.critical(
                self,
                "Could Not Display Analysis Results",
                "The analysis completed, but RC MetaStudio could not display "
                "the results. Your settings and selected inputs are still open. "
                "Close this message, review the display error, and run the analysis "
                "again after correcting it.\n\nDetails: %s: %s"
                % (e.__class__.__name__, e),
            )
            return False
        return True

    def _show_analysis_result(self, results, *, context=None, edit_copy_spec=None):
        form = results_window.ResultsWindow(
            results,
            parent=self,
            context=context,
            edit_copy_spec=edit_copy_spec,
            worker_client=self.analysis_worker,
        )
        try:
            form.edit_copy_requested.connect(self._edit_analysis_copy)
            form.show()
        except Exception:
            form.deleteLater()
            raise
        return form

    def edit_group_name(self, cur_group_name):
        orig_group_name = copy.copy(cur_group_name)
        edit_group_form = edit_name_dialogs.EditGroupNameDialog(
            cur_group_name, parent=self
        )
        if edit_group_form.exec():
            try:
                existing_groups = list(self.model.dataset.get_group_names())
                if orig_group_name in existing_groups:
                    existing_groups.remove(orig_group_name)
                new_group_name = name_validation.validate_unique_name(
                    "group", edit_group_form.group_name_le.text(), existing_groups
                )
            except ValueError as exc:
                QMessageBox.warning(self, "Warning", str(exc))
                return

            def redo_f():
                return self.model.rename_group(orig_group_name, new_group_name)

            def undo_f():
                return self.model.rename_group(new_group_name, orig_group_name)

            rename_group_command = meta_globals.CallbackCommand(redo_f, undo_f)
            self._commit_model_operation(rename_group_command.redo)

    def add_covariate(self):
        form = add_new_dialogs.AddCovariateDialog(self)
        form.covariate_name_le.setFocus()
        if form.exec():
            # then the user clicked 'ok'.
            try:
                new_covariate_name = dataset_table_model.validate_new_covariate_name(
                    self.model.dataset, form.covariate_name_le.text()
                )
            except ValueError as exc:
                QMessageBox.warning(self, "Warning", str(exc))
                return

            # Covariate names must remain unique.
            new_covariate_type = str(form.datatype_cbo_box.currentText()).lower()
            self._commit_model_operation(
                self._make_add_covariate_command(
                    new_covariate_name, new_covariate_type
                ).redo
            )

    def _make_add_covariate_command(self, covariate_name, covariate_type):
        state = {"stable_id": None}

        def redo():
            covariate = self._add_new_covariate(
                covariate_name, covariate_type, stable_id=state["stable_id"]
            )
            state["stable_id"] = covariate.stable_id

        def undo():
            self._undo_add_new_covariate(covariate_name)

        return meta_globals.CallbackCommand(
            redo, undo, description="Add covariate %s" % covariate_name
        )

    def _add_new_covariate(self, covariate_name, covariate_type, stable_id=None):
        covariate = self.model.add_covariate(
            covariate_name, covariate_type, stable_id=stable_id
        )
        self.tableView.synchronize_column_widths()
        self._refresh_advanced_analysis_actions()
        return covariate

    def _undo_add_new_covariate(self, covariate_name):
        self.model.remove_covariate(covariate_name)
        self.tableView.synchronize_column_widths()
        self._refresh_advanced_analysis_actions()

    def add_new(self, startup_outcome: main_wizard.DatasetInfo | None = None) -> None:
        redo_f, undo_f = None, None
        if self.current_dimension == "outcome" and not startup_outcome:
            form = add_new_dialogs.AddOutcomeDialog(
                parent=self, is_diagnostic=self.model.is_diagnostic()
            )
            form.outcome_name_le.setFocus()
            if form.exec():
                # then the user clicked ok and has added a new outcome.
                # here we want to add the outcome to the dataset, and then
                # display it
                try:
                    new_outcome_name = dataset_table_model.validate_new_outcome_name(
                        self.model.dataset, form.outcome_name_le.text()
                    )
                except ValueError as exc:
                    QMessageBox.warning(self, "Warning", str(exc))
                    return
                # the outcome type is one of the enumerated types; we don't worry about
                # unicode encoding
                new_outcome_type = str(form.datatype_cbo_box.currentText())

                def redo_f():
                    return self._add_new_outcome(new_outcome_name, new_outcome_type)

                previous_outcome = str(self.model.current_outcome_name)

                def undo_f():
                    return self._undo_add_new_outcome(
                        new_outcome_name, previous_outcome
                    )
        elif (
            self.current_dimension == "outcome" and startup_outcome
        ):  # For dealing with outcomes from the startup form
            new_outcome_name = qt_text.to_native_text(startup_outcome["name"])
            new_outcome_type = str(startup_outcome["data_type"])
            new_outcome_subtype = startup_outcome.get("sub_type")

            def redo_f():
                return self._add_new_outcome(
                    new_outcome_name, new_outcome_type, new_outcome_subtype
                )

            previous_outcome = str(self.model.current_outcome_name)

            def undo_f():
                return self._undo_add_new_outcome(new_outcome_name, previous_outcome)
        elif self.current_dimension == "group":
            form = add_new_dialogs.AddGroupDialog(self)
            form.group_name_le.setFocus()
            if form.exec():
                try:
                    new_group_name = dataset_table_model.validate_new_group_name(
                        self.model.dataset, form.group_name_le.text()
                    )
                except ValueError as exc:
                    QMessageBox.warning(self, "Warning", str(exc))
                    return
                current_groups = list(self.model.get_current_groups())

                def redo_f():
                    return self._add_new_group(new_group_name)

                def undo_f():
                    return self._undo_add_new_group(new_group_name, current_groups)
        else:
            # then the dimension is follow-up
            form = add_new_dialogs.AddFollowUpDialog(self)
            form.follow_up_name_le.setFocus()
            if form.exec():
                try:
                    follow_up_lbl = dataset_table_model.validate_new_follow_up_name(
                        self.model.dataset,
                        self.model.current_outcome_name,
                        form.follow_up_name_le.text(),
                    )
                except ValueError as exc:
                    QMessageBox.warning(self, "Warning", str(exc))
                    return

                def redo_f():
                    return self._add_new_follow_up_for_cur_outcome(follow_up_lbl)

                previous_follow_up = self.model.get_current_follow_up_name()

                def undo_f():
                    return self._undo_add_follow_up_for_cur_outcome(
                        previous_follow_up, follow_up_lbl
                    )

        if redo_f is not None and undo_f is not None:
            next_command = meta_globals.CallbackCommand(redo_f, undo_f)
            self._commit_model_operation(next_command.redo)

    def _add_new_group(self, new_group_name):
        self.model.add_new_group(new_group_name)
        current_groups = list(self.model.get_current_groups())
        current_groups[1] = new_group_name
        self.model.set_current_groups(current_groups)
        # Refresh the displayed group columns after renaming.
        self.display_groups(current_groups)

    def _undo_add_new_group(self, added_group, previously_displayed_groups):
        self.model.remove_group(added_group)
        self.model.set_current_groups(previously_displayed_groups)
        self.display_groups(previously_displayed_groups)

    def _undo_add_new_outcome(self, added_outcome, previously_displayed_outcome):
        self.model.remove_outcome(added_outcome)
        self.display_outcome(previously_displayed_outcome)

    def _add_new_outcome(self, outcome_name, outcome_type, sub_type=None):
        self.model.add_new_outcome(outcome_name, outcome_type, sub_type=sub_type)
        self.display_outcome(outcome_name)

    def _add_new_follow_up_for_cur_outcome(self, follow_up_lbl):
        self.model.add_follow_up_to_current_outcome(follow_up_lbl)
        self.display_follow_up(self.model.get_t_point_for_follow_up_name(follow_up_lbl))

    def _undo_add_follow_up_for_cur_outcome(self, prev_follow_up, follow_up_to_del):
        self.model.remove_follow_up_from_outcome(
            follow_up_to_del, str(self.model.current_outcome_name)
        )
        self.display_follow_up(
            self.model.get_t_point_for_follow_up_name(prev_follow_up)
        )

    def next(self):
        # Disable navigation when there is no next item in this dimension.
        # if there is only one point (e.g., outcome). otherwise you end
        # up enqueueing a bunch of pointless undo/redos.
        redo_f, undo_f = None, None
        if self.current_dimension == "outcome":
            old_outcome = self.model.current_outcome_name
            # Preserve the current groups because the next outcome can select
            # different defaults and undo must restore the original view.
            previous_groups = self.model.get_current_groups()
            next_outcome = self.model.get_next_outcome_name()

            def redo_f():
                return self.display_outcome(next_outcome)

            previous_follow_up = self.model.get_current_follow_up_name()

            def undo_f():
                return self.display_outcome(
                    old_outcome,
                    follow_up_name=previous_follow_up,
                    group_names=previous_groups,
                )
        elif self.current_dimension == "group":
            previous_groups = self.model.get_current_groups()
            new_groups = self.model.next_groups()

            def redo_f():
                return self.display_groups(new_groups)

            def undo_f():
                return self.display_groups(previous_groups)
        elif self.current_dimension == "follow-up":
            old_follow_up_t_point = self.model.current_follow_up_index
            next_follow_up_t_point = self.model.get_next_follow_up()[0]

            def redo_f():
                return self.display_follow_up(next_follow_up_t_point)

            def undo_f():
                return self.display_follow_up(old_follow_up_t_point)

        if redo_f is not None and undo_f is not None:
            next_command = meta_globals.CallbackCommand(redo_f, undo_f)
            self._commit_model_operation(next_command.redo)

    def previous(self):
        redo_f, undo_f = None, None
        if self.current_dimension == "outcome":
            old_outcome = self.model.current_outcome_name
            next_outcome = self.model.get_previous_outcome_name()

            def redo_f():
                return self.display_outcome(next_outcome)

            def undo_f():
                return self.display_outcome(old_outcome)
        elif self.current_dimension == "group":
            current_groups = self.model.get_current_groups()
            prev_groups = self.model.get_previous_groups()

            def redo_f():
                return self.display_groups(prev_groups)

            def undo_f():
                return self.display_groups(current_groups)
        elif self.current_dimension == "follow-up":
            old_follow_up_t_point = self.model.current_follow_up_index
            previous_follow_up_t_point = self.model.get_previous_follow_up()[0]

            def redo_f():
                return self.display_follow_up(previous_follow_up_t_point)

            def undo_f():
                return self.display_follow_up(old_follow_up_t_point)

        if redo_f is not None and undo_f is not None:
            prev_command = meta_globals.CallbackCommand(redo_f, undo_f)
            self._commit_model_operation(prev_command.redo)

    def next_dimension(self):
        """In keeping with the dimensions metaphor, wherein the various
        components that can comprise a dataset are 'dimensions' (e.g.,
        outcomes), this function iterates over the dimensions. So if you call
        this method, then 'next()', the next method will step forward in the
        dimension made active here.
        """
        if self.current_dimension_index == len(self.dimensions) - 1:
            self.current_dimension_index = 0
        else:
            self.current_dimension_index += 1
        self.update_dimension()

    def previous_dimension(self):
        if self.current_dimension_index == 0:
            self.current_dimension_index = len(self.dimensions) - 1
        else:
            self.current_dimension_index -= 1
        self.update_dimension()

    def update_dimension(self):
        self.current_dimension = self.dimensions[self.current_dimension_index]
        self.navigation_label.setText(self.current_dimension)
        dimension = self.current_dimension
        actions = (
            (self.nav_left_btn, f"Previous {dimension}", f"Show the previous {dimension}."),
            (self.nav_right_btn, f"Next {dimension}", f"Show the next {dimension}."),
            (self.nav_add_btn, f"Add {dimension}", f"Add a new {dimension} to the dataset."),
        )
        for button, name, description in actions:
            button.setText(name)
            button.setToolTip(name)
            button.setStatusTip(description)
            button.setAccessibleName(name)
            button.setAccessibleDescription(description)
        self._update_navigation_controls()

    def _update_navigation_controls(self):
        """Keep cyclic navigation affordances honest for the active dimension."""
        can_previous, can_next = self._navigation_availability()
        dimension = self.current_dimension
        for direction, button, can_navigate in (
            ("previous", self.nav_left_btn, can_previous),
            ("next", self.nav_right_btn, can_next),
        ):
            if can_navigate:
                button.setEnabled(True)
                button.setToolTip(f"{direction.title()} {dimension}")
                button.setStatusTip(f"Show the {direction} {dimension}.")
                button.setAccessibleDescription(
                    f"Show the {direction} {dimension}."
                )
            else:
                unavailable = f"No {direction} {dimension} available."
                button.setEnabled(False)
                button.setToolTip(unavailable)
                button.setStatusTip(unavailable)
                button.setAccessibleDescription(unavailable)

    def _navigation_availability(self):
        dimension = self.current_dimension
        if dimension == "outcome":
            item_count = len(self.model.dataset.get_outcome_names())
            can_navigate = item_count > 1
            return can_navigate, can_navigate
        elif dimension == "follow-up":
            outcome_name = self.model.current_outcome_name
            item_count = (
                len(self.model.dataset.get_follow_up_names_for_outcome(outcome_name))
                if outcome_name is not None
                else 0
            )
            can_navigate = item_count > 1
            return can_navigate, can_navigate
        return self._group_navigation_availability()

    def _group_navigation_availability(self):
        outcome_name = self.model.current_outcome_name
        follow_up_name = self.model.get_current_follow_up_name()
        group_names = (
            self.model.dataset.get_group_names_for_outcome_follow_up(
                outcome_name, follow_up_name
            )
            if outcome_name is not None and follow_up_name is not None
            else []
        )
        current_groups = tuple(self.model.get_current_groups())
        previous_groups = tuple(self.model.get_previous_groups())
        can_previous = (
            bool(previous_groups)
            and previous_groups != current_groups
            and set(previous_groups).issubset(group_names)
        )
        return can_previous, len(group_names) > 1

    def display_groups(self, groups):
        self.model.set_current_groups(groups)
        self.model.hydrate_derived_previews()
        self.model.reset_model()
        self.tableView.synchronize_column_widths()
        self._update_navigation_controls()

    def display_outcome(self, outcome_name, group_names=None, follow_up_name=None):
        # Never retain a group or follow-up that belongs to another outcome.
        self.model.set_current_outcome(outcome_name)
        self.populate_metrics_menu(metric_to_check=self.model.current_effect)

        if follow_up_name is not None:
            self.model.set_current_follow_up(follow_up_name)
        else:
            # If a follow up isn't explicitly passed in, attempt to use
            # the current follow up. If this does not exist for the outcome
            # to be displayed, then display a different follow up.
            current_follow_up = self.model.get_current_follow_up_name()
            if not self.model.outcome_has_follow_up(outcome_name, current_follow_up):
                # then the outcome does not have this follow up and we have to
                # step on to the next one.
                next_follow_up = self.model.get_next_follow_up()[1]
                self.model.set_current_follow_up(next_follow_up)

        # now we check the groups.
        if group_names is not None:
            self.model.set_current_groups(group_names)
        else:
            # then no group names were explicitly passed in; ascertain
            # that the outcome/fu contains the current groups; if not,
            # set them to something else.
            current_groups = self.model.get_current_groups()
            if not all(
                [
                    self.model.outcome_follow_up_has_group(
                        outcome_name, self.model.get_current_follow_up_name(), group
                    )
                    for group in current_groups
                ]
            ):
                self.model.set_current_groups(self.model.next_groups())

        self.current_outcome_label.setText(
            "<font color='Blue'>%s</font>" % outcome_name
        )
        self.current_follow_up_label.setText(
            "<font color='Blue'>%s</font>" % self.model.get_current_follow_up_name()
        )
        self.model.hydrate_derived_previews()
        self.model.reset_model()
        self.tableView.synchronize_column_widths()
        self._update_navigation_controls()

    def display_follow_up(self, time_point):
        self.model.current_follow_up_index = time_point
        self.update_follow_up_label()
        self.model.hydrate_derived_previews()
        self.model.reset_model()
        self.tableView.synchronize_column_widths()
        self._update_navigation_controls()

    def update_follow_up_label(self):
        self.current_follow_up_label.setText(
            "<font color='Blue'>%s</font>" % self.model.get_current_follow_up_name()
        )

    def open(self, file_path=None, raise_on_error=False):
        """Open a validated structured project and restore its durable working state.

        Opening a project is a document boundary, not an undoable edit. The undo stack is
        reset after a successful load so Ctrl+Z cannot step back into the previously open
        dataset.
        """
        if not self._authorize_destructive_project_action():
            return
        try:
            # if no file path is provided, prompt the user.
            if file_path is None:
                file_path = QFileDialog.getOpenFileName(
                    parent=self,
                    caption="RCMetaStudio - Open Project",
                    directory=get_default_open_directory(),
                    filter="RC MetaStudio Project (*.rcms)",
                )
                file_path = _qt_dialog_path(file_path)

                # if the user didn't select anything, we return false.
                if file_path == "":
                    return False

            file_path = _resolve_open_file_path(file_path)

            try:
                self.workspace.open(file_path, install=self._install_open_document)
            except Exception as e:
                msg = _format_open_project_error(file_path, e)
                if raise_on_error:
                    raise RuntimeError(msg) from e
                QMessageBox.critical(self, "Could Not Open Project", msg)
                return None

            self.out_path = file_path
            self._document_generation += 1
            self.model.analysis_source_path = file_path
            self.dataset_file_lbl.setText("Open Project: %s" % file_path)
            self._update_recent_project_nonfatal(file_path, "opened")
            self._refresh_workspace_results()
            return True
        finally:
            self._resume_raw_previews()

    def _install_open_document(self, document):
        """Adapt a validated session document into the live Qt model."""
        runtime = document
        previous_model = self.model
        previous_current = self.tableView.currentIndex()
        current_cell = (
            (previous_current.row(), previous_current.column())
            if previous_current.isValid()
            else None
        )
        selection_model = required(
            self.tableView.selectionModel(), "workspace selection model"
        )
        selected_cells = [
            (index.row(), index.column()) for index in selection_model.selectedIndexes()
        ]
        try:
            self._set_model_adapter(
                runtime.dataset,
                runtime.model_state,
                check_for_appropriate_metric=not runtime.restored_selection,
                preserve_state_selection=runtime.restored_selection,
                recalculate_outcomes=False,
            )
        except Exception:
            self._restore_failed_open(previous_model, current_cell, selected_cells)
            raise

    def _restore_failed_open(self, model, current_cell, selected_cells):
        """Restore the live Qt adapter after a candidate model fails to install."""
        self._disconnect_model_signals()
        self.model = model
        self.tableView.restore_model(model)
        self._setup_connections(menu_actions=False)
        if len(model.dataset) >= 2:
            self.enable_menu_options_that_require_dataset()
        else:
            self.disable_menu_options_that_require_dataset()
        self._refresh_advanced_analysis_actions()
        self.populate_metrics_menu(metric_to_check=model.current_effect)
        self.update_outcome_lbl()
        self.update_follow_up_label()
        selection_model = required(
            self.tableView.selectionModel(), "workspace selection model"
        )
        selection_model.clearSelection()
        select = QtCore.QItemSelectionModel.SelectionFlag.Select
        for row, column in selected_cells:
            selection_model.select(model.index(row, column), select)
        if current_cell is not None:
            selection_model.setCurrentIndex(
                model.index(*current_cell),
                QtCore.QItemSelectionModel.SelectionFlag.NoUpdate,
            )

    def delete_study(self, study, study_index=None):
        def undo_f():
            return self._add_study(study, study_index=study_index)

        def redo_f():
            return self._remove_study(study)

        delete_command = meta_globals.CallbackCommand(redo_f, undo_f)
        self._commit_model_operation(delete_command.redo)

    def change_covariate_type(self, covariate):
        current_dataset = self.workspace.snapshot().dataset
        # keep the current study order, because we're going to sort the studies
        # on the change_cov_form but we want to revert to the ordering
        # they came in with when we're done.
        original_study_order = [study.name for study in self.model.dataset.studies]

        change_type_form = covariate_type_dialog.CovariateTypeDialog(
            current_dataset, covariate, parent=self
        )

        if change_type_form.exec():
            modified_dataset = change_type_form.dataset
            # revert to original study ordering
            modified_dataset.studies.sort(
                key=cmp_to_key(
                    modified_dataset.cmp_studies(
                        compare_by="ordered_list",
                        ordered_list=original_study_order,
                        confidence_multiplier=self.model.get_confidence_multiplier(),
                    )
                )
            )

            old_state_dict = self.tableView.model().get_state()
            new_state_dict = copy.deepcopy(old_state_dict)

            self._commit_model_operation(
                lambda: self.set_model(modified_dataset, new_state_dict)
            )

    def rename_covariate(self, covariate):
        orig_cov_name = copy.copy(covariate.name)
        # The group-name editor is also used for covariate labels.
        edit_cov_form = edit_name_dialogs.EditCovariateNameDialog(
            orig_cov_name, parent=self
        )
        if edit_cov_form.exec():
            # the field names are also poorly named, in this case. here we mean the
            # **covariate name**, of course.
            try:
                existing_covariates = list(self.model.dataset.get_covariate_names())
                if orig_cov_name in existing_covariates:
                    existing_covariates.remove(orig_cov_name)
                new_cov = name_validation.validate_unique_name(
                    "covariate",
                    edit_cov_form.group_name_le.text(),
                    existing_covariates,
                )
            except ValueError as exc:
                QMessageBox.warning(self, "Warning", str(exc))
                return

            # The model owns the actual covariate rename and undo operation.
            def redo_f():
                return self.model.rename_covariate(orig_cov_name, new_cov)

            def undo_f():
                return self.model.rename_covariate(new_cov, orig_cov_name)

            rename_cov_command = meta_globals.CallbackCommand(redo_f, undo_f)
            self._commit_model_operation(rename_cov_command.redo)

    def delete_covariate(self, covariate):
        # Synchronize direct model edits made by an adapter before publishing
        # the next atomic workspace change.
        self.data_dirtied()
        covariate_values_by_study = self.model.dataset.get_covariate_values(
            covariate.name
        )
        stable_id = getattr(covariate, "stable_id", None)

        def undo_f():
            self.model.add_covariate(
                covariate.name,
                meta_globals.COV_INTS_TO_STRS[covariate.data_type],
                covariate_values=covariate_values_by_study,
                stable_id=stable_id,
            )
            self._refresh_advanced_analysis_actions()

        def redo_f():
            self.model.remove_covariate(covariate)
            self._refresh_advanced_analysis_actions()

        delete_command = meta_globals.CallbackCommand(redo_f, undo_f)
        self._commit_model_operation(delete_command.redo)

    def _refresh_advanced_analysis_actions(self):
        self._enable_action_meta_regression()
        self._enable_action_subgroup_ma()

    def _add_study(self, study, study_index=None):
        self.model.dataset.add_study(study, study_index=study_index)
        self.model.reset_model()
        self.data_dirtied()

    def _remove_study(self, study):
        self.model.dataset.studies.remove(study)
        self.model.reset_model()
        self.data_dirtied()

    def set_model(
        self,
        data_model,
        state_dict=None,
        check_for_appropriate_metric=False,
        preserve_state_selection=False,
        recalculate_outcomes=True,
    ):
        self._set_model_adapter(
            data_model,
            state_dict=state_dict,
            check_for_appropriate_metric=check_for_appropriate_metric,
            preserve_state_selection=preserve_state_selection,
            recalculate_outcomes=recalculate_outcomes,
        )
        self.data_dirtied()

    def _set_model_adapter(
        self,
        data_model,
        state_dict=None,
        check_for_appropriate_metric=False,
        preserve_state_selection=False,
        recalculate_outcomes=True,
    ):
        # An empty dataset starts with one editable blank row.
        add_blank_study = len(data_model) < 1
        self.model = dataset_table_model.DatasetTableModel(
            dataset=data_model, add_blank_study=add_blank_study
        )
        self.model.enable_worker_raw_previews()

        self._disconnect_model_signals()
        if len(data_model) >= 2:
            self.enable_menu_options_that_require_dataset()
        else:
            self.disable_menu_options_that_require_dataset()

        self._enable_action_meta_regression(len(data_model) >= 2)

        self.tableView.setModel(self.model)

        # Restore view state only after replacing the model.
        if state_dict is not None:
            self.model.set_state(state_dict)

        self.tableView.model().update_column_indices()
        self.tableView.synchronize_column_widths()

        if check_for_appropriate_metric:
            self.tableView.change_metric_if_appropriate()

        self.model_updated(
            preserve_selection=preserve_state_selection,
            recalculate_outcomes=recalculate_outcomes,
        )

    def model_updated(self, preserve_selection=False, recalculate_outcomes=True):
        """Call me when the model is changed."""
        if preserve_selection:
            group_names = self.model.dataset.get_group_names()
            if self.model.current_groups:
                self.model.group_index_a = group_names.index(
                    self.model.current_groups[0]
                )
                if len(self.model.current_groups) > 1:
                    self.model.group_index_b = group_names.index(
                        self.model.current_groups[1]
                    )
                else:
                    self.model.group_index_b = self.model.group_index_a
            self.model.previous_groups = list(self.model.current_groups)
        else:
            self.model.update_current_group_names()
            self.model.update_current_outcome()
            self.model.update_current_time_points()

        if recalculate_outcomes and self.model.current_outcome_name is not None:
            self.model.hydrate_derived_previews()

        # The retired model remains connected to its slots, so reconnect the
        # view but not menu actions, which would otherwise accumulate handlers.
        self._setup_connections(menu_actions=False)
        self.tableView.synchronize_column_widths()
        self.update_outcome_lbl()
        self.update_follow_up_label()

        current_data_type = self.tableView.model().get_current_outcome_type(
            get_str=False
        )
        if self.metric_menu_is_set_for != current_data_type:
            self.populate_metrics_menu(
                metric_to_check=self.tableView.model().current_effect
            )

        self.model.reset_model()
        self._update_confidence_level_label()
        self._update_navigation_controls()
        self._schedule_raw_previews()

    def update_outcome_lbl(self):
        self.current_outcome_label.setText(
            "<font color='Blue'>%s</font>" % self.model.current_outcome_name
        )

    def quit(self):
        self.close()

    def prompt_to_save_unsaved_data(self):
        choice = QMessageBox.warning(
            self,
            "Warning",
            "You've made unsaved changes to your data. Do you want to save your changes?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
        )
        return choice

    def save_as(self):
        return self.save(save_as=True)

    def save(self, save_as=False):

        if not self._flush_analysis_drafts():
            return False

        docs_path = get_user_documents_path()
        destination = self.out_path
        if self.out_path is None or save_as:
            # use current out_path otherwise base it on the current dataset name
            if self.out_path:
                out_f = str(self.out_path)
            else:
                out_f = os.path.join(docs_path, self.model.get_name())

            out_f = QFileDialog.getSaveFileName(
                parent=self,
                caption="RCMetaStudio - Save Project",
                directory=out_f,
                filter="RC MetaStudio Project (*.rcms)",
            )
            out_f = _qt_dialog_path(out_f)
            if out_f == "" or out_f is None:
                return None
            destination = out_f

        destination = str(destination)
        if not destination.lower().endswith(".rcms"):
            destination += ".rcms"

        durability_error = None
        try:
            self.data_dirtied()
            self.workspace.save(destination)
        except project_format.ProjectDurabilityError as e:
            durability_error = e
        except Exception as e:
            app_error_handler.log_exception(type(e), e, e.__traceback__)
            QMessageBox.critical(
                self,
                "Could Not Save Project",
                "RC MetaStudio could not save %s.\n\nDetails: %s: %s"
                % (destination, e.__class__.__name__, e),
            )
            return False

        # The durable document commit is complete. Machine-local recent-project
        # bookkeeping must never turn this successful save into a false failure.
        self.out_path = destination
        self.model.analysis_source_path = destination
        self.dataset_file_lbl.setText("Open Project: %s" % destination)
        if durability_error is not None:
            self._report_durability_uncertain_save(destination, durability_error)
        self._update_recent_project_nonfatal(destination, "saved")
        self._invalidate_recovery_snapshot()
        return True

    def _make_new_dataset_and_setup_spreadsheet(self, dataset_info):
        is_diagnostic = dataset_info["data_type"] == "diagnostic"
        self.new_dataset(is_diagnostic=is_diagnostic)
        self.model.dataset.summary = copy.deepcopy(dataset_info)

        tmp = self.current_dimension
        self.current_dimension = "outcome"
        self.add_new(dataset_info)  # add the outcome
        self.current_dimension = tmp

        if dataset_info["data_type"] in ["binary", "continuous"]:
            self.model.current_effect = dataset_info["effect"]  # set current effect
            self.populate_metrics_menu(metric_to_check=self.model.current_effect)
            self.model.try_to_update_outcomes()
            self.model.reset_model()

    def _handle_wizard_results(self, wizard_data):
        path = wizard_data["path"]  # route through wizard

        dataset_info = wizard_data["outcome_info"]

        if path == "open":
            self.open(file_path=wizard_data["selected_dataset"])
        elif path == "new_dataset":
            self._make_new_dataset_and_setup_spreadsheet(dataset_info)
            self.workspace.start_new_document()
            self._document_generation += 1
            self.out_path = None
            self._notify_user_that_data_is_unsaved()
            self._refresh_workspace_results()

        elif path == "csv_import":
            csv_data = wizard_data["csv_data"]
            try:
                staged = main_wizard.build_staged_import_model(csv_data, dataset_info)
            except csv_import.CsvImportError as error:
                QMessageBox.warning(
                    self,
                    "Could Not Import CSV",
                    "%s\n\nReview the mapping or source file and try again." % error,
                )
                return
            self._commit_model_operation(
                lambda: self.set_model(staged.dataset, state_dict=staged.get_state())
            )
            self.workspace.start_new_document()
            self._document_generation += 1
            self.out_path = None
            self._notify_user_that_data_is_unsaved()
            self._refresh_workspace_results()


class ChangeConfidenceLevelCommand:
    """Undo a confidence-level change."""

    def __init__(
        self,
        old_conf_lvl,
        new_conf_lvl,
        mainform,
        description="Change confidence level",
    ):

        self.old_cl = old_conf_lvl
        self.new_cl = new_conf_lvl
        self.mainform = mainform

    def redo(self):
        self._set_confidence_level(self.new_cl)

    def undo(self):
        self._set_confidence_level(self.old_cl)

    def _set_confidence_level(self, confidence_level):
        self.mainform.model.set_confidence_level(confidence_level)
        self.mainform.cl_label.setText(
            _format_confidence_level_status(confidence_level)
        )
        self.mainform.model.reset_model()
