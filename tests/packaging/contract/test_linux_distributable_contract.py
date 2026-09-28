from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
POLICY_SPEC = importlib.util.spec_from_file_location(
    "r_dependency_policy", ROOT / "scripts" / "r_dependency_policy.py"
)
assert POLICY_SPEC is not None and POLICY_SPEC.loader is not None
POLICY = importlib.util.module_from_spec(POLICY_SPEC)
POLICY_SPEC.loader.exec_module(POLICY)


def test_linux_policy_rejects_a_linux_source_fallback(tmp_path):
    manifest_path = ROOT / "config" / "r-dependencies.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["binary_package_policy"]["linux_binary"]["source_fallback"] = True
    changed_manifest = tmp_path / "r-dependencies.json"
    changed_manifest.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(POLICY.PolicyError, match="Linux binaries must use"):
        POLICY.load_policy(changed_manifest)


def test_linux_policy_emits_binary_only_noble_installer_configuration():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "r_dependency_policy.py"),
            "--manifest",
            str(ROOT / "config" / "r-dependencies.json"),
            "--emit-dcf",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    fields = {
        line.split(": ", maxsplit=1)[0]: line.split(": ", maxsplit=1)[1]
        for line in result.stdout.splitlines()
    }

    assert fields["Linux-Binary-Repository"].endswith("/__linux__/noble/2026-07-16")
    assert fields["Linux-Binary-R-Install-Type"] == "source"
    assert fields["Linux-Binary-Package-Type"] == "binary"
    assert fields["Linux-Binary-Tag"] == "4.6-noble"
    assert fields["Linux-Binary-Source-Fallback"] == "false"
    assert "meta=8.5-0" in fields["Pinned-Authorities"].split(",")
