"""Keep representative native images; preserve other captures as raw execution evidence."""
import json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
archive=HERE/'raw'/'uncurated-native';archive.mkdir(exist_ok=True)
for index in sorted(HERE.glob('MATRIX-*.json')):
 rows=json.loads(index.read_text())
 for row in rows:
  p=HERE/row['path']
  if not p.exists() or not row['path'].startswith('screenshots/'):continue
  name=p.name
  keep=not name.endswith('-bottom.png')
  keep=keep or '-subgroup-report-bottom.png' in name
  keep=keep or '-standard-figure' in name
  keep=keep or ('matrix-hr-' in name and '-figure' in name)
  keep=keep or ('matrix-hr-' in name and ('-cumulative-report-bottom' in name or '-leave-one-out-report-bottom' in name))
  keep=keep or ('matrix-diagnostic-cumulative-figure-1-bottom' in name)
  keep=keep or '-subgroup-figure-bottom' in name
  if not keep:
   row['original_capture_path']=row['path'];row['path']='raw/uncurated-native/'+name;shutil.move(p,archive/name)
  row['curated']=keep
 index.write_text(json.dumps(rows,indent=2)+'\n')
print('curated native matrix screenshots',len(list((HERE/'screenshots').glob('matrix-*.png'))))
