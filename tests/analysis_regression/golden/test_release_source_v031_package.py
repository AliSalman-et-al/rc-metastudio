from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

from scripts.capture_v031_package_reference import build_manifest
from scripts import capture_v031_package_reference as package_capture
from tests.analysis_regression.golden.support import release_source_v031_package as package_support
from tests.analysis_regression.golden.support.release_source_v031_package import (
    AUTHORITY_SCOPE,
    CAPTURE_KIND,
    RELEASE,
    VERSIONS,
    canonical_sha256,
    expected_effective_params,
    compare_package_manifests,
    _artifact_identity,
    load_case_specs,
    validate_package_manifest,
)


def _manifest(role):
    specs = load_case_specs()
    cases = []
    for spec in specs["cases"]:
        request = {
            name: spec[name]
            for name in ("family", "metric", "method", "workflow")
        }
        request["params"] = deepcopy(spec["params"])
        studies = list(spec["input"]["study_names"])
        returns_fit_order = spec["method"] not in {"diagnostic.reitsma", "small-study-effects"}
        availability = [
            {
                "method": name,
                "available": True,
                "reason": "",
                "role": "primary",
                "usable_studies": [{"state": "finite", "value": len(studies)}],
                "required_inputs": [],
                "warnings": [],
            }
            for name in spec["params"].get("tests", [])
        ]
        cases.append(
            {
                "id": spec["id"],
                "family": spec["family"],
                "metric": spec["metric"],
                "method": spec["method"],
                "workflow": spec["workflow"],
                "request": request,
                "effective_request": {
                    "family": spec["family"],
                    "method": spec["method"],
                    "workflow": spec["workflow"],
                    "params": expected_effective_params(spec),
                    "source": "small-study-call-arguments" if spec["method"] == "small-study-effects" else "rcmetar.request",
                },
                "input": deepcopy(spec["input"]),
                "input_sha256": canonical_sha256(spec["input"]),
                "request_sha256": canonical_sha256(request),
                "ordered_input_studies": studies,
                "eligibility": {
                    "ordered_input_studies": studies,
                    "fit_study_order": studies if returns_fit_order else None,
                    "api_returned_fit_order": returns_fit_order,
                    "usable_studies": len(studies),
                    "usable_count_matches_input": True,
                    "excluded_studies": [] if returns_fit_order else None,
                    "method_availability": availability,
                },
                "warnings": [],
                "outputs": _synthetic_outputs(spec),
                "artifacts": [
                    dict(item, sha256="1" * 64, size_bytes=100)
                    for item in _artifact_identity(spec["id"], spec)
                ],
            }
        )
    return {
        "schema_version": 1,
        "capture_kind": CAPTURE_KIND,
        "authority_scope": AUTHORITY_SCOPE,
        "capture_role": role,
        "release": RELEASE.copy(),
        "versions": VERSIONS.copy(),
        "environment": {
            "runner_os": "Windows",
            "runner_arch": "AMD64",
            "embedded_r_home_confirmed": True,
            "embedded_rcmetar_library_confirmed": True,
            "release_archive_sha256_verified": True,
        },
        "workflow": {
            "repository": "owner/repo",
            "workflow_ref": "owner/repo/.github/workflows/release-capability-reference.yml@refs/heads/test",
            "source_sha": "a" * 40,
            "run_id": "123",
            "run_attempt": "1",
            "run_url": "https://github.com/owner/repo/actions/runs/123",
        },
        "case_ids": specs["case_ids"],
        "cases": cases,
    }


def _synthetic_outputs(spec):
    if spec["method"] == "small-study-effects":
        return {
            "tests": {
                name: {"p.value": [{"state": "finite", "value": 0.25}]}
                for name in spec["params"]["tests"]
            },
            "methods_not_applicable": "",
            "warning_section": None,
            "test_summary": None,
            "reported_warning": None,
        }
    if spec["method"] == "diagnostic.reitsma":
        return {
            "summary": {
                "clinical_interpretation": "8 studies",
                "summary_operating_point": None,
                "sampling_based_summary_ratios": None,
                "sroc_auc": None,
                "marginal_prediction": None,
                "between_study_heterogeneity": None,
                "diagnostic_i_squared": None,
                "model_information": None,
            },
            "reported_warning": None,
        }
    return {
        "statistics": {
            "b": [{"state": "finite", "value": 0.25}],
            "se": [{"state": "finite", "value": 0.1}],
            "ci.lb": [{"state": "neg_inf"}],
            "ci.ub": [{"state": "pos_inf"}],
            "k": [{"state": "finite", "value": len(spec["input"]["study_names"])}],
            "study_labels": list(spec["input"]["study_names"]),
            "weights": [
                {"state": "finite", "value": 0.25}
                for _ in spec["input"]["study_names"]
            ],
        },
        "reported_warning": None,
    }


