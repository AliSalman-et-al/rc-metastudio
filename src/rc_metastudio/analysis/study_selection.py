# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Domain operations shared by the dataset table adapter."""

from dataclasses import dataclass
from rc_metastudio.analysis.catalog import (
    BINARY_ONE_ARM_METRICS, CONTINUOUS_ONE_ARM_METRICS, ONE_ARM_METRICS, RAW_FIELDS_PER_ARM,
    RATIO_DATA_TYPES,
)

from collections.abc import Callable, Mapping, Sequence
from typing import Protocol, cast

from rc_metastudio.domain_ids import RowId
from rc_metastudio.project.model import Sheet, StudyRow
from rc_metastudio.project.study import AnalysisUnit, EffectSource
from rc_metastudio.ratio_data import RATIO_FIELDS
from rc_metastudio.analysis.catalog import BINARY, CONTINUOUS, DIAGNOSTIC
from rc_metastudio.analysis.validation import EMPTY_VALS

def comparison_key(sheet: Sheet | None, metric: str | None) -> tuple[str, ...]:
    if sheet is None:
        return ()
    arms = sheet.arms[:1] if metric in ONE_ARM_METRICS else sheet.arms
    return tuple(arm.id for arm in arms)


def display_effect_source(
    unit: AnalysisUnit, metric: str | None, arm_key: tuple[str, ...], arm_names: Sequence[str],
) -> EffectSource:
    selected = unit.calculator_source(metric, arm_key)
    if selected is not None:
        return selected
    return _source_from_raw(unit.get_raw_data_for_arms(arm_names))


def _source_from_raw(raw: Sequence[object]) -> EffectSource:
    return "derived_preview" if any(value not in (None, "") for value in raw) else "entered"


@dataclass(frozen=True, slots=True)
class FitCovariate:
    id: str
    name: str
    data_type: int


@dataclass(frozen=True, slots=True)
class FitStudy:
    id: RowId
    label: str
    year: int | None
    raw: tuple[object, ...]
    effects: tuple[tuple[object, object], ...]
    covariates: tuple[object, ...]
    prefer_entered: bool
    ratio: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class FitSelection:
    source_metric: str | None
    metrics: tuple[str, ...]
    studies: tuple[FitStudy, ...]
    covariates: tuple[FitCovariate, ...]

    def raw_for_fit(self) -> Sequence[Sequence[object]] | None:
        if any(row.prefer_entered for row in self.studies):
            return None
        return _complete_fit_raw_rows([row.raw for row in self.studies], self.source_metric)

    def effects_for(self, metric: str) -> tuple[tuple[object, object], ...]:
        index = self.metrics.index(metric)
        return tuple(row.effects[index] for row in self.studies)


class FitModel(Protocol):
    @property
    def current_sheet(self) -> Sheet | None: ...

    @property
    def current_effect(self) -> str | None: ...

    @property
    def confidence_multiplier(self) -> float: ...


def capture_fit_selection(
    model: FitModel,
    metrics: Sequence[str],
    *,
    covariates: Sequence[Mapping[str, object]] | None = None,
    studies: Sequence[StudyRow] | None = None,
) -> FitSelection:
    """Capture backend inputs from canonical rows before calling the worker."""
    sheet = model.current_sheet
    if sheet is None:
        raise ValueError("Select an outcome before preparing analysis inputs.")
    metrics = tuple(metrics)
    source_metric = model.current_effect if sheet.data_type == DIAGNOSTIC else metrics[0]
    arm_key = comparison_key(sheet, source_metric)
    arm_names = tuple(arm.name for arm in sheet.arms)
    confidence = model.confidence_multiplier
    descriptors = tuple(
        FitCovariate(cast(str, cov["id"]), str(cov["name"]), cast(int, cov["data_type"]))
        for cov in (sheet.covariates if covariates is None else covariates)
    )
    selected_ids = None if studies is None else {study.id for study in studies}
    rows = (
        _capture_fit_study(row, metrics, source_metric, arm_key, arm_names, confidence, descriptors, sheet.data_type)
        for row in sheet.rows if row.include and (selected_ids is None or row.id in selected_ids)
    )
    return FitSelection(source_metric, metrics, tuple(rows), descriptors)


