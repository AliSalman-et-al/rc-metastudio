"""Assemble TSA review sheets and measure the retained render artifacts."""

import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent / "tsa-phase4"
sys.path.insert(0, str(PRIOR))
from review import CASES as PHASE4_CASES, STYLES, SVG, manifest, sheet, steps

CASES = {**PHASE4_CASES, "peto": "tsa-peto"}
WIDTHS = (89, 120, 174)


def number(node, key):
    return float(node.attrib[key].removesuffix("px"))


def style_number(node, key):
    return float(re.search(rf"{key}: ([0-9.]+)", node.attrib["style"])[1])


def text_box(node):
    size = style_number(node, "font-size")
    width = number(node, "textLength")
    anchor = {"start": 0, "middle": .5, "end": 1}[node.attrib.get("text-anchor", "start")]
    transform = node.attrib.get("transform")
    if transform:
        x, y = map(float, re.fullmatch(r"translate\(([^,]+),([^)]+)\) rotate\(-90\)", transform).groups())
        return x - .77*size, y - (1-anchor)*width, x + .23*size, y + anchor*width
    x, y = number(node, "x"), number(node, "y")
    return x - anchor*width, y - .77*size, x + (1-anchor)*width, y + .23*size


def artwork(path, case, print_width=None):
    svg = ET.parse(path).getroot()
    _, _, width, height = map(float, svg.attrib["viewBox"].split())
    text = list(svg.iter(SVG + "text"))
    labels = [node.text for node in text]
    xlabel = next(i for i, label in enumerate(labels) if label.startswith("Cumulative ") and "Z" not in label)
    tick_end = next(i for i in range(xlabel + 1, len(labels)) if labels[i].startswith("−"))
    ticks = labels[xlabel + 1:tick_end]
    panels = [node for node in svg.iter(SVG + "polyline")
              if "stroke: #333333;" in node.attrib.get("style", "")]
    assert panels, path
    group, = [group for group in svg.iter(SVG + "g") if panels[0] in list(group)]
    clip = group.attrib["clip-path"].removeprefix("url(#").removesuffix(")")
    panel = svg.find(f".//{SVG}clipPath[@id='{clip}']/{SVG}rect")
    left, top = number(panel, "x"), number(panel, "y")
    wide, tall = number(panel, "width"), number(panel, "height")
    panel_fraction = wide / width
    lines = list(svg.iter(SVG + "line"))
    ris, = [node for node in lines if "stroke: #8C8C8C;" in node.attrib.get("style", "")]
    conventional = [node for node in lines if "stroke: #A6A6A6;" in node.attrib.get("style", "")
                    and abs(number(node, "x1") - left) < .02]
    assert conventional and all(number(node, "x2") == number(ris, "x1") for node in conventional), path
    boxes = [text_box(node) for node in text]
    clipped = [label for label, (x, y, end, bottom) in zip(labels, boxes)
               if x < -.2 or y < -.2 or end > width + .2 or bottom > height + .2]
    overlaps = []
    for i, (x, y, end, bottom) in enumerate(boxes):
        for j, (a, b, c, d) in enumerate(boxes[:i]):
            if min(end, c) - max(x, a) > .6 and min(bottom, d) - max(y, b) > .6:
                overlaps.append(f"{labels[j]} | {labels[i]}")
    favours = [box for node, box in zip(text, boxes)
               if node.attrib.get("transform") and "fill: #4A4A4A;" in node.attrib["style"]]
    assert favours and max(box[2] for box in favours) < left, path
    rings = [node for node in svg.iter(SVG + "circle")
             if "stroke: #333333;" in node.attrib.get("style", "")]
    assert bool(rings) == (case != "md"), (case, path, rings)
    if case in ("bcg", "peto"):
        assert len(rings) == 1 and number(rings[0], "cy") > top + tall, path
    bubbles = [
        (2*number(node, "r") + style_number(node, "stroke-width"))/tall
        for node in svg.iter(SVG + "circle")
        if "fill-opacity:" in node.attrib.get("style", "")
        and left <= number(node, "cx") <= left + wide and top <= number(node, "cy") <= top + tall
    ]
    bubble_fraction = max(bubbles)
    assert bubble_fraction <= .061, (path, bubble_fraction)
    minimum_pt = min(style_number(node, "font-size") for node in text)
    minimum_line = min(style_number(node, "stroke-width") for node in svg.iter()
                       if "stroke-width:" in node.attrib.get("style", ""))
    assert 1 <= len(ticks) <= 6, (path, ticks)
    if print_width is not None:
        assert minimum_pt >= 6 and minimum_line >= .5, (path, minimum_pt, minimum_line)
    assert panel_fraction >= (.60 if print_width == 89 else .72), (path, panel_fraction)
    return (f"{width:.2f} × {height:.2f} pt", f"{panel_fraction:.1%}", " ".join(ticks),
            minimum_pt, minimum_line, f"{bubble_fraction:.1%}", " / ".join(clipped), " / ".join(overlaps))


