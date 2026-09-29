# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Frozen inputs and authority numerics for diagnostic univariate analyses."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Mapping, Sequence
from typing import cast

import pytest

from rc_metastudio.analysis_results import AnalysisResult, parse_analysis_result
from rc_metastudio.diagnostic_analysis_backend import (
    DiagnosticBackend,
    create_diagnostic_request,
    create_diagnostic_r_data,
    diagnostic_request_from_mapping,
    run_diagnostic_analysis,
)
from rc_metastudio.diagnostic_analysis_results import (
    DiagnosticResultError,
    diagnostic_numerics_from_authority_model,
    parse_diagnostic_numerics,
)
from rc_metastudio.diagnostic_analysis_snapshot import (
    DiagnosticInputSnapshot,
    freeze_diagnostic_input,
)


@dataclass
class _Study:
    id: int
    name: str
    year: int | None
    include: bool = True


class _Model:
    current_effect = "DOR"
    current_outcome_name = "Disease"

    def __init__(self, studies, raw_rows, estimates, standard_errors):
        self.studies = studies
        self.raw_rows = raw_rows
        self.estimates = estimates
        self.standard_errors = standard_errors

    def get_current_follow_up_name(self):
        return "12 months"

    def get_current_groups(self):
        return ["Disease+", "Disease-"]

    def get_studies(self, only_if_included=True):
        return [study for study in self.studies if study.include or not only_if_included]

    def get_current_estimates_and_standard_errors(
        self, only_if_included=True, only_these_studies=None, effect=None
    ):
        selected = [
            study
            for study in self.studies
            if (not only_if_included or study.include)
            and (only_these_studies is None or study.id in only_these_studies)
        ]
        return (
            [self.estimates[study.id] for study in selected],
            [self.standard_errors[study.id] for study in selected],
        )

    def get_current_raw_data(self, only_if_included=True, only_these_studies=None):
        return [
            self.raw_rows[study.id]
            for study in self.studies
            if (not only_if_included or study.include)
            and (only_these_studies is None or study.id in only_these_studies)
        ]

    def get_confidence_level(self):
        return 95.0


class _Bridge:
    def __init__(self):
        self.ro = type("Runtime", (), {"globalenv": {}})()
        self.model_mapping = {
            "b": 0.8,
            "se": 0.35,
            "ci.lb": 0.1,
            "ci.ub": 1.5,
            "pval": 0.022,
            "k": 2,
            "tau2": 0.03,
            "QE": 1.2,
            "QE.df": 1,
            "QEp": 0.27,
            "I2": 16.7,
            "yi.f": [0.2, 1.0],
            "vi.f": [0.04, 0.1],
            "study.weights": [0.7, 0.3],
        }
        self.created_data: dict[str, object] | None = None
        self.request: dict[str, object] | None = None

    def _r_numeric_vector(self, values: object) -> object:
        return list(cast(Sequence[object], values))

    def _r_character_vector(self, values: object) -> object:
        return list(cast(Sequence[object], values))

    def _r_year_vector(self, values: object) -> object:
        return list(cast(Sequence[object], values))

    def execute_r_function(self, name: str, *args: object, **kwargs: object) -> object:
        if name == "list":
            return {}
        assert name == "rcmetar.create.diagnostic.data"
        self.created_data = kwargs
        return kwargs

    def get_available_methods(self, **kwargs: object) -> Mapping[str, str]:
        return {}

    def get_params(self, method: str) -> tuple[object, object, object, object]:
        return (), {}, (), {}

    def get_method_description(self, method: str) -> str:
        return method

    def get_analysis_plot_capabilities(
        self, data_type: str, method: str, workflow: str = "standard"
    ) -> object:
        return {}

    def run_versioned_analysis_request(
        self, request: Mapping[str, object], res_name: str, data_name: str
    ) -> AnalysisResult:
        self.request = dict(request)
        self.ro.globalenv[res_name] = {"Summary": {"MAResults": self.model_mapping}}
        return _analysis_result()

    def r_object_to_python(self, value: object) -> object:
        return value

    def diagnostic_convert_scale(
        self,
        values: list[float | None],
        metric: str,
        convert_to: str = "display.scale",
    ) -> list[object]:
        return [None if value is None else math.exp(value) for value in values]


def _analysis_result() -> AnalysisResult:
    return parse_analysis_result(
        {
            "version": 1,
            "texts": {"summary": "Diagnostic analysis"},
            "images": {},
            "display_images": {},
            "image_var_names": {},
            "image_params_paths": {},
            "image_order": [],
            "plot_capabilities": {},
            "sections": [
                {
                    "id": "summary",
                    "kind": "text",
                    "order": 0,
                    "title": "Summary",
                    "source_key": "summary",
                }
            ],
        }
    )