def _capture_fit_study(
    row: StudyRow, metrics: tuple[str, ...], source_metric: str | None,
    arm_key: tuple[str, ...], arm_names: tuple[str, ...], confidence: float,
    covariates: tuple[FitCovariate, ...], data_type: int,
) -> FitStudy:
    unit = row.analysis_unit
    raw = unit.get_raw_data_for_arms(arm_names)
    selected_source = unit.calculator_source(source_metric, arm_key)
    if data_type in RATIO_DATA_TYPES:
        record = unit.ratio_input(arm_names)
        record.validate()
        source = record.selected_source(raw, metric=metrics[0])
        ratio = tuple(source if name == "source" else getattr(record, name) for name in RATIO_FIELDS)
        effects = tuple((None, None) for _ in metrics)
    else:
        ratio = ()
        source = selected_source if selected_source is not None else _source_from_raw(raw)
        effects = tuple(unit.get_effect_and_se_for_source(source, metric, arm_key, confidence) for metric in metrics)
    return FitStudy(
        row.id, row.label, row.year, tuple(raw), effects,
        tuple(row.covariate_values.get(cov.id) for cov in covariates),
        selected_source == "entered", ratio,
    )


def raw_data_is_complete(raw_data: Sequence[object]) -> bool:
    return all(value not in ("", None) for value in raw_data)


def raw_data_is_empty(raw_data: Sequence[object]) -> bool:
    return all(value in EMPTY_VALS for value in raw_data)


def has_entered_data(analysis_unit: AnalysisUnit) -> bool:
    return any(
        value not in EMPTY_VALS
        for group in analysis_unit.arms_by_id.values()
        for value in group.raw_data
    ) or any(
        value not in EMPTY_VALS
        for effect_groups in analysis_unit.entered_effects.values()
        for effect_data in effect_groups.values()
        for key, value in effect_data.items()
        if key != "calculator_source"
    )


def has_study_entered_data(study):
    return bool(study.label.strip() or study.year or any(v not in EMPTY_VALS for v in study.covariate_values.values()) or has_entered_data(study.analysis_unit))


_FIRST_ARM_FIELDS = (
    dict.fromkeys(BINARY_ONE_ARM_METRICS, RAW_FIELDS_PER_ARM[BINARY])
    | dict.fromkeys(CONTINUOUS_ONE_ARM_METRICS, RAW_FIELDS_PER_ARM[CONTINUOUS])
)


def fit_raw_rows(
    studies: Sequence[StudyRow],
    raw_rows: Sequence[Sequence[object]],
    metric: str,
    arm_key: tuple[str, ...],
) -> Sequence[Sequence[object]] | None:
    """Return complete raw inputs for the selected studies when raw data has authority."""
    if len(raw_rows) != len(studies) or any(
        study.analysis_unit.calculator_source(metric, arm_key) == "entered"
        for study in studies
    ):
        return None
    return _complete_fit_raw_rows(raw_rows, metric)


def _complete_fit_raw_rows(
    raw_rows: Sequence[Sequence[object]], metric: str | None,
) -> Sequence[Sequence[object]] | None:
    arm_fields = _FIRST_ARM_FIELDS.get(metric) if metric is not None else None
    if arm_fields is not None:
        raw_rows = [row[:arm_fields] for row in raw_rows]
    return raw_rows if all(raw_data_is_complete(row) for row in raw_rows) else None


def included_studies_have_effects(
    studies: Sequence[StudyRow],
    effect_for_study: Callable[[int], Sequence[object]],
) -> bool:
    return all(
        all(value is not None for value in effect_for_study(index))
        for index, study in enumerate(studies)
        if study.include
    )
