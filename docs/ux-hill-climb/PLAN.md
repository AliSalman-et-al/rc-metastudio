# Spreadsheet to manuscript: implementation plan

Planning baseline: `7f1057d6`, 31 October 2026. Phase 1 changes documentation only. No application, test, R, dependency, sample-project or format changes have been made. This is a ranked backlog, not an implementation authorization or a claim that the proposed UI exists.

## Constraints and branch receipt

Fetched origin. Local and origin `ux/audit-improvements` were both `7f1057d6` (ahead 0, behind 0). Checkout initially selected local `ux/hill-climb` at `0ac3a6fd`; `git rev-list --count ux/hill-climb --not ux/audit-improvements` returned 0. `git ls-remote --heads origin ux/hill-climb` returned no branch. Switched to the existing audit branch; no reset, rebase, new branch, deletion or stash operation. Push every documentation commit normally to the audit branch; on failure wait 30 seconds, retry once, then stop.

Preserve statistical authority packages, methods, input precision, eligibility, defaults and numerical results. Advanced analyses remain reachable from the analysis menu. Collapsing parameter controls must never remove capabilities. Summary of Findings must not introduce an automatic certainty-grading method or a new estimator.

CONTEXT.md owns vocabulary. Historical audit screenshots/transcripts and v1 format descriptions intentionally retain the old UI/schema labels: changing these would misdescribe the inspected release. The new sheet model replaces that behavior only in a later implementation phase. In particular, the proposal reopens ADR-0009's v1 persistence choice; its stable-identity principle remains useful. Decide the format version before implementation, rather than silently overriding that ADR.

## Ranked backlog

Order reflects expected reviewer benefit per unit of effort, with prerequisite work promoted first. Effort S/M/L is a planning judgement, not a measured duration. Each row ends in a reviewable completion gate.

