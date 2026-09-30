# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt-free workspace ownership contracts."""

from pathlib import Path
import hashlib

import pytest

from rc_metastudio import project_format
from rc_metastudio import project_adapter
from rc_metastudio import saved_analysis
from rc_metastudio.project_format import load_project
from rc_metastudio.workspace_session import SavedAnalysisConflict, WorkspaceSession

ROOT = Path(__file__).resolve().parents[3]


def _saved_analysis_record() -> saved_analysis.SavedAnalysisRecord:
    return saved_analysis.create_record(
        input_snapshot={"family": "binary", "studies": []},
        specification={"version": 1, "family": "binary", "method": "binary.random"},
        results={"version": 1, "summary": {}, "sections": []},
        status="partial",
        backend_versions={"R": "4.6.1"},
        figures=[
            saved_analysis.SavedFigureInput(
                "plot",
                "Plot",
                "image/svg+xml",
                b'<svg xmlns="http://www.w3.org/2000/svg"></svg>',
            )
        ],
    )


def _figure_record() -> saved_analysis.SavedAnalysisRecord:
    figure = b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="2" height="2"/></svg>'
    asset = "assets/%s.svg" % hashlib.sha256(figure).hexdigest()
    return saved_analysis.create_record(
        input_snapshot={"family": "binary", "studies": [{"id": "s1"}]},
        specification={"version": 1, "family": "binary", "method": "binary.random"},
        results={
            "version": 1,
            "summary": {"estimate": 1.25},
            "binary_numerics": {"pooled": {"estimate": 1.25}},
            "images": {"forest": asset},
            "display_images": {"forest": asset},
            "sections": [],
        },
        status="complete",
        backend_versions={"R": "4.6.1"},
        figures=[
            saved_analysis.SavedFigureInput("images:forest", "Forest plot", "image/svg+xml", figure),
            saved_analysis.SavedFigureInput("display_images:forest", "Forest plot", "image/svg+xml", figure),
        ],
        presentation={"fp_xlabel": "Effect"},
    )


def test_session_replaces_and_undoes_one_complete_snapshot() -> None:
    document = load_project(ROOT / "sample_projects" / "amino.rcms")
    session = WorkspaceSession(document)
    project = session.project
    state = session.state
    assert project is not None and state is not None
    dataset = project["dataset"]
    assert isinstance(dataset, dict)
    dataset["title"] = "Edited"

    session.commit(project, state)

    assert session.is_dirty
    assert session.undo()
    assert not session.is_dirty
    assert session.redo()
    edited = session.project
    assert edited is not None and isinstance(edited["dataset"], dict)
    assert edited["dataset"]["title"] == "Edited"


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


def test_failed_open_preserves_document_history_and_path(tmp_path: Path) -> None:
    document = load_project(ROOT / "sample_projects" / "amino.rcms")
    session = WorkspaceSession(document, ROOT / "sample_projects" / "amino.rcms")
    before = session.project
    bad = tmp_path / "invalid.rcms"
    bad.write_bytes(b"not an rcms archive")

    with pytest.raises(ValueError):
        session.open(bad)

    assert session.project == before
    assert session.path == ROOT / "sample_projects" / "amino.rcms"
    assert not session.is_dirty


def test_failed_install_preserves_document_history_and_path(tmp_path: Path) -> None:
    document = load_project(ROOT / "sample_projects" / "amino.rcms")
    source = ROOT / "sample_projects" / "amino.rcms"
    session = WorkspaceSession(document, source)
    project = session.project
    state = session.state
    assert project is not None and state is not None
    dataset = project["dataset"]
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
    dataset = project["dataset"]
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
    dataset = project["dataset"]
    assert isinstance(dataset, dict)
    dataset["title"] = "Saved"
    session.commit(project, state)
    destination = tmp_path / "saved.rcms"

    assert session.save(destination) == destination
    assert not session.is_dirty
    saved = load_project(destination).project
    assert isinstance(saved["dataset"], dict)
    assert saved["dataset"]["title"] == "Saved"


def test_live_runtime_identity_survives_checkpoint_and_save(tmp_path: Path) -> None:
    document = load_project(ROOT / "sample_projects" / "continuous.rcms")
    session = WorkspaceSession(document)
    runtime = session.runtime
    assert runtime is not None
    dataset = runtime.dataset

    dataset.title = "Live identity"
    session.update_live_state(
        project_adapter.RuntimeProject(
            dataset=dataset,
            model_state=runtime.model_state,
            restored_selection=runtime.restored_selection,
        )
    )
    session.checkpoint()
    assert session.runtime is not None
    assert session.runtime.dataset is dataset
    assert session.can_undo

    destination = tmp_path / "identity.rcms"
    session.save(destination)
    assert session.runtime is not None
    assert session.runtime.dataset is dataset
    assert load_project(destination).project == session.project


