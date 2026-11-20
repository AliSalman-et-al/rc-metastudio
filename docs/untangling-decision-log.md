# RC MetaStudio untangling decision log

Audit base: `ab96977bef884bc6bdb40cf981f63dada0c7a11f`, clean `joss/refactor`. Both optional cleanups are in scope. Test cleanup follows the structural edits. Paths and line numbers in the audit refer to this base.

## Evidence before edits

- Strict Windows Ty passed. Receipt: `artifacts/verification/typing/20261121T000202-721763cf/command.json`.
- The real Qt/R doctor passed. Manifest: `artifacts/verification/rcms/20261120T190227Z-34c676cc-doctor/manifest.json`. This establishes startup with the selected installed library.
- The structural inventory under `.tmp/untangle/before/` records 425 Python/R files, 2,292 resolved Python import sites and 7,748 Python decision sites. The scanner does not resolve R dispatch, Qt auto-connection, shell calls or Python dynamic imports, so call sites and tests still determine whether a finding is valid.
- The clean fast run is recorded in `.tmp/untangle/baseline-fast.log`. It observed a failure before any edits. Preserve its final diagnostics for test cleanup.
- Git evidence: `ab96977b` and `41faf92d` changed the R bridge and Results together. `d727be6e` and `26a0f484` changed both R verification entry points and their shared support. Co-change is a lead to investigate. The behavior contracts below govern consolidation.

## Workspace and startup

1. Carry parsed tabular input to a sheet through one semantic import boundary. Keep parsing and preview apart from publishing an edited sheet.
   - Hidden links: `csv_import.py:21–48` and `main_wizard.py:778–820,922` serialize the same normalized input through two representations.
   - Needless links: `main_window.py:1566–1585` constructs a temporary table model and `dataset_table_model.py:593–615` uses its visual column/context mapping to apply import edits. Use the same field schema as the grid with workspace editing. Preserve ratio inputs, covariates, provenance and transactional failure.
2. Give project replacement and history one commit point and pass the originating sheet when publishing result edits.
   - Hidden links: `main_window.py:849–871,1007–1086,1533–1585` sequences history mutation, view installation and checkpoint updates differently for undo/redo, open, wizard creation and import. CSV explicitly retains its first undo operation.
   - Special case: `main_window.py:747–755,930–940` duplicates live-sheet checks; the change then reads the currently visible sheet. Keep protection against old Results on a replaced project and preserve selection and dirty state on failure.
3. Reuse the generated Qt build root for forms and resources and leave document checkpointing with the operation that established it.
   - Hidden link: `qt6_ui.py:15,25–30` and `qt6_resources.py:14,43–53` independently resolve the same generated build.
   - Surplus: `launch.py:259–262,380` repeats initial or already successful open checkpoints. The entry point and composition also repeat resource and exception initialization (`__main__.py:17–18`, `launch.py:297–298`). Preserve early automation diagnostics, packaged resources and deferred R startup.
4. Share the current-format archive normalization pass for read/write.
   - Hidden link: `project_format.py:307–331,445–470` separately order schema, metric and semantic handling.
   - Required cases: v1/v2 migrations and their pre-migration validation, archive size/trust constraints, atomic replacement, and legacy input provenance remain part of the public format.

## Analysis, Results and calculators

5. Let the Python bridge prepare and run diagnostic input in one serialized call.
   - Hidden link: `analysis_adapter.py:309–320` knows count and direct-effect conversions, while `r_bridge.py:1085–1140` uses the converted Python container shape to recover which branch it needs.
   - Keep joint Reitsma count-only, preserve independent direct-effect input and per-metric errors, and retain the v1 wire contract.
6. Discover methods and validate selections by domain identity, then apply labels at display time.
   - Needless link: `analysis_setup_dialog.py:1192–1259` owns R objects while querying methods, intersects label-keyed mappings, adjusts string prefixes and recognizes Reitsma by display text.
   - Surplus: `analysis_adapter.py:128–175` forwards pure operations through an executing service. Its covariate completeness path at :187–211 goes from stable IDs through names and back; validate selected studies by ID.
