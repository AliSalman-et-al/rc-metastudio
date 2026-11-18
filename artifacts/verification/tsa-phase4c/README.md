# TSA plot verification

RC MetaStudio ran with native Qt 6.12.0 and R 4.6.2 on Windows x64. Five cases ran
through Results and Edit Plot at Fit width, in Default, RevMan and BMJ, at measured
device scales of 100% and 150%. The driver checked the existing numerical
contract and the updated [plot descriptor](../../../tests/analysis_regression/baseline/tsa-plot-descriptors.json).

| Style | Native TSA matrix | Four-plot contact sheet |
| --- | --- | --- |
| Default | [100% and 150%](native-default.png) | [Comparison](contact-default.png) |
| RevMan | [100% and 150%](native-revman.png) | [Comparison](contact-revman.png) |
| BMJ | [100% and 150%](native-bmj.png) | [Comparison](contact-bmj.png) |

The matrices show BCG OR with overrun and LIL, Pignon HR, entered MD, RR MH
with a futility crossing, and the 36-look MD stress case. The comparison sheets
combine the new BCG capture with the three other plot images from Phase 4.

- The stress case preserves both wrapped favours labels. The lower box intersects
  the Z-curve and bubbles, which paint over it. The SVG assertions check that
  intersecting bubble centers are present and paint after the box.
- BCG displays 0% through 300% in uniform 50-point steps. The other four cases
  display 0% through 100% in uniform 25-point steps.
- Each SVG uses the same 9.79-unit legend font size. The full legend fits in all
  cases, including Pignon's two-line title. Fit width scales the full figure
  to the viewport.

The [screenshot index](screenshots.csv) lists all 30 window captures and figure
crops. The [audit log](review.log) records the rendered tick labels, font sizes,
manifest hash checks, text bounds and SVG equality across display scales. The
local run directories retain the exact inputs, action records, SVGs, exports
and screenshots.

## Replay

Use the generated Qt forms and the runtime, dependency seed library and Poppler
paths from [replay.ps1](replay.ps1). The host's base display scale was 125%.
Pass `-SystemScale` for another base scale. Use a fresh `-Run` name to retain a
second qualification and pass that name to the contact-sheet script.

```powershell
& ./artifacts/verification/tsa-phase4c/replay.ps1 -Lane setup
& ./artifacts/verification/tsa-phase4c/replay.ps1 -Lane r
& ./artifacts/verification/tsa-phase4c/replay.ps1 -Lane native100
& ./artifacts/verification/tsa-phase4c/replay.ps1 -Lane native150
uv run python artifacts/verification/tsa-phase4c/contact_sheets.py
```

The [typing transcript](qualification/setup/typing.log) retains the full
win32 command and its result before desktop work. The
[R transcript](qualification/r/r-tests.log) covers TSA, the bubble renderer,
small-study effects, Reitsma and the plot inventory. The ten desktop invocation
logs are under `qualification/native100/` and `qualification/native150/`.
