# Slice 8A

The opening notes below describe the inherited partial implementation. The numbered completion record supersedes their unfinished items and interrupted test status.

Import: the unlabelled “Binary” selector was a worksheet name, not a data family.
It now has a Worksheet label; Data type remains the single format selector.
Removed the redundant preview caption and made the blank-template action a link.
The xlsx-import scenario now clicks the welcome-page Import data button and checks
that the selected workbook is loaded and ready to import. It also retains the
existing toolbar and equivalent-CSV checks.

Metric: removed both instructional paragraphs, removed the title ellipsis and
label colon, and used metric names instead of code prefixes. Proportion, Odds
ratio (OR), Risk ratio (RR), Risk difference (RD), Mean difference and Standardized
mean difference (SMD) have explicit clinical names; other names use sentence case.
The default marker remains on the initially selected default only. This is the
new-sheet wizard; existing sheet metric-change warnings were not changed.

Calculators: the shared readout uses three decimal places for p-values, with
<0.001 for smaller values. Diagnostic readouts retain labelled SE but omit Z and
P. Diagnostic reconstruction now uses the same “Reconstruct group data” label as
the other two dialogs; “Entered Effect” becomes “Entered effect estimate”, and
Disease +/− and Test +/− lose parentheses. Display assertions changed only for
the intended p-value text; R numerical comparisons remain intact.

HR from p: not offered. RatioDataDialog accepts ratio plus CI or log ratio plus
SE. CalculatorService has no HR-from-p operation. No conditional SE assertion was
added.

Amber finding: dataset_table_model.py applies #D6A93A and italic font to all
populated effect columns, including entered values. It does not mark disagreement
between computed and entered effects. Replacement is unfinished; no color change
is claimed.

Copy-sweep count: 0 additional strings changed. Candidate searches were run in
Python and UI files, but reviewer-visible triage/rewrite remains unfinished.
The explicitly requested calculator wording above changes 6 distinct strings;
wizard naming changes are described separately above.

Unfinished: group SE/CI and prevalence precision; binary result-table height and
column fit; neutral computed-cell styling in both themes and grid screenshots;
full wizard copy review and conditional entered-effect warning audit; complete
copy sweep. No numerical calculation or accepted-value code was changed.

Evidence: screens/slice8a-import.png, slice8a-metric.png and
slice8a-calculator-{binary,continuous,diagnostic}.png. These are Qt offscreen
captures; they do not establish native display behavior. Verification manifests,
commands, runtime identities, screenshots, inputs and transcripts remain under
artifacts/verification/rcms/. Final run status is recorded below.

Verification setup: source build/sheets-baseline/ENV.sh; then
`uv run --no-sync python scripts/build_qt6.py generate --build-root "$RCMS_QT6_BUILD_ROOT"`.
The first runs used stale generated forms; these were superseded by rebuilt runs.
The first selected pytest run was interrupted after 5 passes for that rebuild.

All nine rebuilt desktop scenarios passed (each invoked as
`uv run --no-sync python scripts/verify_rcms.py SCENARIO`):
- xlsx-import: Evidence: /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/artifacts/verification/rcms/20261031T232551Z-ac0303db-xlsx-import
- csv: Evidence: /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/artifacts/verification/rcms/20261031T232609Z-3390d23a-csv
- calculator-binary: Evidence: /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/artifacts/verification/rcms/20261031T232621Z-214390e0-calculator-binary
- calculator-continuous: Evidence: /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/artifacts/verification/rcms/20261031T232639Z-3ff90ac3-calculator-continuous
- calculator-diagnostic: Evidence: /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/artifacts/verification/rcms/20261031T232653Z-901b3f1b-calculator-diagnostic
- calculator-ratio-precision: Evidence: /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/artifacts/verification/rcms/20261031T232720Z-c4c61930-calculator-ratio-precision
- amino: Evidence: /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/artifacts/verification/rcms/20261031T232905Z-1b021e89-amino
- sheets: Evidence: /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/artifacts/verification/rcms/20261031T232918Z-3fb896f0-sheets
- hillclimb: Evidence: /home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/artifacts/verification/rcms/20261031T232935Z-b0d3d023-hillclimb

Selected E2E command: `uv run --no-sync python -m pytest tests/e2e -n 2 -q -k "calculator or wizard or import or csv or ux or audit or review"`.
Stopped cleanly for partial handback: 9 passed in 213.25s, exit 2
(KeyboardInterrupt), no reported failures. This is incomplete, not a passing suite.
Both remote pushes were withheld. Remaining default-marker behavior when changing
selection also needs review; the existing marker behavior was retained.

Step 1: removed amber, italics and forced black text. Effect cells use a low-opacity neutral gray overlay and inherit theme text. No calculation changes.

Step 2: group numeric cells use estimate precision only when painted; prevalence paints at estimate precision and retains round-trip text. Binary metric table fits its rows and columns. Existing accepted-row and numerical assertions remain the verification gate.

Step 3: searched all top-level Python and forms UI text setters, titles, tooltips, messages and strings (R output and method names excluded). Focused replacements:
- dataset_table_view.py: Invalid clipboard cell → Clipboard value cannot be used
- main_window.py: Importing from CSV... → Import CSV
- diagnostic_data_dialog.ui: INCONSISTENT FORM → Check the study values
- binary_data_dialog.ui: INCONSISTENT FORM → Check the study values
- progress_dialog.ui: Running Analysis... → Running analysis
- csv_import_page.ui: Quote Character: → Quote mark
- csv_import_page.ui: Delimiter: → Column separator
- csv_import_page.ui: Has column labels? → First row contains column names
- csv_import_page.ui: CSV exported from Excel? → Use Excel CSV format
- csv_import_page.ui: Preview of imported data → Data preview

