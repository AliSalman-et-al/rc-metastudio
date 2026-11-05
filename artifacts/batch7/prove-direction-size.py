"""Check the actual saved SVG direction and axis tick font sizes."""
from pathlib import Path
from xml.etree import ElementTree as ET
import json
import re

rows = []
for scenario in ("after-continuous", "after-amino"):
    source = next((Path(__file__).parent / "receipts" / scenario).glob("*.svg"))
    texts = list(ET.parse(source).iter("{http://www.w3.org/2000/svg}text"))
    directions = [n for n in texts if "".join(n.itertext()).startswith("Favours")]
    numbers = [n for n in texts if re.fullmatch(r"[-−+\d.,eE]+", "".join(n.itertext()))]
    tick_y = max(float(n.attrib["y"]) for n in numbers)
    ticks = [n for n in numbers if float(n.attrib["y"]) == tick_y]
    def size(node):
        return float(re.search(r"font-size:\s*([\d.]+)px", node.attrib["style"])[1])
    assert directions and ticks
    assert all(size(n) == size(ticks[0]) for n in directions)
    rows.append(dict(scenario=scenario, direction_px=[size(n) for n in directions],
                     tick_px=size(ticks[0]), svg=str(source)))
Path(__file__).with_name("direction-size-proof.json").write_text(json.dumps(rows, indent=2) + "\n")
