import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from jsonschema import validate

from ._workflow import load_workflow


ROOT = Path(__file__).resolve().parents[3]


def load_delivery():
    path = ROOT / "scripts" / "delivery.py"
    spec = importlib.util.spec_from_file_location("delivery_contract_module", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def workflow_step(workflow, job_name: str, step_name: str):
    return next(
        step
        for step in workflow["jobs"][job_name]["steps"]
        if step.get("name") == step_name
    )


def test_candidate_requires_an_rc_version(tmp_path):
    delivery = load_delivery()

    with pytest.raises(ValueError, match="candidate version must be an RC version"):
        delivery.init_release(
            argparse.Namespace(
                version=delivery.repository_version(),
                commit="a" * 40,
                repository="AliSalman-et-al/rc-metastudio",
                trust_profile="macos-trusted",
                target=["windows-x64", "macos-arm64", "linux-x64"],
                output=str(tmp_path / "release-set.json"),
            )
        )


def test_clean_slate_delivery_state_machine(tmp_path):
    delivery = load_delivery()
    manifest_path = tmp_path / "release-set.json"
    commit = "a" * 40
    release_version = delivery.repository_version()
    rc_version = f"{release_version}-rc.1"
    delivery.init_release(
        argparse.Namespace(
            version=rc_version,
            commit=commit,
            repository="AliSalman-et-al/rc-metastudio",
            trust_profile="unsigned-community",
            target=["windows-x64", "macos-arm64", "linux-x64"],
            output=str(manifest_path),
        )
    )
    manifest = delivery.load(manifest_path)
    schema = json.loads(
        (ROOT / "delivery/release-set.schema.json").read_text(encoding="utf-8")
    )
    validate(instance=manifest, schema=schema)
    assert manifest["channel"] == "candidate"
    assert set(manifest["policy_inputs"]) == set(delivery.POLICY_INPUTS)
    assert "scripts/test-bounded-package-process.ps1" in delivery.POLICY_INPUTS
    assert "scripts/qt6_macos_feasibility.py" in delivery.POLICY_INPUTS
    assert "scripts/normalize_macos_macho.py" in delivery.POLICY_INPUTS
    assert "scripts/sign_macos_app.py" in delivery.POLICY_INPUTS
    assert "scripts/sign-notarize-macos-artifact.sh" in delivery.POLICY_INPUTS
    assert "scripts/package-linux.sh" in delivery.POLICY_INPUTS
    assert "scripts/build-linux-package.sh" in delivery.POLICY_INPUTS
    assert "scripts/install-r-deps-linux.R" in delivery.POLICY_INPUTS
    assert "packaging/pyinstaller/rc-metastudio-linux.spec" in delivery.POLICY_INPUTS
    assert "delivery/release-set.schema.json" in delivery.POLICY_INPUTS
    assert "delivery/stage-result.schema.json" in delivery.POLICY_INPUTS
    assert "config/macos-package-targets.json" in delivery.POLICY_INPUTS
    assert ".github/workflows/community-release-candidate.yml" in delivery.POLICY_INPUTS
    assert (
        ".github/workflows/macos-trusted-release-candidate.yml"
        in delivery.POLICY_INPUTS
    )
    assert manifest["release_targets"] == ["windows-x64", "macos-arm64", "linux-x64"]
    registry = json.loads((ROOT / "delivery/targets.json").read_text(encoding="utf-8"))
    assert registry["targets"]["linux-x64"] == {
        "runner": "ubuntu-24.04",
        "os": "linux",
        "architecture": "x86_64",
        "artifact": "RCMetaStudio-linux-x64.tar.gz",
        "signing_profile": "unsigned",
    }
    for target in manifest["release_targets"]:
        previous = delivery.release_identity_digest(manifest)
        for stage in delivery.required_stages(manifest, target):
            artifact = tmp_path / f"{target}-{stage}.bin"
            artifact.write_bytes(f"{target}:{stage}".encode())
            result = tmp_path / f"{target}-{stage}.json"
            delivery.stage_result(
                argparse.Namespace(
                    target=target,
                    stage=stage,
                    commit=commit,
                    input_digest=previous,
                    output_file=[str(artifact)],
                    result=str(result),
                )
            )
            delivery.attach(
                argparse.Namespace(manifest=str(manifest_path), result=str(result))
            )
            previous = delivery.canonical_digest(delivery.load(result))
    delivery.verify(argparse.Namespace(manifest=str(manifest_path)))
    rc_path = tmp_path / "release-set-rc.json"
    delivery.promote(
        argparse.Namespace(
            manifest=str(manifest_path),
            from_channel="candidate",
            channel="rc",
            version=None,
            output=str(rc_path),
        )
    )
    with pytest.raises(ValueError, match="requires the macos-trusted profile"):
        delivery.promote(
            argparse.Namespace(
                manifest=str(rc_path),
                from_channel="rc",
                channel="stable",
                version=release_version,
                output=str(tmp_path / "unsigned-stable.json"),
            )
        )

    trusted_manifest_path = tmp_path / "macos-trusted-release-set.json"
    delivery.init_release(
        argparse.Namespace(
            version=rc_version,
            commit=commit,
            repository="AliSalman-et-al/rc-metastudio",
            trust_profile="macos-trusted",
            target=["windows-x64", "macos-arm64", "linux-x64"],
            output=str(trusted_manifest_path),
        )
    )
    trusted_manifest = delivery.load(trusted_manifest_path)
    validate(instance=trusted_manifest, schema=schema)
    assert delivery.required_stages(trusted_manifest, "windows-x64") == [
        "assembled",
        "unsigned-qualified",
        "verified",
        "attested",
    ]
    assert delivery.required_stages(trusted_manifest, "macos-arm64") == [
        "assembled",
        "signed",
        "notarized",
        "verified",
        "attested",
    ]
    assert delivery.required_stages(trusted_manifest, "linux-x64") == [
        "assembled",
        "unsigned-qualified",
        "verified",
        "attested",
    ]
    for target in trusted_manifest["release_targets"]:
        previous = delivery.release_identity_digest(trusted_manifest)
        for stage in delivery.required_stages(trusted_manifest, target):
            artifact = tmp_path / f"trusted-{target}-{stage}.bin"
            artifact.write_bytes(f"trusted:{target}:{stage}".encode())
            result = tmp_path / f"trusted-{target}-{stage}.json"
            delivery.stage_result(
                argparse.Namespace(
                    target=target,
                    stage=stage,
                    commit=commit,
                    input_digest=previous,
                    output_file=[str(artifact)],
                    result=str(result),
                )
            )
            delivery.attach(
                argparse.Namespace(
                    manifest=str(trusted_manifest_path), result=str(result)
                )
            )
            previous = delivery.canonical_digest(delivery.load(result))
    delivery.verify(argparse.Namespace(manifest=str(trusted_manifest_path)))
    trusted_rc_path = tmp_path / "macos-trusted-release-set-rc.json"
    delivery.promote(
        argparse.Namespace(
            manifest=str(trusted_manifest_path),
            from_channel="candidate",
            channel="rc",
            version=None,
            output=str(trusted_rc_path),
        )
    )
    stable_path = tmp_path / "release-set-stable.json"
    delivery.promote(
        argparse.Namespace(
            manifest=str(trusted_rc_path),
            from_channel="rc",
            channel="stable",
            version=release_version,
            output=str(stable_path),
        )
    )
    stable = delivery.load(stable_path)
    assert stable["channel"] == "stable"
    assert stable["version"] == release_version
    assert stable["trust_profile"] == "macos-trusted"

    bad = json.loads(manifest_path.read_text(encoding="utf-8"))
    bad["targets"]["windows-x64"]["stages"].pop()
    bad_path = tmp_path / "bad.json"
    delivery.write(bad_path, bad)
    with pytest.raises(ValueError, match="incomplete or out-of-order"):
        delivery.verify(argparse.Namespace(manifest=str(bad_path)))


def test_release_workflows_have_immutable_structured_topology():
    candidate = load_workflow(".github/workflows/candidate.yml")
    community = load_workflow(".github/workflows/community-release-candidate.yml")
    trusted = load_workflow(".github/workflows/macos-trusted-release-candidate.yml")
    promote = load_workflow(".github/workflows/promote.yml")
    legacy = load_workflow(".github/workflows/package-verification.yml")

    assert candidate["permissions"] == {"contents": "read"}
    assert set(candidate["jobs"]) == {
        "initialize",
        "build",
        "qualify-macos-14",
        "qualify-ubuntu-26",
        "candidate-gate",
    }
    assert candidate["jobs"]["build"]["needs"] == "initialize"
    assert candidate["jobs"]["qualify-macos-14"]["needs"] == "build"
    assert candidate["jobs"]["qualify-ubuntu-26"]["needs"] == "build"
    assert candidate["jobs"]["candidate-gate"]["needs"] == [
        "build",
        "qualify-macos-14",
        "qualify-ubuntu-26",
    ]
    candidate_qualifications = [
        step
        for step in candidate["jobs"]["build"]["steps"]
        if str(step.get("name", "")).startswith("Qualify every route in the exact")
    ]
    assert len(candidate_qualifications) == 3
    assert all("--all-routes" in step["run"] for step in candidate_qualifications)
    assert {
        item["target"]
        for item in candidate["jobs"]["build"]["strategy"]["matrix"]["include"]
    } == {"windows-x64", "macos-arm64", "linux-x64"}

    assert community["permissions"] == {"contents": "read", "actions": "read"}
    assert {
        item["target"]
        for item in community["jobs"]["qualify"]["strategy"]["matrix"]["include"]
    } == {"windows-x64", "macos-arm64", "linux-x64"}
    assert {
        item["target"]
        for item in community["jobs"]["attest"]["strategy"]["matrix"]["include"]
    } == {"windows-x64", "macos-arm64", "linux-x64"}
    assert community["jobs"]["attest"]["needs"] == "qualify"
    assert community["jobs"]["attest"]["permissions"]["attestations"] == "write"
    assert community["jobs"]["publish-rc"]["needs"] == "attest"
    assert community["jobs"]["publish-rc"]["permissions"]["contents"] == "write"

    assert trusted["permissions"] == {"contents": "read", "actions": "read"}
    assert trusted["jobs"]["carry-windows"]["needs"] == "validate-candidate"
    assert trusted["jobs"]["sign-submit-macos"]["environment"] == "macos-signing"
    assert set(trusted["jobs"]["finalize-macos"]["needs"]) == {
        "validate-candidate",
        "sign-submit-macos",
    }
    assert set(trusted["jobs"]["attest"]["needs"]) == {
        "carry-windows",
        "carry-linux",
        "finalize-macos",
        "qualify-macos-14",
    }
    assert trusted["jobs"]["qualify-macos-14"]["needs"] == "finalize-macos"
    assert trusted["jobs"]["qualify-macos-14"]["runs-on"] == "macos-14"
    for job in ("finalize-macos", "qualify-macos-14"):
        assert any("--all-routes" in step.get("run", "") for step in trusted["jobs"][job]["steps"])
    assert trusted["jobs"]["carry-linux"]["runs-on"] == "ubuntu-24.04"
    linux_launch = workflow_step(
        trusted, "carry-linux", "Launch unchanged unsigned Linux bytes"
    )
    assert "LaunchRCMetaStudio.sh" in linux_launch["run"]
    assert "xvfb-run -a" in linux_launch["run"]
    assert {
        item["target"]
        for item in trusted["jobs"]["attest"]["strategy"]["matrix"]["include"]
    } == {"windows-x64", "macos-arm64", "linux-x64"}
    assert trusted["jobs"]["publish-rc"]["needs"] == "attest"

    assert promote["permissions"] == {"contents": "read"}
    assert promote["jobs"]["promote"]["environment"] == "production-release"
    assert promote["jobs"]["promote"]["permissions"] == {"contents": "write"}
    assert set(legacy["jobs"]) == {"windows-package", "macos-packages", "linux-package"}
    assert legacy["permissions"] == {"contents": "read"}

    verify_rc = workflow_step(
        promote, "promote", "Verify RC release set and exact asset digests"
    )
    assert "(cd promotion && sha256sum --check SHA256SUMS)" in verify_rc["run"]
    assert 'git fetch origin "refs/tags/$RC_TAG:refs/tags/$RC_TAG"' in verify_rc["run"]
    assert "RCMetaStudio-linux-x64.tar.gz" in verify_rc["run"]
    assert "linux-x64.cdx.json" in verify_rc["run"]

    publishers = (
        (
            community,
            "publish-rc",
            "Publish clearly labeled immutable unsigned RC",
            'test "$(git rev-list -n 1 "$TAG")" = "${{ inputs.source_sha }}"',
            'tag_args=(--target "${{ inputs.source_sha }}")',
        ),
        (
            trusted,
            "publish-rc",
            "Publish immutable macOS-trusted RC",
            'test "$(git rev-list -n 1 "$TAG")" = "${{ inputs.source_sha }}"',
            'tag_args=(--target "${{ inputs.source_sha }}")',
        ),
        (
            promote,
            "promote",
            "Publish stable release without rebuilding",
            'test "$(git rev-list -n 1 "$STABLE_TAG")" = "$source_sha"',
            'tag_args=(--target "$source_sha")',
        ),
    )
    for workflow, job_name, step_name, verified_target, targeted_tag in publishers:
        run = workflow_step(workflow, job_name, step_name)["run"]
        assert "gh release view" in run and "refusing overwrite" in run
        assert "git ls-remote --exit-code --tags origin" in run
        assert verified_target in run
        assert "tag_args=(--verify-tag)" in run
        assert targeted_tag in run
        assert '"${tag_args[@]}"' in run

    assert legacy["jobs"]["linux-package"]["uses"] == "./.github/workflows/package-linux.yml"
    for workflow, step_name in (
        (community, "Assemble unsigned community release set"),
        (trusted, "Assemble macOS-trusted release set"),
    ):
        run = workflow_step(workflow, "publish-rc", step_name)["run"]
        assert "RCMetaStudio-linux-x64.tar.gz" in run
        assert "linux-x64.cdx.json" in run

    sign = workflow_step(
        trusted, "sign-submit-macos", "Sign exact candidate app and submit it to Apple"
    )
    preserved = workflow_step(
        trusted, "sign-submit-macos", "Preserve exact signed bytes and submission ID"
    )
    finalize = workflow_step(
        trusted,
        "finalize-macos",
        "Wait for Apple, then staple and verify preserved bytes",
    )
    final_launch = workflow_step(
        trusted, "finalize-macos", "Launch final signed and stapled macOS bytes"
    )
    assert "--mode sign-and-submit" in sign["run"]
    assert (
        '(cd submitted && shasum -a 256 "$ARTIFACT" > "$ARTIFACT.sha256")'
        in sign["run"]
    )
    assert preserved["uses"].startswith("actions/upload-artifact@")
    assert preserved["with"] == {
        "name": "submitted-${{ matrix.target }}",
        "path": "submitted",
        "if-no-files-found": "error",
        "retention-days": 30,
        "compression-level": 0,
    }
    assert '(cd submitted && shasum -a 256 -c "$ARTIFACT.sha256")' in finalize["run"]
    assert "--mode finalize" in finalize["run"]
    assert '--input-archive "submitted/$ARTIFACT"' in finalize["run"]
    assert 'xcrun stapler validate "qualified/$ARTIFACT"' in final_launch["run"]
    assert "codesign --verify --verbose=4" in final_launch["run"]
    signer = (ROOT / "scripts/sign-notarize-macos-artifact.sh").read_text(
        encoding="utf-8"
    )
    assert "xcrun notarytool submit" in signer
    assert "xcrun notarytool wait" in signer
    assert "xcrun stapler staple" in signer
    assert "xcrun stapler validate" in signer


def test_notarization_status_workflow_uses_protected_credentials():
    workflow = load_workflow(".github/workflows/notarization-status.yml")
    job = workflow["jobs"]["status"]
    assert job["environment"] == "macos-signing"
    assert workflow["permissions"] == {"contents": "read"}
    query = next(
        step
        for step in job["steps"]
        if step.get("name") == "Query notarization history and status"
    )
    assert set(query["env"]) >= {
        "APPLE_ID",
        "APPLE_APP_SPECIFIC_PASSWORD",
        "APPLE_TEAM_ID",
    }
    assert query["env"]["APPLE_ID"] == "${{ secrets.APPLE_ID }}"
    assert (
        query["env"]["APPLE_APP_SPECIFIC_PASSWORD"]
        == "${{ secrets.APPLE_APP_SPECIFIC_PASSWORD }}"
    )
    assert query["env"]["APPLE_TEAM_ID"] == "${{ secrets.APPLE_TEAM_ID }}"
    assert "xcrun notarytool history" in query["run"]
    assert 'xcrun notarytool info "$SUBMISSION_ID"' in query["run"]
    assert "--output-format json" in query["run"]
    assert "submission_id must be a UUID" in query["run"]
