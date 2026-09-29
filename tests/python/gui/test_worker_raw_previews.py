# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from rc_metastudio import automation
from rc_metastudio import analysis_worker_client
from rc_metastudio import main_window


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
        monkeypatch.setattr(window.analysis_worker, "stop", lambda: stopped.append(True))
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
