# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Diagnostic subgroup inputs stay frozen and use RCMetaR's subgroup route."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

from rc_metastudio import analysis_worker
from rc_metastudio.analysis_results import AnalysisResult, ResultSection
from rc_metastudio.diagnostic_analysis_backend import (
    DiagnosticBackend,
    create_diagnostic_r_data,
)
from rc_metastudio.diagnostic_analysis_snapshot import (
    DiagnosticCovariateInput,
    DiagnosticInputSnapshot,
    DiagnosticStudyInput,
    freeze_diagnostic_input,
)
from rc_metastudio.subgroup_analysis import (
    create_subgroup_plan,
    create_subgroup_request,
    prepare_subgroup_snapshot,
)


def _snapshot() -> DiagnosticInputSnapshot:
    return DiagnosticInputSnapshot(
        version=2,
        outcome="Disease",
        time_point="12 months",
        groups=("Disease status",),
        metric="DOR",
        input_source="counts",
        confidence_level=95.0,
        studies=(
            DiagnosticStudyInput(1, "Study 1", 2020, 12, 3, 5, 18, None, None),
            DiagnosticStudyInput(2, "Study 2", 2021, 8, 2, 4, 15, None, None),
            DiagnosticStudyInput(3, "Study 3", 2022, 7, 4, 2, 13, None, None),
            DiagnosticStudyInput(4, "Study 4", 2023, 6, 1, 3, 11, None, None),
        ),
        covariates=(
            DiagnosticCovariateInput("region", "factor", ("1 2", "1", "1", None)),
        ),
    )


class _Bridge:
    def __init__(self, result: AnalysisResult | None = None):
        self.ro = SimpleNamespace(globalenv={})
        self.result = result
        self.created_data = None
        self.covariates = []

    def _r_numeric_vector(self, values):
        return list(values)

    def _r_character_vector(self, values):
        return list(values)

    def _r_year_vector(self, values):
        return list(values)

    def execute_r_function(self, name, *args, **kwargs):
        if name == "list":
            return list(args)
        if name == "rcmetar.create.covariate.values":
            self.covariates.append(kwargs)
            return kwargs
        if name == "rcmetar.create.diagnostic.data":
            self.created_data = kwargs
            return kwargs
        raise AssertionError(name)

    def get_r_version_string(self):
        return "R test"

    def get_r_package_version(self, package):
        return package + " test"

    def run_versioned_analysis_request(self, request):
        assert request["workflow"] == "subgroup"
        return cast(AnalysisResult, self.result)


def _result(summary: str, summary_key: str = "Subgroup Summary") -> AnalysisResult:
    return AnalysisResult(
        version=1,
        texts={summary_key: summary},
        images={},
        display_images={},
        image_var_names={},
        image_params_paths={},
        image_order=None,
        plot_capabilities={},
        sections=(
            ResultSection(
                "subgroup.backend_summary",
                "text",
                0,
                summary_key,
                summary,
                summary_key,
            ),
        ),
    )


def test_legacy_diagnostic_snapshot_round_trips_without_covariates():
    source = _snapshot().to_mapping()
    source["version"] = 1
    source.pop("covariates")

    restored = DiagnosticInputSnapshot.from_mapping(source)

    assert restored.version == 1
    assert restored.covariates == ()
    assert "covariates" not in restored.to_mapping()


def test_diagnostic_subgroup_plan_filters_missing_rows_and_freezes_factor_values():
    snapshot = _snapshot()
    plan = create_subgroup_plan(snapshot, "region", missing_policy="missing_category")
    prepared = prepare_subgroup_snapshot(snapshot, plan)
    request = create_subgroup_request(
        snapshot,
        plan,
        method="diagnostic.random",
        parameters={"measure": "DOR", "conf.level": 95.0},
    )

    assert plan.family == "diagnostic"
    assert request.to_mapping()["data_type"] == "diagnostic"
    assert request.workflow == "subgroup"
    assert len(prepared.studies) == 4
    assert prepared.covariates[0].values[:3] == ("1 2", "1", "1")
    assert prepared.covariates[0].values[3] == plan.levels[-1].backend_value


