# Projects, editing, and CSV import

Users open an `.rcms` project, edit studies, undo or redo changes, save/reopen the project, and import study data from CSV.

## Advanced transaction proof

- `project-structure` uses the same sheet-tab transaction drive as `sheets`: add, rename, delete, undo/redo, arm swap and persistence. The obsolete structure editor is removed.
- `project-table-covariates` creates numeric Dose and factor Region through their dialogs, pastes/copies a 19×2 clipboard rectangle, undoes/redoes once, sorts through the actual name-header context menu, and saves/reopens. Compare study identity, inclusion and attached covariates before/after. Sorting changes display order, not canonical dataset identity. Run the reopened Dose regression and Region subgroup with independent numerical fits. It also converts/edits a covariate type, renames/deletes/undoes it, reopens the saved result and checks the other sheet remains unchanged.
- `project-shell` opens through the real Open action with a test-owned picker path, edits a name, cancels a dirty-open prompt, saves through Save As, opens the recent-file action, and reads the actual About/Legal dialog. The accepted name and clean state must survive.

These add to `editing`, `csv`, and the eight original New Dataset workflows plus the HR/IRR metric variants. They do not establish structural deletion, every navigation state, all dirty-close responses, shortcuts, native picker interaction, earlier import pages, or Excel import. Use the targeted recipes below when those paths change.

## Sub-features

- `project-edit`: Unicode study rename, Return advances, dirty state, undo/redo.
- `project-persist`: Save As and reopen preserve edited values.
- `project-reject`: corrupt open preserves the active project and save destination.
- `csv-import`: UTF-8 BOM headers, quoted Unicode names, numeric/factor covariates and raw counts reach analysis and persist. Windows must retain names even when Python UTF-8 mode is disabled.
- `dataset-create`: all eight original New Dataset paths and the two HR/IRR variants reach default analysis and save/reopen; see the analysis dataset matrix.

## How to get to it (user POV)

- File > Open, toolbar Open, Ctrl+O (Cmd+O on macOS), File > Open Recent, or opening a project at startup.
- Edit a study cell in the main table; Edit > Undo/Redo.
- File > Save/Save As, toolbar Save, Ctrl+S (Cmd+S on macOS).
- File > Import CSV or the import toolbar action; Dataset > New Dataset starts the creation wizard.

## Driving it with Qt E2E

Preconditions: doctor passes; `sample_projects/amino.rcms` is readable; no user project is involved.

- **Edit and persist.** Run `uv run python scripts/verify_rcms.py editing`. The driver opens the sample through the application's open path, edits the NAME column with a QLineEdit, sends Return, and triggers `action_undo`/`action_redo`. Save As uses an isolated file-picker destination. `workflow/edited.rcms` reopens with `München – edited`; `edit-reopened` captures the table and preserved save path after a corrupt open fails. The reopened data still analyze through real R.
- **Import and persist.** Run `uv run python scripts/verify_rcms.py csv`. The wizard's `select_file_btn` loads a generated CSV. `csv-preview` shows three rows. The reopened `workflow/imported.rcms` contains `Alpha, München`, numeric Dose `7.0` and factor Region `South`; analysis displays the imported study weights.
- **Entry reachability.** Editing/CSV call the open path directly and start CSV on its import page. New Dataset scenarios start at `action_new_dataset` and traverse real pages. For open menu/toolbar/shortcut/recent/startup or earlier CSV-page changes, add the exact entry drive. Handles: `action_open`, `action_save_as`, `action_save`, `action_import_csv`, `action_new_dataset`.
- `ux-improvements` adds a rejected header, deliberate unique-column mapping, duplicate mapping rejection, cleared-required-field rejection with both custom and exact headers, recovery without stale preview/payload, CSV-template headers, original raw counts/covariates after reopening, and inline duplicate covariate recovery. The CSV page keeps file selection when its picker is cancelled; errors disable completion and retain the file. Mapping and preview have separate tabs. Earlier import pages and native picker operation still need their own entry proof.

