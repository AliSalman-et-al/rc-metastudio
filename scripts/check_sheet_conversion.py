#!/usr/bin/env python3
"""Proof: frozen source pair data/settings must survive conversion and both round trips.

Run: uv run python scripts/check_sheet_conversion.py
Failures covered: lost/duplicated pairs or rows; reordered data; changed raw/effect,
confidence, inclusion, covariate, label or settings values; lossy runtime/archive IO.
"""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile
from rc_metastudio.project_format import load_project, save_project
from rc_metastudio.project_adapter import project_to_dataset, dataset_to_project

ROOT = Path(__file__).resolve().parents[1]

def check():
    print('| file | pairs → sheets | equal |')
    print('| --- | --- | --- |')
    for path in sorted((ROOT/'sample_projects').glob('*.rcms')):
        original = subprocess.check_output(['git','show',f'322ede26:sample_projects/{path.name}'], cwd=ROOT)
        with zipfile.ZipFile(io.BytesIO(original)) as z:
            source = json.loads(z.read('project.json'))['dataset']
            state = json.loads(z.read('state.json'))
        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp)/'source.rcms'; legacy.write_bytes(original)
            document = load_project(legacy)
            sheets = iter(document.project['sheets']); count = 0
            for outcome in source['outcomes']:
                pairs = list(outcome['follow_ups'])
                if not pairs or any(u['outcome']==outcome['name'] and u['follow_up'] is None for r in source['studies'] for u in r['analysis_units']):
                    pairs.insert(0,None)
                for follow in pairs:
                    sheet = next(sheets); count += 1
                    assert sheet['covariates'] == source['covariates']
                    for key,value in (source.get('summary') or {}).items():
                        assert sheet['settings']['summary'][key] == value
                    for key,value in state.items():
                        if key not in {'schema_version','active_outcome','active_follow_up','active_groups'}:
                            assert sheet['settings'][key] == value
                    labels = {a['id']:a['name'] for a in sheet['arms']}
                    assert len(sheet['rows']) == len(source['studies'])
                    for old,row in zip(source['studies'],sheet['rows'],strict=True):
                        assert row['label'] == old['name']
                        for key in ('year','sample_size','include','manually_excluded','notes','covariates'):
                            assert row[key] == old[key], (path.name,key)
                        unit = next((u for u in old['analysis_units'] if (u['outcome'],u['follow_up'])==(outcome['name'],follow)),None)
                        expected_raw = {a['name']:a['raw_data'] for a in unit['groups']} if unit else {}
                        assert {labels[k]:v for k,v in row['raw_data'].items()} == expected_raw
                        expected_effects = unit['entered_effects'] if unit else {}
                        effects = {}
                        for entry in row['entered_effects']:
                            effects.setdefault(entry['metric'],{})['-'.join(labels[a] for a in entry['arms'])] = entry['values']
                        assert effects == expected_effects
                        assert [{'groups':[labels[a] for a in entry['arms']], 'input':entry['input']} for entry in row['ratio_inputs']] == (unit.get('ratio_inputs',[]) if unit else [])
            assert next(sheets,None) is None
            assert dataset_to_project(project_to_dataset(document.project)) == document.project
            dest = Path(tmp)/'v3.rcms'
            save_project(dest,document.project,document.state)
            reopened = load_project(dest)
            assert reopened.project == document.project and reopened.state == document.state
            assert legacy.read_bytes() == original
            print(f'| {path.name} | {count} → {len(document.project["sheets"])} | yes |')
if __name__ == '__main__': check()
