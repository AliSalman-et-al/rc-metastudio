# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt owner for one isolated analysis child process at a time."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from collections.abc import Mapping

from PyQt6 import QtCore
from PyQt6.QtCore import QProcess, QProcessEnvironment, pyqtSignal


class AnalysisWorkerClient(QtCore.QObject):
    """Launch and own one standard binary analysis process without a queue."""

    progress = pyqtSignal(str, str)
    completed = pyqtSignal(str, object, object, object)
    methodsReady = pyqtSignal(str, object, object)
    failed = pyqtSignal(str, object)
    busyChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process: QProcess | None = None
        self._run_id: str | None = None
        self._stdout = bytearray()
        self._stderr = bytearray()
        self._response: dict[str, object] | None = None
        self._stopping = False

    @property
    def is_busy(self) -> bool:
        return self._process is not None

    def submit(
        self,
        run_id: str,
        input_snapshot: Mapping[str, object],
        request: Mapping[str, object],
    ) -> None:
        if self._process is not None:
            raise RuntimeError("An analysis is already running; RC MetaStudio does not queue analyses.")
        payload = json.dumps(
            {
                "operation": "analysis",
                "run_id": run_id,
                "input": dict(input_snapshot),
                "request": dict(request),
            },
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        self._start(run_id, payload)

    def request_methods(
        self,
        run_id: str,
        input_snapshot: Mapping[str, object],
        query: Mapping[str, object],
    ) -> None:
        """Load method metadata asynchronously in the isolated R process."""
        if self._process is not None:
            raise RuntimeError("An analysis is already running; RC MetaStudio does not queue analyses.")
        payload = json.dumps(
            {
                "operation": "methods",
                "run_id": run_id,
                "input": dict(input_snapshot),
                "query": dict(query),
            },
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        self._start(run_id, payload)

    def _start(self, run_id: str, payload: bytes) -> None:
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        program, arguments = _worker_command()
        process.setProgram(program)
        process.setArguments(arguments)
        environment = QProcessEnvironment.systemEnvironment()
        if not getattr(sys, "frozen", False):
            source_root = str(Path(__file__).resolve().parents[1])
            python_path = environment.value("PYTHONPATH")
            environment.insert(
                "PYTHONPATH",
                os.pathsep.join(item for item in (source_root, python_path) if item),
            )
        process.setProcessEnvironment(environment)
        process.started.connect(lambda: self._write_request(process, payload))
        process.readyReadStandardOutput.connect(lambda: self._read_stdout(process))
        process.readyReadStandardError.connect(lambda: self._read_stderr(process))
        process.errorOccurred.connect(
            lambda error: self._process_error(process, error)
        )
        process.finished.connect(
            lambda exit_code, exit_status: self._process_finished(
                process, exit_code, exit_status
            )
        )
        self._process = process
        self._run_id = run_id
        self._stdout.clear()
        self._stderr.clear()
        self._response = None
        self._stopping = False
        self.busyChanged.emit(True)
        process.start()

    def stop(self) -> None:
        """Stop the active isolated worker and reject its pending run."""
        if self._process is None:
            return
        self._finish_failure(
            {
                "type": "AnalysisStoppedError",
                "message": "The analysis worker was stopped before it returned a result.",
                "details": "The worker process was terminated.",
            }
        )

    def _write_request(self, process: QProcess, payload: bytes) -> None:
        if process is self._process:
            process.write(payload)
            process.closeWriteChannel()

    def _read_stdout(self, process: QProcess) -> None:
        self._stdout.extend(bytes(process.readAllStandardOutput()))
        self._consume_messages()

    def _read_stderr(self, process: QProcess) -> None:
        self._stderr.extend(bytes(process.readAllStandardError()))

    def _consume_messages(self) -> None:
        while b"\n" in self._stdout:
            line, _, rest = self._stdout.partition(b"\n")
            self._stdout = bytearray(rest)
            if not line:
                continue
            try:
                message = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                self._response = {
                    "type": "failure",
                    "run_id": self._run_id,
                    "error": {
                        "type": type(error).__name__,
                        "message": "The analysis worker returned an invalid message.",
                        "details": bytes(line).decode("utf-8", errors="replace"),
                    },
                }
                continue
            if not isinstance(message, dict) or message.get("run_id") != self._run_id:
                continue
            message_type = message.get("type")
            if message_type == "progress" and isinstance(message.get("stage"), str):
                self.progress.emit(self._run_id or "", message["stage"])
            elif message_type in {"result", "methods", "failure"}:
                self._response = message

    def _process_error(self, process: QProcess, error: QProcess.ProcessError) -> None:
        if (
            process is not self._process
            or self._stopping
            or error != QProcess.ProcessError.FailedToStart
        ):
            return
        message = {
            "type": type(error).__name__,
            "message": (
                "The isolated R analysis worker could not start. Check that the "
                "bundled RCMetaR engine is installed and restart RC MetaStudio."
            ),
            "details": process.errorString(),
        }
        self._finish_failure(message)

    def _process_finished(
        self,
        process: QProcess,
        exit_code: int,
        exit_status: QProcess.ExitStatus,
    ) -> None:
        if process is not self._process:
            return
        if self._stopping:
            self._dispose_process(process)
            return
        self._read_stdout(process)
        self._read_stderr(process)
        response = self._response
        if (
            response is None
            or response.get("type") not in {"result", "methods"}
            or exit_code != 0
        ):
            error = response.get("error") if response is not None else None
            if not isinstance(error, Mapping):
                error = {
                    "type": "WorkerProcessError",
                    "message": "The analysis worker exited before returning a result.",
                    "details": bytes(self._stderr).decode("utf-8", errors="replace")
                    or process.errorString()
                    or f"Exit code: {exit_code}; status: {exit_status.name}",
                }
            self._finish_failure(dict(error))
            return
        run_id = self._run_id or ""
        result = response.get("result")
        warnings = response.get("warnings", [])
        backend_versions = response.get("backend_versions", {})
        self._dispose_process(process)
        if response.get("type") == "methods":
            self.methodsReady.emit(run_id, response.get("catalogue"), backend_versions)
        else:
            self.completed.emit(run_id, result, warnings, backend_versions)

    def _finish_failure(self, error: Mapping[str, object]) -> None:
        run_id = self._run_id or ""
        process = self._process
        if process is not None and process.state() != QProcess.ProcessState.NotRunning:
            self._stopping = True
            process.kill()
            process.waitForFinished(3000)
        self._dispose_process(process)
        self.failed.emit(run_id, dict(error))

    def _dispose_process(self, process: QProcess | None) -> None:
        if process is None or process is not self._process:
            return
        self._process = None
        self._run_id = None
        self._response = None
        self._stopping = False
        process.deleteLater()
        self.busyChanged.emit(False)


def _worker_command() -> tuple[str, list[str]]:
    if getattr(sys, "frozen", False):
        return sys.executable, ["--analysis-worker"]
    return sys.executable, ["-m", "rc_metastudio", "--analysis-worker"]
