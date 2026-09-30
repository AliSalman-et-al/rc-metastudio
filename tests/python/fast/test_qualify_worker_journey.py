# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import cast

import pytest

import rc_metastudio
from scripts import qualify_worker_journey
from rc_metastudio import worker_journey_qualification


_RUNS = {
    "binary.standard": ("binary", "standard", "OR", "binary.random"),
    "binary.cumulative": ("binary", "cumulative", "OR", "binary.random"),
    "binary.leave-one-out": (
        "binary",
        "leave-one-out",
        "OR",
        "binary.random",
    ),
    "continuous.standard": ("continuous", "standard", "SMD", "continuous.random"),
    "diagnostic.standard": ("diagnostic", "standard", "Sens", "diagnostic.random"),
}

_FOLLOW_ON_RUNS = {
    route: identity
    for route, (_sample, identity) in qualify_worker_journey._ROUTES.items()
    if route not in qualify_worker_journey._CORE_ROUTES
}

_RESULT_EVIDENCE: dict[str, dict[str, object]] = {
    "binary.one-arm": {
        "status": "available", "kind": "one-arm-proportion", "metric": "PLO",
        "arm_label": "Intervention", "pooled_proportion": 0.42,
        "study_count": 19, "input_study_count": 19, "raw_arm_totals": 824,
        "figure_status": "available",
        "numeric_oracle": "observed_only_no_independent_expected_value",
    },
    "continuous.entered-effect": {
        "status": "available", "kind": "entered-effect-continuous",
        "input_source": "entered", "metric": "SMD", "pooled_estimate": 0.31,
        "study_count": 6, "input_study_count": 6, "figure_status": "available",
        "numeric_oracle": "observed_only_no_independent_expected_value",
    },
    "binary.meta-regression": {
        "status": "available", "kind": "generic-meta-regression",
        "formula": "yi ~ 1 + Qualification.index", "moderators": ["Qualification index"],
        "coefficient_count": 2, "eligible_study_count": 19,
        "coefficients": [
            {"label": "Intercept", "estimate": -0.2},
            {"label": "Qualification index", "estimate": 0.03},
        ], "figure_status": "available",
        "numeric_oracle": "observed_only_no_independent_expected_value",
    },
    "continuous.meta-regression": {
        "status": "available", "kind": "generic-meta-regression",
        "formula": "yi ~ 1 + Qualification.index", "moderators": ["Qualification index"],
        "coefficient_count": 2, "eligible_study_count": 6,
        "coefficients": [
            {"label": "Intercept", "estimate": 0.1},
            {"label": "Qualification index", "estimate": 0.08},
        ], "figure_status": "available",
        "numeric_oracle": "observed_only_no_independent_expected_value",
    },
    "diagnostic.reitsma-meta-regression": {
        "status": "available",
        "kind": "joint-reitsma-meta-regression",
        "report_status": "available",
        "formula": "cbind(tsens, tfpr) ~ `Qualification index`",
        "package_version": "0.5.12",
        "converged": True,
        "effective_settings": {
            "missing_moderator_policy": "exclude",
            "joint_metrics": "Sens,Spec",
            "estimator": "REML",
            "correction_policy": "All studies if any zero exists",
            "correction_factor": 0.5,
            "confidence_level": 90.0,
        },
        "moderator": {
            "name": "Qualification index",
            "kind": "continuous",
            "unit": "study index",
            "unit_step": 1.0,
        },
        "input_study_count": 17,
        "eligible_study_count": 15,
        "eligible_study_order": [
            "Study 1", "Study 3", "Study 4", "Study 5", "Study 6",
            "Study 7", "Study 8", "Study 10", "Study 11", "Study 12",
            "Study 13", "Study 14", "Study 15", "Study 16", "Study 17",
        ],
        "exclusions": [
            {"study_name": "Study 2", "reason": "Missing moderator value(s): Qualification index"},
            {"study_name": "Study 9", "reason": "Missing moderator value(s): Qualification index"},
        ],
        "sensitivity_coefficients": [
            {"term": "Qualification index", "model_estimate": 0.02, "p_value": 0.4},
        ],
        "false_positive_rate_coefficients": [
            {"term": "Qualification index", "model_estimate": -0.01, "p_value": 0.7},
        ],
        "overall_ml_test": {
            "label": "All moderators", "fit_estimator": "ML", "statistic": 1.4,
            "degrees_of_freedom": 2, "p_value": 0.49,
            "included_study_order": [
                "Study 1", "Study 3", "Study 4", "Study 5", "Study 6",
                "Study 7", "Study 8", "Study 10", "Study 11", "Study 12",
                "Study 13", "Study 14", "Study 15", "Study 16", "Study 17",
            ],
        },
        "moderator_ml_tests": [
            {
                "label": "Qualification index", "fit_estimator": "ML", "statistic": 1.4,
                "degrees_of_freedom": 2, "p_value": 0.49,
                "included_study_order": [
                    "Study 1", "Study 3", "Study 4", "Study 5", "Study 6",
                    "Study 7", "Study 8", "Study 10", "Study 11", "Study 12",
                    "Study 13", "Study 14", "Study 15", "Study 16", "Study 17",
                ],
            }
        ],
        "unavailable_outputs": [
            {"name": name, "reason": "No conditional prediction implementation was supplied."}
            for name in (
                "conditional_summary_operating_point", "adjusted_sroc", "sroc_auc"
            )
        ],
        "figure_status": "available",
        "numeric_oracle": "observed_only_no_independent_expected_value",
    },
    "diagnostic.reitsma": {
        "status": "available", "kind": "joint-reitsma",
        "measures": ["Sensitivity", "Specificity"],
        "summary": "Sensitivity 0.81; specificity 0.76",
        "section_statuses": {"Summary operating point": "available", "SROC": "available"},
        "figure_status": "available",
        "numeric_oracle": "observed_only_no_independent_expected_value",
    },
    "binary.plot-edit": {
        "status": "available",
        "kind": "binary-plot-edit",
        "study_count": 19,
        "input_study_count": 19,
        "figure_status": "available",
        "figure_key": "analysis.standard.forest_plot.1",
        "figure_title": "Forest Plot",
        "numeric_oracle": "observed_only_no_independent_expected_value",
    },
    "binary.small-study-effects": {
        "status": "available", "kind": "small-study-effects",
        "report_status": "complete", "usable_studies": 19,
        "primary_test_status": "available", "primary_test_method": "egger",
        "section_statuses": {"tests": "available", "pooled_comparison": "available"},
        "report_warnings": [], "figure_status": "available",
        "numeric_oracle": "observed_only_no_independent_expected_value",
    },
    "diagnostic.subgroup": {
        "status": "available", "kind": "diagnostic-subgroup",
        "covariate_name": "Qualification region", "missing_policy": "exclude",
        "confidence_level": 90.0, "input_study_count": 17,
        "included_count": 15, "missing_count": 2, "excluded_count": 2,
        "assignments": [
            {
                "study_id": index,
                "study_name": "Study %s" % index,
                "value": None if index in (2, 9) else ("North" if index % 2 else "South"),
                "status": "excluded_missing" if index in (2, 9) else "included",
            }
            for index in range(1, 18)
        ],
        "levels": [
            {
                "label": "North", "study_order": ["Study 1", "Study 3", "Study 5", "Study 7", "Study 11", "Study 13", "Study 15", "Study 17"],
                "included_count": 8, "status": "available",
            },
            {
                "label": "South", "study_order": ["Study 4", "Study 6", "Study 8", "Study 10", "Study 12", "Study 14", "Study 16"],
                "included_count": 7, "status": "available",
            },
        ],
        "overall": {"included_count": 15, "status": "available"},
        "between_subgroup_test_status": "not_calculated",
        "figure_status": "available",
        "numeric_oracle": "observed_only_no_independent_expected_value",
    },
}


def _observed_group_result(count, estimate):
    return {
        "status": "available",
        "reason": None,
        "estimate": estimate,
        "lower_bound": estimate - 0.2,
        "upper_bound": estimate + 0.2,
        "included_count": count,
    }


