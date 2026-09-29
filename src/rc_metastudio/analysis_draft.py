# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Rebuild an editable analysis draft from the inputs retained with a result."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from rc_metastudio import analysis_dataset, dataset_table_model, meta_globals
from rc_metastudio.analysis_snapshot import (
    BinaryInputSnapshot,
    SingleArmBinaryStudyInput,
)

if TYPE_CHECKING:
    from rc_metastudio.analysis_adapter import AnalysisRequest
    from rc_metastudio.continuous_analysis_snapshot import ContinuousInputSnapshot
    from rc_metastudio.cumulative_analysis import CumulativeAnalysisSnapshot
    from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot


@dataclass(frozen=True, slots=True)
class AnalysisEditCopy:
    input_snapshot: BinaryInputSnapshot | ContinuousInputSnapshot | DiagnosticInputSnapshot | CumulativeAnalysisSnapshot
    effective_request: AnalysisRequest


def binary_model(snapshot: BinaryInputSnapshot) -> dataset_table_model.DatasetTableModel:
    """Give a copied analysis its own data model, separate from the live project."""
    model = _base_model(
        snapshot.studies,
        snapshot.outcome,
        snapshot.time_point,
        snapshot.groups,
        snapshot.metric,
        meta_globals.BINARY,
        "proportions",
    )
    dataset = model.dataset
    comparison = model.get_current_group_comparison()
    for row, study in zip(snapshot.studies, dataset.studies):
        unit = study.get_analysis_unit(snapshot.outcome, snapshot.time_point)
        if snapshot.raw_counts_available:
            if isinstance(row, SingleArmBinaryStudyInput):
                unit.get_raw_data_for_group(snapshot.groups[0])[:] = [
                    row.events,
                    row.total,
                ]
            else:
                unit.get_raw_data_for_group(snapshot.groups[0])[:] = [
                    row.treatment_events,
                    row.treatment_total,
                ]
                unit.get_raw_data_for_group(snapshot.groups[1])[:] = [
                    row.control_events,
                    row.control_total,
                ]
        if row.estimate is not None:
            unit.set_effect_for_source(
                "entered",
                snapshot.metric,
                comparison,
                row.estimate,
                standard_error=row.standard_error,
            )
    for covariate in snapshot.covariates:
        dataset.add_covariate(
            analysis_dataset.Covariate(covariate.name, covariate.data_type),
            {row.name: value for row, value in zip(snapshot.studies, covariate.values)},
        )
    model.reset_model()
    return model


def continuous_model(
    snapshot: ContinuousInputSnapshot,
) -> dataset_table_model.DatasetTableModel:
    """Rebuild a continuous editor from frozen study measurements or effects."""
    model = _base_model(
        snapshot.studies,
        snapshot.outcome,
        snapshot.follow_up,
        snapshot.groups,
        snapshot.metric,
        meta_globals.CONTINUOUS,
        snapshot.outcome_subtype,
    )
    dataset = model.dataset
    comparison = model.get_current_group_comparison()
    for row, study in zip(snapshot.studies, dataset.studies):
        unit = study.get_analysis_unit(snapshot.outcome, snapshot.follow_up)
        if row.arm_1 is not None:
            unit.get_raw_data_for_group(snapshot.groups[0])[:] = [
                row.arm_1.sample_size,
                row.arm_1.mean,
                row.arm_1.standard_deviation,
            ]
        if row.arm_2 is not None:
            unit.get_raw_data_for_group(snapshot.groups[1])[:] = [
                row.arm_2.sample_size,
                row.arm_2.mean,
                row.arm_2.standard_deviation,
            ]
        if row.provenance == "entered" and row.estimate is not None:
            unit.set_effect_for_source(
                "entered",
                snapshot.metric,
                comparison,
                row.estimate,
                standard_error=row.standard_error,
            )
    for covariate in snapshot.covariates:
        dataset.add_covariate(
            analysis_dataset.Covariate(covariate.name, covariate.data_type),
            {row.name: value for row, value in zip(snapshot.studies, covariate.values)},
        )
    model.reset_model()
    return model


def diagnostic_model(
    snapshot: DiagnosticInputSnapshot,
) -> dataset_table_model.DatasetTableModel:
    """Rebuild one diagnostic metric's editor without the live project."""
    model = _base_model(
        snapshot.studies,
        snapshot.outcome,
        snapshot.time_point,
        snapshot.groups,
        snapshot.metric,
        meta_globals.DIAGNOSTIC,
        None,
    )
    comparison = model.get_current_group_comparison()
    for row, study in zip(snapshot.studies, model.dataset.studies):
        unit = study.get_analysis_unit(snapshot.outcome, snapshot.time_point)
        if snapshot.input_source == "counts":
            unit.get_raw_data_for_group(snapshot.groups[0])[:] = [
                row.tp,
                row.fn,
                row.fp,
                row.tn,
            ]
        elif row.estimate is not None:
            unit.set_effect_for_source(
                "entered",
                snapshot.metric,
                comparison,
                row.estimate,
                standard_error=row.standard_error,
            )
    model.reset_model()
    return model


def model_for_snapshot(snapshot):
    from rc_metastudio.cumulative_analysis import CumulativeAnalysisSnapshot
    from rc_metastudio.continuous_analysis_snapshot import ContinuousInputSnapshot
    from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot

    if isinstance(snapshot, CumulativeAnalysisSnapshot):
        snapshot = snapshot.input_snapshot
    if isinstance(snapshot, BinaryInputSnapshot):
        return binary_model(snapshot)
    if isinstance(snapshot, ContinuousInputSnapshot):
        return continuous_model(snapshot)
    if isinstance(snapshot, DiagnosticInputSnapshot):
        return diagnostic_model(snapshot)
    raise TypeError("unsupported saved analysis input snapshot")


def _base_model(rows, outcome, time_point, groups, metric, data_type, subtype):
    is_diagnostic = data_type == meta_globals.DIAGNOSTIC
    dataset = analysis_dataset.Dataset(
        title="Analysis copy", is_diagnostic=is_diagnostic
    )
    for row in rows:
        study_id = row.id if hasattr(row, "id") else row.study_id
        dataset.add_study(
            analysis_dataset.Study(study_id, name=row.name, year=row.year)
        )
    dataset.add_outcome(
        analysis_dataset.Outcome(outcome, data_type, sub_type=subtype)
    )
    if time_point != "first":
        dataset.add_follow_up_to_outcome(outcome, time_point)
    default_groups = dataset.get_group_names()
    temporary_groups = [f"__rcms_draft_{uuid.uuid4().hex}" for _ in default_groups]
    for old, temporary in zip(default_groups, temporary_groups):
        dataset.change_group_name(old, temporary)
    names = list(groups)
    if len(names) == 1 and not is_diagnostic:
        unused = "Other arm"
        while unused in names:
            unused += " (unused)"
        names.append(unused)
    for temporary, new in zip(temporary_groups, names):
        dataset.change_group_name(temporary, new)
    model = dataset_table_model.DatasetTableModel(
        dataset=dataset, add_blank_study=False
    )
    model.set_current_outcome(outcome)
    model.set_current_follow_up(time_point)
    if is_diagnostic:
        model.current_groups = names
        model.group_index_a = dataset.get_group_names().index(names[0])
        model.group_index_b = model.group_index_a
    else:
        model.set_current_groups(names)
    model.current_effect = metric
    return model
