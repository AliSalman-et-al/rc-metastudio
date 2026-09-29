# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from types import SimpleNamespace

from rc_metastudio import automation


def test_repeated_draft_flush_does_not_dirty_a_saved_project():
    app, window = automation.start_automation()
    try:
        form = SimpleNamespace(
            _document_generation=window._document_generation,
            _analysis_draft_id=None,
        )
        payload = {
            "selection": {
                "outcome": "Mortality",
                "follow_up": "12 weeks",
                "groups": ["Control", "Treatment"],
                "effect": "OR",
            },
            "settings": {
                "analysis_type": None,
                "method": "binary.random",
                "parameters": {"confidence_level": 95.0},
            },
        }
        assert window._save_analysis_draft_from_dialog(form, payload)
        window.workspace.mark_saved()

        assert window._save_analysis_draft_from_dialog(form, payload)
        assert not window.workspace.is_dirty
        assert len(window.workspace.list_analysis_drafts()) == 1
    finally:
        window.workspace.mark_saved()
        window.close()
        app.processEvents()
