I did the review read-only: no edits, no agents, no tests. I didn't treat `copy-targeted-matrix.log` as a result.

## Blockers (fix before commit)

1. **File dialog captions are corrupted** (looks like a find-and-replace went wrong):
   - `main_window.py:1199` and `main_wizard.py:212` show "Open project Project" → change to "Open project".
   - `main_window.py:1697` shows "Save project Project" → change to "Save project".
   - `main_wizard.py:674` shows "Import data data" → change to "Import data".
   - While you're on these lines, the filter at `main_window.py:1201,1699` and `main_wizard.py:214` should be "RC MetaStudio projects (*.rcms)" (earlier recommendation C2).
2. **Subgroup and leave-one-out reports list a description as a numbered reference.** `repeated_analyses.R:5–6` add `subgroup_ma_ref` and `loo_ma_ref` ("Subgroup Meta-Analysis: estimates are recomputed…") to References. `_references` strips the "Subgroup Meta-Analysis: " prefix and classes the rest as a method reference. The result is an entry like "3. estimates are recomputed within covariate-defined study groups…", and its number also gets a marker in Methods.
   - Fix at the source: in `repeated_analyses.R:474,762,837,929`, stop appending these two strings to `references`. They aren't citations.
   - Only the historical `docs/ux-audit` goldens contain this text. No R test or Python test does.
3. **The unsaved-changes prompt is wrong for New, Open and Import.** `prompt_to_save_unsaved_data` is shared by `_confirm_close` and `_authorize_destructive_project_action`, so "Save changes to “x” before closing?" appears when nothing is closing. Use "Save changes to “x”?".
4. **The startup R error repeats itself and hides the cause.** `r_bridge.py:70` now raises the same user-facing sentence that `_show_analysis_backend_error(startup=True)` builds. The dialog therefore shows that sentence, then "Details: AnalysisBackendUnavailableError: RC MetaStudio could not start its built-in R runtime…". The real cause (rpy2 failure, missing private runtime) is only in `__cause__`.
   - Fix: restore a technical message in `r_bridge.py:70`, for example `f"Embedded R failed to initialize: {error.__class__.__name__}: {error}"`. Keep the user sentence only in `main_window.py`.

## Latest changes: correctness and taste

**manuscript_report.py**
- **Some package references never get a marker.** The marker regex (`\bname\s+package\b`) misses references written "mada: Meta-Analysis of…" (`analysis_contracts.R:189`). In a Reitsma report, mada's reference gets a number but is never cited in the text, and the method markers skip that number. Match `r'\b' + re.escape(name) + r'(?:\s+package\b|:)'`.
- **The "Pooled" lowercasing can mangle labels.** The regex at `:176` (`\bPooled ([A-Z])`) turns custom metric labels into "Pooled sMD", "Pooled oR" or "Pooled hR". Use `r'\bPooled ([A-Z])(?=[a-z])'`.
- **Repeated supplementary tables still appear.** In the report-15 text, Supplementary Tables 4–6 (Heterogeneity, Test for overall effect, Prediction interval) repeat values already in Tables 1–2. This conflicts with the agreed "omit repeated supplementary tables". `:381` only drops `' — Model Results'` and `' — Study weights'`. Drop that title filter and rely on the `quantities <= represented` check, which already protects tables that weren't transferred intact.
- **Estimator names get a capital mid-sentence.** Methods can read "with the Restricted maximum likelihood (REML) estimator". Lowercase the first letter for ML, REML, EB and PMM, giving "restricted maximum likelihood (REML)", "empirical Bayes" and "median-unbiased Paule–Mandel". Leave the eponyms alone.
- **Double parentheses** in "Between-study variance (τ²) (squared log scale)". Use "Between-study variance, τ² (squared log scale)".
- **Double colon in subgroup heterogeneity**, for example "Male: Heterogeneity: Q = …". Pass `heading=f'Heterogeneity in {subgroup}'` instead of a prefix. The `'Residual '` prefix branch at `:275` is now dead code; delete it.
- **Fragile subgroup-test wording.** The F/Q wording is a `str.replace` on the sentence at `:562`. If that sentence changes, the replace silently stops working. Generate the right sentence once in `_report_methods` and drop line 562. Not a blocker.
- **Things that check out:**
  - The software sentence comes first, with RCMS as [1].
  - CI notation uses "to"; P headers are capitalized.
  - The SE column collapses only when every row shares a known scale; otherwise it keeps bare scale values.
  - Singular forms in the continuity sentence are correct.
  - The Knapp–Hartung and t-distribution wording is correct.
  - "Studies in X (k)" is in place, and the fragment paragraph is deleted.
  - Italics skip "RC MetaStudio (version …; …)" because of the `;` guard.
