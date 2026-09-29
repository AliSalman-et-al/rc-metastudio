"""Packaged qualification of an owned worker analysis and retained result."""

from __future__ import annotations

import hashlib
import json
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
    output_path: str, project_path: str, destination_path: str, *, route: str
) -> int:
    """Exercise exactly one bounded route in one fresh package process."""
    from unittest.mock import patch
    from PyQt6 import QtCore
    from rc_metastudio import analysis_setup_dialog, main_window, results_window

    output = Path(output_path).expanduser().resolve()
    source = Path(project_path).expanduser().resolve()
    destination = Path(destination_path).expanduser().resolve()
    binary_workflows = {
        "binary.standard": "standard",
        "binary.cumulative": "cumulative",
        "binary.leave-one-out": "leave-one-out",
    }
    family_routes = {
        "continuous.standard": ("continuous", "SMD", "continuous.random"),
        "diagnostic.standard": ("diagnostic", "Sens", "diagnostic.random"),
    }
    if route not in binary_workflows and route not in family_routes:
        raise ValueError("unsupported worker qualification route: %s" % route)

    app, window = start_automation()
    reopened = None
    try:
        if "rpy2.robjects" in sys.modules:
            raise RuntimeError("qualification main process loaded R before the worker")
        if route in family_routes:
            data_type, metric, method = family_routes[route]
            responsive = []
            evidence = _run_separate_family_journey(
                app,
                source,
                destination,
                window=window,
                data_type=data_type,
                metric=metric,
                method=method,
                event_loop_responsive=responsive,
            )
            _write_json(str(output), {
                "route": route,
                "worker_completed": True,
                "event_loop_responsive": bool(responsive and responsive[0]),
                "saved_analysis_status": evidence["status"],
                "reopened_analysis_count": 1,
                "analysis_runs": [evidence],
                "main_process_r_bridge_absent": "rpy2.robjects" not in sys.modules,
            })
            return 0

        workflow = binary_workflows[route]
        if not window.open(str(source), raise_on_error=True):
            raise RuntimeError("sample project could not be opened")
        if window.model.get_current_outcome_type() != "binary":
            raise RuntimeError("binary route sample does not contain binary data")
        if window.model.current_effect != "OR":
            window.model.current_effect = "OR"
            window._refresh_workspace_context()
        client = window.analysis_worker
        records = []
        if workflow != "standard":
            baseline = _run_worker_analysis(
                window,
                window.go,
                data_type="binary",
                metric="OR",
                workflow="standard",
                method="binary.random",
            )
            records.append(baseline)
        action = {
            "standard": window.go,
            "cumulative": window.cum_ma,
            "leave-one-out": window.loo_ma,
        }[workflow]
        responsive = []
        selected = _run_worker_analysis(
            window,
            action,
            data_type="binary",
            metric="OR",
            workflow=workflow,
            method="binary.random",
            event_loop_responsive=responsive,
        )
        records.append(selected)
        if "rpy2.robjects" in sys.modules:
            raise RuntimeError("qualification analysis loaded R into the main process")

        print("worker journey: loading retry methods", file=sys.stderr, flush=True)
        _await_worker(client, window.go, client.methodsReady)
        retry_forms = window.findChildren(analysis_setup_dialog.AnalysisSetupDialog)
        if not retry_forms:
            raise RuntimeError("retry method catalogue did not open analysis setup")
        retry_form = retry_forms[-1]
        method_label = next(
            (
                label
                for label, value in retry_form.available_method_d.items()
                if value == "binary.random"
            ),
            None,
        )
        if method_label is None:
            raise RuntimeError("binary random-effects retry method is unavailable")
        retry_form.method_cbo_box.setCurrentText(method_label)
        stopped = {}
        stop_loop = QtCore.QEventLoop()

        def stopped_run(_run_id, error):
            stopped["error"] = error
            stop_loop.quit()

        client.failed.connect(stopped_run)
        try:
            retry_form.run_ma()
            progress = retry_form._worker_progress_dialog
            if progress is None:
                raise RuntimeError("worker run did not expose a stop control")
            progress.stop_button.click()
            if not stopped:
                QtCore.QTimer.singleShot(30000, stop_loop.quit)
                stop_loop.exec()
        finally:
            client.failed.disconnect(stopped_run)
        if (
            stopped.get("error", {}).get("type") != "AnalysisStoppedError"
            or not retry_form.isVisible()
            or len(window.workspace.list_saved_analyses()) != len(records)
        ):
            raise RuntimeError("stopped run did not preserve settings and saved history")
        stopped_settings_retained = retry_form.isVisible()
        retry_form._emit_draft_change()
        retry_form.cancel()
        if len(window.workspace.list_analysis_drafts()) != 1:
            raise RuntimeError("stopped run did not retain an editable analysis draft")

        destination.parent.mkdir(parents=True, exist_ok=True)
        window.out_path = str(destination)

        def unexpected_warning(_parent, title, message, *_args):
            raise RuntimeError("unexpected warning during saved journey: %s: %s" % (title, message))

        with patch.object(main_window.QMessageBox, "warning", side_effect=unexpected_warning), patch.object(
            main_window.QMessageBox, "critical", side_effect=unexpected_warning
        ):
            if window.save() is not True:
                raise RuntimeError("worker result project could not be saved")

        reopened = main_window.MainWindow()
        reopened.workspace.mark_saved()
        if not reopened.open(str(destination), raise_on_error=True):
            raise RuntimeError("saved worker result project could not be reopened")
        reopened_saved = reopened.workspace.list_saved_analyses()
        if len(reopened_saved) != len(records):
            raise RuntimeError("reopened project lost one or more analysis results")
        for record, expected in zip(reopened_saved, records, strict=True):
            opened_evidence = _analysis_evidence(reopened, str(record["id"]))
            if not _same_analysis_evidence(expected, opened_evidence):
                raise RuntimeError("reopened project changed saved analysis evidence")
        selected["saved_reopened"] = True
        reopened._open_saved_analysis(records[0]["analysis_id"])
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
        if "rpy2.robjects" in sys.modules:
            raise RuntimeError("opening and exporting the saved result loaded R into the main process")

        _write_json(str(output), {
            "route": route,
            "worker_completed": True,
            "event_loop_responsive": bool(responsive and responsive[0]),
            "stop_acknowledged": True,
            "stopped_settings_retained": stopped_settings_retained,
            "saved_analysis_status": selected["status"],
            "reopened_analysis_count": len(reopened_saved),
            "reopened_draft_count": len(reopened.workspace.list_analysis_drafts()),
            "offline_export": str(export_path),
            "offline_export_bytes": export_path.stat().st_size,
            "analysis_runs": [selected],
            "main_process_r_bridge_absent": "rpy2.robjects" not in sys.modules,
        })
        return 0
    finally:
        if reopened is not None:
            _close_automation_window(app, reopened)
        _close_automation_window(app, window)


