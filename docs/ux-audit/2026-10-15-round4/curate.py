"""Copy selected, unmodified native frames and bind their observed state."""
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
LABELS = {
    **{f: 'native-publication-' + f for f in ('generic-effect', 'diagnostic', 'onearm-proportion', 'twoarm-proportion', 'twoarm-mean', 'twoarm-smd')},
    'reg-coef': 'native-audit-round3-presentation-reg-coef-ready',
    'sequential': 'native-sequential-final',
    'precision': 'native-precision-final',
    'hr': 'native-audit-round3-hr-final',
    'irr': 'native-audit-round3-irr-final',
    'pre-post': 'native-calculator-mode-pre-post-ready',
    'entered-binary': 'native-calculator-mode-entered-binary-ready',
    'entered-continuous': 'native-calculator-mode-entered-continuous-ready',
    'covariates': 'native-project-table-covariates-ready',
    'small-study': 'native-small-study-diagnostic-ready',
    'help': 'native-ux-improvements-verified',
    'settings': 'native-review-workflows-verified',
    'report-after': 'native-amino-ready',
    'report-before': 'before-design-amino',
}
records, frames = [], []
(HERE / 'screenshots').mkdir(exist_ok=True)
for family, label in LABELS.items():
    attempt = json.loads((HERE / 'raw' / (label + '.json')).read_text())
    assert attempt['exit_code'] == 0, attempt
    log = (HERE / 'raw' / attempt['log']).read_text()
    folder = Path(re.search(r'^Evidence: (.+)', log, re.M)[1])
    manifest = json.loads((folder / 'manifest.json').read_text())
    assert manifest['passed'] and manifest['native_requested'], (family, manifest)
    runtime = json.loads((folder / 'runtime.json').read_text())
    assert runtime['platform_plugin'] == 'xcb', runtime
    steps = [json.loads(line) for line in (folder / 'steps.jsonl').read_text().splitlines()]
    observed = [r for r in steps if r['action'].startswith(('round3-', 'round4-', 'calculator-mode-layout', 'ux-', 'review-', 'small-study-'))]
    records.append(dict(family=family, attempt=attempt, evidence=str(folder.relative_to(ROOT)),
                        manifest_sha256=hashlib.sha256((folder / 'manifest.json').read_bytes()).hexdigest(),
                        runtime=runtime, observations=observed))
    selections = []
    if family in ('generic-effect','reg-coef','diagnostic','onearm-proportion','twoarm-proportion','twoarm-mean','twoarm-smd'):
        selections += [r for r in steps if r['action']=='round4-annotations' and
                       (r['digits']==6 or r['digits']==3 and r['style']=='revman')]
        selections += [r for r in steps if r['action'] in ('round4-contextual-calculator','round4-contextual-csv')]
    elif family=='sequential':
        selections += [r for r in steps if r['action'] in ('round3-sequential-rows','round3-null-excluded-rendered')]
    elif family=='precision':
        selections += [r for r in steps if r['action'] in ('round3-bubble-tick-coverage','round3-small-effects-preserved','round3-degenerate-axis-bottom')]
    elif family in ('hr','irr'):
        selections += [r for r in steps if r['action']=='round4-subgroup-weights'][:1]
        selections += [r for r in steps if r['action']=='round3-report-copy-export'][-1:]
    elif family.startswith('report-'):
        selections += [r for r in steps if r['action']=='analysis-results']
    elif family in ('pre-post','entered-binary','entered-continuous'):
        selections += [r for r in steps if r['action']=='calculator-mode-layout']
    elif family=='help':
        selections += [r for r in steps if r['action'] in ('ux-empty-workspace','ux-quick-start','ux-covariate-error','ux-native-result-table')]
    elif family=='settings':
        selections += [r for r in steps if r['action']=='review-study-order-options']
    elif family=='small-study':
        selections += [r for r in steps if r['action']=='matrix-results']
    elif family=='covariates':
        selections += [r for r in steps if r['action'] in ('table-covariates-reopened',)]
    for row in selections:
        captures = row['captures']
        if family.startswith('report-') or family=='small-study':
            captures = [name for name in captures if '-report.png' in name or '-table.png' in name]
        else:
            captures = captures[:1]
        for name in captures:
            target = HERE / 'screenshots' / (family + '-' + name)
            shutil.copyfile(folder / name, target)
            frames.append(dict(path=str(target.relative_to(HERE)), sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                               family=family, action=row['action'], step=row['step'], label=label,
                               observed=row, capture='QScreen.grabWindow'))
# Historical before frames retain their original native re-audit receipt.
for name in ('matrix-diagnostic-standard-figure.png','helper-calculator-continuous-03-0-calculator-effect-preview.png','precision-06-round3-bubble-tick-coverage.png','weights-irr-subgroup-middle.png','matrix-twoarm-mean-cumulative-figure.png'):
    source = HERE.parent / '2026-10-14-round3-reaudit/screenshots' / name
    target = HERE / 'screenshots' / ('before-' + name)
    shutil.copyfile(source, target)
    frames.append(dict(path=str(target.relative_to(HERE)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                       family='before', action='historical native re-audit', capture='QScreen.grabWindow',
                       provenance='../2026-10-14-round3-reaudit/REPORT.md'))
(HERE / 'OBSERVATIONS.json').write_text(json.dumps(records,indent=2,ensure_ascii=False)+'\n')
(HERE / 'SCREENSHOTS.json').write_text(json.dumps(frames,indent=2,ensure_ascii=False)+'\n')
print(f'{len(records)} passed native runs; {len(frames)} unmodified curated frames')
