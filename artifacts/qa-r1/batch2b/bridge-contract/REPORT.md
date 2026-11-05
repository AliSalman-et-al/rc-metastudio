# Bridge resize contract follow-up

CI run 41968678930, checks job 127051703525 failed `_DRIVER` line 279 in test_inprocess_rpy2_backend.py: `assert shrunken_width < initial_plot_width`. The driver constructs ResultsWindow directly; startup and close-before-deliver do not run on this path.

The original assertion assumed every automatic resize shrinks the SVG. With the approved 9 pt readable floor, the real continuous forest is already at its minimum readable width: 1125.759259259 px for both 796 px and 596 px windows (before.log and observation.log). The complete bridge suite reproduced this as its only failure: 1 failed, 6 passed, 2 skipped (suite-before.log).

Per review direction, changed the driver contract rather than removing the product floor:

1. Shrink in automatic mode; independently parse the study label's font size from the real SVG and combine its coordinate and device scales to assert ≥9 pt. Assert plot width exceeds the viewport and the horizontal scrollbar has a positive range.
2. Restore the original window size, trigger the actual Fit width action, then perform the existing resize test. The original shrink assertion, grow assertion and splitter assertions remain unchanged.

Measured automatic state: label 9.000000000000002 pt, horizontal scroll maximum 683, viewport 473 px. Explicit Fit-width plot width: 643 px initially, 443 px after shrinking. The instrumented driver still runs all original assertions and ends with OK (observation-final.log; repeatable observer script observe.py). The requested `python -m pytest tests/r_stack -q` passed with the pinned R binary and required prerequisites: 9 passed, no skips or warnings (suite-required.log). The earlier suite-final.log recorded 7 passes and 2 skips because its direct-R tests used the system Rscript; it is superseded by the required-mode run. Product code and statistics are unchanged.

Environment: `source /home/ali/.t3/qa-env/ENV.sh && export PYTHONPATH=$PWD/src:$PWD`; prepend `$PWD/build/rcmetar-lib` to RCMS_R_LIBS and export R_LIBS/R_LIBS_USER to that value. Also export `R_HOME=$RCMS_R_HOME`, prepend `$RCMS_R_HOME/bin` to PATH, and set `RCMS_R_STACK_REQUIRED=1`; this selects the pinned Rscript rather than /usr/bin/Rscript and turns missing prerequisites into failures. This is the current merged-master R source installed during the preceding merge qualification. Full strict typing targets win32 and passed before qualification; exact command in typing.log. `python scripts/verify.py pre-push` is retained in pre-push.log. Actual Windows execution remains CI-owned.

All pre-push stages passed, including fresh-master code health, fast/golden, GUI and packaging contracts (pre-push.log). Contract change is explicitly documented in the PR body per review direction; no product code changed for this follow-up.
