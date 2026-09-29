# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""An unfinished method selection survives a project save and reopen."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QMessageBox, QSpinBox

from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()

from rc_metastudio import analysis_setup_dialog, main_window

def _reply_with_methods(monkeypatch, window):
    methods = {
        "Binary Random-Effects": "binary.random",
        "Binary Fixed-Effect Mantel-Haenszel": "binary.fixed.mh",
    }
    details = {
        method: {
            "parameters": {"conf.level": "float", "digits": "int"},
            "defaults": {"conf.level": 95.0, "digits": 2},
            "order": ["conf.level", "digits"],
            "metadata": {},
            "description": label,
            "plot_capabilities": [],
        }
        for label, method in methods.items()
    }
    monkeypatch.setattr(
        window.analysis_worker,
        "request_methods",
        lambda run_id, _snapshot, _query: window._analysis_worker_methods_ready(
            run_id, {"available_methods": methods, "details": details}, {}
        ),
    )


def test_analysis_draft_can_be_resumed_after_project_reopen(qapp, tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[3] / "sample_projects" / "amino.rcms"
    destination = tmp_path / "draft.rcms"
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: (_ for _ in ()).throw(AssertionError(message)),
    )
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message, *_buttons: (
            QMessageBox.StandardButton.No
            if _title == "Warning"
            else (_ for _ in ()).throw(AssertionError(message))
        ),
    )
    first = main_window.MainWindow()
    second = None
    try:
        assert first.open(str(source)) is True
        _reply_with_methods(monkeypatch, first)
        first.go()
        form = first.findChildren(analysis_setup_dialog.AnalysisSetupDialog)[-1]
        assert form.isVisible()
        chosen = "Binary Fixed-Effect Mantel-Haenszel"
        assert form.method_cbo_box.findText(chosen) >= 0
        form.method_cbo_box.setCurrentText(chosen)
        digits = next(
            control for control in form.findChildren(QSpinBox)
            if control.accessibleName() == "Decimal Places"
        )
        digits.setValue(4)
        form._emit_draft_change()
        assert first.results_panel.draft_list.count() == 1
        first.out_path = str(destination)
        assert first.save() is True

        second = main_window.MainWindow()
        assert second.open(str(destination)) is True
        assert second.results_panel.draft_list.count() == 1
        _reply_with_methods(monkeypatch, second)
        second._resume_analysis_draft(
            second.workspace.list_analysis_drafts()[0]["id"]
        )
        restored = second.findChildren(analysis_setup_dialog.AnalysisSetupDialog)[-1]
        assert restored.isVisible()
        assert restored.method_cbo_box.currentText() == chosen
        restored_digits = next(
            control for control in restored.findChildren(QSpinBox)
            if control.accessibleName() == "Decimal Places"
        )
        assert restored_digits.value() == 4
    finally:
        for window in (second, first):
            if window is not None:
                window.hide()
                window.deleteLater()
        qapp.processEvents()
