# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt-free ownership of the active project and its undo history."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from uuid import UUID, uuid4

from rc_metastudio.project import archive as project_format
from rc_metastudio.project import adapter as project_adapter
from rc_metastudio.project.model import Dataset, PooledAnalysis, Sheet
from rc_metastudio.domain_ids import SheetId
from rc_metastudio.project.archive import (
    ProjectDocument,
    ProjectDurabilityError,
)

RuntimeProject = project_adapter.RuntimeProject
InstallRuntime = Callable[[RuntimeProject], None]


MAX_UNDO_CHANGES = 100


@dataclass(slots=True)
class WorkspaceTransaction:
    before: RuntimeProject
    depth: int = 1


@dataclass(frozen=True, slots=True)
class SheetAttachment:
    lineage: UUID
    sheet_id: SheetId


def _document_digest(document: ProjectDocument) -> str:
    payload = json.dumps(
        document.project,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class WorkspaceSession:
    """Own project replacement, persistence, and undo/redo independently of Qt."""

    def __init__(
        self, document: ProjectDocument | None = None, path: str | Path | None = None
    ) -> None:
        self._runtime = project_adapter.document_to_runtime_project(document) if document is not None else None
        self._checkpoint = copy.deepcopy(self._runtime)
        self._path = Path(path) if path is not None else None
        self._history: list[RuntimeProject] = []
        self._redo: list[RuntimeProject] = []
        self._transaction: WorkspaceTransaction | None = None
        document = self.document
        self._saved_digest = _document_digest(document) if document else None

    @property
    def document(self) -> ProjectDocument | None:
        if self._runtime is None:
            return None
        return project_adapter.runtime_project_to_document(self._runtime)

    @property
    def runtime(self) -> RuntimeProject | None:
        """Return the canonical live runtime graph owned by this session."""
        return self._runtime

    def record_edit(self, dataset: Dataset, current_sheet_id: SheetId | None) -> None:
        """Record a mutation or replacement of the dataset displayed by the adapter."""
        if self._runtime is None:
            self._runtime = RuntimeProject(dataset, current_sheet_id)
            self._checkpoint = copy.deepcopy(self._runtime)
            return
        if self._runtime.dataset is not dataset:
            self._runtime = RuntimeProject(dataset, current_sheet_id)
        else:
            self._runtime.current_sheet_id = current_sheet_id
        self.checkpoint()

    def checkpoint(self, *, originating_sheet: SheetId | None = None) -> None:
        """Record one live mutation after its adapter boundary has completed."""
        if self._runtime is None or self._transaction is not None:
            return
        current_digest = self._runtime_digest()
        assert self._checkpoint is not None
        if self._runtime.lineage == self._checkpoint.lineage and current_digest == self._checkpoint_digest():
            return
        sheet_id = originating_sheet or self._runtime.current_sheet_id
        before_sheet_id = sheet_id if self._runtime.lineage == self._checkpoint.lineage else self._checkpoint.current_sheet_id
        self._record_before(replace(self._checkpoint, current_sheet_id=before_sheet_id))
        self._checkpoint = copy.deepcopy(replace(self._runtime, current_sheet_id=sheet_id))

    def attach_sheet(self, sheet: Sheet | None) -> SheetAttachment | None:
        runtime = self._runtime
        if sheet is not None and runtime is not None and any(live is sheet for live in runtime.dataset.sheets):
            return SheetAttachment(runtime.lineage, sheet.id)
        return None

    def attached_sheet(self, attachment: SheetAttachment | None) -> Sheet | None:
        runtime = self._runtime
        if attachment is None or runtime is None or attachment.lineage != runtime.lineage:
            return None
        return next((sheet for sheet in runtime.dataset.sheets if sheet.id == attachment.sheet_id), None)

    def edit_sheet(self, attachment: SheetAttachment | None, operation: Callable[[Sheet], None]) -> bool:
        sheet = self.attached_sheet(attachment)
        if sheet is None:
            return False
        operation(sheet)
        self.checkpoint(originating_sheet=sheet.id)
        return True

    def last_pooled_fit(self, sheet: Sheet) -> PooledAnalysis | None:
        if self.attach_sheet(sheet) is None:
            return None
        assert self._runtime is not None
        return self._runtime.last_pooled_fits.get(sheet.id)

    def record_pooled_fit(self, sheet: Sheet, fit: PooledAnalysis) -> None:
        if self.attach_sheet(sheet) is not None:
            assert self._runtime is not None
            self._runtime.last_pooled_fits[sheet.id] = fit

    def discard_pooled_fit(self, sheet_id: SheetId) -> None:
        if self._runtime is not None:
            self._runtime.last_pooled_fits.pop(sheet_id, None)

    def _record_before(self, before: RuntimeProject) -> None:
        self._history.append(before)
        del self._history[:-MAX_UNDO_CHANGES]
        self._redo.clear()

    def _require_idle(self) -> None:
        if self._transaction is not None:
            raise RuntimeError("cannot replace, save or navigate history during a transaction")

    def select_sheet(self, sheet_id: SheetId | None) -> None:
        """Selection is navigation, not a separate undoable edit."""
        if self._runtime is not None:
            self._runtime.current_sheet_id = sheet_id

    @contextmanager
    def change(self, restore: InstallRuntime) -> Generator[None]:
        """Commit one operation, restoring the installed view if it fails."""
        self._begin_change()
        try:
            yield
            self._commit_change()
        except BaseException as error:
            runtime = self._abort_change()
            if runtime is None:
                raise
            try:
                restore(runtime)
            except Exception as restore_error:
                error.add_note(f"Workspace adapter restoration also failed: {restore_error}")
            raise

    def _begin_change(self) -> None:
        if self._runtime is None:
            raise ValueError("cannot edit an empty workspace")
        if self._transaction is None:
            self._transaction = WorkspaceTransaction(copy.deepcopy(self._runtime))
        else:
            self._transaction.depth += 1

    def _abort_change(self) -> RuntimeProject | None:
        transaction = self._transaction
        if transaction is None:
            return None
        self._transaction = None
        self._runtime = transaction.before
        self._checkpoint = copy.deepcopy(self._runtime)
        return self._runtime

    def _commit_change(self) -> None:
        transaction = self._transaction
        if transaction is None:
            return
        transaction.depth -= 1
        if transaction.depth:
            return
        checkpoint = transaction.before
        current_digest = self._runtime_digest()
        checkpoint_digest = _document_digest(
            project_adapter.runtime_project_to_document(checkpoint)
        )
        assert self._runtime is not None
        self._checkpoint = copy.deepcopy(self._runtime)
        if checkpoint.lineage != self._runtime.lineage or checkpoint_digest != current_digest:
            self._record_before(checkpoint)
        self._transaction = None

    def _runtime_digest(self) -> str:
        assert self._runtime is not None
        return _document_digest(
            project_adapter.runtime_project_to_document(self._runtime)
        )

    @property
    def runtime_digest(self) -> str | None:
        return self._runtime_digest() if self._runtime is not None else None

    def _checkpoint_digest(self) -> str:
        assert self._checkpoint is not None
        return _document_digest(
            project_adapter.runtime_project_to_document(self._checkpoint)
        )

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def is_dirty(self) -> bool:
        return self._runtime is not None and self._runtime_digest() != self._saved_digest

    @property
    def can_undo(self) -> bool:
        return bool(self._history)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def open(
        self, path: str | Path, *, install: InstallRuntime | None = None
    ) -> None:
        """Decode and validate before replacing the current project.

        ``install`` is a narrow adapter seam: callers may install the validated
        candidate in another representation before this session commits it.
        If installation fails, this session remains untouched.
        """
        self._require_idle()
        destination = Path(path)
        candidate = project_adapter.load_runtime_project(destination)
        checkpoint = copy.deepcopy(candidate)
        saved_digest = _document_digest(project_adapter.runtime_project_to_document(candidate))
        self._install_runtime(candidate, checkpoint, install)
        self._path = destination
        self._history.clear()
        self._redo.clear()
        self._saved_digest = saved_digest

    def start_new_document(
        self, candidate: RuntimeProject, *, install: InstallRuntime | None = None,
        undo_previous: bool = False,
    ) -> None:
        self._require_idle()
        candidate = replace(candidate, lineage=uuid4())
        previous = copy.deepcopy(self._runtime) if undo_previous else None
        checkpoint = copy.deepcopy(candidate)
        self._install_runtime(candidate, checkpoint, install)
        self._path = None
        self._history[:] = [previous] if previous is not None else []
        self._redo.clear()
        self._saved_digest = None

    def _install_runtime(
        self, candidate: RuntimeProject, checkpoint: RuntimeProject,
        install: InstallRuntime | None,
    ) -> None:
        if install is not None:
            install(candidate)
        self._runtime = candidate
        self._checkpoint = checkpoint

    def save(
        self,
        path: str | Path | None = None,
    ) -> Path:
        """Persist the canonical live runtime without changing its identity."""
        self._require_idle()
        current = self._runtime
        if current is None:
            raise ValueError("cannot save an empty workspace")
        destination = Path(path) if path is not None else self._path
        if destination is None:
            raise ValueError("save path is required for an unnamed workspace")
        serialized = project_adapter.runtime_project_to_document(current)
        try:
            project_format.save_project(
                destination, serialized.project, serialized.state
            )
        except ProjectDurabilityError:
            self._path = destination
            self._saved_digest = _document_digest(serialized)
            self._checkpoint = copy.deepcopy(current)
            raise
        self._path = destination
        self._saved_digest = _document_digest(serialized)
        return destination

    def mark_saved(self) -> None:
        self._require_idle()
        if self._runtime is None:
            raise ValueError("cannot mark an empty workspace as saved")
        self._saved_digest = self._runtime_digest()
        self._checkpoint = copy.deepcopy(self._runtime)

    def undo(self, *, install: InstallRuntime | None = None) -> bool:
        return self._move_history(self._history, self._redo, install)

    def redo(self, *, install: InstallRuntime | None = None) -> bool:
        return self._move_history(self._redo, self._history, install)

    def _move_history(
        self, source: list[RuntimeProject], destination: list[RuntimeProject],
        install: InstallRuntime | None,
    ) -> bool:
        self._require_idle()
        previous = self._checkpoint
        if not source or previous is None:
            return False
        checkpoint = source[-1]
        self._install_runtime(copy.deepcopy(checkpoint), checkpoint, install)
        source.pop()
        destination.append(previous)
        return True