## Gotchas

- Main-window startup maximizes even after saved normal or full-screen placement. `project-shell` exercises both cases and restores the remembered normal size. Use isolated settings.

- Native file pickers are substituted; their platform behavior remains unverified.
- The deliberate corrupt-open box is observed through the error boundary; other unexpected dialogs fail the workflow.
- A visible edit or an archive's existence is insufficient: reopen and observe its content and clean dirty state.
- Project corruption/resource limits and interrupted atomic saves belong to the retained failure tests as well as ordinary persistence proof.

## Structure, table and shell recipes

These are source-backed targeted recipes, not claims that the ordinary editing scenario exercised them. Owners: `main_window.py`, `main_wizard.py`, `dataset_table_view.py`, `edit_dialog.py`.

- **Dataset creation:** `action_new_dataset` opens `MainWizard`; click a type button on `Page_DataType`, Next, choose `metric_cbo_box` by item data, Next, enter `outcome_name_LineEdit`, Finish. Eight automated cases are in analysis.md. Test Back/Cancel and invalid names when changing wizard flow. Empty and one-study states need explicit analysis availability/results checks.
- **Import:** `action_import_csv` starts the data-type/metric/name/import sequence. On the import page use `select_file_btn`, `from_excel_chkbx`, `has_headers_chkbx`, `delimter_le` (actual spelling), `quotechar_le`, and `preview_table`. Malformed/schema-invalid input must leave completion disabled; corrected input must recover. Require correct raw columns and covariate types after reopening, not only preview rows.
- **Structure:** `action_edit` opens `EditDialog`: `outcome_list`, `follow_up_list`, `group_list`, `study_list`, `covariate_list` with corresponding add/remove buttons. Add/rename/remove items, cancel a second draft, accept, undo/redo, and reopen. Assert retained study identity/data across multiple outcomes/follow-ups/groups. Deletion must be confirmed and undoable where supported.
- **Navigation:** `nav_up_btn`/`nav_down_btn` choose dimension, `nav_right_btn`/`nav_left_btn` choose item, `nav_add_btn` adds one. Add dialogs use `outcome_name_le`, `datatype_cbo_box`, `group_name_le`, `follow_up_name_le`. Bounds disable the appropriate controls; switching back must restore the original data and metric.
- **Covariates:** `action_add_covariate` opens `AddCovariateDialog.covariate_name_le`/`datatype_cbo_box`. Header context choices rename/delete or create a factor/continuous copy. Compare values, types and identity, undo/redo and reopen. Use the covariate in subgroup/regression to prove it crosses the analysis boundary.
- **Table:** inclusion checkbox, header Include All/Exclude All, row deletion confirmation, sorting, rectangular copy/paste and clear. Trigger `action_copy`/`action_paste`; assert clipboard/live values, trailing-row expansion and one undo transaction. Invalid bulk data must roll back the whole operation. Sorting must retain values, covariates and inclusion attached to study IDs, not row positions. Auto-fit must not alter data.
- **Confidence:** `action_change_confidence_level` → `ConfidenceLevelDialog.confidence_level_spinbox` → `button_box` OK. Check `cl_label`, actual analysis intervals, undo/redo, save/reopen and inherited parameters.
- **Dirty actions:** Open/New/Import/Close/Quit on an unsaved project: Cancel preserves live project and destination; No proceeds; Yes proceeds only after successful save. Cancelled/failed Save As must preserve the unsaved project. Use test-owned files and record the actual prompt/action/recovered state.
- **Entry and shell:** drive Open/Save actions with only picker paths substituted, their standard shortcuts, `action_open_recent_2.actions()` and QAction `.data()`, and the main start page `start_page.create_button` / `import_button` / `open_button` / recent-project buttons. Open `action_about_legal`, read tabs/links, close it, and confirm application still responds. Restore isolated settings/geometry; never use the user's preferences as fixtures.


## CSV entry and grid guidance

