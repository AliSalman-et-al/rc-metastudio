"""Render the original and final frozen presentation changes for review."""

from collections import Counter
from difflib import unified_diff
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
from zipfile import ZipFile

from PIL import Image, ImageDraw


folder = Path(__file__).resolve().parent
root = folder.parents[2]
baseline = root / "tests/analysis_regression/baseline/observed-golden-baseline.zip"
original_report = folder.parent / "qualification/golden-final-report.json"
original_capture, review_capture = map(Path, sys.argv[1:])
review_report = review_capture / "compatibility-report.json"


def drift(report):
    rows = json.loads(report.read_text(encoding="utf-8"))["comparison"]["rows"]
    counts = Counter(row["classification"] for row in rows)
    assert sum(row["classification"] == "pass" and "matched within tolerance" in row["detail"] for row in rows) == 416, counts
    assert not set(counts) - {"pass", "accepted_exception", "text_artifact_drift"}, counts
    return {(row["id"], row["detail"]) for row in rows if row["classification"] == "text_artifact_drift"}


def side_by_side(before, after, path):
    sides = [Image.open(BytesIO(contents)).convert("RGBA") for contents in (before, after)]
    gap, title, padding = 14, 28, 10
    width = sum(side.width for side in sides) + gap + 2 * padding
    height = title + padding + max(side.height for side in sides)
    panel = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(panel)
    left = padding
    for label, side in zip(("Frozen", "Proposed"), sides, strict=True):
        draw.text((left, 6), label, fill="black")
        panel.paste(side, (left, title), side)
        left += side.width + gap
    draw.line((sides[0].width + padding + gap // 2, 0, sides[0].width + padding + gap // 2, height),
              fill="#c9c9c9")
    panel.save(path)


def table_report(report, capture, heading, subfolder, archive, *, exclusions=frozenset()):
    changes = sorted(drift(report) - exclusions)
    directory = folder / subfolder
    directory.mkdir(exist_ok=True)
    sections = [f"## {heading}", ""]
    for index, (case, detail) in enumerate(changes, 1):
        member = f"captures/{case}.json"
        before = json.loads(archive.read(member))
        after = json.loads((capture / member).read_text(encoding="utf-8"))
        item = f"{index:02d}-{case}"
        if detail.startswith("Text section "):
            label = detail.removeprefix("Text section ").removesuffix(" changed.")
            before_label = next(name for name in before["texts"] if name.casefold() == label.casefold())
            prior = before["texts"][before_label].splitlines()
            current = after["texts"][label].splitlines()
            diff = "\n".join(unified_diff(prior, current, "frozen", "proposed", lineterm=""))
            assert diff, (case, label)
            (directory / f"{item}.diff").write_text(diff + "\n", encoding="utf-8")
            sections.extend((f"### {index}. {case} · {label}", "", "```diff", diff, "```", ""))
        else:
            label = next(plot["label"] for plot in before["artifacts"]
                         if detail.startswith(f"Artifact {plot['label']} "))
            old = next(plot for plot in before["artifacts"] if plot["label"] == label)
            new = next(plot for plot in after["artifacts"] if plot["label"] == label)
            filename = Path(old["bundle_path"] or old["path"]).name
            old_png = archive.read(f"artifacts/{case}/{filename}")
            new_png = (capture / "artifacts" / case / Path(new["bundle_path"] or new["path"]).name).read_bytes()
            assert sha256(old_png).hexdigest() == old["sha256"]
            assert sha256(new_png).hexdigest() == new["sha256"]
            side_by_side(old_png, new_png, directory / f"{item}.png")
            sections.extend((f"### {index}. {case} · {label}", "",
                             f"![Frozen and proposed {label} for {case}]({subfolder}/{item}.png)", ""))
    return sections


original = drift(original_report)
final = drift(review_report)
assert len(original) == 18, len(original)
lines = ["# Frozen presentation review", "",
         "The frozen comparison passed all 416 numerical fields in both captures. "
         "The archive update uses the second capture. It retains the numerical oracle and its tolerances.", "",
         f"The branch originally proposed 18 changes. The final capture proposes {len(final)}, "
         f"of which {len(final - original)} are additional case and output pairs.", ""]
with ZipFile(baseline) as archive:
    lines += table_report(original_report, original_capture, "Original 18 proposed changes", "original", archive)
    lines += table_report(review_report, review_capture, "Final proposed changes", "final", archive)
(folder / "REVIEW.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
