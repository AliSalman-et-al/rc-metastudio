"""Build the reviewable local contact sheet from curated image inventories."""
from pathlib import Path
import json,html
from PIL import Image
HERE=Path(__file__).resolve().parent
sections=[];options=[]
(HERE/'thumbnails').mkdir(exist_ok=True)
for index in sorted(HERE.glob('SELECTED-*.json')):
 rows=json.loads(index.read_text());name=index.stem.removeprefix('SELECTED-')
 for row in rows:
  target=HERE/'thumbnails'/(Path(row['path']).stem+'.jpg')
  source=Image.open(HERE/row['path']).convert('RGB');source.thumbnail((800,800));source.save(target,quality=85,optimize=True)
  row['thumbnail']=str(target.relative_to(HERE))
 options.append('<option value="'+html.escape(name)+'">'+html.escape(name)+' ('+str(len(rows))+')</option>')
 sections.append('<section data-group="'+html.escape(name)+'"><h2>'+html.escape(name)+'</h2><div class="grid">'+''.join('<figure><a href="'+html.escape(r['path'])+'"><img loading="lazy" src="'+html.escape(r['thumbnail'])+'"></a><figcaption>'+html.escape(Path(r['path']).name)+'</figcaption></figure>' for r in rows)+'</div></section>')
(HERE/'contact-sheet.html').write_text('<!doctype html><meta charset="utf-8"><title>RCMS 0.5.0 native re-audit</title><style>body{font:15px system-ui;max-width:1800px;margin:20px auto;color:var(--foreground,#222)}h2{margin-top:28px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,550px),1fr));gap:12px}figure{margin:0;background:var(--card,#eee);padding:10px}img{width:100%;height:auto}figcaption{overflow-wrap:anywhere;font-size:12px}select,button{font:inherit;padding:8px;margin-right:8px}section[hidden]{display:none}</style><h1>RC MetaStudio 0.5.0 — independent native re-audit</h1><p>Click a frame for original resolution. See REPORT.md and INSPECTIONS.md for judgments and limits. Native X11 captures are distinct from the explicitly labelled derived export inspections.</p><label>Evidence group <select id="group">'+''.join(options)+'</select></label><button id="all">Show all</button>'+''.join(sections)+"""<script>
const select=document.querySelector('#group');
function show(){for(const section of document.querySelectorAll('section'))section.hidden=section.dataset.group!==select.value;}
select.value=Array.from(select.options).some(x=>x.value==='export-inspections')?'export-inspections':select.options[0]?.value;
select.addEventListener('change',show);document.querySelector('#all').onclick=()=>document.querySelectorAll('section').forEach(x=>x.hidden=false);show();
</script>""")
print('sections',len(sections))
