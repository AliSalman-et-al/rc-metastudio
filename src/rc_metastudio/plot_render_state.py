# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validated computed data for redrawing saved figures."""

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
_SUBGROUP_STATE_FIELDS = frozenset(
    {
        "names",
        "results",
        "overall",
        "study_rows",
        "header_rows",
        "polygon_rows",
        "overall_row",
        "difference_test",
        "ylim",
    }
)
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
_DIFFERENCE_FIELDS = frozenset({"QM", "df", "QMp"})
_GEOMETRY_STATE_FIELDS = frozenset(
    {"version", "renderer", "figure_key", "geometry", "appearance"}
)
_REGRESSION_RENDERER = "rcmetar_regression_v1"
_FUNNEL_RENDERER = "rcmetar_funnel_v1"
_SROC_RENDERER = "rcmetar_sroc_v1"
_COEFFICIENT_RENDERER = "rcmetar_reitsma_coefficient_v1"
_GEOMETRY_RENDERERS = frozenset(
    {_REGRESSION_RENDERER, _FUNNEL_RENDERER, _SROC_RENDERER, _COEFFICIENT_RENDERER}
)
_GEOMETRY_FIELDS = {
    _REGRESSION_RENDERER: frozenset(
        {
            "moderator", "measure", "point_x", "point_y", "point_size", "labels",
            "line_x", "line_y", "ci_lb", "ci_ub", "pi_lb", "pi_ub",
            "confidence_level",
        }
    ),
    _FUNNEL_RENDERER: frozenset(
        {
            "kind", "metric", "axis_mode", "axis_transform", "effect",
            "standard_error", "labels", "imputed", "center", "pooled_center",
            "tau2", "deeks_predictor",
            "deeks_intercept", "deeks_slope",
        }
    ),
    _SROC_RENDERER: frozenset(
        {
            "point_fpr", "point_sensitivity", "sample_size", "labels",
            "curve_observed", "curve_full", "confidence_region",
            "prediction_region", "summary_sensitivity", "summary_specificity",
            "auc_pauc",
        }
    ),
    _COEFFICIENT_RENDERER: frozenset(
        {"scale", "labels", "estimate", "ci_lb", "ci_ub"}
    ),
}
_GEOMETRY_APPEARANCE_FIELDS = {
    _REGRESSION_RENDERER: frozenset(
        {
            "bp_style", "bp_accent_color", "bp_point_size_multiplier", "bp_xlabel",
            "bp_plot_lb", "bp_plot_ub", "bp_xticks", "bp_yticks",
            "bp_show_regression_line",
            "bp_show_confidence_band", "bp_show_prediction_interval", "bp_show_legend",
        }
    ),
    _FUNNEL_RENDERER: frozenset(
        {
            "funnel.style", "funnel.label.policy", "funnel.point.symbol",
            "funnel.point.size", "funnel.point.color", "funnel.reference.color",
            "funnel.region.color", "funnel.background.color",
            "funnel.reference.visible", "funnel.regression.visible",
            "funnel.pooled.overlay.visible", "funnel.sampling.conf.level",
            "funnel.sampling.region.visible", "funnel.include.tau2",
            "funnel.contour.levels", "funnel.xlab", "funnel.ylab",
            "funnel.xlim.lower", "funnel.xlim.upper", "funnel.xticks",
        }
    ),
    _SROC_RENDERER: frozenset(
        {
            "fp_style", "fp_curve_color", "fp_confidence_color",
            "fp_prediction_color", "fp_accent_color", "fp_point_size_multiplier",
            "fp_marker_area", "fp_point_area_by_sample_size", "fp_show_marker_legend",
            "fp_show_confidence", "fp_show_prediction", "fp_show_summary",
            "fp_show_auc", "fp_show_legend", "fp_xlabel", "fp_ylabel", "fp_plot_lb",
            "fp_plot_ub", "fp_xticks", "fp_sroc_plot_lb", "fp_sroc_plot_ub",
            "fp_sroc_yticks", "fp_curve_lty", "fp_confidence_lty",
            "fp_prediction_lty", "fp_text_cex", "fp_point_pch", "fp_show_labels",
            "fp_show_annotation", "fp_extrapolate", "digits",
        }
    ),
    _COEFFICIENT_RENDERER: frozenset(
        {
            "fp_style", "fp_accent_color", "fp_point_size_multiplier", "fp_xlabel",
            "fp_plot_lb", "fp_plot_ub", "fp_xticks", "fp_show_annotation", "digits",
        }
    ),
}
_GEOMETRY_ARRAY_APPEARANCE_FIELDS = {
    _REGRESSION_RENDERER: frozenset({"bp_xticks", "bp_yticks"}),
    _FUNNEL_RENDERER: frozenset({"funnel.xticks"}),
    _SROC_RENDERER: frozenset({"fp_xticks", "fp_sroc_yticks"}),
    _COEFFICIENT_RENDERER: frozenset({"fp_xticks"}),
}
_GEOMETRY_BOOL_APPEARANCE_FIELDS = {
    _REGRESSION_RENDERER: frozenset(
        {
            "bp_show_regression_line", "bp_show_confidence_band",
            "bp_show_prediction_interval", "bp_show_legend",
        }
    ),
    _FUNNEL_RENDERER: frozenset(
        {
            "funnel.reference.visible", "funnel.regression.visible",
            "funnel.pooled.overlay.visible", "funnel.sampling.region.visible",
            "funnel.include.tau2",
        }
    ),
    _SROC_RENDERER: frozenset(
        {
            "fp_show_marker_legend", "fp_show_confidence", "fp_show_prediction",
            "fp_show_summary", "fp_show_auc", "fp_show_legend",
            "fp_point_area_by_sample_size", "fp_show_labels",
            "fp_show_annotation", "fp_extrapolate",
        }
    ),
    _COEFFICIENT_RENDERER: frozenset({"fp_show_annotation"}),
}
_GEOMETRY_NUMERIC_APPEARANCE_FIELDS = {
    _REGRESSION_RENDERER: frozenset({"bp_point_size_multiplier"}),
    _FUNNEL_RENDERER: frozenset(
        {"funnel.point.symbol", "funnel.point.size", "funnel.sampling.conf.level"}
    ),
    _SROC_RENDERER: frozenset(
        {
            "fp_point_size_multiplier", "fp_text_cex",
            "fp_point_pch", "fp_curve_lty", "fp_confidence_lty",
            "fp_prediction_lty", "digits",
        }
    ),
    _COEFFICIENT_RENDERER: frozenset(
        {"fp_point_size_multiplier", "digits"}
    ),
}
_GEOMETRY_NULLABLE_LABEL_FIELDS = {
    _REGRESSION_RENDERER: frozenset({"bp_xlabel", "bp_ylabel"}),
    _FUNNEL_RENDERER: frozenset({"funnel.xlabel", "funnel.ylabel"}),
    _SROC_RENDERER: frozenset({"fp_xlabel", "fp_ylabel"}),
    _COEFFICIENT_RENDERER: frozenset({"fp_xlabel"}),
}
_PLOT_KIND_RENDERERS = {
    "rcmetar_forest_v1": frozenset(
        {"forest", "cumulative_forest", "leave_one_out_forest", "subgroup_forest"}
    ),
    _REGRESSION_RENDERER: frozenset({"regression"}),
    _FUNNEL_RENDERER: frozenset(
        {"funnel", "contour_funnel", "deeks_funnel", "trimfill_funnel"}
    ),
    _SROC_RENDERER: frozenset({"sroc"}),
    # Reitsma coefficient bundles are forest-shaped capabilities in results,
    # but use a coefficient-only frozen renderer.
    _COEFFICIENT_RENDERER: frozenset({"forest"}),
}


