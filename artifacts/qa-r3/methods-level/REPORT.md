# Area E — first chunk, partial

## Checklist log

1. Opened amino.rcms after R startup completed. Opened Analysis > Meta-analysis. Captured [collapsed](shots/05-dialog.png) and [expanded](shots/06-advanced.png) dialog. Default is binary random effects, DerSimonian-Laird, 95%, normal approximation. Hovered analysis method; tooltip repeats “Binary Random-Effects” ([capture](shots/07-tooltip.png)). Clicked Run analysis; [capture](shots/08-result.png) shows a small blank window while the result was opening. Results and remaining two tooltips not checked.
2. Not exercised.
3. Not exercised.

## Findings

No confirmed findings. Statistical agreement, fine polish at ×2, and known-issue comparison remain unverified.

## Strengths

Advanced settings are grouped under a disclosure control; the default confidence level is visible.

## Score

Not scored: insufficient coverage.

## Step 1 continuation — default results comparison

Restarted, waited for R, reopened amino.rcms and ran the default analysis. Hovered the [analysis method](shots/12-tooltip-method.png), [heterogeneity estimator](shots/13-tooltip-estimator.png), and [inference method](shots/14-tooltip-inference.png): each tooltip repeats its selected value. The results window opened behind the data window; Alt+Escape brought it forward.

| View | Pooled OR | 95% CI | Overall-effect p |
|---|---:|---|---:|
| [Manuscript](shots/19-manuscript.png) | 0.77 | 0.48–1.22 | .267 |
| [Text report](shots/20-text.png) | 0.77 | 0.48–1.22 | .267 |
| [Tables](shots/21-tables.png) | 0.77 | 0.48–1.22 | .267 |
| [Forest plot](shots/22-forest.png) | 0.77 | 0.48–1.22 | 0.267 |

The pooled values agree at displayed precision; p differs only in leading-zero formatting. Forest plot shows the null line at 1. The text report rounds Giamarellou's lower CI to 0.00 while the forest displays 0.0040; this is a display precision difference for an individual study, not a pooled-value disagreement.

## Step 2 — fixed effects

| Method | Pooled OR | 95% CI | Header | Null line | Footer |
|---|---:|---|---|---|---|
| Mantel–Haenszel | 0.71 | 0.54–0.93 | M–H, Fixed | 1 | Overall effect Z = -2.46, P = 0.014; H₀ absent ([plot and footer](shots/29-mh-footer.png)) |
| Peto | 0.71 | 0.54–0.93 | Peto, Fixed | 1 | Overall effect Z = -2.48, P = 0.013; H₀ absent ([header](shots/34-peto-forest.png), [footer](shots/35-peto-footer.png)) |
| Inverse variance | 0.76 | 0.57–1.01 | IV, Fixed | 1 | Overall effect Z = -1.89, P = 0.059; H₀ absent ([header](shots/39-iv-forest.png), [footer](shots/40-iv-footer.png)) |

All three headers identify the selected method, all null lines are at 1, and none of the footer test lines states H₀ = 0. The first method was selected in the initial analysis dialog after restarting; subsequent methods used Change settings.

## Step 3 — random effects and edge cases

REML, normal inference: OR 0.77 (95% CI 0.48–1.23), τ² = 0.40, p = 0.268 ([forest](shots/46-reml-footer.png)). DL previously displayed OR 0.77 (0.48–1.22), τ² = 0.38. OR is unchanged at two decimals, CI and τ² differ.

Paule–Mandel, normal inference: OR 0.77 (95% CI 0.48–1.22), τ² = 0.39 ([forest](shots/49-pm.png)). The OR and CI match DL at displayed precision, while τ² differs by 0.01.

Knapp–Hartung with Paule–Mandel: OR 0.77 (95% CI 0.47–1.27), t = -1.11, p = .282; interval widened from 0.48–1.22. [Forest](shots/51-kh.png) and [manuscript](shots/52-kh-manuscript.png) label t but do not identify degrees of freedom for the t test; the displayed df = 18 is explicitly associated with heterogeneity Q.

90%: forest header, manuscript Results and tables, and text report say 90%; pooled OR 0.77 (0.51–1.16). **Disagreement:** manuscript Methods still says “Confidence intervals (95%) used Knapp-Hartung.” See [manuscript](shots/55-90-manuscript.png), [text](shots/56-90-text.png), [plot](shots/54-90-forest.png).

