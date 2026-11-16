I've finished the read-only copy audit. I made no edits, started no agents and ran no GUI or test commands. I read every visible string in the 25 `.ui` files and pulled every prose-like literal from `src/rc_metastudio/*.py` with an AST pass (about 2,100 strings). I also read About, Cite, plot export, the report generator, the R reference definitions, `CONTEXT.md` and the product docs.

Priority: **P1** = defect or misleading/incorrect meaning, **P2** = inconsistency or unhelpful copy, **P3** = polish.

---

## A. Product description (approved: "RC MetaStudio is open-source software for advanced meta-analysis.")

| Location | Current | Action |
|---|---|---|
| `src/rc_metastudio/about_legal_dialog.py:31` | "RC MetaStudio is open-source desktop software for advanced meta-analysis." | Replace with the approved sentence. Wrap the term as `<span style="white-space:nowrap">meta-analysis</span>`: Qt rich text supports `nowrap` and copied text keeps a real hyphen. Avoid U+2011, which ends up in the clipboard. |
| `pyproject.toml:4` | "RC MetaStudio open-source desktop software for advanced meta-analysis." (**grammar: "is" is missing**) | The approved sentence. |
| `NOTICE.md:3` | "…is open-source desktop software for advanced meta-analysis, developed and maintained by Research Consultancy (RC)." | "RC MetaStudio is open-source software for advanced meta-analysis, developed and maintained by Research Consultancy (RC)." |
| `README.md:7` | "…is an open-source desktop application for performing and reviewing meta-analyses without writing code." | "RC MetaStudio is open-source software for advanced meta-analysis. You can run and review meta-analyses without writing code." |
| **Leave as is** | `CITATION.cff:4`, `application_metadata.py:22` `CITATION_TITLE`, `README.md:39`, the matching string at `manuscript_report.py:166`, and `CHANGELOG.md:357` | The first four are the published Zenodo title. The changelog entry is history. |

No packaging metadata (spec/plist/version file) carries a description.

## B. Real defects found while auditing (P1)

1. `diagnostic_data_dialog.py:390,393`: `"Could not convert %s to integer" % self.two_by_two_table.item(i, j)` puts the **`QTableWidgetItem` object repr** into the message box, titled "Warning". Change it to `.text()` and use: title "Invalid count", text "Enter a whole number for each count."
2. `analysis_setup_dialog.py:739`: the file filter `"png image files: (.png)"` has no `*`, so it filters nothing. Use `"PNG images (*.png)"`.
3. `analysis_setup_dialog.py:1113–1119`: the plural is wrong ("In total, 1 studies were included", "(1 studies were excluded)") and there are double parentheses when participants are listed. Recommended: "In total, 10 studies were included (1,200 participants in Intervention and 1,180 in Control); 2 studies were excluded." Use "1 study was included / excluded" for the singular. The same plural bug is at `manuscript_report.py:26` ("The 1 studies with no events…"), `small_study_effects_dialog.py:303` ("1 usable studies"), `:325` and `:62` ("1 eligible studies").
4. `analysis_method_labels.py:60`: `("to","if0all")` reads "All studies if any study has zero events". `if0all` triggers on any **zero cell**, which includes zero non-events. The label misstates the policy. Use the `CONTEXT.md` term "All studies if any zero exists". Change only the display label, not the stored policy values.
5. `analysis_setup_dialog.py:1146` and prose: the label "all studies if any zero exists" is spliced into a sentence. That produces "A continuity correction of 0.5 was applied to all studies if any zero exists", which states a condition that has already been tested (the code only gets here when `zero` is true). Use:
   - only0: "…was applied to studies with at least one zero cell."
   - all: "…was applied to all studies."
   - if0all: "…was applied to all studies because at least one study had a zero cell."
