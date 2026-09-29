# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Frozen input and worker execution for generic and joint meta-regression."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass, replace
from typing import Callable, Literal, Protocol, cast

from rc_metastudio.analysis_results import AnalysisResult
from rc_metastudio.analysis_snapshot import (
    BinaryCovariateInput,
    BinaryInputSnapshot,
    BinaryStudyInput,
    SingleArmBinaryStudyInput,
    SnapshotValue,
    _BinaryInputModel as BinaryInputModel,
    freeze_binary_input,
)
from rc_metastudio.continuous_analysis_snapshot import (
    ContinuousInputSnapshot,
    ContinuousStudyInput,
    _rcmetar_metric,
    create_continuous_backend_data,
    freeze_continuous_input,
)
from rc_metastudio.continuous_analysis_snapshot import (
    _ContinuousBridge as ContinuousBridge,
)
from rc_metastudio.continuous_analysis_snapshot import (
    _DatasetModel as ContinuousDatasetModel,
)
from rc_metastudio.meta_globals import BINARY_ONE_ARM_METRICS
from rc_metastudio.meta_regression import (
    ContinuousModerator,
    FactorModerator,
    HeterogeneityMethod,
    InferenceMethod,
    MetaRegressionNumerics,
    MetaRegressionPlan,
    MetaRegressionRequest,
    MetaRegressionStudy,
    Moderator,
    parse_meta_regression_result,
    prepare_meta_regression,
)
from rc_metastudio.reitsma_analysis import (
    ReitsmaBridge,
    ReitsmaInputSnapshot,
    ReitsmaModel,
    ReitsmaStudyInput,
    _validate_authority_counts,
)
from rc_metastudio.reitsma_meta_regression import (
    ExcludedStudy as ReitsmaExcludedStudy,
)
from rc_metastudio.reitsma_meta_regression import (
    ReitsmaMetaRegressionResult,
    parse_reitsma_meta_regression_result,
)

DataFamily = Literal["binary", "continuous", "diagnostic"]
ModeratorKind = Literal["continuous", "factor"]
MissingPolicy = Literal["reject", "exclude"]


class _RNamespace(Protocol):
    globalenv: MutableMapping[str, object]
    IntVector: Callable[[Sequence[int]], object]


class _RList(Protocol):
    def rx2(self, key: str) -> object: ...


class MetaRegressionBridge(Protocol):
    ro: _RNamespace

    def _r_numeric_vector(self, values: Sequence[object]) -> object: ...

    def _r_character_vector(self, values: Sequence[str]) -> object: ...

    def _r_year_vector(self, values: Sequence[object]) -> object: ...

    def execute_r_function(self, name: str, *args: object, **kwargs: object) -> object: ...

    def execute_r_string(self, source: str) -> object: ...

    def run_versioned_analysis_request(self, request: Mapping[str, object]) -> object: ...

    def r_object_to_python(self, value: object) -> object: ...


class _StudyRow(Protocol):
    id: object
    name: object
    year: object


class _CovariateDataset(Protocol):
    def get_covariate_values(
        self, name: str, *, ids_for_keys: bool
    ) -> Mapping[object, object]: ...


class MetaRegressionModel(Protocol):
    current_outcome_name: str | None
    current_effect: str
    dataset: _CovariateDataset

    def get_current_outcome_type(self) -> str: ...

    def get_current_follow_up_name(self) -> str | None: ...

    def get_current_groups(self) -> Sequence[object]: ...

    def get_studies(self, only_if_included: bool = True) -> Sequence[_StudyRow]: ...

    def get_current_estimates_and_standard_errors(
        self,
        *,
        only_if_included: bool = True,
        only_these_studies: Sequence[int] | None = None,
    ) -> tuple[Sequence[object], Sequence[object]]: ...

    def get_current_raw_data(
        self,
        only_if_included: bool = True,
        only_these_studies: Sequence[int] | None = None,
    ) -> Sequence[Sequence[object]]: ...


@dataclass(frozen=True, slots=True)
class MetaRegressionStudyInput:
    id: int
    name: str
    year: int | None
    estimate: float | None
    standard_error: float | None
    tp: int | None = None
    fn: int | None = None
    fp: int | None = None
    tn: int | None = None

    def __post_init__(self) -> None:
        if type(self.id) is not int or self.id < 0:
            raise ValueError("meta-regression study identity must be a non-negative integer")
        _text(self.name, "study name")
        if self.year is not None and type(self.year) is not int:
            raise ValueError("study year must be an integer or missing")
        _optional_finite(self.estimate, "study estimate")
        _optional_finite(self.standard_error, "study standard error")
        if (self.estimate is None) != (self.standard_error is None):
            raise ValueError("study estimate and standard error must be paired")
        if self.standard_error is not None and self.standard_error < 0:
            raise ValueError("study standard error cannot be negative")
        for field in ("tp", "fn", "fp", "tn"):
            value = getattr(self, field)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{field.upper()} count must be a non-negative integer or missing")

    def to_mapping(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "year": self.year,
            "estimate": self.estimate,
            "standard_error": self.standard_error,
            "tp": self.tp,
            "fn": self.fn,
            "fp": self.fp,
            "tn": self.tn,
        }


@dataclass(frozen=True, slots=True)
class MetaRegressionCovariateInput:
    name: str
    kind: ModeratorKind
    values: tuple[object, ...]
    unit: str = "unit"
    unit_step: float = 1.0
    reference_level: str | None = None

    def __post_init__(self) -> None:
        _text(self.name, "moderator name")
        if self.kind not in ("continuous", "factor"):
            raise ValueError("moderator kind must be continuous or factor")
        if not isinstance(self.values, tuple):
            raise TypeError("moderator values must be a frozen tuple")
        if self.kind == "continuous":
            _text(self.unit, "continuous moderator unit")
            step = _finite(self.unit_step, "moderator unit step")
            if step <= 0:
                raise ValueError("moderator unit step must be greater than zero")
            if self.reference_level is not None:
                raise ValueError("continuous moderators cannot have a reference level")
            for value in self.values:
                if not _missing(value):
                    _finite(value, f"moderator '{self.name}' value")
        else:
            _text(self.reference_level, "factor reference level")
            if self.unit_step != 1.0:
                raise ValueError("factor moderators cannot have a unit step")
            for value in self.values:
                if not _missing(value) and not isinstance(value, str):
                    raise ValueError(f"factor moderator '{self.name}' values must be text")

    def to_mapping(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "values": list(self.values),
            "unit": self.unit if self.kind == "continuous" else None,
            "unit_step": self.unit_step if self.kind == "continuous" else None,
            "reference_level": self.reference_level,
        }


