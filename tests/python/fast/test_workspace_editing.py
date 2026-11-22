from rc_metastudio.domain_ids import RowId, SheetId
# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from rc_metastudio.workspace.editing import WorkspaceEditingService
from rc_metastudio.workspace.editing import WorkspaceEditingContext
from rc_metastudio.project.model import Dataset, Sheet, StudyRow
from rc_metastudio.project.study import AnalysisUnit


class FakeBridge:
    def effect_for_study(self, *args, **kwargs):
        return {"calc_scale": 0.5}

    def effect_triplet(self, value, scale, *, metric):
        return (value[scale], None, None)

    def binary_convert_scale(self, value, effect, *, convert_to, n1=None):
        return value

    continuous_convert_scale = binary_convert_scale
    diagnostic_convert_scale = binary_convert_scale
    continuous_effect_for_study = effect_for_study
    diagnostic_effects_for_study = effect_for_study


def test_single_arm_binary_preview_needs_no_fabricated_control():
    # A valid single-arm row must calculate without inventing control values;
    # comparative metrics still require their complete second arm.
    from rc_metastudio.analysis.study_selection import calculate_raw_effects

    result, sample_size = calculate_raw_effects(FakeBridge(), 0, "PLO", [4, 20], 95)
    assert result == (0.5, None, None)
    assert sample_size == 20


def test_study_rename_normalizes_and_rejects_blank_or_duplicate_names():
    dataset = Dataset()
    sheet = Sheet(SheetId("sheet"), "Outcome", 0)
    dataset.sheets.append(sheet)
    sheet.rows.extend(StudyRow(RowId(str(i)), name, AnalysisUnit(sheet)) for i, name in enumerate(("Alpha", "Beta")))
    context = WorkspaceEditingContext(
        sheet_id=SheetId("sheet"),
        arm_names=(),
        current_effect=None,
        data_type=None,
        outcome_subtype=None,
        arm_key=(),
        confidence_level=95.0,
        confidence_multiplier=1.96,
    )
    service = WorkspaceEditingService(FakeBridge())

    normalized = service.apply_edit(
        dataset, 0, "name", context, "  Renamed  "
    )
    duplicate = service.apply_edit(
        dataset, 0, "name", context, " Beta "
    )
    blank = service.apply_edit(
        dataset, 0, "name", context, " \t "
    )

    assert normalized is None
    assert dataset.sheets[0].rows[0].label == "Renamed"
    assert duplicate is not None and duplicate.message == "Study 'Beta' with no year already exists in row 2."
    assert blank is not None and blank.message == "Study names cannot be empty."


def test_new_study_rejects_whitespace_name_without_mutating_dataset():
    dataset = Dataset(sheets=[Sheet(SheetId("sheet"), "Outcome", 0)])
    context = WorkspaceEditingContext(
        sheet_id=SheetId("sheet"),
        arm_names=(),
        current_effect=None,
        data_type=None,
        outcome_subtype=None,
        arm_key=(),
        confidence_level=95.0,
        confidence_multiplier=1.96,
    )

    result = WorkspaceEditingService(FakeBridge()).apply_edit(
        dataset, 0, "name", context, "   "
    )

    assert result is not None and result.message == "Study names cannot be empty."
    assert len(dataset.sheets[0].rows) == 0
