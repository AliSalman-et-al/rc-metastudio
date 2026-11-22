# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Main RC MetaStudio desktop window."""

from __future__ import annotations
from rc_metastudio.domain_ids import ArmId, SheetId

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING
from PyQt6 import QtCore, QtGui, QtWidgets, sip
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QMouseEvent,
    QAction,
    QCloseEvent,
    QKeyEvent,
    QKeySequence,
    QResizeEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QTableView,
)
import copy

if TYPE_CHECKING:
    from rc_metastudio.results.report import ManuscriptReport
    import ui_main_window as _ui_main_window
else:
    from rc_metastudio import ui_main_window as _ui_main_window
from rc_metastudio.workspace import table_view as dataset_table_view
from rc_metastudio.workspace import table_model as dataset_table_model
from rc_metastudio.analysis import catalog as analysis_catalog

from rc_metastudio.project import model as analysis_dataset
from rc_metastudio.analysis import requests as analysis_adapter
from rc_metastudio.analysis import identity as analysis_identity
from rc_metastudio import app_error_handler
from rc_metastudio.app_error_handler import connect_action
from rc_metastudio import r_runtime
from rc_metastudio.analysis import progress_dialog
from rc_metastudio import qt_layout
from rc_metastudio import adaptive_window
from rc_metastudio import name_validation
from rc_metastudio.project import adapter as project_adapter
from rc_metastudio.project import archive as project_format
from rc_metastudio.importing import tabular as csv_import
from rc_metastudio.workspace import editing as workspace_editing
from rc_metastudio.settings import (
    add_file_to_recent_files,
    get_default_open_directory,
    get_recent_files,
    get_sample_projects_path,
    get_user_documents_path,
    load_main_column_widths,
    migrate_application_settings,
    recent_file_display_name,
    remove_recent_file,
    save_main_window_placement,
)
from rc_metastudio.qt_object_guard import required

from rc_metastudio import add_new_dialogs
from rc_metastudio.results import window as results_window
from rc_metastudio.analysis import setup_dialog as analysis_setup_dialog
from rc_metastudio.analysis import small_study_effects_dialog
from rc_metastudio.analysis import small_study_effects
from rc_metastudio.analysis import (
    trial_sequential as trial_sequential_analysis,
    trial_sequential_dialog as trial_sequential_analysis_dialog,
)
from rc_metastudio.analysis import diagnostic_metrics_dialog
from rc_metastudio.analysis import subgroup_dialog as subgroup_analysis_dialog
from rc_metastudio import edit_name_dialogs
from rc_metastudio import covariate_type_dialog
from rc_metastudio import confidence_level_dialog
from rc_metastudio import start_page
from rc_metastudio import main_wizard
from rc_metastudio import about_legal_dialog

from rc_metastudio.results.contract import AnalysisResult
from rc_metastudio.workspace.session import WorkspaceSession


DEFAULT_DATASET_NAME = "untitled_dataset"




def _is_bundled_sample(path: str | Path) -> bool:
    return Path(path).resolve().is_relative_to(Path(get_sample_projects_path()).resolve())


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
    if isinstance(exception, project_format.ProjectFormatError):
        reason = str(exception)
        if isinstance(exception, project_format.UnsupportedProjectVersionError):
            message = "This project's file format is not supported. Update RC MetaStudio, then try again."
        elif isinstance(exception, project_format.ProjectAccessError):
            message = 'RC MetaStudio could not read this file. Check that it exists and that you can open it.'
        else:
            message = 'This file is damaged or is not a valid RC MetaStudio project. Open another .rcms file or restore a backup.'
        return message + '\n\nDetails: ' + reason
    return "Could not open %s.\n\nDetails: %s" % (
        file_path,
        exception,
    )






def _pooled_analysis_availability(
    label: str, minimum: int, included: int, r_ready: bool,
) -> tuple[bool, str]:
    if r_ready and included >= minimum:
        return True, label
    if not r_ready and included:
        return False, "R is not ready"
    if not included:
        return False, "requires at least 1 included study"
    return False, f"requires at least {minimum} included studies"


class ImportProgressDialog(progress_dialog.AnalysisProgressDialog):
    def __init__(self, parent=None, row_count: int = 1):
        super().__init__(parent, operation="Importing study data…", blocking=False)
        self.setWindowTitle("Import data")
        self.progress_bar.setRange(0, row_count)
        self.progress_bar.show()


class SheetNameEditor(QtWidgets.QLineEdit):
    cancelled = QtCore.pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event is not None and event.key() == Qt.Key.Key_Escape:
            event.accept()
            self.cancelled.emit()
            return
        super().keyPressEvent(event)


class SheetTabBar(QtWidgets.QTabBar):
    stripPaletteChanged = QtCore.pyqtSignal(QtGui.QPalette, str)
    resized = QtCore.pyqtSignal()
    orderChanged = QtCore.pyqtSignal()
    _updating_palette: bool = False
    _tab_width_limit: int = 0

    def __init__(self, parent):
        super().__init__(parent)
        self._drag_order_changed = False
        self.tabMoved.connect(self._tab_moved)

    def changeEvent(self, a0: QtCore.QEvent | None) -> None:
        super().changeEvent(a0)
        event = a0
        if event is None:
            return
        if event.type() not in (QtCore.QEvent.Type.ApplicationPaletteChange, QtCore.QEvent.Type.PaletteChange) or self._updating_palette:
            return
        self._updating_palette = True
        try:
            palette = QtWidgets.QApplication.palette()
            self._apply_tab_palette(palette)
        finally:
            self._updating_palette = False

    def _apply_tab_palette(self, palette: QtGui.QPalette) -> None:
        window_color = palette.color(QtGui.QPalette.ColorRole.Window)
        text = palette.color(QtGui.QPalette.ColorRole.WindowText)
        base = palette.color(QtGui.QPalette.ColorRole.Base).name()
        highlight = palette.color(QtGui.QPalette.ColorRole.Highlight).name()

        def blend(opacity):
            return QtGui.QColor(*(round(fg * opacity + bg * (1 - opacity))
                                 for fg, bg in zip(text.getRgb()[:3], window_color.getRgb()[:3]))).name()

        rule, muted, hover = blend(.20), blend(.70), blend(.08)
        self.setStyleSheet(f"""
            QTabBar {{ background: {window_color.name()}; border: 0; }}
            QTabBar::tab {{ background: {window_color.name()}; color: {muted};
                font-weight: normal; padding: 4px 12px;
                max-width: {(self._tab_width_limit or self.fontMetrics().height() * 28)}px;
                border: 0; border-top: 1px solid {rule};
                border-left: 1px solid transparent; border-right: 1px solid {rule};
                border-bottom: 2px solid transparent; }}
            QTabBar::tab:hover {{ background: {hover}; color: {text.name()}; }}
            QTabBar::tab:selected {{ background: {base}; color: {text.name()};
                border-top-color: {base}; border-left-color: {rule};
                border-bottom-left-radius: 3px; border-bottom-right-radius: 3px; }}
            QTabBar::tab:selected:focus {{ border-bottom-color: {highlight}; }}
        """)
        self.stripPaletteChanged.emit(palette, f"""
            QToolButton {{ background: transparent; color: {text.name()};
                border: 0; border-top: 1px solid {rule}; padding: 0; }}
            QToolButton:hover {{ background: {hover}; }}
            QToolButton:focus {{ border: 1px solid {highlight}; }}
        """)

    def eventFilter(self, a0: QtCore.QObject | None, a1: QtCore.QEvent | None) -> bool:
        if a0 is not None and sip.isdeleted(a0):
            return True
        if a1 is not None and a1.type() == QtCore.QEvent.Type.ApplicationPaletteChange:
            self.changeEvent(a1)
        return super().eventFilter(a0, a1)

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        size.setWidth(min((self._tab_width_limit or self.fontMetrics().height() * 28),
                          max(self.fontMetrics().height() * 4, size.width())))
        return size

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        super().resizeEvent(a0)
        self.resized.emit()

    def _tab_moved(self, _source: int, _destination: int) -> None:
        if QApplication.mouseButtons() & Qt.MouseButton.LeftButton:
            self._drag_order_changed = True
        else:
            self.orderChanged.emit()

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        super().mouseReleaseEvent(a0)
        if self._drag_order_changed:
            self._drag_order_changed = False
            self.orderChanged.emit()


