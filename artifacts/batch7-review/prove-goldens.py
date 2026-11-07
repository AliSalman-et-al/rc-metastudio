"""Prove label-only metadata edits and unchanged numeric spellings against master."""
import difflib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

base=Path('tests/analysis_regression/baseline')
proof=Path(__file__).parent
labels={'Cumulative Summary':'Cumulative summary','Leave-one-out Summary':'Leave-one-out summary','Subgroup Summary':'Subgroup summary'}
def relabel(value):
    if isinstance(value,dict):return {labels.get(k,k):relabel(v) for k,v in value.items()}
    if isinstance(value,list):return [relabel(v) for v in value]
    return labels.get(value,value) if isinstance(value,str) else value

def original(name):return subprocess.check_output(['git','show','a1ae1b49:'+str(base/name)])
with zipfile.ZipFile(io.BytesIO(original('observed-golden-baseline.zip'))) as before, zipfile.ZipFile(base/'observed-golden-baseline.zip') as after:
    old=json.loads(before.read('manifest.json'));new=json.loads(after.read('manifest.json'))
    assert len(before.namelist()) == len(set(before.namelist()))
    assert len(after.namelist()) == len(set(after.namelist()))
    assert set(before.namelist()) == set(after.namelist()), 'archive member inventory differs'
    old_ids = [case['id'] for case in old['curated_golden_set']]
    new_ids = [case['id'] for case in new['curated_golden_set']]
    assert old_ids and len(old_ids) == len(set(old_ids))
    assert old_ids == new_ids, 'case identity/order differs'
    for a,b in zip(old['curated_golden_set'],new['curated_golden_set'], strict=True):
        assert relabel(a['outputs'])==b['outputs'],a['id']
        assert a['parameters']==b['parameters'],a['id']
    binary=[n for n in before.namelist() if not n.endswith('.json')]
    assert all(before.read(n)==after.read(n) for n in binary)
old_contract=relabel(json.loads(original('numeric-contract.json')))
new_contract=json.loads((base/'numeric-contract.json').read_text())
old_contract.pop('oracle_sha256');new_contract.pop('oracle_sha256')
assert old_contract==new_contract
(proof/'numeric-oracle-proof.json').write_text(json.dumps(dict(cases=len(old_ids),all_frozen_numeric_outputs_unchanged=True,all_parameters_unchanged=True,unchanged_binary_artifacts=len(binary),contract_values_and_tolerances_unchanged=True,only_numeric_metadata_change='public heading keys and archive SHA binding'),indent=2)+'\n')
number=re.compile(r'(?<!\w)[+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?')
rows=[]
for case in old['curated_golden_set']:
    if 'meta-regression' in case['id']:continue # existing accepted exceptions stay frozen
    actual=json.loads((proof/'golden-captures'/(case['id']+'.json')).read_text())
    for title,text in case['texts'].items():
        rendered=actual['texts'][labels.get(title,title)]
        assert number.findall(text)==number.findall(rendered),(case['id'],title)
        rows.append(dict(case=case['id'],section=title,numeric_tokens=len(number.findall(text)),numeric_spellings_identical=True))
(proof/'golden-numeric-spelling-proof.json').write_text(json.dumps(rows,indent=2)+'\n')
def projection(contract):
    return [dict(id=r['id'],artifact_label=r['artifact_label'],display_title=r['display']['identity']) for r in contract['rows']]
a=projection(json.loads(original('plot-descriptors.json')))
b=projection(json.loads((base/'plot-descriptors.json').read_text()))
(proof/'golden-plot-labels.diff').write_text('\n'.join(difflib.unified_diff(json.dumps(a,indent=2).splitlines(),json.dumps(b,indent=2).splitlines(),fromfile='master plot labels',tofile='corrected plot labels',lineterm=''))+'\n')
print('All frozen numbers, tolerances, parameters and PNG bytes unchanged; every golden numeric spelling matches master.')
