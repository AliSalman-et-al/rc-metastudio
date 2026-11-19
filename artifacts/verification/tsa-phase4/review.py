from __future__ import annotations

import csv
import hashlib
from io import BytesIO
import json
import os
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps
from PyQt6.QtCore import QBuffer, QIODevice, QRectF, QSize, Qt
from PyQt6.QtGui import QGuiApplication, QImage, QPainter
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtSvg import QSvgRenderer
from rc_metastudio.svg_rendering import svg_bytes_for_qt

ROOT = Path(__file__).resolve().parent
CASES = {
    "bcg": "plot-workflow-trial-sequential",
    "hr": "tsa-hr",
    "md": "tsa-md",
    "rr-mh": "tsa-rr-mh",
    "stress": "tsa-stress",
}
STYLES = ("default", "revman", "bmj")
SVG = "{http://www.w3.org/2000/svg}"


def pil(qimage: QImage) -> Image.Image:
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert qimage.save(buffer, "PNG")
    return Image.open(BytesIO(bytes(buffer.data()))).convert("RGB")


def render(file: Path, width: int = 1000) -> Image.Image:
    if file.suffix == ".pdf":
        pdf = QPdfDocument(None)
        assert pdf.load(str(file)) == QPdfDocument.Error.None_
        assert pdf.pageCount() == 1
        page = pdf.pagePointSize(0)
        return pil(pdf.render(0, QSize(width, round(width * page.height() / page.width()))))
    if file.suffix == ".svg":
        svg = QSvgRenderer(svg_bytes_for_qt(file))
        assert svg.isValid(), file
        page = svg.viewBoxF()
        canvas = QImage(width, round(width * page.height() / page.width()), QImage.Format.Format_RGB32)
        canvas.fill(Qt.GlobalColor.white)
        painter = QPainter(canvas)
        svg.render(painter, QRectF(canvas.rect()))
        painter.end()
        return pil(canvas)
    with Image.open(file) as raster:
        return raster.convert("RGB")


def manifest(run: Path) -> None:
    record = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    assert record["passed"] and record["exit_code"] == 0, run
    for entry in record["files"]:
        path = run / entry["path"]
        with path.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == entry["sha256"], path


def steps(run: Path):
    return [json.loads(line) for line in (run / "steps.jsonl").read_text(encoding="utf-8").splitlines()]


def ink_difference(a: Image.Image, b: Image.Image) -> float:
    a, b = (
        ImageOps.invert(ImageOps.grayscale(image.resize((520, 280), Image.Resampling.LANCZOS)))
        .filter(ImageFilter.GaussianBlur(1.2))
        for image in (a, b)
    )
    delta, ink = (sum(tone * n for tone, n in enumerate(image.histogram()))
                  for image in (ImageChops.difference(a, b), ImageChops.lighter(a, b)))
    return delta / ink


def legend_fits(path: Path) -> None:
    svg = ET.parse(path).getroot()
    _, _, width, _ = map(float, svg.attrib["viewBox"].split())
    for label in svg.iter(SVG + "text"):
        if "x" not in label.attrib:
            continue  # The native captures show the rotated margin labels.
        x = float(label.attrib["x"])
        size = float(label.attrib["textLength"].removesuffix("px"))
        left = x - size * {"end": 1, "middle": .5, "start": 0}[label.attrib.get("text-anchor", "start")]
        assert left >= 0 and left + size <= width, (path, label.text, left, left + size, width)


