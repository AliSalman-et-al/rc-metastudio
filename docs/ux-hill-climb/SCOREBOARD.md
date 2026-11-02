# UX hill climb scoreboard

Product baseline: `322ede26`; harness: `fd7a94df`. No product behavior changed.
Measured with real Qt/R, Linux offscreen, isolated settings and working directory.
This supersedes PLAN.md's source-count estimates. RevMan: **not measured**.

Run from the repository root, selecting the pinned runtime and installed RCMetaR:

```bash
export RCMS_R_HOME="$PWD/build/linux-package/work/qualification/extracted/RCMetaStudio-linux-x64/R"
export RCMS_R_LIBS="$RCMS_R_HOME/library"
uv run python scripts/verify_rcms.py hillclimb
# Repeat, using the evidence directory printed by the first command:
uv run python scripts/verify_rcms.py hillclimb --compare-measures <first-evidence-directory>/measures.json
```

Forms must already be generated under build/qt6-verification (see verify-rcms).
The runtime paths above identify the runtime used here; another installation must
satisfy doctor. `--compare-measures` requires identical counts, completion flags,
parsed numerical sections and result text, excluding wall time. It compares
repetitions of one UI version. For later slices, compare numbers with the committed
baseline-measures.json and inspect effort changes separately: progress requires
lower effort with unchanged numbers, not a refreshed statistical oracle.

Each performed button/cell click or QAction activation increments clicks by one.
QActions represent direct activations; menu-opening pointer travel is not driven
or counted. Each non-text key/chord (including F2, Return, Select All and combo
navigation) increments shortcuts by one. Text contributes its character count;
clipboard contents are preloaded inputs and Ctrl+V contributes one shortcut.
Dialogs count when the drive observes the opened dialog, once per wizard, excluding
results windows. Dialogs are a separate dimension, not added to click totals.
File exports use real nonnative Qt save dialogs, including filename entry and Save.
No handwritten task totals are used: measures accumulate at the gesture helpers.

Task time uses a monotonic clock from the first gesture to the final result or
export assertion. It includes analysis and dialog-capture overhead, excludes the
final result screenshot and task-independent setup/cleanup. This is scripted
wall time, not human reading or pointing time. Offscreen proof does not qualify
native window-manager focus, OS pickers, accessibility or release startup.

T1 starts at the ordinary empty main window, activates Create dataset, selects
two-arm binary/default OR, names Mortality, pastes binary.tsv, includes studies,
and accepts default pooled analysis. T2 continues with that data, creates Region
Category and Dose Numeric, types all 24 values, includes studies again, runs
Region subgroup and Dose regression. T3 continues on the same populated binary
data with default small-study settings. T4 starts from the committed lymph.rcms
fixture; project opening is outside the task, as PLAN specifies. T5 starts from
regenerated T1-data results (the existing analysis helper uses three display
decimals), exports text and plot PDF; setup/reopen is excluded. Manuscript PDF
and DOCX are unavailable, so its counts describe partial work only.

| Task | Clicks | Shortcuts | Typed characters | Dialogs | Wall seconds (min–max; spread) | Completable |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| T1 | 21 | 1 | 9 | 2 | 13.20–18.54; 5.34 | yes |
| T2 | 50 | 74 | 85 | 5 | 19.66–26.40; 6.73 | yes |
| T3 | 2 | 0 | 0 | 1 | 3.49–4.41; 0.92 | yes |
| T4 | 3 | 0 | 0 | 2 | 4.34–4.57; 0.23 | yes |
| T5 | 6 | 0 | 40 | 2 | 0.74–1.17; 0.43 | no (partial) |

## After sheets

Two real offscreen Qt/R repetitions; counts and numerical/text receipts match via
`--compare-measures`. Counts remain derived from performed gestures.

| Task | Clicks (Δ) | Shortcuts (Δ) | Characters (Δ) | Dialogs (Δ) | Seconds min–max | Δ seconds vs baseline first run (range) |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| T1 | 21 (+0) | 1 (+0) | 9 (+0) | 2 (+0) | 9.63–17.50 | -3.57–+4.30 |
| T2 | 50 (+0) | 74 (+0) | 85 (+0) | 5 (+0) | 16.98–39.94 | -2.68–+20.28 |
| T3 | 2 (+0) | 0 (+0) | 0 (+0) | 1 (+0) | 2.91–5.25 | -0.58–+1.76 |
| T4 | 3 (+0) | 0 (+0) | 0 (+0) | 2 (+0) | 2.69–7.04 | -1.65–+2.70 |
| T5 | 6 (+0) | 0 (+0) | 40 (+0) | 2 (+0) | 0.66–0.99 | -0.09–+0.25 |

