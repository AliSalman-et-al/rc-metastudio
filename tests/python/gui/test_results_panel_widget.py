# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import datetime, timezone
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import QtCore, QtGui, QtWidgets

from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()

from rc_metastudio import saved_analysis
from rc_metastudio.results_panel_widget import ResultsPanelWidget


def _record(
    record_id,
    *,
    outcome="Relapse",
    status="complete",
    method="binary.random",
    data_type="binary",
    metric="OR",
    groups=("Treatment A", "Usual care"),
    input_snapshot=None,
    specification=None,
):
    snapshot = (
        input_snapshot
        if input_snapshot is not None
        else {
            "version": 1,
            "outcome": outcome,
            "time_point": "12 months",
            "groups": list(groups),
            "metric": metric,
        }
    )
    saved_specification = (
        specification
        if specification is not None
        else {
            "version": 1,
            "data_type": data_type,
            "workflow": "standard",
            "method": method,
            "metric": metric,
            "params": {"measure": metric},
        }
    )
    return saved_analysis.create_record(
        snapshot,
        saved_specification,
        {"version": 1},
        status=status,
        backend_versions={"R": "4.6.1"},
        record_id=record_id,
        created_at=datetime(2026, 9, 29, 8, 30, tzinfo=timezone.utc),
    ).value


def test_empty_state_and_saved_history_metadata(qapp):
    panel = ResultsPanelWidget()
    panel.set_records(())

    assert "No saved analyses" in panel.empty_state_label.text()
    assert not panel.empty_state_label.isHidden()
    assert panel.history_list.count() == 0

    record = _record("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", status="partial")
    panel.set_records((record,))

    item = panel.history_list.item(0)
    assert item is not None
    assert item.data(QtCore.Qt.ItemDataRole.UserRole) == record["id"]
    assert panel.empty_state_label.isHidden()
    assert not panel.history_list.isHidden()
    for text in (
        "Outcome: Relapse",
        "Time point: 12 months",
        "Direction: Treatment A versus Usual care",
        "Measure: Odds Ratio",
        "Created: 2026-09-29",
        "Method: binary.random",
        "Status: Partial",
    ):
        assert text in item.text()

    row = panel.history_list.itemWidget(item)
    assert row is not None
    buttons = row.findChildren(QtWidgets.QPushButton)
    assert [button.text() for button in buttons] == ["Open", "Edit a copy", "Delete"]
    assert all(button.accessibleName() for button in buttons)


@pytest.mark.parametrize(
    ("data_type", "groups", "metric", "method", "expected_context", "measure"),
    [
        (
            "binary",
            ("Cohort A",),
            "PR",
            "binary.random",
            "Arm: Cohort A",
            "Untransformed Proportion",
        ),
        (
            "continuous",
            ("Treatment B",),
            "TX Mean",
            "continuous.random",
            "Arm: Treatment B",
            "TX Mean",
        ),
        (
            "diagnostic",
            ("Disease status",),
            "Sens",
            "diagnostic.random",
            "Diagnostic group: Disease status",
            "Sensitivity",
        ),
    ],
)
def test_saved_history_uses_frozen_single_group_context(
    qapp, data_type, groups, metric, method, expected_context, measure
):
    panel = ResultsPanelWidget()
    record = _record(
        "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        data_type=data_type,
        groups=groups,
        metric=metric,
        method=method,
    )

    panel.set_records((record,))

    item = panel.history_list.item(0)
    assert item is not None
    assert expected_context in item.text()
    assert f"Measure: {measure}" in item.text()


def test_saved_history_marks_missing_group_context_as_not_recorded(qapp):
    panel = ResultsPanelWidget()
    record = _record(
        "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        groups=(),
    )

    panel.set_records((record,))

    item = panel.history_list.item(0)
    assert item is not None
    assert "Not recorded" in item.text()
    assert "Direction: Not recorded" not in item.text()


