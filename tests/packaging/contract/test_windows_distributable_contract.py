import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]


def _load_source_provenance():
    spec = importlib.util.spec_from_file_location(
        "source_provenance", ROOT / "scripts" / "source_provenance.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_package_metadata_version_only_needs_no_ambient_rscript(tmp_path):
    output = tmp_path / "github-output.txt"
    env = {**os.environ, "GITHUB_OUTPUT": str(output), "PATH": ""}
    script = ROOT / "scripts" / "resolve_package_ci_metadata.py"
    version_only = subprocess.run(
        [sys.executable, str(script), "--version-only"],
        env=env,
        text=True,
        capture_output=True,
    )
    assert version_only.returncode == 0, version_only.stderr
    project_version = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["version"]
    assert output.read_text(encoding="utf-8") == f"version={project_version}\n"
    default = subprocess.run(
        [sys.executable, str(script)], env=env, text=True, capture_output=True
    )
    assert default.returncode != 0
    assert "Rscript is not available on PATH." in default.stderr


def _load_windows_deployment_inspector():
    import importlib.util

    path = ROOT / "scripts" / "inspect_windows_deployment.py"
    spec = importlib.util.spec_from_file_location("inspect_windows_deployment", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_pe(path, machine=0x8664):
    import struct

    payload = bytearray(512)
    payload[0:2] = b"MZ"
    payload[0x3C:0x40] = struct.pack("<I", 0x80)
    payload[0x80:0x84] = b"PE\0\0"
    payload[0x84:0x98] = struct.pack("<HHIIIHH", machine, 0, 0, 0, 0, 0xF0, 0x2022)
    optional = 0x98
    payload[optional : optional + 2] = struct.pack("<H", 0x20B)
    payload[optional + 24 : optional + 32] = struct.pack("<Q", 0x140000000)
    payload[optional + 32 : optional + 40] = struct.pack("<II", 0x1000, 0x200)
    payload[optional + 56 : optional + 64] = struct.pack("<II", 0x1000, 0x200)
    payload[optional + 68 : optional + 70] = struct.pack("<H", 3)
    payload[optional + 108 : optional + 112] = struct.pack("<I", 16)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def test_frozen_windows_bootstrap_indexes_all_private_native_directories(tmp_path):
    from rc_metastudio import r_runtime

    r_home = tmp_path / "R"
    expected = {
        r_home / "bin" / "x64",
        r_home / "library" / "xml2" / "libs" / "x64",
    }
    for directory in expected:
        directory.mkdir(parents=True)
        (directory / "private.dll").write_bytes(b"dll")
    (r_home / "library" / "docs").mkdir(parents=True)
    (r_home / "library" / "docs" / "readme.txt").write_text("not native")

    observed = {
        Path(path) for path in r_runtime._private_windows_dll_directories(r_home)
    }
    assert observed == {path.resolve() for path in expected}


def test_frozen_direct_runtime_probe_validates_private_r_without_a_kit(
    monkeypatch, tmp_path
):
    from tests.python.gui.support import automation_scenarios as automation

    app = tmp_path / "RCMetaStudio"
    executable = app / "RCMetaStudio.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"exe")
    api_bridge = app / "_internal" / "_rinterface_cffi_api.pyd"
    api_bridge.parent.mkdir()
    api_bridge.write_bytes(b"api")
    r_home = app / "R"
    r_dll = r_home / "bin" / "x64" / "R.dll"
    r_dll.parent.mkdir(parents=True)
    r_dll.write_bytes(b"R")

    monkeypatch.setattr(automation.sys, "executable", str(executable))
    shared_library, direct_spike = automation._verified_frozen_runtime_shared_library(
        {"R_HOME": str(r_home), "derivation": {}, "direct_spike": False},
        api_bridge.resolve(),
    )

    assert shared_library == r_dll.resolve()
    assert direct_spike is False


def test_frozen_windows_runtime_bootstraps_without_a_kit(monkeypatch, tmp_path):
    from rc_metastudio import r_runtime

    app = tmp_path / "RCMetaStudio"
    r_home = app / "R"
    (r_home / "bin").mkdir(parents=True)
    (r_home / "library" / "RCMetaR").mkdir(parents=True)
    monkeypatch.setattr(r_runtime.sys, "frozen", True, raising=False)
    monkeypatch.setattr(r_runtime.sys, "platform", "win32")
    monkeypatch.setattr(r_runtime, "_RUNTIME_IDENTITY", None)
    monkeypatch.setattr(r_runtime, "_BOOTSTRAP_THREAD_ID", None)
    monkeypatch.setattr(
        r_runtime,
        "_frozen_kit_identity",
        lambda _root: pytest.fail("Windows native packages must not read a kit"),
    )
    monkeypatch.setattr(
        r_runtime, "_configure_private_runtime_directories", lambda _root: None
    )
    monkeypatch.setattr(r_runtime, "_set_windows_dll_policy", lambda: None)
    monkeypatch.setattr(r_runtime, "_prepend_path", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(r_runtime, "_add_dll_directories", lambda *_args: None)
    monkeypatch.setattr(r_runtime.os, "environ", dict(r_runtime.os.environ))

    configured = r_runtime.configure_bundled_r_environment(str(app))

    assert Path(configured["R_HOME"]).resolve() == r_home.resolve()
    assert configured["kit_sha256"] is None
    assert configured["derivation"] is None


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows ctypes APIs")
def test_windows_dll_policy_fails_closed(monkeypatch):
    from rc_metastudio import r_runtime

    class Kernel32:
        @staticmethod
        def SetDefaultDllDirectories(_policy):
            return 0

    monkeypatch.setattr(r_runtime.sys, "platform", "win32")
    monkeypatch.setattr(
        r_runtime.ctypes, "WinDLL", lambda *_args, **_kwargs: Kernel32()
    )
    monkeypatch.setattr(r_runtime.ctypes, "get_last_error", lambda: 5)
    with pytest.raises(OSError, match="SetDefaultDllDirectories failed"):
        r_runtime._set_windows_dll_policy()


def _windows_deployment_fixture(tmp_path):
    app = tmp_path / "RCMetaStudio"
    qt = app / "_internal" / "PyQt6" / "Qt6"
    _write_pe(app / "RCMetaStudio.exe")
    api_bridge = app / "_internal" / "_rinterface_cffi_api.cp311-win_amd64.pyd"
    _write_pe(api_bridge)
    r_dll = app / "R" / "bin" / "x64" / "R.dll"
    _write_pe(r_dll)
    rcmetar = app / "R" / "library" / "RCMetaR" / "DESCRIPTION"
    rcmetar.parent.mkdir(parents=True)
    rcmetar.write_text("Package: RCMetaR\nVersion: 0.1.1\n", encoding="utf-8")
    kit_root = app / "r-integration-kit"
    kit_root.mkdir(parents=True)
    api_sha256 = hashlib.sha256(api_bridge.read_bytes()).hexdigest()
    r_sha256 = hashlib.sha256(r_dll.read_bytes()).hexdigest()
    (kit_root / "manifest.json").write_text(
        json.dumps(
            {
                "kind": "rc-metastudio-r-integration-kit",
                "target": "windows-x64",
                "architecture": "x86_64",
                "cffi_mode": "API",
                "kit_sha256": "a" * 64,
                "files": [
                    {
                        "path": "bridge/_rinterface_cffi_api.cp311-win_amd64.pyd",
                        "kind": "file",
                        "sha256": api_sha256,
                    },
                    {
                        "path": "runtime/bin/x64/R.dll",
                        "kind": "file",
                        "sha256": r_sha256,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (kit_root / "derivation.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "target": "windows-x64",
                "kit_sha256": "a" * 64,
                "source": {
                    "api_bridge": {
                        "path": "bridge/_rinterface_cffi_api.cp311-win_amd64.pyd",
                        "sha256": api_sha256,
                    },
                    "r_shared_library": {
                        "path": "runtime/bin/x64/R.dll",
                        "sha256": r_sha256,
                    },
                },
                "pre_sign": {
                    "api_bridge": {
                        "path": api_bridge.relative_to(app).as_posix(),
                        "sha256": api_sha256,
                        "signing_identity": "unsigned",
                    },
                    "r_shared_library": {
                        "path": r_dll.relative_to(app).as_posix(),
                        "sha256": r_sha256,
                        "signing_identity": "unsigned",
                    },
                },
                "final": {
                    "api_bridge": {
                        "path": api_bridge.relative_to(app).as_posix(),
                        "sha256": api_sha256,
                        "signing_identity": "unsigned",
                    },
                    "r_shared_library": {
                        "path": r_dll.relative_to(app).as_posix(),
                        "sha256": r_sha256,
                        "signing_identity": "unsigned",
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    for name in (
        "Qt6Core.dll",
        "Qt6Gui.dll",
        "Qt6Network.dll",
        "Qt6Svg.dll",
        "Qt6SvgWidgets.dll",
        "Qt6Widgets.dll",
    ):
        _write_pe(qt / "bin" / name)
    required = {
        "platforms": ("qwindows.dll",),
        "imageformats": ("qico.dll", "qjpeg.dll", "qsvg.dll"),
        "iconengines": ("qsvgicon.dll",),
        "styles": ("qmodernwindowsstyle.dll",),
        "tls": ("qschannelbackend.dll",),
    }
    for family, names in required.items():
        for name in names:
            _write_pe(qt / "plugins" / family / name)
    schema_root = app / "_internal" / "rc_metastudio" / "project_schemas" / "v1"
    source_schema_root = ROOT / "src" / "rc_metastudio" / "project_schemas" / "v1"
    schema_root.mkdir(parents=True)
    for source in source_schema_root.glob("*.schema.json"):
        (schema_root / source.name).write_bytes(source.read_bytes())
    return app


def _windows_runtime_probe(app):
    qt = app / "_internal" / "PyQt6" / "Qt6"
    api_bridge = app / "_internal" / "_rinterface_cffi_api.cp311-win_amd64.pyd"
    r_dll = app / "R" / "bin" / "x64" / "R.dll"
    return {
        "schema_version": 1,
        "frozen": True,
        "python": {
            "version": "3.11.9",
            "executable": str(app / "RCMetaStudio.exe"),
            "architecture": "AMD64",
            "bundle_root": str(app / "_internal"),
        },
        "qt": {
            "pyqt_version": "6.11.0",
            "compiled_qt_version": "6.11.0",
            "runtime_qt_version": "6.11.1",
            "sip_runtime_version": "6.15.2",
            "platform_plugin": "windows",
            "plugins_path": str(qt / "plugins"),
            "library_paths": [str(qt / "plugins")],
            "scale_factor_environment": None,
            "baseline_device_pixel_ratio": 1.0,
            "baseline_logical_dpi": 96.0,
        },
        "rpy2": {
            "distribution_version": "3.6.7",
            "cffi_mode": "API",
            "rinterface_distribution_version": "3.6.6",
            "robjects_distribution_version": "3.6.5",
            "loaded_cffi_mode": "API",
            "api_bridge_loaded": True,
            "api_bridge_path": str(api_bridge),
            "api_bridge_sha256": hashlib.sha256(api_bridge.read_bytes()).hexdigest(),
        },
        "project_schemas": {
            "version": 1,
            "validated_members": ["manifest.json", "project.json", "state.json"],
        },
        "r": {
            "version": "4.6.1",
            "home": str(app / "R"),
            "library_paths": [str(app / "R" / "library")],
            "configured_home": str(app / "R"),
            "configured_library": str(app / "R" / "library"),
            "shared_library_path": str(r_dll),
            "shared_library_sha256": hashlib.sha256(r_dll.read_bytes()).hexdigest(),
            "kit_sha256": "a" * 64,
            "lc_numeric": "C",
        },
    }


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows PE tooling")
def test_windows_runtime_probe_survives_relocation_but_rejects_tampering(tmp_path):
    inspector = _load_windows_deployment_inspector()
    original = _windows_deployment_fixture(tmp_path / "original")
    probe = _windows_runtime_probe(original)
    probe["r"].pop("kit_sha256")
    relocated = tmp_path / "extracted" / "RCMetaStudio-0.2.0-windows-x64"
    shutil.copytree(original, relocated)
    versions = dict(inspector.EXPECTED_VERSIONS)
    provenance = {
        "schema_version": 1,
        "head_sha": "a" * 40,
        "working_tree": "clean",
        "worktree_sha256": "b" * 64,
    }
    inspector.inspect_deployment(
        relocated,
        versions=versions,
        source_commit="a" * 40,
        source_provenance=provenance,
        runtime_probe=probe,
        locked_qt_root=relocated / "_internal" / "PyQt6" / "Qt6",
    )
    r_dll = relocated / "R" / "bin" / "x64" / "R.dll"
    r_dll.write_bytes(r_dll.read_bytes() + b"tampered")
    with pytest.raises(inspector.DeploymentInspectionError, match="frozen R runtime"):
        inspector.inspect_deployment(
            relocated,
            versions=versions,
            source_commit="a" * 40,
            source_provenance=provenance,
            runtime_probe=probe,
            locked_qt_root=relocated / "_internal" / "PyQt6" / "Qt6",
        )


def test_windows_deployment_inspector_resolves_wheel_private_libs_directory():
    inspector = _load_windows_deployment_inspector()
    records = [
        {
            "path": "_internal/numpy/_core/_multiarray_umath.pyd",
            "sha256": "extension",
            "_imports": [{"name": "libscipy_openblas64_example.dll", "kind": "normal"}],
        },
        {
            "path": "_internal/numpy.libs/libscipy_openblas64_example.dll",
            "sha256": "openblas",
            "_imports": [],
        },
    ]

    inspector._resolve_pe_closure(records)

    assert records[0]["imports"] == [
        {
            "name": "libscipy_openblas64_example.dll",
            "kind": "normal",
            "resolution": "app-local",
            "resolved_path": "_internal/numpy.libs/libscipy_openblas64_example.dll",
            "resolved_sha256": "openblas",
        }
    ]


def test_windows_deployment_inspector_recognizes_supported_os_imports():
    inspector = _load_windows_deployment_inspector()

    assert all(
        inspector._is_windows_system_import(name)
        for name in (
            "AUTHZ.dll",
            "DWrite.dll",
            "icuuc.dll",
            "pdh.dll",
            "UIAutomationCore.DLL",
            "WTSAPI32.dll",
        )
    )


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows PE tooling")
def test_windows_deployment_inspector_accepts_one_coherent_x64_qt6_stack(
    tmp_path, monkeypatch
):
    inspector = _load_windows_deployment_inspector()
    app = _windows_deployment_fixture(tmp_path)
    qt_root = app / "_internal" / "PyQt6" / "Qt6"
    _write_pe(qt_root / "plugins" / "imageformats" / "qpdf.dll")
    _write_pe(app / "R" / "library" / "qpdf" / "libs" / "x64" / "qpdf.dll")
    versions = {
        "python": "3.11.9",
        "pyqt6": "6.11.0",
        "qt": "6.11.1",
        "sip": "13.11.1",
        "sip_runtime": "6.15.2",
        "r": "4.6.1",
        "rpy2": "3.6.7",
        "pyinstaller": "6.21.0",
    }

    direct_runtime_probe = _windows_runtime_probe(app)
    direct_runtime_probe["r"].pop("kit_sha256")
    provenance = {
        "schema_version": 1,
        "head_sha": "a" * 40,
        "working_tree": "clean",
        "worktree_sha256": "b" * 64,
    }
    manifest = inspector.inspect_deployment(
        app,
        versions=versions,
        source_commit="a" * 40,
        source_provenance=provenance,
        runtime_probe=direct_runtime_probe,
        locked_qt_root=qt_root,
    )

    assert manifest["target"] == "windows-x64"
    assert manifest["minimum_os"] == "Windows 10 version 1809"
    assert manifest["collector"] == {
        "name": "PyInstaller",
        "version": "6.21.0",
        "provenance": "build-time-only",
        "definition": "packaging/pyinstaller/rc-metastudio.spec",
    }
    assert "r_integration_kit" not in manifest
    assert manifest["embedded_r"]["cffi_mode"] == "API"
    assert manifest["stack"] == versions
    assert manifest["plugins"]["platforms"] == ["qwindows.dll"]
    assert set(manifest["qt_plugins"]) == {
        "platforms/qwindows.dll",
        "imageformats/qico.dll",
        "imageformats/qjpeg.dll",
        "imageformats/qsvg.dll",
        "imageformats/qpdf.dll",
        "iconengines/qsvgicon.dll",
        "styles/qmodernwindowsstyle.dll",
        "tls/qschannelbackend.dll",
    }
    assert all(item["machine"] == "x86_64" for item in manifest["native_files"])
    assert all("imports" in item for item in manifest["native_files"])
    assert set(manifest["project_schema_resources"]) == {
        "manifest.schema.json",
        "project.schema.json",
        "state.schema.json",
    }
    missing_schema = (
        app
        / "_internal"
        / "rc_metastudio"
        / "project_schemas"
        / "v1"
        / "project.schema.json"
    )
    missing_schema.unlink()
    with pytest.raises(
        inspector.DeploymentInspectionError,
        match="missing required project schema resources",
    ):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=qt_root,
        )

    runtime_probe_path = tmp_path / "runtime-probe.json"
    runtime_probe_path.write_text(
        json.dumps(_windows_runtime_probe(app)), encoding="utf-8"
    )
    source_provenance_path = tmp_path / "source-provenance.json"
    source_provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
    output = tmp_path / "deployment-manifest.json"
    captured = {}

    def inspect_from_cli(app_root, **kwargs):
        captured["app_root"] = app_root
        captured.update(kwargs)
        return {"target": "windows-x64", "stack": kwargs["versions"]}

    monkeypatch.setattr(inspector, "inspect_deployment", inspect_from_cli)
    monkeypatch.setattr(
        inspector.sys,
        "argv",
        [
            "inspect_windows_deployment.py",
            "inspect",
            "--app-root",
            str(app),
            "--output",
            str(output),
            "--source-commit",
            "a" * 40,
            "--source-provenance",
            str(source_provenance_path),
            "--runtime-probe",
            str(runtime_probe_path),
            "--locked-qt-root",
            str(app / "_internal" / "PyQt6" / "Qt6"),
            "--python-version",
            versions["python"],
            "--pyqt6-version",
            versions["pyqt6"],
            "--qt-version",
            versions["qt"],
            "--sip-version",
            versions["sip"],
            "--sip-runtime-version",
            versions["sip_runtime"],
            "--r-version",
            versions["r"],
            "--rpy2-version",
            versions["rpy2"],
            "--pyinstaller-version",
            versions["pyinstaller"],
        ],
    )

    assert inspector._main() == 0
    assert captured["versions"] == versions
    assert captured["runtime_probe"] == _windows_runtime_probe(app)
    assert json.loads(output.read_text(encoding="utf-8"))["stack"] == versions


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows PE tooling")
def test_windows_deployment_inspector_records_dirty_source_provenance(tmp_path):
    inspector = _load_windows_deployment_inspector()
    app = _windows_deployment_fixture(tmp_path)
    provenance = {
        "schema_version": 1,
        "head_sha": "a" * 40,
        "working_tree": "dirty",
        "worktree_sha256": "b" * 64,
    }
    manifest = inspector.inspect_deployment(
        app,
        versions=dict(inspector.EXPECTED_VERSIONS),
        source_commit="a" * 40,
        source_provenance=provenance,
        runtime_probe=_windows_runtime_probe(app),
        locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
    )
    assert manifest["source_provenance"] == provenance
    with pytest.raises(inspector.DeploymentInspectionError, match="source provenance"):
        inspector.inspect_deployment(
            app,
            versions=dict(inspector.EXPECTED_VERSIONS),
            source_commit="a" * 40,
            source_provenance=None,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
        )
    with pytest.raises(inspector.DeploymentInspectionError, match="source provenance"):
        inspector.inspect_deployment(
            app,
            versions=dict(inspector.EXPECTED_VERSIONS),
            source_commit="a" * 40,
            source_provenance={
                "schema_version": 1,
                "head_sha": "a" * 40,
                "working_tree": "dirty",
            },
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
        )


def test_source_provenance_frames_binary_untracked_paths_and_contents(tmp_path):
    provenance = _load_source_provenance()
    repo = tmp_path / "repository with spaces"
    repo.mkdir()
    for arguments in (
        ("init",),
        ("config", "user.email", "package@example.test"),
        ("config", "user.name", "Package Test"),
    ):
        subprocess.run(["git", *arguments], cwd=repo, check=True, capture_output=True)
    (repo / "tracked.txt").write_text("base", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "base"], cwd=repo, check=True, capture_output=True
    )
    untracked = repo / "untracked file.bin"
    untracked.write_bytes(b"\x00binary\xff")
    first = provenance.collect_source_provenance(repo)
    assert first["working_tree"] == "dirty"
    untracked.write_bytes(b"\x00changed\xff")
    second = provenance.collect_source_provenance(repo)
    assert second["worktree_sha256"] != first["worktree_sha256"]
    untracked.unlink()
    (repo / "tracked.txt").write_text("changed", encoding="utf-8")
    assert (
        provenance.collect_source_provenance(repo)["worktree_sha256"]
        != first["worktree_sha256"]
    )


def test_final_windows_pe_closure_requires_app_local_msvc_and_tracks_delay_imports():
    inspector = _load_windows_deployment_inspector()
    runtime = {
        "path": "_internal/vcruntime140.dll",
        "sha256": "d" * 64,
        "_imports": [],
    }
    bridge = {
        "path": "_internal/api.pyd",
        "sha256": "a" * 64,
        "_imports": [
            {"name": "VCRUNTIME140.dll", "kind": "delay"},
            {"name": "KERNEL32.dll", "kind": "normal"},
        ],
    }
    inspector._resolve_pe_closure([runtime, bridge])
    assert bridge["imports"] == [
        {
            "name": "VCRUNTIME140.dll",
            "kind": "delay",
            "resolution": "app-local",
            "resolved_path": "_internal/vcruntime140.dll",
            "resolved_sha256": "d" * 64,
        },
        {"name": "KERNEL32.dll", "kind": "normal", "resolution": "system"},
    ]


def test_final_windows_pe_closure_rejects_unique_but_unreachable_dependency():
    inspector = _load_windows_deployment_inspector()
    dependency = {
        "path": "unregistered/private.dll",
        "sha256": "d" * 64,
        "_imports": [],
    }
    owner = {
        "path": "_internal/api.pyd",
        "sha256": "a" * 64,
        "_imports": [{"name": "private.dll", "kind": "normal"}],
    }
    with pytest.raises(inspector.DeploymentInspectionError, match="unreachable"):
        inspector._resolve_pe_closure([dependency, owner])


@pytest.mark.skipif(sys.platform != "win32", reason="requires Windows PE tooling")
def test_windows_deployment_inspector_rejects_legacy_duplicate_and_wrong_architecture(
    tmp_path,
):
    import shutil

    inspector = _load_windows_deployment_inspector()
    versions = {
        "python": "3.11.9",
        "pyqt6": "6.11.0",
        "qt": "6.11.1",
        "sip": "13.11.1",
        "sip_runtime": "6.15.2",
        "r": "4.6.1",
        "rpy2": "3.6.7",
        "pyinstaller": "6.21.0",
    }

    app = _windows_deployment_fixture(tmp_path / "legacy")
    _write_pe(app / "_internal" / "PyQt5" / "Qt5Core.dll")
    with pytest.raises(inspector.DeploymentInspectionError, match="mixed or legacy"):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
        )

    app = _windows_deployment_fixture(tmp_path / "duplicate")
    _write_pe(app / "other" / "Qt6Core.dll")
    with pytest.raises(inspector.DeploymentInspectionError, match="duplicate Qt6"):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
        )

    app = _windows_deployment_fixture(tmp_path / "architecture")
    _write_pe(app / "bad.dll", machine=0x014C)
    with pytest.raises(inspector.DeploymentInspectionError, match="non-x64"):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
        )

    for binding in ("PySide2", "PySide6", "qtpy"):
        app = _windows_deployment_fixture(tmp_path / f"mixed-{binding}")
        _write_pe(app / "_internal" / binding / "binding.pyd")
        with pytest.raises(
            inspector.DeploymentInspectionError, match="mixed or legacy"
        ):
            inspector.inspect_deployment(
                app,
                versions=versions,
                source_commit="a" * 40,
                runtime_probe=_windows_runtime_probe(app),
                locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
            )

    required_plugin = {
        "platforms": "qwindows.dll",
        "imageformats": "qjpeg.dll",
        "iconengines": "qsvgicon.dll",
        "styles": "qmodernwindowsstyle.dll",
        "tls": "qschannelbackend.dll",
    }
    for family, name in required_plugin.items():
        app = _windows_deployment_fixture(tmp_path / f"missing-{family}")
        (app / "_internal" / "PyQt6" / "Qt6" / "plugins" / family / name).unlink()
        with pytest.raises(
            inspector.DeploymentInspectionError, match="missing required Qt"
        ):
            inspector.inspect_deployment(
                app,
                versions=versions,
                source_commit="a" * 40,
                runtime_probe=_windows_runtime_probe(app),
                locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
            )

    app = _windows_deployment_fixture(tmp_path / "duplicate-plugin")
    _write_pe(app / "_internal" / "plugins" / "qwindows.dll")
    with pytest.raises(inspector.DeploymentInspectionError, match="plugin root"):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
        )

    for generated in ("forms/ui_dialog.py", "icons_rc.pyc"):
        app = _windows_deployment_fixture(
            tmp_path / ("generated-" + generated.replace("/", "-"))
        )
        path = app / generated
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("generated", encoding="utf-8")
        with pytest.raises(
            inspector.DeploymentInspectionError, match="generated sources"
        ):
            inspector.inspect_deployment(
                app,
                versions=versions,
                source_commit="a" * 40,
                runtime_probe=_windows_runtime_probe(app),
                locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
            )

    app = _windows_deployment_fixture(tmp_path / "stack-mismatch")
    mismatched = dict(versions, qt="6.11.0")
    with pytest.raises(
        inspector.DeploymentInspectionError, match="differs from the locked"
    ):
        inspector.inspect_deployment(
            app,
            versions=mismatched,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
        )

    app = _windows_deployment_fixture(tmp_path / "misplaced-library")
    source = app / "_internal" / "PyQt6" / "Qt6" / "bin" / "Qt6Network.dll"
    destination = app / "_internal" / "other" / source.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    source.replace(destination)
    with pytest.raises(
        inspector.DeploymentInspectionError, match="outside the authoritative"
    ):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
        )

    app = _windows_deployment_fixture(tmp_path / "runtime-probe-mismatch")
    probe = _windows_runtime_probe(app)
    probe["qt"]["runtime_qt_version"] = "6.11.0"
    with pytest.raises(inspector.DeploymentInspectionError, match="frozen Qt runtime"):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=probe,
            locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
        )

    app = _windows_deployment_fixture(tmp_path / "schema-runtime-probe-mismatch")
    probe = _windows_runtime_probe(app)
    probe["project_schemas"]["validated_members"].remove("state.json")
    with pytest.raises(
        inspector.DeploymentInspectionError,
        match="runtime did not validate the required project schemas",
    ):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=probe,
            locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
        )

    app = _windows_deployment_fixture(tmp_path / "locked-identity-mismatch")
    locked_qt = tmp_path / "locked-qt"
    shutil.copytree(app / "_internal" / "PyQt6" / "Qt6", locked_qt)
    with (locked_qt / "bin" / "Qt6Core.dll").open("ab") as stream:
        stream.write(b"different")
    with pytest.raises(inspector.DeploymentInspectionError, match="identity differs"):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=locked_qt,
        )

    app = _windows_deployment_fixture(tmp_path / "locked-plugin-mismatch")
    locked_qt = tmp_path / "locked-plugin-qt"
    shutil.copytree(app / "_internal" / "PyQt6" / "Qt6", locked_qt)
    with (locked_qt / "plugins" / "platforms" / "qwindows.dll").open("ab") as stream:
        stream.write(b"different")
    with pytest.raises(
        inspector.DeploymentInspectionError, match="plugin identity differs"
    ):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=locked_qt,
        )

    app = _windows_deployment_fixture(tmp_path / "extra-qt-library")
    locked_qt = tmp_path / "extra-qt-library-locked"
    shutil.copytree(app / "_internal" / "PyQt6" / "Qt6", locked_qt)
    _write_pe(app / "_internal" / "PyQt6" / "Qt6" / "bin" / "Qt6Concurrent.dll")
    with pytest.raises(
        inspector.DeploymentInspectionError, match="library identity differs"
    ):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=locked_qt,
        )

    app = _windows_deployment_fixture(tmp_path / "extra-plugin")
    locked_qt = tmp_path / "extra-plugin-locked"
    shutil.copytree(app / "_internal" / "PyQt6" / "Qt6", locked_qt)
    _write_pe(
        app
        / "_internal"
        / "PyQt6"
        / "Qt6"
        / "plugins"
        / "networkinformation"
        / "qnetworklistmanager.dll"
    )
    with pytest.raises(
        inspector.DeploymentInspectionError, match="plugin identity differs"
    ):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=locked_qt,
        )

    app = _windows_deployment_fixture(tmp_path / "mismatched-non-required-plugin")
    locked_qt = tmp_path / "mismatched-non-required-plugin-locked"
    shutil.copytree(app / "_internal" / "PyQt6" / "Qt6", locked_qt)
    locked_extra = (
        locked_qt / "plugins" / "networkinformation" / "qnetworklistmanager.dll"
    )
    _write_pe(locked_extra)
    packaged_extra = (
        app
        / "_internal"
        / "PyQt6"
        / "Qt6"
        / "plugins"
        / "networkinformation"
        / "qnetworklistmanager.dll"
    )
    _write_pe(packaged_extra)
    with packaged_extra.open("ab") as stream:
        stream.write(b"different")
    with pytest.raises(
        inspector.DeploymentInspectionError, match="plugin identity differs"
    ):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=locked_qt,
        )

    app = _windows_deployment_fixture(tmp_path / "duplicate-non-required-plugin")
    locked_qt = tmp_path / "duplicate-non-required-plugin-locked"
    shutil.copytree(app / "_internal" / "PyQt6" / "Qt6", locked_qt)
    locked_extra = (
        locked_qt / "plugins" / "networkinformation" / "qnetworklistmanager.dll"
    )
    packaged_extra = (
        app
        / "_internal"
        / "PyQt6"
        / "Qt6"
        / "plugins"
        / "networkinformation"
        / "qnetworklistmanager.dll"
    )
    _write_pe(locked_extra)
    _write_pe(packaged_extra)
    _write_pe(app / "_internal" / "plugins" / "qnetworklistmanager.dll")
    with pytest.raises(inspector.DeploymentInspectionError, match="plugin root"):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=locked_qt,
        )

    app = _windows_deployment_fixture(tmp_path / "misplaced-unknown-plugin")
    _write_pe(app / "_internal" / "plugins" / "qcustomplugin.dll")
    with pytest.raises(
        inspector.DeploymentInspectionError, match="outside the authoritative plugin"
    ):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
        )

    app = _windows_deployment_fixture(tmp_path / "alternate-qpdf-plugin-tree")
    qt_root = app / "_internal" / "PyQt6" / "Qt6"
    _write_pe(qt_root / "plugins" / "imageformats" / "qpdf.dll")
    _write_pe(app / "_internal" / "plugins" / "imageformats" / "qpdf.dll")
    with pytest.raises(inspector.DeploymentInspectionError, match="plugin root"):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=_windows_runtime_probe(app),
            locked_qt_root=qt_root,
        )

    app = _windows_deployment_fixture(tmp_path / "scaled-runtime-probe")
    probe = _windows_runtime_probe(app)
    probe["qt"]["scale_factor_environment"] = "1.25"
    with pytest.raises(inspector.DeploymentInspectionError, match="frozen Qt runtime"):
        inspector.inspect_deployment(
            app,
            versions=versions,
            source_commit="a" * 40,
            runtime_probe=probe,
            locked_qt_root=app / "_internal" / "PyQt6" / "Qt6",
        )


