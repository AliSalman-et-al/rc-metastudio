"""Measure the physical size of the files produced by the native export drive."""
import argparse
import csv
import gzip
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image
from PyQt6.QtCore import QCoreApplication, QSize
from PyQt6.QtPdf import QPdfDocument


def pdf_size(path: Path, renders: Path) -> tuple[float, float]:
    document = QPdfDocument(None)
    assert document.load(str(path)) == QPdfDocument.Error.None_, path
    assert document.pageCount() == 1
    size = document.pagePointSize(0)
    page = document.render(0, QSize(round(size.width() * 2), round(size.height() * 2)))
    assert page.save(str(renders / (path.stem + "-white.png")))
    return size.width() * 25.4 / 72, size.height() * 25.4 / 72


def size_mm(value: str) -> float:
    for suffix, factor in (("in", 25.4), ("mm", 1.0), ("cm", 10.0), ("pt", 25.4 / 72)):
        if value.endswith(suffix):
            return float(value.removesuffix(suffix)) * factor
    raise ValueError(value)


def dimensions(path: Path, renders: Path) -> tuple[float, float]:
    if path.suffix == ".pdf":
        return pdf_size(path, renders)
    if path.suffix in (".svg", ".svgz"):
        opener = gzip.open if path.suffix == ".svgz" else open
        with opener(path, "rb") as stream:
            root = ET.parse(stream).getroot()
        return size_mm(root.attrib["width"]), size_mm(root.attrib["height"])
    with Image.open(path) as image:
        dpi_x, dpi_y = image.info["dpi"]
        return image.width * 25.4 / dpi_x, image.height * 25.4 / dpi_y


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("evidence", type=Path)
parser.add_argument("destination", type=Path)
args = parser.parse_args()
app = QCoreApplication([])
renders = args.destination.parent / "white-paper"
renders.mkdir(exist_ok=True)
receipts = json.loads((args.evidence / "workflow" / "export-sizes.json").read_text())
failures = []
with args.destination.open("w", newline="", encoding="utf-8") as stream:
    writer = csv.writer(stream)
    writer.writerow(("plot", "format", "requested width (mm)", "requested height (mm)",
                     "actual width (mm)", "actual height (mm)", "within 0.5 mm"))
    for receipt in receipts:
        path = args.evidence / "workflow" / receipt["file"]
        requested = (receipt["width"] * 25.4, receipt["height"] * 25.4)
        actual = dimensions(path, renders)
        passed = all(abs(a - b) <= .5 for a, b in zip(requested, actual))
        writer.writerow((receipt["kind"], path.suffix[1:], *map(lambda x: round(x, 3), (*requested, *actual)), passed))
        if not passed:
            failures.append(path)
assert not failures, failures
