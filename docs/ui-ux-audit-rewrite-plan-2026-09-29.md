# RC MetaStudio: UI/UX audit and rewrite blueprint

**Review date:** September 29, 2026  
**Repository:** AliSalman-et-al/rc-metastudio  
**Audited revision:** `master` at `68c7a41ee94effcd934a49db9557802d0b32e977`  
**Revision date:** September 28, 2026  
**Deliverable:** Source-based audit and implementation plan; no repository changes made.

## 1. Decision

Rewrite the interaction and presentation layers around a single research workflow:

**Prepare data → Configure an analysis → Inspect results → Revise or export.**

Retain PyQt6, the existing statistical implementations, the RCMetaR facade, validated project storage, domain identities, and the sound parts of the plotting infrastructure. Do not replace the statistical engine, port the application to a browser, or wrap the existing interface in another framework. The major change is to make an analysis a persistent, understandable object rather than a sequence of dialogs ending in a temporary graphics window.

The central implementation priority is a **structured results workspace**. It should provide consistent navigation and actions, while giving cumulative analysis, leave-one-out analysis, subgroup analysis, meta-regression, and diagnostic models genuinely different presentations where their scientific meaning differs.

### Evidence and limits

This review traced the main application entry points, configuration and execution routes, results viewer, result/request contracts, plotting actions, CSV import, portions of the data workspace, project schemas, R dispatch, representative R result producers, diagnostic implementation, and selected testing infrastructure. The repository's canonical form manifest was also inspected. Its 29 entries are not a count of every programmatically created application surface.[^manifest]

This is **not a claim that every repository file was reviewed line by line**, nor a native cross-platform usability, screen-reader, performance, or numerical-validation run. A local checkout and runnable PyQt6/rpy2 environment were not available for this review. Findings below distinguish directly observed source behavior from usability hypotheses that require execution or user testing. No screenshots, test passes, usability scores, or latency measurements are invented.

### What already deserves preservation

The source already has immutable result/request contracts; explicit semantic section IDs and plot capabilities; label-to-control accessibility associations; adaptive sizing and native layout policies; transactional project edits; atomic validated saves; diagnostic per-metric failure isolation; and plot-edit commit failure handling. These are foundations to use, not reasons to start again indiscriminately.[^contract][^adapter][^setup][^layout][^project][^viewer][^execute]

## 2. Source-grounded findings

Priority meanings: **P1** is central to reliable task completion or scientific understanding; **P2** is important consistency, discoverability, or maintenance work. These are proposed implementation priorities, not measured incident severities.

| ID | Priority | Evidence and observation | User consequence | Required change |
|---|---|---|---|---|
| F01 | P1 | `ResultSection.kind` only supports text/image and its value is a string. `ResultsWindow` paints these into a `QGraphicsScene`.[^contract][^viewer] | A result table is primarily a visual arrangement of text, not a navigable, sortable, exportable table of statistics. | Extend the existing versioned result contract with typed numerical blocks and render them with native widgets. |
| F02 | P1 | `AnalysisSetupDialog._run_analysis()` reaches `done(Accepted)` in its final cleanup even after failure; `done()` disposes the dialog.[^setup] | Users lose their open configuration after an error and must reconstruct a retry. | Preserve the draft and show an actionable inline failure. Accept/close only after successful completion and delivery. |
| F03 | P1 | Setup calls the operation synchronously; service methods call the R bridge directly; the progress dialog itself is only a dialog wrapper.[^setup][^execute][^progress][^bridge] | The inspected route has no asynchronous execution handoff. Long-running work risks blocking interaction and meaningful progress feedback. Latency was not measured. | Move execution, expensive preparation, and regeneration behind one owned R worker process. |
| F04 | P1 | `add_image_section()` returns without rendering a section when `artifact.can_display()` is false.[^viewer] | A missing plot can disappear without a visible explanation, making the report look more complete than it is. | Keep the section and display its artifact failure independently of numerical results. |
| F05 | P1 | Main-window context cycles through outcome, follow-up, and group using the same navigation controls.[^main] | Users must remember the current mode before interpreting an arrow or the add action. | Replace mode-switching with simultaneous labeled context selectors. |
| F06 | P1 | Standard, diagnostic, subgroup, and small-study-effects workflows take different dialog chains and use a mixture of modal and nonmodal presentation.[^main][^bias] | Repeated choices and inconsistent navigation make related tasks feel unrelated. | One retained analysis draft/editor, with dedicated family-specific sections. |
| F07 | P1 | Plot edit/export actions are constructed in the plot context menu. Body text uses a fixed-width font and a two-step right-click copy tooltip.[^viewer] | Important actions are hidden; the primary report resembles technical output rather than a research workspace. | Visible plot toolbar, table copy/export, proportional report typography, raw output in Details. |
| F08 | P1 | Results navigation connects `itemClicked` to canvas centering in the inspected viewer.[^viewer] | Keyboard selection may not navigate the report equivalently. This is a source-level accessibility risk, not a reproduced screen-reader result. | Selection-driven navigation with explicit focus behavior and keyboard tests. |
| F09 | P1 | Project v1 stores dataset and portable current selection, but has no analysis-run history/result model.[^schema-project][^schema-state] | Saving a dataset is not the same as preserving the analyses and figures produced from it. | Add versioned, portable saved analyses with immutable input/specification provenance. |
| F10 | P1 | CSV headers must match exact required names/order. Blank years fail integer validation even though the project schema permits null years.[^csv][^schema-project] | Users reshape their files to fit RCMS instead of mapping their data; ordinary nonchronological analyses encounter unnecessary import barriers. | Map columns, review inferred types, preserve missing years, and validate ordering only when needed. |
| F11 | P1 | `_covariate_type()` returns factor when any value cannot convert to float, including an empty string.[^csv] | A numeric moderator with missing values can be inferred as categorical. | Ignore recognized missing markers during inference; require review; validate finite numeric values separately. |
| F12 | P2 | `AnalysisRequest.semantic_id` includes all parameters; setup adds `fp_*`/`bp_*` appearance and output-path parameters.[^adapter][^setup] | Statistical identity and presentation identity are mixed. This is not evidence of an existing cache bug. | Separate effective statistical specification, presentation settings, and execution identity. |
| F13 | P2 | Method lists are reverse-sorted by display label, with a special eligible-Reitsma promotion.[^setup] | Ordering and initial selection are not a clearly stated analytical policy. | Explicit, reviewed default-selection rules and meaningful grouping; preserve existing saved choices. |
| F14 | P2 | Hardcoded blue rich-text outcome styling and generic Warning/Yes/No/technical-dialog error copy remain in main-window paths.[^main] | Appearance and recovery language are inconsistent even where shared layout/accessibility work is good. | Semantic colors, explicit action labels, and consistent user-centered recovery copy. |

### Important counter-findings

