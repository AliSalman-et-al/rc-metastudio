# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""A frozen joint model cannot cross a workspace replacement boundary."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QMessageBox

from rc_metastudio.qt6_ui import prepare_generated_ui_imports
from rc_metastudio.qt6_resources import ensure_application_resources

prepare_generated_ui_imports()
ensure_application_resources()

from rc_metastudio import main_window, reitsma_analysis_dialog


def test_project_replacement_invalidates_open_reitsma_setup(qapp, monkeypatch):
    project = (
        Path(__file__).resolve().parents[3] / "sample_projects" / "lymph.rcms"
    )
    warnings = []
    submissions = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message, *_args: warnings.append(message),
    )
    window = main_window.MainWindow()
    monkeypatch.setattr(
        window,
        "prompt_to_save_unsaved_data",
        lambda: QMessageBox.StandardButton.No,
    )
    try:
        assert window.open(str(project)) is True
        window.reitsma()
        dialog = window.findChildren(reitsma_analysis_dialog.ReitsmaAnalysisDialog)[-1]
        opened_generation = window._document_generation
        monkeypatch.setattr(
            window.analysis_worker,
            "submit_reitsma",
            lambda *args, **kwargs: submissions.append((args, kwargs)),
        )

        assert window.open(str(project)) is True
        assert window._document_generation == opened_generation + 1
        dialog._run()

        assert not submissions
        assert dialog.result() == dialog.DialogCode.Rejected
        assert warnings and "project changed" in warnings[-1].lower()
    finally:
        window.hide()
        window.deleteLater()
        qapp.processEvents()