def is_render_state(value: object, figure_key: str | None = None) -> TypeGuard[dict[str, object]]:
    """Accept only a bounded, allowlisted renderer projection."""
    size = render_state_size(value, figure_key)
    return size is not None and size <= MAX_RENDER_STATE_BYTES


def render_state_size(value: object, figure_key: str | None = None) -> int | None:
    """Return encoded size for a structurally valid renderer state."""
    if not isinstance(value, dict):
        return None
    state = cast(dict[str, object], value)
    renderer = state.get("renderer")
    if renderer == "rcmetar_forest_v1":
        if not _valid_forest_state(state, figure_key):
            return None
    elif isinstance(renderer, str) and renderer in _GEOMETRY_RENDERERS:
        if not _valid_geometry_state(state, figure_key, renderer):
            return None
    else:
        return None
    try:
        encoded = json.dumps(
            state,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return None
    return len(encoded)


def _valid_forest_state(state: dict[str, object], figure_key: str | None) -> bool:
    variant = state.get("variant")
    state_fields = (
        _STATE_FIELDS | {"subgroups"} if variant == "subgroup" else _STATE_FIELDS
    )
    if set(state) != state_fields or not _forest_identity(state, figure_key):
        return False
    if not _forest_study_data(state):
        return False
    if variant == "subgroup" and not _forest_subgroups(state):
        return False
    return bool(_forest_params(state.get("params")) and _json_tree(state))


def _valid_geometry_state(
    state: dict[str, object], figure_key: str | None, renderer: str
) -> bool:
    if not _geometry_identity(state, figure_key, renderer):
        return False
    geometry = state.get("geometry")
    appearance = state.get("appearance")
    if not _json_object(geometry) or not _json_object(appearance):
        return False
    if not _geometry_field_sets(state, geometry, appearance, renderer):
        return False
    return _geometry_payload_is_valid(renderer, state, geometry, appearance)


def _geometry_field_sets(
    state: dict[str, object],
    geometry: dict[str, object],
    appearance: dict[str, object],
    renderer: str,
) -> bool:
    if set(state) != _GEOMETRY_STATE_FIELDS:
        return False
    if set(geometry) != _GEOMETRY_FIELDS[renderer]:
        return False
    return set(appearance) == _GEOMETRY_APPEARANCE_FIELDS[renderer]


def _geometry_payload_is_valid(
    renderer: str,
    state: dict[str, object],
    geometry: dict[str, object],
    appearance: dict[str, object],
) -> bool:
    if not _geometry_values(renderer, geometry):
        return False
    if not _geometry_appearance(renderer, appearance, exact=True):
        return False
    return _json_tree(state)


def _geometry_identity(
    state: dict[str, object], figure_key: str | None, renderer: str
) -> bool:
    saved_key = state.get("figure_key")
    return (
        type(state.get("version")) is int
        and state["version"] == 1
        and state.get("renderer") == renderer
        and isinstance(saved_key, str)
        and (figure_key is None or saved_key == figure_key)
    )


def _geometry_values(renderer: str, geometry: dict[str, object]) -> bool:
    labels = geometry.get("labels")
    if not _string_list(labels) or not labels:
        return False
    row_count = len(labels)
    if renderer == _REGRESSION_RENDERER:
        return _regression_geometry(geometry, row_count)
    if renderer == _FUNNEL_RENDERER:
        return _funnel_geometry(geometry, row_count)
    if renderer == _SROC_RENDERER:
        return _sroc_geometry(geometry, row_count)
    return _coefficient_geometry(geometry, row_count)


def _regression_geometry(geometry: dict[str, object], row_count: int) -> bool:
    return (
        _regression_points(geometry, row_count)
        and _regression_curve(geometry)
        and _regression_confidence(geometry)
    )


def _regression_points(geometry: dict[str, object], row_count: int) -> bool:
    if not isinstance(geometry.get("moderator"), str):
        return False
    if not isinstance(geometry.get("measure"), str):
        return False
    if not _aligned_numbers(geometry["point_x"], row_count):
        return False
    if not _aligned_numbers(geometry["point_y"], row_count):
        return False
    return _aligned_positive_numbers(geometry["point_size"], row_count)


def _regression_curve(geometry: dict[str, object]) -> bool:
    line_x = geometry.get("line_x")
    if not isinstance(line_x, list) or not line_x:
        return False
    if not _aligned_numbers(line_x, len(line_x)):
        return False
    if not _regression_curve_bounds(geometry, len(line_x)):
        return False
    return _regression_prediction_bounds(geometry, len(line_x))


def _regression_curve_bounds(
    geometry: dict[str, object], line_count: int
) -> bool:
    return all(
        _aligned_numbers(geometry[field], line_count)
        for field in ("line_y", "ci_lb", "ci_ub")
    )


def _regression_prediction_bounds(
    geometry: dict[str, object], line_count: int
) -> bool:
    pi_lb = geometry.get("pi_lb")
    pi_ub = geometry.get("pi_ub")
    if (pi_lb is None) != (pi_ub is None):
        return False
    if pi_lb is None:
        return True
    return _aligned_numbers(pi_lb, line_count) and _aligned_numbers(pi_ub, line_count)


def _regression_confidence(geometry: dict[str, object]) -> bool:
    level = geometry.get("confidence_level")
    if not _finite_double(level):
        return False
    return 0 < cast(int | float, level) < 100


def _funnel_geometry(geometry: dict[str, object], row_count: int) -> bool:
    return (
        _funnel_axes(geometry)
        and _funnel_study_values(geometry, row_count)
        and _funnel_summary_values(geometry)
        and _funnel_deeks_values(geometry, row_count)
    )


def _funnel_axes(geometry: dict[str, object]) -> bool:
    kind = geometry.get("kind")
    if not isinstance(kind, str) or kind not in {
        "ordinary", "contour", "deeks", "trimfill"
    }:
        return False
    metric = geometry.get("metric")
    if not isinstance(metric, str):
        return False
    if not _funnel_axis_mode(geometry, kind):
        return False
    return _funnel_axis_transform(geometry, kind, metric)


def _funnel_axis_mode(geometry: dict[str, object], kind: str) -> bool:
    expected_axis = (
        "deeks_predictor_effect" if kind == "deeks" else "effect_standard_error"
    )
    return geometry.get("axis_mode") == expected_axis


def _funnel_axis_transform(
    geometry: dict[str, object], kind: str, metric: str
) -> bool:
    expected_transform = (
        "exp_effect_ticks"
        if kind != "deeks" and metric in {"OR", "RR"}
        else "identity"
    )
    return geometry.get("axis_transform") == expected_transform


def _funnel_study_values(geometry: dict[str, object], row_count: int) -> bool:
    if not _aligned_numbers(geometry["effect"], row_count):
        return False
    standard_error = geometry["standard_error"]
    if not _aligned_positive_numbers(standard_error, row_count):
        return False
    imputed = geometry.get("imputed")
    if not isinstance(imputed, list) or not all(type(value) is bool for value in imputed):
        return False
    return len(imputed) == row_count


def _funnel_summary_values(geometry: dict[str, object]) -> bool:
    if not all(
        _finite_double(geometry[field])
        for field in ("center", "pooled_center", "tau2")
    ):
        return False
    if cast(int | float, geometry["tau2"]) < 0:
        return False
    return True


def _funnel_deeks_values(geometry: dict[str, object], row_count: int) -> bool:
    kind = geometry["kind"]
    predictor = geometry.get("deeks_predictor")
    intercept = geometry.get("deeks_intercept")
    slope = geometry.get("deeks_slope")
    if kind == "deeks":
        return (
            _aligned_numbers(predictor, row_count)
            and _finite_double(intercept)
            and _finite_double(slope)
        )
    return predictor is None and intercept is None and slope is None


def _sroc_geometry(geometry: dict[str, object], row_count: int) -> bool:
    if not all(
        _aligned_numbers(geometry[field], row_count)
        for field in ("point_fpr", "point_sensitivity")
    ) or not _aligned_positive_numbers(geometry["sample_size"], row_count):
        return False
    if not all(
        _xy_pair(geometry.get(field), nullable=field in {"confidence_region", "prediction_region"})
        for field in ("curve_observed", "curve_full", "confidence_region", "prediction_region")
    ):
        return False
    if not all(
        _finite_double(geometry[field])
        for field in ("summary_sensitivity", "summary_specificity")
    ):
        return False
    return _optional_number(geometry.get("auc_pauc"))


def _coefficient_geometry(geometry: dict[str, object], row_count: int) -> bool:
    if not isinstance(geometry.get("scale"), str):
        return False
    return all(
        _aligned_numbers(geometry[field], row_count)
        for field in ("estimate", "ci_lb", "ci_ub")
    )


def _xy_pair(value: object, *, nullable: bool) -> bool:
    if value is None:
        return nullable
    if not _json_object(value):
        return False
    pair = value
    if set(pair) != {"x", "y"}:
        return False
    x = pair.get("x")
    y = pair.get("y")
    return (
        isinstance(x, list)
        and bool(x)
        and _aligned_numbers(y, len(x))
        and _aligned_numbers(x, len(x))
    )


def _geometry_appearance(
    renderer: str, appearance: dict[str, object], *, exact: bool
) -> bool:
    fields = _GEOMETRY_APPEARANCE_FIELDS[renderer]
    if exact and set(appearance) != fields:
        return False
    if not set(appearance).issubset(fields):
        return False
    return all(
        _geometry_appearance_value(renderer, field, value, exact)
        for field, value in appearance.items()
    )


def _geometry_appearance_value(
    renderer: str, field: str, value: object, exact: bool
) -> bool:
    arrays = _GEOMETRY_ARRAY_APPEARANCE_FIELDS[renderer]
    booleans = _GEOMETRY_BOOL_APPEARANCE_FIELDS[renderer]
    numbers = _GEOMETRY_NUMERIC_APPEARANCE_FIELDS[renderer]
    nullable_labels = _GEOMETRY_NULLABLE_LABEL_FIELDS[renderer]
    if field in arrays:
        return _appearance_array(value)
    if field == "fp_marker_area":
        return _is_sroc_marker_area(value)
    if field in booleans:
        return type(value) is bool
    if field in numbers:
        return _finite_double(value)
    if value is None and not exact and field in nullable_labels:
        return True
    return isinstance(value, str)


def _is_sroc_marker_area(value: object) -> bool:
    return isinstance(value, str) and value in {"uniform", "sample-size"}


def _appearance_array(value: object) -> bool:
    if isinstance(value, str):
        return True
    if not isinstance(value, list):
        return False
    return _string_list(value) or all(_finite_double(item) for item in value)


def is_plot_presentation(value: object, renderer: object) -> bool:
    """Validate an appearance update against the selected frozen renderer."""
    if not _json_object(value) or not isinstance(renderer, str):
        return False
    if renderer == "rcmetar_forest_v1":
        return is_forest_presentation(value)
    if renderer not in _GEOMETRY_RENDERERS:
        return False
    return _geometry_appearance(renderer, value, exact=False)


def render_state_matches_capability(
    state: object, plot_kind: object, regenerator: object
) -> bool:
    if not isinstance(plot_kind, str) or not isinstance(regenerator, str):
        return False
    if not _json_object(state) or render_state_size(state) is None:
        return False
    renderer = state.get("renderer")
    if not isinstance(renderer, str):
        return False
    expected_regenerator = {
        "rcmetar_forest_v1": "forest",
        _REGRESSION_RENDERER: "regression",
        _FUNNEL_RENDERER: "funnel",
        _SROC_RENDERER: "sroc",
        _COEFFICIENT_RENDERER: "forest",
    }.get(renderer)
    return (
        expected_regenerator is not None
        and regenerator == expected_regenerator
        and plot_kind in _PLOT_KIND_RENDERERS[renderer]
    )


def _forest_identity(state: dict[str, object], figure_key: str | None) -> bool:
    data_type = state.get("data_type")
    style = state.get("style")
    variant = state.get("variant")
    if not _forest_identity_key(state, figure_key):
        return False
    return (
        _is_allowed_string(data_type, {"binary", "continuous", "diagnostic"})
        and _is_allowed_string(style, {"default", "revman", "bmj"})
        and _is_allowed_string(
            variant, {"standard", "cumulative", "leave-one-out", "subgroup"}
        )
        and type(state.get("single_study")) is bool
    )


def _forest_identity_key(state: dict[str, object], figure_key: str | None) -> bool:
    saved_key = state.get("figure_key")
    version = state.get("version")
    return (
        type(version) is int
        and version == 1
        and state.get("renderer") == "rcmetar_forest_v1"
        and isinstance(saved_key, str)
        and (figure_key is None or saved_key == figure_key)
    )


def _is_allowed_string(value: object, allowed: frozenset[str] | set[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _forest_study_data(state: dict[str, object]) -> bool:
    studies_value = state.get("studies")
    summary_value = state.get("summary")
    if not _mapping_with_fields(studies_value, _STUDY_FIELDS):
        return False
    if not _valid_frozen_summary(summary_value):
        return False
    studies = cast(dict[str, object], studies_value)
    labels_value = studies["labels"]
    if not _string_list(labels_value) or not labels_value:
        return False
    labels = cast(list[str], labels_value)
    return _forest_study_vectors(studies, len(labels)) and _forest_display_data(
        state, len(labels)
    )


def _forest_study_vectors(studies: dict[str, object], row_count: int) -> bool:
    for field in ("yi", "vi", "ci_lb", "ci_ub"):
        if not _aligned_optional_numbers(studies[field], row_count):
            return False
    return True


def _forest_display_data(state: dict[str, object], row_count: int) -> bool:
    if not _forest_ilab_data(state.get("ilab"), row_count):
        return False
    if not _forest_auxiliary_values(state, row_count):
        return False
    if not _forest_effect_display(state.get("effect_display"), row_count):
        return False
    return _forest_params(state["params"])


def _forest_ilab_data(value: object, row_count: int) -> bool:
    if not _json_object(value) or set(value) != {
        "matrix", "columns", "headers", "groups"
    }:
        return False
    headers = value["headers"]
    if not _string_list(headers) or not _string_list(value["groups"]):
        return False
    return _ilab_matrix(value["matrix"], len(headers), row_count) and _ilab_columns(
        value["columns"], row_count
    )


def _ilab_matrix(value: object, column_count: int, row_count: int) -> bool:
    if not isinstance(value, list):
        return False
    for row in value:
        if not isinstance(row, list) or len(row) != column_count:
            return False
        if not all(isinstance(cell, str) for cell in row):
            return False
    return not value or len(value) == row_count


def _ilab_columns(value: object, row_count: int) -> bool:
    return isinstance(value, list) and all(
        _ilab_column(column, row_count) for column in value
    )


def _forest_auxiliary_values(state: dict[str, object], row_count: int) -> bool:
    weights = state["weights"]
    if weights is not None and not _aligned_optional_numbers(weights, row_count):
        return False
    if not state["single_study"] and not isinstance(weights, list):
        return False
    sample_sizes = state["sample_sizes"]
    if sample_sizes is not None and not _aligned_optional_numbers(sample_sizes, row_count):
        return False
    return _required_number_list(state["plot_range"], 2)


def _forest_effect_display(value: object, row_count: int) -> bool:
    if not _json_object(value):
        return False
    if set(value) != {"y_disp", "lb_disp", "ub_disp"}:
        return False
    return all(
        _aligned_optional_numbers(value[field], row_count)
        for field in ("y_disp", "lb_disp", "ub_disp")
    )


def _forest_subgroups(state: dict[str, object]) -> bool:
    groups_value = state.get("subgroups")
    if not _json_object(groups_value):
        return False
    groups = groups_value
    if set(groups) != _SUBGROUP_STATE_FIELDS:
        return False
    names_value = groups.get("names")
    if not _string_list(names_value) or not names_value:
        return False
    names = cast(list[str], names_value)
    if not _forest_subgroup_results(groups, len(names)):
        return False
    studies = cast(dict[str, object], state["studies"])
    row_count = len(cast(list[object], studies["labels"]))
    return _forest_subgroup_layout(groups, row_count, len(names))


def _forest_subgroup_results(groups: dict[str, object], group_count: int) -> bool:
    summaries = groups.get("results")
    if not isinstance(summaries, list) or len(summaries) != group_count:
        return False
    if not all(_valid_frozen_summary(item) for item in summaries):
        return False
    if not _valid_frozen_summary(groups.get("overall")):
        return False
    return _forest_subgroup_difference(groups)


def _forest_subgroup_difference(groups: dict[str, object]) -> bool:
    differences = groups.get("difference_test")
    if differences is None:
        return True
    if not _mapping_with_fields(differences, _DIFFERENCE_FIELDS):
        return False
    difference_values = cast(dict[str, object], differences)
    return all(_optional_number(item) for item in difference_values.values())


def _forest_subgroup_layout(
    groups: dict[str, object], row_count: int, group_count: int
) -> bool:
    return (
        _required_number_list(groups.get("study_rows"), row_count)
        and _required_number_list(groups.get("header_rows"), group_count)
        and _required_number_list(groups.get("polygon_rows"), group_count)
        and _optional_number(groups.get("overall_row"))
        and _required_number_list(groups.get("ylim"), 2)
    )


def _valid_frozen_summary(value: object) -> bool:
    if not _summary_mapping(value):
        return False
    summary = cast(dict[str, object], value)
    return all(
        isinstance(item, str) if field == "method" else _optional_number(item)
        for field, item in summary.items()
    )


def _mapping_with_fields(value: object, fields: frozenset[str]) -> bool:
    return isinstance(value, dict) and set(value) == fields and _json_tree(value)


def _summary_mapping(value: object) -> bool:
    return (
        isinstance(value, dict)
        and {"b", "ci_lb", "ci_ub"}.issubset(value)
        and set(value).issubset(_SUMMARY_FIELDS)
        and _json_tree(value)
    )


def _json_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict) and all(isinstance(key, str) for key in value)


def _json_tree(value: object) -> bool:
    pending = [(value, 0)]
    while pending:
        current, depth = pending.pop()
        if depth > 24:
            return False
        if isinstance(current, (dict, list)):
            children = _json_container_children(current, depth + 1)
            if children is None:
                return False
            pending.extend(children)
            continue
        if not _json_scalar(current):
            return False
    return True


def _json_container_children(value: object, depth: int) -> list[tuple[object, int]] | None:
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            return None
        return [(item, depth) for item in value.values()]
    if isinstance(value, list):
        return [(item, depth) for item in value]
    return []


def _json_scalar(value: object) -> bool:
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, (int, float)):
        return _finite_double(value)
    return False


def _string_list(value: object) -> TypeGuard[list[str]]:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _required_number_list(value: object, expected_length: int) -> bool:
    return isinstance(value, list) and len(value) == expected_length and all(
        _finite_double(item) for item in value
    )


def _aligned_optional_numbers(value: object, expected_length: int) -> bool:
    return isinstance(value, list) and len(value) == expected_length and all(
        _optional_number(item) for item in value
    )


def _aligned_numbers(value: object, expected_length: int) -> bool:
    return isinstance(value, list) and len(value) == expected_length and all(
        _finite_double(item) for item in value
    )


def _aligned_positive_numbers(value: object, expected_length: int) -> bool:
    return _aligned_numbers(value, expected_length) and all(
        cast(int | float, item) > 0 for item in cast(list[object], value)
    )


def _optional_number(value: object) -> bool:
    return value is None or _finite_double(value)


def _finite_double(value: object) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value))
    except OverflowError:
        return False


