# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass

from rc_metastudio.workspace_editing import WorkspaceEditingService
from rc_metastudio.workspace_editing import WorkspaceEditingContext, WorkspaceEditTarget
from rc_metastudio.analysis_dataset import Dataset, Study as DomainStudy


class FakeBridge:
    def get_confidence_multiplier_from_r(self, confidence_level):
        return 1.96

    def set_confidence_level(self, confidence_level):
        return None

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


@dataclass
class Study:
    include: bool = False
    manually_excluded: bool = False


def test_study_rename_normalizes_and_rejects_blank_or_duplicate_names():
    dataset = Dataset()
    dataset.add_study(DomainStudy(1, name="Alpha"))
    dataset.add_study(DomainStudy(2, name="Beta"))
    context = WorkspaceEditingContext(
        outcome_name=None,
        follow_up_name=None,
        current_groups=(),
        current_effect=None,
        data_type=None,
        outcome_subtype=None,
        group_comparison="",
        raw_columns=(),
        outcome_columns=(),
        include_column=0,
        name_column=1,
        year_column=2,
        confidence_level=95.0,
        confidence_multiplier=1.96,
    )
    service = WorkspaceEditingService(FakeBridge())

    normalized = service.apply_edit(
        dataset, WorkspaceEditTarget(0, 1, "Alpha"), context, "  Renamed  "
    )
    duplicate = service.apply_edit(
        dataset, WorkspaceEditTarget(0, 1, "Renamed"), context, " Beta "
    )
    blank = service.apply_edit(
        dataset, WorkspaceEditTarget(0, 1, "Renamed"), context, " \t "
    )

    assert normalized.applied is True
    assert dataset.studies[0].name == "Renamed"
    assert duplicate.error == "Duplicate study names not allowed"
    assert blank.error == "Study names cannot be empty."


def test_new_study_rejects_whitespace_name_without_mutating_dataset():
    dataset = Dataset()
    context = WorkspaceEditingContext(
        outcome_name=None,
        follow_up_name=None,
        current_groups=(),
        current_effect=None,
        data_type=None,
        outcome_subtype=None,
        group_comparison="",
        raw_columns=(),
        outcome_columns=(),
        include_column=0,
        name_column=1,
        year_column=2,
        confidence_level=95.0,
        confidence_multiplier=1.96,
    )

    result = WorkspaceEditingService(FakeBridge()).apply_edit(
        dataset, WorkspaceEditTarget(0, 1, ""), context, "   "
    )

    assert result.error == "Study names cannot be empty."
    assert len(dataset.studies) == 0
