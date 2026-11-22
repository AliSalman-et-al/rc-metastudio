# SPDX-License-Identifier: GPL-3.0-or-later
"""Supervise the desktop's private R process and its single active request."""

import atexit
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import json
import logging
import math
import os
from pathlib import Path
import re
import sys
from typing import Literal, TypedDict, cast
import weakref

from PyQt6.QtCore import QCoreApplication, QEventLoop, QObject, QProcess, QProcessEnvironment, QTemporaryDir, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QProgressDialog

from rc_metastudio import r_runtime
from rc_metastudio.rcmetar_identity import expected_source, runtime_versions
from rc_metastudio.r_worker_lifetime import WindowsWorkerJob, kill_worker_group, worker_command


_PROTOCOL = 1
_MAGIC = b"\x1eRCMS"
_FRAME_LIMIT = 16 * 1024**2
_STARTUP_MS = 90_000
CALCULATOR_DEADLINE_MS = 30_000
PREVIEW_DEADLINE_MS = 30_000
_CANCEL_MS = 1_500
_HEARTBEAT_MS = 10_000
_LOG = logging.getLogger(__name__)

CalculatorKind = Literal[
    "binary_effect", "continuous_effect", "diagnostic_effect", "scale",
    "binary_impute", "diagnostic_impute", "continuous_impute", "pre_post", "back_calculate",
]


class CalculatorJob(TypedDict):
    type: Literal["calculator"]
    kind: CalculatorKind
    args: Mapping[str, object]
    vector: bool


class PreviewJob(TypedDict):
    type: Literal["previews"]
    family: str
    metric: str
    metrics: Sequence[str]
    rows: Sequence[Sequence[float | None]]
    two_arm: bool
    confidence: float


WorkerJob = CalculatorJob | PreviewJob


class _Reply(TypedDict):
    protocol: int
    id: int
    status: Literal["ok", "error", "cancelled", "progress"]
    result: object
    message: str | None


class RWorkerError(r_runtime.AnalysisBackendUnavailableError):
    """The job did not complete and its changes must not be published."""


@dataclass
class _Pending:
    id: int
    reply: _Reply | None = None
    error: str | None = None
    cancelled: bool = False

    def finished(self) -> bool:
        return self.reply is not None or self.error is not None


def enabled() -> bool:
    return os.environ.get("RCMS_R_BACKEND") == "worker"


