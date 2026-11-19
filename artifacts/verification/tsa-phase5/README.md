# TSA plot redesign verification

The six cases were BCG OR with the penalised curve, Pignon HR, entered MD,
RR MH with a futility crossing, the 36-look long-label stress case and BCG
Peto fixed effect. The Peto drive used the default TSA design after the
Peto fit and reproduced 6301% accrual. It applied and reopened the saved
x-axis choice in both directions and checked the report after each edit.

The pinned Windows x64 runtime used native Qt 6.12.0 and R 4.6.2. The 125%
host display scale combined with Qt factors of .8 and 1.2 to produce measured
device scales of 1.00 and 1.50. The first five 100% runs used
`0d6c5b9b03def3f997c1b10b38240ac69cba38f0`. The Peto 100%
run, the 150% runs and print outputs used `a84ff2b0`. That follow-up changed
only the viewport metadata of outlined SVG exports and the TIFF test recorder.
All 18 pairs of native display SVGs matched byte for byte. The input design spec v2 has SHA-256
`11e6645a3ffa448080fe11895b131a44a83490115eb20a950f8283b2224e6a35`.

| Style | Native 100% and 150% | 89, 120 and 174 mm at 300 dpi | Four-plot family | Greyscale |
| --- | --- | --- | --- | --- |
| Default | [Native](native-default.png) | [Print](print-default.png) | [Contact sheet](contact-default.png) | [Greyscale](greyscale-default.png) |
| RevMan | [Native](native-revman.png) | [Print](print-revman.png) | [Contact sheet](contact-revman.png) | |
| BMJ | [Native](native-bmj.png) | [Print](print-bmj.png) | [Contact sheet](contact-bmj.png) | [Greyscale](greyscale-bmj.png) |

The family contact sheets reuse the bubble, funnel and forest captures from
phase 4. The [screenshot index](screenshots.csv) locates the individual native
windows and figure crops. The local run directories retain the exact scenario
inputs, runtime identity, action records and plot bundles. The
[print directory](qualification/print/) holds the 54 original TIFFs, the
corresponding PDFs and SVGs, and the geometry SVGs used for measurement.

## Quality gates

| Check | Result | Evidence |
| --- | --- | --- |
| Six cases × three styles at both native scales | Pass | [Screenshot index](screenshots.csv) and [manifest audit](review.log) |
| Six cases × three styles at 89, 120 and 174 mm at 300 dpi | Pass | [Print outputs](qualification/print/) and [render transcript](qualification/print/print.log) |
| No unintended overlap or clipping | Pass | [Geometry audit](geometry.csv) and the native and print sheets above |
| First crossing remains visible | Pass | [Default native sheet](native-default.png) and [Peto at 89 mm](qualification/print/89/peto-default.tiff) |
| Monitoring boundary is smooth between looks | Pass | [RR MH native sheet](native-default.png) and [exact-knot checks](qualification/print/print.log) |
| At most six x-axis labels | Pass | [Geometry audit](geometry.csv) and [Peto percent edit](peto-axis-percent.svg) |
| Favours labels stay clear of data | Pass | [Geometry audit](geometry.csv) and the stress case in the native and print sheets |
| At least 6 pt text and 0.5 pt lines at print widths | Pass | [Geometry audit](geometry.csv), with minima of 6 and 0.6 pt |
| Default and BMJ remain readable in greyscale | Pass | [Default](greyscale-default.png) and [BMJ](greyscale-bmj.png) |
| PDF fonts embedded, SVG fonts outlined, TIFF LZW at 300 and 600 dpi | Pass | [Export audit](review.log), [print files](qualification/print/) and [600 dpi TIFF](qualification/print/peto-default-600.tiff) |
| One four-plot contact sheet per style | Pass | [Default](contact-default.png), [RevMan](contact-revman.png) and [BMJ](contact-bmj.png) |
| Plot docs and golden baseline updated | Pass | [Plot docs](../../../docs/trial-sequential-analysis.md) and [plot descriptor](../../../tests/analysis_regression/baseline/tsa-plot-descriptors.json) |

## Design decisions

- The off-panel marker and its ring are offset 0.03 inches beyond the edge so
  the axis stroke does not obscure them. They remain aligned with the look's
  information value. The Peto and BCG OR extreme Z-scores exercise this layout.
- The HR control uses “Statistical information” for the default option to match
  its units. Participant studies use “Participants”.
- Narrow print exports use compact typography with a 6 pt floor. The legend
  moves below at 89 and 120 mm. The 89 mm layout shifts the join label left
  when it needs clearance from the accrued label. Both ticks stay at their
  transformed positions.
- The shared bubble layout and sizing determine the desktop figure. The print
  sweep uses a 16:9 aspect at each of the requested widths. The Peto desktop
  export also exercises a 300 dpi TIFF at the export dialog's measured aspect.
- The compressed section includes the 4% headroom past the last look within the compressed
  section. The join remains at 80% of panel width in both modes.
- The report adds the prescribed marker-area figure note. The R calculations
  and numerical contracts retain their original values.

## Replay

The [replay script](replay.ps1) records commands, installs the current RCMetaR
from source into an owned library and runs the strict typing gate before native
windows. Supply the generated forms, runtime, dependency seed library and
Poppler paths used by the script. Use a different `-Run` name to retain another
qualification alongside this one.

```powershell
& ./artifacts/verification/tsa-phase5/replay.ps1 -Lane setup
& ./artifacts/verification/tsa-phase5/replay.ps1 -Lane r
& ./artifacts/verification/tsa-phase5/replay.ps1 -Lane native100
& ./artifacts/verification/tsa-phase5/replay.ps1 -Lane native150
& ./artifacts/verification/tsa-phase5/replay.ps1 -Lane print
$env:PATH = (Resolve-Path .tmp/poppler-tsa/poppler-26.09.0/Library/bin).Path + ";" + $env:PATH
uv run python artifacts/verification/tsa-phase5/contact_sheets.py
```

The [typing transcript](final-exports/setup/typing.log) retains the exact
repository-wide win32 command. The [R transcript](final-exports/r/r-tests.log)
covers TSA, the bubble renderer, small-study effects, Reitsma and the plot
inventory. The [full Python transcript](python-full.log) has 868 passes, one
skip and two failures reproduced on the original branch head
[`4151624c`](python-baseline.log). The [focused plot tests](python-plots.log)
passed all 38 tests.
