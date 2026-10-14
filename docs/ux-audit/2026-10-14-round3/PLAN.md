# Round 3 proof plan

Written before implementation. Branch: `ux/audit-improvements`.
Statistical estimation, input eligibility, existing numerical values, and frozen
oracles remain unchanged. No new analysis, test statistic, or prediction interval.

## Runtime prerequisite

Establish the manifest-pinned R 4.6.1 runtime from the repository's SHA-256-pinned
Posit Noble archive in a persistent test-owned directory. Use the dated Noble
binary library policy, install current RCMetaR source into a test-owned library,
and record runtime, dependency, and installed-source provenance. Run doctor with
the existing Qt verification build and native display `:0`. If that runtime cannot
be established, stop and record the exact missing prerequisite. System R 4.3.3 is
not an alternative. Raw transcripts remain ignored.

## R2-01: sequential row identity

Failure modes: omission-only fits mistaken for an overall fit; first or last name
lost; estimate and interval shifted onto another study; excluded or non-estimable
rows shifting identities; cumulative and existing overall-plus-omission paths
broken by the repair. Replace positional inference with explicit result metadata.

Before production changes, extend the real desktop audit drive to compare every
sequential report row and rendered SVG row by role, name, estimate, and CI. Exercise
cumulative and omission paths for binary, continuous, both one-arm families,
generic effects, regression coefficients, diagnostic sensitivity/specificity,
HR, and IRR. Include an excluded HR study and a non-estimable IRR study. Compare
fits with independent public package results where supported. Preserve inputs,
row comparisons, actual plots, and native figure/report captures.

## R2-02: exported clinical identity

Failure modes: copy or text export lacks analysis, outcome, type/metric, comparison
or groups, or follow-up; identity follows the current workspace instead of the
executed result; screen order changes. Drive copy and text export from an actual
result, change the workspace, and repeat. Require the same result-owned identity
as the visible header and configuration-first on-screen body. Check one-arm and
diagnostic identities as well as comparative results. Retain exported payloads.

## R2-03: readable plain-text tables

Failure modes: cells become separate lines; multirow numbers lose their labels;
empty cells disappear; paragraph prose becomes fixed-width text; copy differs
from export. Require a heading row and one tab-separated or aligned line for each
structured table row, preserving cells and order. Compare copied and exported
text with result-owned tables in the real Qt application. Inspect native reports
and retained text for standard, sequential, subgroup, and diagnostic outputs.

## F01 and F02: executed model settings

Failure modes: fixed forest prints estimated tau-squared; fixed report retains a
random estimator; stale settings survive fixed-to-random or random-to-fixed
re-runs; diagnostic components duplicate estimators or attribute the wrong method.
Drive fixed and random fits and both transitions through result-owned re-run.
Require fixed footers to omit tau-squared while retaining Q, df, P, and I-squared.
Require configuration to list only applied settings, each diagnostic component
once with its actual estimator and inference. Inspect standard and sequential
figures plus diagnostic mixed-component reports. Compare existing numerical fields.

## F03: complete and consistent report tables

Failure modes: subgroup k, within-group heterogeneity, or existing PI omitted;
fixed groups acquire tau-squared or PI; group test confused with within-group Q;
sequential labels disagree with figures; omission-only ratios imply a full fit.
For all supported data types, compare subgroup table k, Q, df, P, I-squared,
applicable tau-squared, and available PI with the original package fit outputs.
Independently verify newly displayed fields with public package fits. Do not
calculate a missing PI. Compare sequential report and figure roles: Study added
(k), All studies, and Study omitted: X. Explicitly identify omission-only HR/IRR
reports. Retain complete structured tables and native report captures.

## F04: precision, ticks, and null references

Failure modes: bubble ticks cluster in a small portion of the CI range; comparative
sequential null line missing or outside explicit limits; floating-point residue
prints as meaningful precision; genuinely small values rounded away; report and
figure precision disagree. Before changing formatters, specify a presentation
tolerance for arithmetic residue and distinguish it from small nonzero inputs.
Drive bubbles with wide CI ranges and inspect tick coverage. Inspect comparative
MD/SMD and ratio sequential SVGs for an in-range null at 0 or 1, including explicit
limits excluding the null. Exercise entered zero CI and genuinely small nonzero
effects in native coefficient/generic figures. Numeric fit fields stay identical.

## Required gates and delivery

