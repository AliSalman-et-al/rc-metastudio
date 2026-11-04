# PR 556: Windows shard presentation repair

Run inspected: 41820827724; jobs 126543479160 (shard 1), 126543479243
(shard 2), 126543479437 (shard 3), and 126551955844 (integration aggregate).
The aggregate failed because the R-stack failed; it adds no separate defect.

All three shard logs are retained locally. There are 19 failed scenarios:

- shard 1: analysis-diagnostic-regression-factor, plot-workflow-contour,
  plot-workflow-forest, ratios-irr, results-window.
- shard 2: analysis-diagnostic-regression-continuous, plot-workflow-coefficient,
  plot-workflow-deeks, plot-workflow-leave-one-out, plot-workflow-trimfill,
  project-release-coefficients, ratios-hr, small-study-diagnostic, ux-improvements.
- shard 3: analysis-diagnostic-regression-multiple, project-round6-polish,
  plot-workflow-subgroup, plot-workflow-funnel, plot-workflow-cumulative.

## Diagnosis before assertions

The actual Windows HR and leave-one-out screenshots/SVGs were inspected before
any expectation edits. Both show a real regression: null-anchored labels wrap,
and the left and right text visually run together. The old assertion also
incorrectly treats every text node sharing x as a continuation of one label;
the new anchors deliberately share the null x coordinate.

The renderer now keeps each label on one line, fits both sides with a common
measured font size, and reserves one measured space in drawing coordinates on each side of the null. Qt trims ordinary/nonbreaking outer SVG spaces, so text padding alone is insufficient. The Qt-painted glyph gap is also asserted. It keeps the
existing suppression when the null leaves no room on both sides. Exact label
strings, common baseline, opposite text anchors with a narrow null gutter, device bounds and overlap
checks remain strict. The long-name workflow exercises Default, RevMan and BMJ.

Other failures require the intended F20 funnel label and F16 absence of empty
pooled/model-fit tables. Report tables are found by exact title, presence must
match expected rows, and all remaining headers/values are still checked exactly.

## Replay

`replay.py` executes one real Qt/R application at a time. Commands, evidence
directories and exit codes are indexed in `replay-results.json`; each evidence
manifest retains inputs, runtime, screenshots, SVGs and decoded exports.
An initial HR run reached a valid off-axis omission assertion, then a replay
hit its 600-second budget after subgroup exports. The subsequent serial run
uses 1800 seconds and records timed stacks for unusually slow scenarios.
No full local pre-push suite was run.

Windows x64 Package Qualification succeeded in run 41820827724, job
126543479317. The earlier packaged-smoke/F14 failure does not persist.
Packaging Contract Tests (126543479049) and macOS focused package contracts
(126543479480) also succeeded.

## Final integration fixes

Master is merged through e7d7389c (#558, #559, #560 included). The only
remaining analysis_setup_dialog.py difference from master is F13 wording.
Peto→OR null handling, contribution rules, BMJ method labels, axis validation
and CSV import changes are intact.

The retained HR SVG reproduced an F11 scrollbar feedback loop: 198 refits
while a context menu was opening. The final layout reserves the vertical
scrollbar width regardless of its current visibility. The same probe settles
after four refits; 65 existing Results layout tests pass with -n 1. The live
E2E context route also requires idle resize events to settle.

The final R runner selects forest-metafor-renderer, summary-display and ratios
from the installed private package. It reports 1,258 passing expectations,
zero failures and zero errors. An earlier CSV evidence writer could not encode
a testthat list column; the corrected runner writes only atomic summary
columns and exits successfully. No test expectation was relaxed for that error.

## Environment interruption

The first IRR supervisor disappeared during the context handoff, leaving its
owned child running; that child was stopped before a fresh run. The next run
encountered a shared-filesystem exhaustion: a zero-byte R plot-state file and
`OSError: [Errno 28] No space left on device` during evidence retention. This is
not counted as a pass. The results index was restored from its staged snapshot
(the disk-full write had truncated it), then the same scenario was restarted.
The machine subsequently recovered about 10 GB of free space. No application
assertion or expectation was changed for these interruptions.

## Final outcome

All 23 selected real Qt/R scenarios pass: all 19 Windows shard failures, both
manuscript exports, fixed Peto and MH/RD integration. See replay-results.json
for exact commands, evidence paths and zero exit codes; replay-manifests retains
the corresponding complete manifests, runtime identities and transcripts.
No tolerance changed. Strict typing passes (win32 target), Results layout tests
65 passed (-n 1), and selected R tests 1,258 expectations passed with no failures.
The Windows golden recomparison passes all 475 rows; 13 existing accepted
exceptions remain unchanged.

Native source app: dark palette, +6 pt font, amino.rcms startup path; Analyses
→ Meta-analysis → Run analysis, Alt+F6 to results, scroll four notches to footer.
`native/15-final-results.png` shows the initial 123% width fit;
`native/16-final-favours.png` shows single-line labels on opposite sides of null,
clear of ticks and axis title. Session qa556-f6 was stopped immediately after
capture. Native command transcript: native/final-commands.txt.

Not checked locally: full pre-push suite (CI as instructed), Windows native
execution of the new code, and the complete light/dark/font screenshot matrix.
