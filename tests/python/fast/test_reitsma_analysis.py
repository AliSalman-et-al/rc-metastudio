# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from rc_metastudio.analysis_results import AnalysisResult, parse_analysis_result
from rc_metastudio.dataset_table_model import DatasetTableModel
from rc_metastudio.project_adapter import document_to_runtime_project
from rc_metastudio.project_format import load_project
from rc_metastudio.reitsma_analysis import (
    JOINT_MEASURE,
    ReitsmaAnalysisError,
    ReitsmaEligibilityError,
    ReitsmaInputSnapshot,
    ReitsmaModel,
    ReitsmaRequest,
    ReitsmaStudyInput,
    freeze_reitsma_input,
    run_reitsma_analysis,
)


def _snapshot(*, missing_tp: bool = False) -> ReitsmaInputSnapshot:
    rows = [
        (19, 10, 1, 81),
        (8, 2, 9, 13),
        (41, 12, 1, 49),
        (5, 2, 1, 18),
        (45, 32, 58, 165),
    ]
    studies = tuple(
        ReitsmaStudyInput(
            id=index,
            name=f"Study {index}",
            tp=None if missing_tp and index == 2 else tp,
            fn=fn,
            fp=fp,
            tn=tn,
        )
        for index, (tp, fn, fp, tn) in enumerate(rows, start=1)
    )
    return ReitsmaInputSnapshot(1, "Outcome", "Follow-up", ("Disease status",), studies)


class _DatasetModel:
    current_outcome_name = "Outcome"

    def __init__(self):
        self.studies = [SimpleNamespace(id=index, name=f"Study {index}") for index in range(1, 6)]
        self.raw = [
            [19, 10, 1, 81],
            [8, 2, 9, 13],
            [41, 12, 1, 49],
            [5, 2, 1, 18],
            [45, 32, 58, 165],
        ]

    def get_current_follow_up_name(self):
        return "Follow-up"

    def get_current_groups(self):
        return ["Disease status"]

    def get_studies(self, only_if_included=True):
        assert only_if_included
        return self.studies

    def get_current_raw_data(self, only_if_included=True, only_these_studies=None):
        assert only_if_included
        assert only_these_studies == [study.id for study in self.studies]
        return self.raw


def _analysis_result() -> AnalysisResult:
    keys = [
        "Clinical interpretation",
        "Summary operating point",
        "Sampling-based summary ratios",
        "SROC AUC",
        "Marginal prediction",
        "Between-study heterogeneity",
        "Diagnostic I-squared",
        "Model information",
        "References",
    ]
    return parse_analysis_result(
        {
            "version": 1,
            "texts": {key: f"authority: {key}" for key in keys},
            "images": {},
            "display_images": {},
            "image_var_names": {},
            "image_params_paths": {},
            "image_order": None,
            "plot_capabilities": {},
            "sections": [
                {
                    "id": f"section:{index}",
                    "kind": "text",
                    "order": index,
                    "title": key,
                    "source_key": key,
                }
                for index, key in enumerate(keys)
            ],
        }
    )


class _Bridge:
    def __init__(self, *, fit_error: str | None = None):
        self.ro = SimpleNamespace(globalenv={})
        self.calls: list[tuple[str, object]] = []
        self.fit_error = fit_error

    @staticmethod
    def _r_numeric_vector(values):
        return list(values)

    @staticmethod
    def _r_character_vector(values):
        return list(values)

    def execute_r_function(self, name, *args, **kwargs):
        if name == "rcmetar.create.diagnostic.data":
            data = {
                "TP": kwargs["TP"],
                "FN": kwargs["FN"],
                "FP": kwargs["FP"],
                "TN": kwargs["TN"],
                "study.names": kwargs["study.names"],
            }
            self.calls.append(("data", data))
            return data
        if name == "getFromNamespace":
            assert args == ("rcmetar.reitsma.validate.counts", "RCMetaR")

            def validate(data, **options):
                self.calls.append(("validate", (data, options)))

            return validate
        if name == "rm":
            self.calls.append(("cleanup", kwargs["list"]))
            return None
        raise AssertionError(f"unexpected R function: {name}")

    def run_versioned_analysis_request(self, request, res_name, data_name):
        self.calls.append(("request", request))
        assert data_name in self.ro.globalenv
        if self.fit_error:
            raise RuntimeError(self.fit_error)
        result = _analysis_result()
        self.ro.globalenv[res_name] = result
        return result


def _mapping(value: object) -> Mapping[str, object]:
    assert isinstance(value, Mapping)
    assert all(isinstance(key, str) for key in value)
    return cast(Mapping[str, object], value)


def _request_call(bridge: _Bridge) -> Mapping[str, object]:
    return _mapping(next(payload for kind, payload in bridge.calls if kind == "request"))


