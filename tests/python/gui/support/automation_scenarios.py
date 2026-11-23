# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Verification and automation workflows for RC MetaStudio."""

from __future__ import annotations

import sys

from PyQt6 import QtCore, QtWidgets

from rc_metastudio import app_error_handler
from rc_metastudio.automation import start_automation
from rc_metastudio.launch import (
    _top_level_ids,
    compose_application,
    configure_application,
    dispose_qobjects,
)


def start_shell_smoke(require_native_window=False):
    """Exercise the maintained full shell without invoking analysis."""
    app, meta = start_automation()
    try:
        if require_native_window:
            platform_name = app.platformName().lower()
            expected = {"win32": "windows", "darwin": "cocoa"}.get(sys.platform, "xcb")
            if platform_name != expected:
                raise SystemExit(
                    "Native shell smoke loaded Qt platform %s, expected %s."
                    % (platform_name, expected)
                )
        app.processEvents()
        if not meta.isVisible():
            raise SystemExit("Application shell did not become visible.")
        if meta.menuBar() is None or not meta.menuBar().actions():
            raise SystemExit("Application shell did not expose its menus.")
        print(
            "Application shell smoke passed with Qt platform %s."
            % app.platformName().lower()
        )
    finally:
        if meta.workspace.document is not None:
            meta.workspace.mark_saved()
        meta.close()
        app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
        app.processEvents()
    if meta in app.topLevelWidgets():
        raise SystemExit("Application shell remained owned after close.")
    return 0


class _InjectedStartupFailure(RuntimeError):
    pass


def start_shell_failure_smoke(stage):
    """Observe failed startup and prove the owned shell can be disposed."""
    if stage not in {"r-load", "meta-form"}:
        raise SystemExit("Unknown shell failure stage: %s" % stage)
    app = app_error_handler.get_or_create_application(sys.argv)
    configure_application(app)
    baseline_ids = _top_level_ids(app)
    errors = []

    def r_loader(_app, _splash):
        raise _InjectedStartupFailure(stage)

    from rc_metastudio.main_window import MainWindow

    class FailureShell(MainWindow):
        def _show_analysis_backend_error(self, exception, *, startup=False):
            assert not self.action_go.isEnabled()
            errors.append(exception)

    def meta_factory():
        if stage == "meta-form":
            partial = QtWidgets.QMainWindow()
            partial.setWindowTitle("Injected partial shell")
            partial.show()
            app.processEvents()
            raise _InjectedStartupFailure(stage)
        return FailureShell()

    module = type("MainWindowModule", (), {"MainWindow": meta_factory})
    try:
        _, window = compose_application(app=app, startup="desktop",
                                        main_window_loader=module, r_loader=r_loader)
    except _InjectedStartupFailure:
        if stage != "meta-form":
            raise
    else:
        app.processEvents()
        if stage != "r-load" or len(errors) != 1 or not isinstance(errors[0], _InjectedStartupFailure):
            raise SystemExit("Injected startup failure did not fire: %s" % stage)
        if not window.isVisible() or not window.isEnabled() or window.action_go.isEnabled():
            raise SystemExit("R startup failure did not leave a visible failed shell")
        dispose_qobjects(app, (window,))

    leaked = [widget for widget in app.topLevelWidgets() if id(widget) not in baseline_ids]
    if leaked:
        raise SystemExit("Startup failure leaked top-level objects at %s: %s"
                         % (stage, [type(widget).__name__ for widget in leaked]))
    print("Application shell failure teardown passed at %s." % stage)
    return 0
