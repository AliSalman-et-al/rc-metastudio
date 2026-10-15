"""Curate original native reviewer frames and append the round-six contact sheet."""
import base64
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SHOTS = HERE/'reviewer-screenshots'
SHOTS.mkdir(exist_ok=True)
rows = []
old_pairs = {row['key']:row for row in json.loads((HERE/'SCREENSHOTS.json').read_text())}
old_native = json.loads(subprocess.check_output(['git','show','dc235ab:'+str((HERE/'NATIVE-SELECTED.json').relative_to(ROOT))]))


def steps(directory):
    manifest = json.loads((directory/'manifest.json').read_text())
    assert manifest['passed'] and manifest['native_requested'], directory
    return [json.loads(line) for line in (directory/'steps.jsonl').read_text().splitlines()]


def current(label):
    receipt = json.loads((HERE/'raw'/(label+'.json')).read_text())
    assert receipt['exit_code'] == 0, receipt
    log = (HERE/'raw'/receipt['log']).read_text()
    return Path(re.search(r'^Evidence: (.+)$',log,re.M)[1])


def select(directory, action, **filters):
    found = [step for step in steps(directory) if step['action'] == action and all(step.get(k)==v for k,v in filters.items())]
    assert len(found) == 1, (directory,action,filters,len(found))
    step = found[0]
    return directory/step['captures'][0], dict(evidence=str(directory.relative_to(ROOT)),step=step['step'],action=action,**filters)


