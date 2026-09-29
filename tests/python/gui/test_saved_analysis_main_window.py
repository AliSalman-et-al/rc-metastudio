# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Saved results remain browsable when the original worker files disappear."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QMessageBox

from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()

from rc_metastudio import main_window, results_window, saved_result_adapter


def test_saved_result_survives_project_reopen_with_embedded_figure(qapp, tmp_path, monkeypatch):
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: (_ for _ in ()).throw(AssertionError(message)),
    )
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.No,
    )
    figure = tmp_path / "worker-forest.png"
    image = QImage(2, 2, QImage.Format.Format_ARGB32)
    image.fill(0xFF225588)
    assert image.save(str(figure), "PNG")
    result = {
        "version": 1,
        "texts": {"summary": "Two-arm result"},
        "images": {"forest": str(figure)},
        "display_images": {"forest": str(figure)},
        "image_params_paths": {},
        "plot_capabilities": {
            "forest": {
                "plot_kind": "forest",
                "editable": False,
                "styleable": False,
                "composition": "single",
                "regenerator": "none",
            }
        },
        "sections": [
            {
                "id": "summary",
                "kind": "text",
                "order": 0,
                "title": "Summary",
                "source_key": "summary",
            },
            {
                "id": "forest",
                "kind": "image",
                "order": 1,
                "title": "Forest plot",
                "source_key": "forest",
            },
        ],
    }
    record = saved_result_adapter.capture_result(
        {
            "version": 1,
            "outcome": "Mortality",
            "time_point": "first",
            "groups": ["Treatment", "Control"],
            "metric": "OR",
        },
        {
            "version": 1,
            "data_type": "binary",
            "workflow": "standard",
            "method": "binary.random",
            "metric": "OR",
            "params": {"conf.level": 95},
        },
        result,
        backend_versions={"R": "4.6.1"},
    )
    project = tmp_path / "history.rcms"
    first = main_window.MainWindow()
    second = None
    try:
        first.workspace.add_saved_analysis(record)
        first._refresh_workspace_results()
        assert first.results_panel.history_list.count() == 1
        first.out_path = str(project)
        assert first.save() is True
        figure.unlink()

        second = main_window.MainWindow()
        assert second.open(str(project)) is True
        assert second.results_panel.history_list.count() == 1
        second._open_saved_analysis(str(record.value["id"]))
        viewers = second.findChildren(results_window.ResultsWindow)
        assert len(viewers) == 1
        assert QImage(viewers[0].results.images["forest"]).width() == 2
        assert Path(viewers[0].results.images["forest"]).exists()
    finally:
        for window in (second, first):
            if window is not None:
                window.hide()
                window.deleteLater()
        qapp.processEvents()
