from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QDialog, QLabel, QPushButton

from rc_metastudio import adaptive_window

if TYPE_CHECKING:
    import ui_progress_dialog as _ui_progress_dialog
else:
    from rc_metastudio.forms import ui_progress_dialog as _ui_progress_dialog


class AnalysisProgressDialog(QDialog, _ui_progress_dialog.Ui_ProgressDialog):
    stop_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setModal(False)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.stage_label = QLabel("Preparing analysis")
        self.stage_label.setObjectName("analysis_progress_stage")
        self.stage_label.setAccessibleName("Analysis progress")
        self.stage_label.setWordWrap(True)
        self.verticalLayout.insertWidget(0, self.stage_label)
        self.stop_button = QPushButton("Stop analysis", self)
        self.stop_button.setAccessibleName("Stop analysis")
        self.stop_button.clicked.connect(self.request_stop)
        self.verticalLayout.addWidget(self.stop_button)
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSIENT
        )

    def set_stage(self, stage: str) -> None:
        self.stage_label.setText(str(stage))

    def request_stop(self) -> None:
        if not self.stop_button.isEnabled():
            return
        self.stop_button.setEnabled(False)
        self.set_stage("Stopping analysis…")
        self.stop_requested.emit()

    def closeEvent(  # ty: ignore[invalid-method-override] -- PyQt6 stubs conflict with this runtime-supported override.
        self, event: QCloseEvent | None
    ) -> None:
        if event is not None:
            event.ignore()
            self.request_stop()


def hide_once(progress_dialog):
    if getattr(progress_dialog, "_rcms_hidden", False):
        return
    progress_dialog.hide()
    progress_dialog._rcms_hidden = True
