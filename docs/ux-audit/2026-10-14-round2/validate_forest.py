"""Fail on matrix omissions/errors and decode every rendered PNG."""
import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys
import warnings

from PIL import Image

# Trusted QA stress canvases exceed the soft pixel limit; keep Pillow's hard limit.
warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)

root, output = map(Path, sys.argv[1:])
with (root / "manifest.csv").open(newline="", encoding="utf-8") as stream:
    rows = list(csv.DictReader(stream))
expected = set(itertools.product(
    ("binary_two_arm", "binary_one_arm", "continuous_two_arm", "continuous_one_arm", "diagnostic"),
    ("standard", "cumulative", "leave-one-out", "subgroup"),
    ("default", "revman", "bmj"),
    ("base", "stress", "compact", "sparse", "direct"),
))
assert len(rows) == 300
assert {(r["kind"], r["workflow"], r["style"], r["scenario"]) for r in rows} == expected
images = []
for row in rows:
    assert row["error"] in ("", "NA"), row
    path = Path(row["image"])
    assert path.stat().st_size == int(row["bytes"]), row["case"]
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        image.load()
        assert image.format == "PNG" and min(image.size) > 0
        size = image.size
    images.append(dict(case=row["case"], sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                       width=size[0], height=size[1], bytes=path.stat().st_size))
output.write_text(json.dumps(dict(passed=True, count=len(images), images=images), indent=2))
print("300 complete matrix cases; 0 renderer errors; 300 PNGs fully decoded and hash-bound.")
