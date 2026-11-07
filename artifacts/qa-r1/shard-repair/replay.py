"""Serial real Qt/R replay of the 19 failing Windows shard scenarios."""
import json
import hashlib
import os
import platform
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[3]
scenarios = ['analysis-diagnostic-regression-continuous', 'plot-workflow-coefficient', 'plot-workflow-deeks', 'plot-workflow-leave-one-out', 'plot-workflow-trimfill', 'project-release-coefficients', 'ratios-hr', 'small-study-diagnostic', 'ux-improvements', 'analysis-diagnostic-regression-factor', 'plot-workflow-contour', 'plot-workflow-forest', 'ratios-irr', 'results-window', 'analysis-diagnostic-regression-multiple', 'plot-workflow-cumulative', 'plot-workflow-funnel', 'plot-workflow-subgroup', 'project-round6-polish', 'manuscript-export', 'manuscript-export-direct', 'analysis-binary.fixed.peto', 'plot-workflow-mh-rd']
scenarios.sort(key=lambda scenario: scenario in {'ratios-hr', 'ratios-irr'})
results_path = Path(__file__).parent / 'replay-results.json'
identity = {
    'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
    'diff': hashlib.sha256(subprocess.check_output(['git', 'diff', 'HEAD'], cwd=root)).hexdigest(),
    'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
    'environment': {key: os.environ.get(key) for key in ('RCMS_R_HOME', 'RCMS_R_LIBS', 'R_LIBS', 'R_LIBS_USER', 'RCMS_QT6_BUILD_ROOT', 'QT_QPA_PLATFORM')},
    'inputs': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in sorted((root / 'sample_projects').rglob('*')) if path.is_file()},
    'runtime_files': {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
        for key in ('RCMS_R_LIBS', 'R_LIBS', 'R_LIBS_USER', 'RCMS_QT6_BUILD_ROOT')
        for directory in os.environ.get(key, '').split(os.pathsep) if directory
        for path in sorted(Path(directory).rglob('*'))
        if path.is_file() and (path.name == 'DESCRIPTION' or path.suffix in {'.rdb', '.rdx', '.py'})},
    'driver': hashlib.sha256((Path(__file__).parent / 'run_scenario.py').read_bytes()).hexdigest(),
}
identity_path = results_path.with_suffix('.identity.json')
if '--resume' in sys.argv:
    if not identity_path.exists() or json.loads(identity_path.read_text()) != identity:
        raise SystemExit('Resume identity differs or is absent; run without --resume.')
    results = json.loads(results_path.read_text())
else:
    results = []
identity_path.write_text(json.dumps(identity, indent=2) + '\n')
results = [row for row in results if row['exit_code'] == 0]
for scenario in scenarios:
    if any(row['scenario'] == scenario for row in results):
        continue
    command = [sys.executable, str(Path(__file__).parent / 'run_scenario.py'), scenario]
    log = Path(__file__).parent / (scenario + '.log')
    with log.open('w') as stream:
        run = subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT)
    result = {'scenario': scenario, 'command': command, 'exit_code': run.returncode, 'log': str(log.relative_to(root)), 'evidence': next(iter(log.read_text().splitlines()), '')}
    results.append(result)
    (Path(__file__).parent/'replay-results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(scenario, run.returncode, flush=True)
    if run.returncode:
        break
raise SystemExit(any(result['exit_code'] for result in results))
