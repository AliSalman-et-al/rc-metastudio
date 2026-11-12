# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt-free workspace ownership contracts."""

from pathlib import Path

import pytest

from rc_metastudio import project_format
from rc_metastudio.project_format import load_project
from rc_metastudio.workspace_session import WorkspaceSession
from rc_metastudio.qt_object_guard import required

ROOT = Path(__file__).resolve().parents[3]


def test_abort_restores_nested_edit_without_consuming_existing_redo():
    # Failure modes: partial mutations survive, redo disappears, nested close
    # commits an aborted graph, or the next operation inherits stale depth.
    session = WorkspaceSession(load_project(ROOT / "sample_projects/amino.rcms"))
    required(session.runtime, "workspace runtime").dataset.title = "first edit"
    session.checkpoint()
    assert session.undo()
    before = session.document
    session.begin_change()
    required(session.runtime, "workspace runtime").dataset.title = "partial outer"
    session.begin_change()
    required(session.runtime, "workspace runtime").dataset.notes = "partial inner"
    session.abort_change()
    session.end_change()
    session.end_change()
    assert session.document == before
    assert session.can_redo and not session.can_undo
    assert not session.is_dirty
    session.begin_change()
    required(session.runtime, "workspace runtime").dataset.title = "recovered"
    session.end_change()
    assert session.undo() and session.document == before
    assert session.redo() and required(session.runtime, "workspace runtime").dataset.title == "recovered"


def test_history_retention_does_not_alias_live_edits():
    session = WorkspaceSession(load_project(ROOT / "sample_projects/amino.rcms"))
    for index in range(105):
        required(session.runtime, "workspace runtime").dataset.title = f"edit {index}"
        session.checkpoint()
    undos = 0
    while session.undo():
        undos += 1
    assert undos == 100
    assert required(session.runtime, "workspace runtime").dataset.title == "edit 4"
    for _ in range(100):
        assert session.redo()
    assert required(session.runtime, "workspace runtime").dataset.title == "edit 104"
    required(session.runtime, "workspace runtime").dataset.title = "new branch"
    session.checkpoint()
    assert session.undo() and required(session.runtime, "workspace runtime").dataset.title == "edit 104"


def test_failed_transaction_serialization_remains_abortable():
    session = WorkspaceSession(load_project(ROOT / "sample_projects/amino.rcms"))
    before = session.document
    session.begin_change()
    required(session.runtime, "workspace runtime").dataset.sheets[0].settings["bad"] = float("nan")
    with pytest.raises(ValueError):
        session.end_change()
    assert session.abort_change() is not None
    assert session.document == before
    assert not session.can_undo and not session.is_dirty


def test_save_cannot_publish_a_half_finished_transaction(tmp_path):
    session = WorkspaceSession(load_project(ROOT / "sample_projects/amino.rcms"))
    session.begin_change()
    required(session.runtime, "workspace runtime").dataset.title = "unfinished"
    target = tmp_path / "unfinished.rcms"
    with pytest.raises(RuntimeError, match="transaction"):
        session.save(target)
    assert not target.exists()
    session.abort_change()
    assert not session.is_dirty


@pytest.mark.parametrize("committed_sheet", [0, 1])
def test_redo_restores_committed_sheet_after_unrelated_navigation(committed_sheet):
    session = WorkspaceSession(load_project(ROOT / "sample_projects/amino.rcms"))
    runtime = required(session.runtime, "workspace runtime")
    selected = runtime.dataset.sheets[committed_sheet].id
    runtime.dataset.title = "changed"
    session.select_sheet(selected)
    session.checkpoint()
    session.select_sheet(runtime.dataset.sheets[1 - committed_sheet].id)
    assert session.undo()
    assert required(session.runtime, "workspace runtime").model_state["current_sheet_id"] == selected
    session.select_sheet(runtime.dataset.sheets[1 - committed_sheet].id)
    assert session.redo()
    assert required(session.runtime, "workspace runtime").model_state["current_sheet_id"] == selected


def test_nested_transactions_publish_one_history_entry() -> None:
    document = load_project(ROOT / "sample_projects" / "amino.rcms")
    session = WorkspaceSession(document)
    runtime = session.runtime
    assert runtime is not None

    session.begin_change()
    runtime.dataset.title = "outer"
    session.begin_change()
    runtime.dataset.notes = "inner"
    session.end_change()
    assert not session.can_undo
    session.end_change()

    assert session.undo()
    assert session.runtime is not None
    assert session.runtime.dataset.title != "outer"
    assert session.runtime.dataset.notes != "inner"
    assert not session.can_undo


def test_failed_install_preserves_document_history_and_path(tmp_path: Path) -> None:
    document = load_project(ROOT / "sample_projects" / "amino.rcms")
    source = ROOT / "sample_projects" / "amino.rcms"
    session = WorkspaceSession(document, source)
    project = session.project
    state = session.state
    assert project is not None and state is not None
    dataset = project
    assert isinstance(dataset, dict)
    dataset["title"] = "Edited before failed install"
    session.commit(project, state)
    before = session.document
    previous_runtime = session.runtime

    with pytest.raises(RuntimeError, match="adapter failed"):
        session.open(
            ROOT / "sample_projects" / "continuous.rcms",
            install=lambda _candidate: (_ for _ in ()).throw(
                RuntimeError("adapter failed")
            ),
        )

    assert session.document == before
    assert session.runtime is previous_runtime
    assert session.path == source
    assert session.is_dirty
    assert session.can_undo


def test_durability_failure_commits_the_installed_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = load_project(ROOT / "sample_projects" / "continuous.rcms")
    session = WorkspaceSession(document)
    destination = tmp_path / "durability.rcms"
    project = session.project
    state = session.state
    assert project is not None and state is not None
    dataset = project
    assert isinstance(dataset, dict)
    dataset["title"] = "Installed despite uncertainty"
    runtime = session.runtime
    assert runtime is not None
    runtime.dataset.title = "Installed despite uncertainty"

    def uncertain(_destination: Path) -> None:
        raise project_format.ProjectDurabilityError(
            "project was atomically replaced, but directory durability could not be confirmed; the new file is already installed"
        )

    monkeypatch.setattr(project_format, "_fsync_parent_directory", uncertain)
    with pytest.raises(project_format.ProjectDurabilityError):
        session.save(destination)

    assert session.path == destination
    assert not session.is_dirty
    assert session.project == project
    assert load_project(destination).project == project


def test_save_marks_only_successfully_written_snapshot_clean(tmp_path: Path) -> None:
    document = load_project(ROOT / "sample_projects" / "continuous.rcms")
    session = WorkspaceSession(document)
    project = session.project
    state = session.state
    assert project is not None and state is not None
    dataset = project
    assert isinstance(dataset, dict)
    dataset["title"] = "Saved"
    session.commit(project, state)
    destination = tmp_path / "saved.rcms"

    assert session.save(destination) == destination
    assert not session.is_dirty
    saved = load_project(destination).project
    assert saved["title"] == "Saved"
