# Feature comparison: RC MetaStudio and other meta-analysis software

Checked 2026-11-23; Stata 19 added 2026-11-24.

This file is the evidence record behind the comparison claims in the JOSS
paper. Section 1 lists what RC MetaStudio 0.7.0 ships, with a repository
citation for each item. Section 2 compares those features with eleven other
tools. Section 3 summarises what is shared and what differs.

Versions checked:

| Tool | Version or state checked |
| --- | --- |
| RC MetaStudio | 0.7.0 (CHANGELOG dated 2026-11-21; repository at `cbf78a6a`) |
| RevMan Web | 11.14.0 (release notes, 12 Nov 2026) |
| JASP, Meta-Analysis module | JASP 0.99.0; jaspMetaAnalysis `e1cccc46` (2026-11-21) |
| jamovi modules | jamovi 28.18; MetaJam 0.6.0; MAJOR 1.2.0 on GitHub (library lists 1.2.4); OncoPath 1.1.4 on GitHub (library lists 1.1.2) |
| CTU TSA | 0.9.5.10 Beta with its 2017 manual |
| CMA | v4, from 2025 Wayback snapshots of meta-analysis.com and the linked v3 manual |
| Stata | Release 19 (`[META]` and `[ADAPT]` reference manuals, 2025; StataNow additions noted) |
| MetaXL | 5.3 (user guide, September 2016) |
| Meta-Essentials | workbooks 1.5 |
| Meta-Mar | Classic v4.0.2 |
| MetaDTA / Meta-DiSc 2.0 | MetaDTA 2.1.5; Meta-DiSc 2.0 source of 2022-11-04 |
| OpenMeta[Analyst] | GitHub master `e3147cab` (2020-07-28; last code change 2016-06-05) |

No program other than RC MetaStudio was run for this check. Cells come from
each tool's own documentation, source code or licence, as listed in
Appendix A.


## 1. RC MetaStudio 0.7.0 feature inventory

Only shipped behaviour is listed. Citations are `file:line` in this
repository at the 0.7.0 documentation state (CHANGELOG
[0.7.0](../../CHANGELOG.md), commit `cbf78a6a`).

### 1.1 Data entry and data types

| Feature | Source |
| --- | --- |
| Spreadsheet-style outcome sheets; a project holds several independent outcome sheets, each with its own rows, data type, arm names, covariates and settings | [README.md:8](../../README.md), [user-guide.md:12](../user-guide.md) |
| One-arm proportions (events, total) with measures `PR`, `PLN`, `PLO`, `PAS`, `PFT` | [user-guide.md:23](../user-guide.md) |
| One-arm means (N, mean, SD; or mean, SE, N via calculator) | [user-guide.md:24](../user-guide.md) |
| Reported regression coefficient with CI, and entered effect estimate with SE (generic inverse variance on the supplied scale) | [user-guide.md:25-26](../user-guide.md) |
| Two-arm binary counts, or entered effect; `OR`, `RR`, `RD`, `AS`, `YUQ`, `YUY` | [user-guide.md:27](../user-guide.md) |
| Two-arm continuous (N, mean, SD per arm, or entered effect); `MD`, `SMD` | [user-guide.md:28](../user-guide.md) |
| Hazard ratios as a distinct data type: HR with CI (with source confidence level) or log HR with SE | [user-guide.md:29](../user-guide.md), [user-guide.md:41](../user-guide.md), [ADR-0010](../adr/0010-distinguish-hazard-and-incidence-rate-ratios.md) |
| Incidence rate ratios from events and person-time per arm, or reported IRR with CI or log IRR with SE; raw and reported studies may be mixed in one sheet | [user-guide.md:29](../user-guide.md), [user-guide.md:42-43](../user-guide.md) |
| Diagnostic test accuracy counts (`TP`, `FN`, `FP`, `TN`) or univariate estimates; `Sens`, `Spec`, `PLR`, `NLR`, `DOR` | [user-guide.md:30](../user-guide.md) |
| Numeric and categorical study-level covariates, convertible between the two | [user-guide.md:35](../user-guide.md) |
| Editable arm names, arm swap, and declared benefit direction used in labels, reports and one-sided TSA | [user-guide.md:33](../user-guide.md) |
| Sheet-level confidence level with per-analysis override; source confidence level of entered intervals is kept | [user-guide.md:34](../user-guide.md), [CHANGELOG.md:117](../../CHANGELOG.md) |
| Undo/redo of the last 100 committed edits | [user-guide.md:14](../user-guide.md) |
| Nine bundled published sample projects with cited source tables | [sample_projects/README.md:5-15](../../sample_projects/README.md), [CHANGELOG.md:7](../../CHANGELOG.md) |

Stated limits: no HR reconstruction from Kaplan–Meier curves, log-rank
statistics or IPD, and no Poisson GLMMs
([user-guide.md:46](../user-guide.md)).

### 1.2 Calculators

| Feature | Source |
| --- | --- |
| Per-study calculator that derives effect estimates and SEs from reported statistics, completes partial counts and reconstructs missing summaries | [user-guide.md:32](../user-guide.md) |
| Continuous calculator inputs include N, mean, SD, SE, variance, CI bounds and P value | [continuous_dialog.py:58-77](../../src/rc_metastudio/calculators/continuous_dialog.py) |
| Pre/post continuous inputs with a paired correlation | [user-guide.md:32](../user-guide.md) |
| Reported HR/IRR entry as ratio with CI or log ratio with SE, with conversion between formats | [user-guide.md:41](../user-guide.md) |

### 1.3 Import and export

| Feature | Source |
| --- | --- |
| CSV import with column mapping, custom delimiter and quote character | [user-guide.md:54](../user-guide.md) |
| Excel `.xlsx` import (up to 100,000 rows, 512 columns, 1,000,000 cells; cached formula values) | [user-guide.md:55](../user-guide.md) |
| RevMan 5 `.rm5` import with a review step listing mapped methods and items not imported (prose, references, risk-of-bias tables, graphs) | [user-guide.md:68-86](../user-guide.md) |
| Figure export to PDF, SVG, PNG or TIFF with physical size and DPI | [user-guide.md:182](../user-guide.md), [README.md:43](../../README.md) |
| Report export to PDF or Word `.docx`; section copying | [user-guide.md:183](../user-guide.md) |
| Results tables copied, or exported as formatted CSV or as unrounded values CSV with scales and confidence levels | [user-guide.md:184](../user-guide.md), [CHANGELOG.md:66](../../CHANGELOG.md) |
| Citation export (BibTeX, RIS, EndNote) | [user-guide.md:189](../user-guide.md) |

### 1.4 Analyses

| Feature | Source |
| --- | --- |
| Fixed-effect inverse variance, Mantel–Haenszel and Peto where eligible; random effects (REML default) | [user-guide.md:98](../user-guide.md), [analysis_contracts.R:141](../../r/RCMetaR/R/analysis_contracts.R) |
| τ² estimators `REML`, `DL`, `PM`, `PMM`, `EB`, `SJ`, `ML`, `HE`, `HS`, `HSk` | [user-guide.md:98](../user-guide.md) |
| Inference by normal approximation, t, Knapp–Hartung or modified Knapp–Hartung | [user-guide.md:98](../user-guide.md), [analysis_contracts.R:254-261](../../r/RCMetaR/R/analysis_contracts.R) |
| Prediction interval for random-effects pooled estimates (forest summary label; optional on bubble plots) | [forest_summary.R:167-179](../../r/RCMetaR/R/forest_summary.R), [bubble_metafor.R:279](../../r/RCMetaR/R/bubble_metafor.R) |
| Mantel–Haenszel for raw IRR (fixed, sequential and subgroup fits) | [user-guide.md:44-45](../user-guide.md) |
| Cumulative meta-analysis ordered by table, publication year or study effect, with progress and cancellation | [user-guide.md:103-117](../user-guide.md), [CHANGELOG.md:9](../../CHANGELOG.md) |
| Leave-one-out analysis with an all-studies reference row, ordered by table, year, pooled effect or I² after omission | [user-guide.md:119-125](../user-guide.md) |
| Subgroup analysis on a categorical covariate with a subgroup-difference Q test | [user-guide.md:160](../user-guide.md) |
| Meta-regression with numeric, categorical and multiple moderators (fixed or random effects) | [user-guide.md:161](../user-guide.md) |
| Small-study effects: test choice by data family (Egger, Begg, mixed-effects Egger, Harbord, Peters, Rücker, Pustejovsky–Rodgers; Deeks for diagnostic counts), configurable minimum k | [user-guide.md:167](../user-guide.md), [small_study_effects.R:100-157](../../r/RCMetaR/R/small_study_effects.R) |
| Ordinary and contour-enhanced funnels, trim-and-fill (side and L0/R0 estimator), precision-limit extrapolation, Deeks effective-sample-size funnel | [user-guide.md:168](../user-guide.md) |
| Count-based Reitsma bivariate DTA model (`mada`), summary operating points, SROC curve, joint prediction region, SROC AUC and partial AUC, sampled LR and DOR, diagnostic I² | [user-guide.md:99](../user-guide.md), [ADR-0004:3-13](../adr/0004-use-mada-reitsma-for-joint-diagnostic-models.md) |
| Additive Reitsma bivariate meta-regression with likelihood-ratio moderator tests and separate sensitivity/specificity coefficient plots | [user-guide.md:161](../user-guide.md), [CHANGELOG.md:235](../../CHANGELOG.md) |
| Trial sequential analysis for RR, OR, RD, Peto OR, MD and reported HR: required information size with D² or I² adjustment, Lan–DeMets O'Brien–Fleming or Pocock boundaries, non-binding futility wedge, penalised Z-curve, TSA-adjusted CIs, sensitivity table | [trial-sequential-analysis.md:19-51](../trial-sequential-analysis.md), [trial-sequential-analysis.md:70-82](../trial-sequential-analysis.md), [ADR-0011:37-39](../adr/0011-implement-trial-sequential-analysis-over-metafor-and-gsdesign.md) |

Not offered: TSA for SMD and IRR
([trial-sequential-analysis.md:123-126](../trial-sequential-analysis.md)).
No multilevel/multivariate, Bayesian, network, selection-model or PET-PEESE
analysis appears in the user guide or in `r/RCMetaR/R`; RCMetaR contains
permutation helpers ([permutation.R](../../r/RCMetaR/R/permutation.R)) with
no caller in `src/rc_metastudio`, so they are not a shipped feature.

### 1.5 Figures

| Feature | Source |
| --- | --- |
| Forest, bubble, funnel, SROC, coefficient and TSA figures | [user-guide.md:179](../user-guide.md) |
| Plot editor: Default, BMJ and RevMan styles, labels, captions, colours, axis limits, point scaling; redrawn in R without refitting | [user-guide.md:181](../user-guide.md), [CHANGELOG.md:10](../../CHANGELOG.md) |
| Multi-page forest export | [CHANGELOG.md:10](../../CHANGELOG.md) |
| TSA monitoring plot with participant or information axis, RIS line, futility region and optional penalised curve | [trial-sequential-analysis.md:84-115](../trial-sequential-analysis.md) |

### 1.6 Reports

| Feature | Source |
| --- | --- |
| Formatted text report: Methods, Results, numerical tables, numbered references citing RC MetaStudio and the R packages, model configuration | [user-guide.md:183](../user-guide.md), [CHANGELOG.md:39-41](../../CHANGELOG.md) |
| Rerun with changed settings replaces the result only after a successful fit | [user-guide.md:185](../user-guide.md) |

The 0.5.1 entry "structured Summary of findings"
([CHANGELOG.md:125](../../CHANGELOG.md)) has no matching code in
`src/rc_metastudio` or `r/RCMetaR` (no match for "of findings", "GRADE" or
"certainty"), so it is not counted as a shipped feature.

### 1.7 Projects and reproducibility

| Feature | Source |
| --- | --- |
| `.rcms` v3 project: ZIP of three JSON members with hashes; stores data, covariates and analysis settings; migrates v1/v2 | [project-format.md:3-21](../project-format.md), [user-guide.md:13](../user-guide.md) |
| Validated reading, atomic saving, deterministic output for the same content | [project-format.md:27-33](../project-format.md) |
| Statistics delegated to named, version-pinned R packages (metafor 5.2-1, meta 8.5-0, mada 0.5.12, gsDesign 3.11.0) with a dated binary snapshot and hashes | [README.md:47-54](../../README.md), [ADR-0001](../adr/0001-delegate-statistical-decisions-to-authority-packages.md), [config/r-dependencies.json](../../config/r-dependencies.json) |
| Tutorial R script that reproduces the BCG example directly with metafor | [README.md:35](../../README.md) |