| Rank / feedback | Work and benefit | Effort / dependencies | Completion gate for later implementation |
| --- | --- | --- | --- |
| 1 / a | Replace the outcome × follow-up structure with sheets, each owning study rows. One pair becomes one sheet; a single observation time uses the outcome name; multiple times use `Outcome — follow-up label`. Remove the separate follow-up UI and field from newly written `.rcms`. | L; blocks 2–5, imports and final output identity | Convert every bundled sample and compare every converted sheet's analyses with its original pair, preserving raw values, entered estimates, confidence levels, inclusion, order, covariates, arms and settings. Save/reopen and rerun. Record exact equality of existing numerical fields, not just pooled effects. |
| 2 / b | Replace Navigate / Previous / Next / Add and Outcome / Follow-up selectors with sheet tabs. Add and rename from the tabs. | M; 1 | Switch, add, rename, undo/redo, save/reopen; keyboard focus, many tabs, long names and duplicate-name handling; no rows shared or silently lost. |
| 3 / c | Delete Groups navigation. Dataset → Swap intervention and control acts on the current sheet. Rename the intervention/control column concept to arm in UI and touched code; group means subgroup only. | M; 1–2 | Swap twice restores input and result state; one swap changes direction as dictated by existing methods, with correct arm labels and unchanged underlying counts. Atomic undo, cancel and persistence; define noncomparative behavior explicitly. Do not silently discard extra legacy arms. |
| 4 / d | Remove the four-line block above the grid. Tab carries outcome, column headers carry arm names, analysis dialog carries metric. | S; 1–3 | All data types retain enough identity to enter data safely; gain usable rows at ordinary window sizes. |
| 5 / e | Remove redundant outcome/data type/comparison/follow-up block in analysis setup, or retain one sheet/metric line if needed to prevent mistakes. | S; 1–4 | Setup, results and export agree on current sheet and executed metric. No repeated block. |
| 6 / n | Restrict HR/IRR metric icons to the respective data types. | S; independent | Code already assigns metric icons only for HR/IRR in `ChooseMetricPage.initializePage`; verify actual wizard forward/back transitions for binary, continuous, diagnostic, HR and IRR, both themes. Absence on other metrics is an explicit assertion. Fix only if observed behavior fails. |
| 7 / h | Finish spreadsheet entry: Tab/Enter/arrows, type-to-edit, rectangular Excel/Google Sheets paste and fill-down. Existing clipboard parsing already supports matrices and newline normalization; retain working behavior. | M; finalize against 1–3 | Real clipboard blocks from both products, quoted tabs/newlines, blanks, invalid cells, boundary growth, selection and atomic undo. Fill-down preserves column types and precision. No formulas or stored-type changes. |
| 8 / f | Keep manuscript-relevant defaults visible: effect/model, estimator where applicable, confidence and inference. Put advanced controls behind a single keyboard-operable expansion. Header summarizes every non-default setting; remember expansion state. | M; 5 | Expand in one click or keyboard activation; all existing options reachable; restored state works across sessions; summary reflects actual applied settings. Compare identical configurations before/after with exact numerical contracts. |
| 9 / k | One manuscript exporter, PDF and DOCX, replaces `.txt` report export. Include supplied identity, tables, figures and Methods paragraph. Compact Methods and Results panels have copy buttons and use the same text as export. | L; 1, 5, 8; dependency choice | Real Word/LibreOffice inspection of DOCX and formatted table clipboard HTML plus plain-text fallback; paginate long tables, repeat headers, inspect Unicode and missing metadata. Figures use configurable physical column widths (proposed 85 and 180 mm; journal-specific override), readable type and vector PDF where possible. Both formats use the same executed result content, without rerunning statistics or inventing clinical interpretation. |
| 10 / g | Calculator mode parity with RevMan: 2×2 events/non-events/totals; OR/RR/RD and log inputs where mathematically defined; SE, CI, signed Z and P; continuous mean/SD/N from t-test, CI or SE. Clear active fields and copy/update table. | L; 7; mode decision | Inventory existing modes first. Verify outputs and reconstructed inputs against RevMan and applicable `metafor::escalc` public calls; document any formula/convention differences before acceptance. Boundary cases: zeros, unequal N/SD, invalid CI/P/N, sign ambiguity, impossible reconstruction and full precision after save/reopen. Do not add a statistical method to achieve parity. |
| 11 / i | XLSX import: choose worksheet and range/header, map columns, preview typed validation, confirm import in one transaction. Reuse the CSV mapping experience. | M; 1, 7; XLSX dependency | Recommend openpyxl read-only access: focused XLSX support and bounded streaming without a dataframe dependency. Preserve stored types, explicitly reject formula cells initially rather than calculate or trust stale cached values. Dates, merged cells, hidden rows, locale numbers, empty sheets and invalid mappings receive explicit previews/errors; no partial import. No dependency added now. |
| 12 / l | Forest rows expose per-study weight and CI beside study names; study grid previews effects calculated from raw data. Summary of Findings uses existing results plus explicitly entered certainty judgements. | M/L; 7, 9 | Reuse authority results and existing derived previews; distinguish unestimable from missing. Match study identity with repeated names; verify weights, intervals and totals without changing analysis inputs. SoF keeps relative/absolute scales and provenance explicit; defer any unavailable derived statistic rather than invent a method. |
| 13 / j | RM5 import for supported analysis data, with an import summary of every unsupported item. | L; 1, 7, sample inventory below | Import binary counts and continuous mean/SD/N, names, arm labels and inclusion first. Preview sheets and unmapped content; never silently translate methods or flatten unsupported designs. Compare source numbers to imported rows and independently run supported equivalent configurations. |
| 14 / m | Readability and concise copy across launcher, wizard, grid, setup and results. Remove verbose tutorial prose; use short labels and contextual help. Borrow Anki's explicit primary actions, keyboard flow and restrained native layouts. | M; apply during 2–12, final pass afterward | Before/after native captures with ordinary/long content, light/dark, scaling and keyboard-only operation; keep explanations needed for statistical interpretation. See Anki decision below. |
| 15 / o | Inspect bundle inventory and remove development-only payload such as qualification artifacts from packaging inputs. Evaluate Briefcase installation and upgrades separately. | S cleanup / L installer; independent | Compare path/byte inventory before/after; install and run real Qt/R analyses on supported OSs. Do not delete source evidence folders. Recommend retaining current installer this round until an embedded-R/Qt/signing/upgrade/uninstall spike passes. |
| 16 / p | Profile startup, paste, analysis dispatch, results and exports on representative small/large projects before choosing optimizations. | M; independent baseline, repeat after changed paths | Record hardware/OS/runtime/input hashes, exact commands, cold/warm conditions, wall time and peak memory, repeated runs and spread. Set targets after baseline; act on measured bottlenecks only. No speed claims from code reading. |
| 17 / q | Architecture pass scoped to modules touched by a–c; do before their implementation if approved, not as an extra framework. | M planning; feeds 1–3 | Trace project domain → adapter/format → table model → main-window navigation. Propose one sheet-owned row representation and one current-sheet selection; remove obsolete follow-up/group selectors and callers. Apply the deletion test and a small interface with local invariants. Compare two interface sketches on paper; avoid factories, generic navigation engines and parallel legacy/new runtime models. Document required v1 read conversion at the file seam and resulting caller deletions. |

