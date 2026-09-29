# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import FrozenInstanceError
from collections.abc import Mapping
from typing import cast

import pytest

from rc_metastudio.analysis_adapter import make_analysis_request
from rc_metastudio.analysis_snapshot import (
    BinaryCovariateInput,
    BinaryInputSnapshot,
    BinaryStudyInput,
)
from rc_metastudio.cumulative_analysis import (
    CumulativeAnalysisResult,
    CumulativeAnalysisSnapshot,
    CumulativeOrderSpec,
    CumulativeStudyOrder,
    cumulative_step_from_backend,
    freeze_cumulative_input,
    run_cumulative_analysis,
)
from rc_metastudio.sequential_step_fallback import recover_sequential_steps


def _mapping(value: object) -> Mapping[str, object]:
    assert isinstance(value, Mapping)
    assert all(isinstance(key, str) for key in value)
    return cast(Mapping[str, object], value)


def _rows(value: object) -> list[Mapping[str, object]]:
    assert isinstance(value, list)
    return [_mapping(row) for row in value]


def _snapshot(years=(2001, 1999, 1999, None)) -> BinaryInputSnapshot:
    return BinaryInputSnapshot(
        version=1,
        outcome="Outcome",
        time_point="Week 4",
        groups=("Treatment", "Control"),
        metric="OR",
        raw_counts_available=True,
        studies=tuple(
            BinaryStudyInput(
                id=index,
                name=name,
                year=years[index - 1],
                estimate=float(index) / 10,
                standard_error=0.1,
                treatment_events=index,
                treatment_total=20,
                control_events=index + 1,
                control_total=20,
            )
            for index, name in enumerate(("Alpha", "Bravo", "Charlie", "Delta"), 1)
        ),
        covariates=(BinaryCovariateInput("Age", "continuous", (70.0, 50.0, 55.0, 60.0)),),
    )


def _request():
    return make_analysis_request(
        data_type="binary",
        workflow="cumulative",
        method="binary.random",
        metric="OR",
        parameters={"measure": "OR", "rm.method": "DL", "conf.level": 95.0},
    )


def _backend_row(index: int) -> dict[str, object]:
    return {
        "res": {
            "b": index / 10,
            "ci.lb": index / 10 - 0.2,
            "ci.ub": index / 10 + 0.2,
            "se": 0.1,
            "pval": None if index == 1 else 0.2,
            "k": index,
        }
    }


def test_native_sequence_failure_retains_independent_prefixes_and_omissions():
    source = _snapshot((2001, 1999, 1998, 2000))
    sequence = freeze_cumulative_input(source, CumulativeOrderSpec("project_order", "ascending"))

    def fit(snapshot, request):
        assert request.workflow == "standard"
        ids = tuple(study.id for study in snapshot.studies)
        if ids in ((1, 2), (1, 2, 4)):
            raise RuntimeError("the model did not converge")
        return {
            "b": len(ids) / 10,
            "estimate": len(ids) / 10,
            "ci.lb": len(ids) / 10 - 0.1,
            "ci.ub": len(ids) / 10 + 0.1,
            "se": 0.05,
            "pval": 0.2,
            "k": len(ids),
        }

    cumulative = _mapping(recover_sequential_steps(sequence, _request(), fit)["cumulative_numerics"])
    steps = _rows(cumulative["steps"])
    assert [row["status"] for row in steps] == [
        "complete", "failed", "complete", "complete"
    ]
    assert steps[1]["failure_reason"] == "RuntimeError: the model did not converge"
    assert steps[-1]["is_final"] is True

    leave_one_out_request = make_analysis_request(
        data_type="binary", workflow="leave-one-out", method="binary.random",
        metric="OR", parameters={"measure": "OR", "rm.method": "DL", "conf.level": 95.0},
    )
    leave_one_out = _mapping(recover_sequential_steps(source, leave_one_out_request, fit)["leave_one_out_numerics"])
    rows = _rows(leave_one_out["rows"])
    assert [row["label"] for row in rows] == [
        "All included studies", "Omitting Alpha", "Omitting Bravo",
        "Omitting Charlie", "Omitting Delta",
    ]
    assert rows[3]["status"] == "failed"
    assert rows[3]["reason"] == "the model did not converge"
    assert source.studies[0].id == 1


