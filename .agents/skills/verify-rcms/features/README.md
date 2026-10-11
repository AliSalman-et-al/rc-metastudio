# RCMS verification map

Read the relevant feature before driving it. Start each scenario in the fresh application and test-owned state created by `scripts/verify_rcms.py`. Run from the repo root after the skill's launch/doctor steps. No accounts, servers, ports, or production datasets are needed; the committed sample projects are the baseline.

| Feature | Real desktop scenarios | Additional paths requiring targeted coverage |
| --- | --- | --- |
| [Projects, editing, and CSV](projects.md) | `editing`, `csv`, all `analysis-data-*` creation/persistence drives | Open menu/shortcut/recent/startup entry points; earlier CSV pages; close/save prompts; covariate/outcome/follow-up editing |
| [Meta-analysis](analysis.md) | `amino`, `continuous`, `lymph`, all `analysis-*` scenarios; authority matrix; current-source R-stack | Missing-data confirmations, exclusion changes, alternate parameter UI wiring, unsupported-combination recovery |
| [Effect-size calculators](calculators.md) | `calculator-binary`, `calculator-continuous`, `calculator-diagnostic`, actual single-click row gesture | Metric-menu choice, back-calculation, entered effects, partial data, zero-cell corrections |
| [Results, plot editing, and export](plots.md) | `plot-edit`, plus PDF export in the three sample analyses | Funnel/SROC/coefficient/bubble editors; PNG/SVG/TIFF export; native fractional DPI and long/narrow layouts |
| [Small-study effects analysis](small-study-effects.md) | `small-study-effects`, `small-study-binary-extended`, `small-study-continuous-extended`, `small-study-diagnostic` | Low-heterogeneity Harbord; MD asymmetry; descriptive-only metrics; eligibility/error recovery; direct numerical asymmetry oracles |

## Proof conventions

Pair a user action with its observed result and independent side effect. Menu and toolbar items sharing a QAction are separate entry points when a change touches their reachability. The automated scenarios use the handles documented in each feature; do not claim an unexercised shortcut or native picker is covered.

Evidence is stored per run under `artifacts/verification/rcms/`, outside scratch cleanup. Every run records the command, runtime, exit status, revision/dirty state, action snapshots, and file digests. Failed runs remain inspectable. Check the proof manifest after cleanup.

For a broader feature request, complete affected rows of [coverage.md](../references/coverage.md), including the dataset/metric matrix. Numerical or packaging lanes cannot establish UI reachability by themselves. Record limitations explicitly. The complete desktop command runs 44 workflows; ten original baselines alone are not an all-app verification pass.
