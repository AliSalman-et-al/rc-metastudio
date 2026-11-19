# TSA plot design verification

The native application ran on Windows x64 with Qt 6.12.0, Python 3.14 and
the pinned R 4.6.2 runtime and authority packages. The checked-in replay
sets up a test-owned RCMetaR installation and retains the repository-wide
strict Ty command and transcript for win32 before GUI driving. Each
desktop run keeps its command, runtime, screenshots, steps, exit and file
hashes in its own directory.

## Replay

Run these commands from the repository root. The replay expects the R
distribution, locked Python environment, verified RCC and Poppler in the
locations defined in [replay.ps1](replay.ps1).

```powershell
& ./artifacts/verification/tsa-phase4/replay.ps1 -Lane setup
& ./artifacts/verification/tsa-phase4/replay.ps1 -Lane r
& ./artifacts/verification/tsa-phase4/replay.ps1 -Lane plots
& ./artifacts/verification/tsa-phase4/replay.ps1 -Lane native100
& ./artifacts/verification/tsa-phase4/replay.ps1 -Lane native150
uv run python artifacts/verification/tsa-phase4/review.py
```

For a second replay, pass a fresh `-Run` name to each lane and supply that
name to `review.py`. The host Windows display was
at 125%, so the native runs use Qt scale factors 0.8 and 1.2. The driver
selects Fit width, captures the window and the whole figure viewport, and
records the observed device-pixel ratio. A figure capture fails if any of
the figure falls outside the viewport. On a different Windows display,
pass its base scale as `-SystemScale`.

The Reitsma visual lane uses the installed test package.

```powershell
$env:RCMS_REITSMA_VISUAL_QA_MODE = "installed"
$env:RCMS_REITSMA_VISUAL_QA_LIBRARY = (Resolve-Path .tmp/tsa-phase4-library).Path
$env:R_LIBS = $env:RCMS_REITSMA_VISUAL_QA_LIBRARY
& "$env:USERPROFILE/Downloads/RCMetaStudio-0.5.6-windows-x64/R/bin/Rscript.exe" --vanilla scripts/verify_reitsma_visual_qa.R artifacts/verification/tsa-phase4/reitsma-visual-qualified
& "$env:USERPROFILE/Downloads/RCMetaStudio-0.5.6-windows-x64/R/bin/Rscript.exe" --vanilla artifacts/verification/tsa-phase4/axis-appearance.R artifacts/verification/tsa-phase4
```

## Inputs

| Case | Input and setup |
| --- | --- |
| BCG OR | `sample_projects/BCG.rcms`, random effects, table order, LIL enabled. Monitoring crossing and overrun to 304%. |
| Pignon HR | `sample_projects/Pignon2000-HR.rcms`, missing-year recovery via table order. |
| Entered MD | Driver's three-study fixed MD fixture, anticipated MD −1 and RIS 10,000. Neither boundary crossed. |
| RR MH | Driver's six-study fixed MH RR fixture, one dropped double-zero study, entered RIS 1,000. Futility crossing. |
| Stress | Driver-generated 36-study fixed MD fixture, anticipated MD −1, RIS 10,000 and two favours labels of about 40 characters. |
| SMD | Driver's continuous SMD fixture, disabled TSA action with tooltip. |

The generated projects are retained beside the corresponding screenshot and
SVG captures. The numerical contract includes the first and final values
for each statistical case, plus the LIL, crossing and terminal interval
checks as applicable. The BCG drive probes default restoration and verifies
the same terminal SVG coordinate in the wedge, monitoring line and held
extension. The MD drive saves, reopens and reruns the entered design.

## Evidence

- Windows strict typing [passed](qualification/native150/typing.log) with
  the full source selection and generated-module search paths. The selected
  [R suites](final-labels/r/r-tests.log), the
  [21-case Reitsma visual lane](reitsma-visual-qualified.log) and the
  [38 Python plot tests](qualification/plots/python-plots.log) passed.
  The native TSA cases and the regression, trim-and-fill, SROC and forest
  plot workflows all exited successfully.
- Style contact sheets for [Default](contact-default.png),
  [RevMan](contact-revman.png) and [BMJ](contact-bmj.png).
- The [native screenshot index](screenshots.csv) lists the full window and plot
  crop for every style, case and DPI.
- [Export comparisons](export-comparison.csv) use the plot crop from the native
  100% pass. The app exports SVG, PNG, PDF and TIFF for each case and style.
  The comparison decodes the output, checks aspect and compares the normalized
  ink profiles. The review sheets show the render side by side with each
  decoded export. The desktop runs also decode the report PDF and DOCX and
  compare table clipboard and CSV values.
- The [saved-bundle edit](axis-appearance.log) checks the custom accent, bounds,
  ticks and horizontal label through the production regenerator. The legend
  omits the RIS and futility entries when the bounds exclude those marks.
- The [audit](review.log) verified the desktop manifests and found
  byte-identical plot SVGs between DPI passes for all 15 case/style pairs.
  The 100% BCG, MD and RR runs preceded the HR caption and long-label
  refinements. The 100% HR and stress cases were repeated after those refinements,
  and the full 150% pass used the final package. Titles, axes, favours labels
  and legends fit in the native captures. Dense looks share some marker
  space, and the monitoring curves remain visible through the bubbles.
- Native manifests, raw exports, generated input projects and all window
  captures live under `qualification/`. Bulk evidence is retained in the local
  artifact directory. The branch contains the replay scripts, transcripts,
  indexes and contact sheets.

## Descriptor changes

Plot identity, kind and regenerator stay the same. The revised descriptor
expects the RevMan bubble accent and the visible legend's futility region
label. The fixed 1.6 aspect check gives way to the shared, measured bubble
device aspect. Statistics and the numeric contract are unchanged.

The funnel's shared RevMan preset supplies `#D9D9D9` and the bubble's shared
zero-line renderer supplies `gray50` (`#7F7F7F`). The regression package
calculates marker diameters within its fitted plot call. TSA uses the shared
bubble limits and square-root scaling on the information added at each look,
so area is proportional above the lower size floor.
