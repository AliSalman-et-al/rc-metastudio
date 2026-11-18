#!/usr/bin/env python3
"""Create the canonical named-input provenance for a direct macOS R build."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

if __package__:
    from scripts.macos_direct_build_contract import (
        DIRECT_BUILD_INPUT_MEMBERS,
        DIRECT_R_PPM_SNAPSHOT,
        RCMETAR_VERSION,
    )
else:
    from macos_direct_build_contract import (
        DIRECT_BUILD_INPUT_MEMBERS,
        DIRECT_R_PPM_SNAPSHOT,
        RCMETAR_VERSION,
    )


def record(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError(f"required direct-build input is absent: {path}")
    with path.open("rb") as stream:
        sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
    return {
        "sha256": sha256,
        "size": path.stat().st_size,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--ppm-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--target", choices=("macos-arm64",), required=True)
    parser.add_argument("--official-r-url", required=True)
    parser.add_argument("--official-r-sha256", required=True)
    parser.add_argument("--ppm-contrib-path", required=True)
    parser.add_argument("--bridge", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.qualification_root
    names = {
        label: root / PurePosixPath(member).relative_to("qualification")
        for label, member in DIRECT_BUILD_INPUT_MEMBERS.items()
    }

    def ppm(path: Path) -> dict[str, object]:
        relative = path.relative_to(args.ppm_root).as_posix()
        package, version = path.name.rsplit(".", 1)[0].rsplit("_", 1)
        return {
            "path": relative,
            "package": package,
            "version": version,
            "archive_url": f"{DIRECT_R_PPM_SNAPSHOT}/{args.ppm_contrib_path.strip('/')}/{relative}",
            **record(path),
        }

    archives = [
        ppm(path) for path in sorted(args.ppm_root.rglob("*")) if path.is_file()
    ]
    if not archives:
        raise ValueError("PPM archive inventory is empty")
    names["ppm_archive_inventory"].write_text(
        json.dumps(
            {
                "schema_version": 1,
                "repository": DIRECT_R_PPM_SNAPSHOT,
                "archives": archives,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    inputs = {key: record(path) for key, path in names.items()}
    rcmetar = inputs["rcmetar_source_archive"]
    payload = {
        "schema_version": 1,
        "kind": "rc-metastudio-direct-macos-target-build",
        "target": args.target,
        "source_commit": args.source_commit,
        "official_r": {
            "url": args.official_r_url,
            "sha256": args.official_r_sha256,
        },
        "ppm_snapshot": DIRECT_R_PPM_SNAPSHOT,
        "ppm_archives": archives,
        "rcmetar_source": {
            "name": "RCMetaR",
            "version": RCMETAR_VERSION,
            "url": "https://github.com/ResearchConsultancy/rc-metastudio/tree/"
            + args.source_commit
            + "/r/RCMetaR",
            "source_commit": args.source_commit,
            "archive_sha256": rcmetar["sha256"],
            "archive": rcmetar,
        },
        "rpy2_api_bridge_source_sha256": record(args.bridge)["sha256"],
        "inputs": inputs,
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