Do not describe RCMS as having no accessibility work, no persistence safety, no editable plots, or no diagnostic error isolation. Those claims would be contradicted by the inspected code. Likewise, the R layer already exposes useful numerical objects: cumulative output includes `res$summary.table`, and ordinary summaries retain model result objects. The rewrite should preserve that information across the boundary rather than reconstruct it from formatted strings.[^results-r][^sequential-r]

## 3. Product model and information architecture

### 3.1 One project, two main destinations

Use **Data** and **Results** as the primary destinations. Analysis setup is a retained draft within that workspace, not a third disconnected application.

A project contains the working dataset, named analysis specifications, completed analysis records, and portable presentation choices. Machine-specific placement and caches remain outside the project. A completed result always belongs to the input and effective settings used for that execution—not to whatever happens to be selected now.

A result may be detached into a separate native window for a second monitor. It uses the same result view and commands; it is not a second implementation. Closing a detached viewer does not delete the saved analysis.

### 3.2 Startup

Provide four clear routes: **Open project**, **Import CSV**, **Create dataset**, and **Open example**. Show recent projects directly with readable names and a secondary location. Do not make a recent-project menu the only discovery route. Retain the existing queued startup behavior that avoids problematic early nested modal loops.[^main][^wizard]

For import, choose the file before requiring detailed methodological decisions. Then establish data family and input representation: binary counts, continuous summaries, diagnostic counts, or entered effects with uncertainty. Use one/two study arms only where that distinction is meaningful. A supplied regression coefficient is an effect-estimate input—not necessarily a one-arm clinical study.

### 3.3 The data workspace

Show a compact context strip above the grid:

```text
Outcome [Mortality ▾]   Time point [12 months ▾]
Study arms [Treatment ▾] versus [Control ▾]   Effect measure [Risk ratio ▾]

[Import CSV] [Add study] [Add variable]                 [Set up analysis]

Study | Year | Include | Treatment events | Total | Control events | Total | …
```

For single-arm data, show only the selected arm. For diagnostic counts, show TP/FN/FP/TN rather than artificial treatment/control controls. All current context remains visible when configuring an analysis.

Replace the ambiguous mode-dependent add button with explicit actions. Distinguish **study arms** from **subgroups**, because they represent different concepts. Include search/select controls for long outcome, time-point, and arm lists; arrows may remain optional shortcuts, never the only route.

Changing the reference arm, metric, outcome, or time point changes the intended analysis. Changing column widths does not. The interface must make that distinction visible.

### 3.4 Spreadsheet editing and calculators

Preserve the existing model/view investment and transactional editing. Improve the interface around it rather than creating another dataset representation.[^table]

Keep routine entry in the grid. Put detailed study editing and back-calculation in an explicit **Edit study data** surface. In calculators, separate **Entered values**, **Calculated values**, and **Apply to study**. Calculated previews do not silently become authoritative entered data. Show the method and assumptions next to the derived value.

Pasting a rectangle should be one validated, undoable operation. A failed paste must leave the prior dataset and useful selection intact. Row exclusions should have a visible reason and distinguish deliberate exclusion from missing/ineligible data. Sorting the display must not silently alter a saved cumulative-analysis order.

Expose data issues in one review panel with study, field, value, problem, and corrective action. Avoid modal error dialogs for every invalid cell. Preserve cell context when correcting a problem. Deletion of a study should be reversible; broader destructive actions should name the affected data and provide explicit safe choices.

### 3.5 Import mapping and validation

Replace exact-header matching with a staged pipeline: **read → map → validate → preview → commit**. A mapping is a small typed object, not a generalized ETL framework.

The mapping view shows the source column, selected RCMS field, example values, and inferred type. Users can leave irrelevant columns unmapped. Recognized missing values remain missing; zero is a value, not a missing marker. Distinguish parsing errors, missing optional values, and invalid domain values.

A blank year is valid stored data. When the user chooses chronological cumulative analysis, require an explicit missing-year policy or corrections before running. Do not globally reject the dataset. This aligns import behavior with the existing nullable-year schema.[^csv][^schema-project]

Use an explicit text-encoding policy, handle UTF-8 BOMs, and show decoding failures with a recovery action. Support the currently advertised CSV workflow and spreadsheet paste first; adding a native Excel-file engine is a separate scope decision, not necessary for this rewrite.

## 4. Analysis configuration and state

### 4.1 One retained analysis editor

The editor has a stable heading such as **Configure meta-analysis** or **Configure subgroup analysis**. Show a plain-language summary of the current analysis context at its top.

Present core scientific choices first: analysis type, effect measure, model, estimator/inference where applicable, and confidence level. Reveal study ordering, subgroup variable, or moderators only for the corresponding workflow. Put detailed corrections and other advanced method parameters in an expanded-on-demand section. Figure appearance belongs primarily beside the resulting figure, not on the critical path to the first calculation.

Do not hide consequential settings just because they are advanced. The review summary must disclose the effective estimator, inference, corrections, and input selection before execution. Use the R facade as the method-capability authority, extending it to return availability reasons rather than maintaining a contradictory UI-only registry.[^core]

Persist a draft when users move between Data and Results. A failed run leaves the draft editable. Esc or Close preserves or explicitly discards a draft according to a consistent policy; it never silently discards entered setup values.

### 4.2 Capability and availability states

Use one explicit vocabulary:

- **Available:** supported and the current data meet requirements.
- **Needs data:** supported, but specified required information is missing.
- **Not supported for this analysis:** not implemented for the selected family/workflow.
- **Not estimable:** execution was attempted but could not estimate the requested quantity.
- **Not requested:** an optional output was deliberately not calculated.

Do not conflate these states with a generic disabled button or blank cell. Provide a reason near unavailable controls and a corrective action where possible. Show common unavailable options when the explanation helps discovery; omit irrelevant low-level parameters rather than exposing every possible method knob.

The current Reitsma implementation requires complete TP/FN/FP/TN data, positive diseased and nondiseased denominators, and at least five eligible studies. Report this as an **RCMS implementation requirement**, not a universal methodological law.[^reitsma]

### 4.3 State machine

```text
Draft → Validating → Ready → Running
                       ↑       ├─ Completed
                       │       ├─ Completed with warnings
                       │       ├─ Partial result
                       │       ├─ Failed, draft retained
                       └───────└─ Stopped, draft retained
```

Display progress stages only when observed: **Preparing study data**, **Fitting model**, **Calculating diagnostic summaries**, **Creating figures**. An indeterminate indicator is better than an invented percentage. Show a numerical counter only when the backend reports meaningful work units.

A completed statistical fit with a failed plot is not a wholly failed analysis. A failed primary fit must not be presented as successful simply because an image or ancillary table exists. Result completeness belongs in the result contract.

### 4.4 Execution isolation

Use one worker process with its own initialized R runtime, managed from Qt through a narrow process boundary. A bounded, serialized queue is sufficient initially. Do not run parallel R calls against the existing process-global session or assume that adding `QThread` solves cancellation and global-state concerns.[^bridge][^adapter][^qt-process]

