"""Readable, editable Results tables through the real Qt/R workflow."""

from PyQt6 import QtCore, QtGui, QtWidgets
from tests.python.gui.qt_test_support import key_click
from unittest.mock import patch
import csv


def check_values_export(view, work, record, label):
    source = [t for s in view.results.sections for t in s.tables]
    for table in source:
        if any(h.startswith('Lower bound') and h.endswith('% CI)') for h in table.headers) or table.title == 'Heterogeneity':
            assert table.quantities, (label, table.title, 'numeric attributes lost')
    for index, table in enumerate(view._report_tables):
        view.table_selector.setCurrentIndex(index)
        assert view.export_values_action.isEnabled() == bool(table.quantities)
        if not table.quantities:
            continue
        path = work / f'{label}-{index}-values.csv'
        with patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(str(path), 'csv')):
            view.export_values_action.trigger()
        with path.open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        expected = [(cell, q) for row, numbers in zip(table.rows, table.quantities)
                    for cell, quantities in zip(row, numbers) for q in quantities]
        assert len(rows) == len(expected)
        for exported, (cell, q) in zip(rows, expected):
            assert '—' not in exported['Row'] and ' / (log scale)' not in exported['Row'], exported['Row']
            assert exported['Display'] == cell
            assert exported['Quantity'] == q.role
            assert exported['Scale'] == q.scale
            assert (float(exported['Value']) if exported['Value'] else None) == q.value
            assert (float(exported['Level']) if exported['Level'] else None) == q.level
        record('results-values-export', view, analysis=label, table=table.title, path=str(path), values=rows)
    # Renaming presentation labels must not affect primary-row routing.
    from dataclasses import replace
    from rc_metastudio.manuscript_report import ManuscriptReport
    renamed = replace(view.results, sections=tuple(replace(s, tables=tuple(
        replace(t, headers=tuple('Renamed estimate' if h == 'Estimate' else 'Renamed interval '+str(i)
                                if h.startswith(('Lower bound', 'Upper bound')) else h for i, h in enumerate(t.headers)))
        for t in s.tables)) for s in view.results.sections))
    report = ManuscriptReport.from_result(renamed)
    assert report.sections[0].tables[0].rows == view.manuscript.sections[0].tables[0].rows


def run(app, window, work, root, record, analyze):
    assert window.open(str(root / 'sample_projects/amino.rcms'), raise_on_error=True)
    assert window.model.setData(window.model.index(0, window.model.NAME), 'Gonzalez <α> & colleagues')
    view = analyze(app, window, 'binary.random')
    check_values_export(view, work, record, 'binary')
    view.tables_action.trigger()
    index = next(i for i, table in enumerate(view._report_tables) if table.title == 'Study results')
    view.table_selector.setCurrentIndex(index)
    table = view._report_tables[index]
    key_click(view.result_table, QtCore.Qt.Key.Key_C, QtCore.Qt.KeyboardModifier.ControlModifier)
    mime = app.clipboard().mimeData()
    assert mime is not None and mime.hasHtml() and mime.hasText()
    assert '&lt;α&gt; &amp;' in mime.html()
    editor = QtWidgets.QTextEdit()
    editor.insertHtml(mime.html())
    cursor = editor.textCursor()
    cursor.movePosition(QtGui.QTextCursor.MoveOperation.Start)
    cursor.movePosition(QtGui.QTextCursor.MoveOperation.NextBlock)
    imported = cursor.currentTable()
    assert imported is not None and imported.rows() == len(table.rows) + 1
    assert 'Gonzalez <α> & colleagues' in editor.toPlainText()
    record('results-rich-table-paste', view, html=mime.html(), plain=mime.text(), editable_rows=imported.rows())
    view.result_table.clearSelection()
    view.result_table.setRangeSelected(QtWidgets.QTableWidgetSelectionRange(0, 0, 1, 1), True)
    key_click(view.result_table, QtCore.Qt.Key.Key_C, QtCore.Qt.KeyboardModifier.ControlModifier)
    mime = app.clipboard().mimeData()
    assert mime is not None
    selected = QtWidgets.QTextEdit()
    selected.insertHtml(mime.html())
    plain = mime.text()
    assert plain == '\n'.join('\t'.join(row[:2]) for row in table.rows[:2]) + '\n'
    assert table.headers[0] not in plain
    assert 'Gonzalez <α> & colleagues' in selected.toPlainText()
    record('results-copy-rectangle', view, html=mime.html(), plain=plain)
    editor.close()
    selected.close()
    view.close()