def decode_print(directory, name, mm):
    with Image.open(directory / f"{name}.tiff") as raster:
        assert abs(raster.width - mm / 25.4 * 300) <= 1, (directory, name)
        assert raster.tag_v2[259] == 5 and abs(raster.info["dpi"][0] - 300) < .1, raster.info
        plot = raster.convert("RGB")
    svg = ET.parse(directory / f"{name}.svg").getroot()
    assert not list(svg.iter(SVG + "text")) and list(svg.iter(SVG + "path"))
    assert len(svg.attrib["viewBox"].split()) == 4, svg.attrib
    assert abs(float(svg.get("width").removesuffix("pt")) * 25.4 / 72 - mm) < .01, svg.attrib
    fonts = subprocess.check_output(["pdffonts", str(directory / f"{name}.pdf")], text=True).splitlines()[2:]
    assert fonts and all(row.split()[-5] == "yes" for row in fonts), fonts
    return plot


def main():
    proof = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "qualification")
    screenshots, audit = [], []
    plots, svg_bytes, printed, greyscale = {}, {}, {}, {}
    for scale in (100, 150):
        for case, scenario in CASES.items():
            run = proof / f"native{scale}" / scenario
            manifest(run)
            runtime = json.loads((run / "runtime.json").read_text(encoding="utf-8"))
            assert runtime["platform_plugin"] == "windows", runtime
            recorded = steps(run)
            for style in STYLES:
                name = f"{case}-{style}"
                action = f"tsa-{name}"
                event, = (step for step in recorded if step["action"] == action)
                dpr = event["dpi_scale"]
                assert abs(dpr - scale / 100) < .01, (name, scale, dpr)
                capture, = run.glob(f"*-0-{action}.png")
                screen = run / "workflow" / f"{name}-viewport.png"
                saved = run / "workflow" / f"{name}.svg"
                audit.append((f"native {scale}%", name, *artwork(saved, case)))
                if scale == 100:
                    svg_bytes[name] = saved.read_bytes()
                    for mm in WIDTHS:
                        directory = proof / "print" / str(mm)
                        audit.append((f"{mm} mm", name, *artwork(directory / f"{name}-geometry.svg", case, mm)))
                        printed[mm, case, style] = decode_print(directory, name, mm)
                        if style != "revman":
                            greyscale[mm, case, style] = ImageOps.grayscale(printed[mm, case, style])
                            greyscale[mm, case, style].save(directory / f"{name}-greyscale.png")
                else:
                    assert svg_bytes[name] == saved.read_bytes(), (scale, name)
                with Image.open(screen) as image:
                    plots[scale, case, style] = image.convert("RGB")
                screenshots.append((case, style, scale, dpr, capture.relative_to(ROOT).as_posix(),
                                    screen.relative_to(ROOT).as_posix()))

    with Image.open(proof / "print" / "peto-default-600.tiff") as raster:
        assert raster.tag_v2[259] == 5 and abs(raster.info["dpi"][0] - 600) < .1
    for name, header, rows in (
        ("screenshots", ("case", "style", "scale_percent", "observed_dpr", "window", "plot_crop"), screenshots),
        ("geometry", ("surface", "case-style", "size", "panel_width", "x_ticks", "min_font_pt",
                      "min_line_pt", "largest_bubble", "clipped_text", "overlapping_text"), audit),
    ):
        with (ROOT / f"{name}.csv").open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(header)
            writer.writerows(rows)
    for style in STYLES:
        sheet(ROOT / f"native-{style}.png", [
            (f"{case} at {scale}%", plots[scale, case, style])
            for case in CASES for scale in (100, 150)
        ], 2)
        sheet(ROOT / f"print-{style}.png", [
            (f"{case} at {mm} mm / 300 dpi", printed[mm, case, style])
            for case in CASES for mm in WIDTHS
        ], 3)
        if style != "revman":
            sheet(ROOT / f"greyscale-{style}.png", [
                *[(f"{case} at {scale}%", ImageOps.grayscale(plots[scale, case, style]))
                  for case in CASES for scale in (100, 150)],
                *[(f"{case} at {mm} mm", greyscale[mm, case, style]) for case in CASES for mm in WIDTHS],
            ], 3)
        with Image.open(PRIOR / f"contact-{style}.png") as original:
            page = original.convert("RGB")
        width, height = page.width // 2, page.height // 2
        page.paste("white", (0, 25, width, height))
        plot = ImageOps.contain(plots[100, "bcg", style], (width - 20, height - 34))
        page.paste(plot, ((width - plot.width) // 2, 25))
        page.save(ROOT / f"contact-{style}.png")
    issues = [row for row in audit if row[-1] or row[-2]]
    assert not issues, issues
    print("Verified 36 native captures and 54 print layouts with no text collisions or clipping.")
    print("Every print layout passed the PDF font, SVG outline, and 300 dpi LZW TIFF checks.")
    print("The 600 dpi LZW TIFF passed. The 18 SVG pairs match across native scales.")


if __name__ == "__main__":
    main()
