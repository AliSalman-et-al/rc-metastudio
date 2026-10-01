# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from dataclasses import replace
import json
from types import SimpleNamespace
from typing import cast
from unittest.mock import patch

import pytest

from rc_metastudio.analysis_adapter import make_analysis_request
from rc_metastudio.analysis_results import empty_analysis_result
from rc_metastudio.continuous_analysis_snapshot import (
    ContinuousArmInput,
    ContinuousCovariateInput,
    ContinuousInputSnapshot,
    ContinuousStudyInput,
    continuous_numerics_from_backend,
    execute_continuous_snapshot,
    freeze_continuous_input,
)
from rc_metastudio.continuous_analysis_snapshot import _DatasetModel, _ContinuousBridge


class _Model:
    current_outcome_name = "Blood pressure"

    def __init__(self, metric="SMD", raw=None, *, estimate=0.09452415852032972, se=0.1826761115625136, subtype=None):
        self.current_effect = metric
        self.current_groups = ["tx A", "tx B"]
        self.subtype = subtype
        self.raw = raw if raw is not None else [[60, 94, 22, 60, 92, 20]]
        self.study = SimpleNamespace(id=7, name="Carroll", year=1997)
        self.dataset = SimpleNamespace(
            studies=[self.study],
            covariates=[SimpleNamespace(name="Age", data_type=1)],
            get_covariate_values=lambda _name, ids_for_keys: {7: 52.0},
        )
        self.estimates = [estimate]
        self.standard_errors = [se]
        self.estimate_calls = 0
        self.unit = SimpleNamespace(
            get_effect_for_source=lambda *_args: SimpleNamespace(
                lower=0.0, upper=0.0, standard_error=None
            )
        )

    def get_current_follow_up_name(self):
        return "first"

    def get_current_groups(self):
        return self.current_groups

    def get_current_outcome_subtype(self):
        return self.subtype

    def get_studies(self, only_if_included=True):
        return [self.study]

    def get_current_estimates_and_standard_errors(self, only_if_included, only_these_studies):
        self.estimate_calls += 1
        return self.estimates, self.standard_errors

    def get_current_raw_data(self, only_if_included=True, only_these_studies=None):
        return self.raw

    def get_current_group_comparison(self):
        return "tx A-tx B" if self.current_effect != "TX Mean" else "tx A"

    def _get_canonical_analysis_unit(self, _index):
        return self.unit

    def get_confidence_level(self):
        return 95.0


def _raw_study() -> ContinuousStudyInput:
    return ContinuousStudyInput(
        study_id=7,
        name="Carroll",
        year=1997,
        provenance="raw_reconstructed",
        estimate=0.09452415852032972,
        standard_error=0.1826761115625136,
        arm_1=ContinuousArmInput(60, 94, 22),
        arm_2=ContinuousArmInput(60, 92, 20),
    )


def _request(metric="SMD"):
    return make_analysis_request(
        data_type="continuous",
        workflow="standard",
        method="continuous.random",
        metric=metric,
        parameters={
            "measure": metric,
            "rm.method": "DL",
            "conf.level": 95.0,
            "unset_option": None,
        },
    )


def test_raw_snapshot_freezes_measurements_without_main_process_effect_lookup():
    model = _Model()

    snapshot = freeze_continuous_input(cast(_DatasetModel, model))
    model.raw[0][1] = 999

    assert snapshot.groups == ("tx A", "tx B")
    assert snapshot.effect_convention == "group_1_minus_group_2"
    assert snapshot.effect_scale == "standard_deviation_units"
    assert snapshot.outcome_unit is None
    assert snapshot.studies[0].provenance == "raw_reconstructed"
    assert snapshot.studies[0].estimate is None
    assert snapshot.studies[0].standard_error is None
    assert model.estimate_calls == 0
    assert snapshot.studies[0].arm_1 == ContinuousArmInput(60, 94, 22)
    assert snapshot.covariates[0].values == (52.0,)
    mapped = snapshot.to_mapping()
    study_rows = cast(list[dict[str, object]], mapped["studies"])
    arm_1 = cast(dict[str, object], study_rows[0]["arm_1"])
    assert arm_1["mean"] == 94.0
    assert ContinuousInputSnapshot.from_mapping(snapshot.to_mapping()) == snapshot


def test_entered_effect_snapshot_keeps_original_interval_and_does_not_invent_raw_data():
    model = _Model(
        metric="MD",
        raw=[["", "", "", "", "", ""]],
        estimate=2.0,
        se=3.833,
    )
    model.unit.get_effect_for_source = lambda *_args: SimpleNamespace(
        lower=-5.52313055127718, upper=9.52313055127718, standard_error=None
    )

    snapshot = freeze_continuous_input(cast(_DatasetModel, model))

    assert snapshot.studies[0].provenance == "entered"
    assert snapshot.studies[0].arm_1 is None
    assert snapshot.studies[0].arm_2 is None
    assert snapshot.studies[0].estimate == 2.0
    assert snapshot.studies[0].entered_lower == -5.52313055127718
    assert snapshot.studies[0].entered_upper == 9.52313055127718
    assert snapshot.studies[0].entered_confidence_level == 95.0
    assert not snapshot.raw_measurements_complete
    numerics = continuous_numerics_from_backend(
        snapshot,
        _request("MD"),
        {"res": {"b": 2.0}},
    )
    assert numerics.studies[0].entered_lower == -5.52313055127718
    assert numerics.studies[0].entered_upper == 9.52313055127718
    assert numerics.studies[0].entered_confidence_level == 95.0


