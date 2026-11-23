# RC MetaStudio User Guide

This guide covers entering or importing study data, running meta-analyses, and exporting figures, reports, and exact numeric tables. For a guided example, see [Your first meta-analysis](tutorials/first-analysis.md). For domain definitions, see [CONTEXT.md](../CONTEXT.md).

## Projects and outcome sheets

- **Start a project** from the Welcome page or **File**:
  - **File > New project…** creates a project and walks through selecting the first outcome's data type, effect measure, and outcome name.
  - **File > Open…** opens an existing `.rcms` project.
  - **File > Open sample project** opens any of the nine bundled published examples (also available from **Open a sample project** on the Welcome page when you have no recent projects). Editing and pressing **Save** on a bundled sample opens **Save as…** so you keep your own copy without modifying the sample.
  - **File > Import data…** imports CSV, Excel (`.xlsx`), or RevMan 5 (`.rm5`) files.
- **Outcome sheets:** A project holds one or more independent outcome tabs at the bottom of the workspace. Each outcome has its own study rows, data type, arm names, covariates and analysis settings. Add or rename sheets via **Project > Add outcome…**, **Project > Rename outcome…**, the `+` button beside the tabs, or the tab context menu. Switch sheets with `Ctrl+PgUp` / `Ctrl+PgDown`. Switching sheets does not mark a saved project as modified.
- **Saving:** `.rcms` files store study data, covariates, and analysis settings. Export plots and reports to keep the results of a run. See [Project file format](project-format.md).
- **Undo / Redo:** Workspace history retains the last **100** committed edits (`Ctrl+Z` / `Ctrl+Y`). Failed operations roll back without altering the sheet.
- **Appearance:** Switch between **System**, **Light**, and **Dark** themes under **View > Theme**.

## Entering data and using study calculators

Choose a data type in the New project / Add outcome wizard:

| Wizard category | Input shape | Supported effect measures |
| --- | --- | --- |
| **One arm per study** | **Proportion** (events, total) | `PR`, `PLN`, `PLO`, `PAS`, `PFT` |
| | **Mean** (N, mean, SD or mean, SE, N via calculator) | `Mean` (metafor `MN`) |
| | **Regression coefficient** (coefficient, CI) | `Mean` (generic IV on supplied scale) |
| | **Entered effect estimate** (estimate, SE) | `Mean` (generic IV on supplied scale) |
| **Two arms per study** | **Two-arm binary** (events and totals per arm, or entered effect) | `OR`, `RR`, `RD`, `AS`, `YUQ`, `YUY` |
| | **Means** / **Standardized mean difference** (N, mean, SD per arm, or entered effect) | `MD`, `SMD` |
| | **Time-to-event and event rates** (reported HR/CI or log-HR/SE; raw IRR events + person-time or reported IRR/CI or log-IRR/SE) | `HR`, `IRR` |
| **Diagnostic test accuracy** | **Diagnostic** (`TP`, `FN`, `FP`, `TN`, or univariate estimates) | `Sens`, `Spec`, `PLR`, `NLR`, `DOR` |

- **Study-level calculators:** Click a study's row number (or press `F4` with the row selected) to open the study calculator for that row. Calculators derive effect estimates and standard errors from reported statistics, support partial-count completion and missing-summary reconstruction (including pre/post continuous inputs with a paired correlation), and preserve full numeric precision.
- **Arm names and direction:** Rename arms from the column headers, reverse arms via **Project > Swap intervention and control**, and set clinical benefit direction via **Project > Effect direction** (used in forest labels, reports, and one-sided TSA).
- **Confidence level:** Change the sheet's default output confidence level via **Analysis > Change confidence level…** or the status-bar confidence button (for example `95% CI…`). Individual analyses can override it. Changing output confidence does **not** alter reconstructed study standard errors from a reported source confidence interval.
- **Covariates:** Add numeric or categorical covariates with **Project > Add covariate…**. Right-click a covariate header to rename, delete, or convert between continuous and categorical copies.

