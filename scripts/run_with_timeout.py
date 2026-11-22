"""Run one verification command with inherited output and a hard timeout."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys

if __name__ == "__main__":
    from process_groups import owned_process
else:
    from scripts.process_groups import owned_process


TIMEOUT_EXIT_CODE = 124


def _display_command(command: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(command)
    return shlex.join(command)


def run(command: list[str], *, timeout_seconds: float, label: str) -> int:
    try:
        with owned_process(command) as process:
            return process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        print(
            f"{label} timed out after {timeout_seconds:g} seconds: "
            f"{_display_command(command)}",
            file=sys.stderr,
            flush=True,
        )
        return TIMEOUT_EXIT_CODE


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout-seconds", type=float, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a command is required after --")
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    return run(command, timeout_seconds=args.timeout_seconds, label=args.label)


if __name__ == "__main__":
    raise SystemExit(main())