RC MetaStudio does not export analysis code. Results are output files, not
saved in the project ([user-guide.md:13](../user-guide.md)).

### 1.8 Platform

| Feature | Source |
| --- | --- |
| Free, GPL-3.0-or-later | [README.md:8](../../README.md), [README.md:90](../../README.md) |
| Desktop packages for Windows x64, Apple silicon macOS 14+ and Ubuntu 24.04 x86_64, each bundling Python, Qt 6 and R 4.6.2 | [README.md:16-22](../../README.md), [ADR-0009](../adr/0009-support-qualified-release-platforms.md) |
| Signed and notarised macOS release; checksums and CycloneDX SBOMs | [README.md:24](../../README.md) |
| System, Light and Dark themes | [user-guide.md:15](../user-guide.md) |
| Independently maintained rewrite of OpenMeta[Analyst] | [README.md:88](../../README.md) |

## 2. Comparison matrix

### How cells were assigned

- **✓**: the feature ships and is documented in the tool's own manual,
  website, release notes or source.
- **partial**: the feature ships with a stated limit; Appendix A says which.
- **✗**: the tool's documentation states the feature is absent; or the
  feature is missing from a list the tool presents as its full set of
  measures, input types, analyses or menus; or, where Appendix A says
  "source", a search of the tool's full source found no implementation.
- **?**: not verified. Silence on a page that does not claim to be complete
  gives "?".

Rows are RC MetaStudio features at a readable granularity, plus eight rows
(A18–A21, F3, R2, P2, L4) for features RC MetaStudio lacks. RC MetaStudio
cells cite Section 1. Every other cell has a row-level entry in Appendix A
with its evidence and source.

The jamovi column combines three modules: MetaJam (meta-based pairwise
analyses), MAJOR (metafor-based) and OncoPath (`diagnosticmeta`, using
`mada::reitsma`). The module named in a cell supplies it, and "core" means
jamovi itself. In the MetaDTA / Meta-DiSc 2.0 column, the app named in a
cell supplies it.

| ID | Feature | RC MetaStudio | RevMan Web | JASP (Meta-Analysis) | jamovi (MetaJam, MAJOR, OncoPath) | CTU TSA 0.9.5.10 Beta | CMA v4 | Stata 19 | MetaXL 5.3 | Meta-Essentials 1.5 | Meta-Mar | MetaDTA / Meta-DiSc 2.0 | OpenMeta[Analyst] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | **Data entry and data types** | | | | | | | | | | | | |
| D1 | Two-arm binary counts (OR, RR, RD) | ✓ | ✓ | ✓ | ✓ (MetaJam, MAJOR) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| D2 | Two-arm continuous (MD, SMD) | ✓ | ✓ | ✓ | ✓ (MetaJam, MAJOR) | partial | ✓ | ✓ | ✓ | partial | ✓ | ✗ | ✓ |
| D3 | Single-arm proportions (transformed) and means | ✓ | ✗ | ✓ | ✓ (MetaJam, MAJOR) | ✗ | partial | partial | partial | ✗ | ✗ | ✗ | ✓ |
| D4 | Generic inverse variance (estimate with SE or CI) | ✓ | ✓ | ✓ | ✓ (MetaJam) | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| D5 | Hazard ratio as a dedicated input (HR with CI or log HR with SE) | ✓ | partial | ✗ | ✓ (MetaJam) | ✗ | ✓ | ✗ | ✓ | ✗ | partial | ✗ | ✗ |
| D6 | Incidence rate ratio from events and person-time | ✓ | ✗ | ✓ | ✓ (MetaJam) | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| D7 | Diagnostic 2×2 counts | ✓ | ✓ | ✗ | ✓ (OncoPath) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ (both) | ✓ |
| D8 | Several outcomes in one project | ✓ | ✓ | partial | ✓ (core) | ✗ | ✓ | partial | ✓ | ✗ | ? | ✗ | ✓ |
| D9 | Continuous and categorical study covariates | ✓ | ✓ | ✓ | ✓ (MetaJam) | partial | ✓ | ✓ | partial | partial | ✓ | partial | ✓ |
| | **Calculators** | | | | | | | | | | | | |
| C1 | Effect-size calculator from reported statistics | ✓ | partial | ✓ | ? | ✗ | ✓ | partial | partial | partial | ? | ✗ | ✓ |
| C2 | Pre/post means with a pre–post correlation | ✓ | ? | ✓ | ? | ✗ | ✓ | ✗ | ✗ | ✓ | ? | ✗ | partial |
| | **Import and export** | | | | | | | | | | | | |
| I1 | CSV import | ✓ | ✓ | ✓ | ✓ (core) | partial | partial | ✓ | partial | partial | ✓ | ✓ (both) | ✓ |
| I2 | Excel .xlsx import | ✓ | ? | ✓ | ✓ (core) | ? | partial | ✓ | ✓ | partial | ✓ | ✓ (both) | ✗ |
| I3 | RevMan 5 .rm5 import | ✓ | ✓ | ✗ | ? | partial | ? | ✗ | ? | ? | ? | ✗ | ✗ |
| I4 | Figure export: vector and raster at chosen resolution | ✓ | partial | ✓ | partial (core) | ? | partial | ✓ | partial | partial | ? | partial | partial |
| I5 | Numeric results export (CSV) | ✓ | ✓ | partial | partial (core) | ? | ? | partial | ✓ | partial | ? | ✓ (both) | partial |
| | **Analyses** | | | | | | | | | | | | |
| A1 | Fixed-effect inverse variance | ✓ | ✓ | ✓ | ✓ (MetaJam, MAJOR) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| A2 | Mantel–Haenszel and Peto OR | ✓ | ✓ | ✓ | ✓ (MetaJam) | partial | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| A3 | τ² estimators beyond DerSimonian–Laird | ✓ | partial | ✓ | ✓ (MetaJam, MAJOR) | ✓ | partial | ✓ | ✗ | ✗ | ✓ | ✗ | ✓ |
| A4 | Hartung–Knapp or t-based inference | ✓ | ✓ | ✓ | ✓ (MetaJam) | ✗ | partial | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ |
| A5 | Prediction interval | ✓ | ✓ | ✓ | ✓ (MetaJam, MAJOR) | ? | ✓ | ✓ | ? | ✓ | ✓ | partial (both) | ✗ |
| A6 | Subgroup analysis with a test for differences | ✓ | ✓ | ✓ | ✓ (MetaJam) | ✗ | ✓ | ✓ | partial | ✓ | ✓ | ✓ (Meta-DiSc 2.0) | partial |
| A7 | Meta-regression, more than one moderator | ✓ | ✗ | ✓ | ✓ (MetaJam) | ✗ | ✓ | ✓ | partial | ✗ | ✓ | ✗ | ✓ |
| A8 | Cumulative meta-analysis | ✓ | ? | ✗ | ✓ (MetaJam) | ✓ | ✓ | ✓ | ✓ | ✗ | ? | ✗ | ✓ |
| A9 | Leave-one-out analysis | ✓ | ? | partial | ✓ (MetaJam) | partial | ✓ | ✓ | ✓ | partial | ? | partial (MetaDTA) | ✓ |
| A10 | Funnel plot, including contour-enhanced | ✓ | partial | ✓ | ✓ (MetaJam, MAJOR) | ✗ | partial | ✓ | partial | partial | ✓ | ✗ | ✗ |
| A11 | Small-study tests (Egger, Begg; Harbord or Peters) | ✓ | ✗ | partial | ✓ (MetaJam) | ✗ | partial | ✓ | ✗ | partial | partial | ✗ | ✗ |
| A12 | Trim-and-fill | ✓ | ? | ✓ | ✓ (MetaJam) | ✗ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ |
| A13 | Bivariate DTA model with SROC and regions | ✓ | partial | ✗ | ✓ (OncoPath) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ (both) | partial |
| A14 | Bivariate DTA meta-regression | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | partial (Meta-DiSc 2.0) | ✗ |
| A15 | Deeks' funnel asymmetry test | ✓ | ? | ✗ | ✓ (OncoPath) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| A16 | Trial sequential analysis (RIS, spending boundaries, futility) | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| A17 | Trial sequential analysis for hazard ratios | ✓ | ? | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ? | ✗ | ✗ |
| A18 | Multilevel / multivariate models | ✗ | ? | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| A19 | Bayesian meta-analysis | ✗ | ? | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | partial |
| A20 | Network meta-analysis | ✗ | ? | ✗ | ✗ | ✗ | ✗ | ✗ | partial | ✗ | ✗ | ✗ | ✗ |
| A21 | Selection models or PET-PEESE | ✗ | ? | ✓ | partial (MAJOR) | ✗ | ✗ | ✗ | ✗ | ✗ | ? | ✗ | ✗ |
| | **Figures** | | | | | | | | | | | | |
| F1 | Forest plot with editable appearance and style presets | ✓ | partial | partial | partial (MetaJam) | ✗ | ✓ | partial | partial | partial | ? | partial | partial |
| F2 | Bubble plot for meta-regression | ✓ | ✗ | ✓ | ✓ (MetaJam) | ✗ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | partial |
| F3 | Risk-of-bias tables or plots | ✗ | ✓ | ✓ | ✓ (MetaJam) | ✗ | ? | partial | ✗ | ✗ | ? | ✓ (MetaDTA) | ✗ |
| | **Reports** | | | | | | | | | | | | |
| R1 | Generated Methods/Results report to Word or PDF | ✓ | partial | ? | ? | ? | ✓ | ✗ | ✗ | ✗ | partial | ✗ | ✗ |
| R2 | GRADE / Summary of findings tables | ✗ | ✓ | ✗ | ? | ✗ | ? | ✗ | ✗ | ✗ | ? | partial (Meta-DiSc 2.0) | ✗ |
| | **Projects and reproducibility** | | | | | | | | | | | | |
| P1 | Project file with data and analysis settings | ✓ | ✓ | ✓ | ✓ (core) | ✓ | partial | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ |
| P2 | Analysis code export | ✗ | ? | ✓ | ✓ (core) | ✗ | ✗ | ✓ | partial | partial | ? | ✗ | ✗ |
| P3 | Named, version-pinned statistical engine | ✓ | ? | ✓ | partial (MetaJam) | partial | partial | partial | partial | partial | partial | ✓ (Meta-DiSc 2.0) | partial |
| | **Platform and licence** | | | | | | | | | | | | |
| L1 | Free of charge | ✓ | partial | ✓ | ✓ (core) | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ (both) | ✓ |
| L2 | Open-source licence | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | partial | partial | ✓ (both) | partial |
| L3 | Installable desktop application | ✓ | ✗ | ✓ | ✓ (core) | ✓ | partial | ✓ | partial | partial | ✗ | ✗ | ✓ |
| L4 | Runs in a web browser | ✗ | ✓ | ? | partial (core) | ✗ | ✗ | ✗ | ✗ | partial | ✓ | ✓ (both) | ✗ |

## 3. Same and different

These statements are read off the matrix. "Free tools" means the columns
with ✓ in row L1: JASP, jamovi, CTU TSA, MetaXL, Meta-Essentials, Meta-Mar,
MetaDTA / Meta-DiSc 2.0 and OpenMeta[Analyst]. RevMan Web (a paid
subscription with free access for some users), CMA (commercial) and
Stata 19 (commercial) are not in that set.

### Shared with most tools

Most tools offer two-arm binary and generic inverse-variance input
(D1, D4), fixed-effect inverse variance (A1), Mantel–Haenszel and Peto
pooling (A2), subgroup analysis with a difference test (A6), and a project
or file that reopens data and settings (P1). Most general-purpose tools also
offer:

- two-arm continuous input (D2) and study covariates (D9);
- CSV import (I1);
- τ² estimators beyond DerSimonian–Laird (A3), Hartung–Knapp inference
  (A4) and prediction intervals (A5);
- meta-regression with several moderators (A7) and cumulative analysis (A8);
- trim-and-fill (A12) and a bubble plot (F2).

Some features RC MetaStudio shares with only one to four other tools:

| Feature | Other tools with ✓ |
| --- | --- |
| Hazard ratios as a dedicated input (D5) | jamovi/MetaJam, CMA, MetaXL |
| Incidence rate ratios from person-time (D6) | JASP, jamovi/MetaJam, CMA, MetaXL |
| Contour-enhanced funnels (A10) | JASP, jamovi, Stata 19, Meta-Mar |
| Egger, Begg and Harbord or Peters tests (A11) | jamovi/MetaJam, Stata 19 |
| Bivariate DTA model with SROC and regions (A13) | jamovi/OncoPath, MetaDTA / Meta-DiSc 2.0 |
| Deeks' test (A15) | jamovi/OncoPath |
| Trial sequential analysis (A16) | CTU TSA |
| Version-pinned R engine (P3) | JASP (renv.lock), Meta-DiSc 2.0 (packrat.lock) |

