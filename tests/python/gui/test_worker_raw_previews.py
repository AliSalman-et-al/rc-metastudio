# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from rc_metastudio import automation


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
        model.enable_worker_raw_previews()
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
