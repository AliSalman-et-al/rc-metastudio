# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import tempfile
from pathlib import Path
from typing import cast
from collections.abc import Mapping

import pytest
from PyQt6.QtCore import QEventLoop, QTimer

from rc_metastudio import automation, publication_bias_dialog
from rc_metastudio import project_adapter, project_format
from rc_metastudio.analysis_results import AnalysisResult, empty_analysis_result
from rc_metastudio.analysis_worker_client import AnalysisWorkerClient
from rc_metastudio.dataset_table_model import DatasetTableModel
from rc_metastudio.publication_bias import (
    EligibilityMethod,
    EligibilityReport,
    SmallStudyEffectsRequest,
)
from rc_metastudio.small_study_effects_core import (
    SmallStudyEffectsService,
    freeze_small_study_effects_input,
)
from rc_metastudio.small_study_effects_worker import run_request
from rc_metastudio.saved_result_adapter import capture_result, restore_result


REPO_ROOT = Path(__file__).resolve().parents[3]


class _Signal:
    def __init__(self):
        self.slots = []

    def connect(self, slot):
        self.slots.append(slot)

    def emit(self, *args):
        for slot in self.slots:
            slot(*args)


class _Dialog:
    def __init__(self, model, parent=None):
        self.model = model
        self.parent = parent
        self.input_snapshot = None
        self.preview_requested = _Signal()
        self.analysis_requested = _Signal()
        self.started = []
        self.preview_results = []
        self.completed = []

    def preview_request(self):
        data_type = str(self.model.get_current_outcome_type())
        metric = "DOR" if data_type == "diagnostic" else str(self.model.current_effect)
        return SmallStudyEffectsRequest.create(data_type=data_type, metric=metric)

    def set_input_snapshot(self, snapshot):
        self.input_snapshot = snapshot

    def start_preview(self):
        self.preview_requested.emit(self.input_snapshot, self.preview_request())

    def begin_worker_request(self, run_id, operation):
        self.started.append((run_id, operation))

    def _worker_preview_completed(self, run_id, report):
        self.preview_results.append((run_id, report))

    def _worker_failed(self, run_id, error):
        self.completed.append((run_id, False, error))

    def _worker_completed(self, run_id, delivered, warnings=()):
        self.completed.append((run_id, delivered, warnings))

    def _show_request_failure(self, message):
        self.completed.append((None, False, message))

    def exec(self):
        return 0


class _SmallStudyEffectsService(SmallStudyEffectsService):
    def preview(
        self, model: object, request: SmallStudyEffectsRequest
    ) -> EligibilityReport:
        return EligibilityReport(
            data_type=request.data_type,
            metric=request.metric,
            usable_studies=4,
            methods=(
                EligibilityMethod(
                    method="harbord",
                    available=True,
                    usable_studies=4,
                    role="primary",
                ),
            ),
            raw_data_available=True,
            package_versions=(("RCMetaR", "test"),),
        )

    def execute(
        self, model: object, request: SmallStudyEffectsRequest
    ) -> AnalysisResult:
        return empty_analysis_result()


def _open_sample_window():
    app, window = automation.start_automation()
    assert window.open(str(REPO_ROOT / "sample_projects" / "amino.rcms"))
    return app, window


def _close_sample_window(app, window):
    if window.workspace.document is not None:
        window.workspace.mark_saved()
    window.close()
    app.processEvents()
    app.quit()


@pytest.mark.qsettings
def test_main_window_sends_frozen_preview_to_worker_and_does_not_save_it(monkeypatch):
    app, window = _open_sample_window()
    started = []
    monkeypatch.setattr(publication_bias_dialog, "PublicationBiasDialog", _Dialog)
    monkeypatch.setattr(
        window.analysis_worker,
        "request_small_study_effects_preview",
        lambda run_id, snapshot, request: started.append(
            (run_id, snapshot, request)
        ),
    )
    try:
        saved_count = len(window.workspace.list_saved_analyses())
        window.publication_bias()

        assert len(started) == 1
        run_id, snapshot, request = started[0]
        assert snapshot["outcome"] == window.model.current_outcome_name
        assert snapshot["metric"] == request["metric"]
        assert window._analysis_worker_runs[run_id]["kind"] == "small_study_effects_preview"
        assert len(window.workspace.list_saved_analyses()) == saved_count

        report = EligibilityReport(
            data_type=request["data.type"],
            metric=request["metric"],
            usable_studies=len(snapshot["studies"]),
            methods=(
                EligibilityMethod(
                    method="harbord",
                    available=True,
                    usable_studies=len(snapshot["studies"]),
                    role="primary",
                ),
            ),
            raw_data_available=True,
        )
        dialog = window._analysis_worker_runs[run_id]["dialog"]
        window._analysis_worker_completed(run_id, report.to_mapping(), [], {})
        assert dialog.preview_results == [(run_id, report.to_mapping())]
        assert len(window.workspace.list_saved_analyses()) == saved_count
    finally:
        _close_sample_window(app, window)


