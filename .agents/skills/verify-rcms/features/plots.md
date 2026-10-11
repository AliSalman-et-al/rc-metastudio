# Results, plot editing, and export

Users inspect analysis summaries and plots, apply plot edits, discard subsequent drafts, and export rendered figures.

## Sub-features

- `results-render`: actual summary text and valid rendered analysis plots.
- `plot-apply`: changed axis label regenerates the real R plot and saved parameters.
- `plot-cancel`: Cancel discards the draft after an applied change.
- `plot-pdf`: PDF export from the sample-analysis workflows.

## How to get to it (user POV)

- Run an analysis to open the Results window.
- Double-click an editable plot to open its editor.
- Use a plot's context menu to save/export it in the offered format.

## Driving it with Qt E2E

Preconditions: doctor passes; amino analysis produces a real editable forest plot.

- **Edit and cancel.** Run `uv run python scripts/verify_rcms.py plot-edit`. The existing Results editor path opens `EditPlotDialog`. Fill `x_lbl_le` with `Edited effect axis`, click the button box Apply, and require changed SVG bytes and persisted `fp_xlabel`. Change the draft again and reject the editor; the applied label and a valid SVG remain. `plot-edit-draft` and `plot-applied-cancelled` capture the sequence and final result.
- **Export.** Run `uv run python scripts/verify_rcms.py amino` (or `continuous`/`lymph`). The production Results save-image path writes `workflow/forest.pdf`; require a PDF header and inspect the figure when export behavior changed.
- **Entry reachability.** The driver calls the Results editor/export paths directly. It does not exercise plot hit testing or the context-menu choice. Add those gestures for changes to double-click or menu wiring.

## Gotchas

- A parameter change without changed rendered output is not successful regeneration.
- Samples exercise a forest editor and PDF only. Other plot editors and PNG/SVG/TIFF export need corresponding real artifacts and paths.
- Offscreen screenshots cannot prove screen bounds, native DPI, accessibility, or pixel geometry. Native Results smoke provides fractional-scale fixture evidence; real-R E2E supplies the statistical workflow proof.
- Keep the pre-edit artifact and the last successful applied state when testing failed regeneration or rollback.
