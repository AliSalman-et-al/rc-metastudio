# RC MetaStudio UI/UX review — 15 November 2026

Implementation follow-up: [changes and verification](ui-ux-implementation-2026-11-15.md).
The observations below describe the original review captures.

This review uses **267 indexed native Windows captures** covering the application's
main surfaces, normal light/dark theme pairs, custom dark stress views and three
exported pages. Opus 5.5 High surveyed all 41 contact sheets and inspected 21
full-resolution originals. Codex checked the principal findings against the
screenshots and source. No product code changed during this review.

- [Annotated screenshot gallery](C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/verification/ui-ux-audit-2026-11-15/gallery.html)
- [Original Opus review, with screenshot and source references](C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/verification/ui-ux-audit-2026-11-15/opus-review.md)
- [Coverage and capture limitations](C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/verification/ui-ux-audit-2026-11-15/coverage.md)
- [Screenshot index](C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/verification/ui-ux-audit-2026-11-15/capture-index.json)

## Priorities

| ID | Priority | Finding and recommended change |
| --- | --- | --- |
| UI-1 | High; observed | **Live theme switching leaves stale colours.** The Analysis menu, Advanced and CSV options disclosures, inline errors and results headings/rules can lose contrast. Prefer native controls and the application's shared style; refresh explicit scene/HTML/error colours on palette changes. Prove both switch directions on already-open windows. |
| UI-3 | Medium; observed | **Funnel-family editors expose an internal R temporary path as “Save image to”.** Hide that internal row, as the forest editor already does. Keep user export in Results. |
| UI-2 | Medium; observed | **Prediction-interval explanatory prose is inserted into the Results paragraph and a Model fit value row.** Present it once as a clearly associated note. Preserve its scientific meaning, transform notes and retention in copied/exported reports. This is a presentation issue, not evidence of an incorrect estimate. |
| UI-6 | Medium; observed | **The diagnostic metrics dialog reverses the usual affirmative/Cancel order.** Match the other application footers and use sentence case for its heading. |
| UI-8 | Medium polish; observed | **Results/calculator table headings and number alignment differ from the accepted grid convention.** Use bold, data-aligned headings where appropriate; stop stretching compact results so widely that labels and values become disconnected. |
| UI-4 | Medium polish; observed | **Supplementary details flatten study tables into repeated key:value blocks.** Prefer structured tables with clear provenance. Do not reduce density by deleting fields or scientific notes. Check the DOCX and complete-output retention contracts before changing representation. |
| UI-7 | Low polish; observed | **Plot-editor labels mix colons and Title Case.** Apply a small sentence-case and label-punctuation sweep without changing parameter meaning. |
| UI-5 | Investigate; partly inferred | **Width-fit captures of square plots hide their bottom axes.** Evaluate a whole-plot view for these plot types, preserving readable labels and the existing explicit Fit width command. This is not yet a confirmed first-open defect. |

Useful direct examples:

