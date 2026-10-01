# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Local crash-recovery persistence and validation contracts."""

from datetime import datetime, timezone
from pathlib import Path
import zipfile

import pytest

from rc_metastudio import analysis_draft_records, project_format, recovery_snapshot, saved_analysis
from rc_metastudio.project_format import ProjectDocument
from rc_metastudio.workspace_session import WorkspaceSession


ROOT = Path(__file__).resolve().parents[3]


def _workspace_document() -> ProjectDocument:
    document = project_format.load_project(ROOT / "sample_projects" / "amino.rcms")
    session = WorkspaceSession(document)
    session.add_saved_analysis(
        saved_analysis.create_record(
            input_snapshot={"family": "binary", "studies": []},
            specification={"family": "binary", "method": "binary.random"},
            results={"summary": {}, "sections": []},
            status="partial",
            backend_versions={"R": "4.6.1"},
            figures=[
                saved_analysis.SavedFigureInput(
                    "plot",
                    "Forest plot",
                    "image/svg+xml",
                    b'<svg xmlns="http://www.w3.org/2000/svg"></svg>',
                )
            ],
        )
    )
    session.save_analysis_draft(
        analysis_draft_records.create_record(
            {"outcome": "Recovery", "follow_up": None, "groups": [], "effect": "OR"},
            {"analysis_type": "binary", "method": "binary.random", "parameters": {}},
        )
    )
    result = session.document
    assert result is not None
    return result


def test_recovery_snapshot_round_trips_project_drafts_results_and_preview(tmp_path):
    document = _workspace_document()
    recovery_path = recovery_snapshot.default_recovery_snapshot_path(tmp_path / "app-data")
    saved_path = tmp_path / "saved.rcms"
    project_format.save_project(saved_path, document.project, document.state, assets=document.assets)
    saved_bytes = saved_path.read_bytes()

    preview = recovery_snapshot.write_recovery_snapshot(
        recovery_path,
        document,
        source_project_path=saved_path,
        workspace_was_dirty=True,
        created_at=datetime(2026, 9, 29, 9, 30, tzinfo=timezone.utc),
    )
    recovered = recovery_snapshot.read_recovery_snapshot(recovery_path)
    dataset = document.project["dataset"]
    assert isinstance(dataset, dict)
    studies = dataset["studies"]
    outcomes = dataset["outcomes"]
    assert isinstance(studies, list) and isinstance(outcomes, list)

    assert preview == recovered.preview
    assert preview.created_at == datetime(2026, 9, 29, 9, 30, tzinfo=timezone.utc)
    assert preview.project_title == "aminoglycosides"
    assert preview.source_project_path == str(saved_path)
    assert preview.workspace_was_dirty
    assert preview.study_count == len(studies)
    assert preview.outcome_count == len(outcomes)
    assert preview.saved_analysis_count == 1
    assert preview.analysis_draft_count == 1
    assert recovered.document.project == document.project
    assert recovered.document.state == document.state
    assert recovered.document.assets == document.assets
    assert saved_path.read_bytes() == saved_bytes
    assert project_format.load_project(saved_path).project == document.project


def test_invalid_document_keeps_previous_recovery_snapshot(tmp_path):
    path = recovery_snapshot.default_recovery_snapshot_path(tmp_path)
    original = _workspace_document()
    recovery_snapshot.write_recovery_snapshot(path, original)
    original_bytes = path.read_bytes()
    invalid = ProjectDocument(2, {"schema_version": 2}, {"schema_version": 2})

    with pytest.raises(recovery_snapshot.RecoverySnapshotError):
        recovery_snapshot.write_recovery_snapshot(path, invalid)

    assert path.read_bytes() == original_bytes
    assert recovery_snapshot.read_recovery_snapshot(path).document.project == original.project


def test_recovery_path_cannot_alias_saved_project_or_regular_project_file(tmp_path):
    document = _workspace_document()
    saved_path = tmp_path / "saved.rcms"
    project_format.save_project(saved_path, document.project, document.state, assets=document.assets)
    saved_bytes = saved_path.read_bytes()

    with pytest.raises(recovery_snapshot.RecoverySnapshotError, match="must use"):
        recovery_snapshot.write_recovery_snapshot(saved_path, document)
    with pytest.raises(recovery_snapshot.RecoverySnapshotError, match="must differ"):
        recovery_snapshot.write_recovery_snapshot(
            tmp_path / f"saved{recovery_snapshot.RECOVERY_SUFFIX}",
            document,
            source_project_path=tmp_path / f"saved{recovery_snapshot.RECOVERY_SUFFIX}",
        )

    assert saved_path.read_bytes() == saved_bytes


def test_corrupt_and_incomplete_recovery_reports_error_without_changing_project(tmp_path):
    document = _workspace_document()
    saved_path = tmp_path / "saved.rcms"
    project_format.save_project(saved_path, document.project, document.state, assets=document.assets)
    saved_bytes = saved_path.read_bytes()
    recovery_path = recovery_snapshot.default_recovery_snapshot_path(tmp_path)
    recovery_path.write_bytes(b"incomplete archive")

    with pytest.raises(recovery_snapshot.RecoverySnapshotError, match="corrupt or incomplete"):
        recovery_snapshot.read_recovery_snapshot(recovery_path)

    assert saved_path.read_bytes() == saved_bytes
    assert project_format.load_project(saved_path).project == document.project


def test_discard_invalidates_recovery_slot_and_is_idempotent(tmp_path):
    path = recovery_snapshot.default_recovery_snapshot_path(tmp_path)
    recovery_snapshot.write_recovery_snapshot(path, _workspace_document())

    assert recovery_snapshot.invalidate_recovery_snapshot(path)
    assert not path.exists()
    assert recovery_snapshot.invalidate_recovery_snapshot(path) is False


def test_reader_rejects_duplicate_or_missing_envelope_members(tmp_path):
    path = recovery_snapshot.default_recovery_snapshot_path(tmp_path)
    recovery_snapshot.write_recovery_snapshot(path, _workspace_document())
    incomplete = tmp_path / "incomplete.rcms-recovery"
    with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(incomplete, "w") as target:
        target.writestr("manifest.json", source.read("manifest.json"))
        target.writestr("metadata.json", source.read("metadata.json"))

    with pytest.raises(recovery_snapshot.RecoverySnapshotError, match="incomplete"):
        recovery_snapshot.read_recovery_snapshot(incomplete)
