"""Retain this review's exact attempts, native receipts and curated image hashes."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

attempts, native = [], []
for path in sorted((HERE / 'raw').glob('review1-*.json')):
    row = json.loads(path.read_text())
    if not isinstance(row, dict) or 'command' not in row or 'log' not in row:
        continue
    log = HERE / 'raw' / row['log']
    assert sha(log) == row['sha256'], log
    transcript = log.read_text(errors='replace')
    if row['exit_code']:
        row['failure_transcript_verbatim'] = transcript
    attempts.append(row)
    for match in re.findall(r'^Evidence: (.+)$', transcript, re.MULTILINE):
        directory = Path(match)
        manifest = directory / 'manifest.json'
        if not manifest.is_file():
            continue
        observed = json.loads(manifest.read_text())
        for retained in observed['files']:
            assert sha(directory / retained['path']) == retained['sha256'], (manifest, retained)
        native.append(dict(label=row['label'], evidence=str(directory.relative_to(ROOT)),
                           manifest_sha256=sha(manifest), manifest=observed,
                           runtime=json.loads((directory / 'runtime.json').read_text()),
                           actions=[json.loads(line) for line in (directory / 'steps.jsonl').read_text().splitlines()]))
(HERE / 'REVIEW1-TEST-RUNS.json').write_text(json.dumps(attempts, indent=2) + '\n')
(HERE / 'REVIEW1-NATIVE.json').write_text(json.dumps(native, indent=2) + '\n')
(HERE / 'REVIEW1-FAILURES.txt').write_text('\n\n'.join(row['label'] + '\n' + row['failure_transcript_verbatim'] for row in attempts if row['exit_code']))
curation = json.loads((HERE / 'REVIEW1-CURATION.json').read_text())
for row in curation:
    assert sha(ROOT / row['source']) == sha(ROOT / row['destination']) == row['sha256'], row
print(f'{len(attempts)} attempts, {sum(bool(row["exit_code"]) for row in attempts)} nonzero exits; {len(native)} bound desktop receipts; {len(curation)} unchanged curated images.')
