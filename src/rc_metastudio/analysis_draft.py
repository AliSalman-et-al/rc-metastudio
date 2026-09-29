# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Rebuild an editable analysis draft from the inputs retained with a result."""

import uuid

from rc_metastudio import analysis_dataset, dataset_table_model, meta_globals
from rc_metastudio.analysis_snapshot import (
    BinaryInputSnapshot,
    SingleArmBinaryStudyInput,
)


def binary_model(snapshot: BinaryInputSnapshot) -> dataset_table_model.DatasetTableModel:
    """Give a copied analysis its own data model, separate from the live project."""
    dataset = analysis_dataset.Dataset(title="Analysis copy")
    for row in snapshot.studies:
        dataset.add_study(
            analysis_dataset.Study(row.id, name=row.name, year=row.year)
        )
    dataset.add_outcome(
        analysis_dataset.Outcome(
            snapshot.outcome, meta_globals.BINARY, sub_type="proportions"
        )
    )
    if snapshot.time_point != "first":
        dataset.add_follow_up_to_outcome(snapshot.outcome, snapshot.time_point)
    default_groups = dataset.get_group_names()
    temporary_groups = [f"__rcms_draft_{uuid.uuid4().hex}" for _ in default_groups]
    for old, temporary in zip(default_groups, temporary_groups):
        dataset.change_group_name(old, temporary)
    names = list(snapshot.groups)
    if len(names) == 1:
        unused = "Other arm"
        while unused in names:
            unused += " (unused)"
        names.append(unused)
    for temporary, new in zip(temporary_groups, names):
        dataset.change_group_name(temporary, new)

    model = dataset_table_model.DatasetTableModel(
        dataset=dataset, add_blank_study=False
    )
    model.set_current_outcome(snapshot.outcome)
    model.set_current_follow_up(snapshot.time_point)
    model.set_current_groups(names)
    model.current_effect = snapshot.metric
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