6. `manuscript_report.py:525`: the methods sentence always says "Subgroup differences were tested using heterogeneity Q…", but line 274 shows the test can be **F**. Make the sentence follow the executed test: "Subgroup differences were tested with Cochran's Q across subgroup estimates (inverse-variance weighted)." or "…with an F test." Ask the domain owner which wording to use for F.
7. `dataset_table_model.py:812–815`: the SD-column tooltip returns early, so it lacks the rename and sort hints the other columns have. The upper-bound tooltip has a stray trailing `\n` (line 824), and `{confidence:.1%}` renders "95.0%". Use `f"{level:g}%"`.
8. `ratio_data.py:29`: "Declare a shared person-time unit for both groups." CONTEXT says *Group* means subgroup only. Use "Use the same person-time unit for both arms."
9. `analysis_catalog.py:142`: the default single-arm names are "Group" / "Other group", which conflicts with the Group term. **Needs your decision** (see H).

## C. Global consistency groups (P2: implement each once)

**C1. Dialog and window titles → sentence case.** Everything else (menus, buttons) is already sentence case. Change these:
- `main_window.py`: `:465` "Recent Projects Not Updated", `:483` "Project Saved; Durability Uncertain", `:955` "Analysis Backend Unavailable", `:963` "Could Not Prepare Analysis", `:1130` "Could Not Display Analysis Results", `:1217` "Could Not Open Project", `:1719` "Could Not Save Project"
- `analysis_setup_dialog.py:802` "No Covariates Selected", `:836` "Missing Covariate Values", `:931` and `plot_editor_dialog.py:574` "Plot Accent Color"
- `diagnostic_metrics_dialog.py:74`, `subgroup_analysis_dialog.py:46`, `dataset_table_view.py:261` "Delete Study", `plot_editor_dialog.py:582` "Save %s Plot Image", `results_window.py:1735` "Save Plot As" (→ "Export plot")
- `results_window.py:1833–1840` "No Results"
- `.ui` titles: `binary_back_calculation_dialog.ui:6` and `continuous_back_calculation_dialog.ui:6` "Choose Back Calculation Result" → "Choose back-calculation result"; `covariate_type_dialog.ui:7`; `subgroup_analysis_dialog.ui:11`; `binary/continuous/diagnostic_data_dialog.ui:6`; `csv_import_page.ui:51` "Import Options"; `main_window.ui:217` "Tool Bar" → "Toolbar"

Also replace the generic titles "Warning" (`main_window.py:1667`, `diagnostic_data_dialog.py:391`) and "Insufficient Arguments" (`continuous_data_dialog.py:116`) with titles that say what happened.

**C2. File dialogs.** Drop the "RCMetaStudio - " prefix: `analysis_setup_dialog.py:737` → "Choose plot image location"; `main_window.py:1200`, `main_wizard.py:209` → "Open project"; `main_window.py:1697` → "Save project"; `main_wizard.py:671` → "Import data". Use one filter, "RC MetaStudio projects (*.rcms)", at `main_window.py:659,1202,1699` and `main_wizard.py:211`. `results_window.py:936` "Export manuscript report" → "Export report", to match the action.

**C3. Two-person eponyms take an en dash**, as `CONTEXT.md` does: Mantel–Haenszel, DerSimonian–Laird, Sidik–Jonkman, Hunter–Schmidt, Paule–Mandel, Knapp–Hartung, Freeman–Tukey, Begg–Mazumdar.
- Fix at the source: `analysis_method_labels.py:5–63` and `analysis_catalog.py:24` ("Freeman-Tukey"; `main_wizard.py:458` already uses the en dash), plus `manuscript_report.py:22`.
- Then delete the ad hoc `.replace('DerSimonian-Laird', …)` at `manuscript_report.py:37,48` and the `_CANONICAL_LABEL_REPLACEMENTS` patch.
- **Caution:** `analysis_setup_dialog.py:187,188,1312` compare against display labels ("Diagnostic Fixed-Effect Peto"). Update those comparisons, or better, compare method keys.
- `("rm.method","HE")` shows "Hedges" in Python but "Hedges-Olkin" in R (`analysis_contracts.R` names). Choose one; I recommend "Hedges–Olkin".