The boundary receives a validated input snapshot and effective specification, and returns structured progress, results, warnings, and errors tagged with a run ID. A worker process is a containment and responsiveness design choice; it does not imply an immediate need for distributed jobs, a task broker, or an agent framework.

Cancel must mean something precise. Prefer cooperative cancellation between safe stages. If a running native call cannot be interrupted safely, a documented force-stop terminates the isolated worker, keeps committed project data intact, and rebuilds the worker before subsequent tasks. Ignore late messages from a stopped or superseded run. Protect per-run output locations from collision.

Bring expensive plot regeneration and study calculation requests into this ownership model too. Do not move only the final fit while leaving expensive preparation calls on the UI thread. Initialize method metadata asynchronously or cache a verified capability catalogue so stored data and results remain readable when R cannot start.

## 5. Results workspace: shared structure, specialized content

### 5.1 Common frame

Every saved result should answer: **What was analyzed? Which data? With what method? What was estimated? What could not be calculated? What can I do next?**

```text
Project name                                   Data | Results
──────────────────────────────────────────────────────────────
Saved analyses      Mortality · 12 months · Treatment vs Control
                    Random-effects meta-analysis · Risk ratio
Primary analysis    [Edit a copy] [Copy summary] [Export…] [Detach]
Cumulative
Leave-one-out       Overview | Tables | Plots | Methods & data
By setting          ──────────────────────────────────────────
                    Estimate with labeled interval
                    Study count and important warnings
                    Main analysis-specific table or figure
```

This is an information-architecture schematic, not a screenshot or measured layout. Do not display mock numbers as actual RCMS results.

Use a small number of shallow sections. Do not combine a deep project tree, a deep section tree, tabs inside tabs, and a permanently open settings inspector. On narrower windows, the history list can collapse and figure controls can become a secondary panel without hiding the result title or primary actions.

Overview is a curated reading order, not a wall of every backend field. Tables contains native numerical tables; Plots provides publication figures and their tools; Methods & data preserves provenance, selected/excluded studies, model settings, warnings, references, and optional raw output. Family-specific headings and default selections make these sections meaningful.

### 5.2 Every result header

Include the analysis name, workflow, outcome/time point, selected arm(s) or diagnostic context, effect measure and units/scale, model and estimator, confidence level, analyzed-study count, and execution status. Put less frequently needed backend versions, seed, creation time, and exact input identity in Methods & data.

Show **Data changed since this analysis** when the relevant working data differ. The old result remains valid as a record of its original input; it is not retroactively changed. **Edit a copy** creates a new draft. Rerunning creates a new execution record or an explicit new version, never silently overwrites an existing result.

Study and participant counts must be authoritative. Do not sum sample sizes across overlapping outcomes, arms, or repeated time points to invent a unique participant total. Where a meaningful total is unavailable, report study count and explain the missing total.

### 5.3 Structured tables and figures

Use native table models with stable row IDs, typed numerical cells, human-readable column headings, selectable cells, and visible **Copy table** / **Export table** actions. Numeric sorting must use numbers, not formatted strings. Export a machine-readable CSV with full-precision values and explicit missing/status fields, and provide a formatted table copy suitable for manuscripts.

Keep display formatting separate from calculation. Store analysis scale and display scale explicitly. Label CI and prediction intervals differently. Show `Not estimable` or a concise reason instead of an unexplained dash. Never render a missing estimate as zero. Choose p-value precision centrally and avoid showing a rounded value as an exact zero.

Plots remain generated scientific artifacts. Do not rewrite the R plot algorithms merely to draw everything with Qt. Use a dedicated figure viewer with **Fit width**, **Actual size**, **Zoom**, **Edit appearance**, **Copy image**, and **Export**. Keep image export/edit controls visible and capability-aware; the context menu remains a shortcut.

A missing or unreadable plot keeps its slot: **Forest plot could not be displayed. The numerical results are still available.** Offer regeneration only when supported. A non-regenerable raster should not offer imaginary vector export. Preserve the existing white figure background in dark mode.[^viewer]

### 5.4 Current support matrix

This matrix describes the inspected dispatch and setup routes, not every individual metric/method combination. Availability is still conditional on metric, data completeness, and the backend's feasibility checks.[^core][^setup]

| Family/model | Standard | Cumulative | Leave-one-out | Subgroup | Meta-regression |
|---|---|---|---|---|---|
| Binary, one/two arms where the metric permits | Supported route | Supported route | Supported route | Supported route | Generic meta-regression route |
| Continuous means/differences and supported entered effects | Supported route | Supported route | Supported route | Supported route | Generic meta-regression route |
| Diagnostic univariate sensitivity, specificity, or ratios | Supported route | Supported route | Supported route | Supported route | Do not imply an independent univariate diagnostic-regression route |
| Joint diagnostic Reitsma | Supported | Not advertised | Not advertised | Not advertised | Supported joint model |

**Do not silently substitute independent univariate analyses when the user requested a joint model.** A request for joint cumulative, joint leave-one-out, or joint subgroup analysis is a statistical feature proposal, not a styling change. Existing bootstrap/permutation or other nonprimary APIs also require an explicit inventory before any UI removal; the five requested workflows are not a license to delete other supported functionality.[^core]

## 6. Detailed result layouts

### 6.1 Standard two-arm binary meta-analysis

Lead with the pooled effect and its labeled confidence interval, then study count, a compact model summary, and the forest plot. Provide a study table with study ID/name, arm data where available, estimate, interval, and method-appropriate weight.

For ratio measures, preserve the logarithmic plotting/calculation convention while displaying the ratio and correct null value. For difference measures, use the appropriate zero reference and explicit unit. These display rules are owned by metric metadata, not guessed from plot titles. Do not describe odds ratios as risk ratios or label raw probabilities as treatment effects.

Treatment/control direction is part of the specification. Show **Treatment versus Control**, not an unlabeled sign. Only display “Favours …” labels when the outcome's beneficial/harmful direction is explicitly known. Keep detailed heterogeneity and model diagnostics in an adjacent structured section, without converting I² into a red/amber/green quality verdict.

### 6.2 Standard single-arm binary pooling

Lead with **Pooled proportion**, the actual arm/population, and its interval. Use percentage formatting consistently across the summary, forest plot, table, and copied result. Denominators and event counts should be visible when present.

Do not show treatment/control columns, a treatment-effect null line, or “Favours intervention/control.” The selected transformation and back-transformation belong in Methods & data and in the effective specification. Preserve existing numerical behavior, including transformations requiring additional information; do not approximate the displayed value from a rounded printed estimate.[^results-r]

### 6.3 Continuous outcomes and entered effects

For a mean difference, report the outcome unit. For a standardized mean difference, identify the actual standardized-effect convention supplied by the backend rather than presenting it as an ordinary measurement unit. For a single-arm mean, identify the population and unit and omit comparison-language artifacts.

For supplied coefficients or generic effects, show the source scale and supplied uncertainty clearly. Do not force these inputs into a misleading raw-data form or invent a clinical comparator. Keep effect provenance visible: **Entered estimate** versus **Calculated from study data**. A user must be able to tell which source controlled the analysis.

