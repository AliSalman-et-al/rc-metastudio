import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from jsonschema import validate


ROOT = Path(__file__).resolve().parents[3]


def load_delivery():
    path = ROOT / "scripts" / "delivery.py"
    spec = importlib.util.spec_from_file_location("delivery_contract_module", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
