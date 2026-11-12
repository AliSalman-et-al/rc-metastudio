# File names and ownership

Name maintained files for the responsibility they own, using `CONTEXT.md` for
domain terms. Keep clear names and established language/framework conventions.
Internal moves update imports, dynamic loads, build inputs, manifests, tests and
current documentation together. Published commands, package names, wire values,
project schemas, help topics and frozen historical evidence retain their contracts.

## Responsibility boundaries

| Owner | Responsibility |
| --- | --- |
| `application_metadata.py` | Application/organization identity and the version derived from the package version |
| `analysis_catalog.py` | Data-family IDs, supported metrics, labels and default arm names |
| `analysis_validation.py` | Numeric analysis parameter limits, validation and input predicates |
| `result_formatting.py` | Result numbers, labels, references, precision defaults and plain-text tables |
| `calculator_controls.py` | Calculator input widgets, table controls, validation and field sizing |
| `calculator_effect_readout.py` | Selected effect source, display-scale conversion and readout presentation |
| `calculator_edit_history.py` | Dialog-local edit commands and undo/redo history |

Catalogue and validation remain independent of Qt. Metadata imports only the
canonical package version. Calculator readouts depend on controls; controls do
not depend on readouts or history. History needs no Qt or R dependency. Callers
import the owner they use; the old catch-all modules have no re-export facade.
Unreferenced legacy globals are removed rather than given a new home.
Qt Designer custom-widget headers import their control owner directly; the
diagnostic prevalence field is generated from `calculator_controls.py`.

Before relocation, the verification obligations are: preserve numeric family
IDs and metric strings/list ordering; preserve validation and rounding behavior;
preserve calculator source selection, inactive inputs, sizing, signals and
undo/redo; inject the test R boundary into its actual new owner; preserve version
bumping; and resolve every runtime, package-resource and script-loader path.
Existing failure checks and real Qt/R workflows provide this proof. Frozen
numerical oracles are unchanged.

## Filename audit

The complete tracked-path inventory, old-to-new mapping, protected-file hashes
and reference checks are retained under `artifacts/verification/filename-audit/`.
Renames distinguish Qt test support from collected tests, loader helpers from
workflow definitions, release-version tests from general release readiness, and
public-package numerical authority tests from frozen golden tests. R source
filenames describe data classes, confidence levels, repeated analyses,
meta-regression and small-study effects while keeping exported symbols stable.

The UI label **Publication Bias** remains available; the internal analysis
boundary is named **small-study effects**, as defined in `CONTEXT.md`.
Qt Designer source names and generated class/module names remain controlled by
the form manifest. Public verification and packaging command paths stay stable.

## Rename ledger

