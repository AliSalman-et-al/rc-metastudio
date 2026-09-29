# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Subgroup missing-data policy and RCMetaR result contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast
import zipfile

import pytest

from rc_metastudio.analysis_results import AnalysisResult, ResultSection
from rc_metastudio.analysis_snapshot import (
    BinaryCovariateInput,
    BinaryInputSnapshot,
    BinaryStudyInput,
)
from rc_metastudio.continuous_analysis_snapshot import (
    ContinuousCovariateInput,
    ContinuousInputSnapshot,
    ContinuousStudyInput,
)
from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot
from rc_metastudio.subgroup_analysis import (
    MissingCovariatePolicy,
    create_subgroup_plan,
    create_subgroup_request,
    parse_subgroup_result,
    prepare_subgroup_snapshot,
    render_subgroup_result,
    subgroup_figure_available,
)


ROOT = Path(__file__).resolve().parents[3]
BASELINE = ROOT / "tests" / "analysis_regression" / "baseline"


def _binary_snapshot(values: list[str | int | None]) -> BinaryInputSnapshot:
    studies = tuple(
        BinaryStudyInput(index, f"Study {index}", 2000 + index, None, None, None, None, None, None)
        for index in range(1, len(values) + 1)
    )
    return BinaryInputSnapshot(
        version=1,
        outcome="Outcome",
        time_point="12 months",
        groups=("Treatment", "Control"),
        metric="OR",
        raw_counts_available=False,
        studies=studies,
        covariates=(
            BinaryCovariateInput("group", "factor", tuple(values)),
            BinaryCovariateInput("age", "continuous", tuple(range(len(values)))),
        ),
    )


def _continuous_snapshot(values: list[str | int | None]) -> ContinuousInputSnapshot:
    studies = tuple(
        ContinuousStudyInput(
            study_id=index,
            name=f"Study {index}",
            year=2000 + index,
            provenance="entered",
            estimate=0.1,
            standard_error=0.2,
            arm_1=None,
            arm_2=None,
        )
        for index in range(1, len(values) + 1)
    )
    return ContinuousInputSnapshot(
        version=1,
        outcome="Outcome",
        follow_up="12 months",
        groups=("Treatment", "Control"),
        metric="SMD",
        outcome_subtype=None,
        outcome_unit=None,
        studies=studies,
        covariates=(ContinuousCovariateInput("group", "factor", tuple(values)),),
    )


def _capture_and_contract(case_id: str) -> tuple[dict[str, object], dict[str, float]]:
    with zipfile.ZipFile(BASELINE / "observed-golden-baseline.zip") as archive:
        capture = cast(dict[str, object], json.loads(archive.read(f"captures/{case_id}.json")))
    contract = cast(dict[str, object], json.loads((BASELINE / "numeric-contract.json").read_text()))
    cases = cast(list[dict[str, object]], contract["cases"])
    case = next(row for row in cases if row["id"] == case_id)
    sections = cast(dict[str, object], case["sections"])
    return capture, cast(dict[str, float], sections["Subgroup Summary"])


def _assert_close(actual: float | None, expected: float) -> None:
    assert actual is not None
    assert abs(actual - expected) <= 0.001 + 1e-9 * abs(expected)


def test_exclude_policy_records_missing_studies_and_keeps_rows_aligned():
    snapshot = _binary_snapshot(["early", None, "late", "", "early"])

    plan = create_subgroup_plan(snapshot, "group", missing_policy="exclude")
    restored = type(plan).from_mapping(plan.to_mapping())
    prepared = cast(BinaryInputSnapshot, prepare_subgroup_snapshot(snapshot, restored))

    assert plan == restored
    assert plan.included_count == 3
    assert plan.missing_count == 2
    assert plan.excluded_count == 2
    assert [row.status for row in plan.assignments] == [
        "included", "excluded_missing", "included", "excluded_missing", "included"
    ]
    assert [study.id for study in prepared.studies] == [1, 3, 5]
    assert prepared.covariates[0].values == ("early", "late", "early")
    assert prepared.covariates[1].values == (0, 2, 4)
    assert snapshot.covariates[0].values == ("early", None, "late", "", "early")


def test_missing_category_is_collision_free_and_serialized():
    snapshot = _binary_snapshot(["__RCMS_MISSING__", "", "late", None, "early"])

    plan = create_subgroup_plan(snapshot, "group", missing_policy="missing_category")
    prepared = cast(
        BinaryInputSnapshot,
        prepare_subgroup_snapshot(snapshot, type(plan).from_mapping(plan.to_mapping())),
    )

    missing_level = next(level for level in plan.levels if level.is_missing_category)
    assert missing_level.label == "Missing values"
    assert missing_level.backend_value == "__RCMS_MISSING___2"
    assert plan.included_count == 5
    assert plan.missing_count == 2
    assert plan.excluded_count == 0
    assert prepared.covariates[0].values == (
        "__RCMS_MISSING__", "__RCMS_MISSING___2", "late", "__RCMS_MISSING___2", "early"
    )


