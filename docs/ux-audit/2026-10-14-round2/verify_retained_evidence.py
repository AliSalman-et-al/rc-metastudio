"""Check committed log bytes, curated images and unchanged statistical oracles."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def sha(data):
    return hashlib.sha256(data).hexdigest()

records = json.loads((HERE / "RUNS.json").read_text())
for record in records:
    path = HERE / record["log"]
    committed = subprocess.check_output(
        ["git", "show", "HEAD:" + path.relative_to(ROOT).as_posix()], cwd=ROOT)
    assert sha(committed) == record["sha256"], path
screens = json.loads((HERE / "SCREENSHOTS.json").read_text())
for screen in screens:
    path = HERE / screen["path"]
    assert "Manually checked" in screen["inspection"], path
    assert sha(path.read_bytes()) == screen["sha256"], path
native = [r for r in records if r["label"].startswith("after-final-native-")]
assert len(native) == 22 and all(r["exit_code"] == 0 for r in native)
assert subprocess.check_output(["git", "diff", "84fdbc57", "HEAD", "--",
    "tests/analysis_regression/baseline"], cwd=ROOT) == b""
result = dict(passed=True, command=["uv", "run", "python",
    "docs/ux-audit/2026-10-14-round2/verify_retained_evidence.py"],
    revision=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
        text=True).strip(), committed_log_digests=len(records),
    reviewed_screenshot_digests=len(screens), final_native_passes=len(native),
    oracle_diff="")
(HERE / "EVIDENCE-INTEGRITY.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result))