`ux-improvements` requires instructions and the picker visible at initial CSV
entry and re-entry after scrolling. Entry focuses the picker and resets the owned
scroll timer; the GUI teardown case closes a wizard before that timer fires.
Required mapping fields precede optional fields. The grid explains inclusion and
derived cells locally; automatic study-name sizing gets spare width while user
widths remain respected. Delete study is separated from Copy/Paste and names the
confirmed study. Covariate prerequisites are visible in the structure dialog.

## HR and IRR

See [ratios.md](ratios.md) for the compact input, original-source persistence, analysis, plot and small-study workflows. Run `ratios-hr` and `ratios-irr` after changes affecting these families; these exercise actual menu deletion before/after sorting and identity-safe undo/redo/reopen. `ratios-samples` checks the bundled 65-study Pignon HR and nine-study Niel-Weise IRR projects, original source values, independent fits, and identical save/reopen content; the broader shared-change lane remains required.

## Main start page and navigation

`review1-design --native` exercises startup without a welcome modal, present and
missing recent paths (including wrapping full paths), Create/CSV wizard Cancel,
Open picker Cancel, recent-project opening, and outcome/follow-up/group selector
switching. The table is hidden until an outcome exists. Light and dark native
palette captures are retained. `project-shell`, `project-structure`, `csv` and the
data-type matrix supply successful creation/import/save/reopen/undo behavior.
File pickers remain substituted; native OS picker operation is not claimed.

## Outcome and arm naming

`audit-round3-arm-names` creates default and custom comparative binary/continuous, single-arm mean and diagnostic datasets through the real wizard. It checks trimming, inline duplicate rejection, actual model group identity/order, grid/calculator labels, three comparative figure styles, report/copy/export, canonical CSV template/mapping/preview and silent legacy aliases, save/reopen, and preservation of an old project's stored tx A/tx B names. Native round-five evidence also runs this at Qt scale 2; OS scaling and screen readers remain unqualified.

Round-five review follow-up: the shipped examples use readable arm names, while
`audit-round3-arm-names` creates an explicitly legacy input from immutable test
snapshots and proves it reopens without relabelling. The same drive checks integer
count display in the real CSV preview and sentence-case binary calculator headers.
`review1-design` exercises the single-row recent list with middle-elided paths,
full accessible names/tooltips, missing state, Locate/Remove and reopening a sample.

`project-display-labels` recursively inspects attached menus for all ten families,
opens actual calculators and records contextual action popups. The shared desktop
recorder also rejects internal built-in vocabulary in visible labels, tooltips,
combo choices and report widgets for every captured dialog in the complete matrix.
Investigator group names are preserved. `project-shell` waits for stable real
window-manager state before placement assertions and measures active normal-text
palette contrast. `review1-design` additionally measures derived/selected grid
contrast and keyboard traversal; native 1.5×/2× drives cover this host's scaling.
These checks do not qualify assistive-technology behavior or every inactive/error
colour on other operating systems.

Sheet acceptance drives: `sheets-legacy` checks original 322ede26 archives against the retained pre-migration numerical fixture and input hashes; `sheets-edges` checks invalid names, deletion prompts, last-sheet retention and transactions; `sheets-swap` checks binary/continuous/HR/IRR pooled inversion, headers, counts, restoration, SVG arm labels and diagnostic gating; `sheets-persist` checks clipboard independence, local covariates and three-sheet reopen. Every desktop startup probes pre-ready R rejection. Clinical favours direction labels are user-defined, not inferred from arm names; automatic favours-label migration remains unexercised.

## RevMan import

`rm5-import` exercises the File action and welcome wizard import button through
review, default setup and Run on both Fleiss sheets. It compares raw cells with
meta::read.rm5, displayed Aspirin results with RevMan's stored attributes and
SMD with metacr at default precision (the exact-Hedges difference is disclosed).
Derived XML inputs cover pending data, non-integer years, duplicate names and
IV-random/DL, MH-random unavailable and Peto-fixed mapping. Dirty review Cancel
preserves data/path/dirty/history; confirmation invokes the existing save prompt.
Malformed and non-RevMan XML leave the project intact. Save/reopen retains settings.
Native pickers and exhaustive DTA structures remain unexercised.

