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

Steps 2–5 have not been implemented: zero-cell MH pooling, Methods truth,
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