**C4. Method and parameter labels → sentence case** (`analysis_method_labels.py`):
- "Binary Fixed-Effect Inverse Variance" → "Fixed-effect inverse-variance", and the same pattern for MH, Peto and Random-effects. The data-type prefix repeats the sheet type; see H.
- "Maximum Likelihood" → "Maximum likelihood (ML)", "Restricted Maximum Likelihood" → "Restricted maximum likelihood (REML)"
- "Random-Effects Method" → "Between-study variance estimator" (matches the `:1503` tooltip and the report prose)
- "Inference Method" → "Inference method" (R metadata already uses this; also fix the R error text "The selected Inference Method requires…")
- "Confidence Level" → "Confidence level", "Decimal Places" → "Decimal places", "Meta-Regression" → "Meta-regression", "No studies" → "None" (matches correction.policy)

**C5. "metric" → "effect measure"** wherever it means the effect measure. The wizard and `.ui` labels already say "Effect measure":
- `binary_data_dialog.ui:67,68` ("selected metric scale", "selected effect metric")
- `workspace_editing.py:639` "No effect metric is selected." → "Choose an effect measure first."
- `main_window.py:1068` "Choose a %s effect-size measure or calculator metric." → "Choose a %s effect measure."
- `dataset_table_model.py:495` ("selected metric… another applicable metric")
- "Diagnostic metrics" stays.

**C6. US spelling** (the app uses "color"): `analysis_setup_dialog.py:748` and `plot_editor_dialog.py:73` "accent colours" → "colors"; `analysis_setup_dialog.py:960` "Tick Include" → "Select Include".

**C7. Back-calculation wording:** use "back-calculation" (hyphenated noun) at `continuous_data_dialog.py:1496` and the `.ui` titles. Rewrite the choice prompts:
- `binary_data_dialog.py:1204` and `binary_back_calculation_dialog.ui:15` disagree with each other. Both → "Two sets of counts match the entered values. Choose one. Neither set includes a continuity correction for zero counts."
- `continuous_data_dialog.py:1496–1498` → "More than one {sample size} matches the entered values. Choose one:"
- "Rerun" vs "Re-run": `results_window.py:794` → "Rerun this analysis with its original dataset and changed settings (Ctrl+Shift+R)." and "This analysis cannot be rerun from here." This matches `funnel_plot_editor_dialog.ui:13`.

**C8. Validation messages: one voice.** Imperative, no "!", no "Please", same wording for the same rule:

| Old (sites) | New |
|---|---|
| "Raw data needs to be numeric." (`binary_data_dialog.py:830`, `continuous_data_dialog.py:774`, `diagnostic_data_dialog.py:404`, `workspace_editing.py:443,447`), "Must be numeric!" (`calculator_controls.py:361`), "Outcomes must be numeric." (`workspace_editing.py:536,540`; **"Outcomes" misuses the domain term**) | "Enter a number." |
| "Expected a whole number (count), but a decimal value was entered." (×3) | "Counts must be whole numbers." |
| "Number of events cannot be greater than number of samples." (`workspace_editing.py:494,498`) | "Events cannot exceed the arm total." (already used at `binary_data_dialog.py:974`) |
| "Count cannot be zero or negative" (`workspace_editing.py:506`) | "Participants must be a positive whole number." |
| "Years need to be integers." (`workspace_editing.py:423,427`) | "Enter the year as a whole number, for example 2019." |
| "Please enter a study name before entering study data." (`workspace_editing.py:346,354`) | "Enter a study name first." |
| "You have already entered raw data for this study. If you want to enter the outcome directly…" (`workspace_editing.py:575`) | "This study already has arm data. To enter an effect estimate instead, clear the arm data first." |
| "The lower CI must be less than the point estimate!" / "The higher CI must be greater…!" / "The lower CI must be less than the higher CI!" (`calculator_controls.py:99,105,111`) | "The lower limit must be below the estimate." / "The upper limit must be above the estimate." / "The lower limit must be below the upper limit." |
| "The interval must satisfy lower < estimate < upper." (`ratio_data.py:40`) | "The lower limit must be below the estimate, and the estimate below the upper limit." |
| "Correlation must be between -1 and +1" (`continuous_data_dialog.py:572`) | "Correlation must be between −1 and 1." |
| "Diagnostic 2x2 table…" (`diagnostic_data_dialog.py:480`, `workspace_editing.py:526`) | "Enter at least one count greater than zero." |
| "%s %s named %s already exists. Please pick another name." (`name_validation.py:22`) | "A covariate named “X” already exists. Choose another name." |
| "Enter an unambiguous finite number using '.' or ',' as decimal separator." (`calculator_controls.py:82`) vs "Enter a finite number using a decimal point or decimal comma." (`ratio_data_dialog.py:213`) | Use the second wording for both. |
| "Confidence interval must be specified" (`continuous_data_dialog.py:116,118`; it is really the **level**) | "Confidence level is missing." (internal guard only) |

