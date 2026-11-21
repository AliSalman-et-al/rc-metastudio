# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared static contracts for analysis results crossing the R boundary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Literal, TypedDict, get_args, cast
import math

from rc_metastudio.results import plot_capabilities
from rc_metastudio.results.plot_capabilities import PlotCapability, PlotKind
from rc_metastudio.results.formatting import sentence_case_title

NO_RESULTS_MESSAGE = "No results could be computed for this analysis."


class RawAnalysisResult(TypedDict, total=False):
    """Untrusted result shape accepted at the application boundary."""

    version: int
    texts: dict[str, str]
    images: dict[str, str]
    display_images: dict[str, str]
    image_var_names: dict[str, str]
    image_params_paths: dict[str, str]
    image_order: list[str] | None
    plot_capabilities: dict[str, dict[str, object]]
    sections: list[dict[str, object]]


QuantityRole = Literal['estimate', 'ci_lower', 'ci_upper', 'pi_lower', 'pi_upper',
                       'se', 'statistic', 'df', 'df2', 'p', 'q', 'i2', 'tau2', 'k', 'weight', 'value']
QuantityScale = Literal['display', 'log', 'logit', 'arcsine', 'freeman-tukey', 'percent', 'proportion', '']
TableRole = Literal['pooled', 'coefficients', 'fitted', 'heterogeneity', 'residual_heterogeneity',
                    'overall_test', 'subgroup_test', 'model_fit', 'model_tests',
                    'model_specification', 'calculation', 'study_results',
                    'cumulative', 'leave_one_out', 'trial_sequential', 'prediction', 'supporting']


@dataclass(frozen=True, slots=True)
class Quantity:
    role: QuantityRole
    value: float | None
    scale: QuantityScale = ''
    level: float | None = None

    def __post_init__(self) -> None:
        if self.role not in get_args(QuantityRole) or self.scale not in get_args(QuantityScale):
            raise ValueError('unknown result quantity role or scale')
        if self.value is not None and (type(self.value) is not float or math.isnan(self.value)):
            raise ValueError('result quantity must be a float or None; NaN is not a missing value')
        interval = self.role in ('ci_lower', 'ci_upper', 'pi_lower', 'pi_upper')
        if interval:
            if type(self.level) is not float or not 0 < self.level < 100:
                raise ValueError('interval quantity needs a confidence level in percent')
        elif self.level is not None:
            raise ValueError('only interval quantities have a confidence level')


@dataclass(frozen=True, slots=True)
class ResultTable:
    title: str
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    quantities: tuple[tuple[tuple[Quantity, ...], ...], ...] = ()
    role: TableRole = field(kw_only=True)
    metric: str = ''
    metric_label: str = ''
    workflow: str = ''
    inference: str = ''
    vertical: bool = False
    label_column: int | None = None

    def __post_init__(self) -> None:
        if self.role not in get_args(TableRole):
            raise ValueError('unknown or missing result table role')
        if self.inference not in ('', 'z', 't', 'knha', 'adhoc'):
            raise ValueError('unknown result table inference')
        if any(not isinstance(value, str) for value in (self.metric, self.metric_label, self.workflow)):
            raise ValueError('result table context must be text')
        if type(self.vertical) is not bool or (self.label_column is not None and (
                type(self.label_column) is not int or not 0 <= self.label_column < len(self.headers))):
            raise ValueError('invalid result table layout')
        _validate_table_quantities(self.quantities, len(self.rows), len(self.headers))


def _validate_table_quantities(quantities, height, width):
    if not quantities:
        return
    if len(quantities) != height:
        raise ValueError('result quantity shape must match the displayed table')
    for row in quantities:
        if len(row) != width:
            raise ValueError('result quantity shape must match the displayed table')
        for cell in row:
            if not isinstance(cell, tuple) or any(not isinstance(q, Quantity) for q in cell):
                raise ValueError('result quantity shape must match the displayed table')


