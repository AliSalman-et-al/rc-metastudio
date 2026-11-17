"""Prove that a real tall forest PDF keeps figures out of its caption band."""

import copy
import subprocess
from pathlib import Path
from uuid import uuid4
from scripts.verification_evidence import desktop_tool_executable
from unittest.mock import patch
from xml.etree import ElementTree as ET

from PyQt6 import QtCore, QtGui, QtWidgets


def run(app, window, work, root, record, analyze):
    from rc_metastudio.manuscript_report import write_pdf
    from rc_metastudio.svg_rendering import svg_bytes_for_qt
    from PyQt6.QtSvg import QSvgRenderer

    assert window.open(str(root / 'sample_projects/amino.rcms'), raise_on_error=True)
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
    xml = subprocess.check_output([desktop_tool_executable('pdftotext'), '-bbox', str(path), '-'])
    (work / 'tall-forest-layout.xml').write_bytes(xml)
    pages = ET.fromstring(xml).findall('.//{*}page')
    checked = []
    for number, page in enumerate(pages, 1):
        words = page.findall('.//{*}word')
        captions = [word for word in words if word.text == 'Figure']
        if not captions:
            continue
        caption_top = max(float(word.attrib['yMin']) for word in captions)
        caption_words = [word for word in words if abs(float(word.attrib['yMin']) - caption_top) < .5]
        caption_bottom = max(float(word.attrib['yMax']) for word in caption_words)
        prefix = work / f'tall-forest-page-{number}'
        subprocess.run([desktop_tool_executable('pdftoppm'), '-f', str(number), '-l', str(number), '-singlefile',
                        '-scale-to', '1400', '-png', str(path), str(prefix)], check=True)
        image = QtGui.QImage(str(prefix.with_suffix('.png')))
        assert not image.isNull()
        first_row = round((caption_bottom + 4) * image.height() / float(page.attrib['height']))
        colored = sum(image.pixelColor(x, y).value() < 245
                      for y in range(first_row, image.height()) for x in range(image.width()))
        assert colored == 0, (number, 'Figure spills below caption', colored)
        checked.append(dict(page=number, caption_top=caption_top, caption_bottom=caption_bottom,
                            below_caption_pixels=colored, capture=str(prefix.with_suffix('.png'))))
    assert len(checked) >= 2, 'Fixture must split its forest across pages'
    listing = subprocess.check_output([desktop_tool_executable('pdfimages'), '-list', str(path)], text=True)
    assert len(listing.strip().splitlines()) == 2, 'PDF forest was rasterized'
    record('split-forest-pdf', view, pdf=str(path), pages=checked, raster_images=0)

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
