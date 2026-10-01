# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Startup recovery restores work or removes it after an explicit discard."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()

from rc_metastudio import main_window, project_format, recovery_snapshot


def _sample_document():
    source = Path(__file__).resolve().parents[3] / "sample_projects" / "amino.rcms"
    return project_format.load_project(source)


def _click_recovery_button(window, text, qapp):
    prompt = window._recovery_prompt
    button = next(button for button in prompt.buttons() if button.text() == text)
    button.click()
    qapp.processEvents()


def test_startup_restores_valid_recovery_without_overwriting_source(qapp, tmp_path, monkeypatch):
    recovery_path = tmp_path / "recovery.rcms-recovery"
    source_path = tmp_path / "original.rcms"
    recovery_snapshot.write_recovery_snapshot(
        recovery_path, _sample_document(), source_project_path=source_path,
        workspace_was_dirty=True,
    )
    window = main_window.MainWindow()
    try:
        window._recovery_path = recovery_path
        monkeypatch.setattr(window, "_open_startup_wizard", lambda: None)
        window._offer_recovery_or_start()
        _click_recovery_button(window, "Restore work", qapp)

        assert window.model.dataset.title == "aminoglycosides"
        assert window.workspace.is_dirty
        assert window.out_path == str(source_path)
        assert recovery_path.exists()
        assert not source_path.exists()
    finally:
        window.hide()
        window.deleteLater()
        qapp.processEvents()


def test_startup_discards_recovery_only_when_chosen(qapp, tmp_path, monkeypatch):
    recovery_path = tmp_path / "recovery.rcms-recovery"
    recovery_snapshot.write_recovery_snapshot(recovery_path, _sample_document())
    window = main_window.MainWindow()
    started = []
    try:
        window._recovery_path = recovery_path
        monkeypatch.setattr(window, "_open_startup_wizard", lambda: started.append(True))
        window._offer_recovery_or_start()
        assert recovery_path.exists()
        _click_recovery_button(window, "Discard recovery", qapp)

        assert not recovery_path.exists()
        assert started == [True]
        assert window._recovery_enabled
    finally:
        window.hide()
        window.deleteLater()
        qapp.processEvents()
