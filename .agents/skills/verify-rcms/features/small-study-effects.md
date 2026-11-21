# Small-study effects analysis

Users open **Small-study effects…**, inspect eligibility, select procedures, and read package-authoritative results and funnels.

## Sub-features

- `small-study-effects` opens guided configuration, runs the automatic primary asymmetry test on eligible included studies, and renders the ordinary funnel.
- The extended binary, continuous and diagnostic scenarios below cover contour, trim-and-fill, extrapolation and Deeks.

## How to get to it (user POV)

- After opening a project with included study data, choose **Analysis > Small-study effects…** or the matching toolbar action.

## Driving it with Qt E2E

Preconditions: doctor passes; `tests/fixtures/desktop-projects/amino.rcms` has sufficient included raw study data.

- **Counts.** The amino configuration asserts 19 included and 17 eligible studies, with an explanation that two studies with no events in either arm are ineligible for odds-ratio asymmetry tests.
- **Configure.** Run `uv run python scripts/verify_rcms.py small-study-effects`. Trigger `action_publication_bias`; the visible modal is `SmallStudyEffectsDialog`. Enable `ordinary_funnel_check`, record `small-study-configured`, then click the actual OK button.
- **Observe.** Require the failure label to remain hidden, a Results window with a rendered real funnel, and Harbord or Rücker package-method report text. `small-study-results` preserves the report, original plot paths, and retained artifact paths. Its funnel is copied directly into the evidence directory before R removes its session temporary files.
- **Vector clipping.** Ordinary, contour, both trim-and-fill scenarios and Deeks
  must use SVG Results artifacts. `ui-fine-tuning` checks their rendered clipping
  through both production Qt loaders at two scales. The dedicated
  [SVG evidence](../../../../docs/maintaining.md#platform-and-rendering-invariants) also covers
  narrow axes, nonwhite backgrounds and vector-only high-resolution PDF painting.
- **Extended procedures.** Run `small-study-binary-extended`, `small-study-continuous-extended`, and `small-study-diagnostic`. The continuous fixture duplicates the six sample studies into a controlled 12-study dataset to reach the >=10-study asymmetry threshold; it is not a clinical dataset. These drives require contour/trim-and-fill/extrapolation result sections or Deeks output and hidden or disabled inapplicable diagnostic controls. Supplement with the R numerical/eligibility lane; these UI assertions are not full independent asymmetry numerical proof.

## Gotchas

- Interpret asymmetry estimates and eligibility in their study context. The report gives no bias-present or bias-absent verdict.
- The primary asymmetry test is distinct from exploratory asymmetry tests and the pooled display model.
- Eligibility is computed by RCMetaR for the included eligible study set; do not silently drop individual studies or guess availability from the UI.
- A diagnostic Deeks effective-sample-size funnel is distinct from an ordinary or contour-enhanced funnel.
- The original baseline proves one binary automatic method and ordinary funnel. Extended drives do not establish every eligibility route, effect measure or presentation option below.

## Procedures and eligibility routes

The Package default checkbox reads meta’s k.min default from its method formal. Unchecking it exposes an explicit minimum of 3 or more; meta itself requires at least 3. No RCMS ten-study gate applies to metafor mixed-effects Egger or extrapolation.

The dialog in `src/rc_metastudio/analysis/small_study_effects_dialog.py` submits eligibility and analysis requests to `r/RCMetaR/R/small_study_effects.R`. R eligibility selects the available procedures. Configure the dataset and metric to exercise each route.

| Data/metric | Required automatic route |
| --- | --- |
| Two-arm raw OR, at least meta k.min (default 10) | Harbord primary; Rücker/Peters exploratory; no RCMS tau² gate |
| Raw two-group SMD, at least meta k.min | Classical Egger primary; Pustejovsky–Rodgers exploratory |
| MD/generic compatible effects, varied standard errors | Classical Egger and Begg follow meta k.min; mixed-effects Egger follows metafor |
| RR/RD/one-arm compatible effects | Package-supported Egger/Begg with effect–SE caveats; no silent OR substitution |
| Diagnostic complete counts, at least meta k.min and varied ESS | DOR-context Deeks; ordinary/contour/extrapolation disabled; trim-and-fill sensitivity group hidden |
| k=4, k=2, constant SE, missing raw SMD or diagnostic counts | Explicit unavailable reasons; supported descriptive behavior remains usable |

Use `context_label` and `automatic_test_label` to capture family/metric/included/eligible counts and primary/exploratory identity. Exclusion changes must update eligibility; do not silently drop eligible studies.

## Configuration and recovery recipe

Trigger `action_publication_bias`. Set `ordinary_funnel_check`, `contour_funnel_check`, `contour_levels_edit` (e.g. `85,95,99`), or diagnostic `deeks_funnel_check`. Exercise `sampling_confidence_combo`, `include_tau2_check`, `correction_policy_combo`, `style_combo`, `point_size_spin`, `pooled_overlay_check`, `reference_line_check`, and `label_policy_combo` after corresponding changes.

Trim-and-fill uses `trim_fill_check`, `trim_fill_estimator_combo` (L0/R0), `trim_fill_side_combo` (auto/left/right), `trim_fill_model_combo` (random/common). Automatic side uses meta's single selected scenario for every metric; the report names the selected side. ma.common follows meta's TRUE default independently of the display model. Verify imputed counts, augmented effects and warnings, not merely a funnel filename. `extrapolation_check` adds the separate extrapolation report.

Capture configuration and click `button_box` OK. Require hidden `failure_label` and check the semantic sections for the selected procedures. Trim-and-fill result sections use `small-study.trim-and-fill.<scenario>`. Retain the rendered images and editable plot artifacts for each requested and supported funnel before R quits.

Invalid contour levels show `failure_label` inline, focus the contour field and leave Run enabled before any progress popup opens. Check that correction succeeds and the project stays intact. Diagnostic label policies offer None and All. The Deeks Results editor omits pseudo-confidence, tau² and pooled-overlay controls. Funnel presentation edits must preserve fitted statistics, Deeks ESS geometry and trim-and-fill augmentation.

## Statistical oracle requirements

`test-small-study-effects.R` and the R-stack test procedure identity, routing, preparation and regeneration. They are not independent numerical oracles for all procedures. When statistical behavior changes, construct inputs separately and compare test statistic, coefficient/SE, p, df, interval, k and corrections to pinned `meta::metabias`/`metafor::regtest`/`metafor::ranktest` calls as appropriate. For trim-and-fill compare package fit and augmented inputs; for extrapolation compare the fitted regression and target prediction. For Deeks independently check ESS=`4*nDiseased*nNonDiseased/(nDiseased+nNonDiseased)` and its inverse-square-root predictor. Record exact calls/package versions and tolerances; agreement of two RCMS helper calls is not an independent oracle.


## HR and IRR

See [ratios.md](ratios.md) for the compact input, original-source persistence, analysis, plot and small-study workflows. Run `ratios-hr` and `ratios-irr` after changes affecting these families; the broader shared-change lane remains required.

`project-round6-polish` opens the nine-study IRR sample and tries four invalid
contour inputs. `contour-inline-validation` records the inline message with Run
still enabled. Enter `90,95,99` and check the rendered contour in
`contour-validation-recovered`. Execution failures use the generic unexpected-error
dialog after the shared running popup closes and its wait cursor is restored.

The extended small-study drives assert that the confidence selector, pseudo-confidence-region checkbox and contour-level editor do not overlap.

The `small-study-effects` drive observes the shared analysis popup while the real service executes, records `small-study-running`, and requires it to be hidden before Results. The popup uses the outcome and effect measure as context; CSV import retains its separate determinate-progress semantics.
