# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Screen-bounded About dialog."""

from math import ceil
import platform
from html import escape
from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
from PyQt6.QtWidgets import QApplication
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QUrl, QEvent, QTimer
from PyQt6.QtGui import QPalette
from PyQt6.QtGui import QPixmap, QRegion, QTextDocument
from PyQt6.QtWidgets import QDialog, QDialogButtonBox

from rc_metastudio import adaptive_window, qt_layout
from rc_metastudio import application_metadata
from rc_metastudio.qt_object_guard import required

if TYPE_CHECKING:
    import ui_about_legal as _ui_about_legal
else:
    from rc_metastudio.forms import ui_about_legal as _ui_about_legal


ABOUT_TEXT = """<table align="center" cellpadding="12" cellspacing="0">
<tr><td bgcolor="#ffffff"><img src="rcms:about-logo" width="260" alt="RC MetaStudio"></td></tr>
</table>

<p>RC MetaStudio is open-source desktop software for advanced meta-analysis.</p>
<p>Developed and maintained by Research Consultancy (RC).</p>
<p>Ali Salman, Kaneez Fatima, Muhammad Shahzeb Khan, Tariq Jamal Siddiqi, Muhammad Shariq Usman, and contributors.</p>
<p>Licensed under GPL-3.0-or-later.</p>
<p>Version {version}<br>{runtime}</p>
<p><a href="https://github.com/AliSalman-et-al/rc-metastudio">Visit website</a></p>
<p><a href="https://github.com/AliSalman-et-al/rc-metastudio/issues">Report an issue</a>
&nbsp;&nbsp;·&nbsp;&nbsp;
<a href="https://github.com/AliSalman-et-al/rc-metastudio/blob/master/NOTICE.md">Credits and licenses</a></p>
"""


class AboutLegalDialog(QDialog, _ui_about_legal.Ui_AboutLegalDialog):
    def __init__(self, parent=None, *, r_version: str | None = None):
        super(AboutLegalDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('About RCMS')
        self.debug_info = f'RC MetaStudio {application_metadata.VERSION}\nPython {platform.python_version()} · Qt {QT_VERSION_STR} · PyQt {PYQT_VERSION_STR}\n{r_version or 'R runtime not loaded'}\n{platform.platform()}'
        debug_button = required(self.buttonBox.addButton('Copy debug info', QDialogButtonBox.ButtonRole.ActionRole), 'debug button')
        copied_timer = QTimer(debug_button)
        copied_timer.setSingleShot(True)
        copied_timer.timeout.connect(lambda: debug_button.setText('Copy debug info'))
        def copy_debug():
            self._copy_debug_info()
            debug_button.setText('Copied')
            copied_timer.start(2000)
        debug_button.clicked.connect(copy_debug)
        required(self.content_scroll_area.viewport(), "About viewport").setAutoFillBackground(False)
        document = required(self.content_scroll_area.document(), "About document")
        self._refresh_links()
        self.content_scroll_area.setAccessibleName("About RC MetaStudio")
        self.content_scroll_area.setOpenExternalLinks(True)
        self.content_scroll_area.setTabChangesFocus(True)
        close_button = self.buttonBox.button(QDialogButtonBox.StandardButton.Close)
        if close_button is None:
            raise RuntimeError("About dialog is missing its Close button")
        close_button.setObjectName("about_legal_close_button")
        close_button.setAccessibleName("Close About")
        close_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setTabOrder(self.content_scroll_area, close_button)
        layout = required(self.layout(), "About layout")
        margins = layout.contentsMargins()
        preferred_width = max(360, self.fontMetrics().averageCharWidth() * 76)
        # Measure independently of QTextBrowser's viewport-driven document width.
        measured_document = required(document.clone(), "About measurement document")
        measured_document.setTextWidth(preferred_width - margins.left() - margins.right())
        content_height = (
            ceil(measured_document.size().height()) + margins.top() + margins.bottom()
            + layout.spacing() + self.buttonBox.sizeHint().height()
        )
        adaptive_window.set_content_preferred_width(
            self, 360, preferred_width,
            preferred_height=max(self.fontMetrics().lineSpacing() * 22, content_height),
        )
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )

    def _copy_debug_info(self):
        from rc_metastudio import r_bridge, r_runtime
        text = self.debug_info
        if r_runtime.is_ready():
            text += '\nR libraries: ' + '; '.join(r_bridge.get_r_library_paths())
            for package in ('RCMetaR', 'metafor', 'meta', 'mada'):
                text += f'\n{package} {r_bridge.get_r_package_version(package)}'
        required(QApplication.clipboard(), 'clipboard').setText(text)

    def changeEvent(self, event: QEvent | None) -> None:
        super().changeEvent(event)
        if event is not None and event.type() in (QEvent.Type.PaletteChange, QEvent.Type.ApplicationPaletteChange, QEvent.Type.DevicePixelRatioChange) and hasattr(self, "content_scroll_area"):
            QTimer.singleShot(0, self._refresh_links)

    def _refresh_links(self):
        browser = self.content_scroll_area
        scrollbar = required(browser.verticalScrollBar(), "About scrollbar")
        position = scrollbar.value()
        logo = QPixmap(":/misc/about-logo.png")
        logo = logo.copy(QRegion(logo.mask()).boundingRect())
        # QTextBrowser otherwise reduces the full-resolution image with fast
        # sampling. Prepare screen pixels once and retain the native aspect ratio.
        ratio = self.devicePixelRatioF()
        logo = logo.scaledToWidth(round(260 * ratio), Qt.TransformationMode.SmoothTransformation)
        logo.setDevicePixelRatio(ratio)
        required(browser.document(), "About document").addResource(
            QTextDocument.ResourceType.ImageResource, QUrl("rcms:about-logo"), logo)
        color = qt_layout.readable_link_color(browser.palette()).name()
        browser.setHtml(ABOUT_TEXT.format(version=application_metadata.VERSION, runtime=escape(self.debug_info.split('\n', 1)[1]).replace('\n', '<br>')).replace('<a href=', '<a style="color:' + color + '" href='))
        scrollbar.setValue(position)
