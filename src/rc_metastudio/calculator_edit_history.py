# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Dialog-local calculator edit commands and undo history."""

from collections.abc import Callable
from typing import Protocol, TypeAlias


class CalculatorCommandOwner(Protocol):
    def update_back_calculation_button(self, engage: bool = False) -> None: ...


EditState: TypeAlias = tuple[object, ...]


StateRestorer: TypeAlias = Callable[..., None]


class FieldEditCommand:
    """Transient undo record for fields inside one open calculator dialog."""

    def __init__(
        self,
        *,
        owner: CalculatorCommandOwner,
        restore_state: StateRestorer,
        old_state: EditState,
        new_state: EditState,
        description: str = "",
        refresh_on_initial_redo: bool = True,
    ) -> None:
        self.owner = owner
        self.just_created = True
        self.restore_state = restore_state
        self.old_state = old_state
        self.new_state = new_state
        self.refresh_on_initial_redo = refresh_on_initial_redo

    def redo(self) -> None:
        if self.just_created:
            self.just_created = False
            if self.refresh_on_initial_redo:
                self.owner.update_back_calculation_button()
        else:
            self.restore_state(*self.new_state)

    def undo(self) -> None:
        self.restore_state(*self.old_state)


class TransientEditHistory:
    """Small dialog-local history; it is discarded when the dialog closes."""

    def __init__(self) -> None:
        self._commands: list[FieldEditCommand] = []
        self._index = 0

    def push(self, command: FieldEditCommand) -> None:
        del self._commands[self._index :]
        self._commands.append(command)
        self._index += 1
        command.redo()

    def undo(self) -> None:
        if self._index:
            self._index -= 1
            self._commands[self._index].undo()

    def redo(self) -> None:
        if self._index < len(self._commands):
            self._commands[self._index].redo()
            self._index += 1


def push_field_edit(
    history: TransientEditHistory,
    *,
    owner: CalculatorCommandOwner,
    restore_state: StateRestorer,
    old_state: EditState,
    new_state: EditState,
    description: str = "",
    refresh_on_initial_redo: bool = True,
) -> None:
    """Publish an already-applied calculator edit as one undoable state change."""
    history.push(
        make_field_edit_command(
            owner=owner,
            restore_state=restore_state,
            old_state=old_state,
            new_state=new_state,
            description=description,
            refresh_on_initial_redo=refresh_on_initial_redo,
        )
    )


def make_field_edit_command(
    *,
    owner: CalculatorCommandOwner,
    restore_state: StateRestorer,
    old_state: EditState,
    new_state: EditState,
    description: str = "",
    refresh_on_initial_redo: bool = True,
) -> FieldEditCommand:
    """Build a calculator edit command for a caller with atomic publication rules."""
    return FieldEditCommand(
        owner=owner,
        restore_state=restore_state,
        old_state=old_state,
        new_state=new_state,
        description=description,
        refresh_on_initial_redo=refresh_on_initial_redo,
    )
