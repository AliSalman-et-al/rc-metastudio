# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from rc_metastudio import analysis_dataset, meta_globals
from rc_metastudio.analysis_snapshot import freeze_binary_input
from rc_metastudio.continuous_analysis_snapshot import freeze_continuous_input
from rc_metastudio.cumulative_analysis import CumulativeOrderSpec, freeze_cumulative_input
from rc_metastudio.dataset_table_model import DatasetTableModel
from rc_metastudio.diagnostic_analysis_snapshot import freeze_diagnostic_input
from rc_metastudio.meta_regression_analysis import (
    MetaRegressionCovariateInput,
    freeze_meta_regression_input,
)
from rc_metastudio.publication_bias import SmallStudyEffectsRequest
from rc_metastudio.reitsma_analysis import freeze_reitsma_input
from rc_metastudio.saved_analysis import input_snapshot_identity
from rc_metastudio.saved_analysis_freshness import saved_input_matches_current_data
from rc_metastudio.small_study_effects_core import freeze_small_study_effects_input


def _binary_model(*, extra_context=False):
    dataset = analysis_dataset.Dataset("Freshness")
    studies = [
        analysis_dataset.Study(1, name="Alpha", year=2010),
        analysis_dataset.Study(2, name="Beta", year=2020),
    ]
    for study in studies:
        dataset.add_study(study)
    dataset.add_outcome(
        analysis_dataset.Outcome("Mortality", meta_globals.BINARY, sub_type="proportions")
    )
    dataset.add_follow_up_to_outcome("Mortality", "12 months")
    for study, counts in zip(studies, (([5, 20], [10, 25]), ([2, 18], [7, 24])), strict=True):
        study.get_analysis_unit("Mortality", "first").set_raw_data_for_groups(
            meta_globals.DEFAULT_GROUP_NAMES, counts
        )
        study.get_analysis_unit("Mortality", "12 months").set_raw_data_for_groups(
            meta_globals.DEFAULT_GROUP_NAMES, counts
        )
    dataset.add_covariate(
        analysis_dataset.Covariate("Age", "continuous"),
        {"Alpha": 45.0, "Beta": 61.0},
    )
    if extra_context:
        dataset.add_outcome(
            analysis_dataset.Outcome("Readmission", meta_globals.BINARY, sub_type="proportions")
        )
        dataset.add_follow_up_to_outcome("Readmission", "6 months")
        dataset.add_group("Placebo", "Readmission")
        for study in studies:
            study.get_analysis_unit("Readmission", "first").set_raw_data_for_groups(
                meta_globals.DEFAULT_GROUP_NAMES + ["Placebo"],
                [[4, 20], [8, 25], [3, 15]],
            )
            study.get_analysis_unit("Readmission", "6 months").set_raw_data_for_groups(
                meta_globals.DEFAULT_GROUP_NAMES + ["Placebo"],
                [[2, 20], [5, 25], [1, 15]],
            )
    model = DatasetTableModel(dataset=dataset, add_blank_study=False)
    model.set_current_outcome("Mortality")
    model.set_current_follow_up("first")
    model.set_current_groups(meta_globals.DEFAULT_GROUP_NAMES)
    model.current_effect = "OR"
    return model


def _diagnostic_model():
    dataset = analysis_dataset.Dataset("Diagnostic", is_diagnostic=True)
    for study in (
        analysis_dataset.Study(1, name="Alpha", year=2010),
        analysis_dataset.Study(2, name="Beta", year=2020),
    ):
        dataset.add_study(study)
    dataset.add_outcome(analysis_dataset.Outcome("Disease", meta_globals.DIAGNOSTIC))
    for study, counts in zip(
        dataset.studies, ([8, 2, 3, 17], [7, 3, 4, 16]), strict=True
    ):
        study.get_analysis_unit("Disease", "first").set_raw_data_for_groups(
            ["test 1"], [counts]
        )
    dataset.add_covariate(
        analysis_dataset.Covariate("Dose", "continuous"),
        {"Alpha": 1.0, "Beta": 2.0},
    )
    model = DatasetTableModel(dataset=dataset, add_blank_study=False)
    model.set_current_outcome("Disease")
    model.set_current_follow_up("first")
    model.current_groups = ["test 1"]
    model.current_effect = "Sens"
    return model


def _continuous_model():
    dataset = analysis_dataset.Dataset("Continuous")
    for study in (
        analysis_dataset.Study(1, name="Alpha", year=2010),
        analysis_dataset.Study(2, name="Beta", year=2020),
    ):
        dataset.add_study(study)
    dataset.add_outcome(analysis_dataset.Outcome("Weight", meta_globals.CONTINUOUS))
    for study, arms in zip(
        dataset.studies,
        (([30, 70.0, 8.0], [29, 72.0, 9.0]), ([25, 68.0, 7.0], [24, 71.0, 8.0])),
        strict=True,
    ):
        study.get_analysis_unit("Weight", "first").set_raw_data_for_groups(
            meta_globals.DEFAULT_GROUP_NAMES, arms
        )
    model = DatasetTableModel(dataset=dataset, add_blank_study=False)
    model.set_current_outcome("Weight")
    model.set_current_follow_up("first")
    model.set_current_groups(meta_globals.DEFAULT_GROUP_NAMES)
    model.current_effect = "SMD"
    return model


