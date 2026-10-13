# RCMS round two — changes and evidence

Local branch `ux/audit-improvements`; baseline `84fdbc57`. No push or PR.
The latest user scope in [PLAN.md](PLAN.md) governs this round: extend existing
analyses when independently verified; no new analysis families.

## Product changes

Results now carry R table headers and cells through the versioned boundary instead
of rebuilding statistics from printed strings. The report uses wrapping system-font
prose and compact tables. A native Tables view provides real headers/cells, keyboard
copy and CSV export. Diagnostic joint results open on the clinical summary; model
configuration follows the results. The combined dispatcher preserves the joint
summary container and its semantic identity. Optional R model titles are accepted
for fixed diagnostic sequential results.

Report and figure zoom have independent state. Fit width is enabled only for the
figure. CSV instructions stay outside the scrolling fields, and page entry resets
position and focus. Its delayed reset belongs to the page, preventing a callback
from reaching a deleted scrollbar after wizard teardown.

Forest headings retain the selected metric, including entered effects and regression
coefficients. Diagnostic moderator labels use the actual covariate, contrast and
reference rather than backend coefficient tokens; measured margins accommodate
wrapped labels. Automatic ranges include finite confidence intervals and leave
room for endpoint caps; explicit user bounds remain exact. Tick labels are spaced
using rendered widths and small nonzero bounds retain useful precision.

Standard random univariate results show package prediction limits, with PI headings
and a scale/interpretation note. Overall-effect Z/t statistics and subgroup QM/F,
df and P appear in structured tables. These reuse established metafor results;
original estimation, inclusion, inference and numerical oracles are unchanged.
RevMan already supplies weights, totals and heterogeneity/overall-effect lines;
this round preserves that capability and corrects the Z/t label. It does not add
weights to every other style or invent unavailable tests.

Cumulative figures name the study added and k. Omission figures use All studies
and the actual omitted name. Bubble legends identify weighted size and the report
explains its rescaling. Report/figure/table exports use outcome/task context in their
names and feedback reflects the latest action. Reports include the existing project
filename and actual arm names in ratio-scale explanations.

Shared calculator sizing fits the displayed glyphs, preserves leading signs/digits
and permits expansion. Automatic grid sizing gives spare room to study names while
respecting user widths. Local inclusion/derived-cell and covariate guidance explains
existing behavior. Delete study is separated from Copy/Paste and names its target.
Plot-editor headings and visibility checkboxes are explicit. Small-study task names
and the third-party NOTICE link are consistent.

## Plan reconciliation

| Item | Status | Commits and evidence |
|---|---|---|
| P01 | Done | `7e09ef7`, `d01c803`, `219ba37`, `5a3ee2a`; clinical-summary, zoom, CSV-entry and mixed-method native evidence; failed triggers retained |
| P02 | Done for demonstrated paths | `f8b89df`, `76a7e33`; metric/moderator and finite-range renderer tests, native top/bottom captures, complete 300-case visual matrix |
| P03 | Partial | `692285d`, `7201aec`, `e5f35bf`, `0c1043a`; native cells, CSV/clipboard equality and 32 public-package comparisons. Legacy free-form R output remains selectable wrapping text; HR/IRR moderator-test printout is not yet a native coefficient table |
| P04 | Partial | `450de28`, `3fa0cd2`, `082f97d`; contextual report/export names, existing RevMan annotations, row/k and bubble semantics. Project identity is in reports/export names rather than every figure; no invented clinical benefit direction or exposure unit |
| P05 | Partial | `e5f35bf`, `450de28`; calculator/grid/structure/editor native evidence. Existing system palette/font retained; broad light-theme, screen-reader and OS-DPI qualification remains outstanding |
| P06 | Verification in progress | Exact completed commands/results are in RUNS.json; final package/matrix completion and reviewed screenshot index will be reconciled before handoff |

## Re-audit findings and ranked next round

