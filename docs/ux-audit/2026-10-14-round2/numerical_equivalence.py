"""Compare the original frozen fields, without changing any oracle or tolerance."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
before = ROOT / "build/qt6-verification/golden-compatibility-round2-before-retry"
after = ROOT / "build/qt6-verification/golden-compatibility-round2-handoff"
contract_path = ROOT / "tests/analysis_regression/baseline/numeric-contract.json"
contract = json.loads(contract_path.read_text())
rows = []
for case in contract["cases"]:
    old = json.loads((before / "captures" / (case["id"] + ".json")).read_text())["outputs"]
    new = json.loads((after / "captures" / (case["id"] + ".json")).read_text())["outputs"]
    for section, values in case["sections"].items():
        for field, expected in values.items():
            actual_before, actual_after = old[section][field], new[section][field]
            assert actual_before == actual_after, (case["id"], section, field)
            rows.append(dict(case=case["id"], section=section, field=field,
                             expected=expected, before=actual_before, after=actual_after))
report = json.loads((after / "compatibility-report.json").read_text())
classifications = Counter(row["classification"] for row in report["comparison"]["rows"])
assert set(classifications) <= {"pass", "accepted_exception", "text_artifact_drift"}, classifications
oracle_diff = subprocess.check_output(["git", "diff", "--name-only", "84fdbc57", "HEAD", "--",
                                       "tests/analysis_regression/baseline"], cwd=ROOT, text=True)
assert not oracle_diff, oracle_diff
old_authorities = json.loads((HERE / "before-authorities-results.json").read_text())
new_authorities = json.loads((HERE / "authorities-handoff-results.json").read_text())
assert old_authorities["cases"] == new_authorities["cases"]
result = dict(passed=True, case_count=len(contract["cases"]), metric_count=len(rows),
              exact_before_after=True, max_absolute_difference=0, oracle_diff=oracle_diff,
              contract_sha256=hashlib.sha256(contract_path.read_bytes()).hexdigest(),
              authority_case_count=len(new_authorities["cases"]), authority_cases_identical=True,
              strict_golden_passed=report["passed"], strict_golden_classifications=dict(classifications),
              rows=rows)
(HERE / "NUMERICAL-EQUIVALENCE.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"{len(rows)} frozen fields exactly unchanged; {len(new_authorities['cases'])} authority cases identical.")