Step 4: remaining wizard page copy:
- data_type_page: One piece of data from each study or studies with one group → One group per study
- data_type_page: Data on two or more groups per study → Two or more groups per study
- data_type_page: Data on test performance → Diagnostic test accuracy
- outcome_name_page: Name the outcome and arms → Outcome and groups
- outcome_name_page: Enter the outcome being measured → For example, mortality
- outcome_name_page: Arm names are optional. Leave them blank to use Intervention and Control. → Default group names: Intervention and Control.
- welcome_page: What would you like to do? → Start a review
- csv_import_page: Choose an Excel or CSV file. → Excel or CSV file

The outcome page runtime title also uses Outcome and groups / Outcome. Capture setup selects data before entering dependent pages and includes the alternate-row palette.

Visual follow-up: restrict fixed estimate precision to group SE and CI columns; sample sizes and other summaries retain their compact display. First full pytest attempt ended externally with SIGTERM (exit 143) after 13 passes, no failures or final summary. Owned orphan children were closed by PID before retry.

First uninterrupted selected suite: 50 passed, 1 failed in 1675.16s. review1-design timed out waiting behind the import file picker; its later italic/amber assertion was also obsolete. Updated the real start-page drive to supply a test-owned CSV and check normal font plus composited theme-text contrast. Targeted review1-design passed: artifacts/verification/rcms/20261101T002146Z-58823f8d-review1-design. All numerical assertions are unchanged.

## Final completion evidence

All nine requested serial scenarios passed on the final rerun. Commands used `source build/sheets-baseline/ENV.sh` and `uv run --no-sync python scripts/verify_rcms.py SCENARIO`; no uv sync was run.
- xlsx-import: `artifacts/verification/rcms/20261101T002217Z-bf9d1df7-xlsx-import`
- csv: `artifacts/verification/rcms/20261101T002236Z-8fd59e93-csv`
- calculator-binary: `artifacts/verification/rcms/20261101T002247Z-d4e1f29e-calculator-binary`
- calculator-continuous: `artifacts/verification/rcms/20261101T002302Z-5d20bf55-calculator-continuous`
- calculator-diagnostic: `artifacts/verification/rcms/20261101T002314Z-750b1dfc-calculator-diagnostic`
- calculator-ratio-precision: `artifacts/verification/rcms/20261101T002340Z-6f73c8e9-calculator-ratio-precision`
- amino: `artifacts/verification/rcms/20261101T002524Z-f5b0ed3e-amino`
- sheets: `artifacts/verification/rcms/20261101T002537Z-e368282f-sheets`
- hillclimb: `artifacts/verification/rcms/20261101T002555Z-5c579446-hillclimb`

Final uninterrupted command: `uv run --no-sync python -m pytest tests/e2e -n 2 -q -k "calculator or wizard or import or csv or ux or audit or review"`. Result: **51 passed in 1630.99s (27m10s), exit 0**. Transcript: [SLICE8A-pytest.txt](SLICE8A-pytest.txt). Each test retains its own evidence manifest under artifacts/verification/rcms. Earlier interrupted and failed evidence remains intact.

Screens refreshed: import, metric, binary/continuous/diagnostic calculators, light/dark effect grid, and light/dark welcome/data-type/outcome/CSV pages. Scope: Qt offscreen, not native display qualification. Existing baseline accepted-row fixtures and numerical assertions passed unchanged. No numerical algorithms changed. All four numbered steps are complete.

## Grid capture correction

The blank Include/Study Name columns were a capture artifact introduced by
`f221b3d32ef45f6c5c6c06857810af846f300577` (forced rightmost horizontal scroll),
not the neutral-tint model change. Reproduced with HEAD's real Qt/R capture in
both palettes. The new visibility assertion failed at that capture state:
row 1's name rectangle started at x=-73, outside the viewport. Capture now uses
a 1200-pixel window, leftmost scroll and explicit viewport/header repaint.
Both refreshed palette images show Include, Study Name and Gonzalez correctly.
The sheets/amino drives check the headers, model study label and nonuniform
interior pixels of the first study-name cell; the palette capture checks both.

The calculator width assertion first failed with widths [43, 57, 57, 324].
All four binary metric columns now share the viewport using Qt Stretch sections.
No numerical computation or stored precision changed.

Verification evidence (`artifacts/verification/rcms/`, retained manifests include
commands, runtime, assertions and screenshots):

- Original capture reproduction: `20261101T005620Z-ecd4c766-xlsx-import`.
- Capture visibility failure: `20261101T005633Z-f5eac31e-xlsx-import`.
- Calculator width failure: `20261101T005652Z-ce75a211-calculator-binary`.
- Corrected light/dark capture: `20261101T005703Z-40de6e47-xlsx-import`.
- Requested ordered drives: `20261101T005726Z-1d255bb5-sheets`,
  `20261101T005744Z-241d10ed-amino`,
  `20261101T005802Z-9d7d3c7f-calculator-binary`,
  `20261101T005817Z-a9522284-hillclimb` (all passed).

Commands use `source build/sheets-baseline/ENV.sh`, then
`uv run --no-sync python scripts/verify_rcms.py SCENARIO`.
This is real Qt offscreen/R evidence, not native window-manager qualification.

The uninterrupted sheets → amino → calculator-binary → hillclimb sequence and
`uv run --no-sync python -m pytest tests/e2e -n 2 -q -k "sheets or grid or editing or calculator"`
passed: **24 tests in 373.23 seconds**. Selection evidence index:
`artifacts/verification/rcms/slice8a-grid-correction-pytest.json`.