**C9. Quotes:** use curly quotes “…” consistently.
- `dataset_table_view.py:262` "Delete study %s?" → "Delete study “%s”?"
- `workspace_editing.py:364,414` use ‘…’ → “…”
- `results_window.py:1398,1460`: "To save the image:\nright-click on the image and choose "Export plot…"." → "To save this plot, right-click it and choose Export plot…"
- `manuscript_report.py:405` "Cochran's Q" vs `:738` "Cochran’s Q" → curly in both.

## D. Area-by-area findings

**Main window and menus**
- `main_window.py:1640` title "Delete sheet" → "Delete outcome". The UI says *outcome* everywhere else.
- `main_window.py:1625` context-menu "Rename" → "Rename outcome…", to match `:350`.
- `main_window.py:1667–1676`: title "Warning", text "You've made unsaved changes to your data. Do you want to save your changes?", button "Discard". Recommended: title "Unsaved changes", text "Save changes to “{project}” before closing?", buttons Save / Don't save / Cancel.
- `main_window.py:466` "machine-local recent-project list" → "…but could not update Open recent."
- `main_window.py:484`: "RC MetaStudio installed the saved project at %s, but the operating system could not confirm final directory durability. The document is treated as saved so later actions do not discard work by retrying a replacement." → "RC MetaStudio saved the project to %s, but the operating system could not confirm the save is complete on disk. Keep a backup copy until you save again." Keep the Details line.
- `main_window.py:951,959` "Method & Parameters dialog" → "analysis settings". The dialog title is "Method and parameters".
- `main_window.py:946` and `r_bridge.py:70`: "Install or repair the pinned R/RCMetaR runtime… packaged integration kit" → "RC MetaStudio could not start its built-in R runtime, so analyses are unavailable. Reinstall RC MetaStudio, then try again." Keep the technical text in Details (see H).
- `r_bridge.py:85` "Cannot initialize rpy2…" → put it under Details only.
- `r_bridge.py:256` "Please install this package and then restart" → "Install this R package, then restart RC MetaStudio."
- `main_window.py:551` "waiting for R" → "R is starting".

**Data table tooltips** (`dataset_table_model.py`)
- `:802` "Sort on this column by right-clicking the column header and selecting 'sort studies by <column>'" → "Right-click the header to sort studies by this column."
- `:815` "Rename arm by right-clicking…" → "Right-click the header to rename this arm."
- `:804` "# True Positives" etc. → "True positives (TP)", "False negatives (FN)", "False positives (FP)", "True negatives (TN)"
- `:829` "Standard Error" → "Standard error"
- `:839` "Check if you want to include this study in the meta-analysis" → "Include this study in analyses"
- `dataset_table_view.py:104`: the accessible description "Gold marks…" refers to a colour, which a screen reader can't use. Use "Effect estimate and confidence interval columns are highlighted."

**Wizard and start page**
- Data-subtype naming is split three ways: "Generic effect size" (`data_type_page.ui:165`, `main_wizard.py:1015`), "Entered effect" (`main_wizard.py:456,621`, `continuous_data_dialog.py:1614`) and "Generic entered effect" (`analysis_identity.py:72`). See H.
- `welcome_page.ui:141–170`: "Project site / How to cite / Issues" now differ from About ("Visit website / Report an issue") and the new Cite dialog. If the page is still reachable, use "Website · Cite · Report an issue". The refresh doc removed "Project site" from Help.
- `publication_bias_dialog.ui:5` "Publication Bias - RC MetaStudio" is overridden at `small_study_effects_dialog.py:102`. Align the `.ui` string or leave it.
- `rm5_import.py:42,231` say "RCMS", which is unexplained to users → "RC MetaStudio".

