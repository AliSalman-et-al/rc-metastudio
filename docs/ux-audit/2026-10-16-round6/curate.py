"""Copy original native screenshots, bind their hashes, and build the contact sheet."""
import base64
import hashlib
import html
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EVIDENCE = ROOT / 'artifacts/verification/rcms'
SHOTS = HERE / 'screenshots'
SHOTS.mkdir(exist_ok=True)
BEFORE = HERE.parent / '2026-10-16-round5-reaudit/screenshots'
pairs = []


def native_step(scenario, action, **filters):
    for directory in sorted(EVIDENCE.glob('*-' + scenario), reverse=True):
        manifest_path = directory / 'manifest.json'
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text())
        if not manifest.get('passed') or not manifest.get('native_requested'):
            continue
        steps = [json.loads(line) for line in (directory/'steps.jsonl').read_text().splitlines()]
        for step in reversed(steps):
            if step['action'] == action and all(step.get(key) == value for key,value in filters.items()):
                return directory/step['captures'][0], dict(evidence=str(directory.relative_to(ROOT)), step=step['step'], action=action)
    raise ValueError((scenario, action, filters))


def copy(source, name):
    target = SHOTS / (name + '.png')
    shutil.copyfile(source, target)
    return dict(path=str(target.relative_to(HERE)), source=str(source.relative_to(ROOT)),
                sha256=hashlib.sha256(target.read_bytes()).hexdigest())


def pair(key, label, before, after, evidence, observation):
    pairs.append(dict(key=key, label=label, before=copy(before,key+'-before'),
                      after=copy(after,key+'-after'), evidence=evidence, observation=observation))


for key,label,old,scenario,action,filters,note in (
    ('tiny-sd','Tiny SD survives real keyboard entry','calculator-tiny-keyboard-replay-preview.png','calculator-mode-continuous-metrics','calculator-precision-input',{'input':'0.00001'},'Full-precision input is stored separately from compact display. Accept/save/reopen and independent effects are asserted in the native helper.'),
    ('metric-label','Contextual mean action','metric-menu-visible-tx-mean.png','project-display-labels','display-metric-popup',{'family':'onearm-mean'},'Attached one-arm menu uses the contextual display name. The sweep also covers coefficients, entered effects, MD/SMD and HR/IRR.'),
    ('ci-caps','65-study subgroup CI caps','matrix-hr-subgroup-figure.png','audit-round3-round5','round5-long-figure',{'workflow':'subgroup','style':'default'},'Caps are bounded in row units. Retained SVG checks cover short and long figures and exported vectors.'),
    ('wrapped-headers','BMJ wrapped arm headers','long-arm-bmj-matrix-twoarm-proportion-standard-figure.png','project-round6-polish','measured-wrapped-arm-headers',{'style':'bmj','names':['Cognitive behavioural therapy plus usual care','Usual care only']},'The rule and superheading follow measured wrapped text height. All three styles and three name-length pairs are measured.'),
    ('diagnostic-precision','Diagnostic report at six digits','matrix-diagnostic-meta-regression-report.png','project-round6-polish','diagnostic-selected-precision',{'shape':'continuous','digits':6},'Text, Tables, copy and export use selected precision. Two/six digits and three moderator shapes are checked.'),
    ('visible-legend','Legend follows visible bands','bubble-hidden-ci-legend.png','plot-workflow-regression','bubble-visible-legend',{'style':'BMJ','line':True,'confidence':False,'prediction':False},'Hidden confidence/prediction bands have no legend entries; twelve visibility/style combinations are asserted.'),
):
    source,evidence = native_step(scenario,action,**filters)
    pair(key,label,BEFORE/old,source,evidence,note)

for family,scenario in [('proportion','project-axis-proportions'),('other','project-axis-others')]:
    before_scenario = '20261015T113634Z-5b581de0-project-axis-proportions' if family == 'proportion' else '20261015T113900Z-3da6217b-project-axis-others'
    directory = EVIDENCE / before_scenario
    for step in map(json.loads,(directory/'steps.jsonl').read_text().splitlines()):
        if step['action'] != 'axis-baseline':
            continue
        measure,style = step['measure'],step['style']
        if measure in ('Sens', 'Spec'):
            source,evidence = native_step('audit-round3-presentation-diagnostic','round4-annotations',
                                          family='diagnostic',digits=3,style=style,title='diagnostic.'+measure+'.forest')
        else:
            source,evidence = native_step(scenario,'axis-default',measure=measure,style=style)
        pair('axis-'+measure.lower()+'-'+style,measure+' axis · '+style,directory/step['captures'][0],source,evidence,
             'Native default before/after. The same helper measures tick/interval geometry, exact numeric fit and weight equality, saved Edit plot choice, Cancel and exported SVG.')

(HERE/'SCREENSHOTS.json').write_text(json.dumps(pairs,indent=2)+'\n')
body = []
for row in pairs:
    images = []
    for role in ('before','after'):
        item = row[role]
        data = base64.b64encode((HERE/item['path']).read_bytes()).decode()
        images.append(f'<figure><figcaption>{role.title()}</figcaption><a href="{item["path"]}"><img alt="{html.escape(row["label"])} — {role}" src="data:image/png;base64,{data}"></a></figure>')
    body.append(f'<section id="{row["key"]}"><h2>{html.escape(row["label"])}</h2><div class="pair">'+''.join(images)+f'</div><p>{html.escape(row["observation"])}</p><small>{html.escape(row["evidence"]["evidence"])} · step {row["evidence"]["step"]}</small></section>')
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Round 6 before and after</title><style>body{margin:0;color:var(--foreground,#20242a);font:15px/1.5 var(--font-sans,system-ui)}section{margin:0 0 28px}h2{font-size:18px;margin:12px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}figure{margin:0;min-width:0}figcaption{font-weight:600}img{width:100%;height:auto}p{margin:8px 0}small{color:var(--muted-foreground,#595f69);overflow-wrap:anywhere}@media(max-width:560px){.pair{grid-template-columns:1fr}}</style><body>'''+''.join(body)+'</body></html>'
(HERE/'contact-sheet.html').write_text(page)
print(f'{len(pairs)} native before/after pairs; original copies and hashes in SCREENSHOTS.json.')
