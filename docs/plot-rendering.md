# SVG display and export

Results displays ordinary, contour-enhanced, trim-and-fill and Deeks funnels as
SVG using the same measured-text, resize and zoom path as other plots. Figures
remain vector content in Results and manuscript output.

[Qt's SVG support](https://doc.qt.io/qt-6/svgextensions.html) omits `clipPath`.
The shared `svg_rendering.svg_bytes_for_qt` loader adapts the rectangular,
untransformed clip groups emitted by svglite into symbol viewports in memory.
Origin-based viewports and translated contents preserve plot coordinates; Qt
clips them through QPainter. The loader also expands percentage-sized canvas
backgrounds to the actual viewBox size.

Saved SVG files retain R's original clipping paths. PNG/TIFF/PDF plot exports
use R/librsvg. The display adapter does not support arbitrary clip shapes,
transformed clip groups, malformed or unit-suffixed SVG input. Nonpositive clip
sizes hide their contents.

Qt can replace a caller's painter clip inside a symbol. Paginated report output
therefore intersects each SVG group and its canvas with the visible page slice
before rendering. Verify caption clearance and page boundaries on a long,
multi-page forest; a plot's standalone appearance is insufficient.

After the strict typing gate, use the configured runtime in the
[verification skill](../.agents/skills/verify-rcms/SKILL.md):

```powershell
uv run python -m pytest tests/e2e -q -k 'plot-workflow-funnel or plot-workflow-contour or plot-workflow-trimfill or plot-workflow-deeks or manuscript-split-figure'
uv run python scripts/verify_rcms.py ui-fine-tuning --native
```

Retain decoded SVG/PDF geometry, text size, nonwhite-background comparisons,
large-render output and raster/vector identity alongside screenshots. The
[plot feature map](../.agents/skills/verify-rcms/features/plots.md) records the
exercised paths and limitations. Source display checks do not qualify native
pickers, every DPI setting, another platform or a release archive.
