"""Collect completed command receipts and verify retained helper artifact hashes."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent
rows=[];errors=[]
for file in sorted((HERE/'raw').glob('*.json')):
 data=json.loads(file.read_text())
 if not isinstance(data,dict) or 'label' not in data:continue
 item=dict(data);item['receipt']=str(file.relative_to(HERE))
 log=HERE/'raw'/data['log']
 if 'sha256' in data and hashlib.sha256(log.read_bytes()).hexdigest()!=data['sha256']:errors.append(str(log))
 evidence=next((line.removeprefix('Evidence: ') for line in log.read_text().splitlines() if line.startswith('Evidence: ')),None)
 if evidence:
  m=Path(evidence)/'manifest.json';item['evidence']=evidence
  if m.exists():
   manifest=json.loads(m.read_text());item['manifest_sha256']=hashlib.sha256(m.read_bytes()).hexdigest();item['passed']=manifest['passed'];item['artifacts']=len(manifest['files'])
   for f in manifest['files']:
    target=m.parent/f['path']
    if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest()!=f['sha256']:errors.append(str(target))
  else:item['manifest_missing']=True
 rows.append(item)
(HERE/'OUTCOMES.json').write_text(json.dumps({'runs':rows,'hash_errors':errors},indent=2)+'\n')
print('completed receipts',len(rows),'hash errors',len(errors),'helper passes',sum(r.get('passed',False) for r in rows))
assert not errors,errors