## Migration and numerical proof

Agreed conversion is pair-to-sheet with names as above, retaining the same trial independently on multiple sheets. Do not merge study rows across sheets. Before coding, enumerate every bundled `.rcms` and its pairs; record original hashes, settings and numerical contracts. Name collisions, empty labels, extra arms, missing pair data, project-wide covariates and cross-outcome operations require an explicit policy, not data loss. Recommend deterministic unique display names with retained original labels in the conversion receipt; ask the user to decide beyond the agreed conversion.

Recommend a versioned new writer and an explicit old-file read conversion, leaving the source file untouched until Save As. This is a recommendation, not a decided compatibility commitment. Capture original and converted files, exact commands, runtime identity, per-sheet input mapping and numerical diffs. Compare all available supported analyses and options used by samples, not only default pooling. For expected floating-point platform variation use the existing qualified policy; do not relax tolerances or refresh numerical oracles to pass.

Before implementation write the end-to-end acceptance cases and failure list: pair omitted/duplicated, wrong study ownership, swapped arms, rounded values, lost covariate/inclusion, stale current selection, wrong settings, broken undo, save interruption, unsupported legacy structure. Use real Qt/R through [verify-rcms](../../.agents/skills/verify-rcms/SKILL.md); retain inputs, exact command, actions/results, numerical comparisons and decoded exports. The shared model change requires its full profile and targeted new-sheet native drives. Existing green coverage does not prove a new path.

## Five-task baseline

These are **counted from code/UI**, never measured. Count one click per activation, one keystroke/chord per command, and dialogs opened separately (dialogs are not added again to interaction totals). Typed text is reported explicitly; do not call a text entry one physical keystroke. Use the same fixed input and starting state in subsequent native measurement. Dialog counts exclude the results window and count the wizard once despite multiple pages. Error prompts and optional settings are outside the successful default path. Do not compare these partial counts as complete task timings.