| Previous path | Current path |
| --- | --- |
| `src/rc_metastudio/runtime_types.py` | `src/rc_metastudio/qt_object_guard.py` |
| `src/rc_metastudio/tabular_data.py` | `src/rc_metastudio/row_padding.py` |
| `src/rc_metastudio/publication_bias.py` | `src/rc_metastudio/small_study_effects.py` |
| `src/rc_metastudio/publication_bias_dialog.py` | `src/rc_metastudio/small_study_effects_dialog.py` |
| `src/rc_metastudio/result_sections.py` | `src/rc_metastudio/result_formatting.py` |
| `scripts/verification_resources.py` | `scripts/desktop_worker_capacity.py` |
| `scripts/qt_window_ownership.py` | `scripts/qt_form_ownership_audit.py` |
| `scripts/macos_evidence.py` | `scripts/macos_feasibility_evidence.py` |
| `r/RCMetaR/R/classes.R` | `r/RCMetaR/R/analysis_data_classes.R` |
| `r/RCMetaR/R/meta_global.R` | `r/RCMetaR/R/confidence_level.R` |
| `r/RCMetaR/R/meta_methods.R` | `r/RCMetaR/R/repeated_analyses.R` |
| `r/RCMetaR/R/meta_reg.R` | `r/RCMetaR/R/meta_regression.R` |
| `r/RCMetaR/R/publication_bias.R` | `r/RCMetaR/R/small_study_effects.R` |
| `r/RCMetaR/tests/testthat/test-publication-bias.R` | `r/RCMetaR/tests/testthat/test-small-study-effects.R` |
| `r/RCMetaR/tests/testthat/test-refactor-regressions.R` | `r/RCMetaR/tests/testthat/test-subgroup-covariate-plot-data.R` |
| `tests/python/gui/test_types.py` | `tests/python/gui/qt_test_support.py` |
| `tests/packaging/contract/_workflow.py` | `tests/packaging/contract/_module_loader.py` |
| `tests/packaging/contract/test_release_readiness_contract.py` | `tests/packaging/contract/test_release_version_bump.py` |
| `tests/packaging/contract/test_release_shell_repairs.py` | `tests/packaging/contract/test_release_shell_failure_safety.py` |
| `tests/packaging/contract/test_clean_slate_delivery_contract.py` | `tests/packaging/contract/test_delivery_state_machine.py` |
| `tests/python/gui/test_user_facing_text_regressions.py` | `tests/python/gui/test_main_window_context_menu.py` |
| `tests/python/gui/test_declarative_dialog_sizing.py` | `tests/python/gui/test_parented_wizard_sizing.py` |
| `tests/python/fast/test_dataset_model_edit_values.py` | `tests/python/fast/test_dataset_table_editing.py` |
| `tests/python/fast/test_publication_bias_contract.py` | `tests/python/fast/test_small_study_effects_contract.py` |
| `tests/python/gui/test_publication_bias_dialog.py` | `tests/python/gui/test_small_study_effects_dialog.py` |
| `tests/r_stack/test_reitsma_golden.py` | `tests/r_stack/test_reitsma_mada_authority.py` |
| `tests/e2e/review_workflows.py` | `tests/e2e/analysis_settings_workflows.py` |

## Desktop verification ownership

The chronological E2E bundles are replaced by owners for plot geometry,
analysis-result checks, presentation workflows, desktop/keyboard navigation,
prediction intervals, group labels, colour exports, coefficient axes, diagnostic
precision, contour recovery and arm headers. Shared plot-window observations
and disposal have one support owner. Existing scenario orchestration calls the
independent workflows directly. Scenario names, event IDs and artifact names
remain stable so previous evidence retains its meaning.

Two uncalled release helper functions were removed. They had no registered
scenario or test caller and supplied no executable qualification coverage.

## Remaining design review

`test_main_window_automation_launch.py` still combines startup, covariate editing,
results resizing and plot-editor transactions. A further division should give
those independent scenarios their own owners while preserving shared fixtures
and distinct failure diagnostics. Large application windows retain ownership of
their UI composition; line count alone is not a reason to split them.

`r_bridge.py` combines conversion, execution and result presentation. A useful
next seam would move fully materialized Python result presentation into its own
owner, with explicit display precision. Live rpy2 object inspection must stay
inside the existing R transaction, with one session owner. Numerical and report
contracts need fresh proof before changing that seam.

`r_runtime` owns environment configuration and readiness; `r_bridge.initialize_r`
owns the embedded interpreter. Launch publishes readiness after library loading
and working-directory initialization complete. Runtime bootstrap failure clears
readiness. A restart remains necessary after embedded-R initialization failure.

No directory restructuring is required for the changes above.

## Code symbols

Names describe the domain and the operation actually performed. An outcome is
the endpoint; its sheet has a data type. Arms are intervention/control column
groups; subgroup categories retain the term group. Derived effect previews are
distinct from analysis effect estimates. `CONTEXT.md` remains the vocabulary
owner; these internal renames introduce no new domain concepts.

