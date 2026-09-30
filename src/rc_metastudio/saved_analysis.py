# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Portable, data-only saved analysis records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import PurePosixPath
import re
from typing import TypeAlias, cast
import uuid
import xml.etree.ElementTree as ET


MAX_RECORDS = 100
MAX_FIGURES_PER_RECORD = 32
MAX_PROJECT_ASSETS = 32
MAX_FIGURE_SIZE = 4 * 1024 * 1024
MAX_TOTAL_ASSET_SIZE = 16 * 1024 * 1024
MAX_RECORD_JSON_SIZE = 4 * 1024 * 1024
MAX_TOTAL_RECORD_JSON_SIZE = 12 * 1024 * 1024
_ASSET_NAME = re.compile(r"^assets/([0-9a-f]{64})\.(svg|png|jpg)$")
_MEDIA_TYPES = {
    "image/svg+xml": "svg",
    "image/png": "png",
    "image/jpeg": "jpg",
}
_RECORD_FIELDS = {
    "schema_version",
    "id",
    "created_at",
    "status",
    "input_snapshot",
    "input_identity",
    "specification",
    "specification_identity",
    "results",
    "warnings",
    "backend_versions",
    "presentation",
    "figures",
}
_FIGURE_FIELDS = {"id", "title", "media_type", "asset", "sha256", "size"}

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


class SavedAnalysisError(ValueError):
    """A saved analysis record or one of its assets is invalid."""


@dataclass(frozen=True, slots=True)
class SavedFigureInput:
    """One figure captured from a completed analysis result."""

    id: str
    title: str
    media_type: str
    data: bytes


@dataclass(frozen=True, slots=True)
class SavedAnalysisRecord:
    """Validated JSON record plus the content-addressed bytes it references."""

    value: JsonObject
    assets: dict[str, bytes]


def record_revision(record: SavedAnalysisRecord) -> str:
    """Return an optimistic-concurrency token for one complete saved record."""
    validate_record(record.value, record.assets)
    digest = hashlib.sha256(_json_bytes(record.value, "saved analysis record"))
    for name, payload in sorted(record.assets.items()):
        digest.update(name.encode("utf-8"))
        digest.update(hashlib.sha256(payload).digest())
    return digest.hexdigest()


def _json_object_values(value: dict[object, object], label: str) -> Iterable[object]:
    if any(not isinstance(key, str) for key in value):
        raise SavedAnalysisError(f"{label} has a non-text property name")
    return value.values()


def _json_children(value: object, label: str) -> Iterable[object]:
    if isinstance(value, dict):
        return _json_object_values(value, label)
    if isinstance(value, (list, tuple)):
        return value
    if value is None or isinstance(value, (bool, str, int)):
        return ()
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SavedAnalysisError(f"{label} contains a non-finite number")
        return ()
    raise SavedAnalysisError(
        f"{label} contains unsupported {type(value).__name__} data"
    )


def _validate_json_tree(value: object, label: str) -> None:
    pending = [(value, 1)]
    while pending:
        current, depth = pending.pop()
        if depth > 32:
            raise SavedAnalysisError(f"{label} exceeds the JSON nesting limit")
        pending.extend((item, depth + 1) for item in _json_children(current, label))


def _json_bytes(value: object, label: str) -> bytes:
    _validate_json_tree(value, label)
    try:
        payload = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise SavedAnalysisError(f"{label} is not portable JSON") from exc
    if len(payload) > MAX_RECORD_JSON_SIZE:
        raise SavedAnalysisError(f"{label} exceeds the saved-record size limit")
    return payload


def _digest(value: object, label: str) -> str:
    return hashlib.sha256(_json_bytes(value, label)).hexdigest()


def _validate_svg_element(element: ET.Element) -> None:
    name = element.tag.rsplit("}", 1)[-1].lower()
    if name in {"script", "foreignobject"}:
        raise SavedAnalysisError("SVG figure contains active or external content")
    for key, value in element.attrib.items():
        local_name = key.rsplit("}", 1)[-1].lower()
        if local_name.startswith("on"):
            raise SavedAnalysisError("SVG figure event handlers are not allowed")
        if local_name == "href" and value and not value.startswith("#"):
            raise SavedAnalysisError("SVG figure external references are not allowed")


