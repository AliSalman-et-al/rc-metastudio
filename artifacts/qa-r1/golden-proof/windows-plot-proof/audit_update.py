"""Require exactly the two reviewed PNGs and their SHA bindings to change."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

root=Path(__file__).resolve().parents[4]
here=Path(__file__).parent
baseline=root/'tests/analysis_regression/baseline'
cases={'amino-binary-leave-one-out','continuous-leave-one-out'}
changes=[]
before_bytes=subprocess.check_output(['git','show','2974b88b3a9f2727036fde015750a54eb1f99637:tests/analysis_regression/baseline/observed-golden-baseline.zip'],cwd=root)
with zipfile.ZipFile(io.BytesIO(before_bytes)) as old, zipfile.ZipFile(baseline/'observed-golden-baseline.zip') as new:
    assert old.namelist()==new.namelist()
    for name in old.namelist():
        a,b=old.read(name),new.read(name)
        if a==b: continue
        changes.append(name)
        if name.endswith('.png'):
            assert any(name.startswith('artifacts/'+case+'/') for case in cases)
            continue
        a,b=json.loads(a),json.loads(b)
        if name=='manifest.json': pairs=zip(a['curated_golden_set'],b['curated_golden_set'],strict=True)
        else:
            assert name in {f'captures/{case}.json' for case in cases}
            pairs=[(a,b)]
        for x,y in pairs:
            if x['id'] in cases:
                for artifact in x['artifacts']:
                    artifact['sha256']=next(v['sha256'] for v in y['artifacts'] if v['label']==artifact['label'])
            assert x==y, ('non-artifact-SHA data changed',name)
        assert a==b
    assert len(changes)==5, changes
for filename in ['numeric-contract.json','plot-descriptors.json','manifest.json']:
    a=json.loads(subprocess.check_output(['git','show','2974b88b3a9f2727036fde015750a54eb1f99637:tests/analysis_regression/baseline/'+filename],cwd=root))
    b=json.loads((baseline/filename).read_text())
    if filename=='manifest.json':
        for field in ['observed_golden_analysis_bundle','golden_numeric_contract','golden_plot_descriptor_contract']:
            a[field]=b[field]
    else:
        a['oracle_sha256']=b['oracle_sha256']
        if filename=='plot-descriptors.json':
            for x,y in zip(a['rows'],b['rows'],strict=True):
                if x['id'] in cases:x['artifact_oracle_sha256']=y['artifact_oracle_sha256']
    assert a==b, filename
result={'passed':True,'changed_archive_members':changes,'numerical_contract':'Identical except archive SHA binding. Tolerances unchanged.','plot_descriptors':'Only two artifact oracle SHA bindings and archive SHA. All capabilities, identities and names unchanged.'}
(here/'update-audit.json').write_text(json.dumps(result,indent=2)+'\n')
stat=subprocess.check_output(['git','diff','--stat','--','tests/analysis_regression/baseline'],cwd=root,text=True)
(here/'reference-diff-stat.txt').write_text(stat)
print(json.dumps(result,indent=2));print(stat)
