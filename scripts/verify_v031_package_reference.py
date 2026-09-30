#!/usr/bin/env python3
"""Compare a pinned v0.3.1 package capture with a candidate package replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from tests.analysis_regression.golden.support.release_source_v031_package import (  # noqa: E402
    compare_package_manifests,
    validate_package_manifest,
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="Hosted release-reference manifest.json")
    parser.add_argument("candidate", type=Path, help="Locally captured candidate-replay manifest.json")
    parser.add_argument("--report", type=Path, help="Optional path for the comparison JSON report")
    return parser.parse_args()


def read_manifest(path):
    manifest = json.loads(path.read_text(encoding="utf-8"))
    validate_package_manifest(manifest)
    return manifest


def main():
    args = parse_args()
    try:
        reference = read_manifest(args.reference)
        candidate = read_manifest(args.candidate)
        comparison = compare_package_manifests(reference, candidate)
        report = {
            **comparison,
            "reference_versions": reference["versions"],
            "candidate_versions": candidate["versions"],
            "reference_workflow": reference["workflow"],
            "candidate_workflow": candidate["workflow"],
        }
        rendered = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        if args.report is not None:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0 if comparison["passed"] else 1
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print("Package API verification failed: %s" % error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