### Only RC MetaStudio, among the free tools checked

Firm: every other free tool is ✗ or partial.

1. **Pairwise meta-analysis, bivariate DTA meta-analysis and trial
   sequential analysis in one application.** No other free tool has both
   A13 and A16. JASP is ✗ on both, and jamovi has A13 (OncoPath) but not
   A16. CTU TSA, MetaXL, Meta-Essentials and Meta-Mar lack A13.
   MetaDTA / Meta-DiSc 2.0 and OpenMeta[Analyst] lack A16.
2. **Bivariate (Reitsma) DTA meta-regression with several continuous or
   categorical moderators** (A14). Meta-DiSc 2.0 fits one dichotomous
   covariate in the bivariate model, assuming equal between-study variances
   (partial; Plana et al. 2022). jamovi/OncoPath and OpenMeta[Analyst] fit
   covariates in separate univariate models (✗). JASP lists bivariate DTA
   as not implemented (✗). Outside the free set, RevMan Web does not fit
   the bivariate model (✗), CMA has no DTA format (✗) and Stata 19 has no
   built-in bivariate DTA command (✗).

No source contradicts the next four, but each has unverified cells.
Word these as "not documented by the other tools checked".

3. **Trial sequential analysis for hazard ratios** (A17). CTU TSA has no HR
   measure ([trial-sequential-analysis-methods.md:134](trial-sequential-analysis-methods.md)).
   JASP, jamovi, MetaXL, Meta-Essentials, MetaDTA / Meta-DiSc 2.0 and
   OpenMeta[Analyst] have no TSA. Meta-Mar is "?" because its feature page
   does not claim to be complete. RevMan Web, outside the free set, is
   also "?". The R package tsahr does TSA for hazard ratios, so the claim
   holds only for applications with a graphical interface
   ([ADR-0011:32-33](../adr/0011-implement-trial-sequential-analysis-over-metafor-and-gsdesign.md)).
4. **Direct RevMan 5 `.rm5` import** (I3). JASP, MetaDTA / Meta-DiSc 2.0 and
   OpenMeta[Analyst] have no such importer (✗). CTU TSA reads RevMan data
   only through a CSV converter, and only for dichotomous outcomes
   (partial). jamovi, MetaXL, Meta-Essentials and Meta-Mar are "?".
   RevMan Web imports .rm5 but is not in the free set.
5. **A generated Methods/Results report with references, exported to Word
   or PDF** (R1). Meta-Mar offers optional AI-written reports whose content
   and export are undocumented (partial). MetaXL, Meta-Essentials,
   MetaDTA / Meta-DiSc 2.0 and OpenMeta[Analyst] have no report generator
   (✗). JASP, jamovi and CTU TSA are "?": they export output as HTML, PDF
   or .docx, and no generated prose was found. Outside the free set, CMA
   generates a report with references (✓).
6. **Forest plots with both style presets and colour, label and axis
   editing** (F1). The free tools that have editable forest plots are
   partial. JASP has axis and colour settings but no presets.
   jamovi/MetaJam has presets (Default, RevMan 5, JAMA, BMJ) but no colour
   options. Meta-Mar is "?". Outside the free set, CMA documents both (✓).
   Of the claims in this section, this one depends most on interpretation.

### Present in other tools, absent from RC MetaStudio

- **Multilevel and multivariate models** (`rma.mv`): JASP, Stata 19 (A18).
- **Bayesian meta-analysis**: JASP (RoBMA, NoBMA, BiBMA). OpenMeta[Analyst]
  has a Bayesian HSROC model for DTA only (A19).
- **Selection models and PET-PEESE**: JASP. jamovi/MAJOR offers selection
  models for some effect types (A21).
- **Network meta-analysis**: MetaXL offers chained indirect comparisons
  through one common comparator (A20, partial). No tool in the matrix fits
  a full network model. Dedicated network tools such as MetaInsight were
  not checked.
- **Risk-of-bias plots** (F3): RevMan Web; JASP and jamovi/MetaJam through
  robvis; MetaDTA, which shows QUADAS-2 judgements on the SROC; Stata 19
  (`meta forestplot, robias()` in StataNow, partial).
- **GRADE or Summary of findings tables**: RevMan Web. Meta-DiSc 2.0 has a
  partial "Summary of findings" view (R2).
- **Analysis code export**: JASP ("Show metafor R code"), jamovi ("the
  exact R code behind it") and Stata 19 (Meta-Analysis Control Panel
  actions echo Stata commands) (P2).
- **Use in a web browser without installation**: RevMan Web, Meta-Mar,
  MetaDTA / Meta-DiSc 2.0 and jamovi Cloud (L4).
- **Analyses outside the matrix rows**:
  - JASP: casewise influence diagnostics, GLMMs, meta-analytic SEM and
    location-scale models.
  - CMA: more than 100 data-entry formats.
  - Stata 19: L'Abbé plots, Galbraith plots and psychometric correlation
    corrections (`meta psycorr` in StataNow).
  - MetaXL: the quality-effects and IVhet models, and the Doi plot with
    the LFK index.

### Notes for citing this file

- JASP's FEATURE_COVERAGE.md lists `leave1out()` and `cumul()` as not
  implemented. JASP does ship `influence()` casewise diagnostics, so A9 is
  partial, not ✗.
- RevMan Web added REML, HKSJ and prediction intervals in release 8.15.0
  (January 2025), and HR for O–E and variance data in 11.11.0 (October
  2026). It does not fit hierarchical DTA models: its SROC plot draws
  parameters estimated in other software.
- The MAJOR build in the jamovi library (1.2.4) is newer than its GitHub
  source (1.2.0), so MAJOR cells describe the GitHub code.
- Meta-Mar's repository licence (MIT) and website licence (AGPL-3.0)
  disagree.
- CMA cells come from archived 2025 pages and a v3 manual. Read the CMA ✗
  cells as "not listed by the vendor", and recheck them against a current
  v4 manual before publication.
- Stata 19 cells reflect Stata's built-in `[META]` and `[ADAPT]` suites
  (`Statistics > Meta-analysis`), not community-contributed SSC or *Stata
  Journal* commands such as `metandi`, `midas`, `metadta`, `metacumbounds`
  or `network`.
- The A10 ✓ for JASP rests on reading its funnel-plot QML. That code fills
  significance regions around the null at 0.90, 0.95 and 0.99 but does
  not label them "contour-enhanced".
- The row count (49) is above the 30–45 target. Merging further would hide
  cells that the uniqueness claims depend on, such as A14, A16 and A17.

## Appendix A. Row-level evidence for other tools

### RevMan Web

Version checked: RevMan Web 11.14.0 (release notes, 12 Nov 2026); Cochrane Handbook v6.5.1 ch. 10 (Nov 2026).

Sources:

- **RM1**: https://documentation.cochrane.org/revman-kb/files/210600101/210600103/1/1654774257333/Statistical_methods_in_revman.pdf
- **RM2**: https://documentation.cochrane.org/revman-kb/data-package-specification-249561249.html
- **RM3**: https://documentation.cochrane.org/revman-kb/revman-release-notes-342261851.html
- **RM4**: https://documentation.cochrane.org/revman-kb/data-and-analyses-in-dta-reviews-236847625.html
- **RM5**: https://documentation.cochrane.org/revman-kb/pre-define-analyses-260702251.html
- **RM6**: https://documentation.cochrane.org/revman-kb/sensitivity-analyses-260702328.html
- **RM7**: https://documentation.cochrane.org/revman-kb/calculator-95420946.html
- **RM8**: https://documentation.cochrane.org/revman-kb/files/210600101/210600104/1/1654774275069/revman5-calculator.pdf
- **RM9**: https://documentation.cochrane.org/revman-kb/populate-study-data-260702462.html
- **RM10**: https://documentation.cochrane.org/revman-kb/managing-your-reviews-212995000.html
- **RM11**: https://documentation.cochrane.org/revman-kb/save-a-figure-or-forest-plot-159089420.html
- **RM12**: https://documentation.cochrane.org/revman-kb/export-data-228786748.html
- **RM13**: https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-10
- **RM14**: https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-13
- **RM15**: https://documentation.cochrane.org/revman-kb/add-a-figure-95420437.html
- **RM16**: https://documentation.cochrane.org/revman-kb/analysis-graphs-in-dta-reviews-236847627.html
- **RM17**: https://documentation.cochrane.org/revman-kb/files/210600101/297467907/1/1707731495443/stats-methods.pdf
- **RM18**: https://documentation.cochrane.org/revman-kb/automatic-scd-analyses-358776998.html
- **RM19**: https://documentation.cochrane.org/revman-kb/report-analysis-results-142314014.html
- **RM20**: https://documentation.cochrane.org/revman-kb/ (pages "Summary of findings tables in RevMan" and "Versions of reviews")
- **RM21**: https://documentation.cochrane.org/revman-kb/statistical-methods-210600101.html
- **RM22**: https://www.cochrane.org/products-and-services/review-writing-software
- **RM23**: https://www.cochrane.org/about-us/news/revman-web-cochranes-systematic-review-production-software-now-available-wider-academic
- **RM24**: https://documentation.cochrane.org/revman-kb/supported-hardware-and-browsers-284918055.html

| ID | Cell | Evidence | Source |
| --- | --- | --- | --- |
| D1 | ✓ | Dichotomous data (events/totals); OR, RR, RD formulae for MH, IV and Peto | RM1 |
| D2 | ✓ | Continuous n, mean, SD per group; MD and SMD | RM1 |
| D3 | ✗ | Data package lists four data types: dichotomous, continuous, contrast-level, O–E and variance; no single-arm type | RM2 |
| D4 | ✓ | Contrast-level (generic) data: estimate and SE, SE calculable from a CI | RM1, RM13 |
| D5 | partial | HR via O–E and variance ("Hazard Ratio now works for O-E and Variance analyses", 11.11.0, Oct 2026) or as generic contrast data; no HR-with-CI type | RM3, RM2 |
| D6 | ✗ | No person-time data type among the four; rate ratios only as generic contrast data | RM2 |
| D7 | ✓ | DTA reviews take TP, FP, FN, TN per study | RM4 |
| D8 | ✓ | A review holds many outcomes and analyses | RM5 |
| D9 | ✓ | Study or test covariates "can be continuous or categorical" | RM4, RM6 |
| C1 | partial | Calculator converts SE or CI of group means to SD and supports GIV entry; "not available when analyzing two-by-two data directly" | RM7 |
| C2 | ? | No pre–post correlation input documented; RevMan 5.2 calculator says its formulae do not apply to change scores | RM8 |
| I1 | ✓ | Study data import in CSV (Covidence or extraction templates); JSON also | RM9 |
| I2 | ? | Only CSV and JSON import are named | RM9 |
| I3 | ✓ | "Create review from file": data package or .rm5 (article text not recreated) | RM10 |
| I4 | partial | SVG or PNG download; other formats or resolutions only via support; no PDF or TIFF | RM11 |
| I5 | ✓ | Export ZIP includes analysis and study data as CSV | RM12 |
| A1 | ✓ | Fixed-effect methods available | RM13 |
| A2 | ✓ | Mantel–Haenszel OR/RR/RD and Peto OR | RM1 |
| A3 | partial | REML (default since 2024) and DL; Paule–Mandel not offered | RM13, RM5 |
| A4 | ✓ | Summary CI options HKSJ or Wald (Wald default) | RM5, RM3 |
| A5 | ✓ | "Prediction intervals can optionally be calculated in RevMan" (8.15.0, Jan 2025) | RM13, RM3 |
| A6 | ✓ | Test for subgroup differences, selected by default | RM5, RM1 |
| A7 | ✗ | "Meta-regression … is not implemented in RevMan" | RM13 |
| A8 | ? | Not mentioned in the knowledge base | — |
| A9 | ? | Sensitivity analyses documented only as covariate include/exclude filters | RM6 |
| A10 | partial | Funnel plot with 95% region for fixed-effect analyses only; contours not documented | RM15 |
| A11 | ✗ | "None of the recommended tests for funnel plot asymmetry is implemented in RevMan" | RM14 |
| A12 | ? | Not mentioned | — |
| A13 | partial | SROC with confidence and prediction regions drawn from parameters fitted elsewhere; "These hierarchical models can not be fitted in RevMan" | RM16 |
| A14 | ✗ | Hierarchical DTA models are not fitted in RevMan | RM16 |
| A15 | ? | Not mentioned | — |
| A16 | ✗ | Not mentioned in the knowledge base; author check of the application found no TSA (23 Nov 2026) | Author check |
| A17 | ? | Not mentioned | — |
| A18 | ? | Study-centric data handles multi-arm covariance; no multilevel model documented | RM17 |
| A19 | ? | Not mentioned | — |
| A20 | ? | Not mentioned | — |
| A21 | ? | Handbook discusses selection models without reference to RevMan | RM14 |
| F1 | partial | Sorting, scale, RoB columns and group labels documented; no colour or style presets | RM18, RM3 |
| F2 | ✗ | No meta-regression, so no bubble plot | RM13 |
| F3 | ✓ | Risk-of-bias graph and summary, RoB 2 table beside forest, QUADAS graphs | RM15, RM5 |
| R1 | partial | Results insert into author text as dynamic links; no generated Methods/Results prose; review export to Word/PDF | RM19, RM12 |
| R2 | ✓ | Summary of findings tables in RevMan or linked with GRADEpro GDT | RM20, RM3 |
| P1 | ✓ | Cloud-hosted review stores data and analyses, with versions | RM20, RM23 |
| P2 | ? | No code export documented | — |
| P3 | ? | Formulae published; engine and version not named | RM21 |
| L1 | partial | Paid subscription; free for Cochrane reviews and some sponsored or Research4Life users; pricing page requires login | RM22, RM23 |
| L2 | ✗ | Proprietary software-as-a-service hosted by Cochrane | RM23, RM3 |
| L3 | ✗ | Hosted service only (RevMan 5 is a separate older product) | RM24 |
| L4 | ✓ | "You can use Chrome, Firefox, and newer versions of Edge" | RM24 |

