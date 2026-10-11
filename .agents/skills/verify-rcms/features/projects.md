# Projects, editing, and CSV import

Users open an `.rcms` project, edit studies, undo or redo changes, save/reopen the project, and import study data from CSV.

## Sub-features

- `project-edit`: Unicode study rename, Return advances, dirty state, undo/redo.
- `project-persist`: Save As and reopen preserve edited values.
- `project-reject`: corrupt open preserves the active project and save destination.
- `csv-import`: quoted names, numeric/factor covariates and raw counts reach analysis and persist.

## How to get to it (user POV)

- File > Open, toolbar Open, Ctrl+O (Cmd+O on macOS), File > Open Recent, or opening a project at startup.
- Edit a study cell in the main table; Edit > Undo/Redo.
- File > Save/Save As, toolbar Save, Ctrl+S (Cmd+S on macOS).
- File > Import CSV or the import toolbar action; Dataset > New Dataset starts the creation wizard.

## Driving it with Qt E2E

Preconditions: doctor passes; `sample_projects/amino.rcms` is readable; no user project is involved.

- **Edit and persist.** Run `uv run python scripts/verify_rcms.py editing`. The driver opens the sample through the application's open path, edits the NAME column with a QLineEdit, sends Return, and triggers `action_undo`/`action_redo`. Save As uses an isolated file-picker destination. `workflow/edited.rcms` reopens with `München – edited`; `edit-reopened` captures the table and preserved save path after a corrupt open fails. The reopened data still analyze through real R.
- **Import and persist.** Run `uv run python scripts/verify_rcms.py csv`. The wizard's `select_file_btn` loads a generated CSV. `csv-preview` shows three rows. The reopened `workflow/imported.rcms` contains `Alpha, München`, numeric Dose `7.0` and factor Region `South`; analysis displays the imported study weights.
- **Entry reachability.** These scenarios call the open path directly and start CSV on its import page. For a menu, toolbar, shortcut, recent-file, startup, or earlier wizard-page change, add a targeted drive from that entry point. Main-window handles are `action_open`, `action_save_as`, `action_save`, `action_import_csv`, and `action_new_dataset`.

## Gotchas

- Native file pickers are substituted; their platform behavior remains unverified.
- The deliberate corrupt-open box is observed through the error boundary; other unexpected dialogs fail the workflow.
- A visible edit or an archive's existence is insufficient: reopen and observe its content and clean dirty state.
- Project corruption/resource limits and interrupted atomic saves belong to the retained failure tests as well as ordinary persistence proof.
