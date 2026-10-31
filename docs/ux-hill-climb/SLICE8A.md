# Slice 8A — partial implementation

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
