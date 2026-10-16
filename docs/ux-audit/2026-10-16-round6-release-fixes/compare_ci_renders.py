"""Compare retained c62df31/current native frames and rasterized SVG figures."""
import hashlib
import json
import os
from pathlib import Path
import sys

from PIL import Image, ImageChops
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = HERE / "raw/lexer"
os.environ["QT_QPA_PLATFORM"] = "offscreen"
app = QGuiApplication([])


def evidence(label):
    receipt = json.loads((RAW / "raw" / (label + ".json")).read_text())
    assert receipt["exit_code"] == 0, label
    lines = (RAW / "raw" / receipt["log"]).read_text().splitlines()
    path = Path(next(line.removeprefix("Evidence: ") for line in lines if line.startswith("Evidence: ")))
    manifest = json.loads((path / "manifest.json").read_text())
    assert manifest["passed"], path
    return path


def raster(path):
    renderer = QSvgRenderer(str(path))
    assert renderer.isValid(), path
    size = renderer.defaultSize()
    image = QImage(size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return Image.frombytes("RGBA", (size.width(), size.height()), bytes(image.constBits().asarray(image.sizeInBytes())), "raw", "BGRA").convert("RGB")


def compare(before, after, svg):
    a = raster(before) if svg else Image.open(before).convert("RGB")
    b = raster(after) if svg else Image.open(after).convert("RGB")
    bbox = ImageChops.difference(a, b).getbbox() if a.size == b.size else "different dimensions"
    return {"before": str(before.relative_to(ROOT)), "after": str(after.relative_to(ROOT)),
            "before_sha256": hashlib.sha256(before.read_bytes()).hexdigest(),
            "after_sha256": hashlib.sha256(after.read_bytes()).hexdigest(),
            "before_size": a.size, "after_size": b.size,
            "pixel_identical": bbox is None, "difference_bbox": bbox}


def captured_paths(folder):
    paths = {}
    for line in (folder / "steps.jsonl").read_text().splitlines():
        step = json.loads(line)
        for name in step["captures"]:
            paths[name] = folder / name
        for title, name in step["artifacts"].items():
            suffix = Path(name).suffix.lower()
            if suffix in {".svg", ".png"}:
                paths[f'{step["step"]}:{title}{suffix}'] = folder / name
    return paths


rows = []
for scenario in sys.argv[1:]:
    before = evidence(("before3-" if scenario == "review1-design" else "before2-") + scenario)
    after = evidence("after-" + scenario)
    assert json.loads((before / "manifest.json").read_text())["head"].startswith("c62df31")
    old_paths = captured_paths(before)
    new_paths = captured_paths(after)
    assert old_paths.keys() == new_paths.keys(), (scenario, old_paths.keys() ^ new_paths.keys())
    comparisons = [compare(old_paths[name], new_paths[name], name.endswith(".svg")) for name in sorted(old_paths)]
    plots = [item for name, item in zip(sorted(old_paths), comparisons) if ":" in name]
    native = [item for name, item in zip(sorted(old_paths), comparisons) if ":" not in name]
    counts = {
        "scenario": scenario, "pairs": len(comparisons), "plot_pairs": len(plots),
        "svg_pairs": sum(item["before"].endswith(".svg") for item in plots),
        "raster_pairs": sum(item["before"].endswith(".png") for item in plots),
        "pixel_identical_plot_pairs": sum(item["pixel_identical"] for item in plots),
        "native_pairs": len(native),
        "pixel_identical_native_pairs": sum(item["pixel_identical"] for item in native),
    }
    rows.append({"scenario": scenario, "before_manifest": str((before / "manifest.json").relative_to(ROOT)),
                 "after_manifest": str((after / "manifest.json").relative_to(ROOT)), "comparisons": comparisons,
                 "counts": counts})
report = {"baseline": "c62df31", "rasterizer": "Qt QSvgRenderer at SVG defaultSize; opaque white RGB", "families": rows}
report["counts"] = {key: sum(row["counts"][key] for row in rows)
                    for key in rows[0]["counts"] if key != "scenario"}
(HERE / "CI-VISUAL-COMPARISON.json").write_text(json.dumps(report, indent=2) + "\n")
for row in rows:
    changed = [r for r in row["comparisons"] if not r["pixel_identical"]]
    print(row["scenario"], len(row["comparisons"]), "pairs;", len(changed), "differ")
    for item in changed:
        print(item["before"], item["difference_bbox"])
