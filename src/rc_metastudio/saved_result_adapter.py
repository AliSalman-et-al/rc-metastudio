# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Capture analysis output for a portable project and reopen it without R."""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from rc_metastudio import analysis_results, saved_analysis


_MEDIA_TYPES = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}
_EXTENSIONS = {
    "image/svg+xml": "svg",
    "image/png": "png",
    "image/jpeg": "jpg",
}


def capture_result(
    input_snapshot: Mapping[str, object],
    specification: Mapping[str, object],
    result: Mapping[str, object],
    *,
    warnings: tuple[str, ...] = (),
    backend_versions: Mapping[str, str],
) -> saved_analysis.SavedAnalysisRecord:
    """Store numerical output and bounded figure bytes, never machine-local paths."""
    analysis_results.parse_analysis_result(result)
    portable: dict[str, object] = copy.deepcopy(dict(result))
    figures: list[saved_analysis.SavedFigureInput] = []
    figure_warnings = list(warnings)
    sections = portable.get("sections")
    section_titles: dict[str, str] = {}
    for section in (sections if isinstance(sections, list) else []):
        if not isinstance(section, dict):
            continue
        fields = cast(dict[str, object], section)
        key, title = fields.get("source_key"), fields.get("title")
        if fields.get("kind") == "image" and isinstance(key, str) and isinstance(title, str):
            section_titles[key] = title
    captured_paths: dict[str, str] = {}
    for field in ("images", "display_images"):
        paths_value = portable.get(field, {})
        if not isinstance(paths_value, dict):
            raise ValueError(f"analysis {field} must be a mapping")
        paths = cast(dict[str, str], paths_value)
        for key, original_path in paths.items():
            if not isinstance(key, str) or not isinstance(original_path, str):
                raise ValueError(f"analysis {field} needs text paths")
            if original_path in captured_paths:
                paths[key] = captured_paths[original_path]
                continue
            path = Path(original_path)
            media_type = _MEDIA_TYPES.get(path.suffix.lower())
            if not media_type or not path.is_file():
                paths[key] = ""
                figure_warnings.append(f"{key}: figure was unavailable for saving")
                continue
            if path.stat().st_size > saved_analysis.MAX_FIGURE_SIZE:
                paths[key] = ""
                figure_warnings.append(f"{key}: figure exceeded the project size limit")
                continue
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            asset = f"assets/{digest}.{_EXTENSIONS[media_type]}"
            figure_id = f"{field}:{key}"
            figures.append(
                saved_analysis.SavedFigureInput(
                    figure_id,
                    section_titles.get(key, key),
                    media_type,
                    data,
                )
            )
            paths[key] = asset
            captured_paths[original_path] = asset
    portable["image_params_paths"] = {}
    capabilities_value = portable.setdefault("plot_capabilities", {})
    if not isinstance(capabilities_value, dict):
        raise ValueError("analysis plot capabilities must be a mapping")
    capabilities = cast(dict[str, dict[str, object]], capabilities_value)
    for capability in capabilities.values():
        if not isinstance(capability, dict):
            raise ValueError("analysis plot capability must be a mapping")
        capability["editable"] = False
        capability["styleable"] = False
        capability["regenerator"] = "none"
    texts = portable.get("texts")
    if isinstance(texts, Mapping) and "sequential_recovery" in texts:
        figure_warnings.append(
            "The native sequence figure was unavailable; see Incomplete sequence for the retained step results."
        )
    estimate = _pooled_estimate(portable)
    available = (
        isinstance(estimate, dict)
        and cast(dict[str, object], estimate).get("status") == "available"
    )
    status = "complete" if available and not figure_warnings[len(warnings):] else "partial"
    if (
        isinstance(portable.get("meta_regression_numerics"), Mapping)
        or isinstance(portable.get("reitsma_meta_regression_numerics"), Mapping)
    ):
        status = "complete" if not figure_warnings[len(warnings):] else "partial"
    cumulative = portable.get("cumulative_numerics")
    leave_one_out = portable.get("leave_one_out_numerics")
    if isinstance(cumulative, Mapping):
        cumulative = cast(Mapping[str, object], cumulative)
        status = (
            "complete"
            if cumulative.get("status") == "complete" and not figure_warnings[len(warnings):]
            else "partial"
        )
    elif isinstance(leave_one_out, Mapping):
        leave_one_out = cast(Mapping[str, object], leave_one_out)
        rows = leave_one_out.get("rows")
        status = (
            "complete"
            if isinstance(rows, list)
            and all(isinstance(row, Mapping) and row.get("status") == "available" for row in rows)
            and not figure_warnings[len(warnings):]
            else "partial"
        )
    scientific_specification: dict[str, object] = copy.deepcopy(dict(specification))
    params_value = scientific_specification.get("params")
    presentation: dict[str, object] = {}
    if isinstance(params_value, dict):
        params = cast(dict[str, object], params_value)
        presentation = {
            key: value
            for key, value in params.items()
            if key.startswith(("fp_", "bp_"))
            and not key.endswith(("outpath", "display_path"))
        }
        scientific_specification["params"] = {
            key: value
            for key, value in params.items()
            if not key.startswith(("fp_", "bp_"))
        }
    return saved_analysis.create_record(
        input_snapshot,
        scientific_specification,
        portable,
        status=status,
        warnings=figure_warnings,
        backend_versions=backend_versions,
        figures=figures,
        presentation=presentation,
    )


def _pooled_estimate(result: Mapping[str, object]) -> object:
    for family in (
        "binary_numerics",
        "binary_proportion_numerics",
        "continuous_numerics",
        "diagnostic_numerics",
    ):
        numerics = result.get(family)
        if not isinstance(numerics, Mapping):
            continue
        pooled = numerics.get("pooled")
        if not isinstance(pooled, Mapping):
            continue
        if family == "continuous_numerics":
            return pooled.get("estimate")
        display = pooled.get("display")
        if isinstance(display, Mapping):
            return display.get("estimate")
    return None


def restore_result(
    record: saved_analysis.SavedAnalysisRecord, output_dir: Path
) -> analysis_results.AnalysisResult:
    """Materialize checked figure bytes for the existing native Results viewer."""
    saved_analysis.validate_record(record.value, record.assets)
    result = copy.deepcopy(record.value["results"])
    if not isinstance(result, dict):
        raise ValueError("saved result must be a mapping")
    result["image_params_paths"] = {}
    capabilities = result.get("plot_capabilities", {})
    if not isinstance(capabilities, dict):
        raise ValueError("saved result plot capabilities must be a mapping")
    for capability in capabilities.values():
        if not isinstance(capability, dict):
            raise ValueError("saved result plot capability must be a mapping")
        capability["editable"] = False
        capability["styleable"] = False
        capability["regenerator"] = "none"
    output_dir.mkdir(parents=True, exist_ok=True)
    materialized: dict[str, str] = {}
    for field in ("images", "display_images"):
        paths = result.get(field, {})
        if not isinstance(paths, dict):
            raise ValueError(f"saved result {field} must be a mapping")
        for key, asset in paths.items():
            if asset == "":
                continue
            if not isinstance(asset, str) or asset not in record.assets:
                raise ValueError(f"saved result {field} references a missing figure")
            if asset not in materialized:
                path = output_dir / Path(asset).name
                path.write_bytes(record.assets[asset])
                materialized[asset] = str(path)
            paths[key] = materialized[asset]
    return analysis_results.parse_analysis_result(result)
