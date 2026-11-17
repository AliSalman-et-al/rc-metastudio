# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Terminate verification children that started their own POSIX sessions."""

from collections.abc import Callable
import os
import signal
import subprocess
import time


_killpg: Callable[[int, int], None] | None = getattr(os, "killpg", None)
_sigkill: int = getattr(signal, "SIGKILL", signal.SIGTERM)


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
