# General fit-contribution presentation rule

Replace both MH/RD branches with one shared standard-study effect calculation:
1. Use the fit's finite individual effect and variance when available.
2. When the fit's individual effect is unavailable but its weight is positive, retain the prepared display effect/variance.
3. With no finite fitted effect and no positive fit weight, mask the display effect and interval as Not estimable.

The report and binary forest consume that same effect vector. Both journal styles derive Not-estimable flags from it; their separate raw-total heuristics are removed. No method class or measure name participates in this decision. The single-study path retains its existing interval contract.

## Ten-fit before/after proof

`proof.R` captures the six original QA studies for OR/RR/RD with MH/fixed IV/random IV and Peto OR (ten supported combinations), including the rendered study-effect vectors, flags, fitted weights and display intervals. Peto RR/RD are unsupported and are not invented as extra fits. Before capture used the installed a2886609 implementation; after capture uses this worktree's newly installed source. `compare.R` asserts every fit field and weight is exactly identical (elapsed time and captured execution environment excluded), every plot weight equals the fitted weight, and every row satisfies the contribution rule. It writes all **60 study rows** to `ten-fit-table.tsv` with paired before/after effect/CI, weight, Not-estimable flags, and plot/report weight labels. `comparison.log` also prints the ten double-zero Gamma rows.

All 60 displayed rows, weights and flags remain the same as the previously corrected presentation, while the implementation no longer branches on MH/RD. All ten fitted results and their weights remain exactly unchanged. Direct metafor coefficient/weight checks are retained by proof.R.

Commands from repository root (source `/home/ali/.t3/qa-env/ENV.sh`):
```
$RCMS_R_HOME/bin/Rscript artifacts/qa-r1/peto-null/contribution-rule/proof.R $PWD/build/rcmetar-lib artifacts/qa-r1/peto-null/contribution-rule/before.rds
$RCMS_R_HOME/bin/R CMD INSTALL -l $PWD/build/rcmetar-lib r/RCMetaR
$RCMS_R_HOME/bin/Rscript artifacts/qa-r1/peto-null/contribution-rule/proof.R $PWD/build/rcmetar-lib artifacts/qa-r1/peto-null/contribution-rule/after.rds
$RCMS_R_HOME/bin/Rscript artifacts/qa-r1/peto-null/contribution-rule/compare.R
```

The first command runs BEFORE installing the changed source; do not overwrite the saved before.rds with a second post-change run. R code changes are presentation only, without refitting or mutating the returned fit.

## Genuinely non-estimable rows

MH OR/RR Gamma has no finite individual ratio and zero weight: Not estimable with **0.0%** in both plot and report. MH RD Gamma has 9.829528% weight: finite RD=0 with its corrected CI. Peto Gamma's fitted individual effect is finite despite zero weight, so it retains that effect and 0.0%. A zero weight alone does not make an otherwise finite effect Not estimable.

The existing MH/Peto E2E assertions are kept and strengthened: actual SVG weight nodes are sorted by visual Y position and compared with each report row; every Not-estimable report row must have zero weight. The existing MH RD/BMJ/axis-validation drive is retained unchanged.

Qualification: strict Ty (win32, exact command and generated paths) passes before GUI. R ratio tests: 390 pass before the redundant raw-total predicate removal; final direct ten-fit proof and three E2E drives run after installation. Each *-final.log identifies its complete durable evidence directory with runtime identity, manifest, inputs, actual plot/report outputs and action/assertion receipts. Initial drives/logs are retained separately. Numerical and golden references are untouched. No new native/theme matrix is claimed for this internal refactor; the previously retained native proof exercises the same displayed results.

Final results: all three current-source E2E manifests pass (results.json), and current-source test-ratios.R passes 390 assertions with no failures/warnings/skips after the shared predicate cleanup. No complete R/desktop/native matrix rerun for this refactor; CI owns the broader qualification.
