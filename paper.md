---
title: 'RC MetaStudio: open-source software for advanced meta-analysis'
tags:
  - meta-analysis
  - evidence synthesis
  - systematic review
  - trial sequential analysis
  - Python
  - R
authors:
  - name: Ali Salman
    orcid: 0009-0001-1102-226X
    corresponding: true
    affiliation: 1
  - name: Kaneez Fatima
    affiliation: 2
  - name: Muhammad Shahzeb Khan
    affiliation: 2
  - name: Tariq Jamal Siddiqi
    affiliation: 3
  - name: Muhammad Shariq Usman
    affiliation: 4
affiliations:
  - name: Dow University of Health Sciences, Karachi, Pakistan
    index: 1
  - name: Baylor Scott & White Research Institute, Dallas, TX, United States
    index: 2
  - name: Baylor University Medical Center, Dallas, TX, United States
    index: 3
  - name: UT Southwestern Medical Center, Dallas, TX, United States
    index: 4
date: 23 November 2026
bibliography: docs/paper.bib
---
# Summary

Meta-analysis combines quantitative results across independent primary studies
to estimate an overall effect and analyze variation among study outcomes
[@gurevitch2018]. Systematic reviews with meta-analysis sit at the top of
traditional evidence hierarchies [@murad2016] and inform guidelines and policy
[@gurevitch2018]. Yet graphical meta-analysis software remains fragmented,
leaving reviewers to switch between separate tools or write R code. RC
MetaStudio is a free, open-source desktop program (GNU GPL v3) for Windows,
macOS, and Linux that brings basic and advanced meta-analysis methods into a
dedicated workspace. Reviewers run these analyses without coding, rely on
established R packages for results they can trust, and export publication-ready
figures, numeric tables, and draft reports.

# Statement of need

Meta-analyses across research fields span distinct data types, each with its
own statistical models. Studies report binary counts, continuous means,
time-to-event outcomes, event rates, or diagnostic sensitivity and specificity.
Beyond pooling, reviewers run subgroup comparisons, meta-regression,
leave-one-out influence checks, small-study effect assessments, or trial
sequential analysis (TSA), which adjusts significance thresholds for repeated
cumulative testing.

Graphical tools split these methods across separate programs and add-on
modules. In R, packages such as `metafor` [@viechtbauer2010] and `meta`
[@balduzzi2019] offer broad method coverage, but using them means writing and
checking scripts for every analysis. That scripting requirement deters many
reviewers [@wallace2012] and adds work even for those who code.

Cochrane's Review Manager (RevMan) was the most commonly reported software in
biomedical and health-science meta-analyses published in 2021 and 2023
[@forero2026], and it ranked third, behind R and Stata, across 1,000
meta-analyses in ten disciplines [@wu2026]. Yet Cochrane ended downloads of its
free desktop application, RevMan 5, on 25 April 2023 [@cochrane2022digest;
@wu2026]. Its browser-based successor, RevMan Web, requires a paid subscription
for most authors outside Cochrane Reviews [@cochrane2023revmanweb;
@cochranekb]. As of 23 November 2026, Cochrane lists a standard individual
subscription at £130 per year (£100 academic, £80 student)
[@cochranerevmanpricing]. That recurring cost is a barrier for reviewers with
limited funding.

RC MetaStudio removes both the scripting and subscription barriers. One desktop
program covers the data types, statistical models, and follow-up analyses
above, and reviewers can import existing RevMan 5 (`.rm5`) files directly.

# State of the field

Graphical meta-analysis tools fall into four groups: specialized review suites,
general statistics programs, commercial software, and focused tools (Table
\ref{tbl:comparison}). RevMan Web supports writing Cochrane reviews
[@cochrane2023revmanweb], figures [@revmanfigure], and linked reporting
[@revmanreport]. Yet it lacks methods that Cochrane's own handbook describes
and recommends, including meta-regression [@deeks2024ch10] and funnel-asymmetry
tests [@page2024ch13], and it does not fit bivariate or other hierarchical
diagnostic models [@revmandta].

