# -*- mode: python ; coding: utf-8 -*-
"""Authoritative PyInstaller definition for the portable Linux application."""

import importlib.util
import os
from pathlib import Path

repo_root = Path(SPECPATH).resolve().parents[1]
collection_spec = importlib.util.spec_from_file_location(
    "rcms_generated_ui_collection",
    repo_root / "packaging" / "pyinstaller" / "generated_ui_collection.py",
)
collection_module = importlib.util.module_from_spec(collection_spec)
collection_spec.loader.exec_module(collection_module)
app_source = repo_root / "src" / "rc_metastudio"
qt6_build_root = Path(os.environ["RCMS_QT6_BUILD_ROOT"]).resolve()
pyqt_root = Path(os.environ["RCMS_PYQT_ROOT"]).resolve()
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


a = Analysis(
    [str(app_source / "__main__.py")],
    pathex=[str(app_source), str(app_source / "forms")],
    binaries=qt_plugin_binaries,
    datas=collection_module.application_data(app_source, qt6_build_root),
    hiddenimports=collection_module.APPLICATION_HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=collection_module.APPLICATION_EXCLUDES,
    noarchive=False,
    optimize=0,
)
a.binaries = [entry for entry in a.binaries if Path(entry[1]).name != "libqtiff.so"]
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