def test_saved_continuous_history_uses_frozen_follow_up(qapp):
    panel = ResultsPanelWidget()
    record = _record(
        "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        input_snapshot={
            "version": 1,
            "outcome": "blood pressure",
            "follow_up": "first",
            "groups": ["tx A", "tx B"],
            "metric": "SMD",
        },
        specification={
            "version": 1,
            "data_type": "continuous",
            "workflow": "standard",
            "method": "continuous.random",
            "metric": "SMD",
            "params": {"measure": "SMD"},
        },
    )

    panel.set_records((record,))

    item = panel.history_list.item(0)
    assert item is not None
    assert "Outcome: blood pressure" in item.text()
    assert "Time point: first" in item.text()
    assert "Measure: Standardized Mean Difference" in item.text()


def test_saved_cumulative_history_uses_nested_frozen_input(qapp):
    panel = ResultsPanelWidget()
    record = _record(
        "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        input_snapshot={
            "family": "binary",
            "input_snapshot": {
                "version": 1,
                "outcome": "clinical failure",
                "time_point": "first",
                "groups": ["tx A", "tx B"],
                "metric": "OR",
            },
            "ordering": {"field": "project_order", "direction": "ascending"},
            "sequence": [],
            "version": 1,
        },
        specification={
            "version": 1,
            "data_type": "binary",
            "workflow": "cumulative",
            "method": "binary.random",
            "metric": "OR",
            "params": {"measure": "OR"},
        },
    )

    panel.set_records((record,))

    item = panel.history_list.item(0)
    assert item is not None
    assert "Outcome: clinical failure" in item.text()
    assert "Time point: first" in item.text()
    assert "Direction: tx A versus tx B" in item.text()
    assert "Measure: Odds Ratio" in item.text()
    assert "Method: binary.random" in item.text()


def test_saved_small_study_effects_history_names_selected_tests(qapp):
    panel = ResultsPanelWidget()
    record = _record(
        "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        specification={
            "version": 1,
            "data.type": "binary",
            "metric": "OR",
            "tests": ["rucker-as-re", "peters"],
            "funnels": ["ordinary"],
        },
    )

    panel.set_records((record,))

    item = panel.history_list.item(0)
    assert item is not None
    assert "Measure: Odds Ratio" in item.text()
    assert "Method: Small-study effects · Tests: rucker-as-re, peters" in item.text()


def test_refresh_preserves_selected_id_and_clears_removed_selection(qapp):
    panel = ResultsPanelWidget()
    first = _record("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    second = _record(
        "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        outcome="Hospitalization",
        method="binary.fixed",
    )
    panel.set_records((first, second))
    panel.history_list.setCurrentItem(panel.history_list.item(1))

    refreshed_second = _record(
        second["id"], outcome="Hospitalization", method="binary.fixed"
    )
    panel.set_records((refreshed_second, first))

    current = panel.history_list.currentItem()
    assert current is not None
    assert current.data(QtCore.Qt.ItemDataRole.UserRole) == second["id"]

    panel.set_records((first,))
    assert panel.history_list.currentItem() is None


def test_row_actions_and_keyboard_activation_emit_record_id(qapp):
    panel = ResultsPanelWidget()
    record = _record("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    panel.set_records((record,))
    item = panel.history_list.item(0)
    row = panel.history_list.itemWidget(item)
    assert row is not None
    buttons = {
        button.text(): button
        for button in row.findChildren(QtWidgets.QPushButton)
    }
    opened = []
    edit_copies = []
    deleted = []
    panel.open_requested.connect(opened.append)
    panel.edit_copy_requested.connect(edit_copies.append)
    panel.delete_requested.connect(deleted.append)

    buttons["Open"].click()
    buttons["Edit a copy"].click()
    buttons["Delete"].click()
    assert opened == [record["id"]]
    assert edit_copies == [record["id"]]
    assert deleted == [record["id"]]

    panel.history_list.setCurrentItem(item)
    panel.history_list.setFocus()
    for event_type in (
        QtCore.QEvent.Type.KeyPress,
        QtCore.QEvent.Type.KeyRelease,
    ):
        event = QtGui.QKeyEvent(
            event_type,
            QtCore.Qt.Key.Key_Return,
            QtCore.Qt.KeyboardModifier.NoModifier,
        )
        QtWidgets.QApplication.sendEvent(panel.history_list, event)
    assert opened == [record["id"], record["id"]]
