# Windows CI split evidence

Baseline: five latest successful workflow runs retrieved on 2026-11-04 with
`gh run view RUN --json jobs,createdAt,updatedAt,url` and
`gh run view --log --job JOB_ID`. Run `measure.py` after saving those JSON and log
files under `/tmp/ci-measure/RUN.{json,log}` to reproduce the table (minutes).
R deps starts at locked identity validation and includes cache validation/copy.
R build/check ends at INSTALL; Reitsma includes both visual drives; bridge ends
at desktop launch. Rest is total job wall time less those phases (setup, package
installation, golden capture, upload, cleanup). Verdict is workflow creation to
Gate completion, including runner queueing and other required jobs.

`config/desktop-durations.json` contains median call seconds from the duration
summaries of those five logs. Existing logs expose only the slowest ten cases:
other scenarios use 60 seconds as a balancing estimate, assigned to the lightest
bin after measured cases. Ties use node ID and bin index. New cases cannot vanish:
each shard collects the complete suite and verifies the partition has exactly
one copy of every collected node before selecting its bin. Every worker retains
its full partition alongside JUnit results and the existing per-scenario evidence.
No assertions or reference results change. Default local r-stack still runs all
checks and desktop cases. CI runs strict checks plus three parallel desktop jobs;
each owns a freshly built/installed RCMetaR with manifest-validated dependencies.

Removed full-history checkout only from the R-stack job and its desktop copies:
their Git calls read HEAD, status, diff HEAD and tracked/untracked file inventory,
not ancestor commits. Other jobs retain their existing checkout settings.

Local verification on Linux, targeting win32 for Ty (2026-11-04):

```bash
source /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/build/sheets-baseline/ENV.sh
export UV_PROJECT_ENVIRONMENT=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/.venv
export PYTHONPATH="$PWD/src:$PWD"
uv run --no-sync python scripts/build_qt6.py generate
export RCMS_QT6_BUILD_ROOT="$PWD/build/qt6"
uv run --no-sync ty check --python-platform win32 \
  --extra-search-path build/qt6/generated/rc_metastudio \
  --extra-search-path build/qt6/generated/rc_metastudio/forms \
  --extra-search-path . --extra-search-path src/rc_metastudio \
  --extra-search-path src --extra-search-path scripts \
  --extra-search-path tests/python/gui src/rc_metastudio scripts tests r/RCMetaR/inst/qa
uv run --no-sync python -m pytest --strict-markers tests/e2e --collect-only -q \
  --desktop-shard 1 --shard-report build/ci-sharding/partition.json
uv run --no-sync python -m pytest --strict-markers tests --collect-only -q
```

Results: strict typing passed; 46/137 cases selected with complete exact-once
partition; full strict-marker collection passed (1010 tests). Initial attempts
used the ENV.sh generated-root path before generating forms here and failed
because that directory did not exist; the commands above use this worktree's
actual generated tree. These are collection/type proofs, not Windows execution.
