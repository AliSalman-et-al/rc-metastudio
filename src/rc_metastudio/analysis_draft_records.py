# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Portable, validated records for unfinished analysis editor state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from typing import TypeAlias, cast
import uuid


MAX_DRAFTS = 100
MAX_DRAFT_JSON_SIZE = 1024 * 1024
_METRICS = {
    "OR", "RD", "RR", "AS", "YUQ", "YUY", "PR", "PLN", "PLO", "PAS",
    "PFT", "MD", "SMD", "TX Mean", "Sens", "Spec", "PLR", "NLR", "DOR",
}

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


class AnalysisDraftError(ValueError):
    """An unfinished analysis draft is invalid or too large to persist."""


@dataclass(frozen=True, slots=True)
class AnalysisDraftRecord:
    """One validated data-only draft."""

    value: JsonObject


def _json_bytes(value: object) -> bytes:
    pending = [(value, 1)]
    while pending:
        current, depth = pending.pop()
        if depth > 32:
            raise AnalysisDraftError("draft exceeds the JSON nesting limit")
        if isinstance(current, dict):
            if any(not isinstance(key, str) for key in current):
                raise AnalysisDraftError("draft has a non-text property name")
            pending.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, (list, tuple)):
            pending.extend((item, depth + 1) for item in current)
        elif current is None or isinstance(current, (bool, str, int)):
            continue
        elif isinstance(current, float):
            if not math.isfinite(current):
                raise AnalysisDraftError("draft contains a non-finite number")
        else:
            raise AnalysisDraftError(
                f"draft contains unsupported {type(current).__name__} data"
            )
    try:
        payload = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise AnalysisDraftError("draft is not portable JSON") from exc
    if len(payload) > MAX_DRAFT_JSON_SIZE:
        raise AnalysisDraftError("draft exceeds the 1 MiB size limit")
    return payload


def _json_object(value: object, label: str) -> JsonObject:
    if not isinstance(value, Mapping) or any(not isinstance(k, str) for k in value):
        raise AnalysisDraftError(f"{label} must be an object with text keys")
    try:
        copied = json.loads(_json_bytes(dict(value)).decode("utf-8"))
    except (json.JSONDecodeError, RecursionError) as exc:
        raise AnalysisDraftError(f"{label} cannot be copied safely") from exc
    return cast(JsonObject, copied)


def _validate_selection(selection: object) -> JsonObject:
    value = _json_object(selection, "draft selection")
    if set(value) != {"outcome", "follow_up", "groups", "effect"}:
        raise AnalysisDraftError("draft selection has unknown or missing fields")
    for field in ("outcome", "follow_up"):
        item = value[field]
        if item is not None and (not isinstance(item, str) or not item):
            raise AnalysisDraftError(f"draft selection {field} must be text or null")
    groups = value["groups"]
    if (
        not isinstance(groups, list)
        or len(groups) > 2
        or any(not isinstance(group, str) or not group for group in groups)
        or len(groups) != len(set(groups))
    ):
        raise AnalysisDraftError(
            "draft selection groups must be up to two unique names"
        )
    effect = value["effect"]
    if effect is not None and (not isinstance(effect, str) or effect not in _METRICS):
        raise AnalysisDraftError("draft selection effect is not a supported measure")
    return value


def _validate_settings(settings: object) -> JsonObject:
    value = _json_object(settings, "draft settings")
    if set(value) != {"analysis_type", "method", "parameters"}:
        raise AnalysisDraftError(
            "draft settings require analysis_type, method, and parameters"
        )
    for field in ("analysis_type", "method"):
        item = value.get(field)
        if item is not None and (not isinstance(item, str) or not item):
            raise AnalysisDraftError(f"draft settings {field} must be text or null")
    parameters = value.get("parameters")
    if not isinstance(parameters, dict):
        raise AnalysisDraftError("draft settings parameters must be an object")
    return value


def _validate_timestamp(value: object) -> str:
    if not isinstance(value, str):
        raise AnalysisDraftError("draft updated_at must be an ISO timestamp")
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AnalysisDraftError("draft updated_at must be an ISO timestamp") from exc
    if timestamp.tzinfo is None:
        raise AnalysisDraftError("draft updated_at must include a timezone")
    return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def create_record(
    selection: Mapping[str, object],
    settings: Mapping[str, object],
    *,
    record_id: str | None = None,
    updated_at: datetime | None = None,
) -> AnalysisDraftRecord:
    """Build a validated draft from the current editor context and settings."""
    try:
        identifier = (
            str(uuid.UUID(record_id))
            if record_id is not None
            else str(uuid.uuid4())
        )
    except (ValueError, AttributeError) as exc:
        raise AnalysisDraftError("draft id must be a UUID") from exc
    timestamp = updated_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise AnalysisDraftError("draft updated_at must include a timezone")
    value: JsonObject = {
        "schema_version": 1,
        "id": identifier,
        "updated_at": (
            timestamp.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        ),
        "selection": _validate_selection(selection),
        "settings": _validate_settings(settings),
    }
    _json_bytes(value)
    return AnalysisDraftRecord(value)


def validate_project_records(project: Mapping[str, object]) -> None:
    """Validate every draft record in a project after JSON Schema checks."""
    raw_records = project.get("analysis_drafts", [])
    if not isinstance(raw_records, list):
        raise AnalysisDraftError("analysis_drafts must be an array")
    if len(raw_records) > MAX_DRAFTS:
        raise AnalysisDraftError(f"a project can contain at most {MAX_DRAFTS} drafts")
    seen_ids: set[str] = set()
    for record in raw_records:
        if not isinstance(record, dict):
            raise AnalysisDraftError("analysis draft must be an object")
        record = cast(dict[str, object], record)
        if set(record) != {
            "schema_version",
            "id",
            "updated_at",
            "selection",
            "settings",
        }:
            raise AnalysisDraftError("analysis draft has unknown or missing fields")
        if record["schema_version"] != 1:
            raise AnalysisDraftError("analysis draft has an unsupported schema version")
        identifier = record["id"]
        if not isinstance(identifier, str):
            raise AnalysisDraftError("analysis draft id must be a UUID")
        try:
            canonical_id = str(uuid.UUID(identifier))
        except ValueError as exc:
            raise AnalysisDraftError("analysis draft id must be a UUID") from exc
        if identifier != canonical_id or identifier in seen_ids:
            raise AnalysisDraftError(
                "analysis draft IDs must be unique canonical UUIDs"
            )
        seen_ids.add(identifier)
        _validate_timestamp(record["updated_at"])
        _validate_selection(record["selection"])
        _validate_settings(record["settings"])
        _json_bytes(record)
