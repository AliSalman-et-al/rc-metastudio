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


def test_project_schema_runtime_probe_validates_migration_and_current_versions(
    monkeypatch,
):
    from rc_metastudio import automation, project_format

    calls = []
    load_schema = project_format._schema

    def observe_schema(version, member):
        calls.append((version, member))
        return load_schema(version, member)

    monkeypatch.setattr(project_format, "_schema", observe_schema)

    assert automation._project_schema_probe_record() == {
        "version": 2,
        "validated_members": ["manifest.json", "project.json", "state.json"],
    }
    assert calls == [
        (version, member)
        for version in (1, 2)
        for member in ("manifest.json", "project.json", "state.json")
    ]


def test_gui_test_support_project_schema_probe_validates_current_format(
    monkeypatch,
):
    from rc_metastudio import project_format
    from tests.python.gui.support import automation_scenarios

    calls = []
    load_schema = project_format._schema

    def observe_schema(version, member):
        calls.append((version, member))
        return load_schema(version, member)

    monkeypatch.setattr(project_format, "_schema", observe_schema)

    assert automation_scenarios._project_schema_probe_record() == {
        "version": project_format.CURRENT_FORMAT_VERSION,
        "validated_members": ["manifest.json", "project.json", "state.json"],
    }
    assert calls == [
        (version, member)
        for version in range(1, project_format.CURRENT_FORMAT_VERSION + 1)
        for member in ("manifest.json", "project.json", "state.json")
    ]


def test_pyinstaller_specs_bundle_each_project_schema_generation():
    specs = (
        "rc-metastudio.spec",
        "rc-metastudio-linux.spec",
        "rc-metastudio-macos.spec",
    )
    source_root = ROOT / "src" / "rc_metastudio" / "project_schemas"
    expected_members = {
        "manifest.schema.json",
        "project.schema.json",
        "state.schema.json",
    }

    for filename in specs:
        spec = (ROOT / "packaging" / "pyinstaller" / filename).read_text(
            encoding="utf-8"
        )
        assert 'project_schema_root = app_source / "project_schemas"' in spec
        assert 'project_schema_root.glob("v*")' in spec
        assert 'version_root.glob("*.schema.json")' in spec
        assert '"project_schemas" / version_root.name' in spec

    for version in ("v1", "v2"):
        assert {
            path.name for path in (source_root / version).glob("*.schema.json")
        } == expected_members


def test_ubuntu_package_evidence_rejects_outdated_project_schema_probe():
    build = (ROOT / "scripts" / "build-linux-package.sh").read_text(
        encoding="utf-8"
    )

    assert 'probe_data.get("schema_version") != 1' in build
    assert '"version": 2' in build
    assert '"validated_members": ["manifest.json", "project.json", "state.json"]' in build


def test_private_r_xml2_native_dependencies_are_bundled_and_resolved():
    build = (ROOT / "scripts" / "build-linux-package.sh").read_text(
        encoding="utf-8"
    )
    runtime_block = build.split("runtime_libraries=(", maxsplit=1)[1].split(")", maxsplit=1)[0]

    for soname in (
        "libxml2.so.2",
        "libicuuc.so.74",
        "libicui18n.so.74",
        "libicudata.so.74",
    ):
        assert soname in runtime_block
    assert 'check_bundled_dependency "$archive_root/R/library/xml2/libs/xml2.so" libxml2.so.2' in build
