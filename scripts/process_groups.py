# SPDX-FileCopyrightText: 2026 Ali Salman and RC MetaStudio contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Start and terminate owned verification process trees."""

from collections.abc import Callable, Generator
from contextlib import contextmanager
import os
import signal
import subprocess
import time
from typing import BinaryIO


_killpg: Callable[[int, int], None] | None = getattr(os, "killpg", None)
_sigkill: int = getattr(signal, "SIGKILL", signal.SIGTERM)


@contextmanager
def owned_process(
    command: list[str],
    *,
    stdin: int | None = None,
    stdout: BinaryIO | None = None,
    stderr: BinaryIO | None = None,
    grace_seconds: float = 5,
) -> Generator[subprocess.Popen[bytes]]:
    windows = os.name == "nt"
    # Assign the job before the command can start a child (including Python's
    # Windows virtual environment redirector launching the real interpreter).
    create_suspended = 0x00000004
    process = subprocess.Popen(
        command,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP | create_suspended) if windows else 0,
        start_new_session=os.name == "posix",
    )
    job = None
    try:
        if windows:
            import psutil
            from rc_metastudio.r_worker_lifetime import WindowsWorkerJob

            job = WindowsWorkerJob(process.pid)
            psutil.Process(process.pid).resume()
        yield process
    except BaseException:
        if not windows:
            terminate_process_group(process, grace_seconds=grace_seconds)
        raise
    finally:
        if windows:
            if job is None:
                process.kill()
            else:
                job.close()
            _wait_for_exit(process)


def _wait_for_exit(process: subprocess.Popen[bytes]) -> None:
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"process {process.pid} remained alive after cleanup") from error


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
    _wait_for_exit(process)


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
