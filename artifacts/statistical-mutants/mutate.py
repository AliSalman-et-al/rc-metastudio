"""Apply one historical mutant and restore only its exact owned file preimages."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import shutil

root = Path.cwd().resolve()
patch = Path(sys.argv[1]).resolve()
names = subprocess.check_output(['git', 'apply', '--numstat', str(patch)], text=True)
paths = [root / line.split('\t')[2] for line in names.splitlines()]
if not paths or any(not p.resolve().is_relative_to(root) or p.is_symlink() or not p.is_file() for p in paths):
    raise SystemExit('Mutants must modify existing regular files inside the checkout')
preimages = {p: p.read_bytes() for p in paths}
subprocess.run(['git', 'apply', '--check', str(patch)], check=True)
backup = Path(tempfile.mkdtemp(prefix='rcms-mutant-preimages-'))
for index, (path, content) in enumerate(preimages.items()):
    (backup / str(index)).write_bytes(content)
(backup / 'paths.txt').write_text('\n'.join(str(path) for path in preimages))
print(f'Mutant recovery preimages: {backup}', flush=True)

def interrupted(signum, frame):
    raise KeyboardInterrupt(f'interrupted by signal {signum}')

for signum in (signal.SIGINT, signal.SIGTERM):
    signal.signal(signum, interrupted)
try:
    subprocess.run(['git', 'apply', str(patch)], check=True)
    result = subprocess.run(sys.argv[2:])
finally:
    for path, content in preimages.items():
        path.write_bytes(content)
        if path.read_bytes() != content:
            raise RuntimeError(f'Could not restore {path}; recovery retained at {backup}')
shutil.rmtree(backup)
raise SystemExit(result.returncode)
