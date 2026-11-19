# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validate plot capabilities and resolve their user-interface contracts."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, cast, get_args

PlotKind = Literal[
    "forest",
    "cumulative_forest",
    "leave_one_out_forest",
    "subgroup_forest",
    "reitsma_coefficient",
    "regression",
    "roc",
    "sroc",
    "trial_sequential",
    "funnel",
    "contour_funnel",
    "deeks_funnel",
    "trimfill_funnel",
    "other",
]
PlotRegenerator = Literal["forest", "regression", "funnel", "sroc", "trial_sequential", "none"]


@dataclass(frozen=True, slots=True)
class PlotCapability:
    """Immutable capability data attached to one semantic plot artifact."""

    plot_kind: PlotKind
    editable: bool
    styleable: bool
    regenerator: PlotRegenerator


REQUIRED_FIELDS = (
    "plot_kind",
    "editable",
    "styleable",
    "composition",
    "regenerator",
)

_FOREST_OPTIONS = frozenset(("style", "appearance", "forest", "axis", "summary"))
_FUNNEL_OPTIONS = frozenset(("funnel", "axis"))
_PLOT_RULES: dict[str, tuple[PlotRegenerator, frozenset[str]]] = {
    "forest": ("forest", _FOREST_OPTIONS | {"columns"}),
    "cumulative_forest": ("forest", _FOREST_OPTIONS),
    "leave_one_out_forest": ("forest", _FOREST_OPTIONS),
    "subgroup_forest": ("forest", _FOREST_OPTIONS),
    "reitsma_coefficient": ("forest", frozenset(("style", "appearance", "axis"))),
    "regression": (
        "regression",
        frozenset(("style", "appearance", "axis", "regression")),
    ),
    "roc": ("none", frozenset()),
    "sroc": ("sroc", frozenset(("style", "appearance", "axis", "sroc"))),
    "trial_sequential": ("trial_sequential", frozenset(("style", "appearance", "tsa_axis"))),
    "funnel": ("funnel", _FUNNEL_OPTIONS),
    "contour_funnel": ("funnel", _FUNNEL_OPTIONS),
    "deeks_funnel": ("funnel", _FUNNEL_OPTIONS),
    "trimfill_funnel": ("funnel", _FUNNEL_OPTIONS),
    "other": ("none", frozenset()),
}


def option_groups(plot_kind: str) -> frozenset[str]:
    rule = _PLOT_RULES.get(plot_kind)
    return rule[1] if rule is not None else frozenset()


def validate_result(result: Mapping[str, object]) -> dict[str, PlotCapability]:
    images = _string_mapping(result.get("images"), "images")
    descriptors = _descriptor_mapping(result.get("plot_capabilities"))
    missing = sorted(set(images) - set(descriptors))
    extra = sorted(set(descriptors) - set(images))
    if missing:
        raise ValueError(
            "Plot capability descriptor missing for: %s" % ", ".join(missing)
        )
    if extra:
        raise ValueError(
            "Plot capability descriptor has no matching image: %s" % ", ".join(extra)
        )

    normalized = {
        title: _validate_descriptor(title, descriptors[title]) for title in images
    }
    params_paths = _string_mapping(
        result.get("image_params_paths"), "image_params_paths"
    )
    missing_params = sorted(
        title
        for title, descriptor in normalized.items()
        if descriptor.editable and title not in params_paths
    )
    if missing_params:
        raise ValueError(
            "Editable plot capability descriptor missing plot data for: %s"
            % ", ".join(missing_params)
        )
    return normalized


def _string_mapping(value: object, label: str) -> dict[str, str]:
    if value is None or value == [] or value == ():
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    normalized: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise ValueError(f"{label} keys and values must be text")
        normalized[key] = item
    return normalized


def _descriptor_mapping(value: object) -> dict[str, dict[str, object]]:
    if value is None or value == [] or value == ():
        return {}
    if not isinstance(value, dict):
        raise ValueError("plot_capabilities must be a mapping")
    normalized: dict[str, dict[str, object]] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, dict):
            raise ValueError("plot capability entries must be named mappings")
        descriptor: dict[str, object] = {}
        for field, field_value in item.items():
            if not isinstance(field, str):
                raise ValueError("plot capability field names must be text")
            descriptor[field] = field_value
        normalized[key] = descriptor
    return normalized


def _validate_descriptor(title: str, descriptor: dict[str, object]) -> PlotCapability:
    _validate_descriptor_fields(title, descriptor)
    editable, styleable = _descriptor_flags(title, descriptor)
    if descriptor["composition"] != "single":
        raise ValueError("Unknown composition for %s: %s" % (title, descriptor["composition"]))
    plot_kind = _plot_kind(descriptor["plot_kind"], title)
    regenerator = _regenerator(descriptor["regenerator"], title)
    _validate_plot_rules(title, plot_kind, editable, styleable, regenerator)
    return PlotCapability(plot_kind, editable, styleable, regenerator)


def _validate_descriptor_fields(title: str, descriptor: dict[str, object]) -> None:
    if not isinstance(descriptor, dict):
        raise ValueError("Plot capability descriptor for %s must be a mapping" % title)
    missing = [field for field in REQUIRED_FIELDS if field not in descriptor]
    extra = sorted(set(descriptor) - set(REQUIRED_FIELDS))
    if missing or extra:
        raise ValueError(
            "Invalid plot capability fields for %s (missing: %s; extra: %s)"
            % (title, ", ".join(missing) or "none", ", ".join(extra) or "none")
        )


def _descriptor_flags(title: str, descriptor: dict[str, object]) -> tuple[bool, bool]:
    editable = descriptor["editable"]
    styleable = descriptor["styleable"]
    if not isinstance(editable, bool):
        raise ValueError("editable for %s must be boolean" % title)
    if not isinstance(styleable, bool):
        raise ValueError("styleable for %s must be boolean" % title)
    return editable, styleable


def _validate_plot_rules(
    title: str,
    plot_kind: PlotKind,
    editable: bool,
    styleable: bool,
    regenerator: PlotRegenerator,
) -> None:
    if editable and regenerator == "none":
        raise ValueError("Editable plot %s requires a regenerator" % title)
    if editable and regenerator != _PLOT_RULES[plot_kind][0]:
        raise ValueError(
            "Plot regenerator %s does not support plot kind %s for %s"
            % (regenerator, plot_kind, title)
        )
    if styleable and not option_groups(plot_kind):
        raise ValueError("Styleable plot %s requires option groups" % title)


def _plot_kind(value: object, title: str) -> PlotKind:
    if not isinstance(value, str) or value not in _PLOT_RULES:
        raise ValueError("Unknown plot_kind for %s: %s" % (title, value))
    return cast(PlotKind, value)


def _regenerator(value: object, title: str) -> PlotRegenerator:
    if value not in get_args(PlotRegenerator):
        raise ValueError("Unknown plot regenerator for %s: %s" % (title, value))
    return cast(PlotRegenerator, value)
