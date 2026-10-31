# Statistical corrections

## Step 1 — Q among displayed subgroup estimates

The old moderator fit estimated a shared residual heterogeneity variance instead
of testing the displayed subgroup estimates with their displayed standard errors.
All subgroup estimators now use heterogeneity Q from an independent fixed-effect
fit of those summary estimates (inverse squared SE weights, groups minus one df,
chi-square p). The FE override and IV moderator convention are removed.

Authorized numerical changes, listed by the task before implementation:

| Fixture | Old Q | New Q | Independent authority |
| --- | ---: | ---: | --- |
| BCG RR, absolute latitude >=35, DL | 15.544 (display) | 14.903849407 | meta::metabin, Inverse, DL, subgroup, tau.common=FALSE |
| BCG RR, absolute latitude >=35, REML | 17.145 (display) | 18.001340175 | meta::metabin, Inverse, REML, subgroup, tau.common=FALSE |
| OR authority fixture, MH | 27.08745 | 29.23978 | meta::metabin, MH, common subgroup Q |
| OR authority fixture, Peto | 27.08745 | 26.63551 | meta::metabin, Peto, common subgroup Q |
| OR authority fixture, DL | shared-tau moderator Q | 10.85996 | meta::metabin, Inverse, DL, tau.common=FALSE |

MH difference from meta: 1.421085e-14; Peto: -1.776357e-14.
These fixtures have no zero cells; pooled/study results are unchanged.
The earlier Fleiss1993 fixed-IV correction 4.852384 -> 5.680480 remains
valid (p 0.027608 -> 0.017155); a fixed summary-estimate Q is algebraically
equivalent to the previous FE moderator test. No frozen oracle was regenerated.

Test-first evidence: the new independent meta subgroup comparisons failed on
MH before implementation (build/sheets-baseline/step1-before.log).
After implementation all 96 recorded authority cases plus the new DL/REML BCG
checks passed (step1-after.log and step1-authorities.json in the same directory).
RCMetaR was reinstalled into build/sheets-r-library; installation log and
source/installed SHA-256 provenance are step1-install.log and
step1-install-provenance.json.

Strict golden gate: 474 comparisons / 415 numerical fields, no numerical
drift. Two text_artifact_drift failures (amino-binary-subgroup and
continuous-subgroup) reflect the new Q label; the frozen oracle is unchanged.
Report: build/qt6-verification/golden-compatibility-step1/compatibility-report.json.
Targeted offscreen desktop plot-workflow-subgroup passed; evidence:
artifacts/verification/rcms/20261031T202614Z-2f8692ad-plot-workflow-subgroup.
This exercises the real Qt/R subgroup plot and exports, not native OS gestures.

## Remaining work

Zero-cell MH pooling and Methods truth are implemented below. Remaining:
binary sequential/regression authority expansion, desktop swap and calculator
confidence-level audits. Full final qualification and pushes remain pending.
The old continuous-only sequential/regression limitation still applies.

## Golden text authorization

amino-binary-subgroup: 0.187/0.666 -> 0.307/0.579, authority
meta::metabin(allstudies=TRUE), Q=0.3073583, p=0.5793058.
continuous-subgroup: 0.226/0.634 -> 0.293/0.589, authority metafor
escalc SMD with separate DL fits, Q=0.2926188, p=0.5885472.
The meta SMD variance convention explains its different Q. Qm label becomes Q.
numbers inside text sections are compared as whole strings, not among numerical fields.
Inline continuous authority passed: build/sheets-baseline/text-authorities.json.

## Zero-cell MH

Shared binary MH fitter now passes original counts with metafor defaults;
subgroup, leave-one-out and cumulative refits call that same fitter.
Test-first authority failure: text-authorities.log, zero MH OR b.
OR log estimate -0.246501 -> -0.2544752, CI [-0.7916301, 0.2826796];
RR corrected estimate -0.2219334, CI [-0.6929202, 0.2490533].
metafor::rma.mh defaults and meta::metabin(method="MH", MH.exact=TRUE)
agree on both estimates and intervals within 1e-6. No non-MH numerical edits.
Authority evidence: build/sheets-baseline/mh-authorities.json (97 cases).
Installed into build/sheets-r-library (mh-install.log).
Peto add=.5: -0.2459687 [-0.7727998, 0.2808624]; add=0:
-0.2541451 [-0.7896609, 0.2813707]. Correction reaches Peto pooling.

