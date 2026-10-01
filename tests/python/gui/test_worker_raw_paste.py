# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from rc_metastudio import automation


def test_pasted_raw_previews_are_published_and_reject_only_stale_rows(monkeypatch):
    app, window = automation.start_automation()
    submissions = []
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
        model.enable_worker_raw_previews()

        def forbidden_r_call(*_args, **_kwargs):
            raise AssertionError("transactional raw paste must not calculate in R")

        monkeypatch.setattr(
            model.editing_service.bridge, "effect_for_study", forbidden_r_call
        )
        monkeypatch.setattr(
            model.editing_service.bridge, "binary_convert_scale", forbidden_r_call
        )
        monkeypatch.setattr(
            window.analysis_worker,
            "submit_calculator",
            lambda run_id, calls: submissions.append((run_id, calls)),
        )

        rows = (
            ("Alpha", "2024", (4, 10, 4, 10)),
            ("Beta", "2023", (7, 12, 2, 10)),
        )
        for row, (name, year, raw_data) in enumerate(rows):
            assert model.setData(model.index(row, model.NAME), name)
            assert model.setData(model.index(row, model.YEAR), year)
            for column, value in zip(model.RAW_DATA, raw_data):
                assert model.setData(model.index(row, column), value)
        window._raw_preview_timer.stop()
        window._submit_raw_previews()
        old_run_id, old_calls = submissions.pop()
        study_ids = {study.id for study in model.dataset.studies}
        assert {int(call["id"]) for call in old_calls} == study_ids

        assert window.tableView.paste_contents(
            model.index(0, model.NAME),
            [["Alpha", "2024", "5", "10", "4", "10"]],
        )
        model = window.model
        window._raw_preview_timer.stop()
        window._submit_raw_previews()
        new_run_id, new_calls = submissions.pop()
        assert len(new_calls) == 1
        assert new_calls[0]["id"] == str(model.dataset.studies[0].id)
        assert new_calls[0]["args"]["raw_data"] == [5.0, 10.0, 4.0, 10.0]

        old_results = {
            call["id"]: [[0.1, 0.05, 0.2], 10]
            if call["args"]["raw_data"][0] == 4.0
            else [[0.2, 0.1, 0.3], 12]
            for call in old_calls
        }
        window.analysis_worker.calculatorCompleted.emit(
            old_run_id,
            {
                "calls": [
                    {"id": call["id"], "result": old_results[call["id"]]}
                    for call in old_calls
                ]
            },
        )
        window._raw_preview_timer.stop()
        group_comparison = model.get_current_group_comparison()
        first_preview = model.get_current_analysis_unit_for_study(0).get_effect_for_source(
            "derived_preview", "OR", group_comparison
        )
        second_preview = model.get_current_analysis_unit_for_study(1).get_effect_for_source(
            "derived_preview", "OR", group_comparison
        )
        assert first_preview.estimate is None
        assert second_preview.estimate == 0.2

        window.analysis_worker.calculatorCompleted.emit(
            new_run_id,
            {
                "calls": [
                    {"id": new_calls[0]["id"], "result": [[0.6, 0.3, 0.8], 10]}
                ]
            },
        )
        window._raw_preview_timer.stop()
        current_preview = model.get_current_analysis_unit_for_study(0).get_effect_for_source(
            "derived_preview", "OR", group_comparison
        )
        assert current_preview.estimate == 0.6
    finally:
        window._raw_preview_timer.stop()
        if window.workspace.document is not None:
            window.workspace.mark_saved()
        window.close()
        app.processEvents()