def test_plan_requires_a_factor_and_two_nonempty_levels():
    with pytest.raises(ValueError, match="categorical"):
        create_subgroup_plan(_binary_snapshot([1, 2]), "age", missing_policy="exclude")
    with pytest.raises(ValueError, match="at least two"):
        create_subgroup_plan(_binary_snapshot(["early", None]), "group", missing_policy="exclude")
    with pytest.raises(ValueError, match="whether"):
        create_subgroup_plan(
            _binary_snapshot(["early", "late"]),
            "group",
            missing_policy=cast(MissingCovariatePolicy, None),
        )


def test_continuous_subgroup_request_uses_frozen_factor_choice():
    snapshot = _continuous_snapshot(["control", "treated", "control"])
    plan = create_subgroup_plan(snapshot, "group", missing_policy="exclude")

    request = create_subgroup_request(
        snapshot,
        plan,
        method="continuous.random",
        parameters={"measure": "SMD", "rm.method": "DL"},
    )

    assert request.workflow == "subgroup"
    assert dict((parameter.name, parameter.value) for parameter in request.parameters)["cov_name"] == "group"
    assert prepare_subgroup_snapshot(snapshot, plan).studies == snapshot.studies


def test_diagnostic_subgroup_is_rejected_by_pinned_authority_matrix():
    diagnostic = DiagnosticInputSnapshot.from_mapping(
        {
            "version": 1,
            "outcome": "Disease",
            "time_point": "12 months",
            "groups": ["Diagnostic cohort"],
            "metric": "DOR",
            "input_source": "counts",
            "confidence_level": 95.0,
            "studies": [
                {
                    "id": 1, "name": "Study 1", "year": 2020,
                    "tp": 4, "fn": 1, "fp": 2, "tn": 5,
                    "estimate": None, "standard_error": None,
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="does not support diagnostic subgroup"):
        create_subgroup_plan(diagnostic, "group", missing_policy="exclude")


@pytest.mark.parametrize(
    ("case_id", "snapshot_factory", "expected_levels"),
    [
        ("amino-binary-subgroup", _binary_snapshot, ("early", "late")),
        ("continuous-subgroup", _continuous_snapshot, ("early", "late")),
    ],
)
def test_subgroup_summary_matches_pinned_numeric_contract(
    case_id, snapshot_factory, expected_levels
):
    capture, expected = _capture_and_contract(case_id)
    count = 19 if case_id == "amino-binary-subgroup" else 15
    values = [expected_levels[index % 2] for index in range(count)]
    snapshot = snapshot_factory(values)
    plan = create_subgroup_plan(snapshot, "group", missing_policy="exclude")
    texts = cast(dict[str, str], capture["texts"])
    result = parse_subgroup_result(
        texts["Subgroup Summary"], plan
    )
    actual_result = AnalysisResult(
        version=1,
        texts={},
        images={},
        display_images={},
        image_var_names={},
        image_params_paths={},
        image_order=(),
        plot_capabilities={},
        sections=(
            ResultSection(
                semantic_id="subgroup.forest",
                kind="image",
                order=0,
                title="Subgroups Forest Plot",
                value="plot.svg",
                source_key="Subgroups Forest Plot",
                plot_kind="subgroup_forest",
            ),
        ),
    )

    for level in result.levels:
        contract_prefix = f"model.subgroup_{level.label}"
        _assert_close(level.estimate, expected[f"{contract_prefix}.estimate"])
        _assert_close(level.lower_bound, expected[f"{contract_prefix}.lower_bound"])
        _assert_close(level.upper_bound, expected[f"{contract_prefix}.upper_bound"])
        _assert_close(level.standard_error, expected[f"{contract_prefix}.standard_error"])
        _assert_close(level.p_value, expected[f"{contract_prefix}.p_value"])
        if case_id.startswith("amino"):
            _assert_close(level.z_value, expected[f"{contract_prefix}.z_value"])
    _assert_close(result.overall.estimate, expected["model.overall.estimate"])
    _assert_close(result.overall.lower_bound, expected["model.overall.lower_bound"])
    _assert_close(result.overall.upper_bound, expected["model.overall.upper_bound"])
    _assert_close(result.overall.standard_error, expected["model.overall.standard_error"])
    _assert_close(result.overall.p_value, expected["model.overall.p_value"])
    assert result.between_subgroup_test.status == "not_calculated"
    assert result.between_subgroup_test.reason is not None
    assert "no between-subgroup test" in result.between_subgroup_test.reason
    assert subgroup_figure_available(actual_result)
    saved_result = result.to_mapping()
    assert saved_result["missing_policy"] == "exclude"
    saved_test = cast(dict[str, object], saved_result["between_subgroup_test"])
    assert saved_test["status"] == "not_calculated"

    if case_id.startswith("amino"):
        for heterogeneity in result.heterogeneity:
            key = "overall" if heterogeneity.label == "Overall" else f"subgroup_{heterogeneity.label}"
            for field, expected_field in (
                ("q", "q"),
                ("degrees_of_freedom", "df"),
                ("p_value", "p_value"),
                ("i_squared", "i_squared"),
            ):
                _assert_close(
                    getattr(heterogeneity, field),
                    expected[f"heterogeneity.{key}.{expected_field}"],
                )
    else:
        assert result.overall.p_value_text == "< 0.001"
        assert result.heterogeneity == ()


def test_between_subgroup_test_is_used_only_when_authority_returns_it():
    plan = create_subgroup_plan(_binary_snapshot(["a", "b"]), "group", missing_policy="exclude")
    text = "Model Results\n Subgroups Studies Estimate Lower Upper Std p z\n Subgroup a 1 1.2 0.2 2.2 0.4 0.3 0.5\n Subgroup b 1 1.3 0.3 2.3 0.4 0.4 0.2\n Overall 2 1.2 0.5 2.0 0.3 0.2 0.4"

    result = parse_subgroup_result(
        text,
        plan,
        between_subgroup_test={
            "statistic": 2.4, "degrees_of_freedom": 1, "p_value": 0.12
        },
    )

    assert result.between_subgroup_test.status == "available"
    assert result.between_subgroup_test.statistic == 2.4
    with pytest.raises(ValueError, match="must return statistic"):
        parse_subgroup_result(text, plan, between_subgroup_test={"p_value": 0.12})


def test_saved_subgroup_summary_states_missing_policy_counts_and_uncalculated_test():
    plan = create_subgroup_plan(
        _binary_snapshot(["early", None, "late"]),
        "group",
        missing_policy="exclude",
    )
    text = (
        "Model Results\n Subgroups Studies Estimate Lower Upper Std p z\n"
        " Subgroup early 1 1.2 0.2 2.2 0.4 0.3 0.5\n"
        " Subgroup late 1 1.3 0.3 2.3 0.4 0.4 0.2\n"
        " Overall 2 1.2 0.5 2.0 0.3 0.2 0.4"
    )

    result = parse_subgroup_result(text, plan)
    rendered = render_subgroup_result(result, plan)

    assert "Missing-value policy: exclude studies with missing values" in rendered
    assert "Studies: 2 analyzed; 1 missing; 1 excluded." in rendered
    assert "early (n=1): estimate 1.2 [0.2, 2.2], p 0.3." in rendered
    assert "Between-subgroup test: Not calculated." in rendered
    assert "it returned no between-subgroup test" in rendered
    assert "Within-subgroup p-values do not test differences" in rendered
    assert "Excluded for missing subgroup values: Study 2" in rendered


def test_missing_category_summary_is_json_safe_and_preserves_frozen_input():
    snapshot = _binary_snapshot(["north", "", "south", None])
    plan = create_subgroup_plan(snapshot, "group", missing_policy="missing_category")
    prepared = cast(BinaryInputSnapshot, prepare_subgroup_snapshot(snapshot, plan))
    missing_level = next(level for level in plan.levels if level.is_missing_category)
    text = (
        "Model Results\n Subgroups Studies Estimate Lower Upper Std p z\n"
        " Subgroup north 1 1.2 0.2 2.2 0.4 0.3 0.5\n"
        " Subgroup south 1 1.3 0.3 2.3 0.4 0.4 0.2\n"
        f" Subgroup {missing_level.backend_value} 2 1.4 0.4 2.4 0.4 0.2 0.6\n"
        " Overall 4 1.3 0.6 2.1 0.3 0.1 0.7"
    )

    result = parse_subgroup_result(text, plan)
    portable = json.loads(json.dumps(result.to_mapping(), allow_nan=False))
    rendered = render_subgroup_result(result, plan)

    assert result.included_count == 4
    assert result.missing_count == 2
    assert result.excluded_count == 0
    assert next(row for row in result.levels if row.label == "Missing values").included_count == 2
    assert portable["missing_policy"] == "missing_category"
    assert portable["included_count"] == 4
    assert "Missing values (n=2): estimate 1.4 [0.4, 2.4], p 0.2." in rendered
    assert "Studies: 4 analyzed; 2 missing; 0 excluded." in rendered
    assert "Assigned to Missing values subgroup: Study 2, Study 4" in rendered
    assert prepared.covariates[0].values == (
        "north", "__RCMS_MISSING__", "south", "__RCMS_MISSING__"
    )
    assert snapshot.covariates[0].values == ("north", "", "south", None)


def test_result_parser_rejects_counts_that_disagree_with_frozen_policy():
    plan = create_subgroup_plan(_binary_snapshot(["a", "b"]), "group", missing_policy="exclude")
    text = "Model Results\n Subgroups Studies Estimate Lower Upper Std p z\n Subgroup a 2 1.2 0.2 2.2 0.4 0.3 0.5\n Subgroup b 1 1.3 0.3 2.3 0.4 0.4 0.2\n Overall 3 1.2 0.5 2.0 0.3 0.2 0.4"

    with pytest.raises(ValueError, match="frozen plan includes"):
        parse_subgroup_result(text, plan)
