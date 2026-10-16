"""Prove the complete warm registry reused intact full-profile artifacts."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.verification_evidence import CACHE, passed_evidence
full = json.loads((HERE / 'FULL-PROFILE.json').read_text())
context = json.loads((HERE / 'WARM-CONTEXT.json').read_text())
attempt = json.loads((HERE / 'raw/dx-warm-matrix.json').read_text())
assert attempt['exit_code'] == 0
log = (HERE / 'raw' / attempt['log']).read_text()
directory = Path(re.search(r'Complete-run evidence: (.+)', log)[1])
summary = json.loads((directory / 'summary.json').read_text())
assert summary['passed'] and len(summary['commands']) == 2
pytest_log = (directory / '00.log').read_text()
assert '98 passed' in pytest_log and context['sha256'] in pytest_log
rows = []
for run in full['runs']:
    if run['scenario'] == 'doctor': continue
    evidence = passed_evidence(context, run['scenario'])
    assert evidence == ROOT / run['evidence'], run
    assert hashlib.sha256((evidence / 'manifest.json').read_bytes()).hexdigest() == run['manifest_sha256']
    rows.append({'scenario': run['scenario'], 'evidence': run['evidence'], 'manifest_sha256': run['manifest_sha256']})
assert len(rows) == 98
record = {'passed': True, 'attempt': attempt, 'context': context['sha256'], 'reused_cases': rows,
          'doctor_command': summary['commands'][1], 'pytest_results_verbatim': [line for line in pytest_log.splitlines() if 'passed in' in line]}
(HERE / 'DX-WARM-PROFILE.json').write_text(json.dumps(record, indent=2) + '\n')
print('All 98 original full-profile manifests reused with intact hashes; fresh doctor passed.')
