"""Keep final native copies and the two development frames used for comparison."""
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
index = HERE/'REVIEW1-NATIVE.json'
records = json.loads(index.read_text())
superseded = {
    'review1-design-reading', 'review1-diagnostic-axis',
    'review1-native-figures-diagnostic', 'review1-native-transforms-qualified',
    'review1-native-design-final', 'review1-native-figures-binary',
    'review1-native-diagnostic-complete', 'review1-native-subgroup-complete',
    'review1-verified-onearm-proportion', 'review1-verified-reg-coef',
    'review1-verified-twoarm-proportion', 'review1-publication-review1-design',
    'review1-bounded-transforms', 'review1-verified-generic-effect',
}
comparisons = {
    'review1-bounded-transforms-16-0-round4-annotations.png',
    'review1-verified-generic-effect-14-0-round4-annotations.png',
}
tracked = set(subprocess.check_output(['git','ls-files','--','docs/ux-audit/2026-10-15-round4/screenshots'],cwd=ROOT,text=True).splitlines())
removed = 0
for label in superseded:
    run = records.get(label)
    if run is None:
        continue
    kept = []
    for frame in run['frames']:
        path = HERE/frame['path']
        if path.name in comparisons or str(path.relative_to(ROOT)) in tracked:
            kept.append(frame)
            continue
        assert path.parent == HERE/'screenshots' and path.name.startswith(label+'-')
        if path.exists():
            path.unlink()
            removed += 1
    run['frames'] = kept
    run['curation'] = 'Superseded audit copies omitted. Every original capture remains hash-bound in the sealed manifest under evidence; the observed action/capture names are retained here. Selected comparison frames remain unmodified.'
index.write_text(json.dumps(records,indent=2,ensure_ascii=False)+'\n')
print(f'Omitted {removed} duplicate development copies; original native artifacts and receipts retained.')
