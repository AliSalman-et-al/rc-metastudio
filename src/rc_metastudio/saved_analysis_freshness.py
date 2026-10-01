# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare a saved analysis input with the project's current data."""

from __future__ import annotations

from collections.abc import Mapping

from rc_metastudio import saved_analysis
from rc_metastudio.analysis_snapshot import BinaryInputSnapshot
from rc_metastudio.dataset_table_model import DatasetTableModel


def saved_input_matches_current_data(
    model: DatasetTableModel, record: Mapping[str, object]
) -> bool | None:
    """Return whether the saved analysis input still matches the project.

    ``None`` means the record predates or uses a snapshot schema that this
    application cannot compare. The current model is never changed.
    """
    snapshot_value = record.get("input_snapshot")
    specification = record.get("specification")
    identity = record.get("input_identity")
    if (
        not isinstance(snapshot_value, Mapping)
        or not isinstance(specification, Mapping)
        or not isinstance(identity, str)
    ):
        return None

    try:
        kind, snapshot, request = _parse_snapshot(snapshot_value, specification)
    except (KeyError, TypeError, ValueError):
        return None

    try:
        current_model = _detached_model(model)
        selection = snapshot.input_snapshot if kind == "cumulative" else snapshot
        if not _select_saved_context(current_model, selection):
            return False
        current_snapshot = _freeze_current_input(
            current_model, kind, snapshot, request
        )
        current_identity = saved_analysis.input_snapshot_identity(
            current_snapshot.to_mapping()
        )
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return False
    return current_identity == identity


def _parse_snapshot(snapshot_value, specification):
    method = specification.get("method")
    workflow = specification.get("workflow")
    if workflow == "cumulative":
        from rc_metastudio.cumulative_analysis import CumulativeAnalysisSnapshot

        return "cumulative", CumulativeAnalysisSnapshot.from_mapping(snapshot_value), None
    if workflow == "meta-regression":
        from rc_metastudio.meta_regression_analysis import MetaRegressionInputSnapshot

        return (
            "meta-regression",
            MetaRegressionInputSnapshot.from_mapping(snapshot_value),
            None,
        )
    if method == "diagnostic.reitsma":
        from rc_metastudio.reitsma_analysis import ReitsmaInputSnapshot

        return "reitsma", ReitsmaInputSnapshot.from_mapping(snapshot_value), None
    if "data.type" in specification:
        from rc_metastudio.publication_bias import SmallStudyEffectsRequest

        request = SmallStudyEffectsRequest.from_mapping(specification)
        return "small-study", _parse_family_snapshot(
            snapshot_value, request.data_type
        ), request

    family = specification.get("data_type")
    if family not in {"binary", "continuous", "diagnostic"}:
        raise ValueError("unsupported saved analysis family")
    return "standard", _parse_family_snapshot(snapshot_value, family), None


def _parse_family_snapshot(value, family):
    if family == "binary":
        from rc_metastudio.cumulative_analysis import (
            _binary_input_snapshot_from_mapping,
        )

        return _binary_input_snapshot_from_mapping(value)
    if family == "continuous":
        from rc_metastudio.continuous_analysis_snapshot import ContinuousInputSnapshot

        return ContinuousInputSnapshot.from_mapping(value)
    if family == "diagnostic":
        from rc_metastudio.diagnostic_analysis_snapshot import DiagnosticInputSnapshot

        return DiagnosticInputSnapshot.from_mapping(value)
    raise ValueError("unsupported saved analysis family")


def _detached_model(model: DatasetTableModel) -> DatasetTableModel:
    detached = DatasetTableModel(dataset=model.dataset.copy(), add_blank_study=False)
    detached.set_confidence_level(model.get_confidence_level())
    return detached


def _select_saved_context(model, snapshot) -> bool:
    outcome = snapshot.outcome
    time_point = getattr(snapshot, "time_point", getattr(snapshot, "follow_up", None))
    groups = tuple(snapshot.groups)
    if outcome not in model.dataset.get_outcome_names():
        return False
    if time_point not in model.dataset.get_follow_up_names_for_outcome(outcome):
        return False
    available_groups = model.dataset.get_group_names_for_outcome_follow_up(
        outcome, time_point
    )
    if not groups or any(group not in available_groups for group in groups):
        return False

    model.set_current_outcome(outcome)
    model.set_current_follow_up(time_point)
    model.set_current_groups(list(groups))
    metric = getattr(snapshot, "metric", None)
    if isinstance(metric, str):
        model.current_effect = metric
    return True


def _freeze_current_input(model, kind, snapshot, request):
    if kind == "reitsma":
        from rc_metastudio.reitsma_analysis import freeze_reitsma_input

        return freeze_reitsma_input(model)
    if kind == "meta-regression":
        from rc_metastudio.meta_regression_analysis import freeze_meta_regression_input

        return freeze_meta_regression_input(model, snapshot.moderators)
    if kind == "small-study":
        from rc_metastudio.small_study_effects_core import (
            freeze_small_study_effects_input,
        )

        return freeze_small_study_effects_input(model, request)
    if kind == "cumulative":
        from rc_metastudio.cumulative_analysis import freeze_cumulative_input

        base = _freeze_family_input(model, snapshot.input_snapshot)
        return freeze_cumulative_input(base, snapshot.ordering)
    return _freeze_family_input(model, snapshot)


def _freeze_family_input(model, snapshot):
    from rc_metastudio.analysis_snapshot import BinaryInputSnapshot, freeze_binary_input
    from rc_metastudio.continuous_analysis_snapshot import (
        ContinuousInputSnapshot,
        freeze_continuous_input,
    )
    from rc_metastudio.diagnostic_analysis_snapshot import (
        DiagnosticInputSnapshot,
        freeze_diagnostic_input,
    )

    if isinstance(snapshot, BinaryInputSnapshot):
        return freeze_binary_input(model)
    if isinstance(snapshot, ContinuousInputSnapshot):
        return freeze_continuous_input(model)
    if isinstance(snapshot, DiagnosticInputSnapshot):
        return freeze_diagnostic_input(
            model, include_covariates=snapshot.version == 2
        )
    raise ValueError("unsupported saved analysis snapshot")
