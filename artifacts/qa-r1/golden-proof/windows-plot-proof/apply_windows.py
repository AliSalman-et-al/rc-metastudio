"""Relocate verified capture paths, then use the repository reference updater."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[4]
here = Path(__file__).parent
capture = here.parent / 'windows-capture'
assert json.loads((here/'proof.json').read_text())['passed']
working = here/'updater-input'
(working/'captures').mkdir(parents=True,exist_ok=True)
report = json.loads((capture/'compatibility-report.json').read_text())
drift = [r for r in report['comparison']['rows'] if r['classification']=='text_artifact_drift']
assert {r['id'] for r in drift} == {'amino-binary-leave-one-out','continuous-leave-one-out'} and len(drift)==2
assert all(r['detail'].startswith('Artifact Leave-one-out Forest plot ') for r in drift)
shutil.copyfile(capture/'compatibility-report.json',working/'compatibility-report.json')
for path in (capture/'captures').glob('*.json'):
    value=json.loads(path.read_text())
    for artifact in value['artifacts']:
        source=capture/'artifacts'/value['id']/Path(artifact['bundle_path']).name
        assert hashlib.sha256(source.read_bytes()).hexdigest()==artifact['sha256']
        artifact['bundle_path']=str(source.resolve())
    (working/'captures'/path.name).write_text(json.dumps(value,indent=2)+'\n')
archive=root/'tests/analysis_regression/baseline/observed-golden-baseline.zip'
shutil.copyfile(archive,here/'before-update.zip')
subprocess.run([sys.executable,str(root/'scripts/regenerate_golden_presentation.py'),str(working)],check=True,cwd=root)
