"""Real project boundaries for the Mean identifier and its legacy spellings."""

import copy
import hashlib
import json
import zipfile

import pytest

from rc_metastudio import project_adapter
from rc_metastudio.project_format import (
    ProjectDocument, ProjectFormatError, load_project, migrate_to_latest, save_project,
)
from tests.python.fast.test_project_format import (
    _first_sheet, _first_study, _group_project, _legacy_group_project, _legacy_state,
    _object, _objects,
)


ALIASES = ("TX Mean", "TXMean", "TX.Mean")
VALUES = {"est": 1.5, "lower": 1.1, "upper": 1.9, "SE": .2,
          "display_est": 1.5, "display_lower": 1.1, "display_upper": 1.9,
          "display_se": .2}


def _legacy_unit(project):
    source = _object(project["dataset"])
    return _objects(_objects(source["studies"])[0]["analysis_units"])[0]


def _document(version, metric):
    if version == 3:
        project = _group_project("continuous", "generic_effect", [["", "", ""], ["", "", ""]])
        sheet = _first_sheet(project)
        for index, arm in enumerate(_objects(sheet["arms"]), 1):
            arm["name"] = f"Tx {index}"
        sheet["settings"] = {"metric": metric, "metric_choices": [metric],
                             "analysis": {"parameters": {"measure": metric}},
                             "summary": {"effect": metric, "metric_choices": [metric]},
                             "axis_label": "Custom Tx Mean label"}
        _first_study(project)["entered_effects"] = [
            {"metric": metric, "arms": [_objects(sheet["arms"])[0]["id"]], "values": copy.deepcopy(VALUES)}
        ]
        state = {"schema_version": 3, "current_sheet_id": "sheet"}
    else:
        project = _legacy_group_project("continuous", "generic_effect", [["", "", ""], ["", "", ""]])
        project["schema_version"] = version
        source = _object(project["dataset"])
        for index, arm in enumerate(_objects(_legacy_unit(project)["groups"]), 1):
            arm["name"] = f"Tx {index}"
        source["summary"] = {"arms": "one", "data_type": "continuous", "sub_type": "generic_effect",
                             "effect": metric, "metric_choices": [metric], "name": "Outcome"}
        _legacy_unit(project)["entered_effects"] = {
            metric: {"Tx 1": copy.deepcopy(VALUES)}
        }
        state = _legacy_state()
        state.update(schema_version=version, active_outcome="Outcome", active_follow_up="first",
                     active_groups=["Tx 1", "Tx 2"], active_effect=metric)
    return project, state


def _archive(path, version, project, state):
    members = {name: json.dumps(value).encode("utf-8")
               for name, value in (("project.json", project), ("state.json", state))}
    manifest = {"format": "rc-metastudio-project", "format_version": version,
                "application": {"name": "RC MetaStudio", "version": "0.5.3"},
                "members": {name: {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                            for name, data in members.items()}}
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
        archive.writestr("manifest.json", json.dumps(manifest).encode("utf-8"))


@pytest.mark.parametrize("version", (1, 2, 3))
@pytest.mark.parametrize("metric", ("Mean", *ALIASES))
def test_mean_archive_migration_preserves_values_and_canonicalizes_resave(tmp_path, version, metric):
    project, state = _document(version, metric)
    original = copy.deepcopy((project, state))
    path = tmp_path / "legacy-mean.rcms"
    _archive(path, version, project, state)
    document = load_project(path)
    sheet = _first_sheet(document.project)
    settings = _object(sheet["settings"])
    assert settings["metric"] == "Mean"
    assert settings["metric_choices"] == ["Mean"]
    assert _object(settings["summary"])["effect"] == "Mean"
    entry = _objects(_first_study(document.project)["entered_effects"])[0]
    assert entry["metric"] == "Mean"
    assert entry["values"] == VALUES
    assert [arm["name"] for arm in _objects(sheet["arms"])] == ["Tx 1", "Tx 2"]
    save_project(path, document.project, document.state)
    assert load_project(path) == document
    assert migrate_to_latest(3, document.project, document.state) == (document.project, document.state)
    assert (project, state) == original


@pytest.mark.parametrize("metric", ALIASES)
def test_direct_mean_document_and_writer_use_canonical_metrics_without_mutating_input(tmp_path, metric):
    project, state = _document(3, metric)
    original = copy.deepcopy((project, state))
    runtime = project_adapter.document_to_runtime_project(ProjectDocument(3, project, state))
    sheet = runtime.dataset.sheets[0]
    unit = sheet.rows[0].analysis_unit
    assert unit.get_effect_for_source("entered", "Mean", (sheet.arms[0].id,)).standard_error == .2
    assert sheet.settings["metric"] == "Mean"
    assert sheet.settings["analysis"]["parameters"]["measure"] == "Mean"
    assert sheet.settings["axis_label"] == "Custom Tx Mean label"
    direct = project_adapter.project_to_dataset(project)
    assert direct.sheets[0].settings["metric"] == "Mean"
    path = tmp_path / "direct-save.rcms"
    save_project(path, project, state)
    assert _object(_first_sheet(load_project(path).project)["settings"])["metric"] == "Mean"
    assert (project, state) == original


@pytest.mark.parametrize("version", (1, 2, 3))
def test_alias_collision_is_rejected_without_overwriting_an_existing_project(tmp_path, version):
    good, good_state = _document(3, "Mean")
    destination = tmp_path / "preserved.rcms"
    save_project(destination, good, good_state)
    original = destination.read_bytes()
    project, state = _document(version, "Mean")
    if version == 3:
        entries = _objects(_first_study(project)["entered_effects"])
        conflicting = copy.deepcopy(entries[0])
        conflicting["metric"] = "TX Mean"
        _object(conflicting["values"])["est"] = 99.
        entries.append(conflicting)
        with pytest.raises(ProjectFormatError, match="duplicate|conflict"):
            save_project(destination, project, state)
    else:
        entries = _object(_legacy_unit(project)["entered_effects"])
        entries["TX Mean"] = {"Tx 1": dict(VALUES, est=99.)}
    source = tmp_path / "conflicting.rcms"
    _archive(source, version, project, state)
    with pytest.raises(ProjectFormatError, match="duplicate|conflict"):
        load_project(source)
    assert destination.read_bytes() == original
