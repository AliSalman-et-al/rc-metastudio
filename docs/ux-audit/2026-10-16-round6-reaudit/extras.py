"""Serial final entry-point checks after the style/scale queue closes."""
from pathlib import Path
import subprocess,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
for attempt in range(216):
 if (HERE/'raw/scale-2.0.json').exists():break
 time.sleep(50)
else:raise SystemExit('No final scale receipt within three hours; no additional GUI started.')
for label,script,bound in [('native-samples','native_samples',600),('native-guard-keyboard','native_guard_keyboard',300),('native-controls','native_controls',300)]:
 if (HERE/'raw'/(label+'.json')).exists():continue
 print('START',label,flush=True)
 subprocess.run([sys.executable,str(HERE/'run.py'),label,sys.executable,'scripts/run_with_timeout.py','--timeout-seconds',str(bound),'--label',label,'--',sys.executable,str(HERE/(script+'.py'))],cwd=ROOT)
 print('FINISH',label,flush=True)
