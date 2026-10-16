"""Render retained actual SVGs as explicitly derived export inspection images."""
from pathlib import Path
import json,hashlib
from PyQt6 import QtCore,QtGui,QtSvg,QtWidgets
HERE=Path(__file__).resolve().parent
app=QtWidgets.QApplication([])
rows=json.loads((HERE/'EXPORT-EVIDENCE.json').read_text())
for row in rows:
 source=HERE/row['path'];renderer=QtSvg.QSvgRenderer(str(source));assert renderer.isValid()
 size=renderer.defaultSize();image=QtGui.QImage(size,QtGui.QImage.Format.Format_ARGB32);image.fill(QtCore.Qt.GlobalColor.white)
 painter=QtGui.QPainter(image);renderer.render(painter);painter.end()
 dest=HERE/'screenshots'/('export-'+source.stem+'.png');assert image.save(str(dest))
 row['rendered']=str(dest.relative_to(HERE));row['rendered_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest();row['rendering']='Derived QtSvg rendering of actual retained vector, not a native screenshot';row['qt']=QtCore.qVersion()
(HERE/'EXPORT-EVIDENCE.json').write_text(json.dumps(rows,indent=2)+'\n')
