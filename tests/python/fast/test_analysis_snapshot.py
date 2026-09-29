from types import SimpleNamespace

import pytest

from rc_metastudio.analysis_snapshot import freeze_binary_input


class _Model:
    current_effect = "OR"
    current_outcome_name = "Mortality"

    def __init__(self):
        self.raw = [[2, 10, 3, 12]]
        self.dataset = SimpleNamespace(
            covariates=[SimpleNamespace(name="Age", data_type=1)],
            get_covariate_values=lambda _name, ids_for_keys: {4: 58.5},
        )

    def get_current_follow_up_name(self):
        return "12 months"

    def get_current_groups(self):
        return ["Treatment", "Control"]

    def get_studies(self, only_if_included):
        return [SimpleNamespace(id=4, name="Study A", year=2020)]

    def get_current_estimates_and_standard_errors(
        self, only_if_included, only_these_studies
    ):
        return [0.5], [0.2]

    def included_studies_have_raw_data(self):
        return True

    def get_current_raw_data(self, only_if_included, only_these_studies):
        return self.raw


def test_binary_input_is_frozen_and_contains_only_included_selected_rows():
    model = _Model()

    snapshot = freeze_binary_input(model)
    model.raw[0][0] = 9

    assert snapshot.metric == "OR"
    assert snapshot.groups == ("Treatment", "Control")
    assert snapshot.studies[0].treatment_events == 2
    assert snapshot.covariates[0].values == (58.5,)
    assert snapshot.to_mapping()["studies"][0]["treatment_events"] == 2


def test_binary_input_rejects_invalid_counts_before_worker_submission():
    model = _Model()
    model.raw[0][0] = 11

    with pytest.raises(ValueError, match="events must be between"):
        freeze_binary_input(model)
