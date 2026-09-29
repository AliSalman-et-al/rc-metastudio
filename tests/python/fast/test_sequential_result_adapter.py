# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from rc_metastudio.sequential_result_adapter import leave_one_out_estimate_from_model


def test_standard_authority_model_keeps_missing_interval_explicit():
    result = leave_one_out_estimate_from_model(
        {"estimate": [0.4], "ci.lb": None, "ci.ub": [0.8], "Q": [2.1]},
        "log odds ratio",
    )

    assert result.estimate.value == 0.4
    assert result.lower_bound.status == "not_estimable"
    assert result.upper_bound.value == 0.8
    assert result.heterogeneity[0].name == "Q"
    assert result.heterogeneity[0].value == 2.1
