from pathlib import Path
import json,hashlib,zipfile,shutil,subprocess,collections
root=Path.cwd(); src=Path('/tmp/win-golden-bca2/full-r-stack-windows-golden-capture'); work=root/'build/windows-golden-bca2-reviewed'; evidence=root/'docs/ci/2026-11-03-windows-goldens'; evidence.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(src.with_suffix('.zip').read_bytes())=='ced16a56262e9b3e2b15667abcc61057f3f4365ffdacf8f71bdcb0436f9f0810'
expected=set('amino-binary-random continuous-random lymph-diagnostic-random-dor amino-binary-cumulative amino-binary-leave-one-out continuous-cumulative continuous-leave-one-out continuous-meta-regression amino-binary-subgroup continuous-subgroup'.split())
report=json.loads((src/'compatibility-report.json').read_text()); drift=[r for r in report['comparison']['rows'] if r['classification']=='text_artifact_drift']; assert len(drift)==10 and {r['id'] for r in drift}==expected and all(r['detail'].startswith('Artifact ') for r in drift)
baseline=root/'tests/analysis_regression/baseline'; before={p.name:p.read_bytes() for p in baseline.iterdir() if p.is_file()}; shutil.copytree(src,work,dirs_exist_ok=True); ledger=[]
for p in (work/'captures').glob('*.json'):
 data=json.loads(p.read_text())
 for a in data['artifacts']:
  old=a['bundle_path']; local=work/'artifacts'/data['id']/Path(old.replace('\\','/')).name
  assert sha(local.read_bytes())==a['sha256']; a['bundle_path']=str(local)
  ledger.append(dict(case=data['id'],original=old,local=str(local),sha256=a['sha256']))
 p.write_text(json.dumps(data,indent=2)+'\n')
subprocess.run(['uv','run','--no-sync','python','scripts/regenerate_golden_presentation.py',str(work)],check=True)
import io
with zipfile.ZipFile(io.BytesIO(before['observed-golden-baseline.zip'])) as z: old={n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(baseline/'observed-golden-baseline.zip') as z: new={n:z.read(n) for n in z.namelist()}
assert old.keys()==new.keys(); changes=[]
def strip_hash(x):
 if isinstance(x,dict): return {k:strip_hash(v) for k,v in x.items() if k!='sha256'}
 if isinstance(x,list): return [strip_hash(v) for v in x]
 return x
for n in old:
 if old[n]==new[n]: continue
 changes.append(n)
 if n.endswith('.json'): assert strip_hash(json.loads(old[n]))==strip_hash(json.loads(new[n])),n
 else: assert n.startswith('artifacts/') and n.split('/')[1] in expected,n
om=json.loads(old['manifest.json']); nm=json.loads(new['manifest.json']); changed_bindings=[]
for a,b in zip(om['curated_golden_set'],nm['curated_golden_set']):
 for aa,bb in zip(a['artifacts'],b['artifacts']):
  if aa['sha256']!=bb['sha256']: changed_bindings.append(a['id'])
assert len(changed_bindings)==10 and set(changed_bindings)==expected
for name in ('numeric-contract.json','plot-descriptors.json'):
 a=json.loads(before[name]);b=json.loads((baseline/name).read_text());a.pop('oracle_sha256');b.pop('oracle_sha256')
 if name=='plot-descriptors.json':
  for rows in (a['rows'],b['rows']):
   for row in rows: row.pop('artifact_oracle_sha256')
 assert a==b,name
assert all(p.read_bytes()==before[p.name] for p in baseline.iterdir() if p.is_file() and p.name not in {'observed-golden-baseline.zip','manifest.json','numeric-contract.json','plot-descriptors.json'})
(evidence/'archive-audit.json').write_text(json.dumps(dict(passed=True,changed_archive_members=changes,changed_plot_bindings=changed_bindings,text_numeric_and_non_hash_case_metadata_unchanged=True,contracts_policy_unchanged=True,before_archive_sha256=sha(before['observed-golden-baseline.zip']),after_archive_sha256=sha((baseline/'observed-golden-baseline.zip').read_bytes())),indent=2)+'\n')
(evidence/'capture-relocation.json').write_text(json.dumps(ledger,indent=2)+'\n')
for case in sorted(expected): shutil.copy2(Path('/tmp/win-golden-bca2/pairs')/(case+'-pair.png'),evidence)
for name in ['download-provenance.json','review-confirmation.json']: shutil.copy2(Path('/tmp/win-golden-bca2')/name,evidence/name)
print('AUDIT PASSED',changed_bindings)
