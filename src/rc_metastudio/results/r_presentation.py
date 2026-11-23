# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Present analysis results received from the RCMetaR worker."""

from collections.abc import Mapping
from contextvars import ContextVar
from dataclasses import replace
import math
import re
from typing import cast, get_args

from rc_metastudio.analysis.method_labels import method_display_label
from rc_metastudio.r_result_wire import (
    RegressionOutput,
    _has_r_names, _is_r_iterable, _is_r_string_vector, _r_attribute, _r_dimnames, _r_dims,
    _r_is_null, _r_mapping_or_empty, _r_na_to_none, _r_names_or_none, _r_singleton_to_scalar,
    r_object_to_python, regression_output, require_result_vector,
)
from rc_metastudio.results import formatting as result_formatting
from rc_metastudio.results.contract import (
    AnalysisResult, Quantity, QuantityRole, QuantityScale, ResultSection, TableRole,
    _report_table_entry, parse_analysis_result,
)
from rc_metastudio.results.formatting import PERCENTAGE_DISPLAY_DIGITS, tabulate


def parse_tsa_result(raw: object, path: str) -> tuple[dict[str, object], tuple[ResultSection, ...]]:
    from rc_metastudio.results.plot_capabilities import PlotCapability

    def table_section(key: str, title: str, order: int, matrix) -> ResultSection:
        identity = f"trial-sequential.{key}"
        table = _report_table_entry(_structured_matrix(title, matrix, None, first_row_headers=True))
        notes = ("— Too little information for a finite TSA-adjusted interval.",) if any("—" in row for row in table.rows) else ()
        return ResultSection(identity, "text", order, title, "", identity, tables=(table,), paragraphs=notes)

    result = require_result_vector(raw).named_fields()
    sections = [table_section("looks", "Trial sequential results", 0, result["table"])]
    if "sensitivity.table" in result:
        sections.append(table_section("sensitivity", "Sensitivity to the anticipated intervention effect",
                                      1, result["sensitivity.table"]))
    plot_title = "Trial sequential plot"
    plot = ResultSection(
        "trial-sequential.plot", "image", 2, plot_title, path, plot_title,
        plot_data=str(require_result_vector(result["plot.prefix"])[0]), capability=PlotCapability(
            "trial_sequential", True, True, "trial_sequential"),
    )
    fields = {key: r_object_to_python(result[key]) for key in ("summary", "package.versions", "fixed_effect_note")}
    looks = require_result_vector(result["looks"]).named_fields()
    fields["looks"] = {
        key: [_r_na_to_none(value) for value in require_result_vector(column)]
        for key, column in looks.items()
    }
    version = require_result_vector(result["version"])[0]
    if type(version) is not int:
        raise ValueError("expected an integer TSA result version")
    fields["version"] = version
    return fields, (*sections, plot)


_RESULT_DISPLAY_DIGITS: ContextVar[int | None] = ContextVar("result_display_digits", default=None)


def parse_result_payload(payload: object) -> AnalysisResult:
    fields = require_result_vector(payload).named_fields()
    values = require_result_vector(fields["values"])
    result = dict(zip(values.names, values)) if len(values) else {}
    studies = fields["studies"]
    if studies is not None:
        result["study.names"] = list(require_result_vector(studies))
    params = _r_mapping_or_empty(result.get("input_params"))
    digits = params.get("digits")
    if isinstance(digits, (tuple, list)):
        digits = digits[0] if digits else None
    token = _RESULT_DISPLAY_DIGITS.set(int(digits) if digits is not None else None)
    try:
        parsed = _parse_display_results(result, regression_output(fields.get("regression")))
        return _with_execution_details(parsed, fields["request"], fields["execution"], fields["contributors"])
    finally:
        _RESULT_DISPLAY_DIGITS.reset(token)


def _with_execution_details(parsed, request, execution, contributors):
    workflow = _r_mapping_or_empty(request).get('workflow', '')
    fields = {} if _r_is_null(execution) else dict(zip(execution.names, execution))
    packages = fields.get('packages')
    software = ', '.join(f'{name} {version[0]}' for name, version in zip(packages.names, packages)) if packages is not None and len(packages) else ''
    inference = fields.get('inference', ())
    return replace(parsed, contributing_studies=None if _r_is_null(contributors) else int(contributors[0]),
                   software=software, inference_methods=tuple(str(code) for code in inference),
                   sections=tuple(replace(section, tables=tuple(replace(table, workflow=str(workflow)) for table in section.tables)) for section in parsed.sections))


def _add_regression_reports(regression: RegressionOutput | None, reports) -> None:
    if regression is None:
        return
    source_tables = reports.get("Summary", {}).get("tables", ())
    source = next((table for table in source_tables if table["role"] == "coefficients"), None)
    if source is None:
        return
    tables = [_regression_coefficient_table(regression)]
    if regression.residual:
        tables.append(_regression_residual_table(regression))
    tables.extend(dict(table) for table in source_tables if table['role'] in ('model_fit', 'model_specification', 'model_tests'))
    context = {key: source[key] for key in ('metric', 'metric_label', 'workflow') if key in source}
    for table in tables:
        table.update(context)
    reports["Summary"] = {"paragraphs": [], "tables": tables}


def _regression_residual_table(regression: RegressionOutput) -> dict[str, object]:
    labels = {"q": "Q", "p": "P value", "tau2": "τ²"}
    headers = [labels[key] for key, _ in regression.residual]
    scale = cast(QuantityScale, regression.scale)
    return {
        "title": "Residual heterogeneity", "role": "residual_heterogeneity",
        "inference": regression.inference, "headers": headers,
        "rows": [[_format_r_table_cell(value, field_name=labels[key]) for key, value in regression.residual]],
        "quantities": [[(Quantity(cast(QuantityRole, key), value, scale if key == "tau2" else ""),)
                        for key, value in regression.residual]],
    }


