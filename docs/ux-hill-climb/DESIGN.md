# Sheet ownership design

Design baseline: 176c88b5. Documentation only. Implements ranks 1–3 and 17 of PLAN.md in a later phase; does not change statistical authority. This supersedes ADR-0009's v1-writing decision, preserving stable identities. User clarification: the sheet format is **v3**. Existing v2 already carries HR/IRR; never reuse its version number. Both v1 and v2 remain readable.

## Current dependency trace

All paths below are under src/rc_metastudio unless stated otherwise. Names here describe existing code, including its historical use of “group” for arm.

| Owner | Pair/arm dependency and callers to migrate |
| --- | --- |
| project_domain.py | OutcomeSnapshot.follow_ups, UnitSnapshot.outcome/follow_up/groups, StudySnapshot.units; semantic validation accumulates available_groups by pair, rejects duplicate units, validates comparison strings and ratio_inputs.groups, and validates active outcome/follow-up/groups. Replace pair validation with sheet/row/arm-reference validation. |
| analysis_dataset.py | Dataset owns global studies, outcomes_by_id and follow_ups_by_outcome_id; label/ordinal views remain. Structure edits traverse all studies; group enumeration and sort comparators accept outcome/follow-up/groups. Study.analysis_units_by_outcome is a nested label view; get/add/replace/remove analysis unit resolves the pair. Outcome and FollowUp hold identities. Eliminate this nesting and global row ownership. |
| analysis_unit.py | AnalysisUnit owns groups_by_id plus groups label view; raw data, entered/calculated/display effect stores and ratio inputs depend on ordered arm comparisons. add/remove/rename_group rebuild comparison keys. Keep source precedence and numerical routines; use ordered ArmId references rather than hyphen-joined names. |
| analysis_adapter.py | AnalysisService prepares datasets through the table/model and R bridge; covariate selection reads dataset.get_covariate_values and get_studies. Requests carry family, workflow, method, metric and parameters, not explicit pair keys. Feed current-sheet rows and settings; bind result identity to executed sheet, never live selection. |
| project_adapter.py | runtime_project_to_document, _runtime_selection/_runtime_follow_up, ProjectStateModel serialize current_outcome_name/current_follow_up_index/current_groups. Dataset/unit serialization and reconstruction translate pair labels, arm comparisons, entered effects and ratio inputs. Replace with direct sheet records; no legacy runtime reconstruction for converted files. |
| dataset_table_model.py | Current outcome, follow-up ordinal, groups, previous_groups and arm indices select canonical units. Header/data/flags, raw and estimate reads, eligibility, sort, state snapshots/restoration, confidence recalculation and edits all consume this selection. Current-unit lookup must become current_sheet.rows[row]. |
| dataset_table_view.py | Header rename uses current_groups; row calculators consume current unit, group comparison and metric. Paste clones the model and commits a transaction; copy/clear and sorting depend on table columns. Preserve transaction behavior while binding each operation to sheet ID. Qt palette ColorGroup is unrelated. |
| workspace_editing.py | WorkspaceEditingContext contains outcome_name/follow_up_name/current_groups/group_comparison; WorkspaceViewState repeats selection. _analysis_unit and raw/edit/recalculate/inclusion paths resolve the pair. Replace context identity with sheet ID and row ID; keep validation and confidence distinction. |
| main_window.py + forms/main_window.ui | _setup_connections wires Navigate, dimension controls, Previous/Next/Add and display labels. add_new dispatches by dimension; next/previous/update_dimension/display_outcome/display_follow_up/display_groups mutate separate selection parts. model_updated, set_model and failed-open restoration resynchronize them. edit_dataset opens the five-list structure editor; metric menus, Run, subgroup, regression, cumulative, leave-one-out and publication-bias actions consume selected model data. Replace navigation with tabs and one selection operation. |

Additional boundary callers: edit_dialog.py and add dialog forms construct old dimensions; main_wizard.py and CSV import create the initial outcome/unit; workspace snapshots/undo restore the old model; r_bridge and dataset_analysis_domain consume model-selected rows/comparisons; calculator dialogs consume AnalysisUnit; project_format.py owns archive validation/migration/atomic save. These must move together with their callers, not remain as parallel runtime graphs. Before implementation, repeat `rg -n 'follow_up|analysis_units_by_outcome|current_groups|group_comparison|follow_ups_by_outcome' src/rc_metastudio` and classify remaining hits as legacy converter, subgroup, or missed caller.

