# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt adapter for persisted workspace column widths."""

from PyQt6.QtCore import QEvent, QObject, QTimer, Qt
from PyQt6.QtWidgets import QTableView

from rc_metastudio.workspace_column_identity import (
    WORKSPACE_COLUMN_IDENTITY_ROLE,
    WorkspaceColumnIdentity,
    WorkspaceColumnWidthState,
)


class WorkspaceColumnWidthController(QObject):
    """Auto-fit a schema once, then preserve the user's section widths."""

    def __init__(self, table, saved_widths=None):
        super().__init__(table)
        self.table = table
        self._widths = (
            saved_widths.copy()
            if isinstance(saved_widths, WorkspaceColumnWidthState)
            else WorkspaceColumnWidthState(saved_widths)
        )
        # Widths loaded from settings represent an explicit user choice. New
        # columns start as automatic widths and can absorb spare viewport
        # space without changing the user's choices.
        self._user_widths = set(self._widths._widths) if saved_widths else set()
        self._applying = False
        self._resize_pending = False
        table.horizontalHeader().sectionResized.connect(self._section_resized)
        table.installEventFilter(self)

    def eventFilter(
        self, a0: QObject | None, a1: QEvent | None
    ) -> bool:
        if (
            a0 is self.table
            and a1 is not None
            and a1.type() == QEvent.Type.Resize
        ):
            self._schedule_fit()
        return super().eventFilter(a0, a1)

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
                width = self._widths.get(key)
                if width is None:
                    self.table.resizeColumnToContents(column)
                    width = self.table.columnWidth(column)
                    self._widths[key] = width
                else:
                    self.table.setColumnWidth(column, width)
        finally:
            self._applying = False
        self.fit_available_width()

    def auto_fit_all(self):
        self._applying = True
        try:
            QTableView.resizeColumnsToContents(self.table)
        finally:
            self._applying = False
        self._capture_visible_widths(mark_user=True)
        self.fit_available_width()

    def _capture_visible_widths(self, mark_user=False):
        for column, key in enumerate(self._schema_keys()):
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
        self._schedule_fit()

    def _schedule_fit(self):
        if self._resize_pending:
            return
        self._resize_pending = True
        QTimer.singleShot(0, self._fit_after_resize)

    def _fit_after_resize(self):
        self._resize_pending = False
        self.fit_available_width()

    def fit_available_width(self):
        """Use spare viewport width without overriding user-owned sections."""
        if self._applying:
            return
        keys = self._schema_keys()
        if not keys:
            return
        available = self.table.viewport().width()
        if available <= 0:
            return
        widths = [self._widths.get(key, self.table.columnWidth(i)) for i, key in enumerate(keys)]
        extra = available - sum(widths)
        automatic = [i for i, key in enumerate(keys) if key not in self._user_widths]
        if extra <= 0 or not automatic:
            return

        self._applying = True
        try:
            share, remainder = divmod(extra, len(automatic))
            for position, column in enumerate(automatic):
                width = widths[column] + share + (1 if position < remainder else 0)
                self.table.setColumnWidth(column, width)
        finally:
            self._applying = False

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
