"""Serial native audit; retain failed attempts and continue independent cases."""
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.verify_rcms import SCENARIOS
HERE = Path(__file__).resolve().parent
records = []
for scenario in SCENARIOS:
    command = [sys.executable, str(HERE / 'run.py'), 'native-' + scenario,
               'uv', 'run', 'python', 'scripts/verify_rcms.py', scenario, '--native']
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(scenario, result.returncode, flush=True)
    records.append(json.loads((HERE / 'raw' / ('native-' + scenario + '.json')).read_text()))
    (HERE / 'RUNS.json').write_text(json.dumps(records, indent=2) + '\n')
