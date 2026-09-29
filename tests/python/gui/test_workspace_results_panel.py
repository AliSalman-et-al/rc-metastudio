# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import datetime, timezone
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import QtCore, QtGui, QtWidgets

from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()

from rc_metastudio import saved_analysis
from rc_metastudio.workspace_results_panel import WorkspaceResultsPanel


def _record(record_id, *, outcome="Relapse", status="complete", method="binary.random"):
    return saved_analysis.create_record(
        {
            "version": 1,
            "outcome": outcome,
            "time_point": "12 months",
            "groups": ["Treatment A", "Usual care"],
            "metric": "OR",
        },
        {
            "version": 1,
            "data_type": "binary",
            "workflow": "standard",
            "method": method,
            "metric": "OR",
            "params": {"measure": "OR"},
        },
        {"version": 1},
        status=status,
        backend_versions={"R": "4.6.1"},
        record_id=record_id,
        created_at=datetime(2026, 9, 29, 8, 30, tzinfo=timezone.utc),
    ).value


def test_empty_state_and_saved_history_metadata(qapp):
    panel = WorkspaceResultsPanel()
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


def test_refresh_preserves_selected_id_and_clears_removed_selection(qapp):
    panel = WorkspaceResultsPanel()
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
    panel = WorkspaceResultsPanel()
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
