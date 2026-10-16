"""Inspect complete Qt-rendered vector footers beyond native viewport bounds."""
import hashlib
import json
from pathlib import Path
import re

from PyQt6.QtCore import QT_VERSION_STR, qVersion
from PyQt6.QtGui import QGuiApplication,QImage,QPainter
from PyQt6.QtSvg import QSvgRenderer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
app = QGuiApplication([])
rows = []
for label,action in [('reviewer-predictions-visible-page','reviewer-prediction-after'),('reviewer-colours-current','reviewer-colour-exports')]:
    receipt = json.loads((HERE/'raw'/(label+'.json')).read_text())
    assert receipt['exit_code'] == 0
    directory = Path(re.search(r'^Evidence: (.+)$',(HERE/'raw'/receipt['log']).read_text(),re.M)[1])
    for step in map(json.loads,(directory/'steps.jsonl').read_text().splitlines()):
        if step['action'] != action:
            continue
        source = next(directory/name for name in step['artifacts'].values() if name.endswith('.svg'))
        renderer = QSvgRenderer(str(source))
        assert renderer.isValid(),source
        size = renderer.defaultSize()
        raster = QImage(size,QImage.Format.Format_RGB32)
        raster.fill(0xffffffff)
        painter=QPainter(raster);renderer.render(painter);painter.end()
        target=HERE/'raw'/f'reviewer-vector-footer-{len(rows):02d}.png'
        footer=raster.copy(0,max(0,raster.height()-650),raster.width(),min(650,raster.height()))
        assert footer.save(str(target))
        rows.append(dict(source=str(source.relative_to(ROOT)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            image=str(target.relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            qt_compiled=QT_VERSION_STR,qt_runtime=qVersion(),label=label,step=step['step'],measure=step.get('measure'),workflow=step.get('workflow'),
            style=step.get('style'),scenario=step.get('scenario'),size=[size.width(),size.height()]))
(HERE/'REVIEWER-VECTOR-FOOTERS.json').write_text(json.dumps(rows,indent=2)+'\n')
app.quit()
print(len(rows),'actual SVGs rendered through QtSvg; lower-device crops retained with input/output hashes.')
