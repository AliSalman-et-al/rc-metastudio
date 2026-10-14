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
`git push origin ux/audit-improvements`; stop on any failed push. No PR.
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
[CMA manual](https://meta-analysis.com/download/Meta-Analysis%20Manual%20V3.pdf),
[JASP guide](https://jasp-stats.org/wp-content/uploads/2022/04/Statistical-Analysis-in-JASP-A-Students-Guide-v16.pdf).
RevMan's aligned study/total grammar, public R explicit metric scales, and the
separate model/heterogeneity tables of JASP/Stata support these choices. CMA's
adjustable report/figure precision reinforces preserving user precision while
making its layout measured. Earlier comparison sources remain in round-two
BENCHMARKS. The archived RevMan 5 link returned `Internal Error`; use retained
round-two evidence and current official documentation, not a claimed new live view.
