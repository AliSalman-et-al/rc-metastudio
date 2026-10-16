"""Bind ignored owned inputs, logs and custom captures after queues close."""
from pathlib import Path
from datetime import datetime,UTC
import hashlib,json
HERE=Path(__file__).resolve().parent
rows=[]
for p in sorted((HERE/'raw').rglob('*')):
 if p.is_file():rows.append({'path':str(p.relative_to(HERE)),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(HERE/'RAW-MANIFEST.json').write_text(json.dumps({'recorded':datetime.now(UTC).isoformat(),'scope':'Owned ignored raw/ files at final audit reconciliation; helper artifact hashes are separately verified in OUTCOMES.json.','files':rows},indent=2)+'\n')
print('retained raw files',len(rows),'bytes',sum(r['size'] for r in rows))
