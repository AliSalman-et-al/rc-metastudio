# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validated, data-only state used to redraw saved forest plots."""

from __future__ import annotations

import json
import math
from typing import TypeGuard, cast


MAX_RENDER_STATE_BYTES = 1_000_000
MAX_TOTAL_RENDER_STATE_BYTES = 2_000_000
FOREST_PARAMETER_FIELDS = frozenset(
    {
        "measure",
        "conf.level",
        "digits",
        "rm.method",
        "create.plot",
        "fp_style",
        "fp_accent_color",
        "fp_col1_str",
        "fp_col2_str",
        "fp_col3_str",
        "fp_col4_str",
        "fp_plot_lb",
        "fp_plot_ub",
        "fp_xlabel",
        "fp_xticks",
        "fp_point_size_multiplier",
        "fp_show_annotation",
        "fp_show_col1",
        "fp_show_col2",
        "fp_show_col3",
        "fp_show_col4",
        "fp_show_headers",
        "fp_show_raw_counts",
        "fp_show_summary_line",
    }
)
FOREST_PRESENTATION_FIELDS = frozenset(
    field for field in FOREST_PARAMETER_FIELDS if field.startswith("fp_")
)
_STATE_FIELDS = frozenset(
    {
        "version",
        "renderer",
        "figure_key",
        "data_type",
        "style",
        "variant",
        "single_study",
        "studies",
        "summary",
        "weights",
        "ilab",
        "sample_sizes",
        "params",
        "plot_range",
        "effect_display",
    }
)
_STUDY_FIELDS = frozenset({"yi", "vi", "ci_lb", "ci_ub", "labels"})
_SUMMARY_FIELDS = frozenset(
    {
        "b",
        "ci_lb",
        "ci_ub",
        "QE",
        "k",
        "p",
        "QEp",
        "I2",
        "tau2",
        "method",
        "zval",
        "pval",
    }
)


def is_render_state(value: object, figure_key: str | None = None) -> TypeGuard[dict[str, object]]:
    """Accept only a bounded forest projection with aligned frozen study rows."""
    if not isinstance(value, dict):
        return False
    state = cast(dict[str, object], value)
    if set(state) != _STATE_FIELDS:
        return False
    state_version = state.get("version")
    state_figure_key = state.get("figure_key")
    data_type = state.get("data_type")
    style = state.get("style")
    variant = state.get("variant")
    if (
        type(state_version) is not int
        or state_version != 1
        or state.get("renderer") != "rcmetar_forest_v1"
        or not isinstance(state_figure_key, str)
        or (figure_key is not None and state_figure_key != figure_key)
        or not isinstance(data_type, str)
        or data_type not in {"binary", "continuous", "diagnostic"}
        or not isinstance(style, str)
        or style not in {"default", "revman", "bmj"}
        or not isinstance(variant, str)
        or variant not in {"standard", "cumulative", "leave-one-out"}
        or type(state.get("single_study")) is not bool
    ):
        return False
    studies_value = state.get("studies")
    summary_value = state.get("summary")
    ilab_value = state.get("ilab")
    if not _mapping_with_fields(studies_value, _STUDY_FIELDS):
        return False
    if not _summary_mapping(summary_value):
        return False
    studies = cast(dict[str, object], studies_value)
    summary = cast(dict[str, object], summary_value)
    for field, item in summary.items():
        if not (isinstance(item, str) if field == "method" else _optional_number(item)):
            return False
    labels_value = studies["labels"]
    if not isinstance(labels_value, list):
        return False
    labels = cast(list[object], labels_value)
    if not isinstance(labels, list) or not labels or not all(
        isinstance(label, str) for label in labels
    ):
        return False
    for field in ("yi", "vi", "ci_lb", "ci_ub"):
        if not _aligned_optional_numbers(studies[field], len(labels)):
            return False
    if not _json_object(ilab_value):
        return False
    ilab = cast(dict[str, object], ilab_value)
    if set(ilab) != {"matrix", "columns", "headers", "groups"}:
        return False
    headers_value = ilab.get("headers")
    groups_value = ilab.get("groups")
    if not _string_list(headers_value) or not _string_list(groups_value):
        return False
    headers = cast(list[str], headers_value)
    matrix = ilab["matrix"]
    if not isinstance(matrix, list) or any(
        not isinstance(row, list)
        or len(row) != len(headers)
        or not all(isinstance(cell, str) for cell in row)
        for row in matrix
    ):
        return False
    if matrix and len(matrix) != len(labels):
        return False
    if not isinstance(ilab["columns"], list) or any(
        not _ilab_column(column, len(labels)) for column in ilab["columns"]
    ):
        return False
    weights = state["weights"]
    if weights is not None and not _aligned_optional_numbers(weights, len(labels)):
        return False
    if not state["single_study"] and not isinstance(weights, list):
        return False
    sample_sizes = state["sample_sizes"]
    if sample_sizes is not None and not _aligned_optional_numbers(sample_sizes, len(labels)):
        return False
    if not _required_number_list(state["plot_range"], 2):
        return False
    effect_display_value = state["effect_display"]
    if not _json_object(effect_display_value):
        return False
    effect_display = cast(dict[str, object], effect_display_value)
    if set(effect_display) != {"y_disp", "lb_disp", "ub_disp"}:
        return False
    if any(
        not _aligned_optional_numbers(effect_display[field], len(labels))
        for field in effect_display
    ):
        return False
    if not _forest_params(state["params"]):
        return False
    try:
        encoded = json.dumps(
        state,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError):
        return False
    return len(encoded) <= MAX_RENDER_STATE_BYTES and _json_tree(value)


