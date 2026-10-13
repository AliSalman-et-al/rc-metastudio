"""Retain verified desktop bundles and selected audit screenshots locally."""

import hashlib
import json
import shutil
from pathlib import Path


root = Path(__file__).resolve().parents[3]
audit = Path(__file__).resolve().parent
artifacts = root / "artifacts/verification/rcms"
destination = audit / "evidence/finish"
destination.mkdir(parents=True, exist_ok=True)
screenshots = audit / "screenshots"
screenshots.mkdir(exist_ok=True)

# Older targeted native runs are preserved with their original revision/dirty
# state. They illustrate prior commits, not a claim that every run used final HEAD.
older = (
    "20261013T104652Z-f667b124-analysis-data-onearm-proportion",
    "20261013T104726Z-7d6411d6-analysis-amino-binary-cumulative",
    "20261013T104738Z-87b6fe35-analysis-amino-binary-meta-regression",
    "20261013T104716Z-a2ed5e07-analysis-diagnostic-joint",
    "20261013T104705Z-5c923b71-project-structure",
    "20261013T112707Z-668c2cd7-calculator-diagnostic",
    "20261013T111811Z-90f8d6c8-ratios-samples",
)
runs = sorted({
    *(artifacts / name for name in older),
    *(path for path in artifacts.iterdir()
      if path.name.startswith("20261013T")
      and path.name >= "20261013T122219Z"
      and (path / "manifest.json").is_file()),
})
rows = []
for source in runs:
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        file = source / entry["path"]
        assert hashlib.sha256(file.read_bytes()).hexdigest() == entry["sha256"], file
    target = destination / source.name
    if not target.exists():
        shutil.copytree(source, target)
    rows.append({
        "source": str(source),
        "local": target.relative_to(audit).as_posix(),
        "scenario": manifest["scenario"],
        "native": manifest["native_requested"],
        "head": manifest["head"],
        "tracked_diff_sha256": manifest["tracked_diff_sha256"],
        "passed": manifest["passed"],
        "exit_code": manifest.get("exit_code"),
        "manifest_sha256": hashlib.sha256((source / "manifest.json").read_bytes()).hexdigest(),
        "files_verified": len(manifest["files"]),
    })

ux = artifacts / "20261013T123948Z-9b58a195-ux-improvements"
onearm = artifacts / "20261013T124132Z-6d34ad0e-analysis-data-onearm-proportion"
aliases = {
    "empty-workspace": (ux, "02-0-ux-empty-workspace.png"),
    "quick-start": (ux, "03-0-ux-quick-start.png"),
    "analysis-setup": (ux, "05-0-analysis-configured.png"),
    "readable-report": (ux, "07-0-ux-readable-report.png"),
    "plot-toolbar": (ux, "08-0-ux-plot-toolbar.png"),
    "csv-cleared-required": (ux, "10-0-ux-csv-cleared-required.png"),
    "csv-cleared-exact-headers": (ux, "12-0-ux-csv-cleared-exact-headers.png"),
    "csv-recovered": (ux, "13-0-ux-csv-recovered.png"),
    "small-ratio-grid": (ux, "17-0-ux-small-ratio.png"),
    "covariate-error": (ux, "18-0-ux-covariate-error.png"),
    "mapped-reopened": (ux, "19-0-ux-mapped-reopened.png"),
    "report-200": (artifacts / "20261013T122942Z-b1a164c5-ux-improvements", "07-0-ux-readable-report.png"),
    "onearm-creation": (onearm, "02-0-data-type-selected.png"),
    "onearm-grid": (onearm, "03-0-data-populated.png"),
    "onearm-results": (onearm, "07-0-matrix-results.png"),
    "cumulative-setup": (artifacts / older[1], "03-0-matrix-configured.png"),
    "cumulative-results": (artifacts / older[1], "04-0-matrix-results.png"),
    "regression-results": (artifacts / older[2], "04-0-matrix-results.png"),
    "diagnostic-results": (artifacts / older[3], "05-0-matrix-results.png"),
    "structure-editor": (artifacts / older[4], "02-0-structure-draft.png"),
    "diagnostic-calculator": (artifacts / older[5], "03-0-calculator-accept.png"),
    "hr-results": (artifacts / older[6], "03-0-bundled-ratio-sample-metafor-comparison.png"),
    "irr-results": (artifacts / older[6], "09-0-bundled-ratio-sample-metafor-comparison.png"),
}
for scenario, alias in (("analysis-amino-binary-leave-one-out", "leave-one-out-results"),
                        ("analysis-amino-binary-subgroup", "subgroup-results")):
    candidates = [path for path in runs if path.name.endswith("-" + scenario)]
    aliases[alias] = (candidates[-1], "04-0-matrix-results.png")

image_rows = []
for alias, (source, name) in aliases.items():
    target = screenshots / (alias + ".png")
    shutil.copy2(source / name, target)
    image_rows.append({
        "screenshot": target.relative_to(audit).as_posix(),
        "source": str(source / name),
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    })

summary = {
    "runs": rows,
    "screenshots": image_rows,
    "new_desktop_runs": sum(path.name not in older for path in runs),
    "all_original_manifest_files_verified": True,
    "logs_sha256": {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(audit.glob("finish-*.log"))
    },
    "supplemental_native_mean_regression": {
        "local": "evidence-final/20261013T123233Z-supplemental-onearm-mean-meta-regression",
        "status": json.loads((audit / "evidence-final/20261013T123233Z-supplemental-onearm-mean-meta-regression/status.json").read_text()),
        "files_sha256": {
            file.relative_to(audit).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
            for file in sorted((audit / "evidence-final/20261013T123233Z-supplemental-onearm-mean-meta-regression").rglob("*"))
            if file.is_file()
        },
    },
}
(audit / "finish-evidence.json").write_text(
    json.dumps(summary, indent=2) + "\n", encoding="utf-8"
)
print(f"Verified/copied {len(rows)} runs and {len(image_rows)} selected screenshots.")
