"""Prove that a real tall forest PDF keeps complete rows, repeated context, and distinct captions."""

import copy
from collections import Counter
import json
import re
from pathlib import Path
from uuid import uuid4
from tests.e2e.pdf_inspection import pdf_image_count, pdf_words, render_pdf_page
from unittest.mock import patch
from xml.etree import ElementTree as ET

from PyQt6 import QtCore, QtGui, QtWidgets


def run(app, window, work, root, record, analyze):
    from rc_metastudio.results.report_export import write_pdf
    from rc_metastudio.results.svg_rendering import svg_bytes_for_qt
    from PyQt6.QtSvg import QSvgRenderer

    assert window.open(str(root / 'tests/fixtures/desktop-projects/amino.rcms'), raise_on_error=True)
    templates = copy.deepcopy(window.model.current_sheet.rows)
    for _ in range(4):
        for template in templates:
            row = copy.deepcopy(template)
            row.id = uuid4().hex
            window.model.current_sheet.rows.append(row)
    for index, row in enumerate(window.model.current_sheet.rows):
        row.label = f'Row{index:03}'
    window.model.set_current_sheet(window.model.current_sheet_id)
    fixture = work / 'tall-forest.rcms'
    with patch.object(QtWidgets.QFileDialog, 'getSaveFileName', return_value=(str(fixture), '')):
        assert window.save_as()
    view = analyze(app, window, 'binary.random')
    record('split-forest-analysis', view, input=str(fixture), rows=len(window.model.current_sheet.rows))
    path = work / 'tall-forest.pdf'
    write_pdf(view.manuscript, path)
    pages = pdf_words(path)
    (work / 'tall-forest-layout.json').write_text(json.dumps(pages, ensure_ascii=False), encoding='utf-8')
    checked = []
    study_rows = Counter()
    for number, page in enumerate(pages, 1):
        words = page.words
        captions = [word for word in words if word.text == 'Figure']
        if not captions:
            continue
        tokens = [word.text for word in words]
        panel_rows = [match[0] for token in tokens if (match := re.match(r"Row\d{3}\b", token))]
        assert len(panel_rows) >= 2, (number, "Figure page needs study rows")
        assert "Study" in tokens and "ratio" in tokens, (number, "Missing headers or axis")
        study_rows.update(panel_rows)
        caption_top = max(word.top for word in captions)
        caption_words = [word for word in words if abs(word.top - caption_top) < .5]
        caption_bottom = max(word.bottom for word in caption_words)
        screenshot = work / f'tall-forest-page-{number}.png'
        render_pdf_page(path, screenshot, number - 1, long_edge=1400)
        image = QtGui.QImage(str(screenshot))
        assert not image.isNull()
        first_row = round((caption_bottom + 4) * image.height() / page.height)
        colored = sum(image.pixelColor(x, y).value() < 245
                      for y in range(first_row, image.height()) for x in range(image.width()))
        assert colored == 0, (number, 'Figure spills below caption', colored)
        checked.append(dict(page=number, caption_top=caption_top, caption_bottom=caption_bottom,
                            below_caption_pixels=colored, capture=str(screenshot)))
    assert len(checked) >= 2, 'Fixture must split its forest across pages'
    expected = Counter(f"Row{i:03}" for i in range(len(window.model.current_sheet.rows)))
    assert study_rows == expected, (expected - study_rows, study_rows - expected)
    raster_images = pdf_image_count(path)
    assert raster_images == 0, ('PDF forest was rasterized', raster_images)
    record('split-forest-pdf', view, pdf=str(path), pages=checked, raster_images=raster_images)

    # Empty plot viewports must hide their contents, including in Qt.
    figure = view.manuscript.figures[0]
    source = Path(figure.display_image or figure.value)
    tree = ET.parse(source)
    for clip in tree.iter('{http://www.w3.org/2000/svg}clipPath'):
        for rectangle in clip:
            rectangle.set('width', '0')
    empty = work / 'zero-width-clips.svg'
    tree.write(empty, encoding='utf-8')
    renderer = QSvgRenderer(svg_bytes_for_qt(empty))
    image = QtGui.QImage(600, 800, QtGui.QImage.Format.Format_RGB32)
    image.fill(QtCore.Qt.GlobalColor.white)
    painter = QtGui.QPainter(image)
    renderer.render(painter)
    painter.end()
    assert all(image.pixelColor(x, y) == QtGui.QColor('white')
               for y in range(image.height()) for x in range(image.width()))
    record('zero-width-svg-clip', view, source=str(empty), hidden=True)
    view.close()