| ID | Status | Result / remaining limit | Evidence |
|---|---|---|---|
| RG01 | Done | Clinical-first joint diagnostic report, wrapping prose; dispatcher metadata fixed at source | clinical-summary before/after; corrected joint and SROC drives |
| RG02 | Done | Independent view zoom; disabled Fit width in report | zoom before/after; native UX at 125/150/200% Qt scale |
| RG03 | Done | Metric-specific model/estimator/inference associations; mixed DL/REML drive | diagnostic-methods before/after; recorded primary and LR/DOR parameters |
| RG04 | Done | Pinned CSV instructions, entry focus/reset and safe timer lifetime | CSV-entry before/after; teardown failure/pass logs |
| N01 | Done | Entered-effect/coefficient and selected metric headings | generic-heading and coefficient-heading; all-style producer tests |
| N02 | Done | Measured/wrapped diagnostic covariate and reference labels | diagnostic-moderators; Reitsma renderer/authority tests |
| N03 | Done for demonstrated paths | Finite automatic intervals, endpoint room, tick spacing and adaptive precision; explicit clipping remains deliberate | continuous/single-arm before/after; renderer and 300-case matrix |
| N04 | Partial | Native tables and report cells from producer arrays, matrices and nested fields; legacy free-form package printouts remain prose | native-table and report; copied/exported cells in UX steps |
| N05 | Done for main binary/continuous/diagnostic routes | Package QM/F/df/P table beside subgroup results; existing HR/IRR test stays in its report | subgroup-report/figure/test table; independent output authorities |
| N06 | Partial | Project/report identity, actual arm-scale explanation, export names, latest-action feedback. Per-figure project/direction/unit metadata not added | report, native export steps and decoded outputs |
| N07 | Partial | Study added/k, Study omitted/All studies and weighted-size legend; raw legacy report row identifiers retained for the frozen contract | cumulative/omission/regression captures and unchanged numerical fields |
| N08 | Partial | Complete calculator previews, study-name room, local colour semantics and separated Delete. Input modes remain the established modes | calculators/workspace; ratio delete/undo/reopen drives |
| N09 | Partial | Local grid and covariate prerequisites; existing results navigation polished. No new navigation subsystem | workspace/structure/quick-start native evidence |
| N10 | Partial | Editor columns, Estimate, Small-study effects and actionable NOTICE link. Browser handoff not qualified | setup/editor/small-study native drives; About GUI tests |
| N11 | Done | Complete effect/CI glyphs in diagnostic preview | diagnostic-calculator before/after; actual glyph-width E2E assertions |

Ranked items 1–7 map to RG01/N04, N01/N02, N03, N04, N05, RG02/RG04 and
RG03 respectively. Item 8 is partial (N06/N07), item 9 is partial (N08/N11) and
item 10 is partial: native keyboard table/copy/export and Qt scale factors
1.25/1.5/2 are exercised, but these are not OS display-scaling or screen-reader
qualification. NVDA/Narrator, Windows High Contrast, multi-monitor DPI, complete
keyboard-only traversal and light-theme qualification remain unqualified.

## Statistical safety

[NUMERICAL-EQUIVALENCE.json](NUMERICAL-EQUIVALENCE.json) records every original
field: 415 fields across 11 cases are exactly equal before/after, maximum absolute
difference zero. All 91 independent authority cases are identical before/after.
The frozen contract SHA is `9e16077c10f308e7bcd44ea6287605a2361fc62fd8cca44727f65faa43c9ea56`;
the baseline/oracle directory has no changes.

The strict golden command intentionally still exits 1: 447 comparisons pass,
13 pre-existing accepted exceptions remain and 14 are classified as text/artifact
drift. There is no numerical-drift classification. Reports, labels and figures
were intentionally changed. No oracle, tolerance or exception was regenerated to
make this check green. Newly displayed PI, overall-effect and subgroup statistics
have 32 independent metric/inference comparisons in
[output-authorities.R](output-authorities.R) and its result JSONs.

## Deliberately skipped

No network/Bayesian/GRADE/risk-of-bias or new plot family. No new estimator or
revised existing CI. No persistent history/tree, re-run-from-results, remembered
per-dataset defaults or forest sorting subsystem: output correctness and shared
controls offered clearer value this round. Existing workspace ordering is retained
and explained. No fabricated benefit direction, person-time unit, AUC CI or PI
back-transform that needs an unspecified new-study sample size. No OS settings,
system R libraries or user projects were changed.

## Evidence and failures

[RUNS.json](RUNS.json) retains exact argv, timestamps, revision, environment, exit
status and log digests. [NATIVE-INDEX.json](NATIVE-INDEX.json) points to complete
hash-checked bundles containing inputs/projects, runtime, steps, plots and exports.
The selected before screenshots are from the original native re-audit at the
baseline; final after captures use shown HWNDs and QScreen.grabWindow. Early
round-two QWidget captures are not claimed as HWND evidence.

Earlier failures are retained, including initial DLL-path/Windows-locale setup,
missing exported predict generic, invalid PFT tick filtering, report/table geometry,
partial sequential labels, obsolete labels/width assertions, expected help-modal
capture, golden-fixture authority stub, CSV teardown and optional model-title bugs,
joint dispatch metadata and finite endpoint caps. The initial full Python runs were
terminated by verified owned PID trees; bounded reruns passed. First R-stack package
tests and a later 80/85 desktop matrix failed; corrected reruns are retained. A
successful final check does not erase these records.
