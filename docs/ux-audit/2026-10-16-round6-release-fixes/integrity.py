"""Check final proof bindings without rerunning statistical fits or UI workflows."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT))
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
installed=json.loads((HERE/'INSTALLED-SOURCE.json').read_text())
for name,sha in installed['source_sha256'].items():assert digest(ROOT/'r/RCMetaR'/name)==sha,name
for name,sha in installed['installed_sha256'].items():assert digest(Path(installed['library'])/'RCMetaR'/name)==sha,name
curated=json.loads((HERE/'CURATED.json').read_text())
for row in curated:assert digest(HERE/row['path'])==row['sha256'],row
full=json.loads((HERE/'FULL-PROFILE.json').read_text())
assert full['passed'] and full['desktop_scenarios']==123 and full['doctor']==1
assert full['summary']['worktree_status_before']==full['summary']['worktree_status_after']==''
from scripts.verification_evidence import source_digest
source_sha=source_digest()
file_count=0
for row in full['runs']:
    work=ROOT/row['evidence'];manifest=json.loads((work/'manifest.json').read_text())
    assert digest(work/'manifest.json')==row['manifest_sha256']
    context=manifest.get('verification_context')
    if context:assert context['source_sha256']==source_sha,(row['scenario'],context['source_sha256'],source_sha)
    for artifact in row['files']:
        assert digest(work/artifact['path'])==artifact['sha256'],artifact
        file_count+=1
numeric=json.loads((HERE/'NUMERICAL-EQUIVALENCE.json').read_text())
assert numeric['passed'] and numeric['original_field_count']==415 and numeric['exact_before_after'] and numeric['max_absolute_difference']==0
baseline_changes=subprocess.check_output(['git','diff','--name-only','c37e427','--','tests/analysis_regression/baseline'],cwd=ROOT,text=True).strip()
assert not baseline_changes,baseline_changes
owned=[]
for pid in (1864035,1869389,1870255,1885143):
    cmd=Path(f'/proc/{pid}/cmdline')
    if cmd.exists() and any(name in cmd.read_text() for name in ('native.py','targeted.py','verify_all.py')):owned.append(pid)
assert not owned,owned
result=dict(passed=True,qualified_source='07c4f4a',source_sha256=source_sha,
    source_install_files=len(installed['source_sha256']),installed_files=len(installed['installed_sha256']),
    profile_receipts=len(full['runs']),profile_artifacts=file_count,curated_files=len(curated),
    inspected_image_frames=sum(row['kind']!='actual export' for row in curated),
    original_fields_exact=415,max_absolute_difference=0,baseline_changes=[],owned_prior_roots_alive=owned,
    full_profile_sha256=digest(HERE/'FULL-PROFILE.json'),curated_manifest_sha256=digest(HERE/'CURATED.json'))
(HERE/'EVIDENCE-INTEGRITY.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
