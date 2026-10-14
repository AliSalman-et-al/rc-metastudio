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
