# SPDX-License-Identifier: GPL-3.0-or-later
"""Adapt R's rectangular SVG clips for Qt without changing exported artwork."""

import gzip
import re
from pathlib import Path
from xml.etree import ElementTree as ET


def svg_bytes_for_qt(path: str | Path) -> bytes:
    opener = gzip.open if str(path).lower().endswith(".svgz") else open
    with opener(path, "rb") as source:
        svg = source.read()
    if b"clip-path" not in svg and b"Segoe UI Symbol" not in svg:
        return svg

    namespace = "http://www.w3.org/2000/svg"
    root = ET.fromstring(svg)
    # Qt resolves a bare family name and can then apply its own glyph fallback.
    for node in root.iter(f"{{{namespace}}}text"):
        style = node.get("style", "")
        if "Segoe UI Symbol" in style:
            node.set("style", re.sub(r"font-family:\s*([^;]+)",
                lambda match: "font-family: " + match[1].split(",", 1)[0].strip(" \"'"), style))
    # Qt treats svglite's percentage canvas as 100 SVG units, not the viewBox.
    _, _, canvas_width, canvas_height = root.attrib["viewBox"].split()
    for canvas in root.findall(f"{{{namespace}}}g[@class='svglite']/{{{namespace}}}rect"):
        for attribute, extent in (("width", canvas_width), ("height", canvas_height)):
            if canvas.get(attribute) == "100%":
                canvas.set(attribute, extent)
    clips = _rectangular_clips(root, namespace)
    groups = [(parent, node) for parent in root.iter() for node in parent
              if node.tag == f"{{{namespace}}}g" and node.get("clip-path") in clips
              and "transform" not in node.attrib]
    for index, (parent, node) in enumerate(groups):
        _clip_group(parent, node, clips[node.get("clip-path")], index, namespace)
    ET.register_namespace("", namespace)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    return ET.tostring(root, encoding="utf-8")


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
