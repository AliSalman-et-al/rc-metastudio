# Sample coverage

## Input shapes in the desktop wizard

The inventory follows `DatasetKind` in [main_wizard.py](../src/rc_metastudio/main_wizard.py), the [analysis catalog](../src/rc_metastudio/analysis/catalog.py) and the [grid columns](../src/rc_metastudio/workspace/columns.py). Reported input and calculator modes are also covered by the [calculator](../.agents/skills/verify-rcms/features/calculators.md) and [ratio](../.agents/skills/verify-rcms/features/ratios.md) maps.

| Wizard choice and subtype | Supported inputs and measures | Sample |
| --- | --- | --- |
| Two-arm binary (`proportions`) | Events and totals by arm, or an entered effect with uncertainty for compatible methods. OR, RD, RR, arcsine difference (AS), Yule's Q (YUQ), Yule's Y (YUY). | Colditz, Barza |
| Single-arm proportion (`proportion`) | Events and total for one cohort. Untransformed (PR), log (PLN), logit (PLO), arcsine (PAS), Freeman–Tukey (PFT). PFT needs the study denominator for inverse transformation. | Feng |
| Two-arm means (`means`) | Two sets of N, mean and SD, or an entered effect with uncertainty. MD default, SMD available. | Poole |
| Standardized mean difference (`smd`) | Same arm summaries and entered-effect route. SMD default, MD available. | Poole, select SMD on the sheet and verify the SMD-first wizard with these same rows |
| Single-arm mean (`mean`) | One N, mean and SD. The calculator can also use a mean's SE with N. RCMS calls the measure `Mean`, metafor calls the raw mean `MN`. | Abe |
| Regression coefficient (`reg_coef`) | A published coefficient and its confidence bounds. The two one-arm entered subtypes use the internal `Mean` metric and inverse variance. | Greenland, coefficient-and-CI sheet |
| Entered effect (`generic_effect`) | A reported estimate and SE on the calculation scale. | Greenland, estimate-and-SE sheet |
| Diagnostic accuracy (`diagnostic`) | TP, FN, FP and TN. Sensitivity, specificity, positive and negative likelihood ratios (PLR/NLR), diagnostic odds ratio (DOR). Compatible single-metric fits can use an entered estimate with uncertainty. Joint sensitivity/specificity requires counts. | Kearon |
| Hazard ratio (`hazard_ratio`) | Reported HR and its CI, or log HR with CI or SE, including source confidence level when supplied. No arm-count-to-HR calculator. | Pignon |
| Incidence rate ratio (`incidence_rate_ratio`) | Events and person-time per arm, or reported IRR with CI, or log IRR with CI/SE. Compatible inverse-variance fits can mix raw and reported rows. | Niel-Weise |

Pre/post correlation is an input to the two-arm continuous calculator. The wizard has no dedicated correlation, single-arm rate, or incidence rate difference measure. A previously calculated correlation on a suitable scale with its SE can use Entered effect, with the scale explicitly named. `OTHER` is an internal enum. Multiple outcomes are separate sheets and are analyzed separately.

## Analysis and calculator inventory

Scope follows the Analysis actions in [main_window.py](../src/rc_metastudio/main_window.py), the backend dispatch in [RCMetaR](../r/RCMetaR/R/rcmetar-core.R) and the verification maps for [analysis](../.agents/skills/verify-rcms/features/analysis.md), [small-study effects](../.agents/skills/verify-rcms/features/small-study-effects.md), [ratios](../.agents/skills/verify-rcms/features/ratios.md) and [results](../.agents/skills/verify-rcms/features/plots.md).

| Function | What to demonstrate |
| --- | --- |
| Pooled inverse variance | Fixed and random effects for each compatible shape. Exercise the random-effects τ² choices HE, DL, HS, HSk, SJ, ML, REML, EB, PM and PMM, and the available z, t, Knapp–Hartung and modified Knapp–Hartung inference strategies on an eligible fit. Read included/contributing counts, weights, heterogeneity, confidence and prediction intervals where available. |
| Count-based estimators | Binary Mantel–Haenszel for OR/RR/RD and Peto for OR. Diagnostic Mantel–Haenszel for DOR/PLR/NLR and single-metric Peto for DOR. Event-rate Mantel–Haenszel for raw IRR. Demonstrate continuity correction and double-zero exclusion where applicable, with study rows retained and contribution counts read from the fit. |
| Sequential and subgroup analysis | Cumulative in chronological or table order as supported, leave-one-out and categorical subgroup. Compare individual steps, omissions, subgroups and the overall estimate. Diagnostic sequential and subgroup analyses use univariate fits. |
| Meta-regression | Numeric, factor with reference category, and multiple moderators on the same source data. Exercise fixed/mixed univariate fits and joint Reitsma moderator fits. Match coefficients and intervals and check the regression plot exposed by each fit. |
| Small-study effects | Ordinary and contour funnels, classical Egger and Begg, mixed-effects Egger, raw OR Harbord/Rücker/Peters, raw SMD Pustejovsky–Rodgers, precision-limit extrapolation and trim-and-fill with automatic, left and right directions. Demonstrate eligibility and explanatory states. Most tests default to at least 10 studies via `meta`; mixed-effects Egger and extrapolation have separate precision and fit requirements. |
| Trial Sequential Analysis | RR/OR/RD, including MH where eligible, Peto OR, MD and reported HR. Exercise binary and continuous information axes, calculated and prespecified required information size, publication-year and table ordering, monitoring and futility, O'Brien–Fleming/Pocock, diversity/I² and no adjustment, binary penalized Z curve, and design sensitivity. Use explicit design assumptions in the exercise. [TSA guide](../docs/trial-sequential-analysis.md) |
| Diagnostic accuracy | Univariate and combined selections, sensitivity/specificity paired output, Reitsma REML and ML with SROC, Deeks with complete counts and varied effective sample size, diagnostic regression and its coefficient plots. The diagnostic small-study route is Deeks. It has its own funnel and skips ordinary/contour, trim-and-fill and extrapolation. |
| Study calculators | Binary counts and partial-count completion, one-arm proportions, continuous N/mean/SD/SE and MD/SMD (including offered variance and standardization choices), one-arm mean, diagnostic counts and Sens/Spec, and HR/IRR source formats. Exercise entered-estimate precedence and analyze the accepted inputs. |
| Reconstruction | In an editable copy, mask a known binary cell and use its effect, CI and study totals to reconstruct candidate counts. Mask a continuous arm value and use its known MD and CI to reconstruct the missing summary. Mask a diagnostic table and use original N, prevalence and sensitivity/specificity inputs to recover an eligible table. Validate any ambiguous choices against the retained source row. The pre/post mode needs genuine pre/post summaries plus a compatible paired correlation. |
| Results | Use the same runs for forest, study/fit data tables, text and manuscript reports, sequential/subgroup tables, regression and specialized plots. Exercise plot editing, export, exact numerical tables and Change settings on the owning workflow. |

