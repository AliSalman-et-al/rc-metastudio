# Results design review (Opus 5.5 High), 15 November 2026

Status: independent research and design only. No product code, tests, GUI runs or commits.
The reconciled implementation decisions are in [results-presentation-2026-11-15.md](results-presentation-2026-11-15.md#reconciled-decisions-after-opus-review). Recommendations below are the reviewer’s proposals, not a record of accepted product changes.
Branch `ui/desktop-polish-and-icons` at `27f37313`. The evidence comes from
the current source and the native run
[`20261115T105214Z-02d68633-ui-fine-tuning`](../artifacts/verification/rcms/20261115T105214Z-02d68633-ui-fine-tuning/).
This review was written independently of
[results-presentation-2026-11-15.md](results-presentation-2026-11-15.md), which
appeared while it was in progress. Section 8 records where the two documents
agree and where they differ.

## 1. Verdict

The main weakness of Results is not its layout. **The same number appears
inconsistently across surfaces.** One pooled odds ratio and its P value pass
through at least four formatters: R's table formatter, R's forest annotation,
the Python manuscript layer and the Text report column rewriter. Each formatter
has its own rules. In one result the user sees `P = 0.015` on the forest plot,
`p = .015` in the manuscript prose, `.015` in Model fit and `0.015` in
Supplementary details. One code path also adds precision that the source never
had. A researcher who copies a number into a paper cannot tell which form is
authoritative.

Results is RCMS's core value only if it gives one auditable account of an
executed analysis, in which every surface agrees: the screen, the figure, the
clipboard, CSV, DOCX and PDF. The first job is therefore to make the surfaces
agree. A new layout comes after that.

The current stack is adequate for this: Qt widgets, `QTextDocument`,
python-docx, `QPdfWriter` and R-rendered figures. The weak point is the
boundary contract. It carries display strings, and Python reverse-engineers
their meaning from titles and regular expressions (Section 5). No web stack or
new dependency is needed.

## 2. What the sources establish

Each source is classified as a **journal rule**, a **structural model** or a
**product precedent**. None is treated as a universal style guide.

| Source | Kind | What it establishes | What it does *not* establish |
| --- | --- | --- | --- |
| [JAMA Instructions for Authors](https://jamanetwork.com/journals/jama/pages/instructions-for-authors) | Journal rule | Report estimates with uncertainty and reproducible methods. P conventions use three decimals below .01, two from .01 upward, and bounds below .001 or above .99. Meta-analysis prose avoids causal claims. Submission tables use editable cells and readable type; figures disclose units, uncertainty and scales. | A universal software style. RCMS should adopt individual conventions for explicit product reasons. |
| [Cochrane Handbook ch. 10](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-10) | Methods guidance | §10.11.3.1: "It is a mistake to compare within-subgroup inferences such as P values"; use a formal test. §10.10.2 gives overlapping I² ranges. §10.10.4.2: the CI "does not describe the degree of heterogeneity"; prediction intervals present variability. | Formatting. |
| [Wickham, Tidy Data, JSS 59(10)](https://www.jstatsoft.org/article/view/v059i10) (full PDF read) | Structural model | Separate variables, observations and observational units (§2.3). The paper discusses combined fields, reshaping and linked tables, while recognizing useful presentation layouts that differ from tidy storage. | A requirement that every screen table use a tidy export layout. |
| [broom](https://broom.tidymodels.org/) and the [tidier developer guide](https://www.tidymodels.org/learn/develop/broom/) | Structural model | `tidy()` returns one row per model component; `glance()` returns "a one-row tibble providing model-level summarizations"; `augment()` returns one row per observation. Column names are lowercase, such as `term`, `estimate`, `std.error`, `statistic` and `p.value`. "If a summary metric … is not defined … use `NA`." | Any rounding or display rule. broom keeps numbers numeric; its printed digits are tibble printing, not guidance. |
| [easystats report](https://easystats.github.io/report/) and [report_table](https://easystats.github.io/report/articles/report_table.html) | Product precedent | One report object yields narrative, a table and a summary. `report_table()` "prettifies the printing", while `as.data.frame()` keeps raw `CI_low`/`CI_high` and full-precision p. The narrative labels effects "statistically significant" and uses Cohen/Field magnitude adjectives. | A wording model for RCMS. Its automatic significance and magnitude labels are exactly what a meta-analysis report should not generate. |
| JASP: [R analyses guide](https://github.com/jasp-stats/jasp-desktop/blob/development/Docs/development/r-analyses-guide.md), [`utils.js` formatColumn](https://github.com/jasp-stats/jasp-desktop/blob/development/Desktop/html/js/utils.js) (commit `3302d1a`), [`table.js`](https://github.com/jasp-stats/jasp-desktop/blob/development/Desktop/html/js/table.js), [jaspMetaAnalysis helpers](https://github.com/jasp-stats/jaspMetaAnalysis/blob/master/R/classicalmetaanalysis-helpers.R) (commit `94b8bdb`) | Product precedent (first-party source) | R sends **raw numbers plus a column format** (`type = "number"|"integer"|"pvalue"`, `format = "sf:4;dp:3"`, `"dp:3;p:.001"`). The client formats a **whole column at once**: for `sf`, it finds the column's least significant digit, so the column shares one decimal position. P drops the leading zero and becomes `< .001` below the bound. Global user preferences cover fixed decimals, exact P and ×10ⁿ notation. Footnotes attach to cells, rows or columns. The display uses `&minus;`, and HTML copy converts U+2212 back to `-`. Meta-analysis tables show **"95% CI" and "95% PI" as separate overtitled Lower/Upper pairs** in the same estimates table. | That RCMS needs JASP's web renderer. The mechanism is R-numbers-in, client-format-out, and it maps onto Qt. |

## 3. Observed defects, ordered by scientific risk

Every row cites a capture or code. "Observed" means visible in the retained
run. "Code" means readable in the source but not exercised in that run.

| ID | Severity | Finding | Evidence |
| --- | --- | --- | --- |
| R1 | **High, observed** | **Fabricated precision.** `_presentation_cell` re-rounds every decimal it finds to `manuscript_digits`. When R has already formatted to 4 significant figures, this *pads with zeros*: `10.51 (SE 42.59; 95% CI -80.26 to 101.3)` becomes `10.510 (SE 42.590; 95% CI -80.260 to 101.300)`. The same export then shows both versions. It also changes `-0.8605` to `-0.860` while the supplement keeps `-0.8605`. | [43-report.txt](../artifacts/verification/rcms/20261115T105214Z-02d68633-ui-fine-tuning/43-report.txt) (Model fit vs Supplementary details). [manuscript_report.py:369](../src/rc_metastudio/manuscript_report.py#L369) |
| R2 | **High, observed** | **Four P notations in one result.** Forest: `P = 0.015`, `P = 0.267`. Manuscript prose: `p = .015`. Model fit: `.015`. Text report supplement: header `P`, value `0.015`. Small-study output: `p = 0.609` and R's `< 0.001` against Python's `< .001`. | [26-report.txt](../artifacts/verification/rcms/20261115T105214Z-02d68633-ui-fine-tuning/26-report.txt); [forest capture](../artifacts/verification/rcms/20261115T105214Z-02d68633-ui-fine-tuning/26-0-analysis-results-bottom.png). Formatters: [manuscript_report.py:52](../src/rc_metastudio/manuscript_report.py#L52), [results_window.py:1762](../src/rc_metastudio/results_window.py#L1762), [display.R:74](../r/RCMetaR/R/display.R#L74), [small_study_effects.R:1019](../r/RCMetaR/R/small_study_effects.R#L1019), [plotting.R:10](../r/RCMetaR/R/plotting.R#L10), [forest_style_revman.R:227](../r/RCMetaR/R/forest_style_revman.R#L227) |
| R3 | **High, observed** | **Automatic significance verdicts.** The small-study output prints `Result: No clear evidence of small-study effects (p = 0.609)`, or "Evidence of small-study effects" whenever `p < .05`. Nobody configured that alpha. The verdict is generated in two places. | [small_study_effects.R:574](../r/RCMetaR/R/small_study_effects.R#L574), [:910](../r/RCMetaR/R/small_study_effects.R#L910); 43-report.txt |
| R4 | **High, code** | **CI classification from rounded strings.** `_interval_meaning` parses the *displayed* bounds and writes either "excludes 1, with lower odds … in A than in B" or "includes 1, so these data do not show a clear difference". At three decimals, an upper bound of 0.9996 displays as `1.000` and gets classified as "includes 1". The sentence is also a dichotomous significance reading in prose form. | [manuscript_report.py:78–107](../src/rc_metastudio/manuscript_report.py#L78); visible in [28-0 manuscript](../artifacts/verification/rcms/20261115T105214Z-02d68633-ui-fine-tuning/28-0-polish-manuscript-light.png) |
| R5 | High, code | **Per-subgroup P in manuscript prose.** Each subgroup sentence carries its own `z` and `p`, which invites the within-group comparison that Cochrane §10.11.3.1 calls a mistake. The test for subgroup differences sits in a separate Model fit row. | [manuscript_report.py:218–234](../src/rc_metastudio/manuscript_report.py#L218), [:296](../src/rc_metastudio/manuscript_report.py#L296) |
| R6 | Medium, observed | **Scale mixing.** The primary row shows OR 0.770 (ratio scale) next to SE 0.236 and z -1.111, which are log-scale values. A "SE scale: (log scale)" column patches over this. τ² = 0.378 is printed with no scale, though it is on the log-OR scale. A coherent log-scale row already exists in the supplement ("Calculation scale (log)"). | 26-report.txt; [manuscript_report.py:130](../src/rc_metastudio/manuscript_report.py#L130) |
| R7 | Medium, observed | **Reitsma output labelled as an effect, at two precisions.** The primary table is titled "Pooled effect" with an "Effect" column for sensitivity and specificity. The same export shows `65.8%` in the primary table and `65.762%` in "Clinical interpretation" prose and the supplement. Labels include `Lower bound (95% CI )`, `full FPR bounds` and `note:`. Correct and worth keeping: sampling-based summary ratios use Mean/Median/"95% interval" and stay out of the primary table. | [69-report.txt](../artifacts/verification/rcms/20261115T105214Z-02d68633-ui-fine-tuning/69-report.txt), [70-0 clinical report](../artifacts/verification/rcms/20261115T105214Z-02d68633-ui-fine-tuning/70-0-clinical-report.png) |
| R8 | Medium, code | **Denominators.** Participant totals are correctly withheld for HR, IRR and entered effects ([analysis_setup_dialog.py:1063](../src/rc_metastudio/analysis_setup_dialog.py#L1063)), but this shows the row `Participants: Not available`, which reads like missing data rather than "not applicable". The diagnostic sum adds only complete count rows ([:1078](../src/rc_metastudio/analysis_setup_dialog.py#L1078)). If an included study lacks counts, the label "Participants" overstates coverage. This needs a check against which diagnostic workflows admit incomplete rows. | code only |
| R9 | Medium, observed | **One estimate rendered four times in the Text report:** the Pooled effect table, the "Pooled Odds ratio: 0.770 (95% CI …)" sentence, an "Estimate [95% CI]" table, and the calculation-scale table. Text report and Manuscript repeat the same three primary tables. | 26-report.txt; [26-0 report](../artifacts/verification/rcms/20261115T105214Z-02d68633-ui-fine-tuning/26-0-analysis-results-report.png) |
| R10 | Medium, code | **Paper tables are less legible than the app.** PDF and DOCX left-align every cell ([manuscript_report.py:460](../src/rc_metastudio/manuscript_report.py#L460), [:587](../src/rc_metastudio/manuscript_report.py#L587)), while the app right-aligns numbers. There is no rule under the header. PDF body text is Arial 9 pt ([:649](../src/rc_metastudio/manuscript_report.py#L649)). Long tables do not repeat headers. | code |
| R11 | Medium, observed | **CSV is a formatted presentation table.** The 95% CI is one cell, `0.485 to 1.222`, so two variables share one column (Tidy Data §3.2). The values are rounded strings, and P is `.267`. | [36-0 tables](../artifacts/verification/rcms/20261115T105214Z-02d68633-ui-fine-tuning/36-0-polish-tables-dark.png), [results_window.py:614](../src/rc_metastudio/results_window.py#L614) |
| R12 | Low, observed | Forest rows use `0.571 [0.170, 1.916]`, while the report uses `0.170 to 1.916`. The forest has no weight column (box size encodes weight, which JAMA accepts). | 26-0 figure captures |

Existing strengths worth protecting: immutable validated results; stable
section IDs; source caveats kept verbatim; a prediction-interval note
distinguished from the CI; trim-and-fill and extrapolation caveats ("not a
corrected or more valid result", "not bias-adjusted"); primary versus additional
asymmetry roles; package versions and calls in Method details; white
publication canvases in dark mode; editable figures; real DOCX tables.

## 4. Scientific contract for every Results surface

These rules apply to the screen, the figure, the clipboard, CSV, DOCX and PDF.
Most of them already hold somewhere in RCMS; they need to hold everywhere.

1. **Uncertainty is never optional.** No estimate appears without its interval,
   and no P appears without the estimate it tests (JAMA's rule, adopted as a
   product rule because it is sound in general).
2. **RCMS writes no verdicts.** Generated text does not say significant, clear,
   evidence of, robust, important or effective, and adds no magnitude adjective.
   The author interprets. The exception is a fixed caveat that RCMS owns, such
   as "does not establish publication bias".
3. **CI and PI never share a label, a column or a sentence.** The PI is reported
   only where the authority package returned it (random effects with enough
   studies). It always carries the one-line meaning already used in the app.
4. **Each scale-bearing number names its scale** where the scale differs from
   the presented estimate: τ² (log OR scale), SE (log scale), meta-regression
   coefficients (log scale). Ratios display as ratios on log-spaced axes. Log
   values appear only on rows labelled log.
5. **Denominators are never synthesized.** Show participant totals only when
   every included study supplies counts of people. Never relabel person-time,
   event counts or entered estimates as participants. Omit the row rather than
   print "Not available" when the quantity does not apply.
6. **Subgroups are compared only through the test for subgroup differences.**
   Per-subgroup P stays in the supplement, never in prose or the primary table.
7. **Small-study output reports numbers, roles and fixed caveats.** It gives no
   yes/no result. The primary method is labelled primary, and other methods do
   not vote.
8. **Reitsma output is a summary operating point**, not a pooled effect.
   Sampling-based summary ratios keep their Mean/Median/95% interval form and
   stay out of the primary table. Univariate pooled ratios are never placed
   beside them as if they were the same quantity.
9. **Formatting never changes meaning.** No inference is computed from a
   rounded string. No added digit implies precision the producer did not
   supply. Any value shown rounded is reachable unrounded in one step.

## 5. Is the current architecture adequate?

**Yes for rendering. Not yet for numerical semantics.**

- `QTextBrowser` with simple HTML, `QTableWidget`, python-docx and
  `QPdfWriter` already produce everything the design needs: aligned columns,
  rules, footnotes, captions, repeated headers (`QTextTableFormat` header rows
  "get repeated when a table is broken across a page boundary"; DOCX uses the
  `w:tblHeader` row property) and white paper output. A browser renderer would
  add a second layout engine without solving the actual problem.
- The actual problem is that `ResultTable.rows` holds **strings only**
  ([analysis_results.py:57](../src/rc_metastudio/analysis_results.py#L57)).
  `manuscript_report.py` therefore decides behavior by matching human titles
  and headers, such as `'Study weights'`, `'Test of subgroup differences'`,
  `startswith('Lower bound')` and `'prediction' in note.casefold()`, and by
  regular expressions over cell text. [ADR 0011](adr/0011-use-a-versioned-analysis-boundary.md)
  says human-facing titles are presentation only, so this code works against
  that ADR. R1, R2, R4 and R11 all follow from it.
- JASP shows the shape of a fix that suits this codebase. The producer sends
  numbers with a column role and format. One client-side formatter renders a
  whole column. RCMS should **extend the existing versioned contract** in that
  direction rather than add a second report engine. Each numeric report column
  gets a `role` (`estimate`, `conf_low`, `conf_high`, `pi_low`, `pi_high`,
  `se`, `statistic`, `df`, `p`, `tau2`, `i2`, `q`, `k`, `n`, `weight`, `text`)
  and a `scale` (`ratio`, `log`, `logit`, `identity`, `percent`), plus a
  parallel numeric value (`null` where the source is text, a bound or
  missing). R and Python ship together, so this should be a clean bump to
  version 2 with no dual-version parser ([AGENTS.md](../AGENTS.md): no
  compatibility layers).
- Do not do this first. It touches every RCMetaR display builder. The
  increments in Section 7 fix most of the visible risk without it, and they
  shrink the code that version 2 later replaces.

## 6. Design recommendation

### 6.1 One account, three views of it

Keep the accepted navigation model. The current nav (Manuscript, Text report,
Tables, Settings, figures) has the right destinations but the wrong division of
content. I recommend:

- **Report** (rename of Text report): the scientific account. It opens with
  the primary table, then heterogeneity, then study results, then the complete
  supplementary output and its references. Remove its duplicate pooled renders
  (R9). One pooled row plus the coherent calculation-scale row remains.
- **Manuscript**: prose and numbered tables for copying into a paper. It reads
  from the same facts as Report and adds no new numbers.
- **Tables**: inspection and transfer of individual tables.
- Figures stay as their own nav items. Keep the current landing choice (first
  plot, or Report for Reitsma). The forest plot already presents every study's
  uncertainty and the pooled CI and PI. That is uncertainty first, and
  rerouting users away from it would not improve anything.

### 6.2 Representative Report layout (app, light or dark palette)

```
clinical failure · Odds ratio · Intervention vs Control
Random effects (DerSimonian–Laird) · 19 studies · 1097 and 1080 participants
───────────────────────────────────────────────────────────────────────────
                     Studies   Estimate   95% CI            95% PI            P
Odds ratio                19      0.770   0.485 to 1.222    0.212 to 2.799   .267
───────────────────────────────────────────────────────────────────────────
PI: the range for the underlying effect in a new comparable study; it is not
the confidence interval of the pooled estimate.

Heterogeneity
                     τ² (log OR)     I²       Q    df      P
                           0.378  46.0%  33.360    18   .015

Calculation scale (log OR)
                     Estimate   95% CI              SE        z
log odds ratio         -0.262   -0.724 to 0.200   0.236   -1.111

Study results (19) … Supplementary output … References · Settings
```

- The P column comes last and is narrow. Test statistics move to the log-scale
  row, where SE, z and estimate share a scale. This fixes R6 and follows JAMA's
  "no need to present the values of test statistics" for the primary row
  without deleting anything.
- The PI sits beside the CI as its own column, as in JASP's separate
  "95% CI"/"95% PI" pairs, with the existing one-line note directly beneath.
  **This needs the user's approval.** UI-2 placed the note beneath Model fit.
  This proposal keeps the note's wording and position relative to the PI value
  but moves the PI into the primary row. If it is declined, keep the PI in the
  heterogeneity block. Do not split it between both.
- "Model fit" no longer exists as a grab-bag. Counts move into the identity
  line. Heterogeneity becomes its own block. Model tests and specification go
  to the supplement.
- The layout uses bold, aligned headers; right-aligned numerals; one rule under
  the header and one under the body; no vertical rules; and widths sized to
  content (already accepted under UI-8).
- **Subgroup:** one row per subgroup with Studies, Estimate, 95% CI and 95% PI,
  with no per-subgroup P. The test for subgroup differences follows as a single
  line, for example `Test for subgroup differences: Q = 4.21, df = 2, P = .12`
  (illustrative values).
- **Reitsma:** the title is "Summary operating point", with columns Estimate,
  95% CI and 95% PI for sensitivity, specificity and false-positive rate.
  Sampling-based summary ratios follow under their own title, with the
  existing Mean, Median and 95% interval columns.
- **Small-study:** the title is "Small-study effects". The primary method row
  shows k, coefficient, 95% CI, statistic and P, labelled *Primary*. Other
  methods are labelled *Additional*. The fixed caveats follow. Trim-and-fill
  and extrapolation each get a labelled row, and their caveat appears directly
  under that row, never only in a footnote.

### 6.3 Paper output (PDF and DOCX; white page, black text, any app theme)

```
Table 1. Pooled estimate
─────────────────────────────────────────────────────────────────────
Outcome            Studies   OR      95% CI            95% PI            P
─────────────────────────────────────────────────────────────────────
Clinical failure        19   0.770   0.485 to 1.222    0.212 to 2.799   .267
─────────────────────────────────────────────────────────────────────
Abbreviations: CI, confidence interval; OR, odds ratio; PI, prediction interval.
Random-effects model (DerSimonian–Laird); pooled on the log odds ratio scale.
```

- Use 10 pt table text (JAMA's 10–12 pt submission range; the current 9 pt is
  below it), 11 pt body text and bold captions above tables. Right-align
  numeric columns, as the app already does.
- Rules: in PDF, top, under the header and bottom. In DOCX, keep a real Word
  table with header-row repetition. JAMA says "Do not draw extra lines or
  rules" for *submissions*, so DOCX should stay a plain editable grid without
  custom rules. That is a journal rule, adopted here only for the
  submission-oriented format.
- Add an abbreviation footnote per table (JAMA) and a scale footnote where
  needed. Footnotes are cheap and remove ambiguity, which makes them a good
  product choice regardless of journal.
- Figures: forest and other ratio plots keep log axes with ratio labels. That
  matches JAMA, and the current figures already do it. Favours labels at the
  *top* are a JAMA rule; Cochrane and RevMan place them at the bottom. Keep the
  bottom as the default. Do not add a style switch until someone needs one.

### 6.4 Numeric formatting decisions

`d` is the user's display digits. Existing R and Python helpers already
implement most rows; the change is to apply them in **one** place per surface
family.

| Quantity | Display | CSV and plain-text copy |
| --- | --- | --- |
| Estimate, CI and PI bounds, linear scale | `d` decimals | Full precision when contract version 2 exists; until then the displayed string |
| Ratio-scale estimate or bound below the display unit (e.g. 0.0004) | `d` significant figures (the existing `format_effect_number` rule); beyond 6 decimals, `4.2 × 10⁻⁷` | `4.2e-07` |
| P | No leading zero, uppercase *P* in prose and headers. `<.001` below .001; `>.999` above .999; never `P = 0` or `P = 1.000`. Producer bounds such as `< 0.001` render as bounds and are never re-expanded. | The same value. Exact P is also reachable in Method details, as small-study output already provides |
| τ², τ | `d` decimals, scale named. Exact 0 (estimator at the boundary) shows as `0` padded to `d`. A positive value below the unit shows as `<0.001` (absolute scale: a bound is honest and not over-emphasized) | Full precision |
| I² | One decimal with `%`; a positive value below 0.05% shows as `<0.1%` | Number without `%` in its own column |
| Q, z, t, coefficients | `d` decimals | Full precision |
| df, k, N, events | Integers. Fractional df (Knapp–Hartung) keep R's precision | Same |
| Weights | One decimal with `%` | Number, percent unit in header |
| Diagnostic proportions | One decimal with `%`, the **same** precision in prose, primary table and supplement | Proportion, not percent |
| Intervals | `a to b` in text and tables (JAMA's own example uses "to"). The figure keeps `[a, b]`: the forest column is compact, and changing it means touching R figure goldens; revisit with the forest increment | Separate lower and upper columns |
| Negative sign | ASCII `-` everywhere | ASCII `-` |
| Missing, not estimable, not applicable | `NA` with a table footnote stating which (JAMA allows NA for not applicable or not available; the footnote disambiguates) | Empty cell plus a status column when version 2 exists |

**P digits are a decision for the user.** I recommend the adaptive JAMA/AMA
rule (two decimals at or above .01, three below, `<.001`) as the *house*
default. The reason is not that one journal requires it. Three decimals on a P
of .267 implies a precision that a P value's sampling variability does not
support, and the adaptive rule never prints that false precision. The cost is
that `.267` becomes `.27` in displays. The exact value stays reachable. Ship
the notation unification (Increment 1) first, keeping three decimals, so the
digit change remains a separate, visible decision.

**Typographic minus is deliberately not recommended.** JASP shows U+2212 and
then has to strip it on copy. That forks every copy path for a small visual
gain, and an Excel paste of U+2212 produces text, not numbers.

### 6.5 Manuscript sentence templates

These are deterministic, contain no verdicts, and use only facts already in
the result:

- Standard: `19 studies were included (1097 participants in Intervention, 1080 in Control). The pooled odds ratio was 0.770 (95% CI, 0.485 to 1.222; P = .267). Between-study variance was τ² = 0.378 on the log odds ratio scale (I² = 46.0%); the 95% prediction interval was 0.212 to 2.799.`
- Delete the CI classification sentence (R4) and the I² category adjective
  rather than repair them. The interval is already in the preceding clause.
  The Cochrane I² ranges overlap by design and are a judgment for the author.
  If the user wants the adjective kept, it must be computed from a numeric I²
  rather than a string, and quoted as the Handbook's wording.
- Subgroup (illustrative values): `Pooled odds ratios were 0.70 (95% CI, …) in A and 0.95 (95% CI, …) in B. Test for subgroup differences: Q = …, df = 1, P = …`, with no per-subgroup P.
- HR, IRR, or entered estimates: no participant clause. IRR: `… across 12 studies (person-time in person-years)` only if the sheet declares one shared unit.
- Small-study: `The primary asymmetry test (Rücker AS+RE, 17 studies) gave a coefficient of -0.8605 (95% CI, -4.367 to 2.646; P = .61). Funnel plot asymmetry can reflect publication bias, heterogeneity, study design, or chance.`
- Avoid causal phrasing in generated prose, for example "effect of
  Intervention on". The statistical term "effect estimate" stays acceptable,
  but rename the manuscript table title "Pooled effect" to "Pooled estimate".
  The neutral title also fixes the Reitsma misnomer.

### 6.6 Copy and export

- **Copy table** puts both HTML (a real table that pastes into Word) and TSV on
  the clipboard. The report already does this; the table copy does not.
- **Export table CSV** stays the formatted table until contract version 2
  exists. Label it truthfully as "Export table (formatted, CSV)…". Contract
  version 2 adds "Export data (CSV)…": tidy, one row per component, columns
  `term, estimate, conf.low, conf.high, conf.level, pi.low, pi.high, std.error, statistic, df, p.value, scale`,
  full precision, `NA` for undefined. That borrows broom's vocabulary, not its
  code.
- PDF and DOCX use the same tables as the screen. Every export must agree
  digit-for-digit with the Report view at the same digits setting. That is the
  core acceptance property (Section 7).

## 7. Increments, safest first

Each increment is presentation-only unless marked. Each one ends with a native
run that leaves retained screen captures, `report.txt`, a copied clipboard
payload, CSV, DOCX XML and a rendered PDF. The binary sample from run 26, the
small-study sample from 43 and the Reitsma sample from 69/70 provide fixed
inputs. Decide the failure list before writing code (AGENTS.md).

| # | Change | Files | Acceptance evidence |
| --- | --- | --- | --- |
| 1 | **Stop fabricating precision; unify P notation (3 decimals).** `_presentation_cell` may round to fewer digits but never pad beyond the source string's decimals. Use one `p_value` for Manuscript, Report and Tables, with uppercase P headers. | `manuscript_report.py`, `results_window.py` (`_report_heterogeneity_columns`) | In 43-report, Model fit and the supplement show identical `10.51 (SE 42.59; 95% CI -80.26 to 101.3)`. In 26-report, every P except the forest's shows `.015`/`.267`. A cell such as `0.0004`, at three digits, stays `0.0004`. |
| 2 | **Remove generated verdicts.** Delete `_interval_meaning`/`_included_interval` prose and the I² adjective. In R, replace `Result: [No clear] evidence …` with `P = …` (keep the label row). | `manuscript_report.py`; `small_study_effects.R` plus its testthat expectations | A grep of all exported text for `clear evidence\|clear difference\|significant` returns nothing. A Rücker case with P < .05 shows a number, not a verdict. Caveat sentences are byte-identical before and after. |
| 3 | **Subgroup and denominator honesty.** Remove per-subgroup P from prose. Put the test for subgroup differences directly under the subgroup table. Omit `Participants: Not available`. Make the diagnostic participant total all-or-nothing, as binary already is. | `manuscript_report.py`, `analysis_setup_dialog.py` | Amino subgroup run: prose has one P, the interaction test's. HR/IRR/entered runs: no participant clause or row. A diagnostic run with one incomplete included study: no total. |
| 4 | **Scale and label clarity.** τ² is labelled with its scale. Move SE and z to the calculation-scale row. Rename "Pooled effect" to "Pooled estimate", and use "Summary operating point" for Reitsma. Use one percent precision across the Reitsma prose, primary table and supplement. Fix the `(95% CI )`, `full FPR bounds` and `note:` labels at their R source. | `manuscript_report.py`, `reitsma_methods.R` | 69-report: `65.8%` everywhere, or the full value everywhere, never both. No primary-table row mixes ratio and log scale. |
| 5 | **Paper typography.** Right-align numeric columns in PDF and DOCX; add a header rule (PDF only); set repeating header rows (`QTextTableFormat.setHeaderRowCount`, DOCX `w:tblHeader`); 10 pt tables; abbreviation footnotes. | `manuscript_report.py` | A rendered PDF page image, a DOCX opened in Word, and a 40-row study table spanning a page all show headers repeated and numerals aligned. Text retention passes unchanged. |
| 6 | **Report de-duplication and PI placement.** Needs user approval for PI placement (Section 6.2). | `results_window.py`, `manuscript_report.py` | The pooled estimate appears once in Report plus once on the log scale. The PI is never in the same column or sentence as the CI. Light/dark already-open-window transitions pass. |
| 7 | **Contract version 2 (R + Python, major).** Add column roles, scale and numeric values; one column formatter; delete title/regex dispatch; add tidy data CSV. Optionally move the forest P annotation to the house rule (this needs the R forest goldens re-baselined). | `analysis_results.py`, RCMetaR display builders, `manuscript_report.py`, `results_window.py` | All Section 4 rules pass on the workflow matrix (binary, continuous, one-arm, subgroup, regression, cumulative, leave-one-out, HR, IRR, entered estimates, Reitsma, small-study; non-95% level; zero cells; NA/Inf; tiny values; a bound at the null). Held numerics match independent R oracles. Screen, CSV, DOCX and PDF agree for every cell. |

Increments 1–4 are small, independent and reversible, and they remove the
scientifically risky output. Increment 7 is the only one that changes the
boundary.

## 8. Agreements, objections and differences from the concurrent study

The two documents agree on the following: package numerical authority;
CI/PI distinction; no denominators synthesized; a numeric contract before
journal styling; paper output stays white; no web stack.

The objections below are mine:

- **Do not restructure navigation before fixing agreement.** A new reading
  order over inconsistent numbers would make the inconsistency look more
  authoritative. Fix R1–R4 first.
- **Do not keep the CI-classification sentence in any form** while it reads
  rounded strings. Rewording it does not fix the rounding-at-the-null
  misclassification; only deletion or numeric input does. I recommend
  deletion.
- **Keep the forest plot as the default landing view.** It already presents
  uncertainty first. An "answer-first" report landing would duplicate what the
  forest footer shows.
- **The P house rule should be adaptive, not three decimals.** The concurrent
  study keeps the present convention. I recommend the adaptive rule as a user
  decision, after notation unification, for the false-precision reason in
  Section 6.4.
- **Do not add journal style switches.** One house style with stated reasons
  is enough. JAMA-only conventions, such as favours labels on top, stay out
  until a user needs them.
- **No typographic minus** (Section 6.4).
- **Do not use easystats-style automatic wording.** Its "statistically
  significant and large" pattern is the specific failure RCMS must avoid. Use
  its raw/pretty separation, not its prose.

## 9. Not verified

- The diagnostic partial-sum risk (R8) is a source reading. I did not trace
  which diagnostic workflows admit an included study without counts.
- The `<thead>` to `headerRowCount` mapping in Qt's HTML importer is
  unverified; setting the format after `setHtml` avoids depending on it.
- Subgroup and IRR outputs were read from source, not from retained captures.
  The cited captures cover binary random effects, small-study and Reitsma.
- The DOCX rendering in Word and the PDF page images were not inspected; the
  earlier review notes that external DOCX page rendering is outside its
  inventory.
- JAMA quotations come from the live page dated November 6, 2026. The AMA
  Manual of Style was not consulted.
