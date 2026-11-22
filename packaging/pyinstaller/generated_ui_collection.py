# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Collect the application files and imports shared by all release targets."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

from rc_metastudio.rcmetar_identity import STAMP_COMMAND, source_sha


APPLICATION_HIDDEN_IMPORTS = [
    "openpyxl",
    "docx",
    "lxml.etree",
    "rpy2.robjects",
    "rpy2.rinterface",
    "_rinterface_cffi_api",
    "PyQt6.QtNetwork",
    "PyQt6.QtSvg",
    "PyQt6.QtSvgWidgets",
]
APPLICATION_EXCLUDES = ["PyQt5", "PySide2", "PySide6", "qtpy", "_rinterface_cffi_abi"]


def application_data(app_source: Path, qt6_build_root: Path) -> list[tuple[str, str]]:
    package = app_source.parents[1] / "r" / "RCMetaR"
    fingerprint = package / "inst" / "source.sha256"
    if fingerprint.read_text(encoding="ascii").strip() != source_sha(package):
        raise ValueError(f"Update the RCMetaR source SHA before packaging. Run {STAMP_COMMAND}.")
    project_schema_dir = Path("rc_metastudio") / "project_schemas"
    project_schemas = (app_source / "project_schemas").glob("v*/*.schema.json")
    data = [
        *copy_metadata("rpy2"),
        (str(fingerprint), "rc_metastudio"),
        (str(app_source.parents[1] / "config" / "r-dependencies.json"), "rc_metastudio"),
        *collect_data_files("docx", includes=["templates/*"]),
        (str(qt6_build_root / "resources" / "icons.rcc"), "resources"),
    ]
    data.extend(
        (str(path), str(project_schema_dir / path.parent.name))
        for path in sorted(project_schemas)
    )
    return data


def pyinstaller_module_entries(
    qt6_build_root: str | Path,
) -> tuple[tuple[str, str, str], ...]:
    package_root = Path(qt6_build_root).resolve() / "generated" / "rc_metastudio"
    forms_root = package_root / "forms"
    modules = [
        (f"rc_metastudio.{path.stem}", str(path), "PYMODULE")
        for path in sorted(package_root.glob("ui_*.py"))
    ]
    modules.extend(
        (f"rc_metastudio.forms.{path.stem}", str(path), "PYMODULE")
        for path in sorted(forms_root.glob("ui_*.py"))
    )
    if not modules:
        raise ValueError(f"no generated Qt modules found under {package_root}")
    return tuple(modules)
