from pathlib import Path
from PIL import Image
from xml.etree import ElementTree
import sys

folder = Path(sys.argv[1])
plots = list(folder.glob("*.png"))
assert len(plots) == 300, len(plots)
for path in plots:
    with Image.open(path) as image:
        image.load()
    ElementTree.parse(path.with_suffix(".svg"))
print("300 PNG files decoded and 300 SVG files parsed.")
