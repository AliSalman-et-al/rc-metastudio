from typing import cast

from PyQt6 import QtWidgets

from rc_metastudio.qt6_ui import prepare_generated_ui_imports
from qt_test_support import required

prepare_generated_ui_imports()

def test_issue_190_main_window_does_not_expose_toolbar_toggle_popup():
    from rc_metastudio.main_window import MainWindow

    app = cast(
        QtWidgets.QApplication,
        required(
            QtWidgets.QApplication.instance() or QtWidgets.QApplication([]),
            "application",
        ),
    )
    window = MainWindow()
    window.workspace.mark_saved()

    try:
        assert window.createPopupMenu() is None
        assert required(
            window.toolBar.toggleViewAction(), "toolbar toggle action"
        ).isEnabled()
    finally:
        window.close()
        window.deleteLater()
    app.processEvents()
