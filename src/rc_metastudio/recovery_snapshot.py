# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Atomic local recovery snapshots that reuse the portable project format."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import BinaryIO, cast
import zipfile

from rc_metastudio import project_format
from rc_metastudio.project_domain import JsonObject
from rc_metastudio.project_format import ProjectDocument


RECOVERY_SUFFIX = ".rcms-recovery"
_FORMAT = "rc-metastudio-recovery"
_FORMAT_VERSION = 1
_MEMBERS = ("manifest.json", "metadata.json", "project.rcms")
_MAX_METADATA_SIZE = 16 * 1024
_MAX_PROJECT_SIZE = project_format.ProjectArchiveLimits().max_archive_size
_MAX_RECOVERY_SIZE = _MAX_PROJECT_SIZE + 64 * 1024


class RecoverySnapshotError(ValueError):
    """A recovery snapshot cannot be safely created or read."""


class RecoverySnapshotDurabilityError(RecoverySnapshotError):
    """A recovery snapshot was installed but directory durability is uncertain."""


@dataclass(frozen=True, slots=True)
class RecoverySnapshotPreview:
    """Small, validated summary suitable for a startup recovery prompt."""

    created_at: datetime
    project_title: str
    source_project_path: str | None
    workspace_was_dirty: bool
    study_count: int
    outcome_count: int
    saved_analysis_count: int
    analysis_draft_count: int


@dataclass(frozen=True, slots=True)
class RecoverySnapshot:
    """A validated project document and metadata from one recovery snapshot."""

    preview: RecoverySnapshotPreview
    document: ProjectDocument


def default_recovery_snapshot_path(application_data_directory: str | os.PathLike[str]) -> Path:
    """Return the single local recovery slot under the app's private data folder."""
    return Path(application_data_directory) / f"recovery{RECOVERY_SUFFIX}"


def write_recovery_snapshot(
    path: str | os.PathLike[str],
    document: ProjectDocument,
    *,
    source_project_path: str | os.PathLike[str] | None = None,
    workspace_was_dirty: bool = False,
    created_at: datetime | None = None,
) -> RecoverySnapshotPreview:
    """Atomically replace a separate recovery file without touching the project."""
    destination = Path(path)
    _require_recovery_path(destination)
    source_text = os.fspath(source_project_path) if source_project_path is not None else None
    if source_text is not None and not isinstance(source_text, str):
        raise RecoverySnapshotError("source project path must be text")
    if source_text is not None and _same_path(destination, Path(source_text)):
        raise RecoverySnapshotError("recovery snapshot path must differ from the saved project")
    if not isinstance(workspace_was_dirty, bool):
        raise RecoverySnapshotError("workspace dirty state must be a boolean")
    timestamp = created_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise RecoverySnapshotError("recovery snapshot time must include a timezone")
    timestamp = timestamp.astimezone(timezone.utc)
    metadata: JsonObject = {
        "created_at": timestamp.isoformat().replace("+00:00", "Z"),
        "source_project_path": source_text,
        "workspace_was_dirty": workspace_was_dirty,
    }

    temporary_path: Path | None = None
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="rcms-recovery-") as temporary_directory:
            project_path = Path(temporary_directory) / "project.rcms"
            project_format.save_project(
                project_path,
                document.project,
                document.state,
                assets=document.assets,
            )
            project_size, project_digest = _file_integrity(project_path)
            if project_size > _MAX_PROJECT_SIZE:
                raise RecoverySnapshotError("project is too large for local recovery")
            manifest = {
                "format": _FORMAT,
                "format_version": _FORMAT_VERSION,
                "members": {
                    "metadata.json": _integrity(_json_bytes(metadata)),
                    "project.rcms": {"sha256": project_digest, "size": project_size},
                },
            }
            with tempfile.NamedTemporaryFile(
                mode="w+b",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                with zipfile.ZipFile(
                    cast(BinaryIO, temporary),
                    "w",
                    compression=zipfile.ZIP_STORED,
                    allowZip64=False,
                ) as archive:
                    archive.writestr("manifest.json", _json_bytes(manifest))
                    archive.writestr("metadata.json", _json_bytes(metadata))
                    archive.write(project_path, "project.rcms")
                temporary.flush()
                os.fsync(temporary.fileno())
            if temporary_path.stat().st_size > _MAX_RECOVERY_SIZE:
                raise RecoverySnapshotError("recovery snapshot exceeds its size limit")
            read_recovery_snapshot(temporary_path, _allow_temporary_path=True)
        os.replace(temporary_path, destination)
        temporary_path = None
        _fsync_parent_directory(destination)
    except RecoverySnapshotError:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise RecoverySnapshotError(f"could not write recovery snapshot: {exc}") from exc
    return _preview(document, metadata)


def read_recovery_snapshot(
    path: str | os.PathLike[str], *, _allow_temporary_path: bool = False
) -> RecoverySnapshot:
    """Read and validate the envelope and embedded project before returning it."""
    source = Path(path)
    if not _allow_temporary_path:
        _require_recovery_path(source)
    try:
        if source.stat().st_size > _MAX_RECOVERY_SIZE:
            raise RecoverySnapshotError("recovery snapshot exceeds its size limit")
        with zipfile.ZipFile(source, "r") as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(_MEMBERS) or set(names) != set(_MEMBERS):
                raise RecoverySnapshotError("recovery snapshot is incomplete or has unexpected files")
            info_by_name = {info.filename: info for info in infos}
            for info in infos:
                if not _regular_member(info) or info.flag_bits & 0x1:
                    raise RecoverySnapshotError("recovery snapshot contains an unsafe archive entry")
                if info.compress_type != zipfile.ZIP_STORED:
                    raise RecoverySnapshotError("recovery snapshot uses unsupported compression")
            manifest_payload = _read_member(archive, info_by_name["manifest.json"], _MAX_METADATA_SIZE)
            metadata_payload = _read_member(archive, info_by_name["metadata.json"], _MAX_METADATA_SIZE)
            manifest = _decode_json(manifest_payload, "manifest.json")
            metadata = _decode_json(metadata_payload, "metadata.json")
            _validate_manifest(
                manifest, metadata_payload, info_by_name["project.rcms"].file_size
            )
            _validate_metadata(metadata)
            project_info = info_by_name["project.rcms"]
            if project_info.file_size > _MAX_PROJECT_SIZE:
                raise RecoverySnapshotError("recovery project is too large")
            with tempfile.TemporaryDirectory(prefix="rcms-recovery-project-") as temporary_directory:
                project_path = Path(temporary_directory) / "project.rcms"
                digest = hashlib.sha256()
                total = 0
                with project_path.open("wb") as project_file:
                    with archive.open(project_info, "r") as member:
                        while chunk := member.read(1024 * 1024):
                            total += len(chunk)
                            if total > _MAX_PROJECT_SIZE:
                                raise RecoverySnapshotError("recovery project is too large")
                            digest.update(chunk)
                            project_file.write(chunk)
                    project_file.flush()
                    os.fsync(project_file.fileno())
                members = cast(dict[str, JsonObject], manifest["members"])
                integrity = members["project.rcms"]
                if total != project_info.file_size or digest.hexdigest() != integrity["sha256"]:
                    raise RecoverySnapshotError("recovery project integrity check failed")
                document = project_format.load_project(project_path)
        return RecoverySnapshot(_preview(document, metadata), document)
    except RecoverySnapshotError:
        raise
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, EOFError) as exc:
        raise RecoverySnapshotError(f"recovery snapshot is corrupt or incomplete: {exc}") from exc


