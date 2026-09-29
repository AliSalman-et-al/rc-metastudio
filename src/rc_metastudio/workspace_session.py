# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt-free ownership of the active project and its undo history."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace as replace_dataclass
from pathlib import Path
from typing import cast

from rc_metastudio import project_format
from rc_metastudio import project_adapter
from rc_metastudio import saved_analysis
from rc_metastudio.project_domain import JsonObject, JsonValue
from rc_metastudio.project_format import (
    ProjectDocument,
    ProjectDurabilityError,
)

RuntimeProject = project_adapter.RuntimeProject
InstallRuntime = Callable[[RuntimeProject], None]


@dataclass(frozen=True, slots=True)
class WorkspaceChange:
    """One complete before/after replacement in the durable workspace."""

    before: RuntimeProject
    after: RuntimeProject


def _copy_runtime(runtime: RuntimeProject) -> RuntimeProject:
    return copy.deepcopy(runtime)


def _document_digest(document: ProjectDocument) -> str:
    payload = json.dumps(
        {
            "assets": {
                name: hashlib.sha256(value).hexdigest()
                for name, value in sorted(document.assets.items())
            },
            "project": document.project,
            "state": document.state,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validated_runtime(document: ProjectDocument) -> RuntimeProject:
    if document.format_version != project_format.CURRENT_FORMAT_VERSION:
        project, state = project_format.migrate_to_latest(
            document.format_version, document.project, document.state
        )
        document = ProjectDocument(
            project_format.CURRENT_FORMAT_VERSION,
            project,
            state,
            document.assets,
        )
    project_format.validate_project_document(document)
    return project_adapter.document_to_runtime_project(document)


def _assets_for_project(
    project: Mapping[str, JsonValue], assets: Mapping[str, bytes]
) -> dict[str, bytes]:
    records = project.get("saved_analyses", [])
    referenced: set[str] = set()
    if isinstance(records, list):
        for record in records:
            if not isinstance(record, dict):
                continue
            figures = record.get("figures", [])
            if not isinstance(figures, list):
                continue
            referenced.update(
                asset
                for figure in figures
                if isinstance(figure, dict)
                if isinstance((asset := figure.get("asset")), str)
            )
    return {name: value for name, value in assets.items() if name in referenced}


class WorkspaceSession:
    """Own project replacement, persistence, and undo/redo independently of Qt."""

    def __init__(
        self, document: ProjectDocument | None = None, path: str | Path | None = None
    ) -> None:
        self._runtime = _validated_runtime(document) if document is not None else None
        self._checkpoint = _copy_runtime(self._runtime) if self._runtime else None
        self._path = Path(path) if path is not None else None
        self._history: list[WorkspaceChange] = []
        self._redo: list[WorkspaceChange] = []
        self._forced_dirty = False
        self._transaction_checkpoint: RuntimeProject | None = None
        self._transaction_depth = 0
        document = self.document
        self._saved_digest = _document_digest(document) if document else None

    @property
    def document(self) -> ProjectDocument | None:
        if self._runtime is None:
            return None
        try:
            return project_adapter.runtime_project_to_document(self._runtime)
        except project_adapter.ProjectAdapterError:
            return None

    @property
    def project(self) -> JsonObject | None:
        document = self.document
        return copy.deepcopy(document.project) if document else None

    @property
    def state(self) -> JsonObject | None:
        document = self.document
        return copy.deepcopy(document.state) if document else None

    @property
    def runtime(self) -> RuntimeProject | None:
        """Return the canonical live runtime graph owned by this session."""
        return self._runtime

    def snapshot(self) -> RuntimeProject:
        """Return an isolated runtime checkpoint for a dialog or command."""
        if self._runtime is None:
            raise ValueError("cannot snapshot an empty workspace")
        return _copy_runtime(self._runtime)

    def update_live_state(self, runtime: RuntimeProject) -> None:
        """Update the canonical live graph without creating history."""
        if self._runtime is None:
            self._runtime = runtime
            self._checkpoint = _copy_runtime(runtime)
            self._saved_digest = None
            return
        runtime = replace_dataclass(
            runtime,
            saved_analyses=copy.deepcopy(self._runtime.saved_analyses),
            assets=copy.deepcopy(self._runtime.assets),
        )
        if self._runtime is not runtime:
            self._runtime = runtime

    def checkpoint(self, expected_digest: str | None = None) -> None:
        """Record one live mutation after its adapter boundary has completed."""
        if self._runtime is None:
            return
        try:
            current_digest = self._runtime_digest()
        except project_adapter.ProjectAdapterError:
            self._forced_dirty = True
            return
        if expected_digest is not None and expected_digest == self._saved_digest:
            self._saved_digest = current_digest
        if self._transaction_checkpoint is not None:
            return
        assert self._checkpoint is not None
        if current_digest == self._checkpoint_digest():
            return
        before = _copy_runtime(self._checkpoint)
        after = _copy_runtime(self._runtime)
        self._history.append(WorkspaceChange(before, after))
        self._redo.clear()
        self._checkpoint = _copy_runtime(self._runtime)

    def begin_change(self) -> None:
        """Start one atomic UI operation."""
        if self._runtime is None:
            raise ValueError("cannot edit an empty workspace")
        if self._transaction_depth == 0:
            self._transaction_checkpoint = _copy_runtime(self._runtime)
        self._transaction_depth += 1

    def end_change(self) -> None:
        """Publish the current graph as one history entry."""
        if self._transaction_depth == 0:
            return
        self._transaction_depth -= 1
        if self._transaction_depth:
            return
        checkpoint = self._transaction_checkpoint
        self._transaction_checkpoint = None
        if checkpoint is None or self._runtime is None:
            return
        try:
            current_digest = self._runtime_digest()
            checkpoint_digest = _document_digest(
                project_adapter.runtime_project_to_document(checkpoint)
            )
        except project_adapter.ProjectAdapterError:
            self._forced_dirty = True
            self._checkpoint = _copy_runtime(self._runtime)
            return
        if checkpoint_digest == current_digest:
            self._checkpoint = _copy_runtime(self._runtime)
            return
        self._history.append(WorkspaceChange(checkpoint, _copy_runtime(self._runtime)))
        self._redo.clear()
        self._checkpoint = _copy_runtime(self._runtime)

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
        if self._runtime is None:
            return self._forced_dirty
        if self._forced_dirty:
            return True
        try:
            return self._runtime_digest() != self._saved_digest
        except project_adapter.ProjectAdapterError:
            return True

    @property
    def can_undo(self) -> bool:
        return bool(self._history)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def replace(
        self,
        document: ProjectDocument,
        *,
        path: str | Path | None = None,
        record_history: bool = True,
    ) -> None:
        """Validate all replacement data before changing the live workspace."""
        candidate = _validated_runtime(document)
        previous = self._runtime
        if previous is not None and record_history:
            self._history.append(WorkspaceChange(_copy_runtime(previous), candidate))
            self._redo.clear()
        self._runtime = candidate
        self._checkpoint = _copy_runtime(candidate)
        if path is not None:
            self._path = Path(path)

    def commit(
        self,
        project: Mapping[str, JsonValue],
        state: Mapping[str, JsonValue],
    ) -> None:
        """Publish one validated project/state pair as one undoable change."""
        assets = _assets_for_project(
            project, self._runtime.assets if self._runtime is not None else {}
        )
        self.replace(
            ProjectDocument(
                project_format.CURRENT_FORMAT_VERSION,
                dict(project),
                dict(state),
                assets,
            )
        )

    def open(
        self, path: str | Path, *, install: InstallRuntime | None = None
    ) -> ProjectDocument:
        """Decode and validate before replacing the current project.

        ``install`` is a narrow adapter seam: callers may install the validated
        candidate in another representation before this session commits it.
        If installation fails, this session remains untouched.
        """
        candidate = _validated_runtime(project_format.load_project(path))
        if install is not None:
            previous_runtime = self._runtime
            previous_checkpoint = (
                _copy_runtime(self._checkpoint) if self._checkpoint else None
            )
            previous_path = self._path
            previous_history = copy.deepcopy(self._history)
            previous_redo = copy.deepcopy(self._redo)
            previous_saved_digest = self._saved_digest
            previous_forced_dirty = self._forced_dirty
            try:
                install(candidate)
            except Exception:
                self._runtime = previous_runtime
                self._checkpoint = previous_checkpoint
                self._path = previous_path
                self._history = previous_history
                self._redo = previous_redo
                self._saved_digest = previous_saved_digest
                self._forced_dirty = previous_forced_dirty
                raise
        self._runtime = candidate
        self._checkpoint = _copy_runtime(candidate)
        self._path = Path(path)
        self._history.clear()
        self._redo.clear()
        self._saved_digest = self._runtime_digest()
        self._checkpoint = _copy_runtime(self._runtime)
        self._forced_dirty = False
        loaded = self.document
        if loaded is None:
            raise RuntimeError(
                "workspace replacement unexpectedly produced no document"
            )
        return loaded

    def new(self, document: ProjectDocument, path: str | Path | None = None) -> None:
        candidate = _validated_runtime(document)
        self._runtime = candidate
        self._checkpoint = _copy_runtime(candidate)
        self._path = Path(path) if path is not None else None
        self._history.clear()
        self._redo.clear()
        self._saved_digest = self._runtime_digest()
        self._forced_dirty = False

    def start_new_document(self) -> None:
        """Start an unnamed document and discard saved results from prior data."""
        if self._runtime is None:
            raise ValueError("cannot start a new document in an empty workspace")
        if self._transaction_depth:
            raise RuntimeError("cannot start a new document during a transaction")
        self._runtime = replace_dataclass(
            self._runtime,
            saved_analyses=[],
            assets={},
        )
        self._path = None
        self._history.clear()
        self._redo.clear()
        self._checkpoint = _copy_runtime(self._runtime)
        self._saved_digest = None
        self._forced_dirty = False

    def save(
        self,
        path: str | Path | None = None,
    ) -> Path:
        """Persist the canonical live runtime without changing its identity."""
        current = self._runtime
        if current is None:
            raise ValueError("cannot save an empty workspace")
        destination = Path(path) if path is not None else self._path
        if destination is None:
            raise ValueError("save path is required for an unnamed workspace")
        serialized = project_adapter.runtime_project_to_document(current)
        try:
            project_format.save_project(
                destination,
                serialized.project,
                serialized.state,
                assets=serialized.assets,
            )
        except ProjectDurabilityError:
            self._path = destination
            self._saved_digest = self._runtime_digest()
            self._checkpoint = _copy_runtime(current)
            self._forced_dirty = False
            raise
        self._path = destination
        self._saved_digest = self._runtime_digest()
        self._forced_dirty = False
        return destination

    def mark_saved(self) -> None:
        if self._runtime is None:
            raise ValueError("cannot mark an empty workspace as saved")
        self._saved_digest = self._runtime_digest()
        self._checkpoint = _copy_runtime(self._runtime)
        self._forced_dirty = False

    def mark_dirty(self) -> None:
        """Mark the current document dirty when an adapter changes its view state."""
        self._forced_dirty = True

    def undo(self) -> bool:
        if not self._history or self._runtime is None:
            return False
        change = self._history.pop()
        self._redo.append(
            WorkspaceChange(_copy_runtime(change.after), _copy_runtime(self._runtime))
        )
        self._runtime = _copy_runtime(change.before)
        self._checkpoint = _copy_runtime(self._runtime)
        self._forced_dirty = False
        return True

    def redo(self) -> bool:
        if not self._redo or self._runtime is None:
            return False
        change = self._redo.pop()
        self._history.append(
            WorkspaceChange(_copy_runtime(self._runtime), _copy_runtime(change.before))
        )
        self._runtime = _copy_runtime(change.before)
        self._checkpoint = _copy_runtime(self._runtime)
        self._forced_dirty = False
        return True

    def mutate(self, edit: Callable[[JsonObject, JsonObject], None]) -> None:
        """Apply a pure boundary edit and publish it as one coherent change."""
        if self._runtime is None:
            raise ValueError("cannot edit an empty workspace")
        document = self.document
        assert document is not None
        project = copy.deepcopy(document.project)
        state = copy.deepcopy(document.state)
        edit(project, state)
        self.commit(project, state)

    def list_saved_analyses(self) -> tuple[JsonObject, ...]:
        """Return isolated metadata for each saved analysis, in project order."""
        if self._runtime is None:
            return ()
        return tuple(copy.deepcopy(self._runtime.saved_analyses))

    def get_saved_analysis(
        self, record_id: str
    ) -> saved_analysis.SavedAnalysisRecord | None:
        """Return a saved record and only the embedded bytes that it references."""
        if self._runtime is None:
            return None
        record = next(
            (
                value
                for value in self._runtime.saved_analyses
                if value.get("id") == record_id
            ),
            None,
        )
        if record is None:
            return None
        figures = record.get("figures", [])
        if not isinstance(figures, list):
            figures = []
        references = {
            asset
            for figure in figures
            if isinstance(figure, dict)
            if isinstance((asset := figure.get("asset")), str)
        }
        return saved_analysis.SavedAnalysisRecord(
            cast(saved_analysis.JsonObject, copy.deepcopy(record)),
            {
                name: bytes(value)
                for name, value in self._runtime.assets.items()
                if name in references
            },
        )

    def add_saved_analysis(self, record: saved_analysis.SavedAnalysisRecord) -> None:
        """Retain a validated completed result as an undoable project change."""
        current = self._runtime
        if current is None:
            raise ValueError("cannot add an analysis to an empty workspace")
        value = copy.deepcopy(record.value)
        if any(item.get("id") == value.get("id") for item in current.saved_analyses):
            raise ValueError("saved analysis ID already exists in this project")
        project = project_adapter.runtime_project_to_document(current).project
        records = project.get("saved_analyses")
        if not isinstance(records, list):
            raise ValueError("current project saved analyses are invalid")
        records.append(value)
        assets = copy.deepcopy(current.assets)
        for name, payload in record.assets.items():
            previous = assets.get(name)
            if previous is not None and previous != payload:
                raise ValueError("saved analysis asset path has conflicting bytes")
            assets[name] = bytes(payload)
        document = ProjectDocument(
            project_format.CURRENT_FORMAT_VERSION,
            project,
            project_adapter.runtime_project_to_document(current).state,
            assets,
        )
        candidate = _validated_runtime(document)
        self._history.append(
            WorkspaceChange(_copy_runtime(current), _copy_runtime(candidate))
        )
        self._redo.clear()
        self._runtime = replace_dataclass(
            current,
            saved_analyses=candidate.saved_analyses,
            assets=candidate.assets,
        )
        self._checkpoint = _copy_runtime(self._runtime)

    def delete_saved_analysis(self, record_id: str) -> bool:
        """Explicitly remove one saved result and assets no other record uses."""
        current = self._runtime
        if current is None:
            return False
        records = [
            copy.deepcopy(record)
            for record in current.saved_analyses
            if record.get("id") != record_id
        ]
        if len(records) == len(current.saved_analyses):
            return False
        project = project_adapter.runtime_project_to_document(current).project
        project["saved_analyses"] = records
        assets = _assets_for_project(project, current.assets)
        document = ProjectDocument(
            project_format.CURRENT_FORMAT_VERSION,
            project,
            project_adapter.runtime_project_to_document(current).state,
            assets,
        )
        candidate = _validated_runtime(document)
        self._history.append(
            WorkspaceChange(_copy_runtime(current), _copy_runtime(candidate))
        )
        self._redo.clear()
        self._runtime = replace_dataclass(
            current,
            saved_analyses=candidate.saved_analyses,
            assets=candidate.assets,
        )
        self._checkpoint = _copy_runtime(self._runtime)
        return True
