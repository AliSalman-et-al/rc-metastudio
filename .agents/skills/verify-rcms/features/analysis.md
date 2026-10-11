# Meta-analysis

Users select included studies, choose a statistical method and parameters, run the analysis, and read package-authoritative numerical results and plots.

## Sub-features

- `analysis-binary`: amino project, binary random-effects analysis.
- `analysis-continuous`: continuous project, continuous random-effects analysis.
- `analysis-diagnostic`: lymph project, univariate diagnostic odds ratio.
- `analysis-extended`: cumulative, leave-one-out, subgroup, meta-regression and joint diagnostic methods need their own drives.

## How to get to it (user POV)

- Open a project, then Analysis > Meta-Analysis or the matching toolbar button.
- Diagnostic projects first show the metric selection dialog.
- Analysis menu/toolbar also provides Cumulative Meta-Analysis, Leave-One-Out Meta-Analysis, Subgroup Analysis and Meta-Regression.

## Driving it with Qt E2E

Preconditions: doctor passes; committed samples and the frozen numerical contract are present.

- **Binary.** Run `uv run python scripts/verify_rcms.py amino`. The workspace shows Gonzalez and 19 included studies. `action_go` opens `AnalysisSetupDialog`; `method_cbo_box` selects `binary.random`; the Decimal places spinbox is set to three; the dialog OK button runs R. Displayed estimate/intervals match `amino-binary-random` within `0.001`.
- **Continuous.** Run `uv run python scripts/verify_rcms.py continuous`. Carroll and six included studies reach `continuous.random`; compare with `continuous-random`.
- **Diagnostic.** Run `uv run python scripts/verify_rcms.py lymph`. Kinderman and 17 included studies reach metric DOR, then `diagnostic.random`; compare with `lymph-diagnostic-random-dor`. The public heading is Odds Ratio Summary; use typed section identity rather than assuming it is the internal text key.
- **Proof.** Each run records `analysis-action`, `analysis-configured`, `analysis-results`, and `numerical-oracle`. The results scene must display the actual summary and render valid SVG. `workflow/forest.pdf` must be a PDF export, not a renamed image.

## Gotchas

- Dataset length includes excluded studies; count inclusion, not rows alone.
- The selected model matters: a fixed-effects result can look plausible and still be wrong. Require the independent numerical contract.
- These three paths do not establish Reitsma bivariate model, regression, multimetric, subgroup, cumulative, or leave-one-out UI behavior. Use live golden/R evidence and add the affected UI drive.
- Statistical authority packages own estimates; entered effect estimates and reconstructed analysis effect estimates are distinct from transient derived effect previews.
