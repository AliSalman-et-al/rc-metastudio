# RCMS verification map

Read the relevant feature before driving it. Start each scenario in the fresh application and test-owned state created by `scripts/verify_rcms.py`. Run from the repo root after the skill's launch/doctor steps. No accounts, servers, ports, or production datasets are needed; the committed sample projects are the baseline.

| Feature | Real desktop scenarios | Additional paths requiring targeted coverage |
| --- | --- | --- |
| [HR and IRR](ratios.md) | `ratios-hr`, `ratios-irr`: wizard, compact inputs, CSV/persistence, all main analyses, public numerical comparisons, plot editors/decoded exports; `ratios-samples`: bundled metadat data, fits and persistence | Remaining moderator shapes/options; earlier CSV entry points; native DPI and release qualification |
| [Projects, editing, and CSV](projects.md) | `editing`, `csv`, all `analysis-data-*`, `project-structure`, `project-table-covariates`, `project-shell` | Shortcut/startup entry points; earlier CSV/Excel pages; structure deletion/navigation; close/save prompts |
| [Meta-analysis](analysis.md) | Sample and `analysis-*` scenarios; `options-*`; authority matrix; current-source R-stack | Missing-data confirmations, reference levels, unsupported-combination recovery, remaining parameter combinations |
| [Effect-size calculators](calculators.md) | Baseline three calculators and twelve `calculator-mode-*` scenarios, actual single-click row gesture | Remaining transformed metrics, RR/RD and second-candidate back-calculation, unequal-SD/Cohen reconstruction, invalid partial data |
| [Results, plot editing, and export](plots.md) | `plot-edit`, eleven `plot-workflow-*` editor/decoded PDF/PNG/TIFF/SVG drives | Remaining appearance controls, failed regeneration/IO recovery, parameterless PNG, native fractional DPI and long/narrow layouts |
| [Small-study effects analysis](small-study-effects.md) | `small-study-effects`, `small-study-binary-extended`, `small-study-continuous-extended`, `small-study-diagnostic` | Low-heterogeneity Harbord; MD asymmetry; descriptive-only metrics; eligibility/error recovery; direct numerical asymmetry oracles |

## UX effort scoreboard

`hillclimb` drives the five fixed tasks from PLAN.md through the shared desktop
driver and records gesture counts, wall time and numerical/text receipts in
measures.json. See [SCOREBOARD.md](../../../../docs/ux-hill-climb/SCOREBOARD.md)
for fixtures, starting states, repeat comparison and baseline. This is offscreen
effort evidence with QAction activations; native menu traversal and human timing
remain unmeasured. `manuscript-export` verifies PDF/DOCX report export for amino, continuous and
diagnostic results; hillclimb T5 completes with both manuscript formats.

## Proof conventions

Pair a user action with its observed result and independent side effect. Menu and toolbar items sharing a QAction are separate entry points when a change touches their reachability. The automated scenarios use the handles documented in each feature; do not claim an unexercised shortcut or native picker is covered.

Evidence is stored per run under `artifacts/verification/rcms/`, outside scratch cleanup. Every run records the command, runtime, exit status, revision/dirty state, action snapshots, and file digests. Failed runs remain inspectable. Check the proof manifest after cleanup.

For a broader feature request, complete affected rows of [coverage.md](../references/coverage.md), including the dataset/metric matrix. Numerical or packaging lanes cannot establish UI reachability by themselves. Record limitations explicitly. The complete desktop command runs every scenario registered in `scripts/verify_rcms.py` except the separate doctor check; ten original baselines alone are not an all-app verification pass.
