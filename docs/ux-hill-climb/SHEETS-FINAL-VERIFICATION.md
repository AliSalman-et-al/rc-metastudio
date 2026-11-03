# Sheets final UI and packaging verification

Environment: `source build/sheets-baseline/ENV.sh`; all Python commands use
`uv run --no-sync`. No oracle regeneration or numerical changes.

Commands, run sequentially:

- `uv run --no-sync python scripts/verify_rcms.py ratios-hr`
- `uv run --no-sync python scripts/verify_rcms.py hillclimb`
- `uv run --no-sync python scripts/verify_rcms.py results-window`
- `"$RCMS_R_HOME/bin/Rscript" .agents/skills/verify-rcms/scripts/analysis_authorities.R build/sheets-baseline/authorities-final.json`
- `uv run --no-sync python scripts/verify_rcms.py xlsx-import`
- `uv run --no-sync python -m pytest tests/e2e -n 2 -q -k "results or wizard or ratios"`

The first four desktop scenarios passed, with repeatable input/action/result
artifacts in `artifacts/verification/rcms/`:

- `20261101T052818Z-9d0a51b1-ratios-hr`
- `20261101T053127Z-148e9604-hillclimb`
- `20261101T053159Z-64ff69e1-results-window`
- `20261101T053349Z-628e0a57-xlsx-import`

The authority report passed 100 comparisons. Scenario transcripts and the JSON report
are retained in `build/sheets-baseline/*-final.log` and `authorities-final.json`.
The results-window drive asserts no horizontal scrollbar on amino Model results
and a gap of at most 32 logical pixels between the last row and Copy table.
The refreshed metric screenshot comes from xlsx-import; the dark table screenshot
comes from results-window's `15-0-slice8b-results-tables-dark.png`.
These are offscreen Qt/R checks, not native desktop or release-package qualification.

Packaging audit: Linux explicitly included only openpyxl; Windows and macOS
had no explicit export-package imports. All three production specs now include
openpyxl, docx, lxml.etree and `docx/templates/*` data. The macOS feasibility
spec only builds its Qt/R feasibility entry, not the application. Windows/macOS
build scripts and the Linux package wrapper install the locked project environment;
python-docx brings lxml transitively in uv.lock. No build/smoke exclusion removes
these packages. Full platform bundles were not built in this Linux UI verification.

The first pytest attempt was terminated with SIGTERM (143), leaving two owned
drivers; both were terminated before retrying. Its partial transcript is retained
as `build/sheets-baseline/pytest-interrupted.log`. A detached launch did not survive
tool cleanup; the final run uses a dedicated live process.

Final dedicated pytest run completed uninterrupted: **4 passed in 234.40s**.
Per-case manifests and inputs remain in `artifacts/verification/rcms/`.
Afterward, the actual PyInstaller `collect_data_files("docx", includes=["templates/*"])`
returned the default Word template and ancillary template XML files. All packaging
specs compiled; installed docx/openpyxl created real Word/Excel files and lxml.etree
imported. Results and outputs are retained as `build/sheets-baseline/packaging-final.log`,
`packaging-document.docx`, and `packaging-workbook.xlsx`.
