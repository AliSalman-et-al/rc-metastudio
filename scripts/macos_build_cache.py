"""Key the source-built macOS dependencies independently of the app version."""

import hashlib
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path


def cache_keys(root: Path, toolchain: str, architecture: str) -> tuple[str, str]:
    sdk = hashlib.sha256()
    sdk.update(json.dumps([str(root.resolve()), toolchain, architecture]).encode())
    for name in ("scripts/build-macos-package.sh", "config/macos-package-targets.json"):
        sdk.update(hashlib.sha256((root / name).read_bytes()).digest())
    sdk_key = sdk.hexdigest()

    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    del project["project"]["version"]
    for package in lock["package"]:
        if package["source"].get("editable") == ".":
            del package["version"]
    wheel = hashlib.sha256()
    wheel.update(sdk_key.encode())
    wheel.update((root / ".python-version").read_bytes())
    wheel.update(json.dumps([project, lock], sort_keys=True, default=str).encode())
    return sdk_key, wheel.hexdigest()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    commands = (
        ("sw_vers", "-buildVersion"),
        ("xcodebuild", "-version"),
        ("xcrun", "--sdk", "macosx", "--show-sdk-path"),
        ("xcrun", "clang", "--version"),
        ("cmake", "--version"),
        ("ninja", "--version"),
        ("uv", "--version"),
    )
    toolchain = json.dumps([
        subprocess.check_output(command, text=True).strip() for command in commands
    ])
    sdk, wheel = cache_keys(root, toolchain, sys.argv[1])
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
        output.write(f"sdk={sdk}\nwheel={wheel}\n")


if __name__ == "__main__":
    main()
