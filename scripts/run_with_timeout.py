"""Run one verification command with inherited output and a hard timeout."""

from __future__ import annotations

import argparse
import os
import re
import shlex
import signal
import subprocess
import sys


TIMEOUT_EXIT_CODE = 124
_TASKKILL_SUCCESS = re.compile(
    r"SUCCESS: The process with PID \d+(?: \(child process of PID \d+\))? "
    r"has been terminated\.",
    re.IGNORECASE,
)
_TASKKILL_VANISHED_CHILD = re.compile(
    r"ERROR: The process with PID \d+ \(child process of PID \d+\) "
    r"could not be terminated\.",
    re.IGNORECASE,
)
_TASKKILL_NO_RUNNING_INSTANCE = re.compile(
    r"Reason: There is no running instance of the task\.",
    re.IGNORECASE,
)


def _display_command(command: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(command)
    return shlex.join(command)


def _taskkill_output_lines(result: subprocess.CompletedProcess[str]) -> list[str]:
    lines = [
        line.strip()
        for line in f"{result.stdout}\n{result.stderr}".splitlines()
        if line.strip()
    ]
    return lines


def _taskkill_line_width(lines: list[str], index: int) -> int:
    if _TASKKILL_SUCCESS.fullmatch(lines[index]):
        return 1
    if (
        index + 1 < len(lines)
        and _TASKKILL_VANISHED_CHILD.fullmatch(lines[index])
        and _TASKKILL_NO_RUNNING_INSTANCE.fullmatch(lines[index + 1])
    ):
        return 2
    return 0


def _only_reports_vanished_children(result: subprocess.CompletedProcess[str]) -> bool:
    lines = _taskkill_output_lines(result)
    if not lines:
        return False

    found_vanished_child = False
    index = 0
    while index < len(lines):
        width = _taskkill_line_width(lines, index)
        if width == 0:
            return False
        found_vanished_child = found_vanished_child or width == 2
        index += width
    return found_vanished_child


def _terminate_windows_process_tree(process: subprocess.Popen[bytes]) -> None:
    terminated = subprocess.run(
        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if terminated.returncode != 0 and not _only_reports_vanished_children(terminated):
        details = "\n".join(
            part.strip()
            for part in (terminated.stdout, terminated.stderr)
            if part.strip()
        )
        raise RuntimeError(
            f"taskkill /T /F failed for process tree {process.pid} "
            f"with exit code {terminated.returncode}: "
            f"{details or 'no diagnostics'}"
        )
    # A Windows venv redirector can close its job before taskkill reaches its child.
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired as error:
        taskkill_result = (
            "reported an already-gone child"
            if terminated.returncode != 0
            else "reported success"
        )
        raise RuntimeError(
            f"taskkill {taskkill_result} but process {process.pid} remained alive"
        ) from error


def _terminate_posix_process_tree(process: subprocess.Popen[bytes]) -> None:

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass

    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        group_remains = False
    else:
        group_remains = True
    if group_remains:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.wait(timeout=5)


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        _terminate_windows_process_tree(process)
    else:
        _terminate_posix_process_tree(process)


def run(command: list[str], *, timeout_seconds: float, label: str) -> int:
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    process = subprocess.Popen(
        command,
        creationflags=creationflags,
        start_new_session=os.name != "nt",
    )
    try:
        return process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        print(
            f"{label} timed out after {timeout_seconds:g} seconds: "
            f"{_display_command(command)}",
            file=sys.stderr,
            flush=True,
        )
        _terminate_process_tree(process)
        return TIMEOUT_EXIT_CODE
    except BaseException:
        _terminate_process_tree(process)
        raise


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
