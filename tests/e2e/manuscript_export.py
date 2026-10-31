"""Reopen real manuscript exports and compare with the executed result."""
from unittest.mock import patch
import subprocess
import unicodedata
from docx import Document
from PyQt6 import QtWidgets


def run(app, window, work, root, record, analyze):
    for sample, method in (("amino", "binary.random"), ("continuous", "continuous.random"), ("lymph", "diagnostic.random")):
        window.workspace.mark_saved()
        assert window.open(str(root / 'sample_projects' / (sample + '.rcms')), raise_on_error=True)
        view = analyze(app, window, method)
        for suffix in ('pdf', 'docx'):
            path = work / (sample + '.' + suffix)
            def picker(*args, **kwargs):
                dialog = QtWidgets.QFileDialog(view)
                dialog.setOption(QtWidgets.QFileDialog.Option.DontUseNativeDialog)
                dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
                dialog.setNameFilter('Report (*.' + suffix + ')')
                dialog.selectFile(str(path))
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, dialog.accept)
                assert dialog.exec()
                return dialog.selectedFiles()[0], dialog.selectedNameFilter()
            with patch.object(QtWidgets.QFileDialog, 'getSaveFileName', side_effect=picker):
                view.export_report_action.trigger()
            assert path.exists()
            if suffix == 'docx':
                doc = Document(path)
                assert doc.paragraphs[0].text == view.manuscript.title
                assert 'Table 1.' in '\n'.join(p.text for p in doc.paragraphs)
                assert doc.tables[0].rows[0].cells[0].text == 'Statistic'
                assert len(doc.inline_shapes) == len(view.results.images)
                assert all(round(s.width / 36000) in (85, 180) for s in doc.inline_shapes)
                text = '\n'.join(p.text for p in doc.paragraphs)
            else:
                text = subprocess.check_output(['pdftotext', '-layout', str(path), '-']).decode()
            assert 'Methods' in text and 'RC MetaStudio' in text
            normalized = ' '.join(unicodedata.normalize('NFKC', text).split())
            for prose in (view.manuscript.methods, view.manuscript.results):
                assert ' '.join(unicodedata.normalize('NFKC', prose).split()) in normalized
            assert view.manuscript_methods.toPlainText() == view.manuscript.methods
            assert view.manuscript_results.toPlainText() == view.manuscript.results
            assert all(value not in text for value in ('executed settings', 'Project:', '.rcms'))
            assert 'Supplementary details' in text
            if sample == 'amino':
                assert view.manuscript.title == 'clinical failure: random-effects meta-analysis (odds ratio)'
                assert 'The pooled odds ratio was 0.770 (95% CI 0.485 to 1.222; p = 0.267).' in view.manuscript.results
                assert '19 studies were included' in view.manuscript.results
                assert '-0.262' in normalized
            record('manuscript-export-' + sample + '-' + suffix, view, exported=str(path))
        view.close()