def _subgroup_result_fixture(route):
    family, _workflow, metric, _method = _FOLLOW_ON_RUNS[route]
    count = 19 if family == "binary" else 17 if family == "diagnostic" else 6
    missing_indexes = {1, 8} if count >= 10 else {1, 2}
    assignments = []
    groups: dict[str, list[dict[str, object]]] = {}
    for index in range(count):
        value = None if index in missing_indexes else "North" if index % 2 == 0 else "South"
        assignment = {
            "study_id": index + 1,
            "study_name": "Study %s" % (index + 1),
            "value": value,
            "status": "excluded_missing" if value is None else "included",
        }
        assignments.append(assignment)
        if value is not None:
            groups.setdefault(value, []).append(assignment)
    levels = [
        {
            "label": label,
            "study_ids": [row["study_id"] for row in rows],
            "study_order": [row["study_name"] for row in rows],
            **_observed_group_result(len(rows), 0.15 if label == "North" else 0.25),
        }
        for label, rows in groups.items()
    ]
    return {
        "status": "available",
        "kind": "%s-subgroup" % family,
        "family": family,
        "metric": metric,
        "covariate_name": "Qualification region",
        "missing_policy": "exclude",
        "confidence_level": 90.0,
        "input_study_count": count,
        "included_count": count - len(missing_indexes),
        "missing_count": len(missing_indexes),
        "excluded_count": len(missing_indexes),
        "assignments": assignments,
        "levels": levels,
        "overall": {
            "included_count": count - len(missing_indexes),
            **_observed_group_result(count - len(missing_indexes), 0.2),
        },
        "between_subgroup_test_status": "not_calculated",
        "figure_status": "available",
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }


def _numeric_observation(status="available", value=0.1, reason=None):
    return {"status": status, "value": value, "reason": reason}


def _method_variant_result_fixture(route):
    family, workflow, metric, method = _FOLLOW_ON_RUNS[route]
    count = 19 if family == "binary" else 17 if family == "diagnostic" else 6
    return {
        "status": "available",
        "kind": "method-variant",
        "family": family,
        "workflow": workflow,
        "metric": metric,
        "method": method,
        "estimate": 0.2,
        "study_count": count,
        "input_study_count": count,
        "study_order": ["Study %s" % index for index in range(1, count + 1)],
        "figure_status": "available",
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }


def _sequential_result_fixture(route):
    data_type, workflow, metric, _method = _FOLLOW_ON_RUNS[route]
    names = ["Study %s" % index for index in range(1, 7)]
    ids = list(range(1, 7))
    if workflow == "cumulative":
        order = list(reversed(range(6)))
        steps = []
        for index, source_order in enumerate(order):
            included_count = index + 1
            steps.append({
                "order": index,
                "source_order": source_order,
                "study_id": ids[source_order],
                "study_name": names[source_order],
                "included_study_count": included_count,
                "status": "complete",
                "numbers": {
                    "analyzed_study_count": _numeric_observation(value=included_count),
                    "estimate": _numeric_observation(value=0.1 * included_count),
                    "lower_bound": _numeric_observation(value=0.1 * included_count - 0.2),
                    "upper_bound": _numeric_observation(value=0.1 * included_count + 0.2),
                    "standard_error": _numeric_observation(value=0.1),
                    "p_value": _numeric_observation(value=0.5),
                },
            })
        return {
            "status": "available",
            "kind": "cumulative-analysis",
            "data_type": data_type,
            "metric": metric,
            "result_status": "complete",
            "ordering": {
                "field": "project_order",
                "direction": "descending",
                "missing_year_policy": None,
                "tie_policy": "original_project_order",
            },
            "input_study_count": len(ids),
            "input_study_ids": ids,
            "study_ids": list(reversed(ids)),
            "study_order": list(reversed(names)),
            "steps": steps,
            "figure_status": "available",
            "numeric_oracle": "observed_only_no_independent_expected_value",
        }
    rows = [{
        "kind": "baseline",
        "label": "All included studies",
        "study_id": None,
        "remaining_study_count": len(ids),
        "status": "available",
        "numbers": {
            "estimate": _numeric_observation(value=0.2),
            "lower_bound": _numeric_observation(value=0.0),
            "upper_bound": _numeric_observation(value=0.4),
            "change_from_baseline": _numeric_observation(value=0.0),
        },
    }]
    for index, (study_id, name) in enumerate(zip(ids, names, strict=True)):
        partial = index == 2
        rows.append({
            "kind": "omission",
            "label": "Omitting %s" % name,
            "study_id": study_id,
            "remaining_study_count": len(ids) - 1,
            "status": "partial" if partial else "available",
            "numbers": {
                "estimate": _numeric_observation(value=0.2 + index / 100),
                "lower_bound": _numeric_observation(
                    "not_available", None, "Qualification partial interval"
                ) if partial else _numeric_observation(value=0.0),
                "upper_bound": _numeric_observation(value=0.4),
                "change_from_baseline": _numeric_observation(value=index / 100),
            },
        })
    return {
        "status": "available",
        "kind": "leave-one-out-analysis",
        "data_type": data_type,
        "metric": metric,
        "result_status": "partial",
        "row_status_result": "partial",
        "input_study_count": len(ids),
        "study_ids": ids,
        "study_order": names,
        "rows": rows,
        "figure_status": "available",
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }


for _route in _FOLLOW_ON_RUNS:
    if _route.endswith(".subgroup"):
        _RESULT_EVIDENCE[_route] = _subgroup_result_fixture(_route)
    elif _route.endswith(".cumulative") or _route.endswith(".leave-one-out"):
        _RESULT_EVIDENCE[_route] = _sequential_result_fixture(_route)
    elif _route in worker_journey_qualification._METHOD_VARIANT_ROUTES:
        _RESULT_EVIDENCE[_route] = _method_variant_result_fixture(_route)


