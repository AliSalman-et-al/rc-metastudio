# Slice 7: import and wizard choices

Import data now opens the picker first. Cancel preserves the current project.
The loaded page uses the file name, a worksheet selector for multi-sheet workbooks,
a labelled data-type selector, Preview first and Map columns second. The redundant
required-fields table is removed. CSV options collapse below the preview and are
hidden for workbooks, whose reader always uses column labels. The blank CSV
template remains available as a small flat button. Errors appear in red; hidden
rows and columns use singular/plural notices. Import remains one undoable change.

DataTypePage already assigns every button a light/dark resource through
`_ICON_NAMES` and `_apply_theme_icon`. ChooseMetricPage alone added HR/IRR icons
and larger icon geometry. Those special cases are removed: metric choices are
uniformly text-only; data-type buttons retain their existing artwork. No new art
or numerical methods were introduced.

Evidence: `screens/slice7-{light,dark}-data-types.png` and
`screens/slice7-{light,dark}-metrics-*.png` capture the actual Qt pages. The XLSX
driver asserts uniform icon presence, hidden-column disclosure, an OLE-header
protected-workbook rejection, one-step undo/redo, and equal CSV/XLSX project JSON
with generated identifiers normalized. It also checks picker cancellation,
toolbar loading, page title, visible preview and no page scrollbar. CSV checks
its collapsed options can be opened. These are offscreen Qt/R checks, not native
file-picker or platform accessibility qualification.

The Slice 6 screenshot now lives at [screens/slice6-xlsx.png](screens/slice6-xlsx.png).

Final standalone checks (all passed):

- `xlsx-import`: `artifacts/verification/rcms/20261031T231157Z-bbfd5be2-xlsx-import`
- `csv`: `artifacts/verification/rcms/20261031T231220Z-46e46736-csv`
- `sheets`: `artifacts/verification/rcms/20261031T231234Z-cff4c0c5-sheets`
- `amino`: `artifacts/verification/rcms/20261031T231305Z-dd284a72-amino`

Each directory retains the command, runtime, inputs, screenshots and results.
The import view is also retained in [screens/slice7-xlsx.png](screens/slice7-xlsx.png).
- `hillclimb`: `artifacts/verification/rcms/20261031T231322Z-8545567e-hillclimb` (all five tasks completed with numerical/text receipts).

Requested final selection:
`source build/sheets-baseline/ENV.sh` then
`uv run --no-sync python -m pytest tests/e2e -n 2 -q -k "xlsx or csv or import or wizard"`
passed: **3 tests in 76.45 seconds**. All five standalone scenarios above passed
before this selection, one process at a time. No `uv sync` was run. One earlier
CSV invocation ended with signal 143 before producing a manifest; its standalone
retry and final CSV checks passed. Earlier failed XLSX evidence retains the undo
failure and the initially incorrect UUID normalization, both corrected before
the final runs.
