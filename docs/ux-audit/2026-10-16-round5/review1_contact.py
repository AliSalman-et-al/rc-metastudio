"""Rebuild the self-contained contact sheets from unchanged native captures."""
import base64
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
pairs_path = HERE / 'CONTACT-PAIRS.json'
pairs = [row for row in json.loads(pairs_path.read_text()) if not row['title'].startswith('Review 1 ·')]
new = []
def pair(title, description, before, after):
    new.append(dict(title='Review 1 · '+title, description=description,
                    before='screenshots/'+before, after='screenshots/'+after))
for number, style in [('04','Default'),('07','RevMan'),('10','BMJ')]:
    pair(style+' IRR context and totals', 'Same Niel-Weise input: readable separated context, clear exposure headers, original events/person-time totals, bold pooled row and normal inference. No fitted value changed.',
         f'review1-irr-before-{number}-0-round5-irr-context.png', f'review1-irr-after-{number}-0-round5-irr-context.png')
pair('Bundled amino sample', 'Same sample and fitted results; Intervention / Control replace the bundled placeholders without changing user projects.',
     'review1-shell-before-21-0-review1-report-top.png','review1-shell-after-21-0-review1-report-top.png')
pair('Recent projects', 'Present and missing examples now occupy single aligned rows; full paths remain in tooltips and accessible names. Locate/Remove/reopen are exercised.',
     'review1-shell-before-03-0-round5-recent-missing.png','review1-shell-after-03-0-round5-recent-missing.png')
pair('CSV count preview', 'Same four count inputs display as 4 / 20 / 6 / 22. Import strings and effect precision are preserved.',
     'review1-arms-before-25-0-round5-arm-csv-preview.png','review1-arms-after-25-0-round5-arm-csv-preview.png')
pair('Calculator sentence case', 'Same real wizard fixture and calculator values; No event matches the surrounding sentence case.',
     'review1-arms-before-24-0-round5-arm-calculator.png','review1-arms-after-24-0-round5-arm-calculator.png')
for number, style in [('06','Default'),('16','RevMan')]:
    pair(style+' HR footer', 'Same 65-study Pignon sample. A consistent pooled row includes the existing 100% weight. Raw HR events/exposure are unavailable and are not invented.',
         f'native-long-settled-{number}-0-round5-long-figure-bottom.png', f'review1-hr-after-{number}-0-round5-long-figure-bottom.png')
pair('Subgroup heading clearance', 'Same long HR subgroup input. The final taste-pass fix moves the manual rule above the first subgroup heading and reserves the complete header block.',
     'review1-subgroup-rule-before.png','review1-subgroup-rule-after.png')
extra = HERE / 'REVIEW1-EDITOR-PAIRS.json'
if extra.exists():new.extend(json.loads(extra.read_text()))
pairs.extend(new)
pairs_path.write_text(json.dumps(pairs, indent=2, ensure_ascii=False)+'\n')
style = '''body{margin:0;font:15px/1.5 var(--font-sans,system-ui);color:var(--foreground,#222)}h3{font-size:18px;margin:18px 0 6px}p{margin:6px 0 14px}section{padding:8px 0 20px;border-bottom:1px solid var(--border,#bbb)}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;min-width:0}figcaption{font-weight:600;margin-bottom:6px}img{display:block;width:100%;height:auto;cursor:zoom-in;border:1px solid var(--border,#aaa);box-sizing:border-box}small{display:block;overflow-wrap:anywhere;color:var(--muted-foreground,#666);font-size:11px;margin-top:5px}dialog{width:94%;max-width:1800px;border:1px solid var(--border,#aaa);padding:16px;border-radius:var(--radius,8px);background:var(--card,#fff);color:var(--foreground,#222)}dialog::backdrop{background:#000b}dialog img{cursor:default;border:0}button{font:inherit;padding:6px 14px;margin-bottom:12px;cursor:pointer}@media(max-width:650px){.pair{grid-template-columns:1fr}}'''
script = '''const d=document.querySelector('dialog');document.querySelectorAll('figure img').forEach(i=>{const open=()=>{d.querySelector('img').src=i.src;d.showModal()};i.onclick=open;i.onkeydown=e=>{if(e.key==='Enter')open()}});d.querySelector('button').onclick=()=>d.close();console.log('Native frames',document.querySelectorAll('figure img').length);'''
def document(rows, embed=True):
    parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RCMS native comparisons</title><style>'+style+'</style><p>Unmodified Linux Qt captures with pinned R 4.6.1. Click a frame to inspect full resolution. Historical before frames and any input differences retain explicit provenance.</p>']
    for row in rows:
        parts.append('<section><h3>'+html.escape(row['title'])+'</h3><p>'+html.escape(row['description'])+'</p><div class="pair">')
        for side in ('before','after'):
            path=HERE/row[side]
            source='data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode() if embed else str(path.resolve())
            parts.append('<figure><figcaption>'+side.title()+'</figcaption><img tabindex="0" alt="'+html.escape(row['title']+' '+side)+'" src="'+source+'"><small>'+html.escape(row[side])+'</small></figure>')
        parts.append('</div></section>')
    parts.append('<dialog><button autofocus>Close</button><img alt="Full resolution native capture"></dialog><script>'+script+'</script></html>')
    return ''.join(parts)
(HERE/'contact-sheet.html').write_text(document(pairs))
(HERE/'review1-contact-sheet.html').write_text(document(new))
Path('/tmp/rcms-review1-contact-preview.html').write_text(document(new, embed=False))
print(f'{len(pairs)} total comparisons, {len(new)} review follow-up comparisons.')
