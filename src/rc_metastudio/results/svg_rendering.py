# SPDX-License-Identifier: GPL-3.0-or-later
"""Adapt R's rectangular SVG clips for Qt without changing exported artwork."""

import gzip
import re
from pathlib import Path
from xml.etree import ElementTree as ET


_FONT_STACK = re.compile(r"""(font-family\s*:\s*)("[^"]*"|'[^']*'|[^,;}]+)\s*,[^;}]+""", re.IGNORECASE)


def svg_bytes_for_qt(path: str | Path) -> bytes:
    opener = gzip.open if str(path).lower().endswith(".svgz") else open
    with opener(path, "rb") as source:
        svg = source.read()
    if b"clip-path" not in svg and b"font-family" not in svg.lower():
        return svg

    namespace = "http://www.w3.org/2000/svg"
    root = ET.fromstring(svg)
    # Qt resolves a bare family name and can then apply its own glyph fallback.
    def primary(match: re.Match[str]) -> str:
        return match[1] + match[2].strip(" \"'")

    for node in root.iter():
        if style := node.get("style"):
            node.set("style", _FONT_STACK.sub(primary, style))
        if family := node.get("font-family"):
            node.set("font-family", _FONT_STACK.sub(primary, f"font-family:{family}").partition(":")[2])
        if node.tag == f"{{{namespace}}}style" and node.text:
            node.text = _FONT_STACK.sub(primary, node.text)
    # Qt treats svglite's percentage canvas as 100 SVG units, not the viewBox.
    if view_box := root.get("viewBox"):
        _, _, canvas_width, canvas_height = view_box.split()
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
