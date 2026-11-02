# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt adapter for persisted workspace column widths."""

from PyQt6.QtCore import QObject, Qt
from PyQt6.QtWidgets import QTableView

from rc_metastudio.workspace_column_identity import (
    WORKSPACE_COLUMN_IDENTITY_ROLE,
    WorkspaceColumnIdentity,
    WorkspaceColumnWidthState,
)


class WorkspaceColumnWidthController(QObject):
    """Fit automatic columns to contents and preserve manual section widths."""

    def __init__(self, table, saved_widths=None):
        super().__init__(table)
        self.table = table
        self._widths = (
            saved_widths.copy()
            if isinstance(saved_widths, WorkspaceColumnWidthState)
            else WorkspaceColumnWidthState(saved_widths)
        )
        # Widths loaded from settings represent an explicit user choice.
        self._user_widths = set(self._widths._widths) if saved_widths else set()
        self._applying = False
        table.horizontalHeader().sectionResized.connect(self._section_resized)

    def restore(self, widths):
        self._widths = (
            widths.copy()
            if isinstance(widths, WorkspaceColumnWidthState)
            else WorkspaceColumnWidthState(widths)
        )
        self._user_widths = set(self._widths._widths) if widths else set()
        self.synchronize_schema()

    def begin_schema_change(self):
        self._applying = True

    def end_schema_change(self):
        self._applying = False
        self.synchronize_schema()

    def state(self):
        self._capture_visible_widths()
        return WorkspaceColumnWidthState(
            {
                key: self._widths[key]
                for key in self._user_widths
                if key in self._widths._widths
            }
        )

    def synchronize_schema(self):
        model = QTableView.model(self.table)
        if model is None:
            return
        keys = self._schema_keys()
        self._applying = True
        try:
            for column, key in enumerate(keys):
                if self.table.isColumnHidden(column):
                    continue
                width = self._widths.get(key)
                if width is None or key not in self._user_widths:
                    self.table.resizeColumnToContents(column)
                    width = self.table.columnWidth(column)
                    if key.kind == "fixed" and key.components == ("study-name",):
                        width = max(width, self.table.fontMetrics().horizontalAdvance("M" * 22))
                    elif key.kind == "fixed" and key.components == ("year",):
                        width = max(width, self.table.fontMetrics().horizontalAdvance("2026") + 12)
                    elif key.kind == "covariate":
                        width = min(width, self.table.fontMetrics().horizontalAdvance("M" * 20))
                    self.table.setColumnWidth(column, width)
                    self._widths[key] = width
                else:
                    self.table.setColumnWidth(column, width)
        finally:
            self._applying = False

    def auto_fit_all(self):
        self._applying = True
        try:
            QTableView.resizeColumnsToContents(self.table)
        finally:
            self._applying = False
        self._capture_visible_widths(mark_user=True)

    def _capture_visible_widths(self, mark_user=False):
        for column, key in enumerate(self._schema_keys()):
            if self.table.isColumnHidden(column):
                continue
            self._widths[key] = self.table.columnWidth(column)
            if mark_user:
                self._user_widths.add(key)

    def _section_resized(self, logical_index, _old_size, new_size):
        if self._applying or new_size <= 0:
            return
        keys = self._schema_keys()
        if 0 <= logical_index < len(keys):
            self._widths[keys[logical_index]] = int(new_size)
            self._user_widths.add(keys[logical_index])

    def _schema_keys(self):
        model = QTableView.model(self.table)
        if model is None:
            return []
        identities = []
        for column in range(model.columnCount()):
            value = model.headerData(
                column, Qt.Orientation.Horizontal, WORKSPACE_COLUMN_IDENTITY_ROLE
            )
            identities.append(
                WorkspaceColumnIdentity.coerce(
                    value, fallback_section=column, model=model
                )
            )
        return identities
