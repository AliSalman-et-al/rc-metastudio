"""Serial native queue, with bounded wait for an already-owned header replay."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
if len(sys.argv) > 1:
    pid = int(sys.argv[1])
    command = Path(f'/proc/{pid}/cmdline')
    if command.exists():
        assert b'round6-release-fixes/native.py\x00headers-fixed-3' in command.read_bytes()
    deadline = time.monotonic() + 900
    while command.exists() and time.monotonic() < deadline:
        time.sleep(5)
    assert not command.exists(), 'owned header replay still active; no second native lane started'
commands = [
    ('presentation-1', ['uv','run','python',str(HERE/'native.py'),'presentation-1']),
    ('coefficient-1', ['uv','run','python','scripts/verify_rcms.py','project-release-coefficients','--native']),
    ('back-continuous-1', ['uv','run','python','scripts/verify_rcms.py','calculator-mode-back-continuous','--native']),
    ('back-binary-1', ['uv','run','python','scripts/verify_rcms.py','calculator-mode-back-binary','--native']),
    ('pln-axes-1', ['uv','run','python','scripts/verify_rcms.py','project-axis-proportions','--native']),
    ('stress-1', ['uv','run','python','scripts/verify_rcms.py','calculator-ratio-precision','--native']),
]
rows = []
for label, command in commands:
    result = subprocess.run(['uv','run','python','docs/ux-audit/2026-10-14-round3/run.py',label,
        'uv','run','python','scripts/run_with_timeout.py','--timeout-seconds','900','--label',label,'--',*command],cwd=ROOT)
    rows.append(dict(label=label,exit_code=result.returncode))
    (HERE/'TARGETED.json').write_text(json.dumps(rows,indent=2)+'\n')
sys.exit(any(row['exit_code'] for row in rows))
