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
    _sync_small_study_effects_report_images(portable, restoring=False)
    _sync_reitsma_report_images(portable, restoring=False)
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
    small_study_effects = portable.get("small_study_effects")
    if isinstance(small_study_effects, Mapping):
        report = cast(Mapping[str, object], small_study_effects).get("report")
        status = (
            "complete"
            if isinstance(report, Mapping)
            and cast(Mapping[str, object], report).get("status") == "complete"
            and not figure_warnings[len(warnings):]
            else "partial"
        )
    subgroup_numerics = portable.get("subgroup_numerics")
    if isinstance(subgroup_numerics, Mapping):
        levels = cast(Mapping[str, object], subgroup_numerics).get("levels")
        overall = cast(Mapping[str, object], subgroup_numerics).get("overall")
        request_params = specification.get("params")
        wants_plot = (
            isinstance(request_params, Mapping)
            and cast(Mapping[str, object], request_params).get("create.plot") is True
        )
        plot_available = (
            not wants_plot
            or subgroup_numerics.get("figure_status") == "available"
        )
        status = (
            "complete"
            if isinstance(overall, Mapping)
            and overall.get("status") == "available"
            and isinstance(levels, list)
            and levels
            and all(
                isinstance(level, Mapping) and level.get("status") == "available"
                for level in levels
            )
            and plot_available
            and not figure_warnings[len(warnings) :]
            else "partial"
        )
    reitsma_report = portable.get("reitsma_report")
    if isinstance(reitsma_report, Mapping):
        raw_sections = cast(Mapping[str, object], reitsma_report).get("sections")
        sections_by_key: dict[str, Mapping[str, object]] = {}
        if isinstance(raw_sections, list):
            for raw_section in raw_sections:
                if not isinstance(raw_section, Mapping):
                    continue
                section = cast(Mapping[str, object], raw_section)
                key = section.get("key")
                if isinstance(key, str):
                    sections_by_key[key] = section
        specification_params = specification.get("params")
        wants_sroc = (
            isinstance(specification_params, Mapping)
            and cast(Mapping[str, object], specification_params).get("create.plot") is True
        )
        summary = sections_by_key.get("Summary operating point")
        sroc = sections_by_key.get("SROC")
        status = (
            "complete"
            if summary is not None
            and summary.get("status") == "available"
            and (not wants_sroc or (sroc is not None and sroc.get("status") == "available"))
            and not figure_warnings[len(warnings):]
            else "partial"
        )
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
    _sync_small_study_effects_report_images(result, restoring=True)
    _sync_reitsma_report_images(result, restoring=True)
    return analysis_results.parse_analysis_result(result)


def _sync_small_study_effects_report_images(
    result: dict[str, object], *, restoring: bool
) -> None:
    """Keep saved report figure status aligned with portable image assets."""
    small_value = result.get("small_study_effects")
    if not isinstance(small_value, dict):
        return
    report_value = small_value.get("report")
    if not isinstance(report_value, dict):
        return
    report = cast(dict[str, object], report_value)
    images_value = result.get("images", {})
    display_value = result.get("display_images", {})
    if not isinstance(images_value, Mapping) or not isinstance(display_value, Mapping):
        return
    images = cast(Mapping[str, str], images_value)
    display_images = cast(Mapping[str, str], display_value)
    unavailable_reason = (
        "The saved project did not contain this figure."
        if restoring
        else "The figure could not be captured in the saved project."
    )

    def has_figure(key: object) -> bool:
        if not isinstance(key, str):
            return False
        path = display_images.get(key) or images.get(key)
        return isinstance(path, str) and bool(path) and (
            not restoring or Path(path).is_file()
        )

    figures_value = report.get("figures")
    missing = False
    if isinstance(figures_value, list):
        for raw in figures_value:
            if not isinstance(raw, dict) or raw.get("status") != "available":
                continue
            figure = cast(dict[str, object], raw)
            if not has_figure(figure.get("key")):
                figure["status"] = "not_available"
                figure["reason"] = unavailable_reason
                missing = True

    requests_value = report.get("funnel_requests")
    if isinstance(requests_value, list):
        for raw in requests_value:
            if not isinstance(raw, dict) or raw.get("status") != "available":
                continue
            request = cast(dict[str, object], raw)
            if not has_figure(request.get("figure_key")):
                request["status"] = "not_available"
                request["reason"] = unavailable_reason
                missing = True
    if missing:
        report["status"] = "partial"
        sections_value = report.get("sections")
        if isinstance(sections_value, list):
            for raw in sections_value:
                if isinstance(raw, dict) and raw.get("key") == "funnel_figures":
                    raw["status"] = "not_available"
                    raw["reason"] = unavailable_reason


def _sync_reitsma_report_images(result: dict[str, object], *, restoring: bool) -> None:
    """Keep the joint report's SROC reference aligned with its stored image."""
    report_value = result.get("reitsma_report")
    if not isinstance(report_value, dict):
        return
    report = cast(dict[str, object], report_value)
    sections_value = report.get("sections")
    if not isinstance(sections_value, list):
        return
    images_value = result.get("images", {})
    display_images_value = result.get("display_images", {})
    if not isinstance(images_value, Mapping) or not isinstance(display_images_value, Mapping):
        return
    images = cast(Mapping[str, str], images_value)
    display_images = cast(Mapping[str, str], display_images_value)
    for raw_section in sections_value:
        if not isinstance(raw_section, dict):
            continue
        section = cast(dict[str, object], raw_section)
        if (
            section.get("kind") != "image"
            or section.get("status") != "available"
        ):
            continue
        key = section.get("key")
        path = display_images.get(key) or images.get(key) if isinstance(key, str) else None
        if isinstance(path, str) and path:
            section["value"] = path
            continue
        section["status"] = "not_available"
        section["value"] = None
        section["reason"] = (
            "The saved project did not contain this figure."
            if restoring
            else "The figure could not be captured in the saved project."
        )
