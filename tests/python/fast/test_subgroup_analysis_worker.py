# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Worker-side subgroup summaries come only from the RCMetaR result."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from rc_metastudio import analysis_worker, analysis_worker_client, saved_result_adapter
from rc_metastudio.analysis_results import AnalysisResult, ResultSection
from rc_metastudio.analysis_snapshot import (
    BinaryCovariateInput,
    BinaryInputSnapshot,
    BinaryStudyInput,
)
from rc_metastudio.subgroup_analysis import (
    create_subgroup_plan,
    create_subgroup_request,
    prepare_subgroup_snapshot,
)
from rc_metastudio.subgroup_analysis_worker import attach_subgroup_report


def _snapshot() -> BinaryInputSnapshot:
    studies = tuple(
        BinaryStudyInput(
            index,
            f"Study {index}",
            2000 + index,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        for index in range(1, 4)
    )
    return BinaryInputSnapshot(
        version=1,
        outcome="Outcome",
        time_point="12 months",
        groups=("Treatment", "Control"),
        metric="OR",
        raw_counts_available=False,
        studies=studies,
        covariates=(
            BinaryCovariateInput("region", "factor", ("north", None, "south")),
        ),
    )


def _backend_result(summary):
    result = AnalysisResult(
        version=1,
        texts={"Subgroup Summary": summary},
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
                "Subgroup Summary",
                summary,
                "Subgroup Summary",
            ),
        ),
    )
    return result


def _summary(plan):
    lines = ["Model Results", " Subgroups Studies Estimate Lower Upper Std p z"]
    for index, level in enumerate(plan.levels, start=1):
        lines.append(
            " Subgroup %s %d 1.%d 0.2 2.2 0.4 0.3 0.5"
            % (level.backend_value, level.included_count, index)
        )
    lines.append(
        " Overall %d 1.3 0.6 2.1 0.3 0.1 0.7" % plan.included_count
    )
    return "\n".join(lines)


@pytest.mark.parametrize("policy", ["exclude", "missing_category"])
def test_worker_run_saves_policy_plan_and_authority_rows_offline(policy, monkeypatch, tmp_path):
    snapshot = _snapshot()
    plan = create_subgroup_plan(snapshot, "region", missing_policy=policy)
    prepared = prepare_subgroup_snapshot(snapshot, plan)
    request = create_subgroup_request(
        snapshot,
        plan,
        method="binary.random",
        parameters={"conf.level": 95.0, "cov_name": "region"},
    )
    summary = _summary(plan)
    backend_result = _backend_result(summary)

    class Bridge:
        ro = SimpleNamespace(globalenv={})

        @staticmethod
        def get_r_version_string():
            return "R test"

        @staticmethod
        def get_r_package_version(package):
            return package + " test"

        @staticmethod
        def run_versioned_analysis_request(mapping):
            assert mapping == request.to_mapping()
            return backend_result

    monkeypatch.setattr(analysis_worker, "_initialize_backend", lambda: Bridge())
    monkeypatch.setattr(analysis_worker, "_create_binary_data", lambda *_args: None)
    messages = []
    monkeypatch.setattr(analysis_worker, "_send", messages.append)

    analysis_worker._execute(
        {
            "operation": "subgroup",
            "run_id": "subgroup-1",
            "input": snapshot.to_mapping(),
            "request": request.to_mapping(),
            "subgroup_plan": plan.to_mapping(),
        }
    )

    result_payload = messages[-1]["result"]
    assert result_payload["subgroup_numerics"]["missing_policy"] == policy
    assert result_payload["subgroup_plan"]["assignments"] == plan.to_mapping()["assignments"]
    assert len(result_payload["subgroup_numerics"]["levels"]) == len(plan.levels)
    assert plan.included_count == len(prepared.studies)
    if policy == "exclude":
        assert "Study 2" in result_payload["texts"]["subgroup_analysis_summary"]
        assert "Excluded for missing subgroup values" in result_payload["texts"]["subgroup_analysis_summary"]
    else:
        assert "Study 2" in result_payload["texts"]["subgroup_analysis_summary"]
        assert "Assigned to Missing values subgroup" in result_payload["texts"]["subgroup_analysis_summary"]

    record = saved_result_adapter.capture_result(
        snapshot.to_mapping(),
        request.to_mapping(),
        result_payload,
        backend_versions={"R": "R test", "RCMetaR": "RCMetaR test"},
    )
    restored = saved_result_adapter.restore_result(record, Path(tmp_path) / "restored")
    assert restored.subgroup_numerics["missing_policy"] == policy
    assert restored.subgroup_plan["missing_policy"] == policy
    assert "Study 2" in restored.texts["subgroup_analysis_summary"]


def test_worker_client_sends_explicit_subgroup_plan(monkeypatch):
    client = analysis_worker_client.AnalysisWorkerClient()
    started = []
    monkeypatch.setattr(
        client,
        "_start",
        lambda run_id, payload, *, operation, artifact_identity=None: started.append(
            (run_id, json.loads(payload), operation)
        ),
    )
    snapshot = {"version": 1, "metric": "OR"}
    request = {"workflow": "subgroup", "method": "binary.random"}
    plan = {"missing_policy": "exclude"}

    client.submit_subgroup("subgroup-1", snapshot, request, plan)

    assert started == [
        (
            "subgroup-1",
            {
                "operation": "subgroup",
                "run_id": "subgroup-1",
                "input": snapshot,
                "request": request,
                "subgroup_plan": plan,
            },
            "subgroup",
        )
    ]


def test_worker_report_uses_authority_rows_and_warns_against_p_value_comparison():
    snapshot = _snapshot()
    plan = create_subgroup_plan(snapshot, "region", missing_policy="exclude")
    result = _backend_result(_summary(plan))
    attached, numerics = attach_subgroup_report(result, plan)

    assert numerics.excluded_count == 1
    assert numerics.levels[0].estimate == 1.1
    assert attached.texts["subgroup_analysis_summary"].startswith(
        "Grouping variable: region\nMissing-value policy: exclude studies with missing values"
    )
    assert attached.texts["subgroup_analysis_summary"].endswith(
        "Within-subgroup p-values do not test differences between subgroup levels."
    )
    assert attached.sections[-1].semantic_id == "subgroup.summary"
