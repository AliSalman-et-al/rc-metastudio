"""Verify band placement against the actual displayed SVG study labels."""
import csv
from pathlib import Path
import re
import sys
from xml.etree import ElementTree as ET

directory = Path(sys.argv[1])
namespace = "{http://www.w3.org/2000/svg}"
results = []
for path in sorted(directory.glob("[0-9]*.svg")):
    root = ET.parse(path).getroot()
    rectangles = [
        (float(rect.attrib["y"]), float(rect.attrib["height"]))
        for rect in root.iter(namespace + "rect")
        if "fill: #EEEEEE" in rect.get("style", "")
    ]
    labels = sorted(
        (float(node.attrib["y"]), node.text)
        for node in root.iter(namespace + "text")
        if node.text and " / " not in node.text and (re.search(r",? [12][0-9]{3}$", node.text) or node.text == "All studies")
    )
    subgroup = "subgroup_forest" in path.name
    banded = subgroup or "-default-" in path.name
    checked = []
    if banded:
        expected_count = 6 if subgroup else 14 if "leave_one_out" in path.name else 13
        assert len(labels) == expected_count, (path, labels)
        for index, (y, label) in enumerate(labels):
            shaded = any(top < y < top + height for top, height in rectangles)
            expected = (index % 3 if subgroup else index) % 2 == 0
            assert shaded == expected, (path, label, expected, shaded)
            checked.append(label if shaded else "")
        assert len(rectangles) == sum(bool(label) for label in checked), path
    else:
        assert not rectangles, path
    results.append((path.name, len(labels), len(rectangles), " | ".join(filter(None, checked))))
assert len(results) == 36, len(results)
with Path(sys.argv[2]).open("w", newline="", encoding="utf-8") as target:
    writer = csv.writer(target)
    writer.writerow(("plot", "displayed rows", "grey bands", "shaded labels"))
    writer.writerows(results)


