"""Prove the update changes only Windows PNG bytes and their hash bindings."""
from pathlib import Path
import json,zipfile,subprocess,io
root=Path.cwd();here=root/'artifacts/batch7-windows';base=root/'tests/analysis_regression/baseline'
report=json.loads(Path('/tmp/ci575-golden/compatibility-report.json').read_text());cases={r['id'] for r in report['comparison']['rows'] if r['classification']=='text_artifact_drift'}
oldbytes=subprocess.check_output(['git','show','5c213523:tests/analysis_regression/baseline/observed-golden-baseline.zip']);changes=[];pngs=[]
def strip_hash(x):
 if isinstance(x,dict):return {k:strip_hash(v) for k,v in x.items() if k!='sha256'}
 if isinstance(x,list):return [strip_hash(v) for v in x]
 return x
with zipfile.ZipFile(io.BytesIO(oldbytes)) as a,zipfile.ZipFile(base/'observed-golden-baseline.zip') as b:
 assert a.namelist()==b.namelist()
 for name in a.namelist():
  x,y=a.read(name),b.read(name)
  if x==y:continue
  changes.append(name)
  if name.endswith('.png'):assert name.split('/')[1] in cases;pngs.append(name.split('/')[1])
  else:assert strip_hash(json.loads(x))==strip_hash(json.loads(y)),name
assert set(pngs)==cases and len(pngs)==10
for name in ['numeric-contract.json','plot-descriptors.json','manifest.json']:
 a=json.loads(subprocess.check_output(['git','show','5c213523:tests/analysis_regression/baseline/'+name]));b=json.loads((base/name).read_text())
 if name=='manifest.json':
  for key in ['observed_golden_analysis_bundle','golden_numeric_contract','golden_plot_descriptor_contract']:a[key]=b[key]
 else:
  a['oracle_sha256']=b['oracle_sha256']
  if name=='plot-descriptors.json':
   for x,y in zip(a['rows'],b['rows'],strict=True):x['artifact_oracle_sha256']=y['artifact_oracle_sha256']
 assert a==b,name
(here/'update-audit.json').write_text(json.dumps(dict(passed=True,png_cases=sorted(pngs),changed_members=changes,all_texts_numbers_parameters_policy_and_tolerances_unchanged=True),indent=2)+'\n')
print('PASS: exactly ten Windows PNGs; all semantic differences are artifact/archive hashes. No numeric values or tolerances changed.')
