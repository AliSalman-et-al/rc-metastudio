"""Copy selected evidence and render every header export for manual inspection."""
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtSvg import QSvgRenderer
from PIL import Image
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
shots = HERE/'screenshots'
exports = HERE/'exports'
previews = HERE/'export-previews'
for folder in (shots,exports,previews): folder.mkdir(exist_ok=True)
app = QtWidgets.QApplication([])
index = []
def retain(source, target, kind):
    shutil.copy2(source,target)
    index.append(dict(path=target.relative_to(HERE).as_posix(),source=str(source.relative_to(ROOT)),kind=kind,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
old = ROOT/'docs/ux-audit/2026-10-16-round6-reaudit'
retain(old/'screenshots/project-round6-polish-180-0-measured-wrapped-arm-headers.png',shots/'R6-03-R6-06-before-revman.png','native before')
work = HERE/'raw/headers-fixed-3'
steps = [json.loads(line) for line in (work/'steps.jsonl').read_text().splitlines()]
for step in steps:
    if step['action'] != 'measured-wrapped-arm-headers' or len(step['names'][0]) <= 80: continue
    case = 'twins' if len(step['names'][1])>80 else 'long'
    retain(work/step['captures'][0],shots/f"R6-03-R6-06-after-{step['style']}-{case}.png",'native after')
for style in ('default','revman','bmj'):
    for length,case in ((22,'long'),(94,'twins')):
        for extension in ('svg','pdf','png','tiff'):
            source=work/f'headers-{style}-{length}'/('full-arm.'+extension)
            if not source.exists(): continue
            name=f'{style}-{case}.{extension}'
            retain(source,exports/name,'actual export')
            target=previews/(name+'.png')
            if extension in ('png','tiff'):
                with Image.open(source) as original:
                    original.thumbnail((1800,2000))
                    original.convert('RGB').save(target)
            else:
                if extension=='pdf':
                    document=QPdfDocument(None)
                    assert document.load(str(source))==QPdfDocument.Error.None_
                    size=document.pagePointSize(0)
                    image=document.render(0,QtCore.QSize(1800,round(1800*size.height()/size.width())))
                    document.close()
                else:
                    renderer=QSvgRenderer(str(source))
                    size=renderer.defaultSize()
                    image=QtGui.QImage(1800,round(1800*size.height()/size.width()),QtGui.QImage.Format.Format_RGB32)
                    image.fill(QtCore.Qt.GlobalColor.white)
                    painter=QtGui.QPainter(image);renderer.render(painter);painter.end()
                assert image.save(str(target),'PNG')
            index.append(dict(path=target.relative_to(HERE).as_posix(),source=str(source.relative_to(ROOT)),kind='inspection rendering',sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
(HERE/'CURATED.json').write_text(json.dumps(index,indent=2)+'\n')
body=''.join(f'<figure><figcaption>{html.escape(row["path"])}</figcaption><a href="{row["path"]}"><img src="{row["path"]}" loading="lazy"></a></figure>' for row in index if row['kind'] in ('native before','native after','inspection rendering'))
(HERE/'contact-sheet.html').write_text('<!doctype html><html><meta charset="utf-8"><title>RCMS release fixes — inspected evidence</title><style>body{font:15px system-ui;margin:0;color:var(--foreground,#222)}figure{margin:20px 0}figcaption{font-weight:600;margin:8px 0}img{width:100%;height:auto;border:1px solid #888}a{color:inherit}</style><body><p>v0.5.0 release fixes: native before/after and actual exported figure renderings. Inspection findings are recorded in INSPECTIONS.md. Original exports and input/command receipts remain linked by CURATED.json.</p>'+body+'</body></html>')
print('Retained',len(index),'artifacts for manual inspection')
