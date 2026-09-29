from __future__ import annotations

import copy
import base64
import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from rc_metastudio import project_format, saved_analysis
from rc_metastudio.project_format import ProjectFormatError, load_project, save_project
from rc_metastudio.workspace_session import WorkspaceSession


ROOT = Path(__file__).resolve().parents[3]
SAMPLE = ROOT / "sample_projects" / "amino.rcms"
_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADUlEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)


def _record(*, record_id: str | None = None) -> saved_analysis.SavedAnalysisRecord:
    return saved_analysis.create_record(
        input_snapshot={"family": "binary", "studies": [{"events": [2, 10]}]},
        specification={
            "version": 1,
            "family": "binary",
            "workflow": "standard",
            "method": "binary.random",
            "metric": "OR",
            "parameters": {"confidence_level": 95.0},
        },
        results={"version": 1, "summary": {"estimate": 1.25}, "sections": []},
        status="partial",
        warnings=["One interval could not be estimated."],
        backend_versions={"R": "4.6.1", "RCMetaR": "0.4.1"},
        figures=[
            saved_analysis.SavedFigureInput(
                "forest", "Forest plot", "image/png", _PNG
            )
        ],
        record_id=record_id,
    )


def _archive_members(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _write_archive(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def _tamper_record_version(source: Path, destination: Path) -> None:
    members = _archive_members(source)
    project = json.loads(members["project.json"])
    project["saved_analyses"][0]["schema_version"] = 99
    members["project.json"] = _json_bytes(project)
    manifest = json.loads(members["manifest.json"])
    manifest["members"]["project.json"] = {
        "sha256": hashlib.sha256(members["project.json"]).hexdigest(),
        "size": len(members["project.json"]),
    }
    members["manifest.json"] = _json_bytes(manifest)
    _write_archive(destination, members)


def test_released_v1_project_migrates_without_changing_dataset_or_selection():
    with zipfile.ZipFile(SAMPLE) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        old_project = json.loads(archive.read("project.json"))
        old_state = json.loads(archive.read("state.json"))

    assert manifest["format_version"] == 1
    loaded = load_project(SAMPLE)

    assert loaded.format_version == 2
    assert loaded.project["schema_version"] == 2
    assert loaded.project["saved_analyses"] == []
    assert loaded.project["dataset"] == old_project["dataset"]
    assert loaded.state == {**old_state, "schema_version": 2}


def test_saved_partial_analysis_and_figure_round_trip_without_backend(tmp_path: Path):
    session = WorkspaceSession(load_project(SAMPLE))
    first = _record()
    second = _record()

    session.add_saved_analysis(first)
    project = session.project
    state = session.state
    assert project is not None and state is not None
    dataset = project["dataset"]
    assert isinstance(dataset, dict)
    dataset["title"] = "Edited after run"
    session.commit(project, state)
    session.add_saved_analysis(second)

    assert session.is_dirty
    listed = session.list_saved_analyses()
    assert len(listed) == 2
    assert [item["status"] for item in listed] == ["partial", "partial"]
    saved = session.get_saved_analysis(str(first.value["id"]))
    assert saved is not None
    figures = saved.value["figures"]
    assert isinstance(figures, list)
    figure = figures[0]
    assert isinstance(figure, dict)
    assert saved.assets[figure["asset"]] == _PNG

    destination = tmp_path / "with-results.rcms"
    session.save(destination)
    reopened = load_project(destination)
    reopened_analyses = reopened.project["saved_analyses"]
    assert isinstance(reopened_analyses, list)
    assert len(reopened_analyses) == 2
    assert reopened.assets == {**first.assets, **second.assets}
    reopened_dataset = reopened.project["dataset"]
    assert isinstance(reopened_dataset, dict)
    assert reopened_dataset["title"] == "Edited after run"
    first_reopened = reopened_analyses[0]
    assert isinstance(first_reopened, dict)
    assert first_reopened["input_snapshot"] == first.value[
        "input_snapshot"
    ]

    first_id = str(first.value["id"])
    assert session.delete_saved_analysis(first_id)
    assert session.get_saved_analysis(first_id) is None
    assert len(session.list_saved_analyses()) == 1
    assert session.delete_saved_analysis(first_id) is False
    remaining_id = str(second.value["id"])
    assert session.delete_saved_analysis(remaining_id)
    assert session.runtime is not None and session.runtime.assets == {}


def test_presentation_changes_do_not_change_saved_scientific_identity():
    base = _record()
    input_snapshot = {"family": "binary", "studies": [{"events": [2, 10]}]}
    specification = {
        "version": 1,
        "family": "binary",
        "workflow": "standard",
        "method": "binary.random",
        "metric": "OR",
        "parameters": {"confidence_level": 95.0},
    }
    with_style = saved_analysis.create_record(
        input_snapshot,
        specification,
        {"version": 1, "summary": {"estimate": 1.25}, "sections": []},
        status="partial",
        warnings=["One interval could not be estimated."],
        backend_versions={"R": "4.6.1", "RCMetaR": "0.4.1"},
        presentation={"forest_color": "#0000ff"},
    )

    assert with_style.value["input_identity"] == base.value["input_identity"]
    assert with_style.value["specification_identity"] == base.value["specification_identity"]
    assert with_style.value["presentation"] == {"forest_color": "#0000ff"}


def test_invalid_or_unknown_record_cannot_replace_or_overwrite_valid_project(
    tmp_path: Path,
):
    session = WorkspaceSession(load_project(SAMPLE))
    session.add_saved_analysis(_record())
    destination = tmp_path / "valid.rcms"
    session.save(destination)
    previous_bytes = destination.read_bytes()
    valid_document = load_project(destination)

    invalid_project = copy.deepcopy(valid_document.project)
    analyses = invalid_project["saved_analyses"]
    assert isinstance(analyses, list)
    record = analyses[0]
    assert isinstance(record, dict)
    specification = record["specification"]
    assert isinstance(specification, dict)
    specification["metric"] = "RR"
    with pytest.raises(ProjectFormatError, match="specification_identity"):
        save_project(
            destination,
            invalid_project,
            valid_document.state,
            assets=valid_document.assets,
        )
    assert destination.read_bytes() == previous_bytes

    invalid_archive = tmp_path / "unknown-record.rcms"
    _tamper_record_version(destination, invalid_archive)
    before = session.document
    runtime = session.runtime
    path = session.path
    with pytest.raises(ProjectFormatError, match="saved_analyses"):
        session.open(invalid_archive)
    assert session.document == before
    assert session.runtime is runtime
    assert session.path == path


def test_figure_size_hash_missing_reference_and_archive_path_are_rejected(
    tmp_path: Path,
):
    session = WorkspaceSession(load_project(SAMPLE))
    session.add_saved_analysis(_record())
    destination = tmp_path / "assets.rcms"
    session.save(destination)
    valid_bytes = destination.read_bytes()
    document = load_project(destination)

    with pytest.raises(ProjectFormatError, match="integrity check failed"):
        save_project(
            destination,
            document.project,
            document.state,
            assets={},
        )
    assert destination.read_bytes() == valid_bytes

    asset_name, payload = next(iter(document.assets.items()))
    corrupt_assets = {asset_name: payload[:-1] + b"x"}
    with pytest.raises(ProjectFormatError, match="integrity check failed"):
        save_project(
            destination,
            document.project,
            document.state,
            assets=corrupt_assets,
        )
    assert destination.read_bytes() == valid_bytes

    unverified_members = _archive_members(destination)
    unverified_members[asset_name] = payload[:-1] + b"x"
    unverified = tmp_path / "unverified-asset.rcms"
    _write_archive(unverified, unverified_members)
    with pytest.raises(ProjectFormatError, match="integrity digest mismatch"):
        load_project(unverified)

    members = _archive_members(destination)
    members[asset_name] = payload[:-1] + b"x"
    manifest = json.loads(members["manifest.json"])
    manifest["members"][asset_name] = {
        "sha256": hashlib.sha256(members[asset_name]).hexdigest(),
        "size": len(members[asset_name]),
    }
    members["manifest.json"] = _json_bytes(manifest)
    corrupted = tmp_path / "corrupted-asset.rcms"
    _write_archive(corrupted, members)
    with pytest.raises(ProjectFormatError, match="asset integrity check failed"):
        load_project(corrupted)

    missing_members = _archive_members(destination)
    del missing_members[asset_name]
    missing = tmp_path / "missing-asset.rcms"
    _write_archive(missing, missing_members)
    with pytest.raises(ProjectFormatError, match="integrity entries do not match"):
        load_project(missing)

    with pytest.raises(saved_analysis.SavedAnalysisError, match="4 MiB"):
        saved_analysis.create_record(
            input_snapshot={"study": 1},
            specification={"metric": "OR"},
            results={},
            status="complete",
            backend_versions={"R": "4.6.1"},
            figures=[
                saved_analysis.SavedFigureInput(
                    "large", "Large", "image/png", _PNG + b"x" * (4 * 1024 * 1024)
                )
            ],
        )

    members = _archive_members(destination)
    members["assets/../escaped.png"] = b"not an asset"
    unsafe = tmp_path / "unsafe.rcms"
    _write_archive(unsafe, members)
    with pytest.raises(ProjectFormatError, match="unsupported members"):
        load_project(unsafe)