Evidence: `20261031T001023Z-8aec8197-hillclimb` and
`20261031T001407Z-6c744ee0-hillclimb` under `artifacts/verification/rcms/`.
No task adds a gesture or dialog. The slower second repetition spent longer in
analysis/result waits (T1–T4), with concurrent verification on a contended host;
it does not identify an added sheet interaction. T5 remains partial (no manuscript
PDF/DOCX). These tasks each use one sheet; they do not measure switching tabs.

Avoidable steps for subsequent slices:

- T1: wizard page transitions and twelve study-inclusion clicks after paste.
- T2: separate name/type dialogs, repeated F2/Select All/Return per value, and
  twelve re-inclusion clicks after covariate work. Bulk entry could reduce effort.
- T3: separate action and confirmation; examine whether defaults need a dialog.
- T4: consecutive metrics and analysis-setup confirmations for the default path.
- T5: two separate partial exports and filename entries; neither produces the
  requested manuscript. Completion takes precedence over reducing partial counts.

Evidence: each run has manifest.json (revision, command and hashes), steps.jsonl,
screenshots, runtime.json, measures.json, startup.json, transcripts and retained
workflow exports. Failed development drives remain in artifacts/verification/rcms;
only the two successful final repetitions below establish this baseline.
Committed baseline-measures.json retains the first run's counts and numerical/text
receipt; it is not an independent statistical authority. The driver verifies all
covariate values, row count, result sections and export signatures. Numerical
invariance is across repetitions, not a new independent estimator qualification.

Final repetitions: `20261030T224552Z-ce96ebfd-hillclimb`, `20261030T224719Z-b858da51-hillclimb`.
Both manifests passed; action counts and numerical/text output were identical.

Startup follow-up: visible-window median **14.651 → 1.557 s**, range
**10.459–24.426 → 0.879–2.397 s** (spread **13.967 → 1.518 s**, five runs).
R now loads after first paint; analysis waits for readiness. Launch-to-first-amino
result **36.581 → 20.511 s** (single contended runs, not a speedup guarantee).
Doctor, hillclimb, amino, sheets, strict golden (461 pass / 13 accepted exceptions)
and full desktop matrix (125 passed) are green. Evidence: [STARTUP.md](STARTUP.md).

Original startup measured here: three fresh offscreen doctor processes to visible main
window, **median 11.51 s**, range **9.53–15.22 s**. Includes Python/driver startup
and timeout-wrapper overhead; OS caches were not flushed. This is a development
process-start measure, not a packaged native cold-start benchmark. Evidence IDs:
20261030T224000Z-1d03d53e-doctor, 20261030T224303Z-a6d3a736-doctor,
20261030T224333Z-d2cca108-doctor (startup.json in each directory).

Linux bundle size **copied**, not rebuilt/measured here: **155,248,045 bytes**
tar.gz; **459,948,481 bytes** whole-bundle logical; **66,769,599 bytes** R logical.
Source: [R-BUNDLE.md](R-BUNDLE.md), Final Linux result (qualified 30 October build).
RevMan effort/timing, native human timings and packaged cold startup remain not
measured. Full manuscript PDF/DOCX is not completable in today's application.

## After slice 2a

Real Qt/R offscreen final repetitions: `20261031T065611Z-e0d7bc97-hillclimb`
and `20261031T065719Z-9b877928-hillclimb`. Counts, completion, numerical sections
and result texts agree across both runs; all numerical/text receipts also match
`baseline-measures.json`. Counts remain derived from the gesture helpers.

| Task | Baseline clicks | After clicks | Delta | Baseline shortcuts | After shortcuts | Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T1 | 21 | 9 | -12 | 1 | 1 | 0 |
| T2 | 50 | 16 | -34 | 74 | 26 | -48 |

The slice drive pastes complete studies without inclusion clicks, selects the
first cell of each covariate column once, then types each value and presses Enter.
The original task descriptions above describe the baseline gestures. T3–T5 counts
and outputs are unchanged. Script wall times remain unsuitable for human timing.

The re-exclusion came from `_update_inclusion` checking only the entered-effect
source after every edit, including covariates: raw-data-derived estimates were
therefore treated as missing. Inclusion now changes only on effect/data edits,
using raw completeness or entered-effect completeness and preserving explicit
exclusions. Fill down and Clear group workspace history into one transaction;
paste validates a detached candidate and publishes it once, skipping bad numeric
cells with a status summary.

Verification on settled source `ed888ef7`: full desktop matrix
`source build/sheets-baseline/ENV.sh; uv run --no-sync python -m pytest tests/e2e -n 2 -q`
passed **130/130**. Transcript: `build/slice2a-matrix-settled.log`; each child
retains its own command, inputs, runtime, manifest, screenshots and results under
`artifacts/verification/rcms`. Grid-entry includes a 12-row paste with a bad
numeric cell, explicit exclusion across covariate creation/editing, keyboard
entry, fill, clear and undo/redo, plus a 50-row quoted-tab/newline paste and
undo/redo. Its targeted receipt is `20261031T065435Z-f4d5e968-grid-entry`.
Sheets, sheets-edges, sheets-persist, amino, CSV and all three baseline calculators
also passed targeted drives (`build/slice2a-targeted-final.log`).