**Analysis setup**
- `analysis_setup_dialog.py:722` "exactly one Numeric covariate" and `subgroup_analysis_dialog.py:47` "Select a Category covariate" vs `main_window.py:599` "categorical covariate". Use lowercase "numeric" / "categorical" in prose.
- `:758` and `plot_editor_dialog.py:90` say the same thing two ways. Use one: "Changes the forest plot display order only; pooled estimates are unchanged. Cumulative analysis follows the study table order."
- `confidence_level_dialog.py:28` → "Applies to the study table and to new analyses. Existing results and entered source intervals are unchanged."
- `main_window.py:327` → "Confidence level for table effects and new analyses on this sheet. Each analysis can override it."

**Plot editors and export**
- Caption tooltips differ: `funnel_plot_editor_dialog.py:65` vs `plot_editor_dialog.py:111`. Both → "Shown under the figure when exported alone. Clear it to omit the caption."
- `funnel_plot_editor_dialog.py:148` "leave the default marker" → "Leave as [default] to use the automatic label."
- "tau-squared" (`funnel_plot_editor_dialog.py:145`, `small_study_effects_dialog.py:122`) → "τ²", as in the `.ui` labels.
- `small_study_effects_dialog.py:126` "significance levels, such as 90, 95, 99" — **these are confidence levels.** → "Enter contour confidence levels (%) separated by commas, for example 90, 95, 99." Also unify `funnel_plot_editor_dialog.py:147` "90,95,99" → "90, 95, 99" and `:393`.
- `plot_editor_dialog.py:352,383` "normalized pAUC" → "normalized partial AUC" (CONTEXT term).
- `plot_editor_dialog.py:185–187` "Plot edit error" / "A plot edit could not be rendered. The last successful plot remains active." → "Could not update plot" / "The change could not be drawn. The previous plot is still shown."
- `results_window.py:1492–1497` "Edit plot appearance and regenerate the result before closing." → "Edit this plot's appearance."
- `results_window.py:604` "Export exact producer values, scales and interval levels" → "Export unrounded values with their scales and confidence levels". "This table holds formatted output only" → "Only formatted values are available for this table."
- `plot_export_dialog.py:45` "Height (proportional)" → "Height". `:56` "Original image resolution is preserved." → "This image keeps its original size and resolution."

**Small-study effects** (keep the CONTEXT boundaries)
- `:110` "help distinguish publication bias from other asymmetry" overstates. → "Add significance contours to show where studies fall relative to conventional significance thresholds."
- `:134` → "Impute studies under an assumed asymmetry scenario and show the augmented estimate. This is not a corrected effect."
- `:138`: delete the filler sentence "L0 and R0 are established trim-and-fill estimators."
- `:69,71` "Primary test Classical Egger (…)" → "Primary test: Classical Egger (…)", and the same for "Exploratory tests:".
- `:389` "Try running again when preview is available." → "Availability will be checked again when the analysis runs."
- `publication_bias_dialog.ui:62,64` show raw lowercase values "auto/left/right", "random/common". These texts **are the values sent to R** (`small_study_effects_dialog.py:440–442` read `currentText()`). Relabel to "Automatic / Left / Right" and "Random effects / Common effect" only after switching to `addItem(label, value)` + `currentData()`.

**Errors, About and Cite**
- `app_error_handler.py:15` "Sorry, an unexpected error occurred. RC MetaStudio is still running, but the action could not be completed." → "This action could not be completed. RC MetaStudio is still running." Keep Details.
- `citation_dialog.py:38` "Zenodo · all versions DOI" → "This DOI always points to the latest version."
- `about_legal_dialog.py:47` window title 'About RCMS' vs accessible name "About RC MetaStudio" (see H).

## E. Report formatting (your requested refinements, with the final format)

