# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt-free ownership of the active project and its undo history."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from rc_metastudio import project_format
from rc_metastudio import project_adapter
from rc_metastudio.domain_ids import SheetId
from rc_metastudio.project_format import (
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


def _document_digest(document: ProjectDocument) -> str:
    # The active sheet is persisted navigation, not a document edit.
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

    def update_live_state(self, runtime: RuntimeProject) -> None:
        """Update the canonical live graph without creating history."""
        if self._runtime is None:
            self._runtime = runtime
            self._checkpoint = copy.deepcopy(runtime)
            self._saved_digest = None
            return
        if self._runtime is not runtime:
            self._runtime = runtime

    def checkpoint(self, expected_digest: str | None = None) -> None:
        """Record one live mutation after its adapter boundary has completed."""
        if self._runtime is None or self._transaction is not None:
            return
        current_digest = self._runtime_digest()
        if expected_digest is not None and expected_digest == self._saved_digest:
            self._saved_digest = current_digest
        assert self._checkpoint is not None
        if current_digest == self._checkpoint_digest():
            return
        self._record_before(RuntimeProject(
            self._checkpoint.dataset, self._runtime.current_sheet_id,
        ))
        self._checkpoint = copy.deepcopy(self._runtime)

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

    def begin_change(self) -> None:
        """Start one atomic UI operation."""
        if self._runtime is None:
            raise ValueError("cannot edit an empty workspace")
        if self._transaction is None:
            self._transaction = WorkspaceTransaction(copy.deepcopy(self._runtime))
        else:
            self._transaction.depth += 1

    def abort_change(self) -> RuntimeProject | None:
        """Abort the entire nested operation; return the graph to reinstall."""
        transaction = self._transaction
        if transaction is None:
            return None
        self._transaction = None
        self._runtime = transaction.before
        self._checkpoint = copy.deepcopy(self._runtime)
        return self._runtime

    def end_change(self) -> None:
        """Publish the current graph as one history entry."""
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
        if checkpoint_digest != current_digest:
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
        candidate = project_adapter.runtime_from_loaded_project(project_format.load_project(destination))
        checkpoint = copy.deepcopy(candidate)
        saved_digest = _document_digest(project_adapter.runtime_project_to_document(candidate))
        if install is not None:
            install(candidate)
        self._runtime = candidate
        self._checkpoint = checkpoint
        self._path = destination
        self._history.clear()
        self._redo.clear()
        self._saved_digest = saved_digest

    def start_new_document(self, *, keep_last_change: bool = False) -> None:
        """Start an unnamed document while preserving the live runtime identity."""
        if self._runtime is None:
            raise ValueError("cannot start a new document in an empty workspace")
        if self._transaction is not None:
            raise RuntimeError("cannot start a new document during a transaction")
        self._path = None
        self._history[:] = self._history[-1:] if keep_last_change else []
        self._redo.clear()
        self._checkpoint = copy.deepcopy(self._runtime)
        self._saved_digest = None

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
            self._saved_digest = self._runtime_digest()
            self._checkpoint = copy.deepcopy(current)
            raise
        self._path = destination
        self._saved_digest = self._runtime_digest()
        return destination

    def mark_saved(self) -> None:
        self._require_idle()
        if self._runtime is None:
            raise ValueError("cannot mark an empty workspace as saved")
        self._saved_digest = self._runtime_digest()
        self._checkpoint = copy.deepcopy(self._runtime)

    def undo(self) -> bool:
        self._require_idle()
        if not self._history or self._runtime is None:
            return False
        assert self._checkpoint is not None
        self._redo.append(self._checkpoint)
        self._checkpoint = self._history.pop()
        self._runtime = copy.deepcopy(self._checkpoint)
        return True

    def redo(self) -> bool:
        self._require_idle()
        if not self._redo or self._runtime is None:
            return False
        assert self._checkpoint is not None
        self._history.append(self._checkpoint)
        self._checkpoint = self._redo.pop()
        self._runtime = copy.deepcopy(self._checkpoint)
        return True
