"""Isolation and stable-arm contracts for sheet-owned rows."""
from rc_metastudio.domain_ids import ArmId, RowId, SheetId

from rc_metastudio.project.model import Arm, Dataset, Sheet, StudyRow
from rc_metastudio.project.study import AnalysisUnit
from rc_metastudio.analysis.catalog import BINARY


def _dataset():
    sheet = Sheet(
        SheetId("sheet"), "Outcome", BINARY,
        arms=[Arm(ArmId("control"), "Usual-care"), Arm(ArmId("treatment"), "Treatment")],
        covariates=[{"name": "Region", "type": "factor"}],
    )
    unit = AnalysisUnit(sheet)
    unit.set_raw_data_for_arm("Usual-care", [3, 10])
    unit.set_effect_for_source("entered", "OR", ("control", "treatment"), .75)
    sheet.rows.append(StudyRow(RowId("row"), "Study 1", unit, covariate_values={"Region": "north"}))
    return Dataset(title="Contract dataset", notes="dataset notes", sheets=[sheet])


def test_rename_arm_preserves_effects_when_the_name_contains_a_hyphen():
    sheet = _dataset().sheets[0]
    unit = sheet.rows[0].analysis_unit
    sheet.arms[0].name = "Standard care"
    assert list(unit.arms) == ["Standard care", "Treatment"]
    assert unit.get_effect_for_source("entered", "OR", ("control", "treatment")).estimate == .75
    assert "Usual-care" not in unit.arms
