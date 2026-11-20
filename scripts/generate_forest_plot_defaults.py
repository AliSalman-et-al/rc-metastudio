"""Generate plot defaults from the shared contract."""

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "forest_plot_defaults.json"
PYTHON_TARGET = ROOT / "src/rc_metastudio/results/plot_defaults.py"
R_TARGET = ROOT / "r" / "RCMetaR" / "R" / "forest_defaults.R"
FUNNEL_COLOR_FIELDS = ("point_color", "reference_color", "region_color", "background_color")


def _render_funnel_presets(styles: dict) -> str:
    presets = []
    for style, values in styles.items():
        preset = values["funnel"]
        if not style.isidentifier() or type(preset["point_symbol"]) is not int:
            raise ValueError("invalid funnel style code or point symbol")
        if any(not re.fullmatch(r"#[0-9a-fA-F]{6}", preset[field]) for field in FUNNEL_COLOR_FIELDS):
            raise ValueError("funnel colors must be six-digit hex colors")
        arguments = ", ".join(json.dumps(preset[field]) for field in ("point_symbol", *FUNNEL_COLOR_FIELDS))
        presets.append(f'    "{style}": FunnelStylePreset({arguments}),\n')
    return "".join(presets)


def _style_palette(styles: dict) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    labels = {style: values["label"] for style, values in styles.items()}
    accents = {style: values["accent"] for style, values in styles.items()}
    bubble_accents = {
        style: values.get("bubble_accent", accents[style])
        for style, values in styles.items()
    }
    if "default" not in styles or len(set(labels.values())) != len(labels):
        raise ValueError("styles must include default and have unique labels")
    for colors in (accents, bubble_accents):
        if any(not re.fullmatch(r"#[0-9a-fA-F]{6}", color) for color in colors.values()):
            raise ValueError("style accents must be six-digit hex colors")
    return labels, accents, bubble_accents


def rendered_targets() -> dict[Path, str]:
    defaults = json.loads(CONTRACT.read_text(encoding="utf-8"))
    values = defaults["arm_labels"]
    if len(values) != 2 or not all(
        isinstance(value, str) and value for value in values
    ):
        raise ValueError("arm_labels must contain two non-empty strings")
    intervention, control = (json.dumps(value, ensure_ascii=False) for value in values)
    styles = defaults["styles"]
    labels, accents, bubble_accents = _style_palette(styles)

    def r_colors(colors: dict[str, str]) -> str:
        return ", ".join(f"{json.dumps(key)}={json.dumps(value)}" for key, value in colors.items())

    return {
        PYTHON_TARGET: (
            '"""Generated user-facing plot defaults. Do not edit directly."""\n\n'
            "from enum import StrEnum\n"
            "from typing import NamedTuple\n\n"
            f"FOREST_ARM_LABELS = ({intervention}, {control})\n"
            f"PLOT_STYLE_LABELS = {json.dumps(labels, indent=4)}\n"
            f"PLOT_STYLE_ACCENTS = {json.dumps(accents, indent=4)}\n"
            f"BUBBLE_STYLE_ACCENTS = {json.dumps(bubble_accents, indent=4)}\n\n\n"
            "class FunnelStyle(StrEnum):\n"
            + "".join(f'    {style.upper()} = "{style}"\n' for style in styles)
            + "\n\nclass FunnelStylePreset(NamedTuple):\n"
            "    point_symbol: int\n"
            + "".join(f"    {field}: str\n" for field in FUNNEL_COLOR_FIELDS)
            + "\n\nFUNNEL_STYLE_PRESETS = {\n"
            + _render_funnel_presets(styles)
            + "}\n\n\n"
            "def apply_default_forest_arm_labels(surface):\n"
            "    surface.col3_str_edit.setText(FOREST_ARM_LABELS[0])\n"
            "    surface.col4_str_edit.setText(FOREST_ARM_LABELS[1])\n"
        ),
        R_TARGET: (
            "# Generated from config/forest_plot_defaults.json. Do not edit directly.\n"
            "rcmetar.default.arm.labels <- function() {\n"
            f"    c({intervention}, {control})\n"
            "}\n\n"
            "RCMETAR_PLOT_STYLE_ACCENTS <- list(\n"
            f"    forest=c({r_colors(accents)}),\n"
            f"    bubble=c({r_colors(bubble_accents)})\n"
            ")\n"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for path, content in rendered_targets().items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path.relative_to(ROOT))
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
    if stale:
        parser.error("stale generated defaults: %s" % ", ".join(map(str, stale)))


if __name__ == "__main__":
    main()
