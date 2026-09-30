# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any
import zipfile

import pytest

from scripts import compare_v031_saved_journeys as compare


def _available(value: int | float) -> dict[str, object]:
    return {"reason": None, "status": "available", "value": value}


def _state(value: float) -> dict[str, object]:
    return {"state": "finite", "value": value}


def _fixture(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any], Path]:
    sample_hash = "a" * 64
    route = "binary.standard"
    route_id = "journey-binary-standard"
    analysis_id = "analysis-1"
    study_names = ["S1"]
    params = {
        "measure": "OR", "conf.level": 95, "digits": 2, "rm.method": "DL",
        "inference.method": "z", "adjust": 0.5, "to": "only0",
    }
    journey = {
        "route": route, "sample_project": "amino.rcms", "sample_project_sha256": sample_hash,
        "selected_outcome": "clinical failure", "time_point": "first", "groups": ["tx A", "tx B"],
        "input_representation": "two-arm-raw-binary-counts",
    }
    inp = {
        "study_names": study_names, "years": [2001], "g1O1": [2], "g1O2": [8],
        "g2O1": [1], "g2O2": [9],
    }
    spec: dict[str, Any] = {
        "id": route_id, "family": "binary", "metric": "OR", "method": "binary.random",
        "workflow": "standard", "input": inp, "params": params, "journey": journey,
    }
    snapshot = {
        "version": 1, "outcome": "clinical failure", "metric": "OR", "time_point": "first",
        "groups": ["tx A", "tx B"], "raw_counts_available": True, "covariates": [],
        "studies": [{
            "id": 0, "name": "S1", "year": 2001,
            "treatment_events": 2, "treatment_total": 10,
            "control_events": 1, "control_total": 10,
        }],
    }
    saved_spec = {
        "data_type": "binary", "method": "binary.random", "metric": "OR", "params": params,
        "version": 1, "workflow": "standard",
    }
    plot_summary = {
        "b": 0.3, "ci_lb": -0.4, "ci_ub": 1.0, "k": 1, "zval": 0.75,
        "pval": 0.45, "tau2": 0.0, "QE": 0.0, "QEp": 1.0, "I2": 0.0,
    }
    family_result = {
        "pooled": {
            "calculation": {
                "estimate": _available(0.3), "lower": _available(-0.4), "upper": _available(1.0),
            },
            "study_count": _available(1),
        },
        "studies": [{
            "label": "S1", "order": 0, "calculation": {"estimate": _available(0.3)},
            "weight": _available(100.0),
        }],
    }
    record: dict[str, Any] = {
        "schema_version": 1, "id": analysis_id, "input_snapshot": snapshot,
        "input_identity": compare.canonical_sha256(snapshot),
        "specification": saved_spec,
        "specification_identity": compare.canonical_sha256(saved_spec),
        "status": "complete", "warnings": [],
        "results": {
            "binary_numerics": family_result,
            "plot_render_state": {
                "analysis.standard.forest_plot.1": {
                    "renderer": "rcmetar_forest_v1", "figure_key": "analysis.standard.forest_plot.1",
                    "summary": plot_summary,
                    "studies": {"labels": ["S1, 2001"], "yi": [0.3], "vi": [0.42], "ci_lb": [-0.4], "ci_ub": [1.0]},
                    "weights": [100.0],
                },
            },
        },
    }
    unrelated = dict(record, id="not-the-route-analysis")
    project = {"schema_version": 2, "analysis_drafts": [], "dataset": {}, "saved_analyses": [unrelated, record]}
    state = {"selected_analysis": analysis_id}
    members = {"project.json": _json_bytes(project), "state.json": _json_bytes(state)}
    manifest = {
        "application": {"name": "RC MetaStudio", "version": "0.4.1"},
        "format": "rc-metastudio-project", "format_version": 2,
        "members": {
            name: {"sha256": hashlib.sha256(content).hexdigest(), "size": len(content)}
            for name, content in members.items()
        },
    }
    qualification = tmp_path / "qualification"
    qualification.mkdir()
    report_path = qualification / "worker-journey-linux-x64.json"
    run = {
        "analysis_id": analysis_id, "input_identity": record["input_identity"],
        "status": "complete", "workflow": "standard", "method": "binary.random", "metric": "OR",
    }
    report = {
        "schema_version": 2, "requested_routes": [route],
        "routes": [{
            "route": route, "status": "complete", "sample_project": r"C:\\app\\amino.rcms",
            "sample_project_sha256": sample_hash,
            "observation": {
                "route": route, "saved_analysis_status": "complete", "reopened_analysis_count": 1,
                "analysis_runs": [run],
            },
        }],
    }
    report_path.write_bytes(_json_bytes(report))
    project_path = qualification / "worker-journey-linux-x64-binary-standard.rcms"
    with zipfile.ZipFile(project_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", _json_bytes(manifest))
        for name, content in members.items():
            archive.writestr(name, content)

    statistics = {
        "b": [_state(0.3)], "se": [_state(0.4)], "ci.lb": [_state(-0.4)], "ci.ub": [_state(1.0)],
        "zval": [_state(0.75)], "pval": [_state(0.45)], "tau2": [_state(0.0)],
        "QE": [_state(0.0)], "QEp": [_state(1.0)], "df": [_state(0.0)], "k": [_state(1.0)],
        "I2": [_state(0.0)], "yi": [_state(0.3)], "vi": [_state(0.42)],
        "study_labels": study_names, "weights": [_state(100.0)],
    }
    reference: dict[str, Any] = {
        "id": route_id, "family": "binary", "metric": "OR", "method": "binary.random", "workflow": "standard",
        "request": {"family": "binary", "metric": "OR", "method": "binary.random", "workflow": "standard", "params": params},
        "input": inp, "journey": journey, "status": "success", "warnings": [],
        "eligibility": {
            "ordered_input_studies": study_names,
            "fit_study_order": study_names, "api_returned_fit_order": True,
            "excluded_studies": [], "usable_studies": 1, "usable_count_matches_input": True,
        },
        "outputs": {"statistics": statistics},
    }
    return spec, reference, qualification


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def test_saved_journey_compares_project_selected_by_route_analysis_id(tmp_path: Path) -> None:
    spec, reference, qualification = _fixture(tmp_path)

    row = compare._compare_saved_case(qualification, spec, reference)

    assert row["passed"] is True
    assert row["journey_sources"]["route_report"] == "worker-journey-linux-x64.json"
    assert row["journey_sources"]["saved_project"] == "worker-journey-linux-x64-binary-standard.rcms"
    assert row["journey_sources"]["analysis_id"] == "analysis-1"
    assert len(row["journey_sources"]["input_identity"]) == 64
    assert any(item["field"] == "statistics.se" for item in row["unavailable"])
    assert "statistics.I2" in row["compared_fields"]


@pytest.mark.parametrize(
    ("mutation", "expected_fragment"),
    [
        ("identity", "saved record input identity"),
        ("input_order", "reference ordered input studies"),
        ("order", "reference fit order"),
        ("ci", "statistics.ci.lb"),
        ("weights", "statistics.weights"),
        ("nonfinite", "statistics.yi"),
    ],
)
def test_primary_identity_order_and_numeric_drift_fail(
    tmp_path: Path, mutation: str, expected_fragment: str
) -> None:
    spec, reference, qualification = _fixture(tmp_path)
    reference = copy.deepcopy(reference)
    _mutate_case(tmp_path, qualification, reference, mutation)

    row = compare._compare_saved_case(qualification, spec, reference)

    assert row["passed"] is False
    assert any(expected_fragment in item for item in row["differences"])


def _mutate_case(tmp_path: Path, qualification: Path, reference: dict[str, Any], mutation: str) -> None:
    if mutation == "identity":
        report_path = qualification / "worker-journey-linux-x64.json"
        report = json.loads(report_path.read_text())
        report["routes"][0]["observation"]["analysis_runs"][0]["input_identity"] = "b" * 64
        report_path.write_bytes(_json_bytes(report))
        return
    match mutation:
        case "input_order":
            reference["eligibility"]["ordered_input_studies"] = ["Other"]
        case "order":
            reference["eligibility"]["fit_study_order"] = ["Other"]
        case "ci":
            reference["outputs"]["statistics"]["ci.lb"] = [_state(-0.39)]
        case "weights":
            reference["outputs"]["statistics"]["weights"] = [_state(99.0)]
        case _:
            reference["outputs"]["statistics"]["yi"] = [{"state": "nan"}]


def test_nonfinite_raw_json_and_unsafe_zip_members_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="invalid JSON constant"):
        compare._strict_json(b'{"x":NaN}', "test")

    spec, reference, qualification = _fixture(tmp_path)
    project_path = qualification / "worker-journey-linux-x64-binary-standard.rcms"
    with zipfile.ZipFile(project_path, "a") as archive:
        archive.writestr("../escape.json", b"{}")

    row = compare._compare_saved_case(qualification, spec, reference)

    assert row["passed"] is False
    assert any("unsafe or unsupported member" in item for item in row["differences"])


def test_unretained_se_is_unavailable_but_missing_primary_field_fails(tmp_path: Path) -> None:
    spec, reference, qualification = _fixture(tmp_path)
    row = compare._compare_saved_case(qualification, spec, reference)
    assert row["passed"] is True
    assert {"field": "statistics.se", "reason": "pooled standard error is not retained in this saved result family"} in row["unavailable"]

    del reference["outputs"]["statistics"]["vi"]
    failed = compare._compare_saved_case(qualification, spec, reference)
    assert failed["passed"] is False
    assert any("statistics.vi" in item for item in failed["differences"])
