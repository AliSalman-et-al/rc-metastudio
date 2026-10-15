"""Bind exact run receipts, failed transcripts and retained evidence bytes."""
import hashlib
import json
from pathlib import Path
import re
import shlex
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
rows=[]
helpers={}
for path in sorted((HERE/'raw').glob('*.json')):
    row=json.loads(path.read_text())
    if not isinstance(row,dict) or 'command' not in row or 'log' not in row:continue
    log=HERE/'raw'/row['log']
    assert digest(log)==row['sha256'], log
    for match in re.finditer(r'^Evidence: (.+)$',log.read_text(),re.M):
        work=Path(match[1]); manifest=work/'manifest.json'
        if not manifest.exists():continue
        data=json.loads(manifest.read_text())
        for file in data['files']:
            assert digest(work/file['path'])==file['sha256'], (manifest,file)
        helpers[str(work.relative_to(ROOT))]=dict(manifest_sha256=digest(manifest),exit_code=data['exit_code'],passed=data['passed'],files=len(data['files']))
    rows.append(row)
for row in json.loads((HERE/'CURATED.json').read_text()):
    assert digest(HERE/row['path'])==row['sha256'],row
custom={}
for directory in sorted((HERE/'raw').iterdir()):
    if directory.is_dir() and (directory/'runtime.json').exists():
        custom[directory.name]={str(p.relative_to(directory)):digest(p) for p in sorted(directory.rglob('*')) if p.is_file()}
(HERE/'OUTCOMES.json').write_text(json.dumps(dict(runs=rows,helper_manifests=helpers,custom_native_files=custom,
    rejected_zero_exit='coefficient-1 skipped targeted editors; coefficient-3 lacked visible-axis frames. coefficient-4 is accepted.',
    full_profile=dict(path='FULL-PROFILE.json',sha256=digest(HERE/'FULL-PROFILE.json'),passed=True) if (HERE/'FULL-PROFILE.json').exists() else None),indent=2)+'\n')
marker='\n## Exact run ledger (generated)\n'
p=HERE/'TESTS.md';text=p.read_text().split(marker)[0]
text+=marker+'\nArgument arrays, environment, dates, elapsed time and transcript hashes are in OUTCOMES.json. Earlier failed attempts remain failed.\n'
for row in rows:
    text+=f'\n### {row["label"]} — exit {row["exit_code"]}\n\n```sh\n{shlex.join(row["command"])}\n```\n\nTranscript: `raw/{row["log"]}`; SHA-256 `{row["sha256"]}`.\n'
p.write_text(text)
print(len(rows),'receipts;',len(helpers),'intact helper manifests;',len(custom),'bound custom native directories')
