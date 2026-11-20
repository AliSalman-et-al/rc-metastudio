from pathlib import Path
from xml.etree import ElementTree as ET
import sys

root = Path(sys.argv[1])
ns = "{http://www.w3.org/2000/svg}"
receipts = []
for source in sorted(root.glob("funnel-ref-*.svg")):
    svg = ET.parse(source)
    texts = [node.text for node in svg.iter(ns + "text")]
    fills = [node.attrib["points"] for node in svg.iter(ns + "polygon")
             if "fill: #" in node.get("style", "")]
    ticks = tuple(v for v in texts if v in {"0.25", "0.5", "0.50", "1", "1.00", "2", "2.00"})
    panels = tuple((node.attrib["width"], node.attrib["height"]) for node in svg.iter(ns + "rect")
                   if node.attrib.get("x") and node.attrib.get("y"))
    assert fills and len(ticks) >= 4 and panels, (source, ticks, panels)
    receipts.append((fills, ticks, panels))
    print(source.name, ticks, [line for line in texts if "displayed bounds" in line][0])
assert len(receipts) == 4
assert all(receipt == receipts[0] for receipt in receipts)
print("Region vertices, axis ticks and panel bounds are identical for all four toggle combinations.")
for file, keys in (("contour_funnel.svg", ("P > 0.10", "0.05 < P ≤ 0.10", "0.01 < P ≤ 0.05", "P ≤ 0.01")),
                   ("trimfill_funnel.svg", ("Observed", "Imputed"))):
    svg = ET.parse(root / file)
    texts = {node.text for node in svg.iter(ns + "text")}
    assert set(keys) <= texts, (file, texts)
    print(file, *keys, sep=" | ")
    clips = {f"url(#{clip.attrib['id']})": clip[0].attrib for clip in svg.iter(ns + "clipPath")}
    parents = {child: node for node in svg.iter() for child in node}
    panel = next(rect.attrib for rect in svg.iter(ns + "rect") if
                 rect.get("style", "").startswith("stroke-width:") and rect.get("x"))
    fills = [polygon for polygon in svg.iter(ns + "polygon") if
             "fill: #" in polygon.get("style", "") and len(polygon.get("points", "")) > 100]
    assert fills
    for polygon in fills:
        clipping = clips[parents[polygon].attrib["clip-path"]]
        assert all(clipping[key] == panel[key] for key in ("x", "y", "width", "height"))
    print(f"{len(fills)} filled polygons clipped to the exact panel rectangle")