## Small interface and ownership

In analysis_dataset.py retain Dataset as the project container: title, notes and ordered `sheets: list[Sheet]`. Define SheetId, RowId and ArmId in project_domain.py alongside wire validation. Sheet in analysis_dataset.py owns id, name, family/subtype, ordered arm declarations, ordered StudyRow records, covariate declarations, selected comparison and analysis settings. StudyRow owns id, label, year, sample size, inclusion/manual exclusion, covariate values and one AnalysisUnit. It has no outcome/follow-up map. The same trial on two sheets has independent row IDs and mutable values. Copy covariate declarations and values into each converted sheet; future editing is local.

Rename Group to Arm in analysis_unit.py. Retain all legacy arms and their data, including inactive comparisons. Sheet settings store the active ordered arm IDs; a small arm-pair control in analysis setup handles multi-arm projects without restoring Groups navigation. Noncomparative/diagnostic sheets disable Swap. Swap reverses the active ordered pair atomically, with existing direction rules and no count mutation; twice restores the original state. Preserve all entered comparisons, source confidence and original ratio inputs. Derived preview caches are rebuilt, never serialized as authority.

WorkspaceViewState in workspace_editing.py holds only `current_sheet_id: SheetId | None` as content selection. Confidence and method/metric/plot settings belong to each sheet; copy the effective legacy global settings to every sheet. Qt cell selection remains transient. Dataset supplies `sheet(id)`; table model supplies `set_current_sheet(id)` with one reset and `current_sheet`. Use existing undo commands for add/rename/remove/swap and edits; commands capture sheet/row IDs, not whichever tab is active at undo time. No generic navigation service or second dataset facade.

## Deletion list

These are 12 deletion targets (families of code, not a claim of 12 symbols):

1. Navigate menu and dimension selector wiring in main_window/forms.
2. Previous/Next navigation buttons/actions and next/previous dispatch.
3. Generic navigation Add dispatch; replace with Add Sheet.
4. Outcome selector/label and display_outcome synchronization.
5. Follow-up selector/label and display_follow_up/update_follow_up_label.
6. Groups selector and display_groups/navigation availability.
7. update_dimension/_update_navigation_controls/_navigation_availability branches.
8. Follow-up add/undo dialogs and main-window helpers.
9. Group add/undo navigation dialogs/helpers; retain arm rename through headers.
10. Table-model follow-up getters/setters, round-robin group indices and next_groups helpers.
11. Dataset/Study follow-up indexes and nested pair views, plus old snapshot selection fields.
12. EditDialog outcome/follow-up/group lists and their structure mutations; replace with sheet/arm editing and migrate wizard/import/calculator callers.

Delete the four-line grid identity block with these controls. Tab gives outcome, headers give arm labels, setup gives metric. Keep subgroup covariates and analysis actions.

## Interface sketches

A: `[Mortality] [Pain — 6 months] [+]` above the grid; tab context menu Rename/Delete; keyboard tab cycling; overflow menu lists full names. Headers show Arm labels. Analysis menu retains advanced workflows; Dataset contains Swap arms.

B: a left list of sheets with Add/Rename buttons, selected sheet above the same grid. It handles many long names visibly but consumes horizontal space and introduces a second navigation panel.

Choose A. It uses one selection and keeps spreadsheet width; scrollable tabs plus an overflow list handle long names without adding another permanent panel. Borrow Anki's explicit primary actions and keyboard focus behavior, with native Qt tabs rather than copying its interface.

## Versioned file seam

Keep the authenticated ZIP container: manifest.json with format_version **3**, member byte counts and SHA-256; project.json with schema_version 3, title, notes and ordered sheets; state.json with schema_version 3 and current_sheet_id. Each sheet declares IDs, name, family/subtype, arms, covariates, settings and rows. Each row stores identity/metadata/inclusion, covariate values, raw data keyed by ArmId and entered effects/ratio inputs keyed by ordered ArmIds and metric. Missing values retain their explicit representation; numbers are never passed through display formatting. Settings include metric, confidence, estimator/inference, effect-source selection and existing plot/method parameters; absent historical settings retain the same existing defaults.

