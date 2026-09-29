from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from rc_metastudio import analysis_dataset, analysis_worker, analysis_worker_support
from rc_metastudio.analysis_results import empty_analysis_result, parse_analysis_result
from rc_metastudio.analysis_snapshot import (
    BinaryCovariateInput,
    BinaryInputSnapshot,
    BinaryStudyInput,
    _BinaryInputModel as BinaryInputModel,
)
from rc_metastudio.continuous_analysis_snapshot import (
    ContinuousArmInput,
    ContinuousCovariateInput,
    ContinuousInputSnapshot,
    ContinuousStudyInput,
    create_continuous_backend_data,
)
from rc_metastudio.meta_regression_analysis import (
    MetaRegressionCovariateInput,
    MetaRegressionInputSnapshot,
    MetaRegressionRunRequest,
    MetaRegressionStudyInput,
    MetaRegressionBridge,
    MetaRegressionModel,
    execute_meta_regression,
    freeze_meta_regression_input,
)


def _record(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _records(value: object) -> list[dict[str, object]]:
    assert isinstance(value, list)
    assert all(isinstance(item, dict) for item in value)
    return cast(list[dict[str, object]], value)


def _model():
    studies = tuple(
        SimpleNamespace(id=index, name=f"Study {index}", year=2020 + index)
        for index in range(1, 5)
    )

    class Dataset:
        studies: tuple[SimpleNamespace, ...]
        covariates = (SimpleNamespace(name="dose", data_type=analysis_dataset.CONTINUOUS),)

        def get_covariate_values(self, name, *, ids_for_keys=False):
            assert name == "dose"
            assert ids_for_keys
            return {1: 1.0, 2: None, 3: 3.0, 4: 4.0}

    Dataset.studies = studies

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

        def get_current_raw_data(
            self, *, only_if_included=True, only_these_studies=None
        ):
            assert only_if_included
            assert only_these_studies == [1, 2, 3, 4]
            return ((), (), (), ())

        def get_studies(self, only_if_included=True):
            assert only_if_included
            return studies

        def get_current_estimates_and_standard_errors(
            self, *, only_if_included=True, only_these_studies=None
        ):
            assert only_if_included
            assert only_these_studies == [1, 2, 3, 4]
            return (0.1, 0.2, 0.3, 0.4), (0.08, 0.09, 0.1, 0.11)

        def get_current_outcome_subtype(self):
            return None

        def _get_canonical_analysis_unit(self, _study_index):
            return SimpleNamespace(
                get_effect_for_source=lambda *_args: SimpleNamespace(lower=0.0, upper=1.0)
            )

        def get_current_group_comparison(self):
            return "Control vs Treatment"

        def get_confidence_level(self):
            return 95.0

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


def test_old_saved_meta_regression_snapshot_without_source_still_loads():
    snapshot = freeze_meta_regression_input(
        _model(),
        (MetaRegressionCovariateInput("dose", "continuous", (), "mg", 10),),
    )
    mapping = snapshot.to_mapping()
    del mapping["source_snapshot"]

    restored = MetaRegressionInputSnapshot.from_mapping(mapping)

    assert restored.source_snapshot is None
    assert restored.studies[0].estimate == 0.1


def test_binary_raw_freeze_never_requests_gui_effect_preview():
    studies = tuple(
        SimpleNamespace(id=index, name=f"Study {index}", year=2020 + index)
        for index in range(1, 5)
    )

    class Dataset:
        studies: tuple[SimpleNamespace, ...]
        covariates = (SimpleNamespace(name="dose", data_type=analysis_dataset.CONTINUOUS),)

        def get_covariate_values(self, _name, *, ids_for_keys=False):
            assert ids_for_keys
            return {index: float(index) for index in range(1, 5)}

    class Model:
        current_outcome_name = "Response"
        current_effect = "OR"
        dataset = Dataset()

        def get_current_outcome_type(self):
            return "binary"

        def get_current_follow_up_name(self):
            return "12 months"

        def get_current_groups(self):
            return ("Treatment", "Control")

        def get_studies(self, only_if_included=True):
            assert only_if_included
            return studies

        def get_current_raw_data(self, *, only_if_included=True, only_these_studies=None):
            assert only_if_included
            assert only_these_studies == [1, 2, 3, 4]
            return ((1, 10, 2, 10), (2, 10, 3, 10), (3, 10, 4, 10), (4, 10, 5, 10))

        def get_current_estimates_and_standard_errors(self, **_kwargs):
            raise AssertionError("raw rows must not request a GUI derived-effect preview")

    snapshot = freeze_meta_regression_input(
        cast(MetaRegressionModel, Model()),
        (MetaRegressionCovariateInput("dose", "continuous", ()),),
    )

    assert isinstance(snapshot.source_snapshot, BinaryInputSnapshot)
    assert snapshot.source_snapshot.raw_counts_available
    assert snapshot.studies[0].estimate is None
    assert snapshot.studies[0].standard_error is None
    assert snapshot.moderators[0].values == (1.0, 2.0, 3.0, 4.0)
    assert MetaRegressionInputSnapshot.from_mapping(snapshot.to_mapping()) == snapshot

    class MixedSourceModel(Model):
        def get_current_raw_data(
            self, *, only_if_included=True, only_these_studies=None
        ):
            assert only_if_included
            assert only_these_studies == [1, 2, 3, 4]
            return ((1, 10, 2, 10), (), (3, 10, 4, 10), (4, 10, 5, 10))

    with pytest.raises(ValueError, match="all have complete event counts"):
        freeze_meta_regression_input(
            cast(MetaRegressionModel, MixedSourceModel()),
            (MetaRegressionCovariateInput("dose", "continuous", ()),),
        )


def test_continuous_raw_freeze_never_requests_gui_effect_preview():
    studies = tuple(
        SimpleNamespace(id=index, name=f"Study {index}", year=2020 + index)
        for index in range(1, 5)
    )

    class Dataset:
        studies: tuple[SimpleNamespace, ...]
        covariates = (SimpleNamespace(name="dose", data_type=analysis_dataset.CONTINUOUS),)

        def get_covariate_values(self, _name, *, ids_for_keys=False):
            assert ids_for_keys
            return {index: float(index) for index in range(1, 5)}

    Dataset.studies = studies

    class Model:
        current_outcome_name = "Response"
        current_effect = "SMD"
        dataset = Dataset()

        def get_current_outcome_type(self):
            return "continuous"

        def get_current_follow_up_name(self):
            return "12 months"

        def get_current_groups(self):
            return ("Treatment", "Control")

        def get_studies(self, only_if_included=True):
            assert only_if_included
            return studies

        def get_current_raw_data(self, *, only_if_included=True, only_these_studies=None):
            assert only_if_included
            assert only_these_studies == [1, 2, 3, 4]
            return tuple((10, float(index), 1, 10, 0, 1) for index in range(1, 5))

        def get_current_estimates_and_standard_errors(self, **_kwargs):
            raise AssertionError("raw rows must not request a GUI derived-effect preview")

        def get_current_outcome_subtype(self):
            return None

    snapshot = freeze_meta_regression_input(
        cast(MetaRegressionModel, Model()),
        (MetaRegressionCovariateInput("dose", "continuous", ()),),
    )

    assert isinstance(snapshot.source_snapshot, ContinuousInputSnapshot)
    assert snapshot.source_snapshot.raw_measurements_complete
    assert snapshot.studies[0].estimate is None
    assert snapshot.studies[0].standard_error is None
    assert snapshot.moderators[0].values == (1.0, 2.0, 3.0, 4.0)
    assert MetaRegressionInputSnapshot.from_mapping(snapshot.to_mapping()) == snapshot


@pytest.mark.parametrize("family", ["binary", "continuous"])
def test_raw_effects_are_prepared_by_rcmetar_before_meta_regression(
    family, monkeypatch
):
    studies = tuple(
        MetaRegressionStudyInput(index, f"Study {index}", 2020 + index, None, None)
        for index in range(1, 5)
    )
    moderator = MetaRegressionCovariateInput("dose", "continuous", (1.0, 2.0, 3.0, 4.0))
    if family == "binary":
        source = BinaryInputSnapshot(
            version=1,
            outcome="Response",
            time_point="12 months",
            groups=("Treatment", "Control"),
            metric="OR",
            raw_counts_available=True,
            studies=tuple(
                BinaryStudyInput(
                    index,
                    f"Study {index}",
                    2020 + index,
                    None,
                    None,
                    index,
                    10,
                    index + 1,
                    10,
                )
                for index in range(1, 5)
            ),
            covariates=(BinaryCovariateInput("dose", "continuous", (1.0, 2.0, 3.0, 4.0)),),
        )
        raw_backend = {"raw": True}

        def create_binary(snapshot, bridge):
            assert snapshot.raw_counts_available
            bridge.ro.globalenv["tmp_obj"] = raw_backend
            return raw_backend

        monkeypatch.setattr(analysis_worker_support, "_create_binary_data", create_binary)
    else:
        source = ContinuousInputSnapshot(
            version=1,
            outcome="Response",
            follow_up="12 months",
            groups=("Treatment", "Control"),
            metric="SMD",
            outcome_subtype=None,
            outcome_unit=None,
            studies=tuple(
                ContinuousStudyInput(
                    study_id=index,
                    name=f"Study {index}",
                    year=2020 + index,
                    provenance="raw_reconstructed",
                    estimate=None,
                    standard_error=None,
                    arm_1=ContinuousArmInput(10, float(index), 1.0),
                    arm_2=ContinuousArmInput(10, 0.0, 1.0),
                )
                for index in range(1, 5)
            ),
            covariates=(
                ContinuousCovariateInput("dose", "continuous", (1.0, 2.0, 3.0, 4.0)),
            ),
        )
        raw_backend = None

    snapshot = MetaRegressionInputSnapshot(
        version=1,
        data_type=family,
        outcome="Response",
        time_point="12 months",
        groups=("Treatment", "Control"),
        metric="OR" if family == "binary" else "SMD",
        studies=studies,
        moderators=(moderator,),
        source_snapshot=source,
    )
    request = MetaRegressionRunRequest(family, snapshot.metric)

    class Fit:
        def rx2(self, key):
            assert key == "res"
            return {
                "k": 4,
                "p": 2,
                "method": "REML",
                "b": [0.1, 0.05],
                "se": [0.1, 0.02],
                "ci.lb": [-0.096, 0.011],
                "ci.ub": [0.296, 0.089],
                "zval": [1.0, 2.5],
                "pval": [0.317, 0.012],
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
        def __init__(self):
            self.ro = SimpleNamespace(globalenv={})
            self.calls = []

        def _r_numeric_vector(self, values):
            return list(values)

        def _r_character_vector(self, values):
            return list(values)

        def _r_year_vector(self, values):
            return list(values)

        def execute_r_function(self, name, *args, **kwargs):
            self.calls.append((name, args, kwargs))
            if name == "rcmetar.create.covariate.values":
                return kwargs
            if name == "list":
                if kwargs:
                    return kwargs
                return list(args)
            if name == "rcmetar.create.continuous.data":
                return kwargs
            if name == "rcmetar.create.binary.data":
                return kwargs
            if name == "rcmetar.prepare.analysis.data":
                if family == "binary":
                    assert args[0] is raw_backend
                else:
                    assert "N1" in args[0] and "N2" in args[0]
                return SimpleNamespace(
                    y=[0.11, 0.22, 0.33, 0.44],
                    SE=[0.08, 0.09, 0.1, 0.11],
                )
            if name == "slot":
                return getattr(args[0], args[1])
            if name in ("sort", "unique"):
                return args[0]
            raise AssertionError(name)

        def run_versioned_analysis_request(self, analysis_request):
            assert analysis_request["workflow"] == "meta-regression"
            effect_data_calls = [
                call[2]
                for call in self.calls
                if call[0] in ("rcmetar.create.binary.data", "rcmetar.create.continuous.data")
                and "y" in call[2]
            ]
            assert effect_data_calls
            assert effect_data_calls[-1]["y"] == [0.11, 0.22, 0.33, 0.44]
            assert effect_data_calls[-1]["SE"] == [0.08, 0.09, 0.1, 0.11]
            self.ro.globalenv["result"] = Fit()
            return empty_analysis_result()

        def r_object_to_python(self, value):
            return value

    bridge = FakeBridge()
    execution = execute_meta_regression(
        snapshot, request, cast(MetaRegressionBridge, bridge)
    )

    prepare_calls = [call for call in bridge.calls if call[0] == "rcmetar.prepare.analysis.data"]
    assert len(prepare_calls) == 1
    expected_parameters = {"measure": "OR" if family == "binary" else "SMD"}
    if family == "binary":
        expected_parameters.update(adjust=0.5, to="only0")
    assert prepare_calls[0][1][1] == expected_parameters
    assert execution.plan is not None
    assert [study.estimate for study in execution.plan.studies] == [0.11, 0.22, 0.33, 0.44]
    assert [study.standard_error for study in execution.plan.studies] == [0.08, 0.09, 0.1, 0.11]


def test_nonnumeric_prepared_effect_keeps_original_study_identity():
    from rc_metastudio.meta_regression_analysis import _worker_effect_vector

    with pytest.raises(ValueError, match="study 'Gonzalez'"):
        _worker_effect_vector([None, 0.25], ("Gonzalez", "Prins"), "estimate")


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
    assert "bp_outpath" not in _record(request.to_mapping()["params"])
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

    execution = execute_meta_regression(
        snapshot, request, cast(MetaRegressionBridge, FakeBridge())
    )

    numerics = execution.result.meta_regression_numerics
    assert numerics is not None
    assert numerics["eligible_study_ids"] == [1, 3, 4]
    assert numerics["excluded_studies"] == [
        {"id": 2, "label": "Study 2", "missing_moderators": ["dose"]}
    ]
    coefficient = _records(numerics["coefficients"])[1]
    assert _record(coefficient["estimate"])["value"] == 0.05
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


@pytest.mark.parametrize("family", ["binary", "continuous"])
def test_raw_meta_regression_matches_pinned_rcmetar_preparation(family):
    from rc_metastudio import r_backend
    from rc_metastudio.analysis_worker import _create_binary_data

    bridge = r_backend.install_r_backend()
    try:
        loader = bridge.RLibraryLoader()
        loader.load_metafor()
        loader.load_rcmetar()
    except Exception as error:
        pytest.skip(f"Pinned R authority is unavailable: {error}")
    assert bridge.get_r_package_version("RCMetaR") == "0.4.1"

    study_names = ("Study A", "Study B", "Study C", "Study D")
    years = (2020, 2021, 2022, 2023)
    factor_values = ("A", "A", "B", "B")
    if family == "binary":
        source = BinaryInputSnapshot(
            version=1,
            outcome="Response",
            time_point="12 months",
            groups=("Treatment", "Control"),
            metric="OR",
            raw_counts_available=True,
            studies=tuple(
                BinaryStudyInput(index, study_names[index - 1], years[index - 1], None, None,
                                 treatment, 20, control, 20)
                for index, treatment, control in zip(
                    range(1, 5), (1, 2, 4, 6), (2, 3, 5, 6), strict=True
                )
            ),
            covariates=(BinaryCovariateInput("cohort", "factor", factor_values),),
        )
        measure = "OR"
    else:
        source = ContinuousInputSnapshot(
            version=1,
            outcome="Response",
            follow_up="12 months",
            groups=("Treatment", "Control"),
            metric="SMD",
            outcome_subtype=None,
            outcome_unit=None,
            studies=tuple(
                ContinuousStudyInput(
                    index,
                    study_names[index - 1],
                    years[index - 1],
                    "raw_reconstructed",
                    None,
                    None,
                    ContinuousArmInput(20, mean, sd1),
                    ContinuousArmInput(20, comparator, sd2),
                )
                for index, mean, comparator, sd1, sd2 in zip(
                    range(1, 5), (1.0, 1.5, 2.0, 2.2), (0.0, 0.2, 0.5, 0.8),
                    (1.0, 1.0, 1.1, 0.9), (1.1, 1.2, 0.9, 1.0), strict=True
                )
            ),
            covariates=(ContinuousCovariateInput("cohort", "factor", factor_values),),
        )
        measure = "SMD"

    snapshot = MetaRegressionInputSnapshot(
        version=1,
        data_type=family,
        outcome="Response",
        time_point="12 months",
        groups=("Treatment", "Control"),
        metric=measure,
        studies=tuple(
            MetaRegressionStudyInput(index, study_names[index - 1], years[index - 1], None, None)
            for index in range(1, 5)
        ),
        moderators=(MetaRegressionCovariateInput(
            "cohort", "factor", factor_values, reference_level="A"
        ),),
        source_snapshot=source,
    )
    if isinstance(source, BinaryInputSnapshot):
        raw_data = _create_binary_data(source, bridge)
    else:
        raw_data = create_continuous_backend_data(source, bridge)
    params = bridge.execute_r_function("list", measure=measure)
    prepared = bridge.execute_r_function(
        "rcmetar.prepare.analysis.data", raw_data, params
    )
    expected_y = bridge.r_object_to_python(bridge.execute_r_function("slot", prepared, "y"))
    expected_se = bridge.r_object_to_python(bridge.execute_r_function("slot", prepared, "SE"))

    execution = execute_meta_regression(
        snapshot,
        MetaRegressionRunRequest(family, measure),
        bridge,
    )
    fit = bridge.ro.globalenv["result"].rx2("res")
    fit = bridge.execute_r_function(
        "structure",
        fit,
        **{"class": bridge._r_character_vector(("rma.uni", "rma"))},
    )
    expected_test = bridge.r_object_to_python(
        bridge.execute_r_function("anova", fit, btt=bridge.ro.IntVector([2]))
    )
    expected_test = _record(expected_test)

    assert execution.plan is not None
    assert [study.estimate for study in execution.plan.studies] == pytest.approx(expected_y)
    assert [study.standard_error for study in execution.plan.studies] == pytest.approx(expected_se)
    assert execution.result.meta_regression_numerics is not None
    assert execution.result.meta_regression_numerics["coefficients"]
    moderator_test = _records(
        execution.result.meta_regression_numerics["moderator_tests"]
    )[0]
    assert moderator_test["key"] == "moderator.cohort"
    assert _record(moderator_test["statistic"])["value"] == pytest.approx(expected_test["QM"])
    assert _record(moderator_test["numerator_degrees_of_freedom"])["value"] == expected_test["m"]
    assert _record(moderator_test["p_value"])["value"] == pytest.approx(expected_test["QMp"])


def test_amino_binary_meta_regression_keeps_zero_cell_studies_eligible(qapp):
    from rc_metastudio import project_adapter, project_format, r_backend
    from rc_metastudio.analysis_snapshot import freeze_binary_input
    from rc_metastudio.analysis_worker import _create_binary_data
    from rc_metastudio.dataset_table_model import DatasetTableModel

    bridge = r_backend.install_r_backend()
    try:
        loader = bridge.RLibraryLoader()
        loader.load_metafor()
        loader.load_rcmetar()
    except Exception as error:
        pytest.skip(f"Pinned R authority is unavailable: {error}")
    assert bridge.get_r_package_version("RCMetaR") == "0.4.1"

    sample = Path(__file__).resolve().parents[3] / "sample_projects" / "amino.rcms"
    runtime = project_adapter.document_to_runtime_project(
        project_format.load_project(sample)
    )
    model = DatasetTableModel(dataset=runtime.dataset, add_blank_study=False)
    model.set_state(runtime.model_state)
    model.current_effect = "OR"
    source_snapshot = freeze_binary_input(cast(BinaryInputModel, model))
    assert isinstance(source_snapshot, BinaryInputSnapshot)
    binary_studies = [
        study for study in source_snapshot.studies if isinstance(study, BinaryStudyInput)
    ]
    assert len(binary_studies) == len(source_snapshot.studies)
    assert any(
        study.treatment_events == 0
        or study.treatment_total == study.treatment_events
        or study.control_events == 0
        or study.control_total == study.control_events
        for study in binary_studies
    )
    moderator_values = tuple(
        float(index) for index in range(1, len(source_snapshot.studies) + 1)
    )
    source_snapshot = replace(
        source_snapshot,
        covariates=source_snapshot.covariates
        + (BinaryCovariateInput("Qualification index", "continuous", moderator_values),),
    )
    snapshot = MetaRegressionInputSnapshot(
        version=1,
        data_type="binary",
        outcome=source_snapshot.outcome,
        time_point=source_snapshot.time_point,
        groups=source_snapshot.groups,
        metric=source_snapshot.metric,
        studies=tuple(
            MetaRegressionStudyInput(
                study.id, study.name, study.year, None, None
            )
            for study in source_snapshot.studies
        ),
        moderators=(
            MetaRegressionCovariateInput(
                "Qualification index", "continuous", moderator_values, "study index"
            ),
        ),
        source_snapshot=source_snapshot,
    )

    raw_data = _create_binary_data(source_snapshot, bridge)
    preparation_parameters = bridge.execute_r_function(
        "list", measure="OR", adjust=0.5, to="only0"
    )
    prepared = bridge.execute_r_function(
        "rcmetar.prepare.analysis.data", raw_data, preparation_parameters
    )
    expected_y = bridge.r_object_to_python(
        bridge.execute_r_function("slot", prepared, "y")
    )
    expected_se = bridge.r_object_to_python(
        bridge.execute_r_function("slot", prepared, "SE")
    )

    execution = execute_meta_regression(
        snapshot,
        MetaRegressionRunRequest("binary", "OR"),
        bridge,
    )

    assert execution.plan is not None
    assert execution.plan.eligible_study_count == 19
    assert [study.label for study in execution.plan.studies] == [
        study.name for study in source_snapshot.studies
    ]
    assert [study.moderator_values for study in execution.plan.studies] == [
        (value,) for value in moderator_values
    ]
    assert [study.estimate for study in execution.plan.studies] == pytest.approx(expected_y)
    assert [study.standard_error for study in execution.plan.studies] == pytest.approx(expected_se)
    assert all(value is not None for value in expected_y + expected_se)
