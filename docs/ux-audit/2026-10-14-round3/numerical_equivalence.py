"""Compare every original field with a new real-R capture without rewriting it."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--capture", type=Path, required=True)
args = parser.parse_args()
original = json.loads((HERE.parent / "2026-10-14-round2/NUMERICAL-EQUIVALENCE.json").read_text())
rows = []
for row in original["rows"]:
    capture = json.loads((args.capture / "captures" / (row["case"] + ".json")).read_text())
    value = capture["outputs"][row["section"]][row["field"]]
    assert value == row["before"], (row, value)
    rows.append({**row, "after": value})
policies = {}
for name in original["policy_sha256"]:
    path = ROOT / "tests/analysis_regression/baseline" / name
    baseline = subprocess.check_output(["git", "show", "71a8545:tests/analysis_regression/baseline/" + name], cwd=ROOT)
    actual = path.read_bytes()
    if name in {"numeric-contract.json", "plot-descriptors.json"}:
        before, after = json.loads(baseline), json.loads(actual)
        for record in (before, after):
            record.pop("oracle_sha256")
            if name == "plot-descriptors.json":
                for item in record["rows"]:
                    item.pop("artifact_oracle_sha256")
        assert before == after, name
    else:
        assert baseline == actual, name
    policies[name] = hashlib.sha256(actual).hexdigest()
result = dict(passed=True, original_field_count=len(rows), max_absolute_difference=0,
              exact_before_after=True, rows=rows, policy_sha256=policies,
              capture=str(args.capture), additional_fields="Checked by the real audit's public-package subgroup comparisons.")
(HERE / "NUMERICAL-EQUIVALENCE.json").write_text(json.dumps(result, indent=2) + "\n")
print(f"{len(rows)} original fields exactly unchanged; maximum difference 0; original numerical contracts, tolerances, and exceptions unchanged.")
