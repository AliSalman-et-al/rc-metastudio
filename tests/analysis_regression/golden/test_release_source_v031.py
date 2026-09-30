import hashlib
import json
from copy import deepcopy
from pathlib import Path

from tests.analysis_regression.golden.support.analysis_regression_compare import (
    NUMERIC_DRIFT,
    TEXT_ARTIFACT_DRIFT,
)
from tests.analysis_regression.golden.support.release_source_v031 import (
    compare_release_source_v031,
)


BASELINE_DIR = Path(__file__).resolve().parents[1] / "baseline" / "release-source-v031"
MANIFEST_SHA256 = "e8c8c95a48c04914be352745b6a529c23f1f1485b4eba4dcdba642b762985811"
PROVENANCE_SHA256 = "145e3550e1f06aa4b40dd5d721483ca76fec9ff823ef971aeb9fe2332b1db1fe"
SOURCE_COMMIT = "f488ba0c01ec458b5e99fa2b5fc9b539872ae1ec"
PUBLISHED_ASSET_SHA256 = "aeb6c9fdcbf00d8762284260ce3cdd7ffa722207d29599d1a428fa00ef30f7bd"
CASE_IDS = (
    "amino-binary-random",
    "continuous-random",
    "lymph-diagnostic-random-dor",
    "amino-binary-cumulative",
    "amino-binary-leave-one-out",
    "continuous-cumulative",
    "continuous-leave-one-out",
    "amino-binary-meta-regression",
    "continuous-meta-regression",
    "amino-binary-subgroup",
    "continuous-subgroup",
)


def test_v031_tagged_source_capture_preserves_release_provenance():
    manifest_bytes = (BASELINE_DIR / "manifest.json").read_bytes()
    provenance_bytes = (BASELINE_DIR / "provenance.json").read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    provenance = json.loads(provenance_bytes.decode("utf-8-sig"))

    assert hashlib.sha256(manifest_bytes).hexdigest() == MANIFEST_SHA256
    assert hashlib.sha256(provenance_bytes).hexdigest() == PROVENANCE_SHA256
    assert provenance_bytes.startswith(b"\xef\xbb\xbf")
    assert provenance["capture"]["manifest_sha256"] == MANIFEST_SHA256
    assert provenance["release"]["tag"] == "v0.3.1"
    assert provenance["release"]["source_commit"] == SOURCE_COMMIT
    assert provenance["release"]["asset_name"] == "RCMetaStudio-windows-x64.zip"
    assert provenance["release"]["asset_sha256"] == PUBLISHED_ASSET_SHA256
    assert provenance["workflow"]["run_id"] == "36672536377"
    assert provenance["capture"]["case_count"] == len(CASE_IDS)
    assert provenance["capture"]["case_ids"] == list(CASE_IDS)
    assert provenance["authority_scope"].startswith(
        "Numerical and semantic analysis results from the v0.3.1 tagged source harness"
    )
    assert "not a run of RCMetaStudio.exe" in provenance["authority_scope"]
    assert "does not establish packaged executable, GUI, or human journey parity" in (
        provenance["authority_scope"]
    )

    cases = manifest["curated_golden_set"]
    assert manifest["passed"] is True
    assert manifest["capture_failures"] == []
    assert [case["id"] for case in cases] == list(CASE_IDS)
    for case in cases:
        assert case["status"] == "success"
        assert case["capture_mode"] == "local-debug"
        assert case["authoritative"] is False
        assert case["authority"] == "local-debug"
        assert case["commit_sha"] == SOURCE_COMMIT
        assert case["tool_versions"]["rc_metastudio"] == "0.3.1"
        assert case["package_versions"]["RCMetaR"] == "0.3.1"


