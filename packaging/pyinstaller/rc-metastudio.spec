# -*- mode: python ; coding: utf-8 -*-
"""Authoritative PyInstaller definition for the Windows x64 application."""

import os
import importlib.util
from pathlib import Path

repo_root = Path(SPECPATH).resolve().parents[1]
collection_spec = importlib.util.spec_from_file_location(
    "rcms_generated_ui_collection",
    repo_root / "packaging" / "pyinstaller" / "generated_ui_collection.py",
)
collection_module = importlib.util.module_from_spec(collection_spec)
collection_spec.loader.exec_module(collection_module)
app_source = repo_root / "src" / "rc_metastudio"
pyqt_root = Path(os.environ["RCMS_PYQT_ROOT"]).resolve()
qt6_build_root = Path(os.environ["RCMS_QT6_BUILD_ROOT"]).resolve()
generated_ui_modules = collection_module.pyinstaller_module_entries(qt6_build_root)
required_plugins = (
    "platforms/qwindows.dll",
    "imageformats/qico.dll",
    "imageformats/qjpeg.dll",
    "imageformats/qsvg.dll",
    "iconengines/qsvgicon.dll",
    "styles/qmodernwindowsstyle.dll",
    "tls/qschannelbackend.dll",
)
qt_plugin_binaries = [
    (
        str(pyqt_root / "Qt6" / "plugins" / relative),
        str(Path("PyQt6") / "Qt6" / "plugins" / Path(relative).parent),
    )
    for relative in required_plugins
]


def is_windows_system_runtime(entry):
    name = Path(entry[0]).name.casefold()
    return (
        name.startswith("api-ms-win-")
        or name.startswith("icudt")
        or name in {"icu.dll", "icuin.dll", "icuuc.dll", "ucrtbase.dll"}
    )

a = Analysis(
    [str(app_source / "__main__.py")],
    pathex=[
        str(app_source),
        str(app_source / "forms"),
    ],
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
a.binaries = [entry for entry in a.binaries if not is_windows_system_runtime(entry)]
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
    icon=[str(app_source / "images" / "rc-metastudio-app-icon-rounded.ico")],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="RCMetaStudio",
)
