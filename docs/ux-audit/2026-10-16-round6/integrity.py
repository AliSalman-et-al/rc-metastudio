"""Check final executable provenance and every retained evidence binding."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from scripts.verification_evidence import source_digest


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


full = read('FULL-PROFILE.json')
assert full['passed'] and full['command']['label'] == 'reviewer-full-final'
profile_directory = Path(full['summary']['commands'][1]['command'][-1]).parent
assert json.loads((profile_directory / 'summary.json').read_text()) == full['summary']
for name, expected in full['summary']['files_sha256'].items():
    assert sha(profile_directory / name) == expected, name
check = read('R-CHECK.json')
assert check['passed'] and check['profile'] == full['command']['label']
assert check['source_sha256'] == source_digest()
assert check['assertions'] == 1825 and check['failures'] == check['warnings'] == 0
for row in check['records'].values():
    assert sha(ROOT / row['retained']) == row['sha256'], row
numeric = read('NUMERICAL-EQUIVALENCE.json')
assert numeric['passed'] and numeric['original_field_count'] == 415
assert numeric['max_absolute_difference'] == 0
geometry = read('AXIS-TITLE-GEOMETRY.json')
assert geometry['passed'] and geometry['svg_artifacts'] == 24 and geometry['minimum_gap_points'] >= 4
for row in geometry['rows']:
    assert sha(ROOT / row['source']) == row['sha256'], row
axis = read('AXIS-NUMERICAL-EQUIVALENCE.json')
assert axis['passed'] and axis['cases'] == 24 and axis['max_absolute_difference'] == 0
install = read('INSTALLED-SOURCE.json')
assert install['exit_code'] == 0
for name, expected in install['source_sha256'].items():
    assert sha(ROOT / 'r/RCMetaR' / name) == expected, name
for name, expected in install['installed_sha256'].items():
    assert sha(Path(install['library']) / 'RCMetaR' / name) == expected, name
unchanged = ['sample_projects', 'tests/fixtures', 'tests/python/fixtures']
assert not subprocess.check_output(['git', 'diff', '--name-only', '80e4bee', '--', *unchanged], text=True).strip()
frames = {}
for pair in read('SCREENSHOTS.json'):
    for role in ('before', 'after'):
        row = pair[role]
        assert sha(HERE / row['path']) == sha(ROOT / row['source']) == row['sha256'], row
        frames[row['path']] = row['sha256']
actual = {str(path.relative_to(HERE)) for path in (HERE / 'screenshots').rglob('*.png')}
assert actual == frames.keys(), (actual - frames.keys(), frames.keys() - actual)
reviewer_frames = {}
for entry in read('REVIEWER-SCREENSHOTS.json'):
    for role in ('before','after'):
        if role not in entry:
            continue
        shot = entry[role]
        assert sha(HERE/shot['path']) == sha(ROOT/shot['source']) == shot['sha256'], shot
        reviewer_frames[shot['path']] = shot['sha256']
assert {str(path.relative_to(HERE)) for path in (HERE/'reviewer-screenshots').glob('*.png')} == reviewer_frames.keys()
for name, row in read('REVIEWER-BEFORE.json').items():
    original = subprocess.check_output(['git','show',row['revision']+':'+str((HERE/name).relative_to(ROOT))])
    assert hashlib.sha256(original).hexdigest() == row['sha256'], name
pft = read('REVIEWER-PFT-AUTHORITIES.json')
assert pft['passed'] and pft['r'] == '4.6.1' and len(pft['rows']) == 6
assert all(row['max_inverse_difference'] < 1e-12 for row in pft['rows'])
assert next(row['version'] for row in pft['packages'] if row['package'] == 'RCMetaR') == '0.5.0'
assert check['package_version'] == '0.5.0'
release = read('RELEASE-PROJECT.json')
assert ROOT / release['profile'] == profile_directory
assert sha(ROOT / release['path']) == release['sha256']
with ZipFile(ROOT / release['path']) as archive:
    project_manifest = json.loads(archive.read('manifest.json'))
assert project_manifest == release['manifest']
assert project_manifest['application']['version'] == '0.5.0'
group_run = next(row for row in full['runs'] if row['scenario'] == 'project-reviewer-groups')
group_steps = [json.loads(line) for line in (ROOT / group_run['evidence'] / 'steps.jsonl').read_text().splitlines()]
saved_project = next(step for step in group_steps if step['action'] == 'reviewer-version-reopened')
assert Path(saved_project['project']) == ROOT / release['source']
assert saved_project['manifest'] == project_manifest
footers = read('REVIEWER-VECTOR-FOOTERS.json')
assert len(footers) == 28
for row in footers:
    assert sha(ROOT / row['source']) == row['source_sha256'], row
    assert sha(ROOT / row['image']) == row['sha256'], row
assert not subprocess.check_output(['git','diff','--name-only','dc235ab','--','tests/analysis_regression/baseline'],text=True).strip()
checked = 0
for row in full['runs']:
    directory = ROOT / row['evidence']
    manifest_path = directory / 'manifest.json'
    assert sha(manifest_path) == row['manifest_sha256'], manifest_path
    manifest = json.loads(manifest_path.read_text())
    context = manifest.get('verification_context')
    if context:
        assert context['source_sha256'] == source_digest(), directory
    else:
        assert manifest['scenario'] == 'doctor', directory
        assert manifest['driver_sha256'] == sha(ROOT / 'tests/e2e/desktop_driver.py')
    for artifact in manifest['files']:
        assert sha(directory / artifact['path']) == artifact['sha256'], artifact
        checked += 1
helpers = {**read('HELPER-EVIDENCE.json'), **read('REVIEWER-HELPER-EVIDENCE.json')}
for row in read('NATIVE-SELECTED.json'):
    path = ROOT / row['evidence'] / 'manifest.json'
    assert sha(path) == row['manifest_sha256'], path
    manifest = json.loads(path.read_text())
    assert manifest['passed'] and manifest['native_requested'], path
for name, row in helpers.items():
    path = ROOT / name / 'manifest.json'
    assert sha(path) == row['manifest_sha256'], path
    manifest = json.loads(path.read_text())
    for artifact in manifest['files']:
        assert sha(path.parent / artifact['path']) == artifact['sha256'], artifact
for row in read('TEST-RUNS.json') + read('REVIEWER-TEST-RUNS.json'):
    assert sha(HERE / 'raw' / row['log']) == row['sha256'], row['label']
files = ['FULL-PROFILE.json', 'NUMERICAL-EQUIVALENCE.json', 'AXIS-NUMERICAL-EQUIVALENCE.json',
         'INSTALLED-SOURCE.json', 'R-CHECK.json', 'AXIS-TITLE-GEOMETRY.json', 'NATIVE-SELECTED.json', 'SCREENSHOTS.json', 'HELPER-EVIDENCE.json', 'TEST-RUNS.json',
         'FAILURES.md', 'INTERRUPTIONS.json', 'contact-sheet.html', 'integrity.py',
         'REVIEWER-BEFORE.json','REVIEWER-PFT-AUTHORITIES.json','REVIEWER-SCREENSHOTS.json',
         'REVIEWER-TEST-RUNS.json','REVIEWER-HELPER-EVIDENCE.json','REVIEWER-FAILURES.md',
         'REVIEWER-VISUAL-REJECTIONS.json','REVIEWER-VISUAL.md','REVIEWER-VECTOR-FOOTERS.json',
         'reviewer-contact-sheet.html','reviewer-gallery.html','RELEASE-PROJECT.json',
         'REVIEWER-REPRODUCE.sh','reviewer_authorities.R','reviewer_collect.py',
         'reviewer_curate.py','reviewer_retain_check.py','reviewer_retain_project.py',
         'reviewer_render_footers.py','select_native.py']
result = dict(passed=True, source_sha256=source_digest(), executable_revision='06df415',
              profile_summary_sha256=sha(profile_directory / 'summary.json'),
              checked_profile_logs_and_authorities=len(full['summary']['files_sha256']),
              desktop_verification_context_sha256=full['verification_context_sha256'],
              desktop_scenarios=full['desktop_scenarios'], doctor=full['doctor'],
              checked_full_profile_artifacts=checked, curated_frames=len(frames), reviewer_curated_frames=len(reviewer_frames), release_version='0.5.0',
              reviewer_contact_entries=len(read('REVIEWER-SCREENSHOTS.json')),
              inspected_vector_footer_crops=len(footers),
              saved_project_application_version=project_manifest['application']['version'],
              saved_project_sha256=release['sha256'],
              contact_pairs=len(read('SCREENSHOTS.json')), selected_passing_native=len(read('NATIVE-SELECTED.json')),
              original_numerical_fields_exact=415,
              axis_numeric_fits_exact=24, max_absolute_difference=0,
              installed_source_matches=True, installed_package_matches=True,
              original_fixtures_unchanged_since='80e4bee', unchanged_paths=unchanged,
              native_receipts=sum(row['native'] is True for row in helpers.values()),
              file_sha256={name: sha(HERE / name) for name in files},
              scope='Linux native Qt and controlled desktop fixtures; final full profile binds final executable bytes. Individual native receipts retain their actual source/install provenance. No screen-reader, Windows/macOS package or native OS picker qualification.')
(HERE / 'EVIDENCE-INTEGRITY.json').write_text(json.dumps(result, indent=2) + '\n')
print(f'Integrity passed: {checked} full-profile artifacts, {len(frames)} historical + {len(reviewer_frames)} reviewer native frames, {len(footers)} SVG footer crops, saved project 0.5.0, 415 exact original fields and 24 exact axis fits.')
