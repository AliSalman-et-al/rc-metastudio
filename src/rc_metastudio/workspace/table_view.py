# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Custom QTableView with copy, paste, undo, and redo support."""

import csv
import io
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtCore import (
    QEvent,
    QObject,
    QSignalBlocker,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QAction, QKeyEvent

from PyQt6.QtWidgets import (
    QApplication,
    QItemDelegate,
    QLineEdit,
    QMenu,
    QMessageBox,
    QTableView,
    QWidget,
)

from rc_metastudio.calculators import binary_dialog as binary_data_dialog
from rc_metastudio.calculators import continuous_dialog as continuous_data_dialog
from rc_metastudio.calculators import diagnostic_dialog as diagnostic_data_dialog
from rc_metastudio import app_error_handler
from rc_metastudio.app_error_handler import connect_action
from rc_metastudio import qt_layout
from rc_metastudio import qt_text
from rc_metastudio import row_padding
from rc_metastudio.analysis.catalog import CONTINUOUS
from rc_metastudio.domain_ids import SheetId
from rc_metastudio.qt_object_guard import required
from rc_metastudio.workspace.column_widths import WorkspaceColumnWidthController
from rc_metastudio.workspace.column_identity import WorkspaceColumnIdentity

if TYPE_CHECKING:
    from rc_metastudio.workspace.table_model import DatasetTableModel


class DatasetTableView(QtWidgets.QTableView):
    studyDeletionRequested = pyqtSignal(object)
    armRenameRequested = pyqtSignal(str)
    covariateRenameRequested = pyqtSignal(object)
    covariateDeletionRequested = pyqtSignal(object)
    covariateConversionRequested = pyqtSignal(object)
    undoRequested = pyqtSignal()
    redoRequested = pyqtSignal()
    pasteNotice = pyqtSignal(str)
    clipboardError = pyqtSignal(str)

    def paintEvent(self, event: QtGui.QPaintEvent | None) -> None:
        super().paintEvent(event)
        model = super().model()
        if model is None or self.model().current_outcome_name is None or self.model().get_studies():
            return
        viewport = required(self.viewport(), 'study grid viewport')
        rect = viewport.rect().adjusted(24, self.rowHeight(0) * 3, -24, -24)
        if rect.height() < self.fontMetrics().height() * 3:
            return
        painter = QtGui.QPainter(viewport)
        painter.setPen(self.palette().color(QtGui.QPalette.ColorRole.PlaceholderText))
        painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                         'Type a study name in row 1, paste rows from a spreadsheet, or use Import data.')
        painter.end()

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked | QtWidgets.QAbstractItemView.EditTrigger.EditKeyPressed | QtWidgets.QAbstractItemView.EditTrigger.AnyKeyPressed)
        self.setAccessibleName("Study data")
        self.setAccessibleDescription("Study rows and input columns. Effect estimate and confidence interval columns are highlighted. Press Enter to edit a cell, F4 to open the study calculator or Ctrl+Tab to leave the grid.")

        self.study_calculator_action = QAction("Study calculator…", self)
        self.study_calculator_action.setShortcut("F4")
        self.study_calculator_action.setEnabled(False)
        connect_action(self.study_calculator_action, lambda: self.row_header_clicked(self.currentIndex().row()))
        self.edit_transaction: Callable[[Callable[[], None]], None] | None = None

        header = required(self.horizontalHeader(), "workspace column header")
        header_font = header.font()
        header_font.setBold(True)
        header.setFont(header_font)

        self.vert_header = required(self.verticalHeader(), "workspace row header")

        self.vert_header.sectionClicked.connect(
            app_error_handler.safe_slot(self.row_header_clicked, parent=self)
        )

        self.reverse_column_sorts: dict[tuple[SheetId, WorkspaceColumnIdentity], bool] = {}
        self.setAlternatingRowColors(True)
        palette = self.palette()
        for group in (QtGui.QPalette.ColorGroup.Active, QtGui.QPalette.ColorGroup.Inactive):
            palette.setColor(group, QtGui.QPalette.ColorRole.Highlight, QtGui.QColor("#245a81"))
            palette.setColor(group, QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor("#ffffff"))
        self.setPalette(palette)

        headers = required(self.horizontalHeader(), "workspace column header")
        headers.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        headers.customContextMenuRequested.connect(
            app_error_handler.safe_slot(self.header_context_menu, parent=self)
        )
        qt_layout.configure_spreadsheet_table_view(self)
        self._column_widths = WorkspaceColumnWidthController(self)
        self._column_connections: list[QtCore.QMetaObject.Connection] = []

    def model(self) -> "DatasetTableModel":
        """Return the concrete model required by the maintained workspace view."""
        from rc_metastudio.workspace.table_model import DatasetTableModel

        model = super().model()
        if model is None:
            raise RuntimeError("DatasetTableView requires a model")
        return cast(DatasetTableModel, model)

    def setModel(self, model):
        self._disconnect_column_model()
        self._column_widths.begin_schema_change()
        try:
            super(DatasetTableView, self).setModel(model)
        finally:
            self._column_widths.end_schema_change()
        self._connect_column_model(model)
        self.refresh_study_calculator()
        self.synchronize_column_widths()

    def restore_model(self, model):
        """Restore a previously bound model without repeating failed layout work."""
        self._disconnect_column_model()
        QTableView.setModel(self, model)
        self._connect_column_model(model)
        self.refresh_study_calculator()

    def currentChanged(self, current, previous):
        super().currentChanged(current, previous)
        self.refresh_study_calculator()

    def refresh_study_calculator(self):
        self.study_calculator_action.setEnabled(self._can_open_study_calculator(self.currentIndex().row()))

    def _can_open_study_calculator(self, row: int) -> bool:
        from rc_metastudio import r_runtime
        model = QTableView.model(self)
        return (
            r_runtime.is_ready() and model is not None
            and 0 <= row < len(self.model().get_studies(False))
            and bool(self.model()._study_for_row(row).label.strip())
        )

    def _connect_column_model(self, model):
        if model is None:
            return
        self._column_connections.extend((
            model.modelAboutToBeReset.connect(self._begin_column_schema_change),
            model.modelReset.connect(self._end_column_schema_change),
            model.columnsAboutToBeInserted.connect(self._begin_column_schema_change),
            model.columnsInserted.connect(self._end_column_schema_change),
            model.columnsAboutToBeRemoved.connect(self._begin_column_schema_change),
            model.columnsRemoved.connect(self._end_column_schema_change),
            model.headerDataChanged.connect(self.synchronize_column_widths),
        ))

    def _disconnect_column_model(self):
        for connection in self._column_connections:
            try:
                QObject.disconnect(connection)
            except (TypeError, RuntimeError):
                pass
        self._column_connections.clear()

    def _begin_column_schema_change(self, *_args):
        self._column_widths.begin_schema_change()

    def _end_column_schema_change(self, *_args):
        self._apply_column_visibility()
        self._column_widths.end_schema_change()

    def synchronize_column_widths(self, *_args):
        self._apply_column_visibility()
        self._column_widths.synchronize_schema()

    def _apply_column_visibility(self):
        model = self.model()
        hidden = model.columns.hidden_sections()
        for column in range(model.columnCount()):
            self.setColumnHidden(column, column in hidden)

    def auto_fit_columns(self):
        self._column_widths.auto_fit_all()

    def restore_column_widths(self, widths):
        self._column_widths.restore(widths)

    def column_width_state(self):
        return self._column_widths.state()

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent | None) -> None:
        if event is None:
            return
        context_menu = QMenu(self)
        clicked = self.indexAt(event.pos())
        if event.reason() == QtGui.QContextMenuEvent.Reason.Keyboard:
            clicked = self.currentIndex()
        study_index = clicked.row()

        sheet = self.model().current_sheet
        if sheet is None or not 0 <= study_index < len(sheet.rows):
            return

        study = self.model()._study_for_row(study_index)
        delete_action = QAction('Delete study “%s”…' % study.label, self)

        def delete_study():
            answer = QMessageBox.question(
                self,
                "Delete study",
                "Delete study %s?" % study.label,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.studyDeletionRequested.emit(study)

        connect_action(delete_action, delete_study)

        action = QAction("Copy", self)
        connect_action(action, self.copy)
        context_menu.addAction(action)

        action = QAction("Paste", self)
        connect_action(action, self.paste)
        context_menu.addAction(action)

        context_menu.addSeparator()
        calculator_action = required(context_menu.addAction(self.study_calculator_action.text()), "study calculator action")
        calculator_action.setShortcut(self.study_calculator_action.shortcut())
        calculator_action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        calculator_action.setShortcutVisibleInContextMenu(True)
        calculator_action.setEnabled(self._can_open_study_calculator(study_index))
        connect_action(calculator_action, lambda: self.row_header_clicked(study_index))
        context_menu.addAction(delete_action)
        app_error_handler.popup_context_menu(
            context_menu, event.globalPos(), parent=self, event=event
        )

    def header_context_menu(self, pos):
        """Here is where the context menus for column header
        right-clicks are built.
        """
        column_clicked = self.columnAt(pos.x())
        model = self.model()
        raw = model.columns.raw_column(column_clicked)
        cov = model.get_covariate_for_column(column_clicked)

        context_menu = QMenu(self)

        if column_clicked == model.INCLUDE_STUDY:
            action = QAction("Include all", self)
            connect_action(action, lambda: self.model().set_all_studies_included(True))
            if self.model().all_studies_are_included():
                action.setEnabled(False)
            context_menu.addAction(action)

            action = QAction("Exclude all", self)
            connect_action(action, lambda: self.model().set_all_studies_included(False))
            if self.model().all_studies_are_excluded():
                action.setEnabled(False)
            context_menu.addAction(action)

            app_error_handler.popup_context_menu(
                context_menu, self.mapToGlobal(pos), parent=self
            )
        elif column_clicked in (model.NAME, model.YEAR):
            col_name = model.columns.label(column_clicked, (), None).lower()
            action_sort = QAction("Sort studies by %s" % col_name, self)

            connect_action(action_sort, lambda: self.sort_by_col(column_clicked))
            context_menu.addAction(action_sort)

        elif raw is not None or column_clicked in model.columns.effect_sections:
            arm_name = raw.arm_name(model.arm_names) if raw is not None else None
            if arm_name is not None:
                action_rename = QAction("Rename arm %s…" % arm_name, self)
                connect_action(
                    action_rename, lambda: self.armRenameRequested.emit(arm_name),
                )
                context_menu.addAction(action_rename)
            col_name = qt_text.to_native_text(
                model.headerData(column_clicked, Qt.Orientation.Horizontal)
            )
            action_sort = QAction("Sort studies by %s" % col_name, self)
            connect_action(action_sort, lambda: self.sort_by_col(column_clicked))
            context_menu.addAction(action_sort)
        elif cov is not None:
            action_sort = QAction("Sort studies by %s" % cov["name"], self)
            connect_action(action_sort, lambda: self.sort_by_col(column_clicked))
            context_menu.addAction(action_sort)

            action_ren = QAction("Rename covariate %s…" % cov["name"], self)
            connect_action(action_ren, lambda: self.covariateRenameRequested.emit(cov))
            context_menu.addAction(action_ren)

            action_del = QAction("Delete covariate %s…" % cov["name"], self)
            connect_action(action_del, lambda: self.covariateDeletionRequested.emit(cov))
            context_menu.addAction(action_del)

            convert_to_str = "numeric"
            if cov["data_type"] == CONTINUOUS:
                convert_to_str = "category"

            action_change = QAction(
                "Create %s copy of %s…" % (convert_to_str, cov["name"]), self
            )
            connect_action(
                action_change, lambda: self.covariateConversionRequested.emit(cov)
            )
            context_menu.addAction(action_change)

        app_error_handler.popup_context_menu(
            context_menu, self.mapToGlobal(pos), parent=self
        )

    def keyPressEvent(
        self, event: QKeyEvent | None
    ) -> None:
        if event is None:
            return
        if event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
            if event.key() in (QtCore.Qt.Key.Key_Tab, QtCore.Qt.Key.Key_Backtab):
                QWidget.focusNextPrevChild(self, event.key() != QtCore.Qt.Key.Key_Backtab and not event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier)
                event.accept()
            elif event.key() == QtCore.Qt.Key.Key_Z:
                self.undoRequested.emit()
            elif event.key() == QtCore.Qt.Key.Key_Y:
                self.redoRequested.emit()
            elif event.key() == QtCore.Qt.Key.Key_D:
                self.fill_down()
            elif event.key() == QtCore.Qt.Key.Key_C:
                self.copy()
            elif event.key() == QtCore.Qt.Key.Key_V:
                self.paste()
            elif event.key() == QtCore.Qt.Key.Key_A:
                self.selectAll()
                event.accept()
            else:
                super().keyPressEvent(event)
        elif self._is_return_key(event):
            self._move_current_index_vertically(
                -1
                if event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier
                else 1
            )
            event.accept()
        elif self._is_clear_key(event):
            if self.clear_selected_cells():
                event.accept()
            else:
                QTableView.keyPressEvent(self, event)
        else:
            QTableView.keyPressEvent(self, event)

    def _is_return_key(self, event):
        return event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter)

    def _is_clear_key(self, event):
        return event.key() in (QtCore.Qt.Key.Key_Delete, QtCore.Qt.Key.Key_Backspace)

    def clear_selected_cells(self):
        model = self.model()
        selection_model = self.selectionModel()
        if model is None or selection_model is None:
            return False

        indexes = selection_model.selectedIndexes()
        if not indexes:
            indexes = [self.currentIndex()]

        editable_indexes = []
        seen = set()
        for index in indexes:
            if index is None or not index.isValid():
                continue
            key = (index.row(), index.column())
            if key in seen:
                continue
            seen.add(key)
            if model.flags(index) & Qt.ItemFlag.ItemIsEditable:
                editable_indexes.append(index)

        if not editable_indexes:
            return False

        def clear():
            for index in editable_indexes:
                model.setData(index, "")
            model.reset_model()
        required(self.edit_transaction, "workspace edit transaction")(clear)
        return True

    def fill_down(self):
        selection = self.selectionModel()
        if selection is None:
            return
        indexes = selection.selectedIndexes()
        if not indexes:
            return
        columns = sorted({index.column() for index in indexes})
        def fill():
            model = self.model()
            for column in columns:
                rows = sorted(index.row() for index in indexes if index.column() == column)
                value = model.data(model.index(rows[0], column), Qt.ItemDataRole.EditRole)
                for row in rows[1:]:
                    index = model.index(row, column)
                    if model.flags(index) & Qt.ItemFlag.ItemIsEditable:
                        model.setData(index, value)
        required(self.edit_transaction, "workspace edit transaction")(fill)

    def _move_current_index_vertically(self, row_delta):
        self._move_index_vertically_from(self.currentIndex(), row_delta)

    def _move_index_vertically_from(self, index, row_delta):
        model = self.model()
        if index is None or not index.isValid() or model is None:
            return

        target_row = min(max(index.row() + row_delta, 0), model.rowCount() - 1)
        target = model.index(target_row, index.column())
        if target.isValid():
            self.setCurrentIndex(target)
            self.scrollTo(target)

    def copy(self):
        selected_indexes = required(
            self.selectionModel(), "workspace selection model"
        ).selectedIndexes()
        if not selected_indexes:
            return
        upper_left_index = self._upper_left(selected_indexes)
        lower_right_index = self._lower_right(selected_indexes)
        self.copy_contents_in_range(
            upper_left_index, lower_right_index, to_clipboard=True,
            selected_cells={(index.row(), index.column()) for index in selected_indexes},
        )

    def paste(self):
        selected_indexes = required(
            self.selectionModel(), "workspace selection model"
        ).selectedIndexes()
        if not selected_indexes:
            return
        upper_left_index = self._upper_left(selected_indexes)
        self.paste_from_clipboard(upper_left_index)

    def row_header_clicked(self, row):
        if not self._can_open_study_calculator(row):
            return

        signal_blocker = QSignalBlocker(self.vert_header)

        try:
            form = None
            study_index = row
            analysis_unit = self.model().get_current_analysis_unit_for_study(study_index).copy_for_edit()
            arm_names = self.model().arm_names
            current_effect = self.model().current_effect
            arm_key = self.model().get_current_arm_key()
            data_type = self.model().get_current_data_type()
            study_name = self.model()._study_for_row(row).label

            if data_type == "binary":
                form = binary_data_dialog.BinaryDataDialog(
                    analysis_unit,
                    arm_names,
                    arm_key,
                    current_effect,
                    confidence_level=self.model().get_confidence_level(),
                    parent=self,
                    study_name=study_name,
                )
            elif data_type in ("time_to_event", "event_rates"):
                from rc_metastudio.calculators.ratio_dialog import RatioDataDialog
                form = RatioDataDialog(analysis_unit, arm_names, current_effect, parent=self, study_name=study_name)
            elif data_type == "continuous":
                form = continuous_data_dialog.ContinuousDataDialog(
                    analysis_unit,
                    arm_names,
                    arm_key,
                    current_effect,
                    confidence_level=self.model().get_confidence_level(),
                    parent=self,
                    study_name=study_name,
                )
            else:
                form = diagnostic_data_dialog.DiagnosticDataDialog(
                    analysis_unit,
                    arm_names,
                    arm_key,
                    confidence_level=self.model().get_confidence_level(),
                    parent=self,
                    study_name=study_name,
                )
            if form.exec():
                model = self.model()

                def apply_calculator_result():
                    model.set_current_analysis_unit_for_study(study_index, form.analysis_unit)
                    model.update_all_effect_previews()
                    model.reset_model()
                    self.synchronize_column_widths()

                required(self.edit_transaction, "workspace edit transaction")(apply_calculator_result)
        finally:
            del signal_blocker

    def get_covariate_columns(self):
        model = self.model()
        return list(range(model.columns.first_covariate, model.columnCount()))

    def sort_by_col(self, column: int) -> None:
        model = self.model()
        sheet_id = model.current_sheet_id
        if sheet_id is not None:
            key = (sheet_id, model.workspace_column_identity(column))
            reverse = self.reverse_column_sorts.get(key, False)
            model.sort_studies(column, reverse)
            self.reverse_column_sorts[key] = not reverse

    def paste_from_clipboard(self, upper_left_index):
        """Pastes the data in the clipboard starting at the currently selected cell."""
        origin = (upper_left_index.row(), upper_left_index.column())
        clipboard = required(QApplication.clipboard(), "application clipboard")
        clipboard_text = clipboard.text()

        # Some spreadsheet applications use carriage returns between copied
        # rows; normalize them before parsing.
        clipboard_text = clipboard_text.replace("\r\n", "\n").replace("\r", "\n")

        new_content = self._str_to_matrix(clipboard_text)

        # Drop a trailing blank row commonly included in copied spreadsheet data.
        if new_content and new_content[-1] == [""]:
            new_content = new_content[:-1]
        if not any(new_content):
            return False

        if not self.paste_contents(upper_left_index, new_content):
            return False
        active_model = self.model()
        self.setCurrentIndex(active_model.index(*origin))
        return True

    def _preflight_paste(self, upper_left_index, content):
        model = self.model()
        if model is None or upper_left_index is None or not upper_left_index.isValid():
            return False, "Select a valid workspace cell before pasting."
        if len(content[0]) > len(self._paste_columns(upper_left_index.column())):
            return False, "Clipboard data extends beyond the workspace columns."
        return True, None

    def copy_contents_in_range(self, upper_left_index, lower_right_index, to_clipboard, selected_cells=None):
        """Copy the (textual) content of the cells in provided cell_range -- the copied contents will be
        cast to python Unicode strings and returned. If the to_clipboard flag is true, the contents will
        also be copied to the system clipboard
        """
        text_matrix = []

        for row in range(upper_left_index.row(), lower_right_index.row() + 1):
            current_row = []
            for col in range(upper_left_index.column(), lower_right_index.column() + 1):
                if to_clipboard and self.isColumnHidden(col):
                    continue
                if selected_cells is not None and (row, col) not in selected_cells:
                    current_row.append("")
                    continue
                current_index = self.model().createIndex(row, col)
                cur_data = self.model().data(current_index, Qt.ItemDataRole.EditRole)
                if cur_data is not None:
                    cur_str = qt_text.to_native_text(cur_data)
                    current_row.append(cur_str)
                else:
                    current_row.append("")
            text_matrix.append(current_row)

        copied_str = self._matrix_to_str(text_matrix)

        if to_clipboard:
            clipboard = required(QApplication.clipboard(), "application clipboard")
            clipboard.setText(copied_str)
        return copied_str

    def paste_contents(self, upper_left_index, source_content):
        """Validate and publish one clipboard edit through the workspace."""
        source_content = row_padding.normalize_rows(source_content)
        if not source_content:
            return True

        valid, failure = self._preflight_paste(upper_left_index, source_content)
        if not valid:
            self.clipboardError.emit(failure)
            return False
        origin_row, origin_col = upper_left_index.row(), upper_left_index.column()
        try:
            skipped = self.model().paste_cells(origin_row, self._paste_columns(origin_col), source_content)
        except (IndexError, TypeError, ValueError) as exc:
            self.clipboardError.emit(str(exc))
            return False
        if skipped:
            noun = "cell" if skipped == 1 else "cells"
            self.pasteNotice.emit(f"{skipped} {noun} skipped: not a number")
        return True

    def _paste_columns(self, origin):
        return [column for column in range(origin, self.model().columnCount())
                if not self.isColumnHidden(column)]


    def _str_to_matrix(self, text):
        """Transforms raw text (e.g., from the clipboard) to a structured matrix"""
        return list(csv.reader(io.StringIO(text, newline=""), delimiter="\t"))

    def _matrix_to_str(self, matrix):
        """Takes a matrix of data (i.e., a nested list) and converts to a string representation"""
        stream = io.StringIO(newline="")
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerows(matrix)
        return stream.getvalue().removesuffix("\n")

    def _upper_left(self, indexes):
        """Returns the upper most index object in the indexes list."""
        if len(indexes) > 0:
            return self.model().index(min(index.row() for index in indexes), min(index.column() for index in indexes))
        return None

    def _lower_right(self, indexes):
        if len(indexes) > 0:
            return self.model().index(max(index.row() for index in indexes), max(index.column() for index in indexes))
        return None