### JASP (Meta-Analysis)

Version checked: JASP 0.99.0 (2026-10-21); jaspMetaAnalysis master `e1cccc46` (2026-11-21, DESCRIPTION 0.99.0). ESC = inst/qml/EffectSizeComputation.qml; FC = FEATURE_COVERAGE.md; menu = inst/Description.qml.

Sources:

- **J1**: https://github.com/jasp-stats/jaspMetaAnalysis/blob/e1cccc4646048ae64ad5383dfa99fb7d85985369/inst/qml/EffectSizeComputation.qml
- **J2**: https://raw.githubusercontent.com/jasp-stats/jaspMetaAnalysis/e1cccc4646048ae64ad5383dfa99fb7d85985369/FEATURE_COVERAGE.md
- **J3**: https://github.com/jasp-stats/jaspMetaAnalysis/blob/e1cccc4646048ae64ad5383dfa99fb7d85985369/inst/Description.qml
- **J4**: https://github.com/jasp-stats/jaspMetaAnalysis/blob/e1cccc4646048ae64ad5383dfa99fb7d85985369/inst/qml/ClassicalMetaAnalysis.qml
- **J5**: https://github.com/jasp-stats/jaspMetaAnalysis/tree/e1cccc4646048ae64ad5383dfa99fb7d85985369/inst/qml/qml_components (ClassicalMetaAnalysisMethod.qml, ClassicalMetaAnalysisStatistics.qml, ClassicalMetaAnalysisAdvanced.qml, ClassicalMetaAnalysisExport.qml, ForestPlotSettings.qml, BubblePlot.qml)
- **J6**: https://github.com/jasp-stats/jaspMetaAnalysis/blob/e1cccc4646048ae64ad5383dfa99fb7d85985369/inst/qml/FunnelPlot.qml
- **J7**: https://github.com/jasp-stats/jaspMetaAnalysis/tree/e1cccc4646048ae64ad5383dfa99fb7d85985369/R (classicalmetaanalysis-model-summary-tables.R:168; classicalmetaanalysis-diagnostics.R:70-87)
- **J8**: https://github.com/jasp-stats/jaspMetaAnalysis/blob/e1cccc4646048ae64ad5383dfa99fb7d85985369/renv.lock
- **J9**: https://github.com/jasp-stats/jasp-desktop/blob/development/Desktop/widgets/filemenu/computer.cpp
- **J10**: https://github.com/jasp-stats/jasp-desktop/tree/development/Desktop/data/importers
- **J11**: https://github.com/jasp-stats/jasp-desktop/blob/development/Desktop/po/jaspDesktop.pot
- **J12**: https://jasp-stats.org/download/
- **J13**: https://github.com/jasp-stats/jasp-desktop/releases/tag/v0.99.0
- **J14**: https://github.com/jasp-stats/jasp-desktop (LICENSE, AGPL-3.0)
- **J15**: Bartoš, Wagenmakers & Viechtbauer 2026, doi:10.1017/rsm.2026.10127 (docs/paper.bib `bartos2026`; not re-read for this check)

| ID | Cell | Evidence | Source |
| --- | --- | --- | --- |
| D1 | ✓ | ESC independent-groups binary: OR, RR, RD (and Peto) from event counts | J1 |
| D2 | ✓ | ESC means, SDs and sample sizes per group; MD, SMD, SMDH, ROM | J1 |
| D3 | ✓ | ESC single group: PR, PLO, PAS, PFT, MN, MNLN | J1 |
| D4 | ✓ | ESC "Reported effect sizes": effect size with SE, variance or 95% CI | J1 |
| D5 | ✗ | No HR measure in the ESC measure list; HR only as a generic estimate | J1 |
| D6 | ✓ | ESC "Counts per time": events and person-time per group; IRR | J1, J2 |
| D7 | ✗ | No diagnostic design in ESC and no DTA analysis in the module menu | J1, J3 |
| D8 | partial | One dataset per .jasp file; outcomes handled by subsetting or the multivariate model | J3, J12 |
| D9 | ✓ | "Predictors" with factors and covariates | J4, J2 |
| C1 | ✓ | ESC fields for t, F, P value, Cohen's d, 95% CI and SE (partial-count completion not checked) | J1 |
| C2 | ✓ | ESC "Repeated measures" with means, SDs and correlation; MC, SMCC, SMCR | J1 |
| I1 | ✓ | File filter includes *.csv, *.txt, *.tsv | J9 |
| I2 | ✓ | "Spreadsheet Files (*.ods *.xls *.xlsx)" | J9, J10 |
| I3 | ✗ | Complete importer list (csv, excel, ods, readstat, rdata, minitab, database, jasp) has no RevMan importer | J10 |
| I4 | ✓ | Plot export PNG, PDF, EPS, 300 dpi TIFF, PPTX, SVG; custom PPI preference | J11 |
| I5 | partial | Output exports as HTML or PDF; tables copy as text or LaTeX; no direct table-to-CSV found | J11, J5 |
| A1 | ✓ | "Equal Effects" and "Fixed Effects" | J5 |
| A2 | ✓ | rma.mh() and rma.peto() implemented | J2 |
| A3 | ✓ | ML, REML, DL, HE, HS, SJ, EB, PM, generalised Q | J5 |
| A4 | ✓ | Knapp–Hartung adjustment is the default; z and t also offered | J4 |
| A5 | ✓ | "Prediction intervals" option | J5 |
| A6 | ✓ | Subgroup variable with tests for subgroup differences | J4, J7 |
| A7 | ✓ | Mixed-effects meta-regression with several predictors | J2 |
| A8 | ✗ | FC lists metafor::cumul() as not implemented | J2 |
| A9 | partial | FC lists leave1out as not implemented as a distinct analysis; influence() casewise diagnostics ship | J2, J7 |
| A10 | ✓ | "Funnel under H₀" with filled 0.90/0.95/0.99 significance regions (read from QML; not labelled "contour-enhanced") | J6 |
| A11 | partial | Egger regression and Begg rank test; no Harbord or Peters option for binary effects | J6, J2 |
| A12 | ✓ | Trim and fill with L0, R0, Q0 estimators | J6 |
| A13 | ✗ | FC lists bivariate DTA (metamisc::riley) as not implemented; no DTA analysis in the menu | J2, J3 |
| A14 | ✗ | No bivariate DTA model (see A13) | J2 |
| A15 | ✗ | No DTA analysis in the module's analysis menu | J3 |
| A16 | ✗ | No TSA in the module's analysis menu (the deprecated Bayesian analysis has Bayesian sequential plots, not TSA) | J3 |
| A17 | ✗ | As A16 | J3 |
| A18 | ✓ | rma.mv() multilevel and multivariate models | J2 |
| A19 | ✓ | RoBMA, NoBMA and BiBMA Bayesian model averaging | J2 |
| A20 | ✗ | No network meta-analysis in the module's analysis menu | J3 |
| A21 | ✓ | selmodel() 3PSM/4PSM, PET, PEESE, PET-PEESE, WAAP-WLS, RoBMA-PSMA | J2 |
| F1 | partial | Axis label, limits, ticks, sizes, black/blue/red colour; no style presets | J5 |
| F2 | ✓ | Bubble plot with prediction intervals | J5 |
| F3 | ✓ | robvis summary and traffic-light plots (RoB 2, ROBINS-I, QUADAS-2) | J2 |
| R1 | ? | Results export as HTML or PDF; no generated Methods/Results prose found | J11 |
| R2 | ✗ | No GRADE or Summary of findings analysis in the module's analysis menu | J3 |
| P1 | ✓ | .jasp file stores data and analyses and reopens them | J10 |
| P2 | ✓ | "Show metafor R code" option | J5 |
| P3 | ✓ | renv.lock pins metafor 5.0-1 and RoBMA 3.6.1 | J8 |
| L1 | ✓ | "Entirely for free, no strings attached" | J12 |
| L2 | ✓ | AGPL-3.0 (module DESCRIPTION says GPL (>= 2)) | J14 |
| L3 | ✓ | Windows, macOS (arm64, x86_64) and Linux (Flatpak) | J13, J12 |
| L4 | ? | No official browser version found | J12 |

### jamovi (MetaJam, MAJOR, OncoPath)

Version checked: jamovi 28.18 (2026-11-08); MetaJam 0.6.0 (last commit 2026-11-20); MAJOR GitHub 1.2.0 (last code commit 2021-05-21; the jamovi library lists 1.2.4, whose source was not found); OncoPath 1.1.4 on GitHub (2026-11-08), library 1.1.2. A module name in brackets says which module supplies the cell.

Sources:

- **JM1**: https://github.com/MetaJam/MetaJam/tree/main/jamovi (metabin.a.yaml, metacont.a.yaml, metaprop.a.yaml, metagen.a.yaml, metainc.a.yaml, metabin.r.yaml, rob.a.yaml)
- **JM2**: https://github.com/MetaJam/MetaJam (README)
- **JM3**: https://github.com/MetaJam/MetaJam/blob/main/DESCRIPTION
- **JM4**: https://github.com/kylehamilton/MAJOR (README, jamovi/*.a.yaml, DESCRIPTION)
- **JM5**: https://github.com/sbalci/OncoPath/blob/master/jamovi/diagnosticmeta.a.yaml
- **JM6**: https://github.com/sbalci/OncoPath/blob/master/R/diagnosticmeta.b.R
- **JM7**: https://www.jamovi.org/modules.html
- **JM8**: https://www.jamovi.org/features.html
- **JM9**: https://www.jamovi.org/releases.html
- **JM10**: https://forum.jamovi.org/viewtopic.php?p=8395
- **JM11**: https://www.jamovi.org/download.html
- **JM12**: https://github.com/jamovi/jamovi/blob/main/LICENSE.md
- **JM13**: https://jamovi.readthedocs.io/en/latest/usermanual/um_1_installation/

