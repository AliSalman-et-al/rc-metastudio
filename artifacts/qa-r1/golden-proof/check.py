"""Throwaway approval proof. Never edits references; nonzero exit forbids applying changes."""
import argparse
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[3]
BASELINE = ROOT / 'tests/analysis_regression/baseline'
NUMBER = re.compile(r'(?<![\w.])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?')
APPROVED = {'amino-binary-leave-one-out', 'continuous-leave-one-out'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('capture', type=Path)
    parser.add_argument('--baseline', type=Path, default=BASELINE)
    args = parser.parse_args()
    baseline = args.baseline
    current = json.loads((args.capture / 'manifest.json').read_text())
    with zipfile.ZipFile(baseline / 'observed-golden-baseline.zip') as archive:
        old = json.loads(archive.read('manifest.json'))
    before = {row['id']: row for row in old['curated_golden_set']}
    after = {row['id']: row for row in current['curated_golden_set']}
    assert before.keys() == after.keys()
    result = {'passed': True, 'changed_fields': [], 'mismatches': [], 'reference_hashes': {}, 'excluded_current_only_fields': [], 'excluded_preexisting_master_drift': []}
    for path in sorted(baseline.iterdir()):
        if path.is_file():
            result['reference_hashes'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    for case, previous in before.items():
        actual = after[case]
        assert actual['status'] == 'success', (case, actual.get('failure'))
        for field in sorted(set(previous['texts']) | set(actual['texts'])):
            if field not in previous['texts']:
                result['excluded_current_only_fields'].append({'case': case, 'field': field, 'reason': 'not a proposed frozen-field update; existing compatibility exception retained'})
                continue
            left = previous['texts'].get(field, '')
            right = actual['texts'].get(field, '')
            if left == right:
                continue
            if case in ('amino-binary-meta-regression', 'continuous-meta-regression') and field == 'Summary':
                result['excluded_preexisting_master_drift'].append({'case': case, 'field': field, 'reason': 'regression text producer identical to master; existing exception retained'})
                continue
            assert case in APPROVED, case
            assert field == 'Leave-one-out Summary', field
            expected_removals = 19 if case == 'amino-binary-leave-one-out' else 6
            assert left.count('Study omitted: ') == expected_removals
            assert 'Study omitted: ' not in right
            assert ' '.join(left.replace('Study omitted: ', '').split()) == ' '.join(right.split())
            entry = {'case': case, 'field': 'texts.' + field, 'before': left, 'after': right, 'numbers': []}
            old_numbers, new_numbers = NUMBER.findall(left), NUMBER.findall(right)
            if len(old_numbers) != len(new_numbers):
                result['mismatches'].append({'case': case, 'field': field, 'reason': 'number appeared/disappeared',
                                             'old_numbers': old_numbers, 'new_numbers': new_numbers})
            else:
                for index, (a, b) in enumerate(zip(old_numbers, new_numbers)):
                    old_value, new_value = Decimal(a), Decimal(b)
                    precision = new_value.as_tuple().exponent
                    quantum = Decimal(1).scaleb(precision)
                    rounded = old_value.quantize(quantum, rounding=ROUND_HALF_EVEN)
                    passed = new_value == rounded
                    entry['numbers'].append({'index': index, 'old': a, 'new': b, 'quantum': str(quantum),
                                             'rounded': str(rounded), 'passed': passed})
                    if not passed:
                        result['mismatches'].append({'case': case, 'field': field, 'index': index,
                                                     'old': a, 'new': b, 'reason': 'not old rounded to new precision'})
            result['changed_fields'].append(entry)
    assert {entry['case'] for entry in result['changed_fields']} == APPROVED
    result['prefix_and_whitespace_only'] = True
    result['passed'] = not result['mismatches']
    destination = Path(__file__).with_name('output.json')
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'changed_fields': len(result['changed_fields']),
                      'mismatches': result['mismatches'], 'output': str(destination)}, indent=2))
    raise SystemExit(0 if result['passed'] else 1)

if __name__ == '__main__':
    main()
