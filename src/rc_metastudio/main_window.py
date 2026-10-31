# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Main RC MetaStudio desktop window."""

from __future__ import annotations

import os
from functools import cmp_to_key
from typing import TYPE_CHECKING, cast
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
    QApplication,
    QDialog,
    QFileDialog,
    QLabel,
    QMessageBox,
    QTableView,
)
import copy

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
from rc_metastudio import analysis_identity
from rc_metastudio import app_error_handler
from rc_metastudio import r_backend
from rc_metastudio import progress_dialog
from rc_metastudio import qt_layout
from rc_metastudio import adaptive_window
from rc_metastudio import qt_text
from rc_metastudio import name_validation
from rc_metastudio import project_adapter
from rc_metastudio import project_format
from rc_metastudio import csv_import
from rc_metastudio.settings import (
    add_file_to_recent_files,
    get_default_open_directory,
    get_recent_files,
    get_sample_projects_path,
    get_user_documents_path,
    load_main_column_widths,
    load_settings,
    recent_file_display_name,
    save_main_window_placement,
    save_settings,
    update_setting,
)
from rc_metastudio.runtime_types import required

from rc_metastudio import add_new_dialogs
from rc_metastudio import results_window, analysis_setup_dialog
from rc_metastudio import publication_bias_dialog
from rc_metastudio import publication_bias
from rc_metastudio import diagnostic_metrics_dialog
from rc_metastudio import subgroup_analysis_dialog
from rc_metastudio import edit_name_dialogs
from rc_metastudio import covariate_type_dialog
from rc_metastudio import confidence_level_dialog
from rc_metastudio import start_page
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
        return "Confidence level: not set"
    return f"Confidence level: {float(confidence_level):g}%"


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


class ImportProgressDialog(progress_dialog.AnalysisProgressDialog):
    def __init__(self, parent=None, min_=0, max_=10):
        super().__init__(parent)

        self.setWindowTitle("Importing from CSV...")
        self.progress_bar.setRange(min_, max_)

    def setValue(self, value):
        if self.progress_bar.minimum() <= value <= self.progress_bar.maximum():
            self.progress_bar.setValue(value)

    def minimum(self):
        return self.progress_bar.minimum()

    def maximum(self):
        return self.progress_bar.maximum()

    def value(self):
        return self.progress_bar.value()


class SheetTabBar(QtWidgets.QTabBar):
    def mouseReleaseEvent(self, event):
        try:
            super().mouseReleaseEvent(event)
        finally:
            window = self.window()
            if window._sheet_dragging:
                window._sheet_dragging = False
                window.workspace.end_change()


