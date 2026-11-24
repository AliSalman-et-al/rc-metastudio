# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Application operations backed by the supervised RCMetaR process."""

from dataclasses import dataclass
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Literal, cast, overload

from rc_metastudio import r_worker
from rc_metastudio.settings import analysis_scratch
from rc_metastudio.r_result_wire import _r_mapping_or_empty
from rc_metastudio.analysis.method_labels import method_labels_by_id
from rc_metastudio.analysis.errors import DiagnosticExecutionError
from rc_metastudio.results.contract import AnalysisResult, ResultSection
from rc_metastudio.results.r_presentation import parse_result_payload, parse_tsa_result
from rc_metastudio.study_effect_shapes import (
    effect_triplet as effect_triplet,
    normalize_diagnostic_effects,
    normalize_effect_result,
)
from rc_metastudio.analysis.catalog import AvailableMethod, CONTINUOUS, ONE_ARM_METRICS, TWO_ARM_METRICS, TYPE_TO_STR_DICT, analysis_workflow
from rc_metastudio.analysis.validation import EMPTY_VALS, normalize_confidence_level_params, validate_confidence_level
from rc_metastudio.analysis.study_selection import (
    FitModel, FitSelection, capture_fit_selection, raw_data_is_complete,
)
from rc_metastudio.ratio_data import RATIO_FIELDS

from rc_metastudio.analysis.request import AnalysisRequest


def get_r_library_paths():
    """Return the library paths visible to R."""
    return r_worker.current_worker().runtime_info()["libraries"]


def get_r_version_string():
    return r_worker.current_worker().runtime_info()["version"]


def get_r_package_version(package_name):
    version = r_worker.current_worker().runtime_info()["packages"][package_name]
    return version if package_name == "meta" else version.replace("-", ".")


def _worker_calculate(
    kind: r_worker.CalculatorKind, args: Mapping[str, object], *, vector: bool = False,
):
    return r_worker.current_worker().call(
        {"type": "calculator", "kind": kind, "args": args, "vector": vector},
        timeout_ms=r_worker.CALCULATOR_DEADLINE_MS,
    )


def impute_diagnostic_data(diagnostic_data):
    diagnostic_data = normalize_confidence_level_params(diagnostic_data)

    for param, val in list(diagnostic_data.items()):
        if val is None:
            diagnostic_data.pop(param)

    return _worker_calculate("diagnostic_impute", {"data": diagnostic_data})


def impute_binary_data(binary_data):
    binary_data = normalize_confidence_level_params(binary_data)
    remove_entries_with_value(None, binary_data)

    return _worker_calculate("binary_impute", {"data": binary_data})


def back_calculate_continuous_data(
    group1_data, group2_data, effect_data, confidence_level
):
    confidence_level = validate_confidence_level(confidence_level)
    remove_entries_with_value(None, group1_data)
    remove_entries_with_value(None, group2_data)
    remove_entries_with_value(None, effect_data)

    return _worker_calculate("back_calculate", {
        "group1": group1_data, "group2": group2_data, "effect": effect_data,
        "confidence": confidence_level,
    })


def remove_entries_with_value(value_to_remove, values):
    """Remove dictionary entries that equal ``value_to_remove``."""
    for parameter, value in list(values.items()):
        if value == value_to_remove:
            values.pop(parameter)


def impute_continuous_data(continuous_data, alpha):
    if not continuous_data:
        return {"succeeded": False}

    return _worker_calculate("continuous_impute", {"data": continuous_data, "alpha": alpha})


def impute_pre_post_continuous_data(continuous_data, correlation, alpha):
    if len(list(continuous_data.items())) == 0:
        return {"succeeded": False}

    return _worker_calculate("pre_post", {
        "data": continuous_data, "correlation": correlation, "alpha": alpha,
    })


def get_params(method_name):
    result = _worker_catalog({"type": "method_parameters", "method": str(method_name)})
    if not isinstance(result, list) or len(result) != 4:
        raise ValueError("The R worker returned invalid method settings.")
    return tuple(result)


