#!/usr/bin/env python3
"""Retain the original sample corpus and drive each declared pair through Qt/R.

Run before converting samples: uv run python scripts/sheets_baseline.py OUTPUT.
The output directory must be new, so an original baseline cannot be overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--native", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    originals = output / "originals"
    originals.mkdir()
    inventory = []
    for path in sorted((ROOT / "sample_projects").glob("*.rcms")):
        shutil.copy2(path, originals / path.name)
        with zipfile.ZipFile(path) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            project = json.loads(archive.read("project.json"))
            state = json.loads(archive.read("state.json"))
        dataset = project["dataset"]
        pairs = []
        for outcome in dataset["outcomes"]:
            for label in outcome["follow_ups"] or [None]:
                pairs.append({
                    "outcome": outcome["name"], "follow_up": label,
                    "data_type": outcome["data_type"],
                    "rows_with_unit": sum(
                        any(unit["outcome"] == outcome["name"]
                            and unit["follow_up"] == label
                            for unit in row["analysis_units"])
                        for row in dataset["studies"]
                    ),
                })
        inventory.append({"file": path.name,
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "format_version": manifest["format_version"],
                          "state": state, "pairs": pairs})
    receipt = {"command": sys.argv, "head": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "environment": {key: value for key, value in os.environ.items()
                        if key.startswith("RCMS_") or key in {"R_LIBS", "R_LIBS_USER", "R_HOME"}},
        "r_source_sha256": {
            path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((ROOT / "r/RCMetaR").rglob("*")) if path.is_file()
        }, "samples": inventory}
    (output / "inventory.json").write_text(json.dumps(receipt, indent=2) + "\n")
    environment = dict(os.environ, RCMS_SHEETS_BASELINE=str(output))
    command = [sys.executable, str(ROOT / "scripts/verify_rcms.py"), "sheets-baseline"]
    if args.native:
        command.append("--native")
    result = subprocess.run(command, cwd=ROOT, env=environment,
                            capture_output=True, text=True)
    (output / "stdout.log").write_text(result.stdout)
    (output / "stderr.log").write_text(result.stderr)
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
