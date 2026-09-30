# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Capture analysis output for a portable project and reopen it without R."""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import cast

from rc_metastudio import analysis_results, saved_analysis
from rc_metastudio.plot_render_state import (
    render_state_matches_capability,
    validated_render_states,
)


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


def _object_fields(value: object) -> dict[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    fields: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            return None
        fields[key] = item
    return fields


def _mutable_object_fields(value: object) -> dict[str, object] | None:
    fields = _object_fields(value)
    if fields is None or not isinstance(value, dict):
        return None
    return cast(dict[str, object], value)


def _mutable_text_paths(
    value: object, field: str, *, owner: str = "analysis"
) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{owner} {field} must be a mapping")
    for key, path in value.items():
        if not isinstance(key, str) or not isinstance(path, str):
            raise ValueError(f"{owner} {field} needs text paths")
    return cast(dict[str, str], value)


def _has_new_warnings(warnings: list[str], original_count: int) -> bool:
    return len(warnings) > original_count


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
    figure_warnings = list(warnings)
    section_titles = _section_titles(portable)
    figures: list[saved_analysis.SavedFigureInput] = []
    captured_paths: dict[str, str] = {}
    for field in ("images", "display_images"):
        _capture_image_paths(
            portable,
            field,
            section_titles,
            captured_paths,
            figures,
            figure_warnings,
        )
    _sync_small_study_effects_report_images(portable, restoring=False)
    _sync_reitsma_report_images(portable, restoring=False)
    portable["image_params_paths"] = {}
    image_fields = _object_fields(portable.get("images", {}))
    if image_fields is None:
        raise ValueError("analysis result images must be a mapping")
    validated_render_states(portable.get("plot_render_state"), set(image_fields))
    _validated_render_state_reasons(
        portable.get("plot_render_state_unavailable"), set(image_fields)
    )
    _disable_plot_editing(portable)
    texts = _object_fields(portable.get("texts"))
    if texts is not None and "sequential_recovery" in texts:
        figure_warnings.append(
            "The native sequence figure was unavailable; see Incomplete sequence for the retained step results."
        )
    status = _capture_status(
        portable, specification, figure_warnings, len(warnings)
    )
    scientific_specification, presentation = _split_presentation(specification)
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


def replace_saved_figure(
    record: saved_analysis.SavedAnalysisRecord,
    figure_key: str,
    image_data: bytes,
    image_media_type: str,
    *,
    display_data: bytes | None = None,
    display_media_type: str | None = None,
    presentation_update: Mapping[str, object],
) -> saved_analysis.SavedAnalysisRecord:
    """Return a record with one figure and its appearance replaced."""
    saved_analysis.validate_record(record.value, record.assets)
    if not figure_key:
        raise ValueError("a saved figure needs a key")
    results = copy.deepcopy(
        dict(cast(Mapping[str, object], record.value["results"]))
    )
    images = _mutable_text_paths(results.get("images", {}), "images", owner="saved result")
    display_images = _mutable_text_paths(
        results.get("display_images", {}), "display_images", owner="saved result"
    )
    results["images"] = images
    results["display_images"] = display_images

    actual_display_data, actual_display_media_type = _display_figure(
        image_data, image_media_type, display_data, display_media_type
    )
    replaced_ids = {
        f"images:{figure_key}",
        f"display_images:{figure_key}",
    }
    section_title = _section_titles(results).get(figure_key, figure_key)
    figure_titles, retained_figures = _retained_saved_figures(
        record, replaced_ids
    )
    image_id = f"images:{figure_key}"
    image_title = figure_titles.get(image_id, section_title)
    image_asset = _asset_reference(image_media_type, image_data)
    images[figure_key] = image_asset
    retained_figures.append(
        saved_analysis.SavedFigureInput(
            image_id, image_title, image_media_type, bytes(image_data)
        )
    )
    display_id = f"display_images:{figure_key}"
    display_title = figure_titles.get(display_id, section_title)
    display_asset = _asset_reference(actual_display_media_type, actual_display_data)
    display_images[figure_key] = display_asset
    retained_figures.append(
        saved_analysis.SavedFigureInput(
            display_id,
            display_title,
            actual_display_media_type,
            bytes(actual_display_data),
        )
    )
    _sync_small_study_effects_report_images(results, restoring=False)
    _sync_reitsma_report_images(results, restoring=False)

    presentation = _updated_presentation(record, figure_key, presentation_update)
    return saved_analysis.create_record(
        cast(Mapping[str, object], record.value["input_snapshot"]),
        cast(Mapping[str, object], record.value["specification"]),
        cast(Mapping[str, object], results),
        status=str(record.value["status"]),
        warnings=cast(list[str], record.value["warnings"]),
        backend_versions=cast(Mapping[str, str], record.value["backend_versions"]),
        figures=retained_figures,
        presentation=presentation,
        record_id=cast(str, record.value["id"]),
        created_at=datetime.fromisoformat(
            cast(str, record.value["created_at"]).replace("Z", "+00:00")
        ),
    )


def _display_figure(
    image_data: bytes,
    image_media_type: str,
    display_data: bytes | None,
    display_media_type: str | None,
) -> tuple[bytes, str]:
    if display_data is None:
        return image_data, image_media_type
    if display_media_type is None:
        raise ValueError("a display figure needs a media type")
    return display_data, display_media_type


def _retained_saved_figures(
    record: saved_analysis.SavedAnalysisRecord, replaced_ids: set[str]
) -> tuple[dict[str, str], list[saved_analysis.SavedFigureInput]]:
    titles: dict[str, str] = {}
    figures: list[saved_analysis.SavedFigureInput] = []
    for fields in cast(list[Mapping[str, object]], record.value["figures"]):
        identifier = cast(str, fields["id"])
        title = cast(str, fields["title"])
        titles[identifier] = title
        if identifier not in replaced_ids:
            asset = cast(str, fields["asset"])
            figures.append(
                saved_analysis.SavedFigureInput(
                    identifier,
                    title,
                    cast(str, fields["media_type"]),
                    record.assets[asset],
                )
            )
    return titles, figures


def _updated_presentation(
    record: saved_analysis.SavedAnalysisRecord,
    figure_key: str,
    updates: Mapping[str, object],
) -> dict[str, object]:
    presentation = copy.deepcopy(
        dict(cast(Mapping[str, object], record.value["presentation"]))
    )
    figures_value = presentation.get("figures", {})
    if not isinstance(figures_value, dict):
        raise ValueError("saved figure presentation must be a mapping")
    figures = cast(dict[str, object], figures_value)
    figure_value = figures.get(figure_key, {})
    if not isinstance(figure_value, dict):
        raise ValueError("saved figure presentation entry must be a mapping")
    figure = cast(dict[str, object], figure_value)
    for key, value in updates.items():
        if _is_presentation_field(key):
            figure[key] = value
    if figure:
        figures[figure_key] = figure
    presentation["figures"] = figures
    return presentation


def _is_presentation_field(key: str) -> bool:
    return _is_plot_field(key) and not key.endswith(
        ("outpath", "display_path")
    )


def _is_plot_field(key: str) -> bool:
    return key.startswith(("fp_", "bp_", "funnel."))


def _asset_reference(media_type: str, data: bytes) -> str:
    extension = _EXTENSIONS.get(media_type)
    if extension is None:
        raise ValueError("unsupported saved figure media type")
    return "assets/%s.%s" % (hashlib.sha256(data).hexdigest(), extension)


def _section_titles(result: Mapping[str, object]) -> dict[str, str]:
    sections = result.get("sections")
    if not isinstance(sections, list):
        return {}
    titles: dict[str, str] = {}
    for raw_section in sections:
        fields = _object_fields(raw_section)
        if fields is None or fields.get("kind") != "image":
            continue
        key, title = fields.get("source_key"), fields.get("title")
        if isinstance(key, str) and isinstance(title, str):
            titles[key] = title
    return titles


def _capture_image_paths(
    result: dict[str, object],
    field: str,
    titles: Mapping[str, str],
    captured_paths: dict[str, str],
    figures: list[saved_analysis.SavedFigureInput],
    warnings: list[str],
) -> None:
    paths = _mutable_text_paths(result.get(field, {}), field)
    for key, original_path in paths.items():
        if original_path in captured_paths:
            paths[key] = captured_paths[original_path]
            continue
        captured = _capture_figure(field, key, original_path, titles, warnings)
        if captured is None:
            paths[key] = ""
            continue
        asset, figure = captured
        paths[key] = asset
        captured_paths[original_path] = asset
        figures.append(figure)


def _capture_figure(
    field: str,
    key: str,
    original_path: str,
    titles: Mapping[str, str],
    warnings: list[str],
) -> tuple[str, saved_analysis.SavedFigureInput] | None:
    path = Path(original_path)
    media_type = _MEDIA_TYPES.get(path.suffix.lower())
    if not media_type or not path.is_file():
        warnings.append(f"{key}: figure was unavailable for saving")
        return None
    if path.stat().st_size > saved_analysis.MAX_FIGURE_SIZE:
        warnings.append(f"{key}: figure exceeded the project size limit")
        return None
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    asset = f"assets/{digest}.{_EXTENSIONS[media_type]}"
    figure = saved_analysis.SavedFigureInput(
        f"{field}:{key}", titles.get(key, key), media_type, data
    )
    return asset, figure


def _disable_plot_editing(result: dict[str, object]) -> None:
    capabilities = _mutable_object_fields(result.setdefault("plot_capabilities", {}))
    if capabilities is None:
        raise ValueError("analysis plot capabilities must be a mapping")
    for raw_capability in capabilities.values():
        capability = _mutable_object_fields(raw_capability)
        if capability is None:
            raise ValueError("analysis plot capability must be a mapping")
        capability["editable"] = False


def _capture_status(
    result: Mapping[str, object],
    specification: Mapping[str, object],
    warnings: list[str],
    original_warning_count: int,
) -> str:
    has_warning = _has_new_warnings(warnings, original_warning_count)
    estimate = _object_fields(_pooled_estimate(result))
    status = _status(estimate is not None and estimate.get("status") == "available" and not has_warning)
    if _has_mapping(result.get("meta_regression_numerics")) or _has_mapping(
        result.get("reitsma_meta_regression_numerics")
    ):
        status = _status(not has_warning)
    for route_status in (
        _small_study_status(result.get("small_study_effects"), has_warning),
        _subgroup_status(result.get("subgroup_numerics"), specification, has_warning),
        _reitsma_status(result.get("reitsma_report"), specification, has_warning),
        _sequential_status(
            result.get("cumulative_numerics"),
            result.get("leave_one_out_numerics"),
            has_warning,
        ),
    ):
        if route_status is not None:
            status = route_status
    return status


def _status(complete: bool) -> str:
    return "complete" if complete else "partial"


def _has_mapping(value: object) -> bool:
    return _object_fields(value) is not None


def _small_study_status(value: object, has_warning: bool) -> str | None:
    small_study = _object_fields(value)
    if small_study is None:
        return None
    report = _object_fields(small_study.get("report"))
    complete = report is not None and report.get("status") == "complete"
    return _status(complete and not has_warning)


def _subgroup_status(
    value: object, specification: Mapping[str, object], has_warning: bool
) -> str | None:
    subgroup = _object_fields(value)
    if subgroup is None:
        return None
    overall = _object_fields(subgroup.get("overall"))
    levels = subgroup.get("levels")
    params = _object_fields(specification.get("params"))
    wants_plot = params is not None and params.get("create.plot") is True
    plot_available = (
        not wants_plot or subgroup.get("figure_status") == "available"
    )
    complete = (
        overall is not None
        and overall.get("status") == "available"
        and _all_rows_have_status(levels, "available", require_nonempty=True)
        and plot_available
        and not has_warning
    )
    return _status(complete)


def _all_rows_have_status(
    value: object, status: str, *, require_nonempty: bool
) -> bool:
    if not isinstance(value, list) or (require_nonempty and not value):
        return False
    for raw_row in value:
        row = _object_fields(raw_row)
        if row is None or row.get("status") != status:
            return False
    return True


def _reitsma_status(
    value: object, specification: Mapping[str, object], has_warning: bool
) -> str | None:
    report = _object_fields(value)
    if report is None:
        return None
    sections = _sections_by_key(report.get("sections"))
    params = _object_fields(specification.get("params"))
    wants_sroc = params is not None and params.get("create.plot") is True
    summary = sections.get("Summary operating point")
    sroc = sections.get("SROC")
    complete = (
        summary is not None
        and summary.get("status") == "available"
        and (not wants_sroc or (sroc is not None and sroc.get("status") == "available"))
        and not has_warning
    )
    return _status(complete)


def _sections_by_key(value: object) -> dict[str, dict[str, object]]:
    if not isinstance(value, list):
        return {}
    sections: dict[str, dict[str, object]] = {}
    for raw_section in value:
        section = _object_fields(raw_section)
        if section is None:
            continue
        key = section.get("key")
        if isinstance(key, str):
            sections[key] = section
    return sections


def _sequential_status(
    cumulative_value: object, leave_one_out_value: object, has_warning: bool
) -> str | None:
    cumulative = _object_fields(cumulative_value)
    if cumulative is not None:
        return _status(cumulative.get("status") == "complete" and not has_warning)
    leave_one_out = _object_fields(leave_one_out_value)
    if leave_one_out is None:
        return None
    complete = _all_rows_have_status(
        leave_one_out.get("rows"), "available", require_nonempty=False
    )
    return _status(complete and not has_warning)


def _split_presentation(
    specification: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    scientific = copy.deepcopy(dict(specification))
    presentation: dict[str, object] = {}
    params_value = scientific.get("params")
    if isinstance(params_value, dict):
        params = _mutable_object_fields(params_value)
        if params is None:
            raise ValueError("effective specification params must be a mapping")
        presentation = {
            key: value
            for key, value in params.items()
            if _is_presentation_field(key)
        }
        scientific["params"] = {
            key: value
            for key, value in params.items()
            if not _is_plot_field(key)
        }
    return scientific, presentation


def _pooled_estimate(result: Mapping[str, object]) -> object:
    for family in (
        "binary_numerics",
        "binary_proportion_numerics",
        "continuous_numerics",
        "diagnostic_numerics",
    ):
        numerics = _object_fields(result.get(family))
        if numerics is None:
            continue
        pooled = _object_fields(numerics.get("pooled"))
        if pooled is None:
            continue
        if family == "continuous_numerics":
            return pooled.get("estimate")
        display = _object_fields(pooled.get("display"))
        if display is not None:
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
    image_fields = _object_fields(result.get("images", {}))
    if image_fields is None:
        raise ValueError("saved result images must be a mapping")
    states = validated_render_states(result.get("plot_render_state"), set(image_fields))
    _validated_render_state_reasons(
        result.get("plot_render_state_unavailable"), set(image_fields)
    )
    _set_saved_plot_editing(result, states)
    output_dir.mkdir(parents=True, exist_ok=True)
    materialized: dict[str, str] = {}
    for field in ("images", "display_images"):
        _materialize_image_paths(result, field, record.assets, output_dir, materialized)
    _sync_small_study_effects_report_images(result, restoring=True)
    _sync_reitsma_report_images(result, restoring=True)
    return analysis_results.parse_analysis_result(result)


def _set_saved_plot_editing(
    result: dict[str, object], states: Mapping[str, object]
) -> None:
    capabilities = result.get("plot_capabilities", {})
    capability_fields = _mutable_object_fields(capabilities)
    if capability_fields is None:
        raise ValueError("saved result plot capabilities must be a mapping")
    for figure_key, raw_capability in capability_fields.items():
        capability = _mutable_object_fields(raw_capability)
        if capability is None:
            raise ValueError("saved result plot capability must be a mapping")
        capability["editable"] = render_state_matches_capability(
            states.get(figure_key),
            capability.get("plot_kind"),
            capability.get("regenerator"),
        )


def _validated_render_state_reasons(
    value: object, image_keys: set[str]
) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping) or any(
        not isinstance(key, str)
        or key not in image_keys
        or not isinstance(reason, str)
        or not reason
        or len(reason) > 500
        for key, reason in value.items()
    ):
        raise ValueError("saved plot renderer availability reasons are malformed")
    return cast(dict[str, str], dict(value))


def _materialize_image_paths(
    result: dict[str, object],
    field: str,
    assets: Mapping[str, bytes],
    output_dir: Path,
    materialized: dict[str, str],
) -> None:
    paths = _mutable_text_paths(result.get(field, {}), field, owner="saved result")
    for key, asset in paths.items():
        if not asset:
            continue
        if asset not in assets:
            raise ValueError(f"saved result {field} references a missing figure")
        if asset not in materialized:
            path = output_dir / Path(asset).name
            path.write_bytes(assets[asset])
            materialized[asset] = str(path)
        paths[key] = materialized[asset]


def _sync_small_study_effects_report_images(
    result: dict[str, object], *, restoring: bool
) -> None:
    """Keep saved report figure status aligned with portable image assets."""
    small_study = _mutable_object_fields(result.get("small_study_effects"))
    if small_study is None:
        return
    report = _mutable_object_fields(small_study.get("report"))
    if report is None:
        return
    images = _object_fields(result.get("images", {}))
    display_images = _object_fields(result.get("display_images", {}))
    if images is None or display_images is None:
        return
    unavailable_reason = _unavailable_figure_reason(restoring)
    missing = _mark_missing_figure_rows(
        report.get("figures"), "key", images, display_images, restoring, unavailable_reason
    )
    missing = _mark_missing_figure_rows(
        report.get("funnel_requests"),
        "figure_key",
        images,
        display_images,
        restoring,
        unavailable_reason,
    ) or missing
    if missing:
        report["status"] = "partial"
        _mark_unavailable_report_section(report.get("sections"), unavailable_reason)


def _unavailable_figure_reason(restoring: bool) -> str:
    if restoring:
        return "The saved project did not contain this figure."
    return "The figure could not be captured in the saved project."


def _mark_missing_figure_rows(
    value: object,
    identity_field: str,
    images: Mapping[str, object],
    display_images: Mapping[str, object],
    restoring: bool,
    reason: str,
) -> bool:
    if not isinstance(value, list):
        return False
    missing = False
    for raw_row in value:
        row = _mutable_object_fields(raw_row)
        if row is None or row.get("status") != "available":
            continue
        if _has_saved_figure(row.get(identity_field), images, display_images, restoring):
            continue
        row["status"] = "not_available"
        row["reason"] = reason
        missing = True
    return missing


def _has_saved_figure(
    key: object,
    images: Mapping[str, object],
    display_images: Mapping[str, object],
    restoring: bool,
) -> bool:
    if not isinstance(key, str):
        return False
    path = display_images.get(key) or images.get(key)
    return isinstance(path, str) and bool(path) and (
        not restoring or Path(path).is_file()
    )


def _mark_unavailable_report_section(value: object, reason: str) -> None:
    if not isinstance(value, list):
        return
    for raw_section in value:
        section = _mutable_object_fields(raw_section)
        if section is not None and section.get("key") == "funnel_figures":
            section["status"] = "not_available"
            section["reason"] = reason


def _sync_reitsma_report_images(result: dict[str, object], *, restoring: bool) -> None:
    """Keep the joint report's SROC reference aligned with its stored image."""
    report = _mutable_object_fields(result.get("reitsma_report"))
    if report is None:
        return
    sections = report.get("sections")
    if not isinstance(sections, list):
        return
    images = _object_fields(result.get("images", {}))
    display_images = _object_fields(result.get("display_images", {}))
    if images is None or display_images is None:
        return
    reason = _unavailable_figure_reason(restoring)
    for raw_section in sections:
        section = _mutable_object_fields(raw_section)
        if section is not None:
            _sync_reitsma_image_section(section, images, display_images, reason)


def _sync_reitsma_image_section(
    section: dict[str, object],
    images: Mapping[str, object],
    display_images: Mapping[str, object],
    reason: str,
) -> None:
    if section.get("kind") != "image" or section.get("status") != "available":
        return
    key = section.get("key")
    path = display_images.get(key) or images.get(key) if isinstance(key, str) else None
    if isinstance(path, str) and path:
        section["value"] = path
        return
    section["status"] = "not_available"
    section["value"] = None
    section["reason"] = reason
