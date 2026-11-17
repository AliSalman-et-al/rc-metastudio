# SPDX-License-Identifier: GPL-3.0-or-later
"""Copy and export the project's Zenodo software citation."""

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QFileDialog, QLabel, QVBoxLayout

from rc_metastudio.application_metadata import CITATION_AUTHORS, CITATION_DOI, CITATION_TITLE, CITATION_YEAR, CITATION_URL, VERSION, citation_text
from rc_metastudio.qt_object_guard import required
from rc_metastudio import app_error_handler


def citation_export(extension: str) -> str:
    if extension == '.bib':
        authors = ' and '.join(CITATION_AUTHORS)
        title = CITATION_TITLE.replace('RC MetaStudio', '{RC MetaStudio}', 1)
        return f"@misc{{rcmetastudio,\n  author = {{{authors}}},\n  title = {{{title}}},\n  howpublished = {{Zenodo}},\n  year = {{{CITATION_YEAR}}},\n  version = {{{VERSION}}},\n  url = {{{CITATION_URL}}},\n  doi = {{{CITATION_DOI}}}\n}}\n"
    if extension == '.ris':
        return 'TY  - COMP\n' + ''.join(f'AU  - {author}\n' for author in CITATION_AUTHORS) + f'TI  - {CITATION_TITLE}\nPB  - Zenodo\nPY  - {CITATION_YEAR}\nET  - {VERSION}\nUR  - {CITATION_URL}\nDO  - {CITATION_DOI}\nER  - \n'
    return '%0 Computer Program\n' + ''.join(f'%A {author}\n' for author in CITATION_AUTHORS) + f'%T {CITATION_TITLE}\n%I Zenodo\n%D {CITATION_YEAR}\n%7 {VERSION}\n%R {CITATION_DOI}\n%U https://doi.org/{CITATION_DOI}\n'


class CitationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Cite RC MetaStudio')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        browser = QLabel(self)
        browser.setWordWrap(True)
        browser.setTextFormat(Qt.TextFormat.PlainText)
        browser.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        browser.setObjectName("citationText")
        browser.setAccessibleName('Zenodo citation')
        browser.setText(citation_text())
        layout.addWidget(browser)
        layout.addWidget(QLabel("This DOI always points to the latest version.", self))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        copy_button = required(buttons.addButton('Copy citation', QDialogButtonBox.ButtonRole.ActionRole), 'copy citation button')
        copy_button.setMinimumWidth(copy_button.sizeHint().width())
        copied_timer = QTimer(copy_button)
        copied_timer.setSingleShot(True)
        copied_timer.timeout.connect(lambda: copy_button.setText('Copy citation'))
        def copy():
            required(QApplication.clipboard(), 'clipboard').setText(citation_text())
            copy_button.setText('Copied')
            copied_timer.start(2000)
        copy_button.clicked.connect(copy)
        required(buttons.addButton('Export…', QDialogButtonBox.ButtonRole.ActionRole), 'export citation button').clicked.connect(app_error_handler.safe_slot(self._export, parent=self))
        layout.addWidget(buttons)
        self.export_status = QLabel(self)
        self.export_status.hide()
        layout.addWidget(self.export_status)
        self.setMinimumWidth(520)
        self.adjustSize()

    def _export(self):
        filters = {'BibTeX (*.bib)': '.bib', 'RIS (*.ris)': '.ris', 'EndNote (*.enw)': '.enw'}
        path, selected = QFileDialog.getSaveFileName(self, 'Export citation', 'rc-metastudio.bib', ';;'.join(filters))
        if not path:
            return
        typed_extension = Path(path).suffix.lower()
        extension = typed_extension if typed_extension in filters.values() else filters[selected]
        destination = Path(path).with_suffix(extension)
        if str(destination) != path and destination.exists():
            from PyQt6.QtWidgets import QMessageBox
            if QMessageBox.question(self, 'Replace citation?', f'Replace {destination}?') != QMessageBox.StandardButton.Yes:
                return
        destination.write_text(citation_export(extension), encoding='utf-8')
        self.export_status.setText('Saved citation: ' + destination.name)
        self.export_status.show()