### Hazard ratios (HR) and incidence rate ratios (IRR)

HR, IRR, and binary risk ratios (`RR`) are distinct data types. Bundled examples are `Time-to-event (HR) - Head and neck cancer, Pignon 2000` (65 trial results) and `Event rates (IRR) - Catheter infections, Niel-Weise 2008` (9 studies).

- **Reported HR or IRR:** Open the study row dialog and choose **Ratio and confidence interval** (with the publication's original **Source CI (%)**, defaulting to 95%) or **Log ratio and standard error**. Switching formats converts the point estimate; supply uncertainty in the selected format. Known non-Wald intervals should be entered as log ratio and SE.
- **Raw IRR:** Choose **Events and person-time**. Events are nonnegative integers (recurrent events allowed); person-time must be positive and share one declared unit (default `person-years`) across both arms of a study. Different studies may use different units without automatic conversion.
- **Mixed raw and reported IRR:** A sheet may contain both raw and reported IRR studies for inverse-variance pooling. If a study has both inputs, select the intended source explicitly in its dialog. Inactive inputs survive save/reopen, and an incomplete selected source never silently falls back to the other.
- **Zero-event IRR studies:** The table preview uses a 0.5 correction and the sheet confidence level. Analysis settings govern the fit separately. Double-zero raw IRR rows display **Not estimable** (`—`) in the table preview. Under inverse-variance pooling, the configured continuity correction applies; under **Mantel–Haenszel** (available when every included study selects complete raw inputs), pooling uses original counts and excludes double-zero studies. **Use correction in pooling** applies to binary fixed-effect Mantel–Haenszel. Subsets with zero total events in either arm remain non-estimable.
- **Interpretation:** Inverse-variance models use log effects and log-scale uncertainty. Reported intervals are converted using the full log interval width and the source confidence level. Check the report for rounded or asymmetric Wald interval warnings. Forest plots have a null ratio of 1 and use logarithmic geometry. Raw IRR Mantel–Haenszel supports fixed pooling and sequential/subgroup fits.
- **Scope limits:** HR reconstruction from Kaplan–Meier curves, log-rank statistics, or IPD and Poisson GLMMs are not currently supported.

## Importing data (CSV, Excel, and RevMan `.rm5`)

Open **File > Import data…** (or **Import data** on the Welcome page) and select a `.csv`, `.xlsx`, or `.rm5` file. Every import shows a preview before replacing the project; **Cancel** leaves the current project unchanged.

### CSV and Excel (`.xlsx`)

- Map columns to required study fields and optional covariates in the import wizard. CSV supports custom delimiters, quote characters, and UTF-8 / BOM headers.
- **Excel limits:** `.xlsx` import accepts worksheets up to **100,000 rows**, **512 columns**, and **1,000,000 cells** (including distant formatted cells in the declared extent). Trim unused rows or columns in Excel if a workbook exceeds these limits. Formulas import their last saved cached values. Save the calculated workbook before importing.
- **HR and IRR CSV columns:** Required columns are `Study Name,Year,HR,Lower,Upper` for HR, and arm `Events` and `Person-time` columns before `IRR,Lower,Upper` for IRR (leave the unused source blank). Optional named columns after the required fields:

| Optional column | Default | Applies to |
| --- | --- | --- |
| `SE of log effect` | Empty | HR, IRR |
| `Input scale (ratio/log)` | `ratio` | HR, IRR |
| `Source CI (%)` | `95` | HR, IRR |
| `Effect source (raw/reported)` | Empty (required if both present) | IRR |
| `Person-time unit` | `person-years` | IRR |

These synthetic CSV files demonstrate the input format: [`hr.csv`](examples/hr.csv), [`irr-raw.csv`](examples/irr-raw.csv), and [`irr-mixed.csv`](examples/irr-mixed.csv). Include headers for advanced fields. Headerless imports use the defaults. The raw CSV holds the supplied scale, while copied table cells show the ratio. Use a project file to retain the original inputs and inactive sources.

### RevMan 5 (`.rm5`)

Review the proposed outcome sheets, method mappings, and **Not imported** items before accepting. Review prose, references, risk-of-bias tables, and embedded graphs are not imported.

| RevMan 5 input | RC MetaStudio mapping |
| --- | --- |
| Binary `OR`, `RR`, or `RD` | Two-arm binary sheet with ordered intervention/control arms |
| Continuous `MD` or `SMD` | Two-arm continuous sheet (`N`, mean, SD per arm) |
| Fixed MH / Fixed IV / Fixed Peto OR | Binary Mantel–Haenszel / Binary or continuous IV / Binary Peto |
| Random IV | Binary or continuous random effects (`DL`) |
| Random MH | No exact mapping; retained default disclosed in review |
| Generic IV (`HR`, `OR`, `MD`) | Time-to-event, binary, or continuous entered effect and SE (`LOG_DATA=YES` logged once; `NO` kept on analysis scale) |
| Diagnostic test counts | One diagnostic sheet per test (`TP`, `FN`, `FP`, `TN`); diagnostic analyses/covariates not imported |
| Subgroup structure | Categorical covariate (ungrouped rows keep blank values) |
| Free-text IV measures; IPD `O−E` / variance | Listed under **Not imported** |

Import restores sheet confidence and the effect measure. Missing or non-integer years stay blank. A named study with no data and both totals zero remains pending until completed. Repeated outcome names get numbered suffixes. Hover over a tab for its full name. See [fixture provenance](../tests/fixtures/rm5/README.md) for the upstream examples and diagnostic XML structure.

**Statistical differences to review:** Importing a method setting does not guarantee bit-for-bit parity with RevMan. In particular, continuous `SMD` uses `metafor`'s exact Hedges correction and variance rather than RevMan's adjusted-*g* approximation (for example, on the public Fleiss 1993 Mental health outcome, `metafor` gives `-0.3440` vs `-0.3434` from `meta::metacr`), and fixed-effect subgroup-difference tests follow the pinned authority package. Inspect the imported setup and report before publishing.

- Fixed-effect Mantel–Haenszel imports turn on **Use correction in pooling** with a correction of 0.5 for zero-cell studies. The import review shows this under **Imported settings**. You can turn it off under **Advanced**.
- RevMan 5 random-effects Mantel–Haenszel uses Mantel–Haenszel heterogeneity to estimate between-study variance. The import review flags this method as unavailable and Analysis setup retains its default.
- Fixed Peto imports use original counts for individual effects and pooling, as in RevMan.

## Running analyses

All analyses live under the **Analysis** menu (and the toolbar **Analyses** split button). Unavailable actions remain visible with a tooltip explaining what is needed (for example, adding a categorical covariate before subgroup analysis). Missing or incomplete study inputs are shown before fitting, and Results distinguish **included** studies from **contributing** studies.

### Effect-size measure

Change the active sheet's effect measure via **Analysis > Effect-size tools > Two-arm metrics** or **One-arm metrics**, or inside the analysis setup dialog. Changing the measure updates derived previews without altering your raw study counts or means.

### Standard meta-analysis (`Analysis > Meta-analysis…`, `Ctrl+R`)

- Choose **Analysis method** (random-effects defaults to **REML**; fixed-effect inverse variance, Mantel–Haenszel, and Peto appear where eligible), **τ² estimator** (`REML`, `DL`, `PM`, `PMM`, `EB`, `SJ`, `ML`, `HE`, `HS`, `HSk`), **Confidence level**, and under **Advanced**, **Inference method** (`Normal approximation`, `t`, `Knapp–Hartung`, `Modified Knapp–Hartung`) and continuity-correction settings.
- By default, fixed-effect **Mantel–Haenszel** pooling uses the original study counts and applies the continuity correction only to individual study effects. Turn on **Use correction in pooling** under **Advanced** to apply the continuity correction to the pooled estimate as well (switched on automatically for fixed-effect Mantel–Haenszel outcomes imported from RevMan `.rm5` files).
- **Diagnostic accuracy:** Select one or more diagnostic metrics. Choosing paired sensitivity and specificity fits the count-based **`mada` Reitsma bivariate model** (`REML` default, or `ML`), producing paired summary operating points, SROC curves, joint prediction regions, SROC AUC / normalized partial AUC, sampling-based likelihood ratios and DOR (`mada::SummaryPts()`), and named diagnostic I² statistics. Univariate models remain available for individual metrics.

### Cumulative and leave-one-out analyses

Cumulative analysis fits successive prefixes of an ordered study sequence.
Leave-one-out analysis fits the included studies after omitting one study at a
time. Both use the selected statistical authority package for estimates,
intervals, study counts and heterogeneity.

#### Choose the analysis sequence or figure order

In cumulative setup, **Add studies in** selects table, publication-year or
individual study-effect order before fitting. Changing it reruns the prefix
fits: intermediate subsets can change, while the final full fit uses the same
included studies. Missing years go last; ties retain table order. A source with
no publication years is not a chronological sequence. Saved plot editing shows
the stored sequence and explains that changing it requires a rerun. **Change
settings** carries appearance into the new run; Cancel or a failed run preserves
the existing result. A package failure must not silently change the estimator.

Leave-one-out **Row order** changes presentation by table, year, pooled effect
after omission, or I² after omission, lowest first. It never changes subset
membership or fit quantities. A genuine all-studies reference stays first,
including HR/IRR. Older omission-only bundles remain regenerable; their first
omission is not a reference row and must participate in ordering. Weight order
is not a leave-one-out option. Sort unrounded values, preserve table order for
true ties, and put unavailable values last.

#### Read the figure and report

Forests retain each style's fonts, markers, colors and banding. Columns show
study label, package-reported k, optional I², forest, and effect/CI. A full-fit
reference has a bold label and separator. Cumulative labels do not repeat k when
it has its own column. I² uses one decimal consistently in the figure and table.
Hiding the figure's I² column does not remove it from the table.

Use each package fit's k; it can differ from the number of defined individual
effects (`k.yi` in metafor). MH/Peto can retain four studies in k when one of four
individual effects is unavailable because of double-zero events. Do not replace
a package-reported singleton I² merely because k equals one. Genuinely missing
fields remain unavailable.

The sequential table identifies **Step / Study added** or **Study omitted** and
retains every fit, confidence interval, k and available I² in analysis order.
Diagnostic metrics stay separately identifiable. Figure captions state the
independently editable display order. Combined interval cells retain their raw
lower and upper quantities for CSV export.

Results prose gives the cumulative sequence and final fit, or the leave-one-out
full fit and descriptive omission range with named endpoints. It counts
successful fits explicitly and retains failed/non-estimable rows in the table.
It does not repeat an ordinary pooled-effect sentence for every row or infer
robustness, causation, study exclusion, or an influence threshold from P values.
Screen, clipboard, PDF and DOCX use the same report content.

For context, [dmetar InfluenceAnalysis](https://dmetar.protectlab.org/reference/influenceanalysis)
illustrates effect- and I²-sorted leave-one-out diagnostics. The project glossary
in [CONTEXT.md](../CONTEXT.md) defines the domain terms.

### Subgroup analysis and meta-regression

- **Analysis > Subgroup meta-analysis…** requires at least one categorical covariate. Subgroup-difference `Q` tests compare the displayed subgroup estimates and standard errors.
- **Analysis > Meta-regression…** supports numeric, categorical (with selectable reference level), and multiple moderators under fixed- or random-effects univariate models, as well as additive Reitsma bivariate meta-regression for diagnostic counts (with likelihood-ratio moderator block tests and separate sensitivity/specificity coefficient plots). For HR and IRR, coefficients and SEs are reported on the log scale alongside exponentiated multiplicative ratios.

### Small-study effects (`Analysis > Small-study effects…`)

Opens a guided dialog whose available procedures are computed directly by `RCMetaR` from the current effect measure, data completeness, and study count:

- **Primary and exploratory asymmetry tests:** Selected by data family and measure (for example, Harbord primary with Rücker/Peters exploratory for raw two-arm OR; classical Egger primary with Pustejovsky–Rodgers exploratory for raw SMD; classical Egger/Begg and mixed-effects Egger for MD, HR, IRR, and generic effects; Deeks' test for complete diagnostic counts). Minimum study count defaults to `meta`'s `k.min` (typically 10) and can be explicitly adjusted down to 3 where supported.
- **Plots and sensitivity analyses:** Ordinary funnels, contour-enhanced funnels (significance contours centered on the null), trim-and-fill sensitivity analysis (auto/left/right side, L0/R0 estimator), precision-limit extrapolation, and diagnostic Deeks effective-sample-size funnels.
- **Interpretation:** Funnel asymmetry can arise from heterogeneity, selective reporting, methodological differences, or chance; it does **not** by itself prove publication bias. Trim-and-fill and infinite-precision extrapolations are assumption-dependent sensitivity analyses, not bias-corrected true effects.

### Trial Sequential Analysis (`Analysis > Trial Sequential Analysis…`)

Available for two-arm binary outcomes (`RR`, `OR`, `RD`, Peto `OR`), `MD`, and reported `HR`. See the dedicated [Trial Sequential Analysis guide](trial-sequential-analysis.md) for design assumptions, diversity (`D²`) adjustment, Lan–DeMets spending boundaries, futility wedges, penalized Z-curves, sensitivity tables, and differences from Copenhagen Trial Unit TSA.

## Inspecting, editing, and exporting results

The Results window contains a left navigation tree and a main viewer:

- **Figures (forest, bubble, funnel, SROC, coefficient, TSA):**
  - Open at their natural export width; adjust view with **Zoom**, **Fit page** (`Ctrl+0`), and **Fit width** (`Ctrl+Shift+0`).
  - Choose **Edit plot…** (`Ctrl+E`) to change style (**Default**, **BMJ**, **RevMan**), labels, captions, colors, axis limits, point scaling, or leave-one-out row order. **Apply** redraws the figure through R without changing the fitted model; **Cancel** discards unapplied edits.
  - Choose **Export plot…** (`Ctrl+Shift+E`) to save **PDF** or **SVG** (vector) or **PNG** or **TIFF** (raster with LZW compression and configurable physical dimensions and DPI).
- **Text report:** Formatted Methods, Results, numerical tables, numbered references (citing RC MetaStudio and the implementing R packages), and Model configuration. Copy individual sections from **Edit** or save the full report to **PDF** or **Word (`.docx`)** via **Export report…** (`Ctrl+Shift+S`).
- **Data tables (CSV):** Select any result table to copy cells (`Ctrl+C` or **Copy table**), export display strings (**Export formatted CSV…**), or export unrounded numeric quantities with their analysis/display scales and confidence levels (**Export values CSV…**).
- **Rerun with modified settings:** Choose **Change settings…** (`Ctrl+Shift+R`) to reopen setup against the originating sheet and replace the displayed result once the new fit succeeds (cancelling or failing keeps the current result intact).

## Citing RC MetaStudio and getting debug info

- **Help > Cite…** displays the formatted citation and exports BibTeX, RIS, and EndNote records.
- **Help > About RCMS…** shows the RC MetaStudio, Python, Qt, and R versions, links to `NOTICE.md` and the issue tracker, and provides **Copy debug info** for bug reports.
