from __future__ import annotations

from types import SimpleNamespace

import pytest

from rc_metastudio.analysis_results import empty_analysis_result, parse_analysis_result
from rc_metastudio.meta_regression_analysis import (
    MetaRegressionCovariateInput,
    MetaRegressionInputSnapshot,
    MetaRegressionRunRequest,
    MetaRegressionStudyInput,
    execute_meta_regression,
    freeze_meta_regression_input,
)


def _model():
    studies = tuple(
        SimpleNamespace(id=index, name=f"Study {index}", year=2020 + index)
        for index in range(1, 5)
    )

    class Dataset:
        def get_covariate_values(self, name, *, ids_for_keys=False):
            assert name == "dose"
            assert ids_for_keys
            return {1: 1.0, 2: None, 3: 3.0, 4: 4.0}

    class Model:
        current_outcome_name = "Response"
        current_effect = "SMD"
        dataset = Dataset()

        def get_current_outcome_type(self):
            return "continuous"

        def get_current_follow_up_name(self):
            return "12 months"

        def get_current_groups(self):
            return ("Control", "Treatment")

        def get_studies(self, only_if_included=True):
            assert only_if_included
            return studies

        def get_current_estimates_and_standard_errors(
            self, *, only_if_included=True, only_these_studies=None
        ):
            assert only_if_included
            assert only_these_studies == [1, 2, 3, 4]
            return (0.1, 0.2, 0.3, 0.4), (0.08, 0.09, 0.1, 0.11)

    return Model()


def test_snapshot_round_trip_keeps_missing_moderator_values_explicit():
    snapshot = freeze_meta_regression_input(
        _model(),
        (MetaRegressionCovariateInput("dose", "continuous", (), "mg", 10),),
    )

    restored = MetaRegressionInputSnapshot.from_mapping(snapshot.to_mapping())

    assert restored == snapshot
    assert restored.metric == "SMD"
    assert restored.studies[1].estimate == 0.2
    assert restored.moderators[0].values == (1.0, None, 3.0, 4.0)
    assert restored.moderators[0].unit == "mg"
    assert restored.moderators[0].unit_step == 10


def test_request_round_trip_keeps_missing_policy_and_excludes_machine_paths():
    request = MetaRegressionRunRequest(
        data_type="continuous",
        metric="SMD",
        missing_moderator_policy="exclude",
        heterogeneity_method="REML",
        inference_method="z",
    )

    restored = MetaRegressionRunRequest.from_mapping(request.to_mapping())

    assert restored == request
    assert "bp_outpath" not in request.to_mapping()["params"]
    assert restored.missing_moderator_policy == "exclude"


def test_request_rejects_univariate_reitsma_view():
    mapping = MetaRegressionRunRequest(
        data_type="diagnostic",
        metric="Sensitivity and specificity",
    ).to_mapping()
    mapping["metric"] = "Spec"

    with pytest.raises(ValueError, match="one joint Reitsma request"):
        MetaRegressionRunRequest.from_mapping(mapping)


def test_generic_runner_uses_the_explicit_exclusion_set_and_attaches_typed_result():
    snapshot = MetaRegressionInputSnapshot(
        version=1,
        data_type="continuous",
        outcome="Response",
        time_point="12 months",
        groups=("Control", "Treatment"),
        metric="SMD",
        studies=(
            MetaRegressionStudyInput(1, "Study 1", 2021, 0.1, 0.08),
            MetaRegressionStudyInput(2, "Study 2", 2022, 0.2, 0.09),
            MetaRegressionStudyInput(3, "Study 3", 2023, 0.3, 0.1),
            MetaRegressionStudyInput(4, "Study 4", 2024, 0.4, 0.11),
        ),
        moderators=(
            MetaRegressionCovariateInput(
                "dose", "continuous", (1.0, None, 3.0, 4.0), "mg", 1
            ),
        ),
    )
    request = MetaRegressionRunRequest(
        "continuous", "SMD", missing_moderator_policy="exclude"
    )

    class RResult:
        def rx2(self, key):
            assert key == "res"
            return {
                "k": 3,
                "p": 2,
                "method": "REML",
                "b": [0.15, 0.05],
                "se": [0.1, 0.02],
                "ci.lb": [-0.046, 0.011],
                "ci.ub": [0.346, 0.089],
                "zval": [1.5, 2.5],
                "pval": [0.134, 0.012],
                "QM": 6.25,
                "m": 1,
                "QMp": 0.012,
                "tau2": 0.01,
                "se.tau2": 0.02,
                "I2": 10,
                "H2": 1.1,
                "R2": 20,
                "QE": 2.4,
                "QEp": 0.3,
            }

    class FakeBridge:
        ro = SimpleNamespace(globalenv={})

        def _r_numeric_vector(self, values):
            return list(values)

        def _r_character_vector(self, values):
            return list(values)

        def _r_year_vector(self, values):
            return list(values)

        def execute_r_function(self, name, *args, **kwargs):
            if name == "rcmetar.create.covariate.values":
                return kwargs
            if name == "list":
                return list(args)
            if name in ("rcmetar.create.continuous.data", "rcmetar.create.binary.data"):
                return kwargs
            raise AssertionError(name)

        def run_versioned_analysis_request(self, request):
            assert request["workflow"] == "meta-regression"
            assert request["method"] == "meta.regression"
            assert request["metric"] == "SMD"
            self.ro.globalenv["result"] = RResult()
            return empty_analysis_result()

        def r_object_to_python(self, value):
            return value

    execution = execute_meta_regression(snapshot, request, FakeBridge())

    numerics = execution.result.meta_regression_numerics
    assert numerics is not None
    assert numerics["eligible_study_ids"] == [1, 3, 4]
    assert numerics["excluded_studies"] == [
        {"id": 2, "label": "Study 2", "missing_moderators": ["dose"]}
    ]
    assert numerics["coefficients"][1]["estimate"]["value"] == 0.05
    assert execution.result.sections[0].title == "Meta-regression specification"
    parsed = parse_analysis_result(
        {
            **{
                "version": execution.result.version,
                "texts": dict(execution.result.texts),
                "images": dict(execution.result.images),
                "display_images": dict(execution.result.display_images),
                "image_var_names": dict(execution.result.image_var_names),
                "image_params_paths": dict(execution.result.image_params_paths),
                "image_order": list(execution.result.image_order or ()),
                "plot_capabilities": {},
                "sections": [
                    {
                        "id": section.semantic_id,
                        "kind": section.kind,
                        "order": section.order,
                        "title": section.title,
                        "source_key": section.source_key,
                    }
                    for section in execution.result.sections
                ],
                "meta_regression_numerics": dict(numerics),
            }
        }
    )
    assert parsed.meta_regression_numerics == numerics
