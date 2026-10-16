"""Build a standalone before/after page from bound, unmodified native captures."""
import base64
from html import escape
import json
import os
from pathlib import Path

HERE = Path(os.environ.get("RCMS_AUDIT_DIR", Path(__file__).resolve().parent))
receipts = json.loads((HERE / os.environ.get('RCMS_NATIVE_INDEX', 'REVIEW1-NATIVE.json')).read_text())


def frame(label, action, **values):
    run = receipts[label]
    step = next(step for step in run['observed'] if step['action'] == action and all(step.get(key) == value for key, value in values.items()))
    return HERE / 'screenshots' / (label + '-' + step['captures'][0])


def picture(path, caption):
    data = base64.b64encode(path.read_bytes()).decode()
    source = str(path.resolve()) if os.environ.get('RCMS_CONTACT_LOCAL_IMAGES') else 'data:image/png;base64,' + data
    return f'<figure><figcaption>{escape(caption)}</figcaption><img tabindex="0" alt="{escape(caption)}" src="{source}" title="Click to inspect at full resolution"><small>{escape(str(path.relative_to(HERE)))}</small></figure>'

external = HERE / 'CONTACT-PAIRS.json'
if not external.is_file():
    pairs = [
        ('D4-04 · Start in the main window', 'Create, import or open directly; the worksheet appears when an outcome exists.',
         HERE/'screenshots/help-02-0-ux-empty-workspace.png', frame('review1-reading-qualified','review1-start-before-check')),
        ('D4-05 · Read the result first', 'Pooled result, heterogeneity, test and prediction interval precede model configuration and calculation details.',
         HERE/'screenshots/report-before-04-0-analysis-results-report.png', frame('review1-reading-qualified','review1-report-top')),
        ('D4-05 · One caption per clinical result', 'Repeated section/table captions are removed from the report, copied text and table selector.',
         HERE/'screenshots/review1-clinical-complete-analysis-diagnostic-regression-multiple-04-0-matrix-results-report.png', HERE/'screenshots/review1-reading-finished-analysis-diagnostic-regression-multiple-04-0-matrix-results-report.png'),
        ('Finding 2 / D4-07 · Diagnostic forest, three decimals', 'Measured header leading, round probability ticks and a separate axis-title baseline.',
         HERE/'screenshots/diagnostic-24-0-round4-annotations.png', frame('review1-publication-audit-round3-presentation-diagnostic','round4-annotations',digits=3,style='revman',title='diagnostic.Sens.forest')),
        ('Findings 1 and 3 · BMJ binary forest, six decimals', 'Pooled label clears totals; conventional overall-test wording clears the first tick and footer.',
         HERE/'screenshots/twoarm-proportion-72-0-round4-annotations.png', frame('review1-publication-audit-round3-presentation-twoarm-proportion','round4-annotations',digits=6,style='bmj')),
        ('Finding 4 / D4-06 · Calculator controls', 'Compact confidence wording and consistent native actions, with the existing estimate and interval unchanged.',
         HERE/'screenshots/entered-continuous-02-0-calculator-mode-layout.png', frame('review1-bounded-calculator-mode-entered-continuous','calculator-mode-layout')),
        ('D4-07 · Keep reference guides within the evidence rows', 'The default forest null guide stops at the studies, leaving the pooled estimate and inference footer clear.',
         frame('review1-verified-generic-effect','round4-annotations',digits=3,style='default'), frame('review1-bounded-generic-effect','round4-annotations',digits=3,style='default')),
        ('Finding 3 / D4-07 · Name the displayed clinical quantity', 'A logit analysis displays Proportion and names the actual tested null: proportion = 0.5.',
         HERE/'screenshots/review1-bounded-transforms-16-0-round4-annotations.png', HERE/'screenshots/review1-qualified-audit-round3-presentation-transforms-64-0-round4-annotations.png'),
    ]
external = HERE / 'CONTACT-PAIRS.json'
pair_labels = {}
if external.is_file():
    pair_labels = {i: (row.get('before_label', 'Before'), row.get('after_label', 'After'))
                   for i, row in enumerate(json.loads(external.read_text()))}
    pairs = [(row['title'], row['description'], HERE / row['before'], HERE / row['after'])
             for row in json.loads(external.read_text())]
body = [('<h2>Native UX comparison</h2>' if not external.is_file() else '') + '<p>Unmodified Linux Qt screen captures with pinned R 4.6.1. Click a frame to inspect its full resolution. Historical before frames retain their original provenance. Workflow, fixture and range differences are stated beside each comparison.</p>']
for number, (title, description, before, after) in enumerate(pairs):
    before_label, after_label = pair_labels.get(number, ('Before', 'After'))
    body.append(f'<section><h3>{escape(title)}</h3><p>{escape(description)}</p><div class="pair">'+picture(before,before_label)+picture(after,after_label)+'</div></section>')
if not external.is_file():
    body.append('<section><h3>D4-04 / D4-06 · Recent projects and native palettes</h3><p>Full paths wrap; missing files remain visible and unavailable. The same controls follow the native light and dark palettes.</p><div class="pair">'+picture(frame('review1-reading-qualified','review1-start-dark'),'Native dark palette')+picture(frame('review1-reading-qualified','review1-start-light'),'Native light palette')+'</div></section>')
    body.append('<section><h3>D4-06 · Clear navigation</h3><p>Choose outcomes, follow-ups or groups, then use Previous / Next / Add. Existing operations and tooltips remain.</p>'+picture(frame('review1-reading-qualified','review1-workspace-navigation'),'Dataset navigation at 1000 × 720')+'</section>')
html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RC MetaStudio native comparison</title><style>
body{margin:0;font:15px/1.5 var(--font-sans,system-ui);color:var(--foreground,#222)}h2{font-size:22px}h3{font-size:18px;margin:20px 0 6px}p{margin:6px 0 14px}section{padding:12px 0 20px;border-bottom:1px solid var(--border,#bbb)}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;min-width:0}figcaption{font-weight:600;margin-bottom:6px}img{display:block;width:100%;height:auto;cursor:zoom-in;border:1px solid var(--border,#aaa);box-sizing:border-box}small{display:block;overflow-wrap:anywhere;color:var(--muted-foreground,#666);font-size:11px;margin-top:5px}dialog{width:94%;max-width:1800px;border:1px solid var(--border,#aaa);padding:16px;border-radius:var(--radius,8px);background:var(--card,#fff);color:var(--foreground,#222)}dialog::backdrop{background:#000b}dialog img{cursor:default;border:0}button{font:inherit;padding:6px 14px;margin-bottom:12px;cursor:pointer}@media(max-width:650px){.pair{grid-template-columns:1fr}}
</style>'''+''.join(body)+'''<dialog><button autofocus>Close full-resolution view</button><img alt="Full-resolution native capture"></dialog><script>
const dialog=document.querySelector('dialog');document.querySelectorAll('figure img').forEach(img=>{const open=()=>{dialog.querySelector('img').src=img.src;dialog.querySelector('img').alt=img.alt;dialog.showModal()};img.onclick=open;img.onkeydown=e=>{if(e.key==='Enter')open()}});dialog.querySelector('button').onclick=()=>dialog.close();console.log('Native comparison frames:',document.querySelectorAll('figure img').length);
</script></html>'''
target = HERE / ('raw/contact-sheet.preview.html' if os.environ.get('RCMS_CONTACT_LOCAL_IMAGES') else 'contact-sheet.html')
target.write_text(html)
print('Wrote self-contained contact-sheet.html with', len(pairs)*2 + (0 if external.is_file() else 3), 'bound native frames')
