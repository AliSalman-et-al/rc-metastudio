import argparse
import importlib.util
import json
import subprocess
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


@pytest.mark.parametrize("target", ["windows-x64", "linux-x64", "macos-arm64"])
def test_unsigned_qualification_carries_exact_candidate_and_evidence(tmp_path, target):
    delivery = load_delivery()
    commit = "a" * 40
    version = f"{delivery.repository_version()}-rc.1"
    candidate = tmp_path / "candidate"
    artifact = candidate / "artifacts" / delivery.candidate_artifact(delivery.targets()[target])
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"candidate archive bytes")
    record_path = candidate / "candidate" / f"{target}.assembled.json"
    manifest_path = record_path.with_name("release-set.json")
    delivery.init_release(argparse.Namespace(
        version=version, commit=commit, repository="example/rc-metastudio",
        trust_profile="unsigned-community", output=manifest_path,
    ))
    qualified = tmp_path / "qualified"
    tree = qualified / "tree"
    tree.mkdir(parents=True)
    (tree / "launcher").write_bytes(b"extracted application")
    assembled = subprocess.run(
        [sys.executable, str(ROOT / "scripts/delivery.py"), "record-assembled",
         "--target", target, "--archive", str(artifact), "--manifest", str(manifest_path),
         "--tree", str(tree)],
        check=False, capture_output=True, text=True,
    )
    assert assembled.returncode == 0, assembled.stderr
    command = [
        sys.executable, str(ROOT / "scripts/delivery.py"), "record-unsigned-qualification",
        "--target", target, "--commit", commit, "--version", version,
        "--candidate", str(candidate), "--qualified", str(qualified),
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (qualified / artifact.name).read_bytes() == artifact.read_bytes()
    records = qualified / "records"
    assert (records / record_path.name).read_bytes() == record_path.read_bytes()
    unsigned = delivery.load(records / f"{target}.unsigned-qualified.json")
    verified = delivery.load(records / f"{target}.verified.json")
    assert unsigned["input_digest"] == delivery.canonical_digest(delivery.load(record_path))
    assert verified["input_digest"] == delivery.canonical_digest(unsigned)
    assert {item["name"] for item in verified["outputs"]} == {
        artifact.name, f"{target}.inventory.json", f"{target}.cdx.json",
    }
    inventory = delivery.load(qualified / f"{target}.inventory.json")
    assert inventory["files"][0]["path"] == "launcher"
    assert delivery.load(qualified / f"{target}.cdx.json")["metadata"]["component"]["version"] == version
    prior_verified = (records / f"{target}.verified.json").read_bytes()
    artifact.write_bytes(b"changed archive")
    rejected = subprocess.run(command, check=False, capture_output=True, text=True)
    assert rejected.returncode == 2, rejected.stderr
    assert "archive does not match stage output" in rejected.stderr
    assert (records / f"{target}.verified.json").read_bytes() == prior_verified
    assert (qualified / artifact.name).read_bytes() == b"candidate archive bytes"


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
    assert manifest["release_targets"] == ["windows-x64", "macos-arm64", "linux-x64"]
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
    altered = delivery.load(manifest_path)
    policy_input = next(iter(altered["policy_inputs"]))
    altered["policy_inputs"][policy_input] = "0" * 64
    altered_path = tmp_path / "altered-policy.json"
    altered_path.write_text(json.dumps(altered), encoding="utf-8")
    with pytest.raises(ValueError, match="digest"):
        delivery.verify(argparse.Namespace(manifest=str(altered_path)))
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