def invalidate_recovery_snapshot(path: str | os.PathLike[str]) -> bool:
    """Remove the recovery slot after an intentional discard; missing is harmless."""
    destination = Path(path)
    _require_recovery_path(destination)
    try:
        destination.unlink()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise RecoverySnapshotError(f"could not discard recovery snapshot: {exc}") from exc
    _fsync_parent_directory(destination)
    return True


def _preview(
    document: ProjectDocument, metadata: JsonObject
) -> RecoverySnapshotPreview:
    project = document.project
    dataset = project.get("dataset")
    dataset_value = dataset if isinstance(dataset, dict) else {}
    title = dataset_value.get("title")
    outcomes = dataset_value.get("outcomes")
    studies = dataset_value.get("studies")
    saved_analyses = project.get("saved_analyses")
    analysis_drafts = project.get("analysis_drafts")
    return RecoverySnapshotPreview(
        created_at=datetime.fromisoformat(
            cast(str, metadata["created_at"]).replace("Z", "+00:00")
        ),
        project_title=title if isinstance(title, str) else "Untitled project",
        source_project_path=cast(str | None, metadata["source_project_path"]),
        workspace_was_dirty=cast(bool, metadata["workspace_was_dirty"]),
        study_count=len(studies) if isinstance(studies, list) else 0,
        outcome_count=len(outcomes) if isinstance(outcomes, list) else 0,
        saved_analysis_count=len(saved_analyses) if isinstance(saved_analyses, list) else 0,
        analysis_draft_count=len(analysis_drafts) if isinstance(analysis_drafts, list) else 0,
    )


