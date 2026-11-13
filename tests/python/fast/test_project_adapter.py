from __future__ import annotations
import copy
from pathlib import Path
import pytest
from rc_metastudio import project_adapter
from rc_metastudio.project_format import ProjectDocument, migrate_to_latest, JsonObject, JsonValue
from rc_metastudio.workspace_session import WorkspaceSession
from tests.python.fast.test_project_format import _group_project, _legacy_state


def test_raw_values_added_to_omitted_arms_are_dirty_and_survive_reopen(tmp_path):
    from rc_metastudio.project_format import load_project
    from rc_metastudio.qt_object_guard import required

    project = _group_project("binary", None, [[1, 10], [2, 20]])
    project["sheets"][0]["rows"][0]["raw_data"] = {}
    document = ProjectDocument(3, project, dict(schema_version=3, current_sheet_id=project["sheets"][0]["id"]))
    session = WorkspaceSession(document)
    runtime = required(session.runtime, "workspace runtime")
    unit = runtime.dataset.sheets[0].rows[0].analysis_unit
    assert not project_adapter.dataset_to_project(runtime.dataset)["sheets"][0]["rows"][0]["raw_data"]
    for arm, cells in zip(unit.arms_by_id.values(), ([1, 10], [2, 20]), strict=True):
        arm.raw_data[:] = cells
    session.checkpoint()
    assert session.is_dirty and session.can_undo
    target = tmp_path / "new-raw.rcms"
    session.save(target)
    restored = project_adapter.document_to_runtime_project(load_project(target))
    assert [arm.raw_data for arm in restored.dataset.sheets[0].rows[0].analysis_unit.arms_by_id.values()] == [[1, 10], [2, 20]]


def _legacy_multi_arm_project(family: str) -> JsonObject:
    data_type = {"binary": 0, "continuous": 1}[family]
    subtype = {"binary": "proportions", "continuous": "means"}[family]
    raw_values: dict[str, list[JsonValue]] = {
        "binary": [[1, 10], [2, 20], [3, 30]],
        "continuous": [[10, 1.0, 0.5], [20, 2.0, 0.75], [30, 3.0, 1.0]],
    }
    return {
        "schema_version": 1,
        "dataset": {
            "analysis_family": family,
            "covariates": [],
            "is_diagnostic": False,
            "notes": "",
            "outcomes": [
                {
                    "data_type": data_type,
                    "follow_ups": ["first"],
                    "name": "Outcome",
                    "sub_type": subtype,
                }
            ],
            "studies": [
                {
                    "analysis_units": [
                        {
                            "entered_effects": {},
                            "follow_up": "first",
                            "groups": [
                                {
                                    "id": index,
                                    "name": f"Arm {index + 1}",
                                    "raw_data": raw,
                                }
                                for index, raw in enumerate(raw_values[family])
                            ],
                            "outcome": "Outcome",
                        }
                    ],
                    "covariates": {},
                    "id": 0,
                    "include": True,
                    "manually_excluded": False,
                    "name": "Study",
                    "notes": "",
                    "sample_size": None,
                    "year": 2026,
                }
            ],
            "summary": None,
            "title": "Adapter group contract",
        },
    }


def _multi_arm_project(family):
    raw = {"binary": [[1, 10], [2, 20], [3, 30]],
           "continuous": [[10, 1., .5], [20, 2., .75], [30, 3., 1.]]}[family]
    return _group_project(family, {"binary": "proportions", "continuous": "means"}[family], raw)


@pytest.mark.parametrize("family", ["binary", "continuous"])
def test_adapter_round_trip_preserves_every_multi_arm_group(family):
    project = _multi_arm_project(family)
    dataset = project_adapter.project_to_dataset(copy.deepcopy(project))
    assert project_adapter.dataset_to_project(dataset) == project
    assert list(dataset.sheets[0].rows[0].analysis_unit.arms) == ["Arm 1", "Arm 2", "Arm 3"]


def _identities(dataset):
    sheet = dataset.sheets[0]
    return sheet.id, tuple(row.id for row in sheet.rows), tuple(arm.id for arm in sheet.arms)


def test_adapter_reconstructs_sheet_row_and_arm_identities_across_reopen():
    dataset = project_adapter.project_to_dataset(_multi_arm_project("binary"))
    reopened = project_adapter.project_to_dataset(project_adapter.dataset_to_project(dataset))
    assert _identities(reopened) == _identities(dataset)
    assert reopened.sheets[0].rows[0].analysis_unit.sheet is reopened.sheets[0]
    assert tuple(reopened.sheets[0].rows[0].analysis_unit.arms_by_id) == tuple(a.id for a in reopened.sheets[0].arms)


