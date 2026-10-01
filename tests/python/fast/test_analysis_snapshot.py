from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast

import pytest

from rc_metastudio.analysis_snapshot import (
    BinaryStudyInput,
    SingleArmBinaryStudyInput,
    _BinaryCovariate,
    _BinaryDataset,
    _BinaryInputModel,
    freeze_binary_input,
)


@dataclass
class _Study:
    id: int = 4
    name: str = "Study A"
    year: int | str | None = 2020


@dataclass
class _Covariate:
    name: str = "Age"
    data_type: int = 1


class _Dataset(_BinaryDataset):
    covariates: Sequence[_BinaryCovariate] = (_Covariate(),)

    def get_covariate_values(
        self, name: str, ids_for_keys: bool = False
    ) -> Mapping[int, object]:
        return {4: 58.5}


class _Model(_BinaryInputModel):
    current_effect: str | None = "OR"
    current_outcome_name: str | None = "Mortality"

    def __init__(self):
        self.raw = [[2, 10, 3, 12]]
        self.dataset = _Dataset()

    def get_current_follow_up_name(self):
        return "12 months"

    def get_current_groups(self):
        return ["Treatment", "Control"]

    def get_studies(self, only_if_included):
        return [_Study()]

    def get_current_estimates_and_standard_errors(
        self, only_if_included, only_these_studies
    ):
        return [0.5], [0.2]

    def included_studies_have_raw_data(self):
        return True

    def get_current_raw_data(self, only_if_included, only_these_studies):
        return self.raw


def _mapping(value: object) -> Mapping[str, object]:
    assert isinstance(value, Mapping)
    assert all(isinstance(key, str) for key in value)
    return cast(Mapping[str, object], value)


def test_binary_input_is_frozen_and_contains_only_included_selected_rows():
    model = _Model()

    snapshot = freeze_binary_input(model)
    model.raw[0][0] = 9

    assert snapshot.metric == "OR"
    assert snapshot.groups == ("Treatment", "Control")
    assert isinstance(snapshot.studies[0], BinaryStudyInput)
    assert snapshot.studies[0].treatment_events == 2
    assert snapshot.covariates[0].values == (58.5,)
    mapped_studies = snapshot.to_mapping()["studies"]
    assert isinstance(mapped_studies, list) and mapped_studies
    assert _mapping(mapped_studies[0])["treatment_events"] == 2


def test_binary_input_rejects_invalid_counts_before_worker_submission():
    model = _Model()
    model.raw[0][0] = 11

    with pytest.raises(ValueError, match="events must be between"):
        freeze_binary_input(model)


@pytest.mark.parametrize(
    ("metric", "groups", "raw", "estimate"),
    [
        ("OR", ["Treatment", "Control"], [[None, None, None, None]], 0.5),
        ("PLO", ["Cohort A"], [[None, None]], -1.3862943611198906),
    ],
)
def test_binary_input_freezes_entered_effects_without_raw_counts(
    metric, groups, raw, estimate
):
    class EnteredEffectsModel(_Model):
        def __init__(self):
            super().__init__()
            self.current_effect = metric
            self.raw = raw
            self.groups = groups
            self.estimate = estimate
            self.estimate_calls = 0

        def get_current_groups(self):
            return self.groups

        def get_current_estimates_and_standard_errors(
            self, only_if_included, only_these_studies
        ):
            self.estimate_calls += 1
            return [self.estimate], [0.2]

    model = EnteredEffectsModel()

    snapshot = freeze_binary_input(model)

    assert snapshot.raw_counts_available is False
    assert model.estimate_calls == 1
    row = snapshot.studies[0]
    if metric == "PLO":
        assert isinstance(row, SingleArmBinaryStudyInput)
        assert row.estimate == estimate
        assert row.standard_error == 0.2
        assert row.events is None
        assert row.total is None
    else:
        assert isinstance(row, BinaryStudyInput)
        assert row.estimate == estimate
        assert row.standard_error == 0.2
        assert row.treatment_events is None
        assert row.control_events is None
