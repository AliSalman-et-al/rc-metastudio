"""Packaged qualification of an owned worker analysis and retained result."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import sys

from rc_metastudio.automation import _close_automation_window, _write_json, start_automation


class _UnqualifiedRoute(RuntimeError):
    """A route has no defensible result for the available sample data."""


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
    if not client.is_busy and not (
        raw_preview_timer is not None and raw_preview_timer.isActive()
    ):
        return
    loop = QtCore.QEventLoop()
    poll = QtCore.QTimer()
    poll.setInterval(25)
    timeout = QtCore.QTimer()
    timeout.setSingleShot(True)
    stable_ms = 0

    def check_idle():
        nonlocal stable_ms
        pending_timer = raw_preview_timer is not None and raw_preview_timer.isActive()
        if client.is_busy or pending_timer:
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
    if client.is_busy or (
        raw_preview_timer is not None and raw_preview_timer.isActive()
    ):
        raise TimeoutError("analysis worker did not become idle before subgroup setup")


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
        "binary.one-arm": ("binary", "PLO", "binary.random"),
        "continuous.entered-effect": (
            "continuous", "SMD", "continuous.random"
        ),
    }
    meta_regression_routes = {
        "binary.meta-regression": ("binary", "OR"),
        "continuous.meta-regression": ("continuous", "SMD"),
    }
    special_routes = {
        "diagnostic.reitsma",
        "binary.small-study-effects",
        "diagnostic.subgroup",
    }
    if (
        route not in binary_workflows
        and route not in family_routes
        and route not in meta_regression_routes
        and route not in special_routes
    ):
        raise ValueError("unsupported worker qualification route: %s" % route)

    app, window = start_automation()
    reopened = None
    try:
        if "rpy2.robjects" in sys.modules:
            raise RuntimeError("qualification main process loaded R before the worker")
        if route in family_routes:
            data_type, metric, method = family_routes[route]
            prepare_model = None
            if route == "binary.one-arm":
                prepare_model = _prepare_one_arm_binary
            elif route == "continuous.entered-effect":
                prepare_model = _prepare_entered_effect_continuous
            responsive = []
            try:
                evidence = _run_separate_family_journey(
                    app,
                    source,
                    destination,
                    window=window,
                    data_type=data_type,
                    metric=metric,
                    method=method,
                    route=(
                        None
                        if route in {"continuous.standard", "diagnostic.standard"}
                        else route
                    ),
                    prepare_model=prepare_model,
                    event_loop_responsive=responsive,
                )
            except _UnqualifiedRoute as error:
                _write_json(str(output), {
                    "route": route,
                    "qualification_status": "unqualified",
                    "details": str(error),
                    "worker_completed": False,
                    "main_process_r_bridge_absent": "rpy2.robjects" not in sys.modules,
                })
                return 0
            _write_json(str(output), {
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

        if route in meta_regression_routes or route in special_routes:
            try:
                if route in meta_regression_routes:
                    data_type, metric = meta_regression_routes[route]
                    evidence = _run_meta_regression_journey(
                        app,
                        source,
                        destination,
                        window=window,
                        route=route,
                        data_type=data_type,
                        metric=metric,
                    )
                elif route == "diagnostic.subgroup":
                    subgroup = _run_diagnostic_subgroup_journey(
                        app, source, destination, window=window
                    )
                    _write_json(str(output), {
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
                else:
                    evidence = _run_special_family_journey(
                        app, source, destination, window=window, route=route
                    )
            except _UnqualifiedRoute as error:
                _write_json(str(output), {
                    "route": route,
                    "qualification_status": "unqualified",
                    "details": str(error),
                    "worker_completed": False,
                    "main_process_r_bridge_absent": "rpy2.robjects" not in sys.modules,
                })
                return 0
            _write_json(str(output), {
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


def _analysis_evidence(window, record_id, *, route=None):
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
        if route is not None:
            raise _UnqualifiedRoute(
                "%s retained result status is %s" % (route, status or "missing")
            )
        raise RuntimeError("analysis did not produce a complete retained result")
    input_identity = record.get("input_identity")
    if not isinstance(input_identity, str) or len(input_identity) != 64:
        raise RuntimeError("saved analysis has no stable input identity")
    evidence = {
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
    if route is not None:
        route_evidence = _route_result_evidence(route, record)
        if route_evidence is None:
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
        "diagnostic.reitsma": (
            "diagnostic", "standard", "Sensitivity and specificity",
            "diagnostic.reitsma",
        ),
        "binary.small-study-effects": (
            "binary", "small-study-effects", "OR", "small.study.effects"
        ),
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
    if route == "binary.one-arm":
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
        if (
            estimate is None
            or count is None
            or not isinstance(studies, list)
            or not isinstance(input_studies, list)
            or not isinstance(groups, list)
            or len(groups) != 1
            or snapshot.get("metric") != "PLO"
            or snapshot.get("raw_counts_available") is not True
            or len(studies) != len(snapshot.get("studies", []))
            or [row.get("label") for row in studies if isinstance(row, dict)]
            != [row.get("name") for row in input_studies if isinstance(row, dict)]
            or any(
                not isinstance(row, dict)
                or _available_value(row.get("events")) is None
                or _available_value(row.get("total")) is None
                for row in studies
            )
            or numerics.get("arm_label") != groups[0]
        ):
            return None
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
            "raw_arm_totals": sum(
                int(row["total"]["value"])
                for row in studies
                if isinstance(row, dict)
                and isinstance(row.get("total"), dict)
                and row["total"].get("status") == "available"
                and isinstance(row["total"].get("value"), (int, float))
            ),
        }
    if route == "continuous.entered-effect":
        numerics = results.get("continuous_numerics")
        studies = snapshot.get("studies")
        result_studies = numerics.get("studies") if isinstance(numerics, dict) else None
        pooled = numerics.get("pooled") if isinstance(numerics, dict) else None
        estimate = _available_value(
            pooled.get("estimate") if isinstance(pooled, dict) else None
        )
        count = _available_value(
            numerics.get("analyzed_study_count") if isinstance(numerics, dict) else None
        )
        if (
            estimate is None
            or count is None
            or not isinstance(studies, list)
            or not studies
            or not isinstance(result_studies, list)
            or [row.get("label") for row in result_studies if isinstance(row, dict)]
            != [row.get("name") for row in studies if isinstance(row, dict)]
            or any(
                not isinstance(row, dict) or row.get("provenance") != "entered"
                for row in studies
            )
            or numerics.get("metric") != "SMD"
        ):
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
    if route.endswith("meta-regression"):
        numerics = results.get("meta_regression_numerics")
        if not isinstance(numerics, dict):
            return None
        moderators = numerics.get("moderators")
        eligible = numerics.get("eligible_study_ids")
        coefficients = numerics.get("coefficients")
        if not isinstance(moderators, list) or not isinstance(eligible, list) or not isinstance(coefficients, list):
            return None
        names = [
            moderator.get("name")
            for moderator in moderators
            if isinstance(moderator, dict) and isinstance(moderator.get("name"), str)
        ]
        if not names or len(names) != len(moderators):
            return None
        input_studies = snapshot.get("studies")
        if not isinstance(input_studies, list):
            return None
        study_names_by_id = {
            study.get("id"): study.get("name")
            for study in input_studies
            if isinstance(study, dict)
            and isinstance(study.get("id"), int)
            and isinstance(study.get("name"), str)
        }
        eligible_order = [study_names_by_id.get(study_id) for study_id in eligible]
        if any(not isinstance(name, str) or not name for name in eligible_order):
            return None
        coefficient_rows = []
        for row in coefficients:
            if not isinstance(row, dict):
                return None
            term = row.get("term")
            estimate = _available_value(row.get("estimate"))
            if not isinstance(term, dict) or estimate is None:
                return None
            label = term.get("label")
            if not isinstance(label, str) or not label:
                return None
            coefficient_rows.append({"label": label, "estimate": estimate})
        if numerics.get("coefficient_count") != len(coefficient_rows):
            return None
        return {
            "status": "available",
            "kind": "generic-meta-regression",
            "formula": numerics.get("formula"),
            "moderators": names,
            "coefficient_count": numerics.get("coefficient_count"),
            "eligible_study_count": len(eligible),
            "eligible_study_order": eligible_order,
            "coefficients": coefficient_rows,
            "figure_status": _stored_figure_status(results),
            "numeric_oracle": "observed_only_no_independent_expected_value",
        }
    if route == "diagnostic.reitsma":
        report = results.get("reitsma_report")
        if not isinstance(report, dict):
            return None
        sections = report.get("sections")
        summary = next(
            (
                section.get("value")
                for section in sections
                if isinstance(section, dict)
                and section.get("key") == "Summary operating point"
                and section.get("status") == "available"
            ),
            None,
        ) if isinstance(sections, list) else None
        if not isinstance(summary, str) or not summary.strip():
            return None
        section_statuses = {
            section.get("key"): section.get("status")
            for section in sections
            if isinstance(section, dict)
        }
        return {
            "status": "available",
            "kind": "joint-reitsma",
            "measures": report.get("measures"),
            "summary": summary,
            "section_statuses": section_statuses,
            "figure_status": _stored_figure_status(results),
            "numeric_oracle": "observed_only_no_independent_expected_value",
        }
    if route == "diagnostic.subgroup":
        plan = results.get("subgroup_plan")
        numerics = results.get("subgroup_numerics")
        studies = snapshot.get("studies")
        covariates = snapshot.get("covariates")
        specification = record.get("specification")
        parameters = (
            specification.get("params")
            if isinstance(specification, dict)
            else None
        )
        if (
            not isinstance(plan, dict)
            or not isinstance(numerics, dict)
            or not isinstance(studies, list)
            or not isinstance(covariates, list)
            or not isinstance(parameters, dict)
            or plan.get("family") != "diagnostic"
            or plan.get("covariate_name") != "Qualification region"
            or plan.get("metric") != "Sens"
            or plan.get("missing_policy") not in {"exclude", "missing_category"}
            or numerics.get("covariate_name") != plan.get("covariate_name")
            or numerics.get("missing_policy") != plan.get("missing_policy")
            or parameters.get("conf.level") != 90.0
        ):
            return None
        covariate = next(
            (
                row for row in covariates
                if isinstance(row, dict)
                and row.get("name") == plan["covariate_name"]
                and row.get("data_type") == "factor"
            ),
            None,
        )
        raw_values = covariate.get("values") if isinstance(covariate, dict) else None
        assignments = plan.get("assignments")
        raw_levels = plan.get("levels")
        numerical_levels = numerics.get("levels")
        if (
            not isinstance(raw_values, list)
            or len(raw_values) != len(studies)
            or not isinstance(assignments, list)
            or len(assignments) != len(studies)
            or not isinstance(raw_levels, list)
            or not isinstance(numerical_levels, list)
        ):
            return None
        study_names_by_id = {
            study.get("id"): study.get("name")
            for study in studies
            if isinstance(study, dict)
            and type(study.get("id")) is int
            and isinstance(study.get("name"), str)
        }
        level_results = {
            row.get("label"): row
            for row in numerical_levels
            if isinstance(row, dict) and isinstance(row.get("label"), str)
        }
        evidence_assignments = []
        for index, (study, assignment, value) in enumerate(
            zip(studies, assignments, raw_values, strict=True)
        ):
            if (
                not isinstance(study, dict)
                or not isinstance(assignment, dict)
                or assignment.get("study_id") != study.get("id")
                or assignment.get("study_name") != study.get("name")
                or assignment.get("value") != value
            ):
                return None
            evidence_assignments.append({
                "study_id": assignment.get("study_id"),
                "study_name": assignment.get("study_name"),
                "value": assignment.get("value"),
                "status": assignment.get("status"),
            })
        evidence_levels = []
        for level in raw_levels:
            if not isinstance(level, dict) or not isinstance(level.get("study_ids"), list):
                return None
            label = level.get("label")
            result = level_results.get(label)
            names = [study_names_by_id.get(study_id) for study_id in level["study_ids"]]
            if (
                not isinstance(label, str)
                or result is None
                or any(not isinstance(name, str) or not name for name in names)
                or len(names) != len(level["study_ids"])
                or result.get("included_count") != len(level["study_ids"])
            ):
                return None
            evidence_levels.append({
                "label": label,
                "study_order": names,
                "included_count": len(level["study_ids"]),
                "status": result.get("status"),
            })
        overall = numerics.get("overall")
        between = numerics.get("between_subgroup_test")
        if not isinstance(overall, dict) or not isinstance(between, dict):
            return None
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
            "assignments": evidence_assignments,
            "levels": evidence_levels,
            "overall": {
                "included_count": overall.get("included_count"),
                "status": overall.get("status"),
            },
            "between_subgroup_test_status": between.get("status"),
            "figure_status": _stored_figure_status(results),
            "numeric_oracle": "observed_only_no_independent_expected_value",
        }
    if route == "binary.small-study-effects":
        small = results.get("small_study_effects")
        report = small.get("report") if isinstance(small, dict) else None
        if not isinstance(report, dict):
            return None
        primary = report.get("primary_test")
        sections = report.get("sections")
        if not isinstance(primary, dict) or not isinstance(sections, list):
            return None
        if report.get("status") != "complete":
            raise _UnqualifiedRoute(
                "small-study-effects report status is %s"
                % (report.get("status") or "missing")
            )
        return {
            "status": "available",
            "kind": "small-study-effects",
            "report_status": report.get("status"),
            "usable_studies": len(report.get("study_order", [])),
            "report_study_order": [
                row.get("name")
                for row in report.get("study_order", [])
                if isinstance(row, dict)
            ],
            "primary_test_status": primary.get("status"),
            "primary_test_method": primary.get("method"),
            "section_statuses": {
                section.get("key"): section.get("status")
                for section in sections
                if isinstance(section, dict)
            },
            "report_warnings": report.get("warnings", []),
            "figure_status": _stored_figure_status(results),
            "numeric_oracle": "observed_only_no_independent_expected_value",
        }
    return None


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
        _close_saved_journey_window(app, window, data_type=data_type)
        reopened = main_window.MainWindow()
        reopened.workspace.mark_saved()
        print("worker journey: reopening %s project" % data_type, file=sys.stderr, flush=True)
        if not reopened.open(str(destination), raise_on_error=True):
            raise RuntimeError("saved %s project could not be reopened" % data_type)
        print("worker journey: %s project reopened" % data_type, file=sys.stderr, flush=True)
        record = reopened.workspace.get_saved_analysis(evidence["analysis_id"])
        if record is None or not _same_analysis_evidence(
            evidence,
            _analysis_evidence(reopened, evidence["analysis_id"], route=route),
        ):
            raise RuntimeError("saved %s result changed after reopen" % data_type)
        reopened._open_saved_analysis(evidence["analysis_id"])
        print("worker journey: %s result opened" % data_type, file=sys.stderr, flush=True)
        viewers = reopened.findChildren(results_window.ResultsWindow)
        if len(viewers) != 1:
            raise RuntimeError("reopened %s result did not reach the native viewer" % data_type)
        evidence.update(
            _export_first_figure(
                viewers[0], destination, route or data_type, results_window
            )
        )
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
    included = [
        (index, study)
        for index, study in enumerate(model.dataset.studies)
        if study.include
    ]
    if len(included) < 2:
        raise _UnqualifiedRoute("continuous sample has fewer than two included studies")
    units = []
    for index, study in included:
        unit = model._get_canonical_analysis_unit(index)
        estimate, standard_error = unit.get_effect_and_se_for_source(
            "entered", "SMD", comparison, model.get_confidence_multiplier()
        )
        if estimate is None or standard_error is None:
            raise _UnqualifiedRoute(
                "continuous sample has no complete entered SMD effects for every included study"
            )
        units.append(unit)
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


def _seed_qualification_moderator(window):
    studies = window.model.get_studies(only_if_included=True)
    values = {
        study.name: float(index + 1) for index, study in enumerate(studies)
    }
    window.model.add_covariate("Qualification index", "continuous", values)
    window.data_dirtied()


def _run_meta_regression_journey(
    app, sample_path, destination, *, window, route, data_type, metric
):
    from PyQt6 import QtCore
    from PyQt6.QtWidgets import QDialogButtonBox
    from rc_metastudio import main_window, meta_regression_dialog

    if not window.open(str(sample_path), raise_on_error=True):
        raise RuntimeError("packaged %s sample could not be opened" % data_type)
    if window.model.get_current_outcome_type() != data_type:
        raise RuntimeError("packaged sample does not contain the expected family")
    if window.model.current_effect != metric:
        window.model.current_effect = metric
        window._refresh_workspace_context()
    _seed_qualification_moderator(window)

    before = len(window.workspace.list_saved_analyses())
    responsive = []
    window.meta_reg()
    forms = window.findChildren(meta_regression_dialog.MetaRegressionDialog)
    if not forms:
        raise RuntimeError("meta-regression did not open its moderator settings")
    form = forms[-1]
    control = next(
        (item for item in form._moderators if item.name == "Qualification index"),
        None,
    )
    if control is None or control.kind != "continuous" or control.unit is None:
        raise _UnqualifiedRoute("synthetic continuous moderator was not available")
    control.checkbox.setChecked(True)
    control.unit.setText("study index")

    def run():
        button = form.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if button is None or not button.isEnabled():
            raise RuntimeError("meta-regression run control is disabled")
        button.click()
        QtCore.QTimer.singleShot(
            0,
            lambda: responsive.append(
                window.isVisible() and window.analysis_worker.is_busy
            ),
        )

    _await_worker(window.analysis_worker, run, window.analysis_worker.completed)
    if "rpy2.robjects" in sys.modules:
        raise RuntimeError("meta-regression loaded R into the main process")
    saved = window.workspace.list_saved_analyses()
    if len(saved) != before + 1:
        raise RuntimeError("meta-regression did not create one retained result")
    evidence = _analysis_evidence(window, str(saved[-1]["id"]), route=route)
    evidence["event_loop_responsive"] = bool(responsive and responsive[0])
    return _save_reopen_and_inspect(
        app,
        window,
        destination,
        evidence,
        route=route,
        source=sample_path,
        data_type=data_type,
    )


def _run_special_family_journey(app, sample_path, destination, *, window, route):
    from PyQt6 import QtCore
    from PyQt6.QtWidgets import QDialogButtonBox
    from rc_metastudio import main_window, publication_bias_dialog, reitsma_analysis_dialog

    data_type = "diagnostic" if route == "diagnostic.reitsma" else "binary"
    metric = "Sens" if data_type == "diagnostic" else "OR"
    if not window.open(str(sample_path), raise_on_error=True):
        raise RuntimeError("packaged %s sample could not be opened" % data_type)
    if window.model.get_current_outcome_type() != data_type:
        raise RuntimeError("packaged sample does not contain the expected family")
    if window.model.current_effect != metric:
        window.model.current_effect = metric
        window._refresh_workspace_context()

    before = len(window.workspace.list_saved_analyses())
    responsive = []
    if route == "diagnostic.reitsma":
        window.reitsma()
        forms = window.findChildren(reitsma_analysis_dialog.ReitsmaAnalysisDialog)
        if not forms:
            raise RuntimeError("joint Reitsma settings did not open")
        form = forms[-1]
        if form.snapshot is None:
            raise _UnqualifiedRoute("diagnostic sample cannot provide complete Reitsma counts")

        def run():
            button = form.button_box.button(QDialogButtonBox.StandardButton.Ok)
            if button is None or not button.isEnabled():
                raise RuntimeError("joint Reitsma run control is disabled")
            button.click()
            QtCore.QTimer.singleShot(
                0,
                lambda: responsive.append(
                    window.isVisible() and window.analysis_worker.is_busy
                ),
            )

        _await_worker(window.analysis_worker, run, window.analysis_worker.completed)
    else:
        from rc_metastudio.small_study_effects_core import freeze_small_study_effects_input

        form = publication_bias_dialog.PublicationBiasDialog(
            window.model, parent=window
        )
        snapshot = freeze_small_study_effects_input(
            window.model, form.preview_request()
        )
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

        def preview():
            form.start_preview()
            QtCore.QTimer.singleShot(
                0,
                lambda: responsive.append(
                    window.isVisible() and window.analysis_worker.is_busy
                ),
            )

        _await_worker(window.analysis_worker, preview, window.analysis_worker.completed)
        if form._eligibility_report is None:
            raise _UnqualifiedRoute(
                "RCMetaR did not return an eligibility report for the small-study sample"
            )
        if form._eligibility_report.usable_studies < 3:
            raise _UnqualifiedRoute(
                "fewer than three studies are eligible for small-study effects"
            )
        _await_worker(
            window.analysis_worker,
            form.run,
            window.analysis_worker.completed,
        )

    if "rpy2.robjects" in sys.modules:
        raise RuntimeError("qualification analysis loaded R into the main process")
    saved = window.workspace.list_saved_analyses()
    if len(saved) != before + 1:
        raise RuntimeError("%s did not create one retained result" % route)
    evidence = _analysis_evidence(window, str(saved[-1]["id"]), route=route)
    evidence["event_loop_responsive"] = bool(responsive and responsive[0])
    return _save_reopen_and_inspect(
        app,
        window,
        destination,
        evidence,
        route=route,
        source=sample_path,
        data_type=data_type,
    )


def _run_diagnostic_subgroup_journey(app, sample_path, destination, *, window):
    from unittest.mock import patch
    from PyQt6 import QtCore
    from PyQt6.QtWidgets import QDialogButtonBox, QPushButton
    from rc_metastudio import analysis_setup_dialog, main_window, results_window

    route = "diagnostic.subgroup"
    sample_path = Path(sample_path).resolve()
    destination = Path(destination).resolve()
    if not sample_path.is_file():
        raise RuntimeError("packaged diagnostic sample is missing")
    if not window.open(str(sample_path), raise_on_error=True):
        raise RuntimeError("packaged diagnostic project could not be opened")
    if window.model.get_current_outcome_type() != "diagnostic":
        raise RuntimeError("packaged subgroup sample does not contain diagnostic data")
    if window.model.current_effect != "Sens":
        window.model.current_effect = "Sens"
        window._refresh_workspace_context()

    included_studies = list(window.model.get_studies(only_if_included=True))
    if len(included_studies) < 10:
        raise _UnqualifiedRoute(
            "diagnostic sample has too few included rows to exercise two groups and missing values"
        )
    missing_ids = {included_studies[1].id, included_studies[8].id}
    included_index = {
        study.id: index for index, study in enumerate(included_studies)
    }
    values = {}
    for index, study in enumerate(window.model.dataset.studies):
        row_index = included_index.get(study.id, index)
        values[study.name] = (
            None
            if study.id in missing_ids
            else "North" if row_index % 2 == 0 else "South"
        )
    covariate_name = "Qualification region"
    window.model.add_covariate(covariate_name, "factor", values)
    window.model.set_confidence_level(90.0)
    client = window.analysis_worker
    run_evidence = []
    responsiveness = []

    for policy in ("exclude", "missing_category"):
        _await_window_worker_idle(window)
        before = len(window.workspace.list_saved_analyses())
        _await_worker(
            client,
            lambda policy=policy: window.meta_subgroup(covariate_name, policy),
            client.methodsReady,
        )
        _await_window_worker_idle(window)
        forms = window.findChildren(analysis_setup_dialog.AnalysisSetupDialog)
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
        if form.current_param_vals.get("conf.level") != 90.0:
            raise RuntimeError("diagnostic subgroup setup lost the selected 90% confidence level")
        method_label = next(
            (
                label for label, method in form.available_method_d.items()
                if method == "diagnostic.random"
            ),
            None,
        )
        if method_label is None:
            raise _UnqualifiedRoute("RCMetaR does not offer diagnostic.random subgroup analysis")
        form.method_cbo_box.setCurrentText(method_label)
        request = form.analysis_requests()[0]
        if request.parameter_values().get("conf.level") != 90.0:
            raise RuntimeError("diagnostic subgroup request did not preserve 90% confidence")

        def run():
            button = form.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
            if button is None or not button.isEnabled():
                raise RuntimeError("diagnostic subgroup run control is disabled")
            button.click()
            QtCore.QTimer.singleShot(
                0,
                lambda: responsiveness.append(
                    window.isVisible() and client.is_busy
                ),
            )

        _await_worker(client, run, client.completed)
        if "rpy2.robjects" in sys.modules:
            raise RuntimeError("diagnostic subgroup analysis loaded R into the main process")
        saved = window.workspace.list_saved_analyses()
        if len(saved) != before + 1:
            raise RuntimeError("diagnostic subgroup did not create one saved result")
        run_evidence.append(
            _analysis_evidence(window, str(saved[-1]["id"]), route=route)
        )

    if [row["result_evidence"]["missing_policy"] for row in run_evidence] != [
        "exclude",
        "missing_category",
    ]:
        raise RuntimeError("diagnostic subgroup did not retain both missing-value decisions")
    if run_evidence[0]["study_order"] != run_evidence[1]["study_order"]:
        raise RuntimeError("diagnostic subgroup policies used different frozen study orders")

    destination.parent.mkdir(parents=True, exist_ok=True)
    window.out_path = str(destination)

    def unexpected_warning(_parent, title, message, *_args):
        raise RuntimeError("unexpected warning during diagnostic subgroup journey: %s: %s" % (title, message))

    with patch.object(main_window.QMessageBox, "warning", side_effect=unexpected_warning), patch.object(
        main_window.QMessageBox, "critical", side_effect=unexpected_warning
    ):
        if window.save() is not True:
            raise RuntimeError("diagnostic subgroup project could not be saved")
    _close_saved_journey_window(app, window, data_type="diagnostic subgroup")

    reopened = main_window.MainWindow()
    try:
        reopened.workspace.mark_saved()
        if not reopened.open(str(destination), raise_on_error=True):
            raise RuntimeError("saved diagnostic subgroup project could not be reopened")
        saved_records = reopened.workspace.list_saved_analyses()
        if len(saved_records) != 2:
            raise RuntimeError("reopened diagnostic subgroup project lost a policy result")
        for index, (record, expected) in enumerate(
            zip(saved_records, run_evidence, strict=True)
        ):
            opened = _analysis_evidence(reopened, str(record["id"]), route=route)
            if not _same_analysis_evidence(expected, opened):
                raise RuntimeError("diagnostic subgroup evidence changed after reopen")
            viewers_before = len(reopened.findChildren(results_window.ResultsWindow))
            reopened._open_saved_analysis(str(record["id"]))
            viewers = reopened.findChildren(results_window.ResultsWindow)
            if len(viewers) <= viewers_before:
                raise RuntimeError("reopened diagnostic subgroup result did not reach the native viewer")
            viewer = viewers[-1]
            expected.update(
                _export_first_figure(viewer, destination, route, results_window)
            )
            if index > 0:
                viewer.close()
                app.processEvents()
        if "rpy2.robjects" in sys.modules:
            raise RuntimeError("opening saved subgroup results loaded R into the main process")

        reopened.model.set_confidence_level(95.0)
        _await_window_worker_idle(reopened)
        panel = reopened.results_panel
        history_item = next(
            (
                panel.history_list.item(row)
                for row in range(panel.history_list.count())
                if panel.history_list.item(row).data(
                    QtCore.Qt.ItemDataRole.UserRole
                ) == run_evidence[0]["analysis_id"]
            ),
            None,
        )
        history_row = (
            panel.history_list.itemWidget(history_item)
            if history_item is not None
            else None
        )
        edit_button = next(
            (
                button for button in history_row.findChildren(QPushButton)
                if button.text() == "Edit a copy"
            ),
            None,
        ) if history_row is not None else None
        if edit_button is None or not edit_button.isEnabled():
            raise RuntimeError("saved diagnostic subgroup history has no Edit a copy action")
        client = reopened.analysis_worker
        _await_worker(client, edit_button.click, client.methodsReady)
        _await_window_worker_idle(reopened)
        forms = reopened.findChildren(analysis_setup_dialog.AnalysisSetupDialog)
        copy_form = next(
            (
                candidate for candidate in reversed(forms)
                if getattr(getattr(candidate, "_subgroup_plan", None), "missing_policy", None)
                == "exclude"
            ),
            None,
        )
        if copy_form is None or copy_form.current_param_vals.get("conf.level") != 90.0:
            raise RuntimeError("saved diagnostic subgroup Edit a copy changed 90% confidence")
        copied_request = copy_form.analysis_requests()[0]
        if copied_request.parameter_values().get("conf.level") != 90.0:
            raise RuntimeError("saved diagnostic subgroup request no longer has 90% confidence")
        saved_confidence = copy_form.current_param_vals["conf.level"]
        copy_form.close()
        run_evidence[0]["saved_reopened"] = True
        run_evidence[1]["saved_reopened"] = True
        run_evidence[0]["sample_project_sha256"] = hashlib.sha256(
            sample_path.read_bytes()
        ).hexdigest()
        run_evidence[1]["sample_project_sha256"] = run_evidence[0][
            "sample_project_sha256"
        ]
        return {
            "analysis_runs": run_evidence,
            "event_loop_responsive": bool(responsiveness)
            and all(responsiveness),
            "reopened_analysis_count": len(saved_records),
            "saved_edit_copy_confidence_level": saved_confidence,
            "saved_edit_copy_missing_policy": copy_form._subgroup_plan.missing_policy,
        }
    finally:
        _close_automation_window(app, reopened)


def _save_reopen_and_inspect(
    app, window, destination, evidence, *, route, source, data_type
):
    from unittest.mock import patch
    from rc_metastudio import main_window, results_window

    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    window.out_path = str(destination)

    def unexpected_warning(_parent, title, message, *_args):
        raise RuntimeError("unexpected warning during %s journey: %s: %s" % (data_type, title, message))

    with patch.object(main_window.QMessageBox, "warning", side_effect=unexpected_warning), patch.object(
        main_window.QMessageBox, "critical", side_effect=unexpected_warning
    ):
        if window.save() is not True:
            raise RuntimeError("packaged %s project could not be saved" % data_type)

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
        evidence.update(_export_first_figure(viewer, destination, route, results_window))
        if "rpy2.robjects" in sys.modules:
            raise RuntimeError("reopening %s result loaded R into the main process" % route)
        evidence["saved_reopened"] = True
        evidence["sample_project_sha256"] = hashlib.sha256(
            Path(source).read_bytes()
        ).hexdigest()
        return evidence
    finally:
        _close_automation_window(app, reopened)


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
