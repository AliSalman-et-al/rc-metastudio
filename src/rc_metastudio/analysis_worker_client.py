# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Qt owner for one isolated analysis child process at a time."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from collections.abc import Mapping, Sequence
from typing import Literal, TypedDict

from PyQt6 import QtCore
from PyQt6.QtCore import QProcess, QProcessEnvironment, pyqtSignal


class PlotArtifactIdentity(TypedDict):
    """Identity for rejecting plot results from an obsolete UI request."""

    analysis_id: str
    figure_key: str
    generation: int


PlotOperation = Literal["plot_parameters", "plot_export", "plot_edit"]
_PLOT_OPERATIONS = frozenset(("plot_parameters", "plot_export", "plot_edit"))
_PLOT_REGENERATORS = frozenset(("forest", "regression", "funnel", "sroc"))
_PLOT_EXTENSIONS = frozenset(("pdf", "png", "tif", "tiff", "svg"))


class AnalysisWorkerClient(QtCore.QObject):
    """Launch and own one analysis or plot worker process without a queue."""

    progress = pyqtSignal(str, str)
    completed = pyqtSignal(str, object, object, object)
    calculatorCompleted = pyqtSignal(str, object)
    methodsReady = pyqtSignal(str, object, object)
    plotProgress = pyqtSignal(str, str, object, str)
    plotCompleted = pyqtSignal(str, str, object, object)
    plotFailed = pyqtSignal(str, str, object, object)
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
        self._stop_error: dict[str, str] | None = None
        self._operation = "analysis"
        self._artifact_identity: PlotArtifactIdentity | None = None

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
            raise RuntimeError(
                "An analysis is already running; RC MetaStudio does not queue analyses."
            )
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
        self._start(run_id, payload, operation="analysis")

    def submit_meta_regression(
        self,
        run_id: str,
        input_snapshot: Mapping[str, object],
        request: Mapping[str, object],
    ) -> None:
        if self._process is not None:
            raise RuntimeError(
                "An analysis is already running; RC MetaStudio does not queue analyses."
            )
        payload = json.dumps(
            {
                "operation": "meta_regression",
                "run_id": run_id,
                "input": dict(input_snapshot),
                "request": dict(request),
            },
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        self._start(run_id, payload, operation="meta_regression")

    def submit_subgroup(
        self,
        run_id: str,
        input_snapshot: Mapping[str, object],
        request: Mapping[str, object],
        plan: Mapping[str, object],
    ) -> None:
        """Run one frozen subgroup request with its explicit missing policy."""
        if self._process is not None:
            raise RuntimeError(
                "An analysis is already running; RC MetaStudio does not queue analyses."
            )
        payload = json.dumps(
            {
                "operation": "subgroup",
                "run_id": run_id,
                "input": dict(input_snapshot),
                "request": dict(request),
                "subgroup_plan": dict(plan),
            },
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        self._start(run_id, payload, operation="subgroup")

    def submit_reitsma(
        self,
        run_id: str,
        input_snapshot: Mapping[str, object],
        request: Mapping[str, object],
        *,
        staging_dir: str | os.PathLike[str] | None = None,
    ) -> None:
        """Run one frozen count-based joint Reitsma request in the worker."""
        if self._process is not None:
            raise RuntimeError(
                "An analysis is already running; RC MetaStudio does not queue analyses."
            )
        request_payload: dict[str, object] = {
            "operation": "reitsma",
            "run_id": run_id,
            "input": dict(input_snapshot),
            "request": dict(request),
        }
        if staging_dir is not None:
            request_payload["staging_dir"] = _nonempty_path(
                staging_dir, "staging_dir"
            )
        payload = json.dumps(
            request_payload,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        self._start(run_id, payload, operation="reitsma")

    def submit_calculator(
        self, run_id: str, calls: Sequence[Mapping[str, object]]
    ) -> None:
        """Run an explicit batch of study calculator operations in the worker."""
        if self._process is not None:
            raise RuntimeError(
                "An analysis is already running; RC MetaStudio does not queue analyses."
            )
        payload = json.dumps(
            {
                "operation": "calculator",
                "run_id": run_id,
                "calls": [dict(call) for call in calls],
            },
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        self._start(run_id, payload, operation="calculator")

    def request_small_study_effects_preview(
        self,
        run_id: str,
        input_snapshot: Mapping[str, object],
        request: Mapping[str, object],
    ) -> None:
        """Check RCMetaR eligibility for one frozen small-study-effects request."""
        if self._process is not None:
            raise RuntimeError(
                "An analysis is already running; RC MetaStudio does not queue analyses."
            )
        payload = json.dumps(
            {
                "operation": "small_study_effects_preview",
                "run_id": run_id,
                "input": dict(input_snapshot),
                "request": dict(request),
            },
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        self._start(run_id, payload, operation="small_study_effects_preview")

    def submit_small_study_effects(
        self,
        run_id: str,
        input_snapshot: Mapping[str, object],
        request: Mapping[str, object],
        *,
        staging_dir: str | os.PathLike[str],
    ) -> None:
        """Run a frozen request and retain any R-generated figures for capture."""
        if self._process is not None:
            raise RuntimeError(
                "An analysis is already running; RC MetaStudio does not queue analyses."
            )
        staging_path = _nonempty_path(staging_dir, "staging_dir")
        payload = json.dumps(
            {
                "operation": "small_study_effects",
                "run_id": run_id,
                "input": dict(input_snapshot),
                "request": dict(request),
                "staging_dir": staging_path,
            },
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        self._start(run_id, payload, operation="small_study_effects")

    def request_methods(
        self,
        run_id: str,
        input_snapshot: Mapping[str, object],
        query: Mapping[str, object],
    ) -> None:
        """Load method metadata asynchronously in the isolated R process."""
        if self._process is not None:
            raise RuntimeError(
                "An analysis is already running; RC MetaStudio does not queue analyses."
            )
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
        self._start(run_id, payload, operation="methods")

    def request_plot_parameters(
        self,
        run_id: str,
        *,
        artifact_identity: Mapping[str, object],
        regenerator: str,
        params_path: str | os.PathLike[str],
        staging_dir: str | os.PathLike[str],
    ) -> None:
        """Load plot parameters from staged copies of the persisted sidecars.

        The caller creates and later removes ``staging_dir``.
        """
        payload = self._plot_payload(
            "plot_parameters",
            run_id,
            artifact_identity,
            regenerator,
            params_path,
            staging_dir,
        )
        self._start_plot(run_id, payload, "plot_parameters", artifact_identity)

    def request_plot_export(
        self,
        run_id: str,
        *,
        artifact_identity: Mapping[str, object],
        regenerator: str,
        params_path: str | os.PathLike[str],
        staging_dir: str | os.PathLike[str],
        output_extension: str,
    ) -> None:
        """Regenerate a plot into a caller-owned staging directory.

        The result's candidate image remains there until the caller promotes or
        discards it, then removes the staging directory.
        """
        payload = self._plot_payload(
            "plot_export",
            run_id,
            artifact_identity,
            regenerator,
            params_path,
            staging_dir,
        )
        payload["output_extension"] = _plot_extension(output_extension)
        self._start_plot(run_id, payload, "plot_export", artifact_identity)

    def edit_plot(
        self,
        run_id: str,
        *,
        artifact_identity: Mapping[str, object],
        regenerator: str,
        params_path: str | os.PathLike[str],
        staging_dir: str | os.PathLike[str],
        updated_params: Mapping[str, object],
        output_path: str | os.PathLike[str],
        output_extension: str,
        display_path: str | os.PathLike[str] | None = None,
    ) -> None:
        """Apply plot edits without writing into the stored artifact.

        ``output_path`` and optional ``display_path`` are the final destinations
        serialized in the staged parameter files. Rendering itself stays under
        ``staging_dir``; the caller promotes all candidate files together.
        """
        payload = self._plot_payload(
            "plot_edit",
            run_id,
            artifact_identity,
            regenerator,
            params_path,
            staging_dir,
        )
        payload["updated_params"] = dict(updated_params)
        payload["output_path"] = _nonempty_path(output_path, "output_path")
        payload["output_extension"] = _plot_extension(output_extension)
        if display_path is not None:
            payload["display_path"] = _nonempty_path(display_path, "display_path")
        self._start_plot(run_id, payload, "plot_edit", artifact_identity)

    def _plot_payload(
        self,
        operation: PlotOperation,
        run_id: str,
        artifact_identity: Mapping[str, object],
        regenerator: str,
        params_path: str | os.PathLike[str],
        staging_dir: str | os.PathLike[str],
    ) -> dict[str, object]:
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("plot worker request needs a run identity")
        if not isinstance(regenerator, str) or regenerator not in _PLOT_REGENERATORS:
            raise ValueError("unsupported plot regenerator: %s" % regenerator)
        identity = _plot_artifact_identity(artifact_identity)
        return {
            "operation": operation,
            "run_id": run_id,
            "artifact_identity": identity,
            "regenerator": regenerator,
            "params_path": _nonempty_path(params_path, "params_path"),
            "staging_dir": _nonempty_path(staging_dir, "staging_dir"),
        }

    def _start_plot(
        self,
        run_id: str,
        payload: Mapping[str, object],
        operation: PlotOperation,
        artifact_identity: Mapping[str, object],
    ) -> None:
        encoded = json.dumps(
            dict(payload), allow_nan=False, separators=(",", ":")
        ).encode("utf-8") + b"\n"
        self._start(
            run_id,
            encoded,
            operation=operation,
            artifact_identity=_plot_artifact_identity(artifact_identity),
        )

    def _start(
        self,
        run_id: str,
        payload: bytes,
        *,
        operation: str,
        artifact_identity: PlotArtifactIdentity | None = None,
    ) -> None:
        if self._process is not None:
            raise RuntimeError(
                "An analysis is already running; RC MetaStudio does not queue analyses."
            )
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
        self._stop_error = None
        self._operation = operation
        self._artifact_identity = artifact_identity
        self.busyChanged.emit(True)
        process.start()

    def stop(self) -> None:
        """Request worker termination; acknowledge it when the process exits."""
        process = self._process
        if process is None or self._stopping:
            return
        self._stopping = True
        self._stop_error = {
            "type": "AnalysisStoppedError",
            "message": "The analysis worker was stopped before it returned a result.",
            "details": "The worker process was terminated.",
        }
        if process.state() == QProcess.ProcessState.NotRunning:
            self._process_finished(process, process.exitCode(), process.exitStatus())
        else:
            process.kill()

    def stop_and_wait(self, timeout_ms: int = 3000) -> bool:
        """Finish worker ownership before a window or project is destroyed."""
        process = self._process
        if process is None:
            return True
        self.stop()
        if process is not self._process:
            return True
        if (
            process.state() != QProcess.ProcessState.NotRunning
            and not process.waitForFinished(timeout_ms)
        ):
            return False
        if process is self._process:
            self._process_finished(process, process.exitCode(), process.exitStatus())
        return True

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
            if self._operation in _PLOT_OPERATIONS:
                if not self._matches_plot_response(message):
                    continue
                if message_type == "progress" and isinstance(message.get("stage"), str):
                    self.plotProgress.emit(
                        self._run_id or "",
                        self._operation,
                        self._artifact_identity or {},
                        message["stage"],
                    )
                elif message_type == "plot_result" and isinstance(
                    message.get("result"), dict
                ):
                    self._response = message
                elif message_type == "failure":
                    self._response = message
                continue
            if message_type == "progress" and isinstance(message.get("stage"), str):
                self.progress.emit(self._run_id or "", message["stage"])
            elif message_type in {"result", "methods", "failure"}:
                self._response = message

    def _matches_plot_response(self, message: Mapping[str, object]) -> bool:
        return (
            message.get("operation") == self._operation
            and message.get("artifact_identity") == self._artifact_identity
        )

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
            run_id = self._run_id or ""
            operation = self._operation
            artifact_identity = self._artifact_identity or {}
            error = self._stop_error or {
                "type": "AnalysisStoppedError",
                "message": "The worker was stopped.",
            }
            self._dispose_process(process)
            if operation in _PLOT_OPERATIONS:
                self.plotFailed.emit(run_id, operation, artifact_identity, error)
            else:
                self.failed.emit(run_id, error)
            return
        self._read_stdout(process)
        self._read_stderr(process)
        response = self._response
        if (
            response is None
            or response.get("type") not in {"result", "methods", "plot_result"}
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
        operation = self._operation
        artifact_identity = self._artifact_identity
        self._dispose_process(process)
        if response.get("type") == "plot_result":
            self.plotCompleted.emit(
                run_id,
                operation,
                artifact_identity or {},
                result,
            )
        elif response.get("type") == "methods":
            self.methodsReady.emit(run_id, response.get("catalogue"), backend_versions)
        elif operation == "calculator":
            self.calculatorCompleted.emit(run_id, result)
        else:
            self.completed.emit(run_id, result, warnings, backend_versions)

    def _finish_failure(self, error: Mapping[str, object]) -> None:
        run_id = self._run_id or ""
        operation = self._operation
        artifact_identity = self._artifact_identity
        process = self._process
        if process is not None and process.state() != QProcess.ProcessState.NotRunning:
            self._stopping = True
            process.kill()
            process.waitForFinished(3000)
        self._dispose_process(process)
        if operation in _PLOT_OPERATIONS:
            self.plotFailed.emit(
                run_id,
                operation,
                artifact_identity or {},
                dict(error),
            )
        else:
            self.failed.emit(run_id, dict(error))

    def _dispose_process(self, process: QProcess | None) -> None:
        if process is None or process is not self._process:
            return
        self._process = None
        self._run_id = None
        self._response = None
        self._stopping = False
        self._stop_error = None
        self._operation = "analysis"
        self._artifact_identity = None
        process.deleteLater()
        self.busyChanged.emit(False)


def _worker_command() -> tuple[str, list[str]]:
    if getattr(sys, "frozen", False):
        return sys.executable, ["--analysis-worker"]
    return sys.executable, ["-m", "rc_metastudio", "--analysis-worker"]


def _plot_artifact_identity(value: Mapping[str, object]) -> PlotArtifactIdentity:
    if not isinstance(value, Mapping):
        raise ValueError("plot worker request needs an artifact identity")
    analysis_id = value.get("analysis_id")
    figure_key = value.get("figure_key")
    generation = value.get("generation")
    if (
        not isinstance(analysis_id, str)
        or not analysis_id
        or not isinstance(figure_key, str)
        or not figure_key
        or not isinstance(generation, int)
        or isinstance(generation, bool)
        or generation < 0
        or set(value) != {"analysis_id", "figure_key", "generation"}
    ):
        raise ValueError("plot artifact identity is invalid")
    return {
        "analysis_id": analysis_id,
        "figure_key": figure_key,
        "generation": generation,
    }


def _nonempty_path(value: str | os.PathLike[str], name: str) -> str:
    path = os.fspath(value)
    if not isinstance(path, str) or not path:
        raise ValueError("plot worker request needs %s" % name)
    return path


def _plot_extension(value: str) -> str:
    extension = str(value).lower().lstrip(".")
    if extension not in _PLOT_EXTENSIONS:
        raise ValueError("unsupported plot output format: %s" % value)
    return extension
