"""Apply only an already-proved text projection, with independent structural guards."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASELINE = ROOT / 'tests/analysis_regression/baseline'
proof = json.loads((HERE / 'output.json').read_text())
assert proof['passed'] and not proof['mismatches']
for name, digest in proof['reference_hashes'].items():
    assert hashlib.sha256((BASELINE / name).read_bytes()).hexdigest() == digest, name
old_dir = HERE / 'old'
old_dir.mkdir(exist_ok=True)
for path in BASELINE.iterdir():
    if path.is_file():
        if (old_dir / path.name).exists():
            assert path.read_bytes() == (old_dir / path.name).read_bytes(), path.name
        else:
            shutil.copy2(path, old_dir / path.name)

changed = {(entry['case'], entry['field'].removeprefix('texts.')): entry for entry in proof['changed_fields']}
archive_path = BASELINE / 'observed-golden-baseline.zip'
with zipfile.ZipFile(archive_path) as archive:
    infos = archive.infolist()
    original = {info.filename: archive.read(info) for info in infos}
manifest = json.loads(original['manifest.json'])
expected = copy.deepcopy(manifest)
for row in expected['curated_golden_set']:
    for (case, field), entry in changed.items():
        if row['id'] == case:
            assert row['texts'].get(field, '') == entry['before']
            row['texts'][field] = entry['after']

def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()

replacement = dict(original)
replacement['manifest.json'] = encoded(expected)
for row in expected['curated_golden_set']:
    name = 'captures/' + row['id'] + '.json'
    before = json.loads(original[name])
    after = copy.deepcopy(before)
    after['texts'] = row['texts']
    assert {k:v for k,v in before.items() if k != 'texts'} == {k:v for k,v in after.items() if k != 'texts'}
    if before != after:
        replacement[name] = encoded(after)

candidate = HERE / 'presentation-only.zip'
with zipfile.ZipFile(candidate, 'w') as archive:
    for info in infos:
        archive.writestr(info, replacement[info.filename])

with zipfile.ZipFile(candidate) as archive:
    assert archive.namelist() == list(original)
    for name, data in original.items():
        observed = archive.read(name)
        if name.startswith('artifacts/'):
            assert observed == data, name
        elif name.endswith('.json'):
            before, after = json.loads(data), json.loads(observed)
            if name == 'manifest.json':
                for row in after['curated_golden_set']:
                    row['texts'] = next(r for r in before['curated_golden_set'] if r['id'] == row['id'])['texts']
            else:
                after['texts'] = before['texts']
            assert before == after, name
        else:
            assert observed == data, name

digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
shutil.copyfile(candidate, archive_path)
report = {'passed': True, 'changed_text_fields': len(changed),
          'numeric_tokens_proved': sum(len(e['numbers']) for e in proof['changed_fields']),
          'png_members_byte_identical': sum(n.startswith('artifacts/') for n in original),
          'all_nontext_archive_fields_identical': True, 'binding_only_changes': []}
outer = json.loads((BASELINE / 'manifest.json').read_text())
for name, key in [('numeric-contract.json','golden_numeric_contract'), ('plot-descriptors.json','golden_plot_descriptor_contract')]:
    path = BASELINE / name
    old = json.loads(path.read_text())
    new = copy.deepcopy(old)
    new['oracle_sha256'] = digest
    assert {k:v for k,v in old.items() if k != 'oracle_sha256'} == {k:v for k,v in new.items() if k != 'oracle_sha256'}
    path.write_bytes(encoded(new))
    outer[key]['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    outer[key]['size'] = path.stat().st_size
    report['binding_only_changes'].append(name + ': /oracle_sha256')
outer['observed_golden_analysis_bundle']['sha256'] = digest
outer['observed_golden_analysis_bundle']['size'] = archive_path.stat().st_size
(BASELINE / 'manifest.json').write_bytes(encoded(outer))
report['numeric_cases_and_tolerances_identical'] = True
report['plot_descriptor_rows_identical'] = True
(HERE / 'structural-proof.json').write_bytes(encoded(report))
print(json.dumps(report, indent=2))