def test_diagnostic_snapshot_freeze_captures_covariates_and_backend_data():
    class Covariate:
        name = "region"
        data_type = 4

    class Dataset:
        covariates = [Covariate()]

        @staticmethod
        def get_covariate_values(_name, *, ids_for_keys=False):
            assert ids_for_keys
            return {1: "north", 2: None}

    class Model:
        current_effect = "DOR"
        current_outcome_name = "Disease"
        dataset = Dataset()

        @staticmethod
        def get_current_follow_up_name():
            return "12 months"

        @staticmethod
        def get_current_groups():
            return ["Disease status"]

        @staticmethod
        def get_studies(*, only_if_included=True):
            return [
                SimpleNamespace(id=1, name="Study 1", year=2020),
                SimpleNamespace(id=2, name="Study 2", year=2021),
            ]

        @staticmethod
        def get_current_raw_data(*, only_if_included=True, only_these_studies=None):
            return [[12, 3, 5, 18], [8, 2, 4, 15]]

        @staticmethod
        def get_current_estimates_and_standard_errors(**_kwargs):
            raise AssertionError("count snapshots must not query derived effects")

        @staticmethod
        def get_confidence_level():
            return 95.0

    snapshot = freeze_diagnostic_input(Model(), include_covariates=True)
    bridge = _Bridge()
    create_diagnostic_r_data(snapshot, cast(DiagnosticBackend, bridge))

    assert snapshot.version == 2
    assert snapshot.covariates[0].values == ("north", None)
    assert bridge.created_data["covariates"] == bridge.covariates
    assert bridge.covariates[0]["cov.vals"] == ["north", None]


def test_diagnostic_worker_runs_subgroup_request_with_frozen_covariate(monkeypatch):
    snapshot = _snapshot()
    plan = create_subgroup_plan(snapshot, "region", missing_policy="exclude")
    request = create_subgroup_request(
        snapshot,
        plan,
        method="diagnostic.random",
        parameters={"measure": "DOR", "conf.level": 95.0},
    )
    summary = "\n".join(
        (
            "Model Results",
            " Subgroups Studies Estimate Lower Upper Std p z",
            " Subgroup 1 2 1.2 0.2 2.2 0.4 0.3 0.5",
            " Subgroup 1 2 1 1.1 0.1 2.1 0.3 0.2 0.4",
            " Overall 3 1.3 0.6 2.1 0.3 0.1 0.7",
        )
    )
    backend_result = _result(summary, "Summary")
    bridge = _Bridge(backend_result)
    messages = []
    monkeypatch.setattr(analysis_worker, "_initialize_backend", lambda: bridge)
    monkeypatch.setattr(analysis_worker, "_send", messages.append)

    analysis_worker._execute(
        {
            "operation": "subgroup",
            "run_id": "diagnostic-subgroup-1",
            "input": snapshot.to_mapping(),
            "request": request.to_mapping(),
            "subgroup_plan": plan.to_mapping(),
        }
    )

    result_payload = messages[-1]["result"]
    assert result_payload["subgroup_numerics"]["included_count"] == 3
    assert result_payload["subgroup_numerics"]["levels"][0]["estimate"] == 1.1
    assert result_payload["subgroup_plan"]["family"] == "diagnostic"
    assert bridge.created_data["covariates"][0]["cov.vals"] == ["1 2", "1", "1"]
    assert messages[-1]["backend_versions"]["mada"] == "mada test"


def test_numeric_prefix_labels_use_the_row_with_the_matching_study_count():
    snapshot = _snapshot()
    plan = create_subgroup_plan(snapshot, "region", missing_policy="exclude")
    summary = "\n".join(
        (
            "Model Results",
            " Subgroups Studies Estimate Lower Upper Std p z",
            " Subgroup 1 2 1.2 0.2 2.2 0.4 0.3 0.5",
            " Subgroup 1 2 1 1.1 0.1 2.1 0.3 0.2 0.4",
            " Overall 3 1.3 0.6 2.1 0.3 0.1 0.7",
        )
    )

    from rc_metastudio.subgroup_analysis import parse_subgroup_result

    parsed = parse_subgroup_result(summary, plan)

    assert [level.label for level in parsed.levels] == ["1 2", "1"]
    assert [level.estimate for level in parsed.levels] == [1.1, 1.2]
