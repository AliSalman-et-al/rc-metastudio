"""Render retained publication exports for visual inspection, without editing them."""
import hashlib
import json
from pathlib import Path

from PIL import Image
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtSvg import QSvgRenderer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
receipts = json.loads((HERE / 'REVIEW1-NATIVE.json').read_text())
app = QtWidgets.QApplication([])
output = HERE / 'export-previews'
output.mkdir(exist_ok=True)
rows = []
for label, prefix in [('review1-publication-audit-round3-presentation-twoarm-proportion', 'twoarm-proportion-bmj-'),
                      ('review1-publication-audit-round3-presentation-diagnostic', 'diagnostic-revman-')]:
    run = receipts[label]
    folder = ROOT / run['evidence']
    for step in run['observed']:
        if step['action'] != 'family-export-decoded' or not step['family'].startswith(prefix):
            continue
        if prefix.startswith('diagnostic') and 'Sens.forest' not in step['family']:
            continue
        extension = step['format']
        original = folder / 'workflow' / Path(step['exports'][extension]).name
        assert original.is_file(), original
        target = output / (original.stem + '-' + extension + '.png')
        if extension in {'png','tiff'}:
            with Image.open(original) as source:
                dimensions = source.size
                source.thumbnail((1800, 2000), Image.Resampling.LANCZOS)
                source.convert('RGB').save(target)
        else:
            if extension == 'pdf':
                document = QPdfDocument(app)
                assert document.load(str(original)) == QPdfDocument.Error.None_
                size = document.pagePointSize(0)
                dimensions = (size.width(), size.height())
                preview = document.render(0, QtCore.QSize(1800, round(1800*size.height()/size.width())))
                document.close()
            else:
                renderer = QSvgRenderer(str(original))
                assert renderer.isValid()
                size = renderer.defaultSize()
                dimensions = (size.width(), size.height())
                preview = QtGui.QImage(1800, round(1800*size.height()/size.width()), QtGui.QImage.Format.Format_RGB32)
                preview.fill(QtCore.Qt.GlobalColor.white)
                painter = QtGui.QPainter(preview)
                renderer.render(painter)
                painter.end()
            assert preview.save(str(target))
        rows.append(dict(label=label, family=step['family'], format=extension,
                         original=str(original.relative_to(ROOT)), dimensions=dimensions,
                         original_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
                         preview=str(target.relative_to(HERE)), preview_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                         purpose='Derived review preview; original publication export unchanged'))
(HERE / 'REVIEW1-EXPORTS.json').write_text(json.dumps(rows, indent=2)+'\n')
print('Retained',len(rows),'publication export previews for inspection')
