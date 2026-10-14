"""Retain exact installed bytes from an active, owned R-stack library."""
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
source = Path(sys.argv[1]).resolve()
target = ROOT / 'build/ux-round3/r-stack-retained-273bd6a'
assert source.name == 'library' and source.parent.name.startswith('RCMetaR-r-stack-'), source
assert not target.exists(), target
record = json.loads((HERE / 'INSTALLED-SOURCE.json').read_text())
package = ROOT / 'r/RCMetaR'
assert all(hashlib.sha256((package / name).read_bytes()).hexdigest() == value for name, value in record['source_sha256'].items())
shutil.copy2(HERE / 'INSTALLED-SOURCE.json', HERE / 'NATIVE-INSTALLED-SOURCE.json')
shutil.copytree(source, target)
def hashes(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.rglob('*')) if p.is_file()}
assert hashes(source) == hashes(target)
record.update(command=[sys.executable, str(Path(__file__).relative_to(ROOT)), str(source)],
              utc=datetime.now(UTC).isoformat(), library=str(target), retained_from=str(source),
              native_source_install_command=record['command'],
              source_install_command=[record['r_home']+'/bin/R', 'CMD', 'INSTALL', '--library='+str(source), str(next(source.parent.glob('RCMetaR_*.tar.gz')))],
              installed_sha256=hashes(target / 'RCMetaR'),
              qualification_note='Exact R-stack installed bytes retained after R CMD check, Reitsma and all 9 bridge tests passed; full desktop/golden/authority qualification recorded separately.')
(HERE / 'INSTALLED-SOURCE.json').write_text(json.dumps(record, indent=2) + '\n')
print('Retained exact R-stack library:', target)