@dataclass(frozen=True, slots=True)
class MetaRegressionInputSnapshot:
    """Included outcome rows and selected moderator values copied at submit time."""

    version: int
    data_type: DataFamily
    outcome: str
    time_point: str
    groups: tuple[str, ...]
    metric: str
    studies: tuple[MetaRegressionStudyInput, ...]
    moderators: tuple[MetaRegressionCovariateInput, ...]
    source_snapshot: BinaryInputSnapshot | ContinuousInputSnapshot | None = None

    def __post_init__(self) -> None:
        if type(self.version) is not int or self.version != 1:
            raise ValueError("unsupported meta-regression input snapshot version")
        if self.data_type not in ("binary", "continuous", "diagnostic"):
            raise ValueError("unsupported meta-regression data family")
        _text(self.outcome, "outcome")
        _text(self.time_point, "time point")
        _text(self.metric, "measure")
        expected_groups = 1 if self.data_type == "diagnostic" else None
        if not self.groups or any(not isinstance(group, str) or not group.strip() for group in self.groups):
            raise ValueError("meta-regression input requires selected study group(s)")
        if expected_groups is not None and len(self.groups) != expected_groups:
            raise ValueError("joint Reitsma meta-regression requires one selected study group")
        if not self.studies:
            raise ValueError("include at least one study before running meta-regression")
        if len({study.id for study in self.studies}) != len(self.studies):
            raise ValueError("meta-regression study identities must be unique")
        if not self.moderators:
            raise ValueError("select at least one moderator before running meta-regression")
        if len({moderator.name for moderator in self.moderators}) != len(self.moderators):
            raise ValueError("meta-regression moderator names must be unique")
        if any(len(moderator.values) != len(self.studies) for moderator in self.moderators):
            raise ValueError("moderator values must match the included study rows")
        if self.data_type == "diagnostic":
            if self.source_snapshot is not None:
                raise ValueError(
                    "joint Reitsma meta-regression cannot include a generic source snapshot"
                )
            for study in self.studies:
                if any(getattr(study, field) is not None for field in ("estimate", "standard_error")):
                    raise ValueError("joint Reitsma input must retain raw counts, not univariate effects")
        elif self.source_snapshot is None:
            if any(study.estimate is None for study in self.studies):
                raise ValueError(
                    "generic meta-regression requires an estimate and standard error for each included study"
                )
        else:
            _validate_source_snapshot(self)

    def to_mapping(self) -> dict[str, object]:
        mapping: dict[str, object] = {
            "version": self.version,
            "data_type": self.data_type,
            "outcome": self.outcome,
            "time_point": self.time_point,
            "groups": list(self.groups),
            "metric": self.metric,
            "studies": [study.to_mapping() for study in self.studies],
            "moderators": [moderator.to_mapping() for moderator in self.moderators],
        }
        if self.source_snapshot is not None:
            mapping["source_snapshot"] = self.source_snapshot.to_mapping()
        return mapping

    @classmethod
    def from_mapping(cls, value: object) -> MetaRegressionInputSnapshot:
        fields = {
            "version", "data_type", "outcome", "time_point", "groups",
            "metric", "studies", "moderators",
        }
        if not isinstance(value, Mapping) or set(value) not in (fields, fields | {"source_snapshot"}):
            raise ValueError("meta-regression input snapshot has unknown or missing fields")
        source = cast(Mapping[str, object], value)
        groups = source["groups"]
        studies = source["studies"]
        moderators = source["moderators"]
        if not isinstance(groups, list) or not isinstance(studies, list) or not isinstance(moderators, list):
            raise ValueError("meta-regression input rows must be lists")
        data_type = source["data_type"]
        if data_type not in ("binary", "continuous", "diagnostic"):
            raise ValueError("unsupported meta-regression data family")
        source_snapshot_value = source.get("source_snapshot")
        source_snapshot: BinaryInputSnapshot | ContinuousInputSnapshot | None = None
        if source_snapshot_value is not None:
            if data_type == "binary":
                source_snapshot = _binary_snapshot_from_mapping(source_snapshot_value)
            elif data_type == "continuous":
                source_snapshot = ContinuousInputSnapshot.from_mapping(source_snapshot_value)
            else:
                raise ValueError("diagnostic meta-regression cannot include a generic source snapshot")
        return cls(
            version=_integer(source["version"], "snapshot version"),
            data_type=cast(DataFamily, data_type),
            outcome=_text(source["outcome"], "outcome"),
            time_point=_text(source["time_point"], "time point"),
            groups=tuple(_text(group, "study group") for group in groups),
            metric=_text(source["metric"], "measure"),
            studies=tuple(_study_input(item) for item in studies),
            moderators=tuple(_covariate_input(item) for item in moderators),
            source_snapshot=source_snapshot,
        )


