# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Typed, Qt-independent requests at the Analysis Adapter boundary."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Protocol

from rc_metastudio import r_operations
from rc_metastudio.project import model as analysis_dataset
from rc_metastudio.analysis.request import AnalysisParameter, AnalysisRequest, AnalysisValue
from rc_metastudio.results.contract import AnalysisResult, parse_analysis_result


class CovariateSelectionModel(Protocol):
    """Model operations required by covariate-qualified study selection."""

    @property
    def current_sheet(self) -> analysis_dataset.Sheet | None: ...

    def get_studies(
        self, only_if_included: bool = True
    ) -> list[analysis_dataset.StudyRow]: ...


class MetaRegressionModel(Protocol):
    """Model operation required by meta-regression conversion."""

    dataset: analysis_dataset.Dataset


@dataclass(frozen=True)
class StudySelectionResult:
    """Included studies that have values for every selected covariate."""

    studies: tuple[analysis_dataset.StudyRow, ...]
    has_missing_values: bool
    excluded_study_names: tuple[str, ...] = ()


def select_studies_for_covariates(
    model: CovariateSelectionModel,
    selected_covariates: Sequence[dict],
) -> StudySelectionResult:
    """Select included studies with complete values for selected covariates."""
    if model.current_sheet is None:
        raise RuntimeError("Study selection requires an active sheet.")
    covariate_ids = [covariate["id"] for covariate in selected_covariates]
    studies = []
    excluded_study_names = []
    for study in model.get_studies(only_if_included=True):
        values = (study.covariate_values.get(covariate_id) for covariate_id in covariate_ids)
        if all(value is not None and str(value).strip() for value in values):
            studies.append(study)
        else:
            excluded_study_names.append(str(study.label))
    return StudySelectionResult(
        tuple(studies), bool(excluded_study_names), tuple(excluded_study_names)
    )


def _typed_result(value: object) -> AnalysisResult:
    """Parse raw boundary data once; R worker results are already typed."""
    if isinstance(value, AnalysisResult):
        return value
    return parse_analysis_result(value)


def execute_analysis_requests(
    model: object,
    requests: Sequence[AnalysisRequest],
    selected_covariates: Sequence[dict] = (),
) -> AnalysisResult:
    """Execute a frozen set of analysis requests through the R backend."""
    if not requests:
        raise ValueError("No analysis requests were configured.")
    data_types = {request.data_type for request in requests}
    if len(data_types) != 1:
        raise ValueError("One execution cannot mix analysis data families.")
    data_type = requests[0].data_type
    if data_type == "diagnostic":
        return _typed_result(r_operations.run_model_diagnostic_analysis(
            model, requests
        ))
    if len(requests) != 1:
        raise ValueError("Standard execution requires exactly one request.")
    return _typed_result(r_operations.run_model_analysis(
        model, requests[0], **_conversion_kwargs(selected_covariates)
    ))


def _conversion_kwargs(
    selected_covariates: Sequence[dict],
) -> dict[str, object]:
    if not selected_covariates:
        return {}
    return {"covs_to_include": selected_covariates}


def execute_meta_regression_request(
    model: MetaRegressionModel,
    studies: Sequence[analysis_dataset.StudyRow],
    selected_covariates: Sequence[dict],
    request: AnalysisRequest,
    fixed_effects: bool,
    default_confidence_level: AnalysisValue,
) -> AnalysisResult:
    """Convert the dataset and execute one frozen meta-regression request."""
    conversion_kwargs = {
        "covs_to_include": selected_covariates,
        "studies": studies,
    }
    parameters = request.parameter_values()
    if request.data_type == "binary":
        parameters.setdefault("to", "only0")
        parameters.setdefault("adjust", 0.5)
    parameters.setdefault("conf.level", default_confidence_level)
    parameters["rm.method"] = (
        "FE" if fixed_effects else parameters.get("rm.method", "REML")
    )
    regression_request = replace(
        request,
        workflow="meta-regression",
        parameters=tuple(AnalysisParameter(name, value) for name, value in parameters.items()),
    )
    return _typed_result(r_operations.run_model_analysis(
        model, regression_request, **conversion_kwargs,
    ))