| Previous name | Current name | Meaning |
| --- | --- | --- |
| `get_current_outcome_type` / `get_current_outcome_subtype` | `get_current_data_type` / `get_current_data_subtype` | Sheet input data type and subtype |
| `default_group_names` | `default_arm_names` | Intervention/control arm defaults |
| `EditGroupNameDialog` / `edit_group_name` / `rename_group` | `EditArmNameDialog` / `edit_arm_name` / `rename_arm` | Rename an arm while retaining its identity |
| `blank_all_studies` | `_set_all_studies_included` | Change inclusion flags without clearing study data |
| `update_outcome_if_possible` | `update_effect_previews_if_possible` | Refresh transient raw-data effect previews |
| `PublicationBiasDialog` | `SmallStudyEffectsDialog` | Configure small-study effects analysis |
| `TestMethod` | `AsymmetryTestMethod` | Statistical asymmetry methods, independent of the test runner |
| `seems_sane` | `is_valid_plot_tick_list` | Validate finite plot ticks |
| `table_cells_editable` | `table_has_no_editable_cells` | True when no existing cell can be edited |
| `evaluate` / `save_table_data` | `validate_calculator_input` / `snapshot_table_text` | Validate input or capture table text, without saving a project |
| `just_created` / `_index` | `initial_redo_pending` / `_applied_command_count` | Already-applied edit publication and undo/redo boundary |
| `restored_selection` | `restored_active_sheet` | Restore the active sheet, distinct from a row or cell selection |
| `run_round5` | `run_long_figures_and_bubble_bounds` | Long-figure and bubble-plot proof |

Callers, protocols, keyword arguments, tests and dynamic symbol references move
together. Existing public commands, statistical method IDs, project/settings
keys, Qt Designer identifiers, framework overrides, UI labels and historical
evidence retain their contracts. Mathematical notation stays concise when its
meaning is already clear. Confirmed unused definitions are deleted instead of
renamed or retained behind compatibility aliases.

Vulture is a review aid. A reported symbol needs a caller and contract review;
an unused callback argument or pytest fixture is not sufficient evidence of dead
code. Conversely, remove helpers reached only from a confirmed dead owner, then
rescan. Keep persisted migration keys even when an obsolete window's state
accessors are removed.

## Retained legacy boundaries

Legacy project v1/v2 schemas and conversion live at the archive read boundary.
Existing user projects and saved forest bundles still open. Old Mean spellings
normalize to `Mean`; old CSV headers are input aliases. Stored user arm names,
notes and labels remain user data. No current sample builder writes the old
outcome/follow-up graph.

Qt6 provides native Python values and file-dialog tuples directly. Redundant
Qt4 conversion wrappers, the R-backend forwarding module, numeric arm IDs, the
unused two-way dictionary and the one-off pre-conversion capture are removed.
Study effect comparisons use stable arm-ID tuples. Edit rollback restores
measurements and inclusion explicitly through the study's edit snapshot.

Golden execution consumes the same typed `AnalysisRequest` as production.
Historical oracle metadata stays independent of executable request structure;
the harness does not inject shadow modules or obsolete execution methods.

| Removed compensation | Ownership that makes it unnecessary |
| --- | --- |
| QVariant/QString and file-dialog shape wrappers | Qt6 supplies native values and documented tuples directly |
| R-backend forwarding module and duplicate cache owner | `r_runtime` configures the environment and readiness; `r_bridge` initializes R once |
| Numeric IDs alongside stable arm identities | Study arm measurements use the persisted `ArmId` |
| Raw `__dict__` rollback | The existing edit snapshot restores measurements and inclusion |
| Unconditional reads of a second arm | Calculators select the metric's arity before reading arm data |
| Old outcome/follow-up graphs created only to migrate them | Sample builders write current sheets, rows and stable IDs |
| Shadow modules translating obsolete test APIs | Golden cases contain explicit production analysis requests |

Calculator metric choices still depend on entered-effect keys, then append the
current metric when that history is absent. Saving a raw-only study can therefore
narrow its calculator choices after reopening. A future change should derive
choices from the metric catalog and an explicit input-capability policy. Review
how switching metrics should behave for entered-only studies before changing
those choices.

The documented intermittent Windows widget-painting crash remains unreproduced;
passing native source checks do not establish its original trigger or a fix.
