# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import ModuleType, SimpleNamespace
from typing import cast

import pytest

from rc_metastudio import analysis_worker
from rc_metastudio.analysis_results import parse_analysis_result
from rc_metastudio.analysis_snapshot import (
    BinaryInputSnapshot,
    SingleArmBinaryStudyInput,
    _BinaryCovariate,
    _BinaryDataset,
    _BinaryInputModel,
    freeze_binary_input,
)


@dataclass
class _Study:
    id: int
    name: str
    year: int | str | None


class _Dataset(_BinaryDataset):
    covariates: Sequence[_BinaryCovariate] = ()

    def get_covariate_values(
        self, name: str, ids_for_keys: bool = False
    ) -> Mapping[int, object]:
        return {}


class _OneArmModel(_BinaryInputModel):
    current_effect: str | None = "PLO"
    current_outcome_name: str | None = "Infection"

    def __init__(self, raw_rows: list[list[object]] | None = None):
        self.raw_rows = [[2, 10]] if raw_rows is None else raw_rows
        self.studies = [
            _Study(id=11 + index, name=f"Study {index + 1}", year=2020)
            for index, _row in enumerate(self.raw_rows)
        ]
        self.dataset = _Dataset()

    def get_current_follow_up_name(self):
        return "12 months"

    def get_current_groups(self):
        return ["Cohort A"]

    def get_studies(self, only_if_included):
        return self.studies

    def get_current_estimates_and_standard_errors(
        self, only_if_included, only_these_studies
    ):
        return [-1.3862943611198906] * len(self.studies), [0.7905694150420949] * len(self.studies)

    def get_current_raw_data(
        self, only_if_included: bool, only_these_studies: Sequence[int]
    ) -> Sequence[Sequence[object]]:
        return self.raw_rows


def _mapping(value: object) -> Mapping[str, object]:
    assert isinstance(value, Mapping)
    assert all(isinstance(key, str) for key in value)
    return cast(Mapping[str, object], value)


def _one_arm_snapshot_mapping(metric="PLO"):
    return {
        "version": 1,
        "outcome": "Infection",
        "time_point": "12 months",
        "groups": ["Cohort A"],
        "metric": metric,
        "raw_counts_available": True,
        "studies": [
            {
                "id": 11,
                "name": "Study A",
                "year": 2020,
                "estimate": -1.3862943611198906,
                "standard_error": 0.7905694150420949,
                "events": 2,
                "total": 10,
            }
        ],
        "covariates": [],
    }


def _proportion_result(numerics):
    return parse_analysis_result(
        {
            "version": 1,
            "texts": {"Summary": "RCMetaR proportion result"},
            "sections": [
                {
                    "id": "binary.proportion.summary",
                    "kind": "text",
                    "order": 0,
                    "title": "Summary",
                    "source_key": "Summary",
                }
            ],
            "binary_proportion_numerics": numerics,
        }
    )


def _proportion_numerics(metric="PR"):
    estimate = {"status": "available", "value": 0.2, "reason": None}
    lower = {"status": "available", "value": -0.1, "reason": None}
    upper = {"status": "available", "value": 0.5, "reason": None}
    interval = {"estimate": estimate, "lower": lower, "upper": upper}
    return {
        "version": 1,
        "metric": metric,
        "arm_label": "Cohort A",
        "calculation_scale": {"PR": "proportion", "PLO": "logit", "PFT": "freeman_tukey"}[metric],
        "display_scale": "proportion",
        "pooled": {
            "calculation": interval,
            "display": interval,
            "study_count": {"status": "available", "value": 1, "reason": None},
            "back_transformation_denominators": [10] if metric == "PFT" else None,
        },
        "studies": [
            {
                "order": 0,
                "label": "Study A",
                "events": {"status": "available", "value": 2, "reason": None},
                "total": {"status": "available", "value": 10, "reason": None},
                "calculation": interval,
                "display": interval,
            }
        ],
    }


def test_one_arm_snapshot_keeps_arm_identity_and_raw_denominator():
    snapshot = freeze_binary_input(_OneArmModel())

    assert snapshot.groups == ("Cohort A",)
    assert isinstance(snapshot.studies[0], SingleArmBinaryStudyInput)
    assert snapshot.studies[0].events == 2
    assert snapshot.studies[0].total == 10
    assert snapshot.to_mapping()["groups"] == ["Cohort A"]


def test_one_arm_snapshot_rejects_mixed_count_and_entered_effect_sources():
    with pytest.raises(ValueError, match="must all have complete event counts"):
        freeze_binary_input(_OneArmModel([[2, 10], [None, None]]))