def _record(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _records(value: object) -> list[dict[str, object]]:
    assert isinstance(value, list)
    assert all(isinstance(item, dict) for item in value)
    return cast(list[dict[str, object]], value)


def _observation(route):
    data_type, workflow, metric, method = (_RUNS | _FOLLOW_ON_RUNS)[route]
    result_evidence = None
    if route in _FOLLOW_ON_RUNS:
        result_evidence = copy.deepcopy(_RESULT_EVIDENCE[route])
    if route.endswith(".subgroup"):
        include_evidence = copy.deepcopy(_RESULT_EVIDENCE[route])
        missing_evidence = copy.deepcopy(include_evidence)
        missing_assignments = _records(missing_evidence["assignments"])
        missing_rows = [row for row in missing_assignments if row["value"] is None]
        missing_evidence.update(
            missing_policy="missing_category",
            included_count=len(missing_assignments),
            excluded_count=0,
            assignments=[
                dict(row, status="included") for row in missing_assignments
            ],
            levels=_records(include_evidence["levels"]) + [
                {
                    "label": "Missing values",
                    "study_ids": [row["study_id"] for row in missing_rows],
                    "study_order": [row["study_name"] for row in missing_rows],
                    **_observed_group_result(len(missing_rows), 0.05),
                }
            ],
            overall={
                "included_count": len(missing_assignments),
                **_observed_group_result(len(missing_assignments), 0.2),
            },
        )
        value: dict[str, object] = {
            "route": route,
            "worker_completed": True,
            "event_loop_responsive": True,
            "saved_analysis_status": "complete",
            "reopened_analysis_count": 2,
            "main_process_r_bridge_absent": True,
            "saved_edit_copy_opened": True,
            "live_project_confidence_level": 95.0,
            "saved_edit_copy_confidence_level": 90.0,
            "saved_edit_copy_missing_policy": "exclude",
            "analysis_runs": [],
        }
        for policy, evidence in (
            ("exclude", include_evidence),
            ("missing_category", missing_evidence),
        ):
            run = {
                "data_type": data_type,
                "workflow": workflow,
                "metric": metric,
                "method": method,
                "status": "complete",
                "saved_reopened": True,
                "input_identity": ("a" if policy == "exclude" else "c") * 64,
                "result_text_sha256": ("b" if policy == "exclude" else "d") * 64,
                "study_order": [
                    row["study_name"]
                    for row in _records(include_evidence["assignments"])
                ],
                "warnings": [],
                "result_evidence": evidence,
                "figure_status": "exported",
                "figure_export_bytes": 2048,
            }
            _records(value["analysis_runs"]).append(run)
        value["qualification_status"] = "complete"
        return value

    value: dict[str, object] = {
        "route": route,
        "worker_completed": True,
        "event_loop_responsive": True,
        "saved_analysis_status": "complete",
        "reopened_analysis_count": 1,
        "main_process_r_bridge_absent": True,
        "analysis_runs": [
            {
                "data_type": data_type,
                "workflow": workflow,
                "metric": metric,
                "method": method,
                "status": "complete",
                "saved_reopened": True,
                "input_identity": "a" * 64,
                "result_text_sha256": "b" * 64,
                "study_order": ["Study 1", "Study 2"],
                "warnings": [],
            }
        ],
    }
    if route.startswith("binary."):
        if route in _RUNS:
            value.update(
                stop_acknowledged=True,
                stopped_settings_retained=True,
                reopened_draft_count=1,
                offline_export_bytes=1024,
            )
    if route in _FOLLOW_ON_RUNS:
        assert result_evidence is not None
        count = result_evidence.get(
            "eligible_study_count",
            result_evidence.get(
                "usable_studies",
                result_evidence.get(
                    "study_count",
                    result_evidence.get(
                        "input_study_count", {"diagnostic.reitsma": 17}.get(route, 0)
                    ),
                ),
            ),
        )
        assert isinstance(count, int)
        if route.endswith(".subgroup"):
            study_order = [
                row["study_name"] for row in _records(result_evidence["assignments"])
            ]
        elif route.endswith(".cumulative") or route.endswith(".leave-one-out"):
            study_order = cast(list[str], result_evidence["study_order"])
        else:
            study_order = ["Study %s" % index for index in range(1, count + 1)]
        run = _records(value["analysis_runs"])[0]
        run["study_order"] = study_order
        if route.endswith("meta-regression"):
            if route != "diagnostic.reitsma-meta-regression":
                result_evidence["eligible_study_order"] = study_order
        if route == "diagnostic.reitsma-meta-regression":
            run["study_order"] = ["Study %s" % index for index in range(1, 18)]
            run["report_view_after_reopen"] = True
        if route == "binary.small-study-effects":
            result_evidence["report_study_order"] = study_order
        result_status = result_evidence.get("result_status", "complete")
        if route in {"continuous.leave-one-out", "diagnostic.leave-one-out"}:
            run["status"] = cast(str, result_status)
            value["saved_analysis_status"] = cast(str, result_status)
        value["qualification_status"] = "complete"
        run["result_evidence"] = result_evidence
        run["figure_status"] = "exported"
        run["figure_export_bytes"] = 2048
        if route == "binary.plot-edit":
            plot_identity = {
                "analysis_id": "saved-record-id",
                "figure_key": "analysis.standard.forest_plot.1",
            }
            regeneration_identity = dict(plot_identity, generation=2)
            edit_identity = dict(plot_identity, generation=3)
            value["analysis_runs"][0]["analysis_id"] = "saved-record-id"
            run.update(
                saved_plot_regeneration={
                    "worker_completed": True,
                    "worker_request": {
                        "run_id": "saved-plot-regenerate-run",
                        "operation": "saved_plot_render",
                        "artifact_identity": regeneration_identity,
                    },
                    "record_revision_before": "a" * 64,
                    "record_revision_after": "b" * 64,
                    "stored_image_sha256": "c" * 64,
                },
                saved_plot_edit={
                    "worker_completed": True,
                    "worker_request": {
                        "run_id": "saved-plot-edit-run",
                        "operation": "saved_plot_render",
                        "artifact_identity": edit_identity,
                    },
                    "record_revision_before": "b" * 64,
                    "record_revision_after": "d" * 64,
                },
                saved_edited_artifact={
                    "persistence": "saved_record",
                    "record_id": "saved-record-id",
                    "figure_key": "analysis.standard.forest_plot.1",
                    "record_revision": "d" * 64,
                    "style": {"fp_xlabel": "Qualification effect direction"},
                    "image_sha256": "e" * 64,
                },
                saved_edited_artifact_after_reopen={
                    "record_id": "saved-record-id",
                    "figure_key": "analysis.standard.forest_plot.1",
                    "record_revision": "d" * 64,
                    "style": {"fp_xlabel": "Qualification effect direction"},
                    "image_sha256": "e" * 64,
                },
                source_result_unchanged=True,
                saved_edited_reopened=True,
            )
    return value


def _route_observation(route):
    value = _observation(route)
    if (
        route in qualify_worker_journey._METHOD_VARIANT_ROUTES
        and route in qualify_worker_journey._BINARY_METHOD_WORKFLOW_ROUTES
    ):
        value.update(
            stop_acknowledged=True,
            stopped_settings_retained=True,
            reopened_draft_count=1,
            offline_export_bytes=1024,
        )
    return value


def _inputs(tmp_path):
    artifact = tmp_path / "package.tar.gz"
    artifact.write_bytes(b"package")
    sample_root = tmp_path / "sample_projects"
    sample_root.mkdir()
    sample = sample_root / "amino.rcms"
    sample.write_bytes(b"binary sample")
    for name in ("continuous.rcms", "lymph.rcms"):
        (sample_root / name).write_bytes(name.encode())
    return artifact, sample


def test_qualifier_runs_each_route_in_a_fresh_bounded_process(tmp_path, monkeypatch):
    artifact, sample = _inputs(tmp_path)
    calls = []

    def run(command, *, timeout, environment):
        calls.append((command, timeout, environment))
        Path(command[2]).write_text(json.dumps(_observation(command[5])), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="route stdout", stderr="route stderr")

    monkeypatch.setattr(qualify_worker_journey, "_run_package", run)
    output = tmp_path / "qualification" / "worker.json"
    destination = tmp_path / "qualification" / "saved.rcms"
    result = qualify_worker_journey.qualify(
        tmp_path / "launcher",
        sample,
        destination,
        output,
        artifact=artifact,
        r_home=tmp_path / "R",
        r_libs=tmp_path / "R" / "library",
        route_timeout=90,
    )

    assert [call[0][5] for call in calls] == list(_RUNS)
    assert all(call[1] == 90 for call in calls)
    assert all(call[0][1] == "--automation-package-worker-journey" for call in calls)
    assert all(call[2]["RCMS_R_HOME"] == str(tmp_path / "R") for call in calls)
    assert all("R_HOME" not in call[2] for call in calls)
    assert result["passed"] is True
    assert result["gate"] == "bounded-core-worker"
    assert result["requested_routes"] == list(_RUNS)
    assert result["package_sha256"] == qualify_worker_journey._sha256_file(artifact)
    assert result["sample_project_sha256"] == qualify_worker_journey._sha256_file(sample)
    assert [route["status"] for route in _records(result["routes"])] == ["complete"] * 5
    assert len(_records(result["analysis_runs"])) == 5
    assert _record(result["host"])["system"] == qualify_worker_journey.platform.system()
    assert json.loads(output.read_text(encoding="utf-8")) == result


def test_qualifier_cannot_reuse_evidence_from_an_earlier_attempt(tmp_path, monkeypatch):
    artifact, sample = _inputs(tmp_path)
    output = tmp_path / "worker.json"

    def produce_observation(command, *, timeout, environment):
        Path(command[2]).write_text(json.dumps(_observation(command[5])), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(qualify_worker_journey, "_run_package", produce_observation)
    arguments = (tmp_path / "launcher", sample, tmp_path / "saved.rcms", output)
    assert qualify_worker_journey.qualify(
        *arguments, artifact=artifact, routes=("binary.standard",)
    )["passed"] is True

    monkeypatch.setattr(
        qualify_worker_journey,
        "_run_package",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    artifact.write_bytes(b"different package")
    result = qualify_worker_journey.qualify(
        *arguments, artifact=artifact, routes=("binary.standard",)
    )
    assert result["passed"] is False
    assert _records(result["routes"])[0]["status"] == "failed"


def test_offline_figure_export_requires_a_new_output_for_every_result(tmp_path):
    image = tmp_path / "stored.png"
    image.write_bytes(b"stored figure")
    destination = tmp_path / "saved.rcms"
    stale_export = destination.with_suffix(".binary-subgroup.png")
    stale_export.write_bytes(b"old policy figure")
    dialog = SimpleNamespace(getSaveFileName=lambda *args: ("", ""))
    results_window = SimpleNamespace(QFileDialog=dialog)
    viewer = SimpleNamespace(
        images={"figure": str(image)},
        create_plot_artifact=lambda *args: object(),
        plot_service=SimpleNamespace(export=lambda *args: None),
        save_image_as=lambda *args, **kwargs: None,
    )
    with pytest.raises(RuntimeError, match="could not be exported offline"):
        worker_journey_qualification._export_first_figure(
            viewer, destination, "binary.subgroup", results_window
        )
    assert stale_export.read_bytes() == b"old policy figure"

    paths = []

    def export(*args, **kwargs):
        path = Path(dialog.getSaveFileName()[0])
        paths.append(path)
        path.write_bytes(image.read_bytes())

    viewer.save_image_as = export
    for _ in range(2):
        evidence = worker_journey_qualification._export_first_figure(
            viewer, destination, "binary.subgroup", results_window
        )
        assert evidence["figure_status"] == "exported"
        assert evidence["source_figure_sha256"] == qualify_worker_journey._sha256_file(image)
        assert evidence["figure_export_sha256"] == qualify_worker_journey._sha256_file(paths[-1])
    assert paths[0] != paths[1]


def test_qualifier_records_timeout_and_continues_later_routes(tmp_path, monkeypatch):
    artifact, sample = _inputs(tmp_path)
    calls = []

    def run(command, *, timeout, environment):
        calls.append(command[5])
        if command[5] == "binary.cumulative":
            error = qualify_worker_journey.subprocess.TimeoutExpired(
                command, timeout, output=b"worker progress", stderr=b"last stderr"
            )
            setattr(error, "worker_pid", 456)
            setattr(error, "worker_returncode", None)
            setattr(error, "worker_process_state", "cleanup_unconfirmed")
            raise error
        Path(command[2]).write_text(json.dumps(_observation(command[5])), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(qualify_worker_journey, "_run_package", run)
    output = tmp_path / "worker.json"
    result = qualify_worker_journey.qualify(
        tmp_path / "launcher",
        sample,
        tmp_path / "saved.rcms",
        output,
        artifact=artifact,
        route_timeout=30,
    )

    assert calls == list(_RUNS)
    assert result["passed"] is False
    routes = _records(result["routes"])
    assert [route["status"] for route in routes] == [
        "complete",
        "timed_out",
        "complete",
        "complete",
        "complete",
    ]
    timed_out = routes[1]
    assert timed_out["elapsed_seconds"] == 30
    assert timed_out["stdout"] == "worker progress"
    assert timed_out["stderr"] == "last stderr"
    assert timed_out["worker_pid"] == 456
    assert timed_out["worker_process_state"] == "cleanup_unconfirmed"
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is False


def test_qualifier_marks_missing_sample_unavailable_and_continues(tmp_path, monkeypatch):
    artifact, sample = _inputs(tmp_path)
    (sample.parent / "continuous.rcms").unlink()
    calls = []

    def run(command, *, timeout, environment):
        calls.append(command[5])
        Path(command[2]).write_text(json.dumps(_observation(command[5])), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(qualify_worker_journey, "_run_package", run)
    result = qualify_worker_journey.qualify(
        tmp_path / "launcher",
        sample,
        tmp_path / "saved.rcms",
        tmp_path / "worker.json",
        artifact=artifact,
    )

    assert calls == [route for route in _RUNS if route != "continuous.standard"]
    assert result["passed"] is False
    unavailable = _records(result["routes"])[3]
    assert unavailable["route"] == "continuous.standard"
    assert unavailable["status"] == "unavailable"
    details = unavailable["details"]
    assert isinstance(details, str) and "missing" in details


def test_qualifier_selected_route_is_not_reported_as_core_gate(tmp_path, monkeypatch):
    artifact, sample = _inputs(tmp_path)

    def run(command, *, timeout, environment):
        Path(command[2]).write_text(json.dumps(_observation(command[5])), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(qualify_worker_journey, "_run_package", run)
    result = qualify_worker_journey.qualify(
        tmp_path / "launcher",
        sample,
        tmp_path / "saved.rcms",
        tmp_path / "worker.json",
        artifact=artifact,
        routes=("diagnostic.standard",),
    )

    assert result["passed"] is True
    assert result["gate"] == "selected-routes"
    assert result["requested_routes"] == ["diagnostic.standard"]
    assert len(_records(result["analysis_runs"])) == 1


@pytest.mark.parametrize("route", tuple(_FOLLOW_ON_RUNS))
def test_follow_on_routes_require_result_specific_persisted_evidence(route):
    observation = _route_observation(route)

    assert qualify_worker_journey._route_observation_valid(route, observation)
    assert _RESULT_EVIDENCE[route]["numeric_oracle"] == (
        "observed_only_no_independent_expected_value"
    )


def test_plot_edit_route_requires_saved_render_edit_commit_reopen_and_export():
    observation = _observation("binary.plot-edit")

    assert qualify_worker_journey._route_observation_valid(
        "binary.plot-edit", observation
    )

    run = _records(observation["analysis_runs"])[0]
    evidence = _record(run["result_evidence"])
    evidence["figure_key"] = "another-figure"
    assert not qualify_worker_journey._route_observation_valid(
        "binary.plot-edit", observation
    )
    evidence["figure_key"] = "analysis.standard.forest_plot.1"
    reopened = _record(run["saved_edited_artifact_after_reopen"])
    reopened["image_sha256"] = "f" * 64
    assert not qualify_worker_journey._route_observation_valid(
        "binary.plot-edit", observation
    )
    reopened["image_sha256"] = "e" * 64
    edit = _record(run["saved_plot_edit"])
    edit["worker_completed"] = False
    assert not qualify_worker_journey._route_observation_valid(
        "binary.plot-edit", observation
    )


def test_saved_plot_qualification_reads_only_the_target_figure_presentation(monkeypatch):
    expected_label = "Qualification effect direction"
    figure_key = "analysis.standard.forest_plot.1"
    edited = {
        "record_id": "saved-record-id",
        "figure_key": figure_key,
        "record_revision": "d" * 64,
        "style": {"fp_xlabel": expected_label},
        "image_sha256": "e" * 64,
    }
    monkeypatch.setattr(
        worker_journey_qualification, "_analysis_evidence", lambda *_args, **_kwargs: {}
    )
    monkeypatch.setattr(
        worker_journey_qualification, "_same_analysis_evidence", lambda *_args: True
    )

    wrong_record = SimpleNamespace(
        value={
            "id": "saved-record-id",
            "presentation": {
                "fp_xlabel": expected_label,
                "figures": {
                    "analysis.standard.forest_plot.2": {"fp_xlabel": expected_label},
                    figure_key: {"fp_xlabel": "Wrong figure label"},
                },
            },
        }
    )
    evidence = {"analysis_id": "saved-record-id", "saved_edited_artifact": edited}
    with pytest.raises(RuntimeError, match="did not survive reopen"):
        worker_journey_qualification._validate_reopened_edited_plot(
            object(), evidence, "binary.plot-edit", wrong_record, "d" * 64, "e" * 64
        )

    correct_record = SimpleNamespace(
        value={
            "id": "saved-record-id",
            "presentation": {
                "fp_xlabel": expected_label,
                "figures": {
                    "analysis.standard.forest_plot.2": {"fp_xlabel": "Other figure"},
                    figure_key: {"fp_xlabel": expected_label},
                },
            },
        }
    )
    artifact = worker_journey_qualification._saved_edited_plot_artifact(
        correct_record, "d" * 64, "e" * 64, edited
    )
    assert artifact == edited
    evidence["saved_edited_artifact"] = artifact
    worker_journey_qualification._validate_reopened_edited_plot(
        object(), evidence, "binary.plot-edit", correct_record, "d" * 64, "e" * 64
    )

    missing_target = SimpleNamespace(
        value={
            "presentation": {
                "fp_xlabel": expected_label,
                "figures": {
                    "analysis.standard.forest_plot.2": {"fp_xlabel": expected_label}
                },
            }
        }
    )
    with pytest.raises(RuntimeError, match="no scoped presentation"):
        worker_journey_qualification._saved_edited_plot_artifact(
            missing_target, "d" * 64, "e" * 64, edited
        )


def test_plot_edit_evidence_resolves_display_title_to_saved_image_key():
    results = {
        "binary_numerics": {"pooled": {}},
        "images": {"analysis.standard.forest_plot.1": "assets/forest.svg"},
        "sections": [
            {
                "kind": "image",
                "title": "Forest Plot",
                "source_key": "analysis.standard.forest_plot.1",
            }
        ],
    }

    evidence = worker_journey_qualification._plot_edit_result_evidence(
        results, {"studies": [{}, {}]}, {}
    )

    assert evidence is not None
    assert evidence["figure_status"] == "available"
    assert evidence["figure_key"] == "analysis.standard.forest_plot.1"
    assert evidence["figure_title"] == "Forest Plot"

    results["sections"] = []
    assert worker_journey_qualification._plot_edit_result_evidence(
        results, {"studies": [{}, {}]}, {}
    ) is None


@pytest.mark.parametrize(
    ("route", "field", "value"),
    [
        ("binary.one-arm", "pooled_proportion", float("nan")),
        ("continuous.entered-effect", "input_study_count", 5),
        ("binary.meta-regression", "coefficients", []),
        ("diagnostic.reitsma", "measures", ["Sensitivity"]),
        ("binary.small-study-effects", "report_status", "partial"),
        ("diagnostic.reitsma-meta-regression", "exclusions", []),
        ("diagnostic.reitsma-meta-regression", "effective_settings", {}),
    ],
)
def test_follow_on_route_rejects_missing_or_incomplete_semantics(route, field, value):
    observation = _observation(route)
    observation["analysis_runs"][0]["result_evidence"][field] = value

    assert not qualify_worker_journey._route_observation_valid(route, observation)


def _reitsma_meta_regression_saved_inputs():
    eligible = [str(index) for index in range(1, 18) if index not in {2, 9}]
    study_names = {str(index): "Study %s" % index for index in range(1, 18)}

    def coefficient(term, side, direction, estimate):
        return {
            "term": term,
            "model_side": side,
            "effect_direction": direction,
            "model_estimate": estimate,
            "standard_error": 0.1,
            "model_statistic": estimate / 0.1,
            "p_value": 0.2,
            "model_ci_lower": estimate - 0.2,
            "model_ci_upper": estimate + 0.2,
            "reported_odds_ratio": 1.0,
            "odds_ratio_ci_lower": 0.5,
            "odds_ratio_ci_upper": 2.0,
        }

    studies = [
        {"id": index, "name": study_names[str(index)]}
        for index in range(1, 18)
    ]
    values = [None if index in {2, 9} else float(index) for index in range(1, 18)]
    snapshot = {
        "version": 1,
        "data_type": "diagnostic",
        "outcome": "Disease status",
        "time_point": "present",
        "groups": ["lymph-node"],
        "metric": "Sensitivity and specificity",
        "studies": studies,
        "moderators": [
            {
                "name": "Qualification index",
                "kind": "continuous",
                "values": values,
                "unit": "study index",
                "unit_step": 1.0,
                "reference_level": None,
            }
        ],
    }
    specification = {
        "version": 1,
        "data_type": "diagnostic",
        "workflow": "meta-regression",
        "method": "diagnostic.reitsma",
        "metric": "Sens",
        "missing_moderator_policy": "exclude",
        "params": {
            "estimator": "REML",
            "adjust": 0.5,
            "correction.policy": "All studies if any zero exists",
            "conf.level": 90.0,
            "digits": 3,
            "create.plot": True,
            "joint.metrics": "Sens,Spec",
        },
    }
    test_row = {
        "label": "All moderators",
        "comparison": "full model vs intercept-only model",
        "statistic": 1.4,
        "degrees_of_freedom": 2,
        "p_value": 0.49,
        "fit_estimator": "ML",
        "included_study_ids": eligible,
    }
    numerics = {
        "schema": "reitsma-meta-regression-v1",
        "formula": "cbind(tsens, tfpr) ~ `Qualification index`",
        "estimator": "REML",
        "correction": {"policy": "All studies if any zero exists", "factor": 0.5},
        "package_version": "0.5.12",
        "converged": True,
        "eligible_study_ids": eligible,
        "exclusions": [
            {
                "study_id": str(index),
                "reason": "Missing moderator value(s): Qualification index",
            }
            for index in (2, 9)
        ],
        "moderator_coding": [
            {
                "name": "Qualification index",
                "kind": "continuous",
                "levels": [],
                "reference_level": None,
                "observed_range": [1.0, 17.0],
            }
        ],
        "sensitivity_coefficients": [
            coefficient("Qualification index", "sensitivity", "sensitivity", 0.02),
        ],
        "false_positive_rate_coefficients": [
            coefficient("Qualification index", "false_positive_rate", "specificity", -0.01),
        ],
        "overall_ml_likelihood_ratio_test": test_row,
        "moderator_block_ml_tests": [
            {**test_row, "label": "Qualification index"}
        ],
        "unavailable_outputs": [
            {"name": name, "reason": "No conditional prediction implementation was supplied."}
            for name in (
                "conditional_summary_operating_point", "adjusted_sroc", "sroc_auc"
            )
        ],
    }
    record = {"specification": specification}
    result = {"reitsma_meta_regression_numerics": numerics, "images": {}}
    return result, snapshot, record


def test_reitsma_meta_regression_saved_evidence_keeps_specification_and_exclusions():
    from rc_metastudio.worker_journey_qualification import (
        _reitsma_meta_regression_result_evidence,
    )

    result, snapshot, record = _reitsma_meta_regression_saved_inputs()
    evidence = _reitsma_meta_regression_result_evidence(result, snapshot, record)

    assert evidence["effective_settings"]["missing_moderator_policy"] == "exclude"
    assert evidence["effective_settings"]["joint_metrics"] == "Sens,Spec"
    assert evidence["input_study_count"] == 17
    assert evidence["eligible_study_count"] == 15
    assert [row["study_name"] for row in evidence["exclusions"]] == [
        "Study 2", "Study 9"
    ]
    assert len(evidence["sensitivity_coefficients"]) == 1
    assert len(evidence["false_positive_rate_coefficients"]) == 1
    assert evidence["overall_ml_test"]["fit_estimator"] == "ML"
    assert evidence["moderator_ml_tests"][0]["label"] == "Qualification index"
    assert evidence["numeric_oracle"] == "observed_only_no_independent_expected_value"


def test_reitsma_report_view_uses_nested_saved_result_evidence():
    from rc_metastudio.worker_journey_qualification import (
        _reitsma_meta_regression_result_evidence,
        _reitsma_meta_regression_report_visible,
    )

    result, snapshot, record = _reitsma_meta_regression_saved_inputs()
    saved_evidence = _reitsma_meta_regression_result_evidence(
        result, snapshot, record
    )
    cell = SimpleNamespace(text=lambda: "ML")
    viewer = SimpleNamespace(
        reitsma_meta_regression_details=SimpleNamespace(
            text=lambda: "Eligible study IDs (15); exclusions (2); Qualification index"
        ),
        reitsma_sensitivity_coefficient_table=SimpleNamespace(
            rowCount=lambda: len(saved_evidence["sensitivity_coefficients"])
        ),
        reitsma_false_positive_rate_coefficient_table=SimpleNamespace(
            rowCount=lambda: len(saved_evidence["false_positive_rate_coefficients"])
        ),
        reitsma_meta_regression_test_table=SimpleNamespace(
            rowCount=lambda: 2,
            item=lambda row, column: cell if (row, column) == (0, 2) else None,
        ),
    )

    assert _reitsma_meta_regression_report_visible(
        viewer, {"result_evidence": saved_evidence}
    )


@pytest.mark.parametrize("corruption", ("policy", "exclusions", "coefficients", "tests"))
def test_reitsma_meta_regression_saved_evidence_rejects_drift(corruption):
    from rc_metastudio import worker_journey_qualification

    result, snapshot, record = _reitsma_meta_regression_saved_inputs()
    if corruption == "policy":
        record["specification"]["missing_moderator_policy"] = "reject"
    elif corruption == "exclusions":
        result["reitsma_meta_regression_numerics"]["exclusions"] = []
    elif corruption == "coefficients":
        result["reitsma_meta_regression_numerics"]["false_positive_rate_coefficients"] = []
    else:
        result["reitsma_meta_regression_numerics"]["overall_ml_likelihood_ratio_test"]["fit_estimator"] = "REML"

    assert worker_journey_qualification._reitsma_meta_regression_result_evidence(
        result, snapshot, record
    ) is None


def test_diagnostic_subgroup_route_requires_both_saved_missing_policies():
    observation = _observation("diagnostic.subgroup")

    assert qualify_worker_journey._route_observation_valid(
        "diagnostic.subgroup", observation
    )
    assert qualify_worker_journey._analysis_runs_valid(
        observation["analysis_runs"], ("diagnostic.subgroup",)
    )

    observation["analysis_runs"].pop()
    assert not qualify_worker_journey._route_observation_valid(
        "diagnostic.subgroup", observation
    )


@pytest.mark.parametrize(
    "route", ("binary.subgroup", "continuous.subgroup", "diagnostic.subgroup")
)
def test_each_subgroup_route_requires_two_retained_records(route):
    observation = _observation(route)

    assert qualify_worker_journey._analysis_runs_valid(
        observation["analysis_runs"], (route,)
    )
    assert qualify_worker_journey._qualification_passed(
        [{"status": "complete"}], observation["analysis_runs"], (route,)
    )
    assert not qualify_worker_journey._analysis_runs_valid(
        observation["analysis_runs"][:1], (route,)
    )


@pytest.mark.parametrize(
    "route", ("continuous.leave-one-out", "diagnostic.leave-one-out")
)
def test_partial_leave_one_out_result_survives_route_aggregation(route):
    observation = _observation(route)

    assert observation["saved_analysis_status"] == "partial"
    assert qualify_worker_journey._route_observation_valid(route, observation)
    assert qualify_worker_journey._qualification_passed(
        [{"status": "complete"}], observation["analysis_runs"], (route,)
    )


def test_cumulative_unavailable_backend_count_keeps_prefix_count_check():
    evidence = _sequential_result_fixture("continuous.cumulative")
    first_step = _records(evidence["steps"])[0]
    numbers = _record(first_step["numbers"])
    numbers["analyzed_study_count"] = _numeric_observation(
        "not_available", None, "The backend did not return analyzed study count."
    )

    assert qualify_worker_journey._route_result_evidence_valid(
        "continuous.cumulative", evidence
    )

    first_step["included_study_count"] = 2
    assert not qualify_worker_journey._route_result_evidence_valid(
        "continuous.cumulative", evidence
    )


def test_selected_subgroup_route_aggregates_both_policy_records(tmp_path, monkeypatch):
    artifact, sample = _inputs(tmp_path)

    def run(command, *, timeout, environment):
        Path(command[2]).write_text(
            json.dumps(_observation(command[5])), encoding="utf-8"
        )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(qualify_worker_journey, "_run_package", run)
    result = qualify_worker_journey.qualify(
        tmp_path / "launcher",
        sample,
        tmp_path / "saved.rcms",
        tmp_path / "worker.json",
        artifact=artifact,
        routes=("diagnostic.subgroup",),
    )

    assert result["passed"] is True
    assert result["gate"] == "selected-routes"
    assert result["requested_routes"] == ["diagnostic.subgroup"]
    assert len(_records(result["analysis_runs"])) == 2


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda e: e.update(excluded_count=1), False),
        (lambda e: e.update(confidence_level=95.0), False),
        (lambda e: e["levels"][0].update(included_count=7), False),
        (lambda e: e.update(between_subgroup_test_status="available"), False),
    ],
)
def test_diagnostic_subgroup_route_rejects_inconsistent_counts_and_saved_settings(
    mutation, expected
):
    observation = _observation("diagnostic.subgroup")
    mutation(observation["analysis_runs"][0]["result_evidence"])

    assert qualify_worker_journey._route_observation_valid(
        "diagnostic.subgroup", observation
    ) is expected


def test_diagnostic_subgroup_route_requires_edit_copy_to_keep_saved_confidence():
    observation = _observation("diagnostic.subgroup")

    assert qualify_worker_journey._route_observation_valid(
        "diagnostic.subgroup", observation
    )
    observation["saved_edit_copy_confidence_level"] = 95.0
    assert not qualify_worker_journey._route_observation_valid(
        "diagnostic.subgroup", observation
    )
    observation = _observation("diagnostic.subgroup")
    observation["saved_edit_copy_missing_policy"] = "missing_category"
    assert not qualify_worker_journey._route_observation_valid(
        "diagnostic.subgroup", observation
    )


def test_follow_on_route_is_unqualified_when_the_source_reports_a_gap(tmp_path, monkeypatch):
    artifact, sample = _inputs(tmp_path)

    def run(command, *, timeout, environment):
        observation = {
            "route": command[5],
            "qualification_status": "unqualified",
            "details": "no independent numerical oracle for this route",
        }
        Path(command[2]).write_text(json.dumps(observation), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(qualify_worker_journey, "_run_package", run)
    result = qualify_worker_journey.qualify(
        tmp_path / "launcher",
        sample,
        tmp_path / "saved.rcms",
        tmp_path / "worker.json",
        artifact=artifact,
        routes=("binary.meta-regression",),
    )

    assert result["passed"] is False
    unqualified = _records(result["routes"])[0]
    assert unqualified["status"] == "unqualified"
    details = unqualified["details"]
    assert isinstance(details, str) and "no independent numerical oracle" in details


def test_route_evidence_must_match_requested_route():
    observation = _observation("binary.standard")

    assert qualify_worker_journey._route_observation_valid("binary.standard", observation)
    observation["route"] = "binary.leave-one-out"
    assert not qualify_worker_journey._route_observation_valid("binary.standard", observation)


def test_analysis_run_identity_validation_preserves_duplicate_route_identities():
    run = {
        "data_type": "continuous",
        "workflow": "standard",
        "metric": "SMD",
        "method": "continuous.random",
        "status": "complete",
        "saved_reopened": True,
        "input_identity": "a" * 64,
        "result_text_sha256": "b" * 64,
        "study_order": ["Study 1", "Study 2"],
        "warnings": [],
    }

    assert qualify_worker_journey._analysis_runs_valid(
        [run, dict(run, input_identity="c" * 64)],
        ("continuous.standard", "continuous.entered-effect"),
    )
    assert not qualify_worker_journey._analysis_runs_valid(
        [run], ("continuous.standard", "continuous.entered-effect")
    )


def test_package_timeout_bounds_cleanup_when_a_child_holds_output_pipes(monkeypatch):
    class Pipe:
        closed = False

        def close(self):
            self.closed = True

    class HangingProcess:
        pid = 123
        returncode = None

        def __init__(self):
            self.stdout = Pipe()
            self.stderr = Pipe()
            self.communication_timeouts = []
            self.wait_timeout = None
            self.killed = False

        def communicate(self, timeout):
            self.communication_timeouts.append(timeout)
            raise qualify_worker_journey.subprocess.TimeoutExpired(
                ["app"], timeout, output=b"partial", stderr=b"pending"
            )

        def poll(self):
            return None

        def kill(self):
            self.killed = True

        def wait(self, timeout):
            self.wait_timeout = timeout
            raise qualify_worker_journey.subprocess.TimeoutExpired(["app"], timeout)

    process = HangingProcess()
    monkeypatch.setattr(
        qualify_worker_journey.subprocess, "Popen", lambda *args, **kwargs: process
    )
    monkeypatch.setattr(
        qualify_worker_journey, "_terminate_process_tree", lambda _process: None
    )

    with pytest.raises(qualify_worker_journey.subprocess.TimeoutExpired) as caught:
        qualify_worker_journey._run_package(["app"], timeout=1, environment={})

    assert process.communication_timeouts == [1, 10]
    assert process.wait_timeout == 2
    assert process.killed is True
    assert process.stdout.closed is True
    assert process.stderr.closed is True
    assert getattr(caught.value, "worker_pid") == 123
    assert getattr(caught.value, "worker_returncode") is None
    assert getattr(caught.value, "worker_process_state") == "cleanup_unconfirmed"


def test_qualifier_requires_positive_timeout(tmp_path):
    artifact, sample = _inputs(tmp_path)
    (sample.parent / "continuous.rcms").unlink()

    with pytest.raises(ValueError, match="positive"):
        qualify_worker_journey.qualify(
            tmp_path / "launcher",
            sample,
            tmp_path / "saved.rcms",
            tmp_path / "worker.json",
            artifact=artifact,
            route_timeout=0,
        )


def test_qualifier_records_linux_distribution_for_platform_identity(monkeypatch):
    monkeypatch.setattr(qualify_worker_journey.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        qualify_worker_journey.platform, "release", lambda: "6.8.0"
    )
    monkeypatch.setattr(
        qualify_worker_journey.platform, "version", lambda: "#1 SMP"
    )
    monkeypatch.setattr(
        qualify_worker_journey.platform, "machine", lambda: "x86_64"
    )
    monkeypatch.setattr(
        qualify_worker_journey.platform,
        "freedesktop_os_release",
        lambda: {"ID": "ubuntu", "VERSION_ID": "26.04"},
    )

    identity = qualify_worker_journey._host_identity()

    assert identity["os_release"] == {"ID": "ubuntu", "VERSION_ID": "26.04"}


def test_all_routes_cli_selects_every_registered_route(monkeypatch):
    selected: list[object] = []

    def fake_qualify(*args: object, **kwargs: object) -> dict[str, object]:
        selected.append(kwargs.get("routes"))
        return {"passed": True}

    monkeypatch.setattr(qualify_worker_journey, "qualify", fake_qualify)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qualify_worker_journey",
            "--executable", "app",
            "--sample", "sample.rcms",
            "--destination", "copy.rcms",
            "--output", "journey.json",
            "--artifact", "package.zip",
            "--all-routes",
        ],
    )

    assert qualify_worker_journey.main() == 0
    assert selected == [tuple(qualify_worker_journey._ROUTES)]


def test_all_additional_routes_cli_skips_only_the_core_routes(monkeypatch):
    selected: list[object] = []

    def fake_qualify(*args: object, **kwargs: object) -> dict[str, object]:
        selected.append(kwargs.get("routes"))
        return {"passed": True}

    monkeypatch.setattr(qualify_worker_journey, "qualify", fake_qualify)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qualify_worker_journey",
            "--executable", "app",
            "--sample", "sample.rcms",
            "--destination", "copy.rcms",
            "--output", "journey.json",
            "--artifact", "package.zip",
            "--all-additional-routes",
        ],
    )

    assert qualify_worker_journey.main() == 0
    additional = tuple(
        route for route in qualify_worker_journey._ROUTES
        if route not in qualify_worker_journey._CORE_ROUTES
    )
    assert len(additional) == 43
    assert selected == [additional]


