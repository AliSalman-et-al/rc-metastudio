"""Real Qt/R cache proof, including damaged evidence and changed inputs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.verification_evidence import CACHE, file_digest, verification_context

OUT = Path(__file__).resolve().parent
RAW = OUT / 'raw'
SCENARIO = 'analysis-data-generic-effect'
rows = []
proof_id = str(time.time_ns())


def run(label, context, expected=0):
    env = os.environ | {'RCMS_E2E_CONTEXT': json.dumps(context), 'RCMS_E2E_REUSE_PASSED': '1'}
    command = [sys.executable, 'scripts/verify_rcms.py', SCENARIO]
    start = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    seconds = time.monotonic() - start
    log = RAW / ('dx-resume-' + proof_id + '-' + label + '.log')
    log.write_text(result.stdout)
    lines = [line.removeprefix('Evidence: ') for line in result.stdout.splitlines() if line.startswith('Evidence: ')]
    assert result.returncode == expected, result.stdout
    assert len(lines) == 1, result.stdout
    evidence = Path(lines[0])
    manifest = json.loads((evidence / 'manifest.json').read_text())
    assert manifest['passed'] == (expected == 0), manifest
    row = {'label': label, 'command': command, 'seconds': seconds, 'exit_code': result.returncode,
           'reused': 'Reused passed evidence:' in result.stdout, 'evidence': str(evidence.relative_to(ROOT)),
           'context': context['sha256'], 'log': str(log.relative_to(ROOT)), 'log_sha256': file_digest(log)}
    rows.append(row)
    print(row, flush=True)
    return evidence, row


base = verification_context()
for index in range(5):
    evidence, row = run('unchanged-' + str(index), base)
    assert row['reused'], row

for mode in ('corrupt', 'missing'):
    png = next(evidence.glob('*.png'))
    original = png.read_bytes()
    try:
        if mode == 'corrupt': png.write_bytes(original + b'altered evidence')
        else: png.unlink()
        next_evidence, row = run(mode, base)
        assert not row['reused'] and next_evidence != evidence, row
    finally:
        png.write_bytes(original)
    evidence = next_evidence

source = ROOT / 'scripts/verification_resources.py'
original_source = source.read_bytes()
try:
    source.write_bytes(original_source + b'\n# Cache invalidation proof only; restored by this script.\n')
    changed = verification_context()
    assert changed['sha256'] != base['sha256']
    _, row = run('changed-source', changed)
    assert not row['reused'], row
finally:
    source.write_bytes(original_source)

profile = RAW / 'cache-proof.Rprofile'
profile.write_text('# Test-owned empty startup profile.\n')
old_profile = os.environ.get('R_PROFILE_USER')
try:
    os.environ['R_PROFILE_USER'] = str(profile)
    changed = verification_context()
    assert changed['sha256'] != base['sha256']
    _, row = run('changed-runtime-profile', changed)
    assert not row['reused'], row
finally:
    if old_profile is None: os.environ.pop('R_PROFILE_USER', None)
    else: os.environ['R_PROFILE_USER'] = old_profile

old_build = os.environ['RCMS_QT6_BUILD_ROOT']
try:
    os.environ['RCMS_QT6_BUILD_ROOT'] = str(RAW / 'intentionally-missing-generated-forms')
    changed = verification_context()
    assert changed['sha256'] != base['sha256']
    _, row = run('failed-startup', changed, expected=1)
    assert not row['reused'], row
    assert not (CACHE / str(changed['sha256']) / (SCENARIO + '.json')).exists()
finally:
    os.environ['RCMS_QT6_BUILD_ROOT'] = old_build

assert verification_context() == base
_, row = run('restored-inputs', base)
assert row['reused'], row
(OUT / 'DX-RESUME.json').write_text(json.dumps({'passed': True, 'context': base, 'observations': rows}, indent=2) + '\n')
