"""Audit accepted desktop evidence and all curated native file hashes."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.verify_rcms import SCENARIOS


def checked_record(label):
    record = json.loads((HERE / "raw" / f"{label}.json").read_text())
    assert record["exit_code"] == 0, label
    assert hashlib.sha256((HERE / "raw" / record["log"]).read_bytes()).hexdigest() == record["sha256"]
    return record


def checked_bundle(path):
    manifest = json.loads((path / "manifest.json").read_text())
    assert manifest["passed"] and manifest["exit_code"] == 0, path
    for entry in manifest["files"]:
        file = path / entry["path"]
        assert hashlib.sha256(file.read_bytes()).hexdigest() == entry["sha256"], file
    return manifest, len(manifest["files"])


run = checked_record("review2-desktop-accepted")
started, finished = map(datetime.fromisoformat, (run["started"], run["finished"]))
rows = []
for path in (ROOT / "artifacts/verification/rcms").glob("*/manifest.json"):
    manifest = json.loads(path.read_text())
    if not manifest.get("started_utc") or manifest.get("native_requested") or not started <= datetime.fromisoformat(manifest["started_utc"]) <= finished:
        continue
    manifest, count = checked_bundle(path.parent)
    rows.append(dict(scenario=manifest["scenario"], path=str(path.parent), files=count))
expected = set(SCENARIOS) - {"doctor"}
assert len(rows) == len(expected) == 86
assert {row["scenario"] for row in rows} == expected
curated = json.loads((HERE / "raw/curated-review2.json").read_text())
assert len(curated) == 19
native = {}
for frame in curated:
    original = Path(frame["source"])
    assert hashlib.sha256(original.read_bytes()).hexdigest() == frame["sha256"], original
    assert hashlib.sha256((HERE / "screenshots" / frame["file"]).read_bytes()).hexdigest() == frame["sha256"]
    if original.parent not in native:
        manifest, count = checked_bundle(original.parent)
        assert manifest["native_requested"], original
        native[original.parent] = count
diagnostic = checked_record("review2-complete-native-lymph")
diagnostic_log = (HERE / "raw" / diagnostic["log"]).read_text()
diagnostic_path = Path(next(line.removeprefix("Evidence: ") for line in diagnostic_log.splitlines() if line.startswith("Evidence: ")))
manifest, count = checked_bundle(diagnostic_path)
assert manifest["native_requested"]
native[diagnostic_path] = count
report = dict(passed=True, desktop=rows, desktop_files=sum(row["files"] for row in rows),
              native_bundles=len(native), native_files=sum(native.values()), curated=curated)
(HERE / "raw/review2-evidence-validation-results.json").write_text(json.dumps(report, indent=2))
print(f"86 desktop bundles and {len(native)} native bundles verified; 19 untouched curated frames; "
      f"{report['desktop_files'] + report['native_files']} retained files hash-checked.")
