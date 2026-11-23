# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt-free workspace ownership contracts."""

from pathlib import Path

import pytest

from rc_metastudio.project import archive as project_format
from rc_metastudio.project.archive import load_project
from rc_metastudio.workspace.session import WorkspaceSession
from rc_metastudio.qt_object_guard import required

ROOT = Path(__file__).resolve().parents[3]


def test_history_retention_does_not_alias_live_edits():
    session = WorkspaceSession(load_project(ROOT / "tests/fixtures/desktop-projects/amino.rcms"))
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
    session = WorkspaceSession(load_project(ROOT / "tests/fixtures/desktop-projects/amino.rcms"))
    before = session.document
    with pytest.raises(ValueError):
        with session.change(lambda _: None):
            required(session.runtime, "workspace runtime").dataset.sheets[0].settings["bad"] = float("nan")
    assert session.document == before
    assert not session.can_undo and not session.is_dirty


def test_save_cannot_publish_a_half_finished_transaction(tmp_path):
    session = WorkspaceSession(load_project(ROOT / "tests/fixtures/desktop-projects/amino.rcms"))
    target = tmp_path / "unfinished.rcms"
    with pytest.raises(RuntimeError, match="transaction"):
        with session.change(lambda _: None):
            required(session.runtime, "workspace runtime").dataset.title = "unfinished"
            session.save(target)
    assert not target.exists()
    assert not session.is_dirty


@pytest.mark.parametrize("committed_sheet", [0, 1])
def test_redo_restores_committed_sheet_after_unrelated_navigation(committed_sheet):
    session = WorkspaceSession(load_project(ROOT / "tests/fixtures/desktop-projects/amino.rcms"))
    runtime = required(session.runtime, "workspace runtime")
    selected = runtime.dataset.sheets[committed_sheet].id
    runtime.dataset.title = "changed"
    session.select_sheet(selected)
    session.checkpoint()
    session.select_sheet(runtime.dataset.sheets[1 - committed_sheet].id)
    assert session.undo()
    assert required(session.runtime, "workspace runtime").current_sheet_id == selected
    session.select_sheet(runtime.dataset.sheets[1 - committed_sheet].id)
    assert session.redo()
    assert required(session.runtime, "workspace runtime").current_sheet_id == selected


def test_failed_install_preserves_document_history_and_path(tmp_path: Path) -> None:
    document = load_project(ROOT / "tests/fixtures/desktop-projects" / "amino.rcms")
    source = ROOT / "tests/fixtures/desktop-projects" / "amino.rcms"
    session = WorkspaceSession(document, source)
    required(session.runtime, "workspace runtime").dataset.title = "Edited before failed install"
    session.checkpoint()
    before = session.document
    previous_runtime = session.runtime

    with pytest.raises(RuntimeError, match="adapter failed"):
        session.open(
            ROOT / "tests/fixtures/desktop-projects" / "continuous.rcms",
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
    document = load_project(ROOT / "tests/fixtures/desktop-projects" / "continuous.rcms")
    session = WorkspaceSession(document)
    destination = tmp_path / "durability.rcms"
    runtime = session.runtime
    assert runtime is not None
    runtime.dataset.title = "Installed despite uncertainty"
    expected = required(session.document, "workspace document").project

    def uncertain(_destination: Path) -> None:
        raise project_format.ProjectDurabilityError(
            "project was atomically replaced, but directory durability could not be confirmed; the new file is already installed"
        )

    monkeypatch.setattr(project_format, "_fsync_parent_directory", uncertain)
    with pytest.raises(project_format.ProjectDurabilityError):
        session.save(destination)

    assert session.path == destination
    assert not session.is_dirty
    assert load_project(destination).project == expected


def test_save_marks_only_successfully_written_snapshot_clean(tmp_path: Path) -> None:
    document = load_project(ROOT / "tests/fixtures/desktop-projects" / "continuous.rcms")
    session = WorkspaceSession(document)
    required(session.runtime, "workspace runtime").dataset.title = "Saved"
    session.checkpoint()
    destination = tmp_path / "saved.rcms"

    assert session.save(destination) == destination
    assert not session.is_dirty
    saved = load_project(destination).project
    assert saved["title"] == "Saved"
