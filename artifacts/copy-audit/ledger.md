# Copy audit ledger

Base: 7dec12db. Entries are keyed by row number in Gemini’s replacements.csv. File and line refer to the audit location.

Totals: 375 applied, 53 changed, 59 skipped. The table includes all 33 meaning-change verdicts.

| # | Audit location | Outcome | Reason / meaning-change verdict |
|---:|---|---|---|
| 1 | `r/RCMetaR/R/binary_methods.R:175` | changed | **Meaning:** Verified only0, if0all, all and none in analysis_contracts.R and the method metadata. Used the actual displayed label "No studies". |
| 2 | `r/RCMetaR/R/binary_methods.R:287` | changed | **Meaning:** Verified only0, if0all, all and none in analysis_contracts.R and the method metadata. Used the actual displayed label "No studies". |
| 3 | `r/RCMetaR/R/binary_methods.R:401` | changed | **Meaning:** Verified only0, if0all, all and none in analysis_contracts.R and the method metadata. Used the actual displayed label "No studies". |
| 4 | `r/RCMetaR/R/binary_methods.R:497` | changed | **Meaning:** Verified only0, if0all, all and none in analysis_contracts.R and the method metadata. Used the actual displayed label "No studies". |
| 5 | `r/RCMetaR/R/continuous_methods.R:115` | changed | **Meaning:** Continuous mean and coefficient fits do not use a 2 × 2 table. This legacy metadata does not drive the continuous model fit. Avoided claiming these settings adjust continuous values. |
| 6 | `r/RCMetaR/R/continuous_methods.R:213` | changed | **Meaning:** Continuous mean and coefficient fits do not use a 2 × 2 table. This legacy metadata does not drive the continuous model fit. Avoided claiming these settings adjust continuous values. |
| 7 | `r/RCMetaR/R/diagnostic_methods.R:236` | changed | **Meaning:** Verified only0, if0all, all and none in analysis_contracts.R and the method metadata. Used the actual displayed label "No studies". |
| 8 | `r/RCMetaR/R/diagnostic_methods.R:337` | changed | **Meaning:** Verified only0, if0all, all and none in analysis_contracts.R and the method metadata. Used the actual displayed label "No studies". |
| 9 | `r/RCMetaR/R/diagnostic_methods.R:444` | changed | **Meaning:** Verified only0, if0all, all and none in analysis_contracts.R and the method metadata. Used the actual displayed label "No studies". |
| 10 | `r/RCMetaR/R/diagnostic_methods.R:540` | changed | **Meaning:** Verified only0, if0all, all and none in analysis_contracts.R and the method metadata. Used the actual displayed label "No studies". |
| 11 | `src/rc_metastudio/forms/main_window.ui:122` | applied | **Meaning:** False tooltip: menuMetric only lists effect measures (Study calculator lives under Edit), and uses 'metric' instead of CONTEXT.md term 'effect measure'. |
| 12 | `src/rc_metastudio/forms/main_window.ui:123` | applied | **Meaning:** False status tip: menuMetric only lists effect measures (Study calculator lives under Edit), and uses 'metric' instead of CONTEXT.md term 'effect measure'. |
| 13 | `src/rc_metastudio/forms/main_window.ui:120` | applied | **Meaning:** Menu title promises 'tools', but the menu only switches the outcome's effect measure; align with CONTEXT.md term 'Effect measure'. |
| 14 | `r/RCMetaR/R/trial_sequential_analysis.R:275` | changed | **Meaning:** The input resolver emits exactly one of these two keys. Preserved required.inputs for the bridge and changed only the reason. |
| 15 | `src/rc_metastudio/analysis/identity.py:110` | changed | **Meaning:** Context is empty for the default single arm and nonempty for a custom name or comparison. Only omit the empty line. |
| 16 | `src/rc_metastudio/results/report.py:1059` | skipped | **Meaning:** Moderators are already a display string from R, and names can contain commas. The proposed helper is undefined. Avoided guessing list boundaries. |
| 17 | `src/rc_metastudio/results/report.py:58` | applied | Tense shift inside a single Methods sentence ('was applied... uses') visible in 091-mh-methods-zero-cell-rule.png; use past tense consistently. |
| 18 | `src/rc_metastudio/results/report.py:961` | applied | Present tense inside past-tense TSA Results section (adjacent sentence: 'The conventional estimate was...'); align to past tense. |
| 19 | `r/RCMetaR/R/diagnostic_methods.R:182` | applied | Leading space and missing space after ASCII hyphen produces ' Sensitivity -Model Results'; use clean em dash spacing. |
| 20 | `r/RCMetaR/R/diagnostic_methods.R:282` | applied | Leading space and missing space after ASCII hyphen produces ' Sensitivity -Model Results'; use clean em dash spacing. |
| 21 | `r/RCMetaR/R/diagnostic_methods.R:384` | applied | Leading space and missing space after ASCII hyphen produces ' Sensitivity -Model Results'; use clean em dash spacing. |
| 22 | `r/RCMetaR/R/diagnostic_methods.R:482` | applied | Missing space after ASCII hyphen produces 'Sensitivity -Model Results'; use clean em dash spacing. |
| 23 | `r/RCMetaR/R/forest_summary.R:316` | changed | **Meaning:** The branch formats a non-finite P value. Missing inferential output does not establish that a statistic is impossible to estimate. |
| 24 | `src/rc_metastudio/results/plot_text.py:26` | changed | **Meaning:** This shared configurator covers axis and forest heading fields. Only automatic arm headings have the stated wrapping guarantee. |
| 25 | `src/rc_metastudio/results/plot_text.py:42` | changed | **Meaning:** The phrase is appended every time an automatic value is loaded. A different append string would still repeat it. Removed the append separately and set the automatic help only on fields without help. |
| 26 | `src/rc_metastudio/importing/tabular.py:445` | changed | Used a count label to avoid plural agreement and a new branch. Grammar bug: outputs '1 formula cells use their saved values.' when one formula cell is present. |
| 27 | `src/rc_metastudio/results/report.py:675` | changed | **Meaning:** These calls construct pooled tables, which should still say Effect. Set Term on the coefficient table in _regression_section instead. |
| 28 | `src/rc_metastudio/results/report.py:677` | changed | **Meaning:** These calls construct pooled tables, which should still say Effect. Set Term on the coefficient table in _regression_section instead. |
| 29 | `src/rc_metastudio/forms/main_window.ui:14` | applied | Missing space in product name ('RCMetaStudio') contradicts CONTEXT.md ('RC MetaStudio') and causes Qt to append ' - RC MetaStudio' creating a doubled title. |
| 30 | `src/rc_metastudio/main_wizard.py:1077` | applied | Missing space in wizard window title causes 'RCMetaStudio - RC MetaStudio' in 142-native-csv-wizard.png and 217-xlsx-95-study-preview.png. |
| 31 | `src/rc_metastudio/application_metadata.py:8` | skipped | Qt application identity is used for app paths and settings. Visible titles use the spaced name. |
| 32 | `src/rc_metastudio/about_legal_dialog.py:46` | applied | Unexpanded 'RCMS' abbreviation; also causes Qt to render 'About RCMS - RC MetaStudio' in 003-about-open.png. |
| 33 | `src/rc_metastudio/main_window.py:378` | applied | Use full product name 'RC MetaStudio' rather than unexpanded 'RCMS' in Help menu. |
| 34 | `src/rc_metastudio/forms/choose_metric_page.ui:20` | applied | Untranslated Qt Designer placeholder 'WizardPage' exposed to screen readers and window accessibility trees. |
| 35 | `src/rc_metastudio/forms/csv_import_page.ui:13` | applied | Untranslated Qt Designer placeholder 'WizardPage' exposed to screen readers and window accessibility trees. |
| 36 | `src/rc_metastudio/forms/data_type_page.ui:20` | applied | Untranslated Qt Designer placeholder 'WizardPage' exposed to screen readers and window accessibility trees. |
| 37 | `src/rc_metastudio/forms/welcome_page.ui:20` | applied | Untranslated Qt Designer placeholder 'WizardPage' exposed to screen readers and window accessibility trees. |
| 38 | `src/rc_metastudio/forms/results_window.ui:37` | changed | Placeholder is a QTreeWidget header. The visible forest and report nodes are populated programmatically. |
| 39 | `src/rc_metastudio/main_window.py:159` | applied | **Meaning:** Progress dialog says 'Import CSV' even when importing Excel (.xlsx) or RevMan (.rm5) files. |
| 40 | `src/rc_metastudio/main_wizard.py:527` | applied | **Meaning:** Accessible name says 'CSV' even when mapping columns of an Excel (.xlsx) workbook. |
| 41 | `src/rc_metastudio/main_wizard.py:540` | applied | **Meaning:** Accessible name says 'CSV' even when previewing an Excel (.xlsx) workbook. |
| 42 | `src/rc_metastudio/main_wizard.py:736` | applied | **Meaning:** Says 'CSV header' even when the user imported an Excel (.xlsx) file. |
| 43 | `src/rc_metastudio/main_wizard.py:880` | applied | **Meaning:** Accessible name says 'CSV column' even when mapping an Excel (.xlsx) file. |
| 44 | `src/rc_metastudio/importing/tabular.py:125` | applied | **Meaning:** Says 'CSV file' even when raised during Excel (.xlsx) import. |
| 45 | `src/rc_metastudio/importing/tabular.py:182` | changed | **Meaning:** The reader rejects extra fields only. The shared parser can receive Excel cells, so CSV-specific comma advice is unreliable. |
| 46 | `src/rc_metastudio/importing/tabular.py:192` | applied | **Meaning:** Says 'CSV column' even when mapping an Excel (.xlsx) file. |
| 47 | `src/rc_metastudio/importing/tabular.py:194` | applied | **Meaning:** Says 'CSV column' even when mapping an Excel (.xlsx) file. |
| 48 | `src/rc_metastudio/importing/tabular.py:212` | applied | **Meaning:** Says 'CSV' even for Excel imports and adds clear action. |
| 49 | `src/rc_metastudio/importing/tabular.py:237` | changed | **Meaning:** The import wizard uses a mapping panel, not a tab named Map columns. |
| 50 | `src/rc_metastudio/importing/tabular.py:245` | changed | **Meaning:** The old text is split across adjacent f-strings. The positional validation requires the minimum column count and is shared with spreadsheets. Updated both literal fragments. |
| 51 | `src/rc_metastudio/forms/publication_bias_dialog.ui:26` | applied | Exposes implementation term 'Package default'; label by user-facing behavior. |
| 52 | `src/rc_metastudio/forms/publication_bias_dialog.ui:26` | changed | Kept the default dynamic and did not claim a fixed threshold across methods. |
| 53 | `src/rc_metastudio/forms/publication_bias_dialog.ui:27` | applied | Exposes internal R package name ('meta') and 'The package' in tooltip. |
| 54 | `src/rc_metastudio/results/report.py:564` | changed | Used natural wording for not estimable. |
| 55 | `src/rc_metastudio/results/report.py:1068` | applied | Replaces developer-facing 'where the package reports it' and standardizes apostrophe. |
| 56 | `src/rc_metastudio/project/archive.py:247` | applied | Leaks container implementation ('ZIP container') in user-visible error dialog (139-corrupt-project-error.png). |
| 57 | `src/rc_metastudio/main_window.py:133` | changed | Kept the underlying exception message and removed the class name. The cause is not necessarily a missing or locked file. |
| 58 | `src/rc_metastudio/main_window.py:487` | changed | The original message is split across adjacent literals. Updated both fragments and removed the exception class. |
| 59 | `src/rc_metastudio/main_window.py:871` | applied | Drops Python exception class name from user-facing R startup error. |
| 60 | `src/rc_metastudio/main_window.py:878` | applied | Drops Python exception class name from analysis preparation error. |
| 61 | `src/rc_metastudio/main_window.py:969` | applied | Drops Python exception class name from results display error. |
| 62 | `src/rc_metastudio/main_window.py:1567` | changed | Kept the underlying exception message. Permissions and disk space are not the only possible causes. |
| 63 | `src/rc_metastudio/analysis/setup_dialog.py:968` | applied | Drops Python exception class name from technical error details pane. |
| 64 | `src/rc_metastudio/app_error_handler.py:13` | applied | Replaces developer-centric 'Unexpected error' dialog title with plain, calm heading. |
| 65 | `src/rc_metastudio/importing/revman.py:230` | changed | IPD is an XML tag tested against the RevMan document. Expanded only the displayed warning. |
| 66 | `r/RCMetaR/R/ratio_methods.R:252` | changed | Kept the scope of the correction and used two short sentences. |
| 67 | `r/RCMetaR/R/reitsma_methods.R:40` | applied | Replaces raw R package name 'mada' in user-facing error detail. |
| 68 | `r/RCMetaR/R/reitsma_methods.R:59` | applied | Replaces raw S4 class name 'DiagnosticData' in error message. |
| 69 | `r/RCMetaR/R/reitsma_methods.R:104` | applied | Replaces raw package name 'mada' with plain statistical wording. |
| 70 | `r/RCMetaR/R/reitsma_methods.R:123` | applied | Replaces raw package/internal coefficient wording with plain statistical wording. |
| 71 | `r/RCMetaR/R/reitsma_methods.R:129` | applied | Replaces raw package/internal wording with plain statistical wording. |
| 72 | `r/RCMetaR/R/reitsma_methods.R:161` | applied | Removes internal R package name 'mada' and 'output fields'. |
| 73 | `r/RCMetaR/R/reitsma_methods.R:644` | applied | Removes internal R package name 'mada'. |
| 74 | `r/RCMetaR/R/reitsma_methods.R:782` | applied | Removes raw package name 'mada' from warning prefix. |
| 75 | `r/RCMetaR/R/reitsma_methods.R:783` | applied | Removes raw package name 'mada' from warning prefix. |
| 76 | `r/RCMetaR/R/reitsma_methods.R:1004` | skipped | The explicit mada version identifies the authority for this model. Preserved its provenance. |
| 77 | `r/RCMetaR/R/trial_sequential_analysis.R:312` | applied | Removes internal R package name 'gsDesign' from user-facing error. |
| 78 | `r/RCMetaR/R/small_study_effects.R:403` | skipped | These technical details identify the statistical authority, regression predictor, or weights. The proposed wording removes that provenance or precision. |
| 79 | `r/RCMetaR/R/small_study_effects.R:450` | skipped | These technical details identify the statistical authority, regression predictor, or weights. The proposed wording removes that provenance or precision. |
| 80 | `r/RCMetaR/R/small_study_effects.R:494` | skipped | These technical details identify the statistical authority, regression predictor, or weights. The proposed wording removes that provenance or precision. |
| 81 | `r/RCMetaR/R/small_study_effects.R:495` | skipped | These technical details identify the statistical authority, regression predictor, or weights. The proposed wording removes that provenance or precision. |
| 82 | `r/RCMetaR/R/small_study_effects.R:496` | skipped | These technical details identify the statistical authority, regression predictor, or weights. The proposed wording removes that provenance or precision. |
| 83 | `r/RCMetaR/R/small_study_effects.R:497` | skipped | These technical details identify the statistical authority, regression predictor, or weights. The proposed wording removes that provenance or precision. |
| 84 | `r/RCMetaR/R/small_study_effects.R:23` | changed | Preserved the accepted lower bound. |
| 85 | `r/RCMetaR/R/small_study_effects.R:260` | applied | Replaces raw R parameter identifier 'conf.level' with UI label. |
| 86 | `r/RCMetaR/R/small_study_effects.R:263` | applied | Replaces raw R parameter identifier 'conf.level' with UI label. |
| 87 | `r/RCMetaR/R/rcmetar-core.R:728` | applied | Replaces raw S4 class name 'DiagnosticData'. |
| 88 | `r/RCMetaR/R/rcmetar-core.R:943` | applied | Replaces raw S4 class names with user-facing data types. |
| 89 | `r/RCMetaR/R/rcmetar-core.R:985` | applied | Replaces internal parameter/class names ('cov_name', 'CovariateValues') with actionable guidance. |
| 90 | `r/RCMetaR/R/plotting.R:209` | applied | Removes internal R package/class names ('metafor rma'). |
| 91 | `r/RCMetaR/R/plotting.R:387` | applied | Removes internal wording ('metafor-backed plot bundle'). |
| 92 | `r/RCMetaR/R/rcmetar-core.R:523` | applied | Removes internal R package/class names ('metafor rma'). |
| 93 | `r/RCMetaR/R/rcmetar-core.R:544` | applied | Removes internal wording ('metafor render bundle'). |
| 94 | `r/RCMetaR/R/permutation.R:39` | applied | Removes internal phrasing ('Pinned metafor'). |
| 95 | `r/RCMetaR/R/small_study_effects.R:601` | skipped | The proposed helper does not exist. The existing helper already supplies the percentage and also labels confidence intervals elsewhere. |
| 96 | `r/RCMetaR/R/small_study_effects.R:605` | changed | The proposed fragment would leave an unfinished expression and round exact endpoints. Changed range punctuation only. |
| 97 | `src/rc_metastudio/results/plot_export.py:177` | applied | Add thousands separators for large raster dimensions (e.g., '9,172 × 19,584 pixels' instead of '9172 × 19584 pixels' in 294-hr-sized-export-settings.png). |
| 98 | `src/rc_metastudio/results/plot_export.py:88` | applied | Align terminology with Edit plot ('Figure caption') so the same text line is not called 'Figure caption' in one dialog and 'title line' in another. |
| 99 | `src/rc_metastudio/results/window.py:1775` | changed | Changed only the string in the shared export-dialog area. |
| 100 | `src/rc_metastudio/analysis/setup_dialog.py:449` | applied | Removes ALL CAPS shouting. |
| 101 | `src/rc_metastudio/covariate_type_dialog.py:232` | applied | Vague error does not tell the user why the cell cannot be edited or which column is editable. |
| 102 | `src/rc_metastudio/workspace/editing.py:259` | changed | This rejection is reached with no outcome or a negative row, not for a calculated cell. |
| 103 | `src/rc_metastudio/workspace/editing.py:299` | applied | Explains why the cell cannot be edited while keeping row and column identification. |
| 104 | `src/rc_metastudio/workspace/table_model.py:533` | changed | The selected column has no editable field, which does not guarantee calculator availability. |
| 105 | `src/rc_metastudio/workspace/table_model.py:555` | changed | This rejection is for an invalid model index. |
| 106 | `src/rc_metastudio/workspace/editing.py:556` | applied | Removes second-person blame ('You have already...') and replaces 'outcome' (sheet concept) with 'effect estimate' and 'raw data' with 'arm data'. |
| 107 | `src/rc_metastudio/calculators/binary_dialog.py:1158` | skipped | Old literal no longer exists at this surface in current HEAD. |
| 108 | `src/rc_metastudio/forms/binary_back_calculation_dialog.ui:15` | applied | Tighter, calmer phrasing matching binary_dialog.py. |
| 109 | `src/rc_metastudio/main_window.py:603` | changed | The shared error surface covers study edits and rejected clipboard data. Generic 'Warning' QMessageBox title; name the problem. |
| 110 | `src/rc_metastudio/main_window.py:991` | applied | Generic 'Warning' QMessageBox title; name the problem. |
| 111 | `src/rc_metastudio/main_window.py:1005` | applied | Generic 'Warning' QMessageBox title; name the problem. |
| 112 | `src/rc_metastudio/main_window.py:1144` | applied | Generic 'Warning' QMessageBox title; name the problem. |
| 113 | `src/rc_metastudio/covariate_type_dialog.py:67` | applied | Generic 'Warning' QMessageBox title; name the problem. |
| 114 | `src/rc_metastudio/calculators/binary_dialog.py:714` | applied | Generic 'Warning' QMessageBox title; name the problem. |
| 115 | `src/rc_metastudio/calculators/binary_dialog.py:879` | applied | Generic 'Warning' QMessageBox title; name the problem. |
| 116 | `src/rc_metastudio/calculators/binary_dialog.py:891` | applied | Generic 'Warning' QMessageBox title; name the problem. |
| 117 | `src/rc_metastudio/calculators/continuous_dialog.py:607` | applied | Generic 'Warning' QMessageBox title; name the problem. |
| 118 | `src/rc_metastudio/calculators/continuous_dialog.py:823` | applied | Generic 'Warning' QMessageBox title; name the problem. |
| 119 | `src/rc_metastudio/calculators/continuous_dialog.py:834` | applied | Generic 'Warning' QMessageBox title; name the problem. |
| 120 | `src/rc_metastudio/calculators/continuous_dialog.py:1096` | applied | Generic 'Warning' QMessageBox title; name the problem. |
| 121 | `src/rc_metastudio/calculators/diagnostic_dialog.py:503` | applied | Generic 'Warning' QMessageBox title; name the problem. |
| 122 | `src/rc_metastudio/calculators/diagnostic_dialog.py:516` | applied | Generic 'Warning' QMessageBox title; name the problem. |
| 123 | `src/rc_metastudio/calculators/diagnostic_dialog.py:730` | applied | Generic 'Warning' QMessageBox title; name the problem. |
| 124 | `src/rc_metastudio/start_page.py:48` | applied | Add serial comma (consistent with US scientific prose and CONTEXT.md). |
| 125 | `src/rc_metastudio/start_page.py:55` | applied | Action opens the New project wizard; add trailing ellipsis (matches File > New project…). |
| 126 | `src/rc_metastudio/start_page.py:56` | applied | Action opens the Import data wizard; add trailing ellipsis (matches File > Import data… and welcome_page.ui). |
| 127 | `src/rc_metastudio/start_page.py:57` | applied | Action opens the file picker dialog; add trailing ellipsis (matches welcome_page.ui). |
| 128 | `src/rc_metastudio/forms/welcome_page.ui:58` | applied | Button advances to project setup wizard pages; align ellipsis with sibling buttons. |
| 129 | `src/rc_metastudio/main_wizard.py:533` | applied | Button opens a Save file dialog; add trailing ellipsis. |
| 130 | `src/rc_metastudio/results/window.py:899` | applied | Add serial comma and terminal period (matches sentence-form tooltips). |
| 131 | `src/rc_metastudio/results/plot_editor.py:170` | applied | Add serial comma. |
| 132 | `src/rc_metastudio/results/window.py:343` | applied | Add serial comma and align 'data tables' with sidebar label. |
| 133 | `src/rc_metastudio/results/window.py:345` | applied | Add serial comma. |
| 134 | `src/rc_metastudio/workspace/table_view.py:78` | applied | Add serial comma. |
| 135 | `src/rc_metastudio/forms/publication_bias_dialog.ui:41` | applied | Combo values are bare numbers (90, 95, 99) with no '%' unit (visible in 125-small-study-setup-ready.png). |
| 136 | `src/rc_metastudio/forms/publication_bias_dialog.ui:44` | applied | Line edit values are bare numbers ('90, 95, 99'); align with funnel_plot_editor_dialog.ui ('Null contour levels (%)'). |
| 137 | `src/rc_metastudio/analysis/trial_sequential.py:25` | applied | Expand 'HKSJ' on first appearance in TSA setup and manuscript Methods. |
| 138 | `src/rc_metastudio/forms/edit_plot_dialog.ui:150` | applied | Avoid ad-hoc abbreviation 'Conf. Int.'; 'CI' is standard across RC MetaStudio. |
| 139 | `src/rc_metastudio/r_bridge.py:2375` | changed | Applied the binding P value style. Preserved recognition of legacy headers. |
| 140 | `r/RCMetaR/R/analysis_contracts.R:14` | changed | Applied the binding P value style. Preserved recognition of legacy headers. |
| 141 | `r/RCMetaR/R/trial_sequential_analysis.R:480` | applied | Add leading zeros, serial comma, and expand 'LIL'. |
| 142 | `src/rc_metastudio/results/window.py:1521` | skipped | Already fixed. The plot tooltip uses the current context-menu wording. |
| 143 | `src/rc_metastudio/results/window.py:1573` | skipped | Already fixed. The plot tooltip uses the current context-menu wording. |
| 144 | `src/rc_metastudio/results/window.py:1605` | changed | Plot types expose different editor controls, so listing particular options on the shared button would overpromise. |
| 145 | `src/rc_metastudio/results/window.py:1608` | changed | Plot types expose different editor controls, so listing particular options on the shared button would overpromise. |
| 146 | `src/rc_metastudio/results/window.py:1610` | changed | Plot types expose different editor controls, so listing particular options on the shared button would overpromise. |
| 147 | `src/rc_metastudio/forms/analysis_setup_dialog.ui:174` | applied | Avoid tautological tooltip that repeats the button label 'Choose color…'. |
| 148 | `src/rc_metastudio/forms/edit_plot_dialog.ui:67` | applied | Avoid tautological tooltip that repeats the button label 'Choose color…'. |
| 149 | `src/rc_metastudio/results/plot_editor.py:232` | applied | Avoid tautological tooltip that repeats the button label. |
| 150 | `src/rc_metastudio/forms/analysis_setup_dialog.ui:216` | applied | Avoid vague repeated tooltip across four different column heading labels. |
| 151 | `src/rc_metastudio/forms/analysis_setup_dialog.ui:243` | applied | Avoid vague repeated tooltip across four different column heading labels. |
| 152 | `src/rc_metastudio/forms/analysis_setup_dialog.ui:270` | applied | Avoid vague repeated tooltip across four different column heading labels. |
| 153 | `src/rc_metastudio/forms/analysis_setup_dialog.ui:297` | applied | Avoid vague repeated tooltip across four different column heading labels. |
| 154 | `src/rc_metastudio/results/window.py:446` | changed | The node links to the report sensitivity section. |
| 155 | `src/rc_metastudio/results/window.py:308` | applied | Dead duplicate setAccessibleName immediately overwritten on line 342; keep one consistent name. |
| 156 | `src/rc_metastudio/results/window.py:312` | applied | Dead duplicate setAccessibleName immediately overwritten on line 344; keep one consistent name. |
| 157 | `src/rc_metastudio/forms/results_window.ui:33` | applied | Align .ui accessibleName with the runtime value set in results/window.py:342. |
| 158 | `src/rc_metastudio/forms/results_window.ui:65` | applied | Align .ui accessibleName with the runtime value set in results/window.py:344. |
| 159 | `src/rc_metastudio/calculators/effect_readout.py:139` | applied | Align P-value notation ('P') and '=' sign spacing with report conventions. |
| 160 | `src/rc_metastudio/main_window.py:342` | skipped | This button opens the confidence-level dialog, and its dynamic text uses an ellipsis already. |
| 161 | `src/rc_metastudio/results/window.py:436` | changed | This nested link belongs to the Text report. Decision 7 reserves Data tables for the separate results page. |
| 162 | `src/rc_metastudio/results/window.py:426` | applied | Avoid conflating the table viewer with one export format '(CSV)' — tables can also be copied to clipboard. |
| 163 | `src/rc_metastudio/results/window.py:882` | applied | Align menu action with sidebar label 'Data tables'. |
| 164 | `src/rc_metastudio/results/window.py:427` | changed | The page offers more than one copy/export representation. |
| 165 | `sample_projects/manifest.json:9` | applied | Use spaced em dash instead of ASCII hyphen between data type and dataset title. |
| 166 | `sample_projects/manifest.json:10` | applied | Add serial comma. |
| 167 | `sample_projects/manifest.json:23` | applied | Use spaced em dash instead of ASCII hyphen. |
| 168 | `sample_projects/manifest.json:37` | applied | Use spaced em dash instead of ASCII hyphen. |
| 169 | `sample_projects/manifest.json:38` | applied | Add serial comma and use 'study' instead of 'trial'. |
| 170 | `sample_projects/manifest.json:51` | applied | Use spaced em dash instead of ASCII hyphen. |
| 171 | `sample_projects/manifest.json:52` | applied | Add serial comma and standardize straight apostrophe. |
| 172 | `sample_projects/manifest.json:69` | applied | Use spaced em dash instead of ASCII hyphen. |
| 173 | `sample_projects/manifest.json:72` | applied | Add serial comma. |
| 174 | `sample_projects/manifest.json:89` | applied | Use spaced em dash and align with CONTEXT.md term 'Entered effect estimate'. |
| 175 | `sample_projects/manifest.json:103` | applied | Use spaced em dash instead of ASCII hyphen. |
| 176 | `sample_projects/manifest.json:117` | applied | Use spaced em dash instead of ASCII hyphen. |
| 177 | `sample_projects/manifest.json:135` | applied | Use spaced em dash instead of ASCII hyphen. |
| 178 | `sample_projects/manifest.json:138` | applied | Add serial comma. |
| 179 | `src/rc_metastudio/forms/analysis_setup_dialog.ui:253` | skipped | This form value is converted at runtime to an empty field with an Automatic placeholder. Removing it from XML changes the initialization path. |
| 180 | `src/rc_metastudio/forms/analysis_setup_dialog.ui:280` | skipped | This form value is converted at runtime to an empty field with an Automatic placeholder. Removing it from XML changes the initialization path. |
| 181 | `src/rc_metastudio/forms/analysis_setup_dialog.ui:307` | skipped | This form value is converted at runtime to an empty field with an Automatic placeholder. Removing it from XML changes the initialization path. |
| 182 | `src/rc_metastudio/forms/analysis_setup_dialog.ui:385` | skipped | This form value is converted at runtime to an empty field with an Automatic placeholder. Removing it from XML changes the initialization path. |
| 183 | `src/rc_metastudio/forms/analysis_setup_dialog.ui:399` | skipped | This form value is converted at runtime to an empty field with an Automatic placeholder. Removing it from XML changes the initialization path. |
| 184 | `src/rc_metastudio/forms/analysis_setup_dialog.ui:413` | skipped | This form value is converted at runtime to an empty field with an Automatic placeholder. Removing it from XML changes the initialization path. |
| 185 | `src/rc_metastudio/forms/analysis_setup_dialog.ui:427` | skipped | This form value is converted at runtime to an empty field with an Automatic placeholder. Removing it from XML changes the initialization path. |
| 186 | `src/rc_metastudio/forms/continuous_data_dialog.ui:41` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 187 | `src/rc_metastudio/forms/diagnostic_metrics_dialog.ui:7` | applied | CONTEXT.md prefers 'effect measure' over 'metric'. |
| 188 | `src/rc_metastudio/forms/diagnostic_metrics_dialog.ui:18` | applied | CONTEXT.md prefers 'effect measure' over 'metric'. |
| 189 | `src/rc_metastudio/forms/diagnostic_metrics_dialog.ui:21` | applied | CONTEXT.md prefers 'effect measure' over 'metric'. |
| 190 | `src/rc_metastudio/forms/edit_plot_dialog.ui:174` | skipped | The editor loads saved/default values through the runtime placeholder layer. Preserved the form sentinel. |
| 191 | `src/rc_metastudio/forms/edit_plot_dialog.ui:198` | skipped | The editor loads saved/default values through the runtime placeholder layer. Preserved the form sentinel. |
| 192 | `src/rc_metastudio/forms/edit_plot_dialog.ui:316` | skipped | The editor loads saved/default values through the runtime placeholder layer. Preserved the form sentinel. |
| 193 | `src/rc_metastudio/forms/edit_plot_dialog.ui:330` | skipped | The editor loads saved/default values through the runtime placeholder layer. Preserved the form sentinel. |
| 194 | `src/rc_metastudio/forms/edit_plot_dialog.ui:344` | skipped | The editor loads saved/default values through the runtime placeholder layer. Preserved the form sentinel. |
| 195 | `src/rc_metastudio/forms/edit_plot_dialog.ui:368` | skipped | The editor loads saved/default values through the runtime placeholder layer. Preserved the form sentinel. |
| 196 | `src/rc_metastudio/forms/funnel_plot_editor_dialog.ui:58` | skipped | The editor loads saved/default values through the runtime placeholder layer. Preserved the form sentinel. |
| 197 | `src/rc_metastudio/forms/funnel_plot_editor_dialog.ui:62` | skipped | Funnel initialization interprets the form sentinel. Preserved the placeholder protocol. |
| 198 | `src/rc_metastudio/forms/funnel_plot_editor_dialog.ui:64` | skipped | Funnel initialization interprets the form sentinel. Preserved the placeholder protocol. |
| 199 | `src/rc_metastudio/forms/funnel_plot_editor_dialog.ui:66` | skipped | Funnel initialization interprets the form sentinel. Preserved the placeholder protocol. |
| 200 | `src/rc_metastudio/forms/main_window.ui:274` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 201 | `src/rc_metastudio/forms/main_window.ui:297` | applied | Aligns .ui action with runtime label in main_window.py:329 and adds ellipsis for dialog-opening menu item (see Maintainer Decision #4 on Publication Bias vs Small-study effects). |
| 202 | `src/rc_metastudio/forms/publication_bias_dialog.ui:5` | applied | Aligns .ui dialog title with runtime title in small_study_effects_dialog.py:154 (see Maintainer Decision #4). |
| 203 | `src/rc_metastudio/forms/publication_bias_dialog.ui:38` | applied | CONTEXT.md defines the diagnostic funnel as 'Deeks effective-sample-size funnel'. |
| 204 | `src/rc_metastudio/forms/results_window.ui:14` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 205 | `src/rc_metastudio/forms/subgroup_analysis_dialog.ui:11` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 206 | `src/rc_metastudio/analysis/catalog.py:152` | skipped | This default is part of project data and one-arm caption/header suppression. A literal-only rename would change existing project display behavior. Preserved legacy default handling. |
| 207 | `src/rc_metastudio/analysis/catalog.py:152` | skipped | This default is part of project data and one-arm caption/header suppression. A literal-only rename would change existing project display behavior. Preserved legacy default handling. |
| 208 | `src/rc_metastudio/analysis/diagnostic_metrics_dialog.py:71` | applied | CONTEXT.md prefers 'effect measure' over 'metric'. |
| 209 | `src/rc_metastudio/analysis/diagnostic_metrics_dialog.py:72` | applied | CONTEXT.md prefers 'effect measure' over 'metric'. |
| 210 | `src/rc_metastudio/analysis/diagnostic_metrics_dialog.py:103` | changed | The warning is now split across adjacent literals. Updated the surviving effect-measure wording. |
| 211 | `src/rc_metastudio/analysis/diagnostic_metrics_dialog.py:113` | applied | CONTEXT.md prefers 'effect measure' over 'metric'. |
| 212 | `src/rc_metastudio/analysis/identity.py:107` | skipped | This default is part of project data and one-arm caption/header suppression. A literal-only rename would change existing project display behavior. Preserved legacy default handling. |
| 213 | `src/rc_metastudio/analysis/setup_dialog.py:2160` | applied | CONTEXT.md prefers 'effect measure' over 'metric'. |
| 214 | `src/rc_metastudio/analysis/small_study_effects_dialog.py:43` | applied | En dash in eponymous author pair. |
| 215 | `src/rc_metastudio/analysis/small_study_effects_dialog.py:46` | applied | En dash in eponymous author pair. |
| 216 | `src/rc_metastudio/analysis/small_study_effects_dialog.py:165` | applied | CONTEXT.md defines the diagnostic funnel as 'Deeks effective-sample-size funnel'. |
| 217 | `src/rc_metastudio/analysis/small_study_effects_dialog.py:166` | applied | Align with CONTEXT.md term 'Deeks effective-sample-size funnel'. |
| 218 | `src/rc_metastudio/analysis/small_study_effects_dialog.py:259` | skipped | Common effect is the specific model assumption and the authority package option. Fixed effect is potentially ambiguous here. |
| 219 | `src/rc_metastudio/analysis/small_study_effects_dialog.py:587` | skipped | Common effect is the specific model assumption and the authority package option. Fixed effect is potentially ambiguous here. |
| 220 | `src/rc_metastudio/analysis/trial_sequential.py:22` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 221 | `src/rc_metastudio/analysis/trial_sequential.py:107` | applied | US spelling (app standard is US English). |
| 222 | `src/rc_metastudio/analysis/trial_sequential.py:108` | applied | US spelling (app standard is US English). |
| 223 | `src/rc_metastudio/analysis/trial_sequential.py:117` | applied | CONTEXT.md uses 'outcome' for user-facing sheets. |
| 224 | `src/rc_metastudio/analysis/trial_sequential.py:124` | applied | US spelling (app standard is US English). |
| 225 | `src/rc_metastudio/analysis/trial_sequential.py:124` | applied | US spelling (app standard is US English). |
| 226 | `src/rc_metastudio/analysis/trial_sequential_dialog.py:41` | applied | US spelling (app standard is US English). |
| 227 | `src/rc_metastudio/analysis/trial_sequential_dialog.py:34` | applied | CONTEXT.md uses 'arm' instead of 'group' and 'study' instead of 'trial'. |
| 228 | `src/rc_metastudio/analysis/trial_sequential_dialog.py:36` | applied | CONTEXT.md uses 'study' instead of 'trial'. |
| 229 | `src/rc_metastudio/analysis/trial_sequential_dialog.py:37` | applied | CONTEXT.md uses 'study' instead of 'trial'. |
| 230 | `src/rc_metastudio/analysis/trial_sequential_dialog.py:39` | applied | En dash in eponymous author pair. |
| 231 | `src/rc_metastudio/analysis/trial_sequential_dialog.py:41` | applied | US spelling (app standard is US English). |
| 232 | `src/rc_metastudio/analysis/trial_sequential_dialog.py:94` | applied | En dash in eponymous author pair. |
| 233 | `src/rc_metastudio/analysis/trial_sequential_dialog.py:97` | applied | US spelling (app standard is US English). |
| 234 | `src/rc_metastudio/calculators/diagnostic_dialog.py:495` | skipped | Old literal no longer exists at this surface in current HEAD. |
| 235 | `src/rc_metastudio/calculators/effect_readout.py:204` | applied | CONTEXT.md prefers 'effect measure' over 'metric'. |
| 236 | `src/rc_metastudio/calculators/ratio_dialog.py:85` | applied | CONTEXT.md defines this concept as 'source confidence level'. |
| 237 | `src/rc_metastudio/calculators/ratio_dialog.py:235` | applied | Hyphenate 'non-negative' consistently. |
| 238 | `src/rc_metastudio/main_window.py:127` | applied | Standardize quotation marks/apostrophes (avoid mixed straight and curly quotes). |
| 239 | `src/rc_metastudio/main_window.py:344` | applied | CONTEXT.md uses 'outcome' for user-facing sheets. |
| 240 | `src/rc_metastudio/main_window.py:345` | applied | CONTEXT.md uses 'outcome' for user-facing sheets and 'confidence level' over 'interval level'. |
| 241 | `src/rc_metastudio/main_window.py:718` | applied | CONTEXT.md uses 'outcome' for user-facing sheets. |
| 242 | `src/rc_metastudio/main_window.py:1213` | applied | US spelling (app standard is US English). |
| 243 | `src/rc_metastudio/main_window.py:1214` | applied | US spelling (app standard is US English). |
| 244 | `src/rc_metastudio/main_window.py:1278` | applied | CONTEXT.md uses 'outcome' for user-facing sheets. |
| 245 | `src/rc_metastudio/main_window.py:1278` | applied | CONTEXT.md uses 'outcome' for user-facing sheets. |
| 246 | `src/rc_metastudio/main_window.py:1477` | applied | Standardize quotation marks/apostrophes (avoid mixed straight and curly quotes). |
| 247 | `src/rc_metastudio/main_window.py:1485` | applied | Standardize quotation marks/apostrophes (avoid mixed straight and curly quotes). |
| 248 | `src/rc_metastudio/main_window.py:1510` | applied | Standardize quotation marks/apostrophes (avoid mixed straight and curly quotes). |
| 249 | `src/rc_metastudio/main_window.py:1518` | applied | Standardize quotation marks/apostrophes (avoid mixed straight and curly quotes). |
| 250 | `src/rc_metastudio/main_wizard.py:156` | applied | CONTEXT.md specifies 'entered effect estimate' (matches data_type_page.ui:165). |
| 251 | `src/rc_metastudio/name_validation.py:6` | applied | CONTEXT.md standardizes study comparison cohorts as 'Arm' rather than 'Group'. |
| 252 | `src/rc_metastudio/name_validation.py:22` | applied | Standardize quotation marks/apostrophes (avoid mixed straight and curly quotes). |
| 253 | `src/rc_metastudio/name_validation.py:49` | applied | Standardize quotation marks/apostrophes (avoid mixed straight and curly quotes). |
| 254 | `src/rc_metastudio/name_validation.py:49` | applied | Standardize quotation marks/apostrophes (avoid mixed straight and curly quotes). |
| 255 | `src/rc_metastudio/r_bridge.py:508` | applied | CONTEXT.md prefers 'effect measure' over 'metric'. |
| 256 | `src/rc_metastudio/r_bridge.py:1056` | applied | US spelling (app standard is US English). |
| 257 | `src/rc_metastudio/r_bridge.py:1057` | applied | US spelling (app standard is US English). |
| 258 | `src/rc_metastudio/r_bridge.py:1142` | skipped | Old literal no longer exists at this surface in current HEAD. |
| 259 | `src/rc_metastudio/r_bridge.py:2084` | applied | Multiplication sign '×' instead of ASCII 'x'. |
| 260 | `src/rc_metastudio/r_bridge.py:2086` | applied | Multiplication sign '×' instead of ASCII 'x'. |
| 261 | `src/rc_metastudio/r_bridge.py:2103` | applied | CONTEXT.md specifies 'normalized partial SROC AUC'. |
| 262 | `src/rc_metastudio/results/formatting.py:130` | skipped | These are recognized upstream input aliases. Their displayed value is already SE (logit scale). |
| 263 | `src/rc_metastudio/results/formatting.py:131` | skipped | These are recognized upstream input aliases. Their displayed value is already SE (logit scale). |
| 264 | `src/rc_metastudio/results/formatting.py:136` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 265 | `src/rc_metastudio/results/formatting.py:137` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 266 | `src/rc_metastudio/results/formatting.py:138` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 267 | `src/rc_metastudio/results/formatting.py:139` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 268 | `src/rc_metastudio/results/formatting.py:140` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 269 | `src/rc_metastudio/results/formatting.py:141` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 270 | `src/rc_metastudio/results/formatting.py:162` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 271 | `src/rc_metastudio/results/formatting.py:163` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 272 | `src/rc_metastudio/results/formatting.py:164` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 273 | `src/rc_metastudio/results/formatting.py:193` | skipped | The matches recognize legacy ASCII eponyms for title normalization. Kept backwards recognition. |
| 274 | `src/rc_metastudio/results/formatting.py:193` | skipped | The matches recognize legacy ASCII eponyms for title normalization. Kept backwards recognition. |
| 275 | `src/rc_metastudio/results/formatting.py:194` | skipped | The matches recognize legacy ASCII eponyms for title normalization. Kept backwards recognition. |
| 276 | `src/rc_metastudio/results/formatting.py:194` | skipped | The matches recognize legacy ASCII eponyms for title normalization. Kept backwards recognition. |
| 277 | `src/rc_metastudio/results/funnel_editor.py:418` | skipped | This occurrence is used to detect the scale key. Kept legacy comparison. |
| 278 | `src/rc_metastudio/results/plot_editor.py:89` | applied | CONTEXT.md uses 'outcome' for user-facing sheets. |
| 279 | `src/rc_metastudio/results/plot_editor.py:393` | applied | CONTEXT.md specifies 'summary operating point'. |
| 280 | `src/rc_metastudio/results/plot_editor.py:394` | applied | CONTEXT.md specifies 'normalized partial SROC AUC'. |
| 281 | `src/rc_metastudio/results/plot_editor.py:425` | applied | CONTEXT.md specifies 'normalized partial SROC AUC'. |
| 282 | `src/rc_metastudio/results/report.py:691` | applied | Standardize quotation marks/apostrophes (avoid mixed straight and curly quotes). |
| 283 | `src/rc_metastudio/results/report.py:723` | applied | Standardize quotation marks/apostrophes (avoid mixed straight and curly quotes). |
| 284 | `src/rc_metastudio/results/report.py:779` | applied | US spelling (app standard is US English). |
| 285 | `src/rc_metastudio/results/report.py:920` | applied | En dash in eponymous author pair. |
| 286 | `src/rc_metastudio/results/report.py:921` | applied | En dash in eponymous author pair. |
| 287 | `src/rc_metastudio/results/report.py:924` | applied | US spelling (app standard is US English). |
| 288 | `src/rc_metastudio/results/report.py:972` | applied | US spelling (app standard is US English). |
| 289 | `src/rc_metastudio/results/report.py:973` | applied | US spelling (app standard is US English). |
| 290 | `src/rc_metastudio/results/report.py:1333` | applied | En dash in eponymous author pair. |
| 291 | `src/rc_metastudio/results/report.py:1356` | applied | Standardize quotation marks/apostrophes (avoid mixed straight and curly quotes). |
| 292 | `src/rc_metastudio/workspace/columns.py:161` | skipped | This is the legacy study column header used for backwards-compatible import and export. |
| 293 | `src/rc_metastudio/workspace/columns.py:229` | applied | Hyphenate 'non-negative' consistently. |
| 294 | `src/rc_metastudio/workspace/editing.py:480` | applied | Hyphenate 'non-negative' consistently. |
| 295 | `src/rc_metastudio/workspace/editing.py:519` | skipped | Old literal no longer exists at this surface in current HEAD. |
| 296 | `src/rc_metastudio/workspace/table_model.py:411` | changed | Raw inputs can include diagnostic cells or a single arm, so used study values. |
| 297 | `src/rc_metastudio/workspace/table_model.py:425` | applied | CONTEXT.md defines this concept as 'source confidence level'. |
| 298 | `src/rc_metastudio/workspace/table_view.py:218` | applied | Standardize quotation marks/apostrophes (avoid mixed straight and curly quotes). |
| 299 | `r/RCMetaR/R/analysis_contracts.R:157` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 300 | `r/RCMetaR/R/analysis_contracts.R:158` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 301 | `r/RCMetaR/R/analysis_contracts.R:161` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 302 | `r/RCMetaR/R/analysis_contracts.R:162` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 303 | `r/RCMetaR/R/analysis_contracts.R:163` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 304 | `r/RCMetaR/R/analysis_contracts.R:166` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 305 | `r/RCMetaR/R/analysis_contracts.R:167` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 306 | `r/RCMetaR/R/analysis_contracts.R:168` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 307 | `r/RCMetaR/R/analysis_contracts.R:171` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 308 | `r/RCMetaR/R/analysis_contracts.R:172` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 309 | `r/RCMetaR/R/analysis_contracts.R:173` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 310 | `r/RCMetaR/R/analysis_contracts.R:176` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 311 | `r/RCMetaR/R/analysis_contracts.R:177` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 312 | `r/RCMetaR/R/analysis_contracts.R:180` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 313 | `r/RCMetaR/R/analysis_contracts.R:186` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 314 | `r/RCMetaR/R/analysis_contracts.R:189` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 315 | `r/RCMetaR/R/analysis_contracts.R:192` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 316 | `r/RCMetaR/R/analysis_contracts.R:195` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 317 | `r/RCMetaR/R/analysis_contracts.R:198` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 318 | `r/RCMetaR/R/analysis_contracts.R:199` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 319 | `r/RCMetaR/R/analysis_contracts.R:202` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 320 | `r/RCMetaR/R/analysis_contracts.R:205` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 321 | `r/RCMetaR/R/analysis_contracts.R:208` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 322 | `r/RCMetaR/R/analysis_contracts.R:211` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 323 | `r/RCMetaR/R/analysis_contracts.R:214` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 324 | `r/RCMetaR/R/analysis_contracts.R:222` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 325 | `r/RCMetaR/R/analysis_contracts.R:223` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 326 | `r/RCMetaR/R/analysis_contracts.R:227` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 327 | `r/RCMetaR/R/analysis_contracts.R:240` | applied | En dash in eponymous author pair. |
| 328 | `r/RCMetaR/R/analysis_contracts.R:241` | applied | En dash in eponymous author pair. |
| 329 | `r/RCMetaR/R/analysis_contracts.R:242` | applied | En dash in eponymous author pair. |
| 330 | `r/RCMetaR/R/analysis_contracts.R:243` | applied | En dash in eponymous author pair. |
| 331 | `r/RCMetaR/R/analysis_contracts.R:244` | applied | En dash in eponymous author pair. |
| 332 | `r/RCMetaR/R/analysis_contracts.R:246` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 333 | `r/RCMetaR/R/analysis_contracts.R:248` | applied | En dash in eponymous author pair. |
| 334 | `r/RCMetaR/R/analysis_contracts.R:249` | applied | En dash in eponymous author pair. |
| 335 | `r/RCMetaR/R/analysis_contracts.R:261` | applied | En dash in eponymous author pair. |
| 336 | `r/RCMetaR/R/analysis_contracts.R:262` | applied | En dash in eponymous author pair. |
| 337 | `r/RCMetaR/R/analysis_contracts.R:288` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 338 | `r/RCMetaR/R/analysis_contracts.R:289` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 339 | `r/RCMetaR/R/analysis_contracts.R:294` | applied | Use en dash in eponymous label and citation page range (matches report.py citations). |
| 340 | `r/RCMetaR/R/binary_methods.R:17` | applied | Hyphenate 'non-negative' consistently. |
| 341 | `r/RCMetaR/R/binary_methods.R:115` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 342 | `r/RCMetaR/R/binary_methods.R:169` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 343 | `r/RCMetaR/R/binary_methods.R:206` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 344 | `r/RCMetaR/R/binary_methods.R:282` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 345 | `r/RCMetaR/R/binary_methods.R:283` | applied | En dash in eponymous author pair. |
| 346 | `r/RCMetaR/R/binary_methods.R:329` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 347 | `r/RCMetaR/R/binary_methods.R:396` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 348 | `r/RCMetaR/R/binary_methods.R:436` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 349 | `r/RCMetaR/R/binary_methods.R:490` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 350 | `r/RCMetaR/R/binary_methods.R:492` | applied | Use standard compound adjective 'between-study'. |
| 351 | `r/RCMetaR/R/continuous_methods.R:64` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 352 | `r/RCMetaR/R/continuous_methods.R:109` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 353 | `r/RCMetaR/R/continuous_methods.R:147` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 354 | `r/RCMetaR/R/continuous_methods.R:206` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 355 | `r/RCMetaR/R/continuous_methods.R:208` | applied | Use standard compound adjective 'between-study'. |
| 356 | `r/RCMetaR/R/diagnostic_methods.R:10` | skipped | This label maps the diagnostic measure contract. Applied sentence case at display sites where it is safe. |
| 357 | `r/RCMetaR/R/diagnostic_methods.R:177` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 358 | `r/RCMetaR/R/diagnostic_methods.R:230` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 359 | `r/RCMetaR/R/diagnostic_methods.R:239` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 360 | `r/RCMetaR/R/diagnostic_methods.R:239` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 361 | `r/RCMetaR/R/diagnostic_methods.R:240` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 362 | `r/RCMetaR/R/diagnostic_methods.R:277` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 363 | `r/RCMetaR/R/diagnostic_methods.R:332` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 364 | `r/RCMetaR/R/diagnostic_methods.R:333` | applied | En dash in eponymous author pair. |
| 365 | `r/RCMetaR/R/diagnostic_methods.R:340` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 366 | `r/RCMetaR/R/diagnostic_methods.R:340` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 367 | `r/RCMetaR/R/diagnostic_methods.R:341` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 368 | `r/RCMetaR/R/diagnostic_methods.R:379` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 369 | `r/RCMetaR/R/diagnostic_methods.R:399` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 370 | `r/RCMetaR/R/diagnostic_methods.R:439` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 371 | `r/RCMetaR/R/diagnostic_methods.R:477` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 372 | `r/RCMetaR/R/diagnostic_methods.R:533` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 373 | `r/RCMetaR/R/diagnostic_methods.R:535` | applied | Use standard compound adjective 'between-study'. |
| 374 | `r/RCMetaR/R/diagnostic_methods.R:543` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 375 | `r/RCMetaR/R/diagnostic_methods.R:543` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 376 | `r/RCMetaR/R/diagnostic_methods.R:544` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 377 | `r/RCMetaR/R/forest_axis.R:78` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 378 | `r/RCMetaR/R/forest_axis.R:81` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 379 | `r/RCMetaR/R/forest_metafor.R:1106` | skipped | This default is part of project data and one-arm caption/header suppression. A literal-only rename would change existing project display behavior. Preserved legacy default handling. |
| 380 | `r/RCMetaR/R/forest_style_bmj.R:50` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 381 | `r/RCMetaR/R/forest_style_bmj.R:64` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 382 | `r/RCMetaR/R/forest_style_bmj.R:216` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 383 | `r/RCMetaR/R/forest_style_bmj.R:217` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 384 | `r/RCMetaR/R/forest_style_bmj.R:218` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 385 | `r/RCMetaR/R/forest_style_bmj.R:726` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 386 | `r/RCMetaR/R/forest_style_default.R:86` | skipped | This default is part of project data and one-arm caption/header suppression. A literal-only rename would change existing project display behavior. Preserved legacy default handling. |
| 387 | `r/RCMetaR/R/forest_summary.R:183` | applied | En dash in eponymous author pair. |
| 388 | `r/RCMetaR/R/meta_regression.R:74` | changed | Regression Plot is an artifact key shared by the image and parameter bundle. Renamed the visible plot title at presentation instead. |
| 389 | `r/RCMetaR/R/meta_regression.R:76` | changed | Regression Plot is an artifact key shared by the image and parameter bundle. Renamed the visible plot title at presentation instead. |
| 390 | `r/RCMetaR/R/meta_regression.R:96` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 391 | `r/RCMetaR/R/meta_regression.R:127` | applied | Use standard compound adjective 'between-study'. |
| 392 | `r/RCMetaR/R/numeric_display.R:129` | applied | En dash in eponymous author pair. |
| 393 | `r/RCMetaR/R/numeric_display.R:132` | applied | En dash in eponymous author pair. |
| 394 | `r/RCMetaR/R/permutation.R:46` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 395 | `r/RCMetaR/R/permutation.R:53` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 396 | `r/RCMetaR/R/plotting.R:360` | applied | En dash in eponymous author pair. |
| 397 | `r/RCMetaR/R/plotting.R:373` | applied | CONTEXT.md specifies 'entered effect estimate' instead of legacy 'Generic effect'. |
| 398 | `r/RCMetaR/R/ratio_methods.R:51` | applied | Hyphenate 'non-positive' consistently. |
| 399 | `r/RCMetaR/R/ratio_methods.R:105` | applied | En dash in eponymous author pair. |
| 400 | `r/RCMetaR/R/ratio_methods.R:109` | applied | CONTEXT.md standardizes missing/undefined estimates as 'Not estimable'. |
| 401 | `r/RCMetaR/R/ratio_methods.R:132` | applied | CONTEXT.md standardizes missing/undefined estimates as 'Not estimable'. |
| 402 | `r/RCMetaR/R/ratio_methods.R:167` | changed | Used a plain-language label without treating not estimable as a hyphenated adjective. |
| 403 | `r/RCMetaR/R/ratio_methods.R:198` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 404 | `r/RCMetaR/R/ratio_methods.R:201` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 405 | `r/RCMetaR/R/ratio_methods.R:225` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 406 | `r/RCMetaR/R/ratio_methods.R:249` | applied | En dash in eponymous author pair. |
| 407 | `r/RCMetaR/R/ratio_methods.R:253` | applied | CONTEXT.md uses 'arm' rather than 'group'. |
| 408 | `r/RCMetaR/R/ratio_methods.R:253` | applied | CONTEXT.md uses 'arm' rather than 'group', and expands 'MH' with an en dash. |
| 409 | `r/RCMetaR/R/rcmetar-core.R:834` | applied | CONTEXT.md prefers 'effect measure' over 'metric'. |
| 410 | `r/RCMetaR/R/rcmetar-core.R:1065` | skipped | The result adapter uses this R key to reconcile the fitted inference method with the requested setting. It hides the source key and displays the fitted method under Inference. |
| 411 | `r/RCMetaR/R/reitsma_methods.R:329` | skipped | These are internal matrix column selectors. Renaming them would require changing the R result schema and its consumers. |
| 412 | `r/RCMetaR/R/reitsma_methods.R:330` | skipped | These are internal matrix column selectors. Renaming them would require changing the R result schema and its consumers. |
| 413 | `r/RCMetaR/R/reitsma_methods.R:331` | skipped | These are internal matrix column selectors. Renaming them would require changing the R result schema and its consumers. |
| 414 | `r/RCMetaR/R/reitsma_methods.R:393` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 415 | `r/RCMetaR/R/reitsma_methods.R:600` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 416 | `r/RCMetaR/R/reitsma_methods.R:636` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 417 | `r/RCMetaR/R/reitsma_methods.R:646` | skipped | These are internal matrix column selectors. Renaming them would require changing the R result schema and its consumers. |
| 418 | `r/RCMetaR/R/reitsma_methods.R:647` | skipped | These are internal matrix column selectors. Renaming them would require changing the R result schema and its consumers. |
| 419 | `r/RCMetaR/R/reitsma_methods.R:647` | skipped | These are internal matrix column selectors. Renaming them would require changing the R result schema and its consumers. |
| 420 | `r/RCMetaR/R/reitsma_methods.R:936` | applied | Use superscript 'I²' symbol consistently. |
| 421 | `r/RCMetaR/R/reitsma_methods.R:952` | applied | Use superscript 'I²' symbol consistently. |
| 422 | `r/RCMetaR/R/reitsma_methods.R:1009` | applied | Align with 'Decimal places' used in all other method dialogs (binary/continuous/diagnostic/meta-regression). |
| 423 | `r/RCMetaR/R/reitsma_methods.R:1152` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 424 | `r/RCMetaR/R/reitsma_methods.R:1278` | applied | Use superscript 'I²' symbol consistently. |
| 425 | `r/RCMetaR/R/repeated_analyses.R:9` | applied | US spelling (app standard is US English). |
| 426 | `r/RCMetaR/R/repeated_analyses.R:57` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 427 | `r/RCMetaR/R/repeated_analyses.R:58` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 428 | `r/RCMetaR/R/repeated_analyses.R:59` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 429 | `r/RCMetaR/R/repeated_analyses.R:60` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 430 | `r/RCMetaR/R/repeated_analyses.R:61` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 431 | `r/RCMetaR/R/repeated_analyses.R:62` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 432 | `r/RCMetaR/R/repeated_analyses.R:63` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 433 | `r/RCMetaR/R/repeated_analyses.R:64` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 434 | `r/RCMetaR/R/repeated_analyses.R:65` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 435 | `r/RCMetaR/R/repeated_analyses.R:66` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 436 | `r/RCMetaR/R/repeated_analyses.R:67` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 437 | `r/RCMetaR/R/repeated_analyses.R:109` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 438 | `r/RCMetaR/R/repeated_analyses.R:219` | applied | Multiplication sign '×' instead of ASCII 'x'. |
| 439 | `r/RCMetaR/R/repeated_analyses.R:287` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 440 | `r/RCMetaR/R/repeated_analyses.R:360` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 441 | `r/RCMetaR/R/repeated_analyses.R:360` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 442 | `r/RCMetaR/R/repeated_analyses.R:410` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 443 | `r/RCMetaR/R/repeated_analyses.R:458` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 444 | `r/RCMetaR/R/repeated_analyses.R:469` | changed | Used a plain-language label without treating not estimable as a hyphenated adjective. |
| 445 | `r/RCMetaR/R/repeated_analyses.R:502` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 446 | `r/RCMetaR/R/repeated_analyses.R:534` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 447 | `r/RCMetaR/R/repeated_analyses.R:592` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 448 | `r/RCMetaR/R/repeated_analyses.R:636` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 449 | `r/RCMetaR/R/repeated_analyses.R:670` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 450 | `r/RCMetaR/R/repeated_analyses.R:698` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 451 | `r/RCMetaR/R/repeated_analyses.R:742` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 452 | `r/RCMetaR/R/results_display.R:63` | applied | En dash in eponymous author pair. |
| 453 | `r/RCMetaR/R/results_display.R:114` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 454 | `r/RCMetaR/R/results_display.R:439` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 455 | `r/RCMetaR/R/results_display.R:446` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 456 | `r/RCMetaR/R/results_display.R:462` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 457 | `r/RCMetaR/R/results_display.R:663` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 458 | `r/RCMetaR/R/results_display.R:666` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 459 | `r/RCMetaR/R/results_display.R:795` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 460 | `r/RCMetaR/R/small_study_effects.R:161` | applied | CONTEXT.md uses 'arm' rather than 'group'. |
| 461 | `r/RCMetaR/R/small_study_effects.R:173` | applied | CONTEXT.md uses 'arm' rather than 'group'. |
| 462 | `r/RCMetaR/R/small_study_effects.R:312` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 463 | `r/RCMetaR/R/small_study_effects.R:424` | applied | Use en dash in eponymous pair and CONTEXT.md term 'arm'. |
| 464 | `r/RCMetaR/R/small_study_effects.R:451` | applied | En dash in eponymous author pair. |
| 465 | `r/RCMetaR/R/small_study_effects.R:559` | changed | Decision 6 specifies uppercase P and no hyphen. |
| 466 | `r/RCMetaR/R/small_study_effects.R:900` | changed | Decision 6 specifies uppercase P and no hyphen. |
| 467 | `r/RCMetaR/R/small_study_effects.R:969` | skipped | Common effect is the specific model assumption and the authority package option. Fixed effect is potentially ambiguous here. |
| 468 | `r/RCMetaR/R/small_study_effects.R:1017` | applied | En dash in eponymous author pair. |
| 469 | `r/RCMetaR/R/small_study_effects.R:1020` | applied | En dash in eponymous author pair. |
| 470 | `r/RCMetaR/R/small_study_effects.R:1036` | applied | En dash in eponymous author pair. |
| 471 | `r/RCMetaR/R/small_study_effects.R:1039` | applied | CONTEXT.md prefers 'effect measure' over 'metric'. |
| 472 | `r/RCMetaR/R/small_study_effects.R:1100` | applied | Align plot title with CONTEXT.md term 'Deeks effective-sample-size funnel'. |
| 473 | `r/RCMetaR/R/small_study_effects.R:1104` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 474 | `r/RCMetaR/R/small_study_effects.R:1105` | applied | Use sentence case (consistent with ~95% of RC MetaStudio UI and headings). |
| 475 | `r/RCMetaR/R/small_study_effects.R:1260` | skipped | Common effect is the specific model assumption and the authority package option. Fixed effect is potentially ambiguous here. |
| 476 | `r/RCMetaR/R/trial_sequential_analysis.R:12` | applied | CONTEXT.md prefers 'effect measure' over 'metric'. |
| 477 | `r/RCMetaR/R/trial_sequential_analysis.R:13` | applied | CONTEXT.md uses 'outcome' for user-facing sheets. |
| 478 | `r/RCMetaR/R/trial_sequential_analysis.R:113` | applied | CONTEXT.md uses 'outcome' for user-facing sheets. |
| 479 | `r/RCMetaR/R/trial_sequential_analysis.R:165` | applied | CONTEXT.md uses 'outcome' for user-facing sheets. |
| 480 | `r/RCMetaR/R/trial_sequential_analysis.R:414` | applied | US spelling (app standard is US English). |
| 481 | `r/RCMetaR/R/trial_sequential_analysis.R:426` | applied | US spelling (app standard is US English). |
| 482 | `r/RCMetaR/R/trial_sequential_analysis.R:525` | applied | CONTEXT.md uses 'outcome' instead of 'sheet', plus en dash in Hartung–Knapp. |
| 483 | `r/RCMetaR/R/trial_sequential_analysis.R:528` | applied | En dash in eponymous author pair. |
| 484 | `r/RCMetaR/R/trial_sequential_analysis.R:549` | applied | CONTEXT.md uses 'outcome' for user-facing sheets. |
| 485 | `r/RCMetaR/R/trial_sequential_plot.R:50` | changed | The token supplies the width measurement for the rendered phrase. Updated the source label in the same helper. |
| 486 | `r/RCMetaR/R/trial_sequential_plot.R:56` | applied | US spelling. Matched the visible prefix and the width sample. |
| 487 | `r/RCMetaR/R/trial_sequential_plot.R:157` | applied | US spelling (app standard is US English). |
