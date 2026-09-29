# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6 import QtCore

from rc_metastudio import automation
from rc_metastudio import analysis_worker_client
from rc_metastudio import main_window
from rc_metastudio.meta_globals import BINARY


def test_raw_study_preview_waits_for_worker_and_rejects_stale_result(monkeypatch):
    app, window = automation.start_automation()
    try:
        window._handle_wizard_results(
            {
                "path": "new_dataset",
                "outcome_info": {
                    "arms": "two",
                    "data_type": "binary",
                    "sub_type": "proportions",
                    "effect": "OR",
                    "metric_choices": [],
                    "name": "Mortality",
                },
                "csv_data": None,
                "selected_dataset": None,
            }
        )
        model = window.model
        assert model._defer_raw_previews is True
        monkeypatch.setattr(
            model.editing_service.bridge,
            "effect_for_study",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("Grid editing must not run R")
            ),
        )
        assert model.setData(model.index(0, model.NAME), "Alpha")
        for offset, count in enumerate((5, 10, 4, 10)):
            assert model.setData(model.index(0, model.RAW_DATA[offset]), count)
        first, = model.take_pending_raw_previews()
        assert first.raw_data == (5.0, 10.0, 4.0, 10.0)

        assert model.setData(model.index(0, model.RAW_DATA[0]), 6)
        second, = model.take_pending_raw_previews()
        assert second.revision > first.revision
        assert model.apply_worker_raw_preview(first, [[0.5, 0.2, 0.8], 10]) is False
        assert model.apply_worker_raw_preview(second, [[0.6, 0.3, 0.9], 10]) is True
        effect = model.get_current_analysis_unit_for_study(0).get_effect_for_source(
            "derived_preview", "OR", model.get_current_group_comparison()
        )
        assert effect.estimate == 0.6
    finally:
        if window.workspace.document is not None:
            window.workspace.mark_saved()
        window.close()
        app.processEvents()


def test_main_window_applies_only_current_worker_preview(monkeypatch):
    app, window = automation.start_automation()
    try:
        window._handle_wizard_results(
            {
                "path": "new_dataset",
                "outcome_info": {
                    "arms": "two",
                    "data_type": "binary",
                    "sub_type": "proportions",
                    "effect": "OR",
                    "metric_choices": [],
                    "name": "Mortality",
                },
                "csv_data": None,
                "selected_dataset": None,
            }
        )
        model = window.model
        monkeypatch.setattr(
            model.editing_service.bridge,
            "effect_for_study",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("The GUI must not calculate study effects")
            ),
        )
        submissions = []
        monkeypatch.setattr(
            window.analysis_worker,
            "submit_calculator",
            lambda run_id, calls: submissions.append((run_id, calls)),
        )
        assert model.setData(model.index(0, model.NAME), "Alpha")
        for offset, count in enumerate((5, 10, 4, 10)):
            assert model.setData(model.index(0, model.RAW_DATA[offset]), count)
        window._submit_raw_previews()
        first_id, first_calls = submissions.pop()
        assert first_calls[0]["operation"] == "calculate_raw_effects"
        assert first_calls[0]["args"]["raw_data"] == [5.0, 10.0, 4.0, 10.0]

        assert model.setData(model.index(0, model.RAW_DATA[0]), 6)
        window.analysis_worker.calculatorCompleted.emit(
            first_id,
            {"calls": [{"id": first_calls[0]["id"], "result": [[0.5, 0.2, 0.8], 10]}]},
        )
        window._submit_raw_previews()
        second_id, second_calls = submissions.pop()
        window.analysis_worker.calculatorCompleted.emit(
            second_id,
            {"calls": [{"id": second_calls[0]["id"], "result": [[0.6, 0.3, 0.9], 10]}]},
        )
        effect = model.get_current_analysis_unit_for_study(0).get_effect_for_source(
            "derived_preview", "OR", model.get_current_group_comparison()
        )
        assert effect.estimate == 0.6
    finally:
        window._raw_preview_timer.stop()
        if window.workspace.document is not None:
            window.workspace.mark_saved()
        window.close()
        app.processEvents()


def test_closing_during_background_preview_does_not_prompt(monkeypatch):
    app, window = automation.start_automation()
    stopped = []
    try:
        window.workspace.mark_saved()
        window._analysis_worker_runs["preview"] = {"kind": "raw_previews"}
        monkeypatch.setattr(
            analysis_worker_client.AnalysisWorkerClient,
            "is_busy",
            property(lambda _self: True),
        )
        monkeypatch.setattr(
            window.analysis_worker,
            "stop_and_wait",
            lambda: (stopped.append(True), True)[1],
        )
        monkeypatch.setattr(
            main_window.QMessageBox,
            "exec",
            lambda _self: (_ for _ in ()).throw(AssertionError("Background preview prompted")),
        )
        assert window.close()
        assert stopped == [True]
        assert not window._raw_preview_timer.isActive()
    finally:
        app.processEvents()


