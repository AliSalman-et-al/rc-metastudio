"""Run only remaining targeted captures after the three serial queues close."""
from pathlib import Path
import subprocess,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
for attempt in range(288):
 if (HERE/'raw/native-controls.json').exists():break
 time.sleep(50)
else:raise SystemExit('No final native-controls receipt within four hours; no GUI started.')
commands=[
 ('matrix-hr--wording-recovery','native_matrix.py',['hr','--ratio-wording']),
 ('matrix-irr--wording-recovery','native_matrix.py',['irr','--ratio-wording']),
 ('matrix-diagnostic--lower-recovery','native_matrix.py',['diagnostic','--component-lower']),
 ('native-toolbar','native_toolbar.py',[]),
 ('native-editor-inventory','native_editor_inventory.py',[]),
]
for label,script,args in commands:
 if (HERE/'raw'/(label+'.json')).exists():continue
 print('START',label,flush=True)
 subprocess.run([sys.executable,str(HERE/'run.py'),label,sys.executable,'scripts/run_with_timeout.py','--timeout-seconds','600','--label',label,'--',sys.executable,str(HERE/script),*args],cwd=ROOT)
 print('FINISH',label,flush=True)
