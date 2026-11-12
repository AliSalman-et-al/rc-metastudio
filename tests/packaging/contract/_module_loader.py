# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Load packaging scripts for behavioral contract tests."""

from importlib import util
from pathlib import Path
from types import ModuleType


def load_module_from_path(name: str, path: Path) -> ModuleType:
    """Load a Python module from a file after validating its import spec."""

    spec = util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module {name!r} from {path}")
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