1. **CI notation, one form everywhere: "95% CI 0.49 to 1.22".** "to" is safe with negative bounds. Change `manuscript_report.py:226` from `({level} [{lo}, {hi}], z = …, P = …)` to `({level} {lo} to {hi}; z = …; P = …)`. Example: "The pooled odds ratio was 0.77 (95% CI 0.49 to 1.22; z = −1.12; P = 0.27)." Tables and prediction prose already use "to".
2. **Heterogeneity as one sentence** in the residual format (`:111–124`, `:751–753`, `:275`):
   - "Heterogeneity: Q = 33.36 (df = 18; P = 0.015); I² = 46.0%; τ² = 0.378."
   - "Residual heterogeneity: Q = … (df = …; P = …); τ² = …; I² = …."
   - "Test for subgroup differences: Q = 2.10 (df = 1; P = 0.15)." Keep the table title "Test of subgroup differences": it is an identity key at `:272,349`. Change the prose only.
3. **P headers:** `:382` header `'p'` → `'P'`. Fit labels: "Heterogeneity p" → "Heterogeneity P", "Between-group p" → "Between-group P", "Test p" → "Test P" (`:277,290,738`). `_row` label `'p-value'` (`:80`) is internal; no change.
4. **One SE header** (`:382`, `_pooled_standard_error` `:708`). Look only at rows that have an SE:
   - All rows share one known scale → header `SE (log scale)` and drop the "SE scale" column.
   - Scales differ, or any row's scale is unknown → keep `SE` plus a column headed `SE scale` with bare values `log`, `logit`, `outcome`, `—`. Strip the parentheses and the word "scale".
   - The scale always remains, in the header or the column, and in Values CSV and Model configuration.
5. **"Pooled odds ratio":** at `:254`, when a non-coefficient row's effect equals the metric (single overall row), the label becomes `f"Pooled {effect_metric}"` with only the first letter capitalized. That gives "Pooled odds ratio", never "Pooled Odds Ratio". Subgroup, term and leave-one-out rows keep their own labels. Reitsma keeps "Summary sensitivity".
6. **References without role prefixes** (`analysis_contracts.R` adds "Fixed-effect inverse-variance meta-analysis: ", "Implementation reference: ", etc.). In `_held_section_content` (`:165`), first record whether a line begins "Implementation reference:" or "Statistical implementation:" (that marks a package citation). Then strip `^[A-Z][^:]{2,60}: ` before display. Python change only; R and goldens stay untouched.
7. **Numbered in-text markers:** RC MetaStudio [1] on the software sentence. Package-implementation references go after the package name: "*metafor* (version 5.0-1) [3]". Remaining method references go at the end of the first pooling sentence, as "[2]" or "[2, 4]". Numbers come from the final References list, so they always match. **Ordering issue (see H):** [1] appears in the *last* Methods sentence, which breaks order-of-first-citation.
8. Smaller report copy:
   - `:531` "Cumulative meta-analysis was performed in current study order." → "Cumulative meta-analysis added one study at a time in study table order."
   - `:55` produces "Confidence intervals (95%) used Knapp-Hartung." Map to "95% confidence intervals used the normal approximation / the t distribution / the Knapp–Hartung adjustment / the modified Knapp–Hartung adjustment."
   - `:381,155` "…for this workflow" → "…for this analysis. See Supplementary details for the full output."
   - `:388`: delete the fragment paragraph "Model comparisons and sensitivity analyses."
   - `:248` "Studies (k) (Subgroup)" → "Studies in {subgroup} (k)".
9. Reference accuracy, verified from memory only (no web access here):
   - Rucker → **Rücker** in two R strings; use `\u00fc` for R ASCII rules.
   - "Progress in Cardiovascular Disease" → "…Diseases".
   - Harbord et al., *Biostatistics* 8(2) is **2007**, not 2006.
   - Reitsma, Harbord, Rutter and bootstrap entries lack DOIs while the others have them.

## F. Remaining optional refinements: implementation spec

