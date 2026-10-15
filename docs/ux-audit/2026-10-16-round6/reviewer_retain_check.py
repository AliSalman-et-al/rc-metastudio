"""Retain the full profile's R check files before its owned temp tree closes."""
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0,str(ROOT))
from scripts.verification_evidence import source_digest

label = 'reviewer-full-final'
outer = HERE/'raw'/(label+'.log')
for attempt in range(120):
    text = outer.read_text(errors='replace') if outer.exists() else ''
    match = re.search(r'^Complete-run evidence: (.+)$',text,re.M)
    if match:
        profile = Path(match[1])
        log = profile/'00.log'
        body = log.read_text(errors='replace') if log.exists() else ''
        roots = re.findall(r'(/tmp/RCMetaR-r-stack-[^/\s\x1b]+)',body)
        for name in dict.fromkeys(roots):
            check = Path(name)/'RCMetaR.Rcheck'
            status = check/'00check.log'
            tests = check/'tests/testthat.Rout'
            if not status.exists() or not tests.exists():
                continue
            status_text = status.read_text(errors='replace')
            tests_text = tests.read_text(errors='replace')
            counts = re.findall(r'\[ FAIL (\d+) \| WARN (\d+) \| SKIP (\d+) \| PASS (\d+) \]',tests_text)
            if 'Status: OK' not in status_text or not counts:
                continue
            fail,warn,skip,passed = map(int,counts[-1])
            assert fail == warn == 0 and passed == 1825 and skip == 1, counts[-1]
            assert '0.5.0' in status_text, status_text[:1000]
            records = {}
            for relative in ('tests/testthat.Rout','00check.log'):
                source = check/relative
                target = HERE/'raw'/(label+'-'+source.name)
                shutil.copyfile(source,target)
                records[relative] = dict(source=str(source),retained=str(target.relative_to(ROOT)),
                    sha256=hashlib.sha256(target.read_bytes()).hexdigest(),tail=target.read_text(errors='replace').splitlines()[-22:])
            result = dict(passed=True,profile=label,source_revision='06df415',source_sha256=source_digest(),
                retained_utc=datetime.now(UTC).isoformat(),assertions=passed,failures=fail,warnings=warn,skips=skip,
                package_version='0.5.0',skip_reason='Opt-in visual gallery; unchanged scope documented in QUALIFICATION.',records=records)
            (HERE/'R-CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps(result),flush=True)
            sys.exit(0)
    time.sleep(10)
raise RuntimeError('No completed passing R check found in the owned full-profile temp tree within 20 minutes')