### 6.4 Cumulative meta-analysis

The first line should identify analytical ordering: **Cumulative analysis · current study order**, or the explicitly chosen field and direction. Preserve the existing input order for migrated specifications unless the user deliberately changes it; the current R loop uses dataset order.[^sequential-r]

Present a table with step, study added, ordering value, studies included, cumulative estimate, interval, and relevant heterogeneity. The primary figure is a cumulative forest plot using the same row identities and order. A separate label identifies the final all-included-studies estimate.

Require stable tie-breaking and a visible missing-order-value policy for newly chosen ordering. Sorting a displayed results table must not change the underlying cumulative sequence. Do not suggest that successive estimates are independent trials or that the first crossing of a significance threshold establishes a stopping rule.

Retain early non-estimable steps with their reasons rather than making them disappear. Changing the existing all-or-nothing execution to collect step-level failures is an explicit backend contract change that must be tested; it must not introduce fallback estimators.

### 6.5 Leave-one-out analysis

Start with the **All included studies** estimate as a clearly labeled baseline. The main table contains omitted study, remaining study count, pooled estimate, interval, change from the baseline on a named scale, and available heterogeneity.

The forest plot should include a visually distinct full-sample reference. Use **Omitting [study]**, not a bare study name that could be mistaken for that study's own effect. An omitted-study run that fails remains a visible row with a status and reason.

A secondary summary may report the range of recalculated estimates. Do not automatically call a study an outlier or the finding “robust” based only on crossing p = .05. Do not offer one-click permanent exclusion without making clear that it changes the analysis dataset and creates a new result.

### 6.6 Subgroup analysis

Lead with **Subgroup analysis by [variable]**. Show the variable's levels, included/missing counts, each subgroup estimate and interval, and the subgroup forest plot. Place the test for subgroup differences beside the subgroup summaries when the backend actually computes an appropriate test.

Do not infer a subgroup difference from significance in one subgroup and nonsignificance in another. If no between-subgroup test is returned, show **Between-subgroup comparison not calculated** rather than an invented p-value or empty cell.

Preserve meaningful level labels and explicit reference/coding information. Missing subgroup values need an explicit policy: correct them, exclude the affected studies for this run with approval, or use a supported missing category if scientifically intended. Do not silently mix these policies. Keep collapsed/expanded subgroup rows synchronized between tables and figures only as presentation, not as analysis inclusion.

### 6.7 Generic meta-regression

Show the model formula, included studies, moderators and units, categorical reference levels, estimation/inference settings, and missing-data exclusions before the coefficient table. Distinguish intercept and moderator effects. The table should contain term, coefficient, interval, SE, test statistic and degrees of freedom where relevant, and p-value.

Provide the appropriate omnibus moderator test and factor/block tests when returned, plus residual heterogeneity. Preserve whether inference uses z or t and the corresponding degrees of freedom; the R display code already distinguishes these cases.[^results-r]

A bubble plot is appropriate only for a supported presentation of the fitted model. For multiple moderators, do not draw an apparently adjusted curve without explicitly specifying what is held fixed. Show conditional predictions only when the backend exposes the required prediction data and semantics. Otherwise, use the coefficient table and supported figures and explain why a single curve is not shown.

Use neutral association language. The interface must not turn study-level associations into patient-level causal conclusions.

### 6.8 Joint diagnostic Reitsma analysis

Treat this as a first-class report, not a binary-analysis template with different labels.

The reading order is **paired summary operating point → SROC figure → prediction information → sampling-based summary ratios → model/heterogeneity details**. Sensitivity and specificity should remain together in the summary, each with its interval and study context. Do not collapse them into one “accuracy” score.

Show the SROC axis as sensitivity against false-positive rate with the relationship to specificity stated clearly. Confidence and prediction regions need distinct line styles and a legend, not color alone. A joint prediction region describes the underlying paired accuracy of a new study, not its observed binomial counts. Preserve the R implementation's conversion of FPR intervals to specificity, including reversed endpoints and covariance signs.[^reitsma]

Keep three distinct concepts distinct: the summary operating point; sampling-based summary ratios; and independently pooled univariate ratios. In the current implementation, sampling-based ratios include mean, median, and equal-tail interval information. Do not label every interval a confidence interval or compute these quantities by taking ratios of the summary operating point.[^context][^reitsma][^reitsma-test]

If presenting SROC AUC, name its actual FPR range. The current terminology specifies 0.01–0.99; normalized partial SROC AUC has its own observed-range/fixed-grid interpretation. Do not invent an AUC confidence interval. Use the named diagnostic heterogeneity measures rather than a generic univariate I² badge.[^context][^reitsma-test]

Do not promise Reitsma-derived forest plots, new marginal predictions, or new statistics merely because a common view has space for them. Render the artifacts and numerical quantities the supported backend actually returns; new calculations require independent scope and numerical tests.

### 6.9 Diagnostic meta-regression

Use a joint-model heading and keep the sensitivity and specificity coefficient tables/plots explicitly labeled. Include moderator coding, reference levels, model estimator, joint/block tests, and model limitations.

The underlying model uses sensitivity/FPR representations, while clinical display may use specificity. Preserve the exact implemented sign and scale transformations; do not simply rename an FPR coefficient column. The current capability route deliberately uses separate coefficient forests rather than the generic bubble plot.[^core][^reitsma]

Do not show a universal “adjusted SROC,” overall adjusted AUC, or pooled operating point without a defined moderator profile and a supported prediction implementation. Such outputs are not required to make this interface feel consistent with other result families.

### 6.10 Small-study effects

Preserve the dedicated scientific boundary. Use **Small-study effects** as the explanatory heading, retaining a discoverable Publication bias synonym where navigation familiarity matters. Show eligible/ineligible methods with reasons, and distinguish primary from exploratory analyses.

The result order should be data/method eligibility, primary test result, supported funnel plot(s), and clearly labeled sensitivity/exploratory analyses. A significance contour is not evidence that publication bias has been identified. Trim-and-fill is a sensitivity analysis, not a corrected truth. Infinite-precision extrapolation is exploratory, not an unbiased effect.[^context][^bias]

Deeks plots need their own axes and semantics. Do not reuse ordinary funnel pseudo-confidence triangles. The model used for the pooled overlay and the asymmetry test are separate decisions and should be disclosed separately. Never silently change the eligible study set to make an otherwise unavailable procedure run.[^context]

## 7. Visual system

### 7.1 Direction

Use a quiet, content-first scientific desktop interface: restrained neutral surfaces, one accent, strong text hierarchy, and consistent alignment. Avoid a web-dashboard aesthetic with giant cards, decorative metrics, gradients, fake terminals, or celebratory scientific-result states. Polish should make the work easier to read, not compete with it.

Keep native Qt interaction and platform conventions. Extend a small semantic token layer around the existing layout policies; do not build an application-wide design-system framework before concrete controls require it.[^layout]

### 7.2 Proposed tokens

