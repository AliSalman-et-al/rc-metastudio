# Small-study effects analysis

Users reach guided small-study effects analysis through the Publication Bias UI label, inspect eligibility, select procedures, and read package-authoritative results and funnels.

## Sub-features

- `small-study-open`: the main action opens guided configuration.
- `small-study-primary`: the automatic primary asymmetry test runs on included studies.
- `small-study-funnel`: ordinary funnel output renders alongside the report.
- `small-study-extended`: binary/continuous contour, trim-and-fill and extrapolation; diagnostic Deeks have separate matrix drives.

## How to get to it (user POV)

- After opening a project with at least two included studies, choose Analysis > Publication Bias or the matching toolbar button.

## Driving it with Qt E2E

Preconditions: doctor passes; `sample_projects/amino.rcms` has sufficient included raw study data.

- **Counts.** The amino configuration asserts 19 included and 17 eligible studies, with an explanation that two studies with no events in either arm are ineligible for odds-ratio asymmetry tests.
- **Configure.** Run `uv run python scripts/verify_rcms.py small-study-effects`. Trigger `action_publication_bias`; the visible modal is `PublicationBiasDialog`. Enable `ordinary_funnel_check`, record `small-study-configured`, then click the actual OK button.
- **Observe.** Require the failure label to remain hidden, a Results window with a rendered real funnel, and Harbord or Rücker package-method report text. `small-study-results` preserves the report, original plot paths, and retained artifact paths. Its funnel is copied directly into the evidence directory before R removes its session temporary files.
- **Extended procedures.** Run `small-study-binary-extended`, `small-study-continuous-extended`, and `small-study-diagnostic`. The continuous fixture duplicates the six sample studies into a controlled 12-study dataset to reach the >=10-study asymmetry threshold; it is not a clinical dataset. These drives require contour/trim-and-fill/extrapolation result sections or Deeks output and hidden or disabled inapplicable diagnostic controls. Supplement with the R numerical/eligibility lane; these UI assertions are not full independent asymmetry numerical proof.

## Gotchas

- Publication Bias is a navigation label. Results do not establish a bias-present/bias-absent verdict.
- The primary asymmetry test is distinct from exploratory asymmetry tests and the pooled display model.
- Eligibility is computed by RCMetaR for the included eligible study set; do not silently drop individual studies or guess availability from the UI.
- A diagnostic Deeks effective-sample-size funnel is distinct from an ordinary or contour-enhanced funnel.
- The original baseline proves one binary automatic method and ordinary funnel. Extended drives do not establish every eligibility route, effect measure or presentation option below.

## Procedures and eligibility routes

Source owners: `publication_bias_dialog.py:_preview_request`, `_update_controls`, `_request`, `run`; `r/RCMetaR/R/publication_bias.R`. The UI has no per-test selector: R eligibility selects all available methods. Configure the dataset/metric to reach each required route rather than inventing a checkbox.

| Data/metric | Required automatic route |
| --- | --- |
| Two-arm raw OR, >=10, low REML tau² <=0.1 | Harbord primary; Rücker/Peters additional |
| Two-arm raw OR, >=10, high tau² | Rücker primary; Harbord unavailable with reason; Peters additional |
| Raw two-group SMD, >=10 | Pustejovsky–Rodgers primary; ordinary Egger sensitivity |
| MD/generic compatible effects, >=10 and varied standard errors | Classical/mixed-effects Egger and Begg |
| RR/RD/one-arm or otherwise unsupported primary measure | Descriptive output and explicit unavailable primary; no silent OR substitution |
| Diagnostic complete counts, >=10 and varied ESS | DOR-context Deeks; ordinary/contour/extrapolation disabled; trim-and-fill sensitivity group hidden |
| k=4, k=2, constant SE, missing raw SMD or diagnostic counts | Explicit unavailable reasons; supported descriptive behavior remains usable |

Use `context_label` and `automatic_test_label` to capture family/metric/included/eligible counts and primary/additional identity. Exclusion changes must update eligibility; do not silently drop eligible studies.

## Configuration and recovery recipe

Trigger `action_publication_bias`. Set `ordinary_funnel_check`, `contour_funnel_check`, `contour_levels_edit` (e.g. `85,95,99`), or diagnostic `deeks_funnel_check`. Exercise `sampling_confidence_combo`, `include_tau2_check`, `correction_policy_combo`, `style_combo`, `point_size_spin`, `pooled_overlay_check`, `reference_line_check`, and `label_policy_combo` after corresponding changes.

Trim-and-fill uses `trim_fill_check`, `trim_fill_estimator_combo` (L0/R0), `trim_fill_side_combo` (auto/left/right), `trim_fill_model_combo` (random/common). OR/SMD automatic side produces separate left/right sensitivity scenarios; MD package-auto is a single scenario. Verify imputed counts, augmented effects and warnings, not merely a funnel filename. `extrapolation_check` adds the separate extrapolation report.

Capture configuration and click `button_box` OK. Require hidden `failure_label` and the expected semantic sections: `small-study.data-eligibility`, `small-study.tests`, `small-study.method-details`, `small-study.methods-not-applicable`, `small-study.extrapolation`, and `small-study.trim-and-fill` or `.left`/`.right` as applicable. Require real retained `small-study.funnel.*`, `small-study.contour_funnel.*`, `small-study.deeks_funnel.*`, and trim-and-fill images. Copy `.data/.res/.params` and temporary funnels before R quits.

Invalid contour levels must keep the modal recoverable, show `failure_label`, re-enable OK, preserve the project, and succeed after correction. Observe and dismiss the expected error specifically; other dialogs still fail the drive. Diagnostic label policies only offer None/All; no pseudo-confidence/tau²/pooled overlays. Funnel presentation edits must preserve fitted statistics, Deeks ESS geometry and trim-and-fill augmentation.

## Statistical oracle requirements

`test-publication-bias.R` and the R-stack test procedure identity, routing, preparation and regeneration. They are not independent numerical oracles for all procedures. When statistical behavior changes, construct inputs separately and compare test statistic, coefficient/SE, p, df, interval, k and corrections to pinned `meta::metabias`/`metafor::regtest`/`metafor::ranktest` calls as appropriate. For trim-and-fill compare package fit and augmented inputs; for extrapolation compare the fitted regression and target prediction. For Deeks independently check ESS=`4*nDiseased*nNonDiseased/(nDiseased+nNonDiseased)` and its inverse-square-root predictor. Record exact calls/package versions and tolerances; agreement of two RCMS helper calls is not an independent oracle.


## HR and IRR

See [ratios.md](ratios.md) for the compact input, original-source persistence, analysis, plot and small-study workflows. Run `ratios-hr` and `ratios-irr` after changes affecting these families; the broader shared-change lane remains required.

The native nine-study IRR sample drive also exercises invalid contour levels (`95,100`), the explicit error, enabled OK after dismissal, correction to `85,95,99`, and successful ordinary/contour results. The current error presentation uses the generic unexpected-error dialog and leaves the busy indicator visible until retry; record this presentation limitation separately from successful recovery. This native evidence does not turn that recipe into an automated test.
