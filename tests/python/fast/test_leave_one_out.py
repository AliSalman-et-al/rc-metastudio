# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import cast
import zipfile

import pytest

from rc_metastudio.leave_one_out import (
    LeaveOneOutEstimate,
    LeaveOneOutNumber,
    NamedHeterogeneity,
    run_leave_one_out,
)


@dataclass(frozen=True)
class _Study:
    id: int
    name: str


@dataclass(frozen=True)
class _Covariate:
    name: str
    values: tuple[int, ...]


@dataclass(frozen=True)
class _Snapshot:
    version: int
    outcome: str
    time_point: str
    metric: str
    studies: tuple[_Study, ...]
    covariates: tuple[_Covariate, ...]


def _snapshot() -> _Snapshot:
    return _Snapshot(
        1,
        "Mortality",
        "12 months",
        "OR",
        (_Study(11, "Study A"), _Study(12, "Study B"), _Study(13, "Study C")),
        (_Covariate("Age", (41, 52, 63)),),
    )


def _estimate(value: float, *, scale: str = "log_odds_ratio") -> LeaveOneOutEstimate:
    return LeaveOneOutEstimate(
        effect_scale=scale,
        estimate=LeaveOneOutNumber.available(value),
        lower_bound=LeaveOneOutNumber.available(value - 0.2),
        upper_bound=LeaveOneOutNumber.available(value + 0.2),
        heterogeneity=(NamedHeterogeneity("tau_squared", 0.04),),
    )


def test_report_starts_with_full_baseline_and_labels_each_omission_on_named_scale():
    estimates = {frozenset({11, 12, 13}): 0.5, frozenset({12, 13}): 0.6,
                 frozenset({11, 13}): 0.3, frozenset({11, 12}): 0.45}
    report = run_leave_one_out(
        _snapshot(),
        lambda subset: _estimate(estimates[frozenset(s.id for s in subset.studies)]),
        method="binary.random",
        data_type="binary",
        effect_scale="log_odds_ratio",
    )

    assert [row.label for row in report.rows] == [
        "All included studies",
        "Omitting Study A",
        "Omitting Study B",
        "Omitting Study C",
    ]
    assert [row.remaining_study_count for row in report.rows] == [3, 2, 2, 2]
    assert [row.change_from_baseline.value for row in report.rows] == pytest.approx(
        [0, 0.1, -0.2, -0.05]
    )
    assert all(row.change_scale == "log_odds_ratio" for row in report.rows)
    assert report.rows[0].heterogeneity[0] == NamedHeterogeneity("tau_squared", 0.04)
    raw_rows = report.to_mapping()["rows"]
    assert isinstance(raw_rows, list)
    assert isinstance(raw_rows[0], dict)
    assert cast(dict[str, object], raw_rows[0])["label"] == "All included studies"


def test_omissions_receive_aligned_immutable_snapshots_and_original_is_preserved():
    original = _snapshot()
    seen = []

    def fit(subset):
        seen.append(subset)
        return _estimate(0.25)

    report = run_leave_one_out(
        original, fit, method="binary.random", data_type="binary", effect_scale="log_odds_ratio"
    )

    assert seen[0] is original
    assert [tuple(study.id for study in subset.studies) for subset in seen[1:]] == [
        (12, 13),
        (11, 13),
        (11, 12),
    ]
    assert [subset.covariates[0].values for subset in seen[1:]] == [
        (52, 63),
        (41, 63),
        (41, 52),
    ]
    assert original.studies == (_Study(11, "Study A"), _Study(12, "Study B"), _Study(13, "Study C"))
    assert original.covariates[0].values == (41, 52, 63)
    assert report.rows[1].study_id == 11


def test_failed_and_non_estimable_omissions_remain_visible_with_reasons():
    def fit(subset):
        if subset.studies[0].id == 12 and len(subset.studies) == 2:
            raise RuntimeError("metafor could not fit the subset")
        if len(subset.studies) == 2:
            return LeaveOneOutEstimate.not_estimable(
                "No pooled estimate was returned.", effect_scale="log_odds_ratio"
            )
        return _estimate(0.5)

    report = run_leave_one_out(
        _snapshot(), fit, method="binary.random", data_type="binary", effect_scale="log_odds_ratio"
    )

    failed, not_estimable = report.rows[1:3]
    assert (failed.status, failed.reason) == ("failed", "metafor could not fit the subset")
    assert failed.estimate.status == "not_available"
    assert not_estimable.status == "not_estimable"
    assert not_estimable.reason == "No pooled estimate was returned."
    assert not_estimable.change_from_baseline.reason is not None
    assert len(report.rows) == 4


def test_single_study_keeps_non_estimable_empty_omission_without_calling_backend():
    original = _snapshot()
    one_study = _Snapshot(
        original.version,
        original.outcome,
        original.time_point,
        original.metric,
        original.studies[:1],
        (_Covariate("Age", original.covariates[0].values[:1]),),
    )
    calls = []

    def fit(subset):
        calls.append(subset)
        return _estimate(0.5)

    report = run_leave_one_out(
        one_study, fit, method="binary.random", data_type="binary", effect_scale="log_odds_ratio"
    )

    assert len(calls) == 1
    assert report.rows[1].label == "Omitting Study A"
    assert report.rows[1].remaining_study_count == 0
    assert report.rows[1].status == "not_estimable"
    assert report.rows[1].reason is not None
    assert "No studies remain" in report.rows[1].reason


