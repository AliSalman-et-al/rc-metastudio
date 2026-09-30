"""Packaged qualification of an owned worker analysis and retained result."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import sys
import uuid


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
_FAMILY_SEQUENTIAL_ROUTES = {
    "continuous.cumulative": ("continuous", "cumulative", "SMD", "continuous.random"),
    "diagnostic.cumulative": ("diagnostic", "cumulative", "Sens", "diagnostic.random"),
    "continuous.leave-one-out": (
        "continuous", "leave-one-out", "SMD", "continuous.random"
    ),
    "diagnostic.leave-one-out": (
        "diagnostic", "leave-one-out", "Sens", "diagnostic.random"
    ),
}
_SUBGROUP_ROUTES = {
    "binary.subgroup": ("binary", "OR", "binary.random"),
    "continuous.subgroup": ("continuous", "SMD", "continuous.random"),
    "diagnostic.subgroup": ("diagnostic", "Sens", "diagnostic.random"),
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
}
_METHOD_VARIANT_ROUTE_SPECS = tuple(
    (family, workflow, metric, method)
    for family, workflows, metric, methods in (
        (
            "binary",
            ("standard", "cumulative", "leave-one-out", "subgroup"),
            "OR",
            (
                "binary.fixed.inv.var",
                "binary.fixed.mh",
                "binary.fixed.peto",
            ),
        ),
        (
            "continuous",
            ("standard", "cumulative", "leave-one-out", "subgroup"),
            "SMD",
            ("continuous.fixed",),
        ),
        (
            "diagnostic",
            ("standard", "cumulative", "leave-one-out", "subgroup"),
            "Sens",
            ("diagnostic.fixed.inv.var",),
        ),
        (
            "diagnostic",
            ("standard", "cumulative", "leave-one-out", "subgroup"),
            "DOR",
            ("diagnostic.fixed.mh", "diagnostic.fixed.peto"),
        ),
    )
    for workflow in workflows
    for method in methods
)
_METHOD_VARIANT_ROUTES = {
    "%s.%s" % (method, workflow): (
        family, workflow, metric, method
    )
    for family, workflow, metric, method in _METHOD_VARIANT_ROUTE_SPECS
}
_METHOD_VARIANT_STANDARD_ROUTES = frozenset(
    route
    for route, (_family, workflow, _metric, _method)
    in _METHOD_VARIANT_ROUTES.items()
    if workflow == "standard"
)
_BINARY_WORKFLOWS.update(
    {
        route: workflow
        for route, (family, workflow, _metric, _method)
        in _METHOD_VARIANT_ROUTES.items()
        if family == "binary" and workflow in {"standard", "cumulative", "leave-one-out"}
    }
)
_FAMILY_SEQUENTIAL_ROUTES.update(
    {
        route: identity
        for route, identity in _METHOD_VARIANT_ROUTES.items()
        if identity[1] in {"cumulative", "leave-one-out"}
    }
)
_SUBGROUP_ROUTES.update(
    {
        route: (family, metric, method)
        for route, (family, workflow, metric, method)
        in _METHOD_VARIANT_ROUTES.items()
        if workflow == "subgroup"
    }
)
_FAMILY_ROUTES.update(
    {
        route: (family, metric, method)
        for route, (family, workflow, metric, method)
        in _METHOD_VARIANT_ROUTES.items()
        if family != "binary" and workflow == "standard"
    }
)
_STRICT_RESULT_SPECIFICATION_ROUTES = (
    frozenset(_METHOD_VARIANT_ROUTES)
    | frozenset(_FAMILY_SEQUENTIAL_ROUTES)
    | frozenset(_SUBGROUP_ROUTES)
)


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
        reopened = _dispatch_worker_journey_route(
            app, window, source, destination, route, close_window,
            write_evidence, output, QtCore,
        )
        return 0
    finally:
        if reopened is not None:
            close_window(app, reopened)
        close_window(app, window)


def _dispatch_worker_journey_route(
    app, window, source, destination, route, close_window,
    write_evidence, output, qt_core,
):
    if route in _FAMILY_ROUTES:
        _run_family_qualification_route(
            app, window, source, destination, route, close_window,
            write_evidence, output,
        )
        return None
    if _uses_other_qualification_route(route):
        _run_other_qualification_route(
            app, window, source, destination, route, close_window,
            write_evidence, output, qt_core,
        )
        return None
    return _run_binary_qualification_route(
        app, window, source, destination, route, close_window,
        write_evidence, output, qt_core,
    )


def _uses_other_qualification_route(route):
    return route not in _BINARY_WORKFLOWS and (
        route in _META_REGRESSION_ROUTES
        or route in _SPECIAL_ROUTES
        or route in _FAMILY_SEQUENTIAL_ROUTES
        or route in _SUBGROUP_ROUTES
    )


def _qualification_route_supported(route):
    return (
        route in _BINARY_WORKFLOWS
        or route in _FAMILY_SEQUENTIAL_ROUTES
        or route in _FAMILY_ROUTES
        or route in _SUBGROUP_ROUTES
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
    if route in _FAMILY_SEQUENTIAL_ROUTES:
        return _run_sequential_family_qualification_route(
            app, window, source, destination, route, close_window,
            write_evidence, output,
        )
    if route in _SUBGROUP_ROUTES:
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


def _run_sequential_family_qualification_route(
    app, window, source, destination, route, close_window, write_evidence, output
):
    data_type, workflow, metric, method = _FAMILY_SEQUENTIAL_ROUTES[route]
    _open_analysis_sample(window, source, data_type)
    _set_analysis_metric(window, metric)
    responsive = []
    action = window.cum_ma if workflow == "cumulative" else window.loo_ma
    try:
        form = _prepare_family_sequential_form(
            window, action, data_type, metric, workflow, method
        )
        if workflow == "cumulative":
            _configure_cumulative_order(form)
        evidence = _run_worker_analysis(
            window, action,
            data_type=data_type,
            metric=metric,
            workflow=workflow,
            method=method,
            qualification_route=route,
            event_loop_responsive=responsive,
            prepared_form=form,
        )
        evidence["event_loop_responsive"] = bool(responsive and responsive[0])
        _save_reopen_and_inspect(
            app, window, destination, evidence, route=route,
            source=source, data_type=data_type, close_window=close_window,
        )
    except _UnqualifiedRoute as error:
        _write_unqualified_qualification(write_evidence, output, route, error)
        return 0

    write_evidence(str(output), {
        "route": route,
        "qualification_status": "complete",
        "worker_completed": True,
        "event_loop_responsive": evidence["event_loop_responsive"],
        "saved_analysis_status": evidence["status"],
        "reopened_analysis_count": 1,
        "analysis_runs": [evidence],
        "main_process_r_bridge_absent": "rpy2.robjects" not in sys.modules,
    })
    return 0


def _prepare_family_sequential_form(window, action, data_type, metric, workflow, method):
    _client, form, _before = _prepare_worker_analysis_form(
        window, action, data_type, metric, workflow, method
    )
    return form


def _configure_cumulative_order(form):
    form.cumulative_order_field.setCurrentIndex(
        form.cumulative_order_field.findData("project_order")
    )
    form.cumulative_direction.setCurrentIndex(
        form.cumulative_direction.findData("descending")
    )
    form._refresh_cumulative_sequence_preview()
    ordering = form._cumulative_snapshot().ordering
    if ordering.field != "project_order" or ordering.direction != "descending":
        raise RuntimeError("cumulative qualification did not freeze descending project order")


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
        subgroup = _run_subgroup_journey(
            app, source, destination, window=window, route=route,
            close_window=close_window,
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
    method = _METHOD_VARIANT_ROUTES.get(
        route, ("binary", workflow, "OR", "binary.random")
    )[3]
    _open_binary_project(window, source)
    records, selected, responsive = _run_binary_analyses(
        window,
        workflow,
        method,
        qualification_route=(route if route in _METHOD_VARIANT_ROUTES else None),
    )
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
    selected["figure_status"] = "exported"
    selected["figure_export_bytes"] = export_bytes
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


def _run_binary_analyses(window, workflow, method, *, qualification_route=None):
    records = []
    if workflow != "standard":
        records.append(_run_worker_analysis(
            window, window.go, data_type="binary", metric="OR",
            workflow="standard", method="binary.random",
        ))
    action = _binary_workflow_action(window, workflow)
    responsive = []
    prepared_form = None
    if qualification_route is not None:
        _client, prepared_form, _before = _prepare_worker_analysis_form(
            window, action, "binary", "OR", workflow, method
        )
        if workflow == "cumulative":
            _configure_cumulative_order(prepared_form)
    selected = _run_worker_analysis(
        window, action, data_type="binary", metric="OR", workflow=workflow,
        method=method, qualification_route=qualification_route,
        event_loop_responsive=responsive, prepared_form=prepared_form,
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
        _compare_binary_results(
            reopened,
            saved,
            records,
            route=route,
            selected_analysis_id=selected["analysis_id"],
        )
        selected["saved_reopened"] = True
        reopened._open_saved_analysis(selected["analysis_id"])
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


def _compare_binary_results(
    reopened, saved, expected_records, *, route, selected_analysis_id
):
    for record, expected in zip(saved, expected_records, strict=True):
        evidence_route = (
            route
            if expected["analysis_id"] == selected_analysis_id
            and route in _METHOD_VARIANT_ROUTES
            else None
        )
        opened = _analysis_evidence(
            reopened, str(record["id"]), route=evidence_route
        )
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
    prepared_form=None,
):
    if prepared_form is None:
        client, form, before = _prepare_worker_analysis_form(
            window, action, data_type, metric, workflow, method
        )
    else:
        client = window.analysis_worker
        form = prepared_form
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
    return _add_route_result_evidence(evidence, route, record)


def _add_route_result_evidence(evidence, route, record):
    route_evidence = _route_result_evidence(route, record)
    if route_evidence is None:
        _raise_unavailable_route_result(route, record)
    evidence["result_evidence"] = route_evidence
    _update_cumulative_study_order(route, evidence, route_evidence)
    route_spec = (
        None
        if route in _STRICT_RESULT_SPECIFICATION_ROUTES
        else _qualification_route_identity(route)
    )
    if route_spec is not None:
        evidence.update(dict(zip(
            ("data_type", "workflow", "metric", "method"),
            route_spec,
            strict=True,
        )))
    return evidence


def _raise_unavailable_route_result(route, record):
    if route == "binary.plot-edit":
        details = _plot_edit_result_details(record)
        raise _UnqualifiedRoute("binary.plot-edit has no available result (%s)" % details)
    if route in _SUBGROUP_ROUTES:
        details = _subgroup_result_failure_details(record)
        raise _UnqualifiedRoute("%s produced no valid subgroup numerics (%s)" % (route, details))
    if route.endswith(".cumulative"):
        stage = _cumulative_evidence_failure_stage(record)
        raise _UnqualifiedRoute("%s produced no available cumulative result (%s)" % (route, stage))
    raise _UnqualifiedRoute(
        "%s produced no available numerical or semantic result" % route
    )


def _update_cumulative_study_order(route, evidence, route_evidence):
    if not route.endswith(".cumulative"):
        return
    order = route_evidence.get("study_order")
    if isinstance(order, list) and all(isinstance(name, str) for name in order):
        evidence["study_order"] = order


def _plot_edit_result_details(record):
    results = record.get("results")
    if not isinstance(results, dict):
        return "result payload missing"
    snapshot = _plot_edit_input_snapshot(record.get("input_snapshot"))
    images = results.get("images")
    studies = snapshot.get("studies") if isinstance(snapshot, dict) else None
    numerics = results.get("binary_numerics")
    pooled = numerics.get("pooled") if isinstance(numerics, dict) else None
    return "result_status=%s result_fields=%s image_keys=%s numeric_fields=%s pooled_binary_numerics=%s section_statuses=%s worker_error_fields=%s study_count=%s" % (
        results.get("status"),
        sorted(results),
        sorted(images) if isinstance(images, dict) else [],
        sorted(key for key in results if key.endswith("_numerics")),
        pooled,
        _plot_edit_section_statuses(results.get("sections")),
        _plot_edit_error_fields(results),
        len(studies) if isinstance(studies, list) else "missing",
    )


def _plot_edit_input_snapshot(snapshot):
    if isinstance(snapshot, dict):
        nested = snapshot.get("input_snapshot")
        return nested if isinstance(nested, dict) else snapshot
    return None


def _plot_edit_section_statuses(sections):
    return [
        (section.get("source_key"), section.get("status"))
        for section in sections
        if isinstance(section, dict)
    ] if isinstance(sections, list) else []


def _plot_edit_error_fields(results):
    return sorted(key for key in results if "error" in key.lower())


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
    if status == "complete":
        return status
    if _partial_sequential_result_valid(status, route, record):
        return status
    if route is None:
        raise RuntimeError("analysis did not produce a complete retained result")
    raise _incomplete_route_error(record, route, status)


def _partial_sequential_result_valid(status, route, record):
    return (
        status == "partial"
        and route in _FAMILY_SEQUENTIAL_ROUTES
        and _route_result_evidence(route, record) is not None
    )


def _incomplete_route_error(record, route, status):
    estimate_status = _binary_pooled_estimate_status(record)
    plot_details = (
        "; %s" % _plot_edit_result_details(record)
        if route == "binary.plot-edit"
        else ""
    )
    return _UnqualifiedRoute(
        "%s retained result status is %s (warnings: %s; pooled estimate status: %s%s)"
        % (
            route,
            status or "missing",
            record.get("warnings", []),
            estimate_status,
            plot_details,
        )
    )


def _binary_pooled_estimate_status(record):
    results = record.get("results")
    numerics = results.get("binary_numerics") if isinstance(results, dict) else None
    pooled = numerics.get("pooled") if isinstance(numerics, dict) else None
    display = pooled.get("display") if isinstance(pooled, dict) else None
    estimate = display.get("estimate") if isinstance(display, dict) else None
    return estimate.get("status") if isinstance(estimate, dict) else "missing"


def _analysis_input_identity(record):
    input_identity = record.get("input_identity")
    if not isinstance(input_identity, str) or len(input_identity) != 64:
        raise RuntimeError("saved analysis has no stable input identity")
    return input_identity


def _analysis_study_names(studies):
    if any(not isinstance(study, dict) or not isinstance(study.get("name"), str) for study in studies):
        return None
    return [study["name"] for study in studies]


def _analysis_study_id(study):
    if not isinstance(study, dict):
        return None
    value = study.get("id")
    return value if type(value) is int else study.get("study_id")


def _analysis_study_ids(studies):
    ids = [_analysis_study_id(study) for study in studies]
    if any(type(study_id) is not int for study_id in ids):
        return None
    if len(set(ids)) != len(ids):
        return None
    return ids


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
    if route in _METHOD_VARIANT_ROUTES:
        return _METHOD_VARIANT_ROUTES[route]
    return {
        **_FAMILY_SEQUENTIAL_ROUTES,
        **{
            name: (family, "subgroup", metric, method)
            for name, (family, metric, method) in _SUBGROUP_ROUTES.items()
        },
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
    if route in _STRICT_RESULT_SPECIFICATION_ROUTES:
        expected = _qualification_route_identity(route)
        if not _route_specification_matches(record.get("specification"), expected):
            return None
    if route not in _FAMILY_SEQUENTIAL_ROUTES:
        snapshot = snapshot.get("input_snapshot", snapshot)
    if not isinstance(snapshot, dict):
        return None
    builder = _ROUTE_RESULT_BUILDERS.get(route)
    return builder(results, snapshot, record) if builder is not None else None


def _method_variant_result_evidence(results, snapshot, record, route):
    expected = _METHOD_VARIANT_ROUTES.get(route)
    specification = record.get("specification")
    studies = snapshot.get("studies")
    if (
        expected is None
        or not _route_specification_matches(specification, expected)
        or not isinstance(studies, list)
    ):
        return None
    names = _analysis_study_names(studies)
    if names is None:
        return None
    numerics = _method_variant_numerics(results, expected[0], expected[2])
    if numerics is None:
        return None
    summary = _method_variant_pooled_summary(expected[0], numerics, len(studies))
    if summary is None or not _method_variant_studies_match(numerics, names):
        return None
    estimate, count = summary
    return {
        "status": "available",
        "kind": "method-variant",
        "family": expected[0],
        "workflow": expected[1],
        "metric": expected[2],
        "method": expected[3],
        "estimate": estimate,
        "study_count": int(count),
        "input_study_count": len(studies),
        "study_order": names,
        "figure_status": _stored_figure_status(results),
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }


def _route_specification_matches(specification, expected):
    return isinstance(specification, dict) and tuple(
        specification.get(field)
        for field in ("data_type", "workflow", "metric", "method")
    ) == expected


def _method_variant_numerics(results, family, metric):
    numerics = results.get("%s_numerics" % family)
    return (
        numerics
        if isinstance(numerics, dict) and numerics.get("metric") == metric
        else None
    )


def _method_variant_pooled_summary(family, numerics, input_count):
    pooled = numerics.get("pooled")
    if not isinstance(pooled, dict):
        return None
    estimate, count = _method_variant_pooled_values(family, numerics, pooled)
    if not _method_variant_pooled_values_valid(estimate, count, input_count):
        return None
    return estimate, int(count)


def _method_variant_pooled_values(family, numerics, pooled):
    if family == "continuous":
        estimate = _available_value(pooled.get("estimate"))
        count = _available_value(numerics.get("analyzed_study_count"))
    else:
        display = pooled.get("display")
        estimate = _available_value(
            display.get("estimate") if isinstance(display, dict) else None
        )
        count = _available_value(pooled.get("study_count"))

    return estimate, count


def _method_variant_pooled_values_valid(estimate, count, input_count):
    if (
        estimate is None
        or count is None
        or not float(count).is_integer()
        or count <= 0
        or count > input_count
    ):
        return False
    return True


def _method_variant_studies_match(numerics, names):
    studies = numerics.get("studies")
    return isinstance(studies, list) and _study_labels(studies) == names


def _subgroup_result_failure_details(record):
    parts = _subgroup_failure_parts(record)
    if parts is None:
        return "subgroup result context is unavailable"
    specification, plan, numerics, studies, covariates, parameters = parts
    plan_valid, arrays_valid, evidence_stage = _subgroup_failure_checks(parts)
    return "workflow=%s data_type=%s metric=%s method=%s plan=%s numerics=%s plan_valid=%s arrays_valid=%s evidence_stage=%s" % (
        specification.get("workflow"),
        specification.get("data_type"),
        specification.get("metric"),
        specification.get("method"),
        _subgroup_identity_summary(plan),
        _subgroup_identity_summary(numerics),
        plan_valid,
        arrays_valid,
        evidence_stage,
    )


def _subgroup_failure_parts(record):
    specification = record.get("specification")
    snapshot = record.get("input_snapshot")
    results = record.get("results")
    if not all(isinstance(value, dict) for value in (specification, snapshot, results)):
        return None
    snapshot = snapshot.get("input_snapshot", snapshot)
    if not isinstance(snapshot, dict):
        return None
    return (
        specification,
        results.get("subgroup_plan"),
        results.get("subgroup_numerics"),
        snapshot.get("studies"),
        snapshot.get("covariates"),
        specification.get("params"),
    )


def _subgroup_failure_checks(parts):
    specification, plan, numerics, studies, covariates, parameters = parts
    plan_valid = _subgroup_plan_valid(
        plan,
        numerics,
        studies,
        covariates,
        parameters,
        specification.get("data_type"),
        specification.get("metric"),
        specification.get("method"),
    )
    if not plan_valid:
        return False, False, "plan"
    covariate = _qualification_covariate(covariates, plan["covariate_name"])
    raw_values = covariate.get("values") if isinstance(covariate, dict) else None
    arrays_valid = _subgroup_arrays_valid(
        studies, raw_values, plan.get("assignments"), plan.get("levels"), numerics.get("levels")
    )
    if not arrays_valid:
        return True, False, "arrays"
    stage = _subgroup_evidence_failure_stage(plan, numerics, studies, raw_values)
    return True, True, stage


def _subgroup_evidence_failure_stage(plan, numerics, studies, raw_values):
    assignments = plan.get("assignments")
    raw_levels = plan.get("levels")
    numerical_levels = numerics.get("levels")
    assignment_evidence = _subgroup_assignment_evidence(
        studies, assignments, raw_values
    )
    if assignment_evidence is None:
        return "assignments: %s" % _subgroup_first_bad_assignment(
            studies, assignments, raw_values
        )
    level_evidence = _subgroup_level_evidence(
        raw_levels, numerical_levels, _subgroup_study_names_by_id(studies)
    )
    if level_evidence is None:
        return "levels: %s" % _subgroup_model_failure_details(numerical_levels)
    status = _subgroup_status_evidence(numerics)
    if status is None:
        return "status"
    overall, _between = status
    if _subgroup_model_observation(overall) is None:
        return "overall: %s" % _subgroup_model_failure_details([overall])
    return "valid"


def _subgroup_first_bad_assignment(studies, assignments, values):
    for index, (study, assignment, value) in enumerate(
        zip(studies, assignments, values, strict=True)
    ):
        if _subgroup_assignment_row(study, assignment, value) is None:
            return {
                "index": index,
                "study_name": study.get("name") if isinstance(study, dict) else None,
                "study_id": _subgroup_study_id(study) if isinstance(study, dict) else None,
                "assignment": assignment,
                "raw_value": value,
            }
    return None


def _subgroup_model_failure_details(rows):
    if not isinstance(rows, (list, tuple)):
        return []
    return [_subgroup_model_failure_row(row) for row in rows]


def _subgroup_model_failure_row(row):
    if not isinstance(row, dict):
        return {"type": type(row).__name__}
    return {
        "type": type(row).__name__,
        "status": row.get("status"),
        "reason": row.get("reason"),
        "fields": sorted(row),
        "estimate": row.get("estimate"),
        "lower_bound": row.get("lower_bound"),
        "upper_bound": row.get("upper_bound"),
    }


def _subgroup_identity_summary(value):
    if not isinstance(value, dict):
        return type(value).__name__
    fields = (
        "family", "metric", "covariate_name", "missing_policy",
        "included_count", "missing_count", "excluded_count",
    )
    summary = {field: value.get(field) for field in fields if field in value}
    for key in ("assignments", "levels"):
        rows = value.get(key)
        if isinstance(rows, (list, tuple)):
            summary[key] = _subgroup_identity_rows(rows)
    overall = value.get("overall")
    if isinstance(overall, dict):
        summary["overall"] = _selected_subgroup_fields(
            overall, ("status", "included_count", "reason")
        )
    return summary


def _subgroup_identity_rows(rows):
    return [
        _selected_subgroup_fields(
            row, ("label", "status", "included_count", "study_ids")
        )
        for row in rows
        if isinstance(row, dict)
    ]


def _selected_subgroup_fields(value, fields):
    return {field: value.get(field) for field in fields if field in value}


def _cumulative_result_evidence(results, snapshot, record):
    context = _cumulative_evidence_context(results, snapshot, record)
    if context is None:
        return None
    specification, sequence, studies, numerics, steps = context
    observations = _cumulative_step_observations(sequence, steps)
    if observations is None or not _cumulative_order_matches_studies(sequence, studies):
        return None
    status = _cumulative_result_status(numerics, record, observations["steps"])
    if status is None:
        return None
    return {
        "status": "available",
        "kind": "cumulative-analysis",
        "data_type": specification.get("data_type"),
        "metric": specification.get("metric"),
        "result_status": status,
        "ordering": numerics.get("ordering"),
        "input_study_count": len(studies),
        "input_study_ids": [_analysis_study_id(study) for study in studies],
        "study_ids": [step["study_id"] for step in observations["steps"]],
        "study_order": observations["study_order"],
        "steps": observations["steps"],
        "figure_status": _stored_figure_status(results),
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }


def _cumulative_evidence_context(results, snapshot, record):
    specification = record.get("specification")
    if not isinstance(specification, dict):
        return None
    route = "%s.cumulative" % specification.get("data_type")
    sequence = snapshot.get("sequence")
    original = snapshot.get("input_snapshot")
    studies = original.get("studies") if isinstance(original, dict) else None
    numerics = results.get("cumulative_numerics")
    steps = numerics.get("steps") if isinstance(numerics, dict) else None
    ordering = snapshot.get("ordering")
    if not _cumulative_input_valid(route, specification, sequence, studies, numerics, steps, ordering):
        return None
    if not _cumulative_result_mapping_valid(numerics):
        return None
    return specification, sequence, studies, numerics, steps


def _cumulative_evidence_failure_stage(record):
    parts = _cumulative_failure_parts(record)
    if parts is None:
        return "record context"
    stage = _cumulative_input_failure_stage(parts)
    if stage is not None:
        return stage
    _route, _specification, _snapshot, _results, sequence, studies, numerics, steps, _ordering = parts
    observations = _cumulative_step_observations(sequence, steps)
    if observations is None:
        return "step identity or numeric status"
    if not _cumulative_order_matches_studies(sequence, studies):
        return "source study order"
    return (
        "result status"
        if _cumulative_result_status(numerics, record, observations["steps"]) is None
        else "unknown"
    )


def _cumulative_failure_parts(record):
    specification = record.get("specification")
    snapshot = record.get("input_snapshot")
    results = record.get("results")
    if not isinstance(specification, dict) or not isinstance(snapshot, dict) or not isinstance(results, dict):
        return None
    route = "%s.cumulative" % specification.get("data_type")
    sequence = snapshot.get("sequence")
    original = snapshot.get("input_snapshot")
    studies = original.get("studies") if isinstance(original, dict) else None
    numerics = results.get("cumulative_numerics")
    steps = numerics.get("steps") if isinstance(numerics, dict) else None
    ordering = snapshot.get("ordering")
    return route, specification, snapshot, results, sequence, studies, numerics, steps, ordering


def _cumulative_input_failure_stage(parts):
    route, specification, _snapshot, _results, sequence, studies, numerics, steps, ordering = parts
    if not _cumulative_specification_valid(route, specification):
        return "specification"
    if not _cumulative_sequence_shape_valid(sequence, studies, ordering):
        return "frozen sequence or order"
    if not _cumulative_result_shape_valid(numerics, steps, sequence, ordering):
        return "result sequence or ordering"
    if not _cumulative_result_mapping_valid(numerics):
        return "cumulative result contract"
    return None


def _cumulative_result_mapping_valid(numerics):
    try:
        from rc_metastudio.cumulative_analysis import CumulativeAnalysisResult

        CumulativeAnalysisResult.from_mapping(numerics)
    except (TypeError, ValueError):
        return False
    return True


def _cumulative_input_valid(route, specification, sequence, studies, numerics, steps, ordering):
    return (
        _cumulative_specification_valid(route, specification)
        and _cumulative_sequence_shape_valid(sequence, studies, ordering)
        and _cumulative_result_shape_valid(numerics, steps, sequence, ordering)
    )


def _cumulative_specification_valid(route, specification):
    return (
        specification.get("workflow") == "cumulative"
        and _sequential_specification_matches(route, specification)
    )


def _cumulative_sequence_shape_valid(sequence, studies, ordering):
    return (
        isinstance(sequence, list)
        and isinstance(studies, list)
        and len(sequence) == len(studies)
        and isinstance(ordering, dict)
        and ordering.get("field") == "project_order"
        and ordering.get("direction") == "descending"
    )


def _cumulative_result_shape_valid(numerics, steps, sequence, ordering):
    return (
        isinstance(steps, list)
        and len(steps) == len(sequence)
        and isinstance(numerics, dict)
        and numerics.get("ordering") == ordering
    )


def _cumulative_step_observations(sequence, steps):
    observed = []
    names = []
    for index, (planned, step) in enumerate(zip(sequence, steps, strict=True)):
        item = _cumulative_step_observation(planned, step, index, len(sequence))
        if item is None:
            return None
        observed.append(item)
        names.append(item["study_name"])
    return {"steps": observed, "study_order": names}


def _cumulative_step_observation(planned, step, index, step_count):
    if not isinstance(planned, dict) or not isinstance(step, dict):
        return None
    study_id = planned.get("study_id")
    study_name = planned.get("study_name")
    if not _cumulative_step_identity_valid(
        planned, step, study_id, study_name, index, step_count
    ):
        return None
    numbers = _cumulative_numeric_observations(step)
    if numbers is None:
        return None
    return {
        "order": index,
        "source_order": planned.get("source_order"),
        "study_id": study_id,
        "study_name": study_name,
        "included_study_count": index + 1,
        "status": step.get("status"),
        "numbers": numbers,
    }


def _cumulative_result_status(numerics, record, steps):
    status = "complete" if all(step["status"] == "complete" for step in steps) else "partial"
    return status if numerics.get("status") == record.get("status") == status else None


def _sequential_specification_matches(route, specification):
    actual = (
        specification.get("data_type"),
        specification.get("workflow"),
        specification.get("metric"),
        specification.get("method"),
    )
    expected = _FAMILY_SEQUENTIAL_ROUTES.get(route)
    return (expected is not None and actual == expected) or any(
        identity == actual and "%s.%s" % (identity[0], identity[1]) == route
        for identity in _METHOD_VARIANT_ROUTE_SPECS
    )


def _cumulative_step_identity_valid(
    planned, step, study_id, study_name, index, step_count
):
    return (
        _cumulative_source_identity_valid(planned, step, study_id, study_name)
        and _cumulative_position_valid(planned, step, index, step_count)
    )


def _cumulative_source_identity_valid(planned, step, study_id, study_name):
    return (
        type(study_id) is int
        and isinstance(study_name, str)
        and bool(study_name)
        and type(planned.get("source_order")) is int
        and step.get("source_order") == planned.get("source_order")
        and step.get("study_id") == study_id
        and step.get("study_name") == study_name
        and step.get("ordering_value") == planned.get("ordering_value")
    )


def _cumulative_position_valid(planned, step, index, step_count):
    return (
        planned.get("order") == index
        and planned.get("included_study_count") == index + 1
        and step.get("order") == index
        and step.get("included_study_count") == index + 1
        and step.get("is_final") is (index == step_count - 1)
    )


def _cumulative_order_matches_studies(sequence, studies):
    source_by_id = _cumulative_source_index(studies)
    return source_by_id is not None and _cumulative_sequence_matches(
        sequence, source_by_id
    )


def _cumulative_source_index(studies):
    source_by_id = {}
    for index, study in enumerate(studies):
        study_id = _analysis_study_id(study)
        name = study.get("name") if isinstance(study, dict) else None
        if type(study_id) is not int or not isinstance(name, str) or not name:
            return None
        if study_id in source_by_id:
            return None
        source_by_id[study_id] = (index, name)
    return source_by_id


def _cumulative_sequence_matches(sequence, source_by_id):
    if not all(isinstance(step, dict) for step in sequence):
        return False
    ids = [step.get("study_id") for step in sequence]
    if not _cumulative_sequence_id_set_valid(ids, source_by_id):
        return False
    return all(
        _cumulative_sequence_step_matches(step, source_by_id)
        for step in sequence
    )


def _cumulative_sequence_id_set_valid(ids, source_by_id):
    return (
        all(type(study_id) is int for study_id in ids)
        and len(set(ids)) == len(ids)
        and set(ids) == set(source_by_id)
    )


def _cumulative_sequence_step_matches(step, source_by_id):
    source_order, name = source_by_id[step["study_id"]]
    return step.get("source_order") == source_order and step.get("study_name") == name


def _cumulative_numeric_observations(step):
    fields = (
        "analyzed_study_count", "estimate", "lower_bound", "upper_bound",
        "standard_error", "p_value",
    )
    observations = {field: _numeric_observation(step.get(field)) for field in fields}
    if any(value is None for value in observations.values()):
        return None
    analyzed = observations["analyzed_study_count"]
    if not _cumulative_observed_count_valid(
        analyzed, step.get("included_study_count")
    ):
        return None
    return observations


def _cumulative_observed_count_valid(observed, included_count):
    if observed.get("status") == "available":
        return observed.get("value") == included_count
    return observed.get("status") == "not_available"


def _numeric_observation(value):
    if not isinstance(value, dict):
        return None
    observed = _numeric_observation_value(value)
    if observed is None:
        return None
    status, number, reason = observed
    return {"status": status, "value": number, "reason": reason}


def _numeric_observation_value(value):
    status = value.get("status")
    number = value.get("value")
    reason = value.get("reason")
    if status == "available":
        return (status, number, reason) if _finite_result_number(number) and reason is None else None
    if status in {"not_estimable", "not_available"}:
        return (status, None, reason) if number is None and _nonempty_text(reason) else None
    return None


def _nonempty_text(value):
    return isinstance(value, str) and bool(value)


def _leave_one_out_result_evidence(results, snapshot, record):
    context = _leave_one_out_evidence_context(results, snapshot, record)
    if context is None:
        return None
    specification, studies, numerics, rows = context
    observations = _leave_one_out_observations(rows, studies)
    study_order = _analysis_study_names(studies)
    study_ids = _analysis_study_ids(studies)
    if observations is None or study_order is None or study_ids is None:
        return None
    status = _leave_one_out_result_status(record, observations)
    if status is None:
        return None
    return {
        "status": "available",
        "kind": "leave-one-out-analysis",
        "data_type": specification.get("data_type"),
        "metric": specification.get("metric"),
        "result_status": status,
        "row_status_result": status,
        "input_study_count": len(studies),
        "study_ids": study_ids,
        "study_order": study_order,
        "rows": observations,
        "figure_status": _stored_figure_status(results),
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }


def _leave_one_out_evidence_context(results, snapshot, record):
    specification = record.get("specification")
    if not isinstance(specification, dict):
        return None
    snapshot = snapshot.get("input_snapshot", snapshot)
    if not isinstance(snapshot, dict):
        return None
    numerics = results.get("leave_one_out_numerics")
    studies = snapshot.get("studies")
    rows = numerics.get("rows") if isinstance(numerics, dict) else None
    if not _leave_one_out_snapshot_matches(specification, studies, rows):
        return None
    if not _leave_one_out_numerics_match(specification, numerics):
        return None
    return specification, studies, numerics, rows


def _leave_one_out_snapshot_matches(specification, studies, rows):
    route = "%s.leave-one-out" % specification.get("data_type")
    return (
        specification.get("workflow") == "leave-one-out"
        and _sequential_specification_matches(route, specification)
        and isinstance(studies, list)
        and len(studies) >= 2
        and isinstance(rows, list)
        and len(rows) == len(studies) + 1
    )


def _leave_one_out_numerics_match(specification, numerics):
    return (
        isinstance(numerics, dict)
        and numerics.get("data_type") == specification.get("data_type")
        and numerics.get("method") == specification.get("method")
        and numerics.get("metric") == specification.get("metric")
        and numerics.get("change_convention") == "omitted_minus_baseline"
    )


def _leave_one_out_observations(rows, studies):
    observed_rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            return None
        expected_study = None if index == 0 else studies[index - 1]
        observation = _leave_one_out_row_observation(row, index, expected_study, len(studies))
        if observation is None:
            return None
        observed_rows.append(observation)
    return observed_rows


def _leave_one_out_result_status(record, rows):
    status = (
        "complete"
        if all(row["status"] == "available" for row in rows)
        else "partial"
    )
    return status if record.get("status") == status else None


def _leave_one_out_row_observation(row, index, expected_study, study_count):
    if not _leave_one_out_row_identity_valid(row, index, expected_study, study_count):
        return None
    numbers = _leave_one_out_numeric_observations(row)
    if numbers is None or not _leave_one_out_status_valid(row, numbers):
        return None
    return {
        "kind": "baseline" if index == 0 else "omission",
        "label": row.get("label"),
        "study_id": row.get("study_id"),
        "remaining_study_count": study_count if index == 0 else study_count - 1,
        "status": row.get("status"),
        "numbers": numbers,
    }


def _leave_one_out_row_identity_valid(row, index, expected_study, study_count):
    expected_count = study_count if index == 0 else study_count - 1
    if not _leave_one_out_row_fields_valid(row, index, expected_count):
        return False
    if index == 0:
        return _leave_one_out_baseline_identity_valid(row)
    return _leave_one_out_omission_identity_valid(row, expected_study)


def _leave_one_out_row_fields_valid(row, index, expected_count):
    expected_kind = "baseline" if index == 0 else "omission"
    return (
        row.get("kind") == expected_kind
        and row.get("remaining_study_count") == expected_count
        and row.get("status") in {"available", "partial", "not_estimable", "failed"}
    )


def _leave_one_out_baseline_identity_valid(row):
    return row.get("label") == "All included studies" and row.get("study_id") is None


def _leave_one_out_omission_identity_valid(row, expected_study):
    return (
        isinstance(expected_study, dict)
        and row.get("study_id") == _analysis_study_id(expected_study)
        and row.get("label") == "Omitting %s" % expected_study.get("name")
    )


def _leave_one_out_numeric_observations(row):
    numbers = {
        field: _numeric_observation(row.get(field))
        for field in ("estimate", "lower_bound", "upper_bound", "change_from_baseline")
    }
    if any(value is None for value in numbers.values()):
        return None
    return numbers


def _leave_one_out_status_valid(row, numbers):
    status = row.get("status")
    estimate_status = numbers["estimate"].get("status")
    if status in {"available", "partial"}:
        if estimate_status != "available":
            return False
    elif estimate_status not in {"not_estimable", "not_available"}:
        return False
    if status == "available" and not _leave_one_out_interval_available(numbers):
        return False
    return status == "available" or _nonempty_text(row.get("reason"))


def _leave_one_out_interval_available(numbers):
    return all(
        numbers[field].get("status") == "available"
        for field in ("lower_bound", "upper_bound", "change_from_baseline")
    )


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

def _subgroup_result_evidence(results, snapshot, record):
    context = _subgroup_context(results, snapshot, record)
    if context is None:
        return None
    plan, numerics, studies, raw_values, assignments, raw_levels, numerical_levels = context
    study_names = _subgroup_study_names_by_id(studies)
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
    overall_observation = _subgroup_model_observation(overall)
    if overall_observation is None:
        return None
    return {
        "status": "available",
        "kind": "%s-subgroup" % plan["family"],
        "family": plan["family"],
        "metric": plan["metric"],
        "covariate_name": plan["covariate_name"],
        "missing_policy": plan["missing_policy"],
        "confidence_level": 90.0,
        "input_study_count": len(studies),
        "included_count": numerics.get("included_count"),
        "missing_count": numerics.get("missing_count"),
        "excluded_count": numerics.get("excluded_count"),
        "assignments": assignment_evidence,
        "levels": level_evidence,
        "overall": dict(overall_observation, included_count=overall.get("included_count")),
        "between_subgroup_test_status": between.get("status"),
        "figure_status": _stored_figure_status(results),
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }


def _subgroup_context(results, snapshot, record):
    plan = results.get("subgroup_plan")
    numerics = results.get("subgroup_numerics")
    studies = snapshot.get("studies")
    covariates = snapshot.get("covariates")
    specification = record.get("specification")
    parameters = specification.get("params") if isinstance(specification, dict) else None
    data_type = specification.get("data_type") if isinstance(specification, dict) else None
    metric = specification.get("metric") if isinstance(specification, dict) else None
    method = specification.get("method") if isinstance(specification, dict) else None
    if not _subgroup_plan_valid(
        plan, numerics, studies, covariates, parameters, data_type, metric, method
    ):
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


def _subgroup_plan_valid(
    plan, numerics, studies, covariates, parameters, data_type, metric, method
):
    return (
        _subgroup_input_types_valid(plan, numerics, studies, covariates, parameters)
        and data_type in {"binary", "continuous", "diagnostic"}
        and _subgroup_method_supported(data_type, metric, method)
        and plan.get("family") == data_type
        and plan.get("metric") == metric
        and _subgroup_plan_identity_valid(plan)
        and _subgroup_numerics_match_plan(plan, numerics, parameters)
    )


def _subgroup_method_supported(data_type, metric, method):
    return (data_type, metric, method) in {
        (family, subgroup_metric, subgroup_method)
        for family, subgroup_metric, subgroup_method in _SUBGROUP_ROUTES.values()
    }


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
        plan.get("covariate_name") == "Qualification region"
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


def _subgroup_study_names_by_id(studies):
    return {
        _subgroup_study_id(study): study.get("name")
        for study in studies
        if isinstance(study, dict)
        and type(_subgroup_study_id(study)) is int
        and isinstance(study.get("name"), str)
    }


def _subgroup_study_id(study):
    value = study.get("id")
    return value if type(value) is int else study.get("study_id")


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
    study_id = _subgroup_study_id(study)
    if type(study_id) is not int or assignment.get("study_id") != study_id:
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
    observation = _subgroup_model_observation(result)
    if observation is None:
        return None
    return {
        "label": label,
        "study_ids": study_ids,
        "study_order": names,
        "included_count": len(study_ids),
        **observation,
    }


def _subgroup_level_identity_valid(label, names, study_ids, result):
    return (
        isinstance(label, str)
        and result is not None
        and _subgroup_level_ids_valid(study_ids)
        and _subgroup_level_names_valid(names, study_ids)
        and result.get("included_count") == len(study_ids)
    )


def _subgroup_level_ids_valid(study_ids):
    return (
        all(type(study_id) is int for study_id in study_ids)
        and len(study_ids) == len(set(study_ids))
    )


def _subgroup_level_names_valid(names, study_ids):
    return (
        len(names) == len(study_ids)
        and all(isinstance(name, str) and bool(name) for name in names)
    )


def _subgroup_model_observation(result):
    if not isinstance(result, dict):
        return None
    status = result.get("status")
    values = {
        key: result.get(key)
        for key in ("estimate", "lower_bound", "upper_bound")
    }
    if status == "available":
        return _available_subgroup_observation(result, values)
    if status != "not_available":
        return None
    reason = result.get("reason")
    if not _unavailable_subgroup_observation_valid(reason, values):
        return None
    return {"status": status, "reason": reason, **values}


def _available_subgroup_observation(result, values):
    if result.get("reason") is not None:
        return None
    if not all(_finite_result_number(value) for value in values.values()):
        return None
    if not values["lower_bound"] <= values["estimate"] <= values["upper_bound"]:
        return None
    return {"status": "available", "reason": None, **values}


def _unavailable_subgroup_observation_valid(reason, values):
    return (
        isinstance(reason, str)
        and bool(reason)
        and all(value is None for value in values.values())
    )


def _finite_result_number(value):
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
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
    return next(
        (
            section.get("source_key")
            for section in sections
            if _stored_forest_plot_section(section, images)
        ),
        None,
    )


def _stored_forest_plot_section(section, images):
    if not isinstance(section, dict) or section.get("kind") != "image":
        return False
    source_key = section.get("source_key")
    image = images.get(source_key) if isinstance(source_key, str) else None
    return (
        section.get("title") == "Forest Plot"
        and isinstance(image, str)
        and bool(image)
    )


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
    "binary.subgroup": _subgroup_result_evidence,
    "continuous.subgroup": _subgroup_result_evidence,
    "diagnostic.subgroup": _subgroup_result_evidence,
    "continuous.cumulative": _cumulative_result_evidence,
    "diagnostic.cumulative": _cumulative_result_evidence,
    "continuous.leave-one-out": _leave_one_out_result_evidence,
    "diagnostic.leave-one-out": _leave_one_out_result_evidence,
    "binary.small-study-effects": _small_study_result_evidence,
    "binary.plot-edit": _plot_edit_result_evidence,
}
_ROUTE_RESULT_BUILDERS.update(
    {
        route: (
            lambda results, snapshot, record, route=route:
            _method_variant_result_evidence(results, snapshot, record, route)
        )
        for route in _METHOD_VARIANT_STANDARD_ROUTES
    }
)
_ROUTE_RESULT_BUILDERS.update(
    {
        route: {
            "cumulative": _cumulative_result_evidence,
            "leave-one-out": _leave_one_out_result_evidence,
            "subgroup": _subgroup_result_evidence,
        }[workflow]
        for route, (_family, workflow, _metric, _method)
        in _METHOD_VARIANT_ROUTES.items()
        if workflow != "standard"
    }
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

    button = next(
        (
            button
            for widget in _figure_action_widgets(viewer._layout_items, QGraphicsProxyWidget)
            for button in widget.findChildren(QPushButton)
            if button.accessibleName() == label and button.isEnabled()
        ),
        None,
    )
    if button is None:
        raise RuntimeError("saved result viewer has no enabled %s action" % label)
    return button


def _figure_action_widgets(items, proxy_type):
    widgets = []
    for item in items:
        if not isinstance(item, proxy_type):
            continue
        widget = item.widget()
        if widget is not None:
            widgets.append(widget)
    return widgets


def _run_saved_plot_edits(viewer, window, evidence, qt_core):
    artifact = _saved_forest_plot(viewer)
    workspace = window.workspace
    record_id = evidence["analysis_id"]
    figure_key = artifact.figure_key
    regeneration = _regenerate_saved_plot(viewer, workspace, record_id, figure_key)
    appearance = _edit_saved_plot_appearance(
        viewer, workspace, record_id, figure_key, qt_core
    )
    if appearance["revision"] == regeneration["revision_after"]:
        raise RuntimeError("saved figure edit did not advance the record revision")
    opened = _analysis_evidence(window, record_id, route="binary.plot-edit")
    if not _same_analysis_evidence(evidence, opened):
        raise RuntimeError("saved figure editing changed the scientific result")
    evidence["source_result_unchanged"] = True
    return {
        "saved_plot_regeneration": {
            "worker_completed": True,
            "worker_request": regeneration["request"],
            "record_revision_before": regeneration["revision_before"],
            "record_revision_after": regeneration["revision_after"],
            "stored_image_sha256": regeneration["image_sha256"],
        },
        "saved_plot_edit": {
            "worker_completed": True,
            "worker_request": appearance["request"],
            "record_revision_before": regeneration["revision_after"],
            "record_revision_after": appearance["revision"],
            "waited_for_worker_operations": appearance["busy_waits"],
        },
        "saved_edited_artifact": {
            "persistence": "saved_record",
            "record_id": record_id,
            "figure_key": figure_key,
            "record_revision": appearance["revision"],
            "style": {"fp_xlabel": appearance["xlabel"]},
            "image_sha256": appearance["image_sha256"],
        },
    }


def _regenerate_saved_plot(viewer, workspace, record_id, figure_key):
    _, before, _ = _saved_figure_record(workspace, record_id, figure_key)
    button = _figure_action(viewer, "Regenerate figure")
    response = _await_plot_operation(
        viewer.worker_client, button.click, "saved_plot_render"
    )
    request = _plot_worker_request_identity(response, "saved_plot_render")
    _require_plot_target(request, record_id, figure_key, "saved regeneration")
    _, after, image_sha = _saved_figure_record(workspace, record_id, figure_key)
    return {
        "request": request,
        "revision_before": before,
        "revision_after": after,
        "image_sha256": image_sha,
    }


def _edit_saved_plot_appearance(viewer, workspace, record_id, figure_key, qt_core):
    button = _figure_action(viewer, "Edit appearance")
    events, dialog, busy_waits = _edit_saved_forest_plot(
        viewer.worker_client, button, "Qualification effect direction", qt_core
    )
    if dialog._commit_outcome is not True:
        raise RuntimeError("saved figure editor did not commit its worker result")
    request = _plot_worker_request_identity(events, "saved_plot_render")
    _require_plot_target(request, record_id, figure_key, "saved appearance")
    record, revision, image_sha = _saved_figure_record(
        workspace, record_id, figure_key
    )
    style = _saved_figure_presentation(record, figure_key)
    xlabel = style.get("fp_xlabel")
    if xlabel != "Qualification effect direction":
        raise RuntimeError("saved figure appearance was not stored in the record")
    return {
        "request": request,
        "revision": revision,
        "image_sha256": image_sha,
        "xlabel": xlabel,
        "busy_waits": busy_waits,
    }


def _require_plot_target(request, record_id, figure_key, action):
    identity = request["artifact_identity"]
    if identity.get("analysis_id") != record_id or identity.get("figure_key") != figure_key:
        raise RuntimeError("%s response targeted a different figure" % action)


def _saved_figure_presentation(record, figure_key):
    presentation = record.value.get("presentation")
    figures = presentation.get("figures") if isinstance(presentation, dict) else None
    if not isinstance(figures, dict) or not isinstance(figures.get(figure_key), dict):
        raise RuntimeError("saved figure has no scoped presentation for %s" % figure_key)
    return figures[figure_key]


class _SavedPlotEditorRun:
    def __init__(self, client, xlabel, loop):
        self.client = client
        self.xlabel = xlabel
        self.loop = loop
        self.events = []
        self.failure = None
        self.edited = None
        self.busy_waits = []

    def completed(self, run_id, operation, identity, result):
        self.events.append((run_id, operation, identity, result))
        if operation == "saved_plot_render":
            self.loop.quit()

    def failed(self, run_id, operation, identity, error):
        self.failure = {
            "run_id": run_id,
            "operation": operation,
            "identity": identity,
            "error": error,
        }
        self.close_editor()
        self.loop.quit()

    def submit_edit(self):
        if self.edited is not None:
            return
        if self.client.is_busy:
            self._remember_busy_worker()
            return
        dialog = self._visible_plot_editor()
        if dialog is not None:
            self.edited = dialog
            self._apply_edit(dialog)

    def _remember_busy_worker(self):
        state = (
            getattr(self.client, "_operation", None),
            getattr(self.client, "_run_id", None),
        )
        if state not in self.busy_waits:
            self.busy_waits.append(state)

    @staticmethod
    def _visible_plot_editor():
        from PyQt6.QtWidgets import QApplication
        from rc_metastudio import plot_editor_dialog

        dialog_type = plot_editor_dialog.EditPlotDialog
        dialog = QApplication.activeModalWidget()
        if isinstance(dialog, dialog_type):
            return dialog
        return next(
            (
                widget
                for widget in QApplication.topLevelWidgets()
                if isinstance(widget, dialog_type) and widget.isVisible()
            ),
            None,
        )

    def _apply_edit(self, dialog):
        from PyQt6.QtWidgets import QDialogButtonBox

        button = dialog.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if button is None or not button.isEnabled():
            self.failure = "native plot editor has no enabled Apply control"
            dialog.reject()
            self.loop.quit()
            return
        dialog.x_lbl_le.setText(self.xlabel)
        button.click()

    def timed_out(self):
        dialog = self.edited
        self.failure = {
            "message": "plot editor did not finish within 120000 ms",
            "pending_ok": getattr(dialog, "_pending_ok", None),
            "commit_outcome": getattr(dialog, "_commit_outcome", None),
            "inline_error": (
                dialog._commit_error.text()
                if dialog is not None and hasattr(dialog, "_commit_error")
                else None
            ),
            "worker_busy": self.client.is_busy,
            "worker_operation": getattr(self.client, "_operation", None),
            "worker_run_id": getattr(self.client, "_run_id", None),
        }
        self.close_editor()
        self.loop.quit()

    def close_editor(self):
        from PyQt6.QtWidgets import QApplication, QDialog

        dialog = self.edited or QApplication.activeModalWidget()
        if isinstance(dialog, QDialog) and dialog.isVisible():
            dialog.reject()


def _edit_saved_forest_plot(client, edit_button, xlabel, qt_core):
    loop = qt_core.QEventLoop()
    state = _SavedPlotEditorRun(client, xlabel, loop)
    timer = qt_core.QTimer()
    timer.setInterval(20)
    timeout = qt_core.QTimer()
    timeout.setSingleShot(True)

    client.plotCompleted.connect(state.completed)
    client.plotFailed.connect(state.failed)
    timer.timeout.connect(state.submit_edit)
    timeout.timeout.connect(state.timed_out)
    timer.start()
    timeout.start(120000)
    try:
        edit_button.click()
        if not _saved_plot_render_completed(state.events) and state.failure is None:
            loop.exec()
    finally:
        timer.stop()
        timeout.stop()
        client.plotCompleted.disconnect(state.completed)
        client.plotFailed.disconnect(state.failed)
    if state.failure:
        raise RuntimeError("saved plot edit worker failed: %s" % state.failure)
    if not _saved_plot_render_completed(state.events):
        raise TimeoutError("saved plot edit did not complete within 120000 ms")
    if state.edited is None:
        raise RuntimeError("saved plot editor did not present its native edit form")
    return state.events, state.edited, state.busy_waits


def _saved_plot_render_completed(events):
    return any(event[1] == "saved_plot_render" for event in events)


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
    response = _matching_plot_response(response, operation)
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


def _matching_plot_response(response, operation):
    if isinstance(response, list):
        return next(
            (
                item for item in response
                if isinstance(item, tuple) and len(item) == 4
                and item[1] == operation
            ),
            None,
        )
    return response


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

def _run_subgroup_journey(
    app, sample_path, destination, *, window, route, close_window
):
    from PyQt6 import QtCore
    from rc_metastudio import analysis_setup_dialog, main_window, results_window

    sample_path = Path(sample_path).resolve()
    destination = Path(destination).resolve()
    covariate_name = _prepare_subgroup_sample(window, sample_path, route)
    run_evidence = []
    responsiveness = []
    for policy in ("exclude", "missing_category"):
        evidence, responsive = _run_subgroup_policy(
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


def _prepare_subgroup_sample(window, sample_path, route):
    data_type, metric, _method = _SUBGROUP_ROUTES[route]
    if not sample_path.is_file():
        raise RuntimeError("packaged %s sample is missing" % data_type)
    if not window.open(str(sample_path), raise_on_error=True):
        raise RuntimeError("packaged %s project could not be opened" % data_type)
    if window.model.get_current_outcome_type() != data_type:
        raise RuntimeError("packaged subgroup sample does not contain %s data" % data_type)
    _set_analysis_metric(window, metric)
    included = list(window.model.get_studies(only_if_included=True))
    if len(included) < 4:
        raise _UnqualifiedRoute(
            "%s sample has too few included rows for two subgroups and missing values"
            % data_type
        )
    covariate_name = "Qualification region"
    missing_indexes = (1, 8) if len(included) >= 10 else (1, 2)
    values = _qualification_region_values(window.model, included, missing_indexes)
    window.model.add_covariate(covariate_name, "factor", values)
    window.model.set_confidence_level(90.0)
    return covariate_name


def _qualification_region_values(model, included_studies, missing_indexes):
    missing_ids = {included_studies[index].id for index in missing_indexes}
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


def _run_subgroup_policy(
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
    form = _subgroup_form(window, policy, analysis_setup_dialog)
    _configure_subgroup_form(form, _SUBGROUP_ROUTES[route][2])
    responsive = []
    _run_subgroup_form(window, form, responsive, client, qt_core)
    if "rpy2.robjects" in sys.modules:
        raise RuntimeError("subgroup analysis loaded R into the main process")
    saved = window.workspace.list_saved_analyses()
    if len(saved) != before + 1:
        raise RuntimeError("subgroup analysis did not create one saved result")
    return _analysis_evidence(window, str(saved[-1]["id"]), route=route), bool(
        responsive and responsive[0]
    )


def _subgroup_form(window, policy, dialog_type):
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
        raise RuntimeError("subgroup setup did not open for %s" % policy)
    return form


def _configure_subgroup_form(form, method):
    if form.current_param_vals.get("conf.level") != 90.0:
        raise RuntimeError("subgroup setup lost the selected 90% confidence level")
    method_label = next(
        (label for label, available_method in form.available_method_d.items()
         if available_method == method),
        None,
    )
    if method_label is None:
        raise _UnqualifiedRoute("RCMetaR does not offer %s subgroup analysis" % method)
    form.method_cbo_box.setCurrentText(method_label)
    request = form.analysis_requests()[0]
    if request.parameter_values().get("conf.level") != 90.0:
        raise RuntimeError("subgroup request did not preserve 90% confidence")


def _run_subgroup_form(window, form, responsive, client, qt_core):
    from PyQt6.QtWidgets import QDialogButtonBox

    def run():
        button = form.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if button is None or not button.isEnabled():
            raise RuntimeError("subgroup run control is disabled")
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

    destination = _saved_journey_path(destination)
    window.out_path = str(destination)
    _save_project_without_warnings(window, main_window, data_type)
    _close_saved_journey_window(app, window, data_type=data_type)
    reopened = main_window.MainWindow()
    try:
        viewer = _open_saved_result_viewer(
            reopened, destination, evidence, route, data_type, results_window
        )
        if route == "binary.plot-edit":
            from PyQt6 import QtCore
            evidence.update(_run_saved_plot_edits(viewer, reopened, evidence, QtCore))
            _save_project_without_warnings(reopened, main_window, data_type)
            _close_saved_journey_window(app, reopened, data_type=data_type)
            reopened = main_window.MainWindow()
            viewer = _reopen_edited_plot(
                reopened, destination, evidence, route, results_window
            )
        evidence.update(_export_first_figure(viewer, destination, route, results_window))
        if "rpy2.robjects" in sys.modules:
            raise RuntimeError("reopening %s result loaded R into the main process" % route)
        _mark_saved_reopened(evidence, source)
        return evidence
    finally:
        close_window(app, reopened)


def _saved_journey_path(destination):
    path = Path(destination).resolve()
    if path.suffix.lower() != ".rcms":
        path = Path(str(path) + ".rcms")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _open_saved_result_viewer(reopened, destination, evidence, route, data_type, results_window):
    reopened.workspace.mark_saved()
    if not reopened.open(str(destination), raise_on_error=True):
        raise RuntimeError("saved %s project could not be reopened" % data_type)
    record = reopened.workspace.get_saved_analysis(evidence["analysis_id"])
    opened = _analysis_evidence(reopened, evidence["analysis_id"], route=route)
    if record is None or not _same_analysis_evidence(evidence, opened):
        raise RuntimeError("saved %s result changed after reopen" % route)
    viewer = _open_saved_result(reopened, evidence["analysis_id"], route, results_window)
    if route == "diagnostic.reitsma-meta-regression":
        if not _reitsma_meta_regression_report_visible(viewer, evidence):
            raise RuntimeError(
                "reopened Reitsma meta-regression report did not show its saved coefficients and tests"
            )
        evidence["report_view_after_reopen"] = True
    return viewer


def _open_saved_result(reopened, analysis_id, route, results_window):
    reopened._open_saved_analysis(analysis_id)
    viewers = reopened.findChildren(results_window.ResultsWindow)
    if len(viewers) != 1:
        raise RuntimeError("reopened %s result did not reach the native viewer" % route)
    return viewers[0]


def _reopen_edited_plot(reopened, destination, evidence, route, results_window):
    reopened.workspace.mark_saved()
    if not reopened.open(str(destination), raise_on_error=True):
        raise RuntimeError("edited saved project could not be reopened")
    record, revision, image_sha = _saved_edited_plot_record(reopened, evidence)
    _validate_reopened_edited_plot(reopened, evidence, route, record, revision, image_sha)
    viewer = _open_saved_result(reopened, evidence["analysis_id"], route, results_window)
    evidence["saved_edited_artifact_after_reopen"] = _saved_edited_plot_artifact(
        record, revision, image_sha, evidence["saved_edited_artifact"]
    )
    evidence["saved_edited_reopened"] = True
    return viewer


def _saved_edited_plot_record(reopened, evidence):
    edited = evidence["saved_edited_artifact"]
    return _saved_figure_record(
        reopened.workspace, evidence["analysis_id"], edited["figure_key"]
    )


def _validate_reopened_edited_plot(reopened, evidence, route, record, revision, image_sha):
    opened = _analysis_evidence(reopened, evidence["analysis_id"], route=route)
    if not _same_analysis_evidence(evidence, opened):
        raise RuntimeError("saved scientific result changed after figure edit")
    edited = evidence["saved_edited_artifact"]
    style = _saved_figure_presentation(record, edited["figure_key"])
    if (
        str(record.value.get("id")) != edited["record_id"]
        or revision != edited["record_revision"]
        or image_sha != edited["image_sha256"]
        or style.get("fp_xlabel") != edited["style"]["fp_xlabel"]
    ):
        raise RuntimeError("edited figure identity or appearance did not survive reopen")


def _saved_edited_plot_artifact(record, revision, image_sha, edited):
    style = _saved_figure_presentation(record, edited["figure_key"])
    return {
        "record_id": str(record.value["id"]),
        "figure_key": edited["figure_key"],
        "record_revision": revision,
        "style": {"fp_xlabel": style["fp_xlabel"]},
        "image_sha256": image_sha,
    }


def _mark_saved_reopened(evidence, source):
    evidence["saved_reopened"] = True
    evidence["sample_project_sha256"] = hashlib.sha256(Path(source).read_bytes()).hexdigest()


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
    export_path = Path(destination).with_suffix(
        ".%s-%s.png" % (str(route).replace(".", "-"), uuid.uuid4().hex)
    )
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
    source_hash = _sha256_path(figure_path)
    exported_hash = _sha256_path(export_path)
    return {
        "figure_status": "exported",
        "figure_key": figure_key,
        "figure_export_bytes": export_path.stat().st_size,
        "figure_export_sha256": exported_hash,
        "source_figure_sha256": source_hash,
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