def test_entered_interval_lookup_uses_canonical_study_after_an_earlier_exclusion():
    model = _Model(
        metric="MD",
        raw=[["", "", "", "", "", ""]],
        estimate=2.0,
        se=1.0,
    )
    excluded = SimpleNamespace(id=6, name="Excluded", year=1996)
    included = model.study
    model.dataset.studies = [excluded, included]
    with patch.object(model, "_get_canonical_analysis_unit") as lookup:
        lookup.return_value = SimpleNamespace(
            get_effect_for_source=lambda *_args: SimpleNamespace(
                lower=1.0, upper=3.0
            )
        )
        snapshot = freeze_continuous_input(cast(_DatasetModel, model))

    lookup.assert_called_once_with(1)
    assert snapshot.studies[0].study_id == included.id
    assert snapshot.studies[0].entered_lower == 1.0


def test_single_arm_snapshot_keeps_one_group_and_no_clinical_comparator():
    model = _Model(metric="TX Mean", raw=[[30, 71.5, 11.0, 18, 88.0, 9.0]], estimate=71.5, se=2.008316)

    snapshot = freeze_continuous_input(cast(_DatasetModel, model))

    assert snapshot.groups == ("tx A",)
    assert snapshot.effect_convention == "group_1_mean"
    assert snapshot.studies[0].arm_1 == ContinuousArmInput(30, 71.5, 11)
    assert snapshot.studies[0].arm_2 is None


def test_generic_entered_single_arm_effect_keeps_its_scale_and_source_label():
    model = _Model(
        metric="TX Mean",
        raw=[["", "", "", "", "", ""]],
        estimate=0.55,
        se=0.2,
        subtype="generic_effect",
    )
    model.unit.get_effect_for_source = lambda *_args: SimpleNamespace(
        lower=0.16, upper=0.94, standard_error=0.2
    )

    snapshot = freeze_continuous_input(cast(_DatasetModel, model))

    assert snapshot.outcome_subtype == "generic_effect"
    assert snapshot.effect_scale == "entered_effect_scale"
    assert snapshot.effect_convention == "entered_effect_for_group_1"
    assert snapshot.studies[0].provenance == "entered"
    assert snapshot.studies[0].entered_lower == 0.16


def test_included_study_with_partial_raw_values_is_rejected_instead_of_falling_back():
    model = _Model(raw=[[60, 94, "", 60, 92, 20]], estimate=None, se=None)

    with pytest.raises(ValueError, match="partial raw continuous data"):
        freeze_continuous_input(cast(_DatasetModel, model))


def test_continuous_snapshot_rejects_mixed_raw_and_entered_effect_rows():
    model = _Model()
    second = SimpleNamespace(id=8, name="Entered", year=1998)
    model.dataset.studies = [model.study, second]
    model.raw = [[60, 94, 22, 60, 92, 20], ["", "", "", "", "", ""]]
    model.estimates = [0.1, 0.2]
    model.standard_errors = [0.2, 0.3]
    with (
        patch.object(model, "get_studies", return_value=[model.study, second]),
        patch.object(model, "get_current_raw_data", return_value=model.raw),
        pytest.raises(ValueError, match="cannot mix entered effects and raw measurements"),
    ):
        freeze_continuous_input(cast(_DatasetModel, model))

    assert model.estimate_calls == 0


def test_snapshot_rejects_nonfinite_and_inconsistent_arm_values():
    with pytest.raises(ValueError, match="finite"):
        ContinuousStudyInput(
            1, "Study", None, "entered", float("nan"), 0.2, None, None
        )

    with pytest.raises(ValueError, match="unsupported continuous input snapshot"):
        ContinuousInputSnapshot.from_mapping(
            {**ContinuousInputSnapshot(
                1,
                "Outcome",
                "Follow-up",
                ("Arm A", "Arm B"),
                "SMD",
                None,
                None,
                (_raw_study(),),
                (),
            ).to_mapping(), "version": True}
        )
    with pytest.raises(ValueError, match="comparator arm"):
        ContinuousInputSnapshot(
            1,
            "Outcome",
            "Follow-up",
            ("Arm A",),
            "TX Mean",
            None,
            None,
            (_raw_study(),),
            (),
        )


