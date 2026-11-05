# Run 42061617733 follow-up

Read failed Vertical Slice job 127364770771. It passes strict typing, all 310 Windows GUI tests, and the standalone shell smoke with QT_FATAL_WARNINGS=1. There is no setGeometry warning. The later Results smoke validator rejects navigation because its exact expectation still says Forest Plot instead of Forest plot.

No geometry edit is warranted. The earlier 1024×768 HyperV warning used frame margins (8,31,8,8): a 1024×697 client at (0,23) has a 1040×736 native frame at (-8,-8). Asking that maximized client for 1024×689 removes eight more pixels; Windows restores height 697. That was the old invalid request. This run proves the unchanged current clamp passes the Windows fatal-warning shell gate.

Checked other jobs. R-stack checks job 127365236284 also failed: all 416 numerical metrics and exact Windows artifact comparisons passed, but the approved Inference Method exception detail and two regression display identities retained title case. Updated the exact Inference method detail and Regression plot identities only. The plot contract byte hash is refreshed; all 11 oracle artifact hashes, source labels and plot capabilities are identical. Numerical oracles and tolerances are unchanged. run-status-final.json records successes for R-stack shards 2/3 and all completed platform jobs; shard 1 and Windows package qualification were still running at the check.

Commands used from repository root with the existing pinned QA environment:

```bash
source /home/ali/.t3/qa-env/ENV.sh
export UV_PROJECT_ENVIRONMENT=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/.venv
export PYTHONPATH=$PWD/src:$PWD RCMS_QT6_BUILD_ROOT=$PWD/build/qt6-verification
uv run --no-sync python -c 'from scripts.verify import run_typing; from pathlib import Path; run_typing(Path("build/qt6-verification"))'
uv run --no-sync python scripts/native_results_smoke.py --offscreen
uv run --no-sync python scripts/verify.py pre-push
export R_HOME=$RCMS_R_HOME R_LIBS=$RCMS_R_LIBS R_LIBS_USER=$RCMS_R_LIBS
uv run --no-sync python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-navigation
uv run --no-sync python -m pytest tests/analysis_regression/golden/test_analysis_regression_compare.py tests/python/fast/test_native_results_evidence.py -q
```

Results: win32 strict typing passed; Results smoke at scale 1.0 and 1.5 passed (screenshots and JSON retained here; offscreen is not Windows native proof). Full pre-push passed all stages. After the final exact golden expectation edits, the focused consumer tests passed 63/63 and real-R strict golden passed all 475 comparisons / 416 numeric metrics. Logs retain each command and result. Downloaded Windows failure logs are retained. No assertions were loosened or warnings suppressed.
