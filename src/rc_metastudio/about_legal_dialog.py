# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Screen-bounded About dialog."""

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap, QRegion, QTextDocument
from PyQt6.QtWidgets import QDialog, QDialogButtonBox

from rc_metastudio import adaptive_window
from rc_metastudio import application_metadata
from rc_metastudio.qt_object_guard import required

if TYPE_CHECKING:
    import ui_about_legal as _ui_about_legal
else:
    from rc_metastudio.forms import ui_about_legal as _ui_about_legal


ABOUT_TEXT = """<table align="center" bgcolor="white" cellpadding="12" cellspacing="0">
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
        logo = QPixmap(":/misc/about-logo.png")
        logo = logo.copy(QRegion(logo.mask()).boundingRect())
        required(self.content_scroll_area.document(), "About document").addResource(
            QTextDocument.ResourceType.ImageResource, QUrl("rcms:about-logo"), logo
        )
        self.content_scroll_area.setHtml(
            ABOUT_TEXT.format(version=application_metadata.VERSION)
        )
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
        adaptive_window.set_content_preferred_width(
            self, 360, self.fontMetrics().averageCharWidth() * 76,
            preferred_height=self.fontMetrics().lineSpacing() * 22,
        )
        self._layout_controller = adaptive_window.register_adaptive_window(
            self, adaptive_window.WindowRole.TRANSACTIONAL
        )
