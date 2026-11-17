# DTA UI audit (2026-11-17)

Scope: diagnostic data creation/import/calculator, metric selection, standard and
sequential/subgroup/joint/combined/regression analysis, small-study effects,
results/report, plot editors/export and rerun. Other supported data families are
queued after DTA, as requested. This audit is not yet fully qualified or committed.

## Confirmed defects and changes

- LR-only selection offered Peto even though Peto calculates DOR. Native reproduction
  is retained in artifacts/verification/dta-audit/before-routing.log. The earlier
  before.log failed in probe construction (missing confidence level), not product.
- Method discovery now intersects the backend's feasible methods for each requested
  metric. This also restores DOR/LR Mantel–Haenszel and DOR Peto choices for supported
  sequential and subgroup workflows. The secondary combined panel uses the same
  workflow-aware intersection rather than a DOR surrogate or unconditional Peto ban.
- Diagnostic identity, plot captions and standalone report context say Index test,
  rather than Arm/Comparison. Diagnostic favour labels are not manufactured.
- Combined Sens/Spec panel effect label is limited to its own metrics; the second
  panel names its selected LR/DOR metrics. Shared controls only include parameters
  declared by an active method. Switching Reitsma on/off restores/removes its estimator.
- Missing Reitsma choices have a visible explanation for separate workflows,
  incomplete counts or selecting only one component of the joint model.
- The metric selector names both positive/negative likelihood ratios and identifies
  missing entered metrics. Form defaults agree with runtime defaults. Next fires on
  click and completes/deletes the selector instead of hiding a modal child.
- Diagnostic small-study settings explain that Deeks does not use ordinary/contour
  funnel confidence regions. Its effective-sample-size formula uses disease groups
  instead of internal n.e/n.c names. Joint Reitsma model configuration is listed once.

The user explicitly rejected RCMS-only statistical limits. Reitsma minimum-five
and meta-regression max(5, p+2) gates have been removed. Three/four/five-study
fits and four-study regression match direct mada coefficients, covariance and
log likelihood in test-reitsma-small-samples.R. Full R qualification is now required.
No numerical oracle or tolerance has changed. Backend public
API feasibility enforcement is outside the frontend routing fix; valid UI requests
are restricted by the real backend feasibility lists.

## Evidence and remaining work

Strict Ty passes precede native/GUI qualification. The GUI rerun passed 403 tests;
its two initial failures were exact expectations for the renamed selector title and
LR checkbox. Final stable-source qualification remains required before committing.

Native analysis-diagnostic-joint passed the eight LR/DOR availability combinations
(standard/cumulative/leave-one-out/subgroup) and three real Next/Cancel cleanup
cycles. Native analysis-diagnostic-combined passed dynamic estimator visibility and
panel-scoped metric labels. Combined captures are in
artifacts/verification/rcms/20261116T202107Z-7f3c1045-analysis-diagnostic-combined.

The serial native profile logs under artifacts/verification/dta-audit/native-*.log
cover joint/combined, small-study DTA, back-calculation, SROC editing/decoded export,
diagnostic creation, multiple-moderator regression and subgroup. Some are still
running; do not interpret the profile as passed until every exit is confirmed.

Remaining: review data entry/import/editor/rerun paths in depth; inspect new native
captures; prove newly restored fixed-effect sequential/subgroup execution against
public-package references (availability alone is not numerical proof); qualify all
local checks before commit. Opus's optional empty-header small-study table styling
remains under review. Proceed to other data families after the DTA pass.

The earlier suggestion to keep five as a conservative floor is superseded by the
user instruction and ADR-0007. Do not add a Python minimum-five explanation.
Package fitting errors/warnings must remain visible; no silent univariate fallback
should occur just because fewer than five studies are included. Other custom
statistical constraints are being audited against package defaults and limits.

## 17 November continuation

RevMan DTA missing-count imports now identify the missing fields; all-zero rows
remain stored but excluded. Text-only reports retain each source once as labelled
prose, instead of manufacturing empty-header numerical tables. Complete retention
is checked by the shared report observer on clipboard/PDF/DOCX.

Package-policy fixes now cover REML defaults (preserving explicit saved/RevMan
settings), raw-count diagnostic MH pooling, Peto/IRR drop00 defaults, two-study
prediction intervals and mada likelihood comparisons. Small-study settings expose
meta k.min with a Package default choice; RCMetaR reads the default from the actual
meta method formal (meta::gs('k.min') is NULL in the pinned package). The invented
tau threshold/metric blacklist and mixed-Egger/extrapolation ten-study gates are
removed. SMD defaults to Egger; diagnostic correction defaults to only0. Trim-and-fill
uses meta's automatic side and ma.common=TRUE.

