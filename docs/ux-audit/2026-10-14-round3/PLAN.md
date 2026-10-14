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
