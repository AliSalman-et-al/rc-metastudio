# Sequential forest improvements — design discussion

Status: implementation and Opus 5.5 design/copy review complete; final local
qualification pending. Core choices and HR/IRR reference confirmed by the user.

## Established requirements

- Preserve RC MetaStudio's existing forest styles and structure.
- Show the pooled effect and confidence interval for each leave-one-out fit.
- Add per-row heterogeneity from the corresponding authority-package fit.
- Support ordering leave-one-out results by pooled effect after omission and by
  remaining I², with the lowest I² first.
- Keep statistical estimation and inference with the selected R package.
- Consult Opus 5.5 on visual design before implementation.

## Behavior before this change

- Leave-one-out effect-size ordering already sorts the omission fits' pooled
  estimates. Per-row heterogeneity is not displayed in the forest.
- Cumulative ordering is disabled in setup and editing. Each fit uses the next
  prefix of the input sequence.
- Saved plot regeneration uses stored fits; it does not recompute analyses.
- All sequential forest styles share a text-rendering seam and preserve their
  subset fits, providing a common source for an aligned heterogeneity column.
- HR/IRR leave-one-out forests have no all-studies row. The current ordering
  code nevertheless pins their first row; this is a defect to repair.

## Decision tree

1. Cumulative meaning — confirmed.
   - Offer table, year and individual study effect-size ordering before fitting.
   - Refit when the addition sequence changes; preserve cumulative step order.
   - Do not sort fitted cumulative rows by pooled results or invent a greedy
     heterogeneity-driven addition algorithm.
2. Heterogeneity display — confirmed.
   - Shared layout: study label, k, I², forest, effect estimate and confidence interval.
   - Remove cumulative k suffixes from study labels when k has its own column.
   - Show I² by default with a shown/hidden choice; defer optional τ².
3. Leave-one-out options — confirmed.
   - Remove the weight-order option from leave-one-out controls.
   - Retain explicit pooled-effect-after-omission and I²-after-omission ordering.
4. End-to-end workflow — additional Opus 5.5 consultation requested.
   - Review setup controls, editing versus rerunning, structured result tables,
     written reports, export consistency and saved results as one workflow.

## Agreed implementation

- Cumulative `cum_sequence` is an analysis setting (table/year/study effect).
  Plot `fp_study_order` remains a display setting; LOO gains `i2` ordering.
- Add an actual all-studies HR/IRR fit, confirmed by the user, matching the other
  leave-one-out families. Old stored omission-only plots remain regenerable.
- Preserve style markers. Bold the LOO reference label and separate it with a
  thin rule; do not introduce new marker semantics or shaded confidence bands.
- `k` comes from each package fit, not its cumulative step. I² comes from the
  fit, uses one decimal consistently in figure/table, and remains in tables
  when the figure column is hidden. Missing fields display as unavailable.
- Keep the detailed numerical table in canonical analysis order, with an
  explicit Step/Study added or Study omitted identity. The figure caption states
  its independently editable row order.
- Results give the cumulative final fit or the LOO full fit and descriptive
  omission ranges with named endpoints. No per-row prose dump. All numerical
  rows remain available across exports.
- Cumulative plot editing shows the saved sequence with a visible rerun
  explanation. Change settings carries appearance into a new run; cancelling or
  a failed run preserves the existing result.

## Report defect reported by the user

Both current sequential reports turn every fitted row into the same unlabelled
"The pooled ... was ..." sentence, then repeat all those values in the table.
This is an information-design defect, not a request to remove the numerical data.

Required repair:

- Generate workflow-specific Results prose instead of applying the ordinary
  pooled-effect sentence to every sequential fit.
- Leave-one-out: identify the full fit where available and concisely describe
  the range of omission-fit estimates, with named omissions where informative.
- Cumulative: state the addition sequence, identify initial/final fits where
  useful, and retain the steps in accumulation order.
- Retain every fit, CI and available heterogeneity value in structured tables;
  explicitly label studies as omitted or added rather than generic "Effect".
- Do not infer robustness, stability, causation, or a recommendation to exclude
  studies from a P-value threshold or an invented change threshold.