def _run_worker_analysis(
    window,
    action,
    *,
    data_type,
    metric,
    workflow,
    method,
    event_loop_responsive=None,
):
    from rc_metastudio import analysis_setup_dialog

    client = window.analysis_worker
    print("worker journey: requesting %s %s methods" % (data_type, workflow), file=sys.stderr, flush=True)
    _await_worker(client, action, client.methodsReady)
    print("worker journey: %s %s methods ready" % (data_type, workflow), file=sys.stderr, flush=True)
    forms = window.findChildren(analysis_setup_dialog.AnalysisSetupDialog)
    if not forms:
        raise RuntimeError("worker method catalogue did not open analysis setup")
    form = forms[-1]
    selected_workflow = form.analysis_type or "standard"
    if selected_workflow != workflow:
        raise RuntimeError("analysis setup opened the wrong workflow")
    label = next(
        (name for name, value in form.available_method_d.items() if value == method),
        None,
    )
    if label is None:
        raise RuntimeError("%s is unavailable for %s %s" % (method, data_type, metric))
    form.method_cbo_box.setCurrentText(label)
    before = len(window.workspace.list_saved_analyses())
    print("worker journey: running %s %s analysis" % (data_type, workflow), file=sys.stderr, flush=True)
    def run():
        form.run_ma()
        if event_loop_responsive is not None:
            from PyQt6 import QtCore

            QtCore.QTimer.singleShot(
                0,
                lambda: event_loop_responsive.append(
                    window.isVisible() and client.is_busy
                ),
            )

    _await_worker(client, run, client.completed)
    print("worker journey: %s %s analysis completed" % (data_type, workflow), file=sys.stderr, flush=True)
    if "rpy2.robjects" in sys.modules:
        raise RuntimeError("analysis loaded R into the main process")
    saved = window.workspace.list_saved_analyses()
    if len(saved) != before + 1:
        raise RuntimeError("analysis did not create one retained result")
    return _analysis_evidence(window, str(saved[-1]["id"]))