def test_package_reference_case_inventory_covers_the_intended_families():
    specs = load_case_specs()
    assert specs["case_ids"] == [case["id"] for case in specs["cases"]]
    assert {
        case["method"] for case in specs["cases"]
    } >= {
        "binary.fixed.inv.var",
        "binary.fixed.mh",
        "binary.fixed.peto",
        "continuous.fixed",
        "diagnostic.fixed.inv.var",
        "diagnostic.fixed.mh",
        "diagnostic.reitsma",
        "small-study-effects",
    }
    assert any(case["id"] == "binary-entered-or" for case in specs["cases"])
    assert any(case["id"] == "continuous-onearm-txmean" for case in specs["cases"])


def test_pinned_release_package_reference_and_figures_match_manifest_hashes():
    baseline_dir = package_support.CASE_SPEC_PATH.parent
    reference_path = baseline_dir / "manifest.json"
    manifest = json.loads(reference_path.read_text(encoding="utf-8"))

    validate_package_manifest(manifest)

    assert manifest["capture_role"] == "release-reference"
    assert manifest["workflow"]["run_id"] == "36706939728"
    assert manifest["release"]["asset_sha256"] == RELEASE["asset_sha256"]
    for case in manifest["cases"]:
        for artifact in case["artifacts"]:
            artifact_path = baseline_dir / artifact["relative_path"]
            content = artifact_path.read_bytes()
            assert len(content) == artifact["size_bytes"]
            assert hashlib.sha256(content).hexdigest() == artifact["sha256"]


def test_package_reference_spec_rejects_missing_required_field_with_optional_artifact(
    tmp_path, monkeypatch
):
    spec = load_case_specs()
    case = spec["cases"][10]
    case.pop("workflow")
    case["artifact"] = "sroc"
    spec_path = tmp_path / "cases.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    monkeypatch.setattr(package_support, "CASE_SPEC_PATH", spec_path)

    with pytest.raises(ValueError, match="missing a required field"):
        package_support.load_case_specs()


def test_release_reference_manifest_requires_verified_archive_root(tmp_path):
    with pytest.raises(ValueError, match="requires the verified archive root"):
        build_manifest(
            {"cases": [], "runtime": {}, "versions": {}},
            {"case_ids": [], "cases": []},
            "release-reference",
            tmp_path,
        )


def test_release_reference_rejects_modified_extracted_package_with_same_version(tmp_path, monkeypatch):
    archive_root_name = RELEASE["archive_internal_root"]
    app_root = tmp_path / archive_root_name
    files = {
        "RCMetaStudio.exe": b"application",
        "R/bin/Rscript.exe": b"runtime",
        "R/library/RCMetaR/DESCRIPTION": b"Package: RCMetaR\nVersion: 0.3.1\n",
        "R/library/RCMetaR/R/capture.R": b"original source",
    }
    archive = tmp_path / "release.zip"
    with ZipFile(archive, "w") as zip_file:
        for relative, content in files.items():
            zip_file.writestr("%s/%s" % (archive_root_name, relative), content)
            extracted_file = app_root / relative
            extracted_file.parent.mkdir(parents=True, exist_ok=True)
            extracted_file.write_bytes(content)
    monkeypatch.setitem(package_capture.RELEASE, "asset_sha256", package_capture.file_sha256(archive))
    args = SimpleNamespace(
        role="release-reference",
        archive=archive,
        archive_root=app_root,
        rscript=app_root / "R/bin/Rscript.exe",
        library=app_root / "R/library",
    )

    assert package_capture.verify_release_inputs(args) == app_root / "R"
    assert b"Version: 0.3.1" in (app_root / "R/library/RCMetaR/DESCRIPTION").read_bytes()
    (app_root / "R/library/RCMetaR/R/capture.R").write_bytes(b"modified source")

    with pytest.raises(ValueError, match="differs from pinned ZIP"):
        package_capture.verify_release_inputs(args)


