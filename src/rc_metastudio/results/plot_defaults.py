"""Generated user-facing plot defaults. Do not edit directly."""

from enum import StrEnum
from typing import NamedTuple

FOREST_ARM_LABELS = ("Intervention", "Control")
PLOT_STYLE_LABELS = {
    "default": "Default",
    "revman": "RevMan",
    "bmj": "BMJ"
}
PLOT_STYLE_ACCENTS = {
    "default": "#2f5597",
    "revman": "#000000",
    "bmj": "#5f4c9a"
}
BUBBLE_STYLE_ACCENTS = {
    "default": "#2f5597",
    "revman": "#111111",
    "bmj": "#6b58a6"
}


class FunnelStyle(StrEnum):
    DEFAULT = "default"
    REVMAN = "revman"
    BMJ = "bmj"


class FunnelStylePreset(NamedTuple):
    point_symbol: int
    point_color: str
    reference_color: str
    region_color: str
    background_color: str


FUNNEL_STYLE_PRESETS = {
    "default": FunnelStylePreset(19, "#2F5597", "#2F5597", "#DDE6F4", "#FFFFFF"),
    "revman": FunnelStylePreset(15, "#111111", "#000000", "#D9D9D9", "#FFFFFF"),
    "bmj": FunnelStylePreset(18, "#6B58A6", "#6B58A6", "#E8E2F4", "#FFFFFF"),
}


def apply_default_forest_arm_labels(surface):
    surface.col3_str_edit.setText(FOREST_ARM_LABELS[0])
    surface.col4_str_edit.setText(FOREST_ARM_LABELS[1])
