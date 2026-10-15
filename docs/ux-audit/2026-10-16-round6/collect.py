"""Bind recorded commands, failed transcripts and helper artifacts to this round."""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
rows, helpers, failures = [], {}, []
for receipt in sorted((HERE / 'raw').glob('*.json')):
    row = json.loads(receipt.read_text())
    if 'command' not in row or 'exit_code' not in row:
        continue
    log = HERE / 'raw' / row['log']
    assert hashlib.sha256(log.read_bytes()).hexdigest() == row['sha256'], log
    text = log.read_text(errors='replace')
    row['receipt'] = str(receipt.relative_to(ROOT))
    row['helper_evidence'] = []
    for match in re.finditer(r'^Evidence: (.+)$', text, re.M):
        directory = Path(match[1].strip())
        manifest_path = directory / 'manifest.json'
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text())
        checked = 0
        for artifact in manifest['files']:
            path = directory / artifact['path']
            assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == artifact['sha256'], path
            checked += 1
        key = str(directory.relative_to(ROOT))
        row['helper_evidence'].append(key)
        helpers[key] = dict(scenario=manifest['scenario'], exit_code=manifest['exit_code'],
                            passed=manifest['passed'], native=manifest.get('native_requested'),
                            revision=manifest['head'], checked_artifacts=checked,
                            manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest())
    rows.append(row)
    if row['exit_code']:
        for match in re.finditer(r'^Complete-run evidence: (.+)$', text, re.M):
            directory = Path(match[1].strip())
            summary_path = directory / 'summary.json'
            if not summary_path.is_file():
                continue
            summary = json.loads(summary_path.read_text())
            for command in summary['commands']:
                nested = directory / command['log']
                expected = summary['files_sha256'][nested.name]
                assert hashlib.sha256(nested.read_bytes()).hexdigest() == expected, nested
                text += '\n\nComplete-profile log: ' + str(nested.relative_to(ROOT)) + '\n'
                text += nested.read_text(errors='replace')
        failures += ['## ' + receipt.stem, '', 'Command: `' + ' '.join(row['command']) + '`', '', '```text', text, '```', '']
(HERE / 'TEST-RUNS.json').write_text(json.dumps(rows, indent=2) + '\n')
(HERE / 'HELPER-EVIDENCE.json').write_text(json.dumps(helpers, indent=2) + '\n')
(HERE / 'FAILURES.md').write_text('# Failed attempts (verbatim)\n\n' + '\n'.join(failures))
(HERE / 'TESTS.md').write_text('# Recorded verification\n\nExact commands, environment, revisions, log hashes and exits: [TEST-RUNS](TEST-RUNS.json).\n\nHelper inputs/screenshots/projects/logs and checked artifact hashes: [HELPER-EVIDENCE](HELPER-EVIDENCE.json).\n\nAll failed recorded attempts are preserved verbatim in [FAILURES](FAILURES.md); later passes do not erase them.\n\n' + '\n'.join(f'- `{r["label"]}`: exit {r["exit_code"]}, {r["seconds"]:.2f} s.' for r in rows) + '\n')
print(f'{len(rows)} recorded invocations; {len(helpers)} helpers with verified artifacts; {sum(r["exit_code"] != 0 for r in rows)} failed invocations retained.')
