from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

from scripts.capture_v031_package_reference import build_manifest
from scripts import capture_v031_package_reference as package_capture
from scripts.verify_v031_package_reference import read_manifest as read_package_manifest
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


PINNED_CASE_IDS_V1 = (
    "binary-fixed-iv-or",
    "binary-fixed-mh-or",
    "binary-fixed-peto-or",
    "binary-onearm-plo",
    "binary-entered-or",
    "continuous-fixed-md",
    "continuous-onearm-txmean",
    "continuous-entered-md",
    "diagnostic-fixed-iv-sens",
    "diagnostic-fixed-mh-plr",
    "diagnostic-reitsma-joint",
    "small-study-binary-or",
    "small-study-continuous-smd",
    "small-study-diagnostic-dor",
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
                "status": "success",
                **({"journey": deepcopy(spec["journey"])} if "journey" in spec else {}),
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
        "schema_version": 2,
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
        "historical_exe_smoke": None,
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
    outputs = {
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
    if "journey" in spec:
        outputs["statistics"]["I2"] = [{"state": "finite", "value": 42.0}]
        outputs["statistics"]["yi"] = [
            {"state": "finite", "value": 0.25}
            for _ in spec["input"]["study_names"]
        ]
        outputs["statistics"]["vi"] = [
            {"state": "finite", "value": 0.1}
            for _ in spec["input"]["study_names"]
        ]
    return outputs


def test_package_reference_case_inventory_covers_the_intended_families():
    specs = load_case_specs()
    assert specs["case_ids"] == [case["id"] for case in specs["cases"]]
    assert tuple(specs["case_ids"][: len(PINNED_CASE_IDS_V1)]) == PINNED_CASE_IDS_V1
    assert len(specs["case_ids"]) == 19
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


def test_route_package_cases_are_frozen_from_the_hashed_sample_projects():
    specs = load_case_specs()
    by_id = {case["id"]: case for case in specs["cases"]}
    expected_routes = {
        "journey-binary-standard": "binary.standard",
        "journey-continuous-standard": "continuous.standard",
        "journey-diagnostic-standard": "diagnostic.standard",
        "journey-binary-one-arm": "binary.one-arm",
        "journey-continuous-entered-effect": "continuous.entered-effect",
    }
    assert {
        case_id: by_id[case_id]["journey"]["route"] for case_id in expected_routes
    } == expected_routes
    assert by_id["journey-binary-standard"]["params"] == {
        "conf.level": 95,
        "digits": 2,
        "measure": "OR",
        "rm.method": "DL",
        "inference.method": "z",
        "adjust": 0.5,
        "to": "only0",
    }
    assert by_id["journey-binary-one-arm"]["params"] == {
        "conf.level": 95,
        "digits": 2,
        "measure": "PLO",
        "rm.method": "DL",
        "inference.method": "z",
        "adjust": 0.5,
        "to": "only0",
    }
    assert by_id["journey-diagnostic-standard"]["params"] == {
        "conf.level": 95,
        "digits": 2,
        "measure": "Sens",
        "rm.method": "DL",
        "inference.method": "z",
        "adjust": 0.5,
        "to": "only0",
    }
    for case_id in ("journey-continuous-standard", "journey-continuous-entered-effect"):
        assert by_id[case_id]["params"] == {
            "conf.level": 95,
            "digits": 2,
            "measure": "SMD",
            "rm.method": "DL",
            "inference.method": "z",
        }

    for case_id in expected_routes:
        case = by_id[case_id]
        journey = case["journey"]
        sample_path = package_support.REPOSITORY_ROOT / "sample_projects" / journey[
            "sample_project"
        ]
        sample_bytes = sample_path.read_bytes()
        assert hashlib.sha256(sample_bytes).hexdigest() == journey["sample_project_sha256"]
        with ZipFile(sample_path) as archive:
            dataset = json.loads(archive.read("project.json"))["dataset"]

        selected = []
        for study in dataset["studies"]:
            if not study.get("include", True) or study.get("manually_excluded", False):
                continue
            unit = next(
                (
                    unit
                    for unit in study["analysis_units"]
                    if unit["outcome"] == journey["selected_outcome"]
                    and unit["follow_up"] == journey["time_point"]
                ),
                None,
            )
            if unit is None:
                continue
            group_rows = {
                group["name"]: group["raw_data"] for group in unit["groups"]
            }
            groups = [group_rows[name] for name in journey["groups"]]
            if journey["input_representation"] == "entered-continuous-effect":
                entered = unit["entered_effects"]["SMD"]["tx A-tx B"]
                selected.append((study, entered))
            elif any(str(value).strip() for row in groups for value in row):
                selected.append((study, groups))

        actual = case["input"]
        assert actual["study_names"] == [study["name"] for study, _data in selected]
        assert actual["years"] == [study["year"] for study, _data in selected]
        representation = journey["input_representation"]
        if representation in {"two-arm-raw-binary-counts", "one-arm-raw-binary-counts"}:
            arms = [data for _study, data in selected]
            assert actual["g1O1"] == [row[0][0] for row in arms]
            assert actual["g1O2"] == [row[0][1] - row[0][0] for row in arms]
            if representation == "two-arm-raw-binary-counts":
                assert actual["g2O1"] == [row[1][0] for row in arms]
                assert actual["g2O2"] == [row[1][1] - row[1][0] for row in arms]
            else:
                assert actual["g2O1"] == actual["g2O2"] == []
        elif representation == "two-arm-raw-continuous-summary":
            arms = [data for _study, data in selected]
            for field, arm, index in (
                ("N1", 0, 0), ("mean1", 0, 1), ("sd1", 0, 2),
                ("N2", 1, 0), ("mean2", 1, 1), ("sd2", 1, 2),
            ):
                assert actual[field] == [row[arm][index] for row in arms]
        elif representation == "entered-continuous-effect":
            entered = [effect for _study, effect in selected]
            assert actual["y"] == [row["est"] for row in entered]
            assert actual["SE"] == [row["SE"] for row in entered]
        elif representation == "diagnostic-raw-counts-tp-fn-fp-tn":
            rows = [data[0] for _study, data in selected]
            assert actual["TP"] == [row[0] for row in rows]
            assert actual["FN"] == [row[1] for row in rows]
            assert actual["FP"] == [row[2] for row in rows]
            assert actual["TN"] == [row[3] for row in rows]
        else:
            pytest.fail("Unknown route input representation: %s" % representation)


def test_pinned_release_package_reference_and_figures_match_manifest_hashes():
    baseline_dir = package_support.CASE_SPEC_PATH.parent
    reference_path = baseline_dir / "manifest.json"
    manifest = read_package_manifest(reference_path)

    assert manifest["capture_role"] == "release-reference"
    assert manifest["workflow"]["run_id"] == "36706939728"
    assert manifest["release"]["asset_sha256"] == RELEASE["asset_sha256"]
    for case in manifest["cases"]:
        for artifact in case["artifacts"]:
            artifact_path = baseline_dir / artifact["relative_path"]
            content = artifact_path.read_bytes()
            assert len(content) == artifact["size_bytes"]
            assert hashlib.sha256(content).hexdigest() == artifact["sha256"]


def test_public_verifier_keeps_frozen_schema_v1_comparisons_and_rejects_new_inventory():
    reference_path = package_support.CASE_SPEC_PATH.parent / "manifest.json"
    reference = read_package_manifest(reference_path)
    old_candidate = deepcopy(reference)
    old_candidate["capture_role"] = "candidate-replay"

    report = compare_package_manifests(reference, old_candidate)
    assert report["passed"] is True
    assert len(report["rows"]) == len(PINNED_CASE_IDS_V1)

    expanded_candidate = _manifest("candidate-replay")
    with pytest.raises(ValueError, match="identical schema and case inventories"):
        compare_package_manifests(reference, expanded_candidate)


def test_schema_v1_frozen_case_identity_rejects_input_or_parameter_drift():
    specs = load_case_specs()
    specs["cases"][0]["params"]["digits"] += 1

    with pytest.raises(ValueError, match="inputs or parameters changed"):
        package_support._case_specs_for_manifest(1, specs)


def test_schema_v1_statistics_do_not_expand_with_journey_only_i2():
    manifest = read_package_manifest(
        package_support.CASE_SPEC_PATH.parent / "manifest.json"
    )
    manifest["cases"][0]["outputs"]["statistics"]["I2"] = [
        {"state": "finite", "value": 42.0}
    ]

    with pytest.raises(ValueError, match="unknown fields"):
        validate_package_manifest(manifest)


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


def _fake_exe_archive(tmp_path):
    app_root = tmp_path / RELEASE["archive_internal_root"]
    exe_bytes = b"published exe bytes"
    sample_bytes = (
        package_support.REPOSITORY_ROOT / "sample_projects" / "amino.rcms"
    ).read_bytes()
    archive_path = tmp_path / "published.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr(app_root.name + "/RCMetaStudio.exe", exe_bytes)
        archive.writestr(app_root.name + "/sample_projects/amino.rcms", sample_bytes)
    (app_root / "RCMetaStudio.exe").parent.mkdir(parents=True)
    (app_root / "RCMetaStudio.exe").write_bytes(exe_bytes)
    (app_root / "sample_projects").mkdir()
    (app_root / "sample_projects/amino.rcms").write_bytes(sample_bytes)
    return archive_path, app_root


def test_published_exe_smoke_records_as_is_success_and_raw_file_hashes(tmp_path, monkeypatch):
    archive, app_root = _fake_exe_archive(tmp_path)
    output_dir = tmp_path / "capture"
    output_dir.mkdir()
    monkeypatch.setitem(RELEASE, "asset_sha256", package_capture.file_sha256(archive))

    def run(command, *, cwd, env, capture_output, timeout, check):
        assert command[1:] == [
            "--automation-smoke",
            str(app_root / "sample_projects/amino.rcms"),
        ]
        assert cwd == str(app_root)
        assert capture_output is True and timeout == 900 and check is False
        evidence = {
            "schema_version": 1,
            "passed": True,
            "workflows": {
                "expected_normalized_summary_sha256": package_support.HISTORICAL_EXE_EXPECTED_SUMMARY_SHA256,
                "normalized_summary_sha256": package_support.HISTORICAL_EXE_EXPECTED_SUMMARY_SHA256,
            },
        }
        Path(env["RCMS_PACKAGE_SMOKE_EVIDENCE"]).write_text(json.dumps(evidence))
        Path(env["RCMS_AUTOMATION_SMOKE_LOG"]).write_text("packaged-workflow:return\n")
        return SimpleNamespace(returncode=0, stdout=b"passed", stderr=b"")

    monkeypatch.setattr(package_capture.subprocess, "run", run)
    smoke = package_capture.capture_historical_exe_smoke(archive, app_root, output_dir)

    assert smoke["status"] == "success"
    assert smoke["observed_normalized_summary_sha256"] == package_support.HISTORICAL_EXE_EXPECTED_SUMMARY_SHA256
    assert smoke["timeout_seconds"] == 900
    assert smoke["files"]["stdout"]["sha256"] == hashlib.sha256(b"passed").hexdigest()
    package_support._validate_historical_exe_smoke(smoke)

    smoke["command"] = [
        r"C:\runner\work\RCMetaStudio-0.3.1-windows-x64\RCMetaStudio.exe",
        "--automation-smoke",
        r"C:\runner\work\RCMetaStudio-0.3.1-windows-x64\sample_projects\amino.rcms",
    ]
    smoke["sample_project_sha256"] = package_capture.file_sha256(
        package_support.REPOSITORY_ROOT / "sample_projects" / "amino.rcms"
    )
    manifest = _manifest("release-reference")
    manifest["historical_exe_smoke"] = smoke
    validate_package_manifest(manifest)


def test_published_exe_smoke_retains_failure_and_summary_digest_mismatch(tmp_path, monkeypatch):
    archive, app_root = _fake_exe_archive(tmp_path)
    output_dir = tmp_path / "capture"
    output_dir.mkdir()
    observed = "a" * 64
    expected = package_support.HISTORICAL_EXE_EXPECTED_SUMMARY_SHA256
    monkeypatch.setitem(RELEASE, "asset_sha256", package_capture.file_sha256(archive))

    def run(_command, *, env, **_kwargs):
        Path(env["RCMS_AUTOMATION_SMOKE_LOG"]).write_text(
            "Packaged summary identity mismatch: %s != %s.\n" % (observed, expected)
        )
        return SimpleNamespace(returncode=1, stdout=b"", stderr=b"smoke failed")

    monkeypatch.setattr(package_capture.subprocess, "run", run)
    smoke = package_capture.capture_historical_exe_smoke(archive, app_root, output_dir)

    assert smoke["status"] == "failure"
    assert smoke["exit_code"] == 1
    assert smoke["observed_normalized_summary_sha256"] == observed
    assert smoke["files"]["automation_log"]["sha256"] == hashlib.sha256(
        (output_dir / smoke["files"]["automation_log"]["relative_path"]).read_bytes()
    ).hexdigest()
    package_support._validate_historical_exe_smoke(smoke)


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
