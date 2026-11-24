# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Dialog-local calculator undo and redo."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias

from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QWidget

from rc_metastudio.app_error_handler import connect_action


EditState: TypeAlias = tuple[object, ...]


StateRestorer: TypeAlias = Callable[..., None]


@dataclass(frozen=True, slots=True)
class _FieldEdit:
    restore_state: StateRestorer
    old_state: EditState
    new_state: EditState


class TransientEditHistory:
    """Small dialog-local history; it is discarded when the dialog closes."""

    def __init__(self) -> None:
        self._edits: list[_FieldEdit] = []
        self._applied_edit_count = 0

    def bind_shortcuts(self, owner: QWidget) -> None:
        for key, command in (
            (QKeySequence.StandardKey.Undo, self.undo),
            (QKeySequence.StandardKey.Redo, self.redo),
        ):
            action = QAction(owner)
            action.setShortcut(key)
            owner.addAction(action)
            connect_action(action, command, parent=owner)

    def record(
        self,
        *,
        restore_state: StateRestorer,
        old_state: EditState,
        new_state: EditState,
    ) -> None:
        """Record an edit the calculator has already applied."""
        del self._edits[self._applied_edit_count :]
        self._edits.append(_FieldEdit(restore_state, old_state, new_state))
        self._applied_edit_count += 1

    def undo(self) -> None:
        if self._applied_edit_count:
            edit = self._edits[self._applied_edit_count - 1]
            edit.restore_state(*edit.old_state)
            self._applied_edit_count -= 1

    def redo(self) -> None:
        if self._applied_edit_count < len(self._edits):
            edit = self._edits[self._applied_edit_count]
            edit.restore_state(*edit.new_state)
            self._applied_edit_count += 1
