"""Generated user-facing forest-plot defaults. Do not edit directly."""

FOREST_ARM_LABELS = ("Intervention", "Control")
PLOT_STYLE_LABELS = {
    "default": "Default",
    "revman": "RevMan",
    "bmj": "BMJ"
}
PLOT_STYLE_ACCENTS = {
    "default": "#2f5597",
    "revman": "#000000",
    "bmj": "#6b58a6"
}
BUBBLE_STYLE_ACCENTS = {
    "default": "#2f5597",
    "revman": "#111111",
    "bmj": "#6b58a6"
}


def apply_default_forest_arm_labels(surface):
    surface.col3_str_edit.setText(FOREST_ARM_LABELS[0])
    surface.col4_str_edit.setText(FOREST_ARM_LABELS[1])
