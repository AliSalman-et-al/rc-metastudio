# TSA plot review follow-up

The sweep uses the same six cases as Phase 5: BCG OR with the penalised curve,
Pignon HR, entered MD, RR MH with a futility crossing, the 36-look long-label
stress case, and BCG Peto fixed effect at 6301% accrual. Native Windows x64
captures use Qt 6.12.0 and R 4.6.2. With a host scale of 125%, Qt factors of
0.8 and 1.2 yield measured device scales of 1.00 and 1.50.

| Style | Four-plot contact sheet | Native 100% and 150% | 89, 120 and 174 mm at 300 dpi |
| --- | --- | --- | --- |
| Default | [Contact](contact-default.png) | [Native](native-default.png) | [Print](print-default.png) |
| RevMan | [Contact](contact-revman.png) | [Native](native-revman.png) | [Print](print-revman.png) |
| BMJ | [Contact](contact-bmj.png) | [Native](native-bmj.png) | [Print](print-bmj.png) |

The family sheets reuse the bubble, funnel and forest captures from Phase 4.
The [screenshot index](screenshots.csv) records the window, plot crop and
observed device scale for each native capture. The [geometry CSV](geometry.csv)
records the axis ticks, Favours lines, spacing, legend swatch width and text
collisions across 36 native captures and 54 print layouts.

| Review issue | Result | Evidence |
| --- | --- | --- |
| 1. Rotated Favours lines collide | Pass | The audit reproduced a backwards pitch of −0.69 em on the [earlier Peto SVG](before.log). Wrapped lines now share the same vertical centre and have a 1.2 em horizontal baseline pitch in the [geometry CSV](geometry.csv). |
| 2. Favours is truncated | Pass | Line one begins with the full word in every render. The [89 mm print sheet](print-default.png) shows the fallback in the Peto and stress cases. The audit checks that the second line reaches 0.75 of base tick size before truncation. |
| 3. Off-panel looks and crossing ring are too small | Pass | The [Peto print SVG](final/print/89/peto-default-geometry.svg) shows the ±16 axis and the visible original crossing. The [off-panel SVG](final/print/off-panel/default-89.svg) uses a copied Peto bundle with the crossing set to −17 and the following look set to +18. The [off-panel audit](off-panel.csv) measures both solid triangles and the centred crossing ring in 12 renders. |
| 4. Compression-join tick shows a decimal | Pass | [Participant SVG](peto-axis-participants.svg) shows 8,507 and [percent SVG](peto-axis-percent.svg) shows 150%. The geometry audit checks the participant tick at the 80% join. The original join value, 8,506.5, rounds up while the transform keeps the exact position. |
| 5. Futility legend swatch looks empty | Pass | The [89 mm RR MH SVG](final/print/89/rr-mh-default-geometry.svg) shows the filled rectangle. The audit compares its fill, border and stroke width with the plotted region and its width with the line samples. |

The [strict Windows typing gate](final/setup/typing.log),
[TSA and related R plot tests](final/r/r-tests.log), and
[38 focused Python plot tests](final/python/python-plots.log) passed.
The [TSA plot descriptor](../../../tests/analysis_regression/baseline/tsa-plot-descriptors.json)
now expects the Peto axis range and both join labels.

The first 150% BCG attempt rendered all three styles and then read an MD
report from the shared clipboard. The [failed transcript](final/native150/plot-workflow-trial-sequential-failed.log)
and capture are retained. The [retry](final/native150/plot-workflow-trial-sequential.log)
passed the plot and report checks.

## Replay

The [replay script](replay.ps1) records exact commands. It uses the generated
Qt forms, pinned R runtime, Phase 5 dependency seed library and Poppler paths
from the previous sweep. It installs RCMetaR into a separate test library
and records the source revision and patch before launching the app.

```powershell
& ./artifacts/verification/tsa-phase5b/replay.ps1 -Lane setup
& ./artifacts/verification/tsa-phase5b/replay.ps1 -Lane r
& ./artifacts/verification/tsa-phase5b/replay.ps1 -Lane python
& ./artifacts/verification/tsa-phase5b/replay.ps1 -Lane native100
& ./artifacts/verification/tsa-phase5b/replay.ps1 -Lane native150
& ./artifacts/verification/tsa-phase5b/replay.ps1 -Lane print
& ./artifacts/verification/tsa-phase5b/replay.ps1 -Lane sheets
```

The [print transcript](final/print/print.log) records the individual exports.
The [audit transcript](final/sheets/review.log) checks manifest hashes, export
formats and print geometry against those files.

The [native archive](native-evidence.zip) holds the full native runs,
manifests, saved bundles and setup provenance. The [print archive](print-evidence.zip)
holds the TIFF, PDF, outlined SVG and geometry SVG outputs. Both archives
store paths relative to this directory.