def test_all_routes_cli_cannot_be_combined_with_one_route(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qualify_worker_journey",
            "--executable", "app",
            "--sample", "sample.rcms",
            "--destination", "copy.rcms",
            "--output", "journey.json",
            "--artifact", "package.zip",
            "--all-routes",
            "--route", "binary.standard",
        ],
    )

    with pytest.raises(SystemExit) as caught:
        qualify_worker_journey.main()

    assert caught.value.code == 2


@pytest.mark.parametrize(
    ("selection", "other_selection"),
    [
        ("--all-additional-routes", ("--all-routes",)),
        ("--all-additional-routes", ("--route", "binary.standard")),
        ("--all-routes", ("--all-additional-routes",)),
    ],
)
def test_route_set_cli_selections_are_mutually_exclusive(
    monkeypatch, selection, other_selection
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qualify_worker_journey",
            "--executable", "app",
            "--sample", "sample.rcms",
            "--destination", "copy.rcms",
            "--output", "journey.json",
            "--artifact", "package.zip",
            selection,
            *other_selection,
        ],
    )

    with pytest.raises(SystemExit) as caught:
        qualify_worker_journey.main()

    assert caught.value.code == 2


def test_cli_rejects_an_unregistered_method_route(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qualify_worker_journey",
            "--executable", "app",
            "--sample", "sample.rcms",
            "--destination", "copy.rcms",
            "--output", "journey.json",
            "--artifact", "package.zip",
            "--route", "binary.fixed.unknown.standard",
        ],
    )

    with pytest.raises(SystemExit) as caught:
        qualify_worker_journey.main()

    assert caught.value.code == 2


