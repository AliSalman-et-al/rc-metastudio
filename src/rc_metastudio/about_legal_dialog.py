# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Screen-bounded About dialog."""

from math import ceil
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QUrl, QEvent, QTimer
from PyQt6.QtGui import QPalette, QPainter
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
<tr><td><img src="rcms:about-logo" width="260" height="31" alt="RC MetaStudio"></td></tr>
</table>
<p>Version {version}</p>
<p>RC MetaStudio is open-source desktop software for advanced meta-analysis.</p>
<p>Developed and maintained by Research Consultancy (RC).<br>
Ali Salman and RC MetaStudio contributors.</p>
<p>Licensed under GPL-3.0-or-later.</p>
<p><a href="https://github.com/AliSalman-et-al/rc-metastudio/issues">Report an issue</a>
&nbsp;&nbsp;·&nbsp;&nbsp;
<a href="https://github.com/AliSalman-et-al/rc-metastudio/blob/master/NOTICE.md">Credits and licenses</a></p>
"""


class AboutLegalDialog(QDialog, _ui_about_legal.Ui_AboutLegalDialog):
    def __init__(self, parent=None):
        super(AboutLegalDialog, self).__init__(parent)
        self.setupUi(self)
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

    def changeEvent(self, event: QEvent | None) -> None:
        super().changeEvent(event)
        if event is not None and event.type() in (QEvent.Type.PaletteChange, QEvent.Type.ApplicationPaletteChange) and hasattr(self, "content_scroll_area"):
            QTimer.singleShot(0, self._refresh_links)

    def _refresh_links(self):
        browser = self.content_scroll_area
        scrollbar = required(browser.verticalScrollBar(), "About scrollbar")
        position = scrollbar.value()
        logo = QPixmap(":/misc/about-logo.png")
        logo = logo.copy(QRegion(logo.mask()).boundingRect())
        if browser.palette().color(QPalette.ColorRole.Base).lightness() < 128:
            painter = QPainter(logo)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(logo.rect(), browser.palette().color(QPalette.ColorRole.Text))
            painter.end()
        required(browser.document(), "About document").addResource(
            QTextDocument.ResourceType.ImageResource, QUrl("rcms:about-logo"), logo)
        color = qt_layout.readable_link_color(browser.palette()).name()
        browser.setHtml(ABOUT_TEXT.format(version=application_metadata.VERSION).replace('<a href=', '<a style="color:' + color + '" href='))
        scrollbar.setValue(position)
