# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Behavior checks for native remaining-surface evidence."""

import pytest


def test_covariate_cancel_probe_detects_live_sheet_mutation(qapp, monkeypatch):
    from scripts import native_remaining_surfaces_smoke as smoke
    from rc_metastudio import covariate_type_dialog
    assert smoke._observe_covariate_owner_cancel(qapp) is True
    original = covariate_type_dialog.CovariateTypeDialog.__init__
    def mutate_live_sheet(self, dataset, covariate, parent=None):
        assert parent is not None
        original(self, parent.model.current_sheet, covariate, parent=parent)
    monkeypatch.setattr(covariate_type_dialog.CovariateTypeDialog, "__init__", mutate_live_sheet)
    with pytest.raises(RuntimeError, match="cancel did not preserve owner sheet"):
        smoke._observe_covariate_owner_cancel(qapp)


@pytest.mark.parametrize("defect", [None, "escape", "close", "completion"])
@pytest.mark.parametrize("surface", ["import-progress", "shared-progress"])
def test_progress_observer_checks_blocked_gestures_and_owner_completion(qapp, monkeypatch, defect, surface):
    import sys
    from scripts import native_remaining_surfaces_smoke as smoke
    from rc_metastudio import main_window
    from rc_metastudio.analysis import progress_dialog
    dialog_type = main_window.ImportProgressDialog if surface == "import-progress" else progress_dialog.AnalysisProgressDialog
    callback_errors = []
    monkeypatch.setattr(sys, "excepthook", lambda _kind, error, _trace: callback_errors.append(error))
    if defect == "escape":
        monkeypatch.setattr(dialog_type, "reject", lambda self: self.hide())
    elif defect == "close":
        monkeypatch.setattr(dialog_type, "closeEvent", lambda self, event: event.accept())
    window = dialog_type()
    try:
        window.show()
        qapp.processEvents()
        with monkeypatch.context() as completion:
            if defect == "completion":
                completion.setattr(window, "hide", lambda: None)
            observation = smoke._observe_capture_close(qapp, window, surface)
        assert callback_errors == []
        expected = {"close_blocked": True, "escape_blocked": True, "owner_completed": True}
        if defect is None:
            assert observation == expected
        else:
            assert isinstance(observation, dict)
            field = {"close": "close_blocked", "escape": "escape_blocked", "completion": "owner_completed"}[defect]
            assert observation[field] is False
    finally:
        window.hide()
        window.deleteLater()
        qapp.processEvents()