def copy(source, name):
    target = SHOTS/(name+'.png')
    shutil.copyfile(source,target)
    return dict(path=str(target.relative_to(HERE)),source=str(source.relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest())


def add(key,label,after,before=None,note=''):
    source,evidence = after
    row = dict(key=key,label=label,after=copy(source,key+'-after'),evidence=evidence,observation=note)
    if before:
        row['before'] = copy(before,key+'-before')
    rows.append(row)


predictions = current('reviewer-predictions-current')
groups = current('reviewer-groups-current')
colours = current('reviewer-colours-current')
diagnostic = current('reviewer-diagnostic-current')
old_groups = current('reviewer-groups-before')
old_diagnostic = ROOT/next(r['evidence'] for r in old_native if r['scenario']=='project-round6-polish')
old_sequential = ROOT/next(r['evidence'] for r in old_native if r['scenario']=='project-axis-sequential')
for style in ('default','revman','bmj'):
    add('reviewer-pft-'+style,'PFT prediction interval · '+style,
        select(predictions,'reviewer-prediction-after',measure='PFT',workflow='standard',style=style),
        HERE/old_pairs['axis-pft-'+style]['after']['path'],
        'Same six-study counts: the PI now uses the pooled harmonic-mean inverse. Public-package reference values and every Text/Tables/copy/export row are retained. Default marks share blue ink; journal colours are unchanged.')
for workflow in ('cumulative','leave-one-out','subgroup'):
    old,_ = select(old_sequential,'axis-pft-subset-inverses',workflow=workflow)
    add('reviewer-pft-'+workflow,'PFT '+workflow+' inference',
        select(predictions,'reviewer-prediction-after',measure='PFT',workflow=workflow,style='default'),old,
        'The actual fit supplies the sample sizes. Each subgroup footer and table row is compared by entered group order; cumulative/omission footers use their overall fit. All three styles have native proof. Controlled subgroup covariate captions differ (Group / Region).')
for family in ('onearm-proportion','onearm-mean'):
    for style in ('default','revman','bmj'):
        old,_ = select(old_groups,'reviewer-group-before',family=family,group='Group',style=style)
        add('reviewer-'+family+'-'+style,family+' · unnamed group · '+style,
            select(groups,'reviewer-group-after',family=family,group='Group',style=style),old,
            'No bare Group spanner. Raw mean columns are absent on this entered-effect output path; its identity remains single-arm mean. Meaningful custom names remain in the corresponding native cases.')
    old,_ = select(old_groups,'reviewer-group-before',family=family,group='Participants',style='default')
    add('reviewer-'+family+'-custom',family+' · meaningful group',
        select(groups,'reviewer-group-after',family=family,group='Participants',style='default'),old,
        'Participants remains a visible identity. The proportion raw-data spanner is retained; the mean name remains in its standalone caption. RevMan/BMJ custom-name cases are asserted too.')
for shape,digits in (('continuous',6),('factor',2),('multiple',6)):
    old,_ = select(old_diagnostic,'diagnostic-selected-precision',shape=shape,digits=digits)
    add('reviewer-diagnostic-'+shape,'Diagnostic coefficients · '+shape,
        select(diagnostic,'diagnostic-selected-precision',shape=shape,digits=digits),old,
        'Logit estimate/bound scale and odds-ratio intervals are explicit. Raw coefficients and selected precision are unchanged; report and table copy/export bytes are checked.')
for side in ('Sensitivity','Specificity'):
    add('reviewer-table-'+side.lower(),side+' coefficient table and CSV',
        select(diagnostic,'reviewer-table-surface',title=side+' coefficients',label='diagnostic-continuous-6-'+side),
        note='Actual Tables selector, header/cell widgets, Copy table and exported UTF-8 CSV match the structured report. The retained native drive covers both sides at two/six digits and all three moderator shapes.')
for index,step in enumerate(steps(colours)):
    if step['action']=='reviewer-colour-after' and step['scenario'] not in ('analysis-data-twoarm-proportion','analysis-data-onearm-proportion'):
        add('reviewer-colour-'+str(index),'Default ink · '+step['scenario']+' · '+step['title'],
            (colours/step['captures'][0],dict(evidence=str(colours.relative_to(ROOT)),step=step['step'],action=step['action'])),
            note='Rendered blue boxes/intervals/caps/diamonds, black study text, zebra contrast and four decoded export formats are checked. PNG/TIFF/PDF also contain matching blue samples. Fit fields stay exact.')
add('reviewer-arrows','Default clipped CI arrows',select(colours,'reviewer-default-clipped-arrows'),
    note='Actual Edit plot limits produce blue arrow polygons. Unclipped caps are checked before editing; all four exported formats retain the accent and the fitted numerical fields are unchanged.')
for action,label in (('reviewer-about-version','About 0.5.0'),('reviewer-legacy-default-setup','Old default key in setup'),('reviewer-version-reopened','Saved 0.5.0 project reopened')):
    add(action,label,select(groups,action),note='Original 0.4.2 project and paired R settings are retained under legacy-default with hashes. Internal default reopens as Default; the newly saved/reopened project manifest records application.version 0.5.0. Installed RCMetaR also reports 0.5.0.')
(HERE/'REVIEWER-SCREENSHOTS.json').write_text(json.dumps(rows,indent=2)+'\n')
sections=[]
for row in rows:
    pictures=[]
    for role in ('before','after'):
        if role not in row:continue
        shot=row[role]
        data=base64.b64encode((HERE/shot['path']).read_bytes()).decode()
        pictures.append(f'<figure><figcaption>{role.title()}</figcaption><a href="{shot["path"]}"><img alt="{html.escape(row["label"])} {role}" src="data:image/png;base64,{data}"></a></figure>')
    sections.append(f'<section id="{row["key"]}"><h2>{html.escape(row["label"])}</h2><div class="pair">'+''.join(pictures)+f'</div><p>{html.escape(row["observation"])}</p><small>{html.escape(row["evidence"]["evidence"])} · step {row["evidence"]["step"]}</small></section>')
body=''.join(sections)
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Round-six reviewer fixes</title><style>body{margin:0;font:15px/1.5 var(--font-sans,system-ui);color:var(--foreground,#222)}section{margin-bottom:28px}h2{font-size:18px}.pair{display:flex;gap:12px}figure{flex:1;min-width:0;margin:0}img{width:100%;height:auto}small{overflow-wrap:anywhere}@media(max-width:650px){.pair{display:block}}</style><body>'''+body+'</body></html>'
(HERE/'reviewer-contact-sheet.html').write_text(page)
main=(HERE/'contact-sheet.html').read_text()
main=re.sub(r'<section id="reviewer-fixes">.*?</section><!-- reviewer-end -->','',main,flags=re.S)
main=main.replace('</body>', '<section id="reviewer-fixes"><h2>Accepted reviewer fixes and 0.5.0</h2><p><a href="reviewer-contact-sheet.html">Open the reviewer before/after entries and native proof frames</a></p>'+''.join(f'<p><a href="reviewer-contact-sheet.html#{r["key"]}">{html.escape(r["label"])}</a></p>' for r in rows)+'</section><!-- reviewer-end --></body>')
(HERE/'contact-sheet.html').write_text(main)
print(f'{len(rows)} reviewer entries; {sum(int(role in row) for row in rows for role in ("before","after"))} original PNG frames.')
