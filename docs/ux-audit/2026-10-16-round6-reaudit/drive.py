"""Serial fresh native audit; each child keeps its own evidence and settings."""
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.verify_rcms import SCENARIOS
priority=['project-reviewer-predictions','project-reviewer-groups','project-reviewer-colours','project-round6-polish','project-axis-proportions','project-axis-others','project-axis-sequential','calculator-grid-precision','calculator-ratio-precision','project-display-labels']
scenarios=priority+[s for s in SCENARIOS if s not in priority and s!='doctor']
assert len(scenarios)==len(set(scenarios))
(HERE/'SCENARIOS.json').write_text(json.dumps(scenarios,indent=2)+'\n')
for scenario in scenarios:
    receipt=HERE/'raw'/('helper-'+scenario+'.json')
    if receipt.exists():
        continue
    print('START',scenario,flush=True)
    subprocess.run([sys.executable,str(HERE/'run.py'),'helper-'+scenario,sys.executable,'scripts/verify_rcms.py',scenario,'--native'],cwd=ROOT)
    print('FINISH',scenario,flush=True)
for family in ('onearm-proportion','onearm-mean','reg-coef','generic-effect','twoarm-proportion','twoarm-mean','twoarm-smd','diagnostic','hr','irr'):
    label='matrix-'+family
    if (HERE/'raw'/(label+'.json')).exists():continue
    subprocess.run([sys.executable,str(HERE/'run.py'),label,sys.executable,'scripts/run_with_timeout.py','--timeout-seconds','600','--label',label,'--',sys.executable,str(HERE/'native_matrix.py'),family],cwd=ROOT)
for script in ('native_design','native_shell','native_options','native_options_remaining'):
    if (HERE/'raw'/(script+'.json')).exists():continue
    subprocess.run([sys.executable,str(HERE/'run.py'),script,sys.executable,'scripts/run_with_timeout.py','--timeout-seconds','600','--label',script,'--',sys.executable,str(HERE/(script+'.py'))],cwd=ROOT)
