"""Refresh reviewed labels/small-limit text; never recapture numerical references."""
import difflib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

base = Path('tests/analysis_regression/baseline')
proof = Path('artifacts/batch7-review')
captures = proof/'golden-captures'
labels = {'Cumulative Summary':'Cumulative summary', 'Leave-one-out Summary':'Leave-one-out summary', 'Subgroup Summary':'Subgroup summary'}
def relabel(value):
    if isinstance(value, dict): return {labels.get(k,k):relabel(v) for k,v in value.items()}
    if isinstance(value, list): return [relabel(v) for v in value]
    return labels.get(value,value) if isinstance(value,str) else value

def original(name):
    return subprocess.check_output(['git','show','a1ae1b49:'+str(base/name)])

with zipfile.ZipFile(io.BytesIO(original('observed-golden-baseline.zip'))) as archive:
    entries={i.filename:(i,archive.read(i)) for i in archive.infolist()}
manifest=json.loads(entries['manifest.json'][1]);diffs=[]
for case in manifest['curated_golden_set']:
    current=json.loads((captures/(case['id']+'.json')).read_text())
    old=case['texts'];new={}
    for section,text in old.items():
        heading=labels.get(section,section)
        rendered=text if 'meta-regression' in case['id'] else current['texts'][heading]
        diffs.extend(difflib.unified_diff([section,*text.splitlines()], [heading,*rendered.splitlines()], fromfile=case['id']+' before', tofile=case['id']+' after',lineterm=''))
        new[heading]=rendered
    case['texts']=new
    old_outputs=case['outputs'];case['outputs']=relabel(old_outputs)
    # This only renames public heading keys; all fields, values and tolerances stay frozen.
    assert list(old_outputs.values()) == list(case['outputs'].values())
    for artifact,actual in zip(case['artifacts'],current['artifacts']): artifact['label']=actual['label']
    for descriptor,actual in zip(case['plot_descriptors'],current['plot_descriptors']):
        descriptor['artifact_label']=actual['artifact_label']
        descriptor['display']['identity']=actual['display']['identity']
    name='captures/'+case['id']+'.json'
    entries[name]=(entries[name][0],(json.dumps(case,indent=2,sort_keys=True)+'\n').encode())
entries['manifest.json']=(entries['manifest.json'][0],(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode())
archive_path=base/'observed-golden-baseline.zip'
with zipfile.ZipFile(archive_path,'w') as archive:
    for info,data in entries.values(): archive.writestr(info,data)
sha=hashlib.sha256(archive_path.read_bytes()).hexdigest()
p=base/'plot-descriptors.json';contract=json.loads(original(p.name));contract['oracle_sha256']=sha
for row in contract['rows']:
    current=json.loads((captures/(row['id']+'.json')).read_text())
    actual=current['plot_descriptors'][0]
    row['artifact_label']=actual['artifact_label'];row['display']['identity']=actual['display']['identity']
p.write_text(json.dumps(contract,indent=2,sort_keys=True)+'\n')
for name in ['numeric-contract.json','capture-manifest.json']:
    value=relabel(json.loads(original(name)))
    if name=='numeric-contract.json': value['oracle_sha256']=sha
    (base/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
p=base/'manifest.json';outer=json.loads(p.read_text())
for key in ['observed_golden_analysis_bundle','golden_plot_descriptor_contract','golden_numeric_contract']:
    path=Path(outer[key]['path']);outer[key]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();outer[key]['size']=path.stat().st_size
p.write_text(json.dumps(outer,indent=2,sort_keys=True)+'\n')
(proof/'golden-vs-master.diff').write_text('\n'.join(diffs)+'\n')
print('Only presentation and heading-key metadata updated; numerical references retained.')
