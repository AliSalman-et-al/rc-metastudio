"""Wait for the owned serial queue, then run the corrected coefficient proof."""
from pathlib import Path
import subprocess
import sys
import time
pid=int(sys.argv[1])
cmd=Path(f'/proc/{pid}/cmdline')
if cmd.exists(): assert b'round6-release-fixes/targeted.py' in cmd.read_bytes()
deadline=time.monotonic()+1800
while cmd.exists() and time.monotonic()<deadline: time.sleep(5)
assert not cmd.exists(), 'native queue still owns display'
raise SystemExit(subprocess.call(['uv','run','python','docs/ux-audit/2026-10-14-round3/run.py','coefficient-2',
    'uv','run','python','scripts/verify_rcms.py','project-release-coefficients','--native']))
