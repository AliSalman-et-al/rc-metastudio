# Round 4 — failure modes and proof, before implementation

Baseline: clean `ux/audit-improvements` at `7938292`. Only existing workflows and
presentation change. Fits, thresholds and original numerical oracles stay fixed.
Use round-three ENV, installer, command recorder, numerical equivalence and desktop
driver; extend their existing paths rather than creating another composition.

| Item | Failure modes | End-to-end proof decided before coding |
| --- | --- | --- |
| R3-01 | Sequential null reaches footer; no line when null is in range; line when explicit range excludes null; journal export differs | Real cumulative/omission results in default/RevMan/BMJ; compare SVG vertical line endpoints with row labels and footer; explicit excluding range; decode exports |
| R3-02 | Linear ticks pad zeros or overlap title; tiny values disappear; OR/PLO round ticks regress | Existing precision drive extended to linear six-decimal ticks and measured title gap; retain transformed range/round-label assertions; inspect native screenshots |
| F10 | Duplicate names reuse first weight; subgroup order loses identity; excluded rows shift weights; total below 100; other rendering/report name lookups | Original included-row indexes through subgroup grouping; real HR/IRR and binary/continuous duplicate-name results, independently reconstruct effects/refit public metafor; compare each plotted weight and sum; save exact inputs |
| F09 | Raw annotations collide, weight touches CI, bold overall wider than measured; selected precision ignored | Raw diagnostic Sens/Spec, single proportion, binary, MD/SMD at 3/6 digits in journal/default paths; SVG measured text bounds plus native visual review and export decoding |
| F08 | BMJ loses contextual metric or overwrites explicit axis text | Actual coefficient/entered-effect results in three styles; custom label Apply/reopen/export, inspect SVG and native view |
| F04 | Floating residual printed as tiny zero bound; genuine tiny row erased; extreme statistic excessively long | Original coefficient Fixture 2, retained tiny-effect case and extreme 1/SE case; row scale through formatter; inspect SVG/report without changing numeric inputs |
| F05 | Wrong null or transformation named; clinical threshold invented; report and figure disagree | Public metafor metadata and null=0 on calculation scale; diagnostic and supported single-arm transforms; actual report/figure labels, unchanged statistic/p-value |
| F06 | Inactive modes still occupy layout; arm names lost; estimate/actions scroll; switching loses inputs or persistence | Existing twelve calculator modes and baseline binary/continuous drives; native default-size captures, active visibility/primary geometry, unchanged independent previews, Accept/Cancel/undo/reopen |
| F07 | Internal aliases break; Automatic writes literal text instead of sentinel; contextual labels wrong; menu vocabulary/help stale | Existing CSV/covariate/plot editor/small-study/help drives; mapping import aliases retained; actual visible labels/tooltips and edited persisted parameters; native screenshots |

Each focused commit is immediately fast-forward pushed with
`git push origin ux/audit-improvements`; on failure wait 30 seconds and retry
once, then stop if it still fails. No force push or PR.
Before each native R drive reinstall source into round-three's persistent owned
library and retain source/install hashes. Retain exact commands, exits and failure
text in ignored raw logs with curated results in this directory.

Final gates: all 415 original numerical fields exactly equal; strict golden gates
(presentation-only refresh only after reviewing changed text); affected native
screenshots actually inspected for geometry and labels; one final
`verify_all.py --full --fresh`. End-of-round documents identify each item, commits,
evidence and remaining limitations. Screen-reader/keyboard/OS scaling, long figure
reading size and standalone exposure context remain deferred.

## Broadened mandate and deliberate design pass

The user expanded round four to polish existing styles, workflows and statistical
output end to end. Known defects above stay first. No new statistical features.
Survey: read the maintained launcher/wizard, grid, calculator, menu/dialog/setup,
results/Text/Tables/export/help paths and inspect the re-audit's native launcher,
grid, calculator, report and figure evidence. Current native presentation probes
cover styles at both precisions. Native Qt styling already supplies a coherent
host palette; keep it. Default precision remains three; six is a stress probe.

Ranked selections (before implementation):

1. **D4-01 — study weights as an actual table.** Replace the generic
   Statistic/Value representation with Study / Weight (%) rows from the existing
   package vector, retaining row identity and missing values. Clinical value:
   compare contributions directly; copy/CSV should have the same cells.
   Failure modes: wrong names, fractions labelled percentages, accidental reorder,
   differing screen/copy/export. Proof: native standard HR/binary/continuous
   Tables and report; compare every cell with public package weights and totals.
