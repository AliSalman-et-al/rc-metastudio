"""Serial native audit; retain failed attempts and continue independent cases."""
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.verify_rcms import SCENARIOS
HERE = Path(__file__).resolve().parent
records = [] # Every invocation is a new execution; old receipts are historical only.
completed = {r['label'].removeprefix('native-') for r in records if r['exit_code'] == 0}
for scenario in SCENARIOS:
    if scenario in completed:
        continue
    command = [sys.executable, str(HERE / 'run.py'), 'native-' + scenario,
               'uv', 'run', 'python', 'scripts/verify_rcms.py', scenario, '--native']
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(scenario, result.returncode, flush=True)
    receipt = HERE / 'raw' / ('native-' + scenario + '.json')
    row = json.loads(receipt.read_text()) if receipt.exists() else {'label': 'native-' + scenario, 'exit_code': 1, 'error': 'missing receipt'}
    if result.returncode:
        row['exit_code'] = result.returncode
    records.append(row)
    (HERE / 'RUNS.json').write_text(json.dumps(records, indent=2) + '\n')

failed = any(row['exit_code'] != 0 for row in records)
(HERE / 'raw' / 'suite-finished').write_text('completed with failures\n' if failed else 'passed\n')
raise SystemExit(int(failed))
