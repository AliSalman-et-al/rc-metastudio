"""Append exact completed review commands and verbatim failures, retaining history."""
import hashlib
import json
from pathlib import Path
import re
import shlex

HERE = Path(__file__).resolve().parent
rows = []
for path in (HERE / 'raw').glob('review1-*.json'):
    row = json.loads(path.read_text())
    if not {'label', 'command', 'exit_code', 'log'}.issubset(row):
        continue
    log = HERE / 'raw' / row['log']
    assert hashlib.sha256(log.read_bytes()).hexdigest() == row['sha256'], row['label']
    rows.append(row)
rows.sort(key=lambda r: r['started'])
latest = {r['label']: r for r in rows}
assert latest['review1-full-readable']['exit_code'] == 0
assert latest['review1-numerical-final']['exit_code'] == 0
assert all(latest['review1-native-readable-' + family]['exit_code'] == 0
           for family in ('precision', 'hr', 'irr', 'diagnostic'))

body = ['## Opus review 1 — complete command ledger', '',
        'All commands below ran from the repository root after sourcing `ENV.sh`.',
        'Each was wrapped with `uv run python docs/ux-audit/2026-10-14-round3/run.py LABEL COMMAND`.',
        '`TEST-RUNS.json` retains exact argv/environment/timestamps/revision/log SHA-256,',
        'including the original round failures. Raw logs and child manifests remain',
        'available locally; no nonzero attempt counts as a pass.', '',
        '| Label | Exit | Exact command |', '| --- | ---: | --- |']
for r in rows:
    command = shlex.join(r['command']).replace('|', '\\|')
    body.append(f"| {r['label']} | {r['exit_code']} | `{command}` |")
body += ['', '### Verbatim nonzero attempt diagnostics', '',
         'Deliberate before-repair failures, presentation drift, fixture mistakes and',
         'the stopped first full run are retained below. Repeated identical diagnostics',
         'within one helper transcript are printed once. Full assertion payloads are',
         'retained when the exception contains the report. Golden comparison rows are',
         'copied directly from the printed JSON; no numerical oracle was refreshed.', '']
for r in rows:
    if not r['exit_code']:
        continue
    log = (HERE / 'raw' / r['log']).read_text()
    diagnostics = []
    lines = log.splitlines()
    for i, line in enumerate(lines):
        if re.match(r'^(AssertionError|ValueError|RuntimeError|Error)(:|$)', line):
            block = [line]
            j = i + 1
            while j < len(lines) and not lines[j].startswith(('Traceback', '  File ', 'stdout.log', 'stderr.log')):
                block.append(lines[j]); j += 1
            diagnostics.append('\n'.join(block).rstrip())
        elif line.startswith(('Golden compatibility verification failed:', 'UNEXPECTED DIALOG:', 'KeyboardInterrupt')):
            diagnostics.append(line)
        elif 'Processing terminated since k = 0.' in line:
            diagnostics.append(line)
    diagnostics += [m.group(0).strip('\n') for m in re.finditer(
        r'\n[ ]*\{\n[ ]*"classification": "(?!pass"|accepted_exception")[^\n]+[\s\S]*?\n[ ]*\}', log)]
    if r['exit_code'] == 130:
        diagnostics.append('KeyboardInterrupt' if 'KeyboardInterrupt' in log else 'SIGINT: exit 130')
    diagnostics = list(dict.fromkeys(diagnostics))
    assert diagnostics, r['label']
    body += [f"`{r['label']}` — exit {r['exit_code']}", '', '```text', '\n\n'.join(diagnostics), '```', '']
marker = '\n## Opus review 1 — complete command ledger\n'
path = HERE / 'TESTS.md'
previous = path.read_text().split(marker)[0]
path.write_text(previous.rstrip() + '\n\n' + '\n'.join(body).rstrip() + '\n')
print(f'Appended {len(rows)} exact review attempts and {sum(bool(r["exit_code"]) for r in rows)} nonzero exits; prior test history retained.')
