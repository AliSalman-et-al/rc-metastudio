# Hazard ratios and incidence rate ratios

Read [the input/method guide](../../../../docs/hr-irr.md), ADR-0014 through ADR-0016, and the metafor review before changing this contract.

Run `uv run python scripts/verify_rcms.py ratios-hr` and `ratios-irr` against current-source RCMetaR in the pinned test-owned runtime. The shared data-type change also requires `verify_all.py --full`.

## Exercised paths

The real New Dataset wizard selects the shared Time-to-event and event rates entry, then HR/IRR on the existing metric page; Back/Next preserves the chosen family. A Matplotlib SVG supplies the tile icon; every metric choice is text-only. Actual row-header dialogs enter the first two studies and must enable analysis. The compact table hides input metadata; conditional calculator fields and widths are observed. The dialog supports ratio/CI and log/SE, checks missing SE, converts the estimate on format changes, and preserves Cancel. Source confidence edits exercise undo/redo. Context-menu deletion of Study 13 must remove the displayed row and original record, both before and after sorting; undo/redo and save/reopen retain the intended study identity.

Both full original-input and compact default CSV imports reach the production preview/import path, preserving advanced fields or assigning documented defaults. Preview and workspace hide metadata; copy/paste crosses that hidden region into covariates. Invalid paste rolls back atomically. Saved projects reopen and comparisons reverse twice while preserving original inputs.

Fixed/random pooled values, nondefault output confidence, every cumulative/omission/subgroup row, and numeric moderator coefficients/SE/CI are compared with independent public `metafor` calls. Classical Egger coefficient/SE is compared with `meta::metagen` / `meta::metabias`. Ordinary/contour/trim-and-fill results expose eligibility; plots are decoded. IRR exercises single/double zeros, mixed sources, every raw MH main/sequential/subgroup path, direct numerical comparison for every finite MH pooled/sequential/subgroup row, and a labelled non-estimable first cumulative step.

Forest, cumulative, leave-one-out, subgroup, regression and contour editors exercise Apply/reopen/Cancel, ratio geometry and four decoded export formats. Runtime, inputs, displayed numerical comparisons, screenshots, projects, CSVs, plot parameters and decoded exports survive under each run's evidence directory.

The dedicated `ratios-samples` scenario opens both bundled metadat examples (`Pignon2000-HR.rcms` and `NielWeise2008-IRR.rcms`). It checks every source row and stored input, compares fixed/random results directly with metafor (and raw MH for IRR), compares every HR chemotherapy-timing subgroup with metafor, observes the nine-study IRR asymmetry limit with usable descriptive funnels, and saves/reopens separate copies with identical project content. Original HR years stay blank; IRR uses catheter-days and has nine studies. See `sample_projects/README.md` for source attribution and reproducible generation.

## Native and remaining scope

Complete double-zero IRR rows show Not estimable and interval dashes, with an explicit tooltip. `options-zero-cells` also drives the shared formatter through undefined SMD, numeric MD, save/reopen, correction to finite SMD, and incomplete-input recovery. Missing input remains blank; display labels never replace original numeric inputs.

Native Windows driving uses separate test-owned projects/settings and the ordinary app entry point. Review compact workspaces, raw/reported/log dialogs, actual analysis results and funnel layouts for clipping, spacing, scale labels, focus and scroll access. Pair each action with its observed result and save a replayable evidence record.

CSV automation starts at the import page and controls the picker return; it does not prove every earlier import entry point. The targeted moderator is numeric; factor/interactions and legacy bootstrap/permutation are not claimed as newly demonstrated HR/IRR GUI workflows. Backend inference coverage does not prove every UI estimator/inference pair. Windows source evidence does not qualify release packages, other operating systems, or fractional-DPI displays. The [verification report](../../../../docs/hr-irr-verification.md) owns actual run status and limitations.
