"""Compare complete decoded TIFF pixels in bounded strips, including DPI."""
import json
from pathlib import Path
import sys

from PIL import Image, ImageChops

before, after = map(Path, sys.argv[1:3])
with Image.open(before) as first, Image.open(after) as second:
    assert first.size == second.size
    dpi = tuple(map(float, first.info["dpi"]))
    assert dpi == tuple(map(float, second.info["dpi"])) == (600., 600.)
    maximum = 0
    for y in range(0, first.height, 128):
        box = (0, y, first.width, min(y + 128, first.height))
        difference = ImageChops.difference(first.crop(box).convert("RGB"), second.crop(box).convert("RGB"))
        maximum = max(maximum, max(high for low, high in difference.getextrema()))
    assert maximum <= 1, maximum
    record = dict(dimensions=first.size, dpi=dpi, maximum_8bit_channel_difference=maximum,
                  pixels_compared=first.width * first.height,
                  compression_before=first.info["compression"], compression_after=second.info["compression"])
Path(__file__).with_name("TIFF-PIXELS.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record))