RM5 derived-fixture extension: real subgroup dialog compares six grouped studies
and fixed-IV subgroup estimates/CIs to metacr; the existing moderator Q/p
difference is explicitly quantified in SLICE5.md. Generic IV HR, OR and MD run
untouched setup, compare held pooled values/I² at 1e-6, and save/reopen. OR/MD
entered-only capability is exercised first. Review excludes free-text effects
and IPD O-E/variance. This does not qualify other RM5 structures or native pickers.

DTA RM5 extension: Bristol's real workshop review verifies TESTS/TEST/
TEST_DATA/TEST_DATA_ENTRY. A labelled synthetic fixture using that structure
covers two index tests, independent stdlib count parsing in TP/FN/FP/TN order,
review table, default diagnostic analysis and full save/reopen equality.
Original-review redistribution and exhaustive DTA structures remain unqualified.
Fixed-effect subgroup imports disclose the existing random moderator test in
Differs from RevMan; subgroup estimates and the held discrepancy remain unchanged.

`sheets-swap` verifies binary OR/RD and continuous MD before, after, and after
swapping back, against direct metafor DL at 1e-6 (estimate, CI and p). Favours
parameters must follow the arm order. Existing HR/IRR swap coverage remains.

## XLSX import

`xlsx-import` drives the shared mapping/preview page: visible worksheet selection, CSV payload and analysis-text equivalence, precision/date disclosure, hidden rows, formula caches and missing caches, error cells, merges, corrupt/old formats, and save/reopen. Native picker gestures, packaged execution and exhaustive mapping combinations remain unverified.

### Slice 7 import evidence

`xlsx-import` now exercises toolbar picker cancellation and immediate loaded-page
entry, multi-sheet selection, hidden rows/columns, protected/corrupt/formula/merged
workbook rejection, one-step import undo/redo and normalized project equality with
CSV. It asserts Preview first, the Import data title, hidden CSV options for XLSX
and no page vertical scrollbar at the default size. It captures each data-type
and metric page in light/dark palettes and checks uniform icon presence at each
level. `csv` opens the initially collapsed CSV options and retains its Unicode,
covariate, analysis and reopen assertions. Welcome-page picker entry and native
OS file-picker operation remain unexercised by these automated scenarios.

Slice 8A: effect cells use a translucent neutral tint, normal font and inherited
theme text. The xlsx-import drive captures the amino effect grid with light and
dark palettes; review1-design checks composited text contrast and exercises the
start-page import action with a controlled file-picker result.

- **Study identity rendering.** `sheets` and `amino` assert Include/Study Name
  header text, first-row label equality with the study model, a fully visible
  name-cell rectangle and nonuniform interior viewport pixels. `xlsx-import`
  repeats this rendering proof in light/dark palettes before grid capture.

The `sheets` drive also proves inline rename and Escape/invalid-name recovery, adjacent add-button geometry, context Move left with undo, and full active-tab visibility across 20 long-named sheets. It captures the flat strip in light/dark palettes and overflow. A shared horizontal scrollbar in the strip follows the grid range and hides when the grid fits. The drive captures amino at 1024×700 with an expanded study-name column, drags the strip thumb in both directions, checks grid-to-strip scrolling, and asserts hidden-on-fit at 1600×828. The tab separators, content background and add button follow the light/dark palette.

The overflow proof also narrows the window during inline rename and checks both tab/editor visibility and alignment. Arrow visibility is deferred out of the scroll-area range signal to avoid re-entering the active layout.


`ui-crawl` deliberately captures each named surface once, in sections E, F, G, B, C, then retained shell section A. It uses selected real analysis drivers with their assertions intact for the specialized plots. Its index lists omissions and the scenario intentionally fails while D, H, I and J await the next run. This is a visual inventory, not full parameter or native-platform qualification.
