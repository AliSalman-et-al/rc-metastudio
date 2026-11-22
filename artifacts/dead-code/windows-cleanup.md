# Windows verification watchdog

PR #625's first Windows Quick Verification run failed in `test_native_smoke_timeout_runner_streams_output_and_fails_closed`. The watchdog returned 1 in place of the expected 124 because `taskkill /T /F` reported that a child had already exited during cleanup. A retry passed. The original transcript is `quick-jsonlite.log` in the Stage B evidence, SHA-256 `b8a3db8788db202eb497e5b3877cc45457571d0a8f2574fe5268041728c4d385`.

The regression launches a sleeping Python descendant, waits for its own PID through a pipe, then lets the command exit normally. The original watchdog returned while that descendant was still alive. On Windows 11 x64 with Python 3.14.10, the following command failed before the fix with `psutil.TimeoutExpired` waiting five seconds for the descendant.

```powershell
uv run --locked python -m pytest tests/python/fast/test_qt6_build_slice.py -k 'reaps_descendant_when_command_exits' -q --tb=short
```

The watchdog now starts the command suspended, assigns it to the same kind of Windows Job Object used by the application, and resumes it. Job close terminates all descendants on timeout or command exit. The POSIX process-group cleanup still runs on timeout or exception.

The two Windows watchdog tests passed after the fix. They passed 20 consecutive runs, up to four in parallel, for 40 passing cases in total. The original failure, before/after pytest transcripts, and stress transcript are retained under `build/dead-code/`.

```powershell
uv run --locked python -m pytest tests/python/fast/test_qt6_build_slice.py -k 'timeout_runner and not sigterm' -q --tb=short
```
