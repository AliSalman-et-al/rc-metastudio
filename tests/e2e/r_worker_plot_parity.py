"""Compare saved publication files produced by embedded R and the R worker."""

import gzip
import json
from math import ceil
import os
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from PIL import Image, ImageChops
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtPdf import QPdfDocument

from rc_metastudio import r_bridge
from rc_metastudio.results.export_files import staged_output
from rc_metastudio.results.plot_service import PlotService, svg_view_box_size
from rc_metastudio.results.report import ManuscriptReport, write_docx, write_pdf
from tests.analysis_regression.golden.support import golden_analysis, headless_analysis


def run(_app, window, work, _root, record, _analyze):
    r_bridge.load_required_packages()
    cases = compare_golden(work / "golden-publication-files")
    record("golden-publication-parity", window, cases=cases)


def compare_golden(output):
    evidence = {}
    for case in golden_analysis.curated_golden_bundles():
        files = {}
        for backend in ("embedded", "worker"):
            with patch.dict(os.environ, {"RCMS_R_BACKEND": backend}):
                result = headless_analysis.run_headless_analysis(case["case"])
                files[backend] = export_result(result, output / case["id"] / backend)
        evidence[case["id"]] = compare_outputs(files["embedded"], files["worker"])
    (output / "comparisons.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence


def export_result(result, directory):
    directory.mkdir(parents=True, exist_ok=True)
    report = ManuscriptReport.from_result(result)
    files = {}
    service = PlotService()
    for index, figure in enumerate(report.figures):
        if figure.capability is None or figure.capability.regenerator == "none" or not figure.plot_data:
            continue
        regenerator = figure.capability.regenerator
        width, height = svg_view_box_size(figure.display_image or figure.value)
        extensions = ("svg", "png", "tiff", "pdf") if regenerator == "funnel" else ("svg", "svgz", "png", "tiff", "pdf")
        for extension in extensions:
            destination = directory / f"{index}-{figure.plot_kind}.{extension}"
            service.export_sized(
                regenerator=regenerator, params_path=figure.plot_data,
                output_path=str(destination), width=width / 72, height=height / 72, dpi=96,
            )
            files[destination.name] = destination
    for extension, write in (("docx", write_docx), ("pdf", write_pdf)):
        destination = directory / f"report.{extension}"
        write(report, destination)
        files[destination.name] = destination
    return files


def compare_outputs(embedded, worker):
    assert embedded.keys() == worker.keys()
    return {name: compare_file(embedded[name], worker[name]) for name in embedded}


def compare_file(embedded, worker):
    try:
        if embedded.read_bytes() == worker.read_bytes():
            return "identical bytes"
        match embedded.suffix:
            case ".svg":
                compare_svg(embedded.read_bytes(), worker.read_bytes())
            case ".svgz":
                compare_svg(gzip.decompress(embedded.read_bytes()), gzip.decompress(worker.read_bytes()))
            case ".pdf":
                _compare_pdf(embedded, worker)
            case ".docx":
                _compare_docx(embedded, worker)
            case ".png" | ".tiff":
                with Image.open(embedded) as left, Image.open(worker) as right:
                    assert left.size == right.size and left.info.get("dpi") == right.info.get("dpi")
                    assert ImageChops.difference(left.convert("RGB"), right.convert("RGB")).getbbox() is None
            case _:
                raise AssertionError("Unknown export format")
    except AssertionError as error:
        error.add_note(f"Comparing {embedded} and {worker}")
        raise
    return "identical rendered content"


def compare_svg(left, right):
    def attributes(source):
        root = ET.fromstring(source)
        ids = {node.attrib["id"]: f"figure-id-{index}" for index, node in enumerate(root.iter()) if "id" in node.attrib}
        for node in root.iter():
            if "id" in node.attrib:
                node.attrib["id"] = ids[node.attrib["id"]]
            for key, value in node.attrib.items():
                if value.startswith("url(#") and value.endswith(")") and value[5:-1] in ids:
                    node.attrib[key] = f"url(#{ids[value[5:-1]]})"
                elif key.endswith("href") and value.startswith("#") and value[1:] in ids:
                    node.attrib[key] = "#" + ids[value[1:]]
        return ET.canonicalize(ET.tostring(root, encoding="unicode"))

    assert attributes(left) == attributes(right)


def _compare_pdf(embedded, worker):
    left, right = QPdfDocument(None), QPdfDocument(None)
    assert left.load(str(embedded)) == right.load(str(worker)) == QPdfDocument.Error.None_
    assert left.pageCount() == right.pageCount() > 0
    for page in range(left.pageCount()):
        assert left.pagePointSize(page) == right.pagePointSize(page)
        size = left.pagePointSize(page).toSize().scaled(QSize(600, 800), Qt.AspectRatioMode.KeepAspectRatio)
        assert left.render(page, size) == right.render(page, size), page


def _compare_docx(embedded, worker):
    with ZipFile(embedded) as left, ZipFile(worker) as right:
        assert sorted(left.namelist()) == sorted(right.namelist())
        for name in left.namelist():
            if name.endswith(".svg"):
                compare_svg(left.read(name), right.read(name))
            else:
                assert left.read(name) == right.read(name), name


def oversized_svg(source, destination):
    """Convert an SVG larger than the protocol limit using its path only."""
    large = destination.with_suffix(".svg")
    comments = (b"<!--" + b" " * 1024**2 + b"-->\n") * 16
    large.write_bytes(comments + source.read_bytes().split(b"?>", 1)[-1])
    assert large.stat().st_size > 16 * 1024**2
    width, height = svg_view_box_size(large)
    with staged_output(destination) as temporary:
        r_bridge.export_svg_artwork(str(large), str(temporary), width / 72, height / 72, 72)
    with Image.open(destination) as image:
        assert image.size == (ceil(width), ceil(height))
        image.verify()
    return large.stat().st_size
