"""Serial native audit; retain failed attempts and continue independent cases."""
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.verify_rcms import SCENARIOS
HERE = Path(__file__).resolve().parent
records = json.loads((HERE / 'RUNS.json').read_text()) if (HERE / 'RUNS.json').exists() else []
completed = {r['label'].removeprefix('native-') for r in records if r['exit_code'] == 0}
for scenario in SCENARIOS:
    if scenario in completed:
        continue
    command = [sys.executable, str(HERE / 'run.py'), 'native-' + scenario,
               'uv', 'run', 'python', 'scripts/verify_rcms.py', scenario, '--native']
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(scenario, result.returncode, flush=True)
    records.append(json.loads((HERE / 'raw' / ('native-' + scenario + '.json')).read_text()))
    (HERE / 'RUNS.json').write_text(json.dumps(records, indent=2) + '\n')

(HERE / 'raw' / 'suite-finished').write_text('complete\n')