def _validate_svg_text(lowered: str) -> None:
    if "<!doctype" in lowered or "<!entity" in lowered:
        raise SavedAnalysisError("SVG figure declarations are not allowed")
    if "<?xml-stylesheet" in lowered or "@import" in lowered or re.search(
        r"url\((?!\s*['\"]?#)", lowered
    ):
        raise SavedAnalysisError("SVG figure external styles are not allowed")


def _svg_root(svg_text: str) -> ET.Element:
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as exc:
        raise SavedAnalysisError("SVG figure is malformed") from exc
    if root.tag.rsplit("}", 1)[-1].lower() != "svg":
        raise SavedAnalysisError("SVG figure must have an svg root element")
    return root


def _validate_svg_figure(data: bytes) -> None:
    try:
        svg_text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise SavedAnalysisError("SVG figure must be UTF-8") from exc
    _validate_svg_text(svg_text.lower())
    root = _svg_root(svg_text)
    for element in root.iter():
        _validate_svg_element(element)


def _validate_raster_figure(media_type: str, data: bytes) -> None:
    if media_type == "image/png":
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise SavedAnalysisError("PNG figure has an invalid signature")
        return
    if not data.startswith(b"\xff\xd8\xff"):
        raise SavedAnalysisError("JPEG figure has an invalid signature")


def _figure_bytes(media_type: str, data: bytes) -> None:
    if not isinstance(data, bytes) or not data:
        raise SavedAnalysisError("figure data must be non-empty bytes")
    if len(data) > MAX_FIGURE_SIZE:
        raise SavedAnalysisError("figure exceeds the 4 MiB per-asset limit")
    if media_type in {"image/png", "image/jpeg"}:
        _validate_raster_figure(media_type, data)
        return
    if media_type != "image/svg+xml":
        raise SavedAnalysisError(f"unsupported figure media type: {media_type!r}")
    _validate_svg_figure(data)


def _copy_json_object(value: object, label: str) -> JsonObject:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise SavedAnalysisError(f"{label} must be an object with text keys")
    try:
        copied = json.loads(_json_bytes(dict(value), label).decode("utf-8"))
    except (json.JSONDecodeError, RecursionError) as exc:
        raise SavedAnalysisError(f"{label} cannot be copied safely") from exc
    return cast(JsonObject, copied)


def _validated_warnings(warnings: Iterable[str]) -> list[str]:
    values: list[str] = []
    for warning in warnings:
        if len(values) == 1000 or not isinstance(warning, str):
            raise SavedAnalysisError(
                "saved analysis warnings must be at most 1000 strings"
            )
        values.append(warning)
    return values


def _validated_backend_versions(
    backend_versions: Mapping[str, str],
) -> dict[str, str]:
    versions = dict(backend_versions)
    if any(
        not isinstance(key, str) or not key or not isinstance(value, str)
        for key, value in versions.items()
    ):
        raise SavedAnalysisError("backend versions must map non-empty names to text")
    if not versions:
        raise SavedAnalysisError("at least one backend version is required")
    return versions


def _validate_figure_input_id(figure: SavedFigureInput, seen_ids: set[str]) -> None:
    if (
        not isinstance(figure.id, str)
        or not figure.id
        or len(figure.id) > 128
        or figure.id in seen_ids
    ):
        raise SavedAnalysisError("figure IDs and titles must be unique and non-empty")


def _validate_figure_input_title(figure: SavedFigureInput) -> None:
    if not isinstance(figure.title, str) or not figure.title or len(figure.title) > 512:
        raise SavedAnalysisError("figure IDs and titles must be unique and non-empty")


def _validated_figure_input(
    figure: object, seen_ids: set[str]
) -> SavedFigureInput:
    if not isinstance(figure, SavedFigureInput):
        raise SavedAnalysisError("figures must be SavedFigureInput values")
    _validate_figure_input_id(figure, seen_ids)
    _validate_figure_input_title(figure)
    seen_ids.add(figure.id)
    return figure