def available_model_methods(
    model: object, family: str, metrics: Sequence[str], *, workflow: str,
) -> dict[str, AvailableMethod]:
    """Discover methods by identity without exposing the R dataset to callers."""
    if not metrics:
        raise ValueError("Choose at least one effect measure before selecting analysis methods.")
    result = _worker_catalog({
        "type": "available_methods", "family": family, "workflow": workflow,
        "columns": _analysis_columns(model, family, metrics[0]), "metrics": metrics,
    })
    if not isinstance(result, Mapping):
        raise ValueError("The R worker returned an invalid list of available methods.")
    records = result.get("choices")
    requires_counts = result.get("requires_counts")
    if (
        not isinstance(records, list) or len(records) != len(metrics)
        or not isinstance(requires_counts, list)
        or any(not isinstance(method, str) for method in requires_counts)
    ):
        raise ValueError("The R worker returned an invalid list of available methods.")
    choices = [_r_mapping_or_empty(choice) for choice in records]
    compatible = set.intersection(*(set(choice.values()) for choice in choices))
    count_methods = set(requires_counts)
    return {
        method: AvailableMethod(label, method in count_methods)
        for method, label in method_labels_by_id(choices[0]).items()
        if method in compatible
    }

def get_analysis_plot_capabilities(
    data_type: str, method_name: str, workflow: str = "standard",
) -> list[Mapping[str, object]]:
    result = _worker_catalog({
        "type": "plot_capabilities", "family": str(data_type), "method": str(method_name),
        "workflow": analysis_workflow(workflow),
    })
    if not isinstance(result, list) or any(not isinstance(item, Mapping) for item in result):
        raise ValueError("The R worker returned invalid plot capabilities.")
    return result


def _worker_catalog(job: r_worker.CatalogJob) -> object:
    return r_worker.current_worker().call(job, timeout_ms=r_worker.CATALOG_DEADLINE_MS)


def _analysis_columns(table_model, family: str, metric: str, *, covs_to_include=None, studies=None):
    if family == "binary":
        return _binary_data_arguments(table_model, metric=metric, covs_to_include=covs_to_include, studies=studies)
    if family == "continuous":
        return _continuous_data_arguments(table_model, metric=metric, covs_to_include=covs_to_include, studies=studies)
    if family == "diagnostic":
        inputs = capture_fit_selection(table_model, (metric,), covariates=covs_to_include, studies=studies)
        return _diagnostic_data_arguments(inputs, metric=metric)
    if family in ("time_to_event", "event_rates"):
        inputs = capture_fit_selection(table_model, (metric,), covariates=covs_to_include, studies=studies)
        return _ratio_data_arguments(inputs, metric)
    raise ValueError(f"unsupported analysis data family: {family!r}")


def _character_values(values):
    return [None if value in EMPTY_VALS else str(value) for value in values]


def _ratio_data_arguments(inputs: FitSelection, metric: str):
    columns = _analysis_data_kwargs(inputs, metric)
    for index, name in enumerate(RATIO_FIELDS):
        convert = _character_values if name in ("scale", "source", "unit") else _numeric_values
        columns[name] = convert(row.ratio[index] for row in inputs.studies)
    raw = [row.raw if len(row.raw) == 4 else (None,) * 4 for row in inputs.studies]
    columns.update(_named_raw_columns(raw, ("x1", "t1", "x2", "t2")))
    columns["metric"] = metric
    return columns


def _continuous_data_arguments(table_model, covs_to_include=None, studies=None, *, metric=None):
    metric = table_model.current_effect if metric is None else metric
    inputs = capture_fit_selection(table_model, (metric,), covariates=covs_to_include, studies=studies)
    columns = _analysis_data_kwargs(inputs, metric)
    if metric not in ONE_ARM_METRICS and (raw := inputs.raw_for_fit()) is not None:
        columns.update(_named_raw_columns(raw, ("N1", "mean1", "sd1", "N2", "mean2", "sd2")))
    return columns


