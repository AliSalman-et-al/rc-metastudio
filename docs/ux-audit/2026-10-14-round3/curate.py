"""Retain passing native observations and representative, unmodified screenshots."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PREFIX = sys.argv[1] if len(sys.argv) > 1 else "native-final"
LABELS = {family: PREFIX + "-" + family for family in (
    "onearm-proportion", "onearm-mean", "reg-coef", "generic-effect",
    "twoarm-proportion", "twoarm-mean", "twoarm-smd", "diagnostic",
    "hr", "irr", "references", "precision",
)}
observations = []
screenshots = []
index = HERE / "SCREENSHOTS.json"
previous = json.loads(index.read_text()) if index.exists() else []
(HERE / "screenshots").mkdir(exist_ok=True)
for family, label in LABELS.items():
    command = json.loads((HERE / "raw" / (label + ".json")).read_text())
    assert command["exit_code"] == 0, command
    log = (HERE / "raw" / command["log"]).read_text()
    evidence = Path(re.search(r"Evidence: (.+)", log)[1])
    manifest = json.loads((evidence / "manifest.json").read_text())
    steps = [json.loads(line) for line in (evidence / "steps.jsonl").read_text().splitlines()]
    observed = [step for step in steps if step["action"].startswith("round3-")]
    observations.append(dict(family=family, command=command, evidence=str(evidence.relative_to(ROOT)),
                             manifest=manifest, runtime=json.loads((evidence / "runtime.json").read_text()),
                             observations=observed))
    selections = []
    if family in {"hr", "irr", "twoarm-mean", "diagnostic"}:
        selections += [s for s in observed if s["action"] == "round3-sequential-rows"]
    if family in {"references", "precision"}:
        selections += [s for s in observed if s["action"] in {
            "round3-report-copy-export", "round3-zero-bound-presentation",
            "round3-small-effects-preserved", "round3-bubble-tick-coverage"}]
    if family in {"hr", "irr"}:
        selections += [s for s in observed if s["action"] in {
            "round3-sequential-bottom", "round3-fixed-footer-bottom"}]
    if family == "twoarm-mean":
        selections += [s for s in observed if s["action"] == "round3-null-excluded-rendered"]
    for step in selections:
        for source_name in step["captures"]:
            source = evidence / source_name
            target = HERE / "screenshots" / (family + "-" + source_name)
            shutil.copy2(source, target)
            screenshots.append(dict(path=str(target.relative_to(HERE)), source=str(source.relative_to(ROOT)),
                                    sha256=hashlib.sha256(source.read_bytes()).hexdigest(), family=family,
                                    action=step["action"], step=step["step"]))
    for step in observed:
        if step["action"] == "round3-report-copy-export":
            (HERE / "screenshots" / f"{family}-{step['step']:02d}-report.txt").write_text(step["text"], encoding="utf-8")
(HERE / "OBSERVATIONS.json").write_text(json.dumps(observations, indent=2, ensure_ascii=False) + "\n")
retained = {row["path"] for row in screenshots}
for row in previous:
    if row["path"] not in retained:
        (HERE / row["path"]).unlink(missing_ok=True)
index.write_text(json.dumps(screenshots, indent=2) + "\n")
print(f"Retained {len(observations)} native runs and {len(screenshots)} screenshots.")
