"""Apply only the ten hash-verified Windows presentation replacements."""
from pathlib import Path
import json,hashlib,shutil,subprocess,sys
root=Path.cwd();here=root/'artifacts/batch7-windows';capture=Path('/tmp/ci575-golden');work=root/'build/batch7-windows-updater';(work/'captures').mkdir(parents=True,exist_ok=True)
report=json.loads((capture/'compatibility-report.json').read_text());drift=[r for r in report['comparison']['rows'] if r['classification']=='text_artifact_drift']
assert len(drift)==10 and all(r['detail'].startswith('Artifact ') for r in drift)
assert json.loads((here/'windows-data-marks.json').read_text())['passed']
assert json.loads((here/'data-coordinates-proof.json').read_text())['passed']
shutil.copy2(capture/'compatibility-report.json',work/'compatibility-report.json');ledger=[]
for p in (capture/'captures').glob('*.json'):
 value=json.loads(p.read_text())
 for a in value['artifacts']:
  old=a['bundle_path'];source=capture/'artifacts'/value['id']/Path(old.replace('\\','/')).name
  assert hashlib.sha256(source.read_bytes()).hexdigest()==a['sha256'];a['bundle_path']=str(source.resolve())
  ledger.append(dict(case=value['id'],original=old,local=str(source),sha256=a['sha256']))
 (work/'captures'/p.name).write_text(json.dumps(value,indent=2)+'\n')
shutil.copy2(root/'tests/analysis_regression/baseline/observed-golden-baseline.zip','/tmp/ci575-before-update.zip')
subprocess.run([sys.executable,'scripts/regenerate_golden_presentation.py',str(work)],check=True)
(here/'capture-relocation.json').write_text(json.dumps(ledger,indent=2)+'\n')
