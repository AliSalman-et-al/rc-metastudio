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

Startup follow-up: five profiled processes on a contended host measured **median
14.65 s**, range **10.46–24.43 s** (spread **13.97 s**). No product startup
optimization retained: early window construction requires RCMetaR in files reserved
for `ux/sheets`. Breakdown, evidence and proposed fix: [STARTUP.md](STARTUP.md).

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
