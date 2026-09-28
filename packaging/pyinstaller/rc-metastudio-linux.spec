# -*- mode: python ; coding: utf-8 -*-
"""Authoritative PyInstaller definition for the portable Linux application."""

import importlib.util
import os
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata


repo_root = Path(SPECPATH).resolve().parents[1]
collection_spec = importlib.util.spec_from_file_location(
    "rcms_generated_ui_collection",
    repo_root / "packaging" / "pyinstaller" / "generated_ui_collection.py",
)
collection_module = importlib.util.module_from_spec(collection_spec)
collection_spec.loader.exec_module(collection_module)
app_source = repo_root / "src" / "rc_metastudio"
qt6_build_root = Path(os.environ["RCMS_QT6_BUILD_ROOT"]).resolve()
r_home = Path(os.environ["RCMS_R_HOME"]).resolve()
pyqt_root = Path(os.environ["RCMS_PYQT_ROOT"]).resolve()
binary_resource = qt6_build_root / "resources" / "icons.rcc"
project_schema_root = app_source / "project_schemas" / "v1"
project_schema_data = [
    (str(path), str(Path("rc_metastudio") / "project_schemas" / "v1"))
    for path in sorted(project_schema_root.glob("*.schema.json"))
]
generated_ui_modules = collection_module.pyinstaller_module_entries(qt6_build_root)
required_plugins = (
    "platforms/libqxcb.so",
    "imageformats/libqico.so",
    "imageformats/libqjpeg.so",
    "imageformats/libqsvg.so",
    "iconengines/libqsvgicon.so",
    "tls/libqcertonlybackend.so",
)
qt_plugin_binaries = []
for relative in required_plugins:
    source = pyqt_root / "Qt6" / "plugins" / relative
    if not source.is_file():
        raise ValueError(f"locked PyQt6 runtime is missing Qt plugin: {source}")
    qt_plugin_binaries.append(
        (str(source), str(Path("PyQt6") / "Qt6" / "plugins" / Path(relative).parent))
    )


def is_private_r_binary(entry):
    source = Path(entry[1]).resolve()
    return source == r_home or r_home in source.parents


a = Analysis(
    [str(app_source / "__main__.py")],
    pathex=[str(app_source), str(app_source / "forms")],
    binaries=qt_plugin_binaries,
    datas=[
        *copy_metadata("rpy2"),
        (str(binary_resource), "resources"),
        *project_schema_data,
    ],
    hiddenimports=[
        "rpy2.robjects",
        "rpy2.rinterface",
        "_rinterface_cffi_api",
        "PyQt6.QtNetwork",
        "PyQt6.QtSvg",
        "PyQt6.QtSvgWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5", "PySide2", "PySide6", "qtpy", "_rinterface_cffi_abi"],
    noarchive=False,
    optimize=0,
)
# libR is resolved from the app-root R directory by the launcher. Do not copy
# a second R runtime into PyInstaller's private import directory. Qt's bundled
# TIFF plugin targets libtiff.so.5, which Noble does not provide; the app does
# not use that Qt image format plugin.
a.binaries = [
    entry
    for entry in a.binaries
    if not is_private_r_binary(entry) and Path(entry[1]).name != "libqtiff.so"
]
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
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="RCMetaStudio",
)