7. Navigate Results by named section/table identities and session records.
   - Hidden links: `results_window.py:386–451,854–856` couples navigation to translated titles, positional `table-2`, and parallel item-ID dictionaries.
   - Surplus: :377–384 copies plot fields into aliases with no production reader. Inspect dynamic consumers and preserve data read by report/evidence drivers, stable plot order, selection and TSA sensitivity navigation.
8. Give plot style metadata a neutral owner.
   - Hidden links: `plot_defaults.py:4–8`, `small_study_effects.py:50–83`, and `small_study_effects_dialog.py:452–456` repeat preset label facts. `plot_editor_dialog.py:41,696` and `trial_sequential_analysis.py:16,288` import the small-study workflow for shared appearance defaults.
   - Keep differences among funnel, bubble and forest defaults where prescribed by their plotted geometry.
9. Give calculator readout and edit transactions explicit inputs and ownership.
   - Needless link: `calculator_effect_readout.py:155–192` infers private dialog state and installs connections during rendering; :82–85,135 bypass the typed conversion already used by dialog services.
   - Hidden links: field validation and undo/edit snapshots are parallel across `binary_data_dialog.py:656–919`, `continuous_data_dialog.py:555–693,894–960,1226–1294` and `diagnostic_data_dialog.py:457–571,689–814`. `calculator_controls.py:321–365` couples family-specific scalar validation, R conversion, messaging and exception-based branching. Preserve input-specific rules, invalid drafts, cancellation, raw/entered provenance, and interval transformation requirements.
10. Compile the executed analysis context once and make consumers depend on it.
    - Hidden links: `analysis_setup_dialog.py:894–1130` spans configuration, execution, rollback, and rereads widgets/definitions to report the analysis. :928–938 and `trial_sequential_analysis.py:105–125` exchange an implicit last-pooled-method tuple and infer pooling from method suffixes.
    - Special cases: `trial_sequential_analysis_dialog.py:180–195,339–397` owns preview debounce, worker protocol and finish races. The worker and main-thread R isolation are required. Keep latest-only results and test disposal.
11. Separate runtime and result decoding responsibilities.
    - Hidden link: `r_bridge.py:50–127`, `r_runtime.py:15–35` and `launch.py:352–366` coordinate partly initialized global state. Publish ready bindings as one state transition while respecting R's process-wide lifetime.
    - Needless links: `r_bridge.py:1170–2418` contains runtime, wire and result assembly with ambient result precision; :1201–1235 interprets raw model slots to reconstruct R-produced report tables. Move explicit producer metadata with the result when golden/current-source comparison confirms equivalence.
    - Surplus: `reitsma_meta_regression.py:160–592` has only test consumers. Keep its useful independent observations with the tests.

## R authority package

12. Remove unreachable private statistical and plotting routines. Keep explicit errors for unsupported public requests.
    - Surplus and special cases: `meta_regression.R:323–330,350–879` contains unused conditional-means and legacy plot functions; permutation still calls `g.meta.regression`. The unused optional coefficient plot branch calls an undefined helper. `repeated_analyses.R:140,230–271,365–390` rejects conditional means, then carries unreachable variants.
    - Surplus: `plotting.R:394–510` has dead formatter/radii code. `analysis_output.R:104–125` and `rcmetar-core.R:374` have unused private transform implementations. Preserve the live authority package transforms.
13. Allocate analysis artifacts through one scratch owner.
    - Hidden links: `analysis_contracts.R:25` owns scratch. `reitsma_methods.R:747` and `repeated_analyses.R:150–153` fall back to the working directory. The bootstrap path checks NULL after converting it to an empty character vector.
    - Special case: `results_display.R:247,255` uses time-derived artifact prefixes. Use unique paths in owned scratch. Preserve explicit destinations.
14. Normalize v1 request envelopes once and share forest structure by responsibility.
    - Hidden links: `rcmetar-core.R:649,704–723,772–784,845–920` duplicates general and diagnostic envelopes and renames the same field between them. Preserve existing public convenience forms and per-metric error semantics.
    - Needless links: Default, BMJ and shared preflight call RevMan-owned data, axis and summary routines. Move genuinely shared routines to their forest data/axis/summary owners. Preserve style-specific behavior.
    - Surplus: `plotting.R:150–206` builds generic plot data even for fitted models that immediately replace it. Preserve supported row-only plots and their order. `rcmetar-core.R:195–208,1247–1276` repeats plot defaults while the small-study and TSA producers build parallel capability facts.

