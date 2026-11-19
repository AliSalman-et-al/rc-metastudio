"""Audit merged TSA captures and assemble the native and print contact sheets."""

import csv
from html import unescape
import json
from pathlib import Path
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET

from docx import Document
from PIL import Image

PRIOR = Path(__file__).resolve().parents[1] / "tsa-phase5b"
sys.path.insert(0, str(PRIOR))
from contact_sheets import (CASES, STYLES, SVG, WIDTHS, artwork, check_triangles,
                            decode_print, manifest, number, sheet, steps)


def ring_diameter(path):
    svg = ET.parse(path).getroot()
    circles = list(svg.iter(SVG + "circle"))
    ring, = (node for node in circles if "stroke: #333333;" in node.get("style", ""))
    diameter = 2 * number(ring, "r")
    for bubble in circles:
        if bubble is not ring and all(bubble.get(k) == ring.get(k) for k in ("cx", "cy")):
            assert diameter >= 1.35 * 2 * number(bubble, "r") - .03, path
    return diameter


def check_report(run, output):
    note = "Marker area is proportional to the information each trial added."
    workflow = run / "workflow"
    report, = (workflow / "reports").glob("*/audit.json")
    folder = report.parent
    audit = json.loads(report.read_text(encoding="utf-8"))
    assert len(audit["presented"]) == 2
    document = Document(str(folder / "report.docx"))
    assert len(document.tables) == 2 and document.inline_shapes
    assert sum(note in paragraph.text for paragraph in document.paragraphs) == 1
    # The PDF includes the note in its text summary and on the figure page.
    for name, count in (("copy.txt", 1), ("pdf.txt", 2)):
        text = " ".join((folder / name).read_text(encoding="utf-8").split())
        assert text.count(note) == count, name
        assert "Table 2." in text, name
    copied_html = unescape((folder / "copy.html").read_text(encoding="utf-8"))
    assert note in " ".join(copied_html.split())
    primary = audit["presented"][0]
    with (workflow / "bcg-1-formatted.csv").open(encoding="utf-8-sig", newline="") as file:
        assert list(csv.reader(file)) == [primary["headers"], *primary["rows"]]
    with (workflow / "bcg-1-values.csv").open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
        observed = [(row["Column"], row["Quantity"], float(row["Value"]) if row["Value"] else None)
                    for row in rows]
        expected = [(header, quantity["role"], quantity["value"])
                    for line in primary["quantities"] for header, cell in zip(primary["headers"], line)
                    for quantity in cell]
        assert observed == expected
    subprocess.run(["pdftoppm", "-r", "110", "-png", str(folder / "report.pdf"),
                    str(output / "bcg-report")], check=True)
    namespace = "{http://www.w3.org/1999/xhtml}"
    pages = list(ET.parse(folder / "pdf-bbox.xhtml").iter(namespace + "page"))
    caption_copies = 0
    for i, page in enumerate(pages, 1):
        with Image.open(output / f"bcg-report-{i}.png") as image:
            for word in page.iter(namespace + "word"):
                if word.text != "Marker":
                    continue
                caption_copies += 1
                box = tuple(round(float(word.get(key)) * 110 / 72)
                            for key in ("xMin", "yMin", "xMax", "yMax"))
                assert image.crop(box).convert("L").getextrema()[0] < 128, ("Invisible PDF note", i)
    assert caption_copies == 2
    retained = output / "report"
    retained.mkdir(exist_ok=True)
    for name in ("report.pdf", "report.docx", "copy.html", "audit.json", "pdf-bbox.xhtml"):
        shutil.copyfile(folder / name, retained / name)
    for name in ("bcg-1-formatted.csv", "bcg-1-values.csv"):
        shutil.copyfile(workflow / name, retained / name)
    print(f"Opened BCG PDF, DOCX, copied HTML and both CSV exports from {folder}")


def main(proof):
    output = proof / "review"
    output.mkdir(exist_ok=True)
    native, printed = {}, {}
    rings = []
    revisions = set()
    for scale in (100, 150):
        for case, scenario in CASES.items():
            run = proof / f"native{scale}" / scenario
            manifest(run)
            revisions.add(json.loads((run / "manifest.json").read_text(encoding="utf-8"))["head"])
            runtime = json.loads((run / "runtime.json").read_text(encoding="utf-8"))
            assert runtime["platform_plugin"] == "windows", runtime
            recorded = steps(run)
            for style in STYLES:
                name = f"{case}-{style}"
                event, = (step for step in recorded if step["action"] == f"tsa-{name}")
                assert abs(event["dpi_scale"] - scale / 100) < .01, event
                svg = run / "workflow" / f"{name}.svg"
                assert not any(artwork(svg, case)[-2:]), svg
                if case != "md":
                    diameter = ring_diameter(svg)
                    assert diameter >= .16 * 72 - .02, (svg, diameter)
                    rings.append((scale, name, diameter / 72))
                with Image.open(run / "workflow" / f"{name}-viewport.png") as image:
                    native[scale, case, style] = image.convert("RGB")
            if case == "bcg":
                actions = {step["action"]: step for step in recorded}
                assert actions["tsa-configured"]["conclusion"]
                assert actions["tsa-change-settings-result"]["same_window"]
                assert not actions["tsa-change-settings-result"]["project_dirty"]
        manifest(proof / f"native{scale}" / "tsa-smd")
    revision, = revisions
    print(f"Native plot captures all use source revision {revision}.")
    with (output / "ring-diameters.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(("device scale percent", "case-style", "SVG diameter inches"))
        writer.writerows(rings)
    before = ring_diameter(PRIOR / "peto-axis-participants.svg") / 72
    after = next(diameter for scale, name, diameter in rings if scale == 100 and name == "peto-default")
    assert before < .16 <= after
    print(f"Peto Default crossing diameter: {before:.4f} in before, {after:.4f} in merged.")
    off_panel = sorted((proof / "print" / "off-panel").glob("*.svg"))
    assert len(off_panel) == 12
    for svg in off_panel:
        check_triangles(ET.parse(svg).getroot(), svg)
        assert ring_diameter(svg) >= .16 * 72 - .02, svg
    with Image.open(proof / "print" / "peto-default-600.tiff") as raster:
        assert raster.tag_v2[259] == 5 and abs(raster.info["dpi"][0] - 600) < .1
    for style in STYLES:
        for case in CASES:
            for mm in WIDTHS:
                directory = proof / "print" / str(mm)
                name = f"{case}-{style}"
                svg = directory / f"{name}-geometry.svg"
                assert not any(artwork(svg, case, mm)[-2:]), svg
                if case != "md":
                    assert ring_diameter(svg) >= .16 * 72 - .02, svg
                printed[mm, case, style] = decode_print(directory, name, mm)
        sheet(output / f"native-{style}.png", [
            (f"{case} at {scale}%", native[scale, case, style])
            for case in CASES for scale in (100, 150)
        ], 2)
        sheet(output / f"print-{style}.png", [
            (f"{case} at {mm} mm / 300 dpi", printed[mm, case, style])
            for case in CASES for mm in WIDTHS
        ], 3)
    print("Checked 36 native captures, 54 print layouts and 12 off-panel layouts.")
    check_report(proof / "native100" / CASES["bcg"], output)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
