"""Native startup proof. Run in a fresh process; retain screenshots and observations."""
import argparse
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

from PyQt6 import QtCore, QtGui, QtWidgets
from rc_metastudio import app_error_handler, launch, r_runtime

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--failure", action="store_true")
parser.add_argument("--startup-project", action="store_true")
args = parser.parse_args()
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=True)
QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat, QtCore.QSettings.Scope.UserScope, str(output / "settings"))
app = app_error_handler.get_or_create_application([sys.argv[0]])
observations = []

def observe(phase):
    if phase == "splash:visible" or phase.startswith("r-library:") and phase.endswith(":start"):
        splash = next(w for w in app.topLevelWidgets() if isinstance(w, QtWidgets.QSplashScreen) and w.isVisible())
        assert not any(isinstance(w, QtWidgets.QMainWindow) and w.isVisible() for w in app.topLevelWidgets())
        assert splash.message() == {"splash:visible": "Starting R…", "r-library:metafor:start": "Loading metafor…", "r-library:RCMetaR:start": "Loading RCMetaR…", "r-library:grid:start": "Loading grid…"}[phase]
        assert splash.windowFlags() & QtCore.Qt.WindowType.FramelessWindowHint
        assert splash.testAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        assert not splash.windowIcon().isNull()
        font = QtGui.QFont("Segoe UI" if sys.platform == "win32" else app.font().family())
        font.setPointSizeF(13.5 * 72 / splash.logicalDpiY())
        names = "Statistics by R, metafor, meta, mada, and RCMetaR."
        names_width = QtGui.QFontMetricsF(font).horizontalAdvance(names)
        assert names_width <= 344, (names_width, names)
        app.processEvents()
        splash.grab().save(str(output / (phase.replace(":", "-") + ".png")))
        screen = splash.screen()
        assert screen is not None
        screen.grabWindow(0).save(str(output / (phase.replace(":", "-") + "-desktop.png")))
        if os.name == "nt":
            import ctypes
            exstyle = ctypes.windll.user32.GetWindowLongW(int(splash.winId()), -20)
            assert exstyle & 0x40000, hex(exstyle)  # WS_EX_APPWINDOW
            assert not exstyle & 0x80, hex(exstyle)  # WS_EX_TOOLWINDOW
        observations.append({"phase": phase, "message": splash.message(), "dpr": splash.devicePixelRatioF(), "size": [splash.width(), splash.height()], "statistics_line": names, "statistics_line_width": names_width, "clip_width": 344})

errors = []

class ShellPaintObserver(QtCore.QObject):
    paint_count = 0

    def eventFilter(self, a0: QtCore.QObject | None, a1: QtCore.QEvent | None) -> bool:
        if isinstance(a0, QtWidgets.QMainWindow) and a1 is not None and a1.type() == QtCore.QEvent.Type.Paint:
            self.paint_count += 1
        return False

paint_observer = ShellPaintObserver()
app.installEventFilter(paint_observer)
def capture_error(widget):
    assert widget.isVisible()
    assert widget.windowTitle() == "Analysis Backend Unavailable"
    assert paint_observer.paint_count > 0, "Startup shell never painted before the error dialog"
    assert widget.text() == (
        "The analysis backend (R) could not start. "
        "Install or repair the pinned R/RCMetaR runtime, then restart RC MetaStudio.\n\n"
        "Details: RuntimeError: Injected grid load failure after real R packages"
    )
    errors.append(widget.text())
    observations.append({"shell_paint_events_before_error_capture": paint_observer.paint_count,
                         "startup_error": widget.text()})
    widget.screen().grabWindow(0).save(str(output / "failure-desktop.png"))
    widget.grab().save(str(output / "failure-dialog.png"))
    widget.accept()


def close_error():
    for widget in app.topLevelWidgets():
        if isinstance(widget, QtWidgets.QMessageBox) and widget.isVisible():
            timer.stop()
            # Let the native window animations/compositor finish before the desktop capture.
            QtCore.QTimer.singleShot(500, lambda dialog=widget: capture_error(dialog))
            return


def failing_grid(_self):
    raise RuntimeError("Injected grid load failure after real R packages")

os.environ["RCMS_ANALYSIS_SCRATCH_DIR"] = str(output / "scratch")
timer = QtCore.QTimer()
timer.timeout.connect(close_error)
timer.start(50)
with patch.object(launch.settings, "get_base_path", return_value=str(output / "appdata")):
    if args.startup_project:
        compose = launch.compose_application
        def observed_composition(**kwargs):
            return compose(**kwargs, phase_callback=observe)
        marker = output / "project-opened.json"
        sample = Path(__file__).resolve().parents[2] / "sample_projects/amino.rcms"
        with patch.object(launch, "compose_application", observed_composition), patch.object(sys, "argv", [
            "rc-metastudio", "--automation-startup-project-smoke",
            "--automation-startup-completion-marker", str(marker), str(sample),
        ]):
            assert launch.start() == 0
        assert json.loads(marker.read_text())["post_close"]
        assert observations
        (output / "observations.json").write_text(json.dumps(observations, indent=2))
        print("POSITIONAL STARTUP PROOF PASSED", app.platformName())
        timer.stop()
        raise SystemExit(0)
    if args.failure:
        # Patch only the final package call; the runtime and prior packages are real.
        from rc_metastudio import r_bridge
        from rc_metastudio.main_window import MainWindow
        show_error = MainWindow._show_analysis_backend_error
        def observed_error(window, exception, *, startup=False):
            assert paint_observer.paint_count > 0, "Shell must paint before opening the startup error"
            observations.append({"shell_paint_events_before_dialog": paint_observer.paint_count})
            show_error(window, exception, startup=startup)
        with patch.object(r_bridge.RLibraryLoader, "load_grid", failing_grid), patch.object(MainWindow, "_show_analysis_backend_error", observed_error):
            _, window = launch.compose_application(app=app, interactive=True, phase_callback=observe)
    else:
        _, window = launch.compose_application(app=app, interactive=True, phase_callback=observe)
    try:
        assert window.isEnabled() and window.isVisible()
        assert not any(isinstance(w, QtWidgets.QSplashScreen) and w.isVisible() for w in app.topLevelWidgets())
        assert window.statusBar().currentMessage() == ""
        assert r_runtime.is_ready() is not args.failure
        assert bool(errors) is args.failure
        assert window.open(str(Path(__file__).resolve().parents[2] / "sample_projects/amino.rcms"))
        assert window.model.rowCount() > 0
        assert window.action_go.isEnabled() is not args.failure
        if args.failure:
            name = window.model.index(0, window.model.NAME)
            assert window.model.setData(name, "Edited without R")
            destination = output / "edited-without-r.rcms"
            with patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=(str(destination), "")):
                window.save_as()
            assert window.open(str(destination), raise_on_error=True)
            assert window.model.data(window.model.index(0, window.model.NAME)) == "Edited without R"
            assert not window.action_go.isEnabled()
        window.grab().save(str(output / "ready-window.png"))
        observations.append({"enabled": window.isEnabled(), "analysis_enabled": window.action_go.isEnabled(), "rows": window.model.rowCount(), "errors": errors})
        (output / "observations.json").write_text(json.dumps(observations, indent=2), encoding="utf-8")
        print("STARTUP PROOF PASSED", app.platformName(), "DPR", window.devicePixelRatioF())
    finally:
        window.workspace.mark_saved()
        launch.dispose_qobjects(app, (window,))
        timer.stop()
