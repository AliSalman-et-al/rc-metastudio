"""Bind completed pre-interruption prediction cases and the one-case continuation."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent
first=Path(next(x[10:] for x in (HERE/'raw/helper-project-reviewer-predictions.log').read_text().splitlines() if x.startswith('Evidence: ')))
second=HERE/'raw/prediction-remaining'
rows=[]
for evidence in (first,second):
 steps=[json.loads(x) for x in (evidence/'steps.jsonl').read_text().splitlines()]
 for step in steps:
  if step['action']!='reviewer-prediction-after':continue
  files=list(step['captures'])+list(step['artifacts'].values())
  rows.append({'measure':step['measure'],'workflow':step['workflow'],'style':step['style'],'step':step['step'],'evidence':str(evidence),'reference':step['reference'],'files':[{'path':str(evidence/name),'sha256':hashlib.sha256((evidence/name).read_bytes()).hexdigest()} for name in files]})
expected={(m,w,s) for m,w in [('PFT','standard'),('PLO','standard'),('PAS','standard'),('PFT','cumulative'),('PFT','leave-one-out'),('PFT','subgroup')] for s in ('default','revman','bmj')}
assert len(rows)==18 and {(r['measure'],r['workflow'],r['style']) for r in rows}==expected
assert json.loads((HERE/'raw/prediction-remaining-final.json').read_text())['exit_code']==0
(HERE/'PREDICTION-RECOVERY.json').write_text(json.dumps({'status':'All 18 case paths checked: 17 retained from interrupted helper, one fresh continuation. The interrupted outer helper is not called passing.','rows':rows},indent=2)+'\n')
print('18 distinct cases bound; no completed case rerun')