def _binary_data_arguments(table_model, covs_to_include=None, studies=None, *, metric=None):
    metric = table_model.current_effect if metric is None else metric
    inputs = capture_fit_selection(table_model, (metric,), covariates=covs_to_include, studies=studies)
    columns = _analysis_data_kwargs(inputs, metric)
    raw = inputs.raw_for_fit()
    if raw is not None:
        columns.update(_binary_count_columns(raw, metric in TWO_ARM_METRICS))
    return columns


def _binary_count_columns(raw, two_arm: bool):
    group1, group1_totals = _get_col(raw, 0), _get_col(raw, 1)
    group1_nonevents = [total - events for total, events in zip(group1_totals, group1, strict=True)]
    group2, group2_nonevents = [0], [0]
    if two_arm:
        group2, group2_totals = _get_col(raw, 2), _get_col(raw, 3)
        group2_nonevents = [total - events for total, events in zip(group2_totals, group2, strict=True)]
    return {name: _numeric_values(values) for name, values in (
        ("g1O1", group1), ("g1O2", group1_nonevents), ("g2O1", group2), ("g2O2", group2_nonevents),
    )}


def _named_raw_columns(rows: Sequence[Sequence[object]], names: Sequence[str]):
    return {name: _numeric_values(row[index] for row in rows) for index, name in enumerate(names)}


def _diagnostic_data_arguments(inputs: FitSelection, *, metric="Sens"):
    columns = _analysis_data_kwargs(inputs, metric)
    raw = [row.raw for row in inputs.studies]
    if all(map(raw_data_is_complete, raw)):
        columns.update(_named_raw_columns(raw, ("TP", "FN", "FP", "TN")))
    elif any(value in EMPTY_VALS for pair in inputs.effects_for(metric) for value in pair):
        raise ValueError(
            "Diagnostic analysis requires either complete TP/FN/FP/TN counts "
            "or complete entered effect estimates and confidence intervals "
            "for %s." % metric
        )
    return columns


def _analysis_data_kwargs(inputs: FitSelection, metric: str):
    effects = inputs.effects_for(metric)
    return {
        "y": _numeric_values(estimate for estimate, _ in effects),
        "SE": _numeric_values(se for _, se in effects),
        "study.names": _character_values(row.label for row in inputs.studies),
        "years": [None if row.year in EMPTY_VALS else int(row.year) for row in inputs.studies],
        "covariates": _covariate_arguments(inputs),
    }


def _numeric_values(values) -> list[float | None]:
    return [None if value in EMPTY_VALS else float(value) for value in values]


def _covariate_arguments(inputs: FitSelection):
    result = []
    for index, cov in enumerate(inputs.covariates):
        values = [row.covariates[index] for row in inputs.studies]
        convert = _numeric_values if cov.data_type == CONTINUOUS else _character_values
        result.append({
            "cov.name": cov.name, "cov.vals": convert(values),
            "cov.type": TYPE_TO_STR_DICT[cov.data_type], "ref.var": _cov_ref_value(values),
        })
    return result


def _cov_ref_value(values):
    for value in values:
        if value not in EMPTY_VALS:
            return str(value)
    return ""


@overload
def run_small_study_effects(
    table_model,
    request,
    *,
    preview: Literal[False] = False,
) -> AnalysisResult: ...


@overload
def run_small_study_effects(
    table_model,
    request,
    *,
    preview: Literal[True],
) -> Mapping[str, object]: ...


def run_small_study_effects(
    table_model,
    request,
    *,
    preview=False,
) -> AnalysisResult | Mapping[str, object]:
    """Run the complete guided small-study effects workflow in one R call.

    Conversion is intentionally performed at this boundary.  RCMetaR then
    reconstructs compatible raw effects, computes eligibility, validates the
    request, and executes all selected procedures against one eligible set.
    """
    if not isinstance(request, dict):
        raise TypeError("small-study effects request must be a mapping")
    version = request.get("version")
    if type(version) is not int or version != 1:
        raise ValueError("unsupported small-study effects request version")
    r_request = dict(request)
    r_request["preview"] = bool(preview)
    if not preview:
        from rc_metastudio.analysis.identity import plot_caption
        r_request["plot_caption"] = plot_caption(table_model)
    family = request.get("data.type")
    metric = request.get("metric", "DOR")
    columns = _analysis_columns(table_model, family, metric)
    if preview:
        payload = _worker_analysis(_worker_job("small_study", family, columns, r_request))
        return _r_mapping_or_empty(payload)
    return _worker_fit("small_study", family, columns, r_request)