@dataclass(frozen=True, slots=True)
class ResultSection:
    """Stable result identity and stored display/regeneration data."""

    semantic_id: str
    kind: Literal["text", "image"]
    order: int
    title: str
    value: str
    source_key: str
    plot_data: str | None = None
    capability: PlotCapability | None = None
    display_image: str | None = None
    paragraphs: tuple[str, ...] = ()
    tables: tuple[ResultTable, ...] = ()
    prediction_notes: tuple[str, ...] = ()
    configuration_notes: tuple[str, ...] = ()

    @property
    def plot_kind(self) -> PlotKind | None:
        return None if self.capability is None else self.capability.plot_kind


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Validated immutable result contract consumed by application adapters."""

    version: int
    image_var_names: Mapping[str, str]
    image_order: tuple[str, ...] | None
    sections: tuple[ResultSection, ...]
    identity: str = ""
    details: str = ""
    software: str = ""
    analysis_method: str = ""
    manuscript_context: str = ""
    manuscript_title: str = ""
    manuscript_methods: str = ""
    manuscript_comparison: str = ""
    manuscript_metric: str = ""
    manuscript_arms: tuple[str, ...] = ()
    manuscript_favours: tuple[str, ...] = ()
    manuscript_model_info: tuple[tuple[str, str], ...] = ()
    inference_methods: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len({section.semantic_id for section in self.sections}) != len(self.sections) or len(
            {section.order for section in self.sections}
        ) != len(self.sections):
            raise ValueError("analysis result section identity and order must be unique")
        if len({(section.kind, section.source_key) for section in self.sections}) != len(self.sections):
            raise ValueError("analysis result values must have exactly one section")

    @property
    def texts(self) -> Mapping[str, str]:
        return MappingProxyType({s.source_key: s.value for s in self.sections if s.kind == "text"})

    @property
    def images(self) -> Mapping[str, str]:
        return MappingProxyType({s.source_key: s.value for s in self.sections if s.kind == "image"})

    @property
    def display_images(self) -> Mapping[str, str]:
        return MappingProxyType({
            s.source_key: s.display_image for s in self.sections if s.display_image is not None
        })

    @property
    def image_params_paths(self) -> Mapping[str, str]:
        return MappingProxyType({
            s.source_key: s.plot_data for s in self.sections if s.plot_data is not None
        })

    @property
    def plot_capabilities(self) -> Mapping[str, PlotCapability]:
        return MappingProxyType({
            s.source_key: s.capability for s in self.sections if s.capability is not None
        })


def normalize_analysis_result(result: AnalysisResult) -> AnalysisResult:
    """Fold display metadata into configuration before preparing any report."""
    details = result.details
    inference = result.texts.get("Inference Method")
    if inference:
        lines = [line for line in details.splitlines() if not line.startswith("Inference:")]
        lines.append("Inference: " + inference)
        details = "\n".join(lines)
    notes = dict.fromkeys(note for section in result.sections for note in section.configuration_notes)
    if notes:
        lines = details.splitlines()
        lines.extend(note for note in notes if note not in lines)
        details = "\n".join(lines)
    sections = tuple(
        section for section in result.sections
        if section.kind != "text" or section.source_key != "Inference Method"
    )
    if not sections:
        sections += (ResultSection("result.none", "text", 0, "No results", NO_RESULTS_MESSAGE, "No Results"),)
    return replace(result, details=details, sections=sections)


def _sections(raw: RawAnalysisResult, capabilities: Mapping[str, PlotCapability]) -> tuple[ResultSection, ...]:
    sections = tuple(_result_section(item, raw, capabilities) for item in raw["sections"])
    seen_values = {(section.kind, section.source_key) for section in sections}
    expected_values = {("text", key) for key in raw["texts"]} | {("image", key) for key in raw["images"]}
    if seen_values != expected_values:
        raise ValueError("analysis result sections must cover every text and image")
    return sections


def _result_section(
    item: Mapping[str, object],
    raw: RawAnalysisResult,
    capabilities: Mapping[str, PlotCapability],
) -> ResultSection:
    semantic_id, kind, order, title, source_key = _section_fields(item)
    values = raw["texts"] if kind == "text" else raw["images"]
    value = values.get(source_key)
    if value is None:
        raise ValueError("analysis result section references missing value")
    if kind == "text":
        paragraphs, tables, prediction_notes, configuration_notes = _report_content(item.get("report"))
        return ResultSection(semantic_id, kind, order, title, value, source_key,
                             paragraphs=paragraphs, tables=tables, prediction_notes=prediction_notes,
                             configuration_notes=configuration_notes)
    capability = capabilities.get(source_key)
    if capability is None:
        raise ValueError("analysis result image has no plot capability")
    return ResultSection(
        semantic_id,
        kind,
        order,
        title,
        value,
        source_key,
        plot_data=raw["image_params_paths"].get(source_key),
        capability=capability,
        display_image=raw["display_images"].get(source_key),
    )


def _report_content(value: object) -> tuple[tuple[str, ...], tuple[ResultTable, ...], tuple[str, ...], tuple[str, ...]]:
    if value is None:
        return (), (), (), ()
    if not isinstance(value, Mapping):
        raise ValueError("report content must be a mapping")
    fields: dict[str, object] = {}
    for key, field in value.items():
        if isinstance(key, str):
            fields[key] = field
    paragraphs = _optional_string_list(fields.get("paragraphs"), "report paragraphs")
    prediction_notes = _optional_string_list(fields.get("prediction_notes"), "prediction notes")
    configuration_notes = _optional_string_list(fields.get("configuration_notes"), "configuration notes")
    entries = fields.get("tables")
    if not isinstance(entries, (list, tuple)):
        raise ValueError("report tables must be a list")
    return (
        tuple(paragraphs or ()),
        tuple(_report_table_entry(entry) for entry in entries),
        tuple(prediction_notes or ()),
        tuple(configuration_notes or ()),
    )


def _report_rows(rows, width):
    parsed_rows = []
    for row in rows:
        cells = _optional_string_list(row, "report cells")
        if cells is None or len(cells) != width:
            raise ValueError("report row width must match its headers")
        parsed_rows.append(tuple(cells))
    return tuple(parsed_rows)


def _report_quantities(quantities):
    parsed_quantities = []
    for row in quantities:
        if not isinstance(row, (tuple, list)):
            raise ValueError('report quantity row must be a sequence')
        cells = []
        for cell in row:
            if not isinstance(cell, (tuple, list)) or any(not isinstance(q, Quantity) for q in cell):
                raise ValueError('report quantity cell must contain Quantity values')
            cells.append(tuple(cell))
        parsed_quantities.append(tuple(cells))
    return tuple(parsed_quantities)


def _report_table_entry(entry):
    if isinstance(entry, ResultTable):
        return entry
    if not isinstance(entry, Mapping):
        raise ValueError("report table must be a mapping")
    table_fields: dict[str, object] = {}
    for key, field in entry.items():
        if isinstance(key, str):
            table_fields[key] = field
    title = table_fields.get("title")
    headers = _optional_string_list(table_fields.get("headers"), "report headers")
    rows = table_fields.get("rows")
    if not isinstance(title, str) or not title or not headers or not isinstance(rows, (list, tuple)):
        raise ValueError("report table needs a title, headers and rows")
    parsed_rows = _report_rows(rows, len(headers))
    quantities = table_fields.get('quantities', ())
    if not isinstance(quantities, (tuple, list)):
        raise ValueError('report quantities must be nested sequences')
    return ResultTable(title, tuple(headers), parsed_rows, _report_quantities(quantities),
                       role=cast(TableRole, table_fields.get('role')),
                       metric=cast(str, table_fields.get('metric', '')), metric_label=cast(str, table_fields.get('metric_label', '')),
                       workflow=cast(str, table_fields.get('workflow', '')), inference=cast(str, table_fields.get('inference', '')),
                       vertical=cast(bool, table_fields.get('vertical', False)), label_column=cast(int | None, table_fields.get('label_column')))


def _section_fields(
    item: Mapping[str, object],
) -> tuple[str, Literal["text", "image"], int, str, str]:
    semantic_id = _required_section_text(item, "id")
    source_key = _required_section_text(item, "source_key")
    title = sentence_case_title(_required_section_text(item, "title"))
    kind = item.get("kind")
    if kind == "text":
        typed_kind: Literal["text", "image"] = "text"
    elif kind == "image":
        typed_kind = "image"
    else:
        raise ValueError("analysis result section kind is invalid")
    order = item.get("order")
    if type(order) is not int:
        raise ValueError("analysis result section order must be a non-negative integer")
    if order < 0:
        raise ValueError("analysis result section order must be a non-negative integer")
    return semantic_id, typed_kind, order, title, source_key


def _required_section_text(item: Mapping[str, object], field: str) -> str:
    value = item.get(field)
    if isinstance(value, str) and value:
        return value
    label = field.replace("_", " ")
    raise ValueError(f"analysis result section {label} must be non-empty text")


def parse_analysis_result(value: object) -> AnalysisResult:
    """Validate untrusted backend output before application code consumes it."""
    if not isinstance(value, Mapping):
        raise ValueError("analysis result must be a mapping")
    source: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("analysis result field names must be text")
        source[key] = item
    raw: RawAnalysisResult = {
        "version": _result_version(source.get("version")),
        "texts": _string_mapping(source.get("texts"), "texts"),
        "images": _string_mapping(source.get("images"), "images"),
        "display_images": _string_mapping(
            source.get("display_images"), "display_images"
        ),
        "image_var_names": _string_mapping(
            source.get("image_var_names"), "image_var_names"
        ),
        "image_params_paths": _string_mapping(
            source.get("image_params_paths"), "image_params_paths"
        ),
        "image_order": _optional_string_list(source.get("image_order"), "image_order"),
        "plot_capabilities": _object_mapping(
            source.get("plot_capabilities"), "plot_capabilities"
        ),
        "sections": _section_metadata(source.get("sections")),
    }

    capabilities = plot_capabilities.validate_result(raw)
    extra_display_images = sorted(set(raw["display_images"]) - set(raw["images"]))
    if extra_display_images:
        raise ValueError(
            "Display artifacts have no matching plot artifact: %s"
            % ", ".join(extra_display_images)
        )
    software = source.get('software', '')
    inference = _optional_string_list(source.get('inference_methods', []), 'executed inference methods') or []
    if not isinstance(software, str) or any(code not in ('z', 't', 'knha', 'adhoc') for code in inference):
        raise ValueError('invalid executed analysis metadata')
    image_order = raw["image_order"]
    return AnalysisResult(
        version=raw["version"],
        image_var_names=MappingProxyType(raw["image_var_names"]),
        image_order=None if image_order is None else tuple(image_order),
        sections=_sections(raw, capabilities),
        software=software,
        inference_methods=tuple(inference),
    )


def _result_version(value: object) -> int:
    if type(value) is not int or value != 1:
        raise ValueError(f"unsupported analysis result version: {value!r}")
    return value


def _string_mapping(value: object, label: str) -> dict[str, str]:
    if value is None or value == [] or value == ():
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise ValueError(f"{label} keys and values must be text")
        result[key] = item
    return result


def _object_mapping(value: object, label: str) -> dict[str, dict[str, object]]:
    if value is None or value == [] or value == ():
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    result: dict[str, dict[str, object]] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, Mapping):
            raise ValueError(f"{label} entries must be named mappings")
        descriptor: dict[str, object] = {}
        for field, field_value in item.items():
            if not isinstance(field, str):
                raise ValueError(f"{label} field names must be text")
            descriptor[field] = field_value
        result[key] = descriptor
    return result


def _optional_string_list(value: object, label: str) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be a list of text values or null")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{label} must be a list of text values or null")
        result.append(item)
    return result


def _section_metadata(value: object) -> list[dict[str, object]]:
    if value is None:
        raise ValueError("analysis result sections are required")
    if not isinstance(value, (list, tuple)):
        raise ValueError("sections must be a list")
    metadata: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("sections entries must be mappings")
        metadata.append({str(key): field for key, field in item.items()})
    return metadata
