from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QHideEvent, QShowEvent
from PyQt6.QtWidgets import QApplication, QDialog, QLabel

from rc_metastudio import adaptive_window
from rc_metastudio.qt_layout import configure_context_label

if TYPE_CHECKING:
    import ui_progress_dialog as _ui_progress_dialog
else:
    from rc_metastudio.forms import ui_progress_dialog as _ui_progress_dialog


class AnalysisProgressDialog(QDialog, _ui_progress_dialog.Ui_ProgressDialog):
    def __init__(self, parent=None, *, operation="Fitting model and drawing plots…", context="", blocking=True):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setAccessibleName(operation)
        self.setAccessibleDescription(context)
        self._blocking = blocking
        self._wait_cursor_active = False
        self.operation_label = QLabel(operation, self)
        self.operation_label.setWordWrap(True)
        font = self.operation_label.font()
        font.setBold(True)
        self.operation_label.setFont(font)
        self.verticalLayout.insertWidget(0, self.operation_label)
        if context:
            label = QLabel(context, self)
            configure_context_label(label)
            self.verticalLayout.insertWidget(1, label)
        self.verticalLayout.insertSpacing(self.verticalLayout.count() - 1, self.fontMetrics().lineSpacing() // 2)
        if blocking:
            explanation = QLabel("The window will respond again when the analysis finishes.", self)
            explanation.setWordWrap(True)
            self.verticalLayout.addWidget(explanation)
        self.progress_bar.setAccessibleName(operation)
        self.progress_bar.setTextVisible(False)
        adaptive_window.set_content_preferred_width(
            self, 280, self.fontMetrics().averageCharWidth() * 48
        )
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSIENT
        )

    def showEvent(self, event: QShowEvent | None) -> None:
        super().showEvent(event)
        if self._blocking and not self._wait_cursor_active:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self._wait_cursor_active = True

    def hideEvent(self, event: QHideEvent | None) -> None:
        if self._wait_cursor_active:
            QApplication.restoreOverrideCursor()
            self._wait_cursor_active = False
        super().hideEvent(event)

    def reject(self):
        pass

    def closeEvent(self, event: QCloseEvent | None) -> None:
        if event is not None:
            event.ignore()


def hide_once(progress_dialog):
    if getattr(progress_dialog, "_rcms_hidden", False):
        return
    progress_dialog.hide()
    progress_dialog._rcms_hidden = True


def dispose(progress):
    hide_once(progress)
    progress.deleteLater()
