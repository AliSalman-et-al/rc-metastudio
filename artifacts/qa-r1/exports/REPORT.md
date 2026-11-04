# Export contrast fix

## Reproduction

Source: fix/qa-r1-exports, Linux/Xvfb, Qt Fusion dark palette.
Strict typing ran first with Windows target; exact command and output are in
`typing-before.log` and `typing-final.log`.

```
RCMS_QA_APP_SRC=$PWD /home/ali/.t3/qa-env/tools/venv/bin/python /home/ali/.t3/qa-env/tools/ui.py --session exports start --dark
```

Native actions: Ctrl+O; Ctrl+L in the GTK chooser; open
`sample_projects/amino.rcms`; Analyses > Meta-analysis; default binary random
DerSimonian–Laird; Run analysis; Alt+Tab to Results; Export report; save
`artifacts/qa-r1/exports/dark-before.pdf`. Session stopped afterward.

```
pdftoppm -r 60 -png artifacts/qa-r1/exports/dark-before.pdf artifacts/qa-r1/exports/dark-before
pdftohtml -xml -stdout artifacts/qa-r1/exports/dark-before.pdf
```

Observed: body, heading and caption font colours are #eeeeee; table borders
remain black. See dark-before-1.png. Text extraction alone misses the defect.
Qt's default QTextDocument painting palette inherits QApplication Text.

## Change and proof

Shared PDF text-document setup explicitly colours all text black on white,
including supplementary pages and figure captions. DOCX Normal, Title,
Heading 1 and Caption explicitly use black rather than Word theme colours.
No fitting or number formatting changed.

`source /home/ali/.t3/qa-env/ENV.sh; export PYTHONPATH=$PWD/src:$PWD`
then `python scripts/verify_rcms.py manuscript-export-direct` passed in
`artifacts/verification/rcms/20261104T093144Z-25aa7150-manuscript-export-direct`.
This run predates the DOCX style change and final assertion refinement.
It checked all four sample report families, content/table values, caption
geometry, clipboard content, supplementary ordering and writer lifetime under
a dark text palette. dark-after-1.png through dark-after-6.png were rendered
at 60 DPI from that run's amino.pdf and visually inspected: readable text,
complete tables, separate forest page, readable captions and references.

LibreOffice command:
`soffice -env:UserInstallation=file:///tmp/rcms-exports-lo --headless --convert-to pdf --outdir artifacts/qa-r1/exports <workflow>/amino.docx`
The first rendered DOCX page is docx-render-1.png: readable black body, blue
Word template headings (subsequently changed to explicit black).
`docx-document.xml` retains the extracted document XML.

Light comparison: rendered the existing CI amino PDF from
`/home/ali/.t3/qa-round1/ci-evidence/shard1/rcms/20261104T065803Z-54c10749-manuscript-export-direct/workflow/amino.pdf`
at 60 DPI to light-ci-*.png. This is existing CI evidence, not a fresh native
light-mode qualification.

## Audit boundaries

Report UI offers PDF and DOCX only. Copy report publishes HTML and plain text;
table CSV uses UTF-8 BOM and Python csv quoting. R plots use a standalone SVG
with white background; PDF/PNG/TIFF derive from it, not Qt's palette. These are
code-audit observations, not proof of every native export path.

Final targeted run uses sample filenames containing spaces, an en dash and
Greek alpha, and asserts actual black PDF text for Methods, Figure captions
and Supplementary details. Poppler font definitions are document-global.

Not completed: native after-fix light/dark and large-font matrix; native DOCX
before/after; four plot formats in both themes; CSV and overwrite-dialog
native drives; exhaustive fonts/margins/word-splitting review of all report
families. No full pre-push was run, as requested; CI owns that qualification.
Existing numerical/golden references were not regenerated.

Precision/notation handoff to PR3: supplementary Full-precision results and
Text report/raw producer output retain their existing number formatting.
No precision or scientific-notation changes were made here; this drive did
not independently reproduce the example `Q = 2.164253e-31`.

## Final-source result

`python scripts/verify_rcms.py manuscript-export-direct` PASSED:
`artifacts/verification/rcms/20261104T093903Z-d499a20d-manuscript-export-direct`.
Final executable source, DOCX styles, Unicode filenames, actual PDF colour
assertions and all existing report content/layout assertions passed. Exact
command/runtime/artifact hashes are in that run's manifest.json.

Final native drive repeated amino analysis under `start --dark --large-font`;
exported PDF and DOCX using the actual GTK save dialog. See
`dark-large-analysis.png`, `dark-large-result.png`,
`dark-large-docx-saved.png`, `dark-large-final.pdf`, `dark-large-final.docx`.
`pdftoppm -r 60 -png dark-large-final.pdf dark-large-final` rendered all pages;
first page inspected and readable black on white. Native session stopped.
This adds dark/large-font final export proof, but does not fill the remaining
light-theme, four-format plot, overwrite, and table/CSV audit gaps above.
