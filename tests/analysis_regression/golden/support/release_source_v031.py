"""Checks and comparison rules for the tagged-source v0.3.1 reference."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
import re

from tests.analysis_regression.golden.support.analysis_regression_compare import (
    compare_golden_baseline,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
REFERENCE_DIR = (
    REPOSITORY_ROOT / "tests/analysis_regression/baseline/release-source-v031"
)
REFERENCE_MANIFEST = REFERENCE_DIR / "manifest.json"
REFERENCE_PROVENANCE = REFERENCE_DIR / "provenance.json"
REFERENCE_MANIFEST_SHA256 = (
    "e8c8c95a48c04914be352745b6a529c23f1f1485b4eba4dcdba642b762985811"
)
REFERENCE_PROVENANCE_SHA256 = (
    "145e3550e1f06aa4b40dd5d721483ca76fec9ff823ef971aeb9fe2332b1db1fe"
)
META_REGRESSION_CASES = (
    "amino-binary-meta-regression",
    "continuous-meta-regression",
)
CASE_IDENTITY_FIELDS = ("data_family", "dataset", "metric", "method")
TEMPORARY_OUTPUT_PARAMETER_FIELDS = frozenset(
    {"fp_outpath", "fp_display_path", "bp_outpath", "bp_display_path"}
)
HETEROGENEITY_LABEL_CHANGES = (
    ("Residual heterogeneity (t²)", "Residual heterogeneity (τ²)"),
    ("SE of t²", "SE of τ²"),
    ("Residual heterogeneity (t)", "Residual heterogeneity (τ)"),
)
Q_M_LABEL = "Overall moderators (Qₘ)"
RELEASE_Q_M_SEPARATOR_SPACES = 7
CURRENT_Q_M_SEPARATOR_SPACES = 11


def load_release_source_v031():
    manifest_bytes = REFERENCE_MANIFEST.read_bytes()
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_sha256 != REFERENCE_MANIFEST_SHA256:
        raise ValueError("The tagged-source v0.3.1 manifest hash does not match.")

    provenance_bytes = REFERENCE_PROVENANCE.read_bytes()
    provenance_sha256 = hashlib.sha256(provenance_bytes).hexdigest()
    if provenance_sha256 != REFERENCE_PROVENANCE_SHA256:
        raise ValueError("The tagged-source v0.3.1 provenance hash does not match.")
    provenance = json.loads(provenance_bytes.decode("utf-8-sig"))
    if not provenance_bytes.startswith(b"\xef\xbb\xbf"):
        raise ValueError("The tagged-source v0.3.1 provenance BOM is missing.")
    if provenance["capture"]["manifest_sha256"] != manifest_sha256:
        raise ValueError("The source provenance does not identify the frozen manifest.")
    return json.loads(manifest_bytes.decode("utf-8")), provenance


def compare_release_source_v031(current):
    reference, provenance = load_release_source_v031()
    comparable_reference = deepcopy(reference)
    comparable_current = deepcopy(current)
    reference_by_id = {
        case["id"]: case for case in comparable_reference["curated_golden_set"]
    }
    current_by_id = {
        case["id"]: case for case in comparable_current.get("curated_golden_set", [])
    }

    current_case_ids = [
        case["id"] for case in comparable_current.get("curated_golden_set", [])
    ]
    identity_drift = _case_identity_drift(reference_by_id, current_by_id)
    duplicate_case_ids = sorted(
        case_id
        for case_id in set(current_case_ids)
        if current_case_ids.count(case_id) > 1
    )
    if duplicate_case_ids:
        identity_drift.append(
            {"field": "case_ids", "duplicate_ids": duplicate_case_ids}
        )
    capture_status_drift = _capture_status_drift(comparable_current)
    presentation_acceptances = []
    for case_id in META_REGRESSION_CASES:
        expected = reference_by_id.get(case_id)
        actual = current_by_id.get(case_id)
        if (
            expected is None
            or actual is None
            or expected.get("method") != "meta.regression"
            or actual.get("method") != "meta.regression"
        ):
            continue
        expected_text = expected.get("texts", {}).get("Summary")
        actual_text = actual.get("texts", {}).get("Summary")
        if not isinstance(expected_text, str) or not isinstance(actual_text, str):
            continue
        normalized_text, accepted_changes = _accepted_meta_regression_presentation(
            expected_text, actual_text
        )
        if accepted_changes:
            expected["texts"]["Summary"] = normalized_text
            presentation_acceptances.append(
                {
                    "id": case_id,
                    "field": "texts.Summary",
                    "changes": accepted_changes,
                }
            )

    comparison = compare_golden_baseline(comparable_reference, comparable_current)
    passed = (
        comparison["passed"]
        and not identity_drift
        and not capture_status_drift
    )
    return {
        "mode": "tagged-source-v0.3.1-comparison",
        "passed": passed,
        "reference": {
            "tag": provenance["release"]["tag"],
            "source_commit": provenance["release"]["source_commit"],
            "manifest_sha256": provenance["capture"]["manifest_sha256"],
        },
        "comparison": comparison,
        "identity_drift": identity_drift,
        "capture_status_drift": capture_status_drift,
        "presentation_acceptances": presentation_acceptances,
    }


def _case_identity_drift(reference_by_id, current_by_id):
    drift = []
    for case_id, expected in reference_by_id.items():
        actual = current_by_id.get(case_id)
        if actual is None:
            continue
        for field in CASE_IDENTITY_FIELDS:
            if expected.get(field) != actual.get(field):
                drift.append(
                    {
                        "id": case_id,
                        "field": field,
                        "expected": expected.get(field),
                        "actual": actual.get(field),
                    }
                )
        drift.extend(
            _parameter_identity_drift(
                case_id,
                expected.get("parameters"),
                actual.get("parameters"),
            )
        )
    return drift


def _capture_status_drift(current):
    drift = []
    if current.get("passed") is not True:
        drift.append(
            {"field": "passed", "expected": True, "actual": current.get("passed")}
        )
    if current.get("capture_failures") != []:
        drift.append(
            {
                "field": "capture_failures",
                "expected": [],
                "actual": current.get("capture_failures"),
            }
        )
    rows = current.get("curated_golden_set")
    if not isinstance(rows, list):
        drift.append(
            {
                "field": "curated_golden_set",
                "expected": "a list of successful capture rows",
                "actual": rows,
            }
        )
    else:
        for index, row in enumerate(rows):
            status = row.get("status") if isinstance(row, dict) else None
            if status != "success":
                drift.append(
                    {
                        "field": "curated_golden_set[%s].status" % index,
                        "expected": "success",
                        "actual": status,
                    }
                )
    return drift


def _parameter_identity_drift(case_id, expected, actual):
    return _nested_value_drift(case_id, "parameters", expected, actual)


def _nested_value_drift(case_id, field, expected, actual):
    if isinstance(expected, dict) and isinstance(actual, dict):
        drift = []
        for key in sorted(set(expected) | set(actual)):
            if key in TEMPORARY_OUTPUT_PARAMETER_FIELDS:
                continue
            expected_present = key in expected
            actual_present = key in actual
            nested_field = "%s.%s" % (field, key)
            if not expected_present or not actual_present:
                drift.append(
                    {
                        "id": case_id,
                        "field": nested_field,
                        "expected_present": expected_present,
                        "actual_present": actual_present,
                        "expected": expected.get(key),
                        "actual": actual.get(key),
                    }
                )
            else:
                drift.extend(
                    _nested_value_drift(
                        case_id, nested_field, expected[key], actual[key]
                    )
                )
        return drift

    if isinstance(expected, list) and isinstance(actual, list):
        drift = []
        for index in range(max(len(expected), len(actual))):
            nested_field = "%s[%s]" % (field, index)
            expected_present = index < len(expected)
            actual_present = index < len(actual)
            if not expected_present or not actual_present:
                drift.append(
                    {
                        "id": case_id,
                        "field": nested_field,
                        "expected_present": expected_present,
                        "actual_present": actual_present,
                        "expected": expected[index] if expected_present else None,
                        "actual": actual[index] if actual_present else None,
                    }
                )
            else:
                drift.extend(
                    _nested_value_drift(
                        case_id, nested_field, expected[index], actual[index]
                    )
                )
        return drift

    if expected != actual:
        return [{"id": case_id, "field": field, "expected": expected, "actual": actual}]
    return []


def _accepted_meta_regression_presentation(expected_text, actual_text):
    expected_lines = expected_text.splitlines()
    actual_lines = actual_text.splitlines()
    changes = []

    for old_label, new_label in HETEROGENEITY_LABEL_CHANGES:
        expected_match = _unique_label_line(expected_lines, old_label)
        actual_match = _unique_label_line(actual_lines, new_label)
        if expected_match is None or actual_match is None:
            continue
        expected_index, expected_prefix, expected_suffix = expected_match
        actual_index, actual_prefix, actual_suffix = actual_match
        if expected_prefix != actual_prefix or expected_suffix != actual_suffix:
            continue
        expected_lines[expected_index] = expected_prefix + new_label + expected_suffix
        changes.append(
            {
                "kind": "heterogeneity-label",
                "from": old_label,
                "to": new_label,
                "numeric_and_spacing_suffix_unchanged": True,
            }
        )

    expected_q = _q_m_row(expected_lines)
    actual_q = _q_m_row(actual_lines)
    if expected_q and actual_q:
        expected_index, expected_prefix, expected_spaces, expected_suffix = expected_q
        actual_index, actual_prefix, actual_spaces, actual_suffix = actual_q
        if (
            expected_prefix == actual_prefix
            and expected_suffix == actual_suffix
            and len(expected_spaces) == RELEASE_Q_M_SEPARATOR_SPACES
            and len(actual_spaces) == CURRENT_Q_M_SEPARATOR_SPACES
        ):
            expected_lines[expected_index] = (
                expected_prefix + actual_spaces + expected_suffix
            )
            changes.append(
                {
                    "kind": "column-alignment-whitespace",
                    "label": Q_M_LABEL,
                    "reference_separator_spaces": RELEASE_Q_M_SEPARATOR_SPACES,
                    "current_separator_spaces": CURRENT_Q_M_SEPARATOR_SPACES,
                    "numeric_suffix_unchanged": True,
                }
            )

    return "\n".join(expected_lines), changes


def _unique_label_line(lines, label):
    matches = []
    for index, line in enumerate(lines):
        position = line.find(label)
        if position >= 0 and line.count(label) == 1:
            matches.append((index, line[:position], line[position + len(label) :]))
    return matches[0] if len(matches) == 1 else None


def _q_m_row(lines):
    pattern = re.compile(
        r"^(?P<prefix>\s*" + re.escape(Q_M_LABEL) + r")(?P<spaces> +)(?P<suffix>\S.*)$"
    )
    matches = []
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            matches.append(
                (
                    index,
                    match.group("prefix"),
                    match.group("spaces"),
                    match.group("suffix"),
                )
            )
    return matches[0] if len(matches) == 1 else None