def test_route_registry_covers_every_inventory_desktop_method_workflow_cell():
    expected = _inventory_method_workflow_cells()
    actual = _registered_method_routes(expected)

    assert len(expected) == 44
    assert len(qualify_worker_journey._ROUTES) == 48
    assert len(qualify_worker_journey._CORE_ROUTES) == 5
    assert len(qualify_worker_journey._METHOD_VARIANT_ROUTES) == 28
    assert set(qualify_worker_journey._METHOD_VARIANT_ROUTES) == {
        "%s.%s" % (method, workflow)
        for _family, workflow, _metric, method, _sample
        in qualify_worker_journey._METHOD_VARIANT_ROUTE_SPECS
    }
    assert set(qualify_worker_journey._METHOD_VARIANT_ROUTES) == set(
        worker_journey_qualification._METHOD_VARIANT_ROUTES
    )
    assert {
        route: value[1]
        for route, value in qualify_worker_journey._METHOD_VARIANT_ROUTES.items()
    } == worker_journey_qualification._METHOD_VARIANT_ROUTES
    assert sum(
        route not in qualify_worker_journey._CORE_ROUTES
        for route in qualify_worker_journey._ROUTES
    ) == 43
    assert set(actual) == expected
    assert all(len(routes) == 1 for routes in actual.values())


