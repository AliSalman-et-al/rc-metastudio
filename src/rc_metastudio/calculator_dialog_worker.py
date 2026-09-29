# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Latest-request handling for study calculator dialogs."""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping, Sequence
from uuid import uuid4

from PyQt6 import QtCore, QtWidgets


class CalculatorDialogRequests(QtCore.QObject):
    """Send calculator batches to the shared worker and reject stale replies."""

    def __init__(self, worker_client, status_label: QtWidgets.QLabel):
        super().__init__(status_label)
        self._worker = worker_client
        self._status_label = status_label
        self._generation = 0
        self._pending: tuple[
            int,
            list[dict[str, object]],
            Callable[[Mapping[str, object]], None],
            Callable[[object], None],
        ] | None = None
        self._active: tuple[str, int] | None = None
        self._active_call_ids: frozenset[str] = frozenset()
        self._active_result_callback: Callable[[Mapping[str, object]], None] | None = None
        self._active_error_callback: Callable[[object], None] | None = None
        worker_client.calculatorCompleted.connect(self._completed)
        worker_client.failed.connect(self._failed)
        worker_client.progress.connect(self._progress)
        worker_client.busyChanged.connect(self._busy_changed)

    @property
    def generation(self) -> int:
        return self._generation

    def invalidate(self) -> None:
        """Invalidate results after an edit that has not yet been submitted."""
        self._generation += 1
        self._pending = None

    def submit(
        self,
        calls: Sequence[Mapping[str, object]],
        on_result: Callable[[Mapping[str, object]], None],
        on_error: Callable[[object], None] | None = None,
    ) -> int:
        self._generation += 1
        generation = self._generation
        self._pending = (
            generation,
            [copy.deepcopy(dict(call)) for call in calls],
            on_result,
            on_error or self._default_error,
        )
        self._set_status(
            "Waiting for the analysis worker…"
            if self._worker.is_busy
            else "Calculating in the analysis worker…"
        )
        self._start_pending()
        return generation

    def close(self) -> None:
        self.invalidate()
        for signal, slot in (
            (self._worker.calculatorCompleted, self._completed),
            (self._worker.failed, self._failed),
            (self._worker.progress, self._progress),
            (self._worker.busyChanged, self._busy_changed),
        ):
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError):
                pass

    def _start_pending(self) -> None:
        if self._active is not None or self._pending is None or self._worker.is_busy:
            return
        generation, calls, on_result, on_error = self._pending
        self._pending = None
        call_ids = [call.get("id") for call in calls]
        valid_call_ids = [
            call_id for call_id in call_ids if isinstance(call_id, str) and call_id
        ]
        if (
            not calls
            or len(valid_call_ids) != len(calls)
            or len(set(valid_call_ids)) != len(calls)
        ):
            message = "Calculator request call identities must be unique non-empty text."
            if generation == self._generation:
                self._set_status("Study calculation failed; entered values were kept. " + message)
                on_error({"message": message})
            self._start_pending()
            return
        run_id = "calculator-" + uuid4().hex
        self._active = (run_id, generation)
        self._active_call_ids = frozenset(valid_call_ids)
        self._active_result_callback = on_result
        self._active_error_callback = on_error
        try:
            self._worker.submit_calculator(run_id, calls)
        except Exception as error:
            self._active = None
            self._active_call_ids = frozenset()
            self._active_result_callback = None
            self._active_error_callback = None
            if generation == self._generation:
                on_error({"message": str(error)})
            self._start_pending()

    def _completed(self, run_id, result) -> None:
        if self._active is None or run_id != self._active[0]:
            return
        _active_id, generation = self._active
        self._active = None
        if self._pending is not None:
            self._active_call_ids = frozenset()
            self._active_result_callback = None
            self._active_error_callback = None
            self._set_status("Calculating the latest study values…")
            self._start_pending()
            return
        if generation != self._generation:
            self._active_call_ids = frozenset()
            self._active_result_callback = None
            self._active_error_callback = None
            self._set_status("")
            return
        if not isinstance(result, Mapping) or not isinstance(result.get("calls"), list):
            self._invalid_result("The analysis worker returned an invalid calculator result.")
            return
        by_id: dict[str, object] = {}
        for item in result["calls"]:
            if (
                not isinstance(item, Mapping)
                or not isinstance(item.get("id"), str)
                or item["id"] not in self._active_call_ids
                or item["id"] in by_id
            ):
                self._invalid_result(
                    "The analysis worker returned an invalid calculator result."
                )
                return
            by_id[item["id"]] = item.get("result")
        if set(by_id) != self._active_call_ids:
            self._invalid_result("The analysis worker omitted a calculator result.")
            return
        self._set_status("")
        self._active_call_ids = frozenset()
        pending_result = self._active_result_callback
        self._active_result_callback = None
        self._active_error_callback = None
        if pending_result is not None:
            pending_result(by_id)

    def _invalid_result(self, message: str) -> None:
        error = {"message": message}
        error_callback = self._active_error_callback
        self._active_call_ids = frozenset()
        self._active_result_callback = None
        self._active_error_callback = None
        self._set_status("Study calculation failed; entered values were kept. " + message)
        if error_callback is not None:
            error_callback(error)

    def _failed(self, run_id, error) -> None:
        if self._active is None or run_id != self._active[0]:
            return
        _active_id, generation = self._active
        self._active = None
        self._active_call_ids = frozenset()
        error_callback = self._active_error_callback
        self._active_result_callback = None
        self._active_error_callback = None
        if self._pending is not None:
            self._set_status("Calculating the latest study values…")
            self._start_pending()
            return
        if generation == self._generation:
            self._set_status("Study calculation failed; entered values were kept.")
            if error_callback is not None:
                error_callback(error)
        else:
            self._set_status("")
        self._start_pending()

    def _progress(self, run_id, stage) -> None:
        if self._active is not None and run_id == self._active[0]:
            self._set_status(str(stage))

    def _busy_changed(self, busy: bool) -> None:
        if busy:
            return
        self._start_pending()

    def _set_status(self, message: str) -> None:
        self._status_label.setText(message)
        self._status_label.setVisible(bool(message))
        self._status_label.setAccessibleDescription(message)

    def _default_error(self, error: object) -> None:
        detail = (
            next((value for key, value in error.items() if key == "message"), None)
            if isinstance(error, Mapping)
            else None
        )
        self._set_status(
            "Study calculation failed; entered values were kept."
            + (f" {detail}" if isinstance(detail, str) and detail else "")
        )


def install_calculator_dialog_worker(dialog, worker_client):
    """Attach an accessible status line and request controller to a dialog."""
    label = QtWidgets.QLabel(dialog)
    label.setObjectName("calculator_worker_status")
    label.setAccessibleName("Study calculation status")
    label.setWordWrap(True)
    label.hide()
    layout = dialog.layout()
    button_box = getattr(dialog, "buttonBox", None)
    if layout is not None:
        button_index = layout.indexOf(button_box) if button_box is not None else -1
        if button_index >= 0:
            layout.insertWidget(button_index, label)
        else:
            layout.addWidget(label)
    requests = CalculatorDialogRequests(worker_client, label)
    dialog.finished.connect(lambda *_args: requests.close())
    return label, requests
