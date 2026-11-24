"""Rendered labels, result-window disposal and retained-table observations."""

from typing import cast
from unittest.mock import patch
from xml.etree import ElementTree as ET
from PyQt6 import QtCore, QtGui, QtWidgets, sip
from PyQt6.QtSvg import QSvgRenderer

from tests.e2e.dialog_interaction import modal


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
    from rc_metastudio.results.formatting import numeric_cell, report_cell
    from tests.e2e.report_retention import assert_report, assert_retained_table
    assert_report(view)
    held = [(section, table) for section in view.results.sections for table in section.tables if table.title == title]
    assert len(held) == 1, (title, [(s.title, t.title) for s, t in held])
    section, original = held[0]
    title_in_report = original.title if section.title == original.title else section.title + ' — ' + original.title
    if any(table.title == title_in_report for table in view._report_tables):
        retained = assert_retained_table(view, section, original)
    else:
        quantities = {q for row in original.quantities for cell in row for q in cell}
        assert quantities, original.title
        retained = next(table for table in view._report_tables if table.title == 'Model fit'
                        and quantities <= {q for row in table.quantities for cell in row for q in cell})
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
    copied_rows = [[report_cell(cell) if numeric_cell(cell) else cell for cell in row] for row in rows]
    assert list(csv.reader(io.StringIO(app.clipboard().text()),delimiter='\t')) == [headers,*copied_rows]
    target = work / (label + '.csv')
    with patch.object(QtWidgets.QFileDialog,'getSaveFileName',return_value=(str(target),'CSV table (*.csv)')):
        view.export_table_action.trigger()
    with target.open(encoding='utf-8-sig',newline='') as stream:
        assert list(csv.reader(stream)) == [headers,*rows]
    record('reviewer-table-surface',view,title=title,label=label,headers=headers,rows=rows,export=str(target))


def export_formats(app, view, directory, family, record, invoke=None, *, include_title=False):
    directory.mkdir(parents=True, exist_ok=True)
    if invoke is None:
        if view._selected_plot() is None:
            assert view._last_plot_item is not None
            view.nav_tree.setCurrentItem(view._last_plot_item)
            app.processEvents()
        assert view.export_plot_action.isEnabled()
        def invoke(extension, _label):
            view.export_plot_action.trigger()
            app.processEvents()
    files = {}
    for extension, action_label in (
        ("pdf", "PDF"),
        ("png", "PNG"),
        ("tiff", "TIFF"),
        ("svg", "SVG"),
    ):
        destination = directory / (family + "." + extension)
        with patch.object(
            QtWidgets.QFileDialog,
            "getSaveFileName",
            return_value=(str(destination), ""),
        ) as picker:
            from rc_metastudio.results.plot_export import PlotExportDialog
            def accept_export(dialog):
                assert not dialog.include_title.isChecked()
                dialog.include_title.setChecked(include_title)
                dialog.format_control.setCurrentIndex(dialog.format_control.findData(extension))
                record('export-options', dialog, format=extension, dimensions=dialog.dimensions())
                dialog.accept()
            modal(app, PlotExportDialog, accept_export, lambda: invoke(extension, action_label))
        assert picker.call_args is not None
        name_filter = picker.call_args.args[3] if len(picker.call_args.args) > 3 else picker.call_args.kwargs.get("filter", "")
        assert f"*.{extension}" in name_filter, (extension, name_filter)
        assert destination.is_file(), destination
        rendered_pages: list[QtGui.QImage] = []
        if extension == "svg":
            renderer = QSvgRenderer(str(destination))
            assert renderer.isValid()
            rendered = QtGui.QImage(400, 400, QtGui.QImage.Format.Format_RGB32)
            rendered.fill(QtCore.Qt.GlobalColor.white)
            painter = QtGui.QPainter(rendered)
            renderer.render(painter)
            painter.end()
            rendered_pages.append(rendered)
        elif extension == "pdf":
            from PyQt6.QtPdf import QPdfDocument

            document = QPdfDocument(view)
            assert document.load(str(destination)) == QPdfDocument.Error.None_
            assert document.pageCount() > 0
            a4 = QtGui.QPageSize(QtGui.QPageSize.PageSizeId.A4).sizePoints()
            for page in range(document.pageCount()):
                if document.pageCount() > 1:
                    assert document.pagePointSize(page).toSize() == a4
                rendered_pages.append(document.render(page, QtCore.QSize(400, 400)))
            document.close()
        else:
            from PIL import Image

            with Image.open(destination) as image:
                assert image.width > 100 and image.height > 100
                if extension == "tiff":
                    dpi = tuple(float(value) for value in image.info.get("dpi", ()))
                    record("publication-raster-resolution", view, family=family,
                           pixels=image.size, dpi=dpi, exports={extension: str(destination)})
                    assert len(dpi) == 2 and min(dpi) >= 600, (family, "Publication TIFF is below 600 dpi", dpi)
                assert image.crop((0, 0, 1, 1)).convert("RGB").getpixel((0, 0)) == (255, 255, 255)
                image.load()
                assert (
                    min(
                        channel[0]
                        for channel in cast(tuple[tuple[int, int], ...],
                            image.resize((256, 256)).convert("RGB").getextrema())
                    )
                    < 200
                )
        for rendered in rendered_pages:
            assert not rendered.isNull()
            assert any(
                rendered.pixelColor(x, y).lightness() < 200
                for x in range(0, 400, 4)
                for y in range(0, 400, 4)
            ), "Export contains no visible plot content"
        files[extension] = str(destination)
        record(
            "family-export-decoded",
            view,
            family=family,
            format=extension,
            exports={extension: str(destination)},
        )
    return files