These are design proposals, not descriptions of the current application. Use the system palette/high-contrast mode when it takes precedence. Verify rendered combinations and interaction states rather than assuming a hex palette guarantees accessibility.

| Role | Light proposal | Dark proposal | Use |
|---|---|---|---|
| Application background | `#F6F7F9` | `#101828` | Quiet surrounding workspace |
| Content surface | `#FFFFFF` | `#1D2939` | Data/result panes |
| Primary text | `#182230` | `#F9FAFB` | Main reading content |
| Secondary text | `#475467` | `#D0D5DD` | Metadata, not deliberately faint body text |
| Accent/focus | `#175CD3` | `#84ADFF` | Selection, links, focus indications |
| Interactive boundary | `#667085` | `#98A2B3` | Controls requiring a visible boundary |
| Decorative separator | `#D0D5DD` | `#344054` | Nonessential dividers only |
| Warning foreground | `#B54708` | `#FEC84B` | Paired with warning text/icon |
| Error foreground | `#B42318` | `#FDA29B` | Paired with corrective explanation |

Do not use the light decorative separator as the sole visible boundary for an interactive control. Dark-mode accent text is not automatically a suitable filled-button background with white text. Treat foreground/background combinations as pairs.

Use the operating-system UI font for controls and reports. Body text starts from the native readable size; headings use a small number of relative steps. Use tabular numerals where available for statistics. Reserve monospace for raw output, code, and technical diagnostics—not the main report.

Adopt a small spacing scale, such as 4/8/12/16/24 logical pixels, adjusted where native metrics require it. Keep form labels aligned, controls content-sized, and related fields grouped. Numerical tables remain dense enough for research but not clipped. Do not make every field a card or every section title a colored badge.

### 7.3 Figure presentation and export

Figures have a white publication canvas regardless of application theme. Do not invert their data colors in dark mode. Fit the figure to available width initially but preserve an obvious actual-size/zoom control; repeatedly shrinking a 70-study forest plot until it is illegible is not responsive design.

Use common label/number formatting and arm direction across UI, plot, and export. Export choices should explain vector versus raster and, where supported, physical dimensions and resolution. Do not promise “journal-ready” merely because a file is saved at 600 dpi. Verify the actual written format, dimensions, legibility, clipping, and rendering fidelity. Preserve original artifacts when a new export fails.[^viewer]

## 8. Accessibility as release behavior

Use WCAG 2.2 A/AA criteria interpreted through WCAG2ICT as a design and evaluation reference for this desktop application. WCAG2ICT is informative guidance, not a standalone conformance certification.[^wcag2ict]

Prefer native Qt widgets and model/view tables for semantic structure. Accessible names on an enclosing graphics viewport do not, by themselves, provide meaningful table headers, row relationships, values, or per-figure equivalents. Qt provides accessibility facilities, but custom views still need explicit testing with platform assistive technology.[^qt-accessibility][^qt-modelview]

Release expectations:

1. A keyboard-only user can import, correct data, configure, run, navigate results, copy a table, edit a supported figure, export, and return to data.
2. Navigation selection updates content consistently; focus does not unexpectedly jump out of the navigator. Tab reaches the selected content and its actions.
3. Required labels, units, errors, selected values, row/column headers, and states are programmatically available. Essential help is not tooltip-only.
4. Focus is visible and unobscured. Enlarged text and high-DPI display do not clip controls or hide primary actions. Dialogs remain usable on small screens and across monitor changes.
5. Normal-text contrast targets at least 4.5:1; large text at least 3:1; necessary graphical/control boundaries at least 3:1. Status is never communicated by color alone.[^wcag22]
6. Test the actual supported packaged environments: keyboard and NVDA on Windows, VoiceOver on macOS, and an appropriate Linux screen reader on the qualified Ubuntu target. Do not equate an offscreen Qt test with a native assistive-technology pass.

Prefer comfortable click targets around 32–36 logical pixels for isolated desktop actions, consistent with the existing control policies, rather than blindly treating web CSS-pixel target guidance as a physical desktop measurement. Dense table cells need appropriate navigation and selection behavior, not forced oversized rows.[^layout]

## 9. Microcopy specification

### 9.1 Rules

Use sentence case and action-specific verbs. Buttons describe the action: **Run analysis**, **Save changes**, **Export plot**. Keep titles concise while retaining the context needed to avoid mistakes. Errors explain what happened, what remains safe, and the next useful action.

Use “project” for the saved research workspace and “dataset” for its data. Use “study arm” for treatment/control groups and “subgroup” for a moderator-defined collection of studies. Expand unfamiliar statistical abbreviations where introduced, but do not repeatedly explain familiar terms in every cell.

Separate researcher-facing summaries from technical diagnostics. A details disclosure may retain exact R messages and package versions. Do not put stack traces, internal variable names, or phrases such as “cannot build the Method & Parameters dialog” in the main recovery sentence.

Do not replace scientific precision with cheerful simplification. Successful execution is not proof that a result is valid, robust, unbiased, clinically important, or publishable.

### 9.2 Proposed catalogue

The following is a proposed cross-application copy catalogue. It is not a claim that every old string has been inventoried. Braced values are runtime substitutions and require appropriate singular/plural handling.