## Verification and delivery

15. Keep pinned R verification policy and locked Python identities with their inputs; let CLI entry points report their own errors at the edge.
    - Hidden links: `verify_rcmetar_r_default.py:224–241` and `verify_rcmetar_r_stack.py:444–465` enforce the same snapshot policy and subprocess variables independently. The lanes use different cache namespaces and strictness for absent R/dependencies.
    - Surplus: pass-through probe and policy functions in the default and full R verifiers translate the same error, then CLI boundaries catch the translated error. `verify_golden_compatibility.py:47–56`, `verify_rcmetar_r_stack.py:28–32`, and the golden harness duplicate or import workflow-owned live rpy2 pins. Use the dependency lock for the active run while keeping fixed historical oracle identity.
    - Special case: `tests/e2e/desktop_driver.py:262–264` snapshots an unconsumed internal R function body. The runtime identity and artifact fingerprint already bind the evidence.
16. Derive delivery facts from the target and stage that own them.
    - Hidden link: `build-macos-package.sh:165,382` reads the target's R version, then overrides it locally. The downloaded framework version and verification must agree with the selected target.
    - Hidden link: candidate and qualification workflows repeat stage record assembly and the ordering of archive, inventory, SBOM and parent digest. Review common unsigned target behavior alongside the signed/notarized routes. Retain native platform controls, immutable digest framing, and fail-closed publication.
    - Special cases to retain: process-tree cleanup, an independently launched macOS application, sandboxed installer/launcher alternatives, download retry, and notarization propagation are external failure modes. `run_with_timeout.py:26–41` and `run_bounded_process.py:76–92` have common lifecycle mechanics with different logs and escalation requirements.

## Test cleanup policy

- Remove guards that skip required installed R imports and exact versions already qualified by the manifest. Keep meaningful platform skips and numerical/geometry checks.
- Remove assertions that only return the same implementation constant or test a private adapter that no longer exists. Preserve identifiable failures with the same or stronger behavior checks.
- Confirm any pre-existing failure using the same command and host before deciding whether it is an unstable test or a genuine bug.
- Keep the released project fixtures, frozen numerical contracts and historical package evidence.

## Audit refinements before implementation

- Workspace items 1–2 also cover positional column-field duplication in `sheet_columns.py:161–193`, `dataset_table_model.py:469–481` and `workspace_editing.py:346–435`, the private model sync call at `main_window.py:1100`, and its per-model signal setup flag (:643–687). Keep the existing pre-delete checkpoint until callers that bypass transactions have migrated. Ragged clipboard padding is the observable behavior, so its unreachable follow-up rectangularity check can go. Review the unused-in-normal-entry Welcome route (`main_wizard.py:203–303,1057,1234–1237`) against the native test entry points. Replace exception-prefix matching (`main_window.py:113–122`) with an archive-owned reason. Do not conflate strict editing policies with what old saved projects can contain.
- Workspace item 3 also covers process working-directory setup in `settings.py:588–603` and `launch.py:309–335`, with R resetting the same process directory in `r_bridge.py:271–286`. Complete scratch path migration before touching those lifecycle assumptions. Deferred Qt focus and Windows native argv handling have real platform constraints.
- Results item 7 also includes the unused item-to-coordinates map (`results_window.py:363,1121,1433`), the unread manuscript precision field (`analysis_results.py:138`), and the unused caption workflow parameter (`analysis_identity.py:113`).
- R items 13–14 also cover the duplicated plot bundle writers (`results_display.R:245–268`, `small_study_effects.R:1192–1199`) and hardcoded method names and plot publication in repeated/subgroup workflows. Preserve RData member names and style differences. Normalize same-meaning zero-correction inputs at their boundary, retain family eligibility semantics, and distinguish small-study unavailable reasons from failed fits.
- Static limits identified during the audit include Designer custom widgets, subprocess-launched scripts and R symbol dispatch. A suspected unused prevalence widget was located in the .ui file and must stay. An apparent earlier history publication bug was only redundant refresh order. These false leads are excluded from the change list.

