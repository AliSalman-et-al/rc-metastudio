# RC MetaStudio v0.5.0 — independent round-six native re-audit

Audit in progress. Baseline: b48c802 on ux/audit-improvements. No product changes.

The audit uses DISPLAY=:0, pinned R 4.6.1 and the test-owned library selected by
../2026-10-14-round3/ENV.sh. Commands and raw output are retained in ignored raw/;
run.py records revision, command, environment, timestamps, exit and log hash.
The serial drive.py runs every maintained scenario fresh through the real native
Qt/R composition, prioritizing the round-six fixes. This draft is not acceptance.

Required comparison: all 88 inherited IDs and R5-01–R5-11, with visually inspected
native evidence, plus any new R6 findings. Linux source verification cannot qualify
other packaged platforms, actual OS DPI or screen readers. Passing registry cases
cannot establish every possible option/data Cartesian product.
