# Slice 6 — XLSX import

XLSX files use the existing CSV mapping/preview and import transaction. Visible
worksheets are selectable; the first with data is selected. Stored numbers remain
text without locale inference. Dates in Year use the year; other dates use ISO.
Formula caches and hidden rows/columns are disclosed. Missing formula caches,
mapped numeric Excel errors, intersecting merges, corrupt workbooks and `.xls`
are rejected before confirmation. Import actions now say “Import data”.

Dependency: openpyxl 3.1.5, added without syncing/rebuilding rpy2. Doctor passed.
Linux PyInstaller explicitly includes openpyxl; no bundle was built here.

The `xlsx-import` real Qt/R scenario retains generated workbooks, CSV equivalent,
project files and screenshots. It checks worksheet selection (hidden sheet
excluded), exact CSV payload equality, identical analysis text, formula caches,
missing caches, error cells, merges, hidden row disclosure, corrupt/old formats,
float precision, year dates, and save/reopen. Initial failure evidence:
`20261031T225850Z-5c1cc64d-xlsx-import` (XLSX decoded as CSV).
Final evidence receipts are listed below after execution.

Limitations: native OS picker, password-encrypted fixture, hidden-column fixture,
all error codes, import undo gesture and project-JSON byte equality have not been
separately driven. Payload equality and numerical result-text equality are proved;
project identity bytes are not compared. Existing CSV validation/transaction is
reused. No oracle changed. Screenshot: [screens/slice6-xlsx.png](screens/slice6-xlsx.png).

Final serial receipts (`artifacts/verification/rcms/`):
- `20261031T230328Z-052e237f-xlsx-import`
- `20261031T230342Z-40ec4f85-csv`
- `20261031T230353Z-2610a837-sheets`
- `20261031T230411Z-21f0c6a5-amino`

All four passed. `uv run --no-sync python -m pytest tests/e2e -n 2 -q -k
"xlsx or csv or import or wizard"` passed **3 tests** (74.27 seconds).
Doctor: `20261031T225832Z-9ace08c7-doctor`. Every manifest records exact
commands, runtime, input hashes and retained workflow artifacts. Leading empty
rows/columns plus hidden rows failed first in `20261031T230302Z-99214dbb-xlsx-import`
and pass in the final run. An earlier pytest attempt was invalidated by editing
this note during driving; the final run had no concurrent edits. One earlier
sheets/amino invocation overlapped accidentally; both were rerun serially above.
Ruff was unavailable; compileall and `git diff --check` passed.