- Treat missing and non-estimable fits explicitly, including any summary range's
  denominator; do not silently omit failures from the written account.
- Apply the same report content to screen, clipboard, PDF and DOCX.

The shared report generator currently appends ordinary per-row sentences through
`_pooled_rows` and `_effect_summary` in `manuscript_report.py`; preserve the
complete structured numerical rows while separating their presentation from
workflow-specific prose.

Once these meanings are settled, specify ties, unavailable estimates, baseline
placement, report/export consistency, saved regeneration and independent
per-subset numerical comparisons before changing implementation.

Functional reference: [dmetar InfluenceAnalysis documentation](https://dmetar.protectlab.org/reference/influenceanalysis).
Its effect-size and I² sorted forests are leave-one-out diagnostics.

## Opus design recommendations

- Shared layout: study label, k, I², forest, existing effect/CI text. Remove the
  cumulative k suffix from study labels when k has its own column.
- Preserve each style's fonts, markers, colours and banding.
- Distinguish a real all-studies reference with a bold label and separator;
  preserve style markers. This supersedes the first consultation's diamond
  and reference-line suggestion. Old omission-only bundles remain regenerable.
- Keep cumulative rows in accumulation order and distinguish the final full fit.
- Name leave-one-out ordering explicitly: pooled effect after omission and I²
  after omission. Recommend removing its ambiguous weight-order option.
- Prefer I² alone initially; defer optional τ² unless requested.
- Use stable table-position tie breaking and put unavailable results last.
- Budget measured column widths through the existing layout preflight, retaining
  full study labels and effect/CI text in exports.

## Statistical and interaction qualifications

- Fit fields, not the presence of an I² metadata declaration, determine whether
  the package reports I². The code investigation confirms subset fit objects
  remain available, including for MH/Peto paths.
- The retained pinned-metafor probe `package-k-probe.R` shows MH and Peto
  report k=4 but k.yi=3 for four input studies including one double-zero study.
  Keep the package's k field; do not relabel k.yi as k or assume every excluded
  individual effect reduces the package's reported count. This corrects the
  consultation's unverified MH acceptance example.
- Do not replace a package-reported singleton I² with a dash solely because
  k equals one. Display genuinely unavailable values as unavailable.
- Sort with unrounded I². Equal displayed percentages need not be numerical ties.
- Do not automatically disable sorting just because displayed I² values look
  identical. True ties can retain table order without altering statistics.
- The report uses one complete sequential table before Model fit, without a
  duplicate Pooled effect table or a misleading Study results/weights table.
  Its combined CI cell retains both raw interval quantities for CSV export.
  Omission-range prose states the successful-fit denominator; unavailable
  fits remain identifiable in the table and the narrative.
- Automatic column removal and silent dropping of optional columns at narrow
  widths are not settled requirements; prefer consistent explicit settings and
  measured layout over surprising export-dependent content changes.

## Required proof before qualification

Define these behavior checks before implementing the feature. Extend the existing
real Qt/R drives and their report-retention observer rather than creating a second
test harness. Retain inputs, exact commands, observed values and exported files.

1. Leave-one-out effect and I² ordering: compare each labelled subset with the
   corresponding direct public-package fit. Sorting changes row presentation,
   never the subset, estimate, interval, heterogeneity or label-to-value mapping.
2. Stable ties and missing values: sort unrounded package values, retain table
   position for true ties and put unavailable values last. An equal displayed
   percentage must not erase a real numerical ordering difference.
3. Baseline placement: pin an actual all-studies fit only when present. Exercise
   HR/IRR without that row so their first omission participates in ordering.
4. Cumulative addition order: table, year and individual study effect each build
   the expected prefixes. Compare every prefix with the public-package fit;
   intermediate fits may change, while the final full fit stays the same.
5. Workflow controls: LOO exposes explicit result ordering and no weight option;
   cumulative setup reruns a changed sequence. Saved plot editing explains why
   it cannot change that sequence without a rerun. Cancel preserves saved state.
6. Shared forest geometry: in Default, RevMan and BMJ, decoded SVG text and
   geometry prove study, k, I² and effect/CI columns remain aligned with their
   markers. Include long labels, narrow width and native 100%/150% display scales.
7. Missing/non-estimable subsets: retain their labelled rows and unavailable
   fields. Summaries explicitly count unsuccessful fits instead of silently
   treating only successful fits as the entire analysis.
8. Workflow-specific Results: one concise account replaces the repeated generic
   pooled-effect sentences. LOO identifies omission estimates as such; cumulative
   identifies the sequence and final fit. Neither asserts robustness, causation,
   significance-driven study exclusion or an invented influence threshold.
9. Complete tables: every fit, confidence interval and available heterogeneity
   value survives with an explicit omitted/added-study label and the correct k.
   Combined diagnostic metrics remain separate and identifiable.
10. Output consistency: screen, clipboard HTML/text, PDF, DOCX, CSV and saved
    regeneration retain their applicable content and ordering. Report exports
    remain self-contained and the report-retention observer checks all rows.
11. Boundary cases: singleton cumulative prefixes, two-study LOO, dropped
    double-zero effects, MH/Peto fits, ratio-scale transforms and multi-metric
    univariate diagnostic analyses follow package results without invented I².
12. Qualification starts with retained Windows strict typing, then targeted
    native drives and the full profile required by the verification skill for
    shared R analysis changes. Creative changes receive Opus review before commit.

## Retained verification and review

- Opus 5.5 cleared the final UI/UX, design and copy. Its conditional missing-year
  Methods correction is applied; no additional statistical behavior was added.
- `artifacts/verification/sequential-design/cross-family.R` retains 16 year/effect
  sequence comparisons across OR, PLO, MD, Mean, Sens, Spec, HR and IRR. Its JSON
  records inputs, full-precision observed/authority results, table quantities and
  saved plot prefixes; the SVG and regeneration files are retained beside it.
- The Windows 150% native drive passed at
  `artifacts/verification/rcms/20261117T125324Z-f324a30e-review-workflows`.
  It proves successful FE sequence reruns, draft appearance preservation,
  cancellation, omission I²/effect sorting and an independently hidden I² column.
- The final default-scale native drive passed at
  `artifacts/verification/rcms/20261117T130542Z-0f6df6c9-review-workflows`.
  It additionally retains the actual metafor non-convergence path: setup remains
  open, the package error is inspectable and existing output stays unchanged.
  RCMS does not silently change the estimator after a package failure.
- The frozen effect/CI/SE/P oracle is read from the sequential table's typed
  fields by study identity after the layout change. Frozen ZIPs, numeric contracts
  and tolerances are unchanged. Four exact before/after text and PNG descriptor/
  SHA-256 bindings record the requested presentation migration. New k/I² fields
  are compared separately with public-package subset fits.
- The compact Results header uses the estimator abbreviation, e.g.
  `Random-effects (REML)`, retaining its full name in the tooltip and report.
  Native light/dark checks passed at
  `artifacts/verification/rcms/20261117T132735Z-632d59bc-ui-refresh`.
- Windows source qualification passed: 1,118 Python/GUI/packaging checks with
  three skips; the current-source R-stack lane passed its
  package checks, ten bridge checks, all 140 desktop cases and 476 frozen
  compatibility comparisons covering 416 numerical fields.
- The outer full wrapper's additional authority invocation initially selected an
  ambient user-library dependency and failed its version guard. The failed
  transcript remains at `artifacts/verification/rcms/20261117T145635Z-bee6f48a-complete/`.
  With the pinned runtime library ordered before development helpers, all 103
  authority comparisons and doctor passed. This recovery does not relabel the
  original wrapper as successful.
- After that frozen run, the IRR harness regained its study-specific explanation
  assertion for unavailable subsets; the complete IRR drive passed again. This
  verification-only strengthening changed no application or R statistical code.
  Commands, input digests and transcripts are under
  `artifacts/verification/sequential-design/`, including
  `python-recovery-final.log`, `irr-reason-final.log`,
  `authorities-ordered-recovery.log` and `doctor-ordered-recovery.log`.
