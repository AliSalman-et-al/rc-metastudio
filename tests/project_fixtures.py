"""Portable project fixtures shared by archive and workspace tests."""

from copy import deepcopy
from typing import cast

from rc_metastudio.project.archive import CURRENT_FORMAT_VERSION, JsonObject, JsonValue


def legacy_group_project(
    family: str, subtype: str | None, raw_values: list[list[JsonValue]]
) -> JsonObject:
    data_type = {"binary": 0, "continuous": 1, "diagnostic": 2}[family]
    return {
        "schema_version": 1,
        "dataset": {
            "analysis_family": family,
            "covariates": [],
            "is_diagnostic": family == "diagnostic",
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
                                for index, raw in enumerate(raw_values)
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
            "title": "Group contract",
        },
    }


def group_project(family, subtype, raw_values):
    arms = [{"id": f"arm:{i}", "name": f"Arm {i + 1}"} for i in range(len(raw_values))]
    return {"schema_version": CURRENT_FORMAT_VERSION, "title": "Group contract", "notes": "",
            "sheets": [{"id": "sheet", "name": "Outcome", "family": family,
                        "data_type": {"binary": 0, "continuous": 1, "diagnostic": 2}[family],
                        "sub_type": subtype, "arms": arms, "settings": {}, "covariates": [],
                        "rows": [{"id": "row", "label": "Study", "year": 2026,
                                  "sample_size": None, "include": True, "manually_excluded": False,
                                  "notes": "", "covariates": {}, "entered_effects": [], "ratio_inputs": [],
                                  "raw_data": {arm["id"]: raw for arm, raw in zip(arms, raw_values)}}]}]}


def legacy_state():
    return {"schema_version": 1, "active_outcome": None, "active_follow_up": None,
            "active_groups": [], "active_effect": None, "confidence_level": 95.0}


def first_sheet(project):
    return object_records(project["sheets"])[0]


def object_record(value: JsonValue) -> JsonObject:
    """Narrow a JSON value at a test mutation/read boundary."""

    if not isinstance(value, dict):
        raise AssertionError("expected JSON object")
    return value


def object_records(value: JsonValue) -> list[JsonObject]:
    """Narrow a JSON array whose members are objects."""

    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise AssertionError("expected JSON object array")
    return cast(list[JsonObject], value)


def first_study(project: JsonObject) -> JsonObject:
    return object_records(first_sheet(project)["rows"])[0]


_MULTI_ARM_VALUES: dict[str, list[list[JsonValue]]] = {
    "binary": [[1, 10], [2, 20], [3, 30]],
    "continuous": [[10, 1.0, 0.5], [20, 2.0, 0.75], [30, 3.0, 1.0]],
}
_MULTI_ARM_SUBTYPES = {"binary": "proportions", "continuous": "means"}


def legacy_multi_arm_project(family: str) -> JsonObject:
    project = legacy_group_project(family, _MULTI_ARM_SUBTYPES[family], deepcopy(_MULTI_ARM_VALUES[family]))
    object_record(project["dataset"])["title"] = "Adapter group contract"
    return project


def multi_arm_project(family: str):
    return group_project(family, _MULTI_ARM_SUBTYPES[family], deepcopy(_MULTI_ARM_VALUES[family]))
