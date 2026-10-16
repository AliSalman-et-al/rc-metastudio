"""Decode every maintained forest-matrix artifact and retain observed dimensions."""
import csv
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image
from xml.etree import ElementTree

directory = Path(sys.argv[1]).resolve()
rows = list(csv.DictReader((directory / "manifest.csv").open()))
assert len(rows) == 300, len(rows)
assert len({row["case"] for row in rows}) == 300
observed = []
for row in rows:
    assert row["error"] in {"", "NA"}, row
    path = Path(row["image"])
    assert path.stat().st_size == int(row["bytes"]) > 0, row
    with Image.open(path) as image:
        image.load()
        if image.mode != "RGB":
            image = image.convert("RGB")
        assert image.width > 100 and image.height > 100, row
        assert any(minimum < 255 for minimum, maximum in image.getextrema()), row
        dimensions = [image.width, image.height]
    svg = Path(row["svg"])
    document = ElementTree.parse(svg).getroot()
    assert document.tag.endswith("}svg"), row
    assert any(node.tag.endswith("}text") for node in document.iter()), row
    assert max(dimensions) <= 2400, row
    observed.append(dict(case=row["case"], dimensions=dimensions, bytes=path.stat().st_size,
                         svg_sha256=hashlib.sha256(svg.read_bytes()).hexdigest(),
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
record = dict(passed=True, cases=len(rows), manifest=str(directory / "manifest.csv"),
              manifest_sha256=hashlib.sha256((directory / "manifest.csv").read_bytes()).hexdigest(),
              observed=observed)
Path(__file__).with_name("FOREST-MATRIX.json").write_text(json.dumps(record, indent=2) + "\n")
print("300 unique forest cases; no errors; all images decoded with visible nonwhite content.")
