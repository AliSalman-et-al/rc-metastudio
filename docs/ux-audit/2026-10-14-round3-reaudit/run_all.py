"""Serial native audit; retain failed attempts and continue independent cases."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.verify_rcms import SCENARIOS
HERE = Path(__file__).resolve().parent
runs = HERE / 'runs'
runs.mkdir(exist_ok=True)
output = Path(tempfile.mkdtemp(prefix='native-', dir=runs))
raw = output / 'raw'
raw.mkdir()
environment = {**os.environ, 'RCMS_AUDIT_OUTPUT': str(raw)}
print(f'Audit output: {output}', flush=True)
records = []
for scenario in SCENARIOS:
    command = [sys.executable, str(HERE / 'run.py'), 'native-' + scenario,
               'uv', 'run', 'python', 'scripts/verify_rcms.py', scenario, '--native']
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=environment)
    print(scenario, result.returncode, flush=True)
    receipt = raw / ('native-' + scenario + '.json')
    row = json.loads(receipt.read_text()) if receipt.exists() else {'label': 'native-' + scenario, 'exit_code': 1, 'error': 'missing receipt'}
    if result.returncode:
        row['exit_code'] = result.returncode
    records.append(row)
    (output / 'RUNS.json').write_text(json.dumps(records, indent=2) + '\n')

failed = any(row['exit_code'] != 0 for row in records)
(raw / 'suite-finished').write_text('completed with failures\n' if failed else 'passed\n')
raise SystemExit(int(failed))