99%: forest header, manuscript Results and tables, and text report say 99%; pooled OR 0.77 (0.39–1.52). Methods instead says “Confidence intervals (90%) used Knapp-Hartung,” the previous run's level ([manuscript](shots/58-99-manuscript.png), [text](shots/59-99-text.png), [plot](shots/57-99-forest.png)).

### Finding: stale confidence level in Methods

**Major, statistical trust/consistency.** From app start open amino.rcms, run a random-effects analysis, use Change settings to change confidence from 95% to 90%, then inspect Manuscript. Expected Methods to state 90%; actual says 95%, while Results and plot say 90%. Changing 90% to 99% yields Methods 90%. Smallest fix: generate the Methods sentence from the current analysis result's confidence level. Evidence: [90%](shots/55-90-manuscript.png), [99%](shots/58-99-manuscript.png).

### Finding: t-test degrees of freedom not identified

**Minor, statistical trust.** Run amino random effects with Paule–Mandel and Knapp–Hartung. Expected the overall-effect t test to report its degrees of freedom; [manuscript](shots/52-kh-manuscript.png) and [plot](shots/51-kh.png) show t and p without its df. The df displayed belongs to heterogeneity Q. Smallest fix: include the t-test df alongside t.

One included study: unchecked all but Gonzalez ([grid](shots/61-one-study.png)); Analysis > Meta-analysis is disabled, so a run is prevented ([menu](shots/62-one-dialog.png)). No explanatory reason is visible in the menu.

Continuous zero-SD attempt: opened continuous.rcms, which is configured for standardized mean difference, not MD ([dialog](shots/67-continuous-dialog.png)). Entering 0 for Carroll's intervention SD was rejected with “Standard Deviation cannot be zero or negative” and the previous 22 restored ([warning](shots/65-zero-sd.png)). Consequently an MD run with zero SD was not exercised. No sample was saved.

### Area score: 6/10 (provisional)

Core pooled results and method labels were consistent in the exercised paths, but the manuscript Methods reports the previous confidence level after a change, a publication-facing statistical trust defect. The t-test df is not identified. The zero-SD MD case and broader Area E coverage remain unverified, so this is a provisional score.

## Implementation proof — 2026-11-05

Branch fix/qa-r3-methods-level, based on origin/master ffa8c4aa.
Methods used the dialog's original confidence level, unlike results identity which already prefers applied conf.level. Fixed that argument. Estimator/inference/correction already use current_param_vals via _applied_parameters; model uses the current method widget. No stale source found in those fields.

Strict repository typing: PASS, win32 target; exact command/transcript in typing.log.
Targeted real Qt/R: PASS, command source /home/ali/.t3/qa-env/ENV.sh; export PYTHONPATH=$PWD/src:$PWD; prepend $PWD/build/rcmetar-lib to RCMS_R_LIBS/R_LIBS/R_LIBS_USER; python scripts/verify_rcms.py review-workflows.
Evidence: artifacts/verification/rcms/20261105T021428Z-d39bc1ed-review-workflows (manifest, runtime, steps, inputs, screenshots). Assertions verify successive 90%/99% Change settings reruns and KH df = saved res$dfs = k-1 = 18 in Methods, results and forest SVG.

Native light/default: ui.py session methods-e; amino → meta-analysis → Change settings 90%, KH → rerun. After closing the original result, [Methods](shots/13-methods90.png) says 90% and 18 degrees of freedom; [forest](shots/14-forest90.png) shows t (df = 18). Initial screenshot 12 showed the original 95% result window, not the new rerun. Both windows had the same title; it is not a failed rerun.
Numerical proof: numbers.R/numbers.log compare master and changed summary producers on nine saved real-app fits with R identical(): full serialized fitted objects unchanged, all summary values identical except added df column. No numerical references/tolerances regenerated.
Full pre-push/authority/golden/package matrix deferred to CI per task instruction. This is source-app Linux evidence, not release qualification.
Native dark/+6pt: session methods-e-dark, fresh amino run with 90% KH. [Methods/results](shots/20-dark-methods.png) show 90%, t(df=18), readable wrapped text. This dark pass tests initial settings, not Change settings (that trigger is covered by light native and automated reruns). Both owned native sessions stopped. Before evidence remains in original screenshots 51/52/54/55/57/58; no new before dark run was performed.