def _validate_metadata(metadata: JsonObject) -> None:
    if set(metadata) != {"created_at", "source_project_path", "workspace_was_dirty"}:
        raise RecoverySnapshotError("recovery metadata has unknown or missing fields")
    created_at = metadata["created_at"]
    if not isinstance(created_at, str):
        raise RecoverySnapshotError("recovery metadata timestamp is invalid")
    try:
        parsed = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RecoverySnapshotError("recovery metadata timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise RecoverySnapshotError("recovery metadata timestamp has no timezone")
    source_path = metadata["source_project_path"]
    if source_path is not None and (not isinstance(source_path, str) or len(source_path) > 4096):
        raise RecoverySnapshotError("recovery metadata source path is invalid")
    if not isinstance(metadata["workspace_was_dirty"], bool):
        raise RecoverySnapshotError("recovery metadata dirty state is invalid")


def _validate_manifest(
    manifest: JsonObject, metadata_payload: bytes, project_size: int
) -> None:
    if set(manifest) != {"format", "format_version", "members"}:
        raise RecoverySnapshotError("recovery manifest has unknown or missing fields")
    if (
        manifest["format"] != _FORMAT
        or type(manifest["format_version"]) is not int
        or manifest["format_version"] != _FORMAT_VERSION
    ):
        raise RecoverySnapshotError("unsupported recovery snapshot format")
    members = manifest["members"]
    if not isinstance(members, dict) or set(members) != {
        "metadata.json",
        "project.rcms",
    }:
        raise RecoverySnapshotError("recovery manifest member list is invalid")
    for name, size in (
        ("metadata.json", len(metadata_payload)),
        ("project.rcms", project_size),
    ):
        value = members[name]
        if not isinstance(value, dict) or set(value) != {"sha256", "size"}:
            raise RecoverySnapshotError(f"recovery manifest integrity for {name} is invalid")
        digest = value["sha256"]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)
        ):
            raise RecoverySnapshotError(f"recovery manifest digest for {name} is invalid")
        if type(value["size"]) is not int or value["size"] != size:
            raise RecoverySnapshotError(f"recovery manifest size for {name} is invalid")
    expected_metadata = cast(JsonObject, members["metadata.json"])["sha256"]
    if hashlib.sha256(metadata_payload).hexdigest() != expected_metadata:
        raise RecoverySnapshotError("recovery metadata integrity check failed")


def _read_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo, limit: int) -> bytes:
    if info.file_size > limit:
        raise RecoverySnapshotError(f"recovery member {info.filename} exceeds its size limit")
    with archive.open(info, "r") as member:
        data = member.read(limit + 1)
    if len(data) != info.file_size or len(data) > limit:
        raise RecoverySnapshotError(f"recovery member {info.filename} is truncated or too large")
    return data


def _decode_json(payload: bytes, label: str) -> JsonObject:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise RecoverySnapshotError(f"{label} has a duplicate property")
            result[key] = value
        return result

    try:
        value = json.loads(
            payload.decode("utf-8", errors="strict"),
            object_pairs_hook=reject_duplicates,
        )
    except RecoverySnapshotError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise RecoverySnapshotError(f"recovery {label} is malformed") from exc
    if not isinstance(value, dict):
        raise RecoverySnapshotError(f"recovery {label} must be an object")
    return cast(JsonObject, value)


def _json_bytes(value: object) -> bytes:
    try:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return (encoded + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RecoverySnapshotError("recovery metadata is not portable JSON") from exc


def _integrity(payload: bytes) -> dict[str, object]:
    return {"sha256": hashlib.sha256(payload).hexdigest(), "size": len(payload)}


def _file_integrity(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            size += len(chunk)
            if size > _MAX_PROJECT_SIZE:
                raise RecoverySnapshotError("project is too large for local recovery")
            digest.update(chunk)
    return size, digest.hexdigest()


def _regular_member(info: zipfile.ZipInfo) -> bool:
    if info.is_dir():
        return False
    if info.create_system != 3:
        return True
    mode = info.external_attr >> 16
    return stat.S_IFMT(mode) in {0, stat.S_IFREG}


def _require_recovery_path(path: Path) -> None:
    if path.suffix != RECOVERY_SUFFIX:
        raise RecoverySnapshotError(f"recovery files must use the {RECOVERY_SUFFIX} suffix")


def _same_path(left: Path, right: Path) -> bool:
    if left.resolve() == right.resolve():
        return True
    try:
        return left.exists() and right.exists() and os.path.samefile(left, right)
    except OSError:
        return False


def _fsync_parent_directory(destination: Path) -> None:
    if os.name != "posix" or not hasattr(os, "O_DIRECTORY"):
        return
    descriptor: int | None = None
    durability_error: OSError | None = None
    try:
        descriptor = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
        os.fsync(descriptor)
    except OSError as exc:
        durability_error = exc
    if descriptor is not None:
        try:
            os.close(descriptor)
        except OSError as exc:
            durability_error = durability_error or exc
    if durability_error is not None:
        raise RecoverySnapshotDurabilityError(
            "recovery directory durability could not be confirmed"
        ) from durability_error
