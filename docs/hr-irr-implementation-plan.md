# HR and IRR implementation plan

This plan consolidates the accepted design from the grill-with-docs interview. ADR-0014 through ADR-0016 and `CONTEXT.md` own the decisions and terminology. `docs/hr-irr-metafor-review.md` records the package documentation review. The implementation is present; verification status and retained evidence are recorded in [hr-irr-verification.md](hr-irr-verification.md).

## User behavior

- New Dataset offers one Time-to-event and event rates entry, with HR/IRR variants on the existing metric page and distinct persisted families. Existing projects keep their behavior; a project contains one outcome family.
- HR accepts a reported positive ratio and CI with its source confidence level, or a log effect and positive SE. IRR accepts the same reported forms and raw nonnegative integer events with positive person-time per group.
- IRR studies can mix raw and reported input modes in one analysis. If both are present, require an explicit persisted source choice; preserve the inactive inputs and never fall back from an invalid selected source.
- Each raw comparison records one person-time unit for both groups. Units may differ between studies; there is no automatic conversion. Person-time is never treated as sample size.
- The default table retains the usual three ratio/bound columns, with four raw columns additionally for IRR. Original scale, source confidence, source choice, and units are edited in a conditional study dialog. CSV metadata is optional with documented defaults; hiding it must preserve copy/paste alignment and original-input persistence.
- Reported input retains its original scale, estimate, bounds, and source confidence level. Source confidence defaults to 95% and is independent of output confidence.
- Reversing the same comparison negates its canonical log estimate, reverses/negates log interval bounds, and preserves SE/source; ratio displays consequently show reciprocals. It does not infer comparisons between other groups or independent effects within a study.
- Adjustment annotations use existing optional study covariates. The reviewer chooses the reported estimate; RCMS does not choose an adjustment set or automatically combine multiple adjusted/unadjusted alternatives.

## Analysis contract

The canonical study effect is a log ratio with log-scale SE (or equivalent variance). Use metafor 5.0-1 for Wald conversion, raw IRR effect construction, ordinary models, and regression, and meta 8.5-0 for its existing small-study effects authority. Conversion uses `conv.wald(transf=log)` with the supplied per-study source confidence. Invalid completed inputs fail validation; package symmetry warnings remain visible and preserve the computed result. Known non-Wald intervals require a supplied log-effect SE.

Raw IRR effect defaults are `escalc(measure="IRR", add=0.5, to="only0", drop00=TRUE)`. Correction changes both event counts of an affected study and never person-time. Expose the correction amount and applicable package-defined targets; preserve explicit double-zero handling and identify excluded studies. Prepare effects once for the requested included study set, including resolving conditional correction targets before cumulative/omission/subgroup refits, so the same study inputs do not change between those refits.

Mantel–Haenszel uses `rma.mh(measure="IRR")` with original counts/person-time for pooling. Pass display-effect correction separately from the pooled-count settings; do not pre-correct the pooled counts. Preserve the package's separate MH test behavior and explain its test correction distinctly. Require complete selected raw input for every included study; reported-selected studies cannot be silently dropped or switched to raw mode. A subset with zero total events in either arm has a non-estimable pooled IRR; retain its label and reason, including single-study sequential steps, without an inverse-variance fallback.

| Workflow | HR | IRR inverse variance | IRR Mantel–Haenszel |
| --- | --- | --- | --- |
| Fixed-effect pooling | Yes | Yes | Yes |
| Random-effects pooling with existing estimators/inference | Yes | Yes | No |
| Cumulative / leave-one-out | Yes | Yes | Yes; non-estimable steps disclosed |
| Subgroup summaries | Yes | Yes | Yes |
| Subgroup moderator/difference tests | Existing supported IV tests | Existing supported IV tests | No implied moderator test |
| Meta-regression, predictions, conditional means | Yes | Yes | No |
| Existing bootstrap/permutation options | Where supported by existing IV workflow | Where supported by existing IV workflow | No implied new procedure |
| Small-study effects | Generic log-effect procedures | Generic log-effect procedures | Raw-MH fit does not replace those procedures |

Poisson GLMM, HR reconstruction from log-rank/Kaplan–Meier/IPD, mixed-family projects, dedicated adjustment management, and new estimators are outside this release.

## Results and small-study effects

Use ratio-scale estimates and intervals with log-axis geometry in forests, sequential plots, and applicable predictions. Keep moderator coefficients, SEs, and inference on the log scale and add exponentiated coefficients/intervals with clear multiplicative-change labels. Do not exponentiate SEs or label a moderator multiplier as a study HR/IRR. Prediction and confidence intervals remain distinct, and heterogeneity keeps its analysis-scale meaning.

