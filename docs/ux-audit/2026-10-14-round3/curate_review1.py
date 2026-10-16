"""Retain review repairs separately from the original round-three evidence."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
labels = json.loads(sys.argv[1])
observations, screenshots = [], []
output = HERE / 'screenshots/review1'
output.mkdir(exist_ok=True)
for family, label in labels.items():
    attempt = json.loads((HERE / 'raw' / (label + '.json')).read_text())
    assert attempt['exit_code'] == 0, attempt
    log = (HERE / 'raw' / attempt['log']).read_text()
    assert hashlib.sha256(log.encode()).hexdigest() == attempt['sha256']
    evidence = Path(re.search(r'Evidence: (.+)', log)[1])
    manifest = json.loads((evidence / 'manifest.json').read_text())
    assert manifest['passed'], manifest
    steps = [json.loads(line) for line in (evidence / 'steps.jsonl').read_text().splitlines()]
    observed = [s for s in steps if s['action'].startswith('round3-')]
    observations.append(dict(family=family, attempt=attempt, evidence=str(evidence.relative_to(ROOT)),
                             manifest=manifest, runtime=json.loads((evidence / 'runtime.json').read_text()),
                             observations=observed))
    selected = []
    if family == 'precision':
        selected = [s for s in observed if s['action'] in {
            'round3-bubble-tick-coverage', 'round3-degenerate-axis', 'round3-degenerate-axis-bottom', 'round3-small-effects-preserved'}]
    elif family in {'hr', 'irr'}:
        reports = [s for s in observed if s['action'] == 'round3-report-copy-export']
        selected += [next(s for s in reports if s['identity'].startswith('Leave-one-out'))]
        selected += [next(s for s in reports if s['identity'].startswith('Meta-analysis') and 'Estimator:' not in s['text'])]
    elif family == 'diagnostic':
        selected = [next(s for s in observed if s['action'] == 'round3-report-copy-export')]
    for step in selected:
        for name in step['captures']:
            source = evidence / name
            target = output / (family + '-' + name)
            shutil.copy2(source, target)
            screenshots.append(dict(path=str(target.relative_to(HERE)), source=str(source.relative_to(ROOT)),
                                    sha256=hashlib.sha256(target.read_bytes()).hexdigest(), family=family,
                                    action=step['action'], step=step['step']))
    for step in observed:
        if step['action'] == 'round3-report-copy-export':
            (output / f"{family}-{step['step']:02d}-report.txt").write_text(step['text'])
(HERE / 'REVIEW1-OBSERVATIONS.json').write_text(json.dumps(observations, indent=2, ensure_ascii=False) + '\n')
(HERE / 'REVIEW1-SCREENSHOTS.json').write_text(json.dumps(screenshots, indent=2) + '\n')
print(f'Retained {len(observations)} review runs and {len(screenshots)} screenshots without replacing prior evidence.')
