# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Small shared helpers used by the analysis worker and meta-regression."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import Protocol, TypeGuard

from rc_metastudio.analysis_contracts import AnalysisResult, ResultSection
from rc_metastudio.analysis_snapshot import (
    BinaryInputSnapshot,
    BinaryStudyInput,
    SingleArmBinaryStudyInput,
)
from rc_metastudio.meta_globals import BINARY_ONE_ARM_METRICS


class _BinaryDataBridge(Protocol):
    def _r_numeric_vector(self, values: object) -> object: ...

    def _r_character_vector(self, values: object) -> object: ...

    def _r_year_vector(self, values: object) -> object: ...

    def execute_r_function(
        self, function_name: str, *args: object, **kwargs: object
    ) -> object: ...


def _is_binary_data_bridge(value: object) -> TypeGuard[_BinaryDataBridge]:
    return all(
        callable(getattr(value, name, None))
        for name in (
            "_r_numeric_vector",
            "_r_character_vector",
            "_r_year_vector",
            "execute_r_function",
        )
    )


def _is_analysis_result(value: object) -> TypeGuard[AnalysisResult]:
    return isinstance(value, AnalysisResult)


def _create_binary_data(snapshot: BinaryInputSnapshot, bridge: object) -> object:
    """Create RCMetaR's binary data object from a frozen input snapshot."""
    if not _is_binary_data_bridge(bridge):
        raise TypeError("binary analysis needs a configured R bridge")
    import rpy2.robjects as ro

    studies = snapshot.studies
    covariates = _binary_covariates(snapshot, bridge)
    kwargs: dict[str, object] = {
        "y": bridge._r_numeric_vector([study.estimate for study in studies]),
        "SE": bridge._r_numeric_vector([study.standard_error for study in studies]),
        "study.names": bridge._r_character_vector([study.name for study in studies]),
        "years": bridge._r_year_vector([study.year for study in studies]),
        "covariates": covariates,
    }
    if snapshot.raw_counts_available:
        kwargs.update(_binary_raw_counts(snapshot, bridge))
    r_data = bridge.execute_r_function("rcmetar.create.binary.data", **kwargs)
    ro.globalenv["tmp_obj"] = r_data
    return r_data


def _binary_covariates(
    snapshot: BinaryInputSnapshot, bridge: _BinaryDataBridge
) -> object:
    covariate_values = []
    for covariate in snapshot.covariates:
        values = covariate.values
        if covariate.data_type == "continuous":
            r_values = bridge._r_numeric_vector(values)
        elif covariate.data_type == "factor":
            r_values = bridge._r_character_vector(values)
        else:
            raise ValueError("unsupported covariate type in binary input snapshot")
        reference = next((str(item) for item in values if item not in (None, "")), "")
        covariate_values.append(
            bridge.execute_r_function(
                "rcmetar.create.covariate.values",
                **{
                    "cov.name": covariate.name,
                    "cov.vals": r_values,
                    "cov.type": covariate.data_type,
                    "ref.var": reference,
                },
            )
        )
    return bridge.execute_r_function("list", *covariate_values)


def _binary_raw_counts(
    snapshot: BinaryInputSnapshot, bridge: _BinaryDataBridge
) -> dict[str, object]:
    if snapshot.metric in BINARY_ONE_ARM_METRICS:
        return _one_arm_raw_counts(snapshot, bridge)
    return _two_arm_raw_counts(snapshot, bridge)


def _one_arm_raw_counts(
    snapshot: BinaryInputSnapshot, bridge: _BinaryDataBridge
) -> dict[str, object]:
    studies = [
        study
        for study in snapshot.studies
        if isinstance(study, SingleArmBinaryStudyInput)
    ]
    if len(studies) != len(snapshot.studies):
        raise ValueError("single-arm binary input contains a two-arm study row")
    events = [study.events for study in studies]
    totals = [study.total for study in studies]
    return {
        "g1O1": bridge._r_numeric_vector(events),
        "g1O2": bridge._r_numeric_vector(
            [total - event for total, event in zip(totals, events)]
        ),
        "g2O1": bridge._r_numeric_vector([0] * len(studies)),
        "g2O2": bridge._r_numeric_vector([0] * len(studies)),
    }


def _two_arm_raw_counts(
    snapshot: BinaryInputSnapshot, bridge: _BinaryDataBridge
) -> dict[str, object]:
    studies = _two_arm_studies(snapshot)
    treatment_events = [study.treatment_events for study in studies]
    treatment_totals = [study.treatment_total for study in studies]
    control_events = [study.control_events for study in studies]
    control_totals = [study.control_total for study in studies]
    return {
        "g1O1": bridge._r_numeric_vector(treatment_events),
        "g1O2": bridge._r_numeric_vector(
            [total - events for total, events in zip(treatment_totals, treatment_events)]
        ),
        "g2O1": bridge._r_numeric_vector(control_events),
        "g2O2": bridge._r_numeric_vector(
            [total - events for total, events in zip(control_totals, control_events)]
        ),
    }


def _two_arm_studies(snapshot: BinaryInputSnapshot) -> list[BinaryStudyInput]:
    studies = [
        study for study in snapshot.studies if isinstance(study, BinaryStudyInput)
    ]
    if len(studies) != len(snapshot.studies):
        raise ValueError("two-arm binary input contains a one-arm study row")
    return studies


def _wire_result(result: object) -> dict[str, object]:
    """Convert a validated result contract to the worker's JSON shape."""
    if not _is_analysis_result(result):
        raise TypeError("analysis result has an invalid contract")

    def plain(value: object) -> object:
        if is_dataclass(value):
            return {item.name: plain(getattr(value, item.name)) for item in fields(value)}
        if isinstance(value, Mapping):
            return {str(key): plain(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            return [plain(item) for item in value]
        return value

    return {
        "version": result.version,
        "texts": plain(result.texts),
        "images": plain(result.images),
        "display_images": plain(result.display_images),
        "image_var_names": plain(result.image_var_names),
        "image_params_paths": plain(result.image_params_paths),
        "image_order": plain(result.image_order),
        "plot_capabilities": plain(result.plot_capabilities),
        "sections": [_wire_section(section) for section in result.sections],
        "binary_numerics": plain(result.binary_numerics),
        "binary_proportion_numerics": plain(result.binary_proportion_numerics),
        "continuous_numerics": plain(result.continuous_numerics),
        "diagnostic_numerics": plain(result.diagnostic_numerics),
        "cumulative_numerics": plain(result.cumulative_numerics),
        "leave_one_out_numerics": plain(result.leave_one_out_numerics),
        "meta_regression_numerics": plain(result.meta_regression_numerics),
        "reitsma_meta_regression_numerics": plain(
            result.reitsma_meta_regression_numerics
        ),
        "reitsma_report": plain(result.reitsma_report),
        "subgroup_numerics": plain(result.subgroup_numerics),
        "subgroup_plan": plain(result.subgroup_plan),
    }


def _wire_section(section: object) -> dict[str, object]:
    if not isinstance(section, ResultSection):
        raise TypeError("analysis result contains an invalid result section")
    return {
        "id": section.semantic_id,
        "kind": section.kind,
        "order": section.order,
        "title": section.title,
        "source_key": section.source_key,
    }