class MainWindow(QtWidgets.QMainWindow, _ui_main_window.Ui_MainWindow):
    model: dataset_table_model.DatasetTableModel
    tableView: dataset_table_view.DatasetTableView

    def __init__(self, parent=None):
        super().__init__(parent)
        self.analysis_service = analysis_adapter.AnalysisService()
        self.small_study_effects_service = publication_bias.SmallStudyEffectsService()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setupUi(self)
        qt_layout.configure_analysis_menu(self.menuAnalysis)
        self.menuAnalysis.setToolTipsVisible(True)
        for action, icon_name in (
            (self.action_go, "meta-analysis"),
            (self.action_cum_ma, "cumulative-analysis"),
            (self.action_loo_ma, "leave-one-out-analysis"),
            (self.action_subgroup_ma, "subgroup-analysis"),
            (self.action_meta_regression, "meta-regression"),
            (self.action_publication_bias, "publication-bias"),
        ):
            qt_layout.configure_analysis_action_icon(action, icon_name)
        self.analysis_button = QtWidgets.QToolButton(self.toolBar)
        self.analysis_button.setText("Analyses")
        self.analysis_button.setIcon(self.action_go.icon())
        self.analysis_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.analysis_button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.analysis_button.setMenu(self.menuAnalysis)
        self.analysis_button.setAccessibleName("Analyses")
        self.analysis_button.setAccessibleDescription("Choose an analysis. Unavailable analyses explain their prerequisites in the menu.")
        self.analysis_button.setToolTip("Choose an analysis")
        self.analysis_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.toolBar.insertWidget(self.action_go, self.analysis_button)
        for action in (self.action_go, self.action_cum_ma, self.action_loo_ma, self.action_subgroup_ma,
                       self.action_meta_regression, self.action_publication_bias, self.action_change_confidence_level):
            self.toolBar.removeAction(action)
        qt_layout.configure_main_toolbar(self.toolBar)
        dataset_file_label = ElidingStatusLabel(
            self.dataset_file_lbl.text(), self.centralwidget
        )
        self.verticalLayout_3.replaceWidget(self.dataset_file_lbl, dataset_file_label)
        self.dataset_file_lbl.deleteLater()
        self.dataset_file_lbl = dataset_file_label
        self.action_new_dataset.setText("Create dataset…")
        self.start_page = start_page.StartPage(self.action_new_dataset, self.action_import_csv, self.action_open, self)
        self.verticalLayout_3.insertWidget(0, self.start_page)
        self.menu_file.insertAction(self.action_open, self.action_new_dataset)
        self.action_publication_bias.setText("Small-study effects…")
        help_action = QAction("Quick start and shortcuts…", self)
        help_action.triggered.connect(app_error_handler.safe_slot(self.show_quick_start, parent=self))
        self.menuHelp.insertAction(self.action_about_legal, help_action)
        adaptive_window.register_adaptive_window(self, adaptive_window.WindowRole.MAIN)
        table_view = dataset_table_view.DatasetTableView(self.nav_frame)
        self.verticalLayout.replaceWidget(self.tableView, table_view)
        self.tableView.deleteLater()
        self.tableView = table_view
        self.tableView.restore_column_widths(load_main_column_widths())

        self.cl_label = ElidingStatusLabel(
            _format_confidence_level_status(meta_globals.DEFAULT_CONFIDENCE_LEVEL)
        )
        self.cl_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.statusbar.addWidget(self.cl_label, 1)

        self.frame.hide()
        self._sheet_dragging = False
        self.sheet_tabs = SheetTabBar(self)
        self.sheet_tabs.setObjectName("sheet_tabs")
        self.sheet_tabs.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setTabOrder(self.analysis_button, self.sheet_tabs)
        self.setTabOrder(self.sheet_tabs, self.tableView)
        self.sheet_tabs.setExpanding(False)
        self.sheet_tabs.setMovable(True)
        self.sheet_tabs.setUsesScrollButtons(True)
        self.sheet_tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.sheet_tabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        sheet_bar = QtWidgets.QHBoxLayout()
        sheet_bar.addWidget(self.sheet_tabs)
        self.add_sheet_button = QtWidgets.QToolButton(self)
        self.add_sheet_button.setText("+")
        self.add_sheet_button.setToolTip("Add sheet")
        sheet_bar.addWidget(self.add_sheet_button)
        sheet_bar.addStretch()
        self.verticalLayout.addLayout(sheet_bar)
        self.sheet_tabs.currentChanged.connect(self._select_sheet_tab)
        self.sheet_tabs.tabMoved.connect(self._move_sheet_tab)
        self.sheet_tabs.tabBarDoubleClicked.connect(self._rename_sheet)
        self.sheet_tabs.customContextMenuRequested.connect(self._sheet_menu)
        self.add_sheet_button.clicked.connect(self._add_sheet)
        for sequence, delta in (("Ctrl+PgDown", 1), ("Ctrl+PgUp", -1)):
            action = QAction(self)
            action.setShortcut(QKeySequence(sequence))
            action.triggered.connect(lambda checked=False, delta=delta: self.sheet_tabs.setCurrentIndex((self.sheet_tabs.currentIndex() + delta) % max(1, self.sheet_tabs.count())))
            self.addAction(action)
        self.action_swap_arms = QAction("Swap intervention and control", self)
        self.menuDataset.addAction(self.action_swap_arms)
        self.menuDataset.aboutToShow.connect(lambda: self.action_swap_arms.setEnabled(bool(self.model.current_sheet and self.model.current_sheet.family != "diagnostic" and len(self.model.current_sheet.arms) == 2 and self.model.current_effect not in meta_globals.ONE_ARM_METRICS)))
        self.action_swap_arms.triggered.connect(self._swap_sheet_arms)
        self.workspace = WorkspaceSession()
        self.new_dataset()

        self.tableView.setModel(self.model)
        self.tableView.setItemDelegate(dataset_table_view.StudyDelegate(self.tableView))

        self._model_signal_connections = []
        self._setup_connections()
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

        load_settings()
        self.populate_open_recent_menu()
        self.workspace.mark_saved()
        self._update_project_identity()

    def createPopupMenu(self):
        return None

    def start(self):
        self._update_workspace_guidance()
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(  # ty: ignore[invalid-method-override] -- PyQt6's QMainWindow and QWidget stubs conflict for this runtime-supported override.
        self, event: QCloseEvent | None
    ) -> None:
        if event is None:
            return
        if not self._confirm_close():
            event.ignore()
            return
        self._disconnect_model_signals()
        save_main_window_placement(self, self.tableView.column_width_state())
        save_settings()
        event.accept()

    def _confirm_close(self):
        if not self.workspace.is_dirty:
            return True
        choice = self.prompt_to_save_unsaved_data()
        if choice == QMessageBox.StandardButton.Yes:
            return self.save() is True
        return choice == QMessageBox.StandardButton.No

    def _authorize_destructive_project_action(self):
        """Return whether New/Open/Import may replace the current project."""
        if not self.workspace.is_dirty:
            return True
        choice = self.prompt_to_save_unsaved_data()
        if choice == QMessageBox.StandardButton.Yes:
            return self.save() is True
        return choice == QMessageBox.StandardButton.No

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

        wizard = main_wizard.MainWizard(parent=self, path="new_dataset")
        if wizard.exec():
            wizard_data = wizard.get_results()
            self._handle_wizard_results(wizard_data)

    def new_dataset(self, name=DEFAULT_DATASET_NAME, is_diagnostic=False, use_undo_framework=True):
        data_model = analysis_dataset.Dataset(title=name)
        self.model = dataset_table_model.DatasetTableModel(dataset=data_model)
        self.workspace.update_live_state(project_adapter.RuntimeProject(data_model, self.model.get_state(), False))
        self.out_path = None
        self._notify_user_that_data_is_unsaved()

    def _notify_user_that_data_is_unsaved(self):
        self._update_project_identity()

    def _update_project_identity(self, state=None):
        path = getattr(self, "out_path", None)
        name = os.path.basename(path) if path else "Untitled dataset"
        dirty = self.workspace.is_dirty
        self.setWindowTitle(f"{name}{' *' if dirty else ''} — RC MetaStudio")
        empty = not [s.name for s in self.model.dataset.sheets]
        status = state or ("Ready to create or open a dataset" if empty and not dirty and not path else "Unsaved changes" if dirty else "Ready")
        self.dataset_file_lbl.setText(f"{status} · {name}")
        self.dataset_file_lbl.setToolTip(path or "Save the dataset to choose a project file.")

    def toggle_menu_options_that_require_dataset(self, enable):
        self.action_go.setEnabled(enable)
        self.action_cum_ma.setEnabled(enable)
        self.action_loo_ma.setEnabled(enable)
        self._enable_action_meta_regression(enable)
        self._enable_action_subgroup_ma(enable)
        self.action_publication_bias.setEnabled(enable)
        self._update_workspace_guidance()

    def _update_workspace_guidance(self):
        enable = hasattr(self, "model") and self.model.current_outcome_name is not None
        self.start_page.setVisible(not enable)
        self.nav_frame.setVisible(enable)

    def _enable_action_meta_regression(self, dataset_analysis_enabled=None):
        """Enables action_meta_regression if analysis can run and covariates exist."""
        if dataset_analysis_enabled is None:
            dataset_analysis_enabled = self.action_go.isEnabled()
        has_covariates = bool(self.model and (self.model.current_sheet.covariates if self.model.current_sheet else []))
        self.action_meta_regression.setEnabled(
            dataset_analysis_enabled and has_covariates
        )
        self.action_meta_regression.setToolTip("Meta-regression" if has_covariates else "Add a covariate to run meta-regression.")

    def _enable_action_subgroup_ma(self, dataset_analysis_enabled=None):
        """Enables action_subgroup_ma if there are suitable covariate(s)
        i.e. of type Factor
        """
        if dataset_analysis_enabled is None:
            dataset_analysis_enabled = self.action_go.isEnabled()
        has_factor_covariates = bool(
            self.model
            and any(
                cov['data_type'] == meta_globals.FACTOR
                for cov in (self.model.current_sheet.covariates if self.model.current_sheet else [])
            )
        )
        self.action_subgroup_ma.setEnabled(
            dataset_analysis_enabled and has_factor_covariates
        )
        self.action_subgroup_ma.setToolTip("Subgroup meta-analysis" if has_factor_covariates else "Add a categorical covariate to run subgroup analysis.")

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
        self.start_page.set_recent_projects(recent_datasets, self.dataset_selected, self._locate_recent_project, self._remove_recent_project)
        self.action_open_recent_2.clear()
        for dataset in reversed(recent_datasets):
            action_item = QAction(
                recent_file_display_name(dataset), self.action_open_recent_2
            )
            if not os.path.isfile(dataset):
                action_item.setText(action_item.text() + " — Missing file")
                action_item.setEnabled(False)
            action_item.setData(str(dataset))
            action_item.setToolTip(str(dataset))
            action_item.setStatusTip(str(dataset))
            self.action_open_recent_2.addAction(action_item)
            _connect_action(
                action_item, lambda dataset=dataset: self.dataset_selected(dataset)
            )

    def _remove_recent_project(self, path):
        update_setting("recent_files", [entry for entry in get_recent_files() if entry != path])
        save_settings()
        self.populate_open_recent_menu()

    def _locate_recent_project(self, path):
        replacement, _filter = QFileDialog.getOpenFileName(self, "Locate project", os.path.dirname(path), "RC MetaStudio projects (*.rcms)")
        if replacement:
            # Validate the replacement before removing the unavailable path.
            project_format.load_project(replacement)
            add_file_to_recent_files(replacement)
            if os.path.normcase(os.path.realpath(replacement)) != os.path.normcase(os.path.realpath(path)):
                self._remove_recent_project(path)
            else:
                self.populate_open_recent_menu()

    def dataset_selected(self, dataset_path):
        self.open(file_path=dataset_path)

    def _change_global_ci(self):
        previous_confidence_level = self.model.get_confidence_level()

        dialog = confidence_level_dialog.ConfidenceLevelDialog(
            previous_confidence_level, self
        )
        if dialog.exec():
            new_confidence_level = dialog.get_value()

            def apply_confidence_level():
                self.model.set_confidence_level(new_confidence_level)
                self._update_confidence_level_label()
                self.model.reset_model()
                self.data_dirtied()

            self._commit_model_operation(apply_confidence_level)

    def _import_csv(self):
        """Import data from csv file"""
        if not self._authorize_destructive_project_action():
            return
        wizard = main_wizard.MainWizard(parent=self, path="csv_import")
        if wizard.exec():
            wizard_data = wizard.get_results()
            self._handle_wizard_results(wizard_data)

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
                model.dataError, self.data_error, parent=self
            )
        )

        self._model_signal_connections.append(
            app_error_handler.connect_safely(
                self.tableView.dataDirtied, self.data_dirtied, parent=self
            )
        )
        if menu_actions:
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

            _connect_action(self.action_add_covariate, self.add_covariate)

            _connect_action(self.action_meta_regression, self.meta_reg)
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
        if self.model.get_current_outcome_type() != "diagnostic":
            form = self._build_analysis_specs_dialog(
                confidence_level=self.model.get_confidence_level()
            )
        else:
            form = diagnostic_metrics_dialog.DiagnosticMetricsDialog(
                self.model, parent=self
            )
        if form is None:
            return
        form.show()

    def meta_reg(self):
        kwargs = {
            "analysis_type": "meta-regression",
            "confidence_level": self.model.get_confidence_level(),
        }
        if self.model.get_current_outcome_type() == "diagnostic":
            # Reitsma meta-regression is a single joint sensitivity/
            # specificity model. Keep that intent explicit at the UI seam.
            kwargs["diagnostic_metrics"] = ["sens", "spec"]
        form = self._build_analysis_specs_dialog(**kwargs)
        if form is None:
            return
        form.show()

    def publication_bias(self):
        form = publication_bias_dialog.PublicationBiasDialog(
            self.model,
            parent=self,
            analysis_service=self.small_study_effects_service,
        )
        form.exec()

    def data_dirtied(self):
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
        self._notify_user_that_data_is_unsaved()

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
        form.show()

    def cum_ma(self):
        form = None
        if self.model.get_current_outcome_type() != "diagnostic":
            form = self._build_analysis_specs_dialog(
                analysis_type="cumulative",
                confidence_level=self.model.get_confidence_level(),
            )
        else:
            form = diagnostic_metrics_dialog.DiagnosticMetricsDialog(
                self.model, analysis_type="cumulative", parent=self
            )

        if form is None:
            return
        form.show()

    def loo_ma(self):
        form = None
        if self.model.get_current_outcome_type() != "diagnostic":
            form = self._build_analysis_specs_dialog(
                analysis_type="leave-one-out",
                confidence_level=self.model.get_confidence_level(),
            )
        else:
            form = diagnostic_metrics_dialog.DiagnosticMetricsDialog(
                self.model, analysis_type="leave-one-out", parent=self
            )

        if form is None:
            return
        form.show()

    def show_about_legal(self):
        return about_legal_dialog.AboutLegalDialog(self).exec()

    def show_quick_start(self):
        QMessageBox.information(self, "RC MetaStudio quick start",
            "1. Create a dataset and name its outcome and arms. Intervention / Control are the comparative defaults; use the actual treatment names when available. Single-arm data use Group, and diagnostic data use Index test. Existing projects retain their names; rename groups from a column header. Import a UTF-8 CSV using the template and mapping on the import page, or open a sample project.\n\n"
            "2. Enter studies in the table. Click the row calculator to edit study data. Calculated effects use complete raw data where available.\n\n"
            "3. Choose an effect metric matching your data. Add a Numeric or Category covariate for meta-regression; subgroup analysis needs a Category.\n\n"
            "4. Run an analysis, then use the result navigation to select a section or plot. Text report exposes selectable output. Tables provides selectable cells: copy a selection or export the table as CSV. Copy report and Export report keep the analysis identity and table rows. Select a plot to edit or export it.\n\n"
            "5. Change settings… reopens the executed setup; Run creates another result for comparison. The original stays open.\n\n"
            "Cumulative analysis follows the input table sequence: sort the table before running. Plot study order changes display only; it cannot change the cumulative sequence. Small-study effects do not establish publication bias.\n\n"
            "Shortcuts: Ctrl+N New, Ctrl+O Open, Ctrl+S Save. Results: Ctrl+T text/figure view, Ctrl+Shift+C copy report, Ctrl+Shift+E export selected plot.")

    def meta_subgroup(self, selected_covariate):
        form = None
        if self.model.get_current_outcome_type() != "diagnostic":
            form = self._build_analysis_specs_dialog(
                analysis_type="subgroup",
                external_params={"cov_name": selected_covariate},
                confidence_level=self.model.get_confidence_level(),
            )
        else:
            form = diagnostic_metrics_dialog.DiagnosticMetricsDialog(
                self.model,
                analysis_type="subgroup",
                parent=self,
                external_params={"cov_name": selected_covariate},
            )

        if form is None:
            return
        form.show()

    def _build_analysis_specs_dialog(
        self,
        analysis_type=None,
        external_params=None,
        diagnostic_metrics=None,
        confidence_level=None,
    ):
        try:
            kwargs = {
                "analysis_type": analysis_type,
                "parent": self,
                "confidence_level": confidence_level,
            }
            if external_params is not None:
                kwargs["external_params"] = external_params
            if diagnostic_metrics is not None:
                kwargs["diagnostic_metrics"] = diagnostic_metrics
            return analysis_setup_dialog.AnalysisSetupDialog(
                self.model, analysis_service=self.analysis_service, **kwargs
            )
        except Exception as e:
            self._show_analysis_specs_error(e)
            return None

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
        self._update_project_identity()
        if position is not None:
            self.tableView.setCurrentIndex(self.model.index(*position))

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

        elif self.model.get_current_outcome_type() in ("time_to_event", "event_rates"):
            metric = "HR" if self.model.get_current_outcome_type() == "time_to_event" else "IRR"
            self.add_metrics([], [metric], metric_to_check=metric)
            self.metric_menu_is_set_for = self.model.get_current_outcome_type(get_str=False)
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
        label = analysis_identity.metric_label(self.model, metric)
        text = label if metric == "TX Mean" else f"{label} ({metric})"
        metric_action = QAction(text, self)
        metric_action.setToolTip(label)
        metric_action.setStatusTip(label)
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
        if data_type in (meta_globals.BINARY, meta_globals.CONTINUOUS, *meta_globals.RATIO_DATA_TYPES):
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
        self.toggle_menu_options_that_require_dataset(self.action_go.isEnabled())

    def analysis(self, results: AnalysisResult, *, change_settings=None):
        try:
            form = results_window.ResultsWindow(results, parent=self, change_settings=change_settings)
        except Exception as e:
            app_error_handler.log_exception(type(e), e, e.__traceback__)
            QMessageBox.critical(
                self,
                "Could Not Display Analysis Results",
                "The analysis completed, but RC MetaStudio could not display "
                "the results.\n\nDetails: %s: %s" % (e.__class__.__name__, e),
            )
            return
        form.show()

    def edit_group_name(self, cur_group_name):
        orig_group_name = copy.copy(cur_group_name)
        edit_group_form = edit_name_dialogs.EditGroupNameDialog(
            cur_group_name, parent=self
        )
        if edit_group_form.exec():
            try:
                existing_groups = list(self.model.arm_names)
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
        form = add_new_dialogs.AddCovariateDialog(self, existing_names=self.model.get_covariate_names())
        form.covariate_name_le.setFocus()
        if form.exec():
            # then the user clicked 'ok'.
            try:
                new_covariate_name = dataset_table_model.validate_new_covariate_name(
                    self.model, form.covariate_name_le.text()
                )
            except ValueError as exc:
                QMessageBox.warning(self, "Warning", str(exc))
                return

            # Covariate names must remain unique.
            new_covariate_type = str(form.datatype_cbo_box.currentData())
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
            state["stable_id"] = covariate["id"]

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


    def _update_navigation_controls(self):
        pass



    def open(self, file_path=None, raise_on_error=False):
        """Open a validated structured project and restore its durable working state.

        Opening a project is a document boundary, not an undoable edit. The undo stack is
        reset after a successful load so Ctrl+Z cannot step back into the previously open
        dataset.
        """
        if not self._authorize_destructive_project_action():
            return

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
        self.model.analysis_source_path = file_path
        self._update_project_identity("Opened")
        self._update_recent_project_nonfatal(file_path, "opened")
        return True

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
                recalculate_outcomes=True,
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
        if len(model.get_studies(False)) >= 2:
            self.enable_menu_options_that_require_dataset()
        else:
            self.disable_menu_options_that_require_dataset()
        self._refresh_advanced_analysis_actions()
        self.populate_metrics_menu(metric_to_check=model.current_effect)
        self.update_outcome_lbl()
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
        sheet = copy.deepcopy(self.model.current_sheet)
        change_type_form = covariate_type_dialog.CovariateTypeDialog(sheet, covariate, parent=self)
        if change_type_form.exec():
            def apply():
                self.model.current_sheet.covariates = sheet.covariates
                self.model.current_sheet.rows = sheet.rows
                self.model._sync_display_studies()
                self.model.reset_model()
            self._commit_model_operation(apply)

    def rename_covariate(self, covariate):
        orig_cov_name = copy.copy(covariate['name'])
        # The group-name editor is also used for covariate labels.
        edit_cov_form = edit_name_dialogs.EditCovariateNameDialog(
            orig_cov_name, parent=self
        )
        if edit_cov_form.exec():
            # the field names are also poorly named, in this case. here we mean the
            # **covariate name**, of course.
            try:
                existing_covariates = list(self.model.get_covariate_names())
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
        self._commit_model_operation(lambda: self.model.remove_covariate(covariate))
        self._refresh_advanced_analysis_actions()

    def _refresh_advanced_analysis_actions(self):
        self._enable_action_meta_regression()
        self._enable_action_subgroup_ma()

    def _add_study(self, study, study_index=None):
        self.model.current_sheet.rows.insert(study_index if study_index is not None else len(self.model.current_sheet.rows), study)
        self.model.reset_model()
        self.data_dirtied()

    def _remove_study(self, study):
        self.model.current_sheet.rows.remove(study)
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
        add_blank_study = not data_model.sheets
        self.model = dataset_table_model.DatasetTableModel(
            dataset=data_model, add_blank_study=add_blank_study
        )

        self._disconnect_model_signals()
        if bool(data_model.sheets and len(data_model.sheets[0].rows) >= 2):
            self.enable_menu_options_that_require_dataset()
        else:
            self.disable_menu_options_that_require_dataset()

        self._enable_action_meta_regression(bool(data_model.sheets and len(data_model.sheets[0].rows) >= 2))

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
        if self.model.current_sheet:
            self.model.set_current_sheet(self.model.current_sheet_id)
            if recalculate_outcomes:
                self.model.hydrate_derived_previews()
        self._disconnect_model_signals()
        self._setup_connections(menu_actions=False)
        self.tableView.synchronize_column_widths()
        self.populate_metrics_menu(metric_to_check=self.model.current_effect)
        self.model.reset_model()
        self._update_confidence_level_label()
        self._refresh_sheet_tabs()

    def _swap_sheet_arms(self):
        sheet = self.model.current_sheet
        if sheet and sheet.family != "diagnostic" and len(sheet.arms) == 2 and self.model.current_effect not in meta_globals.ONE_ARM_METRICS:
            self._sheet_change(sheet.id, sheet.arms.reverse)

    def _refresh_sheet_tabs(self):
        self.sheet_tabs.blockSignals(True)
        while self.sheet_tabs.count():
            self.sheet_tabs.removeTab(0)
        for sheet in self.model.dataset.sheets:
            index = self.sheet_tabs.addTab(sheet.name)
            self.sheet_tabs.setTabData(index, sheet.id)
            self.sheet_tabs.setTabToolTip(index, sheet.name)
            if sheet.id == self.model.current_sheet_id:
                self.sheet_tabs.setCurrentIndex(index)
        self.sheet_tabs.blockSignals(False)

    def _select_sheet_tab(self, index):
        if index < 0:
            return
        self.model.set_current_sheet(self.sheet_tabs.tabData(index))
        self.workspace.select_sheet(self.model.current_sheet_id)
        self.model_updated()
        self._update_workspace_guidance()

    def _sheet_change(self, sheet_id, operation):
        self.model.set_current_sheet(sheet_id)
        self.workspace.select_sheet(sheet_id)
        def commit():
            operation()
            self.model_updated()
            self.data_dirtied()
        self._commit_model_operation(commit)

    def _sheet_name(self, title, default):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(title)
        layout = QtWidgets.QVBoxLayout(dialog)
        edit = QtWidgets.QLineEdit(default, dialog)
        edit.selectAll()
        layout.addWidget(edit)
        error = QLabel(dialog)
        layout.addWidget(error)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel, dialog)
        layout.addWidget(buttons)
        def accept():
            name = edit.text().strip()
            if not name or any(sheet.name == name for sheet in self.model.dataset.sheets):
                error.setText("Choose a unique outcome name.")
                return
            dialog.accept()
        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)
        return edit.text().strip() if dialog.exec() else None

    def _add_sheet(self):
        import uuid
        if not self.model.current_sheet:
            return
        number = 2
        while any(sheet.name == f"Outcome {number}" for sheet in self.model.dataset.sheets):
            number += 1
        name = self._sheet_name("Add sheet", f"Outcome {number}")
        if name is None:
            return
        sheet = copy.deepcopy(self.model.current_sheet)
        sheet.id, sheet.name, sheet.rows = uuid.uuid4().hex, name, []
        def add():
            self.model.dataset.sheets.append(sheet)
            self.model.set_current_sheet(sheet.id)
        self._sheet_change(self.model.current_sheet_id, add)

    def _rename_sheet(self, index):
        if index < 0:
            return
        sheet = self.model.dataset.sheet(self.sheet_tabs.tabData(index))
        name = self._sheet_name("Rename sheet", sheet.name)
        if name is not None:
            self._sheet_change(sheet.id, lambda: setattr(sheet, "name", name))

    def _sheet_menu(self, position):
        index = self.sheet_tabs.tabAt(position)
        if index < 0:
            return
        menu = QtWidgets.QMenu(self)
        menu.addAction("Rename", lambda: self._rename_sheet(index))
        delete = menu.addAction("Delete", lambda: self._delete_sheet(index))
        delete.setEnabled(self.sheet_tabs.count() > 1)
        menu.exec(self.sheet_tabs.mapToGlobal(position))

    def _delete_sheet(self, index):
        sheet = self.model.dataset.sheet(self.sheet_tabs.tabData(index))
        if len(self.model.dataset.sheets) == 1:
            return
        if sheet.rows and QMessageBox.question(self, "Delete sheet", f'Delete “{sheet.name}” and its rows?') != QMessageBox.StandardButton.Yes:
            return
        def delete():
            self.model.dataset.sheets.remove(sheet)
            self.model.set_current_sheet(self.model.dataset.sheets[max(0, index - 1)].id)
        self._sheet_change(sheet.id, delete)

    def _move_sheet_tab(self, source, destination):
        sheet_id = self.model.current_sheet_id
        self.model.set_current_sheet(sheet_id)
        self.workspace.select_sheet(sheet_id)
        if QApplication.mouseButtons() & Qt.MouseButton.LeftButton and not self._sheet_dragging:
            self.workspace.begin_change()
            self._sheet_dragging = True
        def move():
            sheets = self.model.dataset.sheets
            sheets.insert(destination, sheets.pop(source))
            self.data_dirtied()
        self._commit_model_operation(move)

    def update_outcome_lbl(self):
        pass

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
        self._update_project_identity("Saved")
        if durability_error is not None:
            self._report_durability_uncertain_save(destination, durability_error)
        self._update_recent_project_nonfatal(destination, "saved")
        return True

    def _make_new_dataset_and_setup_spreadsheet(self, dataset_info):
        import uuid
        from rc_metastudio.analysis_dataset import Sheet, Arm
        data_type = meta_globals.STR_TO_TYPE_DICT[dataset_info['data_type']]
        groups = dataset_info.get('groups') or meta_globals.default_group_names(data_type, dataset_info.get('sub_type'))
        sheet = Sheet(uuid.uuid4().hex, dataset_info['name'], data_type, dataset_info.get('sub_type'), dataset_info['data_type'], [Arm(uuid.uuid4().hex, name) for name in groups], settings={'metric': dataset_info.get('effect')})
        self.set_model(analysis_dataset.Dataset(sheets=[sheet]))
        self.model.current_effect = dataset_info.get('effect')
        self.populate_metrics_menu(metric_to_check=self.model.current_effect)
        self.model.reset_model()

    def _handle_wizard_results(self, wizard_data):
        path = wizard_data["path"]  # route through wizard

        dataset_info = wizard_data["outcome_info"]

        if path == "open":
            self.open(file_path=wizard_data["selected_dataset"])
        elif path == "new_dataset":
            self._make_new_dataset_and_setup_spreadsheet(dataset_info)
            self.workspace.start_new_document()
            self.out_path = None
            self._notify_user_that_data_is_unsaved()

        elif path == "csv_import":
            csv_data = wizard_data["csv_data"]

            def import_csv() -> None:
                self._make_new_dataset_and_setup_spreadsheet(dataset_info)
                ImportCsvCommand(
                    imported_data=csv_data["data"],
                    main_form=self,
                    covariate_names=csv_data["covariate_names"],
                    covariate_types=csv_data["covariate_types"],
                ).redo()

            self._commit_model_operation(import_csv)
            self.workspace.start_new_document()
            self.out_path = None
            self._notify_user_that_data_is_unsaved()


