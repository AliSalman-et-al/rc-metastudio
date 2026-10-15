"""Build the reviewable local contact sheet from curated image inventories."""
from pathlib import Path
import json,html
HERE=Path(__file__).resolve().parent
sections=[]
for index in sorted(HERE.glob('SELECTED-*.json')):
 rows=json.loads(index.read_text());name=index.stem.removeprefix('SELECTED-')
 sections.append('<section><h2>'+html.escape(name)+'</h2><div class="grid">'+''.join('<figure><a href="'+html.escape(r['path'])+'"><img loading="lazy" src="'+html.escape(r['path'])+'"></a><figcaption>'+html.escape(Path(r['path']).name)+'</figcaption></figure>' for r in rows)+'</div></section>')
(HERE/'contact-sheet.html').write_text('<!doctype html><meta charset="utf-8"><title>RCMS 0.5.0 native re-audit</title><style>body{font:15px system-ui;max-width:1800px;margin:24px auto;background:#eee;color:#222}h2{margin-top:36px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(550px,1fr));gap:12px}figure{margin:0;background:white;padding:10px}img{width:100%;height:auto}figcaption{overflow-wrap:anywhere;font-size:12px}</style><h1>RC MetaStudio 0.5.0 — independent native re-audit</h1><p>Click a frame for its original resolution. See REPORT.md and INSPECTIONS.md for judgments and limits. Captures are native X11 unless explicitly described otherwise. This sheet indexes curated frames; inclusion alone is not acceptance.</p>'+''.join(sections))
print('sections',len(sections))
