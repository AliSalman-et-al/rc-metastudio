# Small-study effects analysis

Users reach guided small-study effects analysis through the Publication Bias UI label, inspect eligibility, select procedures, and read package-authoritative results and funnels.

## Sub-features

- `small-study-open`: the main action opens guided configuration.
- `small-study-primary`: the automatic primary asymmetry test runs on included studies.
- `small-study-funnel`: ordinary funnel output renders alongside the report.
- `small-study-extended`: Deeks, contour, trim-and-fill sensitivity analysis and extrapolation require separate drives.

## How to get to it (user POV)

- After opening a project with at least two included studies, choose Analysis > Publication Bias or the matching toolbar button.

## Driving it with Qt E2E

Preconditions: doctor passes; `sample_projects/amino.rcms` has sufficient included raw study data.

- **Configure.** Run `uv run python scripts/verify_rcms.py small-study-effects`. Trigger `action_publication_bias`; the visible modal is `PublicationBiasDialog`. Enable `ordinary_funnel_check`, record `small-study-configured`, then click the actual OK button.
- **Observe.** Require the failure label to remain hidden, a Results window with a rendered real funnel, and Harbord or Rücker package-method report text. `small-study-results` preserves the report, original plot paths, and retained artifact paths. Its funnel is copied directly into the evidence directory before R removes its session temporary files.
- **Other procedures.** For a change to eligibility, Deeks, contour editing, trim-and-fill, extrapolation, or exploratory methods, extend the driver from the corresponding configuration controls. Run the full R lane for package calls and statistical identity as well.

## Gotchas

- Publication Bias is a navigation label. Results do not establish a bias-present/bias-absent verdict.
- The primary asymmetry test is distinct from exploratory asymmetry tests and the pooled display model.
- Eligibility is computed by RCMetaR for the included eligible study set; do not silently drop individual studies or guess availability from the UI.
- A diagnostic Deeks effective-sample-size funnel is distinct from an ordinary or contour-enhanced funnel.
- This baseline proves only one binary automatic method and ordinary funnel. It does not prove the extended procedures or every effect measure.
