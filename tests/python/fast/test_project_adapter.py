from __future__ import annotations
import copy
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
