# Sheet migration evidence

Status: baseline preparation only. The sheet-owned runtime, v3 seam and writer,
tabs, undo operations and sample conversion are **not implemented**. No numerical
oracle or bundled project has changed. This increment preserves the working app.

## Reproduce the original corpus capture

Generate forms with `uv run python scripts/build_qt6.py generate --build-root
build/qt6-verification`. Select the pinned R 4.6.1 runtime and a worktree-owned
library containing the current RCMetaR source, then run:

```sh
uv run --no-sync python scripts/sheets_baseline.py build/sheets-baseline/original-corpus-complete
```

Use a new output directory for each invocation. The script refuses to overwrite
one. It retains byte-identical original archives, SHA-256 hashes, declared pairs,
saved settings, current R source hashes, command and runtime environment. It
opens those retained files through the production desktop path and records the
default random-effects analysis's numerical sections for every declared pair.
`numerics.json` is written only after all pairs complete. The standard helper
retains runtime identity, action/configuration/result screenshots and plots.

This is baseline capture, not an independent statistical oracle or a conversion
equality assertion. The existing frozen gates remain authoritative. Additional
HR/IRR fixed, subgroup and MH analyses still require `ratios-samples`; this
recorder alone does not satisfy the complete requested sample proof.

Completed original capture: **8/8 pairs**, exit 0. Numerical sections are in
`build/sheets-baseline/original-corpus-complete/numerics.json`; original inputs
and inventory are beside it. Helper evidence:
`artifacts/verification/rcms/20261030T225528Z-3eb6931f-sheets-baseline`.

| Original file | Version | Pairs → intended sheets | Conversion equality |
| --- | --- | --- | --- |
| BCG.rcms | 1 | 1 → 1 | Not run |
| NielWeise2008-IRR.rcms | 2 | 1 → 1 | Not run |
| Pignon2000-HR.rcms | 2 | 1 → 1 | Not run |
| amino.rcms | 1 | 2 → 2 | Not run |
| continuous.rcms | 1 | 1 → 1 | Not run |
| lymph.rcms | 1 | 1 → 1 | Not run |
| meantime.rcms | 1 | 1 → 1 | Not run |

## Runtime and native evidence

R home: `/home/ali/Documents/Code/rc-metastudio/build/ux-round3/r-home`.
The supplied `r-library` cannot load RCMetaR because `farver` is missing. Copied
`r-stack-retained-273bd6a` into this worktree's `build/sheets-r-library` and
installed `r/RCMetaR` there; no shared or system library was changed. Installation
log and source hashes: `build/sheets-baseline/r-install.log` and
`build/sheets-baseline/r-source-installed.json`. Generated forms are local to
`build/qt6-verification`. Exact environment: `build/sheets-baseline/ENV.sh`.

The locked rpy2-rinterface 3.6.6 wheel lacked its required API module. Rebuilt
that version from source with `RPY2_CFFI_MODE=API` and `LIBRARY_PATH` pointing at
the supplied read-only `ux-round3/link-libs`. Retained build log:
`build/sheets-baseline/rpy2-api-install-linked.log`. Use `--no-sync` to retain
the locally compiled bridge.

Doctor passed: `artifacts/verification/rcms/20261030T225131Z-a97e7ad9-doctor`.
Native Aminoglycosides passed the existing frozen numeric contract:
`artifacts/verification/rcms/20261030T225642Z-c0387de3-amino`.
Before captures: [main window](screens/sheets-before-main.png) and
[analysis setup](screens/sheets-before-analysis.png). These are native xcb
captures; there are no after screenshots yet.

The full desktop command was started but interrupted: **1 passed, 0 reported
failures; remaining scenarios unverified**, exit 2. Transcript:
`build/sheets-baseline/e2e-matrix.log`. This is not a green matrix. Initial
startup failures and the first 120-second corpus timeout remain in the evidence
directories; neither is counted as a product regression or silently discarded.

## Remaining acceptance work