| Situation | Proposed visible copy | Action or supporting behavior |
|---|---|---|
| Empty project | No study data yet. Import a CSV or add your first study. | Import CSV / Add study |
| No prior analyses | Your analyses will appear here after you run them. | Set up analysis |
| Import mapping | Match your columns to the study fields. | Show example values beside each mapping |
| Unmapped requirement | Choose a column for {field}. | Focus the missing mapping |
| Missing optional year | Year is missing for {n} studies. You can still import them. | Explain the consequence only for year-based ordering |
| Numeric inference uncertainty | {column} contains numbers and missing values. | Numeric selected; editable type with preview |
| Invalid numeric data | {study}: {field} must be a finite number. | Go to cell |
| Binary count invalid | {study}: events cannot exceed the total. | Go to cell |
| Diagnostic denominator invalid | {study}: add participants with and without the target condition. | Open the affected count fields |
| Duplicate study name | This name is already used. Choose a different name or identify the existing study. | Preserve entered text |
| Derived preview | Calculated from study data | Details show formula/method and assumptions |
| Calculator commit | Apply calculated values | State which fields will change |
| Missing moderator | {n} studies have no value for {moderator}. | Review studies / Run without these studies |
| Categorical reference | Reference category | Select an explicit level |
| No moderator selected | Select at least one moderator to run meta-regression. | Focus moderator list |
| Cumulative order | Add studies in this order | Ordering field/direction; ties/missing policy |
| Missing order values | Choose how to handle studies with no {ordering field}. | Correct data / Use supported explicit policy |
| Unsupported joint workflow | Joint Reitsma {workflow} is not available in this version. | Offer a separately labeled supported analysis, never a silent substitution |
| Reitsma input requirement | The Reitsma model needs complete TP, FN, FP, and TN counts for every included study. | Review missing counts |
| Reitsma count threshold | This implementation needs at least 5 eligible studies; {n} are available. | Review studies |
| Ready state | Ready to analyze {n} studies | Run analysis |
| Running preparation | Preparing study data… | Stop when supported |
| Running fit | Fitting the selected model… | No invented progress percentage |
| Diagnostic summaries | Calculating sampling-based summary ratios… | Report observed stage, not an invented completion time |
| Generic run failure | The analysis could not be completed. Your settings are still here. | Edit settings / Retry / Technical details |
| Nonconvergence | The selected model did not converge. No alternative model was fitted. | Review settings / Technical details |
| Worker unavailable | The statistical engine could not start. Your project data are unchanged. | Retry engine / Technical details |
| Partial result | Some results could not be calculated. Available results are shown below. | Review affected sections |
| Figure failure | The forest plot could not be displayed. The numerical results are still available. | Regenerate when supported |
| Stop requested | Stopping analysis… | Keep accurate state until stop is acknowledged |
| Stopped | Analysis stopped. Your settings are unchanged. | Edit settings / Run again |
| Old input snapshot | Data changed since this analysis. | Review changes / Run an updated analysis |
| Result revision | Edit a copy | Original result remains unchanged |
| LOO baseline | All included studies | Distinct baseline row/reference |
| LOO row | Omitting {study} | Not a study-specific effect label |
| Missing subgroup test | Between-subgroup comparison not calculated | Explain method/output limitation |
| Joint diagnostic summary | Summary operating point | Paired sensitivity/specificity |
| Diagnostic ratio table | Sampling-based summary ratios | Mean, median, and correctly named interval |
| Diagnostic prediction | Prediction for a new study's underlying sensitivity and specificity | Distinguish from observed counts and confidence in the mean |
| Unavailable AUC interval | An AUC confidence interval is not provided by this method. | Never invent one |
| Small-study caveat | Asymmetry can have causes other than publication bias. | Adjacent to interpretation, not hidden in raw output |
| Trim-and-fill | Trim-and-fill sensitivity analysis | Not “bias-corrected effect” |
| Infinite-precision result | Exploratory infinite-precision estimate | State it is not a corrected effect |
| Plot auto range | Automatic | Do not expose the `[default]` sentinel |
| Plot action | Edit appearance | Does not imply statistical refitting |
| Table action | Copy table | Include headers and readable precision |
| Export action | Export plot | Choose only formats actually supported |
| Export completion | Plot exported to {filename}. | Open folder |
| Export failure | The plot could not be exported. The existing file was not changed. | Use only when atomic-write behavior guarantees that claim |
| Unsaved project | Save changes to {project}? | Save changes / Discard changes / Keep editing |
| Save failure | The project could not be saved to this location. Your changes are still open. | Choose another location / Technical details |
| Delete study | Delete {study} from this dataset? | Delete study / Keep study; undo available |
| Close result viewer | Close view | Does not delete the analysis |

### 9.3 Implementation

Inventory strings from canonical `.ui` forms, Python-created controls/dialogs, backend descriptions and human-facing messages, plot labels, tooltips, status text, export dialogs, and empty/error states. Identify shared concepts and replace duplicates with a small shared label/message module where it removes real duplication. Do not create a runtime copy-management system.

Every error message must be tested with its actual state transition. For example, “Your settings are still here” is only acceptable after failure preserves the draft. “The existing file was not changed” requires a real atomic export path. Copy is a behavioral contract, not a decorative layer.

## 10. Implementation architecture

### 10.1 Preserve boundaries that already work

Keep project schema validation and atomic storage, the existing domain representation and stable identities, the RCMetaR statistical facade, capability-based plotting, and well-tested native layout/resource generation. Edit canonical `.ui` sources rather than committed generated UI modules.[^project][^core][^layout][^maintenance]

A practical target dependency direction is:

```text
Qt project workspace / data editor / result views
                  ↓
Draft validation, project session, run ownership, export commands
                  ↓
Existing domain data + typed analysis/result values
                  ↓
R worker boundary → existing RCMetaR facade and estimators
```

No second analysis engine, generic event bus, plugin registry, or service layer per screen is required. Introduce a module or class only when it takes concrete responsibility away from an oversized controller.

### 10.2 Minimal new or evolved values

**Analysis specification:** family, workflow, measure, effective estimator/inference/correction settings, moderators and reference coding, ordering, and input selection. Normalize defaults before hashing or recording. The final effective specification—not merely the pre-execution form values—is the reproducibility record.

**Analysis run:** unique execution ID, specification, immutable relevant input snapshot/digest, backend versions and seed where used, status, structured result, warnings/errors, and artifact references. A deterministic analytical fingerprint and a unique execution ID serve different purposes. Do not build a cache until there is a demonstrated requirement.

**Result blocks:** a small closed set such as estimate, table, plot, notice, and methods/reference information, with semantic IDs and typed fields. Extend `AnalysisResult`/`ResultSection`; do not keep two permanent result systems. Missing values carry a status/reason distinct from numeric values. Bound geometry and other potentially large arrays.

**Presentation settings:** figure style, labels, visible columns, zoom, formatting, export dimensions, and appearance. These must not change analytical identity. A styling operation may regenerate an artifact but must not silently change the model or data.

### 10.3 Result producer migration

Use R's raw model objects and existing structured numerical result fields as the source. Return explicit values and metadata across the bridge. Never extract numbers with regular expressions from printed R summaries to populate primary tables.[^sequential-r][^results-r]

Migrate one family/workflow at a time while temporarily supporting the old read path only where needed to complete the transition. Keep “Raw output” available for expert review. Remove the obsolete presentation path after all supported cases have parity. Do not preserve old string-parsing machinery indefinitely “just in case.”

### 10.4 Saved analyses and project versioning

Current v1 is deliberately constrained and validates exact members and schemas. Persistent analyses therefore require a deliberate format/schema change, not extra files or fields smuggled into v1.[^project][^schema-project][^schema-state]

Define a reviewed v2 with explicit portable analysis records and bounded assets or regeneration specifications. Preserve atomic writes, deterministic metadata where appropriate, hashes, size limits, unknown-version rejection, and released-version migration tests. Historical pickle support remains out of scope.

A project should reopen saved numerical results without requiring live R. Do not serialize arbitrary Python objects or unvalidated executable R state into a project. Store data-only, validated specifications and outputs. Treat vector assets, external references, file paths, and archive members as untrusted input; retain traversal and resource limits. Temporary caches and machine-specific placement remain outside the archive.

Define a concrete storage policy for large histories: saved analyses versus disposable cache, bounded embedded assets, and explicit user deletion of saved runs. Do not introduce invisible retention deletion. Opening old projects must not alter entered effects, arm selection, or a saved analysis merely because the UI rebuilds controls.

### 10.5 File-level disposition

