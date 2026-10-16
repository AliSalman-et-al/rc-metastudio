"""Compare real artifact metrics with the pre-optimization implementation."""
import importlib.util
import json
from pathlib import Path
import subprocess

from PIL import Image

HERE = Path(__file__).resolve().parent
path = Path("r/RCMetaR/inst/qa/forest_contact_sheets.py")
spec = importlib.util.spec_from_file_location("contact_metrics", path)
current = importlib.util.module_from_spec(spec)
spec.loader.exec_module(current)
old = {}
exec(subprocess.check_output(["git", "show", "b768ffc:" + str(path)], text=True), old)
files = sorted((HERE / "screenshots").glob("*.png"))
blank = HERE / "raw/blank.png"
Image.new("RGB", (300, 200), "white").save(blank)
observed = []
for image in [*files, blank]:
    row = {"image": str(image)}
    before = old["image_metrics"](row)
    after = current.image_metrics(row)
    assert before == after, (image, before, after)
    observed.append(after)
(HERE / "CONTACT-METRICS.json").write_text(json.dumps({"equal": True, "cases": observed}, indent=2) + "\n")
print(f"{len(observed)} before/after metric dictionaries match exactly, including blank image.")