Follow DESIGN.md's migration increments and failure table. In particular, write
the new sheet interaction drives before replacing the runtime graph. Prove
independent row ownership, sheet ID based undo after switching, add/rename/delete,
two-swap identity, disabled noncomparative swap, save/reopen, naming collisions
and legacy multi-follow-up conversion. Preserve raw precision and inactive arms.
Then run the frozen numerical/golden gates, full desktop matrix and full skill
profile. Convert samples only after the production v3 seam is proven, compare
all numerical sections, and update the sample manifest. Deleted product-code
line count in this baseline increment: zero.

## Model and file seam implementation

The UI migration is deliberately pending. No desktop or numerical acceptance is claimed.

Command: `uv run python scripts/check_sheet_conversion.py`

Inputs: exact archive bytes from `git show 322ede26:sample_projects/<file>`. The script authenticates source archives, compares pair data and settings, checks independent runtime reconstruction and v3 archive save/reopen, and verifies source bytes remain unchanged.

| file | pairs → sheets | equal |
| --- | --- | --- |
| BCG.rcms | 2 → 2 | yes |
| NielWeise2008-IRR.rcms | 1 → 1 | yes |
| Pignon2000-HR.rcms | 1 → 1 | yes |
| amino.rcms | 3 → 3 | yes |
| continuous.rcms | 2 → 2 | yes |
| lymph.rcms | 2 → 2 | yes |
| meantime.rcms | 2 → 2 | yes |

### Caller migration inventory

Static inventory of functions referencing removed model APIs (includes callers requiring inspection rather than a claim that every reference fails immediately):