Run numerical equivalence against all 415 retained original fields, golden gates,
the complete R-stack lane, `verify_all.py --full`, affected targeted checks, and
serial native drives for changed figures, reports, copy, and export. Preserve
commands, exit status, inputs, observed assertions, and failure transcripts.
Visually inspect every screenshot cited. Golden numerical contracts, tolerances,
and exceptions are never regenerated to hide a failure. Any presentation-only
golden drift is recorded for review before an authorized refresh.

Commit small changes with normal descriptive messages. No push, PR, history
rewrite, system-library install, or qualified-package modification. Deliver README,
CHANGES mapping items to commits and evidence, TESTS with exact commands/results,
a reproduction script, curated screenshots, and an updated HANDOFF. Mark every
unfinished or unproven item explicitly.

## Subsequent user instruction

After implementation began, the user authorized `git push origin ux/audit-improvements`
after every commit, including the nine existing commits in the first push. Only
ordinary fast-forward pushes are allowed. A failed push stops work and is reported
verbatim. No PR or history rewrite is authorized. This overrides the original
no-push delivery rule above; the original proof plan remains intact.

## Linux export verification budget

Observed before changing the harness budget: both complete HR/IRR editor drives
made valid progress through PDF/PNG exports but exceeded their 600-second process
limit while rendering publication TIFFs. The subgroup raster has 89,661,600
pixels. Preserve all six editors, all 24 decoded exports, 600 dpi dimensions,
public numeric comparisons and rollback checks. Allow a bounded 1,800-second
Linux budget for these complete drives; keep other scenario budgets unchanged.
Prove actual completion and retain elapsed times and failures. This changes no
product behavior, output resolution, assertion or statistical tolerance.

## User-requested resource optimization

The user subsequently requested optimization of blocking verification on this
weaker Linux laptop. Before implementation: TIFF builds an RGBA double array,
separate alpha/channel intermediates and another RGB array; concurrent export
jobs reach multi-gigabyte RSS. The 300-image validator also creates unnecessary
full-sized white and difference images. Timeout extensions alone do not fix this.

Failure modes to prove: changed TIFF colors/alpha compositing, lost white margins,
changed dimensions/DPI/compression, skipped export work, undeleted staging files,
and faster validation that misses empty/corrupt figures. Reuse existing pinned
PNG decoding with nativeRaster and the real TIFF device; independently decode
outputs, retain the existing transparency/DPI gate, and run complete desktop
edit/apply/cancel/four-format exports. Retain a real subgroup SVG input, before/
after commands, errors, dimensions, hashes, peak RSS and elapsed time. Alternate
five fresh-process runs per implementation; do not count failed or interrupted
runs as completed performance measurements. Profile separately. Validate all
300 existing PNGs with full decoding and channel extrema instead of allocating
white/difference canvases. Run resource-heavy lanes serially; re-run the full
profile with unchanged numerical checks after the rendering change.

## Portable verification work reduction

Before implementation: the full profile runs the same desktop registry in the
R-stack pytest lane and again as individual commands. Keep the complete pytest
lane, doctor and authority comparisons, but remove the second traversal. Prove
the collected desktop case count matches the registry excluding doctor, all
cases pass, and their manifests remain available. Serialize desktop cases on
every platform: concurrent publication exports compete for memory and CPU;
native display driving also has a single owner. No timeout increases.

The 300-case geometry gallery currently rasterizes all images at 600 dpi even
though its canonical SVG is sufficient for detailed review. Keep all 300 fits,
styles and scenarios and retain canonical SVGs, with previews bounded to a
2,400-pixel longest edge. Publication export remains covered by the existing
real desktop four-format drives. Failure modes: lost cases or SVG artifacts,
incorrect aspect ratio, hidden rendering errors, empty/corrupt previews. Decode
every preview and parse every SVG; compare canonical SVGs with the prior gallery
by geometry/text, not timestamps or generated IDs. Retain timings and dimensions.

Avoid whole-image copies for a corner-pixel check and derive contact-sheet
metrics from RGB extrema/histograms instead of allocating white/difference
canvases. Prove the metrics match the old implementation on existing real
artifacts, including blank and nonblank images; full decoding remains required.

## Small-effect geometry found during visual inspection

Before changing layout: the native `1e-10` fixture preserves report values but
collapses its figure's marks and leaves one tick. Coordinate scaling floors the
axis span at 1. Failure modes: collapsed tiny/narrow ranges, lost ticks, displaced
headers/footers, changed ordinary geometry. Extend the existing real precision
drive to require at least two distinct scientific axis ticks and six visible
horizontal intervals. Observe it fail before changing the shared span arithmetic;
then run it natively, inspect the figure, and rerun all 300 layouts and the full
profile. Keep numerical fitting and stored quantities unchanged.