def _display_result_sections(result, regression: RegressionOutput | None):
    study_names = _study_names_from_result(result)
    text_d = {}
    text_sources = {}
    reports = {}

    for text_n, text in result.items():
        if text_n in _RESULT_METADATA_KEYS or _r_is_null(text):
            continue
        _add_result_text(text_d, text_n, text, result, study_names)
        if text_n in {"weights", "Weights"}:
            reports["Weights"] = _weight_report(result, text)
        else:
            reports.update(_structured_result_reports(_display_section_name(text_n), text, study_names))
        for index, key in enumerate(key for key in text_d if key not in text_sources):
            text_sources[key] = (text_n, index)

    _add_regression_reports(regression, reports)
    _place_study_table_with_weights(reports)
    return text_d, text_sources, reports


def _weight_report(result, value):
    weights = _weight_values(value)
    names = _weight_study_names(result, value, len(weights))
    return {"paragraphs": [], "tables": [{
        "title": "Study weights", "role": "study_results", "label_column": 0,
        "headers": ["Study", "Weight (%)"],
        "rows": [[str(name), _format_weight(weight)] for name, weight in zip(names, weights, strict=True)],
        "quantities": [[(), (Quantity("weight", _raw_number(weight), "percent"),)] for weight in weights],
    }]}


def _place_study_table_with_weights(reports):
    if "Weights" not in reports or "Summary" not in reports:
        return
    summary_tables = reports["Summary"]["tables"]
    study_table = next((table for table in summary_tables if table["role"] == "study_results"), None)
    if study_table is not None:
        summary_tables.remove(study_table)
        reports["Weights"]["tables"] = [study_table]


def _parse_display_results(result, regression: RegressionOutput | None):
    metadata = _result_metadata(result)
    text_d, text_sources, reports = _display_result_sections(result, regression)
    text_d, text_sources = _apply_text_value_keys(
        text_d, text_sources, metadata["sections"]
    )
    (
        metadata["images"],
        metadata["display_images"],
        metadata["image_var_names"],
        metadata["image_params_paths"],
        metadata["plot_capabilities"],
        metadata["image_order"],
    ) = _apply_image_value_keys(
        metadata["images"],
        metadata["display_images"],
        metadata["image_var_names"],
        metadata["image_params_paths"],
        metadata["plot_capabilities"],
        metadata["image_order"],
        metadata["sections"],
    )
    aliases = _semantic_value_aliases(metadata["sections"], "text")
    reports = {aliases.get(key, key): content for key, content in reports.items()}
    sections = _text_section_metadata(text_sources, metadata["sections"], reports)
    image_offset = len(sections)
    sections.extend(
        _image_section_metadata(
            metadata["images"],
            metadata["image_order"],
            metadata["image_var_names"],
            metadata["plot_capabilities"],
            metadata["sections"],
            image_offset,
        )
    )
    to_return = {
        "version": 1,
        "images": metadata["images"],
        "display_images": metadata["display_images"],
        "image_var_names": metadata["image_var_names"],
        "texts": text_d,
        "image_params_paths": metadata["image_params_paths"],
        "image_order": metadata["image_order"],
        "plot_capabilities": metadata["plot_capabilities"],
        "sections": sections,
    }
    return parse_analysis_result(to_return)


def _apply_text_value_keys(texts, sources, producer_sections):
    """Map producer display fields to their stable semantic source keys."""
    aliases = _semantic_value_aliases(producer_sections, "text")
    for value_key, source_key in aliases.items():
        display_key = _display_section_name(value_key)
        if display_key not in texts or source_key in texts:
            continue
        texts[source_key] = texts.pop(display_key)
        _replace_source_key(sources, value_key, source_key)
    return texts, sources


def _semantic_value_aliases(producer_sections, kind):
    aliases = {}
    for section in producer_sections:
        if section.get("kind") != kind:
            continue
        value_key = section.get("value_key")
        source_key = section.get("source_key")
        if isinstance(value_key, str) and isinstance(source_key, str):
            aliases[value_key] = source_key
    return aliases


def _replace_source_key(sources, value_key, source_key):
    remapped = {}
    for key, (source_name, child_index) in sources.items():
        if source_name == value_key:
            remapped[source_key] = (source_key, child_index)
        else:
            remapped[key] = (source_name, child_index)
    sources.clear()
    sources.update(remapped)


def _result_metadata(result):
    image_order = result.get("image_order")
    if image_order is None or _r_is_null(image_order):
        image_order = None
    else:
        image_order = list(image_order)
    return {
        "images": _r_mapping_or_empty(result.get("images")),
        "display_images": _r_mapping_or_empty(result.get("display_images")),
        "image_var_names": _r_mapping_or_empty(result.get("plot_names")),
        "image_params_paths": _r_mapping_or_empty(result.get("plot_params_paths")),
        "plot_capabilities": _r_mapping_or_empty(result.get("plot_capabilities")),
        "sections": _r_section_metadata(result.get("sections")),
        "image_order": image_order,
    }


def _apply_image_value_keys(
    images,
    display_images,
    variable_names,
    params_paths,
    capabilities,
    image_order,
    producer_sections,
):
    """Map producer display-keyed plot values to stable section source keys."""
    aliases = {
        section["value_key"]: section["source_key"]
        for section in producer_sections
        if section.get("kind") == "image"
        and isinstance(section.get("value_key"), str)
        and isinstance(section.get("source_key"), str)
    }

    def remap(values):
        return {aliases.get(key, key): value for key, value in values.items()}

    return (
        remap(images),
        remap(display_images),
        remap(variable_names),
        remap(params_paths),
        remap(capabilities),
        None if image_order is None else [aliases.get(key, key) for key in image_order],
    )


_RESULT_METADATA_KEYS = frozenset(
    {
        "images",
        "display_images",
        "image_order",
        "plot_names",
        "plot_titles",
        "plot_source_keys",
        "plot_params_paths",
        "plot_capabilities",
        "sections",
        "study.names",
        "input_params",
    }
)


