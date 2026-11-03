# Slice 2b: analysis disclosure and sheet display

Implementation: `e51c2df4`, `227611e3`, `6d4f8eff`, `9872d0cd`, `82c1f6a6`, `f83eadc2` on `ux/sheets`.

The method/model selector, effect-measure label, heterogeneity estimator (when
supported), and confidence level remain visible. Advanced holds inference,
decimal places, correction amount/policy (binary and diagnostic DOR), and other
method-specific extras. Continuous and HR defaults have inference and decimal
places in Advanced. Combined diagnostic panels use the same Advanced section.
The toggle supports Space/Enter and Tab navigation, records its expansion state
in QSettings, and names changed parameters while collapsed. Values and statistical
requests retain the existing control bindings.

The sheet uses its existing fixed-decimal formatter for estimates and bounds,
including values that round to zero. EditRole still returns unrounded values.
Automatic column fitting assigns spare width to the last automatic column;
Study Name no longer absorbs spare viewport width. Manual widths remain owned
by the user.

## Reproduction

Run in the task worktree with its existing environment:

```bash
source build/sheets-baseline/ENV.sh
uv run --no-sync python scripts/build_qt6.py generate --build-root build/qt6-verification
uv run --no-sync python scripts/verify_rcms.py analysis-dialog
uv run --no-sync python -m pytest tests/e2e -n 2 -q -k 'options or amino or continuous or ratios-hr or analysis-data-diagnostic or sheets or grid-entry or hillclimb or analysis-dialog'
uv run --no-sync python scripts/verify_golden_compatibility.py
uv run --no-sync python -m pytest tests/e2e -n 2 -q
```

The targeted selection passed all 32 scenarios in 678.93 seconds. Its transcript
is `build/sheets-baseline/slice2b-targeted-qualified.log`. The strict golden gate
passed; its report is `build/sheets-baseline/slice2b-golden-qualified.log`.
The final full-matrix transcript is
`build/sheets-baseline/slice2b-matrix-final2.log`: all 131 scenarios passed with
`-n 2` in 3256.57 seconds (54:16).
Every scenario retains its own inputs, exact command, runtime, screenshots and
observations under `artifacts/verification/rcms/`.

Final hillclimb evidence: `20261031T091228Z-81e731f2-hillclimb`, compared against
`20261031T065111Z-c1b82fa9-hillclimb`. For every T1–T5 task, clicks, shortcuts,
typed characters, dialogs, completion flags and recorded numbers are identical.
T5 retains the existing partial-completion flag.

A separate two-process application restart check passed with an expanded
preference written by one process and observed by a fresh application process.
The repeatable script and transcripts are
`build/sheets-baseline/slice2b-restart.py`,
`slice2b-restart-write.log`, and `slice2b-restart-read.log`; run its `write` and
`read` phases with `QT_QPA_PLATFORM=offscreen` and the environment above.
The integrated scenario checks dialog reopen persistence; the process-restart
proof is this additional targeted drive.

## Screenshots

All paths are under `docs/ux-hill-climb/screens/`:

- `slice2b-before-analysis.png` and `slice2b-before-main.png`: recaptured with
  the changed production modules and dialog form loaded from `c6b53b66` in an
  isolated application process.
- `slice2b-after-analysis-collapsed.png`
- `slice2b-after-analysis-expanded.png`
- `slice2b-after-main.png`

The preceding dialog had no Advanced section, so there is one before-dialog
capture. New captures use the preceding 631×437 dialog and 1600×828 main-window
sizes. Recapture command: `uv run --no-sync python build/sheets-baseline/slice2b-screens.py before`
and the same command with `after`, with `QT_QPA_PLATFORM=offscreen`. Script and
transcripts remain beside the other evidence scripts. Adaptive minimum sizes are
released immediately before capturing to retain exactly the requested dimensions.

Earlier failed/interrupted runs remain in the evidence directories. The initial
failures exposed an incorrect digits-in-model-details assertion, inclusion of HR
input metadata in the grid-decimal assertion, and a local/shared estimator-label
mismatch; those were corrected. The UX recovery drive also required its old
nonzero tiny-number display expectation to be replaced with `0.00`, while
separately proving the full-precision EditRole value remains `1/9999`. Runs invalidated by edits during driving do not
count as qualification.