def test_package_reference_comparison_accepts_matching_outputs_and_ignores_artifact_bytes():
    reference = _manifest("release-reference")
    candidate = _manifest("candidate-replay")
    descriptor = {
        "name": "SROC",
        "plot_kind": "sroc",
        "format": "png",
        "relative_path": "artifacts/diagnostic-reitsma-joint-sroc.png",
        "sha256": "1" * 64,
        "size_bytes": 100,
    }
    reference_case = reference["cases"][10]
    candidate_case = candidate["cases"][10]
    reference_case["artifacts"] = [descriptor]
    candidate_case["artifacts"] = [dict(descriptor, sha256="2" * 64, size_bytes=120)]

    report = compare_package_manifests(reference, candidate)

    assert report["passed"] is True
    assert report["artifact_content_hashes_compared"] is False
    assert all(row["passed"] for row in report["rows"])


def test_package_reference_schema_rejects_changed_input_even_with_new_identity_hash():
    reference = _manifest("release-reference")
    candidate = _manifest("candidate-replay")
    case = candidate["cases"][0]
    case["input"]["g1O1"][0] += 1
    case["input_sha256"] = canonical_sha256(case["input"])

    with pytest.raises(ValueError, match="primitive input does not match"):
        compare_package_manifests(reference, candidate)


def test_package_reference_comparison_rejects_unexplained_numeric_and_status_drift():
    reference = _manifest("release-reference")
    candidate = _manifest("candidate-replay")
    candidate["cases"][0]["outputs"]["statistics"]["b"][0]["value"] = 0.2501
    candidate["cases"][1]["outputs"]["statistics"]["ci.lb"][0] = {"state": "pos_inf"}
    candidate["cases"][2]["outputs"]["statistics"]["ci.lb"][0] = {"state": "finite", "value": 0}

    report = compare_package_manifests(reference, candidate)

    assert report["passed"] is False
    assert report["rows"][0]["differences"][0]["field"] == "outputs.statistics.b[0].value"
    assert any(
        diff["field"] == "outputs.statistics.ci.lb[0]"
        for diff in report["rows"][1]["differences"]
    )
    assert any(diff["field"] == "outputs.statistics.ci.lb[0]" for diff in report["rows"][2]["differences"])


def test_package_reference_comparison_rejects_study_weight_drift():
    reference = _manifest("release-reference")
    candidate = _manifest("candidate-replay")
    candidate["cases"][0]["outputs"]["statistics"]["weights"][0]["value"] = 0.5

    report = compare_package_manifests(reference, candidate)

    assert report["passed"] is False
    assert any(
        diff["field"] == "outputs.statistics.weights[0].value"
        for diff in report["rows"][0]["differences"]
    )


def test_package_reference_schema_rejects_incomplete_study_weights():
    manifest = _manifest("release-reference")
    manifest["cases"][0]["outputs"]["statistics"]["weights"].pop()

    with pytest.raises(ValueError, match="one study weight per fitted study"):
        validate_package_manifest(manifest)


def test_package_reference_comparison_rejects_artifact_descriptor_drift():
    reference = _manifest("release-reference")
    candidate = _manifest("candidate-replay")
    descriptor = {
        "name": "SROC",
        "plot_kind": "sroc",
        "format": "png",
        "relative_path": "artifacts/diagnostic-reitsma-joint-sroc.png",
        "sha256": "1" * 64,
        "size_bytes": 100,
    }
    reference["cases"][10]["artifacts"] = [descriptor]
    candidate["cases"][10]["artifacts"] = [dict(descriptor, plot_kind="forest")]

    with pytest.raises(ValueError, match="artifact inventory changed"):
        compare_package_manifests(reference, candidate)


def test_package_reference_schema_rejects_inferred_fit_order_and_unknown_numeric_states():
    manifest = _manifest("release-reference")
    eligibility = manifest["cases"][10]["eligibility"]
    eligibility["fit_study_order"] = ["invented"]
    with pytest.raises(ValueError, match="Do not infer fit order"):
        validate_package_manifest(manifest)

    manifest = _manifest("release-reference")
    manifest["cases"][0]["outputs"]["statistics"]["b"] = [{"state": "not-available"}]
    with pytest.raises(ValueError, match="unknown numeric state"):
        validate_package_manifest(manifest)