New independent package comparisons pass in sse-policy-existing-tests.log (first
file), and the migrated small-study suite passes in sse-existing-migrated.log.
Native seven-study threshold and binary report/trimfill proof passed at
artifacts/verification/rcms/20261116T211947Z-12f2ea00-small-study-binary-extended.
Current native DTA small-study/import checks and GUI rerun are still in progress.

Remaining scientific obligations: restored MH/Peto sequential/subgroup numerical
execution, singleton/inference/subgroup-test policy leads, then the non-DTA audit
and complete stable-source qualification. No current changes are committed.

## Package authority follow-up

Opus confirmed that the singleton t/Knapp-Hartung rejection and blank cumulative
rows were RCMS policy. Singleton analysis paths now call the selected metafor
method; the obsolete get.res.for.one.* helpers and their callers/docs are removed.
The genuine leave-one-out minimum of two remains; standard/cumulative analyses
can start with one study. Package warnings are retained as visible report content.
Direct package comparisons cover singleton IV/random fits in all original families
and binary/diagnostic MH/Peto. The previously missing singleton P values are now
retained. Calculator diagnostic intervals also use the package fit.

Small-study Results now contain the primary summary rather than presenting it as
Warning in Supplementary details. Bias coefficients are identified as such. The
minimum-studies control separates Package default from an explicit count >=3;
unavailable methods are named even when another test is usable. Extrapolation of
ratio measures uses exp() for display. Classical Egger intercept intervals come
from metafor::regtest(model='lm'); Peters shows estimate/SE because meta supplies
no interval. No synthetic bias-coefficient intervals are added to meta output.
Trim-and-fill identifies its selected side. The independent authority matrix passed
103 cases in authorities-opus-v3.log. Full qualification is still pending.

Verification corrections retained with the failed transcripts: the fixed-workflow
observer initially assumed PLR/NLR result order instead of using metric labels;
accepted setup dialogs are already deleted by Qt; the previous authority script
explicitly forced Peto drop00=FALSE. These harness assumptions are now corrected.
A generic testthat::test_dir invocation lacked the package test environment;
testthat::test_local is the appropriate source check (r-test-local-first.log).
The first fast-suite runtime selected ambient R 4.6.1; the configured pinned-runtime
recovery passed all 47 tests in the affected modules. The complete rerun remains
in python-complete-opus.log. No frozen oracle has been regenerated.

Latest native small-study UI/one-study proof passed under
artifacts/verification/rcms/20261116T214555Z-5867ad64-small-study-binary-extended.
Its Results sidebar is visibly wider than the intended content-sized default;
repeated opening/restoration is being reviewed before the final UI sign-off.

## Final review follow-up (17 November)

The default Results sidebar now retains a content-sized width, and only an explicit
splitter drag writes proportions. Native repeated short/configuration/short opens
and a manual drag/reopen passed in
artifacts/verification/rcms/20261116T221727Z-365f1f9c-small-study-binary-extended.
The first two attempts are retained: one exposed application of saved proportions
before native maximization; the next asserted before native geometry settled.
The current driver captures the settled native frame before checking restoration.
The GUI Results-layout selection passed 66 tests (sidebar-layout-after.log).

Reports consume the actual metafor fit test. Singleton Knapp-Hartung requests now
report normal-approximation inference exactly once in Model configuration and omit
inapplicable Knapp-Hartung citations. The package retains its REML method field for
singleton random fits; the initial test assumption that it changes to FE was wrong
and is retained in fitted-inference-after.log. No numerical result was changed to
satisfy that assumption. Mixed-fit cumulative/subgroup output reports all fitted
test types. Generic RCMS standard-error-range advice is no longer called a warning;
real package warnings are retained. Headers distinguish eligible from included counts.
The unused one-arm metric auto-switch on project open has been removed.

Source inspection covered binary/continuous one/two-arm input and preview selection,
explicit entered effects, HR/IRR source/scale switching and validation, CSV/XLSX
mapping/year/count preview and transactional import. Partial raw data uses entered
values rather than fabricating complete counts; continuous raw-data setters clear
derived previews. Native calculator/data-creation/import matrix qualification is
still required before claiming these surfaces passed. Opus final review and the
full current-source R-stack/desktop run are pending. No audit changes committed.

