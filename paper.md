---
title: 'RC MetaStudio: open-source desktop software for meta-analysis'
tags:
  - meta-analysis
  - evidence synthesis
  - systematic review
  - graphical user interface
  - Python
  - R
# DRAFT, NOT FOR SUBMISSION. Author list and affiliations are copied from
# CITATION.cff on 17 November 2026 with provisional approval from Ali Salman.
# Each co-author's consent, contribution, current affiliation, ORCID, funding
# and conflicts are unconfirmed. See artifacts/planning/joss/writing/claims.md
# and artifacts/planning/joss/writing-revision/claims.md.
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
date: 17 November 2026
bibliography: docs/paper.bib
---


**Working draft for author review.** Research-use evidence, author metadata and
the AI disclosure are incomplete. This paper is not ready for submission.

# Summary

A meta-analysis combines the results of several studies of the same question
into one estimate with its uncertainty. It is the quantitative core of many
systematic reviews in medicine and other fields. RC MetaStudio is a free,
open-source desktop application for Windows, Apple silicon macOS and Linux
(Ubuntu 24.04) in which researchers run meta-analyses without writing code. A
user types or pastes study data into spreadsheet-like outcome sheets, chooses
an effect measure and a model from menus, and runs the analysis. Supported data
are binary, continuous and diagnostic accuracy outcomes, reported hazard
ratios, and incidence rate ratios. The analyses are standard, cumulative,
leave-one-out, subgroup, meta-regression and small-study-effects analyses, and
bivariate models of diagnostic accuracy. Results appear as tables, as editable
forest, funnel, bubble and summary receiver operating characteristic plots, and
as Methods and Results text that exports to PDF or Word. Meta-analytic
estimation and inference come from the established R packages metafor
[@viechtbauer2010], meta [@balduzzi2019] and mada [@doebler2025mada], which the
application calls rather than reimplements. Its own calculators derive study
effects and standard errors from reported statistics.

# Statement of need

People who carry out systematic reviews include clinicians, students and other
researchers whose training is in their subject rather than in statistical
programming. For these researchers, the software decides which methods they can
use. The R packages metafor and meta implement a wide range of current
meta-analysis methods, but using them means writing R code. @wallace2012
described that requirement as a deterrent to non-technical users and proposed
graphical software over R to bring methodologists' work to applied reviewers.

RC MetaStudio is for researchers who are comfortable with a spreadsheet and
want to take a meta-analysis from study data to figures and report text in one
free application. This paper reports no usability evaluation, so the following
are design goals, not measured properties. The same application should serve a
first pooled estimate and a more advanced analysis, such as a meta-regression
or a bivariate diagnostic model. Data should go in as studies report them,
whether as event counts or as a ratio with its confidence interval. Methods
should be chosen from menus and run with the package's defaults. Figures should
be editable to a journal's requirements. The report should state which method
and package produced each number.

# State of the field

Researchers who do not write R have had three kinds of graphical software. The
first is Cochrane's review software. Review Manager (RevMan) is now
subscription web software, free for authors of Cochrane Reviews and free,
discounted or sponsored for some other users [@cochrane2023revmanweb;
@cochranekb]. Its desktop edition, RevMan 5, is no longer supported
[@cochranestyle], and in 2022 Cochrane announced that its downloads would end
on 25 April 2023 [@cochrane2022digest]. The second is a general statistics program that offers
meta-analysis as one analysis among many. JASP's meta-analysis module is a
graphical interface to metafor. It covers random-effects models,
Mantel–Haenszel and Peto methods, subgroup analysis, meta-regression,
multilevel models, publication-bias tests, and forest and funnel plots, and it
can show the equivalent metafor code [@bartos2026]. jamovi lists several
meta-analysis modules [@jamovimodules]. MAJOR is an interface to metafor.
MetaJam is built on meta, and its listed analyses include cumulative,
leave-one-out, subgroup and meta-regression analyses. OncoPath lists bivariate
diagnostic accuracy models. The third is a dedicated meta-analysis application.
OpenMeta[Analyst] put a Python interface over an R engine so that new methods
written in R could reach end users [@wallace2012].

The free tools' analyses overlap substantially with RC MetaStudio's, and JASP
documents multilevel and multivariate models [@bartos2026] that RC MetaStudio
does not offer. The difference is in how the software is organized. JASP and
jamovi apply an analysis to a data set inside a general statistics program. RC
MetaStudio is organized around outcome sheets. Each sheet holds one outcome,
each row is a study with named arms where applicable, and each study keeps the
input the user entered, such as event counts or a reported hazard ratio with
its confidence interval. Data can also be imported from Excel, CSV or RevMan 5
files. We present no evidence that either arrangement serves users better.

