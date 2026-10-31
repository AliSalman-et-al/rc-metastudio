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
                assert doc.paragraphs[0].text == view.results.identity
                tables = [t for s in view.results.sections for t in s.tables]
                assert len(doc.tables) == len(tables)
                for actual, expected in zip(doc.tables, tables):
                    assert [[c.text for c in r.cells] for r in actual.rows] == [list(expected.headers), *map(list, expected.rows)]
                assert len(doc.inline_shapes) == len(view.results.images)
                assert all(round(s.width / 36000) in (85, 180) for s in doc.inline_shapes)
                text = '\n'.join(p.text for p in doc.paragraphs)
            else:
                text = subprocess.check_output(['pdftotext', '-layout', str(path), '-']).decode()
            assert 'Methods' in text and 'RC MetaStudio' in text
            for line in view.results.details.splitlines():
                if line.strip():
                    assert ' '.join(unicodedata.normalize('NFKC', line).split()) in ' '.join(unicodedata.normalize('NFKC', text).split()), (line, text)
            record('manuscript-export-' + sample + '-' + suffix, view, exported=str(path))
        view.close()
