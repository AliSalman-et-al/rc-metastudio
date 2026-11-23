# SPDX-License-Identifier: GPL-3.0-or-later
"""Adapt R's rectangular SVG clips for Qt without changing exported artwork."""

import gzip
import io
import re
from pathlib import Path
from typing import BinaryIO, cast
from xml.etree import ElementTree as ET

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QTransform


_FONT_STACK = re.compile(r"""(font-family\s*:\s*)("[^"]*"|'[^']*'|[^,;}]+)\s*,[^;}]+""", re.IGNORECASE)


def _open_svg(path: str | Path) -> BinaryIO | gzip.GzipFile:
    return gzip.open(path, "rb") if str(path).lower().endswith(".svgz") else open(path, "rb")


def svg_bytes_for_qt(path: str | Path) -> bytes:
    with _open_svg(path) as source:
        svg = source.read()
    if b"clip-path" not in svg and b"font-family" not in svg.lower():
        return svg

    namespace = "http://www.w3.org/2000/svg"
    root = ET.fromstring(svg)
    _normalize_font_stacks(root, namespace)
    _normalize_canvas_size(root, namespace)
    clips = _rectangular_clips(root, namespace)
    groups = [(parent, node) for parent in root.iter() for node in parent
              if node.tag == f"{{{namespace}}}g" and node.get("clip-path") in clips
              and "transform" not in node.attrib]
    for index, (parent, node) in enumerate(groups):
        _clip_group(parent, node, clips[node.get("clip-path")], index, namespace)
    ET.register_namespace("", namespace)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    return ET.tostring(root, encoding="utf-8")


def svg_text_points_per_inch(path: str | Path, height_per_width: float) -> float:
    """Measure the smallest SVG font against the physical export viewport."""
    with _open_svg(path) as source:
        svg = source.read()
    view_width, view_height = _view_box_size(io.BytesIO(svg))
    sizes = map(float, re.findall(rb"font-size:\s*([\d.]+)px", svg))
    return min(sizes, default=0.0) * 72 * min(1 / view_width, height_per_width / view_height)


def svg_view_box_size(path: str | Path) -> tuple[float, float]:
    with _open_svg(path) as source:
        return _view_box_size(source)


def plot_text_layout_issue(path: Path) -> str | None:
    """Check text written by svglite using the device's measured advances."""
    root = ET.parse(path).getroot()
    canvas = QRectF(*map(float, root.attrib["viewBox"].split())).adjusted(-.5, -.5, .5, .5)
    boxes: list[QRectF] = []
    for node in root.iter("{http://www.w3.org/2000/svg}text"):
        size = re.search(r"font-size:\s*([\d.]+)px", node.get("style", ""))
        length = node.get("textLength")
        if size is None or length is None or not (node.text or "").strip():
            continue
        font = float(size[1])
        if font < 6:
            return "The smallest text is below 6 pt."
        width = float(length.removesuffix("px"))
        offset = {"middle": width / 2, "end": width}.get(node.get("text-anchor", ""), 0)
        bounds = QRectF(-offset, -.74 * font, width, .94 * font)
        transform = re.fullmatch(r"translate\(([-\d.]+),\s*([-\d.]+)\) rotate\(([-\d.]+)\)",
                                 node.get("transform", ""))
        if transform:
            x, y, degrees = map(float, transform.groups())
            bounds = QTransform.fromTranslate(x, y).rotate(degrees).mapRect(bounds)
        else:
            bounds.translate(float(node.get("x", "0")), float(node.get("y", "0")))
        if not canvas.contains(bounds):
            return f"‘{node.text}’ extends beyond the figure."
        for other in boxes:
            intersection = bounds.intersected(other)
            if intersection.width() * intersection.height() > .2 * min(
                bounds.width() * bounds.height(), other.width() * other.height()
            ):
                return f"‘{node.text}’ overlaps other text."
        boxes.append(bounds)
    return None


def _view_box_size(source: BinaryIO | gzip.GzipFile) -> tuple[float, float]:
    with_root = ET.iterparse(source, events=("start",))
    _, root = cast(tuple[str, ET.Element], next(with_root))
    _, _, width, height = map(float, root.attrib["viewBox"].replace(",", " ").split())
    return width, height


def _normalize_font_stacks(root: ET.Element, namespace: str) -> None:
    def primary(match: re.Match[str]) -> str:
        return match[1] + match[2].strip(" \"'")

    for node in root.iter():
        if style := node.get("style"):
            node.set("style", _FONT_STACK.sub(primary, style))
        if family := node.get("font-family"):
            node.set("font-family", _FONT_STACK.sub(primary, f"font-family:{family}").partition(":")[2])
        if node.tag == f"{{{namespace}}}style" and node.text:
            node.text = _FONT_STACK.sub(primary, node.text)


def _normalize_canvas_size(root: ET.Element, namespace: str) -> None:
    if view_box := root.get("viewBox"):
        _, _, canvas_width, canvas_height = view_box.split()
        for canvas in root.findall(f"{{{namespace}}}g[@class='svglite']/{{{namespace}}}rect"):
            for attribute, extent in (("width", canvas_width), ("height", canvas_height)):
                if canvas.get(attribute) == "100%":
                    canvas.set(attribute, extent)


def _rectangular_clips(root, namespace):
    clips = {}
    for clip in root.iter(f"{{{namespace}}}clipPath"):
        children = list(clip)
        if (len(children) != 1 or children[0].tag != f"{{{namespace}}}rect"
                or clip.get("clipPathUnits", "userSpaceOnUse") != "userSpaceOnUse"
                or "transform" in clip.attrib or "transform" in children[0].attrib):
            continue
        clips[f"url(#{clip.get('id')})"] = children[0].attrib
    return clips


def _clip_group(parent, node, rectangle, index, namespace):
    node.attrib.pop("clip-path")
    x, y = rectangle.get("x", "0"), rectangle.get("y", "0")
    width, height = rectangle["width"], rectangle["height"]
    if float(width) <= 0 or float(height) <= 0:
        parent.remove(node)
        return
    identifier = f"rcms-clip-{index}"
    symbol = ET.Element(f"{{{namespace}}}symbol", {
        "id": identifier, "viewBox": f"0 0 {width} {height}",
        "width": width, "height": height, "overflow": "hidden",
    })
    translated = ET.SubElement(symbol, f"{{{namespace}}}g", {
        "transform": f"translate({-float(x)},{-float(y)})",
    })
    position = list(parent).index(node)
    parent.remove(node)
    translated.append(node)
    parent.insert(position, symbol)
    parent.insert(position + 1, ET.Element(f"{{{namespace}}}use", {
        "{http://www.w3.org/1999/xlink}href": f"#{identifier}",
        "x": x, "y": y, "width": width, "height": height,
    }))
