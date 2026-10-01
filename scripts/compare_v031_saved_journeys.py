#!/usr/bin/env python3
"""Compare five saved application journeys with the pinned v0.3.1 package API."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import sys
import zipfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.analysis_regression.golden.support.release_source_v031_package import (
    canonical_sha256,
    validate_package_manifest,
)  # noqa: E402


CASE_SPEC = ROOT / "tests/analysis_regression/baseline/release-source-v031-package-api/cases.json"
JOURNEY_IDS = (
    "journey-binary-standard",
    "journey-continuous-standard",
    "journey-diagnostic-standard",
    "journey-binary-one-arm",
    "journey-continuous-entered-effect",
)
_REQUIRED_PROJECT_MEMBERS = {"manifest.json", "project.json", "state.json"}
_ASSET_NAME = re.compile(r"^assets/([0-9a-f]{64})\.(?:svg|png|jpg)$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MAX_ARCHIVE = 32 * 1024 * 1024
_MAX_MEMBER = 8 * 1024 * 1024
_MAX_TOTAL = 16 * 1024 * 1024
_MAX_MEMBERS = 64
_ABS_TOLERANCE = 1e-8
_REL_TOLERANCE = 1e-8
_TYPED_POOLED_FIELDS = {
    "binary": {"pval": "p_value"},
    "continuous": {"se": "standard_error", "pval": "p_value", "tau2": "tau_squared"},
    "diagnostic": {
        "se": "standard_error", "pval": "p_value", "tau2": "tau_squared",
        "QE": "q", "QEp": "q_p_value", "I2": "i_squared",
    },
}
_FAMILY_RESULT_FIELDS = {
    "binary": ("binary_numerics", {"b": "estimate", "ci.lb": "lower", "ci.ub": "upper"}, True),
    "binary_proportion": ("binary_proportion_numerics", {"b": "estimate", "ci.lb": "lower", "ci.ub": "upper"}, True),
    "continuous": ("continuous_numerics", {"b": "estimate", "ci.lb": "lower_bound", "ci.ub": "upper_bound"}, False),
    "diagnostic": ("diagnostic_numerics", {"b": "estimate", "ci.lb": "lower", "ci.ub": "upper"}, True),
}


def _strict_json(data: bytes, label: str) -> Any:
    def object_from_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{label} contains duplicate JSON property {key!r}.")
            result[key] = value
        return result

    def finite_float(token: str) -> float:
        value = float(token)
        if not math.isfinite(value):
            raise ValueError(f"{label} contains a non-finite JSON number.")
        return value

    def reject_constant(token: str) -> None:
        raise ValueError(f"{label} contains the invalid JSON constant {token}.")

    return json.loads(
        data.decode("utf-8"),
        object_pairs_hook=object_from_pairs,
        parse_float=finite_float,
        parse_constant=reject_constant,
    )


def _read_json(path: Path, label: str, limit: int = _MAX_MEMBER) -> Any:
    if path.stat().st_size > limit:
        raise ValueError(f"{label} exceeds the bounded JSON size.")
    return _strict_json(path.read_bytes(), label)


def _safe_member_name(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        bool(name)
        and "\\" not in name
        and not path.is_absolute()
        and all(part not in {"", ".", ".."} for part in path.parts)
        and (name in {"manifest.json", "project.json", "state.json"} or _ASSET_NAME.fullmatch(name) is not None)
    )


def _read_zip_members(path: Path) -> dict[str, bytes]:
    _validate_archive_file(path)
    with zipfile.ZipFile(path) as archive:
        entries = _validated_zip_entries(archive)
        if archive.testzip() is not None:
            raise ValueError("Saved project archive has a corrupt member.")
        return {entry.filename: archive.read(entry) for entry in entries}


def _validate_archive_file(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Saved project archive must be a regular file inside the qualification output.")
    if path.stat().st_size > _MAX_ARCHIVE:
        raise ValueError("Saved project archive exceeds the size bound.")


def _validated_zip_entries(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    entries = archive.infolist()
    names = {entry.filename for entry in entries}
    if len(entries) > _MAX_MEMBERS or len(names) != len(entries):
        raise ValueError("Saved project archive has too many or duplicate members.")
    if sum(entry.file_size for entry in entries) > _MAX_TOTAL:
        raise ValueError("Saved project archive exceeds the total size bound.")
    if not _REQUIRED_PROJECT_MEMBERS <= names:
        raise ValueError("Saved project archive is incomplete.")
    for entry in entries:
        _validate_zip_entry(entry)
    return entries


def _validate_zip_entry(entry: zipfile.ZipInfo) -> None:
    _validate_zip_member_header(entry)
    _validate_zip_member_size(entry)


def _validate_zip_member_header(entry: zipfile.ZipInfo) -> None:
    mode = entry.external_attr >> 16
    if not _safe_member_name(entry.filename):
        raise ValueError("Saved project archive contains an unsafe or unsupported member.")
    if entry.is_dir() or stat.S_ISLNK(mode) or entry.flag_bits & 1:
        raise ValueError("Saved project archive contains an unsafe or unsupported member.")
    if entry.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
        raise ValueError("Saved project archive contains an unsafe or unsupported member.")


def _validate_zip_member_size(entry: zipfile.ZipInfo) -> None:
    if entry.file_size > _MAX_MEMBER:
        raise ValueError("Saved project archive contains an unsafe or unsupported member.")
    if entry.file_size == 0:
        return
    if not entry.compress_size or entry.file_size / entry.compress_size > 100:
        raise ValueError("Saved project archive contains an oversized compression ratio.")


def _validate_project_manifest(members: dict[str, bytes]) -> dict[str, Any]:
    manifest = _strict_json(members["manifest.json"], "saved project manifest")
    _validate_project_manifest_shape(manifest)
    if set(manifest["members"]) != set(members) - {"manifest.json"}:
        raise ValueError("Saved project manifest member list does not match the archive.")
    _validate_project_member_hashes(members, manifest["members"])
    return _strict_json(members["project.json"], "saved project")


def _validate_project_manifest_shape(manifest: Any) -> None:
    expected = {"application", "format", "format_version", "members"}
    if not isinstance(manifest, dict) or set(manifest) != expected:
        raise ValueError("Saved project manifest fields do not match the v2 schema.")
    if manifest.get("format") != "rc-metastudio-project" or manifest.get("format_version") != 2:
        raise ValueError("Saved project manifest is not a v2 project manifest.")
    if not isinstance(manifest.get("members"), dict):
        raise ValueError("Saved project manifest member table is invalid.")


def _validate_project_member_hashes(members: dict[str, bytes], descriptors: dict[str, Any]) -> None:
    for name, descriptor in descriptors.items():
        content = members[name]
        digest = hashlib.sha256(content).hexdigest()
        _validate_member_descriptor(name, descriptor, digest, len(content))
        _validate_asset_digest(name, digest)


def _validate_member_descriptor(name: str, descriptor: Any, digest: str, size: int) -> None:
    if not isinstance(descriptor, dict) or set(descriptor) != {"sha256", "size"}:
        raise ValueError(f"Saved project member integrity check failed for {name}.")
    sha256, recorded_size = descriptor["sha256"], descriptor["size"]
    if not isinstance(sha256, str) or not _SHA256.fullmatch(sha256) or type(recorded_size) is not int:
        raise ValueError(f"Saved project member integrity check failed for {name}.")
    if sha256 != digest or recorded_size != size:
        raise ValueError(f"Saved project member integrity check failed for {name}.")


def _validate_asset_digest(name: str, digest: str) -> None:
    asset = _ASSET_NAME.fullmatch(name)
    if asset is not None and asset.group(1) != digest:
        raise ValueError(f"Saved project asset name does not match its content hash: {name}.")


def _read_project_archive(path: Path) -> dict[str, Any]:
    project = _validate_project_manifest(_read_zip_members(path))
    if not isinstance(project, dict) or project.get("schema_version") != 2:
        raise ValueError("Saved project has an unsupported project schema.")
    if not isinstance(project.get("saved_analyses"), list):
        raise ValueError("Saved project has no saved analysis list.")
    return project


def _report_paths(qualification_dir: Path, selected_report: Path | None) -> list[Path]:
    root = qualification_dir.resolve(strict=True)
    if selected_report is not None:
        path = selected_report if selected_report.is_absolute() else root / selected_report
        if path.is_symlink():
            raise ValueError("Selected journey report cannot be a symbolic link.")
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(root):
            raise ValueError("Selected journey report must be inside the qualification directory.")
        return [resolved]
    return [path for path in root.glob("*.json") if path.is_file() and not path.is_symlink()]


def _journey_report(path: Path, route: str, required: bool) -> dict[str, Any] | None:
    if path.stat().st_size > 2 * 1024 * 1024:
        return None
    try:
        report = _read_json(path, "worker journey report", 2 * 1024 * 1024)
    except (ValueError, UnicodeDecodeError):
        if required:
            raise
        return None
    if not isinstance(report, dict):
        return None
    routes = report.get("requested_routes")
    if not isinstance(routes, list) or route not in routes or not isinstance(report.get("routes"), list):
        return None
    return report


def _report_candidates(qualification_dir: Path, route: str, selected_report: Path | None) -> list[tuple[Path, dict[str, Any]]]:
    candidates: list[tuple[Path, dict[str, Any]]] = []
    for path in _report_paths(qualification_dir, selected_report):
        report = _journey_report(path, route, selected_report is not None)
        if report is not None:
            candidates.append((path, report))
    return candidates


def _load_saved_record(
    qualification_dir: Path, spec: dict[str, Any], selected_report: Path | None = None
) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    route = spec["journey"]["route"]
    candidates = _report_candidates(qualification_dir, route, selected_report)
    if len(candidates) != 1:
        raise ValueError(f"Expected one qualification report containing {route}; found {len(candidates)}.")
    report_path, report = candidates[0]
    run = _run_for_route(report, route, spec)
    project_path = _project_path_for_report(report_path, route)
    project = _read_project_archive(project_path)
    record = _record_for_analysis(project, run)
    root = qualification_dir.resolve()
    return run, record, report_path.relative_to(root).as_posix(), project_path.relative_to(root).as_posix()


def _run_for_route(report: dict[str, Any], route: str, spec: dict[str, Any]) -> dict[str, Any]:
    routes = report.get("routes")
    if not isinstance(routes, list):
        raise ValueError(f"Qualification report does not contain exactly one {route} route.")
    matching = [item for item in routes if isinstance(item, dict) and item.get("route") == route]
    if len(matching) != 1:
        raise ValueError(f"Qualification report does not contain exactly one {route} route.")
    return _validate_route_record(matching[0], route, spec)


def _record_for_analysis(project: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    analysis_id = run.get("analysis_id")
    records = [
        item for item in project["saved_analyses"]
        if isinstance(item, dict) and item.get("id") == analysis_id
    ]
    if len(records) != 1:
        raise ValueError(f"Saved project does not contain exactly one record for route analysis {analysis_id}.")
    return records[0]


def _validate_route_record(route_record: dict[str, Any], route: str, spec: dict[str, Any]) -> dict[str, Any]:
    observation = route_record.get("observation")
    if not isinstance(observation, dict):
        raise ValueError(f"The saved {route} journey has no observation.")
    _validate_route_completion(route_record, observation, route)
    _validate_route_sample(route_record, route, spec["journey"])
    runs = observation.get("analysis_runs")
    if not isinstance(runs, list) or len(runs) != 1 or not isinstance(runs[0], dict):
        raise ValueError(f"The {route} route did not retain exactly one analysis run.")
    run = runs[0]
    _validate_run_request(run, route, spec)
    return run


def _validate_route_completion(route_record: dict[str, Any], observation: dict[str, Any], route: str) -> None:
    completed = route_record.get("status") == "complete" and observation.get("route") == route
    saved_and_reopened = observation.get("saved_analysis_status") == "complete" and observation.get("reopened_analysis_count") == 1
    if not completed or not saved_and_reopened:
        raise ValueError(f"The saved {route} journey did not complete and reopen one analysis.")


def _validate_route_sample(route_record: dict[str, Any], route: str, journey: dict[str, Any]) -> None:
    same_hash = route_record.get("sample_project_sha256") == journey["sample_project_sha256"]
    same_name = _path_basename(route_record.get("sample_project")) == journey["sample_project"]
    if not same_hash or not same_name:
        raise ValueError(f"The {route} route used a different sample project.")


def _validate_run_request(run: dict[str, Any], route: str, spec: dict[str, Any]) -> None:
    identity = (run.get("status"), run.get("workflow"), run.get("method"), run.get("metric"))
    expected = ("complete", spec["workflow"], spec["method"], spec["metric"])
    if identity != expected:
        raise ValueError(f"The {route} route completed a different analysis request.")


def _project_path_for_report(report_path: Path, route: str) -> Path:
    slug = route.replace(".", "-")
    return report_path.with_name(f"{report_path.stem}-{slug}.rcms")


def _path_basename(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return PureWindowsPath(value).name or PurePosixPath(value).name


def _record_input_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    snapshot = record.get("input_snapshot")
    if not isinstance(snapshot, dict):
        raise ValueError("Saved analysis record has no frozen input snapshot.")
    return snapshot


def _compare_exact(differences: list[str], compared: list[str], field: str, expected: Any, actual: Any) -> None:
    compared.append(field)
    if actual != expected:
        differences.append(f"{field} differs from the pinned case specification.")


def _snapshot_input_differences(snapshot: dict[str, Any], spec: dict[str, Any]) -> list[str]:
    studies = _snapshot_study_rows(snapshot)
    names = [study.get("name") for study in studies]
    years = [study.get("year") for study in studies]
    differences = _snapshot_selection_differences(snapshot, spec, names, years)
    if len(studies) != len(spec["input"]["study_names"]):
        differences.append("input study count differs from the frozen sample.")
        return differences
    differences.extend(_representation_differences(snapshot, studies, spec))
    return differences


def _snapshot_study_rows(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    studies = snapshot.get("studies")
    if not isinstance(studies, list):
        raise ValueError("Saved analysis snapshot has no ordered study rows.")
    if any(not isinstance(study, dict) for study in studies):
        raise ValueError("Saved analysis snapshot contains a malformed study row.")
    return studies


def _representation_differences(snapshot: dict[str, Any], studies: list[dict[str, Any]], spec: dict[str, Any]) -> list[str]:
    representation = spec["journey"]["input_representation"]
    validators = {
        "two-arm-raw-binary-counts": _two_arm_binary_differences,
        "one-arm-raw-binary-counts": _one_arm_binary_differences,
        "two-arm-raw-continuous-summary": _raw_continuous_differences,
        "entered-continuous-effect": _entered_continuous_differences,
        "diagnostic-raw-counts-tp-fn-fp-tn": _diagnostic_differences,
    }
    validator = validators.get(representation)
    if validator is None:
        raise ValueError(f"Unsupported journey input representation: {representation}.")
    return validator(snapshot, studies, spec["input"])


def _snapshot_selection_differences(snapshot: dict[str, Any], spec: dict[str, Any], names: list[Any], years: list[Any]) -> list[str]:
    journey = spec["journey"]
    checks = (
        ("study names", spec["input"]["study_names"], names),
        ("years", spec["input"]["years"], years),
        ("outcome", journey["selected_outcome"], snapshot.get("outcome")),
        ("metric", spec["metric"], snapshot.get("metric")),
        ("groups", journey["groups"], snapshot.get("groups")),
        ("time point", journey["time_point"], snapshot.get("follow_up", snapshot.get("time_point"))),
    )
    return [f"input {name} differs from the frozen sample selection." for name, expected, actual in checks if expected != actual]


def _two_arm_binary_differences(snapshot: dict[str, Any], studies: list[Any], inp: dict[str, Any]) -> list[str]:
    if snapshot.get("raw_counts_available") is not True:
        return ["input raw binary counts are unavailable in the saved snapshot."]
    fields = (
        ("g1O1", lambda row: row.get("treatment_events")),
        ("g1O2", lambda row: row.get("treatment_total", -1) - row.get("treatment_events", 0)),
        ("g2O1", lambda row: row.get("control_events")),
        ("g2O2", lambda row: row.get("control_total", -1) - row.get("control_events", 0)),
    )
    return [
        f"input.{field} differs from the saved raw counts."
        for field, value in fields
        if [value(row) for row in studies] != inp[field]
    ]


def _one_arm_binary_differences(snapshot: dict[str, Any], studies: list[Any], inp: dict[str, Any]) -> list[str]:
    if snapshot.get("raw_counts_available") is not True:
        return ["input one-arm raw counts differ from the saved sample."]
    if inp["g2O1"] or inp["g2O2"]:
        return ["input one-arm raw counts differ from the saved sample."]
    if not _one_arm_counts_match(studies, inp):
        return ["input one-arm raw counts differ from the saved sample."]
    return []


def _one_arm_counts_match(studies: list[Any], inp: dict[str, Any]) -> bool:
    expected_totals = [events + non_events for events, non_events in zip(inp["g1O1"], inp["g1O2"])]
    events = [row.get("events") for row in studies]
    totals = [row.get("total") for row in studies]
    return events == inp["g1O1"] and totals == expected_totals


def _raw_continuous_differences(snapshot: dict[str, Any], studies: list[Any], inp: dict[str, Any]) -> list[str]:
    differences = []
    for index, row in enumerate(studies):
        if row.get("provenance") != "raw_reconstructed":
            differences.append("input continuous rows are not marked raw reconstructed.")
            break
        for arm, suffix in (("arm_1", "1"), ("arm_2", "2")):
            values = row.get(arm)
            if not isinstance(values, dict):
                differences.append(f"input.{arm} is missing from a raw continuous study.")
                continue
            for member, field in (("sample_size", "N"), ("mean", "mean"), ("standard_deviation", "sd")):
                if values.get(member) != inp[f"{field}{suffix}"][index]:
                    differences.append(f"input.{arm}.{member} differs from the saved sample.")
    return differences


def _entered_continuous_differences(snapshot: dict[str, Any], studies: list[Any], inp: dict[str, Any]) -> list[str]:
    for index, row in enumerate(studies):
        if (
            row.get("provenance") != "entered"
            or row.get("arm_1") is not None
            or row.get("arm_2") is not None
            or row.get("estimate") != inp["y"][index]
            or row.get("standard_error") != inp["SE"][index]
        ):
            return ["input entered effect or standard error differs from the saved sample."]
    return []


def _diagnostic_differences(snapshot: dict[str, Any], studies: list[Any], inp: dict[str, Any]) -> list[str]:
    differences = [] if snapshot.get("input_source") == "counts" else ["input diagnostic source is not raw counts."]
    for field in ("TP", "FN", "FP", "TN"):
        if [row.get(field.lower()) for row in studies] != inp[field]:
            differences.append(f"input.{field} differs from the saved diagnostic counts.")
    return differences


def _numeric_values(statistics: dict[str, Any], field: str, count: int) -> list[float | None]:
    values = statistics.get(field)
    if not isinstance(values, list) or len(values) != count:
        raise ValueError(f"Pinned package statistic statistics.{field} has an unexpected cardinality.")
    return [_numeric_value(item, field) for item in values]


def _numeric_value(item: Any, field: str) -> float | None:
    valid_states = {"finite", "na", "nan", "pos_inf", "neg_inf"}
    if not isinstance(item, dict) or item.get("state") not in valid_states:
        raise ValueError(f"Pinned package statistic {field} has an invalid numeric state.")
    if item["state"] != "finite":
        if set(item) != {"state"}:
            raise ValueError(f"Pinned package statistic {field} has a malformed non-finite state.")
        return None
    value = item.get("value")
    if set(item) != {"state", "value"} or type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"Pinned package statistic {field} has an invalid finite value.")
    return float(value)


def _finite_saved(value: Any) -> float | None:
    if type(value) in (int, float) and math.isfinite(value):
        return float(value)
    return None


def _compare_numbers(
    differences: list[str], compared: list[str], field: str,
    expected: list[float | None], actual: list[Any],
) -> None:
    compared.append(field)
    if len(expected) != len(actual):
        differences.append(f"{field} cardinality differs (reference {len(expected)}, saved {len(actual)}).")
        return
    for index, (want, value) in enumerate(zip(expected, actual)):
        got = _finite_saved(value)
        if want is None or got is None:
            differences.append(f"{field}[{index}] finite/non-finite state differs or is unavailable.")
            continue
        tolerance = max(_ABS_TOLERANCE, _REL_TOLERANCE * abs(want))
        if abs(want - got) > tolerance:
            differences.append(f"{field}[{index}] differs: reference {want:.17g}, saved {got:.17g}.")


def _available_number(value: Any) -> float | None:
    if not isinstance(value, dict) or value.get("status") != "available":
        return None
    return _finite_saved(value.get("value"))


def _family_numbers(record: dict[str, Any], spec: dict[str, Any]) -> tuple[dict[str, float | None], list[dict[str, Any]], list[float | None]]:
    section, pooled_map, uses_calculation = _family_numeric_section(record, spec)
    pooled = section["pooled"]
    points = pooled.get("calculation") if uses_calculation else pooled
    if not isinstance(points, dict):
        raise ValueError("Saved family numeric result has no pooled estimate fields.")
    pooled_values = {name: _available_number(points.get(source)) for name, source in pooled_map.items()}
    typed_source = section if spec["family"] == "continuous" else pooled
    for field, source in _TYPED_POOLED_FIELDS[spec["family"]].items():
        if source in typed_source:
            pooled_values[field] = _available_number(typed_source[source])
    studies = section["studies"]
    study_values = _family_study_estimates(studies, uses_calculation)
    return pooled_values, studies, study_values


def _family_numeric_section(record: dict[str, Any], spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str], bool]:
    results = record.get("results")
    if not isinstance(results, dict):
        raise ValueError("Saved analysis has no results object.")
    family_key = _result_family_key(spec)
    section_name, pooled_map, uses_calculation = _FAMILY_RESULT_FIELDS[family_key]
    section = results.get(section_name)
    _validate_family_section(section, section_name)
    return section, pooled_map, uses_calculation


def _result_family_key(spec: dict[str, Any]) -> str:
    if spec["family"] == "binary" and spec["metric"] == "PLO":
        return "binary_proportion"
    return spec["family"]


def _validate_family_section(section: Any, section_name: str) -> None:
    if not isinstance(section, dict) or not isinstance(section.get("pooled"), dict):
        raise ValueError(f"Saved analysis is missing {section_name}.")
    studies = section.get("studies")
    if not isinstance(studies, list):
        raise ValueError(f"Saved analysis is missing {section_name}.")
    if any(not isinstance(study, dict) for study in studies):
        raise ValueError("Saved analysis contains a malformed numeric study record.")


def _family_study_estimates(studies: list[dict[str, Any]], uses_calculation: bool) -> list[float | None]:
    if not uses_calculation:
        return [_finite_saved(study.get("estimate")) for study in studies]
    return [
        _available_number(calculation.get("estimate")) if isinstance(calculation, dict) else None
        for calculation in (study.get("calculation") for study in studies)
    ]


def _forest_labels(snapshot: dict[str, Any]) -> list[str]:
    studies = snapshot.get("studies")
    if not isinstance(studies, list):
        raise ValueError("Saved analysis snapshot has no ordered study rows for forest labels.")
    return [_forest_label(study) for study in studies]


def _forest_label(study: Any) -> str:
    if not isinstance(study, dict) or not isinstance(study.get("name"), str):
        raise ValueError("Saved analysis snapshot has an invalid forest study label.")
    label = study["name"]
    year_text = _forest_year_text(study.get("year"))
    if year_text and re.search(rf"(^|[^0-9]){re.escape(year_text)}$", label.strip()) is None:
        label = f"{label}, {year_text}"
    if len(label) > 72:
        return f"{label[:56]}...{label[-13:]}"
    return label


def _forest_year_text(year: Any) -> str:
    if type(year) is int and year != 0:
        return str(year)
    if type(year) is float and math.isfinite(year) and year != 0:
        return str(int(year)) if year.is_integer() else str(year)
    return ""


def _compare_reference_identity(spec: dict[str, Any], reference: dict[str, Any], differences: list[str], compared: list[str]) -> None:
    case_id = spec["id"]
    _compare_exact(differences, compared, "reference.id", case_id, reference.get("id"))
    expected_request = {key: spec[key] for key in ("family", "metric", "method", "workflow")}
    expected_request["params"] = spec["params"]
    _compare_exact(differences, compared, "reference.request", expected_request, reference.get("request"))
    _compare_exact(differences, compared, "reference.input", spec["input"], reference.get("input"))
    _compare_exact(differences, compared, "reference.journey", spec["journey"], reference.get("journey"))
    _compare_exact(differences, compared, "reference status", "success", reference.get("status"))
    eligibility = reference.get("eligibility")
    if not isinstance(eligibility, dict):
        raise ValueError("Pinned package case has no eligibility record.")
    names = spec["input"]["study_names"]
    checks = (
        ("ordered input studies", names, eligibility.get("ordered_input_studies")),
        ("fit order", names, eligibility.get("fit_study_order")),
        ("fit-order flag", True, eligibility.get("api_returned_fit_order")),
        ("excluded studies", [], eligibility.get("excluded_studies")),
        ("usable count", len(names), eligibility.get("usable_studies")),
        ("usable-count equality", True, eligibility.get("usable_count_matches_input")),
    )
    for field, expected, actual in checks:
        _compare_exact(differences, compared, f"reference {field}", expected, actual)


def _compare_saved_record(spec: dict[str, Any], reference: dict[str, Any], run: dict[str, Any], record: dict[str, Any], differences: list[str], compared: list[str]) -> dict[str, Any]:
    _compare_exact(differences, compared, "saved record id", run.get("analysis_id"), record.get("id"))
    _compare_exact(differences, compared, "saved record input identity", run.get("input_identity"), record.get("input_identity"))
    _compare_exact(differences, compared, "saved record status", "complete", record.get("status"))
    _compare_exact(differences, compared, "saved record warnings", reference.get("warnings"), record.get("warnings"))
    expected_specification = {
        "data_type": spec["family"], "method": spec["method"], "metric": spec["metric"],
        "params": spec["params"], "version": 1, "workflow": spec["workflow"],
    }
    specification = record.get("specification")
    _compare_exact(differences, compared, "saved requested specification", expected_specification, specification)
    if isinstance(specification, dict):
        _compare_exact(differences, compared, "saved specification identity", canonical_sha256(specification), record.get("specification_identity"))
    snapshot = _record_input_snapshot(record)
    _compare_exact(differences, compared, "saved record input snapshot identity", canonical_sha256(snapshot), record.get("input_identity"))
    differences.extend(_snapshot_input_differences(snapshot, spec))
    return snapshot


def _saved_plot_state(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    results = record.get("results")
    states = results.get("plot_render_state") if isinstance(results, dict) else None
    plot_state = states.get("analysis.standard.forest_plot.1") if isinstance(states, dict) else None
    if not isinstance(plot_state, dict) or plot_state.get("renderer") != "rcmetar_forest_v1":
        raise ValueError("Saved analysis is missing its frozen standard forest geometry.")
    summary, studies = plot_state.get("summary"), plot_state.get("studies")
    if not isinstance(summary, dict) or not isinstance(studies, dict):
        raise ValueError("Saved forest geometry has no pooled or study values.")
    return plot_state, summary


def _compare_primary_statistics(spec: dict[str, Any], statistics: dict[str, Any], plot_state: dict[str, Any], plot_summary: dict[str, Any], record: dict[str, Any], differences: list[str], compared: list[str]) -> tuple[dict[str, float | None], list[dict[str, Any]], list[float | None]]:
    study_names = spec["input"]["study_names"]
    if statistics.get("study_labels") != study_names:
        differences.append("reference study labels differ from the frozen input order.")
    pooled_values, family_studies, family_yi = _family_numbers(record, spec)
    if [study.get("label") for study in family_studies] != study_names:
        differences.append("saved numeric study labels differ from the frozen input order.")
    plot_studies = plot_state.get("studies")
    if not isinstance(plot_studies, dict) or plot_studies.get("labels") != _forest_labels(
        _record_input_snapshot(record)
    ):
        differences.append("saved forest labels differ from the frozen study names and years.")
    for field, summary_key in (("b", "b"), ("ci.lb", "ci_lb"), ("ci.ub", "ci_ub")):
        expected = _numeric_values(statistics, field, 1)
        _compare_numbers(differences, compared, f"statistics.{field} vs saved forest summary", expected, [plot_summary.get(summary_key)])
        _compare_numbers(differences, compared, f"statistics.{field} vs saved numeric result", expected, [pooled_values.get(field)])
    expected_k = _numeric_values(statistics, "k", 1)
    _compare_numbers(differences, compared, "statistics.k vs saved forest summary", expected_k, [plot_summary.get("k")])
    _compare_numbers(differences, compared, "statistics.k vs saved numeric table row count", expected_k, [len(family_studies)])
    _compare_numbers(differences, compared, "statistics.k vs saved numeric result", expected_k, [_available_number(_study_count_value(record, spec))])
    _compare_study_vectors(spec, statistics, plot_state, family_studies, family_yi, study_names, differences, compared)
    return pooled_values, family_studies, family_yi


def _compare_family_study_fields(spec: dict[str, Any], statistics: dict[str, Any], family_studies: list[dict[str, Any]], differences: list[str], compared: list[str]) -> None:
    if spec["family"] == "continuous":
        _compare_continuous_study_variances(statistics, family_studies, differences, compared)
    elif spec["family"] == "diagnostic":
        _compare_diagnostic_study_fields(statistics, family_studies, differences, compared)
    else:
        _compare_binary_study_weights(statistics, family_studies, differences, compared)


def _compare_continuous_study_variances(statistics: dict[str, Any], studies: list[dict[str, Any]], differences: list[str], compared: list[str]) -> None:
    variances = []
    for study in studies:
        standard_error = _finite_saved(study.get("standard_error"))
        variances.append(None if standard_error is None else standard_error**2)
    expected = _numeric_values(statistics, "vi", len(studies))
    _compare_numbers(differences, compared, "statistics.vi vs saved continuous standard error squared", expected, variances)


def _compare_diagnostic_study_fields(statistics: dict[str, Any], studies: list[dict[str, Any]], differences: list[str], compared: list[str]) -> None:
    count = len(studies)
    expected_vi = _numeric_values(statistics, "vi", count)
    expected_weights = _numeric_values(statistics, "weights", count)
    variances = [_available_number(study.get("variance")) for study in studies]
    fractions = [_available_number(study.get("weight_fraction")) for study in studies]
    _compare_numbers(differences, compared, "statistics.vi vs saved diagnostic variance", expected_vi, variances)
    weights_percent = [None if value is None else value * 100 for value in fractions]
    _compare_numbers(differences, compared, "statistics.weights vs saved diagnostic weight fraction percent", expected_weights, weights_percent)


def _compare_binary_study_weights(statistics: dict[str, Any], studies: list[dict[str, Any]], differences: list[str], compared: list[str]) -> None:
    if not any("weight" in study for study in studies):
        return
    expected = _numeric_values(statistics, "weights", len(studies))
    weights = [_available_number(study.get("weight")) for study in studies]
    _compare_numbers(differences, compared, "statistics.weights vs saved binary study weights", expected, weights)


def _compare_study_vectors(spec: dict[str, Any], statistics: dict[str, Any], plot_state: dict[str, Any], family_studies: list[dict[str, Any]], family_yi: list[float | None], study_names: list[str], differences: list[str], compared: list[str]) -> None:
    vectors = _saved_forest_vectors(plot_state, len(study_names))
    count = len(study_names)
    yi, vi, weights = vectors
    for field, actual in (("yi", yi), ("vi", vi), ("weights", weights)):
        _compare_numbers(differences, compared, f"statistics.{field}", _numeric_values(statistics, field, count), actual)
    _compare_numbers(differences, compared, "statistics.yi vs saved family numerics", _numeric_values(statistics, "yi", count), family_yi)
    _compare_family_study_fields(spec, statistics, family_studies, differences, compared)


def _saved_forest_vectors(plot_state: dict[str, Any], count: int) -> tuple[list[Any], list[Any], list[Any]]:
    studies = plot_state.get("studies")
    if not isinstance(studies, dict):
        raise ValueError("Saved forest geometry has no study vectors.")
    yi, vi, weights = studies.get("yi"), studies.get("vi"), plot_state.get("weights")
    if not isinstance(yi, list) or not isinstance(vi, list) or not isinstance(weights, list):
        raise ValueError("Saved forest geometry vectors are malformed.")
    if any(len(values) != count for values in (yi, vi, weights)):
        raise ValueError("Saved forest geometry does not align with the frozen study count.")
    return yi, vi, weights


def _compare_optional_statistics(spec: dict[str, Any], statistics: dict[str, Any], summary: dict[str, Any], pooled: dict[str, float | None], differences: list[str], compared: list[str], unavailable: list[dict[str, str]]) -> None:
    _compare_optional_family_statistics(spec, statistics, pooled, differences, compared, unavailable)
    _compare_optional_forest_statistics(statistics, summary, differences, compared, unavailable)
    unavailable.append({"field": "statistics.df", "reason": "degrees of freedom are not retained in the saved numeric result"})


def _compare_optional_family_statistics(spec: dict[str, Any], statistics: dict[str, Any], pooled: dict[str, float | None], differences: list[str], compared: list[str], unavailable: list[dict[str, str]]) -> None:
    typed_fields = _TYPED_POOLED_FIELDS[spec["family"]]
    for field in ("se", "pval", "tau2", "QE", "QEp", "I2"):
        if field in typed_fields:
            _compare_optional_typed_value(field, statistics, pooled, differences, compared, unavailable)
    if "se" not in typed_fields:
        unavailable.append({"field": "statistics.se", "reason": "pooled standard error is not retained in this saved result family"})


def _compare_optional_typed_value(field: str, statistics: dict[str, Any], pooled: dict[str, float | None], differences: list[str], compared: list[str], unavailable: list[dict[str, str]]) -> None:
    name = f"family_table.statistics.{field}"
    if field not in statistics:
        unavailable.append({"field": name, "reason": "the published package API did not return this statistic"})
    elif field not in pooled:
        unavailable.append({"field": name, "reason": "the saved family numeric table does not retain this statistic"})
    else:
        _compare_numbers(differences, compared, name, _numeric_values(statistics, field, 1), [pooled[field]])


def _compare_optional_forest_statistics(statistics: dict[str, Any], summary: dict[str, Any], differences: list[str], compared: list[str], unavailable: list[dict[str, str]]) -> None:
    for field in ("zval", "pval", "tau2", "QE", "QEp", "I2"):
        if field not in statistics:
            unavailable.append({"field": f"statistics.{field}", "reason": "not returned by the published package API"})
        elif field not in summary:
            unavailable.append({"field": f"statistics.{field}", "reason": "not retained in the saved forest summary"})
        else:
            _compare_numbers(differences, compared, f"statistics.{field}", _numeric_values(statistics, field, 1), [summary[field]])


def _compare_saved_case(qualification_dir: Path, spec: dict[str, Any], reference: dict[str, Any], selected_report: Path | None = None) -> dict[str, Any]:
    differences: list[str] = []
    unavailable: list[dict[str, str]] = []
    compared: list[str] = []
    case_id = spec["id"]
    try:
        _compare_reference_identity(spec, reference, differences, compared)
        run, record, report_source, project_source = _load_saved_record(qualification_dir, spec, selected_report)
        _compare_saved_record(spec, reference, run, record, differences, compared)
        statistics = reference.get("outputs", {}).get("statistics")
        if not isinstance(statistics, dict):
            raise ValueError("Pinned package case has no analysis statistics.")
        plot_state, summary = _saved_plot_state(record)
        pooled, family_studies, family_yi = _compare_primary_statistics(spec, statistics, plot_state, summary, record, differences, compared)
        _compare_optional_statistics(spec, statistics, summary, pooled, differences, compared, unavailable)
        return {
            "id": case_id,
            "passed": not differences,
            "journey_sources": {
                "route_report": report_source,
                "saved_project": project_source,
                "analysis_id": run.get("analysis_id"),
                "input_identity": record.get("input_identity"),
            },
            "compared_fields": compared,
            "unavailable": unavailable,
            "differences": differences,
        }
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, UnicodeDecodeError) as error:
        differences.append(str(error))
        return {"id": case_id, "passed": False, "compared_fields": compared, "unavailable": unavailable, "differences": differences}


def _study_count_value(record: dict[str, Any], spec: dict[str, Any]) -> Any:
    results = record.get("results", {})
    if spec["family"] == "binary":
        section = results.get("binary_proportion_numerics" if spec["metric"] == "PLO" else "binary_numerics", {})
    elif spec["family"] == "continuous":
        section = results.get("continuous_numerics", {})
        return section.get("analyzed_study_count")
    else:
        section = results.get("diagnostic_numerics", {})
    return section.get("pooled", {}).get("study_count")


def _load_case_specs(path: Path) -> dict[str, Any]:
    spec = _read_json(path, "journey case specification", 2 * 1024 * 1024)
    if not isinstance(spec, dict) or set(spec) != {"schema_version", "case_ids", "cases"}:
        raise ValueError("Journey case specification schema is invalid.")
    if spec["schema_version"] != 1 or not isinstance(spec["cases"], list) or not isinstance(spec["case_ids"], list):
        raise ValueError("Journey case specification schema is invalid.")
    _validate_case_inventory(spec)
    return spec


def _validate_case_inventory(spec: dict[str, Any]) -> None:
    _validate_case_ids(spec)
    _validate_journey_inventory(spec)


def _validate_case_ids(spec: dict[str, Any]) -> None:
    ids = [case.get("id") for case in spec["cases"] if isinstance(case, dict)]
    if len(ids) != len(spec["cases"]):
        raise ValueError("Journey case specifications are missing, duplicated, or out of order.")
    if ids != spec["case_ids"] or len(ids) != len(set(ids)):
        raise ValueError("Journey case specifications are missing, duplicated, or out of order.")


def _validate_journey_inventory(spec: dict[str, Any]) -> None:
    journey_specs = [case for case in spec["cases"] if "journey" in case]
    if tuple(case["id"] for case in journey_specs) != JOURNEY_IDS:
        raise ValueError("Journey case inventory does not match the five qualified routes.")


def compare_saved_journeys(
    qualification_dir: Path,
    case_path: Path,
    reference_path: Path,
    selected_report: Path | None = None,
) -> dict[str, Any]:
    case_specs = _load_case_specs(case_path)
    manifest = _read_json(reference_path, "published package-reference manifest", 2 * 1024 * 1024)
    validate_package_manifest(manifest, case_specs=case_specs)
    if manifest.get("schema_version") != 2 or manifest.get("capture_role") != "release-reference":
        raise ValueError("Comparison requires a fresh schema-v2 published release reference.")
    references = {case["id"]: case for case in manifest["cases"]}
    cases = [spec for spec in case_specs["cases"] if "journey" in spec]
    rows = [
        _compare_saved_case(qualification_dir, spec, references[spec["id"]], selected_report)
        for spec in cases
    ]
    return {
        "schema_version": 1,
        "mode": "saved-journey-to-published-v031-package-api",
        "authority_scope": manifest["authority_scope"],
        "release": manifest["release"],
        "reference_manifest_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        "reference_workflow": manifest["workflow"],
        "numeric_tolerance": {"absolute": _ABS_TOLERANCE, "relative": _REL_TOLERANCE},
        "passed": all(row["passed"] for row in rows),
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification-dir", type=Path, required=True)
    parser.add_argument("--cases", type=Path, default=CASE_SPEC)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--report", type=Path, help="select one aggregate journey report when qualification includes multiple platforms")
    parser.add_argument("--output", type=Path, help="write the JSON comparison report to this path")
    args = parser.parse_args()
    try:
        report = compare_saved_journeys(args.qualification_dir, args.cases, args.reference, args.report)
        status = 0 if report["passed"] else 1
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, UnicodeDecodeError) as error:
        report = {"schema_version": 1, "passed": False, "error": str(error)}
        status = 2
    encoded = json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    if args.output is not None:
        try:
            args.output.write_text(encoded, encoding="utf-8")
        except OSError as error:
            report = {"schema_version": 1, "passed": False, "error": f"Could not write comparison output: {error}"}
            status = 2
            encoded = json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    print(encoded, end="")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