def _analysis_evidence(window, record_id):
    saved = window.workspace.get_saved_analysis(record_id)
    if saved is None:
        raise RuntimeError("saved analysis record is missing")
    record = saved.value
    specification = record.get("specification")
    snapshot = record.get("input_snapshot")
    result = record.get("results")
    if not isinstance(specification, dict) or not isinstance(snapshot, dict):
        raise RuntimeError("saved analysis is missing its input or specification")
    if not isinstance(result, dict):
        raise RuntimeError("saved analysis is missing its result")
    input_snapshot = snapshot.get("input_snapshot", snapshot)
    studies = input_snapshot.get("studies") if isinstance(input_snapshot, dict) else None
    texts = result.get("texts")
    if not isinstance(studies, list) or not studies or not isinstance(texts, dict) or not texts:
        raise RuntimeError("saved analysis has no study identity or result text")
    if any(not isinstance(study, dict) or not isinstance(study.get("name"), str) for study in studies):
        raise RuntimeError("saved analysis study identity is invalid")
    summary = json.dumps(texts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    status = record.get("status")
    if status != "complete":
        raise RuntimeError("analysis did not produce a complete retained result")
    input_identity = record.get("input_identity")
    if not isinstance(input_identity, str) or len(input_identity) != 64:
        raise RuntimeError("saved analysis has no stable input identity")
    return {
        "analysis_id": record_id,
        "data_type": specification.get("data_type"),
        "metric": specification.get("metric"),
        "workflow": specification.get("workflow"),
        "method": specification.get("method"),
        "status": status,
        "input_identity": input_identity,
        "study_order": [study["name"] for study in studies],
        "result_text_sha256": hashlib.sha256(summary.encode("utf-8")).hexdigest(),
        "warnings": record.get("warnings", []),
    }


def _same_analysis_evidence(left, right):
    return all(
        left.get(key) == right.get(key)
        for key in (
            "data_type",
            "metric",
            "workflow",
            "method",
            "status",
            "input_identity",
            "study_order",
            "result_text_sha256",
        )
    )


def _run_separate_family_journey(
    app,
    sample_path,
    destination,
    *,
    window=None,
    data_type,
    metric,
    method,
    event_loop_responsive=None,
):
    from unittest.mock import patch
    from rc_metastudio import main_window, results_window

    sample_path = Path(sample_path).resolve()
    destination = Path(destination).resolve()
    owns_window = window is None
    if not sample_path.is_file():
        raise RuntimeError("packaged %s sample project is missing" % data_type)
    if owns_window:
        print("worker journey: creating %s window" % data_type, file=sys.stderr, flush=True)
        window = main_window.MainWindow()
        print("worker journey: %s window created" % data_type, file=sys.stderr, flush=True)
    reopened = None
    try:
        window.workspace.mark_saved()
        print("worker journey: opening %s sample" % data_type, file=sys.stderr, flush=True)
        if not window.open(str(sample_path), raise_on_error=True):
            raise RuntimeError("packaged %s project could not be opened" % data_type)
        if window.model.get_current_outcome_type() != data_type:
            raise RuntimeError("packaged sample does not contain the expected family")
        if window.model.current_effect != metric:
            window.model.current_effect = metric
            window._refresh_workspace_context()
        evidence = _run_worker_analysis(
            window,
            window.go,
            data_type=data_type,
            metric=metric,
            workflow="standard",
            method=method,
            event_loop_responsive=event_loop_responsive,
        )
        print("worker journey: %s analysis completed" % data_type, file=sys.stderr, flush=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
        window.out_path = str(destination)

        def unexpected_warning(_parent, title, message, *_args):
            raise RuntimeError("unexpected warning during %s journey: %s: %s" % (data_type, title, message))

        with patch.object(main_window.QMessageBox, "warning", side_effect=unexpected_warning), patch.object(
            main_window.QMessageBox, "critical", side_effect=unexpected_warning
        ):
            if window.save() is not True:
                raise RuntimeError("packaged %s project could not be saved" % data_type)
        print("worker journey: %s project saved" % data_type, file=sys.stderr, flush=True)
        reopened = main_window.MainWindow()
        reopened.workspace.mark_saved()
        print("worker journey: reopening %s project" % data_type, file=sys.stderr, flush=True)
        if not reopened.open(str(destination), raise_on_error=True):
            raise RuntimeError("saved %s project could not be reopened" % data_type)
        print("worker journey: %s project reopened" % data_type, file=sys.stderr, flush=True)
        record = reopened.workspace.get_saved_analysis(evidence["analysis_id"])
        if record is None or not _same_analysis_evidence(
            evidence, _analysis_evidence(reopened, evidence["analysis_id"])
        ):
            raise RuntimeError("saved %s result changed after reopen" % data_type)
        reopened._open_saved_analysis(evidence["analysis_id"])
        print("worker journey: %s result opened" % data_type, file=sys.stderr, flush=True)
        viewers = reopened.findChildren(results_window.ResultsWindow)
        if len(viewers) != 1:
            raise RuntimeError("reopened %s result did not reach the native viewer" % data_type)
        if "rpy2.robjects" in sys.modules:
            raise RuntimeError("reopening %s result loaded R into the main process" % data_type)
        evidence["saved_reopened"] = True
        evidence["sample_project_sha256"] = hashlib.sha256(
            sample_path.read_bytes()
        ).hexdigest()
        return evidence
    finally:
        if reopened is not None:
            _close_automation_window(app, reopened)
        if owns_window:
            _close_automation_window(app, window)
