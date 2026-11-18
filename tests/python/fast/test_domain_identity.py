# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
from rc_metastudio import analysis_dataset, analysis_catalog
from rc_metastudio.domain_ids import SheetId
from rc_metastudio.analysis_unit import AnalysisUnit


def _unit():
    sheet = analysis_dataset.Sheet(SheetId("sheet"), "Outcome", analysis_catalog.CONTINUOUS)
    return AnalysisUnit(sheet, arm_names=["group 1"], arm_stable_ids=["arm"])


def test_entered_edit_does_not_hide_which_source_a_preview_belongs_to():
    unit = _unit()
    key = ("arm",)
    unit.set_derived_effect_preview("Mean", key, 2.0, 1.5, 2.5, 1.96)
    unit.set_effect("Mean", key, 3.0)
    assert unit.get_effect_for_source("entered", "Mean", key).estimate == 3.0
    assert unit.get_effect_for_source("derived_preview", "Mean", key).estimate == 2.0