class ImportCsvCommand:
    def __init__(
        self,
        main_form=None,
        imported_data=None,
        covariate_names=None,
        covariate_types=None,
        description="Import a CSV file",
    ):
        if main_form is None:
            raise ValueError("CSV import requires a main form")
        self.imported_data = csv_import.normalize_import_rows(imported_data or [])
        self.covariate_names = list(covariate_names or [])
        self.covariate_types = list(covariate_types or [])
        self.main_form: MainWindow = main_form

    def redo(self):
        self._import_data_into_new_dataset()

    def _import_data_into_new_dataset(self):
        num_rows = len(self.imported_data)
        if num_rows == 0:
            return
        num_cols = len(self.imported_data[0])

        if self.covariate_names != []:
            for name, covariate_type in zip(self.covariate_names, self.covariate_types):
                self.main_form._add_new_covariate(name, covariate_type)

        # Copy data into table
        import_progress = ImportProgressDialog(
            self.main_form, 0, num_rows * num_cols - 1
        )

        import_progress.setValue(0)
        import_progress.show()
        try:
            for row in range(num_rows):
                for col in range(num_cols):
                    import_progress.setValue(row * num_cols + col)
                    QApplication.processEvents()
                    value = str(self.imported_data[row][col])
                    self.main_form.model.setData(
                        self.main_form.model.index(row, col + 1), value, import_csv=True
                    )

        finally:
            progress_dialog.hide_once(import_progress)