def _add_result_text(texts, name, value, result, study_names):
    title = _display_section_name(name)
    if name == "References":
        texts[title] = result_formatting.format_references(value)
        return
    if name in ("weights", "Weights"):
        texts["Weights"] = make_weights_str(result)
        return
    if "gui.ignore" in name:
        return
    if (summary := _summary_text(value)) is not None:
        texts[title] = _format_result_text(summary)
        return
    if _is_table_summary(value):
        texts.update(_format_table_summary(title, value, study_names=study_names))
        return
    if _has_r_names(value):
        texts.update(
            _format_named_result_summary(title, value, study_names=study_names)
        )
        return
    if _is_r_iterable(value):
        texts[title] = _format_r_vector(value, field_name=name)
        return
    texts[title] = _format_r_table_cell(value, field_name=name)


def _text_section_metadata(sources, producer_sections, reports=None):
    by_source = {
        section["source_key"]: section
        for section in producer_sections
        if section.get("kind") == "text"
    }
    sections = []
    for order, (title, source) in enumerate(sources.items()):
        source_key, child_index = source
        supplied = by_source.get(source_key)
        semantic_id = _section_semantic_id("text", source_key, supplied, child_index)
        section_title, section_source = _section_display_fields(
            title, supplied, child_index
        )
        sections.append(
            {
                "id": semantic_id,
                "kind": "text",
                "order": order,
                "title": section_title,
                "source_key": section_source,
                "report": (reports or {}).get(title),
            }
        )
    return sections


def _structured_result_reports(title, value, study_names):
    """Carry producer arrays as cells; never reverse-parse printed statistics."""
    if _summary_text(value) is not None:
        return {title: _structured_summary_display(value, study_names)}
    if len(_r_dims(value)) == 2 and not _is_large_display_shape(_r_dims(value)):
        return {title: {"paragraphs": [], "tables": [_structured_matrix(title, value, study_names)]}}
    if _has_r_names(value) and (_is_named_table_summary(value) or _is_named_text_summary(value)):
        reports = {}
        for name, child in zip(list(value.names), list(value)):
            if name and not _r_is_null(child):
                reports.update(_structured_result_reports(
                    _summary_section_name(title, _display_section_name(name)), child, study_names))
        return reports
    if _has_r_names(value):
        content = _structured_named_content(title, value, study_names)
        return {title: content} if content["tables"] else {}
    return {}


def _raw_number(value):
    if _r_na_to_none(value) is None:
        return None
    number = float(value)
    return None if math.isnan(number) else number


def _numeric_fields(value, nrow, ncol):
    attributes = _r_attribute(value, 'rcms.numeric')
    if _r_is_null(attributes):
        return []
    fields = dict(zip(list(attributes.names), list(attributes)))
    columns, roles, scales, levels = [list(fields[key]) for key in ('column', 'role', 'scale', 'level')]
    if tuple(_r_dims(fields['values'])) != (nrow, len(columns)):
        raise ValueError('R numeric result dimensions do not match the display')
    values = list(fields['values'])
    if not len(columns) == len(roles) == len(levels) or len(scales) not in (len(columns), nrow*len(columns)):
        raise ValueError('R numeric result fields are misaligned')
    result: list[list[tuple[Quantity, ...]]] = [[() for _ in range(ncol)] for _ in range(nrow)]
    for index, (column, role, level) in enumerate(zip(columns, roles, levels)):
        column = int(column)-1
        if not 0 <= column < ncol:
            raise ValueError('R numeric result column is outside the display')
        for row in range(nrow):
            scale = scales[index*nrow+row] if len(scales) != len(columns) else scales[index]
            quantity = Quantity(cast(QuantityRole, str(role)), _raw_number(values[row + index*nrow]), cast(QuantityScale, str(scale)), _raw_number(level))
            result[row][column] += (quantity,)
    return result


def _automatic_quantity(value):
    return (Quantity('value', float(value)),) if type(value) in (float, int) and _r_na_to_none(value) is not None and not math.isnan(float(value)) else ()


def _structured_named_content(title, value, study_names):
    paragraphs, tables, rows, quantities = [], [], [], []
    fields = _numeric_fields(value, 1, len(value))
    for index, (name, child) in enumerate(zip(list(value.names), list(value))):
        if not name or _r_is_null(child):
            continue
        label = _format_summary_label(name)
        if len(_r_dims(child)) == 2:
            tables.append(_structured_matrix(label, child, study_names))
        elif _has_r_names(child):
            nested = _structured_named_content(label, child, study_names)
            paragraphs.extend(nested["paragraphs"])
            tables.extend(nested["tables"])
        else:
            _append_named_scalar(name, child, label, fields, index, paragraphs, rows, quantities)

    if rows:
        tables.insert(0, {"title": title, **_table_context(value), "headers": ["Statistic", "Value"], "rows": rows, 'quantities': quantities if any(any(row) for row in quantities) else []})
    return {"paragraphs": paragraphs, "tables": tables}


def _structured_matrix(title, matrix, study_names, first_row_headers=False):
    nrow, ncol = _r_dims(matrix)
    values = _matrix_cell_values(list(matrix), nrow, ncol)
    dimnames = _r_dimnames(matrix)
    headers, row_names = _structured_matrix_headers(values, dimnames, nrow, ncol, study_names, first_row_headers)
    context = _table_context(matrix)
    if context.pop('coefficient_display', False):
        _label_diagnostic_coefficients(headers, dimnames, context.pop('coefficient_level'))
    rows, quantities = _structured_matrix_rows(matrix, values, nrow, ncol, headers, first_row_headers)
    if row_names is not None:
        headers = ["Term"] + headers
        rows = [[name] + row for name, row in zip(row_names, rows)]
        quantities = [[()] + row for row in quantities]
    return {"title": context.pop('report_title', title), **context, "headers": headers, "rows": rows, 'quantities': quantities if any(any(row) for row in quantities) else []}


def _table_context(value):
    metadata = _r_attribute(value, 'rcms.table')
    if _r_is_null(metadata):
        raise ValueError('missing result table role')
    context = dict(_r_mapping_or_empty(metadata))
    if context.get('role') not in get_args(TableRole):
        raise ValueError('unknown result table role')
    context['label_column'] = int(context['label_column']) if context.get('label_column') is not None else None
    return context


