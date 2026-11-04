"""Serial real Qt/R replay of the 19 failing Windows shard scenarios."""
import json
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
scenarios = ['analysis-diagnostic-regression-continuous', 'plot-workflow-coefficient', 'plot-workflow-deeks', 'plot-workflow-leave-one-out', 'plot-workflow-trimfill', 'project-release-coefficients', 'ratios-hr', 'small-study-diagnostic', 'ux-improvements', 'analysis-diagnostic-regression-factor', 'plot-workflow-contour', 'plot-workflow-forest', 'ratios-irr', 'results-window', 'analysis-diagnostic-regression-multiple', 'plot-workflow-cumulative', 'plot-workflow-funnel', 'plot-workflow-subgroup', 'project-round6-polish', 'manuscript-export', 'manuscript-export-direct', 'analysis-binary.fixed.peto', 'plot-workflow-mh-rd']
scenarios.sort(key=lambda scenario: scenario in {'ratios-hr', 'ratios-irr'})
results_path = Path(__file__).parent / 'replay-results.json'
results = json.loads(results_path.read_text()) if results_path.exists() and '--fresh' not in sys.argv else []
results = [row for row in results if row['exit_code'] == 0]
for scenario in scenarios:
    if any(row['scenario'] == scenario for row in results):
        continue
    command = [sys.executable, str(Path(__file__).parent / 'run_scenario.py'), scenario]
    log = Path(__file__).parent / (scenario + '.log')
    with log.open('w') as stream:
        run = subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT)
    result = {'scenario': scenario, 'command': command, 'exit_code': run.returncode, 'log': str(log.relative_to(root)), 'evidence': log.read_text().splitlines()[0]}
    results.append(result)
    (Path(__file__).parent/'replay-results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(scenario, run.returncode, flush=True)
    if run.returncode:
        break
raise SystemExit(any(result['exit_code'] for result in results))
