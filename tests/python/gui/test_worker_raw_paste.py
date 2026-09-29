# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from rc_metastudio import automation


def test_paste_candidate_defers_raw_effects_before_restoring_table_state(monkeypatch):
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
        model.enable_worker_raw_previews()

        def forbidden_r_call(*_args, **_kwargs):
            raise AssertionError("transactional raw paste must not calculate in R")

        monkeypatch.setattr(model.editing_service.bridge, "effect_for_study", forbidden_r_call)
        monkeypatch.setattr(model.editing_service.bridge, "binary_convert_scale", forbidden_r_call)
        assert window.tableView.paste_contents(
            model.index(0, model.NAME),
            [["Alpha", "2024", "5", "10", "4", "10"]],
        )

        committed = window.model
        request, = committed.take_pending_raw_previews()
        assert request.raw_data == (5.0, 10.0, 4.0, 10.0)
        assert request.study_id == committed.dataset.studies[0].id
    finally:
        if window.workspace.document is not None:
            window.workspace.mark_saved()
        window.close()
        app.processEvents()
