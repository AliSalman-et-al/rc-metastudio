"""Retain the latest passing round-six native proof for each affected workflow."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
modes = ('binary-metrics', 'continuous-metrics', 'diagnostic-metrics',
         'onearm-proportion', 'onearm-mean', 'entered-binary', 'entered-continuous',
         'entered-diagnostic', 'pre-post', 'back-binary', 'back-continuous', 'back-diagnostic')
scenarios = ['calculator-mode-' + mode for mode in modes]
scenarios += ['calculator-grid-precision', 'calculator-ratio-precision', 'project-display-labels',
              'project-round6-polish', 'project-axis-proportions', 'project-axis-others',
              'project-axis-sequential', 'audit-round3-round5', 'audit-round3-presentation-transforms',
              'audit-round3-presentation-diagnostic',
              'plot-workflow-regression', 'plot-workflow-funnel', 'plot-workflow-contour',
              'plot-workflow-trimfill', 'project-shell', 'review-workflows', 'ratios-hr', 'ratios-irr']
rows = []


def select(scenario):
    for path in sorted((ROOT / 'artifacts/verification/rcms').glob('*-' + scenario + '/manifest.json'), reverse=True):
        if path.parent.name[:16] < '20261015T105828Z':
            continue
        manifest = json.loads(path.read_text())
        if not manifest.get('native_requested') or not manifest.get('passed'):
            continue
        runtime = json.loads(path.with_name('runtime.json').read_text())
        for artifact in manifest['files']:
            actual = hashlib.sha256((path.parent / artifact['path']).read_bytes()).hexdigest()
            assert actual == artifact['sha256'], artifact
        steps = [json.loads(line) for line in path.with_name('steps.jsonl').read_text().splitlines()]
        return dict(scenario=scenario, evidence=str(path.parent.relative_to(ROOT)),
                    manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    source_revision=manifest['head'], checked_artifacts=len(manifest['files']),
                    actions=list(dict.fromkeys(step['action'] for step in steps)), runtime=runtime)
    raise AssertionError(('No passing round-six native proof', scenario))


for scenario in scenarios:
    rows.append(select(scenario))
# These two independently owned receipts share a wrapper; preserve their exact identities.
for name, scale in [('20261015T115917Z-4030619d-review1-design', '1.5'),
                    ('20261015T120012Z-87b47122-review1-design', '2')]:
    path = ROOT / 'artifacts/verification/rcms' / name / 'manifest.json'
    manifest = json.loads(path.read_text())
    assert manifest['passed'] and manifest['native_requested'], name
    for artifact in manifest['files']:
        assert hashlib.sha256((path.parent / artifact['path']).read_bytes()).hexdigest() == artifact['sha256']
    rows.append(dict(scenario='review1-design', scale=scale, evidence=str(path.parent.relative_to(ROOT)),
                     manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                     checked_artifacts=len(manifest['files']),
                     invocation='raw/native-headers-and-accessibility.json'))
(HERE / 'NATIVE-SELECTED.json').write_text(json.dumps(rows, indent=2) + '\n')
print(f'{len(rows)} selected passing native workflows; every retained artifact hash checked.')
