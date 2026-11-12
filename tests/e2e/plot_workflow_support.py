"""Rendered labels, result-window disposal and retained-table observations."""

from xml.etree import ElementTree as ET
from PyQt6 import QtCore, QtWidgets, sip


def labels(path):
    return [''.join(node.itertext()) for node in ET.parse(path).iter('{http://www.w3.org/2000/svg}text')]


def close(app, view):
    view.close()
    app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    assert sip.isdeleted(view)


def check_table_surface(app, view, work, record, title, label):
    import csv
    import io
    from unittest.mock import patch
    from tests.e2e.report_retention import assert_report, assert_retained_table
    assert_report(view)
    held = [(section, table) for section in view.results.sections for table in section.tables if table.title == title]
    assert len(held) == 1, (title, [(s.title, t.title) for s, t in held])
    section, original = held[0]
    retained = assert_retained_table(view, section, original)
    view.tables_action.trigger()
    index = next(i for i,table in enumerate(view._report_tables) if table is retained)
    view.table_selector.setCurrentIndex(index)
    app.processEvents()
    table = view._report_tables[index]
    headers = [view.result_table.horizontalHeaderItem(i).text() for i in range(view.result_table.columnCount())]
    rows = [[view.result_table.item(r,c).text() for c in range(view.result_table.columnCount())] for r in range(view.result_table.rowCount())]
    assert [" ".join(h.split()) for h in headers] == [" ".join(h.split()) for h in retained.headers]
    assert rows == [list(row) for row in retained.rows]
    assert (table.headers, table.rows) == (retained.headers, retained.rows)
    headers = list(retained.headers)
    view.result_table.clearSelection()
    view.copy_table_action.trigger()
    assert list(csv.reader(io.StringIO(app.clipboard().text()),delimiter='\t')) == [headers,*rows]
    target = work / (label + '.csv')
    with patch.object(QtWidgets.QFileDialog,'getSaveFileName',return_value=(str(target),'CSV table (*.csv)')):
        view.export_table_action.trigger()
    with target.open(encoding='utf-8-sig',newline='') as stream:
        assert list(csv.reader(stream)) == [headers,*rows]
    record('reviewer-table-surface',view,title=title,label=label,headers=headers,rows=rows,export=str(target))
