"""Concise queue state for the audit, without dumping transcripts."""
from pathlib import Path
import json
p=Path(__file__).resolve().parent/'raw'
rows=[json.loads(f.read_text()) for f in p.glob('helper-*.json')]
print('Helper receipts:',len(rows),'passed:',sum(r.get('exit_code')==0 for r in rows),'interrupted:',sum(r.get('exit_code') is None for r in rows),'failed:',[(r['label'],r.get('exit_code')) for r in rows if r.get('exit_code') not in (0,None)])
print('Queue:',(p/'queue.log').read_text().splitlines()[-1][:150])