def _figure_record(
    figure: object, seen_ids: set[str]
) -> tuple[dict[str, object], str, bytes]:
    figure = _validated_figure_input(figure, seen_ids)
    extension = _MEDIA_TYPES.get(figure.media_type)
    if extension is None:
        raise SavedAnalysisError(
            f"unsupported figure media type: {figure.media_type!r}"
        )
    _figure_bytes(figure.media_type, figure.data)
    digest = hashlib.sha256(figure.data).hexdigest()
    asset = f"assets/{digest}.{extension}"
    return (
        {
            "id": figure.id,
            "title": figure.title,
            "media_type": figure.media_type,
            "asset": asset,
            "sha256": digest,
            "size": len(figure.data),
        },
        asset,
        bytes(figure.data),
    )


def _figure_values(
    figures: Iterable[SavedFigureInput],
) -> tuple[list[dict[str, object]], dict[str, bytes]]:
    values: list[dict[str, object]] = []
    assets: dict[str, bytes] = {}
    seen_ids: set[str] = set()
    for figure in figures:
        if len(values) >= MAX_FIGURES_PER_RECORD:
            raise SavedAnalysisError("saved analysis has too many figures")
        value, asset, payload = _figure_record(figure, seen_ids)
        values.append(value)
        assets[asset] = payload
    return values, assets


