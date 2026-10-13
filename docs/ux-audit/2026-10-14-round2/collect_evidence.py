"""Index retained runs and copy reviewable native evidence without changing it."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2), encoding="utf-8")


runs = []
native = []
for path in sorted(HERE.glob("*.json")):
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict) or "command" not in record or "label" not in record:
        continue
    log = HERE / record["log"]
    assert digest(log) == record["sha256"], log
    runs.append(record)
    match = re.search(r"^Evidence: (.+)$", log.read_text(encoding="utf-8"), re.M)
    if not match:
        continue
    bundle = Path(match.group(1).strip())
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    for file in manifest["files"]:
        assert digest(bundle / file["path"]) == file["sha256"], bundle / file["path"]
    native.append(dict(label=record["label"], bundle=str(bundle.relative_to(ROOT)),
                       passed=manifest["passed"], command=manifest["command"],
                       head=manifest["head"], manifest_sha256=digest(bundle / "manifest.json"),
                       file_count=len(manifest["files"])))
    if not record["label"].startswith(("after-final-native-", "after-label-native-")):
        continue
    destination = HERE / "native" / record["label"]
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("manifest.json", "runtime.json", "steps.jsonl", "stdout.log", "stderr.log"):
        shutil.copy2(bundle / name, destination / name)
    screenshots = sorted(bundle.glob("*.png"))
    selected = []
    for screenshot in screenshots:
        name = screenshot.name
        if any(key in name for key in ("analysis-results", "matrix-results", "small-study-results",
                                       "ux-readable-report", "ux-native-result-table", "ux-independent-view-zoom",
                                       "ux-csv-page-entry", "ux-header-geometry", "ux-empty-workspace",
                                       "ux-quick-start", "calculator-open", "calculator-preview",
                                       "plot-editor", "structure-dialog", "analysis-configured")):
            selected.append(screenshot)
    if not selected:
        selected = screenshots[1:3]
    for screenshot in selected:
        shutil.copy2(screenshot, destination / screenshot.name)
    save_path = destination / "selected.json"
    save_path.write_text(json.dumps([dict(path=p.name, sha256=digest(p),
                                         inspection="pending") for p in selected], indent=2), encoding="utf-8")

save("RUNS.json", runs)
save("NATIVE-INDEX.json", native)
files = subprocess.check_output(["git", "ls-files", "r/RCMetaR", "src/rc_metastudio",
                                 "tests/e2e", ".agents/skills/verify-rcms/scripts"], cwd=ROOT,
                                text=True).splitlines()
save("SOURCE.json", dict(head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                                        text=True).strip(),
                         files=[dict(path=p, sha256=digest(ROOT / p)) for p in files]))
print(f"Verified {len(runs)} command logs and {len(native)} complete evidence bundles.")
