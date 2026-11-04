# RD eligibility, BMJ method and axis-bound follow-up

Environment: source `/home/ali/.t3/qa-env/ENV.sh`; export `PYTHONPATH=$PWD/src:$PWD`; install `R CMD INSTALL -l $PWD/build/rcmetar-lib r/RCMetaR` using `$RCMS_R_HOME/bin/R`, then prepend that library to RCMS_R_LIBS and R_LIBS. Source files and installed namespace correspond to this branch. Strict Ty (win32 target, all source paths) runs before GUI; exact commands/transcripts are retained.

## Root cause and display policy

Public metafor rma.mh's default drop00 is c(TRUE,FALSE): the individual effect calculation omits double-zero tables even for RD, but MH RD pooling retains them with positive weight. On the exact six-study QA data Gamma gets 9.829528% weight and contributes RD=0. OR/RR MH double-zero tables have zero weight and no finite individual ratio; Peto's application-specific drop00=FALSE retains its corrected individual estimate with zero weight. IV fits use their existing corrected effects and fitted weights.

The baseline QA package already marks MH RD Gamma Not estimable and suppresses its positive plot weight (before.log), proving the forest bug predates this branch. This branch's earlier yi.f alignment additionally masked the corrected RD report effect; it is now exempt for MH RD. RD display reuses the already computed corrected data effect/CI, including the finite RD=0 interval; every surface uses weights(res) without blanking weights based on the separate individual-effect omission mask. Fit objects are not mutated.

BMJ no longer hard-codes IV or infers random effects from the stale rm.method parameter. Header measurement and drawing use the same fit-derived method as RevMan, resolving sequential/subgroup overall fits where applicable.

The editor validates both axis bounds as finite numbers (or blank/default) before emitting its render request. Invalid input stays in the dialog with a plain inline message and unchanged plot bytes.

## Mechanical statistical proof

From repository root:
```
$RCMS_R_HOME/bin/Rscript artifacts/qa-r1/peto-null/rd-followup/proof.R /home/ali/.t3/qa-env/rcmetar-lib artifacts/qa-r1/peto-null/rd-followup/before.rds
$RCMS_R_HOME/bin/Rscript artifacts/qa-r1/peto-null/rd-followup/proof.R $PWD/build/rcmetar-lib artifacts/qa-r1/peto-null/rd-followup/after.rds
$RCMS_R_HOME/bin/Rscript artifacts/qa-r1/peto-null/rd-followup/compare.R
```

proof.R includes exact six-study counts, OR/RR/RD, MH, fixed and random IV, plus Peto OR (10 fits). Every fit coefficient is identical to a direct public metafor call; weights match within 1e-12 (floating-point representation), using the same display digits. before.rds/after.rds and comparison.log prove **exact equality of every fitted field and every weight before/after**, excluding only elapsed runtime and the captured execution environment. No numerical reference or tolerance was modified.

Gamma MH RD's plotted weight changes NA -> 9.829528%; its fitted weight is identical. Fitted pooled estimates, SEs, tests, heterogeneity, intervals, counts and all weights remain unchanged for all ten fits.

## Presentation fields / golden scope

- MH RD standard forest: corrected double-zero estimate/CI and original positive weight replace Not estimable / blank weight; report retains the same corrected effect/CI and original weight. Its held effect_display fields are finite again. Plot limits may include the restored interval.
- Standard forest weights for omitted ratio rows now display the original 0.0% instead of blank, matching reports.
- BMJ header fields (and their measured widths): stale `IV, random` / `IV, fixed` -> fit-derived `M–H, Fixed`, `Peto, Fixed`, `IV, Fixed`, `IV, Random`; remove the second hard-coded IV prefix.
- Axis validation message is new; invalid edits do not change any plot fields.

No frozen golden reference was regenerated. The eleven frozen standard/extended cases do not select fixed MH RD or BMJ; existing corrected IV zero rows retain their weights. Review any CI-reported presentation field explicitly rather than updating numerical references.

## Real-app proof

`python scripts/verify_rcms.py plot-workflow-mh-rd`: actual Qt/R analysis, double-zero MH RD fixture; compare every SVG weight in row order with report weights at plot precision and check the rounded total; actual Edit plot Apply rejects abc without changing bytes; change to BMJ and assert M–H, Fixed. The original OR MH/Peto scenarios are rerun separately. Each log identifies its full durable evidence directory, with manifest, runtime, raw inputs, figures, copy/PDF/DOCX reports and action/assertion receipts.

The first attempt extending options-zero-cells exceeded its existing 120-second bound; the targeted drive is a separate scenario to keep the original workflow bounded. A later targeted rerun also timed out under shared host contention, without an assertion failure. Failed evidence is retained; the final run result is reported separately. Superseded R-suite transcript retained as r-tests.log; final installed-source qualification is r-tests-final.log.

Native ui.py session `peto-rd` uses this worktree and installed library. `six-study-rd.rcms` is an owned copy of the round-2 project with only selected metric changed to RD. Native screenshots retain the six-study data, MH setup, restored Gamma effect/9.8% weight, BMJ method header and invalid-bound response. Full crossed theme/font matrix is not claimed.

## Final observed results

- Final targeted `plot-workflow-mh-rd` drive: passed. Its ordinary plot-workflow lane allows 240 seconds for initial rendering plus regeneration. SVG weight nodes are ordered by screen Y position before comparing each report row (R emits those nodes bottom-up).
- Original standard OR MH/Peto drives: both passed, command transcripts mh-or.log / peto-or.log.
- Full R testthat run: 1827 passed, 3 failures, zero warnings, one existing opt-in skip. All three failures were the same obsolete `is.na(summary$weights[5])` expectation repeated across styles. Replaced it with exact equality of the entire plotted weight vector to `weights(fit)`; focused test-ratios.R rerun: 390 passed, zero failures/warnings/skips. No other R test failed; the full suite was not repeated after this expectation-only correction.
- Strict Ty: passed; focused Results GUI: 65 passed.
- Pre-push wrapper: interrupted with exit 143 after prepare, typing, code health and fast/golden completed (413 passed, 6 skipped), during GUI. Preserve pre-push-final.log; the remaining GUI and packaging stages were rerun directly, with results in gui-final.log and packaging.log. Do not call the interrupted wrapper a passing full command.
- Source formatting-only changes after installation do not alter the R expression tree; all behavioral changes were installed before R proof and final GUI driving.

Final native validation capture: native-validation-visible.png shows the inline message above the action buttons, outside the scroll area. Session peto-rd stopped after proof. The earlier native-invalid-response.png was captured before that visibility correction; it is retained as failure evidence.

Remaining qualification stages completed: full GUI 364 passed / 1 existing skip; packaging contracts 73 passed / 8 existing platform skips. Final strict Ty transcript passes. All pre-push stages therefore have passing observations, but the interrupted aggregate command is not reported as a complete pass.
