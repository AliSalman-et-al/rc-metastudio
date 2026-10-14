"""Check curated artifact bytes and the final installed-source binding."""
import base64
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

records = json.loads((HERE/'REVIEW1-NATIVE.json').read_text())
frames = 0
for run in records.values():
    assert run['attempt']['exit_code'] == 0
    folder = ROOT/run['evidence']
    assert sha(folder/'manifest.json') == run['manifest_sha256']
    assert run['runtime']['platform_plugin'] == 'xcb'
    assert '4.6.1' in run['runtime']['r']
    for frame in run['frames']:
        assert sha(HERE/frame['path']) == frame['sha256'], frame
        frames += 1
for frame in json.loads((HERE/'SCREENSHOTS.json').read_text()):
    assert sha(HERE/frame['path']) == frame['sha256'], frame['path']
exports = json.loads((HERE/'REVIEW1-EXPORTS.json').read_text())
assert len(exports) == 16
for row in exports:
    assert sha(ROOT/row['original']) == row['original_sha256']
    assert sha(HERE/row['preview']) == row['preview_sha256']
installed = json.loads((HERE/'INSTALLED-SOURCE.json').read_text())
assert installed['exit_code'] == 0 and installed['revision'].startswith('8c8e8a3')
for relative, digest in installed['source_sha256'].items():
    assert sha(ROOT/'r/RCMetaR'/relative) == digest, relative
for relative, digest in installed['installed_sha256'].items():
    assert sha(Path(installed['library'])/'RCMetaR'/relative) == digest, relative
contact = HERE/'contact-sheet.html'
assert sha(contact) == json.loads((HERE/'CONTACT-SHEET-REVIEW.json').read_text())['sha256']
embedded = re.findall(r'src="data:image/png;base64,([^\"]+)"', contact.read_text())
assert len(embedded) == 17
native_hashes = {sha(path) for path in (HERE/'screenshots').glob('*.png')}
assert all(hashlib.sha256(base64.b64decode(data)).hexdigest() in native_hashes for data in embedded)
result = dict(passed=True,native_receipts=len(records),curated_native_frames=frames,
              publication_previews=len(exports),embedded_contact_frames=len(embedded),
              source_files=len(installed['source_sha256']),installed_files=len(installed['installed_sha256']),
              scope='Every curated native/preview/contact byte and final source/install hash checked; original per-run manifests retain full native artifacts.')
(HERE/'EVIDENCE-INTEGRITY.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
