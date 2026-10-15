"""Run remaining targeted audit only after the serial queue closes its last child."""
import json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
for attempt in range(240):
 if (HERE/'raw/native_options_remaining.json').exists():break
 time.sleep(30)
else:raise SystemExit('Main native queue did not finish within two hours; no second GUI started.')
commands=[('axis-apply', [sys.executable,'scripts/run_with_timeout.py','--timeout-seconds','1200','--label','axis-apply','--',sys.executable,str(HERE/'axis_apply.py')],{})]
for style in ('revman','bmj'):
 for family in ('onearm-proportion','onearm-mean','reg-coef','generic-effect','twoarm-proportion','twoarm-mean','twoarm-smd','diagnostic','hr','irr'):
  commands.append(('matrix-'+family+'-'+style,[sys.executable,'scripts/run_with_timeout.py','--timeout-seconds','600','--label','matrix-style','--',sys.executable,str(HERE/'native_matrix.py'),family],{'RCMS_AUDIT_STYLE':style}))
for scale in ('1.5','2.0'):
 commands.append(('scale-'+scale,[sys.executable,'scripts/verify_rcms.py','review1-design','--native'],{'QT_SCALE_FACTOR':scale}))
for label,command,env in commands:
 if (HERE/'raw'/(label+'.json')).exists():continue
 print('START',label,flush=True)
 subprocess.run([sys.executable,str(HERE/'run.py'),label,*command],cwd=ROOT,env={**os.environ,**env})
 print('FINISH',label,flush=True)