class StudyDelegate(QItemDelegate):
    def __init__(self, table: DatasetTableView) -> None:
        super().__init__(table)
        self.table = table

    @staticmethod
    def _check_rect(option):
        style = required(option.widget.style() if option.widget else QApplication.style(), "table checkbox style")
        width = style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_IndicatorWidth, option, option.widget)
        height = style.pixelMetric(QtWidgets.QStyle.PixelMetric.PM_IndicatorHeight, option, option.widget)
        rect = QtCore.QRect(0, 0, width, height)
        rect.moveCenter(option.rect.center())
        return rect

    def paint(self, painter, option, index):
        state = index.data(Qt.ItemDataRole.CheckStateRole)
        if state is None:
            super().paint(painter, option, index)
            return
        self.drawBackground(painter, option, index)
        rect = self._check_rect(option)
        self.drawCheck(painter, option, rect, state)
        self.drawFocus(painter, option, rect.adjusted(-3, -3, 3, 3))

    def editorEvent(self, event, model, option, index):
        state = index.data(Qt.ItemDataRole.CheckStateRole)
        if state is None:
            return super().editorEvent(event, model, option, index)
        if not model.flags(index) & Qt.ItemFlag.ItemIsEnabled:
            return False
        if isinstance(event, QtGui.QMouseEvent):
            if event.button() != Qt.MouseButton.LeftButton or not self._check_rect(option).contains(event.position().toPoint()):
                return False
            if event.type() != QEvent.Type.MouseButtonRelease:
                return True
        elif isinstance(event, QKeyEvent):
            if event.key() not in (Qt.Key.Key_Space, Qt.Key.Key_Select):
                return False
        else:
            return False
        checked = Qt.CheckState.Unchecked if state == Qt.CheckState.Checked else Qt.CheckState.Checked
        return model.setData(index, checked, Qt.ItemDataRole.CheckStateRole)

    def eventFilter(
        self, editor: QObject | None, event: QEvent | None
    ) -> bool:
        if (
            isinstance(editor, QWidget)
            and isinstance(event, QKeyEvent)
            and event.type() == QtCore.QEvent.Type.KeyPress
            and event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter)
            and not event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier
        ):
            direction = (
                -1
                if event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier
                else 1
            )
            edited_index = self.table.currentIndex()
            self.commitData.emit(editor)
            self.closeEditor.emit(
                editor, QtWidgets.QAbstractItemDelegate.EndEditHint.NoHint
            )
            QtCore.QTimer.singleShot(
                0,
                lambda: self.table._move_index_vertically_from(edited_index, direction),
            )
            event.accept()
            return True
        return super(StudyDelegate, self).eventFilter(editor, event)

    def createEditor(self, parent, *args):
        le = QLineEdit(parent)
        return le

    def setEditorData(self, editor, index):
        text = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setText(qt_text.to_native_text(text))
