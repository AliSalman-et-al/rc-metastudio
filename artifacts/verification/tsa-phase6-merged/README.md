# Merged TSA qualification

The merge commit `c0c0409cb33a5d5945705cacbd9a726f66d8c853` has parents
`9662ff12f57b91f9dd2f5853212787f3de754773` (plot redesign) and
`931c9374bc56a31c0f9f1ccb390635bc45238dd6` (workflow improvements).
The tested source is `82bf2cf2cab7cf740ff291f0921126dd4e5fe680`. The final
evidence commit records these runs without changing application or test code.

- The R conflict was resolved by passing the monitoring boundary calculated
  by the workflow directly to the redesigned renderer. The same fit supplies
  the primary result, and sensitivity stays a separate calculation.
- The report conflict was resolved with a figure note rendered below its
  heading. The export check found the PDF text present but invisible below
  the plot, so the note now uses the PDF print palette. The failed visual
  assertion is in [the first export check](qualification/review/report-note-before.log).
- Git merged the changelog, ADR, scenario registry and numeric contract
  cleanly. The guide was edited to describe the plot and workflow together.
  The numeric contract keeps the workflow's measure-specific headers and its
  existing numbers. The plot descriptor keeps the redesign's geometry.
- The first [Peto run](qualification/native100/tsa-peto-failed.log) expected
  one table. The corrected scenario requires a sensitivity table for the
  default calculated RIS while the entered-RIS scenarios still check its
  absence. The first 150% BCG run was invalidated when the PDF fix was
  committed during the drive. The [initial native archive](initial-native-attempts.zip)
  retains both attempts. The final runs start from a fixed revision.

## Replay

Use the repository's locked `uv` environment on Windows x64. This run used
Qt 6.12.0, R 4.6.2 from the 0.5.6 bundle, and Poppler 26.09.0. The replay
uses the same pinned seed library as Phase 5, copies its dependencies into
`.tmp/tsa-phase6-library`, and installs RCMetaR from the checkout. The
[install transcript](qualification/setup/install.log),
[source tree identity](qualification/setup/source.txt) and
[runtime identity](qualification/setup/doctor/runtime.json) record provenance.
The tested source has the identical RCMetaR tree. The host display scale was
125%. The replay sets Qt factors of 0.8 and 1.2 and verifies the observed
device scale in the capture data. Run the native lanes serially because the
reports use the Windows clipboard. Use `-Run <name>` for a fresh output folder.

```powershell
$replay = './artifacts/verification/tsa-phase6-merged/replay.ps1'
& $replay -Lane typing
& $replay -Lane setup
& $replay -Lane r
& $replay -Lane python
& $replay -Lane native100
& $replay -Lane native150
& $replay -Lane print
& $replay -Lane review
```

The [typing transcript](final/typing/typing.log) has the exact repository-wide
Ty command and `win32` target. The [passing R transcript](final/r/r-tests.log) covers
the TSA numerical and bundle tests, plus the related bubble, small-study,
Reitsma and visual inventory tests. The full `tests/python` run finished with
869 passed, one skipped and one failure. The pre-existing
`test_result_owner_exception_still_deletes_real_specs_and_progress` failure
is an `AttributeError` for the test double's missing `is_diagnostic` method.
It [reproduces at `4151624c`](final/baseline/result-owner-exception.log).
See the [full Python transcript](final/python/python-tests.log).
The separate [golden comparison suite](final/python/golden.log) passed all 68 tests.

## Native, print and export evidence

All six plot cases passed at both scales. They cover BCG OR with the penalised
curve, Pignon HR, entered MD, RR MH with a futility crossing, the 36-look
stress case, and BCG Peto. The SMD guard also passed at both scales. The BCG and HR drives assert
asynchronous conclusion previews. BCG also changes power and the anticipated
effect in the same Results window and verifies a clean unchanged rerun. The
Peto scenario checks the fixed-effect notice, sensitivity, and the 68%
crossing at Stein & Aaronson. The plot checks also cover the axis toggle,
regeneration and a native TIFF export.

| Style | Native captures at 100% and 150% | Print at 89, 120 and 174 mm |
| --- | --- | --- |
| Default | [Native](final/review/native-default.png) | [Print](final/review/print-default.png) |
| RevMan | [Native](final/review/native-revman.png) | [Print](final/review/print-revman.png) |
| BMJ | [Native](final/review/native-bmj.png) | [Print](final/review/print-bmj.png) |

The [geometry and report audit](final/review/review.log) validates artifact
hashes, device scales, plot layout, crossing geometry and decoded exports.
The Peto Default [ring diameter](final/review/ring-diameters.csv) grew from
0.0344 in to 0.1600 in in the nominal SVG. The off-panel fixture checks the
ring around both triangle orientations and retains the 1.35× minimum ratio
to the crossing triangle. The [print transcript](final/print/print.log)
records all three widths and exact monitoring knots. PDF fonts are embedded,
SVG text is outlined, and TIFF output decodes with LZW compression at the
requested DPI.

The BCG report was opened as [PDF](final/review/report/report.pdf) and
[DOCX](final/review/report/report.docx). The audit rasterizes every PDF page,
checks the figure note in the text summary and on the figure page, and
decodes the DOCX tables and figure. It also checks the [copied HTML](final/review/report/copy.html),
[formatted CSV](final/review/report/bcg-1-formatted.csv) and
[numeric CSV](final/review/report/bcg-1-values.csv) against the held report.

The [native archive](native-evidence.zip) contains both scales' manifests,
inputs, steps, screenshots, reports and workflow exports, plus the runtime doctor run. The
[print archive](print-evidence.zip) contains the sized PDF, SVG, TIFF and
geometry fixtures. Each archive stores its scenario or width directories
relative to `final/`. The scenarios use controlled file paths and a real
Windows Qt/R runtime. The replay does not qualify OS file pickers or a
packaged installer.
