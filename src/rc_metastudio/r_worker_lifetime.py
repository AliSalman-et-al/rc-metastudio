"""Keep the private R interpreter bound to its desktop process."""

import ctypes
from ctypes import wintypes
import os
import signal
import sys


def worker_command(program: str, args: list[str]) -> tuple[str, list[str]]:
    if sys.platform == "win32":
        return program, args
    # R takes over the shell PID. The watcher holds none of the protocol pipes.
    watch_parent = """
parent=$1
shift
worker=$$
(
    while actual=$(ps -o ppid= -p "$worker" 2>/dev/null) && [ -n "$actual" ]; do
        if [ "$actual" -ne "$parent" ]; then
            if [ "$group" = yes ]; then
                /bin/kill -KILL -- "-$worker"
            else
                kill -KILL "$worker"
            fi
            break
        fi
        sleep 1
    done
) </dev/null >/dev/null 2>&1 &
exec "$@"
"""
    linux = sys.platform == "linux"
    args = ["-c", ("group=yes\n" if linux else "group=no\n") + watch_parent,
            "rcms-r-worker", str(os.getpid()), program, *args]
    return ("setsid", ["/bin/sh", *args]) if linux else ("/bin/sh", args)


def kill_worker_group(pid: int) -> None:
    if sys.platform == "linux" and pid > 0:
        try:
            if os.getpgid(pid) == pid:
                os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


class _BasicLimits(ctypes.Structure):
    _fields_ = [
        ("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
        ("flags", wintypes.DWORD), ("min_working_set", ctypes.c_size_t),
        ("max_working_set", ctypes.c_size_t), ("active_processes", wintypes.DWORD),
        ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
        ("scheduling", wintypes.DWORD),
    ]


class _ExtendedLimits(ctypes.Structure):
    _fields_ = [
        ("basic", _BasicLimits), ("io", ctypes.c_uint64 * 6),
        ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
        ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t),
    ]


class WindowsWorkerJob:
    def __init__(self, pid: int) -> None:
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel.CreateJobObjectW.restype = wintypes.HANDLE
        kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.CreateJobObjectW(None, None)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        self._close = kernel.CloseHandle
        self._handle = handle
        try:
            limits = _ExtendedLimits()
            limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
                raise ctypes.WinError(ctypes.get_last_error())
            process = kernel.OpenProcess(0x0101, False, pid)  # PROCESS_SET_QUOTA | PROCESS_TERMINATE
            if not process:
                raise ctypes.WinError(ctypes.get_last_error())
            try:
                if not kernel.AssignProcessToJobObject(handle, process):
                    raise ctypes.WinError(ctypes.get_last_error())
            finally:
                kernel.CloseHandle(process)
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        if self._handle:
            self._close(self._handle)
            self._handle = None