### Delivery pin ownership

- The two deployment inspectors and Windows exact-archive continuation each repeat the active deployment version table. For the Python version, wheel distributions and R, compare the observed package against the repository's existing pins. Keep the SIP runtime API pin explicit because it is a separate identity from the SIP distribution version.
- In macOS package evidence, observe the PyInstaller version that actually runs and compare that observation with the pinned value. The reported tool identity must vary with the tool that built the package.

## File and package organization

- Put persisted project format, semantic validation, migration, runtime project models, and their conversion in `rc_metastudio/project/`. Keep the bundled schema resources at the existing qualified paths.
- Put editing, session history, table adapters and column rules in `rc_metastudio/workspace/`. Keep tabular workflows and RevMan parsing/review in `rc_metastudio/importing/`. Project code must stay able to load without Qt or R.
- Put request execution and analysis setup in `rc_metastudio/analysis/`; keep dialog and non-dialog code for trial sequential and small-study analyses together. Put result, manuscript and plot presentation in `rc_metastudio/results/`. Keep calculator history, controls, authority calls and the four dialogs in `rc_metastudio/calculators/`.
- Rename the R package's `display.R` to `numeric_display.R` to distinguish scalar formatting from structured report output. Keep the standard flat `R/` layout.
- Use explicit imports at new ownership boundaries. Keep generated Qt module paths, user entry points, and frozen resource destinations. Migrate verification drivers, form custom widget imports, audit paths and code-health rules with their owners.

## Review decisions at qualification

- Keep the pure archive schema and the Qt table editing rules separate. A valid older project can contain values that the current editor would reject. Keep sheet-local ownership for edit rollback and the product's Welcome entry used by native and spreadsheet workflows.
- Keep continuous pre/post draft and back-calculation snapshots, binary supplied-count roles, and diagnostic prevalence inputs with their calculators. Their acceptance and restoration behavior differs. Shared conversion and field validation already sit below those transactions.
- Keep the TSA preview debounce and subprocess. Native embedded R belongs on the main thread. The report copy action now reads the latest accepted report, as proved by rerunning TSA through the Results window.
- Retain the serialized result decoder's precision scope and cross-language regression table interpretation. Passing precision through the existing hierarchy would touch dozens of functions, and removing the Python interpretation requires a complete producer quantity contract and its own verification. Keep historical project and frozen result compatibility checks in place.
- Keep the public legacy confidence fallback, the required platform guards, and the qualified fixed-name diagnostic CSV outputs in owned scratch. The R-source scan found no additional unused ordinary private functions after excluding registered S3 methods and the public default's getter.
- The stand-alone Qt layout audit reported the same 67 existing findings at the audit base and after moving the files. The comparison normalized relocated paths and line numbers and found no additions or removals. The form ownership audit paths and semantic exception rules moved with their owners.
- The final relocation re-audit caught and corrected two test fixtures: the forbidden-project-import history fixture now follows the actual package boundary, and the XLSX year-column mutation applies to the active reader.

## Qualification recoveries

- Candidate recording now uses the dispatching workflow's recorder and the selected source's target registry. The historical-source replay initially failed because the old CLI lacked the new recording command. The replay now checks the selected source SHA, manifest identity and archive and payload checksums.
- The integrated Results drive caught diagnostic method IDs reaching prose without a final label conversion. The report now selects the Reitsma and univariate branches by ID, and resolves display labels only for text. The `results-values` repeat passed.
- The extracted Windows package's 125% probe timed out during one run. Its exact executable passed the same native surface probe when replayed directly. Windows now supplies the ordinary startup-project check and lets the common assembler run the three German-locale surface checks once. The eliminated first pass wrote English-locale files that the assembler overwrote.
- Earlier integrated runs were retired after executable changes. Their R package check, 103 authority comparisons, 21 Reitsma visual cases, nine bridge cases, and individual workflow evidence remain available. The final desktop matrix takes a new strict typing receipt and source/runtime fingerprint.