- **About runtime, readable** (`about_legal_dialog.py:48,117`): show "Version 0.5.5" then "R 4.5.1 · Qt 6.x.y · Python 3.x.y". Take R from `as.character(getRversion())` (`r_bridge.py:141` already computes it). When R isn't ready, show "R is starting". Drop `platform.platform()` and PyQt from the visible text. Keep the full `R.version.string`, PyQt, platform, library paths and package versions in **Copy debug info**.
- **Fixed-width Copied buttons** (`about_legal_dialog.py:49`, `citation_dialog.py:41`): after creating each button, `button.setMinimumWidth(button.sizeHint().width())`. The idle label is the longer one, so "Copied" can't shrink the button.
- **Two-decimal dimensions:** `plot_export_dialog.py:38` `setDecimals(3)` → `2`. The height label is already `.2f`.
- **Saved DPI fallback** (`plot_export_dialog.py:48`): `int(str(…))` raises on "600.0" or garbage. Use `try: dpi = int(float(str(value))) except ValueError: dpi = 600`, then clamp to the range. The width read at `:21–25` already has this pattern.
- **Logo:** no dark variant exists, so keep the white panel in both themes, as you decided.

## G. Left alone deliberately
- The toolbar label "Export plot" vs the menu label "Export plot…" (your convention).
- The *Publication Bias* navigation label (defined in `CONTEXT.md`).
- Internal `ValueError`/`RuntimeError` texts in validators (`analysis_results.py`, `plot_capabilities.py`, `small_study_effects.py`, `workspace_session.py`, `project_*`) that only appear in Details for developer errors.
- The sample study names in `results_window.py:1891`.

## H. Decisions for you
1. **Reinstall vs repair wording** for the R-start failure (`main_window.py:946`, `r_bridge.py:70`): release users can't "repair the pinned runtime". Do developer builds need the current text?
2. **Data-type prefix in method names** ("Binary Fixed-Effect…" → "Fixed-effect…"). It changes the result identity text, and old screenshots/tests will differ.
3. **Generic subtype name:** "Entered effect" (my recommendation; it matches *Entered effect estimate*) or "Generic effect size".
4. **Single-arm default arm name** "Group" / "Other group" conflicts with the Group term. I suggest "Arm"; for a single arm, is the second default needed at all?
5. **Reference order:** move the software sentence to the start of Methods so [1] is cited first (Vancouver), or accept [1] cited last.
6. **"About RCMS…"**: your refresh doc agreed to this label, but everything else says "RC MetaStudio" (Cite, accessible name). Keep the label or rename it.
7. The domain owner should confirm the F-test wording in B6 and the contour-funnel tooltip in D.
8. **Reference-list style:** `citation_text()` uses "Salman, Ali; Fatima, Kaneez… (2026)." while the method references are APA ("Salman, A., Fatima, K., …"). Harmonize the reference-list entry to APA? The published title stays verbatim either way.

## Coverage
- **Inspected:**
  - All 25 `src/rc_metastudio/forms/*.ui` files.
  - Every user-visible string literal in `src/rc_metastudio/*.py` (AST extraction, read in full).
  - About, Cite, plot export and `manuscript_report.py` read line by line.
  - The R reference/method-name definitions (`r/RCMetaR/R/analysis_contracts.R:111–270`).
  - `application_metadata.py`, `pyproject.toml`, `CITATION.cff`, `README.md`, `NOTICE.md`, `CONTEXT.md`, `docs/ui-refresh-2026-11.md`, and the PyInstaller specs (no description fields).
- **Not reviewed:**
  - User-facing strings generated **inside R**: result section titles, unavailability reasons, the R text output in the Results window, and parameter descriptions from R metadata. I only read the references and method-name lists.
  - `project_format.py`, `project_domain.py`, `r_runtime.py`, `launch.py` and `qt_*` messages (mostly corrupt-file or startup errors).
  - `docs/` beyond the refresh note, `CONTRIBUTING.md`, `docs/release.md`.
  - Rendered layout: I didn't check whether any recommended string fits its widget.
- **Risks:** relabeling trim-and-fill combos or method labels changes values that code compares as strings, so B4, C3, C4 and D's combo item each need the key-based change noted. Expect expected-text test updates for the report formatting in E.