@pytest.mark.qsettings
def test_main_window_saves_and_delivers_small_study_result_from_worker(monkeypatch):
    app, window = _open_sample_window()
    snapshot = freeze_small_study_effects_input(
        window.model,
        SmallStudyEffectsRequest.create(
            data_type=str(window.model.get_current_outcome_type()),
            metric=str(window.model.current_effect),
        ),
    )
    request = SmallStudyEffectsRequest.create(
        data_type=str(window.model.get_current_outcome_type()),
        metric=snapshot.metric,
        selected_tests=(),
        selected_funnels=(),
    )
    dialog = _Dialog(window.model)
    started = []
    staging_dirs = []

    def submit(run_id, input_snapshot, specification, *, staging_dir):
        assert Path(staging_dir).is_dir()
        staging_dirs.append(Path(staging_dir))
        started.append((run_id, input_snapshot, specification))

    monkeypatch.setattr(
        window.analysis_worker,
        "submit_small_study_effects",
        submit,
    )
    monkeypatch.setattr(window, "analysis", lambda *_args, **_kwargs: True)
    try:
        run_id = window.submit_small_study_effects(dialog, snapshot, request)
        assert run_id is not None
        assert started == [(run_id, snapshot.to_mapping(), request.to_mapping())]

        result = run_request(
            snapshot, request.to_mapping(), _SmallStudyEffectsService()
        )
        window._analysis_worker_completed(
            run_id,
            result,
            [],
            {"R": "test", "RCMetaR": "test"},
        )

        saved = window.workspace.list_saved_analyses()
        matching = [
            record for record in saved
            if record["specification"] == request.to_mapping()
        ]
        assert len(matching) == 1
        record = matching[0]
        saved_results = record["results"]
        assert isinstance(saved_results, dict)
        saved_report = saved_results["small_study_effects"]
        result_report = result["small_study_effects"]
        assert isinstance(saved_report, dict)
        assert isinstance(result_report, dict)
        assert cast(Mapping[str, object], saved_report)["input_identity"] == cast(
            Mapping[str, object], result_report
        )["input_identity"]
        assert record["input_snapshot"] == snapshot.to_mapping()
        assert dialog.completed == [(run_id, True, [])]
        assert len(staging_dirs) == 1
        assert not staging_dirs[0].exists()
    finally:
        _close_sample_window(app, window)