- **Known limits, accept or defer:**
  - All method references attach to the first pooling sentence. In small-study reports, Egger and trim-and-fill get cited on the pooling sentence.
  - With several packages, numbers follow reference order, not the order of names in the sentence.

**small_study_effects_dialog.py**
- **The label/value separation still isn't done.** `:69` still says "Primary test Classical Egger (…)". Use `"Primary test: "` / `"Primary tests: "` and `"Exploratory test: "` / `"Exploratory tests: "` (earlier item D).
- The trim-and-fill combos switched to `addItem(label, value)` and `currentData()`, and the plurals and tooltips are fixed. No test or driver selects these combos by their old raw text, so that change is safe.

**About, Cite and errors**
- About shows "R 4.6.2 · Qt 6.12.0 · Python 3.14.10". It's concise, the debug clipboard keeps the full detail, and the Copied buttons have fixed widths. Good.
- `app_error_handler.py:15` leaves a trailing space before `\n\n`. Delete it.
- The title "Project saved; save status uncertain" is clumsy. Use "Project saved, but not confirmed".
- `main_window.py:551`: once startup fails, "R is starting" stays on screen permanently, which is false. Use "R is not ready".
- The non-startup backend message still says "backend" and "build the analysis settings". Use "R is not available, so the analysis settings cannot be opened."

## R-generated strings: what users actually see

**Parameter tooltips.** These come from R `description` fields via `parameter_description` and appear as label tooltips and accessible descriptions. They're duplicated across about 12 R method definitions. The minimal fix is one description map in `analysis_method_labels.py` next to the existing labels. Fold the two special cases in `_parameter_label` (`rm.method`, `estimator`) into that map too.

| Parameter | Current text | Replacement |
|---|---|---|
| `to` | Multi-line text naming a nonexistent "Add correction factor" option with values "only 0"/"all" | "Which studies receive the continuity correction." |
| `to` (ratio) | "metafor correction target, resolved once before subset analyses." | Same as above |
| `adjust` | "Constant c that is added to the entries of a two-by-two table." | "Value added to each cell of a 2×2 table that needs correction." |
| `conf.level` | No final period | "Confidence level for intervals." |
| `digits` | "…p-values use at least 3" | "Decimal places for estimates and intervals. P values show at least 3." |
| `inference.method` | "Procedure used to compute…" | "Method for tests and confidence intervals." |
| `drop00` | Label says "groups" | Label "Exclude studies with no events in either arm". The description is fine apart from "groups" → "arms". |

The R `to.names` entry `if0all` still says "All studies if any study has zero events". Python overrides it, but correct the R text too, or confirm it never appears.

**Small-study unavailability reasons.** These are shown verbatim in the dialog.
- `small_study_effects.R:121–122`: "REML log-OR tau^2" → "τ² (REML, log odds ratio)". So `:122` becomes "Unavailable: τ² (REML, log odds ratio) is above 0.1; use Rücker AS+RE."
- `:626`: "Heterogeneity (REML tau-squared): " → "Heterogeneity (τ², REML): ".
- `:220`, `:224`: "effect-SE artifacts" is jargon. Reuse the plain wording already at `:596` and `:600`.