def test_close_and_project_confirmation_pause_pending_previews(monkeypatch):
    app, window = automation.start_automation()
    submissions = []
    monkeypatch.setattr(
        window.analysis_worker, "submit_calculator", lambda *args: submissions.append(args)
    )

    def cancel_after_processing_events():
        app.processEvents()
        window._raw_preview_worker_busy_changed(False)
        app.processEvents()
        assert window._raw_previews_paused
        assert not window._raw_preview_timer.isActive()
        assert submissions == []
        return False

    try:
        with monkeypatch.context() as patch:
            patch.setattr(window, "_confirm_close", cancel_after_processing_events)
            window._raw_preview_timer.start(0)
            assert window.close() is False
            assert not window._raw_previews_paused

            window._raw_preview_timer.start(0)
            assert window._authorize_destructive_project_action() is False
            assert not window._raw_previews_paused
        assert submissions == []
    finally:
        window._raw_preview_timer.stop()
        window.workspace.mark_saved()
        window.close()
        app.processEvents()


def test_one_arm_grid_preview_uses_single_group_raw_shape(monkeypatch):
    app, window = automation.start_automation()
    try:
        window._handle_wizard_results(
            {
                "path": "new_dataset",
                "outcome_info": {
                    "arms": "one",
                    "data_type": "binary",
                    "sub_type": "proportion",
                    "effect": "PLO",
                    "metric_choices": ["PLO"],
                    "name": "Infection",
                },
                "csv_data": None,
                "selected_dataset": None,
            }
        )
        model = window.model
        window.display_groups([model.get_current_groups()[0]])
        submissions = []
        monkeypatch.setattr(
            window.analysis_worker,
            "submit_calculator",
            lambda run_id, calls: submissions.append((run_id, calls)),
        )
        assert model.setData(model.index(0, model.NAME), "Alpha")
        for column, value in zip(model.RAW_DATA, (2, 10)):
            assert model.setData(model.index(0, column), value)
        window._submit_raw_previews()

        run_id, calls = submissions.pop()
        assert calls[0]["args"] == {
            "data_type": BINARY,
            "effect": "PLO",
            "raw_data": [2.0, 10.0],
            "confidence_level": 95.0,
        }
        window.analysis_worker.calculatorCompleted.emit(
            run_id,
            {"calls": [{"id": calls[0]["id"], "result": [[0.2, 0.1, 0.3], 10]}]},
        )
        effect = model.get_current_analysis_unit_for_study(0).get_effect_for_source(
            "derived_preview", "PLO", model.get_current_group_comparison()
        )
        assert effect.estimate == 0.2
    finally:
        window._raw_preview_timer.stop()
        window.workspace.mark_saved()
        window.close()
        app.processEvents()


def test_one_arm_grid_preview_completes_in_r_worker():
    if not os.environ.get("RCMS_R_LIBS"):
        pytest.skip("Pinned R runtime is unavailable")
    app, window = automation.start_automation()
    try:
        window._handle_wizard_results(
            {
                "path": "new_dataset",
                "outcome_info": {
                    "arms": "one",
                    "data_type": "binary",
                    "sub_type": "proportion",
                    "effect": "PLO",
                    "metric_choices": ["PLO"],
                    "name": "Infection",
                },
                "csv_data": None,
                "selected_dataset": None,
            }
        )
        model = window.model
        window.display_groups([model.get_current_groups()[0]])
        assert model.setData(model.index(0, model.NAME), "Alpha")
        for column, value in zip(model.RAW_DATA, (2, 10)):
            assert model.setData(model.index(0, column), value)

        loop = QtCore.QEventLoop()
        failures = []
        window.analysis_worker.calculatorCompleted.connect(lambda *_args: loop.quit())
        window.analysis_worker.failed.connect(
            lambda _run_id, error: (failures.append(str(error)), loop.quit())
        )
        window._submit_raw_previews()
        timeout = QtCore.QTimer(window)
        timeout.setSingleShot(True)
        timeout.timeout.connect(loop.quit)
        timeout.start(30000)
        loop.exec()
        timeout.stop()

        assert not failures
        effect = model.get_current_analysis_unit_for_study(0).get_effect_for_source(
            "derived_preview", "PLO", model.get_current_group_comparison()
        )
        assert effect.estimate == pytest.approx(-1.3862943611198906)
    finally:
        window._raw_preview_timer.stop()
        window.workspace.mark_saved()
        window.close()
        app.processEvents()