## Opus final findings and corrections

Opus's final review accepted the header, sidebar restoration and diagnostic count
handling. The remaining report findings are corrected: Results HTML preserves
small-study summary line breaks (checked against copied QTextDocument lines), and
ordinary analyses list only the package(s) selected by their actual methods rather
than loadedNamespaces(). This prevents meta/mada citations leaking from earlier
analyses in the same R session. A standard singleton run after small-study effects
now explicitly proves only metafor is reported. Small-study execution still reports
both meta and metafor because both run there.

Pinned metafor 5.2-1 also accepts saturated fixed-effect regressions with t or
Knapp-Hartung. The remaining RCMS residual-df guard has been removed, with direct
package comparisons for the accepted fits. Random-effects impossibilities remain
package errors. Probe commands/results are retained in
artifacts/verification/dta-audit/regression-pinned-package-df-probe.log; the first
ambient-package probe is retained separately and is not pinned-runtime evidence.
The focused recovery passed in regression-df-after.log.

The initial complete Python selection passed 1104 tests with 3 skips; the final
rerun remains pending. The first full R check failed seven assertions: two tests
still expected obsolete singleton plot transport fields, one expected entered-only
Peto to silently become an inverse-variance fit, and four expected removed generic
standard-error advice to be warnings. The tests now check actual rma fields, Peto's
count requirement and the retained standard-error range as descriptive information.
No frozen statistical oracle was updated. The final native summary/citation/
clipboard/PDF/DOCX recovery passed in
artifacts/verification/rcms/20261116T222916Z-50a6ef70-small-study-binary-extended.

Earlier pending MH/Peto obligations are closed by native passed runs
20261116T215043Z-d6131dfb-analysis-diagnostic-cumulative,
20261116T215131Z-92cd9d86-analysis-diagnostic-leave-one-out, and
20261116T215603Z-ae0cf764-analysis-diagnostic-subgroup: the driver compares all
metric-labelled rows with direct pinned metafor fits on exactly the same subsets.
The independent authority matrix passed 103 cases before the final reporting-only
changes. Complete current-source qualification and release packaging remain pending.

## Native closure and final-source qualification

The final Python suite passed 1104 tests with 3 platform-specific skips in
python-opus-final.log. The full Windows Qt lane passed 336 core and 67 remaining
GUI tests, plus native shell/calculator/analysis/Results and 100%/150% remaining-
surface probes (native-qt-final.log). R CMD check is Status: OK with the current
ASCII-safe source; 103 authority cases, 21 deterministic Reitsma visual cases and
10 live bridge tests passed in the final full profile. The desktop and golden
stages remain running, so the overall full profile is not yet marked passed.

All eight dataset-creation paths passed natively, including single-arm proportion,
single-arm mean, entered regression coefficient, generic entered effect, two-arm
binary, MD, SMD and DTA. The three native calculator and CSV/XLSX/RevMan import
recovery drives passed too. Logs are final-native-analysis-data-*.log and
final-native-recovery-*.log; each records its unique manifest/evidence directory.
The original binary calculator failure was an invalid harness requirement that
all content remain simultaneously visible at a +6-point font despite the screen
height cap. The retained capture demonstrates normal vertical overflow; the driver
now proves both tables can be revealed by scrolling at the large font, while
requiring no scrolling at the ordinary font. No product sizing rule was relaxed.

## Compatibility migration evidence

Frozen oracle ZIPs, numeric-contract.json and tolerances remain unchanged. The
historical regression capture now explicitly selects DL; it previously inherited
the changed REML default, causing unrelated baseline drift. Pinning its historical
method restores every existing numeric field. The remaining differences are the
reviewed bibliography cleanup and one previously blank singleton cumulative P.
Exact before/after text bindings cover removal of the unused Hedges citation and
non-citation workflow descriptions. A separate exact missing-field binding accepts
only Carroll's new P=0.605; controls reject changed values, non-numbers and any
change to an existing estimate. Direct public metafor SMD reconstruction from
Carroll's counts (60,94,22 versus 60,92,20) gives P=0.6048, rounded to 0.605, retained
in singleton-golden-public-authority.log. Golden control tests pass 59 cases.