def test_windows_qualification_evidence_authenticates_complete_packaged_smoke(tmp_path):
    import json
    import zipfile

    inspector = _load_windows_deployment_inspector()
    windows_accessibility = {
        "focus_widget": "tableView",
        "accessible_name": "Packaged accessibility control",
        "accessible_description": "Verifies packaged Qt accessibility metadata.",
    }
    assert inspector._valid_windows_accessibility(windows_accessibility)
    assert not inspector._valid_windows_accessibility(
        {
            "accessible_name": windows_accessibility["accessible_name"],
        }
    )
    archive = tmp_path / "RCMetaStudio-windows-x64.zip"
    runtime_probe = tmp_path / "runtime-probe.json"
    runtime_value = {"frozen": True}
    runtime_probe.write_text(json.dumps(runtime_value), encoding="utf-8")
    runtime_canonical = (
        json.dumps(runtime_value, sort_keys=True, separators=(",", ":")) + "\n"
    )
    import hashlib

    deployment = tmp_path / "deployment-manifest.json"
    deployment.write_text(
        json.dumps(
            {
                "target": "windows-x64",
                "stack": inspector.EXPECTED_VERSIONS,
                "source_provenance": {
                    "schema_version": 1,
                    "head_sha": "a" * 40,
                    "working_tree": "clean",
                    "worktree_sha256": "d" * 64,
                },
                "runtime_probe_canonical_sha256": hashlib.sha256(
                    runtime_canonical.encode()
                ).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    smoke = tmp_path / "packaged-smoke.json"
    smoke_log = tmp_path / "packaged-smoke.log"
    smoke_log.write_text(
        "\n".join(
            (
                "packaged-workflow:evidence-written",
                "packaged-runtime-probe:passed",
                "packaged-workflow:project-exercise:complete",
                "packaged-workflow:post-close",
                "packaged-workflow:process-exit:0",
                "packaged-surface:scale-1.25-passed",
                "packaged-surface:scale-1.50-passed",
                "packaged-surface:scale-1.75-passed",
                "startup-project:normal-entry-point-passed",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    smoke.write_text(
        json.dumps(
            {
                "passed": True,
                "workflows": {
                    "automation_entry_point": True,
                    "converted_sample": "amino.rcms",
                    "representative_edit": True,
                    "real_r_analysis": True,
                    "result_text": True,
                    "expected_normalized_summary_sha256": inspector.EXPECTED_SUMMARY_SHA256,
                    "raw_summary_sha256": "b" * 64,
                    "normalized_summary_sha256": inspector.EXPECTED_SUMMARY_SHA256,
                    "svg_sha256": {"Forest Plot": "a" * 64},
                    "locale_variants": [
                        {
                            "locale": "en_US",
                            "input": "7.0",
                            "canonical_value": 7.0,
                            "raw_summary_sha256": "b" * 64,
                            "normalized_summary_sha256": inspector.EXPECTED_SUMMARY_SHA256,
                            "svg_sha256": {"Forest Plot": "a" * 64},
                        },
                        {
                            "locale": "de_DE",
                            "input": "7,0",
                            "canonical_value": 7.0,
                            "raw_summary_sha256": "b" * 64,
                            "normalized_summary_sha256": inspector.EXPECTED_SUMMARY_SHA256,
                            "svg_sha256": {"Forest Plot": "a" * 64},
                        },
                    ],
                    "save_reopen": True,
                    "analysis_after_reopen": True,
                    "sample_projects": {
                        "passed": True,
                        "manifest_sha256": "c" * 64,
                        "projects": [
                            {
                                "project": "amino.rcms",
                                "sha256": "d" * 64,
                                "semantic_sha256": "e" * 64,
                                "opened_in_packaged_application": True,
                            }
                        ],
                    },
                },
                "execution": {
                    "automation_exit_code": 0,
                    "positional_user_entry_exit_code": 0,
                    "scale_exit_codes": {"1.25": 0, "1.50": 0, "1.75": 0},
                    "post_close_marker": True,
                    "clean_exit": True,
                },
                "scales": [
                    {
                        "requested": scale,
                        "qt_scale_factor": scale,
                        "device_pixel_ratio": float(scale),
                        "baseline_device_pixel_ratio": 1.0,
                        "binary_resources": True,
                        "locale": "de_DE",
                        "platform_plugin": "windows",
                        "accessibility": windows_accessibility,
                        "tls_backends": ["schannel"],
                        "active_style": "windows11",
                        "available_styles": ["Windows11", "Windows"],
                        "image_formats": ["ico", "jpeg", "svg"],
                    }
                    for scale in ("1.25", "1.50", "1.75")
                ],
            }
        ),
        encoding="utf-8",
    )
    root = "RCMetaStudio-0.2.0-windows-x64"
    embedded = {
        "qualification/deployment-manifest.json": deployment,
        "qualification/runtime-probe.json": runtime_probe,
        "qualification/packaged-smoke.json": smoke,
        "qualification/packaged-smoke.log": smoke_log,
    }
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(f"{root}/RCMetaStudio.exe", b"MZ")
        for relative, source in embedded.items():
            bundle.writestr(f"{root}/{relative}", source.read_bytes())
    archive_report = inspector.inspect_archive(
        archive, archive_root_name=root, embedded_files=embedded
    )
    archive_inspection = tmp_path / "archive-inspection.json"
    archive_inspection.write_text(json.dumps(archive_report), encoding="utf-8")
    extracted_deployment = tmp_path / "deployment-reinspection.json"
    extracted_deployment.write_bytes(deployment.read_bytes())
    extracted_smoke = tmp_path / "extracted-packaged-smoke.json"
    extracted_smoke.write_bytes(smoke.read_bytes())
    extracted_smoke_log = tmp_path / "extracted-packaged-smoke.log"
    extracted_smoke_log.write_bytes(smoke_log.read_bytes())

    evidence = inspector.write_qualification_evidence(
        archive=archive,
        deployment_manifest=deployment,
        smoke_evidence=smoke,
        smoke_log=smoke_log,
        runtime_probe=runtime_probe,
        archive_inspection=archive_inspection,
        extracted_deployment_manifest=extracted_deployment,
        extracted_smoke_evidence=extracted_smoke,
        extracted_smoke_log=extracted_smoke_log,
        output=tmp_path / "evidence.json",
    )

    assert evidence["passed"] is True
    assert evidence["artifact"]["sha256"] == inspector.sha256_file(archive)
    assert evidence["runner"]["runner_arch"]
    assert evidence["logs"][0]["sha256"] == inspector.sha256_file(smoke_log)
    assert evidence["exact_extracted_qualification"][
        "archive_sha256"
    ] == inspector.sha256_file(archive)
    assert evidence["source_provenance"]["working_tree"] == "clean"

    extracted_smoke.write_text("{}", encoding="utf-8")
    with pytest.raises(inspector.DeploymentInspectionError, match="exact-extracted"):
        inspector.write_qualification_evidence(
            archive=archive,
            deployment_manifest=deployment,
            smoke_evidence=smoke,
            smoke_log=smoke_log,
            runtime_probe=runtime_probe,
            archive_inspection=archive_inspection,
            extracted_deployment_manifest=extracted_deployment,
            extracted_smoke_evidence=extracted_smoke,
            extracted_smoke_log=extracted_smoke_log,
            output=tmp_path / "missing-extracted.json",
        )
    extracted_smoke.write_bytes(smoke.read_bytes())

    mutated = json.loads(smoke.read_text(encoding="utf-8"))
    mutated["scales"][0]["device_pixel_ratio"] = 1.0
    smoke.write_text(json.dumps(mutated), encoding="utf-8")
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(f"{root}/RCMetaStudio.exe", b"MZ")
        for relative, source in embedded.items():
            bundle.writestr(f"{root}/{relative}", source.read_bytes())
    archive_report = inspector.inspect_archive(
        archive, archive_root_name=root, embedded_files=embedded
    )
    archive_inspection.write_text(json.dumps(archive_report), encoding="utf-8")
    with pytest.raises(inspector.DeploymentInspectionError, match="incomplete"):
        inspector.write_qualification_evidence(
            archive=archive,
            deployment_manifest=deployment,
            smoke_evidence=smoke,
            smoke_log=smoke_log,
            runtime_probe=runtime_probe,
            archive_inspection=archive_inspection,
            extracted_deployment_manifest=extracted_deployment,
            extracted_smoke_evidence=extracted_smoke,
            extracted_smoke_log=extracted_smoke_log,
            output=tmp_path / "mutated.json",
        )

    for member_names in (
        (f"{root}/../escape.txt",),
        (f"{root}\\qualification\\runtime-probe.json",),
        (f"{root}/A.txt", f"{root}/a.txt"),
    ):
        bad_archive = tmp_path / ("bad-" + str(len(member_names)) + ".zip")
        with zipfile.ZipFile(bad_archive, "w") as bundle:
            for name in member_names:
                bundle.writestr(name, b"bad")
        with pytest.raises(inspector.DeploymentInspectionError):
            inspector.inspect_archive(
                bad_archive, archive_root_name=root, embedded_files=embedded
            )
