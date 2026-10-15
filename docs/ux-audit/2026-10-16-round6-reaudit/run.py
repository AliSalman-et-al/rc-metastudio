"""Retain exact commands, transcripts, runtime environment and exit status."""
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent / "raw"
EVIDENCE.mkdir(exist_ok=True)
label, *command = sys.argv[1:]
assert command and Path(label).name == label
log = EVIDENCE / (label + '.log')
assert not log.exists() and not (EVIDENCE / (label + '.json')).exists(), 'Use a new label to preserve the earlier attempt'
started = datetime.now(UTC).isoformat()
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
start = time.monotonic()
with log.open('w', encoding='utf-8') as stream:
    stream.write(json.dumps(command) + '\n')
    stream.flush()
    process = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
record = dict(audit_scripts_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).resolve().parent.glob('*') if p.suffix in {'.py','.sh'}}, label=label, command=command, cwd=str(ROOT), started=started,
              finished=datetime.now(UTC).isoformat(), seconds=time.monotonic()-start,
              exit_code=process.returncode, revision=revision,
              environment={k: os.environ.get(k) for k in ('RCMS_R_HOME','RCMS_R_LIBS',
                  'RCMS_QT6_BUILD_ROOT','R_LIBS','R_LIBS_USER','QT_QPA_PLATFORM','QT_SCALE_FACTOR','DISPLAY','LD_LIBRARY_PATH','RCMETASTUDIO_QA_ROOT')},
              log=log.name, sha256=hashlib.sha256(log.read_bytes()).hexdigest())
(EVIDENCE / (label + '.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record), flush=True)
sys.exit(process.returncode)