RC MetaStudio is an independent project derived from OpenMeta[Analyst], whose
code it rewrites and maintains separately. The upstream repository targets
Python 2.7, PyQt4 and R 3.x and was last changed in July 2020 [@openmetarepo].
That history belongs to OpenMeta[Analyst]. RC MetaStudio's own public history
begins with its repository and releases in 2026. Python 2.7 reached end
of life in 2020 [@pep373]. The project rewrote the application on current
Python, PyQt6 [@pyqt6] and R [@rcore2026] and kept the separation between
interface and R engine. We chose a standalone application over a JASP or jamovi
module because the outcome-sheet data model, the calculators that derive study
effects from reported statistics, and the report generator are the product. We
judged them simpler to build as one application than inside a program organized
around a different kind of data set. [Authors to confirm this rationale.] The
project therefore adds a review-shaped workspace and no meta-analytic
estimators of its own.

# Software design

The central decision is where the application stops and the statistics begin.
RC MetaStudio draws that line at estimation. Each supported model is fitted by
a function in metafor, meta or mada, such as `rma.uni`, `metabin`, `metabias`,
or `reitsma` for the bivariate model of @reitsma2005. Cumulative, leave-one-out
and subgroup analyses refit those models on subsets of studies. The application
validates inputs, calls the package and presents its result, keeping the
package's estimators, numbers and defaults unless the user changes a setting. A
bundled R package, RCMetaR, holds these calls, so package details stay on the R
side of the boundary. RCMetaR also holds the calculators, which derive a
study's effect and standard error from statistics such as a confidence interval
or P value with the project's own code. The cost is that the application cannot offer a method the
packages lack, and a package update or a changed default can change results.
Earlier releases also departed from some package defaults. The unreleased
version 0.5.6 fixes these departures in the application, including restricted
maximum likelihood as the random-effects default and metafor's exclusion of
double-zero studies in Peto analyses; no package was updated for them. The
latest release, 0.5.5, lacks these fixes. [Authors to cite the release that
contains them before submission.] In return, a reader can check
an estimate against a direct call to the named package. The project's numerical
checks compare results with frozen outputs from an earlier release and with
direct calls to public package functions, and reports list method references
and the implementing package.

The interface is written in Python with PyQt6 and calls R in the same process
through rpy2 [@rpy2]. Python and R exchange immutable requests and versioned,
structured results whose tables can carry exact numeric values beside their
display strings, so the numeric CSV export never parses formatted text.

Releases bundle a private R runtime and R packages pinned in a dependency
manifest, so users need no R installation and the manifest records the package
versions behind each release. The cost is that every package update must be
rebuilt and qualified by the maintainers before users receive it. If R cannot
start, the application stops with an error rather than continuing with a
substitute back end.

A project is saved as an `.rcms` file, a ZIP archive of three JSON documents
checked against packaged schemas. Saves are atomic, and the same content always
produces the same file. A project stores data and analysis settings but not
results. Saved files therefore do not depend on result formats or package
output, and reopening a project means running the analysis again. An exported
report or figure is the record of a particular run.

Plots are drawn by R as vector graphics. The plot editor changes labels,
captions, colors, axis limits, study order and which elements are shown. R then
redraws the figure from the result instead of editing an image, so these edits
change presentation, not the fitted model. Figures export as PDF, PNG, SVG or
TIFF. The text report combines the model output with the dataset and analysis
configuration that produced it, as Methods and Results text, tables and
numbered references. In this design, the application's own code is the review
workflow around each fit, from data entry and settings to figures and report
text.

# Research impact statement

**Draft flag.** This section is incomplete and must not be submitted as
written. JOSS requires evidence that the software is used for research, at
minimum by its developers. Collecting that evidence has been deferred, and this
draft reports none.

What exists now shows availability and reproducibility, not use. RC MetaStudio
has a public repository with versioned releases since July 2026, a concept DOI
that resolves to the latest release [@rcmetastudio], an issue tracker, and
sample projects with binary, continuous, diagnostic, hazard-ratio and
incidence-rate-ratio data. A tutorial accompanying this working draft pairs the
BCG vaccine sample with an R script that checks the sample's counts against the
published data set and fits the same model with metafor, so a reader can
compare the two estimates. [Authors to replace this description with a link to
the released tutorial.] [Authors to add verifiable research uses, such as
published or submitted reviews that used RC MetaStudio, with permission.]

# AI usage disclosure

**Draft flag.** Authors must confirm and complete this statement, including
tool versions, before submission.

Generative AI coding agents were used for code, tests, documentation and design
reviews. OpenAI Codex agents carried out implementation work and the factual
revision of this paper's first draft. Claude Opus 5.5, used through T3 Code,
wrote this paper's first draft from the repository and the cited sources,
reviewed it in a separate session, and researched and wrote this revision.
[Authors to name the tools and versions used across the project's history, to
state how they reviewed and validated AI-assisted code, documentation and this
text, and to confirm that humans made the core design decisions.]

# Acknowledgements

We thank the authors of OpenMeta[Analyst], on whose work RC MetaStudio builds,
and the authors of metafor, meta and mada. RC MetaStudio is not affiliated with
or endorsed by the original OpenMeta[Analyst] authors or their institutions.
[Authors to state funding, or that there was none, and any conflicts of
interest.]

# References
