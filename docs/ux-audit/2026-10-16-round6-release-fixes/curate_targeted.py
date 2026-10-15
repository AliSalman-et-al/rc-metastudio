"""Select action/result frames; manual inspection is recorded separately."""
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
index=json.loads((HERE/'CURATED.json').read_text())
index=[row for row in index if row.get('selection')!='targeted']
def retain(source,name):
    target=HERE/'screenshots'/name
    shutil.copy2(source,target)
    index.append(dict(path=target.relative_to(HERE).as_posix(),source=str(source.relative_to(ROOT)),kind='native targeted',selection='targeted',sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
old=ROOT/'docs/ux-audit/2026-10-16-round6-reaudit/screenshots'
for source,name in [
 ('project-reviewer-predictions-40-0-reviewer-prediction-after.png','R6-01-before-bmj.png'),
 ('project-reviewer-groups-148-0-reviewer-about-version.png','R6-02-before-about.png'),
 ('calculator-mode-back-continuous-02-0-back-calculation-nested-cancel.png','R6-02-before-continuous-prompt.png'),
 ('calculator-mode-back-binary-02-0-back-calculation-nested-cancel.png','R6-02-before-binary-prompt.png'),
 ('project-axis-proportions-163-0-axis-option-reopened.png','R6-04-before-revman.png'),
 ('calculator-ratio-precision-13-0-ratio-precision-reopened-fit.png','R6-05-before-extreme-irr.png'),
 ('matrix-diagnostic-meta-regression-figure-1-bottom.png','R6-07-before-coefficient.png'),
 ('matrix-hr-meta-regression-report-exponentiated--wording-recovery.png','R6-08-before-hr.png'),
 ('matrix-irr-meta-regression-report-exponentiated--wording-recovery.png','R6-08-before-irr.png'),
]: retain(old/source,name)
for label in ('presentation-1','back-continuous-1','back-binary-1','pln-axes-1','stress-2','coefficient-4','small-screen-2'):
    if label=='presentation-1': work=HERE/'raw'/label
    else:
        log=HERE/'raw'/(label+'.log')
        if not log.exists(): continue
        match=re.search(r'^Evidence: (.+)$',log.read_text(),re.M)
        if not match: continue
        work=Path(match[1])
    if not (work/'steps.jsonl').exists(): continue
    for step in map(json.loads,(work/'steps.jsonl').read_text().splitlines()):
        action=step['action']; name=None
        if action=='release-about-content-visible': name='R6-02-after-about.png'
        elif action=='release-bmj-single-arm': name=f'R6-01-after-bmj-{step["group"]}-{step["workflow"]}.png'
        elif action=='release-readable-exponentiated': name=f'R6-08-after-{step["family"]}.png'
        elif action=='back-calculation-nested-cancel': name=f'R6-02-after-{label.split("-")[1]}-prompt.png'
        elif action=='axis-option-reopened' and step.get('measure')=='PLN' and step.get('style') in ('revman','bmj'): name=f'R6-04-after-{step["style"]}.png'
        elif action=='stress-journal-after-reopen' and (step.get('mode')=='raw' or (step.get('mode')=='ratio' and step.get('metric')=='IRR')): name=f'R6-05-after-{step["metric"]}-{step["mode"]}-{step["style"]}.png'
        elif action in ('release-small-screen-top','release-small-screen-bottom'):
            name=f'R6-02-small-{step["kind"]}-'+('top' if action.endswith('top') else 'bottom')+'.png'
        elif action in ('coefficient-log-default-bottom','coefficient-linear-reopened-bottom'):
            side='sensitivity' if '.sensitivity.' in step['title'] else 'specificity'
            name=f'R6-07-after-{side}-'+('log' if action=='coefficient-log-default-bottom' else 'linear')+'.png'
        if name and step['captures']: retain(work/step['captures'][0],name)
(HERE/'CURATED.json').write_text(json.dumps(index,indent=2)+'\n')
body=''.join(f'<figure><figcaption>{html.escape(row["path"])}</figcaption><a href="{row["path"]}"><img src="{row["path"]}" loading="lazy"></a></figure>' for row in index if row['kind']!='actual export')
(HERE/'contact-sheet.html').write_text('<!doctype html><html><meta charset="utf-8"><title>RCMS release fixes</title><style>body{font:15px system-ui;margin:0;color:var(--foreground,#222)}figure{margin:20px 0}figcaption{font-weight:600;margin:8px 0}img{width:100%;height:auto;border:1px solid #888}a{color:inherit}</style><body><p>Release-fix native evidence and actual export renderings. See INSPECTIONS.md for observations and CURATED.json for byte/source bindings.</p>'+body+'</body></html>')
print('Targeted selection complete; inspect every new frame before accepting it.')