def test_worker_snapshot_parses_one_arm_rows_without_treatment_control_fields():
    snapshot = analysis_worker._snapshot_from_mapping(_one_arm_snapshot_mapping())

    assert snapshot.groups == ("Cohort A",)
    assert isinstance(snapshot.studies[0], SingleArmBinaryStudyInput)
    assert snapshot.studies[0].events == 2
    assert snapshot.studies[0].total == 10


def test_worker_snapshot_refuses_counts_that_are_not_declared_as_source():
    value = _one_arm_snapshot_mapping()
    value["raw_counts_available"] = False

    with pytest.raises(ValueError, match="must declare them as the input source"):
        analysis_worker._snapshot_from_mapping(value)


def test_worker_passes_only_the_single_arm_counts_to_rcmetar(monkeypatch):
    robjects = ModuleType("rpy2.robjects")
    globalenv: dict[str, object] = {}
    setattr(robjects, "globalenv", globalenv)
    monkeypatch.setitem(__import__("sys").modules, "rpy2", ModuleType("rpy2"))
    monkeypatch.setitem(__import__("sys").modules, "rpy2.robjects", robjects)
    def execute_r_function(name, *args, **kwargs):
        del args
        return kwargs if name == "rcmetar.create.binary.data" else []

    bridge = SimpleNamespace(
        _r_numeric_vector=lambda values: list(values),
        _r_character_vector=lambda values: list(values),
        _r_year_vector=lambda values: list(values),
        execute_r_function=execute_r_function,
    )
    snapshot = analysis_worker._snapshot_from_mapping(_one_arm_snapshot_mapping())

    data = analysis_worker._create_binary_data(snapshot, bridge)
    data = _mapping(data)

    assert data["g1O1"] == [2]
    assert data["g1O2"] == [8]
    assert data["g2O1"] == [0]
    assert data["g2O2"] == [0]
    assert globalenv["tmp_obj"] is data


def test_proportion_result_preserves_backend_bounds_and_population_label():
    result = _proportion_result(_proportion_numerics())

    assert result.binary_proportion_numerics is not None
    assert result.binary_proportion_numerics.arm_label == "Cohort A"
    assert result.binary_proportion_numerics.pooled.display.lower.value == -0.1
    assert result.binary_numerics is None


def test_proportion_result_rejects_pft_display_without_denominators():
    value = _proportion_numerics("PFT")
    value["pooled"]["back_transformation_denominators"] = None

    with pytest.raises(ValueError, match="back-transformation denominators"):
        _proportion_result(value)


def test_pinned_RCMetaR_041_one_arm_worker_values(monkeypatch):
    try:
        bridge = analysis_worker._initialize_backend()
        version = bridge.get_r_package_version("RCMetaR")
    except Exception as error:
        pytest.skip(f"the configured R runtime is unavailable: {error}")
    if version != "0.4.1":
        pytest.skip(f"pinned RCMetaR 0.4.1 evidence lane; found {version}")

    _definitions, defaults, _order, _metadata = bridge.get_params("binary.random")
    messages = []
    monkeypatch.setattr(analysis_worker, "_send", messages.append)
    request = {
        "run_id": "single-arm-plo-041",
        "operation": "analysis",
        "input": _one_arm_snapshot_mapping("PLO"),
        "request": {
            "version": 1,
            "data_type": "binary",
            "workflow": "standard",
            "method": "binary.random",
            "metric": "PLO",
            "params": dict(defaults, measure="PLO"),
        },
    }

    analysis_worker._execute(request)

    result = _mapping(_mapping(messages[-1])["result"])
    result = _mapping(result["binary_proportion_numerics"])
    assert result["arm_label"] == "Cohort A"
    studies = result["studies"]
    assert isinstance(studies, list) and studies
    study = _mapping(studies[0])
    assert _mapping(study["events"])["value"] == 2
    assert _mapping(study["total"])["value"] == 10
    pooled = _mapping(result["pooled"])
    calculation = _mapping(pooled["calculation"])
    display = _mapping(pooled["display"])
    assert _mapping(calculation["estimate"])["value"] == pytest.approx(
        -1.3862943611198906, abs=1e-12
    )
    assert _mapping(display["estimate"])["value"] == pytest.approx(
        0.2, abs=1e-12
    )
    assert _mapping(display["lower"])["value"] == pytest.approx(
        0.05041281488209275, abs=1e-12
    )