def preview_trial_sequential_analysis(
    model: object, family: str, metric: str, params: Mapping[str, object],
) -> tuple[Mapping[str, object], "WorkerTsaInputs"]:
    inputs = WorkerTsaInputs(family, _analysis_columns(model, family, metric), params)
    result = _worker_analysis(inputs.job("tsa_preview"))
    return _r_mapping_or_empty(result), inputs


@dataclass(frozen=True)
class WorkerTsaInputs:
    family: str
    columns: Mapping[str, object]
    request: Mapping[str, object]

    def job(
        self, kind: Literal["tsa_preview", "tsa_conclusion", "tsa_run"], *,
        stage: Path | None = None, plot: Mapping[str, object] | None = None,
    ) -> r_worker.AnalysisJob:
        return _worker_job(kind, self.family, self.columns, self.request, stage=stage, plot=plot)

    def conclusion(self, deliver: Callable[[Mapping[str, object], Exception | None], None]) -> Callable[[], None]:
        return r_worker.current_worker().start_background(
            self.job("tsa_conclusion"), lambda value, error: deliver(_r_mapping_or_empty(value), error),
        )


def run_trial_sequential_analysis(
    prepared: WorkerTsaInputs, params: Mapping[str, object], path: str,
) -> tuple[dict[str, object], tuple[ResultSection, ...]]:
    with analysis_scratch().result_directory() as stage:
        output = (stage / Path(path).name).as_posix()
        job = prepared.job("tsa_run", stage=stage, plot={**params, "fp_outpath": output})
        raw = _worker_analysis(job)
        fields, sections = parse_tsa_result(raw, output)
        _validate_worker_plots(sections, stage)
        return fields, sections


def run_model_analysis(
    table_model, request: AnalysisRequest, *, covs_to_include=None, studies=None,
) -> AnalysisResult:
    """Convert this frozen model and execute it on the R worker."""
    wire_request = request.to_mapping()
    if (
        request.workflow in {"standard", "cumulative", "leave-one-out", "subgroup"}
        and request.metric in TWO_ARM_METRICS
        and table_model.current_sheet is not None
    ):
        below, above = table_model.current_sheet.effect_direction_arms()
        wire_request["params"] = {
            "measure": request.metric,
            **request.parameter_values(),
            "fp_direction_left": f"Favours {below}" if below else "",
            "fp_direction_right": f"Favours {above}" if above else "",
        }
    columns = _analysis_columns(
        table_model, request.data_type, request.metric, covs_to_include=covs_to_include, studies=studies,
    )
    return _worker_fit("fit", request.data_type, columns, wire_request)


def _worker_job(
    kind: r_worker.AnalysisJobKind,
    family: str, columns: Mapping[str, object] | Sequence[Mapping[str, object]],
    request: Mapping[str, object] | Sequence[Mapping[str, object]],
    *, stage: Path | None = None, plot: Mapping[str, object] | None = None,
) -> r_worker.AnalysisJob:
    return {
        "type": kind, "family": family, "columns": columns, "request": request,
        "stage": stage.as_posix() if stage is not None else "", "plot": {} if plot is None else plot,
    }


def _worker_analysis(job: r_worker.AnalysisJob) -> object:
    return r_worker.current_worker().call(job, timeout_ms=None)


def _validate_worker_plots(sections: Sequence[ResultSection], stage: Path) -> None:
    for section in sections:
        if section.kind != "image":
            continue
        for value in (section.value, section.display_image, section.plot_data):
            if value and not Path(value).resolve().is_relative_to(stage):
                raise ValueError("R worker returned a plot outside its result directory")
        if section.value and not Path(section.value).is_file():
            raise ValueError("R worker returned a missing plot")


