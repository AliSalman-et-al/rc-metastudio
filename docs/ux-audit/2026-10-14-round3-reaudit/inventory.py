"""Bind replay, captures, runtime and completed attempts, retaining failures."""
import json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
runs=[];failures=[]
for p in sorted((HERE/'raw').glob('*.json')):
 d=json.loads(p.read_text())
 if not isinstance(d,dict) or 'exit_code' not in d:continue
 runs.append(d)
 if d['exit_code']:
  failures.append(dict(label=d['label'],exit_code=d['exit_code'],verbatim=(HERE/'raw'/d['log']).read_text()))
 else:
  log=(HERE/'raw'/d['log']).read_text();m=re.search('Evidence: (.+)',log)
  if m:
   e=Path(m[1]);manifest=json.loads((e/'manifest.json').read_text());assert manifest['passed']
   assert json.loads((e/'runtime.json').read_text())['platform_plugin']=='xcb'
   for f in manifest['files']:
    assert hashlib.sha256((e/f['path']).read_bytes()).hexdigest()==f['sha256'],e/f['path']
(HERE/'OUTCOMES.json').write_text(json.dumps(runs,indent=2)+'\n')
(HERE/'FAILURES.json').write_text(json.dumps(failures,indent=2)+'\n')
files=[dict(path=str(p.relative_to(HERE)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in sorted(HERE.rglob('*')) if p.is_file() and 'raw' not in p.relative_to(HERE).parts and '__pycache__' not in p.parts and p.name!='EVIDENCE.json']
(HERE/'EVIDENCE.json').write_text(json.dumps(files,indent=2)+'\n')
print('attempts',len(runs),'failed',len(failures),'files',len(files))
