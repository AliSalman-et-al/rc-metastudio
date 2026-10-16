"""Check the same-head baseline regeneration changes only custom-infix metrics."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.code_health import _r_tokens

folder = ROOT / "docs/ux-audit/2026-10-16-round6-release-fixes/raw/lexer"
before_path = folder / "baseline-before.json"
after_path = ROOT / "artifacts/code-health/baseline.json"
before = json.loads(before_path.read_text())
after = json.loads(after_path.read_text())
assert before["head"] == after["head"] == "8b7796bcc840c3505c5fb0a1328cdd7682880e48"
assert before.keys() == after.keys()
assert all(before[key] == after[key] for key in before if key not in {"functions", "files", "cognitive_complexity"})
assert len(before["functions"]) == len(after["functions"])
changed = []
for old, new in zip(before["functions"], after["functions"]):
    if old == new:
        continue
    assert all(old[key] == new[key] for key in old if key not in {"cyclomatic", "cognitive"})
    assert new["path"].endswith(".R")
    source = subprocess.check_output(["git", "show", f'{after["head"]}:{new["path"]}'], cwd=ROOT).decode("utf-8")
    body = "\n".join(source.splitlines()[new["line"] - 1:new["end_line"]])
    operators = [token for token, _ in _r_tokens(body) if token.startswith("%") and ("||" in token or "&&" in token)]
    assert old["cyclomatic"] - new["cyclomatic"] == old["cognitive"] - new["cognitive"] == len(operators) > 0
    changed.append({"path": new["path"], "function": new["name"], "operators": operators,
                    "before": old, "after": new})
old_files = {item["path"]: item for item in before["files"]}
new_files = {item["path"]: item for item in after["files"]}
assert old_files.keys() == new_files.keys()
for path, new in new_files.items():
    old = old_files[path]
    delta = sum(item["before"]["cyclomatic"] - item["after"]["cyclomatic"] for item in changed if item["path"] == path)
    if not delta:
        assert old == new
        continue
    assert all(old[key] == new[key] for key in old if key not in {"complexity", "hotspot_score"})
    assert old["complexity"]["cyclomatic"] - new["complexity"]["cyclomatic"] == delta
    assert old["complexity"]["functions"] == new["complexity"]["functions"]
    assert new["complexity"]["density"] == new["complexity"]["cyclomatic"] / max(new["lines"], 1)
    assert new["hotspot_score"] == new["churn"]["180"] / max(new["lines"], 1) * new["complexity"]["density"]
assert before["cognitive_complexity"]["total"] - after["cognitive_complexity"]["total"] == sum(len(item["operators"]) for item in changed)
assert after["cognitive_complexity"]["maximum"] == max(item["cognitive"] for item in after["functions"])
assert before["cognitive_complexity"]["functions"] == after["cognitive_complexity"]["functions"]
report = {"head": after["head"], "before_sha256": hashlib.sha256(before_path.read_bytes()).hexdigest(),
          "after_sha256": hashlib.sha256(after_path.read_bytes()).hexdigest(),
          "changed_functions": changed, "changed_function_count": len(changed),
          "removed_false_branches": sum(len(item["operators"]) for item in changed),
          "other_changes": "Only derived file complexity/density/hotspot ranking and cognitive aggregate; all other values identical."}
(ROOT / "docs/ux-audit/2026-10-16-round6-release-fixes/CI-BASELINE-AUDIT.json").write_text(json.dumps(report, indent=2) + "\n")
print(f'PASS: {len(changed)} functions; {report["removed_false_branches"]} false branches; same recorded head')
