from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from rc_metastudio import analysis_draft_records, project_format, saved_analysis
from rc_metastudio.project_format import load_project
from rc_metastudio.workspace_session import WorkspaceSession


ROOT = Path(__file__).resolve().parents[3]
SAMPLE = ROOT / "sample_projects" / "amino.rcms"


def _draft(*, draft_id: str | None = None, outcome: str = "Pain"):
    return analysis_draft_records.create_record(
        {
            "outcome": outcome,
            "follow_up": "12 weeks",
            "groups": ["Control", "Treatment"],
            "effect": "OR",
        },
        {
            "analysis_type": None,
            "method": "binary.random",
            "parameters": {"confidence_level": 95.0, "correction": 0.5},
        },
        record_id=draft_id,
        updated_at=datetime(2026, 9, 29, tzinfo=timezone.utc),
    )


def _saved_analysis():
    return saved_analysis.create_record(
        {"family": "binary", "studies": []},
        {"version": 1, "family": "binary", "method": "binary.random"},
        {"version": 1, "summary": {}, "sections": []},
        status="complete",
        backend_versions={"R": "4.6.1"},
    )


def test_draft_round_trips_separately_from_completed_results(tmp_path: Path):
    session = WorkspaceSession(load_project(SAMPLE))
    result = _saved_analysis()
    draft = _draft()
    session.add_saved_analysis(result)
    session.save_analysis_draft(draft)

    destination = tmp_path / "draft.rcms"
    session.save(destination)
    reopened = WorkspaceSession(load_project(destination))

    assert reopened.list_analysis_drafts() == (draft.value,)
    assert reopened.get_analysis_draft(str(draft.value["id"])) == draft
    assert reopened.list_saved_analyses() == (result.value,)


def test_draft_update_delete_and_undo_are_project_changes():
    session = WorkspaceSession(load_project(SAMPLE))
    original = _draft()
    session.save_analysis_draft(original)
    record_id = str(original.value["id"])
    updated = _draft(draft_id=record_id, outcome="Sleep")

    session.save_analysis_draft(updated)
    assert session.get_analysis_draft(record_id) == updated
    assert session.undo()
    assert session.get_analysis_draft(record_id) == original
    assert session.redo()
    assert session.get_analysis_draft(record_id) == updated

    assert session.delete_analysis_draft(record_id)
    assert session.list_analysis_drafts() == ()
    assert session.undo()
    assert session.get_analysis_draft(record_id) == updated


def test_v1_migration_starts_with_no_unfinished_drafts():
    document = load_project(SAMPLE)

    assert document.format_version == project_format.CURRENT_FORMAT_VERSION
    assert document.project["analysis_drafts"] == []


@pytest.mark.parametrize(
    "selection,settings",
    [
        (
            {
                "outcome": "Pain",
                "follow_up": None,
                "groups": ["Control", "Control"],
                "effect": "OR",
            },
            {},
        ),
        (
            {
                "outcome": "Pain",
                "follow_up": None,
                "groups": [],
                "effect": "not-a-measure",
            },
            {},
        ),
        (
            {"outcome": "Pain", "follow_up": None, "groups": [], "effect": "OR"},
            {
                "analysis_type": None,
                "method": "binary.random",
                "parameters": {"parameter": object()},
            },
        ),
    ],
)
def test_invalid_draft_values_are_rejected(selection, settings):
    with pytest.raises(analysis_draft_records.AnalysisDraftError):
        analysis_draft_records.create_record(selection, settings)


def test_invalid_draft_does_not_change_workspace_or_history():
    session = WorkspaceSession(load_project(SAMPLE))
    before = session.document
    invalid = dict(_draft().value)
    invalid["selection"] = {
        "outcome": "Pain",
        "follow_up": None,
        "groups": ["Control", "Control"],
        "effect": "OR",
    }

    with pytest.raises(project_format.ProjectFormatError, match="analysis_drafts"):
        session.save_analysis_draft(
            analysis_draft_records.AnalysisDraftRecord(invalid)
        )
    assert session.document == before
    assert not session.can_undo


def test_unknown_draft_schema_version_is_rejected_when_opening_project(
    tmp_path: Path,
):
    session = WorkspaceSession(load_project(SAMPLE))
    session.save_analysis_draft(_draft())
    destination = tmp_path / "valid.rcms"
    session.save(destination)
    with zipfile.ZipFile(destination) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    project = json.loads(members["project.json"])
    project["analysis_drafts"][0]["schema_version"] = 99
    members["project.json"] = json.dumps(
        project, sort_keys=True, separators=(",", ":")
    ).encode("utf-8") + b"\n"
    manifest = json.loads(members["manifest.json"])
    manifest["members"]["project.json"] = {
        "sha256": hashlib.sha256(members["project.json"]).hexdigest(),
        "size": len(members["project.json"]),
    }
    members["manifest.json"] = json.dumps(
        manifest, sort_keys=True, separators=(",", ":")
    ).encode("utf-8") + b"\n"
    tampered = tmp_path / "unknown-draft-schema.rcms"
    with zipfile.ZipFile(tampered, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)

    with pytest.raises(project_format.ProjectFormatError, match="analysis_drafts"):
        load_project(tampered)