def _inventory_method_workflow_cells():
    inventory_path = (
        Path(__file__).resolve().parents[3]
        / "tests/analysis_regression/baseline/released-capability-inventory.json"
    )
    combinations = json.loads(
        inventory_path.read_text(encoding="utf-8")
    )["analysis_combinations"]
    expected = set()
    for family, workflows in combinations.items():
        for workflow, entries in workflows.items():
            if workflow == "bootstrap":
                continue
            for entry in entries:
                expected.add((family, workflow, entry["method"]))
    return expected


def _registered_method_routes(expected):
    actual: dict[tuple[str, str, str], list[str]] = {}
    for route, (_sample, identity) in qualify_worker_journey._ROUTES.items():
        # These routes exercise extra input or plot-edit flows over a method cell.
        if route in {
            "binary.one-arm",
            "binary.plot-edit",
            "continuous.entered-effect",
        }:
            continue
        family, workflow, _metric, method = identity
        if (family, workflow, method) in expected:
            actual.setdefault((family, workflow, method), []).append(route)
    return actual


@pytest.mark.parametrize(
    "route", tuple(worker_journey_qualification._METHOD_VARIANT_ROUTES)
)
def test_method_variant_route_selects_its_catalogued_method(route, monkeypatch):
    identity = qualify_worker_journey._ROUTES[route][1]
    family, workflow, metric, method = identity
    label = "Selected %s" % method

    class MethodCombo:
        selected = None

        def setCurrentText(self, value):
            self.selected = value

    form = SimpleNamespace(
        analysis_type=workflow,
        available_method_d={label: method},
        method_cbo_box=MethodCombo(),
    )
    client = SimpleNamespace(methodsReady=object())
    window = SimpleNamespace(
        analysis_worker=client,
        workspace=SimpleNamespace(list_saved_analyses=lambda: []),
        findChildren=lambda _dialog_type: [form],
    )
    dialog_module = SimpleNamespace(AnalysisSetupDialog=type("Dialog", (), {}))
    monkeypatch.setitem(sys.modules, "rc_metastudio.analysis_setup_dialog", dialog_module)
    monkeypatch.setattr(rc_metastudio, "analysis_setup_dialog", dialog_module, raising=False)
    monkeypatch.setattr(
        worker_journey_qualification,
        "_await_worker",
        lambda _client, action, _signal: action(),
    )
    action_calls = []

    worker_journey_qualification._prepare_worker_analysis_form(
        window,
        lambda: action_calls.append("methods-requested"),
        family,
        metric,
        workflow,
        method,
    )

    assert action_calls == ["methods-requested"]
    assert form.method_cbo_box.selected == label
    assert worker_journey_qualification._qualification_route_supported(route)


