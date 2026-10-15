# PR #537 CI repair — stopped on a demonstrated measurement defect

Implementation and merge work stopped on 16 October 2026 under the user's explicit
rule: if the complexity gate demonstrably mis-measures, stop and report instead of
changing it. PR #537 remains open. No merge, tag, release, branch deletion, force
push or settings change occurred. Local checkout remains ux/audit-improvements.

## Defect and exact reproduction

`scripts/code_health.py:_next_r_token` scans `%||%` as `%`, `||`, `%`;
`_r_metric_at` counts that middle token as a boolean branch. `%||%` is one R
custom infix operator, not the language's `||` operator. Aliasing the exact same
operator changes its reported complexity without changing any execution:

```r
`%||%` <- function(x, y) if (is.null(x)) y else x
`%fallback%` <- `%||%`
a <- function(x) { x %||% 1 }
b <- function(x) { x %fallback% 1 }
stopifnot(identical(a(NULL), b(NULL)), identical(a(2), b(2)))
```

Using the unchanged `r_function_metrics` on this file reports a: cyclomatic 2 /
cognitive 1; b: cyclomatic 1 / cognitive 0. Pinned R 4.6.1 confirms exact outputs.
Reproduce with `r_function_metrics(Path(folder), ["operators.R"])` after writing
the snippet to that folder, then run the same file with the pinned Rscript.
The full observed output is retained in `raw/ci/r-operator-measurement.log`.

At approved c62df31, `rcmetar.reitsma.plot.data` has 29 such operators. They account
for 29 of its 36 reported branches (cyclomatic 37). This is a material false
positive. Other `%||%` users can be affected as well. No tokenization, branch
measurement, threshold, exemption, baseline or numerical oracle was changed.

I refactored the 23 reported functions before identifying this lexical defect;
some R splits therefore address inflated measurements. Those ordinary commits
remain pushed and reviewable; no history was rewritten. Resolving the measurement
and deciding which R splits to retain are outstanding before further qualification
or merge work.

## Completed fixes and evidence

- Strict typing: 44 initial errors in evidence drivers repaired through concrete
  Qt/XML types, required values, typed QtTest seams and current Results fields.
- Native Results: validate Text report / Tables / Forest Plot navigation and
  contract-held References; 20 existing fail-closed evidence tests pass.
- Remaining Surfaces: prove blank covariate rejection, then enter a valid name
  before observing actual acceptance. Windows check passed at 20c883c.
- Windows source: explicitly decode UTF-8 Git source, fixing the reproduced
  cp1252 0x9d failure. Restore matching stdout decoding in the process test.
- Core GUI fixtures: current sample arm names and subtype accessor, current
  expanded metric label, real radio-indicator click with selected-state/exact-count
  proof, explicit synthetic geometry provider, and a loaded sample for table/DPR
  proof. The latest Windows-specific repairs still await GitHub results.
- Configuration, report, plotting and verification-helper refactors split real
  presentation stages; CI-COMPLEXITY.json retains all 23 before/after measurements.

Local results on the retained source/test state:

| Gate | Result |
| --- | --- |
| Exact changed-code command, original stable baseline | PASS (20c883c); measurement defect above still applies |
| Strict Windows-target typing | PASS, unchanged scope and rules |
| Strict goldens | PASS, no refresh |
| Original numerical fields | 415 exact; maximum difference 0 |
| Broad fast/GUI sweep | 764 passed, eight platform skips (5906b86) |
| Focused core fixture replay | 42 passed |
| Native drives | Doctor plus seven scenarios passed |
| Fresh full profile | Interrupted under stop rule during R package checking; **not qualified** |
| Arm-names native continuation | Interrupted under stop rule; **not qualified** |
| Generic-effect native continuation | Not run |

The passing native scenarios are project-axis-sequential, project-reviewer-predictions,
project-release-coefficients, plot-workflow-funnel, plot-workflow-regression,
project-table-covariates and review1-design. All use real Qt/xcb and the pinned
private R runtime. Two representative sequential/prediction frames were inspected;
this is not a complete new visual audit. Earlier failures, one diagnostic modal
interruption and the intentional stop receipts remain separate from passing runs.
`CI-EVIDENCE.json` binds retained receipts and artifact manifests.

## GitHub check snapshot at stop

Source/test head: 5906b8660a99aea4338c04f420c86f34ac146af6. The later stop-record
commit changes documentation only. Check snapshot is retained in
`raw/ci/checks-stop-5906b86.json`; this is not an all-green claim.

| Check | State at stop |
| --- | --- |
| Deterministic code-health baseline and gates | Passed |
| Qt6 Verification Change Classifier | Passed |
| Source and Platform Verification — Linux | Passed |
| Focused Native macOS Packaging Contracts | Passed |
| Native Qt6 Vertical Slice | Running |
| Native Qt6 Remaining Surfaces | Running |
| Source and Platform Verification — Windows | Running |
| Source and Platform Verification — macOS | Running |
| Required Windows Full R Stack Evidence | Running |
| Required Windows x64 Package Qualification | Running |
| Packaging Contract Tests | Running |

There is no merge SHA or post-merge verification because no merge was attempted.
