"""Copy before/after surfaces for visual review; leave complete bundles intact."""
import hashlib
import json
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
specs = [
    ("binary-forest", "matrix-twoarm-proportion-standard-figure.png", "amino-bottom", "*results.png"),
    ("binary-axis", "matrix-twoarm-proportion-standard-figure.png", "amino-bottom", "*results-bottom.png"),
    ("continuous-forest", "matrix-twoarm-mean-standard-figure.png", "analysis-data-twoarm-mean-bottom", "*results.png"),
    ("single-arm-forest", "matrix-onearm-proportion-standard-figure.png", "analysis-data-onearm-proportion-bottom", "*results.png"),
    ("generic-heading", "matrix-generic-effect-standard-figure.png", "analysis-data-generic-effect", "*results.png"),
    ("coefficient-heading", "matrix-reg-coef-standard-figure.png", "analysis-data-reg-coef", "*results.png"),
    ("cumulative", "matrix-twoarm-proportion-cumulative-figure.png", "analysis-amino-binary-cumulative-bottom", "*results-bottom.png"),
    ("leave-one-out", "matrix-twoarm-proportion-leave-one-out-figure.png", "analysis-amino-binary-leave-one-out-bottom", "*results-bottom.png"),
    ("subgroup-report", "matrix-twoarm-proportion-subgroup-report.png", "analysis-amino-binary-subgroup-bottom", "*results-report.png"),
    ("subgroup-figure", "matrix-twoarm-proportion-subgroup-figure.png", "analysis-amino-binary-subgroup-bottom", "*results-bottom.png"),
    ("regression", "matrix-twoarm-proportion-meta-regression-figure.png", "analysis-amino-binary-meta-regression-bottom", "*results-bottom.png"),
    ("diagnostic-moderators", "diagnostic-regression-multiple-figure.png", "analysis-diagnostic-regression-multiple-bottom", "*results-bottom.png"),
    ("clinical-summary", "diagnostic-joint-report.png", "analysis-diagnostic-joint-complete", "*results-report.png"),
    ("sroc", "diagnostic-joint-figure.png", "analysis-diagnostic-joint-complete", "*results-figure.png"),
    ("diagnostic-methods", "diagnostic-combined-report.png", "analysis-diagnostic-combined", "*results-report.png"),
    ("report", "14-binary-text-report.png", "amino-bottom", "*results-report.png"),
    ("native-table", "14-binary-text-report.png", "amino-bottom", "*results-table.png"),
    ("csv-entry", "61-csv-instructions-top--modal1.png", "ux-improvements", "*ux-csv-page-entry.png"),
    ("zoom", "zoom-report-after-fit.png", "ux-improvements", "*ux-independent-view-zoom.png"),
    ("workspace", "08-binary-grid.png", "ux-improvements", "*ux-header-geometry.png"),
    ("empty-workspace", "06-empty-workspace.png", "ux-improvements", "*ux-empty-workspace.png"),
    ("diagnostic-calculator", "calculator-diagnostic.png", "calculator-diagnostic", "*calculator-before.png"),
    ("continuous-calculator", "calculator-continuous.png", "calculator-continuous", "*calculator-before.png"),
    ("structure", "42-structure-covariates-empty--modal1.png", "project-structure", "*structure-draft.png"),
]
out = HERE / "screenshots"
out.mkdir(exist_ok=True)
rows = []
for area, old_name, suffix, pattern in specs:
    old = HERE.parent / "2026-10-13-reaudit/screenshots" / old_name
    assert old.is_file(), old
    logs = [p for p in HERE.glob("*native-" + suffix + ".log")
            if p.name.startswith(("after-final-", "after-label-"))]
    logs.sort(key=lambda p: p.stat().st_mtime)
    assert logs, suffix
    log = logs[-1]
    record = json.loads(log.with_suffix(".json").read_text())
    assert record["exit_code"] == 0, record
    bundle = Path(re.search(r"^Evidence: (.+)$", log.read_text(), re.M).group(1).strip())
    candidates = sorted(bundle.glob(pattern))
    assert candidates, (bundle, pattern)
    new = candidates[0]
    for phase, source in (("before", old), ("after", new)):
        destination = out / f"{area}-{phase}.png"
        shutil.copy2(source, destination)
        rows.append(dict(area=area, phase=phase, path=str(destination.relative_to(HERE)),
                         source=str(source.relative_to(ROOT)),
                         sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                         provenance="Native re-audit before round two" if phase == "before" else str(log.name),
                         inspection="pending"))
(HERE / "SCREENSHOTS.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
print(f"Retained {len(rows)} before/after images for review.")
