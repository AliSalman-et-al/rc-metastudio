# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Focused contracts for the typed analysis request boundary."""

from __future__ import annotations

import pytest
from collections.abc import Mapping
from typing import TypedDict

from rc_metastudio.analysis.requests import make_analysis_request


class RequestKwargs(TypedDict):
    data_type: str
    workflow: str | None
    method: str
    metric: str
    parameters: Mapping[str, object]


def _request_kwargs() -> RequestKwargs:
    return {
        "data_type": "binary",
        "workflow": "standard",
        "method": "random",
        "metric": "OR",
        "parameters": {},
    }


@pytest.mark.parametrize("data_type", ["", "unknown", "Binary"])
def test_analysis_request_rejects_unknown_family(data_type: str) -> None:
    values = _request_kwargs()
    values["data_type"] = data_type
    with pytest.raises(ValueError, match="unsupported analysis data family"):
        make_analysis_request(**values)


def test_analysis_request_rejects_unknown_workflow() -> None:
    values = _request_kwargs()
    values["workflow"] = "unknown"
    with pytest.raises(ValueError, match="unsupported analysis workflow"):
        make_analysis_request(**values)


def test_analysis_request_rejects_empty_metric() -> None:
    values = _request_kwargs()
    values["metric"] = ""
    with pytest.raises(ValueError, match="metric must be a non-empty string"):
        make_analysis_request(**values)


def test_analysis_request_rejects_cross_family_metric() -> None:
    values = _request_kwargs()
    values["metric"] = "MD"
    with pytest.raises(ValueError, match="not valid for binary analysis"):
        make_analysis_request(**values)


def test_analysis_request_keeps_settings_captured_at_selection() -> None:
    parameters = {"conf.level": 90.5, "measure": "OR"}
    values = _request_kwargs()
    values["parameters"] = parameters
    request = make_analysis_request(**values)
    parameters.update({"conf.level": 95.0, "measure": "RR"})

    assert request.to_mapping()["params"] == {"conf.level": 90.5, "measure": "OR"}


@pytest.mark.parametrize('missing', [None, '', '  '])
def test_blank_factor_moderator_requires_exclusion_confirmation(missing):
    from rc_metastudio.analysis import requests as analysis_adapter
    from rc_metastudio.project import adapter as project_adapter
    from rc_metastudio.workspace.table_model import DatasetTableModel
    from tests.python.fast.test_project_adapter import _multi_arm_project
    model = DatasetTableModel(dataset=project_adapter.project_to_dataset(_multi_arm_project('binary')), add_blank_study=False)
    row = model.current_sheet.rows[0]
    row.include = True
    row.covariate_values['moderator'] = missing
    result = analysis_adapter.select_studies_for_covariates(model, [{'id': 'moderator', 'name': 'Region', 'type': 'factor'}])
    assert result.has_missing_values
    assert not result.studies