def test_start_new_document_clears_saved_analysis_records_and_assets() -> None:
    session = WorkspaceSession(
        load_project(ROOT / "sample_projects" / "amino.rcms")
    )
    session.add_saved_analysis(_saved_analysis_record())
    assert len(session.list_saved_analyses()) == 1
    assert session.runtime is not None and session.runtime.assets

    imported = project_adapter.document_to_runtime_project(
        load_project(ROOT / "sample_projects" / "continuous.rcms")
    )
    session.update_live_state(imported)
    assert len(session.list_saved_analyses()) == 1
    assert session.runtime is not None and session.runtime.assets

    session.start_new_document()

    document = session.document
    assert document is not None
    assert document.project["saved_analyses"] == []
    assert document.assets == {}
    assert session.list_saved_analyses() == ()
    assert session.runtime is not None and session.runtime.assets == {}


def test_ordinary_live_model_edit_retains_saved_analysis_and_assets() -> None:
    session = WorkspaceSession(
        load_project(ROOT / "sample_projects" / "continuous.rcms")
    )
    session.add_saved_analysis(_saved_analysis_record())
    runtime = session.runtime
    assert runtime is not None

    model_state = dict(runtime.model_state)
    model_state["confidence_level"] = 90.0
    session.update_live_state(
        project_adapter.RuntimeProject(
            dataset=runtime.dataset,
            model_state=model_state,
            restored_selection=runtime.restored_selection,
        )
    )

    document = session.document
    assert document is not None
    assert len(session.list_saved_analyses()) == 1
    assert document.project["saved_analyses"] == list(session.list_saved_analyses())
    assert len(document.assets) == 1


def test_saved_figure_update_is_atomic_stale_safe_and_undoable(tmp_path: Path) -> None:
    session = WorkspaceSession(load_project(ROOT / "sample_projects" / "amino.rcms"))
    original = _figure_record()
    session.add_saved_analysis(original)
    session.mark_saved()
    record_id = str(original.value["id"])
    revision = saved_analysis.record_revision(original)
    updated_figure = b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="3" height="3"/></svg>'

    new_revision = session.update_saved_analysis_figure(
        record_id,
        revision,
        "forest",
        updated_figure,
        "image/svg+xml",
        display_data=updated_figure,
        display_media_type="image/svg+xml",
        presentation_update={"fp_xlabel": "Updated effect"},
    )

    updated = session.get_saved_analysis(record_id)
    assert updated is not None
    assert new_revision == saved_analysis.record_revision(updated)
    assert new_revision != revision
    assert session.is_dirty
    assert updated.value["input_identity"] == original.value["input_identity"]
    assert updated.value["specification_identity"] == original.value["specification_identity"]
    updated_results = updated.value["results"]
    original_results = original.value["results"]
    assert isinstance(updated_results, dict) and isinstance(original_results, dict)
    assert updated_results["summary"] == original_results["summary"]
    assert updated_results["binary_numerics"] == original_results["binary_numerics"]
    presentation = updated.value["presentation"]
    assert isinstance(presentation, dict)
    assert presentation["fp_xlabel"] == "Effect"
    assert presentation["figures"] == {"forest": {"fp_xlabel": "Updated effect"}}

    with pytest.raises(SavedAnalysisConflict, match="changed"):
        session.update_saved_analysis_figure(
            record_id,
            revision,
            "forest",
            updated_figure,
            "image/svg+xml",
            presentation_update={"fp_xlabel": "Stale"},
        )
    assert session.get_saved_analysis(record_id) == updated

    destination = tmp_path / "edited.rcms"
    session.save(destination)
    reopened = load_project(destination)
    stored_records = reopened.project["saved_analyses"]
    assert isinstance(stored_records, list)
    stored = stored_records[0]
    assert isinstance(stored, dict)
    stored_presentation = stored["presentation"]
    assert isinstance(stored_presentation, dict)
    assert stored_presentation["fp_xlabel"] == "Effect"
    assert stored_presentation["figures"] == {"forest": {"fp_xlabel": "Updated effect"}}
    figures = stored["figures"]
    assert isinstance(figures, list)
    figure_assets = {}
    for figure in figures:
        assert isinstance(figure, dict)
        asset = figure["asset"]
        assert isinstance(asset, str)
        figure_assets[asset] = reopened.assets[asset]
    assert set(figure_assets.values()) == {updated_figure}

    assert session.undo()
    undone = session.get_saved_analysis(record_id)
    assert undone is not None
    assert saved_analysis.record_revision(undone) == revision
    assert session.redo()
    redone = session.get_saved_analysis(record_id)
    assert redone is not None
    assert saved_analysis.record_revision(redone) == new_revision


def test_open_installs_and_adopts_the_same_runtime_object() -> None:
    source = ROOT / "sample_projects" / "amino.rcms"
    session = WorkspaceSession(
        load_project(ROOT / "sample_projects" / "continuous.rcms")
    )
    installed = []

    session.open(source, install=installed.append)

    assert installed
    assert session.runtime is installed[0]