def _input_snapshot(*, metric="DOR", input_source="counts"):
    if input_source == "counts":
        studies = [
            {
                "id": 1,
                "name": "Alpha",
                "year": 2020,
                "tp": 12,
                "fn": 3,
                "fp": 5,
                "tn": 18,
                "estimate": 0.2,
                "standard_error": 0.2,
            },
            {
                "id": 2,
                "name": "Beta",
                "year": 2022,
                "tp": 7,
                "fn": 4,
                "fp": 2,
                "tn": 13,
                "estimate": 1.0,
                "standard_error": 0.3,
            },
        ]
    else:
        studies = [
            {
                "id": 1,
                "name": "Alpha",
                "year": 2020,
                "tp": None,
                "fn": None,
                "fp": None,
                "tn": None,
                "estimate": 0.2,
                "standard_error": 0.2,
            },
            {
                "id": 2,
                "name": "Beta",
                "year": 2022,
                "tp": None,
                "fn": None,
                "fp": None,
                "tn": None,
                "estimate": 1.0,
                "standard_error": 0.3,
            },
        ]
    return DiagnosticInputSnapshot.from_mapping(
        {
            "version": 1,
            "outcome": "Disease",
            "time_point": "12 months",
            "groups": ["Disease+", "Disease-"],
            "metric": metric,
            "input_source": input_source,
            "confidence_level": 95.0,
            "studies": studies,
        }
    )


def _authority_model():
    return {
        "b": 0.8,
        "se": 0.35,
        "ci.lb": 0.1,
        "ci.ub": 1.5,
        "pval": 0.022,
        "k": 2,
        "tau2": 0.03,
        "QE": 1.2,
        "QE.df": 1,
        "QEp": 0.27,
        "I2": 16.7,
        "yi.f": [0.2, 1.0],
        "vi.f": [0.04, 0.1],
        "study.weights": [0.7, 0.3],
    }


def test_freeze_preserves_only_included_diagnostic_rows_and_round_trips():
    model = _Model(
        [
            _Study(1, "Alpha", 2020),
            _Study(2, "Excluded", 2021, include=False),
            _Study(3, "Beta", 2022),
        ],
        {1: [12, 3, 5, 18], 2: [1, 1, 1, 1], 3: [7, 4, 2, 13]},
        {1: 0.2, 2: None, 3: 1.0},
        {1: 0.2, 2: None, 3: 0.3},
    )

    snapshot = freeze_diagnostic_input(model)

    assert snapshot.metric == "DOR"
    assert snapshot.input_source == "counts"
    assert [(study.id, study.name, study.tp, study.tn) for study in snapshot.studies] == [
        (1, "Alpha", 12, 18),
        (3, "Beta", 7, 13),
    ]
    assert DiagnosticInputSnapshot.from_mapping(snapshot.to_mapping()) == snapshot


def test_freeze_uses_entered_effects_when_counts_are_incomplete():
    model = _Model(
        [_Study(1, "Alpha", 2020), _Study(2, "Beta", 2022)],
        {1: [None, None, None, None], 2: [None, None, None, None]},
        {1: 0.2, 2: 1.0},
        {1: 0.2, 2: 0.3},
    )

    snapshot = freeze_diagnostic_input(model)
    bridge = _Bridge()
    create_diagnostic_r_data(snapshot, cast(DiagnosticBackend, bridge))

    assert snapshot.input_source == "entered_effects"
    assert bridge.created_data is not None
    assert "TP" not in bridge.created_data
    assert bridge.created_data["y"] == [0.2, 1.0]
    assert bridge.created_data["SE"] == [0.2, 0.3]


def test_freeze_rejects_invalid_counts_and_incomplete_entered_effects():
    with pytest.raises(ValueError, match="whole number"):
        freeze_diagnostic_input(
            _Model(
                [_Study(1, "Alpha", 2020)],
                {1: [1.5, 2, 3, 4]},
                {1: 0.2},
                {1: 0.3},
            )
        )
    with pytest.raises(ValueError, match="estimate and standard error"):
        freeze_diagnostic_input(
            _Model(
                [_Study(1, "Alpha", 2020)],
                {1: [None, None, None, None]},
                {1: None},
                {1: None},
            )
        )


