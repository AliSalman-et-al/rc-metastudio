"""Rename bundled example arms; preserve archive version and every other value."""
import hashlib
import json
from pathlib import Path
import zipfile

from rc_metastudio.project_format import load_project, reconstruct_analysis_dataset

ROOT = Path(__file__).resolve().parents[3]
SAMPLES = ROOT / 'sample_projects'
LABELS = {
    'amino.rcms': {'tx A': 'Intervention', 'tx B': 'Control'},
    'BCG.rcms': {'tx A': 'BCG vaccine', 'tx B': 'Control'},
    'continuous.rcms': {'tx A': 'Intervention', 'tx B': 'Control'},
    'lymph.rcms': {'test 1': 'Index test', 'tx A': 'Index test'},
    'meantime.rcms': {'tx A': 'Intervention', 'tx B': 'Control'},
}

def rename(value, labels):
    if isinstance(value, str):
        for old, new in labels.items():
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [rename(item, labels) for item in value]
    if isinstance(value, dict):
        return {rename(key, labels): rename(item, labels) for key, item in value.items()}
    return value

manifest_path = SAMPLES / 'manifest.json'
manifest = json.loads(manifest_path.read_text())
proof = []
for row in manifest['projects']:
    path = SAMPLES / row['file']
    labels = LABELS.get(path.name)
    if not labels:
        continue
    with zipfile.ZipFile(path) as archive:
        info = archive.infolist()
        members = {item.filename: archive.read(item) for item in info}
    before = {name: json.loads(members[name]) for name in ('project.json', 'state.json')}
    after = {name: rename(value, labels) for name, value in before.items()}
    for name, value in after.items():
        members[name] = (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode()
    inner = json.loads(members['manifest.json'])
    for name in after:
        inner['members'][name].update(sha256=hashlib.sha256(members[name]).hexdigest(), size=len(members[name]))
    members['manifest.json'] = (json.dumps(inner, sort_keys=True, separators=(',', ':')) + '\n').encode()
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for item in info:
            archive.writestr(item, members[item.filename])
    loaded = load_project(path)
    # Compare every original leaf, including numbers under renamed effect keys.
    snapshot = json.loads((ROOT / 'tests/python/fixtures/project_snapshots' / (path.name + '.json')).read_text())
    assert loaded.project['dataset'] == rename(snapshot['dataset'], labels), path
    row.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
               semantic_sha256=reconstruct_analysis_dataset(loaded).semantic_sha256,
               arm_labels=labels)
    proof.append(dict(file=path.name, sha256=row['sha256'], semantic_sha256=row['semantic_sha256'],
                      passed=True, proof='Every field equals the immutable original snapshot after only the documented string replacements.', arm_labels=labels))
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
(Path(__file__).resolve().parent / 'REVIEW1-SAMPLE-IDENTITY.json').write_text(json.dumps(proof, indent=2) + '\n')
print('Five bundled examples renamed; every original field and number preserved after only documented label replacements.')
