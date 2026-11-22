# SPDX-License-Identifier: GPL-3.0-or-later
"""Stage export files and keep Qt-side document composition off the GUI thread."""

from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from PyQt6.QtCore import QEventLoop, QThread, QTimer, Qt
from PyQt6.QtWidgets import QApplication, QProgressDialog

from rc_metastudio import r_worker


@contextmanager
def staged_output(path: str | Path) -> Generator[Path]:
    destination = Path(path).resolve()
    with TemporaryDirectory(prefix=".rcms-export-", dir=destination.parent) as directory:
        temporary = Path(directory) / destination.name
        yield temporary
        temporary.replace(destination)


class _ExportWriter(QThread):
    def __init__(self, write: Callable[[], None]):
        super().__init__()
        self.write = write
        self.error: Exception | None = None

    def run(self) -> None:
        try:
            self.write()
        except Exception as error:
            self.error = error


def compose_export(write: Callable[[], None]) -> None:
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        write()
        return
    app.setProperty("rcmsExportInProgress", True)
    try:
        thread = _ExportWriter(write)
        loop = QEventLoop()
        thread.finished.connect(loop.quit)
        dialog = QProgressDialog("Writing export…", "Cancel", 0, 0, QApplication.activeWindow())
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.canceled.connect(thread.requestInterruption)
        show = QTimer(dialog)
        show.setSingleShot(True)
        show.timeout.connect(dialog.show)
        show.start(200)
        thread.start()
        loop.exec()
        thread.wait()
        show.stop()
        cancelled = dialog.wasCanceled()
        dialog.hide()
        dialog.deleteLater()
        if cancelled:
            raise r_worker.RJobCancelled("The export was cancelled.")
        if thread.error is not None:
            raise thread.error
    finally:
        app.setProperty("rcmsExportInProgress", False)


def check_export_cancelled() -> None:
    thread = QThread.currentThread()
    if thread is not None and thread.isInterruptionRequested():
        raise r_worker.RJobCancelled("The export was cancelled.")
