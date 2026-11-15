"""Readable, editable Results tables through the real Qt/R workflow."""

from PyQt6 import QtCore, QtGui, QtWidgets
from tests.python.gui.qt_test_support import key_click


def run(app, window, work, root, record, analyze):
    assert window.open(str(root / 'sample_projects/amino.rcms'), raise_on_error=True)
    assert window.model.setData(window.model.index(0, window.model.NAME), 'Gonzalez <α> & colleagues')
    view = analyze(app, window, 'binary.random')
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
