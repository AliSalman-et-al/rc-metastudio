import csv
import json
from pathlib import Path
import re
import sys
from xml.etree import ElementTree as ET


destination, *evidence = map(Path, sys.argv[1:])
with destination.open("w", newline="", encoding="utf-8") as output:
    writer = csv.writer(output)
    writer.writerow(("plot", "width (mm)", "minimum SVG font (pt)", "warning shown"))
    for run in evidence:
        workflow = run / "workflow"
        for receipt in json.loads((workflow / "export-sizes.json").read_text(encoding="utf-8")):
            if not receipt["file"].endswith(".svg"):
                continue
            path = workflow / receipt["file"]
            drawing = ET.parse(path).getroot()
            _, _, view_width, view_height = map(float, drawing.attrib["viewBox"].split())
            factor = min(receipt["width"] * 72 / view_width, receipt["height"] * 72 / view_height)
            fonts = map(float, re.findall(r"font-size:\s*([\d.]+)px", path.read_text(encoding="utf-8")))
            smallest = min(fonts, default=None)
            writer.writerow((receipt["kind"], round(receipt["width"] * 25.4, 2),
                             round(smallest * factor, 2) if smallest is not None else "outlined text",
                             receipt["warning"]))