def _stage_worker_request(request: Mapping[str, object], stage: Path) -> dict[str, object]:
    params = request.get("params")
    if not isinstance(params, Mapping):
        return dict(request)
    return {**request, "params": {
        key: (stage / Path(value).name).as_posix()
        if isinstance(value, str) and value and key.endswith(("_outpath", "_display_path")) else value
        for key, value in params.items()
    }}


def _worker_fit(
    kind: Literal["fit", "diagnostic_fit", "small_study"],
    family: str, columns: Mapping[str, object] | Sequence[Mapping[str, object]],
    request: Mapping[str, object] | Sequence[Mapping[str, object]],
) -> AnalysisResult:
    with analysis_scratch().result_directory() as stage:
        staged_request = (
            _stage_worker_request(request, stage) if isinstance(request, Mapping)
            else [_stage_worker_request(item, stage) for item in request]
        )
        job = _worker_job(kind, family, columns, staged_request, stage=stage)
        result = parse_result_payload(_worker_analysis(job))
        _validate_worker_plots(result.sections, stage)
        return result


def _worker_diagnostic_fit(requests: Sequence[AnalysisRequest], columns) -> AnalysisResult:
    try:
        return _worker_fit("diagnostic_fit", "diagnostic", columns, [request.to_mapping() for request in requests])
    except ValueError as error:
        raise DiagnosticExecutionError(str(error)) from error


def run_model_diagnostic_analysis(
    model: object, requests: Sequence[AnalysisRequest],
) -> AnalysisResult:
    """Prepare the diagnostic inputs and run the requested fits in one transaction."""
    if not requests:
        raise ValueError("at least one analysis request is required")
    first = requests[0]
    if any(request.data_type != first.data_type or request.workflow != first.workflow for request in requests):
        raise DiagnosticExecutionError("one execution cannot mix analysis workflows")
    metrics = [request.metric for request in requests]
    inputs = capture_fit_selection(cast(FitModel, model), tuple(dict.fromkeys(("Sens", *metrics))))
    if inputs.raw_for_fit() is not None:
        return _worker_diagnostic_fit(requests, _diagnostic_data_arguments(inputs))
    if any(request.method == "diagnostic.reitsma" for request in requests):
        raise ValueError(
            "Reitsma bivariate model requires complete TP/FN/FP/TN counts; "
            "entered diagnostic effects cannot be used for this method."
        )
    missing = [
        metric for metric in metrics
        if any(value is None for pair in inputs.effects_for(metric) for value in pair)
    ]
    if missing:
        raise ValueError(
            "Diagnostic analysis requires complete TP/FN/FP/TN counts or "
            "complete entered effect estimates and confidence intervals for "
            f"each selected effect measure. Missing entered estimates for: {', '.join(missing)}."
        )
    return _worker_diagnostic_fit(requests, [_diagnostic_data_arguments(inputs, metric=metric) for metric in metrics])


def load_plot_parameters(prefix: str) -> object:
    return _worker_plot({"type": "plot_parameters", "prefix": prefix})


def prepare_plot_edit(
    prefix: str,
    regenerator: str,
    changed: Mapping[str, object],
    output: str,
    staging_directory: str,
) -> object:
    return _worker_plot({
        "type": "plot_edit", "prefix": prefix, "regenerator": regenerator, "changed": changed,
        "output": output, "stage": staging_directory,
    })


def forest_export_dimensions(prefix: str, width: float, include_title: bool) -> tuple[float, float] | None:
    match _worker_plot({
        "type": "plot_geometry", "prefix": prefix, "width": width, "include_title": include_title,
    }):
        case None:
            return None
        case [int() | float() as height, int() | float() as minimum_width]:
            return float(height), float(minimum_width)
        case _:
            raise ValueError("R returned invalid forest geometry.")