## Methods truth

Real result text assertions first failed on generic MH wording
(build/sheets-baseline/methods-before.log). MH now describes individual-only
correction; Peto explicitly describes correction to pooling. IV/DL reports
retained double-zero counts (amino 2; modified real project 3).
PDF/DOCX manuscript-export passed, including real MH/Peto Methods text:
artifacts/verification/rcms/20261031T203534Z-c37bfdd2-manuscript-export.
Source digests: build/sheets-baseline/mh-source-provenance.json.

## Final targeted qualification (this run)

Strict golden gate passed: 474 comparisons, 415 numerical fields; no numerical
field drift. Only the two authorized text Q/p pairs changed. Qm -> Q also
shortens table padding by one space. Archive SHA bindings in both contracts and
the outer manifest were updated; numerical/plot expectations were not changed.
Report: build/qt6-verification/golden-compatibility-stat-fixes/compatibility-report.json.
Amino passed: artifacts/verification/rcms/20261031T203917Z-2fad9760-amino.
Plot subgroup passed:
artifacts/verification/rcms/20261031T203948Z-05646eaa-plot-workflow-subgroup.
Manuscript-export passed at the path recorded above. All desktop runs used
Qt offscreen with real R, serially. No full matrix or push was performed.

Exact shell setup for all commands: `source build/sheets-baseline/ENV.sh`.
Commands (logs under build/sheets-baseline):
- `uv run --no-sync python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-compatibility-stat-fixes`
- `"$R_HOME/bin/Rscript" .agents/skills/verify-rcms/scripts/analysis_authorities.R build/sheets-baseline/mh-authorities.json`
- `uv run --no-sync python scripts/verify_rcms.py amino`
- `uv run --no-sync python scripts/verify_rcms.py manuscript-export`
- `uv run --no-sync python scripts/verify_rcms.py plot-workflow-subgroup`

Additional exact probe: `"$R_HOME/bin/Rscript" build/sheets-baseline/peto-probe.R build/sheets-baseline/peto-probe.json`;
retained inline inputs, command and output in peto-probe.R / peto-probe.log.
RCMS Peto is exactly the add=.5 result quoted above. Old corrected-count MH RR
was -0.2149007 -> -0.2219334 (same metafor/meta authority). These MH probe
values are not frozen golden fields. Installed/source digests are both retained
in mh-source-provenance.json. Full matrix qualification remains for the later run.

## Peto raw-count pooling (2026-11-01)

Test first: `peto-before.log` fails `zero Peto raw pooling b`; after the fix,
`peto-after.log` / `peto-after.json` pass 98 authority cases. Commands use
`source build/sheets-baseline/ENV.sh` then `$R_HOME/bin/Rscript` with
`.agents/skills/verify-rcms/scripts/analysis_authorities.R` and the JSON path.
All named logs here are under build/sheets-baseline.

Metafor's first add/to position controls individual estimates, second controls
pooling (peto-semantics.log). `drop00=FALSE` retains k=5; scalar TRUE drops
double-zero individual estimates but does not request pooled removal (scalar
is expanded to c(TRUE,FALSE)). The shared Peto fitter now uses add=c(.5,0),
to=c("only0","none"); subgroup, cumulative and leave-one-out call it. The
single-study shortcut was removed so refits also use Peto O-E/V.

Probe estimate -0.2459687 -> -0.2541451; CI
[-0.7727998,0.2808624] -> [-0.7896609,0.2813707]. Raw metafor,
meta::metabin(method="Peto",allstudies=TRUE), and independent one-line
O-E/V calculation agree on -0.2541451. Both package intervals agree.
These are probe values, not regenerated frozen expectations. Methods now says
individual study estimates only; pooled Peto uses original counts, asserted
by the manuscript desktop scenario. RCMetaR reinstalled into
build/sheets-r-library (peto-install.log, peto-provenance.json).
Strict golden gate and remaining requested steps are pending.

