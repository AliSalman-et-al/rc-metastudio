# Slice 8b — readable Results

Removed duplicate Text report/Tables toolbar entries (shortcuts remain), hid the
Results navigation header, and sized navigation to its actual labels. The existing
maximized first-use window and saved normal/maximized geometry restoration remain.

The supplied 796×796 screenshot is below the requested 1280×800 desktop size.
Its plot is a full SVG, not a separately scaled thumbnail. At 1280×800 the old
proportional navigation consumed enough space to reduce amino study text to
8.44 pt. Compact navigation raises it to 9.35 pt. No R canvas or manuscript
figure geometry change was needed. Numerical code and frozen oracles are unchanged.

The results-window drive measures SVG study font-size × SVG-viewBox-to-item scale
× effective item-to-viewport transform, converted from logical pixels to points
at 96 DPI (72/96). This is nominal font height, not glyph ink/cap height. The
union of rendered SVG text bounds spans 87.9% of the viewport width (before:
87.6%); it excludes blank paper and includes labels/annotations across the plot.

Red evidence: artifacts/verification/rcms/20261101T010719Z-7e54e993-results-window
records 8.436 pt and duplicate toolbar navigation, then fails the new assertion.
Initial green evidence: artifacts/verification/rcms/20261101T010750Z-602f8d13-results-window
records 9.354 pt, 0.879 width fraction and no duplicates; full workflow passed.

Commands use `source build/sheets-baseline/ENV.sh` and `uv run --no-sync`.
Final serial scenario logs: build/slice8b-<scenario>.log. Each points to its
durable manifest, exact command, runtime identity and screenshots. Six page/theme
captures use a 1280×800 normal window and explicit light/dark Qt palettes;
these prove offscreen Qt rendering, not native desktop DPI/window-manager behavior.

Validation: all 16 requested desktop scenarios passed (results-window, amino,
continuous, manuscript-export, eleven plot-workflow-* families, hillclimb).
Strict golden passed: 11 cases, 475 comparisons, 416 numerical fields;
`build/qt6-verification/golden-compatibility-slice8b/compatibility-report.json`.
Manuscript assertions passed with unchanged PDF/DOCX figure geometry.

The final results-window rerun omits the explicit Fit width action: automatic
resize fitting produces the same 9.354 pt and 0.879 coverage, and the complete
workflow passes. Evidence: artifacts/verification/rcms/20261101T011645Z-8bbd7fb1-results-window;
command log: build/slice8b-results-window-auto-fit.log. Screenshots were copied
from this final run.
