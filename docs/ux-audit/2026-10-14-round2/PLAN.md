# RCMS improvement round two

Branch: `ux/audit-improvements`. Baseline: `84fdbc57c42e8399f45c2a33689deea94408c9fe`.
Work is local; commit small logical units, do not push or create a PR.

## Review 1 proof obligations (before implementation)

- Inspect all 14 presentation drifts individually. Refresh only text/figure members
  through the real golden capture producer; preserve frozen numerical fields,
  tolerances, exceptions and descriptor contracts byte-for-byte.
- Forest failures: run-on/padded summary labels, missing weights/totals, misleading
  automatic direction labels, missing overall tests/PI, overlapping footers. Inspect
  native standard binary/continuous/single-arm, subgroup, sequential and diagnostic
  output and exercise all three styles through the maintained forest matrix.
- Report failures: duplicated identity, numeric first-column alignment, wide CI and
  heterogeneity headers, monospace references, configuration before results. Read
  actual Qt report content and native glyphs; preserve producer numerical cells.
- Properties failures: wrong project after changing the main workspace, lost
  method/inference/CI/covariates/diagnostic metric settings, Cancel causing a run,
  changed settings failing to propagate. Reuse the setup dialog with a result-owned
  input snapshot, without persistent history or per-dataset defaults.
- Ordering failures: study/effect/count/weight rows becoming disconnected, changing
  pooled values, subgroup membership changes, missing-year handling, cumulative
  semantics changing. Order presentation rows only after estimation; default is
  the current input table order. Cumulative order stays explicit and fixed.
- The real `review-workflows` desktop drive is written before implementation and
  must fail on the missing Properties action. Existing full desktop, independent
  authority and frozen gates remain required, plus final native captures.
- Evidence cleanup removes only round-2 files from the Git index and ignores raw
  runs locally. Retain review prose, numerical equivalence, curated screenshots
  and minimal reproduction scripts. Do not touch other untracked audit folders.

## Scope update from the user

The user's latest clarification replaces the earlier restriction to existing
output. No new statistical feature types: network meta-analysis, risk of bias,
GRADE, Bayesian models and new plot families are excluded. Existing meta-analysis,
cumulative, leave-one-out, subgroup and meta-regression may be extended for all
supported data types. Newly reported prediction intervals, heterogeneity,
overall-effect/subgroup tests, weights or totals must come from the established
authority package and receive an independent reference-package comparison retained
in evidence. Existing numerical results and frozen oracles remain unchanged.
Re-run-from-results, remembered sensible defaults, forest study sorting and smoother
navigation are permitted where their value beats their implementation complexity;
output quality and the re-audit regressions remain the first priorities. Table
CSV/copy export serializes producer result cells without re-estimation.

## Priorities and proof obligations

1. **P01 — Restore diagnostic reading and truthful controls (RG01–RG04).**
   Clinical diagnostic results lead with the clinical summary, with wrapping prose.
   Text and figure zoom belong to their respective views. Associate every diagnostic
   model, estimator and inference with its metric. Reset CSV entry to the instructions.
   Prove each original trigger in the live Qt/R driver, including text at 200%,
   switching views, Fit width, combined metrics and CSV page re-entry.
2. **P02 — Faithful forest presentation (N01–N03).** Generate metric headings
   from metric/subtype metadata; measure diagnostic moderator labels; include finite
   confidence intervals in automatic ranges; space ticks and preserve small nonzero
   bounds. Follow metafor's authoritative intervals and RevMan's legible tabular
   figure conventions. Explicit user bounds remain explicit. Verify standard,
   cumulative, omission, subgroup and moderator plots, all styles, and long contrasts.
3. **P03 — Structured reports and tables (N04/N05).** Carry the R producer's
   table headers/rows through the existing versioned result boundary, display native
   accessible tables beside wrapping prose, and add table copy/CSV export. Include
   package-owned subgroup-difference statistics, df and P beside within-group
   estimates. Keep full plain-text copy/export. RevMan's report hierarchy and JASP's
   readable results tables are the reference patterns. Prove displayed cells,
   exported CSV, copied text, keyboard actions and independent numerical values.
4. **P04 — Self-contained scientific output (N06/N07).** Improve context-derived
   export names and copy feedback; use Study added/Study omitted/All studies,
   explain study order and bubble size, and present available model/heterogeneity/
   overall-effect information without recomputing inference. Inspect the existing
   RevMan style before adding totals, weights or annotations: reuse its capabilities.
   Give project/comparison identity where the request already owns it. Never infer
   clinical benefit from arm order or invent person-time units.
5. **P05 — Coherent everyday controls (N08–N11).** Fix complete diagnostic
   calculator values, use actual arm names, improve grid width/selection/derived
   guidance, separate destructive context actions, unify small-study task names,
   and clarify existing plot-editor controls. Prefer system palette/font and a small
   consistent spacing/type scale over another theme/configuration layer. Provide
   local covariate guidance where the existing structure dialog can support it.
6. **P06 — Verify and reconcile every finding.** Native before/after captures
   for each changed surface, including all requested plot families and main workflow
   screens. Inspect every selected screenshot for readable glyphs. Run full Python/
   desktop tests, current-source R-stack/build/check, frozen numerical/golden and
   independent authority comparisons before and after. Keep commands, inputs,
   runtime/source provenance, logs, observed results and durable manifests. Update
   the verification map and CHANGES.md with done/partial/skipped, commits and evidence
   for each plan item and RG/N finding. Report failures and coverage limits explicitly.

Before implementation, extend live workflow assertions for the changed observable
behavior. If a separate failure/geometry test is necessary, enumerate its failure
modes and write it before changing production code. Frozen numerical oracles stay
unchanged. Statistical estimation, inclusion and inference are out of scope.

## Deliberate exclusions

- No new estimator, inferred correction, reformulated existing CI, or regenerated
  numerical oracle. Additional reported quantities need package authority and proof.
- No risk-of-bias/GRADE module, review-management subsystem or persistent analysis
   history tree. These need new domain/storage decisions; polish existing result
   navigation first. Re-run-from-results, remembered per-dataset setup and forest
   study sorting are permitted by the latest scope but remain lower priority than
   output correctness and require a simple design and targeted proof.
- No automatic “Favours A/B” for unknown clinical direction, invented exposure units,
  or user-defined units stuffed into labels. Recommend explicit outcome/direction/unit
  metadata separately if the present domain lacks it.
- No OS-wide display/theme modifications, system-library installs or user project
  edits. Native keyboard/Qt scaling/accessible table checks are in scope; actual
  Narrator/NVDA, Windows High Contrast and multi-monitor OS-DPI qualification must be
  reported as unqualified if this session cannot exercise them.
- No broad calculator rewrite, sprawling command palette or new theming framework.
  Adopt useful conventions in existing shared widgets and R plot producers.

## References

- [Original audit](../2026-10-13-native/REPORT.md)
- [Prior implementation](../2026-10-13-implementation/CHANGES.md)
- [Native re-audit and next-round top ten](../2026-10-13-reaudit/REPORT.md)
- [Verification skill](../../../.agents/skills/verify-rcms/SKILL.md)
- Statistical reference documentation and exact before/after commands will be
  retained in this directory as the baseline is established.
