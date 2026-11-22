#!/usr/bin/env python3
"""Run one package-smoke process with bounded, process-tree-aware cleanup."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

if __name__ == "__main__":
    import packaged_smoke_contract as smoke_contract
    import process_groups
else:
    from scripts import packaged_smoke_contract as smoke_contract, process_groups


def _terminate_owned_pid(path: Path | None) -> None:
    if path is None or not path.is_file() or os.name != "posix":
        return
    raw = path.read_text(encoding="utf-8").strip()
    if not raw.isdigit():
        raise RuntimeError("owned package PID file is malformed")
    pid = int(raw)
    if pid <= 1:
        raise RuntimeError("owned package PID is unsafe")
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)
    raise RuntimeError("owned package process remained alive after SIGKILL")


def run_bounded(
    command: list[str],
    *,
    timeout_seconds: int,
    stdout_path: Path | None = None,
    stderr_path: Path | None = None,
    owned_pid_path: Path | None = None,
) -> int:
    if not command:
        raise ValueError("a child command is required")
    if timeout_seconds < 1:
        raise ValueError("timeout must be positive")
    with ExitStack() as streams:
        def open_log(path: Path | None):
            if path is None:
                return None
            path.parent.mkdir(parents=True, exist_ok=True)
            return streams.enter_context(path.open("ab"))

        pid = None
        try:
            with process_groups.owned_process(
                command,
                stdin=subprocess.DEVNULL,
                stdout=open_log(stdout_path),
                stderr=open_log(stderr_path),
                grace_seconds=1,
            ) as process:
                pid = process.pid
                return process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            print(
                f"package process exceeded its {timeout_seconds}-second watchdog: {command!r}",
                file=sys.stderr,
            )
            _confirm_package_exit(pid, owned_pid_path)
            return 124
        except BaseException:
            if pid is not None:
                _confirm_package_exit(pid, owned_pid_path)
            raise


def _confirm_package_exit(pid: int | None, owned_pid_path: Path | None) -> None:
    try:
        if pid is not None and os.name == "posix" and not process_groups.wait_for_process_group_exit(
            pid, timeout_seconds=5
        ):
            raise RuntimeError("package process group remained alive after SIGKILL")
    finally:
        _terminate_owned_pid(owned_pid_path)


def record_completion(path: Path, result: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(smoke_contract.process_exit_marker(result) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--stdout", type=Path)
    parser.add_argument("--stderr", type=Path)
    parser.add_argument("--owned-pid-file", type=Path)
    parser.add_argument("--completion-log", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        result = run_bounded(
            command,
            timeout_seconds=args.timeout_seconds,
            stdout_path=args.stdout,
            stderr_path=args.stderr,
            owned_pid_path=args.owned_pid_file,
        )
        if args.completion_log is not None:
            record_completion(args.completion_log, result)
        return result
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"bounded package process failed: {exc}", file=sys.stderr)
        return 125


if __name__ == "__main__":
    raise SystemExit(main())
