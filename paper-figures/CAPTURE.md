# JOSS figures

Figures 3 and 4 use the app's Default plot style. The panels were exported
on Windows x64 from master at `ab1a454fc076d54f0ca6d5f438edc69eb9c76cf2`,
with Qt 6.12.0, R 4.6.2, and RCMetaR 0.7.0 installed from that checkout.
Figure 3A was recaptured after #651 (see below).

## App capture

Use a dedicated worktree at the recorded revision. Copy
`capture_default_figures.py`, `assemble_default_figures.py`,
`measure_default_figures.py` and `default_capture_env.ps1` into its
`paper-figures` directory. The native workflow uses isolated Qt settings
and redirects the save picker to a staging directory.

- **Figure 1.** Captured on Windows x64 at
  `9e7c2fba373883c73d7edc2f45de8b26c9fd7a3f` with Qt 6.12.0 and R 4.6.2.
  Copy `capture_rcms.py` and the assembler into the capture worktree's
  `paper-figures` directory. Set up that worktree's Python, R library, and
  generated Qt forms, then point `RCMS_R_HOME`, `RCMS_R_LIBS` and
  `RCMS_QT6_BUILD_ROOT` at them. Run from the worktree root in PowerShell
  with PyMuPDF installed in its capture environment. The script creates and
  removes `C:\Reviews`, which must be absent before capture.

  ```powershell
  $env:PYTHONPATH = "$PWD;$PWD/.agents/skills/verify-rcms/scripts"
  $env:QT_QPA_PLATFORM = 'windows'
  $env:QT_SCALE_FACTOR = '1.16'
  $env:RCMS_PAPER_OUTPUT = (Resolve-Path paper-figures).Path
  $env:RCMS_ANALYSIS_SCRATCH_DIR = (New-Item -ItemType Directory -Force build/joss-figure-1-analysis).FullName
  .venv/Scripts/python.exe paper-figures/capture_rcms.py interface
  .venv/Scripts/python.exe paper-figures/assemble_default_figures.py figure-1-interface
  ```

  The scale factor gives a 1.45 device-pixel ratio on the 1920 × 1080
  capture display at 125% Windows scaling. Choose a scale that leaves
  the entire window and wizard visible on the capture display. The script
  uses fresh Qt settings and light theme. It opens and saves four bundled
  sample copies under a temporary `C:\Reviews` directory for panel A
  (`figure-1a-welcome.png`). It reopens Barza 1996, auto-fits the columns,
  widens the study-name column and aligns the viewport to whole rows.
  Panel B (`figure-1b-new-project.png`) opens **New project** from Welcome
  and captures the live desktop cropped to the untitled main window with
  the data-type page visible. Panel C (`figure-1c-workspace.png`) shows the Barza
  spreadsheet with both outcome tabs visible.
  The three 1856 × 950 px panels are stacked at full width in
  `figure-1-interface.png` and `figure-1-interface.pdf` so the workspace
  headings and wizard choices stay readable. The legacy
  `figure-1-workspace.png` can still be captured with `workspace`.
- **Figure 2.** Open the bundled Colditz 1994 BCG sample. Run the 13 trials
  as a random-effects risk ratio with REML, 95% CI and normal (`z`)
  inference. From that single Results window export Default (A), BMJ (B)
  and RevMan (C). Keep table order and all columns, including both group
  counts and study weights. Default uses an author–year comma. BMJ and
  RevMan omit it in their built-in label formatting. To reproduce, pass
  `forest` to the capture script and `figure-2-forest` to the assembler.
- **Figure 3A.** Open Colditz 1994, select Risk ratio and run meta-regression
  using Absolute latitude as the sole moderator, REML and 95% CI.
  Recaptured at master `5d83000b4cea216ff7d7dd383a344f0e6dae2304`. Its
  horizontal gridlines sit exactly at RR 0.2, 0.5 and 1 in the PDF.
- **Figure 3B.** With the same sample and metric, run Small-study effects
  with the contour-enhanced funnel enabled and 90%, 95%, and 99% contours.
  Keep the common-effect pooled overlay.
- **Figure 4A.** Open Kearon 1998, select sensitivity, specificity and
  diagnostic odds ratio, and run the bivariate Reitsma model.
- **Figure 4B.** Open Pignon 2000 and run hazard-ratio trial sequential
  analysis with Table order because some studies lack publication year.
  Keep the cumulative statistical information axis and remaining defaults.

For Figures 3 and 4, open **Results → Edit plot**, select **Default**, and
accept. Then open **Export plot**, choose **PDF (vector)**, and save with
the proposed width and height. The driver asserts that choosing PDF
leaves the dimensions intact. The capture log records the title and
pagination controls as well as the export dimensions.

## Assembly and review

The assembled PDFs embed original plot panels at 1:1 and Figure 1's
captures at their native pixel dimensions at 300 dpi. Panels are
stacked vertically and share a 4 mm left margin with the visible edges of
the 28 pt Helvetica Bold labels. Each label has its own band above the
panel. A 6 mm gutter separates the previous panel from the next label
band. The PNGs render the assembled PDFs at 300 dpi.

| Panel | Export dialog (mm) | Exported PDF (mm) |
| --- | ---: | ---: |
| 3A Default regression | 241.4 × 143.3 | 241.300 × 143.228 |
| 3B Default contour funnel | 211.7 × 185.6 | 211.667 × 185.561 |
| 4A Default SROC | 177.8 × 174.8 | 177.800 × 174.625 |
| 4B Default TSA | 252.6 × 149.4 | 252.589 × 149.225 |

| Figure | Assembled PDF (mm) | PNG at 300 dpi (px) |
| --- | ---: | ---: |
| 3 | 245.300 × 364.422 | 2898 × 4305 |
| 4 | 256.589 × 359.483 | 3031 × 4246 |

Review of native-resolution tiles found legible legends and clear axes, titles and annotations without
clipped or overlapping text. All four labels start at x = 47 px, with
11 pt of clearance above their panels. The SROC legend has the tightest
spacing and its three entries remain distinct. Study markers overlap
where their plotted positions are close in the regression, SROC and TSA.

The capture comparison matches
the baseline analysis settings and checks that only style fields and
generated paths differ in the plot editor. The funnel's 13 log risk
ratios and standard errors, 90/95/99% contours and common-effect center
(log RR −0.4537096) match the BMJ capture. The saved R model comparison
confirms the regression intercept 0.2514643 and absolute-latitude slope
−0.02910166 on the log RR scale. The SROC summary point is FPR 0.0513148
and sensitivity 0.7716509. Full AUC is 0.9534711, and the plot displays
normalized partial AUC 0.87. TSA shows RIS 4,222, accrued 1,775 (42%), and
crossing at Bavaria 89. Its full sequence of 65 looks and monitoring
boundaries match the BMJ capture.