Source anchors: `main_wizard.py` (`WelcomePage`, `DataTypePage.nextId`, `ChooseMetricPage`, `OutcomeNamePage`), `main_window.py` (`go`, `meta_subgroup_get_cov`, `meta_reg`, `publication_bias`), `dataset_table_view.py` (`paste_from_clipboard`), `diagnostic_metrics_dialog.py` (`ok`), `analysis_setup_dialog.py`, `results_window.py` (text-report save picker). RevMan reference is desktop 5.x, matching the supplied 5.4.1 screenshots; current web RevMan has a different flow. The [5.2 user guide](https://community.cochrane.org/sites/default/files/uploads/inline-files/RevMan_5.2_User_Guide.pdf) and [current calculator documentation](https://documentation.cochrane.org/revman-kb/calculator-95420946.html) establish concepts, not a measured 5.4.1 click trace.

| Task | Current RCMS count (counted from code/UI) | RevMan count (counted from code/UI; incomplete where stated) |
| --- | --- | --- |
| T1 spreadsheet → new project → basic pooled analysis | 9 clicks + 1 paste chord + 9 character keystrokes; 2 dialogs, under assumptions below | Full count undetermined: supplied UI shows outcome tabs/data grid, but not project creation or clipboard path. No measured count. |
| T2 subgroup plus meta-regression | From complete categorical covariate: subgroup menu route 4 clicks/2 dialogs; regression menu route at least 4 clicks/1 dialog; total at least 8 clicks/3 dialogs. Adding/filling covariates uncounted, so complete task count undetermined. | Subgroups shown in supplied tree; complete creation sequence undetermined. Native meta-regression workflow not established; no count assigned or external-tool steps invented. |
| T3 publication-bias analysis | Menu route 3 clicks/1 dialog for default eligible configuration | Full count undetermined: funnel/asymmetry configuration path and eligibility not present in supplied screenshots. |
| T4 diagnostic analysis | From populated diagnostic sheet: Run toolbar + metrics OK + setup OK = 3 clicks/2 dialogs | Full count undetermined: diagnostic configuration not shown; do not substitute intervention-analysis steps. |
| T5 manuscript PDF and DOCX | Unsupported complete task; no finite completion count. Text report and plot PDF are separate exports, not manuscript export. | Full combined-output count undetermined; no end-to-end PDF/DOCX workflow established. |

Concrete task scripts:

1. **T1:** Start at the welcome wizard with a clipboard containing study name and binary raw-data columns (headerless; at least two valid studies). Click New dataset; select two-arm binary; Next; keep default OR; Next; click outcome name and type `Mortality`; Finish; click first destination data cell; paste with Ctrl+V; click Run toolbar; accept defaults with OK. Count: **9 clicks + 1 chord + 9 character keystrokes** (New, type, Next, Next, name field, Finish, cell, Run, OK), 2 dialogs. Starting from an already opened wizard excludes Ctrl+N. Verify column ordering against the fixture before measuring; grid focus or automatic row growth failures invalidate this successful-path count. RevMan script to measure: create review, add comparison/outcome, select binary metric, enter/paste same rows, inspect pooled analysis; unresolved setup/paste gestures prevent a numeric total.
2. **T2:** Continue with T1 data. Dataset → Add covariate; name/type Category, enter one value per row; repeat for Numeric if a separate moderator is desired. Analysis → Subgroup; choose the already selected complete categorical covariate, OK; accept analysis setup. Analysis → Meta-regression; select the categorical moderator (one click assumed); accept. The counted 8-click lower bound excludes all covariate creation/data entry and results-window closure/navigation, whose focus state was not driven. RevMan: create subgroup categories and allocate the same rows; then attempt the requested regression via documented available capability. Record unavailable capability separately, not a fictitious low step count.
3. **T3:** With an eligible populated binary sheet, open Analysis menu; Small-study effects; accept default run. Three clicks, one dialog. Inspect recommended test, exclusions, uncertainty and funnel. RevMan: open the same outcome, locate funnel and available asymmetry actions; count the real trace before comparison.
4. **T4:** Use a saved fixture with study names and TP/FP/FN/TN, all included. Run; keep default joint sensitivity/specificity selection; OK; accept analysis setup. Three clicks, two dialogs. Diagnostic project creation and data entry are explicitly outside this baseline. RevMan: use the same supported diagnostic inputs/model if available, document differences rather than treating different methods as equivalent.
5. **T5:** Start from completed T1 results. Current RCMS Export report opens a `.txt` save picker; a selected plot can export PDF. Neither completes the task. Future script: choose manuscript export, PDF, destination/save; repeat DOCX; open both and check identity, Methods/Results, tables and figures. RevMan: locate whole-review export/print and DOCX support, retain real output and count only after a successful same-scope run.

No native run occurred in this documentation phase. RevMan availability/version and unobserved gestures prevent honest whole-task numeric comparisons. Obtain recordings with timestamps, exact fixture, settings, pointer/keyboard log and exported artifacts next; distinguish counted baselines from measured observations. T2 must include covariate entry and T5 must become completable before claiming progress across all five tasks.

## RM5 sample inventory and proposed scope

Inspected public `meta` sample [Fleiss1993.rm5](https://raw.githubusercontent.com/guido-s/meta/d100dde2c4aa924cef1399973da72f57904e93dd/inst/extdata/Fleiss1993.rm5), SHA-256 `af4215ebcb2c186738fb2fb30abb7366de17678d29efba617f0abe9bb96bfaa7`. Parsed XML, not imported into RCMS. It has 12 STUDY elements, 12 REFERENCE elements, one COMPARISON, one DICH_OUTCOME with seven DICH_DATA and one CONT_OUTCOME with five CONT_DATA. Counts are structural inventory, not step measurements. Empty sections occur too; presence does not establish populated content or coverage of all RM5 variants.

The complete observed element-name inventory is retained below for scope review. Proposed first importer handles supported study identifiers, names, arm labels, dichotomous/continuous raw inputs and inclusion in analysis. Preserve source comparison/outcome labels in the preview and map each analysis to a sheet. Report review narrative, references beyond identifying metadata, risk-of-bias entries, figures, certainty/SoF, unsupported outcomes, methods/settings and extensions as unsupported, with element path and count. No silent replacement of statistical choices. This sample does not qualify diagnostic, generic inverse variance, multi-arm, cluster/crossover or subgroup import; acquire examples before expanding scope.

```text
ABSTRACT
ABS_BACKGROUND
ABS_CONCLUSIONS
ABS_DATA_COLLECTION
ABS_OBJECTIVES
ABS_RESULTS
ABS_SEARCH_STRATEGY
ABS_SELECTION_CRITERIA
ACKNOWLEDGEMENTS
ADDITIONAL_REFERENCES
ADDITIONAL_TABLES
ADDRESS
ADDRESS_1
ADDRESS_2
AGREEMENT
ALLOCATION
ANALYSES_AND_DATA
APPENDICES
APPLICABILITY_OF_FINDINGS
AWAITING_STUDIES
BACKGROUND
BIAS_ASSESSMENT
BLINDING
BODY
CHARACTERISTICS_OF_AWAITING_STUDIES
CHARACTERISTICS_OF_EXCLUDED_STUDIES
CHARACTERISTICS_OF_INCLUDED_STUDIES
CHARACTERISTICS_OF_ONGOING_STUDIES
CHARACTERISTICS_OF_STUDIES
CHAR_INTERVENTIONS
CHAR_METHODS
CHAR_NOTES
CHAR_OUTCOMES
CHAR_PARTICIPANTS
CITY
COCHRANE_REVIEW
COMPARISON
CONCLUSIONS
CONDITION
CONFLICT_OF_INTEREST
CONTACT
CONTRIBUTIONS
CONT_DATA
CONT_OUTCOME
COUNTRY
COVER_SHEET
CREATORS
CRIT_INTERVENTIONS
CRIT_OUTCOMES
CRIT_OUTCOMES_PRIMARY
CRIT_OUTCOMES_SECONDARY
CRIT_PARTICIPANTS
CRIT_STUDIES
DATA_COLLECTION
DATA_EXTRACTION
DATA_SYNTHESIS
DATE
DATES
DEPARTMENT
DESCRIPTION
DICH_DATA
DICH_OUTCOME
DISCUSSION
EFFECT_MEASURES
ELECTRONIC_SEARCHES
EMAIL_1
EMAIL_2
EXCLUDED_STUDIES
EXCLUDED_STUDIES_DESCR
EXCLUSIONS
EXTENSIONS
EXTERNAL_SOURCES
FAX_1
FAX_2
FEEDBACK
FIGURES
FIRST_NAME
FOOTNOTE
FOOTNOTES
GRAPH_LABEL_1
GRAPH_LABEL_2
GROUP_LABEL_1
GROUP_LABEL_2
HETEROGENEITY_ASSESSMENT
HISTORY
IDENTIFIERS
IMPLICATIONS_PRACTICE
IMPLICATIONS_RESEARCH
IMPORTANCE
INCLUDED_CHAR
INCLUDED_STUDIES
INCLUDED_STUDIES_DESCR
INTERNAL_SOURCES
INTERVENTION
INTERVENTION_EFFECTS
KEYWORDS
LAST_CITATION_ISSUE
LAST_NAME
LAST_SEARCH
MAIN_TEXT
MESH_TERMS
METHODS
MIDDLE_INITIALS
MISSING_DATA
MOBILE_PHONE
NAME
NEXT_STAGE
OBJECTIVES
ONGOING_STUDIES
ORGANISATION
OTHER_BIAS_SOURCES
OTHER_REFERENCES
OTHER_SEARCHES
OTHER_VERSIONS_REFERENCES
P
PENDING_REFERENCES
PERSON
PHONE_1
PHONE_2
POSITION
POTENTIAL_BIASES
PREFIX
PROTOCOL_PUBLISHED
PRO_REV_DIFF
PUBLIC_NOTES
QUALITY_ASSESSMENT
QUALITY_ITEM
QUALITY_ITEMS
QUALITY_ITEM_DATA
QUALITY_ITEM_DATA_ENTRY
QUALITY_OF_EVIDENCE
REFERENCE
REGION
RESULTS
REVIEW_PUBLISHED
SEARCH_METHODS
SEARCH_RESULTS
SELECTION_CRITERIA
SELECTIVE_REPORTING
SENSITIVITY_ANALYSIS
SOF_TABLES
SOURCES_OF_SUPPORT
STUDIES
STUDIES_AND_REFERENCES
STUDY
STUDY_DESCRIPTION
STUDY_QUALITY
STUDY_SELECTION
SUBGROUP_ANALYSIS
SUFFIX
SUMMARY
SUMMARY_BODY
SUMMARY_OF_RESULTS
THEORY
TITLE
UNIT_OF_ANALYSIS
UP_TO_DATE
URL
WHATS_NEW
ZIP
```

## Open decisions — user's decision in every case

| Decision | Recommendation for user approval |
| --- | --- |
| Migration beyond agreed pair-to-sheet conversion | Version the new writer, explicitly convert v1 on read, offer Save As without overwriting the source; decide collision names, empty pairs, extra arms, covariate ownership and old-version reopen expectations before coding. No speculative compatibility layer. |
| DOCX dependency | Use python-docx for actual Word tables, paragraphs and images; retain the existing PDF capability where suitable. One result-content representation supplies both serializers and the Methods/Results panels. Confirm package footprint/license and rendered fidelity in Word and LibreOffice before adoption. [Official quickstart](https://python-docx.readthedocs.io/en/latest/user/quickstart.html) demonstrates document, table and picture authoring. No dependency added now. |
| XLSX dependency | openpyxl, read-only worksheet iteration; reject formulas explicitly in the first scope and keep existing numeric types. [Official optimized-mode documentation](https://openpyxl.readthedocs.io/en/stable/optimized.html) describes the streaming reader. Approve handling of formulas, merged/hidden cells and dates before implementing the wizard. |
| Briefcase now or later | Later, after a small cross-platform packaging spike proves embedded R, Qt plugins, signing and real install/upgrade/uninstall behavior. Its [update command](https://briefcase.beeware.org/en/stable/reference/commands/update/) updates the developer's packaged application; do not interpret it as a proven end-user automatic-update solution. Remove development payload from existing bundle inputs first. |
| Anki patterns to borrow | Borrow keyboard-first primary actions and consistent native layouts, not its backend architecture or webview stack. [Reviewer source](https://github.com/ankitects/anki/blob/main/qt/aqt/reviewer.py) provides explicit Return-key action handling; [Qt documentation](https://github.com/ankitects/anki/blob/main/docs-site/addons/qt.mdx) identifies Designer forms. These are source-based pattern candidates, not an Anki usability measurement. User chooses visual patterns after before/after sketches. |
| RM5 import scope | Start with the binary/continuous raw-data sample scope above and an explicit unsupported-item report. Review preview must precede committing imported sheets; expand only with representative source files and numerical comparisons. |
| RevMan calculator modes to match | Target desktop 5.4.1 shown in the attachments, including 2×2 OR/RR/RD, log ratio and interval/SE/Z/P, and continuous mean/SD/N/t/CI/SE paths. Inventory Peto display and continuous combination modes separately: parity must not smuggle in a new statistical method. Current web RevMan documents different context-dependent conversions; choose whether those additional modes are in scope. Undefined log RD and sign-ambiguous reconstructions must be explained, not fabricated. User decides the signed-off mode matrix. |
| Architecture pass this round | Yes, a focused planning pass before a–c implementation, limited to deleting the obsolete dimensions and establishing sheet ownership/selection. Use the codebase-design skill's depth, locality and deletion test; no wholesale rewrite. User decides whether this preparation is included in the next implementation round. |

## Review and next-round evidence

Phase 1 validation is documentation diff review, terminology search, pinned sample XML inventory and Git branch/push receipts. It does not qualify application behavior, numerical preservation, dependencies or installers. Use the supplied `15fa33e2-*.png` attachments as visual problem references (one inspected screenshot explicitly shows RevMan 5.4.1's OR/RR/RD calculator); do not treat screenshots as interaction recordings. [HANDOFF](../ux-audit/HANDOFF.md) retains prior verification context, not new-task proof.

At each later hill-climb round, keep the same five task inputs and settings, change a coherent slice, record successful and failed paths, compare interaction counts and numerical artifacts, and review the result before selecting the next slice. No application code or tests are changed by this plan.
