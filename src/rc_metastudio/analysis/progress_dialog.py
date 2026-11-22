from typing import TYPE_CHECKING
from contextlib import ExitStack

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QHideEvent, QShowEvent
from PyQt6.QtWidgets import QApplication, QDialog, QLabel, QPushButton

from rc_metastudio import adaptive_window
from rc_metastudio.qt_layout import configure_context_label

if TYPE_CHECKING:
    import ui_progress_dialog as _ui_progress_dialog
else:
    from rc_metastudio.forms import ui_progress_dialog as _ui_progress_dialog


class AnalysisProgressDialog(QDialog, _ui_progress_dialog.Ui_ProgressDialog):
    def __init__(self, parent=None, *, operation="Fitting model and drawing plots…", context="", blocking=True,
                 cancellable=False):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        self.setAccessibleName(operation)
        self.setAccessibleDescription(context)
        self._blocking = blocking
        self._wait_cursor_active = False
        self._tracking = ExitStack()
        self.cancelled = False
        self.cancel_button = QPushButton("Cancel", self) if cancellable else None
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
        if blocking or cancellable:
            self.setWindowModality(Qt.WindowModality.ApplicationModal)
        if self.cancel_button is not None:
            self.cancel_button.clicked.connect(self.reject)
            self.verticalLayout.addWidget(self.cancel_button)
        elif blocking:
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
        self._tracking.close()
        if self._wait_cursor_active:
            QApplication.restoreOverrideCursor()
            self._wait_cursor_active = False
        super().hideEvent(event)

    def start_tracking(self) -> None:
        if self.cancel_button is not None:
            from rc_metastudio import r_bridge
            self._tracking.enter_context(r_bridge.sequential_progress(self.track_fit))

    def track_fit(self, index: int, total: int) -> bool:
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(max(0, index - 1))
        if index > total:
            self.operation_label.setText("Drawing plots…")
            if self.cancel_button is not None:
                self.cancel_button.setEnabled(False)
        else:
            self.operation_label.setText(f"Fitting {index} of {total}…" if index else "Fitting overall model…")
        QApplication.processEvents()
        return not self.cancelled

    def reject(self):
        if self.cancel_button is not None:
            self.cancelled = True
            self.cancel_button.setEnabled(False)

    def closeEvent(self, event: QCloseEvent | None) -> None:
        if event is not None:
            event.ignore()


def dispose(progress):
    progress.hide()
    progress.deleteLater()
