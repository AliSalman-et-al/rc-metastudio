"""Check publication PDF dimensions, text geometry, and BMJ analysis parity."""
import json
import os
from pathlib import Path
import sys

from pdfminer.high_level import extract_pages
from rc_metastudio.qt6_ui import prepare_generated_ui_imports

prepare_generated_ui_imports()
from tests.e2e.plot_export_print_sizes import pdf_observations

OUT = Path(os.environ["RCMS_PAPER_OUTPUT"])
EVIDENCE = OUT / "evidence" / "default-style"
PANELS = {
    "figure-3a-regression": "regression",
    "figure-3b-contour-funnel": "contour_funnel",
    "figure-4a-sroc": "sroc",
    "figure-4b-tsa": "trial_sequential",
}
COMPOSITES = ("figure-3-pairwise", "figure-4-diagnostic-sequential")
STYLE_FIELDS = {
    "bp_style", "bp_accent_color", "fp_style", "fp_accent_color",
    "fp_curve_color", "fp_confidence_color", "fp_prediction_color",
    "funnel.style", "funnel.point.symbol", "funnel.point.color",
    "funnel.reference.color", "funnel.region.color", "funnel.background.color",
}
PATH_FIELDS = {"bp_outpath", "bp_display_path", "fp_outpath", "fp_display_path", "funnel.outpath"}
ANALYSIS_EVENTS = {"sample", "analysis", "regression moderator", "small-study settings", "TSA design"}


def events(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.startswith("{")]


def compare_captures(current, baseline):
    current_samples = [i for i, event in enumerate(current) if event["event"] == "sample"]
    baseline_samples = [i for i, event in enumerate(baseline) if event["event"] == "sample"]
    baseline = baseline[baseline_samples[-len(current_samples)]:]
    assert [event for event in current if event["event"] in ANALYSIS_EVENTS] == [
        event for event in baseline if event["event"] in ANALYSIS_EVENTS
    ]
    editors = [{event["name"]: event for event in run if event["event"] == "plot editor"}
               for run in (current, baseline)]
    changes = {}
    for name in PANELS:
        default, bmj = (run[name] for run in editors)
        assert (default["style"], bmj["style"]) == ("default", "bmj")
        left, right = default["parameters"], bmj["parameters"]
        assert left.keys() == right.keys(), name
        changed = {key for key in left if left[key] != right[key]}
        assert changed <= STYLE_FIELDS | PATH_FIELDS, (name, changed)
        changes[name] = sorted(changed - PATH_FIELDS)
    funnel = editors[0]["figure-3b-contour-funnel"]["parameters"]
    return {
        "changed_style_fields": changes,
        "funnel_center_log_rr": funnel["funnel.center"],
        "funnel_contour_levels": funnel["funnel.contour.levels"][1],
        "funnel_prepared_log_rr": funnel["prepared.effects"],
        "funnel_prepared_se": funnel["prepared.standard.errors"],
    }


def main(bmj_log):
    current = events(EVIDENCE / "capture.log")
    units_per_inch = {"cm": 2.54, "mm": 25.4, "in": 1}
    proposals = {}
    for event in current:
        if event["event"] == "export on open":
            factor = units_per_inch[event["units"]]
            height, _ = event["height"].split()
            proposals[event["name"]] = (event["width"] / factor, float(height) / factor)
    assert set(proposals) == set(PANELS), proposals
    observations = {}
    failures = []
    for name in (*PANELS, *COMPOSITES):
        path = OUT / f"{name}.pdf"
        page, = extract_pages(path)
        width, height = proposals.get(name, (page.width / 72, page.height / 72))
        observed = pdf_observations(path, width, height, PANELS.get(name, ""))
        if name in proposals:
            observed["dialog_mm"] = [round(value * 25.4, 3) for value in (width, height)]
        observed["page_mm"] = [round(value * 25.4 / 72, 3) for value in observed["page_pt"]]
        observations[name] = observed
        if (name in PANELS and observed["min_font_pt"] < 6) or observed["outside"] or observed["overlaps"]:
            failures.append(name)
    print(json.dumps({
        "observations": observations,
        "bmj_parity": compare_captures(current, events(bmj_log)),
        "failures": failures,
    }, indent=2, ensure_ascii=False))
    return bool(failures)


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