| ID | Cell | Evidence | Source |
| --- | --- | --- | --- |
| D1 | ✓ (MetaJam, MAJOR) | metabin: RR, OR, RD from event counts | JM1, JM4 |
| D2 | ✓ (MetaJam, MAJOR) | metacont: means, SDs, n per arm; MD, SMD | JM1, JM4 |
| D3 | ✓ (MetaJam, MAJOR) | metaprop: log, logit, arcsine, Freeman–Tukey; metamean | JM1, JM4 |
| D4 | ✓ (MetaJam) | metagen input "Effect Size & SE" or "Effect Size & CI" | JM1 |
| D5 | ✓ (MetaJam) | metagen measure list includes "Hazard ratio (HR)", SE or CI input | JM1 |
| D6 | ✓ (MetaJam) | metainc: events and time per arm; IRR | JM1 |
| D7 | ✓ (OncoPath) | diagnosticmeta: true/false positives and negatives | JM5 |
| D8 | ✓ (core) | .omv file holds data, many analyses and results | JM8 |
| D9 | ✓ (MetaJam) | Covariates and factors lists for meta-regression | JM1 |
| C1 | ? | No calculator analysis in any of the three modules' option lists | JM1, JM4 |
| C2 | ? | No pre/post correlation option found | JM1, JM4 |
| I1 | ✓ (core) | Opens .csv | JM8 |
| I2 | ✓ (core) | Opens .xlsx | JM8 |
| I3 | ? | Format list ends "and more"; no .rm5 mention | JM8, JM9 |
| I4 | partial (core) | SVG, EPS, PDF export; chosen PNG/TIFF resolution not documented | JM10 |
| I5 | partial (core) | Results export to .docx/.odt and LaTeX; no CSV results export found | JM9 |
| A1 | ✓ (MetaJam, MAJOR) | Common-effect model option | JM1, JM4 |
| A2 | ✓ (MetaJam) | metabin method: inverse variance, Mantel–Haenszel, Peto | JM1 |
| A3 | ✓ (MetaJam, MAJOR) | REML, PM, DL, ML, HS, SJ, HE, EB | JM1, JM4 |
| A4 | ✓ (MetaJam) | "Hartung-Knapp" CI in every analysis | JM1 |
| A5 | ✓ (MetaJam, MAJOR) | "Prediction interval" option | JM1, JM4 |
| A6 | ✓ (MetaJam) | Subgroup variables with subgroup test | JM1 |
| A7 | ✓ (MetaJam) | Several covariates and factors in meta-regression | JM1 |
| A8 | ✓ (MetaJam) | Cumulative meta-analysis with sort order and forest | JM1, JM2 |
| A9 | ✓ (MetaJam) | leaveOneOut with forest plot | JM1 |
| A10 | ✓ (MetaJam, MAJOR) | funnelContour; MAJOR "Contour-Enhanced" | JM1, JM4 |
| A11 | ✓ (MetaJam) | Egger, Begg, Thompson, Harbord, Peters, Macaskill, Schwarzer | JM1 |
| A12 | ✓ (MetaJam) | trimFill with L0/R0 and side | JM1 |
| A13 | ✓ (OncoPath) | mada::reitsma with SROC confidence and prediction regions | JM6 |
| A14 | ✗ | OncoPath meta-regression fits one covariate in separate univariate models for sensitivity and specificity | JM5, JM6 |
| A15 | ✓ (OncoPath) | "Assess publication bias using Deeks' funnel plot test" | JM5 |
| A16 | ✗ | No TSA option in the three modules' option lists; no TSA module in the library | JM1, JM4, JM5, JM7 |
| A17 | ✗ | As A16 | JM7 |
| A18 | ✗ | MAJOR README lists "Multilevel Models (rma.mv)" as unchecked; not in MetaJam | JM4, JM1 |
| A19 | ✗ | No Bayesian analysis in the three modules' option lists | JM4, JM1 |
| A20 | ✗ | No NMA option in the three modules; none in the library | JM7 |
| A21 | partial (MAJOR) | Selection models and p-uniform in mean-difference and correlation analyses only; no PET-PEESE | JM4 |
| F1 | partial (MetaJam) | Forest themes Default, RevMan 5, JAMA, BMJ; labels and limits; no colour options | JM1 |
| F2 | ✓ (MetaJam) | Bubble plot with regression line | JM1 |
| F3 | ✓ (MetaJam) | RoB 2, ROBINS-I, ROBINS-E, QUADAS-2, QUIPS summary and traffic-light plots | JM1 |
| R1 | ? | Results export to .docx; no generated Methods/Results prose found | JM9 |
| R2 | ? | No GRADE or Summary of findings option found | JM1 |
| P1 | ✓ (core) | .omv stores data, analyses, options and results | JM8 |
| P2 | ✓ (core) | "Every analysis shows the exact R code behind it" | JM8 |
| P3 | partial (MetaJam) | DESCRIPTION pins meta to a commit; versions not shown to users; MAJOR unpinned | JM3, JM4 |
| L1 | ✓ (core) | "Desktop is always free" | JM11 |
| L2 | ✓ | jamovi AGPL-3.0 with GPL-2+ components; modules GPL | JM12, JM4 |
| L3 | ✓ (core) | Windows, macOS, Linux (Flathub) | JM13 |
| L4 | partial (core) | jamovi Cloud runs in a browser; availability of these modules there not verified | JM11 |

### CTU TSA 0.9.5.10 Beta

Version checked: CTU Trial Sequential Analysis 0.9.5.10 Beta with its 2017 user manual (Thorlund et al.), checked from a local copy outside this repository. ctu.dk/tsa and /tsa/downloads.aspx returned 404 on 2026-11-23. MN = [trial-sequential-analysis-methods.md](trial-sequential-analysis-methods.md).

Sources:

- **T1**: TSA 0.9.5.10 Beta `TSA manual.pdf` (Thorlund K et al., User manual for Trial Sequential Analysis, Copenhagen Trial Unit 2017), printed page numbers; cited in [trial-sequential-analysis-methods.md:15](trial-sequential-analysis-methods.md)
- **T2**: TSA 0.9.5.10 Beta `license_agreement.pdf`
- **T3**: TSA 0.9.5.10 Beta `samples/High perioperative oxygen SSI.TSA` ([trial-sequential-analysis-methods.md:16](trial-sequential-analysis-methods.md))
- **T4**: [docs/research/trial-sequential-analysis-methods.md](trial-sequential-analysis-methods.md)
- **T5**: [docs/adr/0011-implement-trial-sequential-analysis-over-metafor-and-gsdesign.md](../adr/0011-implement-trial-sequential-analysis-over-metafor-and-gsdesign.md)

| ID | Cell | Evidence | Source |
| --- | --- | --- | --- |
| D1 | ✓ | Events and totals per arm; RD, RR, OR, Peto OR | T1 p.12–13, 64 |
| D2 | partial | Mean, SD, n per arm for MD only; "does not facilitate meta-analysis of SMDs" | T1 p.13; T4:121-123 |
| D3 | ✗ | Only two-arm dichotomous or continuous trials | T1 p.58, 64 |
| D4 | ✗ | Only the two trial input types | T1 p.63–64 |
| D5 | ✗ | "Neither CTU nor RTSA supports HR" | T4:134 |
| D6 | ✗ | No TSA source covers rate outcomes | T4:153; T5:37-39 |
| D7 | ✗ | Outside the two input types | T1 p.58 |
| D8 | ✗ | One meta-analysis per .TSA file | T3; T1 p.62 |
| D9 | partial | Per-trial low/high risk-of-bias flag only | T1 p.64–65 |
| C1 | ✗ | Raw counts or mean/SD/n only | T1 p.64 |
| C2 | ✗ | As C1 | T1 p.64 |
| I1 | partial | RM5Converter reads CSV exported from RevMan 5, dichotomous only | T1 p.60–62 |
| I2 | ? | Not mentioned | — |
| I3 | partial | RevMan data via RevMan CSV export and RM5Converter, dichotomous only | T1 p.60 |
| I4 | ? | "Print current graph" only; no file export documented | T1 p.82 |
| I5 | ? | "Generate TSA Report" exists; format not documented | T1 p.82 |
| A1 | ✓ | Fixed-effect inverse-variance weights | T1 p.15 |
| A2 | partial | Peto OR offered; Mantel–Haenszel not documented | T1 p.13; T4:91 |
| A3 | ✓ | DerSimonian–Laird, Sidik–Jonkman, Biggerstaff–Tweedie | T1 p.16–19, 67 |
| A4 | ✗ | Four models with Wald Z and a normal reference | T1 p.16, 67 |
| A5 | ? | Not documented | — |
| A6 | ✗ | Program has five tabs (Meta-analysis, Trials, TSA, Graphs, Diversity); no subgroup analysis | T1 p.58 |
| A7 | ✗ | As A6 | T1 p.58 |
| A8 | ✓ | Cumulative meta-analysis with cumulative Z-curve | T1 p.34, 81 |
| A9 | partial | Manual "Ignore" checkbox per trial; no automatic leave-one-out | T1 p.65 |
| A10 | ✗ | As A6 | T1 p.58 |
| A11 | ✗ | As A6 | T1 p.58 |
| A12 | ✗ | As A6 | T1 p.58 |
| A13 | ✗ | No DTA data | T1 p.58 |
| A14 | ✗ | As A13 | T1 p.58 |
| A15 | ✗ | As A13 | T1 p.58 |
| A16 | ✓ | Required information size, O'Brien–Fleming alpha spending, non-binding beta-spending futility, law-of-iterated-logarithm penalty | T1 p.24, 37–53 |
| A17 | ✗ | No HR measure | T4:134; T5:32-33 |
| A18 | ✗ | As A6 | T1 p.58 |
| A19 | ✗ | Bayesian methods mentioned only as an alternative approach | T1 p.33 |
| A20 | ✗ | Two-intervention comparisons only | T1 p.58 |
| A21 | ✗ | As A6 | T1 p.58 |
| F1 | ✗ | No forest plot; only the Z-curve and boundary graph | T1 p.81–84 |
| F2 | ✗ | No regression | T1 p.58 |
| F3 | ✗ | Low/high bias flag only | T1 p.64–65 |
| R1 | ? | "Generate TSA Report" contents not documented | T1 p.82 |
| R2 | ✗ | As A6 | T1 p.58 |
| P1 | ✓ | .TSA file stores trials, model, measure and zero-event settings | T1 p.60; T3 |
| P2 | ✗ | GUI only, no scripting | T1 §4 |
| P3 | partial | Formulas given in the manual; closed program, version only | T2 §3; T5:28-31 |
| L1 | ✓ | Free of charge, including commercial use; registration required | T2 §2, §5 |
| L2 | ✗ | Licence forbids alteration, decompilation, derivative works and redistribution | T2 §3; T5:28-31 |
| L3 | ✓ | Java JAR, runs where a JRE is installed | T1 p.55–56 |
| L4 | ✗ | Desktop Java program only | T1 p.55 |

### CMA v4

Version checked: Comprehensive Meta-Analysis v4 as described on meta-analysis.com Wayback snapshots dated January–March 2025 (the live site returned 403 to automated access on 2026-11-23), the Version 3 manual linked from the CMA4 manuals page, and the meta-regression manual. Cells may lag the current v4 build.

Sources:

- **CM1**: https://web.archive.org/web/20250322190635/https://meta-analysis.com/pages/features
- **CM2**: https://web.archive.org/web/20250106020044/https://meta-analysis.com/pages/specs
- **CM3**: https://web.archive.org/web/2026/https://meta-analysis.com/pages/formats
- **CM4**: https://web.archive.org/web/2025/https://meta-analysis.com/pages/version-comparison
- **CM5**: https://web.archive.org/web/20250126161039/https://meta-analysis.com/pages/requirements
- **CM6**: https://web.archive.org/web/20250106020059/https://meta-analysis.com/pages/academic_rates
- **CM7**: https://web.archive.org/web/2026/https://meta-analysis.com/pages/comparisons
- **CM8**: Archived https://meta-analysis.com/download/Meta-Analysis%20Manual%20V3.pdf (Version 3 manual)
- **CM9**: Archived https://meta-analysis.com/download/MRManual.pdf (meta-regression manual)
- **CM10**: https://web.archive.org/web/2026/https://meta-analysis.com/pages/license