General statistics programs supply meta-analysis through add-on modules. JASP
covers pairwise and meta-regression analyses but omits bivariate diagnostic and
sequential models [@bartos2026; @jaspcoverage]. In contrast, jamovi splits
pairwise, meta-regression, and diagnostic methods across separate modules
(MetaJam, MAJOR, and OncoPath) and lacks sequential analysis [@jamovimodules].
Commercial software requires paid licenses and leaves method gaps:
Comprehensive Meta-Analysis (CMA) [@cma] is Windows-only and omits bivariate
diagnostic and sequential models, while Stata [@stata] lacks built-in support
for both. Focused tools each cover part of the workflow. MetaDTA [@freeman2019]
and Meta-DiSc 2.0 [@plana2022] target diagnostic accuracy, and the Copenhagen
Trial Unit (CTU) TSA program [@thorlund2017] pairs pooling with sequential
testing. MetaXL [@metaxl] pools pairwise data and exports a dataset to Stata
for regression, while Meta-Mar [@metamar] covers pairwise analyses and
meta-regression.

| Software | Free | Open source | Installable app | Pairwise | Meta-reg. | Biv. DTA | TSA |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| RC MetaStudio | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| RevMan Web [@cochrane2023revmanweb; @cochranekb] | subscription | ✗ | ✗ | ✓ | ✗ | plots only | ✗ |
| JASP [@bartos2026; @jaspcoverage] | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| jamovi [@jamovimodules] | ✓ (core) | ✓ | ✓ (core) | ✓ (MetaJam, MAJOR) | ✓ (MetaJam) | ✓ (OncoPath) | ✗ |
| CMA v4 [@cma] | ✗ | ✗ | Windows only | ✓ | ✓ | ✗ | ✗ |
| Stata 19 [@stata] | ✗ | ✗ | ✓ | ✓ | ✓ | user-written only | user-written only |
| MetaXL 5.3 [@metaxl] | ✓ | ✗ | Excel add-in | ✓ | Stata export | ✗ | ✗ |
| Meta-Mar [@metamar] | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ |
| MetaDTA / Meta-DiSc 2.0 [@freeman2019; @plana2022] | ✓ (both) | ✓ (both) | ✗ | ✗ | ✗ | ✓ (both) | ✗ |
| CTU TSA [@thorlund2017] | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✓ |

