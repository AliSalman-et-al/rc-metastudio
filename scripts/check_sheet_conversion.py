#!/usr/bin/env python3
"""Proof: frozen source pair data/settings must survive conversion and both round trips.

Run: uv run python scripts/check_sheet_conversion.py
Failures covered: lost/duplicated pairs or rows; reordered data; changed raw/effect,
confidence, inclusion, covariate, label or settings values; lossy runtime/archive IO.
"""
import io
from typing import cast
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile
from rc_metastudio.project_format import load_project, save_project
from rc_metastudio.project_adapter import project_to_dataset, dataset_to_project

ROOT = Path(__file__).resolve().parents[1]

def _source_pairs(source, outcome):
    declared = list(outcome['follow_ups'])
    units = [u for r in source['studies'] for u in r['analysis_units']
             if u['outcome'] == outcome['name']]
    if not declared or any(u['follow_up'] is None for u in units):
        declared.insert(0, None)
    populated = set()
    for unit in units:
        measurements = _unit_measurements(unit)
        if any(v not in (None, '') for v in measurements):
            populated.add(unit['follow_up'])
    return [f for f in declared if f in populated] or [declared[0]]


def _unit_measurements(unit):
    measurements = [v for a in unit['groups'] for v in a['raw_data']]
    measurements += [v for es in unit['entered_effects'].values()
                     for e in es.values() for v in e.values()]
    measurements += [entry['input'].get(k)
                     for entry in unit.get('ratio_inputs', [])
                     for k in ('estimate', 'lower', 'upper', 'se')]
    return measurements


def _source_unit(row, outcome, follow):
    return next((u for u in row['analysis_units']
                 if (u['outcome'], u['follow_up']) == (outcome['name'], follow)), None)


def _empty_source_row(row, unit):
    empty_values = (not row['name'] and row['year'] is None and row['sample_size'] is None
                    and not row['notes'] and not row['manually_excluded']
                    and all(v in ('', None) for v in row['covariates'].values()))
    empty_unit = unit is None or (not unit['entered_effects'] and not unit.get('ratio_inputs')
                                 and all(v in ('', None) for arm in unit['groups'] for v in arm['raw_data']))
    return empty_values and empty_unit


def _check_row(old, row, unit, sheet, labels, ids, state, path):
    assert row['label'] == old['name']
    for key in ('year', 'sample_size', 'include', 'manually_excluded', 'notes'):
        assert row[key] == old[key], (path.name, key)
    assert row['covariates'] == {ids[k]: v for k, v in old['covariates'].items()}
    expected_raw = {a['name']: a['raw_data'] for a in unit['groups']} if unit else {}
    assert {labels[k]: v for k, v in row['raw_data'].items()} == expected_raw
    if unit:
        assert set(labels.values()) >= set(expected_raw)
        selected = [n for n in state.get('active_groups', []) if n in labels.values()]
        assert [a['name'] for a in sheet['arms']][:len(selected)] == selected
    _check_effects(row, unit, labels)


def _check_effects(row, unit, labels):
    effects = {}
    for entry in row['entered_effects']:
        effects.setdefault(entry['metric'], {})['-'.join(labels[a] for a in entry['arms'])] = entry['values']
    assert effects == (unit['entered_effects'] if unit else {})
    assert [{'groups': [labels[a] for a in entry['arms']], 'input': entry['input']}
            for entry in row['ratio_inputs']] == (unit.get('ratio_inputs', []) if unit else [])


def _check_covariates(sheet, source):
    assert [{k: v for k, v in c.items() if k != 'id'} for c in sheet['covariates']] == source['covariates']
    ids = {c['name']: c['id'] for c in sheet['covariates']}
    assert len(set(ids.values())) == len(source['covariates'])
    return ids


def _check_pair(sheet, source, state, outcome, follow, path):
    ids = _check_covariates(sheet, source)
    for key, value in (source.get('summary') or {}).items():
        assert sheet['settings']['summary'][key] == value
    for key, value in state.items():
        if key not in {'schema_version', 'active_outcome', 'active_follow_up', 'active_groups'}:
            assert sheet['settings'][key] == value
    labels = {a['id']: a['name'] for a in sheet['arms']}
    retained = [(old, _source_unit(old, outcome, follow)) for old in source['studies']]
    retained = [(old, unit) for old, unit in retained if not _empty_source_row(old, unit)]
    assert len(sheet['rows']) == len(retained)
    for (old, unit), row in zip(retained, sheet['rows'], strict=True):
        _check_row(old, row, unit, sheet, labels, ids, state, path)


def _empty_bundled_row(row):
    return (not row['label'] and row['year'] is None and not row['manually_excluded']
            and not row['entered_effects'] and not row['ratio_inputs']
            and not row['covariates'] and not row['notes'] and row['sample_size'] is None
            and all(v in ('', None) for cells in row['raw_data'].values() for v in cells))


def _check_bundled(path, document):
    bundled = load_project(path)
    # Bundled v3 archives retain the historical empty entry row; legacy import omits it.
    for sheet, converted in zip(cast(list[dict], bundled.project['sheets']), document.project['sheets'], strict=True):
        ids = {r['id'] for r in converted['rows']}
        omitted = [row for row in sheet['rows'] if row['id'] not in ids]
        assert all(_empty_bundled_row(row) for row in omitted)
        sheet['rows'][:] = [row for row in sheet['rows'] if row not in omitted]
    assert bundled.project == document.project and bundled.state == document.state


def _check_file(path):
    original = subprocess.check_output(['git', 'show', f'322ede26:sample_projects/{path.name}'], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(original)) as archive:
        source = json.loads(archive.read('project.json'))['dataset']
        state = json.loads(archive.read('state.json'))
    with tempfile.TemporaryDirectory() as tmp:
        legacy = Path(tmp) / 'source.rcms'
        legacy.write_bytes(original)
        document = load_project(legacy)
        converted_sheets = cast(list[dict], document.project['sheets'])
        sheets = iter(converted_sheets)
        count = 0
        for outcome in source['outcomes']:
            for follow in _source_pairs(source, outcome):
                _check_pair(next(sheets), source, state, outcome, follow, path)
                count += 1
                assert load_project(legacy).project == document.project
        assert next(sheets, None) is None
        assert dataset_to_project(project_to_dataset(document.project)) == document.project
        dest = Path(tmp) / 'v3.rcms'
        save_project(dest, document.project, document.state)
        reopened = load_project(dest)
        assert reopened.project == document.project and reopened.state == document.state
        assert legacy.read_bytes() == original
        _check_bundled(path, document)
        print(f'| {path.name} | {count} → {len(converted_sheets)} | yes |')


def check():
    print('| file | pairs → sheets | equal |')
    print('| --- | --- | --- |')
    for path in sorted((ROOT / 'sample_projects').glob('*.rcms')):
        _check_file(path)


if __name__ == '__main__':
    check()
