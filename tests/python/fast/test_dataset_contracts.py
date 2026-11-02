"""Isolation and stable-arm contracts for sheet-owned rows."""
from rc_metastudio.project_domain import RowId, SheetId
import copy

from rc_metastudio.analysis_dataset import Dataset, Sheet, StudyRow
from rc_metastudio.analysis_unit import AnalysisUnit
from rc_metastudio.meta_globals import BINARY


def _dataset():
    sheet = Sheet(SheetId("sheet"), "Outcome", BINARY, covariates=[{"name": "Region", "type": "factor"}])
    unit = AnalysisUnit(sheet, arm_names=["Usual-care", "Treatment"], arm_stable_ids=["control", "treatment"])
    unit.set_raw_data_for_arm("Usual-care", [3, 10])
    unit.set_effect_for_source("entered", "OR", ("control", "treatment"), .75)
    sheet.rows.append(StudyRow(RowId("row"), "Study 1", unit, covariate_values={"Region": "north"}))
    return Dataset(title="Contract dataset", notes="dataset notes", sheets=[sheet])


def test_copy_preserves_and_isolates_the_complete_dataset_graph():
    source = _dataset()
    cloned = copy.deepcopy(source)
    assert cloned.title == source.title
    assert cloned.notes == source.notes
    assert cloned.sheets[0].covariates == source.sheets[0].covariates
    assert cloned is not source
    sheet = cloned.sheets[0]
    assert sheet.rows[0].analysis_unit.sheet is sheet
    cloned.title = "changed"
    cloned.notes = "changed"
    sheet.settings["metric"] = "RR"
    sheet.covariates[0]["name"] = "Changed region"
    sheet.rows[0].label = "Changed study"
    sheet.rows[0].covariate_values["Region"] = "south"
    sheet.rows[0].analysis_unit.set_raw_data_for_arm("Usual-care", [99, 100])
    sheet.rows[0].analysis_unit.set_effect_for_source("entered", "OR", ("control", "treatment"), .2)
    original = source.sheets[0]
    assert source.title == "Contract dataset"
    assert source.notes == "dataset notes"
    assert original.settings == {}
    assert original.covariates[0]["name"] == "Region"
    assert original.rows[0].label == "Study 1"
    assert original.rows[0].covariate_values == {"Region": "north"}
    assert original.rows[0].analysis_unit.get_raw_data_for_arm("Usual-care") == [3, 10]
    assert original.rows[0].analysis_unit.get_effect_for_source("entered", "OR", ("control", "treatment")).estimate == .75


def test_rename_arm_preserves_effects_when_the_name_contains_a_hyphen():
    unit = _dataset().sheets[0].rows[0].analysis_unit
    unit.rename_arm("Usual-care", "Standard care")
    assert list(unit.arms) == ["Standard care", "Treatment"]
    assert unit.get_effect_for_source("entered", "OR", ("control", "treatment")).estimate == .75
    assert "Usual-care" not in unit.arms
