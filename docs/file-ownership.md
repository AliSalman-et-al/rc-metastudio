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

R startup also spans `r_bridge.initialize_r`, `r_backend.install_r_backend`,
`r_runtime` readiness and launch composition. Module bindings, a saved exception,
backend installation and a ready flag encode different lifecycle milestones.
One lifecycle owner could make those phases explicit, publishing readiness only
after the required initialization completes. Partial-startup failure and the
retry-versus-restart policy require targeted evidence before this redesign.

No directory restructuring is required for the changes above.
