"""Serial real Qt/R replay of the 19 failing Windows shard scenarios."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
root = Path(__file__).resolve().parents[3]
scenarios = ['analysis-diagnostic-regression-continuous', 'plot-workflow-coefficient', 'plot-workflow-deeks', 'plot-workflow-leave-one-out', 'plot-workflow-trimfill', 'project-release-coefficients', 'ratios-hr', 'small-study-diagnostic', 'ux-improvements', 'analysis-diagnostic-regression-factor', 'plot-workflow-contour', 'plot-workflow-forest', 'ratios-irr', 'results-window', 'analysis-diagnostic-regression-multiple', 'plot-workflow-cumulative', 'plot-workflow-funnel', 'plot-workflow-subgroup', 'project-round6-polish', 'manuscript-export', 'manuscript-export-direct', 'analysis-binary.fixed.peto', 'plot-workflow-mh-rd']
scenarios.sort(key=lambda scenario: scenario in {'ratios-hr', 'ratios-irr'})
runs = Path(__file__).parent / 'runs'
runs.mkdir(exist_ok=True)
output = Path(tempfile.mkdtemp(prefix='replay-', dir=runs))
results_path = output / 'replay-results.json'
print(f'Replay output: {output}', flush=True)
results = []
for scenario in scenarios:
    command = [sys.executable, str(Path(__file__).parent / 'run_scenario.py'), scenario]
    log = output / (scenario + '.log')
    with log.open('w') as stream:
        run = subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT)
    result = {'scenario': scenario, 'command': command, 'exit_code': run.returncode, 'log': str(log.relative_to(root)), 'evidence': next(iter(log.read_text().splitlines()), '')}
    results.append(result)
    results_path.write_text(json.dumps(results,indent=2)+'\n')
    print(scenario, run.returncode, flush=True)
    if run.returncode:
        break
raise SystemExit(any(result['exit_code'] for result in results))
