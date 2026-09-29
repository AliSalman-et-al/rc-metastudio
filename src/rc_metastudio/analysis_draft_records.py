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
    _validate_json_tree(value)
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


def _validate_json_tree(value: object) -> None:
    pending = [(value, 1)]
    while pending:
        current, depth = pending.pop()
        if depth > 32:
            raise AnalysisDraftError("draft exceeds the JSON nesting limit")
        pending.extend((item, depth + 1) for item in _json_children(current))


def _json_children(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise AnalysisDraftError("draft has a non-text property name")
        return tuple(value.values())
    if isinstance(value, (list, tuple)):
        return tuple(value)
    if _is_json_scalar(value):
        return ()
    raise AnalysisDraftError(
        f"draft contains unsupported {type(value).__name__} data"
    )


def _is_json_scalar(value: object) -> bool:
    if value is None or isinstance(value, (bool, str, int)):
        return True
    if isinstance(value, float):
        if not math.isfinite(value):
            raise AnalysisDraftError("draft contains a non-finite number")
        return True
    return False


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
        _validate_optional_text(value[field], f"draft selection {field}")
    _validate_groups(value["groups"])
    _validate_effect(value["effect"])
    return value


def _validate_optional_text(item: JsonValue, label: str) -> None:
    if item is not None and (not isinstance(item, str) or not item):
        raise AnalysisDraftError(f"{label} must be text or null")


def _validate_groups(groups: JsonValue) -> None:
    if (
        not isinstance(groups, list)
        or len(groups) > 2
        or any(not isinstance(group, str) or not group for group in groups)
        or len(groups) != len(set(groups))
    ):
        raise AnalysisDraftError(
            "draft selection groups must be up to two unique names"
        )


def _validate_effect(effect: JsonValue) -> None:
    if effect is not None and (not isinstance(effect, str) or effect not in _METRICS):
        raise AnalysisDraftError("draft selection effect is not a supported measure")


def _validate_settings(settings: object) -> JsonObject:
    value = _json_object(settings, "draft settings")
    if not {"analysis_type", "method", "parameters"} <= set(value) or set(value) - {
        "analysis_type", "method", "parameters", "ordering"
    }:
        raise AnalysisDraftError(
            "draft settings require analysis_type, method, and parameters"
        )
    for field in ("analysis_type", "method"):
        _validate_optional_text(value.get(field), f"draft settings {field}")
    parameters = value.get("parameters")
    if not isinstance(parameters, dict):
        raise AnalysisDraftError("draft settings parameters must be an object")
    if "ordering" in value:
        _validate_ordering(value["analysis_type"], value["ordering"])
    return value


def _validate_ordering(analysis_type: JsonValue, ordering: JsonValue) -> None:
    if analysis_type != "cumulative":
        raise AnalysisDraftError("only cumulative drafts can include study ordering")
    from rc_metastudio.cumulative_analysis import CumulativeOrderSpec

    try:
        CumulativeOrderSpec.from_mapping(ordering)
    except ValueError as error:
        raise AnalysisDraftError(str(error)) from error


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
        seen_ids.add(_validate_project_record(record, seen_ids))


def _validate_project_record(record: object, seen_ids: set[str]) -> str:
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
    identifier = _validate_record_id(record["id"], seen_ids)
    _validate_timestamp(record["updated_at"])
    _validate_selection(record["selection"])
    _validate_settings(record["settings"])
    _json_bytes(record)
    return identifier


def _validate_record_id(value: object, seen_ids: set[str]) -> str:
    if not isinstance(value, str):
        raise AnalysisDraftError("analysis draft id must be a UUID")
    try:
        canonical_id = str(uuid.UUID(value))
    except ValueError as exc:
        raise AnalysisDraftError("analysis draft id must be a UUID") from exc
    if value != canonical_id or value in seen_ids:
        raise AnalysisDraftError("analysis draft IDs must be unique canonical UUIDs")
    return value
