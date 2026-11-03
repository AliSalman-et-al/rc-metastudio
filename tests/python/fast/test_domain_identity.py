from rc_metastudio.project_domain import ArmId, RowId, SheetId
# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
from rc_metastudio import analysis_dataset, meta_globals
from rc_metastudio.analysis_unit import AnalysisUnit


def test_editable_labels_do_not_change_domain_identities():
    arm = analysis_dataset.Arm(ArmId("arm"), "Intervention")
    sheet = analysis_dataset.Sheet(SheetId("sheet"), "Outcome", meta_globals.CONTINUOUS, arms=[arm])
    unit = AnalysisUnit(sheet, arm_names=[arm.name], arm_stable_ids=[arm.id])
    row = analysis_dataset.StudyRow(RowId("row"), "Study", unit)
    sheet.rows.append(row)
    dataset = analysis_dataset.Dataset(sheets=[sheet])
    unit_id = unit.stable_id
    sheet.name = "Renamed outcome"
    row.label = "Renamed study"
    unit.rename_arm(arm.name, "Renamed arm")
    arm.name = "Renamed arm"
    assert dataset.sheet(SheetId("sheet")) is sheet
    assert sheet.rows[0] is row and row.id == "row"
    assert row.analysis_unit is unit and unit.stable_id == unit_id
    assert unit.sheet is sheet
    assert unit.arms_by_id["arm"] is unit.arms["Renamed arm"]


def _unit():
    sheet = analysis_dataset.Sheet(SheetId("sheet"), "Outcome", meta_globals.CONTINUOUS)
    return AnalysisUnit(sheet, arm_names=["group 1"], arm_stable_ids=["arm"])


def test_effect_authority_is_explicit_and_preview_is_not_entered_data():
    unit = _unit()
    key = ("arm",)
    unit.set_effect_for_source("entered", "TX Mean", key, 1.0, 0.5, 1.5)
    unit.set_effect_for_source("derived_preview", "TX Mean", key, 2.0, 1.5, 2.5)
    assert unit.get_effect_for_source("entered", "TX Mean", key).estimate == 1.0
    assert unit.get_effect_for_source("derived_preview", "TX Mean", key).estimate == 2.0
    assert unit.get_entered_effect_and_ci("TX Mean", key) == (1.0, 0.5, 1.5)


def test_arm_rename_preserves_each_effect_authority_store():
    unit = _unit()
    key = ("arm",)
    for source, estimate in (("entered", 1.0), ("derived_preview", 2.0), ("analysis", 3.0)):
        unit.set_effect_for_source(source, "TX Mean", key, estimate, .5, 4.0)
    unit.rename_arm("group 1", "renamed-arm")
    assert "group 1" not in unit.arms
    assert unit.arms["renamed-arm"].stable_id == "arm"
    for source, estimate in (("entered", 1.0), ("derived_preview", 2.0), ("analysis", 3.0)):
        assert unit.get_effect_for_source(source, "TX Mean", key).estimate == estimate
        assert set(unit._store(source)["TX Mean"]) == {key}


def test_calculated_effects_are_published_as_previews():
    unit = _unit()
    key = ("arm",)
    unit.set_effect("TX Mean", key, 1.0)
    unit.set_effect_and_ci("TX Mean", key, 2.0, 1.5, 2.5, 1.96)
    assert unit.get_effect_for_source("entered", "TX Mean", key).estimate == 1.0
    assert unit.get_effect_for_source("derived_preview", "TX Mean", key).estimate == 2.0
    assert unit.get_estimate_for_source("derived_preview", "TX Mean", key) == 2.0


def test_entered_edit_does_not_hide_which_source_a_preview_belongs_to():
    unit = _unit()
    key = ("arm",)
    unit.set_effect_and_ci("TX Mean", key, 2.0, 1.5, 2.5, 1.96)
    unit.set_effect("TX Mean", key, 3.0)
    assert unit.get_effect_for_source("entered", "TX Mean", key).estimate == 3.0
    assert unit.get_effect_for_source("derived_preview", "TX Mean", key).estimate == 2.0
