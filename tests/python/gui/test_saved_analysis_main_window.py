# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Saved results remain browsable when the original worker files disappear."""

import os
from pathlib import Path
from typing import cast

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
from rc_metastudio.analysis_results import empty_analysis_result
from rc_metastudio.analysis_snapshot import _BinaryInputModel, freeze_binary_input
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


def test_open_saved_result_marks_changed_current_data_without_running_analysis(
    qapp, monkeypatch
):
    dataset = analysis_dataset.Dataset("Current data")
    studies = [
        analysis_dataset.Study(1, name="Alpha", year=2010),
        analysis_dataset.Study(2, name="Beta", year=2020),
    ]
    for study in studies:
        dataset.add_study(study)
    dataset.add_outcome(
        analysis_dataset.Outcome("Mortality", BINARY, sub_type="proportions")
    )
    for study, counts in zip(
        studies, (([5, 20], [10, 25]), ([2, 18], [7, 24])), strict=True
    ):
        study.get_analysis_unit("Mortality", "first").set_raw_data_for_groups(
            ["tx A", "tx B"], counts
        )

    window = main_window.MainWindow()
    viewer = QWidget(window)
    try:
        window.set_model(dataset, recalculate_outcomes=False)
        snapshot = freeze_binary_input(cast(_BinaryInputModel, window.model))
        record = saved_result_adapter.capture_result(
            snapshot.to_mapping(),
            {
                "version": 1,
                "data_type": "binary",
                "workflow": "standard",
                "method": "binary.random",
                "metric": "OR",
                "params": {"conf.level": 95.0},
            },
            {"version": 1, "texts": {}, "images": {}, "sections": []},
            backend_versions={"R": "4.6.1"},
        )
        window.workspace.add_saved_analysis(record)
        saved_identity = record.value["input_identity"]
        seen = {}
        monkeypatch.setattr(
            window,
            "_show_analysis_result",
            lambda _result, **kwargs: (seen.update(kwargs), viewer)[1],
        )
        monkeypatch.setattr(
            window.analysis_worker,
            "submit",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("opening a saved result must not run analysis")
            ),
        )

        window._open_saved_analysis(str(record.value["id"]))
        assert seen["context"]["working_data_changed"] is False

        window.model.dataset.studies[0].get_analysis_unit(
            "Mortality", "first"
        ).get_raw_data_for_group("tx A")[0] = 6
        window._open_saved_analysis(str(record.value["id"]))

        assert seen["context"]["working_data_changed"] is True
        assert record.value["input_identity"] == saved_identity
    finally:
        window.hide()
        window.deleteLater()
        qapp.processEvents()


def test_changed_data_notice_is_first_accessible_results_overview_item(qapp):
    viewer = results_window.ResultsWindow(
        empty_analysis_result(), context={"working_data_changed": True}
    )
    try:
        viewer.show()
        qapp.processEvents()

        first_item = viewer.nav_tree.topLevelItem(0)
        assert first_item is not None
        assert first_item.text(0) == "Saved result data"
        assert viewer.saved_input_notice is not None
        assert viewer.saved_input_notice.isVisible()
        assert viewer.saved_input_notice.accessibleName() == "Saved result input notice"
        assert viewer.saved_input_notice.text() == (
            "The working data for this analysis has changed. This saved result "
            "uses its original input snapshot."
        )
    finally:
        viewer.close()


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
