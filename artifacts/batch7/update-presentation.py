"""Update presentation only; retain every original numeric output and artifact byte."""
import json, pathlib, zipfile, hashlib, difflib, subprocess, io
base=pathlib.Path('tests/analysis_regression/baseline')
archive=base/'observed-golden-baseline.zip'
with zipfile.ZipFile(io.BytesIO(subprocess.check_output(['git','show','origin/master:'+str(archive)]))) as z: entries={i.filename:(i,z.read(i)) for i in z.infolist()}
manifest=json.loads(entries['manifest.json'][1]); diffs=[]
for case in manifest['curated_golden_set']:
 current=json.loads((pathlib.Path('artifacts/batch7/golden-captures')/(case['id']+'.json')).read_text())
 original_outputs=json.dumps(case['outputs'],sort_keys=True)
 for section,old in case['texts'].items():
  new=old if 'meta-regression' in case['id'] else current['texts'][section]
  diffs.extend(difflib.unified_diff(old.splitlines(),new.splitlines(),fromfile=case['id']+'/'+section+' before',tofile=case['id']+'/'+section+' after',lineterm=''))
  case['texts'][section]=new
 # Output identities change with the displayed heading; PNGs and their hashes stay frozen.
 for artifact, actual in zip(case['artifacts'], current['artifacts']): artifact['label']=actual['label']
 for descriptor, actual in zip(case['plot_descriptors'], current['plot_descriptors']):
  descriptor['artifact_label']=actual['artifact_label']
  descriptor['display']['identity']=descriptor['display']['identity'].replace('Forest Plot','Forest plot')
 assert original_outputs==json.dumps(case['outputs'],sort_keys=True)
 name='captures/'+case['id']+'.json'
 entries[name]=(entries[name][0],(json.dumps(case,indent=2,sort_keys=True)+'\n').encode())
entries['manifest.json']=(entries['manifest.json'][0],(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode())
with zipfile.ZipFile(archive,'w') as z:
 for info,data in entries.values(): z.writestr(info,data)
hashzip=hashlib.sha256(archive.read_bytes()).hexdigest()
p=base/'plot-descriptors.json';r=json.loads(p.read_text());r['oracle_sha256']=hashzip
for row in r['rows']:
 current=json.loads((pathlib.Path('artifacts/batch7/golden-captures')/(row['id']+'.json')).read_text())
 row['artifact_label']=current['plot_descriptors'][0]['artifact_label']
 row['display']['identity']=row['display']['identity'].replace('Forest Plot','Forest plot')
p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
p=base/'numeric-contract.json';r=json.loads(p.read_text());r['oracle_sha256']=hashzip;p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
p=base/'manifest.json';r=json.loads(p.read_text())
for key in ['observed_golden_analysis_bundle','golden_plot_descriptor_contract','golden_numeric_contract']:
 f=pathlib.Path(r[key]['path']);r[key]['sha256']=hashlib.sha256(f.read_bytes()).hexdigest();r[key]['size']=f.stat().st_size
p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
pathlib.Path('artifacts/batch7/golden-presentation.diff').write_text('\n'.join(diffs)+'\n')
print('Updated presentation texts/identities only; original outputs and artifact bytes retained.')
