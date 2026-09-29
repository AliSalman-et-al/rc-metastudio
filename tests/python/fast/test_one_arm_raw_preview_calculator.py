# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from rc_metastudio import dataset_analysis_domain
from rc_metastudio.meta_globals import BINARY, CONTINUOUS


@pytest.mark.parametrize(
    ("data_type", "metric", "raw_data", "method", "expected_args"),
    [
        (BINARY, "PLO", [2, 10], "effect_for_study", (2, 10)),
        (CONTINUOUS, "TX Mean", [10, 4.5, 1.2], "continuous_effect_for_study", (10, 4.5, 1.2)),
    ],
)
def test_one_arm_grid_raw_values_reach_calculator(
    monkeypatch, data_type, metric, raw_data, method, expected_args
):
    class Bridge:
        def __getattr__(self, name):
            assert name == method

            def calculate(*args, **kwargs):
                assert args == expected_args
                assert kwargs == {
                    "two_arm": False,
                    "metric": metric,
                    "confidence_level": 95.0,
                }
                return "calculated"

            return calculate

        def effect_triplet(self, result, scale, *, metric):
            assert (result, scale, metric) == ("calculated", "calc_scale", requested_metric)
            return (0.2, 0.1, 0.3)

    requested_metric = metric
    monkeypatch.setattr(dataset_analysis_domain, "_checked_bridge", lambda bridge: bridge)

    assert dataset_analysis_domain.calculate_raw_effects(
        Bridge(), data_type, metric, raw_data, 95.0
    ) == ((0.2, 0.1, 0.3), raw_data[1] if data_type == BINARY else raw_data[0])
