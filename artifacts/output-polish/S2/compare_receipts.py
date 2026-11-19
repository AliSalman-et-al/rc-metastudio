import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile


folder = Path(__file__).resolve().parent
before, after = (json.loads((folder / side / "precision.json").read_text(encoding="utf-8"))
                 for side in ("before", "after"))

for case in ("RR-bmj-2", "OR-bmj-2", "MD-bmj-2"):
    assert after[case]["annotations"] == before[case]["annotations"]
    for table in ("Pooled effect", "Study results"):
        assert after[case]["tables"][table] == before[case]["tables"][table]
    print(f"{case}: identical two-decimal effect annotations and report tables")

note = "Effect estimates displayed with 3 decimals so intervals are distinguishable."
for case in ("RD-default-2", "RD-bmj-2"):
    collapsed = [sum(lo == hi for _, lo, hi in run[case]["annotations"]) for run in (before, after)]
    assert collapsed[0] > 0 and collapsed[1] == 0
    for extension in ("docx", "html", "pdf"):
        path = folder / "after" / f"{case}.{extension}"
        if extension == "docx":
            with ZipFile(path) as archive:
                text = archive.read("word/document.xml").decode("utf-8")
        elif extension == "pdf":
            text = subprocess.check_output(["pdftotext", "-layout", str(path), "-"], encoding="utf-8")
        else:
            text = path.read_text(encoding="utf-8")
        assert note in text and "95.7%" in text, path
        assert re.search(r"−0\.010[\s\u00a0]+to[\s\u00a0]+−0\.004", text), path
        assert re.search(r"−0\.016[\s\u00a0]+to[\s\u00a0]+0\.002", text), path
    print(f"{case}: {collapsed[0]} collapsed annotations before and none after; estimates, PI and note in all exports")

for digits in (2, 4):
    case = f"factor-{digits}"
    after_text = after[case]["results"]
    assert "I² = 22.2%" in after_text
    assert f"Q = {4.25397:.{digits}f}" in after_text
    assert f"τ² = {0.0088:.{digits}f}" in after_text
    assert "I² = 22.2%" not in before[case]["results"]
    print(f"{case}: residual I² = 22.2%; Q and τ² retain {digits} decimals")
