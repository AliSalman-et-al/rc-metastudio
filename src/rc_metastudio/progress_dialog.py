from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QDialog, QLabel

from rc_metastudio import adaptive_window

if TYPE_CHECKING:
    import ui_progress_dialog as _ui_progress_dialog
else:
    from rc_metastudio.forms import ui_progress_dialog as _ui_progress_dialog


class AnalysisProgressDialog(QDialog, _ui_progress_dialog.Ui_ProgressDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        context = parent.windowTitle() if parent is not None else "Analysis"
        self.setWindowTitle(context)
        label = QLabel(f"Fitting model and drawing plots…\n{context}", self)
        label.setWordWrap(True)
        self.verticalLayout.insertWidget(0, label)
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSIENT
        )


def hide_once(progress_dialog):
    if getattr(progress_dialog, "_rcms_hidden", False):
        return
    progress_dialog.hide()
    progress_dialog._rcms_hidden = True