def test_v031_comparison_accepts_only_the_reviewed_summary_presentation_changes():
    reference = json.loads((BASELINE_DIR / "manifest.json").read_bytes())
    current = _current_with_reviewed_presentation_changes(reference)
    original_current = deepcopy(current)

    report = compare_release_source_v031(current)

    assert report["passed"] is True
    assert report["comparison"]["passed"] is True
    assert all(row["classification"] == "pass" for row in report["comparison"]["rows"])
    assert {item["id"] for item in report["presentation_acceptances"]} == {
        "amino-binary-meta-regression",
        "continuous-meta-regression",
    }
    expected_label_changes = [
        ("Residual heterogeneity (t²)", "Residual heterogeneity (τ²)"),
        ("SE of t²", "SE of τ²"),
        ("Residual heterogeneity (t)", "Residual heterogeneity (τ)"),
    ]
    for acceptance in report["presentation_acceptances"]:
        label_changes = [
            (change["from"], change["to"])
            for change in acceptance["changes"]
            if change["kind"] == "heterogeneity-label"
        ]
        assert label_changes == expected_label_changes
        alignment_change = acceptance["changes"][-1]
        assert alignment_change == {
            "kind": "column-alignment-whitespace",
            "label": "Overall moderators (Qₘ)",
            "reference_separator_spaces": 7,
            "current_separator_spaces": 11,
            "numeric_suffix_unchanged": True,
        }
    assert current == original_current


def test_v031_comparison_still_rejects_changed_meta_regression_wording():
    reference = json.loads((BASELINE_DIR / "manifest.json").read_bytes())
    current = _current_with_reviewed_presentation_changes(reference)
    case = next(
        row
        for row in current["curated_golden_set"]
        if row["id"] == "amino-binary-meta-regression"
    )
    case["texts"]["Summary"] = case["texts"]["Summary"].replace(
        "Meta-Regression", "Meta-Analysis", 1
    )

    report = compare_release_source_v031(current)

    assert report["passed"] is False
    assert any(
        row["id"] == "amino-binary-meta-regression"
        and row["classification"] == TEXT_ARTIFACT_DRIFT
        for row in report["comparison"]["rows"]
    )


def test_v031_comparison_still_rejects_changed_numeric_results():
    reference = json.loads((BASELINE_DIR / "manifest.json").read_bytes())
    current = _current_with_reviewed_presentation_changes(reference)
    case = next(
        row
        for row in current["curated_golden_set"]
        if row["id"] == "continuous-meta-regression"
    )
    case["outputs"]["Summary"]["model.golden_year.coefficient"] += 0.01

    report = compare_release_source_v031(current)

    assert report["passed"] is False
    assert any(
        row["id"] == "continuous-meta-regression"
        and row["classification"] == NUMERIC_DRIFT
        and "Summary.model.golden_year.coefficient" in row["detail"]
        for row in report["comparison"]["rows"]
    )


def test_v031_comparison_rejects_method_identity_drift():
    reference = json.loads((BASELINE_DIR / "manifest.json").read_bytes())
    current = _current_with_reviewed_presentation_changes(reference)
    case = next(
        row
        for row in current["curated_golden_set"]
        if row["id"] == "amino-binary-meta-regression"
    )
    case["method"] = "binary.random"

    report = compare_release_source_v031(current)

    assert report["passed"] is False
    assert {
        "id": "amino-binary-meta-regression",
        "field": "method",
        "expected": "meta.regression",
        "actual": "binary.random",
    } in report["identity_drift"]


def test_v031_comparison_rejects_duplicate_current_case_ids():
    reference = json.loads((BASELINE_DIR / "manifest.json").read_bytes())
    current = _current_with_reviewed_presentation_changes(reference)
    current["curated_golden_set"].append(current["curated_golden_set"][0].copy())

    report = compare_release_source_v031(current)

    assert report["passed"] is False
    assert {
        "field": "case_ids",
        "duplicate_ids": ["amino-binary-random"],
    } in report["identity_drift"]


def _current_with_reviewed_presentation_changes(reference):
    current = deepcopy(reference)
    labels = (
        ("Residual heterogeneity (t²)", "Residual heterogeneity (τ²)"),
        ("SE of t²", "SE of τ²"),
        ("Residual heterogeneity (t)", "Residual heterogeneity (τ)"),
    )
    for case in current["curated_golden_set"]:
        if case["id"] not in {
            "amino-binary-meta-regression",
            "continuous-meta-regression",
        }:
            continue
        summary = case["texts"]["Summary"]
        for old_label, new_label in labels:
            assert summary.count(old_label) == 1
            summary = summary.replace(old_label, new_label, 1)
        old_row = " Overall moderators (Qₘ)" + " " * 7
        new_row = " Overall moderators (Qₘ)" + " " * 11
        assert summary.count(old_row) == 1
        case["texts"]["Summary"] = summary.replace(old_row, new_row, 1)
    return current
