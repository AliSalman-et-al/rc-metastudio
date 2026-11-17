#!/usr/bin/env python3
"""Resolve cross-platform package metadata for GitHub Actions."""

from __future__ import annotations

import argparse
import os
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version-only",
        action="store_true",
        help="legacy alias for the default version-only output",
    )
    parser.parse_args()
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        raise SystemExit("GITHUB_OUTPUT is required.")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = project["project"]["version"]
    with Path(output_path).open("a", encoding="utf-8") as output:
        output.write(f"version={version}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
