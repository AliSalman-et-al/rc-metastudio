# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import io
import json
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from rc_metastudio import analysis_worker, analysis_worker_client, publication_bias
from rc_metastudio.analysis_results import empty_analysis_result
from rc_metastudio.analysis_snapshot import BinaryInputSnapshot, BinaryStudyInput
from rc_metastudio.publication_bias import EligibilityMethod, EligibilityReport, SmallStudyEffectsRequest
from rc_metastudio.small_study_effects_worker import preview_request, run_request


def _snapshot():
    return BinaryInputSnapshot(
        version=1,
        outcome="Mortality",
        time_point="12 months",
        groups=("Treatment", "Control"),
        metric="OR",
        raw_counts_available=True,
        studies=(
            BinaryStudyInput(
                id=7,
                name="Study 7",
                year=2020,
                estimate=None,
                standard_error=None,
                treatment_events=2,
                treatment_total=20,
                control_events=4,
                control_total=20,
            ),
        ),
        covariates=(),
    )


class _Service:
    def __init__(self):
        self.preview_requests = []
        self.execution_requests = []

    def preview(self, model, request):
        self.preview_requests.append((model, request))
        return EligibilityReport(
            data_type="binary",
            metric="OR",
            usable_studies=1,
            methods=(
                EligibilityMethod(
                    method="harbord",
                    available=True,
                    usable_studies=1,
                    role="primary",
                ),
            ),
            raw_data_available=True,
            package_versions=(("RCMetaR", "test"),),
        )

    def execute(self, model, request):
        self.execution_requests.append((model, request))
        return empty_analysis_result()


def test_worker_preview_returns_dotted_eligibility_for_the_frozen_measure():
    snapshot = _snapshot()
    request = SmallStudyEffectsRequest.create(data_type="binary", metric="OR")
    service = _Service()

    report = preview_request(snapshot, request.to_mapping(), service)

    assert report["data.type"] == "binary"
    assert report["metric"] == "OR"
    assert report["usable.studies"] == 1
    methods = report["methods"]
    assert isinstance(methods, list)
    first_method = methods[0]
    assert isinstance(first_method, dict)
    assert cast(Mapping[str, object], first_method)["method"] == "harbord"
    assert service.preview_requests[0][1] == request


def test_worker_run_rechecks_and_saves_one_frozen_context():
    snapshot = _snapshot()
    request = SmallStudyEffectsRequest.create(
        data_type="binary", metric="OR", selected_funnels=()
    )
    service = _Service()

    result = run_request(snapshot, request.to_mapping(), service)

    metadata = result["small_study_effects"]
    assert isinstance(metadata, dict)
    typed_metadata = cast(Mapping[str, object], metadata)
    assert typed_metadata["specification_identity"] == request.semantic_id
    assert typed_metadata["study_order"] == [
        {"order": 0, "study_id": 7, "name": "Study 7"}
    ]
    assert len(service.preview_requests) == 1
    assert len(service.execution_requests) == 1
    assert service.execution_requests[0][1] == request


def test_worker_operations_run_preview_and_analysis_in_the_child_process(monkeypatch):
    class Bridge:
        def get_r_version_string(self):
            return "R test"

        def get_r_package_version(self, package):
            return f"{package} test"

    service = _Service()
    monkeypatch.setattr(analysis_worker, "_initialize_backend", lambda: Bridge())
    monkeypatch.setattr(
        publication_bias, "SmallStudyEffectsService", lambda: service
    )
    snapshot = _snapshot()
    preview_request_value = SmallStudyEffectsRequest.create(
        data_type="binary", metric="OR"
    )
    run_request_value = SmallStudyEffectsRequest.create(
        data_type="binary", metric="OR", selected_tests=("harbord",),
        selected_funnels=(),
    )

    def invoke(operation, request, run_id):
        payload = {
            "operation": operation,
            "run_id": run_id,
            "input": snapshot.to_mapping(),
            "request": request.to_mapping(),
        }
        with tempfile.TemporaryDirectory() as staging:
            if operation == "small_study_effects":
                payload["staging_dir"] = staging
            monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
            stdout = io.StringIO()
            monkeypatch.setattr(sys, "stdout", stdout)
            assert analysis_worker.main() == 0
            return [json.loads(line) for line in stdout.getvalue().splitlines()]

    preview_messages = invoke(
        "small_study_effects_preview", preview_request_value, "preview-1"
    )
    assert preview_messages[-1]["type"] == "result"
    assert preview_messages[-1]["result"]["data.type"] == "binary"
    assert preview_messages[-1]["backend_versions"]["RCMetaR"] == "RCMetaR test"

    run_messages = invoke("small_study_effects", run_request_value, "run-1")
    assert run_messages[-1]["type"] == "result"
    assert run_messages[-1]["result"]["small_study_effects"]["study_order"] == [
        {"order": 0, "study_id": 7, "name": "Study 7"}
    ]
    assert len(service.preview_requests) == 2
    assert len(service.execution_requests) == 1


def test_worker_client_uses_separate_preview_and_run_operations(monkeypatch, tmp_path):
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
    request = {"version": 1, "metric": "OR"}

    client.request_small_study_effects_preview("preview-1", snapshot, request)
    client.submit_small_study_effects(
        "run-1", snapshot, request, staging_dir=tmp_path
    )

    assert [item[2] for item in started] == [
        "small_study_effects_preview",
        "small_study_effects",
    ]
    assert started[0][1]["operation"] == "small_study_effects_preview"
    assert started[1][1]["input"] == snapshot
    assert started[1][1]["request"] == request
    assert started[1][1]["staging_dir"] == str(tmp_path)


def test_worker_copies_r_temp_figures_into_run_owned_staging(tmp_path):
    r_temp = tmp_path / "r-temp"
    staging = tmp_path / "run-staging"
    r_temp.mkdir()
    staging.mkdir()
    funnel = r_temp / "Rtmp-ordinary.png"
    funnel.write_bytes(b"figure bytes")
    result = {
        "images": {"Ordinary Funnel Plot": str(funnel)},
        "display_images": {"Ordinary Funnel Plot": str(funnel)},
    }

    analysis_worker._stage_small_study_effects_figures(result, str(staging))
    funnel.unlink()

    staged_path = result["images"]["Ordinary Funnel Plot"]
    assert Path(staged_path).parent == staging
    assert Path(staged_path).read_bytes() == b"figure bytes"
    assert result["display_images"]["Ordinary Funnel Plot"] == staged_path
