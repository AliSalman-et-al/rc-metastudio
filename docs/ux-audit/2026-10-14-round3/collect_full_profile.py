"""Bind a passing full profile to every expected desktop scenario artifact."""
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.verify_rcms import SCENARIOS

label = sys.argv[1] if len(sys.argv) > 1 else "full-final"
attempt = json.loads((HERE / "raw" / (label + ".json")).read_text())
assert attempt["exit_code"] == 0, attempt
log = (HERE / "raw" / attempt["log"]).read_text()
directory = Path(re.search(r"Complete-run evidence: (.+)", log)[1])
summary = json.loads((directory / "summary.json").read_text())
assert summary["passed"] and len(summary["commands"]) == 3, summary
start = datetime.fromisoformat(attempt["started"])
end = datetime.fromisoformat(attempt["finished"])
runs = []
for manifest in sorted((ROOT / "artifacts/verification/rcms").glob("*/manifest.json")):
    if not re.match(r"\d{8}T\d{6}Z-", manifest.parent.name):
        continue
    stamp = datetime.strptime(manifest.parent.name[:16], "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    if not start <= stamp <= end:
        continue
    observed = json.loads(manifest.read_text())
    if observed.get("native_requested"):
        continue
    assert observed["passed"], manifest
    steps = [json.loads(line) for line in manifest.with_name("steps.jsonl").read_text().splitlines()]
    runs.append(dict(scenario=observed["scenario"], evidence=str(manifest.parent.relative_to(ROOT)),
                     manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
                     actions=[step["action"] for step in steps],
                     runtime=json.loads(manifest.with_name("runtime.json").read_text()),
                     files=observed["files"]))
assert len(runs) == len(SCENARIOS) == 99, len(runs)
assert {run["scenario"] for run in runs} == set(SCENARIOS)
stack_log = (directory / "00.log").read_text()
assert "98 passed" in stack_log and "Status: OK" in stack_log
proof = dict(passed=True, command=attempt, summary=summary, desktop_scenarios=98,
             doctor=1, runs=runs,
             stack_results_verbatim=[line for line in stack_log.splitlines()
                 if "passed" in line or "Status:" in line or "Reitsma visual" in line])
(HERE / "FULL-PROFILE.json").write_text(json.dumps(proof, indent=2) + "\n")
print("Full profile passed: all 98 desktop scenarios once, doctor, and the current-source R-stack gates.")