This is coverage of each desktop function and estimator family. Eligibility applies per sheet, metric and model. Bootstrap and permutation appear in the backend verification map as package or programmatic paths, outside the desktop menu. Network, multilevel, multivariate outcomes other than paired diagnostic accuracy, and single-arm GLMMs from external packages are outside this desktop inventory.

## Coverage matrix

Cells describe what users can exercise with each [bundled sample](README.md). Empty entries leave a workflow to the other projects. Source-backed calculator exercises can involve removing an input or entering a source-derived CI in a saved copy.

| Sample | Pooled methods | Cumulative and leave-one-out | Subgroup | Numeric, factor and multiple moderators | Small-study effects | TSA | Diagnostic and input exercises |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Colditz | IV for all six two-arm measures, with the main-effect estimator and inference sweep on OR | Binary in publication order, compare steps and omissions | Allocation method | Latitude, allocation and latitude + allocation, with a change of reference level | OR Harbord/Rücker/Peters and the RR/RD route | RR, OR, RD and Peto OR with monitoring, design and sensitivity | Binary OR/CI, raw counts, partial counts and count back-calculation |
| Barza | MH OR/RR/RD and Peto OR with two clinical-failure double zeros and one nephrotoxicity double zero. Compare `k.yi`, weights and forest rows. | MH cumulative with a double-zero step, Peto leave-one-out |  |  |  | MH RR with a double-zero row. Test futility with explicit assumptions. | Switch two published outcomes and check real arm direction and both continuity-correction policies |
| Poole | MD and SMD fixed/random on 17 | MD cumulative and SMD leave-one-out | Published trial duration | Year, duration and year + duration under fixed and mixed effects | MD ordinary/contour, classical Egger, Begg, mixed-effects Egger, trim-and-fill sides and limit extrapolation where eligible, plus raw SMD Pustejovsky–Rodgers | MD with target in exacerbations/month and calculated and manual RIS. Observe SMD eligibility. | Arm summaries, MD/SMD settings, entered CI and missing-summary reconstruction |
| Kearon | Sens/Spec/PLR/NLR/DOR IV fixed/random, MH DOR/PLR/NLR, single DOR Peto, joint Reitsma, combined metrics | Univariate DOR cumulative and leave-one-out | Symptomatic vs asymptomatic patients | Year, patient group and both together | Deeks on the 11 retained asymptomatic tables |  | Reitsma SROC, paired output, joint coefficient plots, raw counts and entered Sens/Spec with diagnostic reconstruction |
| Niel-Weise | IRR IV fixed/random and raw MH | IRR cumulative and leave-one-out with direct IV/MH comparisons |  |  | Ordinary/contour funnels, default nine-study eligibility, then an explicit minimum where supported |  | Raw events and positive catheter-days, reported IRR/log IRR and mixed sources in a copy, raw-only MH eligibility |
| Greenland | Fixed/random for both coefficient/CI and estimate/SE, with the same results |  |  |  |  |  | Generic estimate/SE and coefficient/CI imports, same adjusted log scale |
| Abe | Raw mean IV fixed/random |  |  |  |  |  | One-arm mean calculator, direct `metafor::rma(measure="MN", mi=mean, sdi=sd, ni=n, method="REML")` from retained rows |
| Feng | PR, PLN, PLO, PAS and PFT under eligible fixed/random IV fits |  |  |  | Proportion Egger/Begg route with transformation caveat |  | One-arm count calculator, back-transform including PFT |
| Pignon | HR IV fixed/random | HR cumulative in table order and leave-one-out | Chemotherapy timing |  | HR funnel and supported Egger/Begg | Reported HR, missing-year recovery and table order | Reported ratio/CI and log ratio/SE using original O−E and V |