def _section_semantic_id(kind, source_key, supplied, child_index):
    semantic_id = (
        supplied["id"] if supplied is not None else _result_section_id(kind, source_key)
    )
    if child_index:
        return f"{semantic_id}:{child_index + 1}"
    return semantic_id


def _section_display_fields(title, supplied, child_index):
    if supplied is not None and child_index == 0:
        return supplied["title"].replace('I-squared', 'I²'), title
    return title.replace('I-squared', 'I²'), title


def _image_section_metadata(
    images, image_order, variable_names, capabilities, producer_sections, offset
):
    by_source = {
        section["source_key"]: section
        for section in producer_sections
        if section.get("kind") == "image"
    }
    sections = []
    used_ids = set()
    ordered_keys = _ordered_image_keys(images, image_order)
    for index, image_key in enumerate(ordered_keys):
        supplied = by_source.get(image_key)
        capability = capabilities.get(image_key, {})
        semantic_key = _image_semantic_key(image_key, variable_names, capability)
        semantic_id = _image_section_id(supplied, semantic_key, used_ids)
        used_ids.add(semantic_id)
        sections.append(
            {
                "id": semantic_id,
                "kind": "image",
                "order": offset + index,
                "title": _image_section_title(supplied, image_key),
                "source_key": image_key,
            }
        )
    return sections


def _ordered_image_keys(images, image_order):
    return [key for key in (image_order or images) if key in images]


def _image_semantic_key(image_key, variable_names, capability):
    return variable_names.get(
        image_key,
        variable_names.get(image_key.lower(), capability.get("plot_kind", "plot")),
    )


def _image_section_id(supplied, semantic_key, used_ids):
    if supplied is not None:
        return supplied["id"]
    return _unique_result_section_id("image", semantic_key, used_ids)


def _image_section_title(supplied, image_key):
    return supplied["title"] if supplied is not None else image_key


def _unique_result_section_id(kind, source_key, used_ids):
    semantic_id = _result_section_id(kind, source_key)
    if semantic_id not in used_ids:
        return semantic_id
    suffix = 2
    while f"{semantic_id}:{suffix}" in used_ids:
        suffix += 1
    return f"{semantic_id}:{suffix}"


def _study_names_from_result(result):
    study_names = result.get("study.names")
    return study_names if study_names and all(study_names) else None


def _r_section_metadata(r_object):
    converted = r_object_to_python(r_object)
    if converted is None:
        return []
    if not isinstance(converted, list):
        raise ValueError("RCMetaR result sections must be a list")
    sections = []
    for item in converted:
        if not isinstance(item, Mapping):
            raise ValueError("RCMetaR result section must be a mapping")
        section = {
            key: value[0] if isinstance(value, list) and len(value) == 1 else value
            for key, value in item.items()
        }
        sections.append(section)
    return sections


def _is_table_summary(r_object):
    return len(_r_dims(r_object)) in (2, 3)


def _summary_text(r_object):
    value = _r_attribute(r_object, "rcms.formatted")
    return None if _r_is_null(value) else value[0]


def _format_table_summary(section_name, r_object, title=None, study_names=None):
    dims = _r_dims(r_object)
    if len(dims) == 2:
        if _is_large_display_shape(dims):
            return {section_name: _format_shape_summary(dims)}
        return {section_name: _format_r_matrix(r_object, study_names=study_names)}
    if len(dims) == 3:
        if _is_large_display_shape(dims):
            return {section_name: _format_shape_summary(dims)}
        return _format_r_array_sections(
            "Summary", section_name, r_object, study_names=study_names
        )
    return {section_name: _format_r_table_cell(r_object, field_name=section_name)}


def _is_named_table_summary(r_object):
    if not _has_r_names(r_object):
        return False

    for item in list(r_object):
        dims = _r_dims(item)
        if len(dims) in (2, 3):
            return True
    return False


def _result_section_id(kind, source_key):
    """Return a stable semantic ID supplied by the result producer's key."""
    normalized = re.sub(r"[^a-z0-9]+", "-", str(source_key).lower()).strip("-")
    return f"{kind}:{normalized or 'unnamed'}"


def _format_named_result_summary(parent_name, r_object, study_names=None):
    wrapped = _unwrapped_ma_results(r_object)
    if wrapped is not None:
        return {parent_name: _format_named_value(wrapped, study_names=study_names)}
    if _is_named_table_summary(r_object):
        return _format_named_table_summary(
            parent_name, r_object, study_names=study_names
        )
    if _is_named_text_summary(r_object):
        return _format_named_text_summary(parent_name, r_object)
    rendered = _format_named_value(r_object, study_names=study_names)
    return {parent_name: rendered} if rendered else {}


def _unwrapped_ma_results(r_object):
    if not _has_r_names(r_object):
        return None
    names = [str(name) for name in list(r_object.names)]
    if len(names) != 1 or names[0].replace(" ", "") != "MAResults":
        return None
    wrapped = list(r_object)[0]
    return wrapped if _has_r_names(wrapped) else None


def _is_named_text_summary(r_object):
    if not _has_r_names(r_object):
        return False

    has_named_text = False
    for item in list(r_object):
        if not _is_r_string_vector(item) or _r_names_or_none(item) is not None:
            return False
        has_named_text = True
    return has_named_text


def _format_named_text_summary(parent_name, r_object):
    sections = {}
    for name, item in zip(list(r_object.names), list(r_object)):
        if name == "" or not _is_r_string_vector(item):
            continue
        sections[_summary_section_name(parent_name, _display_section_name(name))] = (
            _format_result_text(item[0])
        )

    if not sections:
        sections[parent_name] = _format_result_text(str(r_object))
    return sections


def _format_named_table_summary(parent_name, r_object, study_names=None):
    sections = {}
    for name, item in zip(list(r_object.names), list(r_object)):
        if name == "":
            continue
        sections.update(
            _format_named_table_item(parent_name, str(name), item, study_names)
        )

    if not sections:
        sections[parent_name] = _format_result_text(str(r_object))
    return sections