- `src/rc_metastudio/about_legal_dialog.py:AboutLegalDialog.__init__`
- `src/rc_metastudio/adaptive_controls.py:ChoiceControlController.__init__`
- `src/rc_metastudio/adaptive_controls.py:ChoiceListView.__init__`
- `src/rc_metastudio/adaptive_window.py:AdaptiveWindowController.__init__`
- `src/rc_metastudio/add_new_dialogs.py:AddCovariateDialog.__init__`
- `src/rc_metastudio/add_new_dialogs.py:AddFollowUpDialog.__init__`
- `src/rc_metastudio/add_new_dialogs.py:AddGroupDialog.__init__`
- `src/rc_metastudio/add_new_dialogs.py:AddOutcomeDialog.__init__`
- `src/rc_metastudio/add_new_dialogs.py:AddStudyDialog.__init__`
- `src/rc_metastudio/analysis_adapter.py:AnalysisRequest.parameter_values`
- `src/rc_metastudio/analysis_adapter.py:AnalysisRequest.semantic_id`
- `src/rc_metastudio/analysis_adapter.py:AnalysisService.execute`
- `src/rc_metastudio/analysis_adapter.py:AnalysisService.execute_meta_regression`
- `src/rc_metastudio/analysis_adapter.py:AnalysisService.select_studies_for_covariates`
- `src/rc_metastudio/analysis_adapter.py:CovariateSelectionModel.get_studies`
- `src/rc_metastudio/analysis_adapter.py:StudySelectionResult`
- `src/rc_metastudio/analysis_adapter.py:_conversion_kwargs`
- `src/rc_metastudio/analysis_adapter.py:_execute_binary_request`
- `src/rc_metastudio/analysis_adapter.py:_execute_continuous_request`
- `src/rc_metastudio/analysis_adapter.py:execute_analysis_requests`
- `src/rc_metastudio/analysis_adapter.py:execute_meta_regression_request`
- `src/rc_metastudio/analysis_adapter.py:select_studies_for_covariates`
- `src/rc_metastudio/analysis_setup_dialog.py:AnalysisSetupDialog.__init__`
- `src/rc_metastudio/analysis_setup_dialog.py:AnalysisSetupDialog._add_parameter_controls`
- `src/rc_metastudio/analysis_setup_dialog.py:AnalysisSetupDialog._change_settings_callback`
- `src/rc_metastudio/analysis_setup_dialog.py:AnalysisSetupDialog._choose_plot_color`
- `src/rc_metastudio/analysis_setup_dialog.py:AnalysisSetupDialog._create_parameter_control`
- `src/rc_metastudio/analysis_setup_dialog.py:AnalysisSetupDialog._ordered_parameter_definitions`
- `src/rc_metastudio/analysis_setup_dialog.py:AnalysisSetupDialog._parameter_label`
- `src/rc_metastudio/analysis_setup_dialog.py:AnalysisSetupDialog._register_shared_diagnostic_param`
- `src/rc_metastudio/analysis_setup_dialog.py:AnalysisSetupDialog._restore_settings`
- `src/rc_metastudio/analysis_setup_dialog.py:AnalysisSetupDialog._setup_covariates_tab`
- `src/rc_metastudio/analysis_setup_dialog.py:AnalysisSetupDialog._with_result_identity`
- `src/rc_metastudio/analysis_setup_dialog.py:AnalysisSetupDialog.run_meta_regression`
- `src/rc_metastudio/app_error_handler.py:_call_with_compatible_signal_args`
- `src/rc_metastudio/automation.py:_surface_record`
- `src/rc_metastudio/automation.py:start_package_open_report`
- `src/rc_metastudio/binary_data_dialog.py:BinaryBackCalculationDialog.__init__`
- `src/rc_metastudio/binary_data_dialog.py:BinaryDataDialog.__init__`
- `src/rc_metastudio/binary_data_dialog.py:BinaryDataDialog.update_back_calculation_button`
- `src/rc_metastudio/confidence_level_dialog.py:ConfidenceLevelDialog.__init__`
- `src/rc_metastudio/continuous_data_dialog.py:ContinuousBackCalculationDialog.__init__`
- `src/rc_metastudio/continuous_data_dialog.py:ContinuousDataDialog.__init__`
- `src/rc_metastudio/continuous_data_dialog.py:ContinuousDataDialog._effect_display_label`
- `src/rc_metastudio/covariate_type_dialog.py:CovariateTypeDialog.__init__`
- `src/rc_metastudio/covariate_type_dialog.py:CovariateTypeModel.__init__`
- `src/rc_metastudio/covariate_type_dialog.py:CovariateTypeModel.add_covariate_with_new_type`
- `src/rc_metastudio/covariate_type_dialog.py:CovariateTypeModel.data`
- `src/rc_metastudio/covariate_type_dialog.py:CovariateTypeModel.guess_at_values`
- `src/rc_metastudio/covariate_type_dialog.py:CovariateTypeModel.headerData`
- `src/rc_metastudio/covariate_type_dialog.py:CovariateTypeModel.refresh_covariate_values`
- `src/rc_metastudio/covariate_type_dialog.py:CovariateTypeModel.setData`
- `src/rc_metastudio/covariate_type_dialog.py:CovariateTypeModel.update_included_studies`
- `src/rc_metastudio/covariate_type_dialog.py:module`
- `src/rc_metastudio/dataset_analysis_domain.py:ensure_analysis_unit`
- `src/rc_metastudio/dataset_analysis_domain.py:has_entered_data`
- `src/rc_metastudio/dataset_analysis_domain.py:has_study_entered_data`
- `src/rc_metastudio/dataset_analysis_domain.py:module`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.__init__`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._covariate_cell_data`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._display_data`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._edit_target`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._editing_context`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._get_canonical_analysis_unit`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._get_col_count`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._horizontal_header_display`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._outcome_cell_is_available`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._raw_cell_data`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._role_data`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._sort_outcomes_with_display_source`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._sort_outcomes_with_display_source.compare`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._sort_outcomes_with_display_source.outcome_value`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._sort_studies_with_cmp`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel._sync_display_studies`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.add_covariate`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.add_follow_up_to_current_outcome`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.add_new_group`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.add_new_outcome`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.all_studies_are_excluded`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.all_studies_are_included`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.blank_all_studies`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.data_for_only_one_arm`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_covariate_for_column`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_covariate_names`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_current_analysis_unit_for_study`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_current_estimates_and_standard_errors`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_current_follow_up_name`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_current_outcome_subtype`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_current_outcome_type`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_current_raw_data`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_follow_up_name_for_t_point`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_group_names`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_next_follow_up`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_next_outcome_name`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_outcome_type`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_previous_follow_up`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_previous_outcome_name`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_studies`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.get_t_point_for_follow_up_name`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.hydrate_derived_previews`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.included_studies_have_point_estimates`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.included_studies_have_raw_data`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.max_study_id`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.next_groups`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.num_data_cols_for_current_unit`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.order_studies`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.outcome_follow_up_has_group`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.outcome_has_follow_up`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.recalculate_display_scale`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.remove_covariate`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.remove_follow_up_from_outcome`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.remove_group`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.remove_outcome`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.remove_study`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.rename_covariate`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.rename_group`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.setData`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.set_current_analysis_unit_for_study`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.set_current_follow_up`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.set_current_groups`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.sort_studies`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.try_to_update_outcomes`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.update_current_group_effect`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.update_current_group_names`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.update_current_outcome`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.update_current_time_points`
- `src/rc_metastudio/dataset_table_model.py:DatasetTableModel.workspace_column_identity`
- `src/rc_metastudio/dataset_table_model.py:module`
- `src/rc_metastudio/dataset_table_model.py:validate_new_covariate_name`
- `src/rc_metastudio/dataset_table_model.py:validate_new_follow_up_name`
- `src/rc_metastudio/dataset_table_model.py:validate_new_global_follow_up_name`
- `src/rc_metastudio/dataset_table_model.py:validate_new_group_name`
- `src/rc_metastudio/dataset_table_model.py:validate_new_outcome_name`
- `src/rc_metastudio/dataset_table_view.py:DatasetTableView.__init__`
- `src/rc_metastudio/dataset_table_view.py:DatasetTableView._add_studies_if_necessary`
- `src/rc_metastudio/dataset_table_view.py:DatasetTableView._get_number_of_included_studies`
- `src/rc_metastudio/dataset_table_view.py:DatasetTableView._make_context_menu._context_menu`
- `src/rc_metastudio/dataset_table_view.py:DatasetTableView._make_context_menu._context_menu.delete_study`
- `src/rc_metastudio/dataset_table_view.py:DatasetTableView.header_context_menu`
- `src/rc_metastudio/dataset_table_view.py:DatasetTableView.keyPressEvent`
- `src/rc_metastudio/dataset_table_view.py:DatasetTableView.paste_contents`
- `src/rc_metastudio/dataset_table_view.py:StudyDelegate.__init__`
- `src/rc_metastudio/dataset_table_view.py:module`
- `src/rc_metastudio/diagnostic_data_dialog.py:DiagnosticDataDialog.__init__`
- `src/rc_metastudio/diagnostic_data_dialog.py:DiagnosticDataDialog._update_analysis_unit`
- `src/rc_metastudio/diagnostic_data_dialog.py:DiagnosticDataDialog.update_2x2_table`
- `src/rc_metastudio/diagnostic_metrics_dialog.py:DiagnosticMetricsDialog.__init__`
- `src/rc_metastudio/edit_dialog.py:EditDialog.__init__`
- `src/rc_metastudio/edit_dialog.py:EditDialog._setup_connections`
- `src/rc_metastudio/edit_dialog.py:EditDialog.add_covariate`
- `src/rc_metastudio/edit_dialog.py:EditDialog.add_follow_up`
- `src/rc_metastudio/edit_dialog.py:EditDialog.add_group`
- `src/rc_metastudio/edit_dialog.py:EditDialog.add_outcome`
- `src/rc_metastudio/edit_dialog.py:EditDialog.add_study`
- `src/rc_metastudio/edit_dialog.py:EditDialog.remove_covariate`
- `src/rc_metastudio/edit_dialog.py:EditDialog.remove_follow_up`
- `src/rc_metastudio/edit_dialog.py:EditDialog.remove_group`
- `src/rc_metastudio/edit_dialog.py:EditDialog.remove_outcome`
- `src/rc_metastudio/edit_dialog.py:EditDialog.remove_study`
- `src/rc_metastudio/edit_list_models.py:CovariatesModel.__init__`
- `src/rc_metastudio/edit_list_models.py:CovariatesModel.data`
- `src/rc_metastudio/edit_list_models.py:CovariatesModel.setData`
- `src/rc_metastudio/edit_list_models.py:CovariatesModel.update_covariates_list`
- `src/rc_metastudio/edit_list_models.py:FollowUpsModel.__init__`
- `src/rc_metastudio/edit_list_models.py:FollowUpsModel._follow_up_names_for_current_outcome`
- `src/rc_metastudio/edit_list_models.py:FollowUpsModel.setData`
- `src/rc_metastudio/edit_list_models.py:OutcomesModel.__init__`
- `src/rc_metastudio/edit_list_models.py:OutcomesModel.data`
- `src/rc_metastudio/edit_list_models.py:OutcomesModel.refresh_outcome_list`
- `src/rc_metastudio/edit_list_models.py:OutcomesModel.setData`
- `src/rc_metastudio/edit_list_models.py:StudiesModel.__init__`
- `src/rc_metastudio/edit_list_models.py:StudiesModel.data`
- `src/rc_metastudio/edit_list_models.py:StudiesModel.setData`
- `src/rc_metastudio/edit_list_models.py:StudiesModel.update_study_list`
- `src/rc_metastudio/edit_list_models.py:TXGroupsModel.__init__`
- `src/rc_metastudio/edit_list_models.py:TXGroupsModel.refresh_group_list`
- `src/rc_metastudio/edit_list_models.py:TXGroupsModel.setData`
- `src/rc_metastudio/edit_name_dialogs.py:EditCovariateNameDialog.__init__`
- `src/rc_metastudio/edit_name_dialogs.py:EditGroupNameDialog.__init__`
- `src/rc_metastudio/funnel_plot_editor_dialog.py:FunnelPlotEditorDialog.__init__`
- `src/rc_metastudio/funnel_plot_editor_dialog.py:FunnelPlotEditorDialog._choose_color`
- `src/rc_metastudio/funnel_plot_editor_dialog.py:FunnelPlotEditorDialog._update_color_button`
- `src/rc_metastudio/launch.py:_finish_startup_project`
- `src/rc_metastudio/launch.py:_native_windows_command_line_argv`
- `src/rc_metastudio/main_window.py:ElidingStatusLabel.__init__`
- `src/rc_metastudio/main_window.py:ImportProgressDialog.__init__`
- `src/rc_metastudio/main_window.py:MainWindow.__init__`
- `src/rc_metastudio/main_window.py:MainWindow._add_new_covariate`
- `src/rc_metastudio/main_window.py:MainWindow._add_study`
- `src/rc_metastudio/main_window.py:MainWindow._enable_action_meta_regression`
- `src/rc_metastudio/main_window.py:MainWindow._enable_action_subgroup_ma`
- `src/rc_metastudio/main_window.py:MainWindow._group_navigation_availability`
- `src/rc_metastudio/main_window.py:MainWindow._make_new_dataset_and_setup_spreadsheet`
- `src/rc_metastudio/main_window.py:MainWindow._navigation_availability`
- `src/rc_metastudio/main_window.py:MainWindow._remove_study`
- `src/rc_metastudio/main_window.py:MainWindow._setup_connections`
- `src/rc_metastudio/main_window.py:MainWindow._undo_add_follow_up_for_cur_outcome`
- `src/rc_metastudio/main_window.py:MainWindow._undo_add_new_covariate`
- `src/rc_metastudio/main_window.py:MainWindow._undo_add_new_group`
- `src/rc_metastudio/main_window.py:MainWindow._undo_add_new_outcome`
- `src/rc_metastudio/main_window.py:MainWindow._update_project_identity`
- `src/rc_metastudio/main_window.py:MainWindow._update_workspace_guidance`
- `src/rc_metastudio/main_window.py:MainWindow.add_covariate`
- `src/rc_metastudio/main_window.py:MainWindow.change_covariate_type`
- `src/rc_metastudio/main_window.py:MainWindow.delete_covariate`
- `src/rc_metastudio/main_window.py:MainWindow.delete_covariate.redo_f`
- `src/rc_metastudio/main_window.py:MainWindow.delete_covariate.undo_f`
- `src/rc_metastudio/main_window.py:MainWindow.edit_group_name`
- `src/rc_metastudio/main_window.py:MainWindow.model_updated`
- `src/rc_metastudio/main_window.py:MainWindow.new_dataset`
- `src/rc_metastudio/main_window.py:MainWindow.rename_covariate`
- `src/rc_metastudio/main_wizard.py:ChooseMetricPage.__init__`
- `src/rc_metastudio/main_wizard.py:CsvImportPage.__init__`
- `src/rc_metastudio/main_wizard.py:DataTypePage.__init__`
- `src/rc_metastudio/main_wizard.py:MainWizard.__init__`
- `src/rc_metastudio/main_wizard.py:MainWizard.get_results`
- `src/rc_metastudio/main_wizard.py:OutcomeNamePage.__init__`
- `src/rc_metastudio/main_wizard.py:WelcomePage.__init__`
- `src/rc_metastudio/plot_editor_dialog.py:EditPlotDialog.__init__`
- `src/rc_metastudio/plot_editor_dialog.py:EditPlotDialog._choose_color`
- `src/rc_metastudio/progress_dialog.py:AnalysisProgressDialog.__init__`
- `src/rc_metastudio/publication_bias_dialog.py:PublicationBiasDialog.__init__`
- `src/rc_metastudio/qt_layout.py:_MenuIconProxyStyle.__init__`
- `src/rc_metastudio/qt_workspace_columns.py:WorkspaceColumnWidthController.__init__`
- `src/rc_metastudio/qt_workspace_columns.py:WorkspaceColumnWidthController.restore`
- `src/rc_metastudio/r_bridge.py:_analysis_data_kwargs`
- `src/rc_metastudio/r_bridge.py:_cov_values_for_studies`
- `src/rc_metastudio/r_bridge.py:_r_covariate_list`
- `src/rc_metastudio/r_bridge.py:_r_covariate_values`
- `src/rc_metastudio/r_bridge.py:covariate_to_r_expression`
- `src/rc_metastudio/r_bridge.py:dataset_to_simple_ratio_r_object`
- `src/rc_metastudio/r_bridge.py:packaged_runtime_observation`
- `src/rc_metastudio/ratio_data_dialog.py:RatioDataDialog.__init__`
- `src/rc_metastudio/ratio_data_dialog.py:RatioDataDialog._add_rate_fields`
- `src/rc_metastudio/ratio_data_dialog.py:RatioDataDialog.accept`
- `src/rc_metastudio/reitsma_meta_regression.py:ReitsmaMetaRegressionResult.to_mapping`
- `src/rc_metastudio/reitsma_meta_regression.py:_validate_reference_rows`
- `src/rc_metastudio/reitsma_meta_regression.py:parse_reitsma_meta_regression_result`
- `src/rc_metastudio/results_window.py:ResponsivePixmapItem.__init__`
- `src/rc_metastudio/results_window.py:ResultsWindow.__init__`
- `src/rc_metastudio/results_window.py:ResultsWindow._export_name`
- `src/rc_metastudio/results_window.py:ResultsWindow._plain_text_report`
- `src/rc_metastudio/results_window.py:ResultsWindow._setup_identity`
- `src/rc_metastudio/start_page.py:StartPage.__init__`
- `src/rc_metastudio/start_page.py:StartPage.set_recent_projects`
- `src/rc_metastudio/start_page.py:_RecentPathLabel.__init__`
- `src/rc_metastudio/subgroup_analysis_dialog.py:SubgroupAnalysisDialog.__init__`
- `src/rc_metastudio/subgroup_analysis_dialog.py:SubgroupAnalysisDialog._populate_combo_box`
- `src/rc_metastudio/two_way_dict.py:TwoWayDict.__init__`
- `src/rc_metastudio/workspace_column_identity.py:stable_covariate_identity`
- `src/rc_metastudio/workspace_editing.py:WorkspaceEditingService._edit_covariate`
- `src/rc_metastudio/workspace_editing.py:WorkspaceEditingService._edit_requires_name`
- `src/rc_metastudio/workspace_editing.py:WorkspaceEditingService._edit_study_name`
- `src/rc_metastudio/workspace_editing.py:WorkspaceEditingService._new_study_for_edit`
- `src/rc_metastudio/workspace_editing.py:WorkspaceEditingService._study_for_edit`
- `src/rc_metastudio/workspace_editing.py:WorkspaceEditingService.update_outcome_if_possible`
- `src/rc_metastudio/workspace_editing.py:module`