| ID | Cell | Evidence | Source |
| --- | --- | --- | --- |
| D1 | ✓ | Events and sample size per group; OR, RR, RD | CM3, CM2 |
| D2 | ✓ | Mean, SD and sample size per group; raw MD, d, g | CM3, CM1 |
| D3 | partial | One-group events/n and mean/SD/n; logit mentioned; arcsine or Freeman–Tukey not documented | CM3, CM9 |
| D4 | ✓ | Point estimate with CI, SE or variance, raw or log scale | CM3 |
| D5 | ✓ | "Hazard ratio and confidence limits; Log hazard ratio and standard error" | CM3 |
| D6 | ✓ | "Events and person years in each group" | CM3 |
| D7 | ✗ | No diagnostic 2×2 format in the complete list of entry formats | CM3 |
| D8 | ✓ | "Multiple outcomes within studies; multiple time-points within outcomes" | CM2 |
| D9 | ✓ | Categorical and continuous moderators | CM1, CM4 |
| C1 | ✓ | Entry formats from P values, t, CIs, chi-squared; "100+ formats" | CM3, CM2 |
| C2 | ✓ | "Means, SD pre and post, N, in each group, Pre/Post Corr" | CM3, CM1 |
| I1 | partial | Import is copy-paste through the clipboard; no CSV file import documented | CM7, CM8 §6 |
| I2 | partial | Excel data copied and pasted, not imported as a file | CM8 §6 p.61 |
| I3 | ? | Specs claim import "from … Revman"; method undocumented | CM2 |
| I4 | partial | Export to Word, PowerPoint, WMF; v3 manual says PDF save not operational; no chosen-resolution raster | CM8 §8, CM2 |
| I5 | ? | Reports export to Word; no CSV export of results found | CM2 |
| A1 | ✓ | Inverse variance | CM2 |
| A2 | ✓ | Mantel–Haenszel and Peto | CM2 |
| A3 | partial | MM, ML, REML only in the meta-regression module | CM9, CM2 |
| A4 | partial | Knapp–Hartung "only implemented … for the meta-regression" | CM9 p.157 |
| A5 | ✓ | Prediction interval on the forest plot | CM2, CM1 |
| A6 | ✓ | "Group by" analysis with between-groups heterogeneity | CM8 §3 |
| A7 | ✓ | Several continuous and categorical covariates (Professional edition) | CM4, CM9 |
| A8 | ✓ | "Cumulative analysis. Runs the analysis k times" | CM2 |
| A9 | ✓ | "Runs the analysis k times, each time removing one study" | CM2 |
| A10 | partial | Funnel plot by precision or SE; contour-enhanced not listed | CM2 |
| A11 | partial | Begg and Egger; Harbord or Peters not listed | CM2, CM8 §10 |
| A12 | ✓ | Duval and Tweedie trim and fill | CM2, CM8 |
| A13 | ✗ | No DTA entry format in the complete format list | CM3, CM2 |
| A14 | ✗ | As A13 | CM3 |
| A15 | ✗ | As A13 | CM3 |
| A16 | ✗ | Not in the specs list of computational options | CM2 |
| A17 | ✗ | As A16 | CM2 |
| A18 | ✗ | Specs list one-group, ANOVA and meta-regression models only | CM2 |
| A19 | ✗ | No Bayesian option in the specs list | CM2 |
| A20 | ✗ | Only "multiple comparisons within studies"; no network model listed | CM2 |
| A21 | ✗ | Publication-bias list: funnel, fail-safe N, Orwin, trim and fill, rank and regression tests | CM2 |
| F1 | ✓ | Every element customisable; templates for formats and colour schemes | CM2 |
| F2 | ✓ | Regression plots of effect size on covariate | CM9 |
| F3 | ? | Not mentioned | — |
| R1 | ✓ | Report of all statistics with references; one-click Word export | CM2, CM7 |
| R2 | ? | Not mentioned | — |
| P1 | partial | Data saved as .cma; storage of analysis settings not documented | CM8 §7 p.74 |
| P2 | ✗ | "CMA is a menu-driven program"; no syntax export | CM7 |
| P3 | partial | Formula shown per row; in-house engine without separate version | CM1 |
| L1 | ✗ | Annual lease, academic US$195–495 per year | CM6 |
| L2 | ✗ | Single named-user licence; no source code | CM10 |
| L3 | partial | Windows 7+ only; Mac via Parallels or Boot Camp | CM5 |
| L4 | ✗ | Requirements list a Windows desktop only | CM5 |

### Stata

Version checked: Stata Release 19 (`[META]` Meta-Analysis Reference Manual, 2025, 509 pp.; `[ADAPT]` Adaptive Designs: Group Sequential Trials Reference Manual, 2025, 252 pp.), checked 2026-11-24. Cells reflect Stata's built-in `meta` suite (`Statistics > Meta-analysis` Meta-Analysis Control Panel) and `[ADAPT]`, not community-contributed SSC or *Stata Journal* commands (`metandi`, `midas`, `metadta`, `metacumbounds`, `network`). Page numbers are the manuals' printed page numbers.

Sources:

- **ST1**: https://www.stata.com/manuals/meta.pdf (`[META]` Stata 19 Meta-Analysis Reference Manual, 2025; individual entries verified at `metaintro.pdf`, `metametaesize.pdf`, `metametaset.pdf`, `metametasummarize.pdf`, `metametaforestplot.pdf`, `metametaregress.pdf`, `metaestatbubbleplot.pdf`, `metametafunnelplot.pdf`, `metametabias.pdf`, `metametatrimfill.pdf`, `metametamvregress.pdf`, `metametameregress.pdf`, `metametamultilevel.pdf`)
- **ST2**: https://www.stata.com/manuals/adapt.pdf (`[ADAPT]` Stata 19 Adaptive Designs: Group Sequential Trials Reference Manual, 2025; `adaptgsdesign.pdf`, `adaptgsbounds.pdf`)
- **ST3**: https://www.stata.com/manuals/dimportdelimited.pdf (`[D] import delimited` / `export delimited`)
- **ST4**: https://www.stata.com/manuals/dimportexcel.pdf (`[D] import excel`)
- **ST5**: https://www.stata.com/manuals/g-2graphexport.pdf (`[G-2] graph export`)
- **ST6**: https://www.stata.com/products/compatible-operating-systems/
- **ST7**: https://www.stata.com/order/

| ID | Cell | Evidence | Source |
| --- | --- | --- | --- |
| D1 | ✓ | `meta esize n11 n12 n21 n22`: `lnoratio`, `lnrratio`, `rdiff`, `lnorpeto` | ST1 p.91–94 |
| D2 | ✓ | `meta esize n1 mean1 sd1 n2 mean2 sd2`: `hedgesg`, `cohend`, `glassdelta2`, `glassdelta1`, `mdiff` | ST1 p.91–95 |
| D3 | partial | `meta esize ns n` supports single-arm proportions (`ftukeyprop`, `logitprop`, `proportion`); no single-arm mean syntax | ST1 p.89, 91–95 |
| D4 | ✓ | `meta set esvar sevar` or `meta set esvar cilvar ciuvar` (with `civarlevel()`) | ST1 p.122–124 |
| D5 | ✗ | No hazard-ratio syntax in `meta esize`; manual directs users to `meta set` for precalculated (log) hazard ratios | ST1 p.22, 89, 91, 122 |
| D6 | ✗ | No person-time input in `meta esize`; `lnrratio` takes 2×2 event/non-event counts | ST1 p.91–94 |
| D7 | ✗ | No TP/FP/FN/TN diagnostic accuracy input in `[META]`; manual cites community-contributed `metandi` instead | ST1 p.20–22, 91 |
| D8 | partial | One active dataset and `meta` declaration per frame (`meta mvregress` handles correlated outcomes, not outcome-tabbed projects) | ST1 p.63, 432 |
| D9 | ✓ | `meta regress` accepts continuous covariates and factor variables (`i.var`) | ST1 p.298–300 |
| C1 | partial | `meta set` derives SE from symmetric CI; `meta esize` computes from group summaries or correlations; no general P-value/t/partial-count calculator in `[META]` | ST1 p.89, 122–124 |
| C2 | ✗ | `meta esize` continuous syntax is two independent groups only; no pre–post correlation option | ST1 p.91 |
| I1 | ✓ | `import delimited` reads CSV and text-delimited files | ST3 |
| I2 | ✓ | `import excel` reads `.xls` and `.xlsx` files | ST4 |
| I3 | ✗ | No RevMan 5 `.rm5` importer in `[META]` or Stata import commands | ST1, ST3, ST4 |
| I4 | ✓ | `graph export` writes PDF, SVG, EPS, PNG and TIFF with configurable width/height | ST5 |
| I5 | partial | `export delimited` / `collect export` export datasets and collected tables; `meta` commands store results in `r()`/`e()` rather than direct CSV table export | ST1 p.238, ST3 |
| A1 | ✓ | `common(invvariance)` and `fixed(invvariance)` | ST1 p.91, 240–241 |
| A2 | ✓ | `common(mhaenszel)` for OR/RR/RD and `esize(lnorpeto)` for Peto OR | ST1 p.92–94, 240–241 |
| A3 | ✓ | `reml` (default), `mle`, `ebayes`, `dlaird`, `sjonkman`, `hedges`, `hschmidt` | ST1 p.240 |
| A4 | ✓ | `se(khartung[, truncated])` and `tdistribution` | ST1 p.195, 240, 299–300 |
| A5 | ✓ | `predinterval` in `meta summarize` and `meta forestplot` | ST1 p.195, 240 |
| A6 | ✓ | `meta summarize, subgroup()` reports `Test of group differences: Q_b` | ST1 p.20, 36–37, 238 |
| A7 | ✓ | `meta regress` fits fixed- and random-effects models with multiple continuous and factor moderators | ST1 p.298–300 |
| A8 | ✓ | `meta summarize, cumulative()` and `meta forestplot, cumulative()` | ST1 p.20–21, 195 |
| A9 | ✓ | `meta summarize, leaveoneout` and `meta forestplot, leaveoneout` | ST1 p.20–21, 195 |
| A10 | ✓ | `meta funnelplot` with `contours()` | ST1 p.21, 337–338 |
| A11 | ✓ | `meta bias`: `egger`, `begg`, `harbord`, `peters` | ST1 p.355–356 |
| A12 | ✓ | `meta trimfill` (linear, run and quadratic estimators) | ST1 p.21, 370–371 |
| A13 | ✗ | No built-in bivariate DTA workflow, SROC curve or confidence/prediction regions in `[META]` (`meta mvregress` is general multivariate meta-regression); bivariate DTA requires user-written commands such as `metandi`, `midas` or `metadta` | ST1 Contents p.i, p.20–22, 432 |
| A14 | ✗ | No built-in bivariate DTA model (see A13) | ST1 Contents p.i |
| A15 | ✗ | `meta bias` lists only `egger`, `harbord`, `peters` and `begg`; no Deeks' DTA test | ST1 p.355–356 |
| A16 | ✗ | No meta-analytic TSA in `[META]`; `[ADAPT]` (`gsdesign`, `gsbounds`) designs single group-sequential clinical trials, not meta-analytic TSA; TSA requires user-written commands such as `metacumbounds` | ST1 Contents p.i; ST2 Contents p.i, p.1–14 |
| A17 | ✗ | No built-in TSA (see A16) | ST1, ST2 |
| A18 | ✓ | `meta meregress`, `meta multilevel` and `meta mvregress` | ST1 p.21, 383, 413, 432 |
| A19 | ✗ | No built-in Bayesian meta-analysis command in `[META]` | ST1 Contents p.i |
| A20 | ✗ | Not in `[META]`; manual acknowledges community-contributed `network` | ST1 Contents p.i |
| A21 | ✗ | `[META]` publication-bias suite covers funnel plots, `meta bias` and `meta trimfill` only | ST1 Contents p.i, p.21 |
| F1 | partial | `meta forestplot` customises columns, labels, colours and graph schemes; no journal-specific forest presets such as BMJ or RevMan | ST1 p.193–196 |
| F2 | ✓ | `estat bubbleplot` after `meta regress` | ST1 p.21, 328 |
| F3 | partial | `meta forestplot, robias()` adds risk-of-bias domain columns (StataNow feature documented in Release 19 manual) | ST1 p.195, 224–225 |
| R1 | ✗ | No generated Methods/Results prose in `[META]` | ST1 Contents p.i |
| R2 | ✗ | Not in `[META]` | ST1 Contents p.i |
| P1 | ✓ | Saved `.dta` files store declared `meta` settings alongside data, plus `.do` scripts | ST1 p.63 |
| P2 | ✓ | GUI actions from the Meta-Analysis Control Panel (`Statistics > Meta-analysis`) echo runnable Stata commands | ST1 p.20, 194 |
| P3 | partial | Proprietary Stata version (`version 19` command); closed-source implementation | ST1 p.2 |
| L1 | ✗ | Commercial paid licence | ST7 |
| L2 | ✗ | Proprietary closed-source software | ST1 p.2 |
| L3 | ✓ | Native desktop installers for Windows, macOS and Linux | ST6 |
| L4 | ✗ | Desktop/server installation; no official browser app | ST6 |

### MetaXL 5.3

Version checked: MetaXL 5.3 (user guide v5.3 entry dated September 2016; product page also says 5.3). Page numbers are the guide's.

Sources:

- **X1**: https://www.epigear.com/index_files/MetaXL%20User%20Guide.pdf
- **X2**: https://www.epigear.com/index_files/metaxl.html

