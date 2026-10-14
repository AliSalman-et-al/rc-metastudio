"""Curate action-linked helper captures; never label QWidget grabs as X11 grabs."""
import json,re,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
selections={
 'calculator-binary':['calculator-effect-preview'],
 'calculator-continuous':['calculator-effect-preview'],
 'calculator-diagnostic':['calculator-effect-preview'],
 'ux-improvements':['ux-inline-analysis-error','ux-native-result-table','ux-independent-view-zoom','ux-csv-invalid','ux-csv-mapped','ux-covariate-error'],
 'review-workflows':['review-properties-prefilled','review-study-order-options'],
 'analysis-diagnostic-joint':['clinical-report'],
 'analysis-diagnostic-regression-multiple':['matrix-results','properties-prefilled'],
 'small-study-effects':['small-study-configured','small-study-results'],
 'small-study-diagnostic':['small-study-matrix-configured','matrix-results'],
 'ratios-hr':['ratio-calculator'],
 'plot-workflow-sroc':['family-editor-controls'],
 'plot-workflow-contour':['family-editor-controls'],
 'audit-round3-precision':['round3-zero-bound-presentation','round3-small-effects-preserved','round3-degenerate-axis-bottom','round3-degenerate-axis','round3-bubble-tick-coverage'],
 'audit-round3-hr':['round3-fixed-footer-bottom','round3-fixed-references'],
 'audit-round3-irr':['round3-fixed-footer-bottom','round3-fixed-references'],
 'audit-round3-twoarm-mean':['round3-null-excluded-rendered'],
}
rows=[];observations=[]
for scenario,actions in selections.items():
 metadata=HERE/'raw'/('native-'+scenario+'.json')
 if not metadata.exists():continue
 run=json.loads(metadata.read_text())
 if run['exit_code']!=0:continue
 evidence=Path(re.search('Evidence: (.+)',(HERE/'raw'/run['log']).read_text())[1])
 for step in map(json.loads,(evidence/'steps.jsonl').read_text().splitlines()):
  if step['action'] not in actions:continue
  if scenario=='audit-round3-hr' and step['action']=='round3-fixed-references' and step['step']!=29:continue
  if scenario=='audit-round3-irr' and step['action']=='round3-fixed-references' and step['step']!=33:continue
  observations.append(dict(scenario=scenario,evidence=str(evidence.relative_to(ROOT)),step=step))
  for source in step['captures']:
   name='helper-'+scenario+'-'+source;target=HERE/'screenshots'/name;shutil.copy2(evidence/source,target)
   rows.append(dict(path=str(target.relative_to(HERE)),source=str((evidence/source).relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),scenario=scenario,action=step['action'],capture='QWidget.grab in visible xcb helper'))
selected={row['path'] for row in rows}
for old in (HERE/'screenshots').glob('helper-*.png'):
 if str(old.relative_to(HERE)) not in selected:
  archive=HERE/'raw'/'uncurated';archive.mkdir(exist_ok=True);old.rename(archive/old.name)
(HERE/'HELPER-SCREENSHOTS.json').write_text(json.dumps(rows,indent=2)+'\n')
(HERE/'OBSERVATIONS.json').write_text(json.dumps(observations,indent=2,ensure_ascii=False)+'\n')
print('curated',len(rows))
