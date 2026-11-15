# Results presentation design — 15 November 2026

Status: reconciled batches A–D implemented; qualification is tracked in
[the implementation report](results-implementation-2026-11-15.md).
This extends the desktop polish work on `ui/desktop-polish-and-icons`.

## Reconciled decisions after Opus review

The [independent Opus 5.5 High research](results-opus-design-2026-11-15.md)
identified stronger reasons to address numerical consistency before rearranging
navigation. This section supersedes the initial implementation ordering below.

1. **First remove misleading transformations and generated verdicts.** Preserve
   producer display precision until numeric metadata exists; do not pad an
   already-rounded string or reinterpret rounded CI bounds. Delete the automatic
   CI-null classification sentence and categorical I² adjectives. Report
   small-study method statistics and fixed caveats without a yes/no verdict.
   Keep all actual estimates, tests, limitations and complete output.
2. **Keep three-decimal app P formatting for the first batch.** Unify its
   notation across views, then consider any digit-policy change separately.
   JAMA's adaptive rule is defensible as a style choice; three decimal places
   on .267 is not intrinsically a scientific error. Sampling variability alone
   does not determine the required reporting precision. Distinguish equivalent
   notation (.015 versus 0.015) from an actual numerical discrepancy.
3. **Keep PI in its own labeled block near heterogeneity for now.** Retain the
   accepted explanation immediately beside its value. A separate primary-table
   PI column is an alternative to evaluate, not an automatic addition. CI and PI
   may share a sentence if clearly distinguished; the requirement is semantic
   clarity, not a prohibition on sentence structure.
4. **Keep the existing forest landing view during the consistency work.**
   Improve the Report account and its discoverability. The design study's
   opening summary and interval diagram remain experiments, not replacements
   for the study-level forest plot.
5. **Subgroup prose should lead with estimates and the formal subgroup test.**
   Detailed within-subgroup P values remain available. Reporting them is not
   itself invalid; inferring between-subgroup differences from them is invalid.
6. **Use method-specific headings and explicit scale labels.** Reitsma needs
   summary operating-point language. SE for a log-transformed estimate must
   identify that scale. z is dimensionless; it is not itself a log-scale value.
   τ² is a variance, so its units are the square of the model's analysis scale.
7. **Then improve paper tables and rich copying; finally add numeric roles.**
   The existing v1 boundary gains optional per-cell quantities: raw values,
   roles, scales and interval levels. Missingness uses None; producer display
   text retains bounds and missing-value reasons. Results are not persisted and
   R/Python qualify together, so no version bump is needed. No second report engine,
   new web stack or journal-style selector is justified for this work.

The diagnostic partial-denominator concern is a source-level lead, not a proven
reachable defect: trace method eligibility and included studies before changing
it. Also allow legitimate tests or non-estimable results without manufacturing
an unavailable estimate or interval. Do not promise exact numeric export for
fields for which only formatted strings or bounds are held.

Proposed implementation batches are: (A) precision preservation and factual
wording; (B) subgroup/denominator/scale and diagnostic labels; (C) table geometry,
rich copying and paper pagination; (D) minimal numeric boundary and data export.
Write the failure obligations before each batch and exercise the actual R/Qt
workflows. This research does not authorize silently regenerating statistical
oracles or adopting every optional suggestion in the independent review.

## Product decision

Make the Results window a readable account of an executed analysis: what was
estimated, how uncertain it is, what contributed to it, and what the chosen
method assumes. Start with a small number of useful results, with all underlying
output still reachable. Numerical authority remains with the selected R package.
The opening experience should answer a scientific question rather than ask the
reader to choose between several representations of the same output.

The [interactive design study](design/results-proposal-2026-11-15.html) uses held
amino.rcms results. It demonstrates hierarchy, table typography, distinct CI/PI
representations, and a separate manuscript draft. It does not run an analysis,
implement exports, replace the full forest plot, or demonstrate every workflow.
Its log-axis interval diagram is a design experiment, not an agreed new default
figure. The first implementation should reuse the existing forest plot.

## What the requested sources contribute

