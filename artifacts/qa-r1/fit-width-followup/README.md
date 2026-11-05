# Fit width follow-up to PR 556

The unconditional 14 px scrollbar reservation was a real gap when the vertical
scrollbar was hidden. The existing two exact viewport-derived SVG/raster
assertions reproduce it; before-tests.log records 2 failures, 62 passes.
No expectations or tolerances were changed.

Fit mode now lays out at the maximum width without a vertical scrollbar,
chooses the vertical policy from that height, and narrows only when the full
layout requires scrolling. It keeps that scrollbar visible when narrowing just
makes the scene short enough to fit. Short plots use the full viewport.
Horizontal scrolling is off during fit mode; manual zoom restores AsNeeded
scrolling in both directions. A width snapshot and a refit guard prevent the
layout's own resize notifications from restarting it.

## Repeatable checks (Linux, source Qt app)

Setup: source /home/ali/.t3/qa-env/ENV.sh; PYTHONPATH=$PWD/src:$PWD.
R for the real app: RCMS_R_LIBS=$PWD/build/rcmetar-lib:$RCMS_R_LIBS,
R_LIBS=$RCMS_R_LIBS and R_LIBS_USER=$RCMS_R_LIBS.

- Repository strict typing (win32 target), command printed in typing.log: pass.
- python -m pytest tests/python/gui/test_main_window_automation_launch.py -n 1 -q:
  64 passed (after-tests.log); original exact SVG and raster abs=5 assertions.
- python -m pytest tests/python/gui/test_results_workspace_layout.py -n 1 -q:
  65 passed (results-layout.log).
- python artifacts/qa-r1/shard-repair/run_scenario.py results-window:
  WORKFLOW PASSED, exit 0. Complete manifest/runtime/transcripts copied here;
  original full evidence: artifacts/verification/rcms/20261104T155018Z-68c81277-results-window/.
- python artifacts/qa-r1/fit-width-followup/probe_width.py --assert-stable:
  uses the retained real HR SVG; 3 refits, menu returns, visible vertical
  scrollbar, plot width = available viewport width = 574.0 (width-proof.log).
  The old unfixed behavior recorded 198 refits. No tolerance widened.

Native screenshot: 09-short-fit.png. Started source app via ui.py --session
qa556-fit start sample_projects/continuous.rcms (RCMS_QA_APP_SRC=$PWD,
RCMS_QA_BUILD_ROOT=$RCMS_QT6_BUILD_ROOT, RCMS_QA_R_LIB=$PWD/build/rcmetar-lib).
Analyses → Meta-analysis → Run analysis; Alt+F6 after completion selects Results.
Observed initial 111% width fit, no horizontal or vertical scrollbar and no
extra reserved strip. Session stopped immediately after screenshot.

Only ResultsWindow code changes. No R source, references or numeric values
changed. Full pre-push and native Windows qualification deferred to CI.