def test_failed_baseline_does_not_hide_successful_omissions():
    def fit(subset):
        if len(subset.studies) == 3:
            raise RuntimeError("full-sample model did not converge")
        return _estimate(0.4)

    report = run_leave_one_out(
        _snapshot(),
        fit,
        method="binary.random",
        data_type="binary",
        effect_scale="log_odds_ratio",
    )

    assert report.rows[0].status == "failed"
    assert report.rows[0].reason == "full-sample model did not converge"
    assert all(row.status == "available" for row in report.rows[1:])
    assert all(
        row.change_from_baseline.status == "not_available" for row in report.rows[1:]
    )


def test_report_is_json_safe_and_identifies_direction_and_row_contract():
    report = run_leave_one_out(
        _snapshot(),
        lambda _subset: _estimate(0.5),
        method="binary.random",
        data_type="binary",
        effect_scale="log_odds_ratio",
    )

    wire = report.to_mapping()
    encoded = json.dumps(wire, allow_nan=False)
    decoded = json.loads(encoded)
    assert decoded["change_convention"] == "omitted_minus_baseline"
    assert [row["label"] for row in decoded["rows"]] == [
        "All included studies",
        "Omitting Study A",
        "Omitting Study B",
        "Omitting Study C",
    ]


def test_non_finite_authority_values_are_rejected():
    with pytest.raises(ValueError, match="finite"):
        LeaveOneOutNumber.available(float("inf"))

    with pytest.raises(ValueError, match="finite"):
        NamedHeterogeneity("i_squared", float("nan"))


def test_continuous_leave_one_out_matches_pinned_metafor_authority_values():
    from rc_metastudio import r_bridge
    from rc_metastudio.continuous_analysis_snapshot import (
        ContinuousInputSnapshot,
        ContinuousStudyInput,
    )

    try:
        loader = r_bridge.RLibraryLoader()
        loader.load_metafor()
        loader.load_rcmetar()
    except Exception as error:
        pytest.skip(f"R authority is unavailable: {error}")

    project_path = Path(__file__).resolve().parents[3] / "sample_projects/continuous.rcms"
    with zipfile.ZipFile(project_path) as archive:
        project = json.loads(archive.read("project.json"))
    dataset = project["dataset"]
    studies = []
    for source in dataset["studies"]:
        unit = next(
            item
            for item in source["analysis_units"]
            if item["outcome"] == "blood pressure" and item["follow_up"] == "first"
        )
        entered = unit["entered_effects"]["SMD"]["tx A-tx B"]
        studies.append(
            ContinuousStudyInput(
                source["id"],
                source["name"],
                source["year"],
                "entered",
                entered["est"],
                entered["SE"],
                None,
                None,
                None,
                None,
                None,
            )
        )
    snapshot = ContinuousInputSnapshot(
        1,
        "blood pressure",
        "first",
        ("tx A", "tx B"),
        "SMD",
        None,
        None,
        tuple(studies),
        (),
    )

    def fit(subset):
        raw = r_bridge.execute_r_function(
            "rma.uni",
            yi=r_bridge._r_numeric_vector([study.estimate for study in subset.studies]),
            sei=r_bridge._r_numeric_vector(
                [study.standard_error for study in subset.studies]
            ),
            method="DL",
            test="z",
            level=95,
        )
        model = r_bridge.r_object_to_python(raw)
        return LeaveOneOutEstimate(
            effect_scale="standard_deviation_units",
            estimate=LeaveOneOutNumber.available(model["b"]),
            lower_bound=LeaveOneOutNumber.available(model["ci.lb"]),
            upper_bound=LeaveOneOutNumber.available(model["ci.ub"]),
            heterogeneity=(
                NamedHeterogeneity("tau_squared", model["tau2"]),
                NamedHeterogeneity("i_squared", model["I2"]),
            ),
        )

    report = run_leave_one_out(
        snapshot,
        fit,
        method="continuous.random",
        data_type="continuous",
        effect_scale="standard_deviation_units",
    )
    contract_path = (
        Path(__file__).resolve().parents[2]
        / "analysis_regression/baseline/numeric-contract.json"
    )
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    case = next(
        item
        for item in contract["cases"]
        if item["id"] == "continuous-leave-one-out"
    )
    expected = case["sections"]["Leave-one-out Summary"]

    keys = ("overall", "carroll", "grant", "peck", "donat", "stewart", "young")
    for row, key in zip(report.rows, keys, strict=True):
        prefix = "model.overall." if key == "overall" else f"model.without_{key}."
        assert row.estimate.value == pytest.approx(expected[prefix + "estimate"], abs=0.001)
        assert row.lower_bound.value == pytest.approx(
            expected[prefix + "lower_bound"], abs=0.001
        )
        assert row.upper_bound.value == pytest.approx(
            expected[prefix + "upper_bound"], abs=0.001
        )
