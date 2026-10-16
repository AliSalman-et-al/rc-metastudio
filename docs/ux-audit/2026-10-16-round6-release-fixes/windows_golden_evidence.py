"""Inspect original Windows evidence and golden history without changing an oracle.

Run from the repository root after the download commands in WINDOWS-GOLDENS.md.
"""

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--ci", type=Path, required=True)
parser.add_argument("--linux", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
archive_path = "tests/analysis_regression/baseline/observed-golden-baseline.zip"
commits = subprocess.check_output(
    ["git", "log", "--format=%H", "9caf474", "--", archive_path], text=True
).splitlines()
history = []
for commit in commits:
    payload = subprocess.check_output(["git", "show", f"{commit}:{archive_path}"])
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
    history.append({
        "commit": commit,
        "archive_sha256": hashlib.sha256(payload).hexdigest(),
        "cases": {
            case["id"]: {
                "artifacts": {item["label"]: item["sha256"] for item in case["artifacts"]},
                "texts": {key: hashlib.sha256(value.encode()).hexdigest()
                          for key, value in case["texts"].items()},
            }
            for case in manifest["curated_golden_set"]
        },
    })
changes = []
for current, previous in zip(history, history[1:]):
    changes.append({
        "commit": current["commit"],
        "artifact_changes": [key for key, value in current["cases"].items()
                             if value["artifacts"] != previous["cases"][key]["artifacts"]],
        "text_changes": [[key, section] for key, value in current["cases"].items()
                         for section, digest in value["texts"].items()
                         if digest != previous["cases"][key]["texts"].get(section)],
    })

inventory = [str(path.relative_to(args.ci)) for path in sorted(args.ci.rglob("*"))
             if path.is_file()]
assert inventory, "Windows evidence has not been downloaded"
args.output.mkdir(parents=True, exist_ok=True)
inventory_path = args.ci.parent / "WINDOWS-ARTIFACT-FILES.txt"
inventory_path.write_text("\n".join(inventory) + "\n", encoding="utf-8")
with zipfile.ZipFile(archive_path) as archive:
    reference = json.loads(archive.read("manifest.json"))
linux_report = json.loads((args.linux / "compatibility-report.json").read_text())
text_checks = []
for case_id, section in [
    ("lymph-diagnostic-random-dor", "Odds Ratio Summary"),
    ("amino-binary-subgroup", "Subgroup Summary"),
    ("continuous-subgroup", "Subgroup Summary"),
]:
    expected = next(case for case in reference["curated_golden_set"] if case["id"] == case_id)
    actual = json.loads((args.linux / "captures" / f"{case_id}.json").read_text())
    text_checks.append({
        "id": case_id, "section": section,
        "linux_equals_archive": actual["texts"][section] == expected["texts"][section],
        "linux_text_sha256": hashlib.sha256(actual["texts"][section].encode()).hexdigest(),
    })
result = {
    "reference_head": "9caf474aadd98bcd10e205b47628dfd19be95f25",
    "archive_history": changes,
    "windows_artifact": json.loads((args.ci.parent / "artifact.json").read_text()),
    "windows_file_count": len(inventory),
    "windows_inventory_sha256": hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
    "windows_strict_report_paths": [path for path in inventory if path.endswith("compatibility-report.json")],
    "windows_strict_capture_paths": [path for path in inventory if "/captures/" in path],
    "windows_golden_png_paths": [path for path in inventory
                                 if Path(path).name.startswith("golden_") and path.endswith(".png")],
    "linux_capture": str(args.linux),
    "linux_passed": linux_report["passed"],
    "linux_counts": dict(Counter(row["classification"] for row in linux_report["comparison"]["rows"])),
    "text_checks": text_checks,
    "oracle_changed": subprocess.check_output(
        ["git", "diff", "9caf474", "--", "tests/analysis_regression/baseline"], text=True
    ) != "",
}
(args.output / "WINDOWS-GOLDENS.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({key: value for key, value in result.items()
                  if key not in {"archive_history", "windows_artifact"}}, indent=2))