The first complete desktop run reported 20 passed/120 failed: three stale UI
assertions plus all later cases invalidated when the harness changed during the
run. This was a verification sequencing error, not 120 product defects. The
recovery was paused before further harness edits, including historical DL pinning
and scoped compatibility bindings. Stable-source final full qualification must
now run with no further executable changes. The native arm-naming recovery passed
20261116T225129Z-407389b2-audit-round3-arm-names.

## Final qualification repairs

The stable full profile at 20261117T000706Z-346ca848-complete passed
R CMD check (Status: OK), 103 public-package authority cases, 21 deterministic
Reitsma visual cases and 10 live bridge tests. Its desktop stage finished with
137 passes and three historical-fixture failures. Those were explicit-estimator
omissions in the report swap/subgroup/regression examples and the second panel
of a combined diagnostic legacy fixture; existing expected numbers and tolerances
were retained. The corrected three workflows passed in historical-fixtures-final.log.
The frozen release comparison passed all 11 cases and 476 comparisons in
golden-compatibility-final-reviewed/capture/compatibility-report.json.

A Peto plot failure found during qualification was repaired by retaining the
package's full-length yi.f/vi.f display arrays, including missing effects for
noncontributing studies, and excluding nonfinite values when calculating plot
ranges. Both binary and diagnostic MH/Peto report and forest heterogeneity df
now use the package's estimable-effect count, k.yi. The direct package comparison
failed eight assertions before this repair and passed afterward (peto-df-before.log
and peto-df-after.log). A native Windows Peto drive passed in
20261117T000923Z-028052e9-analysis-binary.fixed.peto. Peto's restored drop00 default
also changes heterogeneity P values and I²; the changelog explicitly records the
correction and asks users to rerun affected analyses. The stale IRR tooltip and
unused diagnostic Peto weight copies were removed or corrected.

The complete Python/GUI/packaging-contract/comparator selection passed 1108 tests
with three skips in python-pinned-final.log. The earlier packaging-policy failure
used ambient R 4.6.1; the retained configured recovery selects pinned R 4.6.2 and
passes. A final complete desktop run and the local release build remain pending.

## Qualification complete

The final unchanged-source desktop run passed all 140 workflows and its fresh
runtime doctor check: artifacts/verification/rcms/20261117T005744Z-9c5adba4-complete
(summary.json passed=true). The final Python/GUI/packaging-contract/comparator
selection passed 1108 tests with three skips in python-commit-qualification.log.
Strict win32 typing passed before GUI qualification. R CMD check, 103 statistical
authority cases, 21 deterministic Reitsma visual cases, 10 bridge tests and the
11-case/476-comparison frozen release check passed as recorded above. The earlier
failed full-profile command remains failed evidence; its recovered desktop stage
is the final complete run, rather than a claim that the original command passed.

The last fixture corrections preserve the historical estimator of each example:
DL for the swapped continuous and binary subgroup examples, REML for the existing
binary regression example, and DL in both panels of the combined diagnostic legacy
fixture. Frozen numerical files and tolerances were not changed. The final report
copy also avoids calling a single meta-regression moderator plural. No application
statistical result changed in these final fixture/copy corrections.

These are Windows source/runtime and native checks. They do not qualify macOS or
Linux release artifacts. The requested local Windows package is built separately
from the committed source and receives its own packaged and exact-archive checks.

## Packaged historical estimator correction

The first local archive build executed its runtime, sample, scale, locale,
save/reopen and normal-entry smoke operations successfully, but final evidence
validation rejected the normalized summary identity. The packaged fixture still
expected historical DL output while its atomic analysis operation inherited the
new REML default. Neither inspector hash nor any numerical oracle was changed.

The existing atomic analysis command now accepts an optional explicit estimator;
the developer smoke assembler requests DL for its four historical analysis
operations. Omitting that option retains the application's REML default. The
existing boundary test was extended before implementation and failed in
package-estimator-before.log. Strict win32 typing and all affected automation and
packaging-contract checks pass (153 passed, two skips). Real Qt/R source probes
passed for both requests: explicit DL restores the original frozen identity
16303526c7c3a40c8805b6245b8806fc765bf4efc2c269807c1a5d460060539d,
while the unconfigured path keeps REML output. Inputs, commands, observations and
results are retained under artifacts/verification/dta-audit/package-estimator-live.
This changes qualification configuration only; ordinary GUI analysis defaults
and statistical calculations are unchanged. The Windows archive is rebuilt from
the following committed correction and qualified again.
