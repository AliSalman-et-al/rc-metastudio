"""Packaged qualification of an owned worker analysis and retained result."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import sys


class _UnqualifiedRoute(RuntimeError):
    """A route has no defensible result for the available sample data."""

    def __init__(self, message, *, worker_completed=False):
        super().__init__(message)
        self.worker_completed = worker_completed


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


def _await_window_worker_idle(window, *, timeout_ms=30000):
    """Let pending raw-preview work finish before starting the selected route."""
    from PyQt6 import QtCore

    client = window.analysis_worker
    raw_preview_timer = getattr(window, "_raw_preview_timer", None)
    if not _window_has_pending_work(client, raw_preview_timer):
        return
    loop = QtCore.QEventLoop()
    poll = QtCore.QTimer()
    poll.setInterval(25)
    timeout = QtCore.QTimer()
    timeout.setSingleShot(True)
    stable_ms = 0

    def check_idle():
        nonlocal stable_ms
        if _window_has_pending_work(client, raw_preview_timer):
            stable_ms = 0
        else:
            stable_ms += poll.interval()
            if stable_ms >= 250:
                loop.quit()

    poll.timeout.connect(check_idle)
    timeout.timeout.connect(loop.quit)
    poll.start()
    timeout.start(timeout_ms)
    loop.exec()
    poll.stop()
    timeout.stop()
    if _window_has_pending_work(client, raw_preview_timer):
        raise TimeoutError("analysis worker did not become idle before subgroup setup")


def _window_has_pending_work(client, timer):
    return client.is_busy or (timer is not None and timer.isActive())


_BINARY_WORKFLOWS = {
    "binary.standard": "standard",
    "binary.cumulative": "cumulative",
    "binary.leave-one-out": "leave-one-out",
}
_FAMILY_ROUTES = {
    "continuous.standard": ("continuous", "SMD", "continuous.random"),
    "diagnostic.standard": ("diagnostic", "Sens", "diagnostic.random"),
    "binary.one-arm": ("binary", "PLO", "binary.random"),
    "continuous.entered-effect": ("continuous", "SMD", "continuous.random"),
}
_META_REGRESSION_ROUTES = {
    "binary.meta-regression": ("binary", "OR"),
    "continuous.meta-regression": ("continuous", "SMD"),
    "diagnostic.reitsma-meta-regression": ("diagnostic", "Sens"),
}
_SPECIAL_ROUTES = {
    "diagnostic.reitsma",
    "binary.small-study-effects",
    "binary.plot-edit",
    "diagnostic.subgroup",
}


def run_worker_journey(
    output_path: str,
    project_path: str,
    destination_path: str,
    *,
    route: str,
    start_application,
    close_window,
    write_evidence,
) -> int:
    """Exercise exactly one bounded route in one fresh package process."""
    from PyQt6 import QtCore
    from rc_metastudio import main_window

    output = Path(output_path).expanduser().resolve()
    source = Path(project_path).expanduser().resolve()
    destination = Path(destination_path).expanduser().resolve()
    if not _qualification_route_supported(route):
        raise ValueError("unsupported worker qualification route: %s" % route)
    app, window = start_application()
    if not isinstance(window, main_window.MainWindow):
        raise RuntimeError("qualification startup did not create a main window")
    reopened = None
    try:
        if "rpy2.robjects" in sys.modules:
            raise RuntimeError("qualification main process loaded R before the worker")
        if route in _FAMILY_ROUTES:
            return _run_family_qualification_route(
                app, window, source, destination, route, close_window,
                write_evidence, output,
            )
        if route in _META_REGRESSION_ROUTES or route in _SPECIAL_ROUTES:
            return _run_other_qualification_route(
                app, window, source, destination, route, close_window,
                write_evidence, output, QtCore,
            )
        reopened = _run_binary_qualification_route(
            app, window, source, destination, route, close_window,
            write_evidence, output, QtCore,
        )
        return 0
    finally:
        if reopened is not None:
            close_window(app, reopened)
        close_window(app, window)


def _qualification_route_supported(route):
    return (
        route in _BINARY_WORKFLOWS
        or route in _FAMILY_ROUTES
        or route in _META_REGRESSION_ROUTES
        or route in _SPECIAL_ROUTES
    )


def _run_family_qualification_route(
    app, window, source, destination, route, close_window, write_evidence, output
):
    data_type, metric, method = _FAMILY_ROUTES[route]
    prepare_model = {
        "binary.one-arm": _prepare_one_arm_binary,
        "continuous.entered-effect": _prepare_entered_effect_continuous,
    }.get(route)
    responsive = []
    try:
        evidence = _run_separate_family_journey(
            app, source, destination, window=window, data_type=data_type,
            metric=metric, method=method,
            route=route if route not in {"continuous.standard", "diagnostic.standard"} else None,
            prepare_model=prepare_model, event_loop_responsive=responsive,
            close_window=close_window,
        )
    except _UnqualifiedRoute as error:
        _write_unqualified_qualification(write_evidence, output, route, error)
        return 0
    write_evidence(str(output), {
        "route": route,
        "qualification_status": "complete",
        "worker_completed": True,
        "event_loop_responsive": bool(responsive and responsive[0]),
        "saved_analysis_status": evidence["status"],
        "reopened_analysis_count": 1,
        "analysis_runs": [evidence],
        "main_process_r_bridge_absent": "rpy2.robjects" not in sys.modules,
    })
    return 0


def _run_other_qualification_route(
    app, window, source, destination, route, close_window,
    write_evidence, output, qt_core,
):
    if route == "diagnostic.subgroup":
        return _run_subgroup_qualification_route(
            app, window, source, destination, route, close_window,
            write_evidence, output,
        )
    try:
        evidence = _run_meta_or_special_journey(
            app, window, source, destination, route, close_window
        )
    except _UnqualifiedRoute as error:
        _write_unqualified_qualification(write_evidence, output, route, error)
        return 0
    write_evidence(str(output), {
        "route": route,
        "qualification_status": "complete",
        "worker_completed": True,
        "event_loop_responsive": evidence.pop("event_loop_responsive", True),
        "saved_analysis_status": evidence["status"],
        "reopened_analysis_count": 1,
        "analysis_runs": [evidence],
        "main_process_r_bridge_absent": "rpy2.robjects" not in sys.modules,
    })
    return 0


def _run_meta_or_special_journey(app, window, source, destination, route, close_window):
    if route in _META_REGRESSION_ROUTES:
        data_type, metric = _META_REGRESSION_ROUTES[route]
        return _run_meta_regression_journey(
            app, source, destination, window=window, route=route,
            data_type=data_type, metric=metric, close_window=close_window,
        )
    return _run_special_family_journey(
        app, source, destination, window=window,
        route=route, close_window=close_window,
    )


def _run_subgroup_qualification_route(
    app, window, source, destination, route, close_window, write_evidence, output
):
    try:
        subgroup = _run_diagnostic_subgroup_journey(
            app, source, destination, window=window, close_window=close_window
        )
    except _UnqualifiedRoute as error:
        _write_unqualified_qualification(write_evidence, output, route, error)
        return 0
    write_evidence(str(output), {
        "route": route,
        "qualification_status": "complete",
        "worker_completed": True,
        "event_loop_responsive": subgroup["event_loop_responsive"],
        "saved_analysis_status": "complete",
        "reopened_analysis_count": subgroup["reopened_analysis_count"],
        "saved_edit_copy_opened": True,
        "live_project_confidence_level": 95.0,
        "saved_edit_copy_confidence_level": subgroup[
            "saved_edit_copy_confidence_level"
        ],
        "saved_edit_copy_missing_policy": subgroup[
            "saved_edit_copy_missing_policy"
        ],
        "analysis_runs": subgroup["analysis_runs"],
        "main_process_r_bridge_absent": "rpy2.robjects" not in sys.modules,
    })
    return 0


def _write_unqualified_qualification(write_evidence, output, route, error):
    write_evidence(str(output), {
        "route": route,
        "qualification_status": "unqualified",
        "details": str(error),
        "worker_completed": error.worker_completed,
        "main_process_r_bridge_absent": "rpy2.robjects" not in sys.modules,
    })


def _run_binary_qualification_route(
    app, window, source, destination, route, close_window,
    write_evidence, output, qt_core,
):
    return _run_binary_workflow(
        app, window, source, destination, route, close_window,
        write_evidence, output, qt_core,
    )

def _run_binary_workflow(
    app, window, source, destination, route, close_window,
    write_evidence, output, qt_core,
):
    from PyQt6 import QtCore
    from rc_metastudio import analysis_setup_dialog

    workflow = _BINARY_WORKFLOWS[route]
    _open_binary_project(window, source)
    records, selected, responsive = _run_binary_analyses(window, workflow)
    _require_worker_only_analysis()
    stopped_settings_retained = _stop_binary_retry_and_preserve_draft(
        window, len(records), analysis_setup_dialog, QtCore
    )
    _save_binary_project(app, window, destination)
    reopened, saved_count, draft_count, export_path, export_bytes = (
        _inspect_reopened_binary_project(
            app, destination, records, selected, route, close_window
        )
    )
    write_evidence(str(output), {
        "route": route,
        "worker_completed": True,
        "event_loop_responsive": bool(responsive and responsive[0]),
        "stop_acknowledged": True,
        "stopped_settings_retained": stopped_settings_retained,
        "saved_analysis_status": selected["status"],
        "reopened_analysis_count": saved_count,
        "reopened_draft_count": draft_count,
        "offline_export": str(export_path),
        "offline_export_bytes": export_bytes,
        "analysis_runs": [selected],
        "main_process_r_bridge_absent": "rpy2.robjects" not in sys.modules,
    })
    return reopened


def _open_binary_project(window, source):
    if not window.open(str(source), raise_on_error=True):
        raise RuntimeError("sample project could not be opened")
    if window.model.get_current_outcome_type() != "binary":
        raise RuntimeError("binary route sample does not contain binary data")
    _set_analysis_metric(window, "OR")


def _run_binary_analyses(window, workflow):
    records = []
    if workflow != "standard":
        records.append(_run_worker_analysis(
            window, window.go, data_type="binary", metric="OR",
            workflow="standard", method="binary.random",
        ))
    action = _binary_workflow_action(window, workflow)
    responsive = []
    selected = _run_worker_analysis(
        window, action, data_type="binary", metric="OR", workflow=workflow,
        method="binary.random", event_loop_responsive=responsive,
    )
    records.append(selected)
    return records, selected, responsive


def _binary_workflow_action(window, workflow):
    return {
        "standard": window.go,
        "cumulative": window.cum_ma,
        "leave-one-out": window.loo_ma,
    }[workflow]


def _require_worker_only_analysis():
    if "rpy2.robjects" in sys.modules:
        raise RuntimeError("qualification analysis loaded R into the main process")


def _stop_binary_retry_and_preserve_draft(window, expected_count, dialog_type, qt_core):
    client = window.analysis_worker
    form = _binary_retry_form(window, client, dialog_type)
    stopped = _stop_binary_retry(form, client, qt_core)
    if not _stopped_binary_run_preserved(window, form, stopped, expected_count):
        raise RuntimeError("stopped run did not preserve settings and saved history")
    retained_settings = form.isVisible()
    form._emit_draft_change()
    form.cancel()
    if len(window.workspace.list_analysis_drafts()) != 1:
        raise RuntimeError("stopped run did not retain an editable analysis draft")
    return retained_settings


def _binary_retry_form(window, client, dialog_type):
    print("worker journey: loading retry methods", file=sys.stderr, flush=True)
    _await_worker(client, window.go, client.methodsReady)
    forms = window.findChildren(dialog_type.AnalysisSetupDialog)
    if not forms:
        raise RuntimeError("retry method catalogue did not open analysis setup")
    form = forms[-1]
    label = next(
        (label for label, method in form.available_method_d.items()
         if method == "binary.random"),
        None,
    )
    if label is None:
        raise RuntimeError("binary random-effects retry method is unavailable")
    form.method_cbo_box.setCurrentText(label)
    return form


def _stop_binary_retry(form, client, qt_core):
    stopped = {}
    loop = qt_core.QEventLoop()

    def stopped_run(_run_id, error):
        stopped["error"] = error
        loop.quit()

    client.failed.connect(stopped_run)
    try:
        form.run_ma()
        progress = form._worker_progress_dialog
        if progress is None:
            raise RuntimeError("worker run did not expose a stop control")
        progress.stop_button.click()
        if not stopped:
            qt_core.QTimer.singleShot(30000, loop.quit)
            loop.exec()
    finally:
        client.failed.disconnect(stopped_run)
    return stopped


def _stopped_binary_run_preserved(window, form, stopped, expected_count):
    return (
        stopped.get("error", {}).get("type") == "AnalysisStoppedError"
        and form.isVisible()
        and len(window.workspace.list_saved_analyses()) == expected_count
    )


def _save_binary_project(app, window, destination):
    from rc_metastudio import main_window

    destination.parent.mkdir(parents=True, exist_ok=True)
    window.out_path = str(destination)
    _save_project_without_warnings(window, main_window, "worker result")
    _close_saved_journey_window(app, window, data_type="worker result")


def _inspect_reopened_binary_project(
    app, destination, records, selected, route, close_window
):
    from rc_metastudio import main_window, results_window

    reopened = main_window.MainWindow()
    try:
        saved = _open_binary_result_project(reopened, destination, records)
        _compare_binary_results(reopened, saved, records)
        selected["saved_reopened"] = True
        reopened._open_saved_analysis(records[0]["analysis_id"])
        viewer = _single_result_viewer(reopened, results_window)
        export_path, export_bytes = _export_binary_figure(
            viewer, destination, results_window
        )
        _require_worker_only_reopen()
        return (
            reopened, len(saved), len(reopened.workspace.list_analysis_drafts()),
            export_path, export_bytes,
        )
    except Exception:
        close_window(app, reopened)
        raise


def _open_binary_result_project(reopened, destination, expected_records):
    reopened.workspace.mark_saved()
    if not reopened.open(str(destination), raise_on_error=True):
        raise RuntimeError("saved worker result project could not be reopened")
    saved = reopened.workspace.list_saved_analyses()
    if len(saved) != len(expected_records):
        raise RuntimeError("reopened project lost one or more analysis results")
    return saved


def _compare_binary_results(reopened, saved, expected_records):
    for record, expected in zip(saved, expected_records, strict=True):
        opened = _analysis_evidence(reopened, str(record["id"]))
        if not _same_analysis_evidence(expected, opened):
            raise RuntimeError("reopened project changed saved analysis evidence")


def _single_result_viewer(window, results_window):
    viewers = window.findChildren(results_window.ResultsWindow)
    if len(viewers) != 1:
        raise RuntimeError("reopened result did not open in the native viewer")
    return viewers[0]


def _export_binary_figure(viewer, destination, results_window):
    from unittest.mock import patch

    images = [
        (key, path) for key, path in viewer.images.items()
        if path and Path(path).is_file()
    ]
    if not images:
        raise RuntimeError("saved result has no portable figure to export")
    key, path = images[0]
    artifact = viewer.create_plot_artifact(key, path)
    export_path = destination.with_suffix(".png")
    with patch.object(
        results_window.QFileDialog, "getSaveFileName",
        return_value=(str(export_path), "PNG"),
    ), patch.object(
        viewer.plot_service, "export",
        side_effect=AssertionError("stored figure export called R"),
    ):
        viewer.save_image_as(artifact, format="png")
    if not export_path.is_file() or export_path.stat().st_size == 0:
        raise RuntimeError("saved result figure could not be exported offline")
    return export_path, export_path.stat().st_size


def _require_worker_only_reopen():
    if "rpy2.robjects" in sys.modules:
        raise RuntimeError("opening and exporting the saved result loaded R into the main process")

def _run_worker_analysis(
    window,
    action,
    *,
    data_type,
    metric,
    workflow,
    method,
    qualification_route=None,
    event_loop_responsive=None,
):
    client, form, before = _prepare_worker_analysis_form(
        window, action, data_type, metric, workflow, method
    )
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
    return _analysis_evidence(
        window, str(saved[-1]["id"]), route=qualification_route
    )


def _prepare_worker_analysis_form(window, action, data_type, metric, workflow, method):
    from rc_metastudio import analysis_setup_dialog

    client = window.analysis_worker
    print("worker journey: requesting %s %s methods" % (data_type, workflow), file=sys.stderr, flush=True)
    _await_worker(client, action, client.methodsReady)
    print("worker journey: %s %s methods ready" % (data_type, workflow), file=sys.stderr, flush=True)
    forms = window.findChildren(analysis_setup_dialog.AnalysisSetupDialog)
    if not forms:
        raise RuntimeError("worker method catalogue did not open analysis setup")
    form = forms[-1]
    if (form.analysis_type or "standard") != workflow:
        raise RuntimeError("analysis setup opened the wrong workflow")
    label = next(
        (name for name, value in form.available_method_d.items() if value == method),
        None,
    )
    if label is None:
        raise RuntimeError("%s is unavailable for %s %s" % (method, data_type, metric))
    form.method_cbo_box.setCurrentText(label)
    return client, form, len(window.workspace.list_saved_analyses())


def _analysis_evidence(window, record_id, *, route=None):
    saved = window.workspace.get_saved_analysis(record_id)
    if saved is None:
        raise RuntimeError("saved analysis record is missing")
    record = saved.value
    evidence_data = _analysis_evidence_data(record, route)
    if evidence_data is None:
        raise RuntimeError("saved analysis record has invalid identity or result text")
    specification, status, input_identity, study_order, result_hash = evidence_data
    evidence = {
        "analysis_id": record_id,
        "data_type": specification.get("data_type"),
        "metric": specification.get("metric"),
        "workflow": specification.get("workflow"),
        "method": specification.get("method"),
        "status": status,
        "input_identity": input_identity,
        "study_order": study_order,
        "result_text_sha256": result_hash,
        "warnings": record.get("warnings", []),
    }
    if route is None:
        return evidence
    route_evidence = _route_result_evidence(route, record)
    if route_evidence is None:
        if route == "binary.plot-edit":
            raise _UnqualifiedRoute(
                "binary.plot-edit has no available result (%s)"
                % _plot_edit_result_details(record)
            )
        raise _UnqualifiedRoute(
            "%s produced no available numerical or semantic result" % route
        )
    evidence["result_evidence"] = route_evidence
    route_spec = _qualification_route_identity(route)
    if route_spec is not None:
        evidence.update(dict(zip(
            ("data_type", "workflow", "metric", "method"),
            route_spec,
            strict=True,
        )))
    return evidence


def _plot_edit_result_details(record):
    results = record.get("results")
    snapshot = record.get("input_snapshot")
    if isinstance(snapshot, dict) and isinstance(snapshot.get("input_snapshot"), dict):
        snapshot = snapshot["input_snapshot"]
    if not isinstance(results, dict):
        return "result payload missing"
    images = results.get("images")
    sections = results.get("sections")
    studies = snapshot.get("studies") if isinstance(snapshot, dict) else None
    section_statuses = [
        (section.get("source_key"), section.get("status"))
        for section in sections
        if isinstance(section, dict)
    ] if isinstance(sections, list) else []
    error_fields = sorted(
        key for key in results if "error" in key.lower()
    )
    numerics = results.get("binary_numerics")
    pooled = numerics.get("pooled") if isinstance(numerics, dict) else None
    return "result_status=%s result_fields=%s image_keys=%s numeric_fields=%s pooled_binary_numerics=%s section_statuses=%s worker_error_fields=%s study_count=%s" % (
        results.get("status"),
        sorted(results),
        sorted(images) if isinstance(images, dict) else [],
        sorted(key for key in results if key.endswith("_numerics")),
        pooled,
        section_statuses,
        error_fields,
        len(studies) if isinstance(studies, list) else "missing",
    )


def _analysis_evidence_data(record, route):
    specification, snapshot, result = _analysis_record_parts(record)
    input_snapshot = snapshot.get("input_snapshot", snapshot)
    studies = _analysis_studies(input_snapshot)
    texts = _analysis_texts(result)
    study_order = _analysis_study_names(studies)
    if study_order is None:
        raise RuntimeError("saved analysis study identity is invalid")
    status = _complete_analysis_status(record, route)
    input_identity = _analysis_input_identity(record)
    result_hash = hashlib.sha256(texts.encode("utf-8")).hexdigest()
    return specification, status, input_identity, study_order, result_hash


def _analysis_record_parts(record):
    specification = record.get("specification")
    snapshot = record.get("input_snapshot")
    result = record.get("results")
    if not isinstance(specification, dict) or not isinstance(snapshot, dict):
        raise RuntimeError("saved analysis is missing its input or specification")
    if not isinstance(result, dict):
        raise RuntimeError("saved analysis is missing its result")
    return specification, snapshot, result


def _analysis_studies(snapshot):
    if not isinstance(snapshot, dict):
        raise RuntimeError("saved analysis has no input snapshot")
    studies = snapshot.get("studies")
    if not isinstance(studies, list) or not studies:
        raise RuntimeError("saved analysis has no study identity")
    return studies


def _analysis_texts(result):
    texts = result.get("texts")
    if not isinstance(texts, dict) or not texts:
        raise RuntimeError("saved analysis has no result text")
    summary = json.dumps(texts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return summary


def _complete_analysis_status(record, route):
    status = record.get("status")
    if status != "complete":
        if route is not None:
            results = record.get("results")
            numerics = (
                results.get("binary_numerics")
                if isinstance(results, dict)
                else None
            )
            pooled = numerics.get("pooled") if isinstance(numerics, dict) else None
            display = pooled.get("display") if isinstance(pooled, dict) else None
            estimate = display.get("estimate") if isinstance(display, dict) else None
            estimate_status = (
                estimate.get("status") if isinstance(estimate, dict) else "missing"
            )
            result_details = (
                "; %s" % _plot_edit_result_details(record)
                if route == "binary.plot-edit"
                else ""
            )
            raise _UnqualifiedRoute(
                "%s retained result status is %s (warnings: %s; pooled estimate status: %s%s)"
                % (
                    route,
                    status or "missing",
                    record.get("warnings", []),
                    estimate_status or "missing",
                    result_details,
                )
            )
        raise RuntimeError("analysis did not produce a complete retained result")

    return status


def _analysis_input_identity(record):
    input_identity = record.get("input_identity")
    if not isinstance(input_identity, str) or len(input_identity) != 64:
        raise RuntimeError("saved analysis has no stable input identity")
    return input_identity


def _analysis_study_names(studies):
    if any(not isinstance(study, dict) or not isinstance(study.get("name"), str) for study in studies):
        return None
    return [study["name"] for study in studies]


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
            "warnings",
            "result_evidence",
        )
    )


def _qualification_route_identity(route):
    return {
        "binary.one-arm": ("binary", "standard", "PLO", "binary.random"),
        "continuous.entered-effect": (
            "continuous", "standard", "SMD", "continuous.random"
        ),
        "binary.meta-regression": (
            "binary", "meta-regression", "OR", "meta.regression"
        ),
        "continuous.meta-regression": (
            "continuous", "meta-regression", "SMD", "meta.regression"
        ),
        "diagnostic.reitsma-meta-regression": (
            "diagnostic", "meta-regression", "Sensitivity and specificity",
            "diagnostic.reitsma",
        ),
        "diagnostic.reitsma": (
            "diagnostic", "standard", "Sensitivity and specificity",
            "diagnostic.reitsma",
        ),
        "binary.small-study-effects": (
            "binary", "small-study-effects", "OR", "small.study.effects"
        ),
        "binary.plot-edit": ("binary", "standard", "OR", "binary.random"),
        "diagnostic.subgroup": (
            "diagnostic", "subgroup", "Sens", "diagnostic.random"
        ),
    }.get(route)


def _route_result_evidence(route, record):
    results = record.get("results")
    snapshot = record.get("input_snapshot")
    if not isinstance(results, dict) or not isinstance(snapshot, dict):
        return None
    snapshot = snapshot.get("input_snapshot", snapshot)
    if not isinstance(snapshot, dict):
        return None
    builder = _ROUTE_RESULT_BUILDERS.get(route)
    return builder(results, snapshot, record) if builder is not None else None


def _one_arm_result_evidence(results, snapshot, record):
    numerics = results.get("binary_proportion_numerics")
    if not isinstance(numerics, dict):
        return None
    pooled = numerics.get("pooled")
    if not isinstance(pooled, dict):
        return None
    display = pooled.get("display")
    estimate = _available_value(
        display.get("estimate") if isinstance(display, dict) else None
    )
    count = _available_value(pooled.get("study_count"))
    studies = numerics.get("studies")
    input_studies = snapshot.get("studies")
    groups = snapshot.get("groups")
    if estimate is None or count is None:
        return None
    if not _one_arm_source_valid(snapshot, groups, input_studies, studies):
        return None
    if not _one_arm_results_valid(numerics, groups, input_studies, studies):
        return None
    return _one_arm_evidence_payload(
        results, snapshot, numerics, estimate, count, studies
    )


def _one_arm_evidence_payload(results, snapshot, numerics, estimate, count, studies):
    return {
        "status": "available",
        "kind": "one-arm-proportion",
        "metric": numerics.get("metric"),
        "arm_label": numerics.get("arm_label"),
        "pooled_proportion": estimate,
        "study_count": int(count),
        "input_study_count": len(snapshot.get("studies", [])),
        "figure_status": _stored_figure_status(results),
        "numeric_oracle": "observed_only_no_independent_expected_value",
        "raw_arm_totals": _one_arm_total_sum(studies),
    }


def _one_arm_total_sum(studies):
    return sum(int(total) for total in (_available_total(row) for row in studies) if total is not None)


def _one_arm_source_valid(snapshot, groups, input_studies, studies):
    return (
        isinstance(groups, list)
        and len(groups) == 1
        and snapshot.get("metric") == "PLO"
        and snapshot.get("raw_counts_available") is True
        and isinstance(input_studies, list)
        and isinstance(studies, list)
        and len(studies) == len(input_studies)
    )


def _one_arm_results_valid(numerics, groups, input_studies, studies):
    labels_match = [
        row.get("label") for row in studies if isinstance(row, dict)
    ] == [row.get("name") for row in input_studies if isinstance(row, dict)]
    return (
        labels_match
        and all(_one_arm_study_values_valid(row) for row in studies)
        and numerics.get("arm_label") == groups[0]
    )


def _one_arm_study_values_valid(row):
    return (
        isinstance(row, dict)
        and _available_value(row.get("events")) is not None
        and _available_value(row.get("total")) is not None
    )


def _available_total(row):
    if not isinstance(row, dict):
        return None
    total = row.get("total")
    if not isinstance(total, dict) or total.get("status") != "available":
        return None
    value = total.get("value")
    return value if isinstance(value, (int, float)) else None

def _continuous_entered_result_evidence(results, snapshot, record):
    numerics = results.get("continuous_numerics")
    if not isinstance(numerics, dict):
        return None
    studies = snapshot.get("studies")
    result_studies = numerics.get("studies")
    pooled = numerics.get("pooled")
    estimate = _available_value(
        pooled.get("estimate") if isinstance(pooled, dict) else None
    )
    count = _available_value(
        numerics.get("analyzed_study_count")
    )
    if estimate is None or count is None:
        return None
    if not _entered_effect_studies_valid(numerics, studies, result_studies):
        return None
    return {
        "status": "available",
        "kind": "entered-effect-continuous",
        "input_source": "entered",
        "metric": numerics.get("metric"),
        "pooled_estimate": estimate,
        "study_count": int(count),
        "input_study_count": len(studies),
        "figure_status": _stored_figure_status(results),
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }


def _entered_effect_studies_valid(numerics, studies, result_studies):
    return (
        isinstance(studies, list)
        and bool(studies)
        and isinstance(result_studies, list)
        and _study_labels(result_studies) == _study_names(studies)
        and all(_entered_effect_provenance_valid(row) for row in studies)
        and numerics.get("metric") == "SMD"
    )


def _study_labels(studies):
    return [row.get("label") for row in studies if isinstance(row, dict)]


def _study_names(studies):
    return [row.get("name") for row in studies if isinstance(row, dict)]


def _entered_effect_provenance_valid(study):
    return isinstance(study, dict) and study.get("provenance") == "entered"

def _meta_regression_result_evidence(results, snapshot, record):
    numerics = results.get("meta_regression_numerics")
    if not isinstance(numerics, dict):
        return None
    details = _meta_regression_evidence_details(numerics, snapshot)
    if details is None:
        return None
    names, eligible_order, coefficient_rows, eligible_count = details
    return {
        "status": "available",
        "kind": "generic-meta-regression",
        "formula": numerics.get("formula"),
        "moderators": names,
        "coefficient_count": numerics.get("coefficient_count"),
        "eligible_study_count": eligible_count,
        "eligible_study_order": eligible_order,
        "coefficients": coefficient_rows,
        "figure_status": _stored_figure_status(results),
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }


def _reitsma_meta_regression_result_evidence(results, snapshot, record):
    numerics = results.get("reitsma_meta_regression_numerics")
    if not isinstance(numerics, dict):
        return None
    inputs = _reitsma_meta_regression_input_details(snapshot, record)
    if inputs is None:
        return None
    report = _reitsma_meta_regression_report_details(numerics, inputs)
    if report is None:
        return None
    return {
        "status": "available",
        "kind": "joint-reitsma-meta-regression",
        "report_status": "available",
        "formula": numerics["formula"],
        "package_version": numerics["package_version"],
        "converged": numerics["converged"],
        "effective_settings": inputs["effective_settings"],
        "moderator": inputs["moderator"],
        "input_study_count": inputs["input_study_count"],
        "eligible_study_count": len(report["eligible_study_order"]),
        "eligible_study_order": report["eligible_study_order"],
        "exclusions": report["exclusions"],
        "sensitivity_coefficients": report["sensitivity_coefficients"],
        "false_positive_rate_coefficients": report["false_positive_rate_coefficients"],
        "overall_ml_test": report["overall_ml_test"],
        "moderator_ml_tests": report["moderator_ml_tests"],
        "unavailable_outputs": report["unavailable_outputs"],
        "figure_status": _stored_figure_status(results),
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }


def _reitsma_meta_regression_input_details(snapshot, record):
    if not _reitsma_snapshot_context_valid(snapshot):
        return None
    settings = _reitsma_saved_settings(record)
    moderator_data = _reitsma_input_moderator(snapshot)
    if settings is None or moderator_data is None:
        return None
    studies, moderator, values = moderator_data
    rows = _reitsma_input_rows(studies, values)
    if rows is None:
        return None
    eligible, exclusions, names_by_id = rows
    if len(exclusions) != 2 or len(eligible) < 3:
        return None
    return {
        "effective_settings": settings,
        "moderator": {
            "name": moderator["name"],
            "kind": moderator["kind"],
            "unit": moderator["unit"],
            "unit_step": moderator["unit_step"],
        },
        "input_study_count": len(studies),
        "eligible_ids": eligible,
        "excluded_ids": [item["study_id"] for item in exclusions],
        "exclusions": exclusions,
        "names_by_id": names_by_id,
    }


def _reitsma_snapshot_context_valid(snapshot):
    groups = snapshot.get("groups")
    return (
        snapshot.get("data_type") == "diagnostic"
        and snapshot.get("metric") == "Sensitivity and specificity"
        and isinstance(snapshot.get("outcome"), str)
        and isinstance(snapshot.get("time_point"), str)
        and isinstance(groups, list)
        and len(groups) == 1
        and isinstance(snapshot.get("studies"), list)
    )


def _reitsma_saved_settings(record):
    specification = record.get("specification")
    params = specification.get("params") if isinstance(specification, dict) else None
    if not isinstance(specification, dict) or not isinstance(params, dict):
        return None
    if not _reitsma_specification_valid(specification, params):
        return None
    correction = params.get("adjust")
    confidence = params.get("conf.level")
    if not _reitsma_settings_ranges_valid(correction, confidence):
        return None
    return {
        "missing_moderator_policy": specification["missing_moderator_policy"],
        "joint_metrics": params["joint.metrics"],
        "estimator": params["estimator"],
        "correction_policy": params["correction.policy"],
        "correction_factor": correction,
        "confidence_level": confidence,
    }


def _reitsma_specification_valid(specification, params):
    return (
        isinstance(specification, dict)
        and specification.get("data_type") == "diagnostic"
        and specification.get("workflow") == "meta-regression"
        and specification.get("method") == "diagnostic.reitsma"
        and specification.get("metric") == "Sens"
        and specification.get("missing_moderator_policy") == "exclude"
        and _reitsma_params_valid(params)
    )


def _reitsma_params_valid(params):
    return (
        isinstance(params, dict)
        and params.get("joint.metrics") == "Sens,Spec"
        and params.get("estimator") in {"REML", "ML"}
        and params.get("correction.policy") in {
            "All studies if any zero exists", "Studies with any zero cell", "None"
        }
    )


def _reitsma_settings_ranges_valid(correction, confidence):
    return (
        _qualification_number(correction)
        and correction >= 0
        and _qualification_number(confidence)
        and 0 < confidence < 100
    )


def _reitsma_input_moderator(snapshot):
    studies = snapshot.get("studies")
    moderators = snapshot.get("moderators")
    if not isinstance(studies, list) or not isinstance(moderators, list) or len(moderators) != 1:
        return None
    moderator = moderators[0]
    if not _reitsma_moderator_input_valid(moderator, len(studies)):
        return None
    return studies, moderator, moderator["values"]


def _reitsma_moderator_input_valid(moderator, study_count):
    if not isinstance(moderator, dict):
        return False
    if moderator.get("name") != "Qualification index":
        return False
    if moderator.get("kind") != "continuous":
        return False
    values = moderator.get("values")
    unit = moderator.get("unit")
    step = moderator.get("unit_step")
    return (
        isinstance(values, list)
        and len(values) == study_count
        and isinstance(unit, str)
        and bool(unit)
        and _reitsma_moderator_step_valid(step)
    )


def _reitsma_moderator_step_valid(step):
    return _qualification_number(step) and step > 0


def _reitsma_input_rows(studies, values):
    eligible = []
    exclusions = []
    names_by_id = {}
    for study, value in zip(studies, values, strict=True):
        row = _reitsma_input_study(study, value, names_by_id)
        if row is None:
            return None
        study_id, name, is_missing = row
        if is_missing:
            exclusions.append(_reitsma_input_exclusion(study_id, name))
        else:
            eligible.append(study_id)
    if len(set(names_by_id.values())) != len(names_by_id):
        return None
    return eligible, exclusions, names_by_id


def _reitsma_input_study(study, value, names_by_id):
    if not isinstance(study, dict):
        return None
    identity = _reitsma_input_identity(study, names_by_id)
    if identity is None:
        return None
    serialized_id, name = identity
    missing = _reitsma_input_value_missing(value)
    if not missing and not _qualification_number(value):
        return None
    names_by_id[serialized_id] = name
    return serialized_id, name, missing


def _reitsma_input_identity(study, names_by_id):
    study_id = study.get("id")
    name = study.get("name")
    if type(study_id) is not int or not isinstance(name, str) or not name:
        return None
    serialized_id = str(study_id)
    if serialized_id in names_by_id:
        return None
    return serialized_id, name


def _reitsma_input_value_missing(value):
    return value is None or value == ""


def _reitsma_input_exclusion(study_id, name):
    return {
        "study_id": study_id,
        "study_name": name,
        "reason": "Missing moderator value(s): Qualification index",
    }


def _reitsma_meta_regression_report_details(numerics, inputs):
    settings = inputs["effective_settings"]
    if not _reitsma_report_header_valid(numerics, settings):
        return None
    eligible = numerics.get("eligible_study_ids")
    exclusions = numerics.get("exclusions")
    if not _reitsma_report_studies_match(eligible, exclusions, inputs):
        return None
    eligible_order = [inputs["names_by_id"][study_id] for study_id in eligible]
    return _reitsma_report_result_rows(numerics, eligible, eligible_order, inputs)


def _reitsma_report_header_valid(numerics, settings):
    correction = numerics.get("correction")
    return (
        numerics.get("schema") == "reitsma-meta-regression-v1"
        and numerics.get("estimator") == settings["estimator"]
        and numerics.get("converged") is True
        and _reitsma_formula_valid(numerics.get("formula"))
        and _reitsma_correction_valid(correction, settings)
        and _reitsma_moderator_coding_matches(numerics.get("moderator_coding"))
    )


def _reitsma_formula_valid(value):
    return isinstance(value, str) and bool(value)


def _reitsma_correction_valid(value, settings):
    return (
        isinstance(value, dict)
        and value.get("policy") == settings["correction_policy"]
        and value.get("factor") == settings["correction_factor"]
    )


def _reitsma_report_studies_match(eligible, exclusions, inputs):
    return (
        eligible == inputs["eligible_ids"]
        and _reitsma_exclusion_rows_match(exclusions, inputs)
    )


def _reitsma_report_result_rows(numerics, eligible, eligible_order, inputs):
    sensitivity = _reitsma_coefficient_rows(
        numerics.get("sensitivity_coefficients"), "sensitivity", "sensitivity"
    )
    false_positive_rate = _reitsma_coefficient_rows(
        numerics.get("false_positive_rate_coefficients"),
        "false_positive_rate",
        "specificity",
    )
    eligible_order = [inputs["names_by_id"][study_id] for study_id in eligible]
    overall = _reitsma_test_row(
        numerics.get("overall_ml_likelihood_ratio_test"),
        "All moderators",
        eligible,
        eligible_order,
    )
    moderator_tests = _reitsma_moderator_test_rows(
        numerics.get("moderator_block_ml_tests"), eligible, eligible_order
    )
    unavailable = _reitsma_unavailable_output_rows(
        numerics.get("unavailable_outputs")
    )
    if (
        sensitivity is None
        or false_positive_rate is None
        or overall is None
        or moderator_tests is None
        or unavailable is None
    ):
        return None
    return {
        "eligible_study_order": eligible_order,
        "exclusions": inputs["exclusions"],
        "sensitivity_coefficients": sensitivity,
        "false_positive_rate_coefficients": false_positive_rate,
        "overall_ml_test": overall,
        "moderator_ml_tests": moderator_tests,
        "unavailable_outputs": unavailable,
    }


def _reitsma_moderator_coding_matches(value):
    if not isinstance(value, list) or len(value) != 1:
        return False
    coding = value[0]
    return _reitsma_continuous_coding_valid(coding)


def _reitsma_continuous_coding_valid(coding):
    if not isinstance(coding, dict):
        return False
    observed_range = coding.get("observed_range")
    return (
        coding.get("name") == "Qualification index"
        and coding.get("kind") == "continuous"
        and (
            observed_range is None
            or (
                isinstance(observed_range, list)
                and len(observed_range) == 2
                and all(_qualification_number(item) for item in observed_range)
            )
        )
    )


def _reitsma_exclusion_rows_match(value, inputs):
    if not isinstance(value, list) or len(value) != len(inputs["excluded_ids"]):
        return False
    return all(
        isinstance(item, dict)
        and item.get("study_id") == expected_id
        and isinstance(item.get("reason"), str)
        and "Qualification index" in item["reason"]
        for item, expected_id in zip(value, inputs["excluded_ids"], strict=True)
    )


def _reitsma_coefficient_rows(value, model_side, effect_direction):
    if not isinstance(value, list) or not value:
        return None
    fields = (
        "model_estimate", "standard_error", "model_statistic", "p_value",
        "model_ci_lower", "model_ci_upper", "reported_odds_ratio",
        "odds_ratio_ci_lower", "odds_ratio_ci_upper",
    )
    rows = []
    for item in value:
        if not _reitsma_coefficient_row_valid(
            item, model_side, effect_direction, fields
        ):
            return None
        rows.append({field: item[field] for field in ("term", *fields)})
    return rows


def _reitsma_coefficient_row_valid(item, model_side, effect_direction, fields):
    if not isinstance(item, dict) or not isinstance(item.get("term"), str):
        return False
    return (
        item.get("model_side") == model_side
        and item.get("effect_direction") == effect_direction
        and all(_qualification_number(item.get(field)) for field in fields)
    )


def _reitsma_test_row(value, expected_label, eligible_ids, eligible_order):
    if not isinstance(value, dict):
        return None
    statistic = value.get("statistic")
    degrees = value.get("degrees_of_freedom")
    p_value = value.get("p_value")
    if not _reitsma_test_identity_valid(value, expected_label, eligible_ids):
        return None
    if not _reitsma_test_values_valid(statistic, degrees, p_value):
        return None
    return {
        "label": expected_label,
        "fit_estimator": "ML",
        "statistic": statistic,
        "degrees_of_freedom": degrees,
        "p_value": p_value,
        "included_study_order": eligible_order,
    }


def _reitsma_test_identity_valid(value, expected_label, eligible_ids):
    return (
        value.get("label") == expected_label
        and value.get("fit_estimator") == "ML"
        and value.get("included_study_ids") == eligible_ids
    )


def _reitsma_test_values_valid(statistic, degrees, p_value):
    return (
        _qualification_number(statistic)
        and type(degrees) is int
        and degrees >= 1
        and _qualification_number(p_value)
        and 0 <= p_value <= 1
    )


def _reitsma_moderator_test_rows(value, eligible_ids, eligible_order):
    if not isinstance(value, list) or len(value) != 1:
        return None
    row = _reitsma_test_row(
        value[0], "Qualification index", eligible_ids, eligible_order
    )
    return [row] if row is not None else None


def _reitsma_unavailable_output_rows(value):
    if not isinstance(value, list) or len(value) != 3:
        return None
    rows = []
    for item in value:
        row = _reitsma_unavailable_output_row(item)
        if row is None:
            return None
        rows.append(row)
    expected = {"conditional_summary_operating_point", "adjusted_sroc", "sroc_auc"}
    return rows if {item["name"] for item in rows} == expected else None


def _reitsma_unavailable_output_row(value):
    if not isinstance(value, dict):
        return None
    name = value.get("name")
    reason = value.get("reason")
    if not isinstance(name, str) or not isinstance(reason, str) or not reason:
        return None
    return {"name": name, "reason": reason}


def _qualification_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _meta_regression_evidence_details(numerics, snapshot):
    parts = _meta_regression_lists(numerics)
    if parts is None:
        return None
    moderators, eligible, coefficients = parts
    names = _meta_moderator_names(moderators)
    input_studies = snapshot.get("studies")
    if names is None:
        return None
    if not isinstance(input_studies, list):
        return None
    study_names_by_id = _study_names_by_id(input_studies)
    eligible_order = [study_names_by_id.get(study_id) for study_id in eligible]
    if not _valid_name_order(eligible_order):
        return None
    coefficient_rows = _meta_coefficient_rows(coefficients)
    if coefficient_rows is None:
        return None
    if numerics.get("coefficient_count") != len(coefficient_rows):
        return None
    return names, eligible_order, coefficient_rows, len(eligible)


def _meta_regression_lists(numerics):
    values = (
        numerics.get("moderators"),
        numerics.get("eligible_study_ids"),
        numerics.get("coefficients"),
    )
    if not all(isinstance(value, list) for value in values):
        return None
    return values


def _meta_moderator_names(moderators):
    names = [
        moderator.get("name")
        for moderator in moderators
        if isinstance(moderator, dict) and isinstance(moderator.get("name"), str)
    ]
    return names if names and len(names) == len(moderators) else None


def _study_names_by_id(studies):
    return {
        study.get("id"): study.get("name")
        for study in studies
        if isinstance(study, dict)
        and isinstance(study.get("id"), int)
        and isinstance(study.get("name"), str)
    }


def _valid_name_order(names):
    return all(isinstance(name, str) and bool(name) for name in names)


def _meta_coefficient_rows(coefficients):
    rows = []
    for row in coefficients:
        evidence = _meta_coefficient_evidence(row)
        if evidence is None:
            return None
        rows.append(evidence)
    return rows


def _meta_coefficient_evidence(row):
    if not isinstance(row, dict):
        return None
    term = row.get("term")
    estimate = _available_value(row.get("estimate"))
    label = term.get("label") if isinstance(term, dict) else None
    if estimate is None or not isinstance(label, str) or not label:
        return None
    return {"label": label, "estimate": estimate}

def _reitsma_result_evidence(results, snapshot, record):
    report = results.get("reitsma_report")
    if not isinstance(report, dict):
        return None
    sections = report.get("sections")
    summary = _reitsma_summary(sections)
    if summary is None:
        return None
    return {
        "status": "available",
        "kind": "joint-reitsma",
        "measures": report.get("measures"),
        "summary": summary,
        "section_statuses": _section_statuses(sections),
        "figure_status": _stored_figure_status(results),
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }


def _reitsma_summary(sections):
    if not isinstance(sections, list):
        return None
    summary = next(
        (
            section.get("value")
            for section in sections
            if isinstance(section, dict)
            and section.get("key") == "Summary operating point"
            and section.get("status") == "available"
        ),
        None,
    )
    return summary if isinstance(summary, str) and summary.strip() else None


def _section_statuses(sections):
    return {
        section.get("key"): section.get("status")
        for section in sections
        if isinstance(section, dict)
    }

def _diagnostic_subgroup_result_evidence(results, snapshot, record):
    context = _diagnostic_subgroup_context(results, snapshot, record)
    if context is None:
        return None
    plan, numerics, studies, raw_values, assignments, raw_levels, numerical_levels = context
    study_names = _diagnostic_study_names_by_id(studies)
    assignment_evidence = _subgroup_assignment_evidence(
        studies, assignments, raw_values
    )
    level_evidence = _subgroup_level_evidence(
        raw_levels, numerical_levels, study_names
    )
    status_evidence = _subgroup_status_evidence(numerics)
    if assignment_evidence is None or level_evidence is None or status_evidence is None:
        return None
    overall, between = status_evidence
    return {
        "status": "available",
        "kind": "diagnostic-subgroup",
        "covariate_name": plan["covariate_name"],
        "missing_policy": plan["missing_policy"],
        "confidence_level": 90.0,
        "input_study_count": len(studies),
        "included_count": numerics.get("included_count"),
        "missing_count": numerics.get("missing_count"),
        "excluded_count": numerics.get("excluded_count"),
        "assignments": assignment_evidence,
        "levels": level_evidence,
        "overall": {
            "included_count": overall.get("included_count"),
            "status": overall.get("status"),
        },
        "between_subgroup_test_status": between.get("status"),
        "figure_status": _stored_figure_status(results),
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }


def _diagnostic_subgroup_context(results, snapshot, record):
    plan = results.get("subgroup_plan")
    numerics = results.get("subgroup_numerics")
    studies = snapshot.get("studies")
    covariates = snapshot.get("covariates")
    specification = record.get("specification")
    parameters = specification.get("params") if isinstance(specification, dict) else None
    if not _subgroup_plan_valid(plan, numerics, studies, covariates, parameters):
        return None
    covariate = _qualification_covariate(covariates, plan["covariate_name"])
    raw_values = covariate.get("values") if isinstance(covariate, dict) else None
    assignments = plan.get("assignments")
    raw_levels = plan.get("levels")
    numerical_levels = numerics.get("levels")
    if not _subgroup_arrays_valid(
        studies, raw_values, assignments, raw_levels, numerical_levels
    ):
        return None
    return plan, numerics, studies, raw_values, assignments, raw_levels, numerical_levels


def _subgroup_plan_valid(plan, numerics, studies, covariates, parameters):
    return (
        _subgroup_input_types_valid(plan, numerics, studies, covariates, parameters)
        and _subgroup_plan_identity_valid(plan)
        and _subgroup_numerics_match_plan(plan, numerics, parameters)
    )


def _subgroup_input_types_valid(plan, numerics, studies, covariates, parameters):
    return (
        isinstance(plan, dict)
        and isinstance(numerics, dict)
        and isinstance(studies, list)
        and isinstance(covariates, list)
        and isinstance(parameters, dict)
    )


def _subgroup_plan_identity_valid(plan):
    return (
        plan.get("family") == "diagnostic"
        and plan.get("covariate_name") == "Qualification region"
        and plan.get("metric") == "Sens"
        and plan.get("missing_policy") in {"exclude", "missing_category"}
    )


def _subgroup_numerics_match_plan(plan, numerics, parameters):
    return (
        numerics.get("covariate_name") == plan.get("covariate_name")
        and numerics.get("missing_policy") == plan.get("missing_policy")
        and parameters.get("conf.level") == 90.0
    )


def _qualification_covariate(covariates, name):
    return next(
        (
            row for row in covariates
            if isinstance(row, dict)
            and row.get("name") == name
            and row.get("data_type") == "factor"
        ),
        None,
    )


def _subgroup_arrays_valid(studies, values, assignments, raw_levels, numerical_levels):
    return (
        isinstance(values, list)
        and len(values) == len(studies)
        and isinstance(assignments, list)
        and len(assignments) == len(studies)
        and isinstance(raw_levels, list)
        and isinstance(numerical_levels, list)
    )


def _diagnostic_study_names_by_id(studies):
    return {
        study.get("id"): study.get("name")
        for study in studies
        if isinstance(study, dict)
        and type(study.get("id")) is int
        and isinstance(study.get("name"), str)
    }


def _subgroup_assignment_evidence(studies, assignments, values):
    evidence = []
    for study, assignment, value in zip(studies, assignments, values, strict=True):
        row = _subgroup_assignment_row(study, assignment, value)
        if row is None:
            return None
        evidence.append(row)
    return evidence


def _subgroup_assignment_row(study, assignment, value):
    if not isinstance(study, dict) or not isinstance(assignment, dict):
        return None
    if assignment.get("study_id") != study.get("id"):
        return None
    if assignment.get("study_name") != study.get("name"):
        return None
    if assignment.get("value") != value:
        return None
    return {
        "study_id": assignment.get("study_id"),
        "study_name": assignment.get("study_name"),
        "value": assignment.get("value"),
        "status": assignment.get("status"),
    }


def _subgroup_level_evidence(raw_levels, numerical_levels, study_names):
    results_by_label = {
        row.get("label"): row
        for row in numerical_levels
        if isinstance(row, dict) and isinstance(row.get("label"), str)
    }
    evidence = []
    for level in raw_levels:
        row = _subgroup_level_row(level, results_by_label, study_names)
        if row is None:
            return None
        evidence.append(row)
    return evidence


def _subgroup_level_row(level, results_by_label, study_names):
    if not isinstance(level, dict):
        return None
    study_ids = level.get("study_ids")
    if not isinstance(study_ids, list):
        return None
    label = level.get("label")
    result = results_by_label.get(label)
    names = [study_names.get(study_id) for study_id in study_ids]
    if not _subgroup_level_identity_valid(label, names, study_ids, result):
        return None
    return {
        "label": label,
        "study_order": names,
        "included_count": len(study_ids),
        "status": result.get("status"),
    }


def _subgroup_level_identity_valid(label, names, study_ids, result):
    return (
        isinstance(label, str)
        and result is not None
        and all(isinstance(name, str) and bool(name) for name in names)
        and len(names) == len(study_ids)
        and result.get("included_count") == len(study_ids)
    )


def _subgroup_status_evidence(numerics):
    overall = numerics.get("overall")
    between = numerics.get("between_subgroup_test")
    if not isinstance(overall, dict) or not isinstance(between, dict):
        return None
    return overall, between

def _plot_edit_result_evidence(results, snapshot, record):
    numerics = results.get("binary_numerics")
    studies = snapshot.get("studies")
    figure_key = _stored_forest_plot_key(results)
    if (
        not isinstance(numerics, dict)
        or figure_key is None
        or not isinstance(studies, list)
        or len(studies) < 2
    ):
        return None
    return {
        "status": "available",
        "kind": "binary-plot-edit",
        "study_count": len(studies),
        "input_study_count": len(studies),
        "figure_status": _stored_figure_status(results),
        "figure_key": figure_key,
        "figure_title": "Forest Plot",
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }


def _stored_forest_plot_key(results):
    images = results.get("images")
    sections = results.get("sections")
    if not isinstance(images, dict) or not isinstance(sections, list):
        return None
    for section in sections:
        if not isinstance(section, dict):
            continue
        source_key = section.get("source_key")
        image = images.get(source_key) if isinstance(source_key, str) else None
        if (
            section.get("kind") == "image"
            and section.get("title") == "Forest Plot"
            and isinstance(image, str)
            and image
        ):
            return source_key
    return None


def _small_study_result_evidence(results, snapshot, record):
    small = results.get("small_study_effects")
    report = small.get("report") if isinstance(small, dict) else None
    if not isinstance(report, dict):
        return None
    details = _small_study_report_details(report)
    if details is None:
        return None
    primary, sections, study_order = details
    if report.get("status") != "complete":
        raise _UnqualifiedRoute(
            "small-study-effects report status is %s"
            % (report.get("status") or "missing")
        )
    return {
        "status": "available",
        "kind": "small-study-effects",
        "report_status": report.get("status"),
        "usable_studies": len(study_order),
        "report_study_order": _small_study_names(study_order),
        "primary_test_status": primary.get("status"),
        "primary_test_method": primary.get("method"),
        "section_statuses": _section_statuses(sections),
        "report_warnings": report.get("warnings", []),
        "figure_status": _stored_figure_status(results),
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }


def _small_study_report_details(report):
    primary = report.get("primary_test")
    sections = report.get("sections")
    study_order = report.get("study_order")
    if not isinstance(primary, dict) or not isinstance(sections, list):
        return None
    if not isinstance(study_order, list):
        return None
    return primary, sections, study_order


def _small_study_names(study_order):
    return [
        row.get("name")
        for row in study_order
        if isinstance(row, dict)
    ]

def _stored_figure_status(results):
    images = results.get("images")
    return (
        "available"
        if isinstance(images, dict)
        and any(isinstance(path, str) and path for path in images.values())
        else "not_available"
    )


def _available_value(value):
    if not isinstance(value, dict) or value.get("status") != "available":
        return None
    number = value.get("value")
    if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
        return None
    return number


_ROUTE_RESULT_BUILDERS = {
    "binary.one-arm": _one_arm_result_evidence,
    "continuous.entered-effect": _continuous_entered_result_evidence,
    "binary.meta-regression": _meta_regression_result_evidence,
    "continuous.meta-regression": _meta_regression_result_evidence,
    "diagnostic.reitsma-meta-regression": _reitsma_meta_regression_result_evidence,
    "diagnostic.reitsma": _reitsma_result_evidence,
    "diagnostic.subgroup": _diagnostic_subgroup_result_evidence,
    "binary.small-study-effects": _small_study_result_evidence,
    "binary.plot-edit": _plot_edit_result_evidence,
}


def _run_separate_family_journey(
    app,
    sample_path,
    destination,
    *,
    window=None,
    data_type,
    metric,
    method,
    route=None,
    prepare_model=None,
    event_loop_responsive=None,
    close_window,
):
    from rc_metastudio import main_window

    sample_path = Path(sample_path).resolve()
    destination = Path(destination).resolve()
    owns_window = window is None
    if not sample_path.is_file():
        raise RuntimeError("packaged %s sample project is missing" % data_type)
    if owns_window:
        print("worker journey: creating %s window" % data_type, file=sys.stderr, flush=True)
        window = main_window.MainWindow()
        print("worker journey: %s window created" % data_type, file=sys.stderr, flush=True)
    if not isinstance(window, main_window.MainWindow):
        raise RuntimeError("worker journey requires a main window")
    reopened = None
    try:
        evidence = _run_family_sample_analysis(
            window,
            sample_path,
            data_type,
            metric=metric,
            method=method,
            prepare_model=prepare_model,
            event_loop_responsive=event_loop_responsive,
            route=route,
        )
        return _save_reopen_and_inspect(
            app,
            window,
            destination,
            evidence,
            route=route,
            source=sample_path,
            data_type=data_type,
            close_window=close_window,
        )
    finally:
        if reopened is not None:
            close_window(app, reopened)
        if owns_window:
            close_window(app, window)


def _run_family_sample_analysis(
    window,
    sample_path,
    data_type,
    *,
    metric,
    method,
    prepare_model,
    event_loop_responsive,
    route,
):
    window.workspace.mark_saved()
    print("worker journey: opening %s sample" % data_type, file=sys.stderr, flush=True)
    if not window.open(str(sample_path), raise_on_error=True):
        raise RuntimeError("packaged %s project could not be opened" % data_type)
    print("worker journey: %s sample opened" % data_type, file=sys.stderr, flush=True)
    if window.model.get_current_outcome_type() != data_type:
        raise RuntimeError("packaged sample does not contain the expected family")
    if window.model.current_effect != metric:
        window.model.current_effect = metric
        window._refresh_workspace_context()
    if prepare_model is not None:
        prepare_model(window)
    evidence = _run_worker_analysis(
        window,
        window.go,
        data_type=data_type,
        metric=metric,
        workflow="standard",
        method=method,
        event_loop_responsive=event_loop_responsive,
    )
    if route is not None:
        evidence = _analysis_evidence(window, evidence["analysis_id"], route=route)
    print("worker journey: %s analysis completed" % data_type, file=sys.stderr, flush=True)
    return evidence


def _prepare_one_arm_binary(window):
    groups = tuple(window.model.get_current_groups())
    if not groups:
        raise _UnqualifiedRoute("binary sample has no selected arm for one-arm analysis")
    window.display_groups([groups[0]])


def _prepare_entered_effect_continuous(window):
    model = window.model
    groups = tuple(model.get_current_groups())
    if len(groups) != 2:
        raise _UnqualifiedRoute(
            "continuous sample does not have two groups for entered SMD effects"
        )
    comparison = "-".join(groups)
    included = _included_study_rows(model)
    if len(included) < 2:
        raise _UnqualifiedRoute("continuous sample has fewer than two included studies")
    units = _entered_effect_analysis_units(model, included, comparison)
    if units is None:
        raise _UnqualifiedRoute(
            "continuous sample has no complete entered SMD effects for every included study"
        )
    for unit in units:
        for group in groups:
            unit.set_raw_data_for_group(group, ["", "", ""])
    model.reset_model()
    window.data_dirtied()
    from rc_metastudio.continuous_analysis_snapshot import freeze_continuous_input

    snapshot = freeze_continuous_input(model)
    if any(study.provenance != "entered" for study in snapshot.studies):
        raise _UnqualifiedRoute(
            "continuous sample could not freeze all included rows as entered effects"
        )


def _included_study_rows(model):
    return [
        (index, study)
        for index, study in enumerate(model.dataset.studies)
        if study.include
    ]


def _entered_effect_analysis_units(model, included, comparison):
    units = []
    for index, _study in included:
        unit = model._get_canonical_analysis_unit(index)
        estimate, standard_error = unit.get_effect_and_se_for_source(
            "entered", "SMD", comparison, model.get_confidence_multiplier()
        )
        if estimate is None or standard_error is None:
            return None
        units.append(unit)
    return units


def _seed_qualification_moderator(window, *, missing_positions=()):
    studies = window.model.get_studies(only_if_included=True)
    if missing_positions and max(missing_positions) >= len(studies):
        raise _UnqualifiedRoute(
            "diagnostic sample needs at least %s included studies for the exclusion route"
            % (max(missing_positions) + 1)
        )
    missing = {studies[index].id for index in missing_positions}
    values = {
        study.name: None if study.id in missing else float(index + 1)
        for index, study in enumerate(studies)
    }
    window.model.add_covariate("Qualification index", "continuous", values)
    window.data_dirtied()


def _run_meta_regression_journey(
    app,
    sample_path,
    destination,
    *,
    window,
    route,
    data_type,
    metric,
    close_window,
):
    from PyQt6 import QtCore
    from rc_metastudio import meta_regression_dialog

    _open_analysis_sample(window, sample_path, data_type)
    _set_analysis_metric(window, metric)
    missing_positions = (1, 8) if route == "diagnostic.reitsma-meta-regression" else ()
    _seed_qualification_moderator(window, missing_positions=missing_positions)

    before = len(window.workspace.list_saved_analyses())
    responsive = []
    form = _meta_regression_form(window, meta_regression_dialog, route)
    _run_meta_regression_form(window, form, responsive, QtCore)
    if "rpy2.robjects" in sys.modules:
        raise RuntimeError("meta-regression loaded R into the main process")
    saved = window.workspace.list_saved_analyses()
    if len(saved) != before + 1:
        raise RuntimeError("meta-regression did not create one retained result")
    evidence = _analysis_evidence(window, str(saved[-1]["id"]), route=route)
    evidence["event_loop_responsive"] = bool(responsive and responsive[0])
    return _save_reopen_and_inspect(
        app, window, destination, evidence, route=route,
        source=sample_path, data_type=data_type, close_window=close_window,
    )


def _open_analysis_sample(window, sample_path, data_type):
    if not window.open(str(sample_path), raise_on_error=True):
        raise RuntimeError("packaged %s sample could not be opened" % data_type)
    if window.model.get_current_outcome_type() != data_type:
        raise RuntimeError("packaged sample does not contain the expected family")


def _set_analysis_metric(window, metric):
    if window.model.current_effect != metric:
        window.model.current_effect = metric
        window._refresh_workspace_context()


def _meta_regression_form(window, meta_regression_dialog, route):
    window.meta_reg()
    forms = window.findChildren(meta_regression_dialog.MetaRegressionDialog)
    if not forms:
        raise RuntimeError("meta-regression did not open its moderator settings")
    form = forms[-1]
    control = _qualification_moderator_control(form)
    if control is None:
        raise _UnqualifiedRoute("synthetic continuous moderator was not available")
    control.checkbox.setChecked(True)
    control.unit.setText("study index")
    if not _configure_reitsma_meta_regression_form(form, route):
        raise RuntimeError("Reitsma meta-regression exclusion choice is unavailable")
    return form


def _qualification_moderator_control(form):
    return next(
        (
            item for item in form._moderators
            if item.name == "Qualification index"
            and item.kind == "continuous"
            and item.unit is not None
        ),
        None,
    )


def _configure_reitsma_meta_regression_form(form, route):
    if route != "diagnostic.reitsma-meta-regression":
        return True
    policy_index = form.policy.findData("exclude")
    if policy_index < 0:
        return False
    form.policy.setCurrentIndex(policy_index)
    form.confidence.setValue(90.0)
    return True


def _run_meta_regression_form(window, form, responsive, qt_core):
    from PyQt6.QtWidgets import QDialogButtonBox

    def run():
        button = form.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if button is None or not button.isEnabled():
            raise RuntimeError("meta-regression run control is disabled")
        button.click()
        qt_core.QTimer.singleShot(
            0,
            lambda: responsive.append(
                window.isVisible() and window.analysis_worker.is_busy
            ),
        )
    _await_worker(window.analysis_worker, run, window.analysis_worker.completed)


def _run_special_family_journey(
    app, sample_path, destination, *, window, route, close_window
):
    if route == "binary.plot-edit":
        return _run_binary_plot_edit_journey(
            app, sample_path, destination, window=window, close_window=close_window
        )
    from PyQt6 import QtCore

    data_type = "diagnostic" if route == "diagnostic.reitsma" else "binary"
    metric = "Sens" if data_type == "diagnostic" else "OR"
    _open_analysis_sample(window, sample_path, data_type)
    _set_analysis_metric(window, metric)
    before = len(window.workspace.list_saved_analyses())
    responsive = []
    if route == "diagnostic.reitsma":
        _run_reitsma_special(window, responsive, QtCore)
    else:
        _run_small_study_special(window, responsive, QtCore)
    if "rpy2.robjects" in sys.modules:
        raise RuntimeError("qualification analysis loaded R into the main process")
    saved = window.workspace.list_saved_analyses()
    if len(saved) != before + 1:
        raise RuntimeError("%s did not create one retained result" % route)
    evidence = _analysis_evidence(window, str(saved[-1]["id"]), route=route)
    evidence["event_loop_responsive"] = bool(responsive and responsive[0])
    return _save_reopen_and_inspect(
        app, window, destination, evidence, route=route,
        source=sample_path, data_type=data_type, close_window=close_window,
    )


def _run_binary_plot_edit_journey(
    app, sample_path, destination, *, window, close_window
):
    _open_analysis_sample(window, sample_path, "binary")
    _set_analysis_metric(window, "OR")
    responsive = []
    evidence = _run_worker_analysis(
        window,
        window.go,
        data_type="binary",
        metric="OR",
        workflow="standard",
        method="binary.random",
        qualification_route="binary.plot-edit",
        event_loop_responsive=responsive,
    )
    if "rpy2.robjects" in sys.modules:
        raise RuntimeError("plot edit journey loaded R into the main process")
    evidence["event_loop_responsive"] = bool(responsive and responsive[0])
    return _save_reopen_and_inspect(
        app, window, destination, evidence, route="binary.plot-edit",
        source=sample_path, data_type="binary", close_window=close_window,
    )


def _saved_forest_plot(viewer):
    section = next(
        (
            item for item in viewer.results.sections
            if item.kind == "image" and item.title == "Forest Plot"
        ),
        None,
    )
    if section is None:
        raise RuntimeError("saved binary result has no Forest Plot section")
    image_path = viewer.images.get(section.source_key)
    if not image_path:
        raise RuntimeError("saved binary result has no stored Forest Plot image")
    artifact = viewer.create_plot_artifact(section.source_key, image_path)
    plot_items = viewer._svg_plot_items + viewer._raster_plot_items
    if not artifact.can_edit() or len(plot_items) != 1:
        raise RuntimeError("saved Forest Plot cannot use the native appearance editor")
    return artifact


def _saved_figure_record(workspace, record_id, figure_key):
    from rc_metastudio import saved_analysis

    record = workspace.get_saved_analysis(record_id)
    if record is None:
        raise RuntimeError("saved figure record is unavailable")
    results = record.value["results"]
    images = results.get("images") if isinstance(results, dict) else None
    asset_name = images.get(figure_key) if isinstance(images, dict) else None
    image_data = record.assets.get(asset_name) if isinstance(asset_name, str) else None
    if not isinstance(image_data, bytes):
        raise RuntimeError("saved figure asset is unavailable")
    return record, saved_analysis.record_revision(record), hashlib.sha256(image_data).hexdigest()


def _figure_action(viewer, label):
    from PyQt6.QtWidgets import QGraphicsProxyWidget, QPushButton

    action_widgets = []
    for item in viewer._layout_items:
        if isinstance(item, QGraphicsProxyWidget):
            widget = item.widget()
            if widget is not None:
                action_widgets.append(widget)
    button = next(
        (
            button
            for widget in action_widgets
            for button in widget.findChildren(QPushButton)
            if button.accessibleName() == label and button.isEnabled()
        ),
        None,
    )
    if button is None:
        raise RuntimeError("saved result viewer has no enabled %s action" % label)
    return button


def _run_saved_plot_edits(viewer, window, evidence, qt_core):
    artifact = _saved_forest_plot(viewer)
    workspace = window.workspace
    record_id = evidence["analysis_id"]
    figure_key = artifact.figure_key
    _, revision_before_regenerate, _ = _saved_figure_record(
        workspace, record_id, figure_key
    )
    regenerate_button = _figure_action(viewer, "Regenerate figure")
    regenerate_response = _await_plot_operation(
        viewer.worker_client,
        regenerate_button.click,
        "saved_plot_render",
    )
    regenerate_request = _plot_worker_request_identity(
        regenerate_response, "saved_plot_render"
    )
    regenerate_identity = regenerate_request["artifact_identity"]
    if (
        regenerate_identity.get("analysis_id") != record_id
        or regenerate_identity.get("figure_key") != figure_key
    ):
        raise RuntimeError("saved regeneration response targeted a different figure")
    _, revision_after_regenerate, regenerated_sha = _saved_figure_record(
        workspace, record_id, figure_key
    )

    edit_button = _figure_action(viewer, "Edit appearance")
    edit_events, dialog, busy_waits = _edit_saved_forest_plot(
        viewer.worker_client,
        edit_button,
        "Qualification effect direction", qt_core,
    )
    if dialog._commit_outcome is not True:
        raise RuntimeError("saved figure editor did not commit its worker result")
    edit_request = _plot_worker_request_identity(
        edit_events, "saved_plot_render"
    )
    edit_identity = edit_request["artifact_identity"]
    if (
        edit_identity.get("analysis_id") != record_id
        or edit_identity.get("figure_key") != figure_key
    ):
        raise RuntimeError("saved appearance response targeted a different figure")
    edited_record, revision_after_edit, edited_sha = _saved_figure_record(
        workspace, record_id, figure_key
    )
    style = edited_record.value.get("presentation")
    xlabel = style.get("fp_xlabel") if isinstance(style, dict) else None
    if xlabel != "Qualification effect direction":
        raise RuntimeError("saved figure appearance was not stored in the record")
    if revision_after_edit == revision_after_regenerate:
        raise RuntimeError("saved figure edit did not advance the record revision")
    opened = _analysis_evidence(window, record_id, route="binary.plot-edit")
    if not _same_analysis_evidence(evidence, opened):
        raise RuntimeError("saved figure editing changed the scientific result")
    evidence["source_result_unchanged"] = True
    return {
        "saved_plot_regeneration": {
            "worker_completed": True,
            "worker_request": regenerate_request,
            "record_revision_before": revision_before_regenerate,
            "record_revision_after": revision_after_regenerate,
            "stored_image_sha256": regenerated_sha,
        },
        "saved_plot_edit": {
            "worker_completed": True,
            "worker_request": edit_request,
            "record_revision_before": revision_after_regenerate,
            "record_revision_after": revision_after_edit,
            "waited_for_worker_operations": busy_waits,
        },
        "saved_edited_artifact": {
            "persistence": "saved_record",
            "record_id": record_id,
            "figure_key": figure_key,
            "record_revision": revision_after_edit,
            "style": {"fp_xlabel": xlabel},
            "image_sha256": edited_sha,
        },
    }


def _edit_saved_forest_plot(client, edit_button, xlabel, qt_core):
    from PyQt6.QtWidgets import QApplication, QDialog
    from PyQt6.QtWidgets import QDialogButtonBox
    from rc_metastudio import plot_editor_dialog

    loop = qt_core.QEventLoop()
    events = []
    failure = {}
    edited = []
    busy_waits = []
    timer = qt_core.QTimer()
    timer.setInterval(20)
    timeout = qt_core.QTimer()
    timeout.setSingleShot(True)

    def completed(run_id, operation, identity, result):
        events.append((run_id, operation, identity, result))
        if operation == "saved_plot_render":
            loop.quit()

    def close_editor():
        dialog = edited[0] if edited else QApplication.activeModalWidget()
        if isinstance(dialog, QDialog) and dialog.isVisible():
            dialog.reject()

    def failed(run_id, operation, identity, error):
        failure["error"] = {
            "run_id": run_id,
            "operation": operation,
            "identity": identity,
            "error": error,
        }
        close_editor()
        loop.quit()

    def submit_edit():
        if edited:
            return
        if client.is_busy:
            busy_state = (
                getattr(client, "_operation", None),
                getattr(client, "_run_id", None),
            )
            if busy_state not in busy_waits:
                busy_waits.append(busy_state)
            return
        dialog = QApplication.activeModalWidget()
        if not isinstance(dialog, plot_editor_dialog.EditPlotDialog):
            dialog = next(
                (
                    widget
                    for widget in QApplication.topLevelWidgets()
                    if isinstance(widget, plot_editor_dialog.EditPlotDialog)
                    and widget.isVisible()
                ),
                None,
            )
        if dialog is None:
            return
        edited.append(dialog)
        button = dialog.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if button is None or not button.isEnabled():
            failure["error"] = "native plot editor has no enabled Apply control"
            dialog.reject()
            loop.quit()
            return
        dialog.x_lbl_le.setText(xlabel)
        button.click()

    def timed_out():
        dialog = edited[0] if edited else None
        failure["error"] = {
            "message": "plot editor did not finish within 120000 ms",
            "pending_ok": getattr(dialog, "_pending_ok", None),
            "commit_outcome": getattr(dialog, "_commit_outcome", None),
            "inline_error": (
                dialog._commit_error.text()
                if dialog is not None and hasattr(dialog, "_commit_error")
                else None
            ),
            "worker_busy": client.is_busy,
            "worker_operation": getattr(client, "_operation", None),
            "worker_run_id": getattr(client, "_run_id", None),
        }
        close_editor()
        loop.quit()

    client.plotCompleted.connect(completed)
    client.plotFailed.connect(failed)
    timer.timeout.connect(submit_edit)
    timeout.timeout.connect(timed_out)
    timer.start()
    timeout.start(120000)
    try:
        edit_button.click()
        if not any(event[1] == "saved_plot_render" for event in events) and not failure:
            loop.exec()
    finally:
        timer.stop()
        timeout.stop()
        client.plotCompleted.disconnect(completed)
        client.plotFailed.disconnect(failed)
    if failure:
        raise RuntimeError("saved plot edit worker failed: %s" % failure["error"])
    if not any(event[1] == "saved_plot_render" for event in events):
        raise TimeoutError("saved plot edit did not complete within 120000 ms")
    if not edited:
        raise RuntimeError("saved plot editor did not present its native edit form")
    return events, edited[0], busy_waits


def _await_plot_operation(client, action, operation, *, timeout_ms=120000):
    from PyQt6 import QtCore

    loop = QtCore.QEventLoop()
    outcome = {}

    def completed(run_id, response_operation, identity, result):
        if response_operation == operation:
            outcome["values"] = (run_id, response_operation, identity, result)
            loop.quit()

    def failed(run_id, response_operation, identity, error):
        outcome["error"] = (run_id, response_operation, identity, error)
        loop.quit()

    timer = QtCore.QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    client.plotCompleted.connect(completed)
    client.plotFailed.connect(failed)
    try:
        action()
        if not outcome:
            timer.start(timeout_ms)
            loop.exec()
        if "error" in outcome:
            raise RuntimeError("plot worker failed: %s" % (outcome["error"],))
        if "values" not in outcome:
            raise TimeoutError("plot worker operation timed out: %s" % operation)
        return outcome["values"]
    finally:
        timer.stop()
        client.plotCompleted.disconnect(completed)
        client.plotFailed.disconnect(failed)


def _plot_worker_request_identity(response, operation):
    if isinstance(response, list):
        response = next(
            (
                item for item in response
                if isinstance(item, tuple) and len(item) == 4
                and item[1] == operation
            ),
            None,
        )
    if not isinstance(response, tuple) or len(response) != 4:
        raise RuntimeError("plot worker response has no request identity")
    run_id, response_operation, artifact_identity, _result = response
    if response_operation != operation or not isinstance(artifact_identity, dict):
        raise RuntimeError("plot worker response identity does not match %s" % operation)
    return {
        "run_id": run_id,
        "operation": response_operation,
        "artifact_identity": dict(artifact_identity),
    }


def _sha256_path(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _run_reitsma_special(window, responsive, qt_core):
    from PyQt6.QtWidgets import QDialogButtonBox
    from rc_metastudio import reitsma_analysis_dialog

    window.reitsma()
    forms = window.findChildren(reitsma_analysis_dialog.ReitsmaAnalysisDialog)
    if not forms:
        raise RuntimeError("joint Reitsma settings did not open")
    form = forms[-1]
    if form.snapshot is None:
        raise _UnqualifiedRoute("diagnostic sample cannot provide complete Reitsma counts")
    _run_special_form(window, form, responsive, qt_core, QDialogButtonBox)


def _run_special_form(window, form, responsive, qt_core, button_box_type):
    def run():
        button = form.button_box.button(button_box_type.StandardButton.Ok)
        if button is None or not button.isEnabled():
            raise RuntimeError("analysis run control is disabled")
        button.click()
        qt_core.QTimer.singleShot(
            0,
            lambda: responsive.append(
                window.isVisible() and window.analysis_worker.is_busy
            ),
        )
    _await_worker(window.analysis_worker, run, window.analysis_worker.completed)


def _run_small_study_special(window, responsive, qt_core):
    from rc_metastudio import publication_bias_dialog
    from rc_metastudio.small_study_effects_core import freeze_small_study_effects_input

    form = publication_bias_dialog.PublicationBiasDialog(window.model, parent=window)
    snapshot = freeze_small_study_effects_input(window.model, form.preview_request())
    form.set_input_snapshot(snapshot)
    form.preview_requested.connect(
        lambda frozen, request: window.submit_small_study_effects_preview(
            form, frozen, request
        )
    )
    form.analysis_requested.connect(
        lambda frozen, request: window.submit_small_study_effects(
            form, frozen, request
        )
    )
    form.show()
    _await_worker(
        window.analysis_worker,
        lambda: _start_small_study_preview(form, window, responsive, qt_core),
        window.analysis_worker.completed,
    )
    report = form._eligibility_report
    if report is None:
        raise _UnqualifiedRoute(
            "RCMetaR did not return an eligibility report for the small-study sample"
        )
    if report.usable_studies < 3:
        raise _UnqualifiedRoute("fewer than three studies are eligible for small-study effects")
    _await_worker(window.analysis_worker, form.run, window.analysis_worker.completed)


def _start_small_study_preview(form, window, responsive, qt_core):
    form.start_preview()
    qt_core.QTimer.singleShot(
        0,
        lambda: responsive.append(window.isVisible() and window.analysis_worker.is_busy),
    )

def _run_diagnostic_subgroup_journey(
    app, sample_path, destination, *, window, close_window
):
    from PyQt6 import QtCore
    from rc_metastudio import analysis_setup_dialog, main_window, results_window

    route = "diagnostic.subgroup"
    sample_path = Path(sample_path).resolve()
    destination = Path(destination).resolve()
    covariate_name = _prepare_diagnostic_subgroup_sample(window, sample_path)
    run_evidence = []
    responsiveness = []
    for policy in ("exclude", "missing_category"):
        evidence, responsive = _run_diagnostic_subgroup_policy(
            window, covariate_name, policy, route, QtCore, analysis_setup_dialog
        )
        run_evidence.append(evidence)
        responsiveness.append(responsive)
    _verify_subgroup_policy_evidence(run_evidence)
    _save_subgroup_project(app, window, destination)

    reopened = main_window.MainWindow()
    try:
        saved_records = _open_subgroup_project(reopened, destination)
        _verify_reopened_subgroup_results(
            app, reopened, destination, saved_records, run_evidence, route,
            results_window,
        )
        if "rpy2.robjects" in sys.modules:
            raise RuntimeError("opening saved subgroup results loaded R into the main process")
        reopened.model.set_confidence_level(95.0)
        _await_window_worker_idle(reopened)
        saved_confidence, saved_policy = _edit_saved_subgroup_copy(
            reopened, run_evidence[0]["analysis_id"], analysis_setup_dialog,
            QtCore,
        )
        _mark_subgroup_reopened(run_evidence, sample_path)
        return {
            "analysis_runs": run_evidence,
            "event_loop_responsive": bool(responsiveness) and all(responsiveness),
            "reopened_analysis_count": len(saved_records),
            "saved_edit_copy_confidence_level": saved_confidence,
            "saved_edit_copy_missing_policy": saved_policy,
        }
    finally:
        close_window(app, reopened)


def _prepare_diagnostic_subgroup_sample(window, sample_path):
    if not sample_path.is_file():
        raise RuntimeError("packaged diagnostic sample is missing")
    if not window.open(str(sample_path), raise_on_error=True):
        raise RuntimeError("packaged diagnostic project could not be opened")
    if window.model.get_current_outcome_type() != "diagnostic":
        raise RuntimeError("packaged subgroup sample does not contain diagnostic data")
    _set_analysis_metric(window, "Sens")
    included = list(window.model.get_studies(only_if_included=True))
    if len(included) < 10:
        raise _UnqualifiedRoute(
            "diagnostic sample has too few included rows to exercise two groups and missing values"
        )
    covariate_name = "Qualification region"
    values = _qualification_region_values(window.model, included)
    window.model.add_covariate(covariate_name, "factor", values)
    window.model.set_confidence_level(90.0)
    return covariate_name


def _qualification_region_values(model, included_studies):
    missing_ids = {included_studies[1].id, included_studies[8].id}
    included_indices = {
        study.id: index for index, study in enumerate(included_studies)
    }
    values = {}
    for index, study in enumerate(model.dataset.studies):
        row_index = included_indices.get(study.id, index)
        values[study.name] = _qualification_region_value(study, row_index, missing_ids)
    return values


def _qualification_region_value(study, row_index, missing_ids):
    if study.id in missing_ids:
        return None
    return "North" if row_index % 2 == 0 else "South"


def _run_diagnostic_subgroup_policy(
    window, covariate_name, policy, route, qt_core, analysis_setup_dialog
):
    client = window.analysis_worker
    _await_window_worker_idle(window)
    before = len(window.workspace.list_saved_analyses())
    _await_worker(
        client,
        lambda policy=policy: window.meta_subgroup(covariate_name, policy),
        client.methodsReady,
    )
    _await_window_worker_idle(window)
    form = _diagnostic_subgroup_form(window, policy, analysis_setup_dialog)
    _configure_diagnostic_subgroup_form(form)
    responsive = []
    _run_diagnostic_subgroup_form(window, form, responsive, client, qt_core)
    if "rpy2.robjects" in sys.modules:
        raise RuntimeError("diagnostic subgroup analysis loaded R into the main process")
    saved = window.workspace.list_saved_analyses()
    if len(saved) != before + 1:
        raise RuntimeError("diagnostic subgroup did not create one saved result")
    return _analysis_evidence(window, str(saved[-1]["id"]), route=route), bool(
        responsive and responsive[0]
    )


def _diagnostic_subgroup_form(window, policy, dialog_type):
    forms = window.findChildren(dialog_type.AnalysisSetupDialog)
    form = next(
        (
            candidate for candidate in reversed(forms)
            if getattr(getattr(candidate, "_subgroup_plan", None), "missing_policy", None)
            == policy
        ),
        None,
    )
    if form is None or form.analysis_type != "subgroup":
        raise RuntimeError("diagnostic subgroup setup did not open for %s" % policy)
    return form


def _configure_diagnostic_subgroup_form(form):
    if form.current_param_vals.get("conf.level") != 90.0:
        raise RuntimeError("diagnostic subgroup setup lost the selected 90% confidence level")
    method_label = next(
        (label for label, method in form.available_method_d.items()
         if method == "diagnostic.random"),
        None,
    )
    if method_label is None:
        raise _UnqualifiedRoute("RCMetaR does not offer diagnostic.random subgroup analysis")
    form.method_cbo_box.setCurrentText(method_label)
    request = form.analysis_requests()[0]
    if request.parameter_values().get("conf.level") != 90.0:
        raise RuntimeError("diagnostic subgroup request did not preserve 90% confidence")


def _run_diagnostic_subgroup_form(window, form, responsive, client, qt_core):
    from PyQt6.QtWidgets import QDialogButtonBox

    def run():
        button = form.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if button is None or not button.isEnabled():
            raise RuntimeError("diagnostic subgroup run control is disabled")
        button.click()
        qt_core.QTimer.singleShot(
            0,
            lambda: responsive.append(window.isVisible() and client.is_busy),
        )
    _await_worker(client, run, client.completed)


def _verify_subgroup_policy_evidence(run_evidence):
    policies = [row["result_evidence"]["missing_policy"] for row in run_evidence]
    if policies != ["exclude", "missing_category"]:
        raise RuntimeError("diagnostic subgroup did not retain both missing-value decisions")
    if run_evidence[0]["study_order"] != run_evidence[1]["study_order"]:
        raise RuntimeError("diagnostic subgroup policies used different frozen study orders")


def _save_subgroup_project(app, window, destination):
    from rc_metastudio import main_window

    destination.parent.mkdir(parents=True, exist_ok=True)
    window.out_path = str(destination)
    _save_project_without_warnings(window, main_window, "diagnostic subgroup")
    _close_saved_journey_window(app, window, data_type="diagnostic subgroup")


def _open_subgroup_project(reopened, destination):
    reopened.workspace.mark_saved()
    if not reopened.open(str(destination), raise_on_error=True):
        raise RuntimeError("saved diagnostic subgroup project could not be reopened")
    records = reopened.workspace.list_saved_analyses()
    if len(records) != 2:
        raise RuntimeError("reopened diagnostic subgroup project lost a policy result")
    return records


def _verify_reopened_subgroup_results(
    app, reopened, destination, records, expected_runs, route, results_window
):
    for index, (record, expected) in enumerate(zip(records, expected_runs, strict=True)):
        _verify_one_reopened_subgroup(reopened, destination, record, expected, route, results_window)
        if index > 0:
            viewers = reopened.findChildren(results_window.ResultsWindow)
            if viewers:
                viewers[-1].close()
                app.processEvents()


def _verify_one_reopened_subgroup(reopened, destination, record, expected, route, results_window):
    opened = _analysis_evidence(reopened, str(record["id"]), route=route)
    if not _same_analysis_evidence(expected, opened):
        raise RuntimeError("diagnostic subgroup evidence changed after reopen")
    before = len(reopened.findChildren(results_window.ResultsWindow))
    reopened._open_saved_analysis(str(record["id"]))
    viewers = reopened.findChildren(results_window.ResultsWindow)
    if len(viewers) <= before:
        raise RuntimeError("reopened diagnostic subgroup result did not reach the native viewer")
    expected.update(_export_first_figure(viewers[-1], destination, route, results_window))


def _edit_saved_subgroup_copy(reopened, analysis_id, dialog_type, qt_core):
    from PyQt6.QtWidgets import QPushButton

    button = _saved_subgroup_edit_button(reopened, analysis_id, qt_core, QPushButton)
    if button is None or not button.isEnabled():
        raise RuntimeError("saved diagnostic subgroup history has no Edit a copy action")
    client = reopened.analysis_worker
    _await_worker(client, button.click, client.methodsReady)
    _await_window_worker_idle(reopened)
    forms = reopened.findChildren(dialog_type.AnalysisSetupDialog)
    form = _subgroup_edit_form(forms)
    if form is None or form.current_param_vals.get("conf.level") != 90.0:
        raise RuntimeError("saved diagnostic subgroup Edit a copy changed 90% confidence")
    request = form.analysis_requests()[0]
    if request.parameter_values().get("conf.level") != 90.0:
        raise RuntimeError("saved diagnostic subgroup request no longer has 90% confidence")
    confidence = form.current_param_vals["conf.level"]
    plan = getattr(form, "_subgroup_plan", None)
    policy = getattr(plan, "missing_policy", None)
    if not isinstance(policy, str):
        raise RuntimeError("saved subgroup Edit a copy lost its missing-value policy")
    form.close()
    return confidence, policy


def _saved_subgroup_edit_button(reopened, analysis_id, qt_core, button_type):
    panel = reopened.results_panel
    for row in range(panel.history_list.count()):
        item = panel.history_list.item(row)
        if item is not None and item.data(qt_core.Qt.ItemDataRole.UserRole) == analysis_id:
            history_row = panel.history_list.itemWidget(item)
            return next(
                (button for button in history_row.findChildren(button_type)
                 if button.text() == "Edit a copy"),
                None,
            ) if history_row is not None else None
    return None


def _subgroup_edit_form(forms):
    return next(
        (
            candidate for candidate in reversed(forms)
            if getattr(getattr(candidate, "_subgroup_plan", None), "missing_policy", None)
            == "exclude"
        ),
        None,
    )


def _mark_subgroup_reopened(run_evidence, sample_path):
    digest = hashlib.sha256(sample_path.read_bytes()).hexdigest()
    for evidence in run_evidence:
        evidence["saved_reopened"] = True
        evidence["sample_project_sha256"] = digest

def _save_reopen_and_inspect(
    app,
    window,
    destination,
    evidence,
    *,
    route,
    source,
    data_type,
    close_window,
):
    from rc_metastudio import main_window, results_window

    destination = Path(destination).resolve()
    if destination.suffix.lower() != ".rcms":
        destination = Path(str(destination) + ".rcms")
    destination.parent.mkdir(parents=True, exist_ok=True)
    window.out_path = str(destination)
    plot_edit = route == "binary.plot-edit"
    _save_project_without_warnings(window, main_window, data_type)

    _close_saved_journey_window(app, window, data_type=data_type)
    reopened = main_window.MainWindow()
    try:
        reopened.workspace.mark_saved()
        if not reopened.open(str(destination), raise_on_error=True):
            raise RuntimeError("saved %s project could not be reopened" % data_type)
        record = reopened.workspace.get_saved_analysis(evidence["analysis_id"])
        opened = _analysis_evidence(reopened, evidence["analysis_id"], route=route)
        if record is None or not _same_analysis_evidence(evidence, opened):
            raise RuntimeError("saved %s result changed after reopen" % route)
        reopened._open_saved_analysis(evidence["analysis_id"])
        viewers = reopened.findChildren(results_window.ResultsWindow)
        if len(viewers) != 1:
            raise RuntimeError("reopened %s result did not reach the native viewer" % route)
        viewer = viewers[0]
        if route == "diagnostic.reitsma-meta-regression":
            if not _reitsma_meta_regression_report_visible(viewer, evidence):
                raise RuntimeError(
                    "reopened Reitsma meta-regression report did not show its saved coefficients and tests"
                )
            evidence["report_view_after_reopen"] = True
        if route == "binary.plot-edit":
            from PyQt6 import QtCore

            evidence.update(_run_saved_plot_edits(viewer, reopened, evidence, QtCore))
            _save_project_without_warnings(reopened, main_window, data_type)
            _close_saved_journey_window(app, reopened, data_type=data_type)
            reopened = main_window.MainWindow()
            reopened.workspace.mark_saved()
            if not reopened.open(str(destination), raise_on_error=True):
                raise RuntimeError("edited saved project could not be reopened")
            record, revision, image_sha256 = _saved_figure_record(
                reopened.workspace,
                evidence["analysis_id"],
                evidence["saved_edited_artifact"]["figure_key"],
            )
            reopened_evidence = _analysis_evidence(
                reopened, evidence["analysis_id"], route=route
            )
            if not _same_analysis_evidence(evidence, reopened_evidence):
                raise RuntimeError("saved scientific result changed after figure edit")
            edited = evidence["saved_edited_artifact"]
            style = record.value.get("presentation")
            if (
                str(record.value.get("id")) != edited["record_id"]
                or revision != edited["record_revision"]
                or image_sha256 != edited["image_sha256"]
                or not isinstance(style, dict)
                or style.get("fp_xlabel") != edited["style"]["fp_xlabel"]
            ):
                raise RuntimeError("edited figure identity or appearance did not survive reopen")
            reopened._open_saved_analysis(evidence["analysis_id"])
            viewers = reopened.findChildren(results_window.ResultsWindow)
            if len(viewers) != 1:
                raise RuntimeError("edited saved result did not reopen in its native viewer")
            viewer = viewers[0]
            evidence["saved_edited_artifact_after_reopen"] = {
                "record_id": str(record.value["id"]),
                "figure_key": edited["figure_key"],
                "record_revision": revision,
                "style": {"fp_xlabel": style["fp_xlabel"]},
                "image_sha256": image_sha256,
            }
            evidence["saved_edited_reopened"] = True
        evidence.update(_export_first_figure(viewer, destination, route, results_window))
        if "rpy2.robjects" in sys.modules:
            raise RuntimeError("reopening %s result loaded R into the main process" % route)
        evidence["saved_reopened"] = True
        evidence["sample_project_sha256"] = hashlib.sha256(
            Path(source).read_bytes()
        ).hexdigest()
        return evidence
    finally:
        close_window(app, reopened)


def _save_project_without_warnings(window, main_window, data_type):
    from unittest.mock import patch

    def unexpected_warning(_parent, title, message, *_args):
        raise RuntimeError("unexpected warning during %s journey: %s: %s" % (data_type, title, message))

    with patch.object(main_window.QMessageBox, "warning", side_effect=unexpected_warning), patch.object(
        main_window.QMessageBox, "critical", side_effect=unexpected_warning
    ):
        if window.save() is not True:
            raise RuntimeError("packaged %s project could not be saved" % data_type)


def _close_saved_journey_window(app, window, *, data_type):
    if not window._flush_analysis_drafts():
        raise RuntimeError("saved %s result left an analysis draft that could not be closed" % data_type)
    if window.workspace.is_dirty and window.save() is not True:
        raise RuntimeError("saved %s result could not be flushed before close" % data_type)
    window.workspace.mark_saved()
    print("worker journey: closing saved %s project" % data_type, file=sys.stderr, flush=True)
    closed = window.close()
    app.processEvents()
    if not closed:
        raise RuntimeError("saved %s project window did not close before reopen" % data_type)
    print("worker journey: saved %s project closed" % data_type, file=sys.stderr, flush=True)


def _export_first_figure(viewer, destination, route, results_window):
    from unittest.mock import patch

    images = [
        (key, path) for key, path in viewer.images.items()
        if path and Path(path).is_file()
    ]
    if not images:
        return {"figure_status": "not_available"}
    figure_key, figure_path = images[0]
    artifact = viewer.create_plot_artifact(figure_key, figure_path)
    export_path = Path(destination).with_suffix(".%s.png" % str(route).replace(".", "-"))
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
        raise RuntimeError("reopened %s figure could not be exported offline" % route)
    return {
        "figure_status": "exported",
        "figure_key": figure_key,
        "figure_export_bytes": export_path.stat().st_size,
    }


def _reitsma_meta_regression_report_visible(viewer, evidence):
    details = getattr(viewer, "reitsma_meta_regression_details", None)
    sensitivity = getattr(viewer, "reitsma_sensitivity_coefficient_table", None)
    specificity = getattr(viewer, "reitsma_false_positive_rate_coefficient_table", None)
    tests = getattr(viewer, "reitsma_meta_regression_test_table", None)
    result_evidence = evidence.get("result_evidence")
    if (
        details is None
        or sensitivity is None
        or specificity is None
        or tests is None
        or not isinstance(result_evidence, dict)
    ):
        return False
    return _reitsma_report_details_visible(details, result_evidence) and _reitsma_report_tables_visible(
        sensitivity, specificity, tests, result_evidence
    )


def _reitsma_report_details_visible(details, evidence):
    text = details.text()
    return (
        "Eligible study IDs (%s)" % evidence["eligible_study_count"] in text
        and "exclusions (%s)" % len(evidence["exclusions"]) in text
        and "Qualification index" in text
    )


def _reitsma_report_tables_visible(sensitivity, specificity, tests, evidence):
    ml_estimator = tests.item(0, 2)
    return (
        sensitivity.rowCount() == len(evidence["sensitivity_coefficients"])
        and specificity.rowCount() == len(evidence["false_positive_rate_coefficients"])
        and tests.rowCount() == 2
        and ml_estimator is not None
        and ml_estimator.text() == "ML"
    )
