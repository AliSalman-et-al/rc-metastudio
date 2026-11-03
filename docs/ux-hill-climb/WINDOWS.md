# Windows verification: forest footers and manuscript export

These presentation/lifecycle fixes are independent of STAT-FIXES and change no
statistical calculations, numerical contracts, oracle data, or gate limits.

## Forest footer regression after 769f80b0

The Windows Full R Stack transcript supplied as `/tmp/jrs5.log` reports different
SVG y coordinates for the two Favours labels in `ux-improvements` and
`results-window`, and footer text outside the device in `ratios-irr`.

Footer wrapping used PNG measurements followed by svglite output. It also
assumed the requested plot width survived the device-width cap, used a fixed
physical allowance per wrapped line, and left vertical text adjustment implicit.
That combination depends on font/device metrics. Default-style `mtext` uses an
absolute cex while `strwidth` scales with the current graphics cex.

The R renderer now measures on its SVG device, budgets wrap widths against the
capped device and graphics margins, and measures line spacing in inches. The
journal layouts solve header/footer clearance together on the final device.
Default margin text is measured at its absolute scale. Direction labels share an
explicit baseline; the direction keyword stays intact while long arm names wrap.

The retained wide-font drive uses production analysis/rendering with an SVG
presentation-device override: 16-point DejaVu Sans Mono, all three forest styles,
short labels and long/unbroken arm names. The original renderer fails the existing
footer device-bounds assertion. The fixed renderer passes the unchanged bounds,
non-overlap, and exact two-baseline assertions. Reproduce from repository root:

```
source build/sheets-baseline/ENV.sh
mkdir -p build/sheets-baseline/footer-after
"$RCMS_R_HOME/bin/R" CMD INSTALL --library="$RCMS_R_LIBS" r/RCMetaR
"$RCMS_R_HOME/bin/Rscript" r/RCMetaR/inst/qa/render_footer_metrics.R build/sheets-baseline/footer-after
PYTHONPATH=. uv run --no-sync python r/RCMetaR/inst/qa/check_footer_metrics.py build/sheets-baseline/footer-after
```

The output directory retains the SVGs, input RDS files and geometry JSON. This is
local font-stress evidence, not a native Windows rendering qualification.

## Manuscript picker and modal timing

Windows decision evidence in `/tmp/jrs5.log`: `manuscript-export-direct` completed
all 28 writes with the observed writer resources released. Its later failure was
the zero-delay small-study callback calling `reject()` on a missing modal. The
dialog variant crashed inside the non-native QFileDialog event loop at picker 5,
during stress cycling, despite prior dialogs/models being destroyed. This
separates writer lifetime from that offscreen picker failure.

There are no `DontUseNativeDialog` occurrences in `src/`. The production export
uses QFileDialog's platform-native picker; the non-native picker in this scenario
is an explicit automation fixture. The dialog scenario retains real non-native
pickers for exactly the first PDF and first DOCX export in the process only.
All later exports use the picker seam. Stress cycles still
trigger the same public export action, with the picker seam returning the target
path. Every export, retained file, content assertion, numerical/prose receipt and
writer-resource assertion remains. Evidence records `manuscript-stress-picker-seam`
for those cycles. The direct variant remains a separate writer-lifetime control.
The small-study callback waits for a visible PublicationBiasDialog before running
or rejecting it.

**The native Windows file picker remains untested by this automation and needs a
person's check:** on Windows, open results, export PDF and DOCX through the normal
picker, repeat after closing/reopening results, and check cancellation and the
saved documents. Local offscreen runs cannot establish that native interaction.

Local evidence and transcripts for this work are retained in
`build/sheets-baseline/windows-*.log` and the directories those transcripts name
under `artifacts/verification/rcms/`. No golden baseline was regenerated.

The targeted desktop rerun also updates the old recoverable-error focus receipt:
focus now belongs to the Details button, matching the earlier requested removal
of the error-label caret. Baseline, bounds and overlap assertions are unchanged.

### Local targeted receipts

All five reported scenarios passed on the installed current R source. Evidence
under `artifacts/verification/rcms/`:

- `20261102T022932Z-3114f7df-ux-improvements`
- `20261102T023216Z-a2a8b08d-results-window`
- `20261102T023809Z-344fa699-ratios-irr`
- `20261102T024514Z-0b64cf8a-manuscript-export`
- `20261102T024704Z-75373204-manuscript-export-direct`

The manuscript receipts require 20 PDF and 8 DOCX writes, released writer
resources, and, at that revision, 8 real picker interactions in dialog mode (0 in direct mode).
R renderer tests passed with their existing assertions; the corrected standalone
invocation explicitly attaches `metafor` before `testthat::test_file`.
The wide-font drive passed all six cases; `footer-after/` retains input RDS files,
SVGs and `geometry.json`. R installation commands/transcripts and source SHA-256
receipts are in `build/sheets-baseline/windows-footer-*`.

### Windows Full R Stack at 520c362c

`/tmp/jrs6.log`, line 1227, records 136 of 137 scenarios passing; only
`manuscript-export` crashes. The access violation occurs in the fifth real
non-native QFileDialog (`picker_number: 5`), now at `lymph-pdf`. The earlier
failure was at `amino-stress-2`, also picker 5. `manuscript-export-direct` passed
all exports. This implicates repeated non-native picker use in one process,
rather than a particular dataset or writer.

The dialog scenario now exercises exactly the first PDF and first DOCX with
real non-native pickers, and returns paths through the picker seam for all later
exports. All 20 PDF and 8 DOCX writes and their file, content and resource-release
assertions remain. Direct mode still uses zero pickers.

The native Windows picker still needs a person's check; this offscreen fixture
does not qualify native save or cancellation behavior.

Local offscreen verification of the two-picker change passed both scenarios:

- `artifacts/verification/rcms/20261102T034227Z-34825d6d-manuscript-export`:
  exactly 2 real pickers (`pdf`, `docx`), 20 PDF and 8 DOCX writes.
- `artifacts/verification/rcms/20261102T034444Z-a40f8b3a-manuscript-export-direct`:
  0 real pickers, 20 PDF and 8 DOCX writes.

Both retain the existing file/content and writer-release assertions. These local
receipts do not establish a passing rerun of the Windows Full R Stack.