def _format_named_table_item(parent_name, name, item, study_names):
    display_name = _display_section_name(name)
    section_name = _summary_section_name(parent_name, display_name)
    dims = _r_dims(item)
    if len(dims) == 2:
        return _format_table_summary(
            section_name, item, display_name, study_names=study_names
        )
    if len(dims) == 3:
        return _format_r_array_sections(
            parent_name, display_name, item, study_names=study_names
        )
    if _is_r_string_vector(item):
        text = ", ".join(str(value) for value in item)
        return {section_name: _format_result_text(text)}
    if _has_r_names(item):
        rendered = _format_named_value(item, study_names=study_names)
    elif _is_r_iterable(item):
        rendered = _format_r_vector(item)
    else:
        rendered = _format_r_table_cell(item, field_name=name)
    return {section_name: rendered} if rendered else {}


def _format_named_value(r_object, study_names=None):
    """Render a named R list without exposing R's console representation."""
    lines = []
    names = list(r_object.names)
    named_items = list(zip(names, list(r_object)))
    named_items = sorted(
        enumerate(named_items),
        key=lambda pair: (_named_value_priority(pair[1][0]), pair[0]),
    )
    for _index, (name, item) in named_items:
        if not name or _r_is_null(item):
            continue
        label = _format_summary_label(name)
        rendered = _format_nested_value(item, study_names=study_names, field_name=name)
        if not rendered:
            continue
        if "\n" in rendered:
            lines.append("%s:" % label)
            lines.extend("  %s" % line for line in rendered.splitlines())
        else:
            lines.append("%s: %s" % (label, rendered))
    return "\n".join(lines)


def _format_nested_value(r_object, study_names=None, field_name=None):
    dims = _r_dims(r_object)
    if len(dims) == 2:
        if dims[0] > 20 or dims[0] * dims[1] > 100:
            return "%d rows × %d columns" % (dims[0], dims[1])
        return _format_r_matrix(r_object, study_names=study_names)
    if len(dims) == 3:
        rendered = _format_r_array_sections(
            "Summary", "Values", r_object, study_names=study_names
        )
        return "\n\n".join(rendered.values())
    if _has_r_names(r_object):
        return _format_named_value(r_object, study_names=study_names)
    if _is_r_iterable(r_object):
        return _format_r_vector(r_object, field_name=field_name)
    return _format_r_table_cell(r_object, field_name=field_name)


def _format_r_vector(r_object, field_name=None):
    names = _r_names_or_none(r_object)
    values = list(r_object)
    if not values:
        return ""
    if names is not None:
        return "\n".join(
            "%s: %s"
            % (
                _format_summary_label(name),
                _format_r_table_cell(value, field_name=name),
            )
            for name, value in zip(names, values)
        )
    if len(values) == 1:
        return _format_r_table_cell(values[0], field_name=field_name)
    return ", ".join(
        _format_r_table_cell(value, field_name=field_name) for value in values
    )


def _named_value_priority(name):
    """Order decision-relevant fields before implementation diagnostics."""
    compact = re.sub(r"[^a-z0-9]", "", str(name).lower())
    if compact in {"estimate", "te", "effect", "coefficient", "b"}:
        return 0
    if compact in {"lower", "lowerbound", "cilb", "ci95lb", "lowerci"}:
        return 1
    if compact in {"upper", "upperbound", "ciub", "ci95ub", "upperci"}:
        return 2
    if compact in {"p", "pvalue", "pval", "prz"}:
        return 3
    if compact in {"se", "stderr", "standarderror", "z", "zvalue", "zval"}:
        return 4
    return 10


def _is_large_display_shape(dims):
    return bool(dims) and (dims[0] > 20 or math.prod(dims) > 100)


def _format_shape_summary(dims):
    if len(dims) == 2:
        return "%d rows × %d columns" % (dims[0], dims[1])
    if len(dims) == 3:
        return "%d rows × %d columns × %d slices" % tuple(dims)
    return "Array with dimensions %s" % " x ".join(str(dim) for dim in dims)


def _format_summary_label(name):
    labels = {
        "logLik": "Log likelihood",
        "moderator": "Moderator",
        "statistic": "Statistic",
        "estimator": "Estimator",
        "formula": "Model formula",
        "studies.used": "Studies used",
        "correction.policy": "Continuity correction policy",
        "correction.factor": "Continuity correction",
        "converged": "Converged",
        "warnings": "Warnings",
        "package.version": "Package version",
        "normalized.partial.AUC": "Normalized partial SROC AUC",
        "partial.FPR.bounds": "Partial FPR bounds",
        "false.positive.rate": "False-positive rate",
        "covariance.sensitivity.specificity": "Sensitivity-specificity covariance",
        "correlation.sensitivity.specificity": "Sensitivity-specificity correlation",
        "summary.seed": "Summary seed",
        "summary.iterations": "Summary iterations",
        "p.value": "P value",
        "z.value": "z value",
    }
    raw_name = str(name)
    if raw_name in labels:
        return labels[raw_name]
    compact_name = re.sub(r"[^a-z0-9]", "", raw_name.lower())
    if compact_name in {"b", "estimate"}:
        return "Estimate"
    if compact_name in {"lower", "cilb", "lowerbound", "lowerci", "lb"}:
        return "Lower bound"
    if compact_name in {"upper", "ciub", "upperbound", "upperci", "ub"}:
        return "Upper bound"
    if compact_name in {"se", "sei", "stderr", "standarderror"}:
        return "Std. error"
    if compact_name in {"sensitivity", "summarysensitivity"}:
        return "Sensitivity"
    if compact_name in {"specificity", "summaryspecificity"}:
        return "Specificity"
    return result_formatting.normalize_identifier_label(raw_name)


def _summary_section_name(parent_name, child_name):
    if parent_name == "Summary":
        return child_name
    return "%s: %s" % (parent_name, child_name)


def _display_section_name(name):
    return method_display_label(str(name))


def _format_r_matrix(matrix, study_names=None):
    dims = _r_dims(matrix)
    dimnames = _r_dimnames(matrix)
    row_names = dimnames[0] if len(dimnames) > 0 and dimnames[0] is not None else None
    col_names = dimnames[1] if len(dimnames) > 1 and dimnames[1] is not None else None
    values = list(matrix)
    return _format_matrix_values(
        values, dims[0], dims[1], row_names, col_names, study_names=study_names
    )


