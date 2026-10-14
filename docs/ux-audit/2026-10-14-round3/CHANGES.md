# Round 3 changes and proof

The plan was committed before product changes (`71a8545`); the real desktop row
and export assertions followed (`8be25b7`). Review the retained observations with
the screenshots, rather than treating a screenshot as a numerical oracle.

| Finding | Implementation commits | Proof and retained observations |
| --- | --- | --- |
| R2-01 | `44e50ae`, `b57fa5e` | Explicit `has_overall` travels with producing fits, renderer bundles, and regeneration state. Every SVG study label shares a y-coordinate with its matching estimate/CI; every report row matches that SVG caption. All ten families, both sequential workflows, diagnostic Sens/Spec, excluded HR/IRR studies and a non-estimable IRR omission are exercised in `OBSERVATIONS.json`. HR/IRR omission-only results never acquire an All studies row. |
| R2-02 | `785bef7` | Copied/exported text starts with the exact executed-result identity. The original HR/IRR result still copies its original outcome, metric, comparison and follow-up after another project opens. The screen stays configuration-first. Retained `screenshots/*-report.txt` and `round3-report-copy-export` observations contain the actual copied/exported bytes. |
| R2-03 | `785bef7` | The same production serializer powers both actions. Header cells and every data row remain tab-separated, including blank cells; prose remains paragraph text. Copy and disk export match exactly for standard, sequential, subgroup and mixed diagnostic reports. |
| F01/F02 | `e6c8369` | Fixed figures omit tau-squared but retain Q/df/P/I-squared. Fixed result configuration excludes random estimators before and after fixed-to-random-to-fixed re-runs. Mixed diagnostic configuration lists five components once, with selected DL on Sens/Spec and actual REML on DOR/PLR/NLR. See `round3-fixed-footer`, `round3-fixed-random-rerun` and references report observations. |
| F03 | `76d9f62`, `b57fa5e` | All subgroup families display fitted k and within-group Q/df/P/I-squared, applicable tau-squared, and existing package prediction intervals when available. Direct public `metafor::rma.uni` fits independently check newly displayed fields and `stats::predict` bounds. Sequential row roles and years agree with figures. Ratio omission reports explicitly say omission-only. |
| F04 | `0a979bb`, `b57fa5e`, `5080d4b`, `f68562f`, `039ef01`, `a56ed34`, `70b996c` | Bubble ticks use the full actual plotted range, including the confidence band. Comparative sequential figures draw an in-range null; the real MD editor's 0.5–2 limits remove it. RevMan/BMJ use spaced ticks so metafor cannot silently drop the null label through overlap. Entered zero CI bounds show zero, while genuinely small effects and standard errors remain nonzero. |

`c7fd142` adds the public subgroup references, source-bound Linux verification
support, and fresh-process family drives. `cce88dc` completes the precision and
explicit-limit drives, updates the intentionally changed copy-report contract,
and deletes the obsolete static bubble tick assertion. No positional first-fit
compatibility path remains.

`7afbbbe` refreshes six reviewed report-text sections in the observed golden
archive: subgroup k/heterogeneity columns and sequential roles/year labels. The
archive's original numerical outputs, numeric rows, tolerance policy and
exceptions remain unchanged. Archive SHA bindings are the only changes to the
numeric and plot-descriptor contracts. New continuous subgroup fields are kept
separately as `additional_outputs` (18 fields) and verified through public fits,
so they cannot silently replace any of the original 415 fields.

The presentation tolerance is eight machine epsilons of each effect/CI row's
maximum absolute magnitude. It changes strings only. A near-zero bound relative
to a 0.2/0.4 row becomes zero; an entire row around `1e-10` retains its estimate,
bounds and SE. Axis labels use the scale of the tick range. Package fits, stored
values and original numerical gates are unchanged.

Curated PNGs are unmodified native captures. `SCREENSHOTS.json` records action,
source and SHA-256; `OBSERVATIONS.json` records actual inputs, tables, public
references, runtime identity and the original manifests. `NUMERICAL-EQUIVALENCE.json`
contains all original values and observed counterparts. Raw logs stay ignored.

No new analysis, statistical test or independently invented PI was added. This
round uses existing fitted outputs and public package prediction methods. Native
OS file pickers, fractional DPI, accessibility and installed release packages are
outside these drives; the file picker returns a test-owned path.

