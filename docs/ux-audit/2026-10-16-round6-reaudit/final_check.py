"""Reconcile completed audit coverage, retained hashes and local report links."""
from pathlib import Path
from datetime import datetime,UTC
import hashlib,json,re,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
scenarios=read(HERE/'SCENARIOS.json');runs=read(HERE/'OUTCOMES.json')['runs'];by={r['label']:r for r in runs}
assert not read(HERE/'OUTCOMES.json')['hash_errors']
for scenario in scenarios:
 r=by['helper-'+scenario]
 if scenario=='project-reviewer-predictions':
  assert r['exit_code'] is None
  assert by['prediction-remaining-final']['exit_code']==0
  assert (HERE/'PREDICTION-RECOVERY.json').is_file()
 else:assert r['exit_code']==0 and r.get('passed'),scenario
families=('onearm-proportion','onearm-mean','reg-coef','generic-effect','twoarm-proportion','twoarm-mean','twoarm-smd','diagnostic','hr','irr')
for style in ('','-revman','-bmj'):
 for family in families:
  if not style and family in ('hr','irr'):
   assert by['matrix-'+family]['exit_code']==1
   assert by['matrix-'+family+'--wording-recovery']['exit_code']==0
   assert next(r for r in read(HERE/'RATIO-MATRIX-RECOVERY.json') if r['family']==family)['unique_cells']==5
  else:assert by['matrix-'+family+style]['exit_code']==0,(family,style)
assert by['native_design']['exit_code']==1 and by['native-toolbar']['exit_code']==0
assert 'QToolBar has been deleted' in (HERE/'raw/native_design.log').read_text()
for label in ('native-toolbar','native_shell','native_options','native_options_remaining','axis-apply','scale-1.5','scale-2.0','native-samples','native-guard-keyboard','native-controls','native-editor-inventory','matrix-diagnostic--lower-recovery'):
 assert by[label]['exit_code']==0,label
for row in read(HERE/'RAW-MANIFEST.json')['files']:
 assert sha(HERE/row['path'])==row['sha256'],row['path']
images={}
for index in sorted(HERE.glob('SELECTED-*.json')):
 for row in read(index):
  p=HERE/row['path'];assert p.is_file() and sha(p)==row['sha256'],p
  images[row['path']]=row['sha256']
for row in read(HERE/'SOURCE-INTEGRITY.json')['files']:
 assert sha(ROOT/row['path'])==row['sha256'],row['path']
changed=subprocess.check_output(['git','diff','--name-only','b48c802','--','src','R','ui','config','pyproject.toml','uv.lock','tests','sample_projects'],cwd=ROOT,text=True).splitlines()
assert not changed,changed
score=read(HERE/'SCORECARD.json');assert len(score['rows'])==100 and len({r['id'] for r in score['rows']})==100
assert 'DRAFT' not in score['status']
report=(HERE/'REPORT.md').read_text();assert 'IN PROGRESS' not in report
for target in re.findall(r'\]\(([^)]+)\)',report):
 if '://' in target or target.startswith('#'):continue
 assert (HERE/target.split('#')[0]).exists(),target
result={'checked':datetime.now(UTC).isoformat(),'revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'maintained_scenarios':len(scenarios),'prediction_recovery':'17 retained cases plus one completed continuation','matrix_cells':150,'curated_images':len(images),'source_files_unchanged':len(read(HERE/'SOURCE-INTEGRITY.json')['files']),'changed_product_or_test_paths':changed,'all_local_report_links_resolve':True,'selected_image_hashes':images}
(HERE/'FINAL-CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:v for k,v in result.items() if k!='selected_image_hashes'})