Illustrative project fragment (other required metadata omitted):

```json
{"schema_version":3,"title":"Review","sheets":[
  {"id":"s1","name":"Mortality","family":"binary","subtype":"proportions",
   "arms":[{"id":"a1","name":"Treatment"},{"id":"a2","name":"Control"}],
   "settings":{"metric":"RR","confidence_level":95,"arms":["a1","a2"]},
   "covariates":[],"rows":[{"id":"r1","name":"Trial A","include":true,
    "manually_excluded":false,"covariates":{},
    "raw_data":{"a1":[3,100],"a2":[8,101]},"entered_effects":[],"ratio_inputs":[]}]}
]}
```

Implement explicit `convert_v1_to_sheet_project` and `convert_v2_to_sheet_project` at project_format.py's read seam, sharing only the actual pair conversion function. Authenticate and validate source schema/semantics first, convert once to v3, validate v3, then construct the sole runtime graph in project_adapter.py. Existing v1→v2 HR/IRR migration must remain readable but must not create a second live model. Retain original source version/path and hash in the open-document receipt. Save on a converted document invokes Save As; reject the original source path, including resolved aliases, until a distinct destination succeeds. Cancellation/failure preserves source bytes and dirty state. Reuse atomic temporary-file/replace/durability handling.

Walk declared outcomes in their existing order, then declared follow-ups in ordinal order; no Cartesian product across different outcomes. A no-follow-up outcome has its explicit null pair. One declared follow-up: outcome name only. Multiple: `Outcome — follow-up label`; retain raw values regardless of labels. Deterministically suffix collisions ` (2)`, ` (3)` in encounter order, checking against already allocated names; blank outcome becomes `Untitled`, blank follow-up becomes `Unnamed`. Report every assigned name and source pair in conversion receipt. New manual rename rejects blank/duplicate names.

Every pair gets one sheet, including an empty declared pair. Copy each study's actual unit into that sheet; where a declared pair has no unit, preserve its row metadata/inclusion/covariates with empty data and report missing data. Never manufacture measurements. Reject duplicate or undeclared pairs, invalid references, conflicting arm identities or an unrepresentable structure before installing the document. Retain source and show exact location/reason. Extra arms are retained; inconsistent active selection gets an explicit warning and first valid comparison, not discarded arms. Map valid current pair to sheet ID; stale pair selects first sheet with a warning, empty project selects null. Source labels appear in receipt only, never as follow-up UI fields.

## Working migration increments

1. Capture every bundled source hash, pair inventory, settings and numerical contracts; write failing real-driver acceptance paths below before implementation. Existing app remains unchanged.
2. Introduce v3 validation and explicit converters at the file seam with round-trip artifacts; existing runtime adapter temporarily projects v3 back into its existing graph internally. Do not enable new writer until every field round-trips; this temporary adapter is removed in step 3.
3. Replace Dataset/Study ownership, unit lookup, editing context, analysis and persistence adapters together; expose sheet selection using existing outcome control temporarily (one choice per sheet). Enable v3 writer and Save As protection; remove temporary projection and pair runtime graph in the same increment. Run full profile.
4. Replace temporary control with tabs; remove the 12 deletion families and stale forms/callers. Add sheet-local arm rename/swap and multi-arm setup selection. Verify native keyboard/overflow and undo.
5. Convert bundled samples through production reader/Save As, retain original evidence, reopen/reanalyze all; update feature map and format docs. Full profile plus targeted native drives before acceptance.

## Acceptance cases defined before implementation

For every run retain input hashes, exact command/environment, conversion receipt, live action/result snapshots, saved/reopened archives and field-by-field/numerical diffs. Use real Qt/R; do not bless refreshed numerical oracles.

