# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace

from rc_metastudio import analysis_worker, analysis_worker_client, reitsma_analysis
from rc_metastudio.analysis_results import empty_analysis_result


def _snapshot():
    return reitsma_analysis.ReitsmaInputSnapshot(
        1,
        "Disease",
        "Follow-up",
        ("Test",),
        tuple(
            reitsma_analysis.ReitsmaStudyInput(index, f"Study {index}", 10, 2, 1, 30)
            for index in range(1, 6)
        ),
    )


def test_worker_runs_one_joint_operation_and_serializes_its_report(monkeypatch):
    class Bridge:
        def get_r_version_string(self):
            return "R test"

        def get_r_package_version(self, package):
            return f"{package} test"

    snapshot = _snapshot()
    request = reitsma_analysis.ReitsmaRequest()
    report = reitsma_analysis.ReitsmaReport(
        1,
        reitsma_analysis.REITSMA_METHOD,
        reitsma_analysis.JOINT_MEASURES,
        (
            reitsma_analysis.ReitsmaReportSection(
                "Summary operating point",
                "Summary operating point",
                "text",
                "available",
                "authority value",
            ),
        ),
    )
    calls = []

    def run(frozen_snapshot, frozen_request, bridge, *, plot_output_path=None):
        calls.append((frozen_snapshot, frozen_request, bridge, plot_output_path))
        return SimpleNamespace(
            result=empty_analysis_result(),
            report=report,
        )

    monkeypatch.setattr(analysis_worker, "_initialize_backend", lambda: Bridge())
    monkeypatch.setattr(reitsma_analysis, "run_reitsma_analysis", run)
    messages = []
    monkeypatch.setattr(analysis_worker, "_send", messages.append)

    with tempfile.TemporaryDirectory() as staging:
        analysis_worker._execute(
            {
                "operation": "reitsma",
                "run_id": "joint-1",
                "input": snapshot.to_mapping(),
                "request": request.to_mapping(),
                "staging_dir": staging,
            }
        )

    assert len(calls) == 1
    assert calls[0][:2] == (snapshot, request)
    assert Path(calls[0][3]).name == "reitsma-sroc.svg"
    assert [message["stage"] for message in messages if message["type"] == "progress"] == [
        "Starting analysis engine",
        "Checking joint count eligibility",
        "Running the joint Reitsma model",
    ]
    result_message = messages[-1]
    assert result_message["type"] == "result"
    assert result_message["backend_versions"] == {
        "R": "R test",
        "mada": "mada test",
        "RCMetaR": "RCMetaR test",
    }
    assert result_message["result"]["reitsma_report"] == report.to_mapping()


def test_worker_client_uses_a_distinct_reitsma_operation(monkeypatch):
    client = analysis_worker_client.AnalysisWorkerClient()
    started = []
    monkeypatch.setattr(
        client,
        "_start",
        lambda run_id, payload, *, operation, artifact_identity=None: started.append(
            (run_id, json.loads(payload), operation)
        ),
    )
    snapshot = {"method": "diagnostic.reitsma", "input_source": "counts"}
    request = {"method": "diagnostic.reitsma", "measures": ["Sensitivity", "Specificity"]}

    client.submit_reitsma(
        "joint-1", snapshot, request, staging_dir="/tmp/reitsma-joint-1"
    )

    assert started == [
        (
            "joint-1",
            {
                "operation": "reitsma",
                "run_id": "joint-1",
                "input": snapshot,
                "request": request,
                "staging_dir": "/tmp/reitsma-joint-1",
            },
            "reitsma",
        )
    ]
