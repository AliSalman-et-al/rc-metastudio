"""Guarded label-only projection using the #556 archive/rebinding mechanism."""
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASE = ROOT / 'tests/analysis_regression/baseline'
CAPTURE = ROOT / 'build/qa567-windows-capture'
CASE = 'lymph-diagnostic-random-dor'
OLD, NEW = 'Odds Ratio Summary', 'Diagnostic Odds Ratio Summary'
OLD_PLOT, NEW_PLOT = 'Odds Ratio Forest Plot', 'Diagnostic Odds Ratio Forest Plot'

def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()

def digest(data):
    return hashlib.sha256(data).hexdigest()

original = {p.name: p.read_bytes() for p in BASE.iterdir() if p.is_file()}
old_dir = HERE / 'old'
old_dir.mkdir(exist_ok=True)
for name, data in original.items():
    target = old_dir / name
    if target.exists():
        assert target.read_bytes() == data, 'Already applied or baseline changed: ' + name
    else:
        target.write_bytes(data)

current = json.loads((CAPTURE / 'captures' / (CASE + '.json')).read_text())
report = json.loads((CAPTURE / 'compatibility-report.json').read_text())
nonpasses = [r for r in report['comparison']['rows'] if r['classification'] not in ('pass', 'accepted_exception')]
assert {r['id'] for r in nonpasses} == {CASE}
contract = json.loads(original['numeric-contract.json'])
case = next(r for r in contract['cases'] if r['id'] == CASE)
old_values = case['sections'][OLD]
new_values = current['outputs'][NEW]
assert set(old_values) == set(new_values)
policy = contract['tolerance_policy']
pairs = []
for field, before in old_values.items():
    after = new_values[field]
    tolerance = max(policy['absolute'], policy['relative'] * abs(before))
    assert abs(after-before) <= tolerance, field
    assert after == before, field
    pairs.append(dict(field=field, before=before, after=after, tolerance=tolerance, delta=after-before))

with zipfile.ZipFile(BASE / 'observed-golden-baseline.zip') as archive:
    infos = archive.infolist()
    members = {i.filename: archive.read(i) for i in infos}
manifest = json.loads(members['manifest.json'])
frozen = next(r for r in manifest['curated_golden_set'] if r['id'] == CASE)
old_text = frozen['texts'][OLD]
new_text = current['texts'][NEW]
assert old_text.replace('\nOdds Ratio -', '\nDiagnostic Odds Ratio -') == new_text
numbers = lambda text: re.findall(r'(?<!\w)[+-]?(?:\d+\.?\d*|\.\d+)(?:[Ee][+-]?\d+)?', text)
assert numbers(old_text) == numbers(new_text)
assert all(value == current['texts'][key] for key, value in frozen['texts'].items() if key != OLD)
assert frozen['artifacts'][0]['sha256'] == current['artifacts'][0]['sha256']
assert digest((CAPTURE/'artifacts'/CASE/'golden_lymph_forest_dor.png').read_bytes()) == frozen['artifacts'][0]['sha256']
proof = dict(passed=True, source_run=41960942547, source_job=127027031169,
             source_capture_commit=current['commit_sha'], baseline_sha256={k:digest(v) for k,v in original.items()},
             case=CASE, old_section=OLD, new_section=NEW, field_sets_identical=True,
             tolerance_policy=policy, numeric_pairs=pairs, numeric_tokens_identical=numbers(old_text),
             old_text=old_text, new_text=new_text, windows_png_byte_identical=True,
             raw_windows_descriptor=current['plot_descriptors'],
             descriptor_note='Raw CI descriptor is null because title lookup missed the renamed forest. Do not freeze nulls. Preserve all required capability/content fields; rename identity only. A repaired production capture separately validates the lookup.')
(HERE/'proof.json').write_bytes(encoded(proof))

