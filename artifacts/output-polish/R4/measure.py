from pathlib import Path
from xml.etree import ElementTree as ET

root = Path(__file__).resolve().parents[1]
namespace = "{http://www.w3.org/2000/svg}"

def nodes(path):
    return list(ET.parse(path).iter(namespace + "text"))

def width(node):
    return float(node.attrib["textLength"].removesuffix("px"))

for metric, step in (("RR", "04"), ("RD", "08")):
    old = nodes(root / f"F7/after/{metric}-bmj-preview.svg")
    assert not any(node.text == "Favours BCG vaccine" for node in old)
    visible = nodes(next((root / "R3/after").glob(f"{step}-0-*.svg")))
    left = next(node for node in visible if node.text == "Favours BCG vaccine")
    right = next(node for node in visible if node.text == "Favours Control")
    axis = float(right.attrib["x"]) - float(left.attrib["x"])
    assert max(width(left), width(right)) <= axis / 2
    gap = axis - width(left) - width(right)
    assert gap > 0
    print(f"{metric}: half-axis {axis / 2:.2f}, left label {width(left):.2f}, right label {width(right):.2f}, gap {gap:.2f} SVG units")

visible = nodes(next((root / "R3/after").glob("05-0-*.svg")))
starts = [node for node in visible if node.text == "Favours the longer"]
assert len(starts) == 2
blocks = [[node for node in visible if node.get("x") == start.get("x")
           and float(node.get("y")) >= float(start.get("y"))
           and "font-weight: bold" in node.get("style", "")] for start in starts]
assert all(len(block) > 1 for block in blocks)
assert all("name" in " ".join(node.text for node in block) for block in blocks)
print("Long labels wrap to " + " and ".join(str(len(block)) for block in blocks) + " lines.")
