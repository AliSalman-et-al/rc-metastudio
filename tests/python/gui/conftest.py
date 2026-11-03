# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit R-boundary injection for GUI behavior tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def inject_gui_boundary(inject_python_boundary, monkeypatch: pytest.MonkeyPatch):
    from rc_metastudio import (
        analysis_adapter,
        binary_data_dialog,
        continuous_data_dialog,
        diagnostic_data_dialog,
        r_bridge,
    )

    for dialog_module in (
        analysis_adapter,
        binary_data_dialog,
        continuous_data_dialog,
        diagnostic_data_dialog,
    ):
        monkeypatch.setattr(dialog_module, "r_bridge", r_bridge, raising=False)


@pytest.fixture(autouse=True)
def dispose_test_windows(qapp, monkeypatch):
    """Dispose each test's windows while its Python callbacks are still alive."""
    import gc

    from PyQt6 import sip

    baseline = {id(widget) for widget in qapp.topLevelWidgets()}
    yield
    # close() only hides ordinary widgets. Leaving them to cyclic GC lets a
    # later application-wide Qt notification destroy windows while iterating
    # its native widget list (notably setWindowIcon during shell composition).
    owned = [widget for widget in qapp.topLevelWidgets() if id(widget) not in baseline]
    for widget in owned:
        if not sip.isdeleted(widget):
            sip.delete(widget)
    gc.collect()
