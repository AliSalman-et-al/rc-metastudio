"""Run real desktop results serially and retain per-surface held-value losses."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def absent_values(data, text):
    from tests.e2e.report_retention import numeric_tokens
    tokens = set(numeric_tokens(text))
    cells = [dict(section=t['section'], table=t['title'], row=i, header=h, value=v)
             for t in data['held'] for i, row in enumerate(t['rows']) for h, v in zip(t['headers'], row)]
    cells += [dict(section=s['section'], table='Held output', row=i, header='Held output', value=line)
              for s in data.get('held_text', []) for i, line in enumerate(s['value'].splitlines())]
    cells += [dict(section=s['section'], table='Held notes', row=i, header='Held note', value=paragraph)
              for s in data.get('held_notes', []) for i, paragraph in enumerate(s['paragraphs'])]
    return [cell for cell in cells if any(token not in tokens for token in numeric_tokens(cell['value']))]


def read_snapshot(path):
    data = json.loads(path.read_text())
    data['directory'] = str(path.parent)
    return data


def compare_result(path, after):
    old = json.loads(path.read_text())
    scenario = path.parts[-3]
    candidates = [read_snapshot(p) for p in (after / scenario).glob('*/audit.json')]
    matches = [data for data in candidates if data['held'] == old['held']
               and (not old.get('held_text') or data.get('held_text') == old['held_text'])]
    assert matches, (scenario, 'no matching real result after restoration')
    new = matches[-1]
    missing = {surface: absent_values(old, (path.parent / (surface + '.txt')).read_text())
               for surface in ('copy', 'pdf', 'docx')}
    restored = {surface: absent_values(new, (Path(new['directory']) / (surface + '.txt')).read_text())
                for surface in ('copy', 'pdf', 'docx')}
    retained_rows = []
    for table in new['held']:
        caption = table['title'] if table['section'] == table['title'] else table['section'] + ' — ' + table['title']
        target = next(t for t in new['presented'] if t['title'] == caption)
        assert (target['headers'], target['rows']) == (table['headers'], table['rows'])
        retained_rows.append(dict(section=table['section'], table=table['title'], rows=len(table['rows'])))
    retained_lines = check_held_text(new)
    assert not any(restored.values()), (scenario, restored)
    return dict(scenario=scenario, before_missing=missing, after_missing=restored,
                exact_labelled_tables=retained_rows, exact_labelled_text_lines=retained_lines)


def check_held_text(data):
    retained = []
    for section in data.get('held_text', []):
        if not section['value']:
            continue
        target = next(t for t in data['presented'] if t['title'] == section['section'] + ' — Held output')
        expected = [[line] for line in section['value'].splitlines()]
        assert (target['headers'], target['rows']) == (['Held output'], expected)
        retained.append(dict(section=section['section'], lines=len(expected)))
    for section in data.get('held_notes', []):
        target = next(t for t in data['presented'] if t['title'] == section['section'] + ' — Held notes')
        assert (target['headers'], target['rows']) == (['Held note'], [[p] for p in section['paragraphs']])
        retained.append(dict(section=section['section'], notes=len(section['paragraphs'])))
    return retained


def compare(before, after):
    comparisons = []
    for directory in before:
        for path in directory.glob('*/*/audit.json'):
            data = read_snapshot(path)
            if not data['held'] and not data.get('held_text'):
                continue
            comparisons.append(compare_result(path, after))
    (after / 'comparison.json').write_text(json.dumps(comparisons, indent=2, ensure_ascii=False))
    print(json.dumps({item['scenario']: {k: len(v) for k, v in item['before_missing'].items()} for item in comparisons}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compare-before', type=Path, action='append')
    parser.add_argument('scenarios', nargs='*')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.compare_before:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        compare(args.compare_before, args.output)
        return
    runs = []
    for scenario in args.scenarios:
        directory = args.output.resolve() / scenario
        environment = dict(os.environ, RCMS_REPORT_AUDIT_DIR=str(directory), RCMS_E2E_REUSE_PASSED='0')
        command = [sys.executable, 'scripts/verify_rcms.py', scenario]
        result = subprocess.run(command, env=environment, capture_output=True, text=True)
        (args.output / (scenario + '.log')).write_text(result.stdout + result.stderr)
        audits = [json.loads(p.read_text()) for p in directory.glob('*/audit.json')]
        runs.append(dict(scenario=scenario, command=command, exit_code=result.returncode,
                         results=len(audits), missing={surface: [cell for a in audits for cell in a['missing'][surface]]
                                                     for surface in ('copy', 'pdf', 'docx')}))
        (args.output / 'summary.json').write_text(json.dumps(runs, indent=2, ensure_ascii=False))
        print(scenario, 'results:', len(audits), 'missing:', {k: len(v) for k, v in runs[-1]['missing'].items()}, flush=True)


if __name__ == '__main__':
    main()