def test_continuous_numerics_keep_backend_interval_scale_and_missingness():
    snapshot = ContinuousInputSnapshot(
        1,
        "Blood pressure",
        "first",
        ("tx A", "tx B"),
        "SMD",
        None,
        None,
        tuple(
            replace(_raw_study(), study_id=index, name=f"Study {index}")
            for index in range(6)
        ),
        (ContinuousCovariateInput("Age", "continuous", (52.0,) * 6),),
    )
    backend = {
        "input_params": {"conf.level": 95.0},
        "res": {
            "b": [0.358],
            "ci.lb": 0.152,
            "ci.ub": 0.565,
            "se": 0.105,
            "pval": 0.001,
            "tau2": 0.037,
            "k": 6,
        },
    }

    numerics = continuous_numerics_from_backend(snapshot, _request(), backend)

    assert numerics.effect_scale == "standard_deviation_units"
    assert numerics.groups == ("tx A", "tx B")
    assert numerics.confidence_level == 95.0
    assert numerics.pooled.estimate.value == 0.358
    assert numerics.pooled.lower_bound.value == 0.152
    assert numerics.pooled.upper_bound.value == 0.565
    assert numerics.studies[0].provenance == "raw_reconstructed"
    assert numerics.analyzed_study_count.value == 6

    unavailable = continuous_numerics_from_backend(
        snapshot, _request(), {"res": {"b": [0.358], "ci.lb": None, "ci.ub": None}}
    )
    assert unavailable.pooled.lower_bound.status == "not_estimable"
    assert unavailable.pooled.lower_bound.value is None
    assert unavailable.confidence_level == 95.0
    json.dumps(numerics.to_mapping(), allow_nan=False)

    absent = continuous_numerics_from_backend(
        snapshot, _request(), {"res": {"b": [0.358]}}
    )
    assert absent.pooled.lower_bound.status == "not_available"

    with pytest.raises(ValueError, match="exceeds submitted"):
        continuous_numerics_from_backend(
            snapshot, _request(), {"res": {"b": [0.358], "k": 7}}
        )
    with pytest.raises(ValueError, match="non-negative integer"):
        continuous_numerics_from_backend(
            snapshot, _request(), {"res": {"b": [0.358], "k": 5.5}}
        )


def test_adapter_passes_single_arm_raw_data_to_rcmetar_and_returns_typed_result():
    from rc_metastudio.continuous_analysis_snapshot import (
        ContinuousInputSnapshot,
        ContinuousStudyInput,
    )

    snapshot = ContinuousInputSnapshot(
        1,
        "Outcome",
        "Week 4",
        ("Active",),
        "TX Mean",
        None,
        None,
        (
            ContinuousStudyInput(
                0,
                "Study",
                2020,
                "raw_reconstructed",
                71.5,
                2.008316,
                ContinuousArmInput(30, 71.5, 11),
                None,
            ),
        ),
        (),
    )

    class _Bridge:
        def __init__(self):
            self.ro = SimpleNamespace(globalenv={})
            self.calls = []

        @staticmethod
        def _r_numeric_vector(values):
            return tuple(values)

        @staticmethod
        def _r_character_vector(values):
            return tuple(values)

        @staticmethod
        def _r_year_vector(values):
            return tuple(values)

        def execute_r_function(self, name, *args, **kwargs):
            self.calls.append((name, args, kwargs))
            if name == "list":
                return kwargs
            if name == "rcmetar.prepare.analysis.data":
                return {"y": (71.5,), "SE": (2.008316,)}
            if name == "slot":
                return args[0][args[1]]
            return {"function": name, "kwargs": kwargs}

        def run_versioned_analysis_request(self, request):
            self.request = request
            self.ro.globalenv["result"] = {
                "input_params": {"conf.level": 95.0},
                "res": {"b": 71.5, "ci.lb": 67.56, "ci.ub": 75.44, "se": 2.008, "k": 1},
            }
            return empty_analysis_result()

        @staticmethod
        def r_object_to_python(value):
            return value

    bridge = _Bridge()

    execution = execute_continuous_snapshot(
        snapshot, _request("TX Mean"), bridge=cast(_ContinuousBridge, bridge)
    )

    factory_name, _, kwargs = next(
        call for call in bridge.calls if call[0] == "rcmetar.create.continuous.data"
    )
    assert factory_name == "rcmetar.create.continuous.data"
    assert kwargs["N1"] == (30,)
    assert kwargs["mean1"] == (71.5,)
    assert kwargs["y"] == (None,)
    assert kwargs["SE"] == (None,)
    assert "N2" not in kwargs
    assert bridge.ro.globalenv["tmp_obj"]["function"] == factory_name
    assert bridge.request["metric"] == "TX Mean"
    assert execution.numerics.pooled.estimate.value == 71.5
    assert execution.numerics.studies[0].estimate == 71.5
    assert execution.numerics.studies[0].standard_error == 2.008316
    assert any(call[0] == "rcmetar.prepare.analysis.data" for call in bridge.calls)
    parameter_list = next(call[2] for call in bridge.calls if call[0] == "list")
    assert "unset_option" not in parameter_list
