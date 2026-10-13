"""Compare the retained pre-round values with a fresh real-R golden capture."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
import io

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--capture", type=Path, default=ROOT / "build/qt6-verification/golden-compatibility-review1-final")
parser.add_argument("--authorities", type=Path, default=HERE / "raw/authorities-results.json")
args = parser.parse_args()
record_path = HERE / "NUMERICAL-EQUIVALENCE.json"
record = json.loads(record_path.read_text(encoding="utf-8"))
for name, expected in record["policy_sha256"].items():
    actual = hashlib.sha256((ROOT / "tests/analysis_regression/baseline" / name).read_bytes()).hexdigest()
    assert actual == expected, name
for row in record["rows"]:
    capture = json.loads((args.capture / "captures" / (row["case"] + ".json")).read_text(encoding="utf-8"))
    actual = capture["outputs"][row["section"]][row["field"]]
    assert actual == row["before"], (row, actual)
    row["after"] = actual
old_bytes = subprocess.check_output(["git", "show", "84fdbc57:tests/analysis_regression/baseline/observed-golden-baseline.zip"], cwd=ROOT)
with zipfile.ZipFile(io.BytesIO(old_bytes)) as old, zipfile.ZipFile(ROOT / "tests/analysis_regression/baseline/observed-golden-baseline.zip") as new:
    old_cases = json.loads(old.read("manifest.json"))["curated_golden_set"]
    new_cases = json.loads(new.read("manifest.json"))["curated_golden_set"]
    assert [(case["id"], case["outputs"]) for case in old_cases] == [(case["id"], case["outputs"]) for case in new_cases]
authorities = json.loads(args.authorities.read_text(encoding="utf-8"))["cases"]
case_hash = hashlib.sha256(json.dumps(authorities, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
assert case_hash == record["authority_cases_sha256"]
report = json.loads((args.capture / "compatibility-report.json").read_text(encoding="utf-8"))
assert report["passed"], report
record.update(strict_golden_passed=True, strict_golden_classifications=dict(Counter(row["classification"] for row in report["comparison"]["rows"])),
              oracle_diff="Presentation bundle and its manifest hash refreshed; numerical outputs and all policy bytes unchanged.",
              max_absolute_difference=0, exact_before_after=True, authority_cases_identical=True)
record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(f"{len(record['rows'])} fields exactly unchanged; maximum difference 0; {len(authorities)} authority cases identical; golden exit 0.")
