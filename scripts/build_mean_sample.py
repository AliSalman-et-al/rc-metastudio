"""Build the published one-arm handgrip example."""

import json

from build_clinical_samples import SAMPLES, project, sheet, update_manifest


def main():
    source = "abe2025.json"
    retained = json.loads((SAMPLES / "sources" / source).read_text(encoding="utf-8"))
    rows = [
        (r["study"], r["year"], [[r["n"], r["mean"], r["sd"]]], [r["device"], r["hand"]],
         f"{r['check']} DOI {r['doi']}", {})
        for r in retained["rows"]
    ]
    item = project(
        "Single-arm mean", "Handgrip strength in young adults, Abe 2025",
        "Abe T, Song JS, Dankel SJ, Viana RB, Abe A, Loenneke JP. Impact of potential moderating factors on absolute test-retest reliability of grip strength measurements in healthy populations: a systematic review with meta-analysis. J Sports Sci Med. 2025;24:543–554.",
        retained["doi"], "pooling measured grip strength in kilograms from one cohort per study.",
        source, "The dynamometers, testing protocols and populations differ. One cohort consists of trained male basketball players. The pooled mean is an instructional example only. Values use the kilogram-force (kg) scale of the dynamometers.",
        [sheet(0, "First-session handgrip strength (kg)", "continuous", "mean", "Mean",
               ["Young adult volunteers"], rows, [("Dynamometer", 4), ("Tested hand", 4)])],
    )
    update_manifest([item])


if __name__ == "__main__":
    main()
