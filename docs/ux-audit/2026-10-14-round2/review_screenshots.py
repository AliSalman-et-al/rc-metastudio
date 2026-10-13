"""Copy selected, unmodified native screenshots from a completed NATIVE.ps1 run."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
SELECTION = {
    "amino": {"binary-default": "04-0-analysis-results.png",
              "report-top": "04-0-analysis-results-report.png",
              "binary-summary": "04-0-analysis-results-bottom.png"},
    "continuous": {"continuous-default": "04-0-analysis-results.png"},
    "analysis-data-onearm-proportion": {"single-arm-default": "07-0-matrix-results.png"},
    "analysis-amino-binary-subgroup": {"subgroup-default": "04-0-matrix-results.png",
                                       "subgroup-difference": "04-0-matrix-results-bottom.png"},
    "analysis-amino-binary-cumulative": {"cumulative": "04-0-matrix-results.png",
                                         "cumulative-summary": "04-0-matrix-results-bottom.png"},
    "analysis-amino-binary-leave-one-out": {"leave-one-out": "04-0-matrix-results.png",
                                            "omission-summary": "04-0-matrix-results-bottom.png"},
    "analysis-amino-binary-meta-regression": {"bubble": "04-0-matrix-results.png"},
    "analysis-diagnostic-joint": {"diagnostic-summary": "05-0-matrix-results.png"},
    "analysis-data-twoarm-mean": {"continuous-raw": "07-0-matrix-results.png"},
    "review-workflows": {"properties": "05-0-review-properties-prefilled.png",
                         "settings-rerun": "15-0-review-settings-rerun.png",
                         "cumulative-order": "16-0-review-cumulative-order.png",
                         "study-order": "07-0-review-study-order-year.png",
                         "study-order-options": "08-1-review-study-order-options.png"},
    "plot-workflow-forest": {"direction-fields": "07-0-family-editor-controls.png"},
}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("prefix", help="NATIVE.ps1 -LabelPrefix")
args = parser.parse_args()
manifest = []
for scenario, pictures in SELECTION.items():
    suffix = "raw" if scenario == "analysis-data-twoarm-mean" else scenario
    label = f"{args.prefix}-{suffix}"
    record = json.loads((HERE / "raw" / f"{label}.json").read_text())
    assert record["exit_code"] == 0, label
    log_bytes = (HERE / "raw" / record["log"]).read_bytes()
    assert hashlib.sha256(log_bytes).hexdigest() == record["sha256"], label
    log = log_bytes.decode("utf-8")
    evidence = next(line.removeprefix("Evidence: ") for line in log.splitlines()
                    if line.startswith("Evidence: "))
    for name, filename in pictures.items():
        source = Path(evidence) / filename
        if not source.is_file():
            matches = list(Path(evidence).glob("*-" + filename.split("-", 2)[2]))
            assert len(matches) == 1, (label, filename, matches)
            source = matches[0]
        target = HERE / "screenshots" / f"review1-{name}.png"
        shutil.copyfile(source, target)
        manifest.append(dict(file=target.name, source=str(source),
                             sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                             revision=record["revision"]))
(HERE / "raw" / "curated-review1.json").write_text(json.dumps(manifest, indent=2))
print(f"Copied {len(manifest)} untouched native screenshots; inspect each before committing.")