def test_entered_effect_edits_survive_history_and_save(tmp_path):
    project = _multi_arm_project("continuous")
    sheet = project["sheets"][0]
    sheet["sub_type"] = "generic_effect"
    sheet["rows"][0]["raw_data"] = {arm["id"]: ["", "", ""] for arm in sheet["arms"]}
    state = {"schema_version": 3, "current_sheet_id": sheet["id"]}
    session = WorkspaceSession(ProjectDocument(3, project, state))
    runtime = session.runtime
    assert runtime is not None
    unit = runtime.dataset.sheets[0].rows[0].analysis_unit
    key = (sheet["arms"][0]["id"],)
    unit.set_effect_for_source("entered", "Mean", key, 1.5, None, None)
    session.checkpoint()
    assert session.is_dirty and session.can_undo
    unit.set_effect_for_source("entered", "Mean", key, 1.5, None, None, .2)
    session.checkpoint()
    runtime.dataset.sheets[0].rows[0].include = False
    session.checkpoint()
    assert session.undo()
    assert session.runtime is not None
    restored = session.runtime.dataset.sheets[0].rows[0].analysis_unit
    assert restored.get_effect_for_source("entered", "Mean", key).standard_error == .2
    assert session.undo()
    assert session.runtime is not None
    restored = session.runtime.dataset.sheets[0].rows[0].analysis_unit
    effect = restored.get_effect_for_source("entered", "Mean", key)
    assert effect.estimate == 1.5 and effect.standard_error is None
    assert session.redo()
    destination = tmp_path / "entered.rcms"
    session.save(destination)
    reopened = WorkspaceSession()
    reopened.open(destination)
    assert reopened.runtime is not None
    effect = reopened.runtime.dataset.sheets[0].rows[0].analysis_unit.get_effect_for_source("entered", "Mean", key)
    assert effect.estimate == 1.5 and effect.standard_error == .2


def test_reader_derives_repeatable_sheet_identities_for_legacy_projects():
    project = _legacy_multi_arm_project("binary")
    first, _ = migrate_to_latest(1, copy.deepcopy(project), _legacy_state())
    second, _ = migrate_to_latest(1, copy.deepcopy(project), _legacy_state())
    assert _identities(project_adapter.project_to_dataset(first)) == _identities(project_adapter.project_to_dataset(second))


def test_document_to_runtime_project_reconstructs_state_and_selection():
    project = _multi_arm_project("binary")
    project["sheets"][0]["settings"] = {"metric": "OR", "confidence_level": 95., "arms": ["arm:0", "arm:1"]}
    state: JsonObject = {"schema_version": 3, "current_sheet_id": "sheet"}
    runtime = project_adapter.document_to_runtime_project(ProjectDocument(3, project, state))
    assert isinstance(runtime, project_adapter.RuntimeProject)
    assert [s.name for s in runtime.dataset.sheets] == ["Outcome"]
    assert runtime.model_state == {"current_sheet_id": "sheet"}
    assert runtime.dataset.sheets[0].settings == project["sheets"][0]["settings"]
    assert runtime.restored_active_sheet is True



def test_storage_boundary_revman_iv_subgroups_reopen(tmp_path):
    import xml.etree.ElementTree as ET
    from rc_metastudio.rm5_import import read_rm5
    from rc_metastudio.project_format import save_project, load_project
    root = ET.parse(Path(__file__).parents[2] / "fixtures/rm5/generic-derived.rm5")
    for outcome in root.iter("IV_OUTCOME"):
        outcome.set("SUBGROUPS", "YES")
        for i, record in enumerate(list(outcome.findall("IV_DATA"))):
            outcome.remove(record)
            group = ET.SubElement(outcome, "IV_SUBGROUP", NO=str(i + 1), ID=f"group-{i + 1}")
            label = f"Region {i}"
            ET.SubElement(group, "NAME").text = label
            group.append(record)
    source = tmp_path / "subgroups.rm5"
    root.write(source)
    dataset = read_rm5(source).dataset
    for sheet in dataset.sheets:
        cov_id = sheet.covariates[0]["id"]
        assert [r.covariate_values.get(cov_id) for r in sheet.rows] == ["Region 0", "Region 1", "Region 2"]
    project = project_adapter.dataset_to_project(dataset)
    state = dict(schema_version=3, current_sheet_id=dataset.sheets[0].id)
    path = tmp_path / "import.rcms"
    save_project(path, project, state)
    assert project_adapter.dataset_to_project(project_adapter.document_to_runtime_project(load_project(path)).dataset) == project
