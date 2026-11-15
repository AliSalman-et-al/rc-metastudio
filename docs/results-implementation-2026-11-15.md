# Results implementation — 15 November 2026

Branch: `ui/desktop-polish-and-icons`. This implements the reconciled decisions
in [the Results design](results-presentation-2026-11-15.md), following the
[independent Opus design](results-opus-design-2026-11-15.md). Forest landing and
the separate prediction-interval block remain as accepted.

## Changes

- Batch A (`f5e195f2`): preserve producer precision; remove rounded-null,
  categorical I² and automatic small-study significance verdicts.
- B/C (`23ac22ef`): lead subgroup prose with the formal comparison, use
  diagnostic summary language, require complete participant denominators,
  provide editable HTML/TSV copying and aligned paper tables with repeated
  headers and readable fonts.
- D: carry validated per-cell quantities from R arrays through the bridge,
  primary/study/model-fit tables and supplementary output. Roles control numeric
  routing. SE identifies its analysis scale; τ² identifies squared log/logit
  units. No formatted statistic is parsed to infer a more precise number.
- Tables offer **Export formatted CSV…** and **Export values CSV…**. The latter
  writes one record per quantity, with its exact double, role, scale, interval
  level and original display text. Combined CI cells export separate bounds.

The contract stays at v1: result objects are not saved in projects and both
producers qualify together. Small-study text summaries, bootstrap summary text,
references and other text-only tables remain formatted output; their numeric
export action is disabled. No estimators, statistical oracles or tolerances changed.

## Evidence

All paths below are under `artifacts/verification/results-implementation-2026-11-15/`
unless an RCMS run is named. Failures and recoveries are retained.

- `proof-plan.md` and `opus-numeric-design.md` enumerate failure obligations
  before implementation. `attribute-probe.log` proves rpy2 attribute retention.
- A: `batch-a-qualified.log` and `batch-a-r-tests.log` prove real manuscript
  export and small-study output after removal of obsolete expectations.
- B/C: `batch-bc.log` and `batch-bc-final.log` cover rich copying, split vector
  figures and complete manuscript export. `word-clipboard-final.log` proves an
  actual editable 20×4 Microsoft Word paste with Unicode and escaped content;
  its DOCX and exact clipboard input are retained beside the log.
- D: `batch-d-gui-contract.log`: 85 GUI/boundary checks passed.
  `batch-d-r-summary-utf8.log`: 105 R display checks passed. The first R run
  used an unavailable Windows locale and failed Unicode comparisons; rerunning
  with UTF-8 preserved the assertions and resolved the environment failure.
- `batch-d-presentation-recheck.log`: three real Qt/R scenarios passed:
  `results-presentation`, `results-values`, `manuscript-export-direct`.
  The values drive covers 90% CIs/PIs for binary/continuous, HR/IRR, Reitsma,
  cumulative, leave-one-out, subgroup, regression and adjusted means. It checks
  exact CSV round trips and 279 independent public metafor/mada comparisons
  within one floating-point step, retaining inputs and the recomputation script.
  It also exercises missing/infinite/tiny/residue states at the R boundary,
  renamed headers and metadata preservation in combined diagnostic results.
- Focused evidence: `artifacts/verification/rcms/20261115T150505Z-6380a551-results-values/`,
  `20261115T150350Z-092869b8-results-presentation/`, and
  `20261115T150350Z-9d16297d-manuscript-export-direct/`.

## Opus review and corrections

[Opus's final review](../artifacts/verification/results-implementation-2026-11-15/opus-final-review.md)
found two blockers. Both have been corrected:

- The overall-t lookup now excludes the between-subgroup comparison table. A
  real Knapp–Hartung subgroup drive first reproduced the false `t (df = 1)`
  heading (`opus-recovery-before.log`), then passed with an unqualified `t`
  heading and no fabricated df sentence. The between-group statistic keeps its
  own Q/F identity.
- The diagnostic driver explicitly selects Sens/Spec/DOR, asserts the selected
  and executed Reitsma method, and requires at least 18 Reitsma comparisons.
  Every tested analysis must contribute public-reference comparisons. A DOR-only
  run can no longer pass under the Reitsma label.

The correction also describes the separate DOR model in combined diagnostic
Methods, labels its PI by metric, uses “summary sensitivity/specificity,” removes
placeholder/SE-scale noise from CSV row identities and guards unavailable
regression heterogeneity fields. No estimates or inference choices changed.

`opus-recovery-focused-final.log` records three passing real Qt/R scenarios.
The expanded values drive has 320 public-package comparisons, now including
adjusted means reconstructed from raw counts and t-inference subgroups, all
within the original one-floating-point-step limit. It also checks the
Freeman–Tukey PI fallback scale at the real R boundary. The GUI/contract lane
passes 85 checks and the expanded R display lane passes 115 assertions.
Evidence: `20261115T153319Z-e54b14ca-results-values`,
`20261115T153207Z-affbd901-manuscript-export-direct`, and
`20261115T153207Z-ee9273d9-results-presentation` under `artifacts/verification/rcms/`.

The earlier full profile was deliberately interrupted before source edits
(`interrupted-profile.json`). Its R package check passed; its complete profile
did not pass. Its transcript and failures remain retained. The original failed
adjusted-means reference output retains the exact hash in its manifest; reference
recovery reconstructs effects from raw counts rather than the preview values,
without changing any statistical oracle or tolerance.

Final Windows results are recorded in the
[UI verification closure](ui-fable-polish-2026-11-15.md#final-verification).
All 136 desktop scenarios have passing evidence on the frozen application after
targeted recovery of obsolete UI contracts. The source golden comparison passes
11 cases and 475 comparisons; the values export passes 320 public comparisons.
The raw full-profile command remains failed and retained; its later golden,
authority and doctor stages were run separately. No baseline or tolerance changed.
The final native tour passes 312 steps, including corrected popup captures.
Selected About-logo checks cover native fractional DPR; macOS/Linux, release
packages and exhaustive DPI/state or Word-page coverage remain unqualified.
