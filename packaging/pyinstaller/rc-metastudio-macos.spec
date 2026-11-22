# -*- mode: python ; coding: utf-8 -*-
"""Authoritative PyInstaller definition for the native Apple-silicon macOS application."""

import os
import importlib.util
import tomllib
from pathlib import Path

repo_root = Path(SPECPATH).resolve().parents[1]
project_version = os.environ.get("RCMS_PROJECT_VERSION")
if project_version is None:
    with (repo_root / "pyproject.toml").open("rb") as metadata:
        project_version = tomllib.load(metadata)["project"]["version"]
collection_spec = importlib.util.spec_from_file_location(
    "rcms_generated_ui_collection",
    repo_root / "packaging" / "pyinstaller" / "generated_ui_collection.py",
)
collection_module = importlib.util.module_from_spec(collection_spec)
collection_spec.loader.exec_module(collection_module)
app_source = repo_root / "src" / "rc_metastudio"
qt6_build_root = Path(os.environ["RCMS_QT6_BUILD_ROOT"]).resolve()
generated_ui_modules = collection_module.pyinstaller_module_entries(qt6_build_root)
# The package builder injects the staged R framework after application collection.
direct_r_marker = repo_root / "packaging" / "pyinstaller" / "direct-r-spike.marker"

a = Analysis(
    [str(app_source / "__main__.py")],
    pathex=[
        str(app_source),
        str(app_source / "forms"),
    ],
    binaries=[],
    datas=[*collection_module.application_data(app_source, qt6_build_root), (str(direct_r_marker), ".")],
    hiddenimports=collection_module.APPLICATION_HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=collection_module.APPLICATION_EXCLUDES,
    noarchive=False,
    optimize=0,
)
a.pure.extend(generated_ui_modules)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RCMetaStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    argv_emulation=False,
    target_arch=os.environ.get("RCMS_TARGET_ARCHITECTURE", "arm64"),
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="RCMetaStudio",
)
app = BUNDLE(
    coll,
    name="RCMetaStudio.app",
    icon=str(app_source / "images" / "rc-metastudio-app-icon-rounded.png"),
    bundle_identifier=os.environ.get(
        "RCMS_BUNDLE_IDENTIFIER", "org.researchconsultancy.rc-metastudio"
    ),
    version=project_version,
    info_plist={
        "LSMinimumSystemVersion": os.environ.get("RCMS_MINIMUM_MACOS_VERSION", "14.0"),
        "NSHighResolutionCapable": True,
        "NSPrincipalClass": "NSApplication",
    },
)
