# Dead code sweep ledger

The comparison starts at `ea6fab68b1c16b473e42bde8035bf6a20f045e70` on `origin/master`. Line counts use the original side of the Git diff, including replaced lines and adjoining blank lines. Locations refer to the baseline.

Vulture and Ruff (F401/F841) supplied Python leads. References were checked in source, tests, scripts, Qt forms, PyInstaller specs, CI, and docs. The R scan counted symbols across definitions and callers, including worker dispatch and test code. Script and fixture names were checked with `git grep` outside their own definitions. Workflow inputs were traced to their conditions and jobs. Artifact downloads and release evidence were checked against the producers.

## Deletions

| Path and symbol | Evidence | Lines removed |
| --- | --- | ---: |
| `.agents/skills/verify-rcms/features/README.md:R worker scenario parity claims` (line 11) | The drivers exercise the worker, public R calls and frozen contracts since #624. Embedded-backend parity no longer exists. | 1 |
| `.agents/skills/verify-rcms/references/lanes.md:package/bridge recovery instructions` (line 30) | The removed bridge suite is absent from the current verification lane. | 1 |
| `.agents/skills/verify-rcms/scripts/advanced_workflows.py:r_operations` (line 89) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `.agents/skills/verify-rcms/scripts/advanced_workflows.py:r_operations` (line 649) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `.agents/skills/verify-rcms/scripts/advanced_workflows.py:r_operations` (line 1005) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `.agents/skills/verify-rcms/scripts/advanced_workflows.py:r_operations` (line 1928) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `.agents/skills/verify-rcms/scripts/analysis_matrix.py:analysis_dataset` (line 84) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `.agents/skills/verify-rcms/scripts/analysis_matrix.py:heterogeneity` (line 826) | No reads of the binding. The required table lookup still fails if the table is missing. | 1 |
| `.agents/skills/verify-rcms/scripts/ratio_workflows.py:r_operations` (line 20) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `.agents/skills/verify-rcms/scripts/ratio_workflows.py:analysis_dataset` (line 23) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `.agents/skills/verify-rcms/scripts/ratio_workflows.py:QtCore` (line 526) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `.agents/skills/verify-rcms/scripts/ratio_workflows.py:r_operations` (line 529) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `.agents/skills/verify-rcms/scripts/sequential_workflows.py:r_operations` (line 12) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `.github/workflows/candidate.yml:macOS candidate diagnostic TOC paths` (line 218) | The removed TOC verifier and embedded-R adapter were the only automated TOC consumers. No current release job downloads or parses these TOCs. | 4 |
| `.github/workflows/package-target.yml:duplicate packaged smoke log glob` (line 136) | The qualification directory glob immediately above already uploads the same files. | 1 |
| `.github/workflows/package-target.yml:macOS diagnostic TOC paths` (line 139) | Same removed TOC consumer as the candidate workflow. The workflow still uploads the qualification evidence and PyInstaller warnings. | 4 |
| `config/r-dependencies.json:grDevices evidence for graphics.off` (line 226) | The obsolete graphics-off facade was the only call. Device-specific closing still uses dev.off. | 1 |
| `docs/maintaining.md:Full RCMetaR verification command comment` (line 128) | The full lane runs the worker and the golden/desktop checks. #624 removed the embedded bridge suite. | 1 |
| `docs/maintaining.md:tests/r_stack description` (line 184) | The retained test compares Reitsma output with public mada. Embedded serialization and NA tests were removed in #624. | 1 |
| `packaging/pyinstaller/rc-metastudio-linux.spec:r_home` (line 17) | Only the obsolete private-R binary filter read RCMS_R_HOME in the spec. | 1 |
| `packaging/pyinstaller/rc-metastudio-linux.spec:is_private_r_binary` (line 38) | No embedded R extension remains in the PyInstaller analysis graph. The package builder copies the worker runtime beside the app. | 5 |
| `packaging/pyinstaller/rc-metastudio-linux.spec:a.binaries R filter` (line 56) | Same obsolete embedded-library filter. The active exclusion of the incompatible Qt TIFF plugin remains. | 9 |
| `packaging/pyinstaller/rc-metastudio.spec:a.binaries R DLL filter` (line 61) | No embedded R extension remains in the PyInstaller analysis graph. The package builder stages R after PyInstaller. | 6 |
| `r/RCMetaR/NAMESPACE:rcmetar.get.mult.from.conf.level` (line 24) | Removed declaration for its uncalled R facade. | 1 |
| `r/RCMetaR/NAMESPACE:rcmetar.graphics.off` (line 25) | Removed declaration for its uncalled R facade. | 1 |
| `r/RCMetaR/NAMESPACE:rcmetar.method.description` (line 30) | Removed declaration for its uncalled R facade. | 1 |
| `r/RCMetaR/R/rcmetar-core.R:@aliases for removed exports` (line 58) | Documentation mirrored three exports with no worker, app, test, or shipped CLI callers. | 1 |
| `r/RCMetaR/R/rcmetar-core.R:rcmetar.method.description` (line 187) | Definition and documentation/export declarations only in tracked files. No worker, app, test, or shipped CLI caller. | 8 |
| `r/RCMetaR/R/rcmetar-core.R:rcmetar.get.mult.from.conf.level` (line 211) | Definition and documentation/export declarations only in tracked files. No worker, app, test, or shipped CLI caller. | 4 |
| `r/RCMetaR/R/rcmetar-core.R:rcmetar.graphics.off` (line 558) | Definition and documentation/export declarations only in tracked files. No worker, app, test, or shipped CLI caller. | 4 |
| `r/RCMetaR/inst/source.sha256:previous source stamp` (line 1) | Regenerated after the R package changes so the worker can authenticate installed source. | 1 |
| `r/RCMetaR/man/rcmetar-core-api.Rd:rcmetar.method.description` (line 13) | Removed declaration for its uncalled R facade. | 1 |
| `r/RCMetaR/man/rcmetar-core-api.Rd:rcmetar.get.mult.from.conf.level` (line 15) | Removed declaration for its uncalled R facade. | 1 |
| `r/RCMetaR/man/rcmetar-core-api.Rd:rcmetar.graphics.off` (line 36) | Removed declaration for its uncalled R facade. | 1 |
| `scripts/audit_dependency_versions.py:main` (line 1) | No tracked callers or operational references. The maintained manifest validator already reports installed R versions and the lock records Python versions. | 39 |
| `scripts/build-linux-package.sh:PyInstaller R environment` (line 164) | Only the removed spec filter required RCMS_R_HOME. R_HOME, R_LIBS, R_LIBS_USER and LD_LIBRARY_PATH are now scoped to the closure Rscript invocation. | 5 |
| `scripts/build-linux-package.sh:r-bundle-closure.R invocation` (line 181) | Scope the staged runtime environment to the Rscript call that consumes it. | 1 |
| `scripts/build-windows-package.ps1:previousAnalysisRHome and previousAnalysisPath` (line 592) | Only the old PyInstaller R environment override used this state. | 2 |
| `scripts/build-windows-package.ps1:PyInstaller R_HOME and PATH override` (line 595) | PyInstaller no longer loads an embedded bridge. R staging and package qualification have their own runtime setup. | 2 |
| `scripts/build-windows-package.ps1:PyInstaller R_HOME and PATH restoration` (line 622) | The removed PyInstaller overrides no longer mutate these variables. | 3 |
| `scripts/check_script_contracts.py:supported_flags, stale_calls, main` (line 1) | No tracked callers, CI step, or documentation entry for this one-off retired-flag scan. | 56 |
| `scripts/check_sheet_conversion.py:standalone v3 sheet conversion checker` (line 1) | No tracked caller outside its own docstring. Project-format snapshot tests and the sheets desktop scenarios continue to exercise historical projects and round trips. | 164 |
| `scripts/inspect_macos_deployment.py:_validate_preflight` (line 1845) | Definition only. #624 removed the PyInstaller R framework TOC verifier and its manifest input. | 22 |
| `scripts/inspect_macos_deployment.py:signing` (line 2002) | No reads of the result. The archive signing validator still runs and can reject invalid evidence. | 1 |
| `scripts/local_r_test_backend.py:create.AnalysisBackendUnavailableError` (line 18) | No production caller references this attribute through r_operations. Exceptions are owned by r_runtime. | 1 |
| `scripts/native_analysis_smoke.py:_install_backend_test_double` (line 77) | Both wrappers only called setattr. The native harnesses call setattr directly at the same test seam. | 7 |
| `scripts/native_analysis_smoke.py:_install_backend_test_double` (line 121) | Both wrappers only called setattr. The native harnesses call setattr directly at the same test seam. | 1 |
| `scripts/native_analysis_smoke.py:_install_backend_test_double` (line 136) | Both wrappers only called setattr. The native harnesses call setattr directly at the same test seam. | 1 |
| `scripts/native_analysis_smoke.py:_install_backend_test_double` (line 184) | Both wrappers only called setattr. The native harnesses call setattr directly at the same test seam. | 1 |
| `scripts/native_analysis_smoke.py:_install_backend_test_double` (line 273) | Both wrappers only called setattr. The native harnesses call setattr directly at the same test seam. | 1 |
| `scripts/native_calculator_smoke.py:_install_backend_test_double` (line 11) | Both wrappers only called setattr. The native harnesses call setattr directly at the same test seam. | 1 |
| `scripts/native_calculator_smoke.py:_install_backend_test_double` (line 37) | Both wrappers only called setattr. The native harnesses call setattr directly at the same test seam. | 7 |
| `scripts/native_calculator_smoke.py:dataset_table_model` (line 233) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `scripts/native_calculator_smoke.py:_install_backend_test_double` (line 243) | Both wrappers only called setattr. The native harnesses call setattr directly at the same test seam. | 1 |
| `scripts/native_calculator_smoke.py:_install_backend_test_double` (line 248) | Both wrappers only called setattr. The native harnesses call setattr directly at the same test seam. | 1 |
| `scripts/native_calculator_smoke.py:_install_backend_test_double` (line 265) | Both wrappers only called setattr. The native harnesses call setattr directly at the same test seam. | 1 |
| `scripts/native_calculator_smoke.py:_install_backend_test_double` (line 273) | Both wrappers only called setattr. The native harnesses call setattr directly at the same test seam. | 1 |
| `scripts/native_calculator_smoke.py:_install_backend_test_double` (line 283) | Both wrappers only called setattr. The native harnesses call setattr directly at the same test seam. | 1 |
| `scripts/native_calculator_smoke.py:_install_backend_test_double` (line 293) | Both wrappers only called setattr. The native harnesses call setattr directly at the same test seam. | 1 |
| `scripts/native_calculator_smoke.py:_install_backend_test_double` (line 298) | Both wrappers only called setattr. The native harnesses call setattr directly at the same test seam. | 1 |
| `scripts/process_groups.py:start_process` (line 5) | Its callers now enter owned_process. On Windows the job owns all descendants before process execution begins. | 1 |
| `scripts/process_groups.py:start_process` (line 17) | Its callers now enter owned_process. On Windows the job owns all descendants before process execution begins. | 1 |
| `scripts/process_groups.py:start_process` (line 23) | Its callers now enter owned_process. On Windows the job owns all descendants before process execution begins. | 2 |
| `scripts/process_groups.py:start_process` (line 29) | Its callers now enter owned_process. On Windows the job owns all descendants before process execution begins. | 1 |
| `scripts/process_groups.py:terminate_process_tree` (line 34) | Job close replaces the racy taskkill snapshot and keeps a bounded wait. POSIX still signals the process group. | 21 |
| `scripts/process_groups.py:terminate_process_tree` (line 58) | Job close replaces the racy taskkill snapshot and keeps a bounded wait. POSIX still signals the process group. | 3 |
| `scripts/process_groups.py:terminate_process_group wait` (line 81) | Job close replaces the racy taskkill snapshot and keeps a bounded wait. POSIX still signals the process group. | 1 |
| `scripts/r_verification_support.py:locked_python_versions import branches` (line 15) | No symbol reads in the helper. The packaging identity script still uses dependency_lock directly. | 6 |
| `scripts/relocate_macos_r_kit.py:direct R kit relocation CLI` (line 1) | No tracked callers following removal of integration-kit production in #624. The package builder uses relocate_macos_r_runtime.sh. | 121 |
| `scripts/run_bounded_process.py:run_bounded and _terminate_package_process` (line 75) | Both callers now use the shared ownership context. Package qualification still checks the process group and separately recorded PID on POSIX. | 6 |
| `scripts/run_bounded_process.py:run_bounded and _terminate_package_process` (line 82) | Both callers now use the shared ownership context. Package qualification still checks the process group and separately recorded PID on POSIX. | 1 |
| `scripts/run_bounded_process.py:run_bounded and _terminate_package_process` (line 88) | Both callers now use the shared ownership context. Package qualification still checks the process group and separately recorded PID on POSIX. | 1 |
| `scripts/run_bounded_process.py:run_bounded and _terminate_package_process` (line 91) | Both callers now use the shared ownership context. Package qualification still checks the process group and separately recorded PID on POSIX. | 1 |
| `scripts/run_bounded_process.py:run_bounded and _terminate_package_process` (line 95) | Both callers now use the shared ownership context. Package qualification still checks the process group and separately recorded PID on POSIX. | 1 |
| `scripts/run_bounded_process.py:run_bounded and _terminate_package_process` (line 97) | Both callers now use the shared ownership context. Package qualification still checks the process group and separately recorded PID on POSIX. | 3 |
| `scripts/run_with_timeout.py:start_process and terminate_process_tree` (line 12) | Both callers now use the shared ownership context. Package qualification still checks the process group and separately recorded PID on POSIX. | 1 |
| `scripts/run_with_timeout.py:start_process and terminate_process_tree` (line 14) | Both callers now use the shared ownership context. Package qualification still checks the process group and separately recorded PID on POSIX. | 1 |
| `scripts/run_with_timeout.py:start_process and terminate_process_tree` (line 27) | Both callers now use the shared ownership context. Package qualification still checks the process group and separately recorded PID on POSIX. | 1 |
| `scripts/run_with_timeout.py:start_process and terminate_process_tree` (line 29) | Both callers now use the shared ownership context. Package qualification still checks the process group and separately recorded PID on POSIX. | 1 |
| `scripts/run_with_timeout.py:start_process and terminate_process_tree` (line 37) | Both callers now use the shared ownership context. Package qualification still checks the process group and separately recorded PID on POSIX. | 1 |
| `scripts/run_with_timeout.py:start_process and terminate_process_tree` (line 39) | Both callers now use the shared ownership context. Package qualification still checks the process group and separately recorded PID on POSIX. | 3 |
| `scripts/verify-archive-windows.ps1:standalone Authenticode-and-ZIP CLI` (line 1) | No tracked callers or docs. The Windows package script builds and qualifies its exact ZIP through the deployment inspector and packaged application. | 15 |
| `scripts/verify.py:time` (line 17) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `scripts/verify_golden_compatibility.py:cast` (line 18) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `src/rc_metastudio/analysis/small_study_effects.py:Literal` (line 18) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `src/rc_metastudio/calculators/binary_dialog.py:is_empty` (line 30) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `src/rc_metastudio/calculators/continuous_dialog.py:is_empty` (line 38) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `src/rc_metastudio/calculators/diagnostic_dialog.py:is_empty` (line 30) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 2 |
| `src/rc_metastudio/cocoa_accessibility.py:find_accessibility_element, bounded_error_message` (line 1) | No imports of the module or callers of either symbol in tracked files, including frozen package specs. | 72 |
| `tests/analysis_regression/golden/test_analysis_regression_compare.py:_text_result and verify_rcmetar_r_stack` (line 33) | No callers of the test helper or references to the imported verifier following #624. | 17 |
| `tests/analysis_regression/golden/test_analysis_regression_compare.py:analysis_catalog` (line 983) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/analysis_regression/golden/test_analysis_regression_compare.py:_headless, _globals` (line 1336) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 2 |
| `tests/analysis_regression/golden/test_analysis_regression_compare.py:_headless, _globals` (line 1346) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 2 |
| `tests/e2e/analysis_presentation_workflows.py:patch` (line 9) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/analysis_presentation_workflows.py:r_operations` (line 121) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/analysis_presentation_workflows.py:r_operations` (line 254) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/analysis_presentation_workflows.py:r_operations` (line 510) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/analysis_result_checks.py:r_operations` (line 71) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/analysis_result_checks.py:r_operations` (line 99) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/analysis_settings_workflows.py:r_operations` (line 19) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/axis_conventions.py:r_operations` (line 98) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/axis_conventions.py:analysis_dataset, r_operations` (line 209) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 2 |
| `tests/e2e/desktop_driver.py:r_operations` (line 574) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/desktop_driver.py:r_operations` (line 835) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/desktop_driver.py:r_operations` (line 1686) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/desktop_driver.py:QTest` (line 2111) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/dta_audit.py:r_operations` (line 17) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/entered_ci.py:r_operations` (line 9) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/forest_colour_exports.py:r_operations` (line 56) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/forest_group_labels.py:r_operations` (line 18) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/forest_prediction_intervals.py:r_operations` (line 17) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/large_forest_export.py:r_oracle` (line 3) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/mean_metric_migration.py:r_operations` (line 94) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/plot_geometry_checks.py:r_operations` (line 130) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/plot_geometry_checks.py:r_operations` (line 195) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/plot_observations.py:r_operations` (line 7) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/polish_journeys.py:r_operations` (line 119) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/published_samples.py:r_operations` (line 11) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/r_worker_plot_files.py:Path` (line 5) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/ratio_precision.py:r_operations` (line 17) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/reitsma_coefficient_axes.py:r_operations` (line 16) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/trial_sequential_workflows.py:sys` (line 5) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/trial_sequential_workflows.py:r_worker` (line 17) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/trial_sequential_workflows.py:TsaService` (line 25) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/trimfill_geometry.py:re` (line 2) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/ui_design_direction.py:overflow` (line 181) | No reads of the binding. The required toolbar extension lookup still runs. | 1 |
| `tests/e2e/ui_fine_tuning.py:QtWidgets` (line 2) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/ui_fine_tuning.py:mouse_click` (line 7) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/e2e/ux_workflows.py:row_bottom` (line 323) | No reads of the mapped coordinate. The scenario checks the full row rectangle against the viewport. | 1 |
| `tests/fit_observations.py:uuid4` (line 9) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/mutants/ci-z-instead-of-t.patch:CI distribution mutation patch` (line 1) | No tracked caller, fixture loader, or mutation workflow. | 11 |
| `tests/mutants/xlsx-year-column.patch:XLSX year-column mutation patch` (line 1) | No tracked caller, fixture loader, or mutation workflow. | 11 |
| `tests/python/fast/test_calculator_qt6.py:calculator_controls` (line 38) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/fast/test_calculator_qt6.py:calculator_edit_history, calculator_effect_readout` (line 337) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 2 |
| `tests/python/fast/test_calculator_qt6.py:calculator_edit_history, calculator_effect_readout` (line 348) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 2 |
| `tests/python/fast/test_calculator_qt6.py:calculator_controls` (line 653) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/fast/test_calculator_qt6.py:calculator_controls, calculator_edit_history` (line 810) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 2 |
| `tests/python/fast/test_calculator_qt6.py:calculator_edit_history` (line 968) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/fast/test_calculator_qt6.py:calculator_edit_history` (line 1037) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/fast/test_main_workspace_policy.py:analysis_dataset` (line 203) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/fast/test_mean_metric_migration.py:JsonValue` (line 12) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/fast/test_qt6_build_slice.py:test_timeout_runner_reports_taskkill_failure` (line 503) | The production watchdog no longer invokes taskkill. The replacement test observes the lifetime of a real Windows descendant. | 16 |
| `tests/python/fast/test_verification_contracts.py:r_verification_support` (line 11) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/fast/test_workspace_editing.py:dataclass` (line 4) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/fast/test_workspace_editing.py:Study` (line 28) | No callers of this local fixture dataclass. Test constructs StudyRow and AnalysisUnit directly. | 6 |
| `tests/python/gui/test_analysis_configuration_layout.py:backend` (line 726) | No reads of the alias. The analysis backend test patch remains active. | 1 |
| `tests/python/gui/test_analysis_failure_safety.py:SimpleNamespace` (line 5) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_compact_transient_layout.py:_frame_margins` (line 24) | Only called by the unused size assertion helper below. | 10 |
| `tests/python/gui/test_compact_transient_layout.py:_assert_content_preferred_outer_size` (line 39) | Definition only. Active layout tests assert actual observed sizes through their own checks. | 16 |
| `tests/python/gui/test_continuous_data_transactional_layout.py:FakeContinuousAnalysisUnit.get_effect_names` (line 47) | Definition only in the repository. The real calculator consults Sheet metrics. | 3 |
| `tests/python/gui/test_csv_import_wizard.py:QtCore` (line 11) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:TYPE_CHECKING` (line 6) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:Ui_AnalysisSetupDialog` (line 21) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 5 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 400) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 902) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 1020) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 1093) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 1167) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 1260) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 1350) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 1402) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 1460) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 1491) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 1527) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 1561) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 1614) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 1798) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 1920) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:QApplication` (line 2318) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:app` (line 2323) | No reads of the local QApplication in this project conversion test. The shared test fixture owns QApplication when needed. | 1 |
| `tests/python/gui/test_main_window_automation_launch.py:r_operations` (line 2353) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_main_wizard_workflow_layout.py:adaptive_window` (line 18) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/python/gui/test_qt6_application_shell.py:main_window` (line 618) | No reads of the loaded-module alias. The test still exercises the window created by automation. | 1 |
| `tests/python/gui/test_qt6_application_shell.py:settings` (line 731) | Unused import in this scope (Ruff F401, checked against the surrounding code and callers). | 1 |
| `tests/r_stack/_r_driver_support.py:embedded-Python driver imports` (line 10) | Only used by run_python_driver below. | 5 |
| `tests/r_stack/_r_driver_support.py:run_python_driver, RCMS_DRIVER_OWNED_CWD, RCMS_SUMMARY_OWNED_LIBRARY` (line 53) | No callers since #624 deleted the in-process R tests. The current Reitsma test uses run_r_driver. | 48 |
| `tests/r_stack/test_reitsma_mada_authority.py:REPO_ROOT calculation` (line 10) | Reuse REPO_ROOT from the shared R driver, which already resolves the same repository path. | 1 |
| `tests/r_stack/test_reitsma_mada_authority.py:REPO_ROOT calculation` (line 13) | Reuse REPO_ROOT from the shared R driver, which already resolves the same repository path. | 1 |
| `tests/r_stack/test_reitsma_mada_authority.py:REPO_ROOT calculation` (line 155) | Reuse REPO_ROOT from the shared R driver, which already resolves the same repository path. | 1 |
| `tests/r_stack/test_reitsma_mada_authority.py:env` (line 159) | No reads of the copied process environment. run_r_driver inherits the environment directly. | 1 |

