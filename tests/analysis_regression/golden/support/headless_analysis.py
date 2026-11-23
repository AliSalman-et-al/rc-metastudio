import os
from dataclasses import dataclass

from rc_metastudio.workspace import table_model as dataset_table_model
from rc_metastudio.analysis import requests as analysis_adapter
from rc_metastudio.project import adapter as project_adapter
from rc_metastudio.project import archive as project_format


@dataclass(frozen=True)
class HeadlessAnalysisCase:
    dataset_path: str
    requests: tuple[analysis_adapter.AnalysisRequest, ...]
    covariates: tuple[dict, ...] = ()


def load_dataset_model(dataset_path):
    dataset_path = os.path.abspath(dataset_path)
    document = project_format.load_project(dataset_path)
    runtime_project = project_adapter.document_to_runtime_project(document)
    model = dataset_table_model.DatasetTableModel(
        dataset=runtime_project.dataset, add_blank_study=False
    )
    if runtime_project.current_sheet_id is not None:
        model.set_current_sheet(runtime_project.current_sheet_id)
    return model


def _add_case_covariates(model, covariates):
    added = []
    for covariate in covariates:
        added_covariate = model.add_covariate(
            covariate["name"], covariate["type"], covariate["values"]
        )
        added.append(added_covariate)
    return tuple(added)


def run_headless_analysis(case):
    model = load_dataset_model(case.dataset_path)
    selected_covariates = _add_case_covariates(model, case.covariates)
    if not case.requests:
        raise ValueError("an analysis case requires at least one request")
    request = case.requests[0]
    model.set_current_metric(request.metric)
    if request.workflow == "meta-regression":
        if len(case.requests) != 1:
            raise ValueError("meta-regression requires exactly one request")
        selection = analysis_adapter.select_studies_for_covariates(model, selected_covariates)
        return analysis_adapter.execute_meta_regression_request(
            model, selection.studies, selected_covariates, request, False,
            request.parameter_values().get("conf.level", 95),
        )
    return analysis_adapter.execute_analysis_requests(
        model, case.requests, selected_covariates=selected_covariates
    )
