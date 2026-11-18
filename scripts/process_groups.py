# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Start and terminate owned verification process trees."""

from collections.abc import Callable
import os
import signal
import subprocess
import time
from typing import BinaryIO


_killpg: Callable[[int, int], None] | None = getattr(os, "killpg", None)
_sigkill: int = getattr(signal, "SIGKILL", signal.SIGTERM)


def start_process(
    command: list[str],
    *,
    stdin: int | None = None,
    stdout: BinaryIO | None = None,
    stderr: BinaryIO | None = None,
) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        command,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        start_new_session=os.name == "posix",
    )


def terminate_process_tree(
    process: subprocess.Popen[bytes], *, grace_seconds: float = 5
) -> None:
    if os.name != "nt":
        terminate_process_group(process, grace_seconds=grace_seconds)
        return
    terminated = subprocess.run(
        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if terminated.returncode != 0:
        details = "\n".join(
            part.strip() for part in (terminated.stdout, terminated.stderr) if part.strip()
        )
        raise RuntimeError(
            f"taskkill /T /F failed for process tree {process.pid} "
            f"with exit code {terminated.returncode}: {details or 'no diagnostics'}"
        )
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            f"taskkill reported success but process {process.pid} remained alive"
        ) from error


def _signal_group(group_id: int, signum: int) -> bool:
    if _killpg is None:
        raise RuntimeError("process groups are unavailable on this platform")
    try:
        _killpg(group_id, signum)
    except ProcessLookupError:
        return False
    return True


def terminate_process_group(process: subprocess.Popen[bytes], *, grace_seconds: float) -> None:
    # Popen(start_new_session=True) makes the leader's PID its process-group ID.
    _signal_group(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        pass
    _signal_group(process.pid, _sigkill)
    process.wait(timeout=5)


def wait_for_process_group_exit(group_id: int, *, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            if not _signal_group(group_id, 0):
                return True
        except PermissionError:
            pass  # The group exists even if the verifier cannot signal it.
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.05)
