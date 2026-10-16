# CI refactor comparison against c62df31

Baseline is a detached, unchanged c62df31 worktree at
`build/ux-round3/lexer-c62df31`. Its RCMetaR is installed into the separate
`build/ux-round3/lexer-before-library`; statistical dependencies are links to the
qualified private dependency library. Current source is 9de179b. Both use pinned
R 4.6.1, the same generated forms, fonts, Qt and native xcb display. The wrapper
receipt records the owning checkout; each baseline helper manifest independently
records c62df31. Installed-source hashes are retained in raw/lexer.

`compare_ci_renders.py` pairs native captures by recorded step/capture and SVGs by
recorded step/artifact identity, never by random scratch filenames. It rasterizes
both actual SVGs with the same Qt renderer at their natural dimensions on white
and compares every pixel. Raw results retain dimensions, file hashes and exact
difference bounds; no focus, path, border or blank-capture differences are masked.
This compares the affected families, not every possible figure/parameter/export.

## Personal inspection journal

- **project-axis-sequential:** inspected before/after `28-0-matrix-results.png`
  (PFT Default subgroup forest). Labels, marks, diamonds, raw columns, inference
  and spacing are visually identical. All six SVG pairs are pixel-identical;
  43/45 native pairs are pixel-identical, two differ by one bottom-right edge pixel.
- **project-reviewer-predictions:** inspected before/after
  `11-0-reviewer-prediction-observed.png` (Default PFT forest),
  `08-0-matrix-results-report.png` (structured summary/prediction report),
  `72-0-matrix-configured.png` (setup), and
  `66-0-reviewer-prediction-after.png` (RevMan PLO forest). All 57 SVG pairs are
  pixel-identical. The inspected figure/report content is identical. Setup differs
  only in native focus border; saved-table status text contains different scratch
  directories, as expected from fresh processes.
- **Rejected baseline captures:** personally inspected baseline/current
  `137-0-matrix-results.png` and `185-0-matrix-results.png`. Baseline steps
  137/139/140/141/142 contain nine blank 550×252 native captures; they are unusable
  visual evidence, despite the drive's passing numerical/state assertions. All
  retained SVGs, including this case, render pixel-identically. The initial step
  185 omission frame differs by unsettled layout height; its later settled figure
  frame is pixel-identical. Keep these discrepancies explicit; do not count all
  native frames as identical or promote a blank frame into proof.
- **analysis-diagnostic-joint:** inspected before/after
  `05-0-matrix-results.png` (clinical report) and
  `05-0-matrix-results-figure.png` (SROC). Report content, axis/curve/regions,
  markers, titles and placement are visually identical.
- **project-release-coefficients:** inspected before/after
  `14-0-coefficient-linear-choice.png` (Default coefficient editor). Axis choice,
  style, appearance fields, labels, buttons and geometry are visually identical.

Further family comparisons and final totals are appended after their retained
native continuations complete. The terminal-session interruption is separately
recorded; completed earlier comparison runs remain available.

- **plot-workflow-funnel:** inspected before/after `05-0-family-editor-controls.png`
  and `07-0-family-plot-cancelled-figure.png`. Appearance/caption controls, buttons,
  curve/points, caption and SE scale label match visually.
- **plot-workflow-regression:** inspected before/after `08-0-family-editor-controls.png`
  and `22-0-family-plot-cancelled-figure.png`. BMJ editor fields/visibility and
  bubble sizes/positions, curve, axes and legend match visually.

The first 24 accepted personally inspected PNGs are copied byte-for-byte into
`ci-visual/`, with original artifact paths and SHA-256 in CI-VISUAL-CURATED.json.
The four additional inspected blank/unsettled comparison frames above remain
explicitly rejected or limited; they are not included in the accepted curation.

## Completed comparison

- **audit-round3-arm-names:** inspected before/after step 100 (case 3, Default,
  Training / Usual care) structured report and the actual full SVG rendered at
  natural size. The continuous raw-arm headings, Mean/SD/N columns, complete arm
  names, counts/totals, six-digit annotations, blue marks, interval/diamond geometry,
  axes and inference footer are visually identical. These four additional accepted
  PNGs are retained, bringing accepted curation to **28 PNGs** (26 native captures
  and two actual SVG renders). Four additional inspected blank/unsettled comparison
  frames remain excluded from accepted curation.

Final comparison: **830 pairs across eight families**. All **127 actual plot
pairs are pixel-identical**: **120 SVG renders and seven raster funnel plots**.
Of 703 native window pairs, 512 are pixel-identical. Other raw differences remain
visible in CI-VISUAL-COMPARISON.json: fresh scratch/recent/CSV paths, native focus
and border state, nine rejected blank baseline captures and one initial unsettled
layout. This is not a claim that every native frame or every PDF/TIFF byte matches.
All inspected representative presentation content matches; ordinary four-format
export/decode assertions remain in the native drives.

The baseline keyboard/recent-project drive initially failed because its scratch
`build` symlink changed canonical recent paths. The owned symlink was replaced by
a real scratch directory, keeping the exact assertion. `before2-review1-design`
stays failed; `before3-review1-design` and the current drive pass. Baseline and
current arm-name drives and the current generic-effect continuation all pass.

To replay a baseline family, use the detached c62df31 checkout and an actual owned
scratch directory, set RCMS_QT6_BUILD_ROOT to the main checkout's generated forms,
and select the separate installed baseline RCMetaR library. Invoke the main
checkout's Python executable with the baseline checkout's `scripts/verify_rcms.py
<scenario> --native`; the helper computes its product/fixture root from its own
script. Keep the baseline package and its source/install provenance separate from
the current library. Commands, arguments, libraries, receipt timestamps and all
artifact hashes are retained under raw/lexer. `CI-LEXER-REPRODUCE.sh` replays current
qualification; `compare_ci_renders.py` recomputes the actual before/after comparisons.


The completion worker reverified every curated/source hash and all 1,660 paired
input file hashes. The 28 personal-inspection entries above belong to the prior
worker's retained journal; their files and acceptance records are preserved.
The final qualification-only repairs change no renderer, report production or
plot parameter; the final strict capture and all 415 fields pass again.
