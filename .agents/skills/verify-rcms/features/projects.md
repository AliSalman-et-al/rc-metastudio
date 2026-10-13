# Projects, editing, and CSV import

Users open an `.rcms` project, edit studies, undo or redo changes, save/reopen the project, and import study data from CSV.

## Advanced transaction proof

- `project-structure` opens the real structure editor, adds a group/follow-up, renames the first group/follow-up/outcome through list delegates, and requires unchanged raw arm order and stable study identity. Cancel a second rename; undo/redo; save/reopen and observe the accepted names/data. Renaming a group must not reorder its analysis arms.
- `project-table-covariates` creates numeric Dose and factor Region through their dialogs, pastes/copies a 19×2 clipboard rectangle, undoes/redoes once, sorts through the actual name-header context menu, and saves/reopens. Compare study identity, inclusion and attached covariates before/after. Sorting changes display order, not canonical dataset identity. Run the reopened Dose regression and Region subgroup with independent numerical fits.
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
- **Entry and shell:** drive Open/Save actions with only picker paths substituted, their standard shortcuts, `action_open_recent_2.actions()` and QAction `.data()`, and startup welcome `create_new_btn`/`import_csv_btn`/`open_btn`/`open_recent_btn`. Open `action_about_legal`, read tabs/links, close it, and confirm application still responds. Restore isolated settings/geometry; never use the user's preferences as fixtures.


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