def _format_r_array_sections(parent_name, array_name, r_array, study_names=None):
    dims = _r_dims(r_array)
    dimnames = _r_dimnames(r_array)
    row_names = dimnames[0] if len(dimnames) > 0 and dimnames[0] is not None else None
    col_names = dimnames[1] if len(dimnames) > 1 and dimnames[1] is not None else None
    slice_names = (
        dimnames[2]
        if len(dimnames) > 2 and dimnames[2] is not None
        else [str(index + 1) for index in range(dims[2])]
    )

    values = list(r_array)
    sections = {}
    slice_size = dims[0] * dims[1]
    for slice_index, slice_name in enumerate(slice_names):
        start = slice_index * slice_size
        end = start + slice_size
        title = "%s - %s" % (array_name, slice_name)
        sections[_summary_section_name(parent_name, title)] = _format_matrix_values(
            values[start:end],
            dims[0],
            dims[1],
            row_names,
            col_names,
            study_names=study_names,
        )
    return sections


def _format_matrix_values(values, nrow, ncol, row_names, col_names, study_names=None):
    values = _matrix_cell_values(values, nrow, ncol)
    headers = _matrix_column_names(col_names, ncol)
    rows = []
    row_names = _matrix_row_names(row_names, nrow, study_names)
    include_row_names = row_names is not None
    if include_row_names:
        headers = [""] + headers

    for row_index in range(nrow):
        row = []
        if include_row_names:
            row.append(row_names[row_index])
        for col_index in range(ncol):
            field_name = headers[col_index + (1 if include_row_names else 0)]
            row.append(
                _format_r_table_cell(
                    values[row_index + (col_index * nrow)],
                    field_name=field_name,
                )
            )
        rows.append(row)

    return _format_text_table(headers, rows)


def _matrix_cell_values(values, nrow, ncol):
    """Return exactly ``nrow * ncol`` safe, column-major table cells."""
    values = list(values)
    expected = nrow * ncol
    if len(values) == expected:
        return values

    if len(values) == ncol:
        flattened = []
        for column in values:
            try:
                column_values = list(column)
            except TypeError:
                column_values = [column]
            flattened.extend(column_values[:nrow])
            if len(column_values) < nrow:
                flattened.extend([None] * (nrow - len(column_values)))
        values = flattened

    if len(values) < expected:
        values.extend([None] * (expected - len(values)))
    return values[:expected]


def _matrix_column_names(col_names, ncol):
    names = list(col_names) if col_names is not None else []
    names = names[:ncol]
    names.extend("V%s" % (index + 1) for index in range(len(names), ncol))
    return [_format_r_table_header(name) for name in names]


def _matrix_row_names(row_names, nrow, study_names):
    if row_names is None:
        return None
    names = list(row_names)[:nrow]
    if len(names) < nrow:
        names.extend(str(index + 1) for index in range(len(names), nrow))
    names = _display_row_names(names, study_names)
    return [result_formatting.normalize_identifier_label(name) for name in names]


def _display_row_names(row_names, study_names):
    if row_names is None:
        return None
    if _row_names_are_generic_study_ids(row_names, study_names):
        return list(study_names)
    return row_names


def _row_names_are_generic_study_ids(row_names, study_names):
    if study_names is None or len(row_names) != len(study_names):
        return False
    expected_numbers = [str(index + 1) for index in range(len(row_names))]
    expected_studies = ["Study %s" % (index + 1) for index in range(len(row_names))]
    return list(row_names) in (expected_numbers, expected_studies)


def _format_r_table_cell(value, field_name=None):
    if _is_r_iterable(value) and len(value) == 1:
        value = _r_singleton_to_scalar(value)
    if value is None or str(value) == "NA":
        return "NA"
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        if isinstance(value, float) and not math.isfinite(value):
            return "NA" if math.isnan(value) else ("-Inf" if value < 0 else "Inf")
        return _format_numeric_table_cell(value, field_name)
    return _format_result_text(str(value))


def _format_text_table(headers, rows):
    table_rows = [headers] + rows
    widths = [
        max(len(str(row[col_index])) for row in table_rows)
        for col_index in range(len(headers))
    ]
    rendered_rows = []
    for row_index, row in enumerate(table_rows):
        cells = []
        for col_index, cell in enumerate(row):
            cell = str(cell)
            if col_index == 0:
                cells.append(cell.ljust(widths[col_index]))
            else:
                cells.append(cell.rjust(widths[col_index]))
        rendered_rows.append("  ".join(cells).rstrip())
        if row_index == 0:
            rendered_rows.append("  ".join("-" * width for width in widths).rstrip())
    return "\n".join(rendered_rows)


def _format_r_table_header(value):
    normalized = str(value).strip()
    percentile = re.fullmatch(r"(\d+(?:\.\d+)?)\s*%", normalized)
    if percentile:
        return "%s%%" % percentile.group(1)
    if re.fullmatch(
        r"\d+(?:\.\d+)?\s*%?\s*ci[._\s]*(?:lb|lower)",
        normalized,
        flags=re.IGNORECASE,
    ):
        return "Lower bound"
    if re.fullmatch(
        r"\d+(?:\.\d+)?\s*%?\s*ci[._\s]*(?:ub|upper)",
        normalized,
        flags=re.IGNORECASE,
    ):
        return "Upper bound"
    compact = normalized.lower().replace(".", " ").replace("_", " ").replace("-", " ")
    compact = " ".join(compact.split())
    if compact == "p value":
        return "P value"
    if normalized.lower() == "pr(>|z|)":
        return "P value"
    if compact == "het p value":
        return "Heterogeneity P value"
    if compact == "omnibus p value":
        return "Omnibus P value"
    if compact == "z value":
        return "z value"
    if compact in ("hpd low", "hpd lower", "ci lb", "lower bound"):
        return "Lower bound"
    if compact in ("hpd high", "hpd upper", "ci ub", "upper bound"):
        return "Upper bound"
    if compact == "median estimate":
        return "Median estimate"
    return result_formatting.normalize_identifier_label(normalized)