def _record(snapshot, specification):
    snapshot_mapping = snapshot.to_mapping()
    return {
        "input_snapshot": snapshot_mapping,
        "input_identity": input_snapshot_identity(snapshot_mapping),
        "specification": specification,
    }


def test_binary_match_uses_saved_selectors_without_mutating_current_selection():
    model = _binary_model(extra_context=True)
    snapshot = freeze_binary_input(model)
    record = _record(
        snapshot,
        {"data_type": "binary", "workflow": "standard", "metric": "OR"},
    )
    model.set_current_outcome("Readmission")
    model.set_current_follow_up("6 months")
    model.set_current_groups(["Placebo", "tx B"])
    model.current_effect = "RR"
    active_selection = (
        model.current_outcome_name,
        model.get_current_follow_up_name(),
        tuple(model.current_groups),
        model.current_effect,
    )

    assert saved_input_matches_current_data(model, record) is True
    assert (
        model.current_outcome_name,
        model.get_current_follow_up_name(),
        tuple(model.current_groups),
        model.current_effect,
    ) == active_selection


def test_changed_input_and_deleted_saved_context_are_detected():
    model = _binary_model()
    record = _record(
        freeze_binary_input(model),
        {"data_type": "binary", "workflow": "standard", "metric": "OR"},
    )
    model.dataset.studies[0].get_analysis_unit("Mortality", "first").get_raw_data_for_group(
        "tx A"
    )[0] = 6
    assert saved_input_matches_current_data(model, record) is False

    model.dataset.remove_outcome("Mortality")
    assert saved_input_matches_current_data(model, record) is False


def test_unknown_or_legacy_snapshot_is_not_reported_as_changed():
    model = _binary_model()
    snapshot = freeze_binary_input(model).to_mapping()
    assert saved_input_matches_current_data(
        model,
        {"input_snapshot": snapshot, "specification": {"workflow": "future"}},
    ) is None
    assert saved_input_matches_current_data(
        model,
        {"input_snapshot": snapshot, "specification": {"data_type": "binary"}},
    ) is None


def test_continuous_snapshot_matches_current_raw_measurements():
    model = _continuous_model()
    record = _record(
        freeze_continuous_input(model),
        {"data_type": "continuous", "workflow": "standard", "metric": "SMD"},
    )
    assert saved_input_matches_current_data(model, record) is True


def test_diagnostic_and_reitsma_snapshots_are_compared_with_their_saved_context():
    model = _diagnostic_model()
    diagnostic = freeze_diagnostic_input(model)
    assert saved_input_matches_current_data(
        model,
        _record(
            diagnostic,
            {"data_type": "diagnostic", "workflow": "standard", "metric": "Sens"},
        ),
    ) is True
    assert saved_input_matches_current_data(
        model,
        _record(
            freeze_reitsma_input(model),
            {"data_type": "diagnostic", "method": "diagnostic.reitsma"},
        ),
    ) is True


def test_reitsma_meta_regression_uses_meta_regression_snapshot_and_moderators():
    model = _diagnostic_model()
    moderator = MetaRegressionCovariateInput(
        "Dose", "continuous", (1.0, 2.0), unit="mg"
    )
    snapshot = freeze_meta_regression_input(model, (moderator,))
    record = _record(
        snapshot,
        {
            "data_type": "diagnostic",
            "method": "diagnostic.reitsma",
            "workflow": "meta-regression",
        },
    )

    assert saved_input_matches_current_data(model, record) is True
    model.dataset.studies[0].set_covariate_value(model.dataset.get_covariate("Dose"), 3.0)
    assert saved_input_matches_current_data(model, record) is False


def test_cumulative_subgroup_meta_regression_and_small_study_inputs_are_compared():
    model = _binary_model()
    base = freeze_binary_input(model)
    cumulative = freeze_cumulative_input(
        base, CumulativeOrderSpec("project_order", "ascending")
    )
    assert saved_input_matches_current_data(
        model,
        _record(
            cumulative,
            {"data_type": "binary", "workflow": "cumulative", "metric": "OR"},
        ),
    ) is True
    assert saved_input_matches_current_data(
        model,
        _record(
            base,
            {"data_type": "binary", "workflow": "subgroup", "metric": "OR"},
        ),
    ) is True

    moderator = MetaRegressionCovariateInput("Age", "continuous", (), "years")
    meta_regression = freeze_meta_regression_input(model, (moderator,))
    assert saved_input_matches_current_data(
        model,
        _record(
            meta_regression,
            {"data_type": "binary", "workflow": "meta-regression"},
        ),
    ) is True

    request = SmallStudyEffectsRequest.create(data_type="binary", metric="OR")
    small_study = freeze_small_study_effects_input(model, request)
    assert saved_input_matches_current_data(
        model, _record(small_study, request.to_mapping())
    ) is True