## Binary sequential and regression authorities

Added direct metafor FE/DL comparisons for binary cumulative, leave-one-out
and continuous-moderator regression: estimates, SE, interval bounds and p-values;
regression also compares QM/QMp and tau-squared. Failure modes were written
before implementation. First targeted run failed on the first cumulative
p-value: the single-study helper omitted it. It now returns the two-sided
normal-test p-value. Targeted checks pass (binary-targeted.log before,
binary-targeted-after.log after); binary-targeted.R retains the exact inputs.
Reinstalled RCMetaR (binary-install.log). Full authority and golden reruns pending.
The Peto-only strict golden gate passed 474 comparisons / 415 numerical fields
with zero frozen drift: golden-compatibility-peto/compatibility-report.json
under build/qt6-verification.

## Stop: unauthorized frozen output change

Full expanded authority script passed 100 cases (binary-final.log/json).
The subsequent strict gate failed: amino-binary-cumulative Gonzalez now
produces a p-value where the frozen result had none, plus cumulative text
drift. This is outside the authorized Peto zero-cell changes. Stopped without
changing any frozen oracle, as instructed. Report:
build/qt6-verification/golden-compatibility-binary-final/compatibility-report.json.
Step 2's p-value fix is committed but cannot be qualified under current
authorization. Desktop swap and ratio-confidence assertions are prepared in
the dirty worktree but unrun/uncommitted. sheets-swap, calculator-ratio-precision,
Manuscript-export and amino remain unrun in this session. No push or full matrix.

## Authorized single-study cumulative p (2026-11-01)

Only affected frozen row: amino-binary-cumulative, Gonzalez (k=1),
model.gonzalez.p_value absent -> 0.365, and the identical text cell.
Authority: explicit user authorization; metafor::escalc OR with counts
6/27 versus 9/27, rma.uni FE Wald test. Exact probe and output:
build/sheets-baseline/cumulative-authorized.R / cumulative-authorized.json.
Other cumulative frozen rows already contain p-values. No other frozen
numerical value changed; archive identity bindings updated narrowly.

## Swap audit

Prepared desktop assertions now load the actual saved plot parameters before
comparing with metafor. OR/RD/MD use original arm counts and direct DL fits,
with tolerance 1e-6 for estimate, both CI bounds and p; Favours follows arms.
Observed before -> swapped (calculation scale): OR -0.261906186 ->
0.261906186, CI [-0.724082087,0.200269715] -> [-0.200269715,0.724082087],
p=0.266708759; RD -0.027142975 -> 0.027142975,
CI [-0.060347200,0.006061251] -> [-0.006061251,0.060347200], p=0.109115104;
MD 7.617160385 -> -7.617160385, CI [3.823294965,11.411025806] ->
[-11.411025806,-3.823294965], p=0.0000831510923. No product defect found.
Failed evidence retained: 20261031T205334Z-9a3da145-sheets-swap (unloaded
params); d6d071dc retry briefly overlapped the corrected run due to an
unfinished-session misread. Neither is claimed as serial final qualification.

## Entered interval confidence audit

The simpler correct design already exists: RatioInput.confidence persists the
original interval level independently of the sheet/output level. No new product
mechanism or blocking dialog is needed. Added desktop assertions accept at 90%,
undo/redo/save/reopen, compare SE with metafor::conv.wald and the explicit
(logU-logL)/(2*qnorm(.95)) formula, compare DL weights at 1e-6, then switch to
95% and require unchanged source bounds, source level and input SE.
For bounds [1.2345678901234567e-8,1e12], source SE is
13.934668740867144 before and after switching; source bounds remain intact.
HR first-study weight is 0.0006822304378178452 percent after switching.

