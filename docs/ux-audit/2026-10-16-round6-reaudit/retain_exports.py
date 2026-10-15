"""Retain actual vectors cited by publication findings without regenerating them."""
from pathlib import Path
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent
rows=[]
for scenario,step,name,export in [('project-round6-polish',180,'R6-03-revman-long-arm.svg',True),('project-reviewer-predictions',40,'R6-01-bmj-single-arm.svg',False)]:
 log=HERE/'raw'/('helper-'+scenario+'.log');ev=Path(next(x[10:] for x in log.read_text().splitlines() if x.startswith('Evidence: ')))
 item=next(x for x in map(json.loads,(ev/'steps.jsonl').read_text().splitlines()) if x['step']==step)
 source=ev/'workflow'/Path(item['export']).name if export else ev/next(iter(item['artifacts'].values()))
 target=HERE/'exports'/name;shutil.copy2(source,target)
 rows.append({'source':str(source),'path':str(target.relative_to(HERE)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
(HERE/'EXPORT-EVIDENCE.json').write_text(json.dumps(rows,indent=2)+'\n')