def test_freeze_and_round_trip_keep_a_metric_free_joint_count_snapshot():
    model = _DatasetModel()

    snapshot = freeze_reitsma_input(cast(ReitsmaModel, model))
    model.raw[0][0] = 900

    assert snapshot.measures == ("Sensitivity", "Specificity")
    assert snapshot.method == "diagnostic.reitsma"
    assert snapshot.studies[0].tp == 19
    assert ReitsmaInputSnapshot.from_mapping(snapshot.to_mapping()) == snapshot
    assert snapshot.to_mapping()["input_source"] == "counts"


def test_live_lymph_project_freezes_the_single_selected_diagnostic_group():
    repo_root = Path(__file__).resolve().parents[3]
    runtime = document_to_runtime_project(
        load_project(repo_root / "sample_projects/lymph.rcms")
    )
    model = DatasetTableModel(dataset=runtime.dataset, add_blank_study=False)
    model.set_state(runtime.model_state)
    model.update_column_indices()

    snapshot = freeze_reitsma_input(cast(ReitsmaModel, model))

    assert snapshot.outcome == "LAG positive"
    assert snapshot.groups == ("test 1",)
    assert len(snapshot.studies) == 17
    assert (
        snapshot.studies[0].name,
        snapshot.studies[0].tp,
        snapshot.studies[0].fn,
        snapshot.studies[0].fp,
        snapshot.studies[0].tn,
    ) == ("Kinderman", 19, 10, 1, 81)


def test_snapshot_rejects_more_than_one_selected_study_group():
    mapping = _snapshot().to_mapping()
    mapping["groups"] = ["Disease status", "Control"]

    with pytest.raises(ValueError, match="groups are invalid"):
        ReitsmaInputSnapshot.from_mapping(mapping)


def test_request_is_joint_and_cannot_round_trip_as_a_univariate_metric():
    request = ReitsmaRequest(create_plot=False)

    mapping = request.to_mapping()
    assert mapping["metric"] == JOINT_MEASURE
    assert mapping["method"] == "diagnostic.reitsma"
    assert "measure" not in cast(dict[str, object], mapping["params"])
    assert ReitsmaRequest.from_mapping(mapping) == request

    mapping["metric"] = "Sens"
    with pytest.raises(ValueError, match="joint Reitsma"):
        ReitsmaRequest.from_mapping(mapping)


def test_runner_uses_one_joint_authority_request_and_orders_portable_report():
    bridge = _Bridge()

    execution = run_reitsma_analysis(_snapshot(), ReitsmaRequest(create_plot=False), bridge)

    request = _request_call(bridge)
    assert request["method"] == "diagnostic.reitsma"
    assert request["metric"] == JOINT_MEASURE
    assert request["workflow"] == "standard"
    assert len([item for kind, item in bridge.calls if kind == "request"]) == 1
    assert execution.result.sections[1].source_key == "Summary operating point"
    report_keys = [section.key for section in execution.report.sections]
    assert report_keys.index("Summary operating point") < report_keys.index("SROC")
    assert report_keys.index("SROC") < report_keys.index("Marginal prediction")
    assert report_keys.index("Marginal prediction") < report_keys.index(
        "Sampling-based summary ratios"
    )
    sroc = next(section for section in execution.report.sections if section.key == "SROC")
    assert sroc.status == "not_available"
    assert sroc.reason == "SROC rendering was disabled for this request."


def test_runner_keeps_transport_plot_path_out_of_the_saved_request():
    bridge = _Bridge()
    output_path = "/run-owned-stage/reitsma-sroc.svg"

    run_reitsma_analysis(
        _snapshot(), ReitsmaRequest(create_plot=True), bridge,
        plot_output_path=output_path,
    )

    authority_request = _request_call(bridge)
    assert _mapping(authority_request["params"])["fp_outpath"] == output_path
    assert "fp_outpath" not in _mapping(ReitsmaRequest().to_mapping()["params"])


def test_missing_count_returns_a_named_reason_without_falling_back_to_univariate():
    bridge = _Bridge()

    with pytest.raises(ReitsmaEligibilityError) as raised:
        run_reitsma_analysis(
            _snapshot(missing_tp=True), ReitsmaRequest(create_plot=False), bridge
        )

    assert raised.value.study_issues[0].study_name == "Study 2"
    assert raised.value.study_issues[0].fields == ("TP",)
    assert "missing required count(s): TP" in str(raised.value)
    assert not any(kind == "request" for kind, _ in bridge.calls)


def test_authority_failure_is_reported_as_joint_failure_not_univariate_fallback():
    bridge = _Bridge(fit_error="primary Reitsma fit did not converge")

    with pytest.raises(ReitsmaAnalysisError, match="primary Reitsma fit did not converge"):
        run_reitsma_analysis(_snapshot(), ReitsmaRequest(create_plot=False), bridge)

    request = _request_call(bridge)
    assert request["method"] == "diagnostic.reitsma"
    assert len([item for kind, item in bridge.calls if kind == "request"]) == 1
