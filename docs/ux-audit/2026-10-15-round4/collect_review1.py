"""Append native review receipts without replacing earlier round-four evidence."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
index = HERE / 'REVIEW1-NATIVE.json'
records = json.loads(index.read_text()) if index.exists() else {}
for label in sys.argv[1:]:
    attempt = json.loads((HERE / 'raw' / (label + '.json')).read_text())
    assert attempt['exit_code'] == 0, attempt
    log = HERE / 'raw' / attempt['log']
    assert hashlib.sha256(log.read_bytes()).hexdigest() == attempt['sha256']
    folder = Path(re.search(r'^Evidence: (.+)', log.read_text(), re.M)[1])
    manifest = json.loads((folder / 'manifest.json').read_text())
    assert manifest['passed'] and manifest['native_requested'], manifest
    runtime = json.loads((folder / 'runtime.json').read_text())
    assert runtime['platform_plugin'] == 'xcb', runtime
    for file in manifest['files']:
        assert hashlib.sha256((folder / file['path']).read_bytes()).hexdigest() == file['sha256'], file
    steps = [json.loads(line) for line in (folder / 'steps.jsonl').read_text().splitlines()]
    selections = [s for s in steps if s['action'].startswith(('review1-', 'clinical-report', 'matrix-results', 'round4-annotations', 'calculator-mode-layout', 'round3-report-copy-export', 'ux-', 'analysis-results', 'review-study-order-options', 'calculator-effect-preview', 'calculator-ci-preview', 'family-plot-cancelled', 'family-editor-controls', 'family-plot-reopened'))]
    frames = []
    for step in selections:
        for name in step['captures']:
            target = HERE / 'screenshots' / (label + '-' + name)
            shutil.copyfile(folder / name, target)
            frames.append(dict(path=str(target.relative_to(HERE)), sha256=hashlib.sha256(target.read_bytes()).hexdigest(), step=step['step'], capture='QScreen.grabWindow'))
    records[label] = dict(attempt=attempt, evidence=str(folder.relative_to(ROOT)), runtime=runtime,
                          manifest_sha256=hashlib.sha256((folder / 'manifest.json').read_bytes()).hexdigest(),
                          observed=steps, frames=frames)
index.write_text(json.dumps(records, indent=2, ensure_ascii=False) + '\n')
print(f'{len(records)} retained native review receipts')