def sheet(path: Path, panels: list[tuple[str, Image.Image]], columns: int, cell=(740, 420)) -> None:
    width, height = cell
    rows = (len(panels) + columns - 1) // columns
    page = Image.new("RGB", (columns * width, rows * height), "white")
    draw = ImageDraw.Draw(page)
    for i, (label, image) in enumerate(panels):
        x, y = i % columns * width, i // columns * height
        draw.text((x + 16, y + 9), label, fill="black")
        fitted = ImageOps.contain(image, (width - 20, height - 34))
        page.paste(fitted, (x + (width - fitted.width) // 2, y + 25))
    page.save(path)


def main() -> None:
    os.environ["QT_QPA_PLATFORM"] = "windows"
    app = QGuiApplication([])
    proof = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "qualification")
    screenshots = []
    audit = []
    compare = {}
    plots = {}
    artwork = {}
    for scale in (100, 150):
        for case, scenario in CASES.items():
            directory = proof / f"native{scale}" / scenario
            manifest(directory)
            runtime = json.loads((directory / "runtime.json").read_text(encoding="utf-8"))
            assert runtime["platform_plugin"] == "windows", runtime
            recorded = steps(directory)
            for style in STYLES:
                name = f"{case}-{style}"
                action = f"tsa-{name}"
                record, = [step for step in recorded if step["action"] == action]
                observed = record["dpi_scale"]
                assert abs(observed - scale/100) < .01, (name, scale, observed)
                capture, = directory.glob(f"*-0-{action}.png")
                screen = directory / "workflow" / f"{name}-viewport.png"
                saved = directory / "workflow" / f"{name}.svg"
                legend_fits(saved)
                screenshots.append((case, style, scale, observed, capture.relative_to(ROOT).as_posix(),
                                    screen.relative_to(ROOT).as_posix()))
                plots[scale, case, style] = render(screen)
                if scale == 100:
                    artwork[name] = saved.read_bytes()
                    exports = directory / "workflow" / "design-exports"
                    compare[case, style] = []
                    for ext in ("svg", "png", "pdf", "tiff"):
                        path = exports / f"{name}.{ext}"
                        output = render(path)
                        native = plots[scale, case, style]
                        aspect = output.width / output.height / (native.width / native.height)
                        error = ink_difference(native, output)
                        audit.append((case, style, ext, aspect, error, path.relative_to(ROOT).as_posix()))
                        compare[case, style].append((ext.upper(), output))
                else:
                    assert artwork[name] == saved.read_bytes(), f"SVG changed with display scale for {name}"
    manifest(proof / "native100" / "tsa-smd")
    with (ROOT / "screenshots.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(("case", "style", "scale_percent", "observed_dpr", "window", "plot_crop"))
        writer.writerows(screenshots)
    with (ROOT / "export-comparison.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(("case", "style", "format", "relative_aspect", "relative_ink_difference", "file"))
        writer.writerows(audit)
    review = ROOT / "review"
    review.mkdir(exist_ok=True)
    for style in STYLES:
        sheet(review / f"native-{style}.png", [
            (f"{case} at {scale}%", plots[scale, case, style]) for case in CASES for scale in (100, 150)
        ], 2)
        sheet(review / f"exports-{style}.png", [
            panel for case in CASES
            for panel in [(f"{case} screen (100%)", plots[100, case, style]), *compare[case, style]]
        ], 5, cell=(465, 270))

    related = proof / "plots"
    for scenario in ("regression", "trimfill", "sroc", "forest"):
        manifest(related / f"plot-workflow-{scenario}")
    regression = related / "plot-workflow-regression"
    trimfill = related / "plot-workflow-trimfill" / "workflow"
    forest = related / "plot-workflow-forest" / "workflow"
    for style in STYLES:
        examples = [
            step for step in steps(regression)
            if step["action"] == "bubble-visible-legend" and step["style"].lower() == style
            and step["line"] and not step["confidence"]
        ]
        step, = examples
        bubble, = step["artifacts"].values()
        forest_label = {"default": "Default", "revman": "RevMan", "bmj": "BMJ"}[style]
        forest_svg = forest / f"forest-{forest_label}-arms-12.svg"
        sheet(ROOT / f"contact-{style}.png", [
            ("Trial sequential analysis", plots[100, "bcg", style]),
            ("Meta-regression bubble", render(regression / bubble)),
            ("Trim-and-fill funnel", render(trimfill / f"trimfill-{style}.svg")),
            ("Forest", render(forest_svg)),
        ], 2)
    assert all(.985 < aspect < 1.015 and error < .36 for _, _, _, aspect, error, _ in audit), audit
    print(f"Checked {len(screenshots)} native captures, {len(audit)} exported files and three style contact sheets")
    app.quit()


if __name__ == "__main__":
    main()