def test_method_variant_route_rejects_unregistered_method_and_identity_changes():
    route = "diagnostic.fixed.peto.standard"
    assert not worker_journey_qualification._qualification_route_supported(
        "diagnostic.fixed.unknown.standard"
    )
    observation = _route_observation(route)

    assert qualify_worker_journey._route_observation_valid(route, observation)
    run = _records(observation["analysis_runs"])[0]
    run["method"] = "diagnostic.fixed.mh"
    assert not qualify_worker_journey._route_observation_valid(route, observation)
    run["method"] = "diagnostic.fixed.peto"
    evidence = _record(run["result_evidence"])
    evidence["metric"] = "Sens"
    assert not qualify_worker_journey._route_observation_valid(route, observation)


def test_binary_cumulative_method_variant_keeps_the_random_warmup(monkeypatch):
    calls = []
    ordering = []
    selected_form = object()
    window = SimpleNamespace(go=object(), cum_ma=object(), loo_ma=object())

    monkeypatch.setattr(
        worker_journey_qualification,
        "_prepare_worker_analysis_form",
        lambda window, action, family, metric, workflow, method: (
            object(), selected_form, 0
        ),
    )
    monkeypatch.setattr(
        worker_journey_qualification,
        "_configure_cumulative_order",
        lambda form: ordering.append(form),
    )

    def run(window, action, **kwargs):
        calls.append((action, kwargs))
        return {"analysis_id": str(len(calls)), "status": "complete"}

    monkeypatch.setattr(worker_journey_qualification, "_run_worker_analysis", run)
    route = "binary.fixed.peto.cumulative"

    records, selected, _responsive = worker_journey_qualification._run_binary_analyses(
        window,
        "cumulative",
        "binary.fixed.peto",
        qualification_route=route,
    )

    assert len(records) == 2
    assert calls[0][0] is window.go
    assert calls[0][1]["workflow"] == "standard"
    assert calls[0][1]["method"] == "binary.random"
    assert calls[1][0] is window.cum_ma
    assert calls[1][1]["workflow"] == "cumulative"
    assert calls[1][1]["method"] == "binary.fixed.peto"
    assert calls[1][1]["qualification_route"] == route
    assert calls[1][1]["prepared_form"] is selected_form
    assert ordering == [selected_form]
    assert selected is records[-1]


