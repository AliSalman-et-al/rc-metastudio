"""Packaged qualification of an owned worker analysis and retained result."""

from __future__ import annotations

import os
from pathlib import Path
import sys

from rc_metastudio.automation import _close_automation_window, _write_json, start_automation


def _await_worker(client, action, success_signal, *, timeout_ms=120000):
    """Wait for one product worker request while keeping the Qt UI responsive."""
    from PyQt6 import QtCore

    loop = QtCore.QEventLoop()
    outcome = {}

    def completed(*values):
        outcome["values"] = values
        loop.quit()

    def failed(_run_id, error):
        outcome["error"] = error
        loop.quit()

    timer = QtCore.QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    success_signal.connect(completed)
    client.failed.connect(failed)
    try:
        action()
        if not outcome:
            timer.start(timeout_ms)
            loop.exec()
        if "error" in outcome:
            raise RuntimeError("worker failed: %s" % outcome["error"])
        if "values" not in outcome:
            raise TimeoutError("worker did not finish within %s ms" % timeout_ms)
        return outcome["values"]
    finally:
        timer.stop()
        success_signal.disconnect(completed)
        client.failed.disconnect(failed)


def run_worker_journey(
    output_path: str, project_path: str, destination_path: str
) -> int:
    """Exercise the saved binary journey through the production worker route."""
    from unittest.mock import patch
    from PyQt6 import QtCore
    from rc_metastudio import analysis_setup_dialog, main_window, results_window

    print("worker journey: starting app", file=sys.stderr, flush=True)
    app, window = start_automation()
    reopened = None
    try:
        if "rpy2.robjects" in sys.modules:
            raise RuntimeError("qualification main process loaded R before the worker")
        source = os.path.abspath(project_path)
        destination = Path(destination_path).resolve()
        print("worker journey: opening project", file=sys.stderr, flush=True)
        if not window.open(source, raise_on_error=True):
            raise RuntimeError("sample project could not be opened")
        client = window.analysis_worker
        print("worker journey: loading methods", file=sys.stderr, flush=True)
        _await_worker(client, window.go, client.methodsReady)
        print("worker journey: methods ready", file=sys.stderr, flush=True)
        forms = window.findChildren(analysis_setup_dialog.AnalysisSetupDialog)
        if not forms:
            raise RuntimeError("worker method catalogue did not open analysis setup")
        form = forms[-1]
        method = "binary.random"
        label = next(
            (label for label, value in form.available_method_d.items() if value == method),
            None,
        )
        if label is None:
            raise RuntimeError("binary random-effects method is unavailable")
        form.method_cbo_box.setCurrentText(label)
        interactive = []

        def run_analysis():
            form.run_ma()
            QtCore.QTimer.singleShot(
                0, lambda: interactive.append(window.isVisible() and client.is_busy)
            )

        print("worker journey: running analysis", file=sys.stderr, flush=True)
        _await_worker(client, run_analysis, client.completed)
        print("worker journey: analysis completed", file=sys.stderr, flush=True)
        if "rpy2.robjects" in sys.modules:
            raise RuntimeError("qualification analysis loaded R into the main process")
        saved = window.workspace.list_saved_analyses()
        if len(saved) != 1:
            raise RuntimeError("worker result was not retained as one saved analysis")
        record_id = str(saved[0]["id"])

        print("worker journey: loading retry methods", file=sys.stderr, flush=True)
        _await_worker(client, window.go, client.methodsReady)
        print("worker journey: retry methods ready", file=sys.stderr, flush=True)
        retry_form = window.findChildren(analysis_setup_dialog.AnalysisSetupDialog)[-1]
        retry_form.method_cbo_box.setCurrentText(label)
        stopped = {}
        stop_loop = QtCore.QEventLoop()

        def stopped_run(_run_id, error):
            stopped["error"] = error
            stop_loop.quit()

        client.failed.connect(stopped_run)
        try:
            print("worker journey: starting stopped run", file=sys.stderr, flush=True)
            retry_form.run_ma()
            progress = retry_form._worker_progress_dialog
            if progress is None:
                raise RuntimeError("worker run did not expose a stop control")
            print("worker journey: requesting stop", file=sys.stderr, flush=True)
            progress.stop_button.click()
            if not stopped:
                QtCore.QTimer.singleShot(30000, stop_loop.quit)
                stop_loop.exec()
            print("worker journey: stop loop completed", file=sys.stderr, flush=True)
        finally:
            client.failed.disconnect(stopped_run)
        if (
            stopped.get("error", {}).get("type") != "AnalysisStoppedError"
            or not retry_form.isVisible()
            or len(window.workspace.list_saved_analyses()) != 1
        ):
            raise RuntimeError("stopped run did not preserve settings and saved history")
        stopped_settings_retained = retry_form.isVisible()
        retry_form._emit_draft_change()
        retry_form.cancel()
        if len(window.workspace.list_analysis_drafts()) != 1:
            raise RuntimeError("stopped run did not retain an editable analysis draft")

        destination.parent.mkdir(parents=True, exist_ok=True)
        print("worker journey: saving project", file=sys.stderr, flush=True)
        window.out_path = str(destination)
        def unexpected_warning(_parent, title, message, *_args):
            raise RuntimeError("unexpected warning during saved journey: %s: %s" % (title, message))

        with patch.object(main_window.QMessageBox, "warning", side_effect=unexpected_warning), patch.object(
            main_window.QMessageBox, "critical", side_effect=unexpected_warning
        ):
            save_succeeded = window.save()
        if save_succeeded is not True:
            raise RuntimeError("worker result project could not be saved")
        print("worker journey: project saved", file=sys.stderr, flush=True)

        reopened = main_window.MainWindow()
        reopened.workspace.mark_saved()
        if not reopened.open(str(destination), raise_on_error=True):
            raise RuntimeError("saved worker result project could not be reopened")
        reopened._open_saved_analysis(record_id)
        viewers = reopened.findChildren(results_window.ResultsWindow)
        if len(viewers) != 1:
            raise RuntimeError("reopened result did not open in the native viewer")
        viewer = viewers[0]
        images = [
            (key, path) for key, path in viewer.images.items()
            if path and Path(path).is_file()
        ]
        if not images:
            raise RuntimeError("saved result has no portable figure to export")
        figure_key, figure_path = images[0]
        artifact = viewer.create_plot_artifact(figure_key, figure_path)
        export_path = destination.with_suffix(".png")
        with patch.object(
            results_window.QFileDialog,
            "getSaveFileName",
            return_value=(str(export_path), "PNG"),
        ), patch.object(
            viewer.plot_service,
            "export",
            side_effect=AssertionError("stored figure export called R"),
        ):
            viewer.save_image_as(artifact, format="png")
        if not export_path.is_file() or export_path.stat().st_size == 0:
            raise RuntimeError("saved result figure could not be exported offline")

        _write_json(output_path, {
            "source_project": source,
            "saved_project": str(destination),
            "worker_completed": True,
            "event_loop_responsive": bool(interactive and interactive[0]),
            "stop_acknowledged": True,
            "stopped_settings_retained": stopped_settings_retained,
            "reopened_draft_count": len(reopened.workspace.list_analysis_drafts()),
            "saved_analysis_id": record_id,
            "saved_analysis_status": saved[0]["status"],
            "reopened_analysis_count": len(reopened.workspace.list_saved_analyses()),
            "reopened_figure_key": figure_key,
            "offline_export": str(export_path),
            "offline_export_bytes": export_path.stat().st_size,
            "backend_versions": saved[0]["backend_versions"],
        })
        return 0
    finally:
        if reopened is not None:
            _close_automation_window(app, reopened)
        _close_automation_window(app, window)