**Reitsma** (visible table titles and notes):
- `:847,1188`: "Diagnostic I-squared" → "Diagnostic I²". `:850,1190`: "I-squared" → "I²". Seven tests reference these strings and need updates.
- `:289`: "Zhou-Dendukuri" → "Zhou–Dendukuri".
- `:859`: "Not provided by mada::AUC(); no invented AUC CI." → "No confidence interval is available for the AUC."
- `:794` and `:858` say the same equivalence sentence twice. Keep one.

**Title-case section titles.** Examples: "Cumulative Summary", "Subgroup Summary", "Ordinary Funnel Plot", "Regression Plot", "Moderator Coefficients", "Adjusted Means", "Bootstrapped Meta Regression Summary", "PPV and NPV by Prevalence". These are also identity strings in tests: 14 tests reference "Ordinary Funnel Plot" and 10 reference "Regression Plot". Treat sentence-casing them as a separate pass. Don't fold it into this commit.

**Internal, leave alone:** `stop()` and validator texts, `rcmetar-core.R:630` "Inference Method" (it's a results key), class names, and plot-capability errors. These only reach Details.

## Startup and corrupt-file messages
- **Corrupt-file errors show raw parser text as the main message.** `_format_open_project_error` shows `ProjectFormatError` and `ProjectAdapterError` text as body prose, so users read things like "manifest.json: missing integrity for data.json" or "events cannot exceed the group total". Replace with:
  - Body: "This file is damaged or is not a valid RC MetaStudio project. Open another .rcms file or restore a backup.", with the raw message under "Details:".
  - Special case "unsupported project format version" as "This project was saved by a newer version of RC MetaStudio. Update RC MetaStudio to open it."
  - Special case "cannot read project" as "RC MetaStudio could not read this file. Check that it exists and that you can open it."
- `r_runtime.py`, `launch.py` and `qt_*` are developer and Details-level text, apart from the splash messages ("Starting R…", "Loading metafor…"), which are fine.

## Earlier audit items still missing
- `continuous_data_dialog.py:116`: "Insufficient Arguments".
- `continuous_data_dialog.py:1496–1498`: "back calculation" and "Please choose one of the following:" (C7).
- `diagnostic_data_dialog.py:392`: now uses `.text()`, but still says "Could not convert %s to int" (B1).
- `analysis_setup_dialog.py:735`: "RCMetaStudio - Plot Path" (C2).
- `main_window.py:1067`: "effect-size measure or calculator metric" (C5).
- `r_bridge.py:256`: "Please install".
- `dataset_table_view.py:104`: "Gold marks…" accessible description.
- `results_window.py:1839`: "No Results" title.
- `publication_bias_dialog.ui:5`: still "Publication Bias - RC MetaStudio".
- Decisions still open: H4 (the "Group"/"Other group" default arm names at `analysis_catalog.py:142`) and H8 (reference-list style).
- Everything else I checked from C1, C3–C9, D and F looks done.

## Bibliography: verify against primary sources (no fixes proposed)
From memory only, so treat each as a lead, not a finding:
- "Rucker" should probably be "Rücker" at `analysis_contracts.R:163,271`.
- "Progress in Cardiovascular **Disease**" may need to be "Diseases".
- Harbord et al., *Biostatistics* 8(2): the year may be 2007, not 2006.
- The Lau 1992 entry in `repeated_analyses.R:4` is in a different citation style ("Lau, Joseph, et al.", "327.4 (1992)").
- Doebler (2025) mada 0.5.12: check the year and format.
- The Sterne & Egger 2005 chapter has no editors listed.
- Reitsma, Harbord, Rutter, Thompson & Sharp and the bootstrap books have no DOIs.
- Check whether Hedges (1983) belongs among the DerSimonian–Laird references.
- The RCMS entry uses "Salman, Ali; …" while the method references use APA (H8).
- *meta* is listed in Methods but has no reference entry.

I didn't check rendered layout for the new strings, the R text pane output beyond titles and reasons, or anything after the uncommitted files changed mid-read. `manuscript_report.py` changed while I was reviewing; I re-read the parts that matter. The commit still depends on the final matrix.