| Existing area | Disposition |
|---|---|
| `main_window.py` and `forms/main_window.ui` | Rewrite workspace composition and navigation; move analysis ownership and import orchestration out of the window; retain reliable project-open/restore behavior. |
| `main_wizard.py` and startup/import pages | Simplify entry paths; replace exact-header workflow with mapping/preview; retain native startup and focus safeguards. |
| `dataset_table_model.py` / `dataset_table_view.py` | Refactor incrementally around existing domain/edit transactions; preserve selection, undo, column ownership; avoid wholesale dataset replacement. |
| Study-data and back-calculation dialogs | Standardize entered/derived/apply hierarchy, inline errors, button semantics, and accessibility; retain domain calculations and validation. |
| `analysis_setup_dialog.py` | Replace the large dialog's orchestration with a retained draft and explicit workflow sections; separate scientific settings from figure settings. |
| `diagnostic_metrics_dialog.py` / `subgroup_analysis_dialog.py` | Fold routine selection into the common draft editor; preserve the distinct model semantics. |
| `publication_bias_dialog.py` / `publication_bias.py` | Keep dedicated scientific request/eligibility logic; align its interaction and report frame. |
| `analysis_adapter.py` / `r_bridge.py` | Preserve typed boundary; separate effective analytical identity from appearance; move R ownership into worker process; transmit structured results. |
| `analysis_results.py` / `result_sections.py` | Evolve the validated contract with typed numerical/status/provenance blocks; retire display-string normalization as primary data transport. |
| `results_window.py` and its form | Replace the all-content graphics canvas with native results pages; reuse dedicated vector/raster figure viewer and export/edit services. |
| Plot services, capabilities, editors, R renderers | Retain valid regeneration semantics; unify visible commands, failure handling, formatting, and export contracts. |
| `qt_layout.py`, adaptive helpers, canonical forms | Consolidate tokens and natural layout ownership; delete obsolete canvas/refit work only after behavior replacement is verified. |
| Project schemas/session/storage | Extend deliberately for saved analyses; preserve validation, atomicity, stable identities, and undo boundaries. |
| R result producers | Add typed result adapters; preserve estimates, scales, correction policies, inference, seeds, and supported/unsupported methods. |
| Tests, scripts, packaging | Extend existing lanes with journey/accessibility/structured-result parity; retain native Windows/macOS/qualified-Ubuntu verification. |

These are disposition recommendations, not claims that every named file was inspected completely.

## 11. Delivery sequence and acceptance gates

### M0 — Freeze scientific and workflow invariants

Create the authoritative family × input representation × metric × workflow × method capability inventory from the R facade and existing fixtures. Document user-visible legacy behavior that must remain, and explicitly identify unsupported combinations. Inventory all reachable UI surfaces and strings, including programmatic dialogs and any less-prominent APIs.

Capture baseline native journeys and representative current screenshots with pinned data and settings. Re-run the existing golden, GUI, R-stack, and packaging lanes in an equipped environment. Record actual timings and failures rather than inventing targets from source size.

**Gate:** Every supported combination targeted for migration has a numerical/semantic fixture or a clearly documented validation gap. No statistical default changes are hidden in UX work.

### M1 — Repair recovery and discoverability in the current UI

Fix failed-analysis draft disposal; show missing-artifact states; expose plot edit/export actions; make results navigation keyboard-consistent; replace generic destructive Yes/No prompts; correct blank-year and missing-value type-inference behavior through the import contract.

**Gate:** Simulated fit/display/export failures preserve user work; every advertised action has a reachable keyboard route; new import behavior has focused tests. Do not claim full responsiveness before the process boundary exists.

### M2 — Build one complete vertical slice

Implement the smallest structured-result contract and native result view for a two-arm binary standard analysis. Include immutable effective specification/input identity, readable estimate, native study table, figure toolbar, warning states, copy/export, and an edit-a-copy path.

**Gate:** The selected result matches existing statistical output and exported artifact behavior; changing figure appearance does not change analytical identity; table sorting and formatting do not change values.

### M3 — Establish durable result ownership and asynchronous execution

Integrate the R worker process, run-ID message ownership, truthful progress, safe stop/failure recovery, and the reviewed project-format migration for saved analyses. Keep the worker serialized initially. Bring preparation and regeneration under the same ownership rules.

**Gate:** UI interaction remains available during fitting; stopping cannot corrupt a saved project; stale worker responses cannot replace a newer run; saved numerical results reopen without R; old structured projects migrate safely.

### M4 — Migrate result families and workflow variants

Add continuous and single-arm variants; cumulative; leave-one-out; subgroup; generic meta-regression; diagnostic univariate; Reitsma; diagnostic meta-regression; small-study effects. Use specialized presenters and shared components only where meaning truly matches.

**Gate:** Each required table, plot, interval, unavailable state, and export is checked against its supported backend contract. Joint diagnostic analyses are never silently converted to univariate analyses. Remove the obsolete full-report graphics canvas only after parity.

### M5 — Replace fragmented data/configuration workflows

Install explicit context selectors, retained analysis drafts, import mapping/preview, consolidated data issues, and consistent study/calculator editing. Retire redundant chooser dialogs and mode-dependent arrows where replaced.

**Gate:** New and experienced users can complete the representative journeys without instructions about hidden modes or right-click-only actions. Preserve undo, data authority, selection, and project boundaries.

### M6 — Accessibility, visual, copy, and packaging qualification

Apply the token/copy inventory across every reachable surface. Run native screen-reader and keyboard journeys, high-DPI/small-screen cases, figure/export QA, and packaged worker-startup tests. Delete redundant compatibility/layout code and tests that only preserve intentionally removed implementation details.

**Gate:** Acceptance evidence is recorded per supported platform and workflow. Unverified cases remain explicitly listed; they do not become “passed” because another platform passed.

## 12. Test plan

Extend the existing verification system rather than building an independent test bureaucracy. The maintained suites already separate fast Python, GUI, statistical golden, R-stack, and packaging contracts.[^maintenance]

### Numerical and semantic parity

Check effect values, CI endpoints, scales and transforms, effective model settings, study inclusion/order, moderator coding, correction policies, standard errors and weights where meaningful, degrees of freedom, warning propagation, and unsupported requests. Test diagnostic interval endpoint reversal, ratio-table meanings, AUC limitations, and the absence of invented joint outputs. Existing Reitsma formatting tests provide useful fixture material but do not certify the new native tables.[^reitsma-test]

Compare structured numeric values with appropriate tolerances. Do not make exact screenshot text or whitespace the sole statistical test. Seed stochastic summaries and record the seed/backend versions; do not replace stochastic outputs with deterministic-looking approximations.

### User journeys