def _ilab_column(value: object, row_count: int) -> bool:
    if not _json_object(value):
        return False
    column = value
    if set(column) != {"key", "group", "header", "values"}:
        return False
    if not all(isinstance(column[key], str) for key in ("key", "group", "header")):
        return False
    values = column["values"]
    return _string_list(values) and len(values) == row_count


def _forest_params(value: object) -> bool:
    if not _json_object(value):
        return False
    params = value
    return set(params).issubset(FOREST_PARAMETER_FIELDS) and all(
        _forest_parameter_value(name, item) for name, item in params.items()
    )


def _forest_parameter_value(name: str, value: object) -> bool:
    if value is None or isinstance(value, (str, bool)) or _finite_double(value):
        return True
    if name == "fp_xticks" and isinstance(value, list):
        return _string_list(value) or all(_optional_number(item) for item in value)
    return False


def is_forest_presentation(value: object) -> bool:
    if not _json_object(value):
        return False
    presentation = value
    return set(presentation).issubset(FOREST_PRESENTATION_FIELDS) and all(
        _forest_parameter_value(name, item) for name, item in presentation.items()
    )


def validated_render_states(value: object, image_keys: set[str]) -> dict[str, dict[str, object]]:
    if value is None:
        return {}
    if not _json_object(value):
        raise ValueError("saved plot renderer state does not match its figures")
    render_states = value
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