def test_authority_numerics_keep_calculation_and_display_scales_and_row_order():
    snapshot = _input_snapshot()
    numerics = diagnostic_numerics_from_authority_model(
        snapshot,
        "diagnostic.random",
        _authority_model(),
        lambda values: [None if value is None else math.exp(value) for value in values],
    )

    assert numerics.scope == "univariate"
    assert numerics.metric == "DOR"
    assert (numerics.calculation_scale, numerics.display_scale) == ("log", "ratio")
    assert numerics.pooled.calculation.estimate.value == 0.8
    assert numerics.pooled.display.estimate.value == pytest.approx(math.exp(0.8))
    assert numerics.pooled.study_count.value == 2
    assert [study.label for study in numerics.studies] == ["Alpha", "Beta"]
    assert [study.weight_fraction.value for study in numerics.studies] == [0.7, 0.3]
    assert numerics.studies[0].display.estimate.value == pytest.approx(math.exp(0.2))
    assert numerics.studies[0].display.lower.status == "not_available"
    reason = numerics.studies[0].display.lower.reason
    assert reason is not None and "confidence limits" in reason
    assert (
        parse_diagnostic_numerics(
            numerics.to_mapping(), input_snapshot=snapshot, method="diagnostic.random"
        )
        == numerics
    )


def test_authority_numerics_mark_missing_outputs_and_apply_metric_scale():
    model = _authority_model()
    del model["se"]
    snapshot = _input_snapshot(metric="Sens")
    numerics = diagnostic_numerics_from_authority_model(
        snapshot,
        "diagnostic.random",
        model,
        lambda values: [None if value is None else 1 / (1 + math.exp(-value)) for value in values],
    )

    assert (numerics.calculation_scale, numerics.display_scale) == ("logit", "proportion")
    assert numerics.pooled.display.estimate.value == pytest.approx(1 / (1 + math.exp(-0.8)))
    assert numerics.pooled.standard_error.status == "not_available"
    reason = numerics.pooled.standard_error.reason
    assert reason is not None and "standard error" in reason


def test_parser_rejects_joint_results_and_study_order_mismatch():
    snapshot = _input_snapshot()
    numeric_mapping = diagnostic_numerics_from_authority_model(
        snapshot,
        "diagnostic.random",
        _authority_model(),
        lambda values: [None if value is None else math.exp(value) for value in values],
    ).to_mapping()
    joint = dict(numeric_mapping, scope="joint")
    with pytest.raises(DiagnosticResultError, match="univariate"):
        parse_diagnostic_numerics(joint, input_snapshot=snapshot, method="diagnostic.random")

    misaligned = dict(numeric_mapping)
    raw_studies = numeric_mapping["studies"]
    assert isinstance(raw_studies, list)
    misaligned["studies"] = list(reversed(raw_studies))
    with pytest.raises(DiagnosticResultError, match="order"):
        parse_diagnostic_numerics(
            misaligned, input_snapshot=snapshot, method="diagnostic.random"
        )

    rows = list(raw_studies)
    first_row = dict(cast(dict[str, object], rows[0]))
    first_tp = dict(cast(dict[str, object], first_row["tp"]))
    first_tp["value"] = 99
    first_row["tp"] = first_tp
    rows[0] = first_row
    changed_input = dict(numeric_mapping, studies=rows)
    with pytest.raises(DiagnosticResultError, match="frozen input"):
        parse_diagnostic_numerics(
            changed_input, input_snapshot=snapshot, method="diagnostic.random"
        )


def test_backend_runs_frozen_standard_request_and_exposes_typed_numerics():
    snapshot = _input_snapshot()
    request = create_diagnostic_request(
        snapshot,
        "diagnostic.random",
        {"measure": "DOR", "method.params": "REML"},
    )
    assert diagnostic_request_from_mapping(request.to_mapping(), snapshot) == request
    bridge = _Bridge()

    run = run_diagnostic_analysis(snapshot, request, cast(DiagnosticBackend, bridge))

    assert run.input_snapshot == snapshot
    assert run.result.texts["summary"] == "Diagnostic analysis"
    assert bridge.request == {
        "version": 1,
        "data_type": "diagnostic",
        "workflow": "standard",
        "method": "diagnostic.random",
        "metric": "DOR",
        "params": {"measure": "DOR", "method.params": "REML"},
    }
    assert bridge.created_data is not None
    assert bridge.created_data["TP"] == [12, 7]
    assert run.numerics.pooled.display.estimate.value == pytest.approx(math.exp(0.8))


def test_backend_rejects_joint_diagnostic_method():
    with pytest.raises(ValueError, match="supported univariate"):
        create_diagnostic_request(_input_snapshot(), "diagnostic.reitsma", {"measure": "DOR"})