`446f65b` records the small-effect geometry failure before its fix. `039ef01`
removes the absolute axis-span/padding floors and uses existing measured text
widths for sparse RevMan tables, including the fitted model label. The real
`1e-10` precision fixture now shows five ticks and six visible intervals; model,
weight and estimate columns remain readable. Native screenshots and the
300-case gallery cover this presentation change.

The user expanded this round to optimize blocking verification on weak hosts.
`b768ffc` replaces floating-point TIFF intermediates with a packed native raster.
`e92463f` removes the duplicate full-profile desktop traversal, serializes desktop
cases on every platform, retains canonical SVGs with bounded gallery previews,
and removes unnecessary full-image copies. Its HR/IRR public-package drives use
the new sequential roles and years. See BENCHMARKS, TIFF-BENCHMARK, TIFF-PIXELS and
CONTACT-METRICS for independent performance/output checks. Original timeouts,
publication dimensions and statistical coverage remain in force.

Final native review caught a 7.535-point weight/estimate overlap at ordinary
scale. `a56ed34` adds the real SVG text-length/anchor proof before the fix;
`70b996c` replaces the remaining fixed annotation offset with the measured
block gap. Every ordinary-scale weight/estimate pair now has at least four
points of separation, while the tiny-scale fixture retains visible intervals
and five scientific ticks. The final full profile is repeated after this fix.

`b77e0f4` records the additional speed/reliability obligations before changes.
`273bd6a` replaces blanket offscreen serialization with CPU/RAM/cgroup-bounded
workers and enables resuming only intact passed evidence with identical execution
inputs. Native drives retain one display owner. The real cache proof damages
artifacts and changes source/startup configuration, observes fresh reruns, and
verifies failed startup is never cached. See DX-RESUME and the final full/fresh
profile for proof; `--fresh` retains an uncached qualification path.

## Opus review 1 — report repairs

Findings 2–5: ratio standard/sequential/subgroup references and fixed regression
now share fit-owned reference selection; binary/continuous/diagnostic standard
fixed/MH/Peto producers already select their correct sets, inherited by their
sequential and subgroup workflows. Standard heterogeneity now uses Q, df,
p-value, I² and random-only τ² from the fit, matching subgroup columns. Removed
ratio display-note duplication and gave sequential summaries descriptive model
titles. Result identity now places workflow details before diagnostic metric
configuration, equally for screen/copy/export. Statistical fitting is unchanged.

The native HR drive `review1-reports-hr` passed with a single omission note,
fixed-effect references and independently verified standard heterogeneity. The
expanded reference matrix first exposed a harness assumption: diagnostic table
titles include their metric prefix. That failed attempt is retained; the check
now selects tables by their Heterogeneity suffix. Final gates/evidence follow.

## Opus review 1 — axes and regeneration boundary

Findings 1, 6 and 7: automatic log bubbles now choose 1/2/5 display-scale
values across the actual rendered range; logit bubbles use round probabilities,
with a display-scale pretty fallback for narrow ranges. Closely spaced tail
labels are thinned and ratio/probability labels lose decimal padding. Linear
axes still use pretty. Missing/invalid sequential overall flags now fail at
construction/validation with a specific TRUE/FALSE requirement. Forest range
owners expand collapsed floating-point ranges relative to their magnitude; the
ordinary and tiny-effect ranges retain their original scale. All styles receive
these valid ranges, eliminating the need for repeated layout span floors.

`review1-r-presentation` passed the summary and forest renderer tests, including
invalid overall flags and valid regeneration. Native precision has already
proved round OR labels and nonzero default/RevMan/BMJ ranges for 1 with SE 1e-20;
the final complete native run and proportion screenshot remain due below.

## Opus review 1 — golden extraction and reviewed text

The standard-table change exposed positional heterogeneity extraction in the
golden capture. Capture now reads Q/df/p/I²/τ² by the report headers and continues
to understand the historical archived headers. It explicitly excludes subgroup
rows; their independently checked quantities do not alter the frozen contract.
The reviewed refresh changes only three standard-summary texts, their capture
members and the archive manifest/SHA bindings. REVIEW1-GOLDEN.json records exact
before/after texts and proves every fitted output and every figure byte retained.
`review1-golden-strict` exits 0; original-field equivalence remains exact.