- [Analysis menu after switching to light](C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261115T084210Z-d0c243b4-ui-crawl/12-0-A-menu-analysis-light.png).
- [Advanced disclosure missing in light](C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261115T084928Z-731e2493-ui-crawl/02-0-E-binary-method-light.png).
- [Funnel editor's internal path](C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261115T084210Z-d0c243b4-ui-crawl/211-0-H-funnel-bottom-light.png).
- [Manuscript and prediction-interval explanation](C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261115T084210Z-d0c243b4-ui-crawl/152-0-F-amino-manuscript-light.png).
- [Diagnostic metrics footer](C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261115T084928Z-731e2493-ui-crawl/36-0-E-diagnostic-metrics-light.png).
- [Results table spacing](C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261115T084210Z-d0c243b4-ui-crawl/156-0-F-amino-tables-light.png).

## Recommended first polish batch

1. Fix the live-theme defects and add targeted native checks for the actual
   rendered menu, disclosures, errors and results labels after both transitions.
2. Hide internal funnel-editor output paths.
3. Move explanatory prediction-interval text into a note, with copy/PDF/DOCX
   retention checks preserving all scientific content.
4. Normalize the diagnostic footer and obvious label inconsistencies.

This keeps the accepted grid, outcome tabs, New project/Add outcome distinction,
upright numeric values, Default plot-style fallback and bordered CI button.

## Additional design suggestions

- **Empty home state:** Codex observed action cards expanding far beyond their
  content when there are no recent projects. Let them size to their contents;
  avoid a fixed pixel height. [Capture](C:/Users/Ali-Salman/Documents/Code/rc-metastudio/artifacts/verification/rcms/20261115T084210Z-d0c243b4-ui-crawl/02-0-A-home-light.png).
- **Metric wizard step:** Opus suggests either a short definition of the chosen
  effect measure or combining the sparse single-combo step with outcome details.
  A definition is the smaller intervention and should be tried first.
- **Converted calculator displays:** investigate excessive floating-point digits
  after ratio/log conversion. Format derived displays without silently rounding
  original inputs or stored precision. The conversion path was not traced in
  this review, so this remains a candidate improvement.

## Qualifications and judgment

The light/dark pairs switch an already-open window in-process; they are not
separate fresh launches. The contrast failures are directly visible. An actual
Windows-settings theme change was not driven. Opus supplied disposable widget
probes, but those scripts were not retained with this bundle; use the retained
native workflow to qualify any implementation rather than treating the probes
as formal verification evidence.

The plot crawl explicitly invokes **Fit width** before the relevant captures.
`ResultsWindow._show_initial_result` also activates width-based fitting, but its
automatic SVG sizing preserves a minimum body-text size. Reproduce first-open
behaviour and check label legibility before changing that policy. Do not simply
shrink every plot to fit its height.

Opus also suggested a stylesheet-string lint. This review does not recommend
adding that gate: literal-colour checks would miss palette-caching failures and
require exceptions for legitimate swatches. Actual theme-transition behaviour
is the more useful proof.

White publication canvases in dark mode are intentional output presentation,
not automatically theme defects. No numerical-method or statistical-authority
change is recommended here.

## Capture provenance and reproducibility

The native helper retained exact commands, fixture inputs, runtime identity,
steps, screenshots and manifests. All 563 retained files across the three source
runs were hash-checked. Strict win32 typing passed before each GUI run.

```powershell
$env:RCMS_R_HOME = 'C:/Program Files/R/R-4.6.2'
$env:RCMS_R_LIBS = (Resolve-Path build/ui-polish-r-library).Path
$env:PATH = "$(Resolve-Path build/poppler/poppler-26.09.0/Library/bin);$env:PATH"
$env:QT_SCALE_FACTOR = '0.8'
uv run python scripts/verify_rcms.py ui-crawl --native

# Continue selected sections without repeating the entire inventory:
$env:RCMS_UI_CRAWL_SECTIONS = 'E,S'
uv run python scripts/verify_rcms.py ui-crawl --native
```

On this host the scale factor produced effective 100% native captures. Main
windows are generally 1280×800, with an additional 1024×700 grid view. Runtime:
Qt/PyQt 6.12.0, Python 3.14.10, R 4.6.2 and RCMetaR 0.5.4 with pinned packages.

- The broad run completed all its application sections but its completeness
  gate **failed** because external DOCX-to-PDF rendering requires unavailable
  LibreOffice. DOCX generation and PDF previews were retained.
- The supplementary analysis pass captured IRR setup before a capture-helper API
  typo stopped the last structure screens. The corrected structure continuation
  then **passed**, including current context menus, arm rename and Add outcome.
- The original failed manifests are preserved, not relabelled as passes.

The bundle does not establish external DOCX page rendering, native OS picker
appearance, other operating systems/DPI settings, exhaustive state combinations,
human task timings or complete statistical/release qualification. Some forms are
opened directly to photograph their states. The legacy Welcome page is an
explicit inventory jump, not the current home screen.

Only capture-harness and review-documentation changes were made for this task.
Previously approved product changes remain uncommitted.
