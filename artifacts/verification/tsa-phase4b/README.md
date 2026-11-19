# TSA plot polish verification

RC MetaStudio ran on Windows x64 with native Qt 6.12.0 and the pinned R 4.6.2 runtime. The driver used real Results and Edit Plot windows at Fit width. It checked displayed TSA values against the existing numeric contract, and checked regular information ticks, the two in-panel favours labels, the tinted dotted swatch, and the legend dash patterns in the regenerated SVGs.

## Captures

| Style | Four-plot comparison | Native TSA matrix |
| --- | --- | --- |
| Default | [Contact sheet](contact-default.png) | [100% and 150%](native-default.png) |
| RevMan | [Contact sheet](contact-revman.png) | [100% and 150%](native-revman.png) |
| BMJ | [Contact sheet](contact-bmj.png) | [100% and 150%](native-bmj.png) |

The four-plot comparison uses the new BCG capture and carries forward the three other plot images from Phase 4. The native matrices show BCG OR with overrun and LIL, Pignon HR, entered MD without crossing, RR MH with futility crossing, and the 36-look MD stress fixture with approximately 40 characters per favours label.

The [screenshot index](screenshots.csv) gives the measured device-pixel ratio, full window, and figure crop for each case and style. The [audit log](review.log) records checks of the desktop manifests, text bounds, and SVG equality across display scales. The driver also checks that the whole figure fits inside the Results viewport.

Visual review of the 30 final captures found no text overlap or clipping. Both stress labels wrap to two lines at each scale and style. Their padded backgrounds obscure the marks beneath the labels as intended.

## Replay

From the repository root, use the generated Qt forms and the runtime, dependency seed library, and Poppler paths in [replay.ps1](replay.ps1). The host's base display scale was 125%. Pass `-SystemScale` when replaying on another display. Use a fresh `-Run` name for another qualification and pass that name to the contact-sheet script.

```powershell
& ./artifacts/verification/tsa-phase4b/replay.ps1 -Lane setup
& ./artifacts/verification/tsa-phase4b/replay.ps1 -Lane r
& ./artifacts/verification/tsa-phase4b/replay.ps1 -Lane native100
& ./artifacts/verification/tsa-phase4b/replay.ps1 -Lane native150
uv run python artifacts/verification/tsa-phase4b/contact_sheets.py
```

The [strict typing transcript](qualification/setup/typing.log) records the full win32 command before the native doctor and desktop cases. The [R transcript](qualification/r/r-tests.log) covers TSA, bubble, small-study effects, Reitsma, and the plot inventory. The ten desktop invocation logs are grouped under `qualification/native100/` and `qualification/native150/`. The local run directories also retain the full manifest and file hashes, generated input projects, action sequence, screenshots, SVGs and exports.

The first 100% HR attempt failed a proposed 1.5-period minimum for the RIS legend key. The key spans 1.27 periods at HR's device size, showing a full dash and gap plus the start of a second dash. The descriptor now requires at least 1.2 periods and the exact plotted dash patterns. The preliminary transcript is retained under `preflight/native100/`.

The first contact-sheet audit found that the last HR legend label extended 1.37 points past its SVG canvas. The final renderer reserves an extra character of legend margin, and the desktop check now enforces that the legend text fits. The preliminary audit is retained under `preflight/figure-width/`.