| Failure to prevent | End-to-end assertion / scenario to extend |
| --- | --- |
| Pair omitted or duplicated | project-structure: multiple outcomes with unequal follow-up counts, empty pair and colliding names; receipt and reopened sheet inventory match each source pair exactly once. |
| Wrong ownership | editing, project-table-covariates: same trial on two sheets; edit/sort/delete/paste one, other sheet unchanged, including covariates/inclusion. |
| Swapped arms | project-structure, ratios-hr/ratios-irr: distinguish counts and labels, one swap direction and two-swap identity; inactive extra-arm data survive. Noncomparative Swap disabled. |
| Rounded values | editing, calculator-mode-* and ratios-samples: long precision raw/entered/source-confidence values survive save/reopen exactly; compare derived results with existing qualified tolerance. |
| Lost covariate/inclusion | csv, project-table-covariates: numeric/factor/missing moderators and manual exclusions copied per sheet, subgroup/regression eligible IDs preserved. |
| Stale selection | project-shell: stale/current/deleted tab IDs, undo removal, failed Open and reopen; selected tab, grid and executed result all identify same sheet. |
| Wrong settings | options-*, analysis-data-*, ratios-hr/irr: differing per-sheet metrics/confidence/method/source settings; switch and reopen, compare actual executed parameters and numerical sections. |
| Broken undo | editing, project-structure: edit/paste/swap/rename/add/delete, switch tab then undo/redo; atomic restoration by IDs and correct dirty state. |
| Save interruption | project-shell plus retained file-boundary failure lane: cancelled picker, write/replace failure and durability uncertainty leave source unchanged and no falsely clean document; retry Save As and reopen. |
| Unsupported legacy structure | project-structure: duplicate/undeclared units, invalid arm references and future version fail before live state changes; supported multi-arm source retains every arm. Conversion receipt explains missing units. |

Shared model change requires `uv run python .agents/skills/verify-rcms/scripts/verify_all.py --full`, plus targeted tab, source-preservation and native picker/keyboard drives. Existing scenarios alone do not prove these new paths.

## RevMan 5.x / RCMS analysis-type parity

Count data representations, not estimators or workflow permutations. RevMan authority: [5.2 User Guide](https://community.cochrane.org/sites/default/files/uploads/inline-files/RevMan_5.2_User_Guide.pdf), Outcome properties p45 and diagnostic sections pp84–91. The URL redirects when opened today; indexed official guide passages establish the five intervention representations and diagnostic counts. RCMS authority: main_wizard.py, meta_globals.py metric lists, project_domain.py family/subtype validation and analysis_adapter.py request families. “Both” means compatible inputs, not identical statistical defaults or diagnostic pooling.

| Representation | Status | RM5 import contract |
| --- | --- | --- |
| Two-arm dichotomous events/totals | In both | Binary sheet; preserve OR/RR/RD selection and available method settings. |
| Two-arm continuous N/mean/SD | In both | Continuous sheet; MD/SMD; preserve arm order. |
| Generic inverse variance estimate/SE | In both | Existing generic-effect/regression-coefficient or matching HR/IRR type; preserve scale, metric and SE. Unknown metric imported with unsupported-analysis report, never relabelled MD. |
| Diagnostic test TP/FP/FN/TN | In both | One sheet per test/data table, independent repeated rows; preserve covariates. Report unsupported RevMan SROC configurations; RCMS Reitsma is not an automatic statistical substitute. |
| O−E and variance | RevMan only | Preserve original O−E, variance, events and totals in import receipt/attached source data; mark analysis unsupported and do not run. Do not infer HR or add an estimator. |
| Other Data free-text table | RevMan only | Preserve cells/headings in imported supplemental data with unsupported-analysis report; no numeric coercion or pooled analysis. |
| One-arm binary proportions (PR/PLN/PLO/PAS/PFT) | RCMS only | No RM5 direct representation. |
| One-arm continuous mean | RCMS only | No RM5 direct representation. |
| Raw incidence events/person-time | RCMS only | Generic entered log IRR is covered above; raw rate pooling is distinct. |

Counts: **4 in both / 2 RevMan only / 3 RCMS only**. HR and entered IRR are generic inverse variance input specializations, not extra rows. AS/YUQ/YUY are RCMS metric extensions, not extra input types. Standard/cumulative/leave-one-out/subgroup/regression/bootstrap/publication-bias workflows are not additional file data types. Import target is every “In both” row, including GIV and diagnostic data. RevMan's descriptive SROC and multiple-test/paired-test analyses require explicit unsupported-method reporting when not reproducible; do not equate shared counts with method parity. Supplemental unsupported data must remain accessible and persist with imported project or its explicit import attachment, never silently disappear.

No blocking design question remains after user authorized v3. Supplemental RM5 storage UI is later importer work; it must satisfy the preservation contract above before that importer ships.