def render_plot_bundle(prefix: str, regenerator: str, output: str,
                       *, include_title: bool = True, outline_text: bool = True,
                       width: float | None = None, height: float | None = None, dpi: int | None = None,
                       page_height: float | None = None) -> tuple[str, ...]:
    result = _worker_plot({
        "type": "plot_render", "prefix": prefix, "regenerator": regenerator, "output": output,
        "include_title": include_title, "outline_text": outline_text,
        "width": width, "height": height, "dpi": dpi, "page_height": page_height,
    })
    if result is None:
        return ()
    if not isinstance(result, list) or not all(isinstance(path, str) for path in result):
        raise ValueError("R returned invalid plot paths.")
    paths = tuple(result)
    directory = Path(output).resolve().parent
    if any(Path(path).resolve().parent != directory or not Path(path).is_file() for path in paths):
        raise ValueError("R returned missing plot artwork or artwork outside the export directory.")
    return paths


def _worker_plot(job: r_worker.PlotJob) -> object:
    return r_worker.current_worker().call(job, timeout_ms=None)


def _get_col(m, i):
    col_vals = []
    for x in m:
        col_vals.append(x[i])
    return col_vals


def diagnostic_effects_for_study(
    tp, fn, fp, tn, metrics=("Spec", "Sens"), confidence_level=95.0
):
    confidence_level = validate_confidence_level(confidence_level)
    result = _worker_calculate("diagnostic_effect", {
        "tp": tp, "fn": fn, "fp": fp, "tn": tn, "metrics": metrics, "conf.level": confidence_level,
    })
    return normalize_diagnostic_effects(result, require_triplets=True)


def continuous_effect_for_study(
    n1,
    m1,
    sd1,
    se1=None,
    n2=None,
    m2=None,
    sd2=None,
    se2=None,
    metric="MD",
    two_arm=True,
    confidence_level=95.0,
):
    confidence_level = validate_confidence_level(confidence_level)
    inputs = {"n1": n1, "m1": m1, "sd1": sd1, "se1": se1,
              "n2": n2, "m2": m2, "sd2": sd2, "se2": se2}
    params = {"two.arm": bool(two_arm), "metric": str(metric), "conf.level": confidence_level}
    result = _worker_calculate("continuous_effect", inputs | params)
    return normalize_effect_result(result, metric=metric)


def study_effect_previews(
    rows: Sequence[Sequence[object]], family: str, metric: str | None,
    metrics: Sequence[str], confidence_level: float,
) -> list[list[tuple[float | None, ...]]]:
    return r_worker.study_previews({
        "type": "previews", "rows": [_numeric_values(row) for row in rows],
        "family": family, "metric": metric or "",
        "metrics": metrics, "two_arm": metric in TWO_ARM_METRICS, "confidence": confidence_level,
    })


def effect_for_study(
    e1, n1, e2=None, n2=None, two_arm=True, metric="OR", confidence_level=95
):
    """Compute an estimate and confidence interval for binary study data."""
    confidence_level = validate_confidence_level(confidence_level)
    inputs = {"e1": e1, "n1": n1, "e2": e2, "n2": n2}
    params = {"two.arm": bool(two_arm), "metric": str(metric), "conf.level": confidence_level}
    result = _worker_calculate("binary_effect", inputs | params)
    return normalize_effect_result(result, metric=metric)


def binary_convert_scale(x, metric_name, convert_to="display.scale", n1=None):
    return generic_convert_scale(x, metric_name, "binary", convert_to, n1)


def continuous_convert_scale(x, metric_name, convert_to="display.scale"):
    return generic_convert_scale(x, metric_name, "continuous", convert_to)


def diagnostic_convert_scale(x, metric_name, convert_to="display.scale"):
    return generic_convert_scale(x, metric_name, "diagnostic", convert_to)


def generic_convert_scale(
    x, metric_name, data_type, convert_to="display.scale", n1=None
):
    if x is None or x == "":
        return None
    islist = isinstance(x, list) or isinstance(
        x, tuple
    )
    return _worker_calculate("scale", {
        "x": _numeric_values(x) if islist else x,
        "metric": str(metric_name), "data.type": str(data_type),
        "convert.to": str(convert_to), "n1": n1,
    }, vector=islist)


def export_svg_artwork(source: str, destination: str, width: float, height: float, dpi: int) -> None:
    """Convert proportionally sized SVG artwork using the installed R renderer."""
    _worker_plot({
        "type": "artwork_export", "source": source, "output": destination,
        "width": width, "height": height, "dpi": dpi,
    })
    return
