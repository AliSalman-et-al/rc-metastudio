# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import cast

import pytest

from rc_metastudio.analysis_results import AnalysisResult, parse_analysis_result
from rc_metastudio.dataset_table_model import DatasetTableModel
from rc_metastudio.analysis_snapshot import BinaryInputSnapshot, BinaryStudyInput
from rc_metastudio.publication_bias import (
    AsymmetryTestSpec,
    EligibilityMethod,
    EligibilityReport,
    FunnelKind,
    FunnelPlotSpec,
    PooledDisplayModel,
    PooledDisplaySpec,
    SmallStudyEffectsRequest,
    TestMethod,
)
from rc_metastudio.small_study_effects_core import (
    SmallStudyEffectsCoreError,
    SmallStudyEffectsEligibilityError,
    build_small_study_effects_plan,
    preview_small_study_effects,
    run_small_study_effects,
)


def _mapping(value: object) -> Mapping[str, object]:
    assert isinstance(value, dict)
    assert all(isinstance(key, str) for key in value)
    return cast(Mapping[str, object], value)


def _rows(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast(list[object], value)


def _snapshot() -> BinaryInputSnapshot:
    rows = (
        (9, "Zulu", 24, 110, 15, 110),
        (3, "Alpha", 30, 150, 18, 150),
        (7, "Beta", 41, 200, 26, 200),
    )
    studies = tuple(
        BinaryStudyInput(
            id=study_id,
            name=name,
            year=2020 + index,
            estimate=None,
            standard_error=None,
            treatment_events=treatment_events,
            treatment_total=treatment_total,
            control_events=control_events,
            control_total=control_total,
        )
        for index, (
            study_id,
            name,
            treatment_events,
            treatment_total,
            control_events,
            control_total,
        ) in enumerate(rows)
    )
    return BinaryInputSnapshot(
        version=1,
        outcome="Mortality",
        time_point="12 months",
        groups=("Treatment", "Control"),
        metric="OR",
        raw_counts_available=True,
        studies=studies,
        covariates=(),
    )


def _eligibility(
    *,
    methods: tuple[EligibilityMethod, ...] | None = None,
    usable_studies: int = 3,
) -> EligibilityReport:
    if methods is None:
        methods = (
            EligibilityMethod(
                "harbord", True, usable_studies=usable_studies,
                required_inputs=("two-arm counts",), role="primary"
            ),
            EligibilityMethod(
                "begg-mazumdar", True, usable_studies=usable_studies,
                required_inputs=("rank-correlation test",), role="exploratory"
            ),
            EligibilityMethod(
                "peters", False, "Requires at least 10 usable studies.",
                usable_studies=usable_studies,
                required_inputs=("two-arm counts",), role="none"
            ),
        )
    return EligibilityReport(
        data_type="binary",
        metric="OR",
        usable_studies=usable_studies,
        methods=methods,
        warnings=("Observed standard-error range should be considered.",),
        raw_data_available=True,
        standard_error_range=(0.1, 0.5),
        package_versions=(("meta", "8.5-0"),),
    )


def _request(*, tests=(), funnels=(), pooled=PooledDisplayModel.COMMON):
    return SmallStudyEffectsRequest(
        data_type="binary",
        metric="OR",
        test_specs=tuple(AsymmetryTestSpec(TestMethod(item)) for item in tests),
        plot_specs=tuple(FunnelPlotSpec(FunnelKind(item)) for item in funnels),
        pooled_display=PooledDisplaySpec(pooled),
    )


def _result(*, failures: str | None = None) -> AnalysisResult:
    texts = {
        "small-study.warning": "Primary asymmetry test: Harbord test.",
        "small-study.data-eligibility": "Studies analyzed: 3",
        "small-study.tests": (
            "Harbord test (primary)\n"
            "  Studies: 3\n"
            "  Result: no clear evidence (p = 0.500)\n"
            "  Model: Harbord native metabin model"
        ),
        "small-study.pooled-comparison": (
            "Common effect\n  Estimate: 1.2\n\nRandom effects (REML)"
        ),
        "small-study.method-details": (
            "Harbord test\n  Package: meta 8.5-0\n"
            "  Predictor: native score variance\n  Call: meta::metabias(...)"
        ),
        "small-study.methods-not-applicable": "Peters test: Requires at least 10 studies.",
    }
    if failures is not None:
        texts["small-study.failures"] = failures
    return parse_analysis_result(
        {
            "version": 1,
            "texts": texts,
            "images": {},
            "display_images": {},
            "image_var_names": {},
            "image_params_paths": {},
            "image_order": None,
            "plot_capabilities": {},
            "sections": [
                {
                    "id": f"section:{index}",
                    "kind": "text",
                    "order": index,
                    "title": key,
                    "source_key": key,
                }
                for index, key in enumerate(texts)
            ],
        }
    )


class _FixedResultService:
    def __init__(self, result: AnalysisResult):
        self.result = result

    def preview(
        self, model: object, request: SmallStudyEffectsRequest
    ) -> EligibilityReport:
        return _eligibility()

    def execute(
        self, model: object, request: SmallStudyEffectsRequest
    ) -> AnalysisResult:
        return self.result


def test_plan_keeps_primary_separate_from_exploratory_and_unavailable_tests():
    plan = build_small_study_effects_plan(_snapshot(), _request(), _eligibility())

    mapping = plan.to_mapping()
    tests = _mapping(mapping["tests"])
    eligibility = _mapping(mapping["eligibility"])
    methods = _rows(eligibility["methods"])
    assert tests["primary_method"] == "harbord"
    assert tests["selected_methods"] == ["harbord"]
    assert tests["additional_methods"] == ["begg-mazumdar"]
    assert _mapping(methods[2])["reason"] == (
        "Requires at least 10 usable studies."
    )
    assert mapping["pooled_display"] == {
        "model": "common",
        "tau_estimator": "REML",
    }
    json.dumps(mapping, allow_nan=False)


def test_explicitly_selected_exploratory_test_does_not_replace_primary_identity():
    plan = build_small_study_effects_plan(
        _snapshot(),
        _request(tests=(TestMethod.BEGG_MAZUMDAR.value,)),
        _eligibility(),
    )

    assert plan.primary_method is not None
    assert plan.primary_method.method == "harbord"
    assert plan.selected_methods == ("begg-mazumdar",)


def test_plan_rejects_requested_unavailable_method_with_authority_reason():
    with pytest.raises(SmallStudyEffectsEligibilityError) as error:
        build_small_study_effects_plan(
            _snapshot(),
            _request(tests=(TestMethod.PETERS.value,)),
            _eligibility(),
        )

    assert error.value.method == "peters"
    assert error.value.reason == "Requires at least 10 usable studies."


def test_plan_rejects_method_specific_study_dropping():
    eligibility = _eligibility(
        methods=(
            EligibilityMethod(
                "harbord", True, usable_studies=2, role="primary"
            ),
        )
    )

    with pytest.raises(SmallStudyEffectsCoreError, match="per-method study dropping"):
        build_small_study_effects_plan(_snapshot(), _request(), eligibility)


def test_plan_rejects_mismatched_input_and_eligibility_identity():
    eligibility = EligibilityReport(
        data_type="continuous",
        metric="MD",
        usable_studies=3,
        methods=(),
    )

    with pytest.raises(SmallStudyEffectsCoreError, match="eligibility does not match"):
        build_small_study_effects_plan(_snapshot(), _request(), eligibility)


def test_preview_and_execution_rebuild_the_same_frozen_study_order():
    snapshot = _snapshot()
    request = _request()

    class Service:
        observed_orders: list[list[str]] = []

        def preview(self, model: object, request: SmallStudyEffectsRequest) -> EligibilityReport:
            assert isinstance(model, DatasetTableModel)
            names = [study.name for study in model.get_studies(only_if_included=True)]
            self.observed_orders.append(names)
            return _eligibility()

        def execute(self, model: object, request: SmallStudyEffectsRequest) -> AnalysisResult:
            assert isinstance(model, DatasetTableModel)
            names = [study.name for study in model.get_studies(only_if_included=True)]
            self.observed_orders.append(names)
            return _result()

    service = Service()
    plan = preview_small_study_effects(snapshot, request, service)
    run = run_small_study_effects(plan, service)

    assert service.observed_orders == [["Zulu", "Alpha", "Beta"]] * 2
    metadata = run.to_mapping()
    report = _mapping(metadata["report"])
    assert metadata["input_identity"] == report["input_identity"]
    assert metadata["study_order"] == report["study_order"]
    assert report["status"] == "complete"
    assert _mapping(report["primary_test"])["model"] == (
        "Harbord native metabin model"
    )
    assert _mapping(_rows(report["exploratory_tests"])[0])["status"] == "not_requested"
    assert _mapping(report["pooled_display"])["model"] == "common"
    json.dumps(metadata, allow_nan=False)

    result_mapping = run.result_mapping()
    assert result_mapping["small_study_effects"] == metadata
    assert parse_analysis_result(result_mapping).texts == run.result.texts


def test_failed_requested_test_is_partial_and_keeps_method_failure_reason():
    request = _request(tests=(TestMethod.HARBORD.value,))
    plan = build_small_study_effects_plan(_snapshot(), request, _eligibility())
    result = _result(failures="Harbord test: model failed to converge")
    run = run_small_study_effects(plan, _FixedResultService(result))

    status = run.report_status
    assert status["status"] == "partial"
    primary_test = _mapping(status["primary_test"])
    assert primary_test["status"] == "failed"
    assert primary_test["reason"] == "Harbord test: model failed to converge"


def test_report_status_keeps_figure_failure_reason_and_marks_unrequested_figures():
    empty_plan = build_small_study_effects_plan(
        _snapshot(), _request(), _eligibility()
    )
    empty_run = run_small_study_effects(
        empty_plan,
        _FixedResultService(_result()),
    )
    figure_section = next(
        _mapping(section)
        for section in _rows(empty_run.report_status["sections"])
        if _mapping(section)["key"] == "funnel_figures"
    )
    assert figure_section["status"] == "not_requested"

    plot_plan = build_small_study_effects_plan(
        _snapshot(), _request(funnels=(FunnelKind.ORDINARY.value,)), _eligibility()
    )
    plot_run = run_small_study_effects(
        plot_plan,
        _FixedResultService(
            _result(failures="Ordinary Funnel Plot: renderer rejected the plot")
        ),
    )
    figure = _mapping(_rows(plot_run.report_status["funnel_requests"])[0])
    assert figure["status"] == "failed"
    assert figure["reason"] == "Ordinary Funnel Plot: renderer rejected the plot"
    assert plot_run.report_status["status"] == "partial"
