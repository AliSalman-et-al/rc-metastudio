from typing import TYPE_CHECKING, cast

from PyQt6 import QtWidgets

from rc_metastudio.qt6_ui import prepare_generated_ui_imports
from test_types import required

prepare_generated_ui_imports()

if TYPE_CHECKING:
    from ui_main_window import Ui_MainWindow
else:
    from rc_metastudio.ui_main_window import Ui_MainWindow


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


def test_change_confidence_level_dialog_does_not_use_legacy_fixed_layout_policy():
    from rc_metastudio import confidence_level_dialog

    app = cast(
        QtWidgets.QApplication,
        required(
            QtWidgets.QApplication.instance() or QtWidgets.QApplication([]),
            "application",
        ),
    )
    dialog = confidence_level_dialog.ConfidenceLevelDialog(95.0)
    dialog.show()
    app.processEvents()

    try:
        assert (
            required(dialog.layout(), "dialog layout").sizeConstraint()
            == QtWidgets.QLayout.SizeConstraint.SetMinimumSize
        )
        from rc_metastudio import adaptive_window

        assert (
            adaptive_window.adaptive_window_state(dialog).policy.archetype.value
            == "transactional"
        )
        assert dialog.minimumWidth() < dialog.sizeHint().width()
    finally:
        dialog.close()
        dialog.deleteLater()
    app.processEvents()
