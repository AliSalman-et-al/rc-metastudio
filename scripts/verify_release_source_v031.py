#!/usr/bin/env python3
"""Compare a current golden capture to the tagged-source v0.3.1 reference."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from tests.analysis_regression.golden.support.release_source_v031 import (  # noqa: E402
    compare_release_source_v031,
)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Compare a current analysis capture with the tagged-source v0.3.1 "
            "numerical and semantic reference."
        )
    )
    parser.add_argument("current_manifest", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)

    current = json.loads(args.current_manifest.read_text(encoding="utf-8"))
    report = compare_release_source_v031(current)
    if args.report:
        args.report.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    summary = {
        "mode": report["mode"],
        "passed": report["passed"],
        "reference": report["reference"],
        "comparison_rows": len(report["comparison"]["rows"]),
        "classification_counts": dict(
            Counter(
                row["classification"] for row in report["comparison"]["rows"]
            )
        ),
        "identity_drift": report["identity_drift"],
        "presentation_acceptances": report["presentation_acceptances"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
