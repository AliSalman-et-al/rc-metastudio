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
