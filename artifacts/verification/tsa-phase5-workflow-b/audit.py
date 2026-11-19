"""Check the retained native run receipts and the BCG PDF's numeric columns."""

import json
import re
import sys
from hashlib import sha256
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).parent / (sys.argv[1] if len(sys.argv) > 1 else "delivery")
CASES = ("doctor", "plot-workflow-trial-sequential", "tsa-hr", "tsa-md", "tsa-rr-mh", "tsa-smd", "tsa-stress")
NS = "{http://www.w3.org/1999/xhtml}"


def step(directory, action):
    matches = [entry for line in (directory / "steps.jsonl").read_text(encoding="utf-8").splitlines()
               if (entry := json.loads(line))["action"] == action]
    result, = matches
    return result


def audit_bcg_pdf(directory, table):
    report, = (directory / "workflow/reports").iterdir()
    pages = ElementTree.parse(report / "pdf-bbox.xhtml").iter(NS + "page")
    page, = [list(page.iter(NS + "word")) for page in pages
             if any(word.text == "1,232,589" for word in page.iter(NS + "word"))]
    clipboard = (report / "copy.html").read_text(encoding="utf-8")
    columns = [table["headers"].index(header) for header in
               ("OR", "RRR", "Required information size", "Accrued (% of required)")]
    positions = {table["headers"][column]: [] for column in columns}
    for row in table["rows"]:
        size, = [word for word in page if word.text == row[columns[2]]]
        line = [word for word in page if word.attrib["yMin"] == size.attrib["yMin"]]
        for column in columns:
            value = row[column]
            # The scenario labels also contain a percentage to the left of RRR.
            word = max((word for word in line if word.text == value),
                       key=lambda word: float(word.attrib["xMax"]))
            positions[table["headers"][column]].append(float(word.attrib["xMax"]))
            assert re.search(r'<p align="right"[^>]*>' + re.escape(value) + r'</p>', clipboard), value
    for header, edges in positions.items():
        assert max(edges) - min(edges) < 0.01, (header, edges)
    print(f"  BCG PDF right edges (points): {positions}")


for target in (100, 150):
    print(f"Native {target}%")
    for case in CASES:
        directory = ROOT / f"native{target}" / case
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        runtime = json.loads((directory / "runtime.json").read_text(encoding="utf-8"))
        assert manifest["passed"] and manifest["exit_code"] == 0 and manifest["native_requested"], case
        assert runtime["platform_plugin"] == "windows", case
        for file in manifest["files"]:
            artifact = directory / file["path"]
            assert sha256(artifact.read_bytes()).hexdigest() == file["sha256"], artifact
        if case in ("plot-workflow-trial-sequential", "tsa-hr"):
            preview = step(directory, "tsa-configured")
            timings = step(directory, "tsa-preview-timings")
            assert preview["dpi_scale"] == target / 100
            print(f"  {case}: {preview['conclusion']} · editor x={preview['editor_x'][0]} · "
                  f"{timings['median_ms']:.2f} ms RIS median · {timings['conclusion_elapsed_ms']:.2f} ms conclusion")
        if case in ("plot-workflow-trial-sequential", "tsa-hr", "tsa-md"):
            preview = step(directory, "tsa-configured")
            assert preview["dpi_scale"] == target / 100
            assert len(set(preview["editor_x"])) == 1
            table = step(directory, "tsa-sensitivity-report")
            print(f"  {case}: {table['headers']} · {table['captures']}")
            if case == "plot-workflow-trial-sequential":
                audit_bcg_pdf(directory, table)
    print(f"  {len(CASES)} successful manifests and artifact hashes verified")
