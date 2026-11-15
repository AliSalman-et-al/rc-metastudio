# SPDX-License-Identifier: GPL-3.0-or-later
"""Adapt R's rectangular SVG clips for Qt without changing exported artwork."""

import gzip
from pathlib import Path
from xml.etree import ElementTree as ET


def svg_bytes_for_qt(
    path: str | Path, clip_bounds: tuple[float, float, float, float] | None = None
) -> bytes:
    opener = gzip.open if str(path).lower().endswith(".svgz") else open
    with opener(path, "rb") as source:
        svg = source.read()
    if b"clip-path" not in svg:
        return svg

    namespace = "http://www.w3.org/2000/svg"
    root = ET.fromstring(svg)
    # Qt treats svglite's percentage canvas as 100 SVG units, not the viewBox.
    _, _, canvas_width, canvas_height = root.attrib["viewBox"].split()
    for canvas in root.findall(f"{{{namespace}}}g[@class='svglite']/{{{namespace}}}rect"):
        for attribute, extent in (("width", canvas_width), ("height", canvas_height)):
            if canvas.get(attribute) == "100%":
                canvas.set(attribute, extent)
        if clip_bounds is not None:
            for attribute, value in zip(("x", "y", "width", "height"), clip_bounds):
                canvas.set(attribute, str(value))
    clips = {}
    for clip in root.iter(f"{{{namespace}}}clipPath"):
        children = list(clip)
        if (len(children) != 1 or children[0].tag != f"{{{namespace}}}rect"
                or clip.get("clipPathUnits", "userSpaceOnUse") != "userSpaceOnUse"
                or "transform" in clip.attrib or "transform" in children[0].attrib):
            continue
        clips[f"url(#{clip.get('id')})"] = children[0].attrib
    groups = [(parent, node) for parent in root.iter() for node in parent
              if node.tag == f"{{{namespace}}}g" and node.get("clip-path") in clips
              and "transform" not in node.attrib]
    for index, (parent, node) in enumerate(groups):
        rectangle = clips[node.attrib.pop("clip-path")]
        x, y = rectangle.get("x", "0"), rectangle.get("y", "0")
        width, height = rectangle["width"], rectangle["height"]
        if clip_bounds is not None:
            left, top, span, extent = clip_bounds
            right = min(float(x) + float(width), left + span)
            bottom = min(float(y) + float(height), top + extent)
            x, y = str(max(float(x), left)), str(max(float(y), top))
            width, height = str(right - float(x)), str(bottom - float(y))
        if float(width) <= 0 or float(height) <= 0:
            parent.remove(node)
            continue
        identifier = f"rcms-clip-{index}"
        # Qt ignores clipPath, but clips symbol viewports with QPainter. Keep
        # that viewport at the origin, then translate back to R's coordinates.
        # Unlike SVG masks, this stays vector at print resolution and high zoom.
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
    ET.register_namespace("", namespace)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    return ET.tostring(root, encoding="utf-8")
