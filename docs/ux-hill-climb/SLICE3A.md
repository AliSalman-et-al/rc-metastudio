# Slice 3a: manuscript export

The Results window now offers PDF and DOCX in one save dialog. Both writers
consume a common content model from the executed result; exporting never calls
an analysis runner. Clipboard copy supplies HTML tables and plain text. The old
text-file export and its ResultsWindow helper are removed; observer checks now
exercise clipboard copy instead of calling the deleted helper.

`uv add python-docx` added python-docx 1.2.0 and lxml 6.1.3 to the lockfile.
No PDF dependency was added. QTextDocument lays out real tables; QPdfWriter and
QPainter paginate the report and paint SVG figures as vectors on separate pages.
DOCX uses real Word tables and PNG figures sized at 300 dpi. Figures use 85 mm,
or 180 mm for landscape aspect ratios above 1.4. Each has a numbered caption.

The result captures loaded RCMetaR/metafor/meta/mada versions at execution time.
The Methods paragraph cites these as loaded packages, rather than pretending that
every loaded namespace necessarily performed a fit. Study counts describe sheet
inclusion flags; they do not claim to count additional model-specific exclusions.
Continuity correction is described when the executed settings and input cells
require it. Existing formatted table cells are copied without numerical changes.

## Verification

Checks were written first in `tests/e2e/manuscript_export.py`. The scenario drives
the real non-native Qt save dialog for amino, continuous, and diagnostic results,
reopens DOCX with python-docx, checks table dimensions/cells and figure widths/count,
and extracts PDF text with the installed `/usr/bin/pdftotext` (no pypdf added).
This uses controlled dialog automation, not a native OS picker.

Environment: `source build/sheets-baseline/ENV.sh`; commands use `uv run --no-sync`.

- Manuscript export: passed, evidence
  `artifacts/verification/rcms/20261031T121149Z-70ba5bb6-manuscript-export`.
- Strict golden gate: passed, `build/slice3a-golden-final.log`, output root
  `build/qt6-verification/golden-compatibility-slice3a-final` (no oracle refresh).
- Full matrix: **133 passed in 3119.24 s**, `build/slice3a-matrix-qualified.log`:
  `python -m pytest tests/e2e -n 2 -q`. Includes manuscript-export, results-window,
  amino, continuous, all plot-workflow scenarios and hillclimb.
- Hillclimb: passed, `20261031T123406Z-ed6eba48-hillclimb`; retained workflow
  contains both `hillclimb-export.pdf` and `hillclimb-export.docx`.
  T5 completable: **no → yes**.

Earlier failed runs are retained. They exposed old text-export expectations in
shared observers; a later interrupted matrix is not counted as passing evidence.

First pages are rendered with pdftoppm. DOCX was converted using installed
LibreOffice headless, with a separate test-owned profile. Images:
`screens/slice3a-pdf-p1.png`, `screens/slice3a-docx-p1.png`.
