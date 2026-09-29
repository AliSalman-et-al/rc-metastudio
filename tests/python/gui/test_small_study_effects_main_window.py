# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

import pytest

from rc_metastudio import automation, publication_bias_dialog
from rc_metastudio.publication_bias import (
    EligibilityMethod,
    EligibilityReport,
    SmallStudyEffectsRequest,
)
from rc_metastudio.small_study_effects_core import freeze_small_study_effects_input
from rc_metastudio.small_study_effects_worker import run_request
from rc_metastudio.analysis_results import empty_analysis_result


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


class _SmallStudyEffectsService:
    def preview(self, _model, request):
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

    def execute(self, _model, _request):
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
    monkeypatch.setattr(
        window.analysis_worker,
        "submit_small_study_effects",
        lambda run_id, input_snapshot, specification: started.append(
            (run_id, input_snapshot, specification)
        ),
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
        assert record["results"]["small_study_effects"]["input_identity"] == result[
            "small_study_effects"
        ]["input_identity"]
        assert record["input_snapshot"] == snapshot.to_mapping()
        assert dialog.completed == [(run_id, True, [])]
    finally:
        _close_sample_window(app, window)
