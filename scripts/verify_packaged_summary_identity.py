"""Capture packaged-smoke summary identities using the source application and pinned R."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from scripts.assemble_packaged_smoke_evidence import (
    PACKAGED_PROCESS_TIMEOUT_SECONDS,
    normalize_packaged_summary_identity,
    normalized_summary_sha256,
    packaged_analysis_arguments,
)
from scripts.packaged_smoke_contract import EXPECTED_SUMMARY_SHA256_BY_SAMPLE
from scripts.verification_evidence import ROOT, desktop_environment


# Set the Qt settings location before starting the ordinary automation entry point.
_SOURCE_ENTRY = """
import sys
from PyQt6.QtCore import QSettings, QStandardPaths
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, sys.argv.pop(1))
QStandardPaths.setTestModeEnabled(True)
from rc_metastudio.__main__ import main
raise SystemExit(main())
"""


def capture_source_summary(sample: str, destination: Path) -> dict[str, str]:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    analysis = destination / "analysis.json"
    command = [sys.executable, "-c", _SOURCE_ENTRY, str(destination),
               *packaged_analysis_arguments(analysis, ROOT / "sample_projects" / sample)]
    appdata = str(destination / "appdata")
    env = desktop_environment() | {
        "RCMS_PACKAGE_LOCALE": "en_US",
        "RCMS_ANALYSIS_SCRATCH_DIR": str(destination / "scratch"),
        "APPDATA": appdata,
        "LOCALAPPDATA": appdata,
        "XDG_DATA_HOME": appdata,
    }
    log_path = destination / "capture.log"
    with log_path.open("w", encoding="utf-8") as log:
        log.write(json.dumps(command) + "\n")
        log.flush()
        process = subprocess.run(command, cwd=destination, env=env, timeout=PACKAGED_PROCESS_TIMEOUT_SECONDS,
                                 stdout=log, stderr=subprocess.STDOUT)
    if process.returncode:
        raise RuntimeError(f"Source packaged analysis failed for {sample}. See {log_path}")
    observation = json.loads(analysis.read_text(encoding="utf-8"))
    summary = observation["texts"].get("Summary")
    if observation["opened"] is not True or not summary:
        raise RuntimeError(f"Source packaged analysis produced no summary for {sample}. See {analysis}")
    normalized = normalize_packaged_summary_identity(summary)
    (destination / "normalized-summary.txt").write_text(normalized + "\n", encoding="utf-8")
    return {"sample": sample, "normalized_summary_sha256": normalized_summary_sha256(summary)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    output_dir = parser.parse_args().output_dir
    for sample in EXPECTED_SUMMARY_SHA256_BY_SAMPLE:
        print(json.dumps(capture_source_summary(sample, output_dir / Path(sample).stem)))


if __name__ == "__main__":
    main()
