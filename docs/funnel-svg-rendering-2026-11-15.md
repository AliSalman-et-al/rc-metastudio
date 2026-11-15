# SVG funnel rendering — 15 November 2026

Ordinary, contour-enhanced, trim-and-fill and Deeks funnels use SVG artifacts in
Results again. This supersedes the PNG workaround in the earlier UI review.
The PNG-specific body-text metadata and its handling have been removed. SVG
fitting uses the same measured text floor, resize and zoom path as other plots.

## Clipping without rasterizing

[Qt supports SVG symbols but does not support clipPath](https://doc.qt.io/qt-6/svgextensions.html).
The shared `svg_rendering.svg_bytes_for_qt` loader converts svglite's rectangular,
untransformed clip groups into symbol viewports in memory. Each symbol has an
origin-based viewport and translated contents; its use element restores the
original plot coordinates. Qt clips that viewport using QPainter, retaining vector
paths and text at display and print resolution. Results and manuscript figures
use the same loader. The saved SVG stays unchanged and retains R's original
clip paths for publication export. PNG/TIFF/PDF plot export still uses R/librsvg.

An initial mask experiment removed the visible spill but triggered Qt buffer
limits during large renders. It was rejected. The implementation uses neither
masks nor embedded raster images. It adapts the rectangular clip groups emitted
by the existing R device; arbitrary SVG clip shapes and transformed clip groups
are outside this adapter's scope.

The loader also expands svglite's percentage-sized background rectangle to its
actual viewBox size. Qt otherwise paints that canvas as only 100 SVG units in
each direction, which the nonwhite-background comparison exposed.

## Review corrections

The [independent Opus review](../artifacts/verification/funnel-svg-2026-11-15/opus-review.md)
accepted the viewport geometry and vector output, then identified two blocking
issues: Qt replaces a caller's painter clip inside a symbol, and the baseline
small-study driver still read removed PNG metadata. The
[resolution record](../artifacts/verification/funnel-svg-2026-11-15/opus-review-resolution.md)
documents the fixes; it is the implementing agent's response, not another Opus
sign-off.

PDF pagination now intersects each SVG group and its canvas with that page's
visible slice before rendering. A real 95-study forest reproduces the original
caption overlap and proves the corrected two-page figure has clear caption bands
and no raster images. Nonpositive clip sizes hide their contents. The baseline
small-study driver now measures the SVG text and scale directly. Arbitrary
malformed or unit-suffixed SVG input remains outside the adapter's scope.

## Final-source evidence

The retained bundle is `artifacts/verification/funnel-svg-2026-11-15/`.
Its `proof-plan.md` records the original failure obligations; `attempts.md` retains
failed and superseded attempts. The following checks ran after the review fixes,
on frozen executable inputs:

| Check | Observed evidence |
| --- | --- |
| Strict win32 typing | Passed before native and E2E qualification; transcripts retain the exact commands under `artifacts/verification/typing/`. |
| Targeted real Qt/R E2E | `e2e-reviewed.log`: **11 passed in 285.11 seconds**. Ordinary/contour/trimfill/Deeks editors and four-format exports, continuous small-study output, baseline small-study workflow, both manuscript-export workflows, HR/IRR and split-figure PDF. |
| Native Windows | `native-reviewed.log`, run `20261115T133622Z-1e1978ef-ui-fine-tuning`: **80 steps passed**. Five funnel variants use SVG Results items; Results/manuscript rendering at 1×/2× has zero region pixels outside the chart and retained interior fill. Automatic text fitting and explicit Fit width pass. |
| Results layouts | `gui-reviewed.log`: **68 passed**. |
| Collection | `collection-reviewed.log`: **1,238 tests collected**, strict markers, exit zero. |
| Narrow axes and colors | `custom-axes.R`, `check_custom_axes.py`, `custom-qt-reviewed.log` and `custom-axes-observations.json`: auto/narrow bounds, labels, colored points/lines/regions and nonwhite backgrounds through both production loaders. Canvas corners match librsvg, colored spill is zero, region coverage differs by less than 0.1%, and marker solid-pixel coverage by less than 3%. |
| Vector PDF | Each custom-axis figure painted through QPdfWriter at 1200 DPI has zero embedded raster images. The maintained `manuscript-split-figure` scenario also checks the real tall forest's PDF pages for caption overflow and raster images, then checks zero-width SVG viewports. |
| R behavior and provenance | `r-funnel-tests.log`: small-study R tests passed. `custom-axes.log` confirms installed bodies of all three changed R functions match source; `r-install.log` retains installation into the test-owned library. The held fit stays byte-identical across presentation edits. These R files are unchanged by the review corrections. |
| Artifact integrity | `evidence-reviewed-audit.json`: **1,948 file entries across 12 final-source runs**, zero missing files or hash mismatches; includes final source SHA-256 values and verifies R source is identical to the earlier passed R checks. |

`symbol-probe.json` retains the original reproduction: thousands of shaded pixels
outside the chart with unadapted Qt rendering, zero with symbol viewports at both
tested scales, and interior fill retained. Earlier nine-case and native runs
remain supporting history, not the final-source qualification. The split-figure
failure in `split-reproduced.log` found 1,601 nonwhite pixels below the first-page
caption; corrected pages were rendered and visually inspected. No failed run is
relabeled as passing.

Runtime: Python 3.14.10, Qt/PyQt 6.12.0, R 4.6.2 and RCMetaR 0.5.4 on Windows.
Offscreen tests use the test-owned Segoe UI directory; native captures use the
Windows backend. Desktop manifests retain exact commands, inputs, runtime and
file hashes under `artifacts/verification/rcms/`.

```powershell
uv run python -m pytest tests/e2e -n auto -q -k 'plot-workflow-funnel or plot-workflow-contour or plot-workflow-trimfill or plot-workflow-deeks or small-study-continuous-extended or manuscript-export or ratios-hr or ratios-irr or small-study-effects or manuscript-split-figure' --durations=11
uv run python scripts/verify_rcms.py ui-fine-tuning --native
```

DOCX figures retain their existing 300-DPI raster insertion; Results and PDF use
vector painting. Source Windows checks do not qualify other platforms, packaged
releases or external Word page rendering. This SVG restoration does not implement
the separate Results reporting redesign.