Funnels use log effects and log-effect SEs; ratio labels may be displayed on the horizontal axis. Significance contours use null zero. Regression residuals retain residual labels. Apply these conventions to regenerated plots, editors, saved parameters, and exported figures as well as the initial results.

Classical Egger is primary under the existing R-owned eligible-set, study-count, positive-SE, and precision-variation rules. Begg and mixed-effects Egger are exploratory; trim-and-fill is optional sensitivity analysis. Preserve all applicable current eligibility conditions and explanatory warnings. Binary/diagnostic/SMD-specific methods are unavailable for these measures. Prepare and disclose one eligible study set for all accepted small-study procedures, including identities/reasons for excluded zero-event rows. A comparison with a raw-count MH result must disclose any difference in study sets. Do not characterize an augmented estimate as bias correction.

## Implementation sequence

1. **Domain, persistence, and input contracts.** Extend metric/family/subtype enums, typed estimate/source records, raw IRR groups, schema validators, and project adapters. Use a new structured project format version with a deterministic migration from released version 1 rather than changing the meaning of released schemas. Preserve stable identities and existing source precedence. Add the wizard, table/calculator entry, source/CI/unit controls, and explicit CSV/import/export fields. Keep invalid paste/import transactional and support undo/redo.
2. **R boundary and effects.** Extend classes, serialized conversion, dispatch, subsetting, and eligibility for HR/IRR. Reconstruct the selected source at the analysis boundary, retaining original inputs and warning provenance. Reuse generic inverse-variance fitting and shared summaries; implement raw IRR MH by direct package call with separate display/pooling zero handling.
3. **All applicable analysis workflows.** Wire standard, cumulative, leave-one-out, subgroup, meta-regression, predictions, and current supported advanced options. Preserve method-specific inference, study sets, non-estimable states, and no-fallback behavior.
4. **Displays and small-study effects.** Replace existing hard-coded OR/RR-only transformation gates where HR/IRR need the same ratio behavior. Update ordinary and small-study figures, comparisons, tables, regression multipliers, plot regeneration/editing, and exports. Deliberately route generic meta-based procedures with R-owned eligibility.
5. **Verification and documentation.** Extend real Qt/R drivers and independent authority comparisons for the new paths. Update the verification feature map, project-format docs, samples, and user-facing input/method guidance based on demonstrated behavior.

Relevant modules include `meta_globals.py`, `analysis_unit.py`, `project_domain.py`, `project_adapter.py`, `dataset_analysis_domain.py`, `dataset_table_model.py`, `workspace_editing.py`, `main_wizard.py`, `csv_import.py`, `r_bridge.py`, project schemas, and RCMetaR classes/core/method/output/plot/regression/small-study modules. Introduce shared helpers only where inspected duplication makes them simpler than explicit extension; do not build a generic effect-type framework for hypothetical future measures.

## Required evidence

- Direct pinned-package numerical comparisons for HR reported effects, IRR reported effects, raw IRR, and mixed IRR sources; nondefault CI levels, heterogeneity estimators, and inference; all cumulative/omission/subgroup rows and moderator shapes; applicable meta-based asymmetry/trim-and-fill output.
- Single-zero, double-zero, all-zero arm, no-correction, correction-target, single-study and insufficient-degrees-of-freedom cases. Check exact study identities/counts, weights, warnings, and non-estimable rows. Distinguish MH pooling from its study-effect display and separate test.
- Prove that changing output confidence leaves study SEs/weights unchanged; source-CI conversion uses the complete log interval width; rounded intervals preserve warnings; invalid/known unsupported input has actionable recovery.
- Prove explicit source selection, inactive-source persistence, no silent fallback, reciprocal direction including repeated reversal, and person-time units that differ across studies but match within each comparison.
- Real New Dataset, table/calculator, CSV entry, transactional invalid paste/import, undo/redo, save/reopen, covariates, inclusion changes, and every applicable analysis action. Save/reopen must preserve sources, original CI/scale/confidence, units, group identities, and analysis/plot parameters.
- Render and inspect ratio geometry, null references, exponentiated coefficient labels, funnels/contours, and plot editor/export/regeneration behavior. Preserve log SEs and distinguish prediction intervals.
- Run `.agents/skills/verify-rcms/scripts/verify_all.py --full` with the current-source installed RCMetaR in a test-owned pinned runtime, plus the newly targeted HR/IRR drives. Record runtime/source provenance and durable numerical/action/result evidence. Preserve the released golden oracles and existing project/workflow tests.

Success means the new families work across all applicable product workflows with package-authoritative numbers, correct scales, preserved input semantics, explicit eligibility, and real desktop/persistence evidence. Existing binary, continuous, and diagnostic behavior must remain verified. Consult the verification report for demonstrated paths and limits; this plan is not a test result.