# Exactly the approved section-key/text and display-identity projection.
frozen['texts'][NEW] = frozen['texts'].pop(OLD)
frozen['texts'][NEW] = new_text
assert frozen['outputs'] == {}
for descriptor in frozen['plot_descriptors']:
    assert descriptor['display']['identity'] == OLD_PLOT
    descriptor['display']['identity'] = NEW_PLOT
member = 'captures/' + CASE + '.json'
replacement = dict(members)
replacement['manifest.json'] = encoded(manifest)
replacement[member] = encoded(frozen)
archive_path = BASE/'observed-golden-baseline.zip'
with zipfile.ZipFile(archive_path, 'w') as archive:
    for info in infos:
        archive.writestr(info, replacement[info.filename])
archive_sha = digest(archive_path.read_bytes())
case['sections'][NEW] = case['sections'].pop(OLD)
contract['coverage'][CASE][NEW] = contract['coverage'][CASE].pop(OLD)
contract['oracle_sha256'] = archive_sha
(BASE/'numeric-contract.json').write_bytes(encoded(contract))
plots = json.loads(original['plot-descriptors.json'])
plots['oracle_sha256'] = archive_sha
for row in plots['rows']:
    if row['id'] == CASE:
        assert row['display']['identity'] == OLD_PLOT
        row['display']['identity'] = NEW_PLOT
(BASE/'plot-descriptors.json').write_bytes(encoded(plots))
outer = json.loads(original['manifest.json'])
for name, key in [('observed-golden-baseline.zip','observed_golden_analysis_bundle'), ('numeric-contract.json','golden_numeric_contract'), ('plot-descriptors.json','golden_plot_descriptor_contract')]:
    data = (BASE/name).read_bytes()
    outer[key].update(sha256=digest(data), size=len(data))
(BASE/'manifest.json').write_bytes(encoded(outer))

# Independent reverse projection: all other cases/fields/members must be identical.
with zipfile.ZipFile(archive_path) as archive:
    assert archive.namelist() == list(members)
    changed = [n for n in members if archive.read(n) != members[n]]
    assert set(changed) == {'manifest.json', member}, changed
    observed = json.loads(archive.read(member))
    observed['texts'][OLD] = old_text
    del observed['texts'][NEW]
    observed['plot_descriptors'][0]['display']['identity'] = OLD_PLOT
    assert observed == json.loads(members[member])
    observed_manifest = json.loads(archive.read('manifest.json'))
    observed_manifest['curated_golden_set'] = [observed if r['id']==CASE else r for r in observed_manifest['curated_golden_set']]
    assert observed_manifest == json.loads(members['manifest.json'])
contract['oracle_sha256'] = json.loads(original['numeric-contract.json'])['oracle_sha256']
case['sections'][OLD] = case['sections'].pop(NEW)
contract['coverage'][CASE][OLD] = contract['coverage'][CASE].pop(NEW)
assert contract == json.loads(original['numeric-contract.json'])
plots['oracle_sha256'] = json.loads(original['plot-descriptors.json'])['oracle_sha256']
next(r for r in plots['rows'] if r['id']==CASE)['display']['identity'] = OLD_PLOT
assert plots == json.loads(original['plot-descriptors.json'])
(HERE/'update-audit.json').write_bytes(encoded(dict(passed=True, changed_archive_members=changed,
    all_other_cases_and_artifacts_byte_identical=True, numeric_fields_and_tolerances_identical=True,
    numeric_contract_changes=[f'{CASE}/sections and coverage/{OLD} -> {NEW}', 'oracle_sha256'],
    descriptor_changes=[f'{CASE}/display/identity: {OLD_PLOT} -> {NEW_PLOT}', 'oracle_sha256'],
    metadata_capabilities_and_content_requirements_unchanged=True,
    outer_manifest_changes='archive/contract SHA256 and size bindings only')))
print('PASS: exact numerical field set, values and tolerances; label-only text/identity; unchanged other cases and all artifacts')