def test_year_ordering_is_stable_and_reorders_covariates_with_studies():
    source = _snapshot()
    cumulative = freeze_cumulative_input(
        source,
        CumulativeOrderSpec("year", "ascending", missing_year_policy="last"),
    )

    ordered = cumulative.ordered_input_snapshot

    assert [step.study_id for step in cumulative.sequence] == [2, 3, 1, 4]
    assert [step.ordering_value for step in cumulative.sequence] == [1999, 1999, 2001, None]
    assert [step.source_order for step in cumulative.sequence] == [1, 2, 0, 3]
    assert [study.name for study in ordered.studies] == ["Bravo", "Charlie", "Alpha", "Delta"]
    assert cast(BinaryInputSnapshot, ordered).covariates[0].values == (
        50.0,
        55.0,
        70.0,
        60.0,
    )
    assert [study.id for study in source.studies] == [1, 2, 3, 4]
    assert CumulativeAnalysisSnapshot.from_mapping(cumulative.to_mapping()) == cumulative
    unordered = dict(cumulative.to_mapping())
    sequence = cast(list[Mapping[str, object]], unordered["sequence"])
    unordered["sequence"] = [sequence[1], sequence[0], *sequence[2:]]
    with pytest.raises(ValueError, match="cumulative step order|declared ordering"):
        CumulativeAnalysisSnapshot.from_mapping(unordered)
    with pytest.raises(FrozenInstanceError):
        setattr(cumulative.sequence[0], "study_id", 8)


def test_year_ordering_requires_missing_policy_only_when_years_are_missing():
    complete = freeze_cumulative_input(
        _snapshot((2001, 1999, 1998, 2000)), CumulativeOrderSpec("year", "ascending")
    )
    assert [step.study_id for step in complete.sequence] == [3, 2, 4, 1]

    with pytest.raises(ValueError, match="explicit policy"):
        freeze_cumulative_input(_snapshot(), CumulativeOrderSpec("year", "ascending"))


def test_missing_year_policy_is_independent_of_direction_and_ties_keep_project_order():
    cumulative = freeze_cumulative_input(
        _snapshot(),
        CumulativeOrderSpec("year", "descending", missing_year_policy="first"),
    )

    assert [step.study_id for step in cumulative.sequence] == [4, 1, 2, 3]
    assert cumulative.sequence[2].source_order < cumulative.sequence[3].source_order
    assert cumulative.ordering.to_mapping()["tie_policy"] == "original_project_order"


def test_preserved_project_order_supports_migrated_sequences():
    cumulative = freeze_cumulative_input(
        _snapshot(), CumulativeOrderSpec("project_order", "ascending")
    )

    assert [step.study_id for step in cumulative.sequence] == [1, 2, 3, 4]
    assert cumulative.ordered_input_snapshot == cumulative.input_snapshot
    assert CumulativeOrderSpec.from_mapping(cumulative.ordering.to_mapping()) == cumulative.ordering
    assert cumulative.to_mapping()["sequence"] == [
        step.to_mapping() for step in cumulative.sequence
    ]


def test_prefix_runner_uses_standard_fits_and_retains_failed_steps_without_substitution():
    cumulative = freeze_cumulative_input(
        _snapshot(), CumulativeOrderSpec("year", "ascending", missing_year_policy="last")
    )
    calls = []

    def analyze(prefix, request):
        calls.append(([study.id for study in prefix.studies], request.workflow))
        if len(calls) == 2:
            raise RuntimeError("single prefix failed")
        return _backend_row(len(calls))

    result = run_cumulative_analysis(cumulative, _request(), analyze)

    assert calls == [([2], "standard"), ([2, 3], "standard"), ([2, 3, 1], "standard"), ([2, 3, 1, 4], "standard")]
    assert result.status == "partial"
    assert [step.status for step in result.steps] == ["complete", "failed", "complete", "complete"]
    assert result.steps[0].p_value.status == "not_estimable"
    assert result.steps[1].failure_reason == "RuntimeError: single prefix failed"
    assert result.steps[1].estimate.value is None
    assert result.final_step.study_id == 4
    assert result.final_step.included_study_count == 4
    assert result.final_step.estimate.value == pytest.approx(0.4)
    mapped = result.to_mapping()
    mapped_steps = cast(list[Mapping[str, object]], mapped["steps"])
    assert [step["is_final"] for step in mapped_steps] == [False, False, False, True]
    assert CumulativeAnalysisResult.from_mapping(mapped) == result

    corrupted = dict(mapped)
    corrupted["steps"] = [
        *mapped_steps[:-1],
        {**mapped_steps[-1], "is_final": False},
    ]
    with pytest.raises(ValueError, match="final-step"):
        CumulativeAnalysisResult.from_mapping(corrupted)


def test_authority_parser_marks_absent_and_nonestimable_values_without_fabricating_numbers():
    order = CumulativeStudyOrder(0, 0, 1, "Alpha", 1, 1)

    absent = cumulative_step_from_backend(order, {"res": {"b": float("nan"), "k": 1}})
    assert absent.estimate.status == "not_estimable"
    assert absent.estimate.value is None
    assert absent.lower_bound.status == "not_available"
    assert absent.status == "not_estimable"

    with pytest.raises(ValueError, match="exceeds the cumulative prefix"):
        cumulative_step_from_backend(order, {"res": {"b": 0.2, "k": 2}})
