"""Bind the final CI-repair qualification to retained commands and artifacts."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = HERE / 'raw/lexer'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def binding(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': digest(path)}


full_path = RAW / 'FULL-PROFILE.json'
full = json.loads(full_path.read_text())
assert full['passed'] and full['desktop_scenarios'] == 123 and full['doctor'] == 1
artifact_count = 0
children = []
for run in full['runs']:
    folder = ROOT / run['evidence']
    manifest = folder / 'manifest.json'
    assert digest(manifest) == run['manifest_sha256'], manifest
    for item in run['files']:
        assert digest(folder / item['path']) == item['sha256'], item
        artifact_count += 1
    children.append({'scenario': run['scenario'], 'manifest': binding(manifest),
                     'artifact_count': len(run['files'])})
receipts = []
for path in sorted((RAW / 'raw').glob('*.json')):
    receipt = json.loads(path.read_text())
    if 'command' not in receipt or 'exit_code' not in receipt:
        continue
    log = path.parent / receipt['log']
    assert digest(log) == receipt['sha256'], log
    receipts.append({**binding(path), 'record': receipt})
curated = json.loads((HERE / 'CI-VISUAL-CURATED.json').read_text())
for item in curated:
    assert digest(HERE / item['path']) == item['sha256'], item
    assert digest(ROOT / item['original']) == item.get('original_sha256', item['sha256']), item
visual = json.loads((HERE / 'CI-VISUAL-COMPARISON.json').read_text())
for family in visual['families']:
    for item in family['comparisons']:
        for side in ('before', 'after'):
            assert digest(ROOT / item[side]) == item[side + '_sha256'], item
assert visual['counts']['plot_pairs'] == visual['counts']['pixel_identical_plot_pairs'] == 127
numeric = json.loads((RAW / 'NUMERICAL-EQUIVALENCE.json').read_text())
assert numeric['passed'] and numeric['original_field_count'] == 415
assert numeric['max_absolute_difference'] == 0 and numeric['exact_before_after']
probes = json.loads((HERE / 'CI-WINDOWS-PROBES.json').read_text())
for item in probes['generator'] + probes['svg_inputs'] + probes['surface_records']:
    assert digest(ROOT / item['path']) == item['sha256'], item
installed = json.loads((RAW / 'INSTALLED-SOURCE.json').read_text())
for name, sha in installed['source_sha256'].items():
    assert digest(ROOT / 'r/RCMetaR' / name) == sha, name
for name, sha in installed['installed_sha256'].items():
    assert digest(Path(installed['library']) / 'RCMetaR' / name) == sha, name
oracle_diff = subprocess.check_output(
    ['git', 'diff', '--name-only', 'c62df31', '--', 'tests/analysis_regression/baseline'],
    cwd=ROOT, text=True).strip()
assert not oracle_diff, oracle_diff
r_diff = subprocess.check_output(
    ['git', 'diff', '--name-only', '035ebd3', '--', 'r/RCMetaR'],
    cwd=ROOT, text=True).strip()
assert not r_diff, r_diff
observer_diff = subprocess.check_output(
    ['git', 'diff', '--name-only', '035ebd3', '--', 'src', 'scripts', 'tests', '.agents', '.github/workflows'],
    cwd=ROOT, text=True).splitlines()
record = {
    'status': 'Local qualification complete; actual final-head GitHub checks required before merge.',
    'full_profile': {**binding(full_path), 'command': full['command'],
                     'summary': full['summary'], 'desktop_scenarios': 123, 'doctor': 1,
                     'artifact_count': artifact_count, 'children': children},
    'receipts': receipts,
    'numerical': {**binding(RAW / 'NUMERICAL-EQUIVALENCE.json'), 'fields': 415, 'maximum_difference': 0},
    'visual': {**binding(HERE / 'CI-VISUAL-COMPARISON.json'), 'counts': visual['counts'],
               'curation': binding(HERE / 'CI-VISUAL-CURATED.json'), 'accepted_inspected_images': len(curated)},
    'package_report_identities': binding(HERE / 'CI-PACKAGE-IDENTITIES.json'),
    'windows_probes': binding(HERE / 'CI-WINDOWS-PROBES.json'),
    'windows_font_followup': binding(HERE / 'CI-FONTS.json'),
    'console_newline_followup': binding(HERE / 'CI-CONSOLE-NEWLINE.json'),
    'installed_source': binding(RAW / 'INSTALLED-SOURCE.json'),
    'golden_oracle_files_unchanged_from_c62df31': True,
    'r_source_unchanged_from_full_profile': True,
    'post_profile_qualification_files': observer_diff,
    'prior_attempts': [binding(RAW / name) for name in ('terminal-interruption.json', 'source-change-stop.json')],
    'scope': 'The full profile binds 035ebd3. Later qualification-observer/header-identity and desktop-evidence boundary/refit/parser repairs do not change fits, report production, rendering, UI defaults, R source or numerical oracles. CI additionally uploads full-R evidence. Their strict golden/numerical/source-hook/native checks and actual final-head GitHub qualification are separate.',
}
(HERE / 'CI-QUALIFICATION.json').write_text(json.dumps(record, indent=2) + '\n')
print(f'CI evidence integrity passed: {len(children)} child manifests, {artifact_count} artifacts, {len(receipts)} exact command receipts, 415 exact fields, 127 identical plots and {len(curated)} curated images.')