def create_record(
    input_snapshot: Mapping[str, object],
    specification: Mapping[str, object],
    results: Mapping[str, object],
    *,
    status: str,
    warnings: Iterable[str] = (),
    backend_versions: Mapping[str, str],
    figures: Iterable[SavedFigureInput] = (),
    presentation: Mapping[str, object] | None = None,
    record_id: str | None = None,
    created_at: datetime | None = None,
) -> SavedAnalysisRecord:
    """Build a record; input/specification digests exclude presentation data."""
    identifier = (
        str(uuid.UUID(record_id)) if record_id is not None else str(uuid.uuid4())
    )
    timestamp = created_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise SavedAnalysisError("saved analysis time must include a timezone")
    timestamp_text = (
        timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    input_value = _copy_json_object(input_snapshot, "input snapshot")
    specification_value = _copy_json_object(specification, "effective specification")
    results_value = _copy_json_object(results, "analysis results")
    presentation_value = _copy_json_object(presentation or {}, "presentation settings")
    if not isinstance(status, str) or status not in {"complete", "partial"}:
        raise SavedAnalysisError("saved analysis status must be complete or partial")
    warning_values = _validated_warnings(warnings)
    versions = _validated_backend_versions(backend_versions)
    figure_values, assets = _figure_values(figures)
    value: JsonObject = {
        "schema_version": 1,
        "id": identifier,
        "created_at": timestamp_text,
        "status": status,
        "input_snapshot": input_value,
        "input_identity": _digest(input_value, "input snapshot"),
        "specification": specification_value,
        "specification_identity": _digest(
            specification_value, "effective specification"
        ),
        "results": results_value,
        "warnings": warning_values,
        "backend_versions": versions,
        "presentation": presentation_value,
        "figures": figure_values,
    }
    validate_record(value, assets)
    return SavedAnalysisRecord(value, assets)


def _validate_record_header(record: Mapping[str, object]) -> None:
    if type(record["schema_version"]) is not int or record["schema_version"] != 1:
        raise SavedAnalysisError("unsupported saved analysis record version")
    try:
        normalized_id = str(uuid.UUID(str(record["id"])))
    except (ValueError, TypeError, AttributeError) as exc:
        raise SavedAnalysisError("saved analysis ID must be a UUID") from exc
    if record["id"] != normalized_id:
        raise SavedAnalysisError("saved analysis ID must use canonical UUID text")


def _validate_record_status(record: Mapping[str, object]) -> None:
    if not isinstance(record["status"], str) or record["status"] not in {
        "complete",
        "partial",
    }:
        raise SavedAnalysisError("saved analysis status is invalid")


def _validate_record_time(record: Mapping[str, object]) -> None:
    timestamp = record["created_at"]
    if not isinstance(timestamp, str):
        raise SavedAnalysisError("saved analysis time must be text")
    try:
        parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SavedAnalysisError("saved analysis time must be ISO 8601") from exc
    if parsed_timestamp.tzinfo is None:
        raise SavedAnalysisError("saved analysis time must include a timezone")


def _validate_record_json_fields(record: Mapping[str, object]) -> None:
    for field in ("input_snapshot", "specification", "results", "presentation"):
        if not isinstance(record[field], Mapping):
            raise SavedAnalysisError(f"saved analysis {field} must be an object")
        _json_bytes(record[field], f"saved analysis {field}")


def _validate_record_identities(record: Mapping[str, object]) -> None:
    for field in ("input_snapshot", "specification"):
        identity_field = (
            "input_identity" if field == "input_snapshot" else "specification_identity"
        )
        expected = _digest(record[field], f"saved analysis {field}")
        if record[identity_field] != expected:
            raise SavedAnalysisError(f"saved analysis {identity_field} does not match")


def _validate_record_warnings(record: Mapping[str, object]) -> None:
    warnings = record["warnings"]
    if not isinstance(warnings, list) or len(warnings) > 1000 or any(
        not isinstance(item, str) for item in warnings
    ):
        raise SavedAnalysisError("saved analysis warnings are invalid")


def _validate_record_backend_versions(record: Mapping[str, object]) -> None:
    versions = record["backend_versions"]
    if not isinstance(versions, Mapping) or not versions or any(
        not isinstance(key, str) or not key or not isinstance(version, str)
        for key, version in versions.items()
    ):
        raise SavedAnalysisError("saved analysis backend versions are invalid")


def _validate_record_figure_id(
    figure: Mapping[str, object], seen_ids: set[str]
) -> str:
    identifier = figure["id"]
    if not isinstance(identifier, str) or not identifier or identifier in seen_ids:
        raise SavedAnalysisError("saved analysis figure IDs must be unique text")
    return identifier


def _validate_record_figure_display(figure: Mapping[str, object]) -> None:
    title = figure["title"]
    if not isinstance(title, str) or not title:
        raise SavedAnalysisError("saved analysis figure title must be non-empty text")
    media_type = figure["media_type"]
    if not isinstance(media_type, str) or media_type not in _MEDIA_TYPES:
        raise SavedAnalysisError("saved analysis figure media type is unsupported")


def _validated_figure_fields(
    value: object, seen_ids: set[str]
) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != _FIGURE_FIELDS:
        raise SavedAnalysisError("saved analysis figure has unknown or missing fields")
    figure = cast(Mapping[str, object], value)
    identifier = _validate_record_figure_id(figure, seen_ids)
    _validate_record_figure_display(figure)
    seen_ids.add(identifier)
    return figure


def _validated_figure_asset_reference(
    figure: Mapping[str, object],
) -> tuple[str, str, str]:
    asset = figure["asset"]
    if not isinstance(asset, str) or PurePosixPath(asset).is_absolute():
        raise SavedAnalysisError("saved analysis figure asset path is unsafe")
    digest = figure["sha256"]
    media_type = cast(str, figure["media_type"])
    match = _ASSET_NAME.fullmatch(asset)
    if (
        match is None
        or match.group(1) != digest
        or _MEDIA_TYPES[media_type] != match.group(2)
    ):
        raise SavedAnalysisError("saved analysis figure asset reference is invalid")
    return asset, media_type, cast(str, digest)


def _validated_figure_size(figure: Mapping[str, object]) -> int:
    size = figure["size"]
    if type(size) is not int or size <= 0 or size > MAX_FIGURE_SIZE:
        raise SavedAnalysisError("saved analysis figure size is invalid")
    return size


def _validate_figure_asset(
    assets: Mapping[str, bytes],
    asset: str,
    media_type: str,
    digest: str,
    size: int,
) -> None:
    payload = assets.get(asset)
    if (
        payload is None
        or len(payload) != size
        or hashlib.sha256(payload).hexdigest() != digest
    ):
        raise SavedAnalysisError("saved analysis figure asset integrity check failed")
    _figure_bytes(media_type, payload)


def _validate_record_figures(
    record: Mapping[str, object], assets: Mapping[str, bytes]
) -> None:
    figures = record["figures"]
    if not isinstance(figures, list) or len(figures) > MAX_FIGURES_PER_RECORD:
        raise SavedAnalysisError("saved analysis figure list is invalid")
    seen_ids: set[str] = set()
    for figure in figures:
        fields = _validated_figure_fields(figure, seen_ids)
        asset, media_type, digest = _validated_figure_asset_reference(fields)
        size = _validated_figure_size(fields)
        _validate_figure_asset(assets, asset, media_type, digest, size)


def _validate_asset_limits(assets: Mapping[str, bytes]) -> None:
    if len(assets) > MAX_PROJECT_ASSETS:
        raise SavedAnalysisError("project contains too many saved-analysis assets")
    if sum(len(payload) for payload in assets.values()) > MAX_TOTAL_ASSET_SIZE:
        raise SavedAnalysisError("saved-analysis assets exceed the 16 MiB limit")


def validate_record(value: object, assets: Mapping[str, bytes]) -> None:
    """Validate record identities, known fields, embedded bytes, and references."""
    if not isinstance(value, Mapping) or set(value) != _RECORD_FIELDS:
        raise SavedAnalysisError("saved analysis record has unknown or missing fields")
    record = cast(Mapping[str, object], value)
    _validate_record_header(record)
    _validate_record_status(record)
    _validate_record_time(record)
    _validate_record_json_fields(record)
    _validate_record_identities(record)
    _validate_record_warnings(record)
    _validate_record_backend_versions(record)
    _validate_record_figures(record, assets)
    _validate_asset_limits(assets)


def _validate_project_asset_map(assets: Mapping[str, bytes]) -> None:
    if not isinstance(assets, Mapping) or any(
        not isinstance(name, str) or not isinstance(payload, bytes)
        for name, payload in assets.items()
    ):
        raise SavedAnalysisError("project assets must map safe names to bytes")


def _project_records(project: Mapping[str, object]) -> list[object]:
    records = project.get("saved_analyses", [])
    if not isinstance(records, list) or len(records) > MAX_RECORDS:
        raise SavedAnalysisError("project saved analyses must be a bounded array")
    return records


def _validate_project_record(
    value: object, assets: Mapping[str, bytes], record_ids: set[str]
) -> tuple[set[str], int]:
    if not isinstance(value, Mapping):
        raise SavedAnalysisError("project saved analysis must be an object")
    validate_record(value, assets)
    record = cast(Mapping[str, object], value)
    record_id = str(uuid.UUID(str(record["id"])))
    if record_id in record_ids:
        raise SavedAnalysisError("project saved analysis IDs must be unique")
    record_ids.add(record_id)
    figures = cast(list[Mapping[str, object]], record["figures"])
    references = {cast(str, figure["asset"]) for figure in figures}
    size = len(_json_bytes(record, "saved analysis record"))
    return references, size


def validate_project_records(
    project: Mapping[str, object], assets: Mapping[str, bytes]
) -> None:
    """Validate all saved records and ensure every archive asset is referenced."""
    _validate_project_asset_map(assets)
    records = _project_records(project)
    if not records:
        if assets:
            raise SavedAnalysisError("project contains assets without saved analyses")
        return
    record_ids: set[str] = set()
    references: set[str] = set()
    total_record_size = 0
    for value in records:
        record_references, record_size = _validate_project_record(
            value, assets, record_ids
        )
        references.update(record_references)
        total_record_size += record_size
        if total_record_size > MAX_TOTAL_RECORD_JSON_SIZE:
            raise SavedAnalysisError("saved analysis records exceed the 12 MiB limit")
    if set(assets) != references:
        raise SavedAnalysisError("project contains unreferenced saved-analysis assets")