@dataclass(frozen=True, slots=True)
class MetaRegressionRunRequest:
    """Supported model settings for one generic or joint run."""

    data_type: DataFamily
    metric: str
    missing_moderator_policy: MissingPolicy = "reject"
    heterogeneity_method: HeterogeneityMethod = "REML"
    inference_method: InferenceMethod = "z"
    confidence_level: float = 95.0
    estimator: Literal["REML", "ML"] = "REML"
    correction_factor: float = 0.5
    correction_policy: str = "All studies if any zero exists"
    digits: int = 3
    create_plot: bool = True
    plot_output_path: str | None = None
    plot_display_path: str | None = None
    version: int = 1

    def __post_init__(self) -> None:
        if type(self.version) is not int or self.version != 1:
            raise ValueError("unsupported meta-regression request version")
        if self.data_type not in ("binary", "continuous", "diagnostic"):
            raise ValueError("unsupported meta-regression request family")
        _text(self.metric, "measure")
        if self.missing_moderator_policy not in ("reject", "exclude"):
            raise ValueError("missing moderator policy must be reject or exclude")
        if self.data_type != "diagnostic":
            if self.heterogeneity_method not in {
                "HE", "DL", "HS", "HSk", "SJ", "ML", "REML", "EB", "PM", "PMM"
            }:
                raise ValueError("unsupported meta-regression heterogeneity method")
            if self.inference_method not in {"z", "t", "knha", "adhoc"}:
                raise ValueError("unsupported meta-regression inference method")
        else:
            if self.estimator not in {"REML", "ML"}:
                raise ValueError("Reitsma estimator must be REML or ML")
            if self.correction_policy not in {
                "Studies with any zero cell", "All studies if any zero exists", "None"
            }:
                raise ValueError("unsupported Reitsma correction policy")
            if _finite(self.correction_factor, "Reitsma correction factor") < 0:
                raise ValueError("Reitsma correction factor cannot be negative")
        confidence = _finite(self.confidence_level, "confidence level")
        if not 0 < confidence < 100:
            raise ValueError("confidence level must be between 0 and 100")
        if type(self.digits) is not int or not 0 <= self.digits <= 15:
            raise ValueError("display digits must be between 0 and 15")
        if type(self.create_plot) is not bool:
            raise ValueError("create_plot must be boolean")
        for path, label in (
            (self.plot_output_path, "plot output"),
            (self.plot_display_path, "plot display"),
        ):
            if path is not None and (not isinstance(path, str) or not path.strip()):
                raise ValueError(f"{label} path must be non-empty text or missing")

    @property
    def method(self) -> str:
        return "diagnostic.reitsma" if self.data_type == "diagnostic" else "meta.regression"

    @property
    def metric_for_authority(self) -> str:
        # RCMetaR's request validator takes one metric label; the selected
        # Reitsma method itself always returns both modeled coefficient sides.
        return "Sens" if self.data_type == "diagnostic" else self.metric

    def to_mapping(self) -> dict[str, object]:
        if self.data_type == "diagnostic":
            params: dict[str, object] = {
                "estimator": self.estimator,
                "adjust": self.correction_factor,
                "correction.policy": self.correction_policy,
                "conf.level": self.confidence_level,
                "digits": self.digits,
                "create.plot": self.create_plot,
                "joint.metrics": "Sens,Spec",
            }
            if self.plot_output_path is not None:
                params["fp_outpath"] = self.plot_output_path
            if self.plot_display_path is not None:
                params["fp_display_path"] = self.plot_display_path
        else:
            params = {
                "rm.method": self.heterogeneity_method,
                "inference.method": self.inference_method,
                "conf.level": self.confidence_level,
                "digits": self.digits,
            }
            if self.plot_output_path is not None:
                params["bp_outpath"] = self.plot_output_path
            if self.plot_display_path is not None:
                params["bp_display_path"] = self.plot_display_path
        return {
            "version": self.version,
            "data_type": self.data_type,
            "workflow": "meta-regression",
            "method": self.method,
            "metric": self.metric_for_authority,
            "missing_moderator_policy": self.missing_moderator_policy,
            "params": params,
        }

    @classmethod
    def from_mapping(cls, value: object) -> MetaRegressionRunRequest:
        source = _exact_mapping(
            value,
            {"version", "data_type", "workflow", "method", "metric", "missing_moderator_policy", "params"},
            "meta-regression request",
        )
        data_type = source["data_type"]
        if data_type not in ("binary", "continuous", "diagnostic"):
            raise ValueError("unsupported meta-regression request family")
        if source["workflow"] != "meta-regression":
            raise ValueError("meta-regression request must identify its workflow")
        settings_value = source["params"]
        if not isinstance(settings_value, Mapping):
            raise ValueError("meta-regression request params must be an object")
        settings = cast(Mapping[str, object], settings_value)
        if data_type == "diagnostic":
            expected = {"estimator", "adjust", "correction.policy", "conf.level", "digits", "create.plot", "joint.metrics"}
            allowed = expected | {"fp_outpath", "fp_display_path"}
            if not expected.issubset(settings) or not set(settings).issubset(allowed) or settings.get("joint.metrics") != "Sens,Spec":
                raise ValueError("Reitsma meta-regression requires paired sensitivity/specificity settings")
            method = "diagnostic.reitsma"
            if source["method"] != method or source["metric"] != "Sens":
                raise ValueError("diagnostic meta-regression must remain one joint Reitsma request")
            return cls(
                data_type="diagnostic",
                metric="Sensitivity and specificity",
                missing_moderator_policy=cast(MissingPolicy, source["missing_moderator_policy"]),
                estimator=cast(Literal["REML", "ML"], settings["estimator"]),
                correction_factor=_finite(settings["adjust"], "Reitsma correction factor"),
                correction_policy=_text(settings["correction.policy"], "correction policy"),
                confidence_level=_finite(settings["conf.level"], "confidence level"),
                digits=_integer(settings["digits"], "display digits"),
                create_plot=_boolean(settings["create.plot"], "create.plot"),
                plot_output_path=_optional_text(settings.get("fp_outpath"), "plot output path"),
                plot_display_path=_optional_text(settings.get("fp_display_path"), "plot display path"),
                version=_integer(source["version"], "request version"),
            )
        expected = {"rm.method", "inference.method", "conf.level", "digits"}
        allowed = expected | {"bp_outpath", "bp_display_path"}
        if not expected.issubset(settings) or not set(settings).issubset(allowed) or source["method"] != "meta.regression":
            raise ValueError("generic meta-regression settings are incomplete or unsupported")
        return cls(
            data_type=cast(DataFamily, data_type),
            metric=_text(source["metric"], "measure"),
            missing_moderator_policy=cast(MissingPolicy, source["missing_moderator_policy"]),
            heterogeneity_method=cast(
                HeterogeneityMethod,
                _text(settings["rm.method"], "heterogeneity method"),
            ),
            inference_method=cast(
                InferenceMethod,
                _text(settings["inference.method"], "inference method"),
            ),
            confidence_level=_finite(settings["conf.level"], "confidence level"),
            digits=_integer(settings["digits"], "display digits"),
            plot_output_path=_optional_text(settings.get("bp_outpath"), "plot output path"),
            plot_display_path=_optional_text(settings.get("bp_display_path"), "plot display path"),
            version=_integer(source["version"], "request version"),
        )


@dataclass(frozen=True, slots=True)
class MetaRegressionExecution:
    result: AnalysisResult
    numerics: MetaRegressionNumerics | ReitsmaMetaRegressionResult
    plan: MetaRegressionPlan | None = None


@dataclass(frozen=True, slots=True)
class _FrozenSource:
    snapshot: BinaryInputSnapshot | ContinuousInputSnapshot | None
    outcome: str
    time_point: str
    groups: tuple[str, ...]
    metric: str
    studies: tuple[MetaRegressionStudyInput, ...]
    study_ids: tuple[int, ...]


def freeze_meta_regression_input(
    model: MetaRegressionModel,
    selected_moderators: Sequence[MetaRegressionCovariateInput],
) -> MetaRegressionInputSnapshot:
    """Freeze selected effects, their source rows, and moderator values."""
    family = model.get_current_outcome_type()
    if family not in ("binary", "continuous", "diagnostic"):
        raise ValueError("Choose a supported outcome before running meta-regression")
    source = _freeze_meta_regression_source(model, cast(DataFamily, family))
    frozen_moderators = _freeze_selected_moderators(
        model, source, selected_moderators
    )
    return MetaRegressionInputSnapshot(
        version=1,
        data_type=cast(DataFamily, family),
        outcome=source.outcome,
        time_point=source.time_point,
        groups=source.groups,
        metric=source.metric,
        studies=source.studies,
        moderators=frozen_moderators,
        source_snapshot=source.snapshot,
    )