| ID | Cell | Evidence | Source |
| --- | --- | --- | --- |
| D1 | ✓ | NumRR/NumOR/NumRD: N, cases, non-cases per arm | X1 Table 2 p.9 |
| D2 | ✓ | WMD, Cohen, Hedges, Glass from N, mean, SD per arm | X1 Table 2, 5 p.10–12 |
| D3 | partial | Prevalence with none, logit or double-arcsine; no single-group mean input | X1 p.32, Table 2 |
| D4 | ✓ | ContCI/ContSE, ORCI/RRCI/RDCI, RDSE | X1 Table 2 |
| D5 | ✓ | "HRCI: input in hazard ratios and confidence intervals" | X1 Table 2, p.71 |
| D6 | ✓ | RateRatio: person-time and event numbers | X1 Table 2 |
| D7 | ✗ | No DTA type in the complete input-type list | X1 Table 2 |
| D8 | ✓ | "You can have multiple MAInputTable functions in an Excel workbook" | X1 p.9 |
| D9 | partial | Moderators only through an exported meta-regression dataset; subgroups by study lists | X1 p.15–16, 49 |
| C1 | partial | CI or SE input only; no P value or t conversions | X1 Table 2 |
| C2 | ✗ | No pre/post input type in the complete list | X1 Table 2 |
| I1 | partial | Data are Excel ranges; CSV enters through Excel | X1 p.6–7 |
| I2 | ✓ | Runs inside Excel on worksheet ranges | X1 p.6, 9 |
| I3 | ? | Not mentioned | — |
| I4 | partial | Plots saved as EMF (vector) or clipboard; no chosen-resolution PNG/TIFF | X1 p.20 |
| I5 | ✓ | "Results can be saved to comma-delimited file (*.csv)" | X1 p.20 |
| A1 | ✓ | "IV: Inverse variance (fixed effects)" | X1 Table 3 p.10 |
| A2 | ✓ | MH and Peto | X1 Table 3 |
| A3 | ✗ | Random effects is DerSimonian–Laird only (IVhet and quality effects also offered) | X1 Table 3, p.6–7 |
| A4 | ✗ | Not among the six methods (IV, RE, IVhet, QE, MH, Peto) | X1 Table 3 |
| A5 | ? | Not found in the guide | — |
| A6 | partial | Per-subgroup pooled results; no subgroup-difference test documented | X1 p.15 |
| A7 | partial | Exports a meta-regression dataset for Stata; no in-tool regression | X1 p.16, 49, 70 |
| A8 | ✓ | MACumulative | X1 p.13, 70 |
| A9 | ✓ | Sensitivity tab "excludes one by one each study" | X1 p.26 |
| A10 | partial | Funnel plot; contour-enhanced not documented | X1 p.22–23 |
| A11 | ✗ | Feature list offers Doi plot and LFK index, not Egger or Begg | X1 p.6–7, 47 |
| A12 | ✗ | Not in the feature list | X1 p.6–7 |
| A13 | ✗ | No DTA input type | X1 Table 2 |
| A14 | ✗ | As A13 | X1 Table 2 |
| A15 | ✗ | As A13 | X1 Table 2 |
| A16 | ✗ | Not in the feature list | X1 p.6–7 |
| A17 | ✗ | As A16 | X1 p.6–7 |
| A18 | ✗ | Not in the feature list | X1 p.6–7 |
| A19 | ✗ | None offered; guide argues its network method is preferable to Bayesian methods | X1 p.43–46 |
| A20 | partial | MANetwork: chained Bucher indirect comparisons through one common comparator | X1 p.14, 70 |
| A21 | ✗ | Not in the feature list (LFK index only) | X1 p.6–7 |
| F1 | partial | Many plot options saved as personal defaults; no named presets | X1 p.20–21 |
| F2 | ✗ | No in-tool regression | X1 p.49 |
| F3 | ✗ | Quality scores feed the quality-effects model; no RoB table or plot | X1 p.6–7, 37 |
| R1 | ✗ | Output is tables and plots only | X1 p.6–7 |
| R2 | ✗ | Not in the feature list | X1 p.6–7 |
| P1 | ✓ | Data and method live in the saved workbook | X1 p.7, 9 |
| P2 | partial | Analysis is a worksheet formula call; no script export | X1 p.9, 49 |
| P3 | partial | Algorithms referenced; closed add-in with MetaXL version only | X1 p.7, 75 |
| L1 | ✓ | "Price: Free"; "free, but copyrighted software" | X2, X1 p.6 |
| L2 | ✗ | Copyrighted freeware; modification prohibited | X1 p.6 |
| L3 | partial | Excel add-in "only compatible with Windows" | X2 |
| L4 | ✗ | Windows Excel add-in only | X2 |

### Meta-Essentials 1.5

Version checked: Meta-Essentials workbooks 1.5 (download files dated 2025-07); the 1.5 manual's title page lists updates to 1.4 (July 2018). Section numbers are the manual's.

Sources:

- **E1**: https://www.eur.nl/en/erim/media/2025-07-user-manual-15
- **E2**: https://www.eur.nl/en/erim/research-support/meta-essentials/download
- **E3**: https://www.eur.nl/en/erim/research-support/meta-essentials
- **E4**: https://pure.eur.nl/en/publications/introduction-comparison-and-validation-of-meta-essentials-a-free-/ (Suurmond et al. 2017, doi:10.1002/jrsm.1260)

| ID | Cell | Evidence | Source |
| --- | --- | --- | --- |
| D1 | ✓ | Workbook 2: 2×2 cells; OR, RR, RD | E1 §2.1, §4.1.1 |
| D2 | partial | Workbook 3 takes n/mean/SD but outputs only Cohen's d or Hedges' g; raw MD only via generic Workbook 1 | E1 §4.2.1, §2 |
| D3 | ✗ | No single-group workbook among the seven | E1 §2.1, E2 |
| D4 | ✓ | Workbook 1: point estimate and its standard error | E1 §2 |
| D5 | ✗ | No hazard-ratio workbook among the seven | E2, E1 §2 |
| D6 | ✗ | No rate workbook | E2 |
| D7 | ✗ | No DTA workbook | E2 |
| D8 | ✗ | One Input sheet per workbook | E1 §3.1 |
| D9 | partial | One categorical subgroup column and one continuous moderator column | E1 §3.1 |
| C1 | partial | t, F, d/g with n; partial 2×2 completion; no P value or CI conversion | E1 §4.2.1.1, §4.1.1 |
| C2 | ✓ | Workbook 4: dependent groups with pre–post correlation | E1 §4.2.1 |
| I1 | partial | Data pasted into the Excel Input sheet | E1 §3.1 |
| I2 | partial | Excel workbooks; data pasted, no importer | E1 §3.1 |
| I3 | ? | Not mentioned | — |
| I4 | partial | Native Excel charts copied to other programs; no export function | E1 §5 |
| I5 | partial | Results sit in Excel sheets; no export function | E1 §3.6 |
| A1 | ✓ | Fixed effect, inverse variance | E1 §3.2.1, §3.7 |
| A2 | ✓ | Workbook 2: inverse variance, Mantel–Haenszel or Peto | E1 §4.1.2.1 |
| A3 | ✗ | Random effects "based on the DerSimonian-Laird estimator" | E1 §3.7 |
| A4 | ✓ | Weighted-variance (Hartung–Knapp type) CI | E1 §3.7, E4 |
| A5 | ✓ | Prediction interval reported and plotted | E1 §3.2.2 |
| A6 | ✓ | Between-subgroups Q test | E1 §3.3 |
| A7 | ✗ | "Only one moderator … at a time" | E1 §3.4 |
| A8 | ✗ | Not among the manual's sheets | E1 contents |
| A9 | partial | Manual include/exclude per study; no automatic leave-one-out | E1 §3.1 |
| A10 | partial | Funnel plot with CI lines; contour-enhanced not documented | E1 §3.5.1 |
| A11 | partial | Egger and Begg–Mazumdar; no Harbord or Peters | E1 §3.5.2 |
| A12 | ✓ | Duval–Tweedie trim and fill | E1 §3.5.1, §3.7 |
| A13 | ✗ | No DTA workbook | E2 |
| A14 | ✗ | As A13 | E2 |
| A15 | ✗ | As A13 | E2 |
| A16 | ✗ | Not among the sheets | E1 contents |
| A17 | ✗ | As A16 | E1 contents |
| A18 | ✗ | Not among the sheets | E1 contents, E4 |
| A19 | ✗ | Not among the sheets | E1 contents |
| A20 | ✗ | Not among the sheets | E1 contents |
| A21 | ✗ | Publication-bias list ends at funnel, Egger, Begg, Galbraith, quantile plots and fail-safe N | E1 §3.5 |
| F1 | partial | Edited as Excel charts; no presets | E1 §5 |
| F2 | ✓ | Moderator plot with weight-sized points and regression line | E1 §3.4 |
| F3 | ✗ | Not among the sheets | E1 contents |
| R1 | ✗ | Not among the sheets | E1 contents |
| R2 | ✗ | Not among the sheets | E1 contents |
| P1 | ✓ | Saved workbook holds data and option choices | E1 §3.1 |
| P2 | partial | Formulas visible on the Calculations sheet; no script export | E1 §3.6 |
| P3 | partial | Visible Excel formulas; workbook version 1.5 | E1 §3.6, E2 |
| L1 | ✓ | "A free tool for meta-analysis" | E3 |
| L2 | partial | CC BY-NC-SA 4.0 (non-commercial; not an OSI licence) | E2 |
| L3 | partial | Needs Microsoft Excel 2010–2016 or WPS Office; not a standalone application | E1 §1 |
| L4 | partial | Works in Excel Online | E1 §1 |

### Meta-Mar

Version checked: Meta-Mar Classic v4.0.2 (repository release 2026-01-23, last commit `aa1a9dae` 2026-02-19; site pages dated 11 Nov 2026). The repository app.R calls itself a simplified version of the live app, which could not be driven for this check.

Sources:

- **MM1**: https://github.com/mirzafarangi/meta-mar0.4.0.2/blob/main/README.md
- **MM2**: https://github.com/mirzafarangi/meta-mar0.4.0.2/blob/main/paper.md
- **MM3**: https://github.com/mirzafarangi/meta-mar0.4.0.2/blob/main/app.R
- **MM4**: https://www.meta-mar.com/ai-info
- **MM5**: https://www.meta-mar.com/documentation
- **MM6**: https://github.com/mirzafarangi/meta-mar0.4.0.2/blob/main/LICENSE and https://www.meta-mar.com/LICENSE

| ID | Cell | Evidence | Source |
| --- | --- | --- | --- |
| D1 | ✓ | Binary event and total counts; OR, RR, RD | MM1 |
| D2 | ✓ | Continuous n, mean, SD per arm; MD, SMD | MM1, MM3 |
| D3 | ✗ | Classic data types are continuous, binary, correlation and pre-calculated | MM4 |
| D4 | ✓ | Pre-calculated TE and seTE (metagen) | MM1 |
| D5 | partial | HR selectable as the measure for generic TE/seTE input; no HR-with-CI entry | MM3 |
| D6 | ✗ | IRR only as a generic measure; no person-time data type | MM1, MM3 |
| D7 | ✗ | No diagnostic data type in Classic | MM4 |
| D8 | ? | One uploaded file per session; several outcomes not documented | MM1 |
| D9 | ✓ | Meta-regression "accommodates continuous and categorical covariates" | MM2 |
| C1 | ? | Not documented | MM5 |
| C2 | ? | Not documented | MM5 |
| I1 | ✓ | "accepts CSV files or manual data entry" | MM1 |
| I2 | ✓ | File input accepts .xlsx (repository app) | MM3 |
| I3 | ? | Not documented | MM5 |
| I4 | ? | Export formats "Not stated" | MM4 |
| I5 | ? | Not documented | MM4 |
| A1 | ✓ | Fixed-effect inverse variance | MM2 |
| A2 | ✓ | Mantel–Haenszel, inverse variance, Peto for binary data | MM3 |
| A3 | ✓ | REML, DL, PM, ML, EB, SJ, HE, HS | MM1 |
| A4 | ✓ | Hartung–Knapp–Sidik–Jonkman and Kenward–Roger CIs | MM1 |
| A5 | ✓ | Prediction intervals | MM3, MM2 |
| A6 | ✓ | Subgroup analysis with between-group heterogeneity test | MM2 |
| A7 | ✓ | Several covariates joined in metareg | MM3 |
| A8 | ? | Not documented | MM4 |
| A9 | ? | "Sensitivity" analyses listed without method; Baujat plot ships | MM4, MM2 |
| A10 | ✓ | Funnel plots "including contour-enhanced variants" | MM2 |
| A11 | partial | Egger and Begg; Harbord or Peters not documented | MM1 |
| A12 | ✓ | Trim-and-fill | MM1 |
| A13 | ✗ | No DTA data type in Classic | MM4 |
| A14 | ✗ | As A13 | MM4 |
| A15 | ✗ | As A13 | MM4 |
| A16 | ✗ | Not mentioned on the feature page; author check of the application found no TSA (23 Nov 2026) | MM4, author check |
| A17 | ? | As A16 | MM4 |
| A18 | ✗ | "Classic does not provide network, Bayesian, multilevel or individual-participant-data meta-analysis" | MM4 |
| A19 | ✗ | As A18 | MM4 |
| A20 | ✗ | As A18 | MM4 |
| A21 | ? | Only fail-safe N documented beyond funnel, Egger, Begg, trim-and-fill | MM1 |
| F1 | ? | Forest plots ship; editing and presets not documented | MM2 |
| F2 | ✓ | Meta-regression "with bubble plot visualization" | MM2 |
| F3 | ? | Not documented | MM5 |
| R1 | partial | Optional AI-written reports (OpenAI); content and Word/PDF export not documented | MM4 |
| R2 | ? | Not documented | MM5 |
| P1 | ✗ | Session-only storage; data deleted when the session ends | MM2 |
| P2 | ? | Not documented | MM5 |
| P3 | partial | Engine named (meta, metafor); versions not pinned in install instructions | MM1 |
| L1 | ✓ | "Free. No account, no tokens, no paid plans." | MM4 |
| L2 | partial | Repository LICENSE is MIT; website says AGPL-3.0 | MM6 |
| L3 | ✗ | Shiny chosen "over desktop deployment"; local use only by running R | MM2 |
| L4 | ✓ | Browser app at meta-mar.com | MM1 |