Strict golden gate (`scripts/verify_golden_compatibility.py --output-root
build/qt6-verification/golden-compatibility-slice2a-final`) passed: **461 passes,
13 existing accepted exceptions**, no numerical changes. Full report:
`build/qt6-verification/golden-compatibility-slice2a-final/compatibility-report.json`.
Earlier failed/interrupted development runs are retained, including a corrected
indentation error, stale test-model references after undo and quoted-parser
failure. They are not counted as passing evidence. Static checking of the view
still reports pre-existing removed-dataset-API errors in the unrelated row-add
helper; no clean whole-project type-check is claimed.

## Slice 3a: T5 manuscript export

T5 completable: **no (partial text + plot export) → yes (PDF + DOCX report)**.
The original baseline rows above remain historical measurements. The new route
uses Export report twice and selects the PDF/Word file types. Both artifacts are
retained in `artifacts/verification/rcms/20261031T123406Z-ed6eba48-hillclimb/workflow/`.
The complete `-n 2` matrix passed all 133 cases; the strict golden gate passed
without refreshing numerical or presentation oracles. See [SLICE3A.md](SLICE3A.md).

## After hill climb

Two fresh real Qt/R offscreen repetitions on `2e245e1c`; the second passed
`--compare-measures` against the first. Counts, completion and numerical/text
receipts match across repetitions. Deltas use the original committed baseline.

| Task | Clicks (Δ) | Shortcuts (Δ) | Characters (Δ) | Dialogs (Δ) | Seconds min–max | Δ seconds vs baseline first run (range) | Completable |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| T1 | 9 (-12) | 1 (+0) | 9 (+0) | 2 (+0) | 5.76–5.80 | -7.45–-7.40 | yes |
| T2 | 16 (-34) | 26 (-48) | 85 (+0) | 5 (+0) | 8.82–8.84 | -10.85–-10.82 | yes |
| T3 | 2 (+0) | 0 (+0) | 0 (+0) | 1 (+0) | 1.38–1.45 | -2.12–-2.04 | yes |
| T4 | 3 (+0) | 0 (+0) | 0 (+0) | 2 (+0) | 1.49–1.50 | -2.85–-2.84 | yes |
| T5 | 6 (+0) | 0 (+0) | 41 (+1) | 2 (+0) | 0.41–0.42 | -0.33–-0.32 | yes |

Evidence: `20261101T021424Z-61af403d-hillclimb` and
`20261101T021548Z-e4deb9d7-hillclimb` under `artifacts/verification/rcms/`.
Commands and transcripts: `build/final-qualification-hillclimb-{1,2}.log`.
Scripted wall time includes analysis/capture waits; it is not human task timing.
T5 now exports manuscript PDF/DOCX (baseline was partial text/plot export),
with one additional typed filename character.

Numerical receipt audit: **no T1–T5 parsed numerical fields or result-text
sections differ from `baseline-measures.json`** in either run. The intentional
subgroup Q/p, zero-cell MH/Peto pooling, sequential and source-confidence
corrections in [STAT-FIXES.md](STAT-FIXES.md) affect their documented fixtures;
they produce no differences in these five receipts. No baseline was refreshed.

Final qualification used `source build/sheets-baseline/ENV.sh` and
`uv run --no-sync` on `1d9df980`, after reverting the icon restoration in
`2e245e1c`. Slice 7 intentionally makes every metric choice text-only; the
shared `ratios-hr` / `ratios-irr` assertion now checks every combo entry has no
icon. All other workflow assertions, including numerical checks, are retained.

One uninterrupted process ran the two targeted workflows (**2 passed**, 176.75
seconds), then the complete fresh E2E matrix (`-n 2 -q --fresh`, **135 passed**,
3017.98 seconds), then the strict golden gate (**passed**, 475 comparisons / 416
numeric fields). Evidence reuse was disabled throughout. Exact commands and
results: `build/final-qualification-2-run.sh` and
`build/final-qualification-2-all.log`; golden report:
`build/qt6-verification/golden-compatibility-final-2/compatibility-report.json`.
Each desktop workflow retains its own inputs, runtime, manifest, transcript and
screenshots under `artifacts/verification/rcms/`. This final full-matrix run
supersedes the earlier qualification with two stale icon-assertion failures.
No numerical implementation, assertions or oracles changed. Generated tracked
slice7 screenshots are excluded from these commits.
