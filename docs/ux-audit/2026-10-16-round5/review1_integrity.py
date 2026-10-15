"""Bind the final profile, original numerical oracle, install and native frames."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.verification_evidence import source_digest
HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(name):
    return json.loads((HERE / name).read_text())

full = read('FULL-PROFILE.json')
assert full['passed'] and full['command']['label'] == 'review1-full-fresh'
numeric = read('NUMERICAL-EQUIVALENCE.json')
assert numeric['passed'] and numeric['original_field_count'] == 415 and numeric['max_absolute_difference'] == 0
install = read('INSTALLED-SOURCE.json')
for name, expected in install['source_sha256'].items():
    assert sha(ROOT / 'r/RCMetaR' / name) == expected, name
for name, expected in install['installed_sha256'].items():
    assert sha(Path(install['library']) / 'RCMetaR' / name) == expected, name
unchanged = ['tests/fixtures', 'tests/python/fixtures', 'tests/analysis_regression/baseline']
assert not subprocess.check_output(['git', 'diff', '--name-only', '008614c', '--', *unchanged], text=True).strip()
frames = {row['path']: row['sha256'] for row in read('SCREENSHOTS.json')}
for row in read('REVIEW1-CURATION.json'):
    path = ROOT / row['destination']
    assert sha(ROOT / row['source']) == sha(path) == row['sha256'], path
    frames[str(path.relative_to(HERE))] = row['sha256']
for name, expected in frames.items():
    assert sha(HERE / name) == expected, name
actual_frames = {str(path.relative_to(HERE)) for path in (HERE / 'screenshots').rglob('*.png')}
assert actual_frames == frames.keys(), (actual_frames - frames.keys(), frames.keys() - actual_frames)
for pair in read('CONTACT-PAIRS.json'):
    assert pair['before'] in frames and pair['after'] in frames, pair
labels = ['review1-native-shell-final', 'review1-native-arms', 'review1-header-final', 'review1-irr-qualified']
labels.extend(row['label'] for row in read('REVIEW1-EDITOR-INITIALS.json'))
assert len(labels) == len(set(labels)) == 15
native = {row['label']: row for row in read('REVIEW1-NATIVE.json')}
selected = []
for label in labels:
    row = native[label]
    assert row['manifest']['passed'] and row['manifest']['exit_code'] == 0, label
    selected.append(dict(label=label, evidence=row['evidence'], manifest_sha256=row['manifest_sha256']))
(HERE / 'REVIEW1-QUALIFIED-NATIVE.json').write_text(json.dumps(selected, indent=2) + '\n')
for row in full['runs']:
    manifest = json.loads((ROOT / row['evidence'] / 'manifest.json').read_text())
    context = manifest.get('verification_context')
    if context:
        assert context['source_sha256'] == source_digest(), row['evidence']
    else:
        assert manifest['scenario'] == 'doctor', row['evidence']
        assert manifest['driver_sha256'] == sha(ROOT / 'tests/e2e/desktop_driver.py')
result = dict(passed=True, source_sha256=source_digest(), frozen_source_revision='63b8d0c',
    r_implementation_revision='d05df93', desktop_verification_context_sha256=full['verification_context_sha256'],
    full_profile_desktop_scenarios=full['desktop_scenarios'], full_profile_doctor=full['doctor'],
    verified_full_profile_artifacts=sum(len(row['files']) for row in full['runs']),
    selected_passing_native_runs=len(selected), review1_receipts=len(native),
    curated_bound_frames=len(frames), new_review_frames=len(read('REVIEW1-CURATION.json')),
    contact_pairs=len(read('CONTACT-PAIRS.json')), installed_source_matches=True, installed_package_matches=True,
    unchanged_since_review_baseline='008614c', unchanged_paths_checked=unchanged,
    original_numerical_fields_exact=415, max_absolute_difference=0,
    file_sha256={name: sha(HERE / name) for name in ['FULL-PROFILE.json', 'NUMERICAL-EQUIVALENCE.json',
        'INSTALLED-SOURCE.json', 'REVIEW1-NATIVE.json', 'REVIEW1-CURATION.json', 'REVIEW1-TEST-RUNS.json',
        'REVIEW1-QUALIFIED-NATIVE.json', 'contact-sheet.html', 'review1-contact-sheet.html']},
    native_scope='Individual receipts bind their actual source and runtime. Final subgroup-layout replacements are selected; earlier unrelated producer paths retain their passing real-native proof. The full fresh profile qualifies all final executable bytes.',
    visual_scope='Linux Qt native driving and decoded exports; no Windows/macOS packaging or screen-reader qualification.')
(HERE / 'EVIDENCE-INTEGRITY.json').write_text(json.dumps(result, indent=2) + '\n')
print(f'Integrity passed: {len(frames)} bound frames, {len(selected)} selected native runs, {full["desktop_scenarios"]} fresh desktop scenarios, 415 exact fields.')
