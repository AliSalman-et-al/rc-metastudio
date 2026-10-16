"""Keep reviewer commands, failed transcripts and original helper hashes additive."""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
rows, helpers, failures = [], {}, []
for receipt in sorted((HERE/'raw').glob('reviewer-*.json')):
    row = json.loads(receipt.read_text())
    if 'command' not in row or 'exit_code' not in row:
        continue
    log = HERE/'raw'/row['log']
    assert hashlib.sha256(log.read_bytes()).hexdigest() == row['sha256'], log
    text = log.read_text(errors='replace')
    row['receipt'] = str(receipt.relative_to(ROOT))
    row['helper_evidence'] = []
    for match in re.finditer(r'^Evidence: (.+)$',text,re.M):
        directory = Path(match[1].strip())
        manifest_path = directory/'manifest.json'
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text())
        for artifact in manifest['files']:
            path = directory/artifact['path']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact['sha256'], path
        name = str(directory.relative_to(ROOT))
        row['helper_evidence'].append(name)
        helpers[name] = dict(scenario=manifest['scenario'],passed=manifest['passed'],exit_code=manifest['exit_code'],
                            native=manifest.get('native_requested'),revision=manifest['head'],
                            checked_artifacts=len(manifest['files']),
                            manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest())
    rows.append(row)
    if row['exit_code']:
        failures += ['## '+row['label'],'','Command: `'+ ' '.join(row['command'])+'`',
                     '',f"Exit: {row['exit_code']}",'','```text',text,'```','']
(HERE/'REVIEWER-TEST-RUNS.json').write_text(json.dumps(rows,indent=2)+'\n')
(HERE/'REVIEWER-HELPER-EVIDENCE.json').write_text(json.dumps(helpers,indent=2)+'\n')
(HERE/'REVIEWER-FAILURES.md').write_text('# Reviewer attempts — nonzero transcripts verbatim\n\n'+'\n'.join(failures))
print(f'{len(rows)} reviewer commands; {len(helpers)} helper manifests/artifacts checked; {sum(bool(r["exit_code"]) for r in rows)} nonzero attempts retained.')
