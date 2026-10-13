# RCMS improvement round two

Branch: `ux/audit-improvements`. Baseline: `84fdbc57c42e8399f45c2a33689deea94408c9fe`.
Work is local; commit small logical units, do not push or create a PR.

## Scope update from the user

This round polishes existing functionality only. No new analyses, estimators,
statistics, plot types, analysis options or navigation/workflow subsystem. No
re-run-from-results, per-dataset remembered settings or forest study-sorting feature.
Prediction intervals, heterogeneity, subgroup-difference tests, weights and totals
may be presented only where the existing R producer already computes them for that
analysis. Trace each displayed statistic to that producer; never add a calculation.
Table CSV/copy export serializes existing result cells only. Cut any proposed
annotation or export that would require new statistical computation.

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

- No new estimator, inferred correction, reformulated CI, or regenerated numerical
  oracle. Presentation cannot change the statistical authority's results.
- No risk-of-bias/GRADE module, review-management subsystem or persistent analysis
   history tree. These need new domain/storage decisions; polish existing result
   navigation first. Re-run-from-results, remembered per-dataset setup and forest
   study sorting are excluded by the user's scope update.
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