| Journey | Evidence required |
|---|---|
| Import a CSV with renamed/reordered columns and missing numeric moderator values | Mapping correct, missing values retained, type inference reviewable, no unintended mutations |
| Run a two-arm binary analysis and export its forest plot | Correct comparator/measure, visible export, identical underlying result |
| Switch to a single-arm proportion or mean | Irrelevant comparison controls disappear without losing other data |
| Configure cumulative analysis with tied/missing years | Explicit analytical order and policy; stable record after display sorting |
| Inspect a problematic leave-one-out run | Baseline visible, omitted study unambiguous, failed step retained |
| Compare subgroups | Correct level counts and test-for-differences availability; no inference from within-group significance |
| Run categorical/multivariable meta-regression | References, units, missing-data exclusions, formula, and valid figure semantics visible |
| Run Reitsma and diagnostic meta-regression | Joint semantics, correct specificity transformation, paired/separate outputs as intended |
| Recover from a model error | Draft retained and editable; previous results untouched |
| Stop a running analysis | Accurate stopping state, clean worker recovery, no late overwrite |
| Save, close, and reopen a project | Data, saved analyses, provenance, and presentation state intact; numeric results readable without R |
| Keyboard/screen-reader review and export | Names, roles, headers, values, focus order, and all essential actions usable |

### Stress and failure cases

Test one-study/too-few-study behavior where supported, many-study forest plots, no eligible studies, all-missing moderators, large categorical sets, Unicode and long study labels, locale-sensitive numeric entry, extreme values, missing/corrupt artifacts, read-only export destinations, failed model convergence, partial diagnostic outputs, failed project migration, and monitor/DPI changes.

Test UI changes while a run is active. The worker must use its input snapshot; results must not accidentally read the newly selected outcome or renamed arm. Test close-window/project actions during a run with a defined ownership and cancellation policy.

### Usability evaluation

Measure task completion, wrong-context analyses, recoverability after errors, time/interaction count to first valid result, and time to locate model/inclusion information. Establish a baseline before claiming improvement. Use medical researchers new to RCMS and experienced meta-analysts; include assistive-technology users where possible.

A useful design review asks a participant to identify the analyzed outcome, comparator, number of included studies, model, interval type, and any incomplete output from a result screen. If the participant has to reconstruct those details from raw output or a remembered dialog, the result frame has failed its purpose.

### Existing commands to retain

Run in an environment with the repository's locked dependencies and required native R/Qt stack:

```powershell
uv run python scripts/verify.py smoke
uv run python scripts/verify.py fast
uv run python scripts/verify.py r-stack
uv run pytest --strict-markers tests --collect-only -q
.\scripts\verify-qt6.ps1
```

Use the relevant native/platform packaging commands and code-health gates documented by the repository. These commands are recommendations drawn from its maintenance guide; they were **not executed as successful verification in this audit**.[^maintenance]

## 13. Definition of done

The rewrite is complete when all existing supported analytical workflows have a clear end-to-end route; completed analyses are inspectable and reproducible objects; errors preserve user work; results are structured and scientifically labeled; critical actions are visible and keyboard-accessible; project storage remains safe; and native evidence supports the visual/accessibility claims on the qualified platforms.

The goal is not fewer features or fewer statistical details. It is fewer hidden states, fewer repeated decisions, fewer ambiguous labels, and less effort spent determining what the software actually did.

## Source references

All repository references below are pinned to the audited commit. A source link does not mean that every line in the linked file was inspected. Key reviewed ranges are identified where applicable.

[^manifest]: [Canonical form manifest](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/ui_form_manifest.py). Full file reviewed.

[^contract]: [Analysis result contract](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/analysis_results.py). Lines 1–320 reviewed.

[^adapter]: [Analysis requests and service](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/analysis_adapter.py). Lines 1–250 and 280–530 reviewed.

[^execute]: [Execution dispatch and diagnostic failure isolation](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/analysis_adapter.py). Lines 280–530 reviewed.

[^setup]: [Analysis setup, request construction, execution and recovery](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/analysis_setup_dialog.py). Lines 1–300, 520–1030, and 1160–1500 reviewed.

[^viewer]: [Results canvas, text handling, plot actions and export](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/results_window.py). Lines 1–1110 reviewed.

[^main]: [Main application workflow and project operations](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/main_window.py). Lines 1–300, 560–1190, and 1490–1820 reviewed.

[^layout]: [Shared native layout/control policy](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/qt_layout.py). Full returned file reviewed.

[^project]: [Project-format contract and durability](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/docs/project-format.md). Full document reviewed.

[^schema-project]: [Version 1 project schema](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/project_schemas/v1/project.schema.json). Full schema reviewed.

[^schema-state]: [Version 1 portable-state schema](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/project_schemas/v1/state.schema.json). Full schema reviewed.

[^progress]: [Progress-dialog implementation](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/progress_dialog.py). Full file reviewed.

[^bridge]: [In-process rpy2 bridge](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/r_bridge.py). Lines 1–250 reviewed; relevant result-parser search excerpts also inspected.

[^csv]: [CSV import validation and type inference](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/csv_import.py). Full file reviewed.

[^table]: [Data table view and editing integration](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/dataset_table_view.py). Lines 1–270 reviewed.

[^wizard]: [Startup and data-type wizard](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/main_wizard.py). Lines 1–285 reviewed.

[^core]: [RCMetaR facade and supported methods/capabilities](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/r/RCMetaR/R/rcmetar-core.R). Lines 1–290 reviewed.

[^sequential-r]: [Cumulative result producer and numerical result structure](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/r/RCMetaR/R/meta_methods.R). Lines 1–300 reviewed.

[^results-r]: [Summary and regression result producers](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/r/RCMetaR/R/results_display.R). Lines 1–250 reviewed.

[^reitsma]: [Reitsma validation and clinical-scale transformations](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/r/RCMetaR/R/reitsma_methods.R). Lines 1–270 reviewed.

[^reitsma-test]: [Reitsma R/Python result-formatting tests](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/tests/r_stack/test_reitsma_result_formatting.py). Full returned file reviewed; tests not executed.

[^bias]: [Small-study-effects configuration and accessible help](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/src/rc_metastudio/publication_bias_dialog.py). Lines 1–265 reviewed.

[^context]: [Authoritative project terminology and scientific distinctions](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/CONTEXT.md). Full document reviewed.

[^maintenance]: [Verification, generated-form and packaging guidance](https://github.com/AliSalman-et-al/rc-metastudio/blob/68c7a41ee94effcd934a49db9557802d0b32e977/docs/maintaining.md). Full document reviewed.

[^wcag2ict]: [W3C, Guidance on Applying WCAG 2 to Non-Web Information and Communications Technologies](https://www.w3.org/TR/wcag2ict/). Published December 11, 2025; informative desktop/non-web interpretation.

[^wcag22]: [W3C, Web Content Accessibility Guidelines 2.2](https://www.w3.org/TR/WCAG22/). Contrast, keyboard, focus, and other accessibility criteria; applicability to desktop requires interpretation.

[^qt-accessibility]: [Qt, Accessibility](https://doc.qt.io/qt-6/accessible.html). Primary documentation for Qt accessibility support.

[^qt-modelview]: [Qt, Model/View Programming](https://doc.qt.io/qt-6/model-view-programming.html). Primary documentation for native data presentation and model/view separation.

[^qt-process]: [Qt, QProcess](https://doc.qt.io/qt-6/qprocess.html). Primary documentation for process management; worker architecture and cancellation policy above are design recommendations.
