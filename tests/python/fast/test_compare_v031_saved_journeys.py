# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
import zipfile

import pytest

from scripts import compare_v031_saved_journeys as compare


def _available(value: int | float) -> dict[str, object]:
    return {"reason": None, "status": "available", "value": value}


def _state(value: float) -> dict[str, object]:
    return {"state": "finite", "value": value}


def _fixture(tmp_path: Path, case_id: str = "journey-binary-standard") -> tuple[dict[str, Any], dict[str, Any], Path]:
    inventory = compare._load_case_specs(compare.CASE_SPEC)
    spec = copy.deepcopy(next(case for case in inventory["cases"] if case["id"] == case_id))
    spec["input"] = {
        key: value[:1] if isinstance(value, list) and value else value
        for key, value in spec["input"].items()
    }
    inp, journey = spec["input"], spec["journey"]
    route, sample_hash, analysis_id = journey["route"], journey["sample_project_sha256"], "analysis-1"
    study_name, year = inp["study_names"][0], inp["years"][0]
    snapshot, row = _input_snapshot(spec, study_name, year)
    representation = journey["input_representation"]
    result_estimate = inp["y"][0] if representation == "entered-continuous-effect" else 0.3
    study_se = inp["SE"][0] if representation == "entered-continuous-effect" else 0.4
    study_variance = study_se**2
    lower, upper = result_estimate - 1.96 * study_se, result_estimate + 1.96 * study_se
    family_name, family_result = _family_result(spec, row, result_estimate, study_se, lower, upper)
    params = spec["params"]
    saved_spec = {
        "data_type": spec["family"], "method": spec["method"], "metric": spec["metric"],
        "params": params, "version": 1, "workflow": spec["workflow"],
    }
    plot_summary = {
        "b": result_estimate, "ci_lb": lower, "ci_ub": upper, "k": 1,
        "zval": result_estimate / study_se, "pval": 0.45, "tau2": 0.0,
        "QE": 0.0, "QEp": 1.0, "I2": 0.0,
    }
    forest_label = f"{study_name}, {int(year)}"
    record: dict[str, Any] = {
        "schema_version": 1, "id": analysis_id, "input_snapshot": snapshot,
        "input_identity": compare.canonical_sha256(snapshot),
        "specification": saved_spec,
        "specification_identity": compare.canonical_sha256(saved_spec),
        "status": "complete", "warnings": [],
        "results": {
            family_name: family_result,
            "plot_render_state": {
                "analysis.standard.forest_plot.1": {
                    "renderer": "rcmetar_forest_v1", "figure_key": "analysis.standard.forest_plot.1",
                    "summary": plot_summary,
                    "studies": {
                        "labels": [forest_label], "yi": [result_estimate],
                        "vi": [study_variance], "ci_lb": [lower], "ci_ub": [upper],
                    },
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
    qualification.mkdir(parents=True)
    report_path = qualification / "worker-journey-linux-x64.json"
    run = {
        "analysis_id": analysis_id, "input_identity": record["input_identity"],
        "status": "complete", "workflow": spec["workflow"],
        "method": spec["method"], "metric": spec["metric"],
    }
    report = {
        "schema_version": 2, "requested_routes": [route],
        "routes": [{
            "route": route, "status": "complete",
            "sample_project": f"C:\\app\\{journey['sample_project']}",
            "sample_project_sha256": sample_hash,
            "observation": {
                "route": route, "saved_analysis_status": "complete", "reopened_analysis_count": 1,
                "analysis_runs": [run],
            },
        }],
    }
    report_path.write_bytes(_json_bytes(report))
    project_path = qualification / f"worker-journey-linux-x64-{route.replace('.', '-')}.rcms"
    with zipfile.ZipFile(project_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", _json_bytes(manifest))
        for name, content in members.items():
            archive.writestr(name, content)

    statistics = {
        "b": [_state(result_estimate)], "se": [_state(study_se)],
        "ci.lb": [_state(lower)], "ci.ub": [_state(upper)],
        "zval": [_state(result_estimate / study_se)], "pval": [_state(0.45)],
        "tau2": [_state(0.0)], "QE": [_state(0.0)], "QEp": [_state(1.0)],
        "df": [_state(0.0)], "k": [_state(1.0)], "I2": [_state(0.0)],
        "yi": [_state(result_estimate)], "vi": [_state(study_variance)],
        "study_labels": [study_name], "weights": [_state(100.0)],
    }
    study_names = inp["study_names"]
    reference: dict[str, Any] = {
        "id": spec["id"], "family": spec["family"], "metric": spec["metric"],
        "method": spec["method"], "workflow": spec["workflow"],
        "request": {key: spec[key] for key in ("family", "metric", "method", "workflow")} | {"params": params},
        "input": inp, "journey": journey, "status": "success", "warnings": [],
        "eligibility": {
            "ordered_input_studies": study_names,
            "fit_study_order": study_names, "api_returned_fit_order": True,
            "excluded_studies": [], "usable_studies": 1, "usable_count_matches_input": True,
        },
        "outputs": {"statistics": statistics},
    }
    return spec, reference, qualification


def _input_snapshot(spec: dict[str, Any], study_name: str, year: int | float) -> tuple[dict[str, Any], dict[str, Any]]:
    inp, journey = spec["input"], spec["journey"]
    representation = journey["input_representation"]
    row: dict[str, Any] = {"id": 0, "name": study_name, "year": year}
    snapshot: dict[str, Any] = {
        "version": 1, "outcome": journey["selected_outcome"], "metric": spec["metric"],
        "time_point": journey["time_point"], "groups": journey["groups"],
        "covariates": [], "studies": [row],
    }
    if representation == "two-arm-raw-binary-counts":
        row.update(
            treatment_events=inp["g1O1"][0],
            treatment_total=inp["g1O1"][0] + inp["g1O2"][0],
            control_events=inp["g2O1"][0],
            control_total=inp["g2O1"][0] + inp["g2O2"][0],
        )
        snapshot["raw_counts_available"] = True
    elif representation == "one-arm-raw-binary-counts":
        row.update(events=inp["g1O1"][0], total=inp["g1O1"][0] + inp["g1O2"][0])
        snapshot["raw_counts_available"] = True
    elif representation == "diagnostic-raw-counts-tp-fn-fp-tn":
        row.update({field.lower(): inp[field][0] for field in ("TP", "FN", "FP", "TN")})
        snapshot["input_source"] = "counts"
    elif representation == "two-arm-raw-continuous-summary":
        row.update(provenance="raw_reconstructed", arm_1=_continuous_arm(inp, "1"), arm_2=_continuous_arm(inp, "2"))
    else:
        row.update(provenance="entered", arm_1=None, arm_2=None, estimate=inp["y"][0], standard_error=inp["SE"][0])
    return snapshot, row


def _continuous_arm(inp: dict[str, Any], suffix: str) -> dict[str, float]:
    return {
        "sample_size": inp[f"N{suffix}"][0], "mean": inp[f"mean{suffix}"][0],
        "standard_deviation": inp[f"sd{suffix}"][0],
    }


def _family_result(spec: dict[str, Any], row: dict[str, Any], estimate: float, standard_error: float, lower: float, upper: float) -> tuple[str, dict[str, Any]]:
    family = spec["family"]
    if family == "continuous":
        study = {
            "order": 0, "study_id": 0, "label": row["name"], "provenance": row["provenance"],
            "estimate": estimate, "standard_error": standard_error,
            "arm_1": row.get("arm_1"), "arm_2": row.get("arm_2"),
            "entered_lower": None, "entered_upper": None, "entered_confidence_level": None,
        }
        section = {
            "version": 1, "metric": spec["metric"],
            "pooled": {"estimate": _available(estimate), "lower_bound": _available(lower), "upper_bound": _available(upper)},
            "standard_error": _available(standard_error), "p_value": _available(0.45),
            "tau_squared": _available(0.0), "analyzed_study_count": _available(1),
            "submitted_study_count": 1, "studies": [study],
        }
        return "continuous_numerics", section
    if family == "diagnostic":
        study = {
            "label": row["name"], "order": 0,
            **{field: row[field.lower()] for field in ("TP", "FN", "FP", "TN")},
            "calculation": {"estimate": _available(estimate)},
            "variance": _available(standard_error**2), "weight_fraction": _available(1.0),
        }
        section = {
            "pooled": {
                "calculation": {"estimate": _available(estimate), "lower": _available(lower), "upper": _available(upper)},
                "standard_error": _available(standard_error), "study_count": _available(1),
                "p_value": _available(0.45), "tau_squared": _available(0.0),
                "q": _available(0.0), "q_p_value": _available(1.0),
                "q_df": {"reason": "Q degrees of freedom were unavailable", "status": "not_available", "value": None},
                "i_squared": _available(0.0),
            },
            "studies": [study],
        }
        return "diagnostic_numerics", section
    study = {"label": row["name"], "order": 0, "calculation": {"estimate": _available(estimate)}}
    pooled = {
        "calculation": {"estimate": _available(estimate), "lower": _available(lower), "upper": _available(upper)},
        "study_count": _available(1),
    }
    if spec["metric"] == "PLO":
        study.update(events=row["events"], total=row["total"])
        return "binary_proportion_numerics", {"pooled": pooled, "studies": [study]}
    pooled["p_value"] = _available(0.45)
    study.update(
        treatment_events=row["treatment_events"], treatment_total=row["treatment_total"],
        control_events=row["control_events"], control_total=row["control_total"],
        weight=_available(100.0),
    )
    return "binary_numerics", {"pooled": pooled, "studies": [study]}


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


@pytest.mark.parametrize("case_id", compare.JOURNEY_IDS)
def test_saved_journey_numeric_shapes_cover_all_routes_and_families(tmp_path: Path, case_id: str) -> None:
    spec, reference, qualification = _fixture(tmp_path, case_id)

    row = compare._compare_saved_case(qualification, spec, reference)

    assert row["passed"] is True, row["differences"]
    if spec["family"] == "continuous":
        assert "family_table.statistics.se" in row["compared_fields"]
        assert "statistics.vi vs saved continuous standard error squared" in row["compared_fields"]
    elif spec["family"] == "diagnostic":
        assert "statistics.vi vs saved diagnostic variance" in row["compared_fields"]
        assert "statistics.weights vs saved diagnostic weight fraction percent" in row["compared_fields"]
        assert "family_table.statistics.QE" in row["compared_fields"]
    elif spec["metric"] == "OR":
        assert "family_table.statistics.pval" in row["compared_fields"]
    else:
        assert any(item["field"] == "family_table.statistics.pval" for item in row["unavailable"])


def test_forest_label_projection_adds_year_once_and_truncates_like_rcmetar() -> None:
    long_name = "A" * 80
    long_label = f"{long_name}, 1990"
    snapshot = {
        "studies": [
            {"name": "Study 1993", "year": 1993},
            {"name": "Unknown year", "year": 0},
            {"name": long_name, "year": 1990},
        ],
    }

    labels = compare._forest_labels(snapshot)

    assert labels == ["Study 1993", "Unknown year", f"{long_label[:56]}...{long_label[-13:]}"]


@pytest.mark.parametrize(
    ("case_id", "path", "value", "field"),
    [
        ("journey-binary-standard", ("binary_numerics", "pooled", "p_value"), 0.4, "pval"),
        ("journey-continuous-standard", ("continuous_numerics", "p_value"), 0.4, "pval"),
        ("journey-continuous-standard", ("continuous_numerics", "tau_squared"), 0.1, "tau2"),
        ("journey-diagnostic-standard", ("diagnostic_numerics", "pooled", "standard_error"), 0.6, "se"),
        ("journey-diagnostic-standard", ("diagnostic_numerics", "pooled", "p_value"), 0.4, "pval"),
        ("journey-diagnostic-standard", ("diagnostic_numerics", "pooled", "tau_squared"), 0.1, "tau2"),
        ("journey-diagnostic-standard", ("diagnostic_numerics", "pooled", "q"), 0.1, "QE"),
        ("journey-diagnostic-standard", ("diagnostic_numerics", "pooled", "q_p_value"), 0.1, "QEp"),
        ("journey-diagnostic-standard", ("diagnostic_numerics", "pooled", "i_squared"), 10.0, "I2"),
    ],
)
def test_typed_pooled_values_are_compared_separately_from_forest_summary(
    tmp_path: Path, case_id: str, path: tuple[str, ...], value: float, field: str,
) -> None:
    spec, reference, qualification = _fixture(tmp_path, case_id)
    _mutate_saved_record(qualification, spec, lambda record: _set_numeric_value(record, path, value))

    row = compare._compare_saved_case(qualification, spec, reference)

    assert row["passed"] is False
    assert f"family_table.statistics.{field}" in row["compared_fields"]
    assert any(f"family_table.statistics.{field}" in item for item in row["differences"])


def test_diagnostic_q_degrees_of_freedom_are_not_used_as_fit_degrees_of_freedom(
    tmp_path: Path,
) -> None:
    spec, reference, qualification = _fixture(tmp_path, "journey-diagnostic-standard")
    _mutate_saved_record(
        qualification, spec,
        lambda record: record["results"]["diagnostic_numerics"]["pooled"].update(q_df=_available(1)),
    )

    row = compare._compare_saved_case(qualification, spec, reference)

    assert row["passed"] is True, row["differences"]
    assert "statistics.df" not in row["compared_fields"]
    assert any(item["field"] == "statistics.df" for item in row["unavailable"])


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


def test_cli_writes_failure_report_when_reference_cannot_be_loaded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    qualification = tmp_path / "qualification"
    qualification.mkdir()
    output = qualification / "journey-comparison.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "compare_v031_saved_journeys.py",
            "--qualification-dir", str(qualification),
            "--reference", str(tmp_path / "missing-reference.json"),
            "--output", str(output),
        ],
    )

    status = compare.main()

    assert status == 2
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is False


def test_unretained_se_is_unavailable_but_missing_primary_field_fails(tmp_path: Path) -> None:
    spec, reference, qualification = _fixture(tmp_path)
    row = compare._compare_saved_case(qualification, spec, reference)
    assert row["passed"] is True
    assert {"field": "statistics.se", "reason": "pooled standard error is not retained in this saved result family"} in row["unavailable"]

    del reference["outputs"]["statistics"]["vi"]
    failed = compare._compare_saved_case(qualification, spec, reference)
    assert failed["passed"] is False
    assert any("statistics.vi" in item for item in failed["differences"])


@pytest.mark.parametrize("case_id", ("journey-continuous-standard", "journey-continuous-entered-effect"))
def test_retained_continuous_pooled_and_study_se_are_compared(tmp_path: Path, case_id: str) -> None:
    spec, reference, qualification = _fixture(tmp_path, case_id)
    _mutate_saved_record(
        qualification, spec,
        lambda record: record["results"]["continuous_numerics"]["standard_error"].update(value=0.6),
    )

    row = compare._compare_saved_case(qualification, spec, reference)

    assert row["passed"] is False
    assert any("family_table.statistics.se" in item for item in row["differences"])

    spec, reference, qualification = _fixture(tmp_path / "study-se", case_id)
    _mutate_saved_record(
        qualification, spec,
        lambda record: record["results"]["continuous_numerics"]["studies"][0].update(standard_error=0.6),
    )
    row = compare._compare_saved_case(qualification, spec, reference)
    assert row["passed"] is False
    assert any("continuous standard error squared" in item for item in row["differences"])


@pytest.mark.parametrize(
    ("field", "difference"),
    [
        ("variance", "saved diagnostic variance"),
        ("weight_fraction", "saved diagnostic weight fraction percent"),
    ],
)
def test_retained_diagnostic_variance_and_weight_fraction_are_compared(
    tmp_path: Path, field: str, difference: str,
) -> None:
    spec, reference, qualification = _fixture(tmp_path, "journey-diagnostic-standard")
    _mutate_saved_record(
        qualification, spec,
        lambda record: record["results"]["diagnostic_numerics"]["studies"][0][field].update(value=0.5),
    )

    row = compare._compare_saved_case(qualification, spec, reference)

    assert row["passed"] is False
    assert any(difference in item for item in row["differences"])


def test_family_table_count_forest_count_and_forest_labels_are_independent(
    tmp_path: Path,
) -> None:
    spec, reference, qualification = _fixture(tmp_path, "journey-continuous-standard")
    _mutate_saved_record(
        qualification, spec,
        lambda record: record["results"]["continuous_numerics"]["analyzed_study_count"].update(value=2),
    )
    row = compare._compare_saved_case(qualification, spec, reference)
    assert any("statistics.k vs saved numeric result" in item for item in row["differences"])

    spec, reference, qualification = _fixture(tmp_path / "forest-k", "journey-continuous-standard")
    _mutate_saved_record(
        qualification, spec,
        lambda record: record["results"]["plot_render_state"]["analysis.standard.forest_plot.1"]["summary"].update(k=2),
    )
    row = compare._compare_saved_case(qualification, spec, reference)
    assert any("statistics.k vs saved forest summary" in item for item in row["differences"])

    spec, reference, qualification = _fixture(tmp_path / "forest-label", "journey-continuous-standard")
    _mutate_saved_record(
        qualification, spec,
        lambda record: record["results"]["plot_render_state"]["analysis.standard.forest_plot.1"]["studies"].update(labels=["wrong label"]),
    )
    row = compare._compare_saved_case(qualification, spec, reference)
    assert any("saved forest labels" in item for item in row["differences"])

    spec, reference, qualification = _fixture(tmp_path / "table-label", "journey-diagnostic-standard")
    _mutate_saved_record(
        qualification, spec,
        lambda record: record["results"]["diagnostic_numerics"]["studies"][0].update(label="wrong label"),
    )
    row = compare._compare_saved_case(qualification, spec, reference)
    assert any("saved numeric study labels" in item for item in row["differences"])


def _mutate_saved_record(
    qualification: Path, spec: dict[str, Any], change: Any,
) -> None:
    path = qualification / f"worker-journey-linux-x64-{spec['journey']['route'].replace('.', '-')}.rcms"
    with zipfile.ZipFile(path) as archive:
        members = {entry.filename: archive.read(entry.filename) for entry in archive.infolist()}
    project = json.loads(members["project.json"])
    record = next(item for item in project["saved_analyses"] if item["id"] == "analysis-1")
    change(record)
    members["project.json"] = _json_bytes(project)
    manifest = json.loads(members["manifest.json"])
    manifest["members"] = {
        name: {"sha256": hashlib.sha256(content).hexdigest(), "size": len(content)}
        for name, content in members.items()
        if name != "manifest.json"
    }
    members["manifest.json"] = _json_bytes(manifest)
    temporary = path.with_suffix(".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    temporary.replace(path)


def _set_numeric_value(record: dict[str, Any], path: tuple[str, ...], value: float) -> None:
    container: Any = record["results"]
    for key in path[:-1]:
        container = container[key]
    container[path[-1]]["value"] = value