def _format_result_text(text):
    if not isinstance(text, str):
        text = str(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(
        r"<U\+([0-9A-Fa-f]{4,6})>",
        lambda match: chr(int(match.group(1), 16)),
        text,
    )
    text = _clean_console_text(text)
    text = _replace_result_labels(text)
    return text


def _clean_console_text(text):
    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue
        if stripped == "NULL" or stripped.startswith(('attr(,"', "[[", "$")):
            continue
        cleaned_lines.append(_console_payload(line, stripped))
    return "\n".join(cleaned_lines).strip()


def _console_payload(line, stripped):
    match = re.match(r"^\[\d+\]\s+(.*)$", stripped)
    if match is None:
        return line
    payload = match.group(1)
    quoted = re.findall(r'"((?:[^"\\]|\\.)*)"', payload)
    if quoted and " ".join(quoted) == payload.replace('"', "").strip():
        return ", ".join(quoted)
    return payload


def _replace_result_labels(text):
    text = text.replace("cbind(tsens, tfpr)", "Sensitivity and false-positive rate")
    for raw_label, display_label in (
        ("Zhou.Dendukuri", "Zhou–Dendukuri"),
        ("Holling.Unadjusted", "Holling (unadjusted)"),
        ("Holling.Adjusted", "Holling (adjusted)"),
        ("posLR", "Positive likelihood ratio"),
        ("invnegLR", "Inverse negative likelihood ratio"),
        ("negLR", "Negative likelihood ratio"),
    ):
        text = text.replace(raw_label, display_label)
    insensitive_replacements = (
        (r"\bHPD[._ \t]+(?:low|lower)\b", "Lower bound"),
        (r"\bHPD[._ \t]+(?:high|upper)\b", "Upper bound"),
        (r"\bci[._ \t]*lb\b", "Lower bound"),
        (r"\bci[._ \t]*ub\b", "Upper bound"),
        (r"\b(?:lower[._]+bound|(?-i:Lower Bound))\b", "Lower bound"),
        (r"\b(?:upper[._]+bound|(?-i:Upper Bound))\b", "Upper bound"),
        (r"\bhet[._ \t]+p[._ \t-]*value\b", "Heterogeneity P value"),
        (r"\bp[._ \t-]*value(s?)\b", r"P value\1"),
        (r"\bz[._ \t-]*value\b", "z value"),
    )
    for pattern, replacement in insensitive_replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def make_weights_str(results):
    """Make a string representing the weights due to each study in the meta analysis"""
    weights_object = results.get("weights", results.get("Weights"))
    if weights_object is None:
        raise Exception("make_weights_str() requires 'weights' in the results")

    raw_weights = _weight_values(weights_object)
    if not raw_weights:
        return "No study weights available.\n"
    weights = [_format_weight(value) for value in raw_weights]
    study_names = _weight_study_names(results, weights_object, len(weights))
    return _weight_table(study_names, weights)


def _weight_values(weights_object):
    return list(weights_object) if _is_r_iterable(weights_object) else [weights_object]


def _format_weight(value):
    scalar = value
    if _is_r_iterable(value) and len(value) == 1:
        scalar = _r_singleton_to_scalar(value)
    if scalar is None or str(scalar) == "NA":
        return "NA"
    try:
        return "{0:.{digits}f}%".format(float(scalar), digits=PERCENTAGE_DISPLAY_DIGITS)
    except (TypeError, ValueError):
        return _format_r_table_cell(scalar)


def _weight_study_names(results, weights_object, count):
    if "study.names" in results:
        study_names = results["study.names"]
    else:
        weight_names = _r_names_or_none(weights_object)
        if weight_names is not None and len(weight_names) == count:
            study_names = weight_names
        else:
            study_names = _default_study_names(count)
    return study_names if len(study_names) == count else _default_study_names(count)


def _default_study_names(count):
    return ["Study %d" % (index + 1) for index in range(count)]


def _weight_table(study_names, weights):
    table, widths = tabulate(
        [study_names, weights], sep=": ", return_col_widths=True, align=["L", "R"]
    )
    header = "{0:<{widths[0]}}  {1:<{widths[1]}}".format(
        "Study names", "Weights", widths=widths
    )
    return "\n".join([header, table]) + "\n"


def _r_text_values(value) -> list[str]:
    return [] if value is None or _r_is_null(value) else [str(part) for part in value]


def _summary_display_tables(fields, study_names):
    tables = [
        _structured_matrix(str(caption), matrix, study_names, first_row_headers=True)
        for caption, matrix in zip(fields["table.titles"], fields["arrays"])
        if not _r_is_null(matrix)
    ]
    calculation = fields.get("calculation.table")
    if calculation is not None and not _r_is_null(calculation):
        scale = str(fields["calculation.scale"][0])
        tables.append(_structured_matrix(
            f"Calculation scale ({scale})", calculation, study_names, first_row_headers=True,
        ))
    study_results = fields.get("study.results")
    if study_results is not None and not _r_is_null(study_results):
        tables.append(_structured_study_table(study_results))
    return tables


def _structured_summary_display(value, study_names):
    fields = dict(zip(value.names, value))
    sentence = _r_text_values(fields.get("summary.sentence"))
    paragraphs = sentence or _r_text_values(fields["model.title"])
    paragraphs.extend(
        note for note in _r_text_values(fields.get("notes"))
        if not note.startswith("Calculation scale:")
    )
    return {
        "paragraphs": paragraphs,
        "tables": _summary_display_tables(fields, study_names),
        "prediction_notes": _r_text_values(fields.get("prediction.notes")),
        "configuration_notes": _r_text_values(fields.get("display.precision.note")),
    }


def _structured_study_table(value):
    data = dict(zip(list(value.names), list(value), strict=True))
    digits = int(data["digits"][0])
    level = float(data["level"][0])
    metric = str(data["metric"][0])
    ratio = metric in {"OR", "RR", "HR", "IRR", "DOR", "PLR", "NLR"}
    rows = []
    quantities = []
    for study, estimate, lower, upper, weight in zip(
        data["study"], data["estimate"], data["lower"], data["upper"], data["weight"],
        strict=True,
    ):
        effects = _display_effect_values((estimate, lower, upper), digits, ratio=ratio)
        if effects[0] == "NA":
            effects = ["Not estimable", "—", "—"]
        rows.append([str(study), *effects, _format_weight(weight)])
        quantities.append([
            (),
            (Quantity("estimate", _raw_number(estimate), "display"),),
            (Quantity("ci_lower", _raw_number(lower), "display", level),),
            (Quantity("ci_upper", _raw_number(upper), "display", level),),
            (Quantity("weight", _raw_number(weight), "percent"),),
        ])
    return {
        "title": "Study weights", "role": "study_results", "label_column": 0,
        "metric": metric, "metric_label": str(data["metric_label"][0]),
        "headers": ["Study", "Effect", "Lower bound", "Upper bound", "Weight (%)"],
        "rows": rows, "quantities": quantities,
    }


def _label_diagnostic_coefficients(headers, dimnames, confidence_level):
    raw_headers = list(dimnames[1])
    level = f'{float(confidence_level):g}'
    names = {"Estimate": "Estimate (logit)", "Odds Ratio": "Odds ratio",
             "Odds Ratio lower": f"{level}% CI lower (OR)",
             "Odds Ratio upper": f"{level}% CI upper (OR)"}
    for index, name in enumerate(raw_headers):
        if re.fullmatch(r"[\d.]+%ci\.lb", name):
            headers[index] = f"{level}% CI lower (logit)"
        elif re.fullmatch(r"[\d.]+%ci\.ub", name):
            headers[index] = f"{level}% CI upper (logit)"
        elif name in names:
            headers[index] = names[name]


def _format_numeric_table_cell(value, field_name):
    compact_name = re.sub(r"[^a-z0-9]", "", str(field_name or "").lower())
    digits = _RESULT_DISPLAY_DIGITS.get()
    if digits is not None:
        if compact_name in {"p", "pvalue", "pval", "prz", "qmp", "qep"}:
            precision = max(3, digits)
            return f"< {10**(-precision):g}" if value < 10**(-precision) else f"{value:.{precision}f}"
        if compact_name in {"df", "studies", "studiesused", "k", "summaryseed", "summaryiterations"} and float(value).is_integer():
            return str(int(value))
        return result_formatting.fixed_result_number(
            value, digits, preserve_positive=compact_name.endswith(("ciloweror", "ciupperor"))
        )
    if compact_name in {"p", "pvalue", "pval", "prz", "qmp", "qep"}:
        if value < 0.001:
            return "< 0.001"
        return "%.3f" % value
    if float(value).is_integer():
        return str(int(value))
    return "%.4g" % value


def _regression_coefficient_table(regression: RegressionOutput) -> dict[str, object]:
    level = regression.level
    scale = cast(QuantityScale, regression.scale)
    statistic = "t" if regression.inference in ("t", "knha", "adhoc") else "z"
    columns: tuple[tuple[str, QuantityRole, QuantityScale, float | None], ...] = (
        ("Estimate", "estimate", scale, None),
        ("Lower bound", "ci_lower", scale, level),
        ("Upper bound", "ci_upper", scale, level),
        ("SE", "se", scale, None),
        (statistic, "statistic", "", None),
        ("P value", "p", "", None),
    )
    rows = []
    quantities = []
    for coefficient in regression.coefficients:
        values = (coefficient.estimate, coefficient.lower, coefficient.upper,
                  coefficient.se, coefficient.statistic, coefficient.p)
        term = "Intercept" if coefficient.term == "intrcpt" else coefficient.term
        rows.append([term, *(_format_r_table_cell(value, field_name=column[0])
                            for column, value in zip(columns, values, strict=True))])
        quantities.append([(), *((Quantity(role, value, value_scale, confidence),)
                                  for (_, role, value_scale, confidence), value in zip(columns, values, strict=True))])
    return {
        "title": "Regression coefficients", "role": "coefficients", "label_column": 0,
        "inference": regression.inference,
        "headers": ["Term", "Estimate", f"Lower bound ({level:g}% CI)", f"Upper bound ({level:g}% CI)",
                    "SE", statistic, "P value"],
        "rows": rows, "quantities": quantities,
    }


def _display_effect_values(values, digits, *, ratio):
    effects = [result_formatting.fixed_result_number(value, digits, preserve_positive=ratio and index > 0)
               if isinstance(value, (float, int)) and math.isfinite(value)
               else _format_r_table_cell(value)
               for index, value in enumerate(values)]
    return effects


def _append_named_scalar(name, child, label, fields, index, paragraphs, rows, quantities):
    text = _format_r_vector(child, field_name=name) if _is_r_iterable(child) else _format_r_table_cell(child, field_name=name)
    if len(text) > 100:
        paragraphs.append(label + ": " + text)
    else:
        rows.append([label, text])
        raw = list(child)[0] if _is_r_iterable(child) and len(child) == 1 else child
        quantities.append([(), fields[0][index] if fields else _automatic_quantity(raw)])


def _structured_matrix_headers(values, dimnames, nrow, ncol, study_names, first_row_headers):
    if first_row_headers:
        headers = [str(values[col * nrow]) for col in range(ncol)]
        row_names = None
    else:
        headers = _matrix_column_names(dimnames[1] if len(dimnames) > 1 else None, ncol)
        row_names = _matrix_row_names(dimnames[0] if dimnames else None, nrow, study_names)
    return headers, row_names


def _structured_matrix_rows(matrix, values, nrow, ncol, headers, first_row_headers):
    rows = [[_format_r_table_cell(values[row + col * nrow], field_name=headers[col])
             for col in range(ncol)] for row in range(1 if first_row_headers else 0, nrow)]
    quantities = _numeric_fields(matrix, len(rows), ncol)
    if not quantities:
        quantities = [[_automatic_quantity(values[row + col*nrow]) for col in range(ncol)]
                      for row in range(1 if first_row_headers else 0, nrow)]
    return rows, quantities
