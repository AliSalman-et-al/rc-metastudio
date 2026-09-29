# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Browsable history of saved workspace analyses."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import cast

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from rc_metastudio import meta_globals, saved_analysis


class ResultsPanelWidget(QWidget):
    """Show saved result metadata and emit navigation requests by record ID."""

    open_requested = pyqtSignal(str)
    edit_copy_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    resume_draft_requested = pyqtSignal(str)
    delete_draft_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("workspaceResultsPanel")

        heading = QLabel("Saved analyses", self)
        heading.setObjectName("savedAnalysesHeading")

        self.empty_state_label = QLabel(
            "No saved analyses yet. Run and save an analysis to see it here.", self
        )
        self.empty_state_label.setObjectName("emptySavedAnalysesLabel")
        self.empty_state_label.setAccessibleName("No saved analyses")
        self.empty_state_label.setWordWrap(True)

        self.history_list = QListWidget(self)
        self.history_list.setObjectName("savedAnalysesList")
        self.history_list.setAccessibleName("Saved analyses")
        self.history_list.setAccessibleDescription(
            "Select a saved analysis, then open it, edit a copy, or delete it."
        )
        self.history_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.history_list.itemActivated.connect(self._open_activated_item)

        layout = QVBoxLayout(self)
        draft_heading = QLabel("Analysis drafts", self)
        draft_heading.setObjectName("analysisDraftsHeading")
        self.draft_list = QListWidget(self)
        self.draft_list.setObjectName("analysisDraftsList")
        self.draft_list.setAccessibleName("Analysis drafts")
        self.draft_list.itemActivated.connect(self._resume_activated_draft)
        layout.addWidget(draft_heading)
        layout.addWidget(self.draft_list)
        layout.addWidget(heading)
        layout.addWidget(self.empty_state_label)
        layout.addWidget(self.history_list)

    def set_drafts(self, records: Sequence[Mapping[str, object]]) -> None:
        """Display unfinished analyses with an explicit resume action."""
        self.draft_list.clear()
        for record in records:
            record_id = str(record["id"])
            selection = cast(Mapping[str, object], record["selection"])
            settings = cast(Mapping[str, object], record["settings"])
            groups = selection.get("groups")
            direction = (
                " versus ".join(str(group) for group in groups)
                if isinstance(groups, list)
                else ""
            )
            title = (
                f"{_display_value(selection.get('outcome'))} · "
                f"{_display_value(selection.get('follow_up'))} · "
                f"{_display_value(selection.get('effect'))} · {direction}"
            )
            detail = (
                f"{_display_value(settings.get('analysis_type'))} · "
                f"{_display_value(settings.get('method'))} · "
                f"Updated {_format_created_at(record.get('updated_at'))}"
            )
            item = QListWidgetItem(f"{title}\n{detail}")
            item.setData(Qt.ItemDataRole.UserRole, record_id)
            row = QWidget(self.draft_list)
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(8, 6, 8, 6)
            summary = QLabel(f"{title}\n{detail}", row)
            summary.setWordWrap(True)
            row_layout.addWidget(summary)
            actions = QHBoxLayout()
            actions.addStretch(1)
            actions.addWidget(
                self._action_button(
                    "Resume", f"Resume analysis draft {title}",
                    self.resume_draft_requested, record_id, row,
                )
            )
            actions.addWidget(
                self._action_button(
                    "Delete", f"Delete analysis draft {title}",
                    self.delete_draft_requested, record_id, row,
                )
            )
            row_layout.addLayout(actions)
            self.draft_list.addItem(item)
            self.draft_list.setItemWidget(item, row)
        self.draft_list.setVisible(bool(records))

    def _resume_activated_draft(self, item: QListWidgetItem) -> None:
        record_id = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(record_id, str):
            self.resume_draft_requested.emit(record_id)

    def set_records(self, records: Sequence[saved_analysis.JsonObject]) -> None:
        """Display saved analysis records while retaining the selected record ID."""
        selected_id = self._selected_id()
        self.history_list.clear()
        restored_item = None
        for record in records:
            record_id = str(record["id"])
            context_text, detail_text = self._record_text(record)
            item = QListWidgetItem(f"{context_text}\n{detail_text}")
            item.setData(Qt.ItemDataRole.UserRole, record_id)
            row = self._record_row(record_id, context_text, detail_text)
            item.setSizeHint(row.sizeHint())
            self.history_list.addItem(item)
            self.history_list.setItemWidget(item, row)
            if record_id == selected_id:
                restored_item = item

        self.history_list.setCurrentItem(restored_item)
        if restored_item is None:
            self.history_list.clearSelection()

        has_records = self.history_list.count() > 0
        self.empty_state_label.setVisible(not has_records)
        self.history_list.setVisible(has_records)

    def _selected_id(self) -> str | None:
        item = self.history_list.currentItem()
        value = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        return value if isinstance(value, str) else None

    def _open_activated_item(self, item: QListWidgetItem) -> None:
        record_id = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(record_id, str):
            self.open_requested.emit(record_id)

    def _record_row(self, record_id: str, context_text: str, detail_text: str):
        row = QWidget(self.history_list)
        row.setObjectName("savedAnalysisRow")
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(8, 6, 8, 6)

        context_label = QLabel(context_text, row)
        context_label.setObjectName("savedAnalysisContext")
        context_label.setAccessibleName(context_text)
        context_label.setWordWrap(True)
        detail_label = QLabel(detail_text, row)
        detail_label.setObjectName("savedAnalysisDetails")
        detail_label.setAccessibleName(detail_text)
        detail_label.setWordWrap(True)
        row_layout.addWidget(context_label)
        row_layout.addWidget(detail_label)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(
            self._action_button(
                "Open",
                f"Open saved analysis {context_text}; record {record_id}",
                self.open_requested,
                record_id,
                row,
            )
        )
        actions.addWidget(
            self._action_button(
                "Edit a copy",
                f"Edit a copy of saved analysis {context_text}; record {record_id}",
                self.edit_copy_requested,
                record_id,
                row,
            )
        )
        actions.addWidget(
            self._action_button(
                "Delete",
                f"Delete saved analysis {context_text}; record {record_id}",
                self.delete_requested,
                record_id,
                row,
            )
        )
        row_layout.addLayout(actions)
        return row

    @staticmethod
    def _action_button(text, accessible_name, signal, record_id, parent):
        button = QPushButton(text, parent)
        button.setAccessibleName(accessible_name)
        button.setToolTip(accessible_name)
        button.clicked.connect(
            lambda _checked=False, value=record_id: signal.emit(value)
        )
        return button

    @staticmethod
    def _record_text(record: Mapping[str, object]) -> tuple[str, str]:
        snapshot_value = record.get("input_snapshot")
        snapshot = (
            cast(Mapping[str, object], snapshot_value)
            if isinstance(snapshot_value, Mapping)
            else {}
        )
        specification_value = record.get("specification")
        specification = (
            cast(Mapping[str, object], specification_value)
            if isinstance(specification_value, Mapping)
            else {}
        )

        outcome = _display_value(snapshot.get("outcome"))
        time_point = _display_value(snapshot.get("time_point"))
        groups = snapshot.get("groups")
        if isinstance(groups, (list, tuple)) and len(groups) >= 2:
            direction = (
                f"{_display_value(groups[0])} versus "
                f"{_display_value(groups[1])}"
            )
        else:
            direction = "Not recorded"
        metric = snapshot.get("metric", specification.get("metric"))
        metric_code = _display_value(metric)
        measure = meta_globals.ALL_METRIC_NAMES.get(metric_code, metric_code)
        method = _display_value(specification.get("method"))
        status = _display_value(record.get("status")).capitalize()
        created = _format_created_at(record.get("created_at"))

        context = (
            f"Outcome: {outcome}  ·  Time point: {time_point}  ·  "
            f"Direction: {direction}  ·  Measure: {measure}"
        )
        details = f"Created: {created}  ·  Method: {method}  ·  Status: {status}"
        return context, details


def _display_value(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return text or "Not recorded"


def _format_created_at(value: object) -> str:
    if not isinstance(value, str):
        return _display_value(value)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone().strftime("%Y-%m-%d %H:%M %Z")
    except ValueError:
        return value
