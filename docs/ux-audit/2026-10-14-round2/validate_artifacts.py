"""Decode retained forest images and bind installed/source verification artifacts."""
import csv
import hashlib
import json
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

matrices = []
for folder in ("forest-visual", "forest-visual-final"):
    manifest = HERE / folder / "manifest.csv"
    rows = list(csv.DictReader(manifest.open(encoding="utf-8")))
    assert len(rows) == 300
    files = []
    for row in rows:
        assert row["error"] in ("NA", ""), row
        path = Path(row["image"])
        assert path.stat().st_size == int(row["bytes"])
        with Image.open(path) as image:
            image.load()
            assert image.width > 100 and image.height > 100
            dimensions = [image.width, image.height]
        files.append(dict(case=row["case"], path=str(path.relative_to(ROOT)),
                          sha256=sha(path), dimensions=dimensions))
    matrices.append(dict(folder=folder, passed=True, case_count=300,
                         manifest_sha256=sha(manifest), files=files))
(HERE / "FOREST-VALIDATION.json").write_text(json.dumps(matrices, indent=2), encoding="utf-8")
library = ROOT / "build/verification/round2-r-library/RCMetaR"
installed = [dict(path=str(path.relative_to(ROOT)), sha256=sha(path))
             for path in sorted(library.rglob("*")) if path.is_file()]
checks = ROOT / "build/verification/round2-package-check"
files = [path for path in checks.rglob("*") if path.is_file() and
         (path.name in ("00check.log", "testthat.Rout") or path.suffix == ".gz")]
(HERE / "INSTALLED-SOURCE.json").write_text(json.dumps(dict(
    install_record="install-handoff.json", installed_files=installed,
    source_files=[dict(path=str(path.relative_to(ROOT)), sha256=sha(path))
                  for path in sorted((ROOT / "r/RCMetaR/R").glob("*.R"))],
    check_artifacts=[dict(path=str(path.relative_to(ROOT)), sha256=sha(path)) for path in files]
), indent=2), encoding="utf-8")
print("Decoded and hash-checked 600 forest images; retained installed/source/check provenance.")