### MetaDTA / Meta-DiSc 2.0

Version checked: MetaDTA v2.1.5 (commit `b3b90ab1`, 2024-11-19); Meta-DiSc 2.0 source zip released 2022-11-04. Both are DTA-only web apps, so rows outside DTA are ✗ by scope. A name in brackets says which app supplies the cell. Where noted "source", absence was established by searching the app's full source, not by a documentation statement.

Sources:

- **DT1**: https://github.com/CRSU-Apps/MetaDTA (README; R/data_page.R, R/analysis_page.R, R/sensititvity_page.R, R/home_page.R)
- **DT2**: Plana MN et al. Meta-DiSc 2.0. BMC Med Res Methodol 2022; doi:10.1186/s12874-022-01788-2 (https://pmc.ncbi.nlm.nih.gov/articles/PMC9707040/)
- **DT3**: https://sourceforge.net/projects/metadisc/files/ (Meta-DiSc 2.0 source: server.R, ui.R, funciones_050922.R, packrat.lock)
- **DT4**: https://github.com/CRSU-Apps/MetaDTA/blob/master/LICENSE

| ID | Cell | Evidence | Source |
| --- | --- | --- | --- |
| D1 | ✗ | DTA-only apps; input is TP, FP, FN, TN | DT1, DT2 |
| D2 | ✗ | As D1 | DT1, DT2 |
| D3 | ✗ | As D1 | DT1, DT2 |
| D4 | ✗ | As D1 | DT1, DT2 |
| D5 | ✗ | As D1 | DT1, DT2 |
| D6 | ✗ | As D1 | DT1, DT2 |
| D7 | ✓ (both) | Required columns TP, FN, FP, TN | DT1, DT2 |
| D8 | ✗ | One 2×2 dataset per upload; Meta-DiSc "does not allow comparing the accuracy of two diagnostic tests" | DT2 |
| D9 | partial | MetaDTA covariates are shown on the SROC only; Meta-DiSc 2.0 takes dichotomous covariates one at a time | DT1, DT2 |
| C1 | ✗ | As D1 | DT1, DT2 |
| C2 | ✗ | As D1 | DT1, DT2 |
| I1 | ✓ (both) | .csv upload | DT1, DT2 |
| I2 | ✓ (both) | .xlsx upload | DT1, DT2 |
| I3 | ✗ | Upload accepts only .csv and .xlsx (source) | DT1, DT3 |
| I4 | partial | MetaDTA PNG/PDF, Meta-DiSc PNG/SVG, fixed size and resolution (source) | DT1, DT3 |
| I5 | ✓ (both) | Download Table buttons write CSV | DT1, DT3 |
| A1 | ✗ | Random-effects bivariate and univariate DTA models only | DT2 |
| A2 | ✗ | As D1 | DT2 |
| A3 | ✗ | Models fitted by ML with glmer; no τ² estimator choice | DT2 |
| A4 | ✗ | As D1 | DT2 |
| A5 | partial (both) | 95% prediction region of the bivariate model only | DT1, DT2 |
| A6 | ✓ (Meta-DiSc 2.0) | Subgroup bivariate model with likelihood-ratio comparison | DT2 |
| A7 | ✗ | Meta-DiSc 2.0 takes one dichotomous covariate at a time; MetaDTA has no meta-regression | DT2, DT1 |
| A8 | ✗ | No cumulative analysis (source) | DT1, DT3 |
| A9 | partial (MetaDTA) | Sensitivity page refits on hand-picked studies | DT1 |
| A10 | ✗ | As D1 | DT2 |
| A11 | ✗ | As D1 | DT2 |
| A12 | ✗ | As D1 | DT2 |
| A13 | ✓ (both) | glmer bivariate model; SROC with summary point, 95% confidence and prediction regions | DT1, DT2 |
| A14 | partial (Meta-DiSc 2.0) | One dichotomous covariate in the bivariate model, equal between-study variances assumed | DT2 |
| A15 | ✗ | No Deeks test (source) | DT1, DT3 |
| A16 | ✗ | Outside DTA scope | DT2 |
| A17 | ✗ | Outside DTA scope | DT2 |
| A18 | ✗ | Outside DTA scope | DT2 |
| A19 | ✗ | Neither app is Bayesian (the separate CRSU app MetaBayesDTA is not in this column) | DT1 |
| A20 | ✗ | Outside DTA scope | DT2 |
| A21 | ✗ | Outside DTA scope | DT2 |
| F1 | partial | Sensitivity and specificity forest plots; no appearance editing or presets (source) | DT1, DT3 |
| F2 | ✗ | No bubble plot (source) | DT1, DT3 |
| F3 | ✓ (MetaDTA) | QUADAS-2 judgements shown on the SROC | DT1 |
| R1 | ✗ | No report generator (source) | DT1, DT3 |
| R2 | partial (Meta-DiSc 2.0) | "Summary of findings" gives TP/FP/FN/TN for a chosen prevalence; no GRADE table | DT2 |
| P1 | ✗ | No save or load of analyses (source) | DT1, DT3 |
| P2 | ✗ | No code export (source) | DT1, DT3 |
| P3 | ✓ (Meta-DiSc 2.0) | packrat.lock pins R 4.1.1 and lme4 1.1-27.1 | DT3 |
| L1 | ✓ (both) | Free; Meta-DiSc has "no restrictions to use by non-academics" | DT2 |
| L2 | ✓ (both) | MetaDTA GPL-3.0; Meta-DiSc 2.0 GPLv3 | DT4, DT2 |
| L3 | ✗ | Web apps; local use only by running the R source | DT2 |
| L4 | ✓ (both) | crsu.shinyapps.io/MetaDTA; www.metadisc.es | DT1, DT2 |

### OpenMeta[Analyst]

Version checked: OpenMeta[Analyst] GitHub master `e3147cab` (2020-07-28); last code change 2016-06-05; no tagged releases; Python 2.7, PyQt4, R 3.x. RC MetaStudio is a rewrite of this program; this column describes the original only. Where noted "source", absence was established by searching the repository source.

Sources:

- **O1**: https://github.com/bwallace/OpenMeta-analyst-/tree/master/src (meta_globals.py, main_wizard.py, ma_data_table_model.py, ma_data_table_view.py, ui_meta.py, meta_form.py, results_window.py, continuous_data_form.py, calculator_routines.py, meta_py_r.py, forms/)
- **O2**: https://github.com/bwallace/OpenMeta-analyst-/tree/master/doc (data_types.html, analysis_methods.html, random-effects_methods.html, subgroup_analysis.html, regression.html, cumulative_analysis.html, leave_one_out_analysis.html, diagnostic_only_methods.html, plot_options.html, covariate.html)
- **O3**: https://github.com/bwallace/OpenMeta-analyst-/tree/master/src/R/openmetar (R/*.r, DESCRIPTION)
- **O4**: https://github.com/bwallace/OpenMeta-analyst-/blob/master/README.txt
- **O5**: https://web.archive.org/web/2019/http://www.cebm.brown.edu/openmeta/

| ID | Cell | Evidence | Source |
| --- | --- | --- | --- |
| D1 | ✓ | Binary two-arm OR, RD, RR | O1 meta_globals.py |
| D2 | ✓ | Continuous N/mean/SD per arm; MD, SMD | O2 data_types.html |
| D3 | ✓ | One-arm proportions (raw, log, logit, arcsine, Freeman–Tukey) and one-arm mean | O1 meta_globals.py |
| D4 | ✓ | Generic effect with effect and SE | O1 main_wizard.py |
| D5 | ✗ | Data types binary, continuous, diagnostic only | O2 data_types.html |
| D6 | ✗ | No person-time data type | O2 data_types.html |
| D7 | ✓ | TP, FN, FP, TN | O2 data_types.html |
| D8 | ✓ | Several outcomes and follow-ups in one .oma file | O1 ui_meta.py |
| D9 | ✓ | Factor and continuous covariates | O2 covariate.html |
| C1 | ✓ | Effect from CI, SE, variance, P value; back-calculation of partial 2×2 tables | O1 forms, calculator_routines.py |
| C2 | partial | Pre/post correlation fields exist but are hidden for SMD | O1 continuous_data_form.py |
| I1 | ✓ | CSV import in the wizard and menu | O1 main_wizard.py |
| I2 | ✗ | No .xlsx import; tables pasted from Excel (source) | O1 ma_data_table_view.py |
| I3 | ✗ | Only .oma open and CSV import (source) | O1 meta_form.py |
| I4 | partial | PDF or PNG save; fixed PNG resolution | O1 results_window.py |
| I5 | partial | Plain-text results copied by select-all; no CSV export | O1 results_window.py |
| A1 | ✓ | Fixed-effect inverse variance | O2 analysis_methods.html |
| A2 | ✓ | Mantel–Haenszel and Peto | O2 analysis_methods.html |
| A3 | ✓ | HE, DL, SJ, ML, REML, EB | O2 random-effects_methods.html |
| A4 | ✗ | No Knapp–Hartung option in GUI parameters (source) | O3 |
| A5 | ✗ | No prediction interval (source) | O3 |
| A6 | partial | Pooled result per subgroup; no subgroup-difference test | O3, O2 subgroup_analysis.html |
| A7 | ✓ | Several factor and continuous covariates, fixed or random | O1 forms, O2 regression.html |
| A8 | ✓ | Cumulative meta-analysis for binary, continuous, diagnostic data | O2 cumulative_analysis.html |
| A9 | ✓ | Leave-one-out meta-analysis | O2 leave_one_out_analysis.html |
| A10 | ✗ | No funnel plot in the GUI (source) | O3 |
| A11 | ✗ | No small-study tests (source) | O3 |
| A12 | ✗ | No trim-and-fill (source) | O3 |
| A13 | partial | Bivariate ML model (lme4) with SROC curve; no confidence or prediction regions | O3 bivariate.r, O2 diagnostic_only_methods.html |
| A14 | ✗ | Diagnostic meta-regression on sensitivity, specificity or DOR separately | O1 forms |
| A15 | ✗ | No Deeks test (source) | O3 |
| A16 | ✗ | No TSA (source) | O3 |
| A17 | ✗ | No TSA (source) | O3 |
| A18 | ✗ | No multilevel models (source) | O3 |
| A19 | partial | Bayesian HSROC for DTA only (Gibbs sampler) | O2 diagnostic_only_methods.html |
| A20 | ✗ | "view network" draws the arm graph only; no NMA model | O1 meta_py_r.py |
| A21 | ✗ | No selection models (source) | O3 |
| F1 | partial | Column labels, axis label, ticks and bounds editable; no colours or presets | O2 plot_options.html |
| F2 | partial | Regression plot only with one continuous covariate and no factors | O2 regression.html |
| F3 | ✗ | No risk-of-bias feature (source) | O1 |
| R1 | ✗ | No report generator (source) | O1 |
| R2 | ✗ | No GRADE or SoF (source) | O1 |
| P1 | ✓ | Saves .oma dataset and .state file and reopens both | O1 meta_form.py |
| P2 | ✗ | No code export (source) | O1 |
| P3 | partial | Engine named (metafor, lme4, openmetar); README gives "metafor 1.6.0ish" | O4 |
| L1 | ✓ | Free binaries; AHRQ-funded | O5 |
| L2 | partial | openmetar DESCRIPTION says GPL (>= 2); repository has no LICENSE file | O3 |
| L3 | ✓ | Windows 7/8 64-bit and macOS 10.10 binaries; Linux from source | O5, O4 |
| L4 | ✗ | Desktop PyQt4 application | O4 |
