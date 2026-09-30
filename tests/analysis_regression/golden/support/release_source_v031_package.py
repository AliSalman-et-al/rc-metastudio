"""Strict comparison for the v0.3.1 RCMetaR package-API extension."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CASE_SPEC_PATH = (
    REPOSITORY_ROOT
    / "tests/analysis_regression/baseline/release-source-v031-package-api/cases.json"
)
RELEASE = {
    "tag": "v0.3.1",
    "source_commit": "f488ba0c01ec458b5e99fa2b5fc9b539872ae1ec",
    "asset_name": "RCMetaStudio-windows-x64.zip",
    "asset_url": "https://github.com/AliSalman-et-al/rc-metastudio/releases/download/v0.3.1/RCMetaStudio-windows-x64.zip",
    "archive_internal_root": "RCMetaStudio-0.3.1-windows-x64",
    "asset_sha256": "aeb6c9fdcbf00d8762284260ce3cdd7ffa722207d29599d1a428fa00ef30f7bd",
}
VERSIONS = {
    "R": "4.6.1",
    "RCMetaR": "0.3.1",
    "mada": "0.5.12",
    "metafor": "5.0-1",
    "meta": "8.5-0",
}
CAPTURE_KIND = "published-v031-embedded-rcmetar-package-api"
AUTHORITY_SCOPE = (
    "Direct calls to RCMetaR 0.3.1 in the SHA-256-pinned v0.3.1 Windows "
    "release archive's embedded R library. This is package API evidence, "
    "not the tagged-source app harness, RCMetaStudio.exe, a GUI journey, "
    "or human/platform parity evidence."
)
NUMERIC_ABSOLUTE_TOLERANCE = 1e-8
NUMERIC_RELATIVE_TOLERANCE = 1e-8
COMMON_FOREST_DEFAULTS = {
    "fp_col1_str": "Study or Subgroup",
    "fp_col2_str": "[default]",
    "fp_col3_str": "Intervention",
    "fp_col4_str": "Control",
    "fp_xlabel": "[default]",
    "fp_plot_lb": "[default]",
    "fp_plot_ub": "[default]",
    "fp_show_col1": True,
    "fp_show_col2": True,
    "fp_show_col3": True,
    "fp_show_col4": True,
    "fp_show_summary_line": True,
    "fp_xticks": "[default]",
    "supress.output": True,
    "write.to.file": False,
}


def load_case_specs():
    spec = json.loads(CASE_SPEC_PATH.read_text(encoding="utf-8"))
    if set(spec) != {"schema_version", "case_ids", "cases"} or spec["schema_version"] != 1:
        raise ValueError("Package-reference case specification schema mismatch.")
    ids = [case.get("id") for case in spec["cases"]]
    if ids != spec["case_ids"] or len(ids) != len(set(ids)):
        raise ValueError("Package-reference case IDs must be unique and ordered.")
    for case in spec["cases"]:
        if set(case) - {
            "id", "family", "metric", "method", "workflow", "input", "params", "artifact"
        }:
            raise ValueError("Package-reference case contains an unknown field.")
        if not {
            "id", "family", "metric", "method", "workflow", "input", "params"
        } <= set(case):
            raise ValueError("Package-reference case is missing a required field.")
        _validate_primitives(case, "case specification")
        names = case["input"].get("study_names")
        if not isinstance(names, list) or not names or any(not isinstance(x, str) for x in names):
            raise ValueError("Package-reference case has no ordered study names.")
    return spec


def canonical_sha256(value):
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def expected_effective_params(spec):
    params = dict(spec["params"])
    if spec["method"] not in {"diagnostic.reitsma", "small-study-effects"}:
        return COMMON_FOREST_DEFAULTS | params
    return params


def validate_package_manifest(manifest):
    required = {
        "schema_version",
        "capture_kind",
        "authority_scope",
        "capture_role",
        "release",
        "versions",
        "environment",
        "workflow",
        "case_ids",
        "cases",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise ValueError("Package-reference manifest fields do not match schema v1.")
    if manifest["schema_version"] != 1:
        raise ValueError("Unsupported package-reference manifest version.")
    if manifest["capture_kind"] != CAPTURE_KIND or manifest["authority_scope"] != AUTHORITY_SCOPE:
        raise ValueError("Package-reference evidence scope is incorrect.")
    if manifest["capture_role"] not in {"release-reference", "candidate-replay"}:
        raise ValueError("Unknown package-reference capture role.")
    if manifest["release"] != RELEASE:
        raise ValueError("Package-reference release identity does not match the pinned archive.")
    if manifest["capture_role"] == "release-reference" and manifest["versions"] != VERSIONS:
        raise ValueError("Release-reference package versions do not match v0.3.1 pins.")
    _validate_primitives(manifest, "manifest")
    environment = manifest["environment"]
    if not isinstance(environment, dict) or set(environment) != {
        "runner_os",
        "runner_arch",
        "embedded_r_home_confirmed",
        "embedded_rcmetar_library_confirmed",
        "release_archive_sha256_verified",
    }:
        raise ValueError("Package-reference environment fields changed.")
    flags = (
        "embedded_r_home_confirmed",
        "embedded_rcmetar_library_confirmed",
        "release_archive_sha256_verified",
    )
    if any(not isinstance(environment[key], bool) for key in flags):
        raise ValueError("Package-reference runtime confirmation flags must be booleans.")
    if manifest["capture_role"] == "release-reference" and not all(
        environment[key] for key in flags
    ):
        raise ValueError("Release-reference capture did not verify the published archive runtime.")
    workflow = manifest["workflow"]
    if not isinstance(workflow, dict) or set(workflow) != {
        "repository", "workflow_ref", "source_sha", "run_id", "run_attempt", "run_url"
    }:
        raise ValueError("Package-reference workflow provenance fields changed.")
    if any(value is not None and not isinstance(value, str) for value in workflow.values()):
        raise ValueError("Package-reference workflow provenance must be text or unavailable.")
    encoded_size = len(json.dumps(manifest, ensure_ascii=False, allow_nan=False).encode("utf-8"))
    if encoded_size > 2 * 1024 * 1024:
        raise ValueError("Package-reference manifest exceeds the 2 MiB bound.")

    specs = load_case_specs()
    expected_ids = specs["case_ids"]
    cases = manifest["cases"]
    if manifest["case_ids"] != expected_ids or not isinstance(cases, list):
        raise ValueError("Package-reference manifest case inventory changed.")
    if [case.get("id") for case in cases if isinstance(case, dict)] != expected_ids:
        raise ValueError("Package-reference cases are missing, duplicated, or out of order.")
    if len(cases) != len(expected_ids):
        raise ValueError("Package-reference manifest contains an unexpected case count.")

    for case, spec in zip(cases, specs["cases"]):
        _validate_case(case, spec)
    return True


def _validate_case(case, spec):
    expected = {
        "id",
        "family",
        "metric",
        "method",
        "workflow",
        "request",
        "effective_request",
        "input",
        "input_sha256",
        "request_sha256",
        "ordered_input_studies",
        "eligibility",
        "warnings",
        "outputs",
        "artifacts",
    }
    if not isinstance(case, dict) or set(case) != expected:
        raise ValueError("Package-reference case fields do not match schema v1.")
    for name in ("id", "family", "metric", "method", "workflow"):
        if case[name] != spec[name]:
            raise ValueError("Package-reference case identity changed: %s." % name)
    request = case["request"]
    if not isinstance(request, dict) or set(request) != {
        "family", "metric", "method", "workflow", "params"
    }:
        raise ValueError("Package-reference request fields do not match the allowlist.")
    expected_request = {name: spec[name] for name in ("family", "metric", "method", "workflow")}
    expected_request["params"] = spec["params"]
    if request != expected_request:
        raise ValueError("Package-reference request does not match the canonical case input.")
    if case["input"] != spec["input"]:
        raise ValueError("Package-reference primitive input does not match the canonical case.")
    if case["input_sha256"] != canonical_sha256(case["input"]):
        raise ValueError("Package-reference input identity hash is invalid.")
    if case["request_sha256"] != canonical_sha256(case["request"]):
        raise ValueError("Package-reference request identity hash is invalid.")
    if case["ordered_input_studies"] != spec["input"]["study_names"]:
        raise ValueError("Package-reference ordered input studies changed.")
    effective = case["effective_request"]
    if not isinstance(effective, dict) or set(effective) != {
        "family", "method", "workflow", "params", "source"
    }:
        raise ValueError("Package-reference normalized request fields changed.")
    if any(effective[key] != request[key] for key in ("family", "method", "workflow")):
        raise ValueError("Package-reference effective request identity changed.")
    if effective["params"] != expected_effective_params(spec):
        raise ValueError("Package-reference effective parameters changed.")
    expected_source = "small-study-call-arguments" if spec["method"] == "small-study-effects" else "rcmetar.request"
    if effective["source"] != expected_source:
        raise ValueError("Package-reference effective request source is unknown.")
    _validate_primitives(case, "case")
    _validate_eligibility(case["eligibility"], spec)
    if not isinstance(case["warnings"], list) or any(
        not isinstance(item, str) for item in case["warnings"]
    ):
        raise ValueError("Package-reference warnings must be an ordered string list.")
    if not isinstance(case["outputs"], dict):
        raise ValueError("Package-reference scientific output must be a JSON object.")
    _validate_outputs(case["id"], case["outputs"], spec)
    _validate_artifacts(case["artifacts"])
    if _artifact_identity(case["id"], spec) != [
        {key: item[key] for key in ("name", "plot_kind", "format", "relative_path")}
        for item in case["artifacts"]
    ]:
        raise ValueError("Package-reference artifact inventory changed.")


def _validate_eligibility(eligibility, spec):
    required = {
        "ordered_input_studies",
        "fit_study_order",
        "api_returned_fit_order",
        "usable_studies",
        "usable_count_matches_input",
        "excluded_studies",
        "method_availability",
    }
    if not isinstance(eligibility, dict) or set(eligibility) != required:
        raise ValueError("Package-reference eligibility fields do not match schema v1.")
    if eligibility["ordered_input_studies"] != spec["input"]["study_names"]:
        raise ValueError("Package-reference eligibility input order changed.")
    if not isinstance(eligibility["usable_studies"], int) or eligibility["usable_studies"] < 0:
        raise ValueError("Package-reference usable-study count is invalid.")
    if not isinstance(eligibility["usable_count_matches_input"], bool):
        raise ValueError("Package-reference usable-count equality flag is invalid.")
    if eligibility["usable_count_matches_input"] != (
        eligibility["usable_studies"] == len(spec["input"]["study_names"])
    ):
        raise ValueError("Package-reference usable-count equality does not match its inputs.")
    if not eligibility["usable_count_matches_input"]:
        raise ValueError("A canonical package-reference case did not use every ordered input study.")
    if eligibility["api_returned_fit_order"] is True:
        if not isinstance(eligibility["fit_study_order"], list):
            raise ValueError("The reported fit order is missing.")
        if eligibility["fit_study_order"] != spec["input"]["study_names"]:
            raise ValueError("Returned fit-study order does not match the canonical input order.")
        if eligibility["excluded_studies"] != []:
            raise ValueError("All canonical standard-analysis studies are expected to remain eligible.")
    elif eligibility["fit_study_order"] is not None:
        raise ValueError("Do not infer fit order when the package API did not return it.")
    if eligibility["excluded_studies"] is not None and not isinstance(
        eligibility["excluded_studies"], list
    ):
        raise ValueError("Excluded studies must be a list or unavailable.")
    if not isinstance(eligibility["method_availability"], list):
        raise ValueError("Package-reference method availability must be a list.")
    for item in eligibility["method_availability"]:
        if not isinstance(item, dict) or set(item) != {
            "method", "available", "reason", "role", "usable_studies", "required_inputs", "warnings"
        }:
            raise ValueError("Package-reference method-availability fields changed.")
        if not isinstance(item["method"], str) or not isinstance(item["available"], bool):
            raise ValueError("Package-reference method-availability identity is invalid.")
        if not isinstance(item["reason"], str) or not isinstance(item["role"], str):
            raise ValueError("Package-reference method-availability detail is invalid.")
        if not isinstance(item["usable_studies"], list) or any(
            not isinstance(count, dict) for count in item["usable_studies"]
        ):
            raise ValueError("Package-reference method-availability count is invalid.")
        if item["required_inputs"] is not None and not isinstance(item["required_inputs"], list):
            raise ValueError("Package-reference method required-inputs field is invalid.")
        if item["warnings"] is not None and not isinstance(item["warnings"], list):
            raise ValueError("Package-reference method warnings field is invalid.")
    if spec["method"] == "small-study-effects":
        available = {
            item["method"]: item["available"]
            for item in eligibility["method_availability"]
        }
        if any(not available.get(method, False) for method in spec["params"]["tests"]):
            raise ValueError("A requested small-study method was not returned as available.")


def _validate_artifacts(artifacts):
    if not isinstance(artifacts, list):
        raise ValueError("Package-reference artifacts must be an ordered list.")
    for item in artifacts:
        if not isinstance(item, dict) or set(item) != {
            "name", "plot_kind", "format", "relative_path", "sha256", "size_bytes"
        }:
            raise ValueError("Package-reference artifact descriptor fields changed.")
        path = item["relative_path"]
        if not isinstance(path, str) or path.startswith(("/", "\\")) or ".." in Path(path).parts:
            raise ValueError("Package-reference artifact path must be relative and contained.")
        if not isinstance(item["sha256"], str) or len(item["sha256"]) != 64:
            raise ValueError("Package-reference artifact hash is invalid.")
        if not isinstance(item["size_bytes"], int) or item["size_bytes"] <= 0:
            raise ValueError("Package-reference artifact size is invalid.")
        if not all(isinstance(item[key], str) and item[key] for key in ("name", "plot_kind", "format")):
            raise ValueError("Package-reference artifact identity is incomplete.")


def _validate_outputs(case_id, outputs, spec):
    if case_id.startswith("small-study-"):
        if set(outputs) != {
            "tests", "methods_not_applicable", "warning_section", "test_summary", "reported_warning"
        }:
            raise ValueError("Small-study output fields changed.")
        if not isinstance(outputs["tests"], dict) or not isinstance(outputs["methods_not_applicable"], str):
            raise ValueError("Small-study output structure is invalid.")
        if list(outputs["tests"]) != spec["params"]["tests"]:
            raise ValueError("Small-study returned test order does not match the request.")
        for name in ("warning_section", "test_summary", "reported_warning"):
            if outputs[name] is not None and not isinstance(outputs[name], str):
                raise ValueError("Small-study returned warning or summary text is invalid.")
        test_fields = {
            "method", "role", "package", "package.version", "call", "predictor", "weighting",
            "inference", "model", "usable.studies", "df", "p.value", "statistic", "coefficient",
            "standard.error", "confidence.interval", "intercept", "se.intercept",
            "confidence.interval.intercept", "prepared.effects", "prepared.standard.errors",
            "effective.sample.size", "deeks.predictor", "deeks.weights", "routing.effects",
            "routing.standard.errors",
        }
        for test in outputs["tests"].values():
            if not isinstance(test, dict) or set(test) - test_fields:
                raise ValueError("Small-study test output contains unknown fields.")
        return

    if case_id == "diagnostic-reitsma-joint":
        if set(outputs) != {"summary", "reported_warning"}:
            raise ValueError("Reitsma output fields changed.")
        sections = {
            "clinical_interpretation", "summary_operating_point", "sampling_based_summary_ratios",
            "sroc_auc", "marginal_prediction", "between_study_heterogeneity",
            "diagnostic_i_squared", "model_information",
        }
        if not isinstance(outputs["summary"], dict) or set(outputs["summary"]) != sections:
            raise ValueError("Reitsma summary must retain every known returned section, including unavailable values.")
        if outputs["reported_warning"] is not None and not isinstance(outputs["reported_warning"], str):
            raise ValueError("Reitsma warning text is invalid.")
        return

    if set(outputs) != {"statistics", "reported_warning"}:
        raise ValueError("Analysis output fields changed.")
    statistic_fields = {
        "b", "se", "ci.lb", "ci.ub", "zval", "pval", "tau2", "QE", "QEp", "df", "k",
        "yi", "vi", "study_labels", "weights",
    }
    if not isinstance(outputs["statistics"], dict) or set(outputs["statistics"]) - statistic_fields:
        raise ValueError("Analysis statistics contain unknown fields.")
    if not {"b", "se", "ci.lb", "ci.ub", "k"}.issubset(outputs["statistics"]):
        raise ValueError("Analysis fit is missing essential returned statistics.")
    if outputs["reported_warning"] is not None and not isinstance(outputs["reported_warning"], str):
        raise ValueError("Analysis warning text is invalid.")


def _artifact_identity(case_id, spec):
    kind = spec.get("artifact")
    if kind is None:
        return []
    if kind == "sroc":
        name, plot_kind, suffix = "SROC", "sroc", "sroc"
    elif case_id == "small-study-diagnostic-dor":
        name, plot_kind, suffix = (
            "Deeks Effective-Sample-Size Funnel Plot",
            "deeks_funnel",
            "deeks-funnel",
        )
    else:
        name, plot_kind, suffix = "Ordinary Funnel Plot", "funnel", "ordinary-funnel"
    return [
        {
            "name": name,
            "plot_kind": plot_kind,
            "format": "png",
            "relative_path": "artifacts/%s-%s.png" % (case_id, suffix),
        }
    ]


def compare_package_manifests(reference, candidate):
    validate_package_manifest(reference)
    validate_package_manifest(candidate)
    if reference["capture_role"] != "release-reference":
        raise ValueError("First manifest must be the published release reference.")
    if candidate["capture_role"] != "candidate-replay":
        raise ValueError("Second manifest must be a current-package replay.")

    rows = []
    for expected, actual in zip(reference["cases"], candidate["cases"]):
        case_id = expected["id"]
        differences = []
        for key in (
            "request_sha256",
            "input_sha256",
            "effective_request",
            "ordered_input_studies",
            "eligibility",
            "warnings",
        ):
            if expected[key] != actual[key]:
                differences.append({"field": key, "expected": expected[key], "actual": actual[key]})
        output_differences = []
        _compare_value(
            expected["outputs"],
            actual["outputs"],
            "outputs",
            output_differences,
        )
        differences.extend(output_differences)
        artifact_drift = _compare_artifacts(expected["artifacts"], actual["artifacts"])
        differences.extend(artifact_drift)
        rows.append({"id": case_id, "passed": not differences, "differences": differences})

    return {
        "mode": "published-v031-package-api-comparison",
        "passed": all(row["passed"] for row in rows),
        "numeric_tolerance": {
            "absolute": NUMERIC_ABSOLUTE_TOLERANCE,
            "relative": NUMERIC_RELATIVE_TOLERANCE,
        },
        "artifact_content_hashes_compared": False,
        "rows": rows,
    }


def _compare_artifacts(expected, actual):
    identity = lambda item: {
        key: item[key] for key in ("name", "plot_kind", "format", "relative_path")
    }
    expected_ids = [identity(item) for item in expected]
    actual_ids = [identity(item) for item in actual]
    if expected_ids == actual_ids:
        return []
    return [{"field": "artifacts", "expected": expected_ids, "actual": actual_ids}]


def _compare_value(expected, actual, path, differences):
    if isinstance(expected, dict) and isinstance(actual, dict):
        if set(expected) != set(actual):
            differences.append({"field": path, "expected_keys": sorted(expected), "actual_keys": sorted(actual)})
            return
        if set(expected) == {"state"} | ({"value"} if expected.get("state") == "finite" else set()):
            _compare_numeric_state(expected, actual, path, differences)
            return
        for key in sorted(expected):
            _compare_value(expected[key], actual[key], "%s.%s" % (path, key), differences)
        return
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            differences.append({"field": path, "expected_length": len(expected), "actual_length": len(actual)})
            return
        for index, (left, right) in enumerate(zip(expected, actual)):
            _compare_value(left, right, "%s[%d]" % (path, index), differences)
        return
    if type(expected) in (int, float) and type(actual) in (int, float):
        if not math.isfinite(expected) or not math.isfinite(actual):
            differences.append({"field": path, "expected": expected, "actual": actual})
            return
        tolerance = max(
            NUMERIC_ABSOLUTE_TOLERANCE,
            NUMERIC_RELATIVE_TOLERANCE * abs(expected),
        )
        if abs(expected - actual) > tolerance:
            differences.append({"field": path, "expected": expected, "actual": actual, "tolerance": tolerance})
        return
    if type(expected) is not type(actual) or expected != actual:
        differences.append({"field": path, "expected": expected, "actual": actual})


def _compare_numeric_state(expected, actual, path, differences):
    allowed_states = {"finite", "na", "nan", "pos_inf", "neg_inf"}
    state = expected.get("state")
    if state not in allowed_states or actual.get("state") not in allowed_states:
        differences.append({"field": path, "expected": expected, "actual": actual})
        return
    if state != actual["state"]:
        differences.append({"field": path, "expected": expected, "actual": actual})
        return
    if state == "finite":
        _compare_value(expected["value"], actual["value"], path + ".value", differences)


def _validate_primitives(value, label):
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("%s contains a non-finite raw JSON number." % label)
        return
    if isinstance(value, list):
        for item in value:
            _validate_primitives(item, label)
        return
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("%s contains a non-string object key." % label)
        if "state" in value:
            state = value["state"]
            if state not in {"finite", "na", "nan", "pos_inf", "neg_inf"}:
                raise ValueError("%s contains an unknown numeric state." % label)
            expected_keys = {"state", "value"} if state == "finite" else {"state"}
            if set(value) != expected_keys:
                raise ValueError("%s contains a malformed numeric state." % label)
            if state == "finite":
                raw = value["value"]
                if type(raw) not in (int, float) or not math.isfinite(raw):
                    raise ValueError("Finite numeric state must contain a finite number.")
            return
        for item in value.values():
            _validate_primitives(item, label)
        return
    raise ValueError("%s contains a non-JSON primitive." % label)