**Total: 180 deletion entries, 899 removed diff lines.**

## Reviewed and kept

| Path and symbol | Evidence |
| --- | --- |
| `src/rc_metastudio/project/migration.py, project/archive.py` | Old .rcms versions are read by the application. Saved-project fixtures and the sheets legacy drive exercise the migration. |
| `src/rc_metastudio/main_wizard.py:_legacy_header_aliases, workspace/columns.py:legacy_label` | Old CSV/Excel headers and metric spellings are accepted by real import paths. |
| `src/rc_metastudio/settings.py:LEGACY_MAIN_WINDOW_GROUP` | Existing installs have the old QSettings key. The layout settings migration clears that key without clearing other settings. |
| `src/rc_metastudio/adaptive_controls.py:choice_controller and dialog scroll filters` | The retained Qt objects keep Python implementations reachable across Qt callbacks. A read of the attribute is unnecessary. |
| `src/rc_metastudio/calculators/controls.py:PrevalenceEdit` | diagnostic_data_dialog.ui declares it as a custom widget. The generated form imports it. |
| `src/rc_metastudio/calculators/*_dialog.py:previousRow, previousColumn` | Qt item-change callback signatures include the previous coordinates. Keeping the signature preserves the Qt slot contract. |
| `src/rc_metastudio/r_worker.py:protocol and results/contract.py:image_var_names` | The TypedDict fields describe decoded worker frames and results. Static attribute reference counts miss string-keyed data. |
| `src/rc_metastudio/analysis/small_study_effects.py:enum members and plotting options` | Values are selected by serialized enum values and sent in dataclass request payloads. |
| `packaging/pyinstaller/generated_ui_collection.py:APPLICATION_HIDDEN_IMPORTS, APPLICATION_EXCLUDES, application_data, pyinstaller_module_entries` | Windows, macOS and Linux specs load the module through importlib and call these declarations. |
| `packaging/pyinstaller/direct-r-spike.marker` | The macOS spec copies the marker. The archive inspector verifies its path and digest. |
| `scripts/configure_macos_r_launchers.py:normalize_fontconfig_links` | The macOS shell build imports and calls it from a Python heredoc. |
| `scripts/verify_golden_compatibility.py:_capture_main` | The golden verifier imports it in a bounded Python subprocess using a command string. |
| `scripts/generate_forest_plot_defaults.py, generate_dataset_type_icons.py, generate_functional_icons.py, regenerate-rc-metastudio-icon.py, build_splash_artwork.py` | These maintainer entry points reproduce committed defaults and shipped artwork. Their consumers use the generated outputs and do not run the generators at startup. |
| `scripts/index_r_binary_archives.py` | Maintainer CLI for recording binary and licence provenance from retained PPM archives. |
| `scripts/desktop_worker_capacity.py:desktop_resources` | The pytest-xdist desktop hook imports it to size the local worker pool. |
| `scripts/verify_packaged_summary_identity.py:capture_source_summary` | The pinned-runtime test verifies both packaged sample hashes against a source capture. |
| `r/RCMetaR/R/permutation.R, rcmetar.run.permutation` | The documented R package permutation feature has numerical and rendering contract coverage in test-rendering-options.R. |
| `r/RCMetaR/R/rcmetar-core.R:rcmetar.analysis.methods, rcmetar.method.references` | Registry validation and statistical result references call these functions inside the R package. |
| `r/RCMetaR/inst/worker.R:jsonlite` | The standalone worker reads and writes framed JSON. PR #625 owns the package declaration and Homebrew cleanup. |
| `tests/python/fixtures/project_snapshots/*.rcms.json, tests/fixtures/legacy-projects/*.rcms` | Project snapshots are selected by filename construction. The sheets legacy drive opens saved fixtures and reopens converted copies. |
| `tests/conftest.py, tests/e2e/conftest.py, tests/python/conftest.py:pytest fixtures and hooks` | pytest discovers hooks and injects fixture arguments. Several fixtures exist for setup, isolation, or teardown side effects. |
| `tests/e2e/desktop_driver.py:scenario functions` | The desktop registry dispatches scenario functions through string references. |
| `.github/workflows/candidate.yml:historical setup and recorder paths` | The release guide allows older protected-master source SHAs. The candidate workflow checks out that SHA, where setup and recorder paths legitimately differ. |
| `.github/workflows/*:published evidence and workflow inputs` | Inputs have workflow conditions or consumers. Retained artifacts either feed another job or preserve qualification evidence for release or failure review. |
| `docs/adr/0012-supervise-a-persistent-r-worker.md and CHANGELOG.md:embedded-R history` | This material records why the worker replaced embedded R and which historical versions used it. |

**Total: 25 retained entries.**
