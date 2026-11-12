from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "resolve_macos_package_target", ROOT / "scripts/resolve_macos_package_target.py"
)
assert SPEC is not None and SPEC.loader is not None
TARGETS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TARGETS)


def test_target_manifest_rejects_silent_architecture_drift(tmp_path: Path):
    manifest = json.loads(
        (ROOT / "config/macos-package-targets.json").read_text(encoding="utf-8")
    )
    manifest["targets"]["arm64"]["delivery_target"] = "macos-x64"
    path = tmp_path / "targets.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(TARGETS.TargetError, match="does not match architecture"):
        TARGETS.load_target("arm64", path)


def test_arm64_framework_component_is_selected_by_its_real_package_identifier(
    tmp_path: Path,
):
    spec = importlib.util.spec_from_file_location(
        "resolve_macos_r_framework_component",
        ROOT / "scripts/resolve_macos_r_framework_component.py",
    )
    assert spec is not None and spec.loader is not None
    resolver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(resolver)
    component = tmp_path / "R-fw.pkg"
    framework = component / "Payload/R.framework"
    framework.mkdir(parents=True)
    (component / "PackageInfo").write_text(
        '<pkg-info identifier="org.R-project.R.fw.pkg" '
        'install-location="/Library/Frameworks" version="4.6.1"/>',
        encoding="utf-8",
    )

    assert (
        resolver.resolve_framework(tmp_path, "4.6.1", "org.R-project.R.fw.pkg")
        == framework.resolve()
    )


def test_arm64_launcher_adapter_rejects_intel_build_metadata(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "configure_macos_r_launchers",
        ROOT / "scripts/configure_macos_r_launchers.py",
    )
    assert spec is not None and spec.loader is not None
    launchers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launchers)

    bash = shutil.which("bash") or "C:/Program Files/Git/bin/bash.exe"
    if not Path(bash).is_file():
        pytest.skip("bash is required to execute the generated launcher")
    binary = tmp_path / "bin"
    binary.mkdir()
    (binary / "config").write_text(launchers.private_config("arm64"), newline="\n")
    upstream = binary / "config.real"
    upstream.write_text('#!/bin/sh\nprintf "%s\\n" "$UPSTREAM_FLAGS"\n', newline="\n")
    upstream.chmod(0o755)
    flags = (
        "-Wl,-headerpad_max_install_names -L/opt/R/arm64/lib "
        "-F/Library/Frameworks/R.framework/.. -framework R "
        "-lpcre2-8 -lbz2 -lz -licucore -ldl -lm -liconv"
    )
    environment = {**os.environ, "R_HOME": ".", "UPSTREAM_FLAGS": flags}
    accepted = subprocess.run(
        [bash, "bin/config", "--ldflags"], cwd=tmp_path, env=environment,
        text=True, capture_output=True, check=True,
    )
    assert accepted.stdout.strip() == (
        "-Wl,-headerpad_max_install_names -L./lib -lR "
        "-lbz2 -lz -licucore -ldl -lm -liconv"
    )
    environment["UPSTREAM_FLAGS"] = flags.replace("/arm64/", "/x86_64/")
    rejected = subprocess.run(
        [bash, "bin/config", "--ldflags"], cwd=tmp_path, env=environment,
        text=True, capture_output=True, check=False,
    )
    assert rejected.returncode != 0
    assert rejected.stdout == ""
    assert "Unexpected upstream" in rejected.stderr