def test_binary_workflow_exports_the_selected_result_after_reopen(monkeypatch, tmp_path):
    opened_ids = []

    class ReopenedWindow:
        workspace = SimpleNamespace(list_analysis_drafts=lambda: [])

        def _open_saved_analysis(self, analysis_id):
            opened_ids.append(analysis_id)

    reopened = ReopenedWindow()
    monkeypatch.setattr(
        rc_metastudio,
        "main_window",
        SimpleNamespace(MainWindow=lambda: reopened),
        raising=False,
    )
    monkeypatch.setattr(rc_metastudio, "results_window", SimpleNamespace(), raising=False)
    monkeypatch.setattr(
        worker_journey_qualification,
        "_open_binary_result_project",
        lambda *_args: [{"id": "warmup"}, {"id": "selected"}],
    )
    monkeypatch.setattr(
        worker_journey_qualification,
        "_compare_binary_results",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        worker_journey_qualification,
        "_single_result_viewer",
        lambda *_args: object(),
    )
    monkeypatch.setattr(
        worker_journey_qualification,
        "_export_binary_figure",
        lambda *_args: (tmp_path / "selected.png", 123),
    )
    monkeypatch.setattr(
        worker_journey_qualification, "_require_worker_only_reopen", lambda: None
    )
    records = [
        {"analysis_id": "warmup"},
        {"analysis_id": "selected"},
    ]
    selected = records[-1]

    result = worker_journey_qualification._inspect_reopened_binary_project(
        object(), tmp_path / "saved.rcms", records, selected, "binary.cumulative", lambda *_: None
    )

    assert opened_ids == ["selected"]
    assert result[1:4] == (2, 0, tmp_path / "selected.png")
    assert result[4] == 123
    assert selected["saved_reopened"] is True


@pytest.mark.parametrize(
    ("route", "numerics"),
    [
        (
            "binary.fixed.mh.standard",
            {
                "metric": "OR",
                "pooled": {
                    "display": {"estimate": _numeric_observation(value=1.4)},
                    "study_count": _numeric_observation(value=2),
                },
                "studies": [{"label": "Alpha"}, {"label": "Beta"}],
            },
        ),
        (
            "continuous.fixed.standard",
            {
                "metric": "SMD",
                "pooled": {"estimate": _numeric_observation(value=0.42)},
                "analyzed_study_count": _numeric_observation(value=2),
                "studies": [{"label": "Alpha"}, {"label": "Beta"}],
            },
        ),
        (
            "diagnostic.fixed.peto.standard",
            {
                "metric": "DOR",
                "pooled": {
                    "display": {"estimate": _numeric_observation(value=2.1)},
                    "study_count": _numeric_observation(value=2),
                },
                "studies": [{"label": "Alpha"}, {"label": "Beta"}],
            },
        ),
    ],
)
def test_standard_method_variant_evidence_uses_saved_model_numbers(route, numerics):
    family, workflow, metric, method = qualify_worker_journey._ROUTES[route][1]
    study_rows = [{"id": 1, "name": "Alpha"}, {"id": 2, "name": "Beta"}]
    record = {
        "specification": {
            "data_type": family,
            "workflow": workflow,
            "metric": metric,
            "method": method,
        },
        "input_snapshot": {"input_snapshot": {"studies": study_rows}},
        "results": {
            "%s_numerics" % family: numerics,
            "images": {"forest": "forest.png"},
        },
    }

    evidence = worker_journey_qualification._route_result_evidence(route, record)

    assert evidence == {
        "status": "available",
        "kind": "method-variant",
        "family": family,
        "workflow": workflow,
        "metric": metric,
        "method": method,
        "estimate": {"binary": 1.4, "continuous": 0.42, "diagnostic": 2.1}[family],
        "study_count": 2,
        "input_study_count": 2,
        "study_order": ["Alpha", "Beta"],
        "figure_status": "available",
        "numeric_oracle": "observed_only_no_independent_expected_value",
    }

    record["specification"]["method"] = "binary.random"
    assert worker_journey_qualification._route_result_evidence(route, record) is None
