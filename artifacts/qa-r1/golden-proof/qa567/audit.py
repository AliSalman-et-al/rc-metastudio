"""Independent full-structure allowlist audit of the committed reference diff."""
import copy
import hashlib
import json
from pathlib import Path
import zipfile
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASE = ROOT/'tests/analysis_regression/baseline'
OLD = HERE/'old'
CASE = 'lymph-diagnostic-random-dor'
BEFORE, AFTER = 'Odds Ratio Summary', 'Diagnostic Odds Ratio Summary'
read = lambda path: json.loads(path.read_text())
expected_numeric = read(OLD/'numeric-contract.json')
case = next(c for c in expected_numeric['cases'] if c['id']==CASE)
case['sections'][AFTER] = case['sections'].pop(BEFORE)
expected_numeric['coverage'][CASE][AFTER] = expected_numeric['coverage'][CASE].pop(BEFORE)
expected_plots = read(OLD/'plot-descriptors.json')
next(r for r in expected_plots['rows'] if r['id']==CASE)['display']['identity'] = 'Diagnostic Odds Ratio Forest Plot'
archive = BASE/'observed-golden-baseline.zip'
archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
expected_numeric['oracle_sha256'] = expected_plots['oracle_sha256'] = archive_sha
assert read(BASE/'numeric-contract.json') == expected_numeric
assert read(BASE/'plot-descriptors.json') == expected_plots
expected_outer = read(OLD/'manifest.json')
for name, key in [('observed-golden-baseline.zip','observed_golden_analysis_bundle'),('numeric-contract.json','golden_numeric_contract'),('plot-descriptors.json','golden_plot_descriptor_contract')]:
    data = (BASE/name).read_bytes()
    expected_outer[key].update(sha256=hashlib.sha256(data).hexdigest(), size=len(data))
assert read(BASE/'manifest.json') == expected_outer
with zipfile.ZipFile(OLD/archive.name) as before, zipfile.ZipFile(archive) as after:
    assert before.namelist()==after.namelist()
    changed = [name for name in before.namelist() if before.read(name)!=after.read(name)]
    assert set(changed)=={'manifest.json',f'captures/{CASE}.json'}
    old_manifest = json.loads(before.read('manifest.json'))
    expected = copy.deepcopy(old_manifest)
    row = next(r for r in expected['curated_golden_set'] if r['id']==CASE)
    row['texts'][AFTER] = row['texts'].pop(BEFORE).replace('\nOdds Ratio -','\nDiagnostic Odds Ratio -')
    row['plot_descriptors'][0]['display']['identity']='Diagnostic Odds Ratio Forest Plot'
    assert json.loads(after.read('manifest.json'))==expected
    assert json.loads(after.read(f'captures/{CASE}.json'))==row
report = dict(passed=True, changed_archive_members=changed, all_numeric_values_and_tolerances_identical=True,
              all_other_cases_and_png_bytes_identical=True, only_metadata_change='lymph display identity label',
              only_numeric_contract_changes='lymph section/coverage keys and oracle SHA binding', outer_manifest='SHA/size bindings only')
(HERE/'independent-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
