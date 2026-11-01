# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt-free workspace ownership contracts."""

from pathlib import Path

import pytest

from rc_metastudio import project_format
from rc_metastudio.project_format import load_project
from rc_metastudio.workspace_session import WorkspaceSession

ROOT = Path(__file__).resolve().parents[3]


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