def _mapping_with_fields(value: object, fields: frozenset[str]) -> bool:
    return isinstance(value, dict) and set(value) == fields and _json_tree(value)


def _summary_mapping(value: object) -> bool:
    return (
        isinstance(value, dict)
        and {"b", "ci_lb", "ci_ub"}.issubset(value)
        and set(value).issubset(_SUMMARY_FIELDS)
        and _json_tree(value)
    )


def _json_object(value: object) -> bool:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _json_tree(value: object) -> bool:
    pending = [(value, 0)]
    while pending:
        current, depth = pending.pop()
        if depth > 24:
            return False
        if isinstance(current, dict):
            if not all(isinstance(key, str) for key in current):
                return False
            pending.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            pending.extend((item, depth + 1) for item in current)
        elif current is None or isinstance(current, (str, bool, int)):
            continue
        elif isinstance(current, float):
            if not math.isfinite(current):
                return False
        else:
            return False
    return True


def _string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _required_number_list(value: object, expected_length: int) -> bool:
    return isinstance(value, list) and len(value) == expected_length and all(
        isinstance(item, (int, float))
        and not isinstance(item, bool)
        and math.isfinite(float(item))
        for item in value
    )


def _aligned_optional_numbers(value: object, expected_length: int) -> bool:
    return isinstance(value, list) and len(value) == expected_length and all(
        _optional_number(item) for item in value
    )


def _optional_number(value: object) -> bool:
    return value is None or (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _ilab_column(value: object, row_count: int) -> bool:
    if not _json_object(value):
        return False
    column = cast(dict[str, object], value)
    if set(column) != {"key", "group", "header", "values"}:
        return False
    if not all(isinstance(column[key], str) for key in ("key", "group", "header")):
        return False
    values = column["values"]
    return _string_list(values) and len(cast(list[str], values)) == row_count


def _forest_params(value: object) -> bool:
    if not _json_object(value):
        return False
    params = cast(dict[str, object], value)
    return set(params).issubset(FOREST_PARAMETER_FIELDS) and all(
        item is None or isinstance(item, (str, bool, int, float))
        for item in params.values()
    )


def is_forest_presentation(value: object) -> bool:
    if not _json_object(value):
        return False
    presentation = cast(dict[str, object], value)
    return set(presentation).issubset(FOREST_PRESENTATION_FIELDS) and all(
        item is None or isinstance(item, (str, bool, int, float))
        for item in presentation.values()
    )


def validated_render_states(value: object, image_keys: set[str]) -> dict[str, dict[str, object]]:
    if value is None:
        return {}
    if not _json_object(value):
        raise ValueError("saved plot renderer state does not match its figures")
    render_states = cast(dict[str, object], value)
    if not set(render_states).issubset(image_keys):
        raise ValueError("saved plot renderer state does not match its figures")
    states: dict[str, dict[str, object]] = {}
    total_size = 0
    for figure_key, raw_state in render_states.items():
        if not isinstance(raw_state, dict) or not is_render_state(raw_state, figure_key):
            raise ValueError("saved plot renderer state is malformed: %s" % figure_key)
        total_size += len(
            json.dumps(raw_state, separators=(",", ":"), allow_nan=False).encode(
                "utf-8"
            )
        )
        states[figure_key] = raw_state
    if total_size > MAX_TOTAL_RENDER_STATE_BYTES:
        raise ValueError("saved plot renderer state exceeds the project size limit")
    return states