2. **D4-02 — results before implementation detail.** Lead standard result tables
   with a short pooled-estimate/CI sentence built from the existing formatted
   producer cells. Present existing calculation-scale cells in a named table
   rather than a package-style paragraph, while keeping the legacy numerical
   oracle path intact. Strengthen heading/padding hierarchy using Qt's native
   palette. Failure modes: changed values, lost scale/SE, duplicated paragraphs,
   overflow, copy/export differences. Proof: native before/after report and Tables,
   exact original 415-field equality, public fitted values and report export.
3. **D4-03 — consistent actions and honest empty state.** Use sentence case and
   ellipses for actions opening another interaction; distinguish an untouched
   empty workspace from edited data. Existing shortcuts/actions remain shared.
   Failure modes: wrong dirty indicator or action reachability. Proof: native
   launcher/grid/menu/help before/after; existing shell/edit/undo/save workflows.

Deferred: global colour/icon/theme replacement, new remembered-choice machinery,
automatic clinical direction, clinical verdict sentences and new analytics.
Existing investigator-supplied favours labels, model/heterogeneity/test/PI footer
grammar and total rows are retained and visually checked with the known fixes.

References reviewed on 15 October (design comparisons, not installed-software
qualification): [RevMan manual analyses](https://documentation.cochrane.org/revman-kb/manual-input-analyses-259686817.html),
[RevMan DTA graphs](https://documentation.cochrane.org/revman-kb/analysis-graphs-in-dta-reviews-236847627.html),
[metafor forest](https://wviechtb.github.io/metafor/reference/forest.rma.html),
[metafor regplot](https://wviechtb.github.io/metafor/reference/regplot.html),
[meta manual](https://cran.r-project.org/web/packages/meta/meta.pdf),
[Stata meta manual](https://www.stata.com/manuals/metameta.pdf),
[CMA features](https://meta-analysis.com/pages/features),
[JASP meta-analysis introduction](https://jasp-stats.org/2017/11/15/meta-analysis-jasp/).
RevMan's aligned study/total grammar, public R explicit metric scales, and the
separate model/heterogeneity tables of JASP/Stata support these choices. CMA's
adjustable report/figure precision reinforces preserving user precision while
making its layout measured. Earlier comparison sources remain in round-two
BENCHMARKS. The archived RevMan 5 link returned `Internal Error`; use retained
round-two evidence and current official documentation, not a claimed new live view.
The archived CMA manual returned HTTP 403 and JASP student guide HTTP 404;
the current official pages above were reviewed instead.

Visual review follow-up before its repair: BMJ uses percentage values with an
unqualified Weight header, and Qt can paint the axis-cleanup background outside
the SVG paper. Make the percent unit explicit and bound that background to the
physical device. Extend annotation proof to numeric raw cells and BMJ's
parenthesized CIs, not only percent-suffixed labels. Inspect fresh BMJ before/after
and decoded exports; statistical values stay untouched.

F06 native follow-up before repair: the pre/post calculator remains 356×388 after
settling, with 127 pixels of vertical overflow. Its primary result still lives
inside the input scroller. Move the existing result and action controls below
that scroller. Prove their full visibility and unchanged position at both scroll
extremes, while retaining the independently checked pre/post reconstruction and
persistence. This is stronger than resizing the same scroll-dependent layout.

Final curated-frame inspection found two BMJ gaps before this repair: the
wrapped pooled-model label's second line touches binary totals, and the longer
null description touches the first axis tick. Reserve the measured bold pooled
label in the study column and the measured endpoint-tick half-width plus text
padding beside the footer. Extend the existing rendered check to include model
labels against totals and inference text against axis ticks. Stop the in-flight
full run (own PID 761953, SIGINT, exit 130), retain its receipt, then reinstall,
recapture affected native families and run a fresh complete qualification.

## Opus review 1: second design batch (ranked before implementation)

The previous push interruption is resolved: the user pushed `ca6815c`; origin was
observed at that exact commit on resumption. Preserve the interrupted receipts.
Qualify that source natively before replacing its historical evidence.

| Rank / item | Reason and finished scope | Failure modes | Proof |
| --- | --- | --- | --- |
| 1 / D4-04 Main-window start page | Replace the blank table and flat action strip with a scrollable, well-spaced start page: Create, Import CSV and Open using existing actions; recent project names and full paths, visibly disabled missing files; short data → analysis → export orientation. Show the ordinary table once an outcome exists. Startup uses this page without a redundant welcome dialog. | Hidden data after creating/opening/importing; Cancel leaves wrong page; missing paths crash; recents stale; small-window overflow; dirty state or startup placement changes. | Native fresh/normal-size start page, present/missing recent entries, Create Cancel and successful wizard, Open and CSV entry Cancel, reopen/save/edit and startup; before/after captures and contact sheet. |
| 2 / D4-05 Results reading page | Key result and numerical tables first, then heterogeneity, tests and PI; configuration and calculation detail later. Compact native-font heading hierarchy, aligned tables, modest page margins; sidebar Text report/Tables entries and section links stay synchronized. Remove duplicate legacy Inference Method by folding actual producer information into configuration. Remember the chosen plot export format in existing result-window settings, preserving it through navigation and a new result; a PNG-only plot must not erase a publication-format preference. | Lost numbers/identity/tables/notes; wrong model inference; navigation opens wrong page; copy/export loses content or differs in order; large zoom or dark palette unreadable. | Native standard, diagnostic and sequential reports, sidebar gestures, table copy/CSV and report copy/export; chosen SVG survives report/plot switching and a fresh analysis window; all 415 original values exact; golden text only via reviewed sanctioned refresh; before/after report captures. |
| 3 / D4-06 Shared native controls and navigation | One small shared Qt policy for button size/spacing and stock dialog icons; primary toolbar actions have text beside icons and all have useful tooltips. Replace unexplained compass presentation with a labeled choice of the existing outcome/follow-up/group dimension and previous/next/add controls using existing operations. Keep palette-owned colours. | Toolbar overflows at normal size; icon/text ambiguity; buttons clipped at scaling; selection changes twice or loses data; inconsistent dark/light output. | Native main window, calculator/setup/structure dialogs and results at ordinary sizes, light and dark palette; actual structure switching/undo/save/reopen; inspect all changed screens. |
| 4 / D4-07 Publication finishing | Shared round display-scale ticks for logit/arcsine/Freeman–Tukey forests, measured multiline header leading and title clearance. Comparative tests use RevMan's concise conventional form; explicit concise H₀ only for ambiguous single-arm/diagnostic/entered/coefficient nulls. Existing direction fields and 3-digit defaults remain. | Non-round or missing ticks, incorrect transform/explicit tick handling, header/footer overlap, a false PFT null, altered fits, lost favours labels. | Native three-style 3/6-digit binary/continuous/diagnostic/single-arm figures; SVG text geometry and four decoded exports; transformed metric probes; existing editor direction persistence; original numerical and golden gates. |

Review fixes precede D4-04..06 implementation. Small confidence-level wording
polish belongs with the report/control presentation work. Reference comparisons
will use official RevMan/metafor documentation: aligned table columns, a compact
overall-test line, deliberate header leading, separate direction labels and
publication exports with the same layout as the app. No new analysis, fitted
quantity, configuration framework or navigation subsystem is introduced.

## Final fresh-profile follow-up (before repair)

`review1-full-gates` exposed three failures after the earlier focused checks:

- The Reitsma moderator coefficient plot has its own existing renderer and saved
  bundle, but the new automatic-tooltip reader invokes the metafor forest planner
  merely because `fp_style` exists. Use the existing Reitsma coefficient bundle
  predicate at that boundary so each renderer keeps its own defaults. Failure
  modes: editor cannot open, another renderer receives wrong defaults, custom
  axis edits or saved geometry lost. Proof: preserve the full failed E2E receipt,
  then drive `plot-workflow-coefficient` natively and offscreen through edit,
  Cancel/reopen and all four decoded exports. Inspect native before/after frames.
- The single-arm calculator assertions demand a visible Back-calculate button,
  although those metrics intentionally have no back-calculation capability.
  Assert that it is hidden in single-arm modes; retain full visibility and fixed
  screen-position checks for every supported action at both scroll extremes.
  Failure modes: accidentally accepting hidden applicable controls, losing the
  estimate or Clear/OK reachability, changed persisted values. Proof: existing
  one-arm proportion/mean E2Es natively and offscreen, including independent
  preview and post-reopen analysis, plus their native screenshots.

No fitted quantity or R calculation changes. After these focused proofs, repeat
the full fresh profile and exact 415-field comparison; retain the failed full
run without treating its other successes as final qualification.
