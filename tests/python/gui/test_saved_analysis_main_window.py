# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Saved results remain browsable when the original worker files disappear."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEvent
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QMessageBox, QWidget

from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()

from rc_metastudio import (
    analysis_dataset,
    data_issue_review,
    main_window,
    results_window,
    saved_result_adapter,
)
from rc_metastudio.meta_globals import BINARY


def _close_result_viewers(window, qapp):
    viewers = window.findChildren(results_window.ResultsWindow)
    runtime_directories = [
        Path(viewer._saved_plot_runtime.name)
        for viewer in viewers
        if viewer._saved_plot_runtime is not None
    ]
    for viewer in viewers:
        assert viewer.close()
        viewer.deleteLater()
    qapp.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()
    assert all(not directory.exists() for directory in runtime_directories)


def test_saved_cumulative_result_restores_original_context(qapp, monkeypatch):
    record = saved_result_adapter.capture_result(
        {
            "version": 1,
            "family": "binary",
            "input_snapshot": {
                "outcome": "Mortality",
                "time_point": "12 months",
                "groups": ["Treatment", "Control"],
            },
        },
        {
            "version": 1,
            "data_type": "binary",
            "workflow": "cumulative",
            "method": "binary.random",
            "metric": "OR",
            "params": {"conf.level": 95},
        },
        {"version": 1, "texts": {}, "images": {}, "sections": []},
        backend_versions={"R": "4.6.1"},
    )
    window = main_window.MainWindow()
    viewer = QWidget(window)
    seen = {}
    try:
        window.workspace.add_saved_analysis(record)
        monkeypatch.setattr(
            window, "_show_analysis_result",
            lambda _result, **kwargs: (seen.update(kwargs), viewer)[1],
        )
        window._open_saved_analysis(str(record.value["id"]))
        assert seen["context"]["outcome"] == "Mortality"
        assert seen["context"]["time_point"] == "12 months"
        assert seen["context"]["direction"] == "Treatment versus Control"
        assert seen["context"]["workflow"] == "cumulative"
        assert seen["context"]["method"] == "binary.random"
    finally:
        window.hide()
        window.deleteLater()
        qapp.processEvents()


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
                _close_result_viewers(window, qapp)
                window.hide()
                window.deleteLater()
        qapp.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qapp.processEvents()


def test_review_correction_returns_to_the_affected_study_cell(qapp):
    dataset = analysis_dataset.Dataset("Review")
    dataset.add_study(analysis_dataset.Study(7, name="Affected study"))
    dataset.add_outcome(
        analysis_dataset.Outcome("Mortality", BINARY, sub_type="proportions")
    )
    window = main_window.MainWindow()
    try:
        window.set_model(dataset, recalculate_outcomes=False)
        review = data_issue_review.review_analysis_data(
            window.model, method_id="binary.random", input_source="raw"
        )
        target = next(issue.target for issue in review.issues if issue.target is not None)
        window.workspace_tabs.setCurrentWidget(window.results_panel)

        window._focus_issue_target(target)

        current = window.tableView.currentIndex()
        assert window.workspace_tabs.currentWidget() is window.nav_frame
        assert window.model.get_ordered_study_ids()[current.row()] == 7
        assert window.model.workspace_column_identity(current.column()) == target.field_identity
    finally:
        window.hide()
        window.deleteLater()
        qapp.processEvents()