def _encode_numbers(value: object) -> object:
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return None
        return {"$num": "+Inf" if value > 0 else "-Inf"}
    if isinstance(value, Mapping):
        return {key: _encode_numbers(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_encode_numbers(item) for item in value]
    return value


def _decode_number(value: dict[str, object]) -> object:
    match value:
        case {"$num": "+Inf"} if len(value) == 1:
            return math.inf
        case {"$num": "-Inf"} if len(value) == 1:
            return -math.inf
    if "$num" in value:
        raise ValueError("invalid wire number")
    return value


def _frame(job_id: int, job: object) -> bytes:
    data = json.dumps(
        {"protocol": _PROTOCOL, "id": job_id, "job": _encode_numbers(job)},
        ensure_ascii=False, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    if len(data) > _FRAME_LIMIT:
        raise ValueError("The R worker request is too large.")
    return _MAGIC + f"{len(data):08x}".encode("ascii") + data


def _runtime_paths() -> tuple[Path, Path]:
    if not os.environ.get("R_HOME"):
        r_runtime.configure_bundled_r_environment()
    if not (home := os.environ.get("R_HOME")):
        raise RWorkerError("The R worker could not locate R. Reinstall the configured R runtime.")
    r_home = Path(home)
    program = r_home / ("bin/x64/Rterm.exe" if sys.platform == "win32" else "bin/R")
    libraries = [Path(path) for name in ("R_LIBS", "R_LIBS_USER", "R_LIBS_SITE")
                 for path in os.environ.get(name, "").split(os.pathsep) if path]
    libraries.append(r_home / "library")
    candidates = (lib / "RCMetaR/worker.R" for lib in libraries)
    script = next((path for path in candidates if path.is_file()), None)
    if script is None or not program.is_file():
        raise RWorkerError("The R worker executable or script is missing. Reinstall the configured R runtime.")
    return program, script


class RWorker(QObject):
    changed = pyqtSignal()
    progress = pyqtSignal(object)
    heartbeat_missing = pyqtSignal(bool)

    def __init__(self, app: QCoreApplication):
        super().__init__(app)
        version, source = expected_source()
        self._startup = _frame(0, {"version": version, "source": source, "pins": runtime_versions()})
        program, script = _runtime_paths()
        executable, args = worker_command(str(program), ["--vanilla", "--no-echo", "-f", str(script)])
        self._process = QProcess(self)
        self._process.setProgram(executable)
        self._process.setArguments(args)
        self._process.started.connect(self._started)
        self._process.readyReadStandardOutput.connect(self._read_reply)
        self._process.readyReadStandardError.connect(self._read_stderr)
        self._process.finished.connect(self._exited)
        self._process.errorOccurred.connect(self._process_error)
        self._deadline = QTimer(self)
        self._deadline.setSingleShot(True)
        self._deadline.timeout.connect(self._timed_out)
        self._startup_timer = QTimer(self)
        self._startup_timer.setSingleShot(True)
        self._startup_timer.timeout.connect(
            lambda: self._interrupt("The R worker could not finish starting in time."),
        )
        self._heartbeat = QTimer(self)
        self._heartbeat.setSingleShot(True)
        self._heartbeat.timeout.connect(lambda: self.heartbeat_missing.emit(True))
        self._watch_heartbeat = False
        self._ready = False
        self._restart = False
        self._start_scheduled = False
        self._windows_job: WindowsWorkerJob | None = None
        self._closed = False
        self._startup_error: str | None = None
        self._startup_stderr = ""
        self._pending: _Pending | None = None
        self._job_id = 0
        self._buffer = bytearray()
        self._control: QTemporaryDir | None = None
        app.aboutToQuit.connect(self.close)
        worker = weakref.ref(self)

        def close_if_alive() -> None:
            from PyQt6.sip import isdeleted

            if (live := worker()) is not None and not isdeleted(live):
                live.close()

        atexit.register(close_if_alive)
        self._start()

    @property
    def pid(self) -> int:
        return int(self._process.processId())

    def _start(self) -> None:
        self._start_scheduled = False
        if self._closed:
            return
        self._restart = False
        self._buffer.clear()
        self._startup_stderr = ""
        self._control = QTemporaryDir()
        if not self._control.isValid():
            self._startup_error = "Could not create the R worker's temporary directory."
            self.changed.emit()
            return
        env = QProcessEnvironment.systemEnvironment()
        directory = self._control.path()
        for name in ("RCMS_WORKER_CONTROL", "TMPDIR", "TMP", "TEMP"):
            env.insert(name, directory)
        self._process.setProcessEnvironment(env)
        self._startup_timer.start(_STARTUP_MS)
        self._process.start()

    def _started(self) -> None:
        try:
            if sys.platform == "win32":
                self._windows_job = WindowsWorkerJob(self.pid)
        except OSError as error:
            _LOG.warning("Could not supervise R worker: %s", error)
            self._interrupt("The R worker could not be bound to the desktop process.")
            return
        if self._process.write(self._startup) != len(self._startup):
            self._interrupt("Could not send the R worker startup request.")

    def _read_stderr(self) -> None:
        data = bytes(self._process.readAllStandardError())
        if data:
            tail = data[-4096:].decode("utf-8", errors="replace").rstrip()
            if self._startup_timer.isActive():
                self._startup_stderr = tail
            _LOG.info("R worker stderr: %s", tail)

    def _read_reply(self) -> None:
        if self._restart or self._closed:
            self._process.readAllStandardOutput()
            return
        self._buffer.extend(bytes(self._process.readAllStandardOutput()))
        try:
            while (reply := self._take_frame()) is not None:
                self._accept_reply(reply)
        except ValueError as error:
            _LOG.warning("Invalid R worker reply: %s", error)
            self._interrupt("The R worker sent an invalid response and will restart. Try again.")

    def _take_frame(self) -> _Reply | None:
        marker = self._buffer.find(_MAGIC)
        if marker < 0:
            marker = max(0, len(self._buffer) - len(_MAGIC) + 1)
        if marker:
            _LOG.warning("Ignored %d bytes on R worker stdout: %r", marker, bytes(self._buffer[:min(marker, 256)]))
            del self._buffer[:marker]
        start = len(_MAGIC) + 8
        if len(self._buffer) < start:
            return None
        header = self._buffer[len(_MAGIC):start]
        if not re.fullmatch(b"[0-9a-f]{8}", header):
            raise ValueError("invalid frame header")
        length = int(header, 16)
        if not 0 < length <= _FRAME_LIMIT:
            raise ValueError("invalid frame length")
        end = start + length
        if len(self._buffer) < end:
            return None
        reply = json.loads(self._buffer[start:end].decode("utf-8"), object_hook=_decode_number)
        del self._buffer[:end]
        return _parse_reply(reply)

    def _accept_reply(self, reply: _Reply) -> None:
        if reply["status"] == "progress":
            self._accept_progress(reply)
            return
        if not self._ready and reply["id"] == 0:
            if reply["status"] == "ok":
                self._ready = True
            else:
                self._startup_error = f"The R worker could not start. {reply['message']}"
        elif self._ready and self._pending is not None and reply["id"] == self._pending.id:
            if self._pending.finished():
                raise ValueError("duplicate response")
            self._pending.reply = reply
        else:
            raise ValueError("unexpected response ID")
        self._deadline.stop()
        self._startup_timer.stop()
        self._heartbeat.stop()
        self.changed.emit()

    def _accept_progress(self, reply: _Reply) -> None:
        if not self._ready or self._pending is None or self._pending.finished() or reply["id"] != self._pending.id:
            raise ValueError("unexpected progress response")
        if self._watch_heartbeat:
            self._heartbeat.start(_HEARTBEAT_MS)
            self.heartbeat_missing.emit(False)
        self.progress.emit(reply["result"])

    def _fail(self, message: str) -> None:
        if self._ready:
            self._restart = True
            self._ready = False
            if self._pending is not None and not self._pending.finished():
                self._pending.error = message
        elif not self._restart and self._startup_error is None:
            self._startup_error = message
        self._deadline.stop()
        self._startup_timer.stop()
        self.changed.emit()

    def _interrupt(self, message: str) -> None:
        self._fail(message)
        if self._process.state() == QProcess.ProcessState.NotRunning:
            self._schedule_restart()
        else:
            self._kill()

    def _kill(self) -> None:
        if self._windows_job is not None:
            self._windows_job.close()
            self._windows_job = None
        try:
            kill_worker_group(self.pid)
        except OSError as error:
            _LOG.warning("Could not terminate R worker group: %s", error)
        finally:
            self._process.kill()

    def _schedule_restart(self) -> None:
        if self._restart and not self._start_scheduled:
            self._start_scheduled = True
            QTimer.singleShot(0, self._start)

    def _timed_out(self) -> None:
        self._interrupt("The R worker did not respond in time and will restart. Try again.")

    def _exited(self, _exit_code: int, _exit_status: QProcess.ExitStatus) -> None:
        if self._windows_job is not None:
            self._windows_job.close()
            self._windows_job = None
        if self._closed:
            return
        if self._startup_timer.isActive() and self._startup_stderr:
            self._fail(f"The R worker could not start. {self._startup_stderr}")
        else:
            self._fail("The R worker stopped and will restart. Try again.")
        self._schedule_restart()

    def _process_error(self, error: QProcess.ProcessError) -> None:
        if not self._closed and error == QProcess.ProcessError.FailedToStart:
            self._startup_error = f"The R worker could not start. {self._process.errorString()}"
            self._fail(self._startup_error)

    def ensure_ready(self) -> None:
        self._wait(lambda: self._ready or self._startup_error is not None or self._closed)
        if not self._ready:
            raise RWorkerError(self._startup_error or "The R worker is closed.")

    def _wait(self, done: Callable[[], bool], *, allow_input: bool = False, delay_ms: int = 0) -> None:
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        flags = QEventLoop.ProcessEventsFlag.AllEvents if allow_input else QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents
        self.changed.connect(loop.quit)
        try:
            if delay_ms:
                timer.start(delay_ms)
            while not done() and (not delay_ms or timer.isActive()):
                loop.exec(flags)
        finally:
            self.changed.disconnect(loop.quit)

    def call(self, job: WorkerJob, *, timeout_ms: int | None) -> object:
        # The bridge also guards reentry while both backends coexist.
        if self._pending is not None:
            raise RWorkerError("Another R job is running.")
        self.ensure_ready()
        self._job_id += 1
        payload = _frame(self._job_id, job)
        pending = _Pending(self._job_id)
        self._pending = pending
        assert self._control is not None
        marker = Path(self._control.path()) / f"{pending.id}.cancel"
        try:
            if timeout_ms is None:
                self._watch_heartbeat = True
                self._heartbeat.start(_HEARTBEAT_MS)
            else:
                self._deadline.start(timeout_ms)
            if self._process.write(payload) != len(payload):
                self._interrupt("Could not send the R job. The R worker will restart. Try again.")
            self._wait(pending.finished, delay_ms=200)
            if not pending.finished():
                self._wait_with_cancel(job, pending, marker)
            return _job_result(pending)
        finally:
            self._deadline.stop()
            self._heartbeat.stop()
            self._watch_heartbeat = False
            self._pending = None
            marker.unlink(missing_ok=True)

    def _wait_with_cancel(self, job: WorkerJob, pending: _Pending, marker: Path) -> None:
        label = "Calculating study previews…" if job["type"] == "previews" else "Calculating study effects…"
        dialog = QProgressDialog(label, "Cancel", 0, 0, QApplication.activeWindow())
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.setMinimumDuration(0)

        def cancel() -> None:
            if pending.finished() or pending.cancelled:
                return
            pending.cancelled = True
            dialog.setLabelText("Cancelling…")
            dialog.setCancelButton(None)
            dialog.show()
            try:
                marker.touch()
            except OSError:
                self._interrupt("The R job was cancelled and the R worker will restart.")
            else:
                self._deadline.start(_CANCEL_MS)
            self.changed.emit()

        def show_heartbeat(missed: bool) -> None:
            if not pending.cancelled:
                dialog.setLabelText("Waiting for R to report progress…" if missed else label)

        dialog.canceled.connect(cancel)
        self.heartbeat_missing.connect(show_heartbeat)
        dialog.show()
        try:
            self._wait(lambda: pending.cancelled or pending.finished(), allow_input=True)
            self._wait(pending.finished)
        finally:
            dialog.canceled.disconnect(cancel)
            self.heartbeat_missing.disconnect(show_heartbeat)
            dialog.deleteLater()
            dialog.hide()

    def close(self) -> None:
        self._closed = True
        self._ready = False
        self._deadline.stop()
        self._startup_timer.stop()
        if self._pending is not None:
            self._pending.error = "The R worker is closed."
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._kill()
            self._process.waitForFinished(2000)
        self._control = None
        self.changed.emit()


def _parse_reply(reply: object) -> _Reply:
    if not isinstance(reply, dict):
        raise ValueError("expected a response object")
    if type(reply.get("protocol")) is not int or reply["protocol"] != _PROTOCOL or type(reply.get("id")) is not int:
        raise ValueError("invalid response protocol or ID")
    if reply.get("status") not in ("ok", "error", "cancelled", "progress") or "result" not in reply or "message" not in reply:
        raise ValueError("invalid response contents")
    if reply["status"] == "error":
        if not isinstance(reply["message"], str):
            raise ValueError("missing error message")
    elif reply["message"] is not None:
        raise ValueError("unexpected error message")
    return cast(_Reply, reply)


def _job_result(pending: _Pending) -> object:
    reply = pending.reply
    if pending.cancelled or (reply is not None and reply["status"] == "cancelled"):
        raise RWorkerError("The R job was cancelled.")
    if pending.error is not None:
        raise RWorkerError(pending.error)
    assert reply is not None
    if reply["status"] != "ok":
        raise ValueError(f"R could not complete the calculation. {reply['message']}")
    return reply["result"]


def current_worker() -> RWorker:
    app = QCoreApplication.instance()
    if app is None:
        raise RWorkerError("The R worker needs the desktop application.")
    worker = app.findChild(RWorker, options=Qt.FindChildOption.FindDirectChildrenOnly)
    if worker is None:
        worker = RWorker(app)
    return worker


def study_previews(job: PreviewJob) -> list[list[tuple[float | None, ...]]]:
    result = current_worker().call(job, timeout_ms=PREVIEW_DEADLINE_MS)
    if not isinstance(result, list) or len(result) != len(job["rows"]):
        raise ValueError("The R worker returned an invalid study preview batch.")
    return [_preview_row(row, len(job["metrics"])) for row in result]


def _preview_row(row: object, metric_count: int) -> list[tuple[float | None, ...]]:
    if not isinstance(row, list) or len(row) != metric_count:
        raise ValueError("The R worker returned an invalid study preview row.")
    return [_preview_values(values) for values in row]


def _preview_values(values: object) -> tuple[float | None, ...]:
    if not isinstance(values, list) or len(values) != 6:
        raise ValueError("The R worker returned an invalid study preview.")
    return tuple(None if value is None else _preview_number(value) for value in values)


def _preview_number(value: object) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError("The R worker returned an invalid study preview number.")
    return float(value)