| Source | Finding | RCMS design inference |
| --- | --- | --- |
| [easystats report](https://easystats.github.io/report/) | A report object supports narrative, tables and a shorter summary. Its example also attaches methods and inference details. | Generate a concise deterministic draft from the same facts as the tables. Borrow the reproducibility, but avoid automatic magnitude/significance adjectives. |
| [report tables](https://easystats.github.io/report/articles/report_table.html) | Printed tables can combine CI fields while the underlying data frame keeps separate numeric bounds and confidence level. | A reader may see “estimate (CI)” while CSV retains separate numeric fields. Display strings must not be the machine-readable result. |
| [broom](https://broom.tidymodels.org/) | `tidy()` describes model components; `glance()` describes a model; `augment()` attaches observation-level information. | Keep pooled/coefficient, model/heterogeneity, and study-level records distinct. broom supplies structure, not a manuscript rounding standard. |
| [Wickham, Tidy Data, JSS 59(10)](https://www.jstatsoft.org/article/view/v059i10), [author's full PDF](https://vita.had.co.nz/papers/tidy-data.pdf) | Variables, observations and observational units have distinct roles. The paper discusses messy presentation tables, reshaping, linked tables, and tidy tools; it also recognizes useful alternatives to tidy layouts. | Use tidy records for computation/export. A readable manuscript table may pivot those records or group interval bounds. Do not mistake a publication layout for the storage schema. |
| [JAMA author instructions](https://jamanetwork.com/journals/jama/pages/instructions-for-authors#SecStatisticalMethodsandDataPresentation) | Emphasize estimates and uncertainty; identify methods, transformations and software. Avoid causal wording for meta-analyses. Report exploratory analyses appropriately. P conventions: below .001 as a bound; .001–.01 to three decimals; .01–.99 to two; above .99 as a bound. | Keep uncertainty beside the estimate. Offer journal formatting at export only after numerical semantics are reliable; do not silently change all app precision to one journal's convention. |
| [JAMA table instructions](https://jamanetwork.com/DocumentLibrary/InstructionsForAuthors/InstructionsForTableCreation.pdf) | Use real editable table cells, rather than table images or spacing tricks; retain uncertainty and denominator context. | Rich table clipboard output should include editable HTML plus plain text. Word output must remain a table. |
| [JASP Getting Started](https://jasp-stats.org/getting-started/) and [hosted user guide, pp. 8–10](https://jasp-stats.org/wp-content/uploads/2024/08/MacDougall-Users-Guide-for-JASP-v-2.0.pdf) | JASP supports manuscript-ready tables, local output actions, copy/paste, annotations and export. The guide shows restrained statistical tables and figure-specific menus. | Use a coherent report surface with object-local actions. Borrow the hierarchy and transfer workflow without copying JASP's entire interface or treating APA and JAMA as identical. |

JAMA's current web instructions take precedence over its older table PDF where
they differ (for example, vertically merged cells). None of these sources
requires RCMS to install report, broom, tidyverse, or a browser renderer.

## Observed RCMS gaps

Inspected `analysis_results.py`, `manuscript_report.py`, `results_window.py` and
native evidence `20261115T105214Z-02d68633-ui-fine-tuning` (especially captures
26, 29, 30, 43, 61 and 70). This is a source/evidence audit, not a new GUI run.

- The navigation offers Manuscript, Text report, Tables, Settings and figures.
  Default selection favors the first plot; a user must discover where the
  statistical account and methods live. Some output also appears in several
  representations without an obvious difference in purpose.
- The primary pooled table includes SE, its scale, z/t and P beside the estimate
  and interval. These are useful audit details, but compete with the main result.
- “Model fit” combines sample counts, heterogeneity, inference tests and a
  prediction interval. Those answer different questions and deserve grouping.
- Manuscript HTML stretches tables to the full page width. Its compact table
  view has improved, but manuscript and report geometry still differ.
- `ResultTable.rows` contains strings. Numeric alignment is inferred from cell
  text. Narrative routing and rounding still depend on table/header titles and
  regular expressions. A renamed heading can affect behavior, contrary to the
  intent of ADR-0011.
- Table copy is TSV only. CSV currently serializes the formatted manuscript
  table, so it cannot promise original numerical precision.
- Current narrative classifies intervals relative to the null using supplied
  strings, and describes I² through overlapping categorical ranges. This can
  overstate what the available precision or a heterogeneity category establishes.
- Existing strengths are substantial: immutable structured results, explicit
  method metadata, editable plots, manuscript generation, PDF/DOCX export,
  supplementary retention, and package provenance. Extend these.

## Proposed reading experience

1. **Identity and method.** Outcome, comparison direction, metric, actual model,
   eligible study count and trustworthy denominator context. Expose exclusions
   and material warnings here. Do not invent participant totals for generic
   estimates, equate participants with person-time, or sum repeated people.
2. **Primary result.** A short, content-sized table with the estimate, labeled
   output CI and a subordinate P column when applicable. One careful sentence
   describes the interval's extent. No significance stars, traffic-light verdict,
   “effective” badge, or unconfigured primary-outcome claim.
3. **Figure.** Existing forest/SROC or method-appropriate plot, with a concise
   caption, explicit scales and local Edit/Copy/Export actions. Keep text legible;
   scroll rather than shrink long forests into a thumbnail.
4. **Variation and sensitivity.** Heterogeneity and prediction intervals belong
   here, with their model assumptions. Distinguish pooled-mean uncertainty from
   between-study variation. Show warnings close to the affected result.
5. **Supporting output.** Study results, model/test details, assumptions, complete
   supplementary tables and references remain reachable through clear sections.
6. **Write-up.** Deterministic Methods/Results drafts use those same facts. Copy
   a paragraph, table or figure independently, or export the complete account.
   Keep clinical interpretation and certainty assessments with the researcher.

Use one Results account with anchors and progressively disclosed detail. Keep
Tables for inspecting/copying data and Write-up for manuscript prose; do not
create three independently computed versions. The prototype's tabs test this
distinction, not a requirement to add another navigation layer.

## Numerical and typographic contract

These are proposed product decisions, rather than claims that all sources use
the same style.

- Keep upright, tabular numerals. Bold aligned column headings; text left,
  numeric fields right, with consistent precision within each statistical field.
  Sparse horizontal rules, short descriptive titles, clear notes, no vertical
  grid in publication tables. The data-entry spreadsheet is a different surface.
- Respect the selected display digits for estimates and intervals. Retain a small
  nonzero estimate or limit with additional significant digits or scientific
  notation; never display a positive ratio bound as zero through rounding.
  Counts are integers. Percent precision depends on whether it represents a
  sample proportion, model estimate, weight or I².
- Preserve numerical values, bounds, status, units, scale and output confidence
  level separately from display text. Missing, not estimable, not applicable,
  bounded and infinite values must remain distinguishable and explained.
- Keep the present app P convention during initial visual work. A later explicit
  manuscript style can apply the researched JAMA convention. Never show P = 0;
  never invent an exact value from a producer's bound. Precision changes must
  not produce or change a significance verdict.
- Do not classify an interval from rounded endpoints or reconstruct precision
  from the number of printed decimals. Where numerical bounds are unavailable,
  report the held output without a derived threshold interpretation.
- Human copy may combine estimate/CI; numeric export needs separate estimate,
  lower, upper, confidence-level and scale fields, including raw P or its bound.
  Label an export of already-rounded strings as a formatted table.
- App surfaces follow light/dark palettes. Paper output uses a deliberate white
  background and dark text. A screenshot of a dark UI is not the report export.
  Fit tables by wrapping, pagination or orientation before reducing readable type.

## Different analyses need different opening content

| Workflow | What should lead |
| --- | --- |
| Standard pooling | Estimate, CI, contributing studies; forest and variation follow. |
| Subgroup | Subgroup estimates plus the actual interaction/between-subgroup test; separate within-group significance is not evidence of a difference. |
| Cumulative | Ordering variable, accumulating estimates and study counts; distinguish sequential estimates from independent tests. |
| Leave one out | Full-data reference, omitted-study estimates and omitted identity. Do not call a result robust solely because P stays on one side of .05. |
| Meta-regression | Coefficients, moderator units/reference levels, model scale, intervals, eligible studies and residual heterogeneity. No automatic causal moderator explanation. |
| Reitsma | Paired summary sensitivity/specificity, uncertainty and SROC; distinguish summary operating-point ratios from sampling-based summary ratios. |
| Small-study effects | Eligibility/limitations and the designated primary asymmetry method. Keep exploratory methods and trim-and-fill sensitivity separate; avoid a publication-bias verdict. |
| Mean/proportion, HR, IRR | Preserve the actual estimand, output scale, time/person-time units and valid denominator context; do not force an intervention comparison onto a one-arm analysis. |

These distinctions follow the repository's domain contracts; none calls for a
new estimator or an undocumented change to package inference.

## Implementation order and proof before changes

1. **Unify presentation using existing facts, after batch A above.** Shared table geometry,
   clear grouping and method-aware entry points; object-local actions and rich
   clipboard tables. Keep estimator behavior and the boundary unchanged. Prove
   light/dark transitions, keyboard access, narrow layouts, long tables, real
   Word paste, and complete copied/exported content before accepting this batch.
2. **Then, make numerical semantics explicit.** Introduce the smallest versioned
   contract change needed for raw values and column roles, from the R producer
   through Python. Replace the affected title/regex decisions; do not bolt a
   second report engine around them. Before coding, enumerate tiny values,
   rounding at the null, bounded P, missing/infinite values, log transforms,
   non-95% output CIs and producer failures. Exercise real Qt/R workflows and
   compare held numerics with independent authorities; freeze the inputs during
   qualification. Existing oracle values and package authority remain intact.
3. **Finally, refine narrative and manuscript export.** Method-specific factual
   summaries, explicit journal styling, repeated table headers, sensible page
   breaks and captions. Compare actual displayed, copied, CSV, DOCX and PDF
   results. Render exported pages and inspect them, rather than relying only on
   text retention or a successful save operation.

Acceptance scenarios must include binary and continuous pooling, one-arm
outcomes, subgroup, regression, cumulative, omission, generic HR/IRR, diagnostic
Reitsma, and small-study methods. Cover zero cells, exclusions, few studies,
failed/not-estimable results, long labels and alternate confidence levels.
Clinical conclusions, risk-of-bias judgments and certainty grading require data
RCMS does not currently hold; the interface must not manufacture them.

No GUI/statistical behavior changes are claimed by this design document.

## Retained observations

The research bundle under `artifacts/verification/results-design-2026-11-15/`
retains [numeric observations](../artifacts/verification/results-design-2026-11-15/numeric-observations.json),
[PDF geometry observations](../artifacts/verification/results-design-2026-11-15/pdf-observation.json)
and [export observations](../artifacts/verification/results-design-2026-11-15/export-observations.json).
The rounded-null example is a constructed code-path observation, not a fitted
end-to-end analysis. The inspected PDF pages document the existing report's
layout; they are not proof that the proposed pagination is implemented.
Completed UI polish and its qualification are recorded separately in the
[implementation report](ui-ux-implementation-2026-11-15.md).