@pytest.mark.qsettings
def test_saved_small_study_edit_copy_reuses_frozen_snapshot_and_request(monkeypatch):
    app, window = _open_sample_window()
    request = SmallStudyEffectsRequest.create(
        data_type=str(window.model.get_current_outcome_type()),
        metric=str(window.model.current_effect),
        confidence_level=90,
        selected_tests=("harbord",),
        selected_funnels=("ordinary",),
        trim_and_fill=True,
        trim_and_fill_estimator="R0",
        trim_and_fill_side="left",
        trim_and_fill_model="common",
        extrapolation=True,
        style="bmj",
    )
    snapshot = freeze_small_study_effects_input(window.model, request)
    payload = run_request(snapshot, request.to_mapping(), _SmallStudyEffectsService())
    record = capture_result(
        snapshot.to_mapping(),
        request.to_mapping(),
        payload,
        backend_versions={"R": "test", "RCMetaR": "test"},
    )
    window.workspace.add_saved_analysis(record)

    created = []
    real_dialog = publication_bias_dialog.PublicationBiasDialog

    def create_dialog(*args, **kwargs):
        dialog = real_dialog(*args, **kwargs)
        created.append(dialog)
        return dialog

    preview_calls = []
    analysis_calls = []
    monkeypatch.setattr(
        publication_bias_dialog, "PublicationBiasDialog", create_dialog
    )
    monkeypatch.setattr(
        window.analysis_worker,
        "request_small_study_effects_preview",
        lambda run_id, frozen, preview: preview_calls.append(
            (run_id, frozen, preview)
        ),
    )
    staging_dirs = []

    def submit(run_id, frozen, specification, *, staging_dir):
        staging_dirs.append(Path(staging_dir))
        analysis_calls.append((run_id, frozen, specification))

    monkeypatch.setattr(
        window.analysis_worker, "submit_small_study_effects", submit
    )

    try:
        window._edit_analysis_copy(record.value)
        assert len(created) == 1
        dialog = created[0]
        assert preview_calls[0][1] == snapshot.to_mapping()
        assert preview_calls[0][2]["data.type"] == request.data_type
        assert preview_calls[0][2]["metric"] == request.metric
        assert dialog.initial_request == request

        run_id = preview_calls[0][0]
        dialog._worker_preview_completed(
            run_id,
            EligibilityReport(
                data_type=request.data_type,
                metric=request.metric,
                usable_studies=len(snapshot.studies),
                methods=(
                    EligibilityMethod(
                        method="harbord",
                        available=True,
                        usable_studies=len(snapshot.studies),
                        role="primary",
                    ),
                ),
                raw_data_available=True,
            ).to_mapping(),
        )
        dialog.run()

        assert len(analysis_calls) == 1
        submitted_run, submitted_snapshot, edited_request = analysis_calls[0]
        assert submitted_snapshot == snapshot.to_mapping()
        assert edited_request["data.type"] == request.data_type
        assert edited_request["metric"] == request.metric
        assert edited_request["conf.level"] == 90
        assert edited_request["tests"] == ["harbord"]
        assert edited_request["funnel.style"] == ["bmj"]
        assert edited_request["trim.and.fill"] is True
        assert edited_request["trim.and.fill.estimator"] == "R0"
        assert edited_request["trim.and.fill.side"] == "left"
        assert edited_request["trim.and.fill.model"] == "common"
        assert edited_request["extrapolation"] is True
        assert len(staging_dirs) == 1 and staging_dirs[0].is_dir()

        window._analysis_worker_failed(
            submitted_run, {"message": "Test cleanup"}
        )
        assert not staging_dirs[0].exists()
    finally:
        if created:
            created[0].close()
        _close_sample_window(app, window)


@pytest.mark.qsettings
def test_live_worker_stages_funnel_before_child_exit_and_saves_it(qapp, tmp_path):
    if os.environ.get("RCMS_RUN_LIVE_SMALL_STUDY_WORKER") != "1":
        pytest.skip("set RCMS_RUN_LIVE_SMALL_STUDY_WORKER=1 for the packaged-R check")

    document = project_format.load_project(REPO_ROOT / "sample_projects" / "amino.rcms")
    runtime = project_adapter.document_to_runtime_project(document)
    model = DatasetTableModel(dataset=runtime.dataset, add_blank_study=False)
    model.set_state(runtime.model_state)
    request = SmallStudyEffectsRequest.create(
        data_type=str(model.get_current_outcome_type()),
        metric=str(model.current_effect),
        selected_tests=(),
        selected_funnels=("ordinary",),
    )
    snapshot = freeze_small_study_effects_input(model, request)
    client = AnalysisWorkerClient()
    loop = QEventLoop()
    response = {}

    def completed(run_id, result, warnings, versions):
        response.update(
            run_id=run_id, result=result, warnings=warnings, versions=versions
        )
        loop.quit()

    def failed(run_id, error):
        response.update(run_id=run_id, error=error)
        loop.quit()

    client.completed.connect(completed)
    client.failed.connect(failed)
    staging = tempfile.TemporaryDirectory(dir=tmp_path, prefix="small-study-worker-")
    try:
        client.submit_small_study_effects(
            "live-small-study",
            snapshot.to_mapping(),
            request.to_mapping(),
            staging_dir=staging.name,
        )
        QTimer.singleShot(180_000, loop.quit)
        loop.exec()

        assert "error" not in response, response.get("error")
        assert "result" in response, "small-study worker did not finish in time"
        image_paths = response["result"]["images"]
        assert image_paths
        assert all(
            Path(path).is_file()
            and Path(path).parent == Path(staging.name)
            for path in image_paths.values()
            if path
        )

        record = capture_result(
            snapshot.to_mapping(),
            request.to_mapping(),
            response["result"],
            warnings=tuple(response["warnings"]),
            backend_versions=response["versions"],
        )
        assert record.value["status"] == "complete"
        with tempfile.TemporaryDirectory(
            dir=tmp_path, prefix="small-study-reopened-"
        ) as reopened:
            restored = restore_result(record, Path(reopened))
            assert restored.images
            assert all(Path(path).is_file() for path in restored.images.values() if path)
    finally:
        client.stop_and_wait()
        staging.cleanup()
