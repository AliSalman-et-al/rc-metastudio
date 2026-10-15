"""Retain the fresh desktop run's saved release project before cleanup."""
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import time
from zipfile import BadZipFile, ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
outer = (HERE/'raw/reviewer-full-final.log').read_text()
profile = Path(re.search(r'^Complete-run evidence: (.+)$',outer,re.M)[1])
started = datetime.strptime(profile.name[:16],'%Y%m%dT%H%M%SZ').replace(tzinfo=UTC).timestamp()
for attempt in range(9000):
    for source in (ROOT/'build/verification/rcms').glob('desktop-*/release-0.5.0.rcms'):
        if source.stat().st_mtime < started:
            continue
        try:
            with ZipFile(source) as archive:
                manifest = json.loads(archive.read('manifest.json'))
            if manifest['application']['version'] != '0.5.0':
                continue
            data = source.read_bytes()
        except (BadZipFile, FileNotFoundError):
            continue
        target = HERE/'release-0.5.0.rcms'
        target.write_bytes(data)
        result = dict(source=str(source.relative_to(ROOT)),path=str(target.relative_to(ROOT)),
                      sha256=hashlib.sha256(data).hexdigest(),manifest=manifest,
                      profile=str(profile.relative_to(ROOT)))
        (HERE/'RELEASE-PROJECT.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result),flush=True)
        raise SystemExit(0)
    time.sleep(.1)
raise RuntimeError('No fresh 0.5.0 release project found before desktop cleanup within 15 minutes')
