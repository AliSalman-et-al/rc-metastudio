"""Reject development-script calls to retired application automation commands."""

from __future__ import annotations

import ast
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
AUTOMATION_FLAG = re.compile(r"--automation-[a-z][a-z0-9-]*")
SCRIPT_SUFFIXES = {".py", ".ps1", ".sh", ".yml", ".yaml", ".R"}
# This flag belongs to the immutable published v0.3.1 executable, not the current app.
HISTORICAL_EXECUTABLE_FLAGS = {
    "scripts/capture_v031_package_reference.py": {"--automation-smoke"},
}


def supported_flags(root: Path) -> set[str]:
    flags: set[str] = set()
    for name in ("launch.py", "automation.py"):
        source = root / "src" / "rc_metastudio" / name
        tree = ast.parse(source.read_text(encoding="utf-8"))
        flags.update(
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and AUTOMATION_FLAG.fullmatch(node.value)
        )
    return flags


def stale_calls(root: Path) -> list[str]:
    supported = supported_flags(root)
    problems: list[str] = []
    paths = sorted(
        path
        for directory in (root / "scripts", root / ".github" / "workflows")
        for path in directory.rglob("*")
        if path.suffix in SCRIPT_SUFFIXES
    )
    for path in paths:
        relative_path = path.relative_to(root).as_posix()
        if relative_path == "scripts/check_script_contracts.py":
            # The checker defines the allowlist; its policy string is not a call site.
            continue
        historical_flags = HISTORICAL_EXECUTABLE_FLAGS.get(relative_path, set())
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stale_flags = set(AUTOMATION_FLAG.findall(line)) - supported - historical_flags
            for flag in sorted(stale_flags):
                problems.append(f"{relative_path}:{number}: {flag}")
    return problems


def main() -> int:
    problems = stale_calls(ROOT)
    if problems:
        print("Retired automation commands:\n" + "\n".join(problems))
        return 1
    print("Script automation command contracts passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
