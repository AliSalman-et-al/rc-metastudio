"""Retain native review proofs and replace the selected audit illustrations."""

import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DESTINATION = Path(__file__).resolve().parent
SCREENSHOTS = DESTINATION.parent / "screenshots"
SELECTIONS = {
    "native-ux-125.log": {"ux-plot-toolbar": "plot-toolbar.png", "ux-readable-report": "readable-report.png", "ux-inline-analysis-error": "analysis-inline-error.png"},
    "native-analysis-amino-binary-cumulative.log": {"matrix-results": "cumulative-results.png"},
    "native-analysis-amino-binary-leave-one-out.log": {"matrix-results": "leave-one-out-results.png"},
    "native-analysis-amino-binary-subgroup.log": {"matrix-results": "subgroup-results.png"},
    "native-analysis-amino-binary-meta-regression.log": {"matrix-results": "regression-results.png"},
    "native-analysis-data-onearm-proportion.log": {"matrix-results": "onearm-results.png"},
    "native-continuous.log": {"analysis-results": "continuous-results.png"},
    "native-analysis-diagnostic-joint.log": {"matrix-results": "diagnostic-results.png"},
    "native-analysis-data-onearm-mean.log": {"matrix-results": "mean-results.png"},
    "native-analysis-data-reg-coef.log": {"matrix-results": "coefficient-results.png"},
    "native-analysis-data-generic-effect.log": {"matrix-results": "entered-effect-results.png"},
    "native-analysis-diagnostic-regression-multiple.log": {"matrix-results": "diagnostic-regression-results.png"},
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


index = []
for log, selections in SELECTIONS.items():
    matches = re.findall(r"Evidence: (.+)", (DESTINATION / log).read_text())
    source = Path(matches[-1].strip())
    manifest = json.loads((source / "manifest.json").read_text())
    assert manifest["passed"] and manifest["native_requested"], source
    for item in manifest["files"]:
        assert digest(source / item["path"]) == item["sha256"], item
    target = DESTINATION / "evidence" / source.name
    shutil.copytree(source, target, dirs_exist_ok=True)
    steps = [json.loads(line) for line in (source / "steps.jsonl").read_text().splitlines()]
    captured = {}
    for action, filename in selections.items():
        step = next(step for step in steps if step["action"] == action)
        shutil.copy2(source / step["captures"][0], SCREENSHOTS / filename)
        captured[filename] = {"action": action, "sha256": digest(SCREENSHOTS / filename)}
    index.append({"log": log, "original": str(source), "retained": str(target.relative_to(ROOT)),
                  "command": manifest["command"], "passed": True, "screenshots": captured,
                  "runtime": json.loads((source / "runtime.json").read_text())})
(DESTINATION / "native-evidence.json").write_text(json.dumps(index, indent=2) + "\n")
print(f"Verified and retained {len(index)} native proofs")