CI desktop scenario passed:
artifacts/verification/rcms/20261031T205616Z-ec3f69bc-calculator-ratio-precision.
The archive's internal manifest also duplicates the cumulative text; initial
strict startup caught the missed duplicate. Corrected the same authorized
Gonzalez p cell there and refreshed bindings, without additional number edits.
Numeric coverage ledger and its count assertion now include the authorized
new field (415 -> 416 fields). Startup ledger mismatch was caught before any
analysis; fixed ledger only, without broadening expected results.

## Final qualification for swap/CI run

Strict golden gate passed, 416 numeric fields (one authorized addition), no
other frozen drift: build/qt6-verification/golden-compatibility-swap-ci/compatibility-report.json.
Authority script passed 100 cases: build/sheets-baseline/swap-ci-authorities.json
and swap-ci-authorities.log. IRR source SE also remains 13.934668740867144;
its first-study weight is 0.029531164162110338 percent, matching metafor.
Commands all source build/sheets-baseline/ENV.sh; Python uses uv run --no-sync:
- python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-compatibility-swap-ci
- "$R_HOME/bin/Rscript" .agents/skills/verify-rcms/scripts/analysis_authorities.R build/sheets-baseline/swap-ci-authorities.json
- python scripts/verify_rcms.py sheets-swap
- python scripts/verify_rcms.py calculator-ratio-precision
- python scripts/verify_rcms.py amino
No uv sync, full matrix or push. Qt offscreen with real R; native gestures and
full qualification remain outside this run's scope.

Final serial desktop receipts, all manifest passed=true / exit_code=0:
- artifacts/verification/rcms/20261031T210049Z-a68be04c-sheets-swap
- artifacts/verification/rcms/20261031T210242Z-1689e68e-amino
- artifacts/verification/rcms/20261031T205616Z-ec3f69bc-calculator-ratio-precision
Strict gate: 475 comparisons / 416 numeric fields. All requested targeted
checks complete. Earlier overlapping attempts are excluded from these receipts.

## Entered OR/MD source intervals retain their confidence

The entered-effect store reconstructed SE using the current sheet multiplier,
so changing output confidence from 90% to 95% silently narrowed input SE.
The real entered-binary drive reproduced OR 2 [1, 4]: SE 0.353653019151067
instead of 0.421403563941800. Bounds now retain their source multiplier in
analysis_unit.py, shared by binary/continuous and RM5 generic OR/MD inputs.
Existing entries without source metadata retain their prior interpretation;
95%-only entries use the same 95% conversion. No oracle was regenerated.
The entered-binary/continuous calculator scenarios additionally enter symmetric
OR/MD intervals at 90%, switch output to 95%, save/reopen, and compare the
actual R analysis study SE against metafor::conv.wald and qnorm(.95) at 1e-6.
MD 2 [1, 3] requires SE 0.607956831911769.
Targeted transcripts: build/sheets-baseline/entered-ci-{red,binary,md}.log.
Qualification: build/sheets-baseline/entered-ci-qualification.log; individual
strict gate, authority and E2E logs share the entered-ci prefix.

Entered-CI qualification completed on a4ef07fe in one uninterrupted serial shell:
strict golden passed (475 comparisons, 416 numeric fields); authority passed
100 cases; desktop E2E finished 131 passed / 3 failed in 3043.16 seconds.
Failures: analysis-sequential-fixed-{cumulative,leave-one-out,subgroup}.
Their public reference helper sequential_workflows.py passes add=c(.5,.5)
to rma.mh, retaining pooling correction despite the earlier original-count MH
fix documented above. Observed vs reference OR: cumulative through Giamarellou
0.369027 vs 0.382841267237438; overall leave-one-out 0.711969 vs
0.720292710361172; subgroup A 0.716852 vs 0.722098995928783.
These comparisons remain unchanged and unresolved; no oracle regenerated.
No pushes performed because qualification failed.
Failure evidence: artifacts/verification/rcms/20261031T214010Z-94837a3f-analysis-sequential-fixed-cumulative,
20261031T214022Z-b00a7ac8-analysis-sequential-fixed-leave-one-out,
20261031T214035Z-7ab5b416-analysis-sequential-fixed-subgroup.
