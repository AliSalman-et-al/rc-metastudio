from rc_metastudio.domain_ids import ArmId, RowId, SheetId
# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from rc_metastudio import r_operations, r_runtime
from rc_metastudio.analysis.catalog import BINARY
from rc_metastudio.workspace.editing import ConfidenceSettings, WorkspaceEditingContext, WorkspaceEditingService
from rc_metastudio.project.model import Arm, Dataset, Sheet, StudyRow
from rc_metastudio.project.study import AnalysisUnit


def test_single_arm_binary_preview_needs_no_fabricated_control(monkeypatch):
    arm = Arm(ArmId("reported"), "Treatment")
    sheet = Sheet(SheetId("sheet"), "Outcome", BINARY, arms=[arm])
    row = StudyRow(RowId("row"), "Study", AnalysisUnit(sheet, raw_data=[[4, 20]]))
    context = WorkspaceEditingContext.for_sheet(sheet, "PLO", ConfidenceSettings(95, 1.96))
    monkeypatch.setattr(r_runtime, "is_ready", lambda: True)

    def preview(rows, family, metric, metrics, confidence):
        assert [list(raw) for raw in rows] == [[4, 20]]
        assert (family, metric, tuple(metrics), confidence) == ("binary", "PLO", ("PLO",), 95)
        return [[(.5, .1, .9, .6, .2, 1.0)]]

    monkeypatch.setattr(r_operations, "study_effect_previews", preview)
    WorkspaceEditingService().update_effect_previews((row,), context, update_inclusion=True)
    assert row.analysis_unit.get_effect_for_source("derived_preview", "PLO", (arm.id,)).estimate == .5
    assert row.analysis_unit.get_display_effect_for_source("derived_preview", "PLO", (arm.id,)) == .6


def test_study_rename_normalizes_and_rejects_blank_or_duplicate_names():
    dataset = Dataset()
    sheet = Sheet(SheetId("sheet"), "Outcome", 0)
    dataset.sheets.append(sheet)
    sheet.rows.extend(StudyRow(RowId(str(i)), name, AnalysisUnit(sheet)) for i, name in enumerate(("Alpha", "Beta")))
    context = WorkspaceEditingContext(
        arm_names=(),
        current_effect=None,
        data_type=None,
        outcome_subtype=None,
        arm_key=(),
        confidence_level=95.0,
        confidence_multiplier=1.96,
    )
    service = WorkspaceEditingService()

    normalized = service.apply_edit(
        dataset.sheets[0], 0, "name", context, "  Renamed  "
    )
    duplicate = service.apply_edit(
        dataset.sheets[0], 0, "name", context, " Beta "
    )
    blank = service.apply_edit(
        dataset.sheets[0], 0, "name", context, " \t "
    )

    assert normalized is None
    assert dataset.sheets[0].rows[0].label == "Renamed"
    assert duplicate is not None and duplicate.message == "Study 'Beta' with no year already exists in row 2."
    assert blank is not None and blank.message == "Study names cannot be empty."


def test_new_study_rejects_whitespace_name_without_mutating_dataset():
    dataset = Dataset(sheets=[Sheet(SheetId("sheet"), "Outcome", 0)])
    context = WorkspaceEditingContext(
        arm_names=(),
        current_effect=None,
        data_type=None,
        outcome_subtype=None,
        arm_key=(),
        confidence_level=95.0,
        confidence_multiplier=1.96,
    )

    result = WorkspaceEditingService().apply_edit(
        dataset.sheets[0], 0, "name", context, "   "
    )

    assert result is not None and result.message == "Study names cannot be empty."
    assert len(dataset.sheets[0].rows) == 0