Table: Software comparison (evidence record in the repository's `docs/research/feature-comparison.md`). Symbols: ✓, available; ✗, not available. Where support is partial or qualified, the cell notes the limit. Parentheses specify scope: jamovi core or module names, or "(both)" for the two diagnostic apps. Abbreviations: Biv. DTA, bivariate diagnostic test accuracy (SROC and regions); CMA, Comprehensive Meta-Analysis; CTU, Copenhagen Trial Unit; Meta-reg., multi-moderator meta-regression; Pairwise, pooling two-group comparisons across studies; SROC, summary receiver operating characteristic; TSA, trial sequential analysis.\label{tbl:comparison}

No maintained tool offered a suitable base for closing this gap. RevMan Web,
CMA, Stata, MetaXL, and CTU TSA are closed source, and the open-source
alternatives (MetaDTA, Meta-DiSc 2.0, and Meta-Mar) are web apps that each
cover part of the range. JASP and jamovi could take new modules, but those
modules would still sit inside general statistics programs rather than a
program built only for meta-analysis.

We therefore built on OpenMeta[Analyst] [@wallace2012], a dedicated open-source
predecessor unmaintained since 2016 [@openmetarepo]. It relied on Python 2.x
(2000), Qt 4.x (2005), and R 3.x (2013). We redesigned its interface and
rebuilt the software on Python 3.x, Qt 6.x, and R 4.x. Among the graphical
tools in Table \ref{tbl:comparison}, RC MetaStudio is the only one with
built-in pairwise, bivariate diagnostic, and trial sequential meta-analyses.

# Software design

Reviewers work in a spreadsheet-style grid where each outcome has its own tab,
arm labels, and covariates (Figure \ref{fig:workspace}). They enter data
directly or import CSV, Excel, or `.rm5` files. Clicking a study's row number
opens a calculator that derives effects and standard errors from confidence
intervals, variances, or P values, completes partial counts, and reconstructs
pre–post summaries from a paired correlation. From the Analysis menu, reviewers
configure the model and options in a single setup dialog. Output appears in a
separate window with plots, tables, and draft Methods and Results text.

![RC MetaStudio [VERSION] workspace for the aminoglycoside-dosing dataset of @barza1996: per-arm counts, derived odds ratios, and two outcome tabs (Clinical failure, Nephrotoxicity). Abbreviations: CI, confidence interval; OR, odds ratio.\label{fig:workspace}](paper-figures/figure-1-workspace.png){ width=100% }

The graphical interface is built on Python 3 and Qt 6 via PyQt6 [@pyqt6] and
delegates statistical computation to a bundled R runtime worker [@rcore2026]
with version-pinned CRAN packages. Bundling R enlarges the installer, but
reviewers install nothing else and every copy runs the same package versions.
Wrapping established meta-analysis packages, rather than writing new
estimators, gives reviewers a consistent interface for running analyses while
keeping the statistical core modular, so back-end packages can be replaced if
better options emerge. Because these packages are widely used and validated in
the R ecosystem, results come from code that reviewers already trust and cite.

Our umbrella package, `RCMetaR`, ties four CRAN packages together behind one
internal API (Table \ref{tbl:methods}). Within `RCMetaR`, `metafor`
[@viechtbauer2010] computes effect sizes and fits pairwise, subgroup,
cumulative, leave-one-out, meta-regression, univariate diagnostic, and
mixed-effects Egger models; `meta` [@balduzzi2019] supplies the remaining
funnel-asymmetry tests and trim-and-fill; `mada` [@doebler2025mada] fits the
Reitsma bivariate model [@reitsma2005] with summary receiver operating
characteristic (SROC) curves and confidence and joint prediction regions; and
`gsDesign` [@gsdesign] computes Lan–DeMets alpha- and beta-spending boundaries
[@landemets1983]. For TSA, `RCMetaR` combines those boundaries with `metafor`'s
cumulative fits through published formulas for heterogeneity-adjusted required
information size [@wetterslev2009; @wetterslev2017], non-binding futility
boundaries [@wetterslev2017; @thorlund2017], penalized Z-curves [@lan2003;
@hu2007], and TSA-adjusted confidence intervals [@wetterslev2017;
@thorlund2017].

| Area | Supported options | R package |
| --- | --- | --- |
| Data types and measures | One-arm proportions (raw, log, logit, arcsine, Freeman–Tukey), means, regression coefficients, and entered effects; two-arm binary (odds ratio, risk ratio, risk difference, arcsine difference, and Yule's Q and Y), continuous (mean difference, standardized mean difference), hazard ratio, and raw or reported incidence rate ratio; diagnostic 2×2 counts (sensitivity, specificity, positive and negative likelihood ratios, and diagnostic odds ratio). | `metafor`, `mada` |
| Pooling and $\tau^2$ estimators | Fixed-effect inverse variance, Mantel–Haenszel (binary and raw incidence rate ratio), and Peto; random effects with ten $\tau^2$ estimators: REML (default), DerSimonian–Laird, Paule–Mandel, median-unbiased Paule–Mandel, empirical Bayes, Sidik–Jonkman, maximum likelihood, Hedges, Hunter–Schmidt, and small-sample-corrected Hunter–Schmidt. | `metafor` |
| Inference and intervals | Normal approximation, $t$, Knapp–Hartung, and modified Knapp–Hartung confidence intervals; random-effects prediction intervals; configurable confidence level. | `metafor` |
| Pairwise follow-up analyses | Subgroup analysis with $Q$ difference test; cumulative analysis (table, year, or effect order); leave-one-out analysis (table, year, effect, or $I^2$ order); fixed- and random-effects meta-regression with numeric, categorical, and multiple moderators. | `metafor` |
| Small-study effects | Egger, mixed-effects Egger, Begg, Harbord, Peters, Rücker, Pustejovsky–Rodgers, and Deeks asymmetry tests; ordinary, contour-enhanced, and Deeks funnels; trim-and-fill (L0 and R0 estimators); precision-limit extrapolation. | `meta`, `metafor` |
| Diagnostic accuracy | Count-based Reitsma bivariate model (REML or maximum likelihood) with summary operating points, SROC curve, confidence and joint prediction regions, SROC AUC and partial AUC, sampled likelihood ratios and diagnostic odds ratio, diagnostic $I^2$, and additive bivariate meta-regression; univariate diagnostic models. | `mada`, `metafor` |
| Trial sequential analysis | Risk ratio, odds ratio, risk difference, Peto odds ratio, mean difference, and reported hazard ratio; $D^2$ or $I^2$ heterogeneity-adjusted required information size; Lan–DeMets O'Brien–Fleming and Pocock spending boundaries; non-binding futility boundaries; penalized Z-curve; TSA-adjusted confidence intervals; anticipated-effect sensitivity table. | `metafor`, `gsDesign`, `RCMetaR` |

Table: Statistical options and features in RC MetaStudio (documented in the repository's `docs/user-guide.md`). Abbreviations: AUC, area under the curve; $D^2$, diversity; $I^2$, percentage of variability due to heterogeneity; $Q$, Cochran's heterogeneity statistic; REML, restricted maximum likelihood; SROC, summary receiver operating characteristic; $\tau^2$, between-study variance; TSA, trial sequential analysis.\label{tbl:methods}

Across all supported methods, `RCMetaR` transforms package outputs into one
consistent presentation of tables, draft text, and plots. R's graphics produce
uniform, journal-ready figures directly from the fitted model object in memory,
so reviewers can use *Edit plot* to switch between the Default, BMJ, and RevMan
styles (Figure \ref{fig:forest}) or adjust labels, colors, axes, and study
order without refitting. The same path draws follow-up pairwise figures (Figure
\ref{fig:pairwise}) and bivariate SROC and TSA monitoring plots (Figure
\ref{fig:diagnostic}). Figures export as PDF, SVG, PNG, or TIFF at chosen
dimensions and resolution; numeric tables as CSV; and draft Methods and Results
reports as PDF or Word (`.docx`).

![Random-effects forest plot of risk ratios for the 13 BCG trials [@colditz1994] in the three built-in styles: (A) Default, (B) BMJ, and (C) RevMan. All three panels come from the same REML fit with normal-approximation 95% CIs (pooled RR 0.49, 95% CI 0.34 to 0.70); only the style differs. Figures \ref{fig:forest} to \ref{fig:diagnostic} were exported from RC MetaStudio [VERSION]. Abbreviations: BCG, bacille Calmette–Guérin; CI, confidence interval; df, degrees of freedom; $I^2$, percentage of variability due to heterogeneity; IV, inverse variance; $Q$ and $\chi^2$, Cochran's heterogeneity statistic; REML, restricted maximum likelihood; RR, risk ratio; $\tau^2$, between-study variance; TPT, Tuberculosis Prevention Trial.\label{fig:forest}](paper-figures/figure-2-forest.pdf){ width=100% }

![Follow-up analyses of the BCG trials in Figure \ref{fig:forest} (Default style). (A) Meta-regression of risk ratios on absolute latitude; circle size reflects study weight. (B) Contour-enhanced funnel plot; shading indicates P value regions around no effect (solid line at 1), and the dashed line marks the common-effect (fixed-effect) estimate. Abbreviations: BCG, bacille Calmette–Guérin; CI, confidence interval.\label{fig:pairwise}](paper-figures/figure-3-pairwise.pdf){ width=100% }

![Diagnostic and trial sequential analyses (Default style). (A) Reitsma SROC curve for noninvasive diagnosis of deep venous thrombosis [@kearon1998] with study points, summary point, confidence region, and joint prediction region. (B) TSA of hazard ratios for chemotherapy in head and neck cancer [@pignon2000]; the horizontal axis shows inverse-variance statistical information (sum of inverse variances of the log HRs), not participant counts. The cumulative Z-curve crosses the conventional boundary first, then the lower monitoring boundary at 42% of RIS with the Bavaria 89 trial (circled). Abbreviations: AUC, area under the curve; HR, hazard ratio; RIS, required information size; SROC, summary receiver operating characteristic; TSA, trial sequential analysis.\label{fig:diagnostic}](paper-figures/figure-4-diagnostic-sequential.pdf){ width=100% }

# Research impact statement

About 500 students, from beginners to experienced clinical researchers, have
used RC MetaStudio in meta-analysis workshops run by Research Consultancy and
the Research Council of Pakistan. Their feedback has shaped the software.

# AI usage disclosure

During development, we used OpenAI GPT (GPT-5.6 onward, via Codex), Anthropic
Claude (Claude 5.0 onward), and Google Gemini (Gemini 4 onward) models to
assist with code, tests, documentation, and paper drafting. We reviewed all
changes before merging and verified behavior through strict type checking,
end-to-end desktop tests, direct R-package comparisons, and cross-checks
against established software such as RevMan and the CTU TSA program. We take
full responsibility for the software and paper.

# Acknowledgements

We thank the authors of OpenMeta[Analyst], `metafor`, `meta`, `mada`, and
`gsDesign`. RC MetaStudio is not affiliated with or endorsed by the
OpenMeta[Analyst] authors or their institutions. Research Consultancy funded
only the AI subscriptions used during development, and its role is disclosed
under Competing interests.

# Competing interests

All five authors hold leadership or research roles at Research Consultancy,
which develops RC MetaStudio, and at its sister organization, the Research
Council of Pakistan. Muhammad Shahzeb Khan and Kaneez Fatima founded both
organizations, where Muhammad Shariq Usman is president, Tariq Jamal Siddiqi is
vice president, and Ali Salman is head research analyst. Both organizations
teach RC MetaStudio in paid meta-analysis workshops.

# References