def _freeze_meta_regression_source(
    model: MetaRegressionModel, family: DataFamily
) -> _FrozenSource:
    if family == "diagnostic":
        return _freeze_diagnostic_meta_regression_source(model)
    return _freeze_generic_meta_regression_source(model, family)


def _freeze_diagnostic_meta_regression_source(model: MetaRegressionModel) -> _FrozenSource:
    outcome = _required_selection(model.current_outcome_name, "an outcome")
    time_point = _required_selection(model.get_current_follow_up_name(), "a time point")
    studies = tuple(model.get_studies(only_if_included=True))
    ids = tuple(_integer(study.id, "study id") for study in studies)
    if not studies:
        raise ValueError("Include at least one study before running meta-regression")
    from rc_metastudio.reitsma_analysis import freeze_reitsma_input

    counts = freeze_reitsma_input(cast(ReitsmaModel, model))
    rows = tuple(
        MetaRegressionStudyInput(
            study.id, study.name, None, None, None,
            study.tp, study.fn, study.fp, study.tn,
        )
        for study in counts.studies
    )
    return _FrozenSource(
        None, outcome, time_point,
        tuple(str(value) for value in model.get_current_groups()),
        "Sensitivity and specificity", rows, ids,
    )


def _required_selection(value: str | None, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Select {label} before running meta-regression")
    return value


def _freeze_generic_meta_regression_source(
    model: MetaRegressionModel, family: Literal["binary", "continuous"]
) -> _FrozenSource:
    if family == "binary":
        snapshot = freeze_binary_input(cast(BinaryInputModel, model))
        outcome, time_point = snapshot.outcome, snapshot.time_point
    else:
        snapshot = freeze_continuous_input(cast(ContinuousDatasetModel, model))
        outcome, time_point = snapshot.outcome, snapshot.follow_up
    source_studies = snapshot.studies
    ids = tuple(
        item.study_id if isinstance(item, ContinuousStudyInput) else item.id
        for item in source_studies
    )
    rows = tuple(
        MetaRegressionStudyInput(
            id=(item.study_id if isinstance(item, ContinuousStudyInput) else item.id),
            name=item.name,
            year=item.year,
            estimate=item.estimate,
            standard_error=item.standard_error,
        )
        for item in source_studies
    )
    return _FrozenSource(
        snapshot, outcome, time_point, snapshot.groups, snapshot.metric, rows, ids
    )


def _freeze_selected_moderators(
    model: MetaRegressionModel,
    source: _FrozenSource,
    selected_moderators: Sequence[MetaRegressionCovariateInput],
) -> tuple[MetaRegressionCovariateInput, ...]:
    if len({moderator.name for moderator in selected_moderators}) != len(selected_moderators):
        raise ValueError("selected moderators must be unique")
    frozen_moderators = []
    for selection in selected_moderators:
        values = _moderator_values(model, source, selection)
        frozen_moderators.append(
            MetaRegressionCovariateInput(
                selection.name,
                selection.kind,
                values,
                selection.unit,
                selection.unit_step,
                selection.reference_level,
            )
        )
    return tuple(frozen_moderators)


def _moderator_values(
    model: MetaRegressionModel,
    source: _FrozenSource,
    selection: MetaRegressionCovariateInput,
) -> tuple[object, ...]:
    if source.snapshot is None:
        values_by_id = model.dataset.get_covariate_values(
            selection.name, ids_for_keys=True
        )
        return tuple(
            _covariate_value(values_by_id.get(study_id), selection.kind)
            for study_id in source.study_ids
        )
    covariate = next(
        (
            item
            for item in source.snapshot.covariates
            if item.name == selection.name
        ),
        None,
    )
    if covariate is None:
        raise ValueError(
            f"Selected moderator '{selection.name}' is missing from the frozen study data"
        )
    if covariate.data_type != selection.kind:
        raise ValueError(
            f"Selected moderator '{selection.name}' has changed data type"
        )
    return tuple(
        _covariate_value(value, selection.kind) for value in covariate.values
    )


def execute_meta_regression(
    snapshot: MetaRegressionInputSnapshot,
    request: MetaRegressionRunRequest,
    bridge: MetaRegressionBridge,
) -> MetaRegressionExecution:
    if snapshot.data_type != request.data_type:
        raise ValueError("meta-regression input family does not match its request")
    if snapshot.metric != request.metric and request.data_type != "diagnostic":
        raise ValueError("meta-regression measure does not match its frozen input")
    if request.data_type == "diagnostic":
        return _execute_reitsma_meta_regression(snapshot, request, bridge)
    return _execute_generic_meta_regression(snapshot, request, bridge)


def _execute_generic_meta_regression(
    snapshot: MetaRegressionInputSnapshot,
    request: MetaRegressionRunRequest,
    bridge: MetaRegressionBridge,
) -> MetaRegressionExecution:
    study_rows = snapshot.studies
    source_snapshot = snapshot.source_snapshot
    if source_snapshot is not None and _source_has_raw_effects(source_snapshot):
        effects = _reconstruct_source_effects(source_snapshot, bridge)
        study_rows = tuple(
            replace(
                study,
                estimate=effects[index][0],
                standard_error=effects[index][1],
            )
            for index, study in enumerate(study_rows)
        )
    studies = tuple(
        MetaRegressionStudy(
            row.id,
            row.name,
            cast(float, row.estimate),
            cast(float, row.standard_error),
        )
        for row in study_rows
    )
    moderators = _moderators_from_snapshot(snapshot, bridge)
    core_request = MetaRegressionRequest(
        studies=studies,
        moderators=moderators,
        heterogeneity_method=request.heterogeneity_method,
        inference_method=request.inference_method,
        confidence_level=request.confidence_level,
        missing_moderator_policy=request.missing_moderator_policy,
        metric=snapshot.metric,
    )
    plan = prepare_meta_regression(core_request)
    result = _run_generic_authority(snapshot, request, plan, bridge)
    raw = bridge.ro.globalenv["result"]
    fit_r = cast(_RList, raw).rx2("res")
    fit = bridge.r_object_to_python(fit_r)
    factor_tests = _generic_factor_tests(plan, fit_r, bridge)
    numerics = parse_meta_regression_result(plan, fit, moderator_tests=factor_tests)
    return MetaRegressionExecution(
        _attach_numerics(
            result, "meta_regression_numerics", numerics.to_mapping()
        ),
        numerics,
        plan,
    )


def _moderators_from_snapshot(
    snapshot: MetaRegressionInputSnapshot,
    bridge: MetaRegressionBridge,
) -> tuple[Moderator, ...]:
    moderators: list[Moderator] = []
    for covariate in snapshot.moderators:
        if covariate.kind == "continuous":
            moderators.append(
                ContinuousModerator(
                    covariate.name, covariate.unit, covariate.values,
                    covariate.unit_step,
                )
            )
        else:
            nonmissing = [str(value) for value in covariate.values if not _missing(value)]
            levels = _authority_levels(nonmissing, bridge)
            moderators.append(
                FactorModerator(
                    covariate.name,
                    cast(str, covariate.reference_level),
                    levels,
                    covariate.values,
                )
            )
    return tuple(moderators)


def _reconstruct_source_effects(
    snapshot: BinaryInputSnapshot | ContinuousInputSnapshot,
    bridge: MetaRegressionBridge,
) -> tuple[tuple[float, float], ...]:
    """Use the pinned RCMetaR preparation boundary for frozen raw rows."""
    if isinstance(snapshot, BinaryInputSnapshot):
        from rc_metastudio.analysis_worker_support import _create_binary_data

        backend_data = _create_binary_data(snapshot, bridge)
        metric = snapshot.metric
    else:
        backend_data = create_continuous_backend_data(
            snapshot, cast(ContinuousBridge, bridge)
        )
        metric = _rcmetar_metric(snapshot.metric)
    bridge.ro.globalenv["tmp_obj"] = backend_data
    parameter_values: dict[str, object] = {"measure": metric}
    if isinstance(snapshot, BinaryInputSnapshot):
        # RCMetaR's raw preview delegates to metafor::escalc with add=1/2,to=only0.
        # Omitting these defaults leaves raw zero-cell studies as NA here.
        parameter_values.update(adjust=0.5, to="only0")
    parameters = bridge.execute_r_function("list", **parameter_values)
    prepared = bridge.execute_r_function(
        "rcmetar.prepare.analysis.data", backend_data, parameters
    )
    estimates = bridge.r_object_to_python(
        bridge.execute_r_function("slot", prepared, "y")
    )
    standard_errors = bridge.r_object_to_python(
        bridge.execute_r_function("slot", prepared, "SE")
    )
    study_names = tuple(study.name for study in snapshot.studies)
    estimate_values = _worker_effect_vector(
        estimates, study_names, "estimate"
    )
    standard_error_values = _worker_effect_vector(
        standard_errors, study_names, "standard error"
    )
    return tuple(zip(estimate_values, standard_error_values, strict=True))


def _worker_effect_vector(
    value: object, study_names: Sequence[str], label: str
) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != len(study_names):
        raise ValueError(
            f"RCMetaR returned the wrong number of meta-regression {label} values "
            f"for {len(study_names)} included studies"
        )
    result = tuple(
        _finite(item, f"RCMetaR {label} for study '{study_names[index]}'")
        for index, item in enumerate(value)
    )
    if label == "standard error" and any(item < 0 for item in result):
        raise ValueError("RCMetaR returned a negative meta-regression standard error")
    return result


def _source_has_raw_effects(
    snapshot: BinaryInputSnapshot | ContinuousInputSnapshot | None,
) -> bool:
    if isinstance(snapshot, BinaryInputSnapshot):
        return snapshot.raw_counts_available
    return isinstance(snapshot, ContinuousInputSnapshot) and snapshot.raw_measurements_complete


def _validate_source_snapshot(snapshot: MetaRegressionInputSnapshot) -> None:
    source = _validated_source_context(snapshot)
    _validate_source_studies(snapshot, source)
    _validate_source_moderators(snapshot, source)


def _validated_source_context(
    snapshot: MetaRegressionInputSnapshot,
) -> BinaryInputSnapshot | ContinuousInputSnapshot:
    source = _source_snapshot_for_family(snapshot)
    source_time_point = (
        source.follow_up if isinstance(source, ContinuousInputSnapshot) else source.time_point
    )
    if (
        snapshot.outcome != source.outcome
        or snapshot.time_point != source_time_point
        or snapshot.groups != source.groups
        or snapshot.metric != source.metric
    ):
        raise ValueError("meta-regression source snapshot context does not match its inputs")
    return source


def _source_snapshot_for_family(
    snapshot: MetaRegressionInputSnapshot,
) -> BinaryInputSnapshot | ContinuousInputSnapshot:
    source = snapshot.source_snapshot
    if snapshot.data_type == "binary":
        if not isinstance(source, BinaryInputSnapshot):
            raise ValueError("binary meta-regression needs a binary source snapshot")
        return source
    if snapshot.data_type == "continuous":
        if not isinstance(source, ContinuousInputSnapshot):
            raise ValueError("continuous meta-regression needs a continuous source snapshot")
        return source
    raise ValueError("diagnostic meta-regression cannot include a generic source snapshot")


def _validate_source_studies(
    snapshot: MetaRegressionInputSnapshot,
    source: BinaryInputSnapshot | ContinuousInputSnapshot,
) -> None:
    if isinstance(source, ContinuousInputSnapshot):
        source_studies = source.studies
        source_ids = tuple(study.study_id for study in source.studies)
    else:
        source_studies = source.studies
        source_ids = tuple(study.id for study in source.studies)
    if len(source_ids) != len(snapshot.studies):
        raise ValueError("meta-regression source rows do not match its study rows")
    raw = _source_has_raw_effects(source)
    for source_study, study, source_id in zip(
        source_studies, snapshot.studies, source_ids, strict=True
    ):
        _validate_source_study(study, source_study, source_id, raw)


def _validate_source_study(
    study: MetaRegressionStudyInput,
    source_study: BinaryStudyInput | SingleArmBinaryStudyInput | ContinuousStudyInput,
    source_id: int,
    raw: bool,
) -> None:
    if (study.id, study.name, study.year) != (
        source_id, source_study.name, source_study.year,
    ):
        raise ValueError("meta-regression source study order does not match its rows")
    if raw:
        if study.estimate is not None or study.standard_error is not None:
            raise ValueError("raw meta-regression rows must not retain derived effects")
    elif (study.estimate, study.standard_error) != (
        source_study.estimate, source_study.standard_error,
    ):
        raise ValueError("entered meta-regression effects must match the source snapshot")


def _validate_source_moderators(
    snapshot: MetaRegressionInputSnapshot,
    source: BinaryInputSnapshot | ContinuousInputSnapshot,
) -> None:
    source_covariates = {item.name: item for item in source.covariates}
    for moderator in snapshot.moderators:
        covariate = source_covariates.get(moderator.name)
        if covariate is None or covariate.data_type != moderator.kind:
            raise ValueError(
                f"meta-regression moderator '{moderator.name}' does not match the source snapshot"
            )
        values = tuple(
            _covariate_value(value, moderator.kind) for value in covariate.values
        )
        if values != moderator.values:
            raise ValueError(
                f"meta-regression moderator '{moderator.name}' values do not match the source snapshot"
            )


def _binary_snapshot_from_mapping(value: object) -> BinaryInputSnapshot:
    fields = {
        "version", "outcome", "time_point", "groups", "metric",
        "raw_counts_available", "studies", "covariates",
    }
    source = _exact_mapping(value, fields, "binary source snapshot")
    groups, studies, covariates = (
        source["groups"], source["studies"], source["covariates"]
    )
    if (
        not isinstance(groups, list)
        or not isinstance(studies, list)
        or not isinstance(covariates, list)
        or type(source["raw_counts_available"]) is not bool
    ):
        raise ValueError("binary source snapshot rows are malformed")
    metric = _text(source["metric"], "binary source measure")
    one_arm = metric in BINARY_ONE_ARM_METRICS
    study_rows = tuple(_binary_study_from_mapping(item, one_arm) for item in studies)
    covariate_rows = tuple(_binary_covariate_from_mapping(item) for item in covariates)
    return BinaryInputSnapshot(
        version=_integer(source["version"], "binary source snapshot version"),
        outcome=_text(source["outcome"], "binary source outcome"),
        time_point=_text(source["time_point"], "binary source time point"),
        groups=tuple(_text(item, "binary source group") for item in groups),
        metric=metric,
        raw_counts_available=source["raw_counts_available"],
        studies=study_rows,
        covariates=covariate_rows,
    )


def _binary_study_from_mapping(
    item: object, one_arm: bool
) -> BinaryStudyInput | SingleArmBinaryStudyInput:
    shared = {"id", "name", "year", "estimate", "standard_error"}
    if one_arm:
        row = _exact_mapping(
            item, shared | {"events", "total"}, "single-arm binary source study"
        )
        return SingleArmBinaryStudyInput(
            id=_integer(row["id"], "study id"),
            name=_text(row["name"], "study name"),
            year=None if row["year"] is None else _integer(row["year"], "study year"),
            estimate=_optional_finite(row["estimate"], "study estimate"),
            standard_error=_optional_finite(row["standard_error"], "study standard error"),
            events=_optional_integer(row["events"], "study events"),
            total=_optional_integer(row["total"], "study total"),
        )
    row = _exact_mapping(
        item,
        shared | {"treatment_events", "treatment_total", "control_events", "control_total"},
        "two-arm binary source study",
    )
    return BinaryStudyInput(
        id=_integer(row["id"], "study id"),
        name=_text(row["name"], "study name"),
        year=None if row["year"] is None else _integer(row["year"], "study year"),
        estimate=_optional_finite(row["estimate"], "study estimate"),
        standard_error=_optional_finite(row["standard_error"], "study standard error"),
        treatment_events=_optional_integer(row["treatment_events"], "treatment events"),
        treatment_total=_optional_integer(row["treatment_total"], "treatment total"),
        control_events=_optional_integer(row["control_events"], "control events"),
        control_total=_optional_integer(row["control_total"], "control total"),
    )


def _binary_covariate_from_mapping(item: object) -> BinaryCovariateInput:
    row = _exact_mapping(item, {"name", "data_type", "values"}, "binary source covariate")
    values = row["values"]
    data_type = row["data_type"]
    if data_type not in ("continuous", "factor") or not isinstance(values, list):
        raise ValueError("binary source covariate is malformed")
    return BinaryCovariateInput(
        _text(row["name"], "covariate name"),
        cast(str, data_type),
        tuple(_snapshot_scalar(value) for value in values),
    )


def _snapshot_scalar(value: object) -> SnapshotValue:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    return _finite(value, "binary source covariate value")


def _run_generic_authority(
    snapshot: MetaRegressionInputSnapshot,
    request: MetaRegressionRunRequest,
    plan: MetaRegressionPlan,
    bridge: MetaRegressionBridge,
) -> AnalysisResult:
    from rc_metastudio.analysis_worker_support import _wire_result

    data = _generic_authority_data(snapshot, plan, bridge)
    bridge.ro.globalenv["tmp_obj"] = data
    result = bridge.run_versioned_analysis_request(
        {
            "version": 1,
            "data_type": snapshot.data_type,
            "workflow": "meta-regression",
            "method": "meta.regression",
            "metric": snapshot.metric,
            "params": _generic_authority_params(snapshot, request, plan),
        }
    )
    wire = _wire_result(result)
    if not isinstance(wire, dict):
        raise TypeError("RCMetaR meta-regression result is not serializable")
    _append_plan_report(wire, snapshot, request, plan)
    return _parse_result_with_numerics(wire)


def _generic_authority_data(
    snapshot: MetaRegressionInputSnapshot,
    plan: MetaRegressionPlan,
    bridge: MetaRegressionBridge,
) -> object:
    planned = plan.studies
    covariates = _generic_authority_covariates(plan, bridge)
    kwargs: dict[str, object] = {
        "y": bridge._r_numeric_vector([study.estimate for study in planned]),
        "SE": bridge._r_numeric_vector([study.standard_error for study in planned]),
        "study.names": bridge._r_character_vector([study.label for study in planned]),
        "years": bridge._r_year_vector(
            [next(row.year for row in snapshot.studies if row.id == study.id) for study in planned]
        ),
        "covariates": covariates,
    }
    constructor = (
        "rcmetar.create.binary.data"
        if snapshot.data_type == "binary"
        else "rcmetar.create.continuous.data"
    )
    return bridge.execute_r_function(constructor, **kwargs)


def _generic_authority_covariates(
    plan: MetaRegressionPlan, bridge: MetaRegressionBridge
) -> object:
    covariate_values = []
    for index, coding in enumerate(plan.moderators):
        values = [study.moderator_values[index] for study in plan.studies]
        if coding.kind == "continuous":
            converted = bridge._r_numeric_vector(values)
        else:
            converted = bridge._r_character_vector([str(value) for value in values])
        covariate_values.append(
            bridge.execute_r_function(
                "rcmetar.create.covariate.values",
                **{
                    "cov.name": coding.name,
                    "cov.vals": converted,
                    "cov.type": coding.kind,
                    "ref.var": coding.reference_level or "",
                },
            )
        )
    return bridge.execute_r_function("list", *covariate_values)


def _generic_authority_params(
    snapshot: MetaRegressionInputSnapshot,
    request: MetaRegressionRunRequest,
    plan: MetaRegressionPlan,
) -> dict[str, object]:
    params = {
        "measure": snapshot.metric,
        "rm.method": request.heterogeneity_method,
        "inference.method": request.inference_method,
        "conf.level": request.confidence_level,
        "digits": request.digits,
    }
    if _single_continuous_moderator(plan):
        if request.plot_output_path:
            params["bp_outpath"] = request.plot_output_path
        if request.plot_display_path:
            params["bp_display_path"] = request.plot_display_path
    return params


def _generic_factor_tests(
    plan: MetaRegressionPlan, fit: object, bridge: MetaRegressionBridge
) -> dict[str, object]:
    if not any(coding.kind == "factor" for coding in plan.moderators):
        return {}
    classes = bridge.r_object_to_python(bridge.execute_r_function("class", fit))
    if not isinstance(classes, (list, tuple)) or "rma" not in classes:
        # RCMetaR 0.4.1 appends adjusted-mean fields with c(), which drops the
        # metafor S3 class from this otherwise complete rma.uni fit list.
        fit = bridge.execute_r_function(
            "structure",
            fit,
            **{"class": bridge._r_character_vector(("rma.uni", "rma"))},
        )
    tests: dict[str, object] = {}
    coefficient_positions_by_moderator: dict[str, list[int]] = {}
    for index, term in enumerate(plan.coefficient_terms[1:], start=2):
        if term.kind == "factor_level" and term.moderator_name is not None:
            coefficient_positions_by_moderator.setdefault(term.moderator_name, []).append(index)
    for coding in plan.moderators:
        if coding.kind != "factor":
            continue
        positions = coefficient_positions_by_moderator[coding.name]
        result = bridge.execute_r_function(
            "anova", fit, btt=bridge.ro.IntVector(positions)
        )
        values = bridge.r_object_to_python(result)
        if not isinstance(values, Mapping):
            raise ValueError(f"RCMetaR did not return a joint test for '{coding.name}'")
        test_values = cast(Mapping[str, object], values)
        statistic = test_values.get("QM")
        if statistic is None:
            statistic = test_values.get("F")
        tests[coding.name] = {
            "statistic": statistic,
            "degrees_of_freedom": test_values.get("m", len(positions)),
            "denominator_degrees_of_freedom": (
                plan.residual_degrees_of_freedom
                if plan.request.inference_method != "z"
                else None
            ),
            "p_value": test_values.get("QMp"),
        }
    return tests


def _execute_reitsma_meta_regression(
    snapshot: MetaRegressionInputSnapshot,
    request: MetaRegressionRunRequest,
    bridge: MetaRegressionBridge,
) -> MetaRegressionExecution:
    from rc_metastudio.analysis_worker_support import _wire_result

    eligible: list[MetaRegressionStudyInput] = []
    exclusions: list[ReitsmaExcludedStudy] = []
    for index, study in enumerate(snapshot.studies):
        missing = tuple(
            moderator.name
            for moderator in snapshot.moderators
            if _missing(moderator.values[index])
        )
        if missing:
            if request.missing_moderator_policy == "reject":
                raise ValueError(
                    f"Study '{study.name}' has missing selected moderator values: "
                    + ", ".join(missing)
                    + "; correct them or explicitly choose exclusion."
                )
            exclusions.append(
                ReitsmaExcludedStudy(
                    str(study.id), "Missing moderator value(s): " + ", ".join(missing)
                )
            )
        else:
            eligible.append(study)
    eligible_ids = {study.id for study in eligible}
    if not eligible:
        raise ValueError("No included studies remain eligible for selected moderators")
    reitsma_snapshot = ReitsmaInputSnapshot(
        1,
        snapshot.outcome,
        snapshot.time_point,
        cast(tuple[str], snapshot.groups),
        tuple(
            ReitsmaStudyInput(study.id, study.name, study.tp, study.fn, study.fp, study.tn)
            for study in eligible
        ),
    )
    covariates = []
    for moderator in snapshot.moderators:
        values = [
            moderator.values[index]
            for index, row in enumerate(snapshot.studies)
            if row.id in eligible_ids
        ]
        if moderator.kind == "continuous":
            scaled = [_finite(value, moderator.name) / moderator.unit_step for value in values]
            r_values = bridge._r_numeric_vector(scaled)
            reference = ""
        else:
            r_values = bridge._r_character_vector([str(value) for value in values])
            reference = cast(str, moderator.reference_level)
        covariates.append(
            bridge.execute_r_function(
                "rcmetar.create.covariate.values",
                **{
                    "cov.name": moderator.name,
                    "cov.vals": r_values,
                    "cov.type": moderator.kind,
                    "ref.var": reference,
                },
            )
        )
    r_covariates = bridge.execute_r_function("list", *covariates)
    data = bridge.execute_r_function(
        "rcmetar.create.diagnostic.data",
        TP=bridge._r_numeric_vector([study.tp for study in eligible]),
        FN=bridge._r_numeric_vector([study.fn for study in eligible]),
        FP=bridge._r_numeric_vector([study.fp for study in eligible]),
        TN=bridge._r_numeric_vector([study.tn for study in eligible]),
        **{
            "study.names": bridge._r_character_vector([study.name for study in eligible]),
            "covariates": r_covariates,
        },
    )
    _validate_authority_counts(reitsma_snapshot, data, cast(ReitsmaBridge, bridge))
    bridge.ro.globalenv["tmp_obj"] = data
    params = {
        "estimator": request.estimator,
        "adjust": request.correction_factor,
        "correction.policy": request.correction_policy,
        "conf.level": request.confidence_level,
        "digits": request.digits,
        "create.plot": request.create_plot,
        "joint.metrics": "Sens,Spec",
    }
    if request.plot_output_path:
        params["fp_outpath"] = request.plot_output_path
    if request.plot_display_path:
        params["fp_display_path"] = request.plot_display_path
    result = bridge.run_versioned_analysis_request(
        {
            "version": 1,
            "data_type": "diagnostic",
            "workflow": "meta-regression",
            "method": "diagnostic.reitsma",
            "metric": "Sens",
            "params": params,
        }
    )
    raw = bridge.ro.globalenv["result"]
    summary_r = cast(_RList, raw).rx2("Summary")
    summary = _reitsma_summary_mapping(summary_r, bridge)
    numerics = parse_reitsma_meta_regression_result(
        summary,
        eligible_study_ids=tuple(str(study.id) for study in eligible),
        exclusions=tuple(exclusions),
    )
    wire = _wire_result(result)
    if not isinstance(wire, dict):
        raise TypeError("RCMetaR Reitsma meta-regression result is not serializable")
    return MetaRegressionExecution(
        _attach_numerics(
            _parse_result_with_numerics(wire),
            "reitsma_meta_regression_numerics",
            numerics.to_mapping(),
        ),
        numerics,
    )


def _reitsma_summary_mapping(
    summary: object, bridge: MetaRegressionBridge
) -> Mapping[str, object]:
    serializer = bridge.execute_r_string(
        "(function(summary) {\n"
        "  for (key in c('Sensitivity coefficients', 'Specificity coefficients')) {\n"
        "    table <- as.data.frame(summary[[key]], check.names=FALSE)\n"
        "    table$term <- rownames(table)\n"
        "    summary[[key]] <- table\n"
        "  }\n"
        "  jsonlite::toJSON(summary, auto_unbox=TRUE, dataframe='rows', na='null', digits=16)\n"
        "})"
    )
    encoded = cast(Callable[[object], object], serializer)(summary)
    encoded_values = cast(Sequence[object], encoded)
    decoded = json.loads(str(encoded_values[0]))
    if not isinstance(decoded, Mapping):
        raise ValueError("RCMetaR Reitsma Summary must be a mapping")
    return cast(Mapping[str, object], decoded)


def _append_plan_report(
    result: dict[str, object],
    snapshot: MetaRegressionInputSnapshot,
    request: MetaRegressionRunRequest,
    plan: MetaRegressionPlan,
) -> None:
    texts_value = result.get("texts")
    sections_value = result.get("sections")
    if not isinstance(texts_value, dict) or not isinstance(sections_value, list):
        raise ValueError("RCMetaR result is missing display sections")
    texts = cast(dict[str, str], texts_value)
    sections = cast(list[dict[str, object]], sections_value)
    included = ", ".join(study.label for study in plan.studies)
    excluded = "; ".join(
        f"{study.label} (missing {', '.join(study.missing_moderators)})"
        for study in plan.excluded_studies
    ) or "None"
    text = (
        f"Formula: {plan.formula}\n"
        f"Effect measure: {snapshot.metric}\n"
        f"Heterogeneity estimator: {request.heterogeneity_method}\n"
        f"Coefficient inference: {request.inference_method}\n"
        f"Confidence level: {request.confidence_level:g}%\n"
        f"Eligible studies ({plan.eligible_study_count}): {included}\n"
        f"Excluded studies: {excluded}"
    )
    key = "Meta-regression specification"
    if key in texts:
        raise ValueError("RCMetaR unexpectedly returned the meta-regression specification section")
    texts[key] = text
    order = max((section.get("order", -1) for section in sections), default=-1) + 1
    sections.append(
        {
            "id": "meta-regression.specification",
            "kind": "text",
            "order": order,
            "title": key,
            "source_key": key,
        }
    )


def _parse_result_with_numerics(result: dict[str, object]) -> AnalysisResult:
    from rc_metastudio.analysis_results import parse_analysis_result

    return parse_analysis_result(result)


def _attach_numerics(result: AnalysisResult, key: str, mapping: Mapping[str, object]) -> AnalysisResult:
    from rc_metastudio.analysis_results import parse_analysis_result
    from rc_metastudio.analysis_worker_support import _wire_result

    wire = _wire_result(result)
    wire[key] = dict(mapping)
    return parse_analysis_result(wire)


def _single_continuous_moderator(plan: MetaRegressionPlan) -> bool:
    return len(plan.moderators) == 1 and plan.moderators[0].kind == "continuous"


def _authority_levels(
    values: Sequence[str], bridge: MetaRegressionBridge
) -> tuple[str, ...]:
    levels = bridge.execute_r_function(
        "sort", bridge.execute_r_function("unique", bridge._r_character_vector(values))
    )
    result = tuple(str(value) for value in cast(Sequence[object], levels))
    if not result:
        raise ValueError("Selected factor moderator has no non-missing values")
    return result


def _study_input(value: object) -> MetaRegressionStudyInput:
    source = _exact_mapping(
        value,
        {"id", "name", "year", "estimate", "standard_error", "tp", "fn", "fp", "tn"},
        "meta-regression study",
    )
    return MetaRegressionStudyInput(
        id=_integer(source["id"], "study id"),
        name=_text(source["name"], "study name"),
        year=None if source["year"] is None else _integer(source["year"], "study year"),
        estimate=_optional_finite(source["estimate"], "study estimate"),
        standard_error=_optional_finite(source["standard_error"], "study standard error"),
        tp=_optional_integer(source["tp"], "TP count"),
        fn=_optional_integer(source["fn"], "FN count"),
        fp=_optional_integer(source["fp"], "FP count"),
        tn=_optional_integer(source["tn"], "TN count"),
    )


def _covariate_input(value: object) -> MetaRegressionCovariateInput:
    source = _exact_mapping(
        value,
        {"name", "kind", "values", "unit", "unit_step", "reference_level"},
        "meta-regression moderator",
    )
    values = source["values"]
    kind = source["kind"]
    if not isinstance(values, list) or kind not in ("continuous", "factor"):
        raise ValueError("meta-regression moderator values or kind are invalid")
    if kind == "continuous":
        unit = _text(source["unit"], "continuous moderator unit")
        step = _finite(source["unit_step"], "moderator unit step")
        reference = None
    else:
        unit = "unit"
        step = 1.0
        reference = _text(source["reference_level"], "factor reference level")
    return MetaRegressionCovariateInput(
        _text(source["name"], "moderator name"),
        cast(ModeratorKind, kind),
        tuple(values),
        unit,
        step,
        reference,
    )


def _covariate_value(value: object, kind: ModeratorKind) -> object:
    if value is None or value == "":
        return None
    if kind == "factor":
        return str(value)
    return _finite(value, "continuous moderator value")


def _optional_year(value: object) -> int | None:
    if value in (None, ""):
        return None
    if type(value) is int:
        return value
    if isinstance(value, str):
        return int(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    raise ValueError("study year must be an integer or missing")


def _exact_mapping(value: object, fields: set[str], label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{label} must be an object")
    if set(value) != fields:
        raise ValueError(f"{label} has unknown or missing fields")
    return cast(Mapping[str, object], value)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value


def _optional_text(value: object, label: str) -> str | None:
    return None if value is None else _text(value, label)


def _finite(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _optional_finite(value: object, label: str) -> float | None:
    return None if value is None else _finite(value, label)


def _integer(value: object, label: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{label} must be an integer")
    return value


def _boolean(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{label} must be boolean")
    return value


def _optional_integer(value: object, label: str) -> int | None:
    return None if value is None else _integer(value, label)


def _missing(value: object) -> bool:
    return value is None or value == ""