class MainWindow(QtWidgets.QMainWindow, _ui_main_window.Ui_MainWindow):
    model: dataset_table_model.DatasetTableModel
    sheet_name_edit: QtWidgets.QLineEdit | None
    tableView: dataset_table_view.DatasetTableView

    def __init__(self, parent=None):
        super().__init__(parent)
        self.analysis_service = analysis_adapter.AnalysisService()
        self.small_study_effects_service = small_study_effects.SmallStudyEffectsService()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setupUi(self)
        qt_layout.configure_analysis_menu(self.menuAnalysis)
        self.menuAnalysis.setToolTipsVisible(True)
        for action, icon_name in (
            (self.action_go, "meta-analysis"),
            (self.action_cum_ma, "cumulative-analysis"),
            (self.action_loo_ma, "leave-one-out-analysis"),
            (self.action_trial_sequential_analysis, "trial-sequential-analysis"),
            (self.action_subgroup_ma, "subgroup-analysis"),
            (self.action_meta_regression, "meta-regression"),
            (self.action_publication_bias, "publication-bias"),
        ):
            qt_layout.configure_analysis_action_icon(action, icon_name)
        self.analysis_button = QtWidgets.QToolButton(self.toolBar)
        self.analysis_button.setDefaultAction(self.action_go)
        self.analysis_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.analysis_button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.analysis_button.setMenu(self.menuAnalysis)
        self.analysis_button.setAccessibleName("Analyses")
        self.analysis_button.setAccessibleDescription("Choose an analysis. Unavailable analyses explain their prerequisites in the menu.")
        self.analysis_button.setToolTip("Choose an analysis")
        self.analysis_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.toolBar.insertWidget(self.action_go, self.analysis_button)
        for action in (self.action_go, self.action_cum_ma, self.action_loo_ma, self.action_trial_sequential_analysis, self.action_subgroup_ma,
                       self.action_meta_regression, self.action_publication_bias, self.action_change_confidence_level):
            self.toolBar.removeAction(action)
        self.action_new_dataset.setText("New project…")
        qt_layout.configure_main_toolbar(self.toolBar)
        self.analysis_button.setAccessibleName("Analyses")
        self.sample_menu = QtWidgets.QMenu("Open sample project", self)
        sample_root = Path(get_sample_projects_path())
        manifest = sample_root / "manifest.json"
        entries = {}
        if manifest.is_file():
            entries = {item["file"]: item for item in json.loads(manifest.read_text(encoding="utf-8"))["projects"]}
        order = {name: index for index, name in enumerate(entries)}
        for path in sorted(sample_root.glob("*.rcms"), key=lambda path: (order.get(path.name, len(order)), path.name.casefold())):
            entry = entries.get(path.name, {})
            caption = entry.get("scientific_name") or path.stem
            description = entry.get("description")
            action = QAction(f"{caption} — {description}" if description else caption, self.sample_menu)
            action.setData(path.name)
            self.sample_menu.addAction(action)
            connect_action(action, lambda sample=path: self.open(file_path=str(sample)))
        self.sample_menu.setEnabled(bool(self.sample_menu.actions()))
        self.start_page = start_page.StartPage(
            self.action_new_dataset, self.action_import_csv, self.action_open, self,
            sample_menu=self.sample_menu,
        )
        self.verticalLayout_3.insertWidget(0, self.start_page)
        self.menu_file.clear()
        for action in (self.action_new_dataset, self.action_open,
                       self.action_open_recent_2.menuAction(), self.sample_menu.menuAction(), self.action_import_csv):
            self.menu_file.addAction(action)
        self.menu_file.addSeparator()
        self.menu_file.addActions([self.action_save, self.action_save_as])
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_quit)
        self.action_publication_bias.setText("Small-study effects…")
        self.action_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        adaptive_window.register_adaptive_window(self, adaptive_window.WindowRole.MAIN)
        table_view = dataset_table_view.DatasetTableView(self.nav_frame)
        self.verticalLayout.replaceWidget(self.tableView, table_view)
        self.tableView.deleteLater()
        self.tableView = table_view
        self.menuEdit.addSeparator()
        self.menuEdit.addAction(self.tableView.study_calculator_action)
        self.tableView.restore_column_widths(load_main_column_widths())

        self.confidence_button = QtWidgets.QPushButton(self.statusbar)
        self.confidence_button.setObjectName("sheet_confidence")
        self.confidence_button.setText("95% CI…")
        self.confidence_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.confidence_button.setAccessibleName("Outcome confidence level, 95%")
        self.confidence_button.setToolTip("Default confidence level for table effects and new analyses on this outcome. Individual analyses can override it.")
        self.confidence_button.clicked.connect(self.action_change_confidence_level.trigger)
        self.statusbar.addPermanentWidget(self.confidence_button)
        self.confidence_button.hide()

        self._setup_sheet_strip()
        self.sheet_tabs.currentChanged.connect(app_error_handler.safe_slot(self._select_sheet_tab, parent=self))
        self.sheet_tabs.orderChanged.connect(app_error_handler.safe_slot(self._save_sheet_order, parent=self))
        self.sheet_tabs.tabBarDoubleClicked.connect(self._rename_sheet)
        self.sheet_tabs.customContextMenuRequested.connect(self._sheet_menu)
        self.add_sheet_button.clicked.connect(self._add_sheet)
        self.menuView.addSeparator()
        self.outcome_navigation_actions = []
        for label, sequence, delta in (("Previous outcome", "Ctrl+PgUp", -1), ("Next outcome", "Ctrl+PgDown", 1)):
            action = QAction(label, self)
            action.setShortcut(QKeySequence(sequence))
            action.setToolTip(label + " (" + sequence + ")")
            action.triggered.connect(lambda checked=False, delta=delta: self.sheet_tabs.setCurrentIndex((self.sheet_tabs.currentIndex() + delta) % max(1, self.sheet_tabs.count())))
            self.addAction(action)
            self.outcome_navigation_actions.append(action)
        self.add_outcome_action = QAction("Add outcome…", self)
        self.add_outcome_action.triggered.connect(self._add_sheet)
        self.rename_outcome_action = QAction("Rename outcome…", self.sheet_tabs)
        self.rename_outcome_action.setShortcut(QKeySequence("F2"))
        self.rename_outcome_action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        self.sheet_tabs.addAction(self.rename_outcome_action)
        self.rename_outcome_action.triggered.connect(lambda: self._rename_sheet(self.sheet_tabs.currentIndex()))
        self.menuDataset.addSeparator()
        self.menuDataset.addActions((self.add_outcome_action, self.rename_outcome_action))
        from rc_metastudio.citation_dialog import CitationDialog
        cite_action = QAction(QtGui.QIcon(':/icons/actions/cite.svg'), 'Cite…', self)
        cite_action.triggered.connect(lambda: CitationDialog(self).exec())
        self.menuHelp.addAction(cite_action)
        self.action_about_legal.setText('About RC MetaStudio…')
        self.add_outcome_action.setIcon(QtGui.QIcon(':/icons/actions/add.svg'))
        self.rename_outcome_action.setIcon(QtGui.QIcon(':/icons/actions/edit-dataset.svg'))
        theme_menu = self.menuView.addMenu('Theme')
        theme_group = QtGui.QActionGroup(self)
        theme_group.setExclusive(True)
        schemes = {'System': Qt.ColorScheme.Unknown, 'Light': Qt.ColorScheme.Light, 'Dark': Qt.ColorScheme.Dark}
        selected_theme = str(QtCore.QSettings().value('appearance/theme', 'System'))
        def set_theme(name):
            QtCore.QSettings().setValue('appearance/theme', name)
            required(QApplication.styleHints(), 'style hints').setColorScheme(schemes[name])
        for name in schemes:
            theme_action = QAction(name, self)
            theme_action.setCheckable(True)
            theme_action.setChecked(name == selected_theme)
            theme_group.addAction(theme_action)
            required(theme_menu, 'Theme menu').addAction(theme_action)
            theme_action.triggered.connect(lambda checked=False, name=name: set_theme(name))
        set_theme(selected_theme if selected_theme in schemes else 'System')
        self.menuHelp.removeAction(self.action_about_legal)
        self.menuHelp.addSeparator()
        self.menuHelp.addAction(self.action_about_legal)
        self.menuDataset.addSeparator()
        self.action_swap_arms = QAction(QtGui.QIcon(":/icons/actions/swap.svg"), "Swap intervention and control", self)
        self.menuDataset.addAction(self.action_swap_arms)
        self.effect_direction_menu = required(self.menuDataset.addMenu("Effect direction"), "effect direction")
        self.effect_direction_menu.aboutToShow.connect(self._populate_effect_direction)
        self.menuDataset.aboutToShow.connect(self._update_swap_arms_enabled)
        self.action_swap_arms.triggered.connect(self._swap_sheet_arms)
        self.workspace = WorkspaceSession()
        data_model = analysis_dataset.Dataset(title=DEFAULT_DATASET_NAME)
        self.model = dataset_table_model.DatasetTableModel(dataset=data_model)
        self.workspace.record_edit(data_model, self.model.current_sheet_id)

        self.tableView.setModel(self.model)
        self.tableView.setItemDelegate(dataset_table_view.StudyDelegate(self.tableView))

        self._model_signal_connections = []
        self._connect_model_signals()
        self._connect_actions()
        self._configure_standard_shortcuts()
        self.tableView.setSelectionMode(QTableView.SelectionMode.ContiguousSelection)
        self.model.reset_model()
        self.tableView.edit_transaction = self._commit_model_operation
        for request, command in (
            (self.tableView.studyDeletionRequested, self.delete_study),
            (self.tableView.armRenameRequested, self.edit_arm_name),
            (self.tableView.covariateRenameRequested, self.rename_covariate),
            (self.tableView.covariateDeletionRequested, self.delete_covariate),
            (self.tableView.covariateConversionRequested, self.change_covariate_type),
            (self.tableView.undoRequested, self.undo),
            (self.tableView.redoRequested, self.redo),
            (self.tableView.pasteNotice, self._show_paste_notice),
            (self.tableView.clipboardError, self.data_error),
        ):
            request.connect(app_error_handler.safe_slot(command, parent=self))
        self.tableView.synchronize_column_widths()

        self._metric_actions: QtGui.QActionGroup | None = None

        migrate_application_settings()
        self.populate_open_recent_menu()
        self.workspace.mark_saved()
        self._update_project_identity()
        self.refresh_analysis_actions()
        self._update_workspace_guidance()

    def createPopupMenu(self):
        return None

    def start(self):
        self._update_workspace_guidance()
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(
        self, event: QCloseEvent | None
    ) -> None:
        if event is None:
            return
        if not self._confirm_discard_or_save():
            event.ignore()
            return
        self._disconnect_model_signals()
        save_main_window_placement(self, self.tableView.column_width_state())
        event.accept()

    def _confirm_discard_or_save(self):
        if not self.workspace.is_dirty:
            return True
        choice = self.prompt_to_save_unsaved_data()
        if choice == QMessageBox.StandardButton.Save:
            return self.save() is True
        return choice == QMessageBox.StandardButton.Discard

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
                    "Recent projects not updated",
                    "The project was %s, but RC MetaStudio could not update the Open recent list."
                    "\n\nDetails: %s" % (operation, exc),
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
                "Project saved, but not confirmed",
                "RC MetaStudio saved the project to %s, but the operating "
                "system could not confirm the save is complete on disk. Keep a backup "
                "copy until you save again.\n\nDetails: %s" % (destination, exception),
            )
        except Exception:
            pass

    def _configure_standard_shortcuts(self):
        """Use platform-native shortcuts for the maintained shell actions."""
        for action, standard_key in (
            (self.action_new_dataset, QKeySequence.StandardKey.New),
            (self.action_open, QKeySequence.StandardKey.Open),
            (self.action_save, QKeySequence.StandardKey.Save),
        ):
            action.setShortcut(QKeySequence(standard_key))
        self.action_quit.setShortcut(QKeySequence("Ctrl+Q"))
        self.action_go.setShortcut(QKeySequence("Ctrl+R"))
        for menu in (self.menu_file, self.menuEdit, self.menuView, self.menuAnalysis, self.menuDataset, self.menuHelp):
            menu.setTitle("&" + menu.title().replace("&", ""))

    def create_new_dataset(self, _checked=False):
        if not self._confirm_discard_or_save():
            return

        wizard = main_wizard.MainWizard(parent=self, path="new_dataset")
        if wizard.exec():
            wizard_data = wizard.get_results()
            self._handle_wizard_results(wizard_data)

    def _update_project_identity(self, state=None):
        path = self.workspace.path
        name = path.name if path is not None else "Untitled project"
        if path is not None and _is_bundled_sample(path):
            name = f"{path.stem.partition(' - ')[2] or path.stem} (sample)"
        dirty = self.workspace.is_dirty
        self.setWindowTitle(f"{name}{' *' if dirty else ''} — RC MetaStudio")
        self.setWindowFilePath(str(path) if path is not None else "")
        if state:
            self.statusbar.showMessage(state, 4000)

    def refresh_analysis_actions(self) -> None:
        self.tableView.refresh_study_calculator()
        included = sum(not study.manually_excluded for study in self.model.get_studies())
        r_ready = r_runtime.is_ready()
        can_analyze = r_ready and included > 0
        sheet = self.model.current_sheet
        covariates = sheet.covariates if sheet else ()
        has_factor = any(covariate["data_type"] == analysis_catalog.FACTOR for covariate in covariates)
        self.action_publication_bias.setEnabled(can_analyze)
        self.action_meta_regression.setEnabled(can_analyze and bool(covariates))
        self.action_subgroup_ma.setEnabled(can_analyze and has_factor)

        for action, label, minimum, shortcut in (
            (self.action_go, "Meta-analysis", 1, " (Ctrl+R)"),
            (self.action_cum_ma, "Cumulative meta-analysis", 1, ""),
            (self.action_loo_ma, "Leave-one-out meta-analysis", 2, ""),
        ):
            enabled, tooltip = _pooled_analysis_availability(label, minimum, included, r_ready)
            action.setEnabled(enabled)
            action.setToolTip(tooltip + shortcut)
        tsa_enabled, tsa_tooltip = _pooled_analysis_availability(
            trial_sequential_analysis.TSA_TITLE, 2, included, r_ready,
        )
        if sheet is not None and self.model.current_effect not in trial_sequential_analysis.SUPPORTED.get(sheet.family, ()):
            tsa_enabled = False
            tsa_tooltip = "Trial sequential analysis supports two-arm RR, OR, RD, Peto OR, MD and reported HR."
        self.action_trial_sequential_analysis.setEnabled(tsa_enabled)
        self.action_trial_sequential_analysis.setToolTip(tsa_tooltip)
        self.action_meta_regression.setToolTip(
            "Meta-regression" if covariates else "Add a covariate to run meta-regression."
        )
        self.action_subgroup_ma.setToolTip(
            "Subgroup meta-analysis" if has_factor else "Add a categorical covariate to run subgroup analysis."
        )

    def _update_workspace_guidance(self):
        enable = self.model.current_sheet is not None
        self.action_save.setEnabled(enable)
        self.action_save_as.setEnabled(enable)
        self.action_save.setToolTip("Save project (Ctrl+S)" if enable else "Create or open a project to save it")
        self.start_page.setVisible(not enable)
        self.nav_frame.setVisible(enable)
        self.confidence_button.setVisible(enable)
        self.add_outcome_action.setEnabled(enable)
        self.rename_outcome_action.setEnabled(enable)
        for action in self.outcome_navigation_actions:
            action.setEnabled(enable and self.sheet_tabs.count() > 1)

    def _show_paste_notice(self, message: str) -> None:
        self.statusbar.showMessage(message, 8000)

    def _disconnect_model_signals(self):
        """Disconnect signals owned by the current dataset model."""
        for connection in self._model_signal_connections:
            connection.disconnect()
        self._model_signal_connections = []

    def data_error(self, msg):
        QMessageBox.warning(self, "Could not edit study data", msg)

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
            self.action_open_recent_2.addAction(action_item)
            connect_action(
                action_item, lambda dataset=dataset: self.dataset_selected(dataset)
            )

    def _remove_recent_project(self, path):
        remove_recent_file(path)
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

            self._commit_model_operation(apply_confidence_level)

    def _import_data(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import data", "", main_wizard.IMPORT_FILE_FILTER
        )
        if not path:
            return
        wizard = main_wizard.MainWizard(parent=self)
        try:
            if not wizard.import_file(path):
                return
            if wizard.get_wizard_path() == "rm5_import" or wizard.exec():
                if self._confirm_discard_or_save():
                    self._handle_wizard_results(wizard.get_results())
        finally:
            wizard.deleteLater()

    def _connect_model_signals(self):
        model = self.model
        self._model_signal_connections.append(
            app_error_handler.connect_safely(
                model.workspaceEditCommitted,
                self._workspace_edit_committed,
                parent=self,
            )
        )

        self._model_signal_connections.append(
            app_error_handler.connect_safely(
                model.dataError, self.data_error, parent=self
            )
        )

    def _connect_actions(self):
        connect_action(self.action_save, self.save)
        connect_action(self.action_save_as, self.save_as)
        connect_action(self.action_open, self.open)
        connect_action(self.action_new_dataset, self.create_new_dataset)
        connect_action(self.action_quit, self.quit)
        connect_action(self.action_go, self._launch_analysis)
        connect_action(self.action_cum_ma, lambda: self._launch_analysis("cumulative"))
        connect_action(self.action_loo_ma, lambda: self._launch_analysis("leave-one-out"))
        connect_action(self.action_trial_sequential_analysis, self._trial_sequential_analysis)

        connect_action(self.action_undo, self.undo)
        connect_action(self.action_redo, self.redo)
        connect_action(self.action_copy, self.tableView.copy)
        connect_action(self.action_paste, self.tableView.paste)
        connect_action(self.action_auto_fit_columns, self.tableView.auto_fit_columns)
        connect_action(self.action_add_covariate, self.add_covariate)

        connect_action(self.action_meta_regression, lambda: self._launch_analysis("meta-regression"))
        connect_action(self.action_publication_bias, self.small_study_effects)
        connect_action(self.action_subgroup_ma, self._choose_subgroup_covariate)

        connect_action(self.action_about_legal, self.show_about_legal)
        connect_action(self.action_change_confidence_level, self._change_global_ci)
        connect_action(self.action_import_csv, self._import_data)

    def _update_confidence_level_label(self):
        confidence_level = self.model.get_confidence_level()
        self.confidence_button.setText(f"{confidence_level:g}% CI…")
        self.confidence_button.setAccessibleName(f"Outcome confidence level, {confidence_level:g}%")

    def _launch_analysis(
        self, analysis_type: analysis_adapter.AnalysisWorkflow | None = None,
        *, covariate: str | None = None,
    ) -> None:
        external_params = {"cov_name": covariate} if covariate is not None else None

        def open_settings(diagnostic_metrics: list[str] | None = None) -> bool:
            form = self._build_analysis_specs_dialog(
                analysis_type=analysis_type,
                external_params=external_params,
                diagnostic_metrics=diagnostic_metrics,
                confidence_level=self.model.get_confidence_level(),
            )
            if form is None:
                return False
            form.show()
            return True

        if not self.model.is_diagnostic():
            open_settings()
        elif analysis_type == "meta-regression":
            open_settings(["sens", "spec"])
        else:
            diagnostic_metrics_dialog.DiagnosticMetricsDialog(
                self.model, open_settings, parent=self
            ).show()

    def _choose_subgroup_covariate(self) -> None:
        subgroup_analysis_dialog.SubgroupAnalysisDialog(
            self.model,
            lambda covariate: self._launch_analysis("subgroup", covariate=covariate),
            parent=self,
        ).show()

    def small_study_effects(self):
        form = small_study_effects_dialog.SmallStudyEffectsDialog(
            self.model,
            parent=self,
            analysis_service=self.small_study_effects_service,
            on_result=self.analysis,
        )
        form.exec()

    def _trial_sequential_analysis(self) -> None:
        sheet = self.model.current_sheet
        if sheet is None:
            return
        settings = trial_sequential_analysis.TSA_SETTINGS
        saved = trial_sequential_analysis.TsaOptions.from_mapping(sheet.settings.get(settings, {}))
        model = dataset_table_model.DatasetTableModel(
            dataset=copy.deepcopy(self.model.dataset), add_blank_study=False, current_sheet_id=sheet.id,
        )
        view: results_window.ResultsWindow | None = None

        def save_options(options: trial_sequential_analysis.TsaOptions) -> None:
            nonlocal saved
            changed = options != saved
            saved = options
            if not changed:
                return

            def update(live_sheet: analysis_dataset.Sheet) -> None:
                if options != trial_sequential_analysis.TsaOptions.from_mapping(live_sheet.settings.get(settings, {})):
                    live_sheet.settings[settings] = options.to_mapping()

            if self.workspace.edit_sheet(sheet, update):
                self._update_project_identity()

        def show_result(result: AnalysisResult, manuscript: ManuscriptReport) -> None:
            nonlocal view
            if view is None:
                view = self.analysis(result, source_sheet=sheet, change_settings=reopen, manuscript=manuscript)
            else:
                view.replace_trial_sequential_result(result, manuscript)

        def reopen(_plot_parameters: dict[str, object], _origin: QtWidgets.QWidget | None = None) -> None:
            form = trial_sequential_analysis_dialog.TrialSequentialAnalysisDialog(
                model, view or self, saved=saved, on_result=show_result, on_settings_saved=save_options,
            )
            form.exec()
            form.deleteLater()

        reopen({})

    def data_dirtied(self):
        self.workspace.record_edit(self.model.dataset, self.model.current_sheet_id)
        self._update_project_identity()

    def _workspace_edit_committed(self):
        self.data_dirtied()
        self.refresh_analysis_actions()

    def _commit_model_operation(self, operation):
        """Run one already validated UI operation as one workspace change."""
        self.workspace.begin_change()
        try:
            operation()
            self.workspace.record_edit(self.model.dataset, self.model.current_sheet_id)
            self.workspace.end_change()
        except BaseException as error:
            runtime = self.workspace.abort_change()
            if runtime is None:
                raise
            try:
                self._install_workspace_runtime(runtime)
                self._update_project_identity()
            except Exception as restore_error:
                error.add_note(f"Workspace adapter restoration also failed: {restore_error}")
            raise
        self._update_project_identity()
        self.refresh_analysis_actions()

    def show_about_legal(self):
        from rc_metastudio import r_operations
        r_version = r_operations.get_r_version_string() if r_runtime.is_ready() else None
        return about_legal_dialog.AboutLegalDialog(self, r_version=r_version).exec()

    def _build_analysis_specs_dialog(
        self,
        analysis_type=None,
        external_params=None,
        diagnostic_metrics=None,
        confidence_level=None,
    ):
        try:
            return analysis_setup_dialog.AnalysisSetupDialog(
                self.model, parent=self, analysis_type=analysis_type,
                external_params=external_params, diagnostic_metrics=diagnostic_metrics,
                confidence_level=confidence_level, analysis_service=self.analysis_service,
                on_result=self.analysis,
            )
        except Exception as e:
            self._show_analysis_specs_error(e)
            return None

    def _show_analysis_specs_error(self, exception):
        if isinstance(exception, r_runtime.AnalysisBackendUnavailableError):
            self._show_analysis_backend_error(exception)
        else:
            self._show_analysis_preparation_error(exception)

    def _show_analysis_backend_error(self, exception, *, startup=False):
        if startup and isinstance(exception, r_runtime.AnalysisBackendUnavailableError):
            QMessageBox.critical(self, "Analysis unavailable", str(exception))
            return
        if startup:
            message = (
                "RC MetaStudio could not start its built-in R runtime, so analyses are unavailable. "
                "Reinstall RC MetaStudio, then try again."
            )
        else:
            message = (
                "R is not available, so the analysis settings cannot be opened."
            )
        message += "\n\nDetails: %s" % exception
        QMessageBox.critical(self, "Analysis unavailable", message)

    def _show_analysis_preparation_error(self, exception):
        message = (
            "RC MetaStudio could not prepare the analysis settings "
            "for this analysis.\n\n"
            "Details: %s" % exception
        )
        QMessageBox.critical(self, "Could not prepare analysis", message)

    def undo(self):
        if self.workspace.undo(install=self._install_workspace_runtime):
            self._update_project_identity()

    def redo(self):
        if self.workspace.redo(install=self._install_workspace_runtime):
            self._update_project_identity()

    def populate_metrics_menu(self, metric_to_check=None):
        for menu in self.menuMetric.findChildren(QtWidgets.QMenu,
                                                 options=Qt.FindChildOption.FindDirectChildrenOnly):
            menu.deleteLater()
        if self._metric_actions is not None:
            self._metric_actions.deleteLater()
        self.menuMetric.clear()
        data_type = self.model.get_current_data_type(get_str=False)
        single, paired = {
            analysis_catalog.BINARY: (analysis_catalog.BINARY_ONE_ARM_METRICS, analysis_catalog.BINARY_TWO_ARM_METRICS),
            analysis_catalog.CONTINUOUS: (analysis_catalog.CONTINUOUS_ONE_ARM_METRICS, analysis_catalog.CONTINUOUS_TWO_ARM_METRICS),
            analysis_catalog.TIME_TO_EVENT: ((), ("HR",)),
            analysis_catalog.EVENT_RATES: ((), ("IRR",)),
        }.get(data_type, ((), ()))
        self.menuMetric.setEnabled(bool(single or paired))
        if not self.menuMetric.isEnabled():
            self._metric_actions = None
            return
        group = self._metric_actions = QtGui.QActionGroup(self.menuMetric)
        group.setExclusive(True)
        selected = metric_to_check or (paired[0] if paired else None)
        for scope, metrics in (("Two-arm", paired), ("One-arm", single)):
            submenu = required(self.menuMetric.addMenu(f"{scope} effect measures"), "metric submenu")
            submenu.setToolTip(f"Choose a {scope.lower()} effect measure.")
            for metric in metrics:
                label = analysis_identity.metric_label(self.model, metric)
                action = required(group.addAction(label if metric == "Mean" else f"{label} ({metric})"), "metric action")
                action.setToolTip(label)
                action.setData(metric)
                action.setCheckable(True)
                action.setChecked(metric == selected)
                submenu.addAction(action)
        group.triggered.connect(app_error_handler.safe_slot(self._metric_selected, parent=self))

    def _metric_selected(self, action: QAction) -> None:
        metric_name = str(action.data())
        if metric_name == self.model.current_effect:
            return

        def apply_metric():
            self.model.set_current_metric(metric_name)
            self.model.reset_model(refresh_previews=True)

        self._commit_model_operation(apply_metric)
        self.tableView.synchronize_column_widths()

    def analysis(
        self, result: AnalysisResult, *,
        source_sheet: analysis_dataset.Sheet | None = None,
        change_settings=None, manuscript: ManuscriptReport | None = None,
    ) -> results_window.ResultsWindow | None:
        sheet = source_sheet or self.model.current_sheet
        identity = result.identity.splitlines()[0] if result.identity else ""
        plot_key = result.analysis_method + " | " + identity
        saved_plots = {
            title: {key: value for key, value in overrides.items() if not key.startswith("fp_favours_")}
            for title, overrides in sheet.settings.get("plot_overrides", {}).get(plot_key, {}).items()
        } if sheet else {}

        def save_plot_override(title: str, overrides: dict[str, object]) -> None:
            def update(live_sheet: analysis_dataset.Sheet) -> None:
                plots = live_sheet.settings.setdefault("plot_overrides", {}).setdefault(plot_key, {})
                plots[title] = overrides

            if self.workspace.edit_sheet(sheet, update):
                self._update_project_identity()

        try:
            form = results_window.ResultsWindow(
                result, parent=self, change_settings=change_settings, manuscript=manuscript,
                source_sheet_name=sheet.name if sheet else None,
                plot_overrides=saved_plots, save_plot_override=save_plot_override if sheet else None,
            )
        except Exception as e:
            app_error_handler.log_exception(type(e), e, e.__traceback__)
            QMessageBox.critical(
                self,
                "Could not display analysis results",
                "The analysis completed, but RC MetaStudio could not display "
                "the results.\n\nDetails: %s" % e,
            )
            return None
        form.show()
        form.raise_()
        form.activateWindow()
        return form

    def edit_arm_name(self, current_arm_name):
        original_arm_name = copy.copy(current_arm_name)
        arm_name_dialog = edit_name_dialogs.EditArmNameDialog(
            current_arm_name, parent=self
        )
        if arm_name_dialog.exec():
            try:
                existing_arm_names = list(self.model.arm_names)
                if original_arm_name in existing_arm_names:
                    existing_arm_names.remove(original_arm_name)
                new_arm_name = name_validation.validate_unique_name(
                    "group", arm_name_dialog.group_name_le.text(), existing_arm_names
                )
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid arm name", str(exc))
                return

            self._commit_model_operation(lambda: self.model.rename_arm(original_arm_name, new_arm_name))

    def add_covariate(self):
        form = add_new_dialogs.AddCovariateDialog(self, existing_names=self.model.get_covariate_names())
        form.covariate_name_le.setFocus()
        if form.exec():
            try:
                new_covariate_name = dataset_table_model.validate_new_covariate_name(
                    self.model, form.covariate_name_le.text()
                )
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid covariate name", str(exc))
                return

            new_covariate_type = str(form.datatype_cbo_box.currentData())
            self._commit_model_operation(
                lambda: self._add_new_covariate(new_covariate_name, new_covariate_type)
            )

    def _add_new_covariate(self, covariate_name, covariate_type, stable_id=None):
        covariate = self.model.add_covariate(
            covariate_name, covariate_type, stable_id=stable_id
        )
        self.tableView.synchronize_column_widths()
        return covariate


    def open(self, file_path=None, raise_on_error=False):
        """Open a validated structured project and restore its durable working state.

        Opening a project is a document boundary, not an undoable edit. The undo stack is
        reset after a successful load so Ctrl+Z cannot step back into the previously open
        dataset.
        """
        if not self._confirm_discard_or_save():
            return

        if file_path is None:
            file_path, _selected_filter = QFileDialog.getOpenFileName(
                parent=self,
                caption="Open project",
                directory=get_default_open_directory(),
                filter="RC MetaStudio projects (*.rcms)",
            )

            if file_path == "":
                return False

        file_path = _resolve_open_file_path(file_path)

        try:
            self.workspace.open(file_path, install=lambda runtime: self._install_workspace_runtime(
                runtime, recalculate_effect_previews=True, keep_current_cell=False,
            ))
        except Exception as e:
            msg = _format_open_project_error(file_path, e)
            if raise_on_error:
                raise RuntimeError(msg) from e
            QMessageBox.critical(self, "Could not open project", msg)
            return None

        self._update_project_identity("Opened")
        self._update_recent_project_nonfatal(os.fspath(file_path), "opened")
        return True

    def _install_workspace_runtime(
        self, runtime: project_adapter.RuntimeProject, *,
        recalculate_effect_previews: bool = False, keep_current_cell: bool = True,
    ) -> None:
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
                runtime.current_sheet_id,
                recalculate_effect_previews=recalculate_effect_previews,
            )
            if keep_current_cell and current_cell is not None:
                self.tableView.setCurrentIndex(self.model.index(*current_cell))
        except Exception as error:
            if self.model is previous_model:
                raise
            try:
                self._restore_workspace_projection(previous_model, current_cell, selected_cells)
            except Exception as restore_error:
                error.add_note(f"Workspace adapter restoration also failed: {restore_error}")
            raise

    def _restore_workspace_projection(self, model, current_cell, selected_cells):
        """Restore the live Qt adapter after a candidate model fails to install."""
        self._disconnect_model_signals()
        self.model = model
        self.tableView.restore_model(model)
        self._connect_model_signals()
        self._refresh_projected_sheet_controls()
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

    def delete_study(self, study):
        self._commit_model_operation(lambda: self._remove_study(study))

    def change_covariate_type(self, covariate):
        sheet = copy.deepcopy(self.model.current_sheet)
        change_type_form = covariate_type_dialog.CovariateTypeDialog(sheet, covariate, parent=self)
        if change_type_form.exec():
            def apply():
                self.model.current_sheet.covariates = sheet.covariates
                converted_values = {row.id: row.covariate_values for row in sheet.rows}
                for row in self.model.current_sheet.rows:
                    row.covariate_values = converted_values[row.id]
                self.model.reset_model()
            self._commit_model_operation(apply)

    def rename_covariate(self, covariate):
        orig_cov_name = copy.copy(covariate['name'])
        covariate_name_dialog = edit_name_dialogs.EditCovariateNameDialog(
            orig_cov_name, parent=self
        )
        if covariate_name_dialog.exec():
            try:
                existing_covariates = list(self.model.get_covariate_names())
                if orig_cov_name in existing_covariates:
                    existing_covariates.remove(orig_cov_name)
                new_cov = name_validation.validate_unique_name(
                    "covariate",
                    covariate_name_dialog.group_name_le.text(),
                    existing_covariates,
                )
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid covariate name", str(exc))
                return

            self._commit_model_operation(lambda: self.model.rename_covariate(orig_cov_name, new_cov))

    def delete_covariate(self, covariate):
        # Synchronize direct model edits made by an adapter before publishing
        # the next atomic workspace change.
        self.data_dirtied()
        self._commit_model_operation(lambda: self.model.remove_covariate(covariate))

    def _remove_study(self, study):
        self.model.current_sheet.rows.remove(study)
        self.model.reset_model()

    def set_model(
        self,
        data_model,
        current_sheet_id: SheetId | None = None,
        recalculate_effect_previews=True,
    ):
        self._set_model_adapter(
            data_model,
            current_sheet_id=current_sheet_id,
            recalculate_effect_previews=recalculate_effect_previews,
        )
        self.data_dirtied()

    def _set_model_adapter(
        self,
        data_model,
        current_sheet_id: SheetId | None = None,
        recalculate_effect_previews=True,
    ):
        model = dataset_table_model.DatasetTableModel(
            dataset=data_model, add_blank_study=False, current_sheet_id=current_sheet_id,
        )
        model.reset_model(refresh_previews=recalculate_effect_previews)
        self._disconnect_model_signals()
        self.model = model
        self.tableView.setModel(self.model)
        self._connect_model_signals()
        self._refresh_projected_sheet_controls()

    def model_updated(self, *, sheet_id: SheetId | None = None) -> None:
        selected = sheet_id if sheet_id is not None else self.model.current_sheet_id
        if selected is not None:
            self.model.set_current_sheet(selected, refresh_previews=True)
        self._refresh_projected_sheet_controls()

    def _refresh_projected_sheet_controls(self) -> None:
        self.populate_metrics_menu(metric_to_check=self.model.current_effect)
        self._update_confidence_level_label()
        self._refresh_sheet_tabs()
        self._update_workspace_guidance()
        self.refresh_analysis_actions()

    def _update_swap_arms_enabled(self):
        sheet = self.model.current_sheet
        self.action_swap_arms.setEnabled(bool(sheet and sheet.family != "diagnostic" and len(sheet.arms) == 2 and self.model.current_effect not in analysis_catalog.ONE_ARM_METRICS))
        self.effect_direction_menu.setEnabled(self.action_swap_arms.isEnabled())

    def _populate_effect_direction(self) -> None:
        self.effect_direction_menu.clear()
        sheet = self.model.current_sheet
        if sheet is None or len(sheet.arms) != 2:
            return
        first = sheet.arms[0].name
        current = sheet.settings.get("effect_direction", "")
        for value, label in (("", "Not shown"), ("below", f"Values below the null favor {first}"),
                             ("above", f"Values above the null favor {first}")):
            action = required(self.effect_direction_menu.addAction(label), "direction choice")
            action.setCheckable(True)
            action.setChecked(current == value)
            action.triggered.connect(lambda checked=False, direction=value: self._set_effect_direction(sheet, direction))

    def _set_effect_direction(self, sheet: analysis_dataset.Sheet, direction: str) -> None:
        def update(live_sheet: analysis_dataset.Sheet) -> None:
            live_sheet.settings["effect_direction"] = direction
            live_sheet.settings.pop("favours_labels", None)
        if self.workspace.edit_sheet(sheet, update):
            self._update_project_identity()

    def _swap_sheet_arms(self):
        sheet = self.model.current_sheet
        if sheet and sheet.family != "diagnostic" and len(sheet.arms) == 2 and self.model.current_effect not in analysis_catalog.ONE_ARM_METRICS:
            def swap():
                sheet.arms.reverse()
            self._sheet_change(sheet.id, swap)

    def _setup_sheet_strip(self):
        self.sheet_name_edit = None
        self.sheet_tabs: SheetTabBar = SheetTabBar(self)
        required(QtWidgets.QApplication.instance(), "application").installEventFilter(self.sheet_tabs)
        self.sheet_tabs.setObjectName("sheet_tabs")
        self.sheet_tabs.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setTabOrder(self.analysis_button, self.sheet_tabs)
        self.setTabOrder(self.sheet_tabs, self.tableView)
        self.sheet_tabs.setExpanding(False)
        self.sheet_tabs.setMovable(True)
        self.sheet_tabs.setUsesScrollButtons(False)
        self.sheet_tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.sheet_tabs.setAutoHide(False)
        self.sheet_tabs.setDrawBase(False)
        self.sheet_tabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.add_sheet_button = QtWidgets.QToolButton(self)
        self.add_sheet_button.setText("+")
        self.add_sheet_button.setToolTip("Add outcome")
        self.add_sheet_button.setAccessibleName("Add outcome")
        add_font = self.sheet_tabs.font()
        add_font.setPointSizeF(add_font.pointSizeF() + 2)
        self.add_sheet_button.setFont(add_font)
        content = QtWidgets.QWidget(self)
        self.sheet_tab_content = content
        row = QtWidgets.QHBoxLayout(content)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self.sheet_tabs)
        self.sheet_tab_scroll = QtWidgets.QScrollArea(self)
        self.sheet_tab_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        required(self.sheet_tab_scroll.viewport(), "sheet viewport").setBackgroundRole(QtGui.QPalette.ColorRole.Window)
        self.sheet_tab_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sheet_tab_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sheet_tab_scroll.setWidget(content)
        self.sheet_tab_scrollbar = required(self.sheet_tab_scroll.horizontalScrollBar(), "sheet scrollbar")
        self.sheet_tab_scroll.setMinimumWidth(100)
        self.sheet_strip = QtWidgets.QWidget(self)
        strip = QtWidgets.QHBoxLayout(self.sheet_strip)
        strip.setContentsMargins(0, 0, 0, 0)
        strip.setSpacing(0)
        self.sheet_scroll_left = QtWidgets.QToolButton(self)
        self.sheet_scroll_right = QtWidgets.QToolButton(self)
        for button, arrow, delta in ((self.sheet_scroll_left, Qt.ArrowType.LeftArrow, -160), (self.sheet_scroll_right, Qt.ArrowType.RightArrow, 160)):
            button.setArrowType(arrow)
            button.setAccessibleName("Scroll outcomes left" if delta < 0 else "Scroll outcomes right")
            button.clicked.connect(lambda checked=False, delta=delta: self.sheet_tab_scrollbar.setValue(self.sheet_tab_scrollbar.value() + delta))
            button.hide()
            strip.addWidget(button)
        strip.addWidget(self.sheet_tab_scroll, 3)
        strip.addWidget(self.add_sheet_button)
        strip.addStretch(0)
        self.sheet_grid_scrollbar = QtWidgets.QScrollBar(Qt.Orientation.Horizontal, self.sheet_strip)
        strip.addWidget(self.sheet_grid_scrollbar, 2)
        self.tableView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        grid = required(self.tableView.horizontalScrollBar(), "grid scrollbar")
        self.sheet_grid_scrollbar.valueChanged.connect(grid.setValue)
        grid.valueChanged.connect(self.sheet_grid_scrollbar.setValue)
        def sync_grid_scrollbar(*_args):
            self.sheet_grid_scrollbar.setRange(grid.minimum(), grid.maximum())
            self.sheet_grid_scrollbar.setPageStep(grid.pageStep())
            self.sheet_grid_scrollbar.setSingleStep(grid.singleStep())
            self.sheet_grid_scrollbar.setVisible(grid.maximum() > grid.minimum())
        grid.rangeChanged.connect(sync_grid_scrollbar)
        sync_grid_scrollbar()
        self.sheet_strip.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.verticalLayout.addWidget(self.sheet_strip)
        scroll = self.sheet_tab_scrollbar
        self._sheet_strip_timer = QtCore.QTimer(self)
        self._sheet_strip_timer.setSingleShot(True)
        self._sheet_strip_timer.timeout.connect(self._update_sheet_strip)
        self.sheet_tabs.stripPaletteChanged.connect(self._apply_sheet_strip_palette)
        self.sheet_tabs.resized.connect(lambda: QtCore.QTimer.singleShot(0, self._scroll_to_sheet_tab))
        self.sheet_tabs._apply_tab_palette(QtWidgets.QApplication.palette())
        scroll.rangeChanged.connect(self._schedule_sheet_strip_update)
        scroll.valueChanged.connect(self._sheet_scroll_changed)
        self._schedule_sheet_strip_update()

    def _apply_sheet_strip_palette(self, palette: QtGui.QPalette, add_button_style: str) -> None:
        self.sheet_tab_content.setPalette(palette)
        self.add_sheet_button.setStyleSheet(add_button_style)
        self._schedule_sheet_strip_update()

    def _schedule_sheet_strip_update(self, *_args):
        # Range changes arrive inside QScrollArea resize/layout processing.
        # Changing child visibility there can leave a shown arrow at zero width.
        self._sheet_strip_timer.start(0)

    def _update_sheet_strip(self):
        extent = max(self.sheet_tabs.fontMetrics().height() + 10, self.sheet_tabs.sizeHint().height())
        self.add_sheet_button.setFixedSize(extent, extent)
        em = self.sheet_tabs.fontMetrics().height()
        natural_width = sum(min(28 * em, self.sheet_tabs.fontMetrics().horizontalAdvance(self.sheet_tabs.tabText(index)) + 24)
                            for index in range(self.sheet_tabs.count()))
        reserved = extent
        if self.sheet_grid_scrollbar.isVisible():
            reserved += 16 * em
        limit = (28 if natural_width <= self.sheet_strip.width() - reserved else 12) * em
        if getattr(self.sheet_tabs, "_tab_width_limit", None) != limit:
            self.sheet_tabs._tab_width_limit = limit
            self.sheet_tabs._apply_tab_palette(QtWidgets.QApplication.palette())
        self.sheet_tabs.setMinimumSize(self.sheet_tabs.sizeHint())
        self.sheet_tab_content.resize(self.sheet_tab_content.sizeHint())
        self.sheet_tab_scroll.setFixedHeight(self.sheet_tab_content.sizeHint().height())
        self.sheet_tab_scroll.setMaximumWidth(self.sheet_tab_content.sizeHint().width())
        required(self.sheet_strip.layout(), "sheet strip layout").activate()
        overflow = self.sheet_tab_scrollbar.maximum() > 0
        self.sheet_scroll_left.setVisible(overflow)
        self.sheet_scroll_right.setVisible(overflow)
        self._sheet_scroll_changed()
        self._scroll_to_sheet_tab()

    def _sheet_scroll_changed(self, *_args):
        scroll = self.sheet_tab_scrollbar
        self.sheet_scroll_left.setEnabled(scroll.value() > 0)
        self.sheet_scroll_right.setEnabled(scroll.value() < scroll.maximum())

    def _scroll_to_sheet_tab(self):
        index = self.sheet_tabs.currentIndex()
        if index >= 0:
            rect = self.sheet_tabs.tabRect(index)
            self.sheet_tab_scroll.ensureVisible(rect.center().x(), rect.center().y(), rect.width() // 2 + 2, 0)

    def _refresh_sheet_tabs(self):
        self._finish_sheet_rename(cancel=True)
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
        self.sheet_tabs.setMinimumSize(self.sheet_tabs.sizeHint())
        content = self.sheet_tab_content
        required(content.layout(), "sheet tab content layout").activate()
        content.resize(content.sizeHint())
        self.sheet_tab_scroll.setFixedHeight(content.sizeHint().height())
        self.sheet_strip.setVisible(self.sheet_tabs.count() > 0)
        self._schedule_sheet_strip_update()
        QtCore.QTimer.singleShot(0, self._scroll_to_sheet_tab)
        self._update_swap_arms_enabled()

    def _select_sheet_tab(self, index):
        self._finish_sheet_rename()
        if index < 0:
            return
        self._scroll_to_sheet_tab()
        sheet_id = self.sheet_tabs.tabData(index)
        if sheet_id == self.model.current_sheet_id:
            return
        try:
            self.model.set_current_sheet(sheet_id, refresh_previews=True)
        except Exception:
            self._refresh_sheet_tabs()
            raise
        self.workspace.select_sheet(sheet_id)
        self._refresh_projected_sheet_controls()

    def _sheet_change(self, sheet_id, operation):
        if sheet_id != self.model.current_sheet_id:
            self.model.set_current_sheet(sheet_id)
        self.workspace.select_sheet(sheet_id)
        def commit():
            self.model_updated(sheet_id=operation())
        self._commit_model_operation(commit)

    def _finish_sheet_rename(self, cancel=False):
        edit = self.sheet_name_edit
        if edit is None:
            return
        name = edit.text().strip()
        sheet_id = edit.property("sheet_id")
        if not cancel and (not name or any(item.id != sheet_id and item.name == name for item in self.model.dataset.sheets)):
            edit.setToolTip("Choose a unique outcome name.")
            QtWidgets.QToolTip.showText(edit.mapToGlobal(edit.rect().bottomLeft()), edit.toolTip(), edit)
            edit.setFocus()
            return
        self.sheet_name_edit = None
        edit.hide()
        edit.deleteLater()
        if not cancel:
            sheet = self.model.dataset.sheet(sheet_id)
            if name != sheet.name:
                self._sheet_change(sheet.id, lambda: setattr(sheet, "name", name))

    def _add_sheet(self):
        if not self.model.current_sheet:
            return
        self._finish_sheet_rename()
        number = 2
        names = [sheet.name for sheet in self.model.dataset.sheets]
        while f"Outcome {number}" in names:
            number += 1
        wizard = main_wizard.MainWizard(
            parent=self, path="new_dataset", existing_outcome_names=names
        )
        wizard.setField("outcomeName", f"Outcome {number}")
        if not wizard.exec():
            return
        result = wizard.get_results()
        if result["path"] != "new_dataset":
            raise RuntimeError("Add outcome requires a new outcome.")
        sheet = self._sheet_from_dataset_info(result["outcome_info"])
        def add():
            self.model.dataset.sheets.append(sheet)
            return sheet.id
        self._sheet_change(self.model.current_sheet_id, add)

    def _rename_sheet(self, index):
        if index < 0:
            return
        if self.sheet_name_edit is not None:
            self._finish_sheet_rename(cancel=True)
        self.sheet_tabs.setCurrentIndex(index)
        self._scroll_to_sheet_tab()
        sheet = self.model.dataset.sheet(self.sheet_tabs.tabData(index))
        edit = SheetNameEditor(sheet.name, self.sheet_tabs)
        self.sheet_name_edit = edit
        edit.setObjectName("sheet_name_edit")
        edit.setProperty("sheet_id", sheet.id)
        rect = self.sheet_tabs.tabRect(index)
        edit.setGeometry(rect)
        edit.returnPressed.connect(self._finish_sheet_rename)
        edit.editingFinished.connect(self._finish_sheet_rename)
        edit.cancelled.connect(lambda: self._finish_sheet_rename(cancel=True))
        edit.show()
        edit.setFocus()
        edit.selectAll()

    def _sheet_menu(self, position):
        index = self.sheet_tabs.tabAt(position)
        if index < 0:
            return
        menu = QtWidgets.QMenu(self)
        menu.addAction("Rename", lambda: self._rename_sheet(index))
        menu.addAction("Add outcome…", self._add_sheet)
        menu.addSeparator()
        for label, destination in (("Move left", index - 1), ("Move right", index + 1)):
            action = menu.addAction(label, lambda checked=False, destination=destination: self.sheet_tabs.moveTab(index, destination))
            required(action, "sheet move action").setEnabled(0 <= destination < self.sheet_tabs.count())
        menu.addSeparator()
        delete = required(menu.addAction(f'Delete \"{self.sheet_tabs.tabText(index)}\"…', lambda: self._delete_sheet(index)), "delete outcome action")
        delete.setEnabled(self.sheet_tabs.count() > 1)
        menu.exec(self.sheet_tabs.mapToGlobal(position))

    def _delete_sheet(self, index):
        sheet = self.model.dataset.sheet(self.sheet_tabs.tabData(index))
        if len(self.model.dataset.sheets) == 1:
            return
        if sheet.rows and QMessageBox.question(self, "Delete outcome", f'Delete \"{sheet.name}\" and its studies?') != QMessageBox.StandardButton.Yes:
            return
        def delete():
            remaining = [item for item in self.model.dataset.sheets if item.id != sheet.id]
            self.model.dataset.sheets.remove(sheet)
            return remaining[max(0, index - 1)].id
        self._sheet_change(sheet.id, delete)

    def _save_sheet_order(self):
        sheets = self.model.dataset.sheets
        by_id = {sheet.id: sheet for sheet in sheets}
        order = [by_id[self.sheet_tabs.tabData(index)] for index in range(self.sheet_tabs.count())]
        def move():
            sheets[:] = order
        self._commit_model_operation(move)

    def quit(self):
        self.close()

    def prompt_to_save_unsaved_data(self):
        prompt = QMessageBox(self)
        prompt.setIcon(QMessageBox.Icon.Warning)
        prompt.setWindowTitle("Unsaved changes")
        path = self.workspace.path
        project = path.name if path is not None else "Untitled project"
        prompt.setText(f"Save changes to \"{project}\"?")
        prompt.setStandardButtons(
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )
        discard = prompt.button(QMessageBox.StandardButton.Discard)
        assert discard is not None
        discard.setText("Don't save")
        prompt.setDefaultButton(QMessageBox.StandardButton.Save)
        prompt.setEscapeButton(QMessageBox.StandardButton.Cancel)
        return prompt.exec()

    def save_as(self):
        return self.save(save_as=True)

    def save(self, save_as=False, *, destination: str | Path | None = None):
        if destination is None:
            path = self.workspace.path
            sample = path is not None and _is_bundled_sample(path)
            if path is None or sample or save_as:
                if path is None or sample:
                    suggested = os.path.join(get_user_documents_path(), path.name if path else self.model.get_name())
                else:
                    suggested = str(path)
                selected, _ = QFileDialog.getSaveFileName(
                    parent=self,
                    caption="Save project as" if path is not None else "Save project",
                    directory=suggested,
                    filter="RC MetaStudio projects (*.rcms)",
                )
                if not selected:
                    return None
                destination = selected
            else:
                destination = path

        destination = str(destination)
        if not destination.lower().endswith(".rcms"):
            destination += ".rcms"

        if _is_bundled_sample(destination):
            QMessageBox.warning(self, "Choose a different location",
                                "Save your project outside the bundled sample projects folder.")
            return False

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
                "Could not save project",
                "RC MetaStudio could not save %s.\n\nDetails: %s"
                % (destination, e),
            )
            return False

        # The durable document commit is complete. Machine-local recent-project
        # bookkeeping must never turn this successful save into a false failure.
        self._update_project_identity("Saved")
        if durability_error is not None:
            self._report_durability_uncertain_save(destination, durability_error)
        self._update_recent_project_nonfatal(destination, "saved")
        return True

    @staticmethod
    def _sheet_from_dataset_info(dataset_info: main_wizard.DatasetInfo) -> analysis_dataset.Sheet:
        import uuid
        from rc_metastudio.project.model import Sheet, Arm
        family = required(dataset_info["data_type"], "dataset type")
        name = required(dataset_info["name"], "outcome name")
        data_type = analysis_catalog.STR_TO_TYPE_DICT[family]
        subtype = dataset_info.get("sub_type")
        groups = dataset_info.get("groups") or analysis_catalog.default_arm_names(data_type, subtype)
        return Sheet(
            SheetId(uuid.uuid4().hex), name, data_type, subtype, family,
            [Arm(ArmId(uuid.uuid4().hex), group) for group in groups],
            settings={"metric": dataset_info.get("effect")},
        )

    def _start_unnamed_project(self, dataset: analysis_dataset.Dataset, *, imported_rows: bool = False) -> None:
        selected = dataset.sheets[0].id if dataset.sheets else None
        candidate = project_adapter.RuntimeProject(dataset, selected)
        self.workspace.start_new_document(candidate, undo_previous=imported_rows,
            install=lambda runtime: self._install_workspace_runtime(
                runtime, recalculate_effect_previews=not imported_rows, keep_current_cell=False,
            ),
        )
        self._update_project_identity()

    def _handle_wizard_results(self, wizard_data: main_wizard.WizardResult):
        if wizard_data["path"] == "open":
            self.open(file_path=wizard_data["selected_dataset"])
        elif wizard_data["path"] == "rm5_import":
            self._start_unnamed_project(wizard_data["rm5_dataset"])
        elif wizard_data["path"] == "new_dataset":
            sheet = self._sheet_from_dataset_info(wizard_data["outcome_info"])
            self._start_unnamed_project(analysis_dataset.Dataset(sheets=[sheet]))

        else:
            self._install_csv_import(wizard_data["outcome_info"], wizard_data["csv_data"])

    def _install_csv_import(self, dataset_info: main_wizard.DatasetInfo, csv_data: csv_import.CsvImportResult):
        sheet = self._sheet_from_dataset_info(dataset_info)
        dataset = analysis_dataset.Dataset(sheets=[sheet])
        for name, data_type in zip(csv_data.covariate_names, csv_data.covariate_types, strict=True):
            workspace_editing.add_covariate(sheet, name, data_type)
        progress = ImportProgressDialog(self, len(csv_data.rows))
        try:
            progress.progress_bar.setValue(0)
            progress.show()
            QApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
            def show_progress(completed: int) -> None:
                progress.progress_bar.setValue(completed)
                progress.progress_bar.repaint()
            warnings = workspace_editing.WorkspaceEditingService().load_import_rows(
                dataset, sheet, csv_data.rows, show_progress,
            )
        finally:
            progress_dialog.dispose(progress)
        self._start_unnamed_project(dataset, imported_rows=True)
        if warnings:
            self.statusbar.showMessage(f"Skipped {len(warnings)} invalid cells. {warnings[0]}", 8000)
