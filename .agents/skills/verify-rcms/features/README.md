# RCMS verification map

Read the relevant feature before driving it. Start each scenario in the fresh application and test-owned state created by `scripts/verify_rcms.py`. Run from the repo root after the skill's launch/doctor steps. No accounts, servers, ports, or production datasets are needed; the committed sample projects are the baseline.

| Feature | Real desktop scenarios | Additional paths requiring targeted coverage |
| --- | --- | --- |
| [Projects, editing, and CSV](projects.md) | `editing`, `csv` | Open menu/shortcut/recent/startup entry points; New Dataset and earlier wizard pages; close/save prompts; covariate/outcome/follow-up editing |
| [Meta-analysis](analysis.md) | `amino`, `continuous`, `lymph` | Cumulative, leave-one-out, subgroup, meta-regression, multi-metric diagnostics, Reitsma bivariate model and regression |
| [Effect-size calculators](calculators.md) | `calculator-binary`, `calculator-continuous`, `calculator-diagnostic` | Tool menu entry points, back-calculation, entered effect estimates, partial data, zero-cell corrections |
| [Results, plot editing, and export](plots.md) | `plot-edit`, plus PDF export in the three sample analyses | Funnel/SROC/coefficient/bubble editors; PNG/SVG/TIFF export; native fractional DPI and long/narrow layouts |
| [Small-study effects analysis](small-study-effects.md) | `small-study-effects` | Diagnostic Deeks funnel; contour, trim-and-fill, extrapolation, unavailable procedures and exploratory tests |

## Proof conventions

Pair a user action with its observed result and independent side effect. Menu and toolbar items sharing a QAction are separate entry points when a change touches their reachability. The automated scenarios use the handles documented in each feature; do not claim an unexercised shortcut or native picker is covered.

Evidence is stored per run under `artifacts/verification/rcms/`, outside scratch cleanup. Every run records the command, runtime, exit status, revision/dirty state, action snapshots, and file digests. Failed runs remain inspectable. Check the proof manifest after cleanup.

For a broader feature request, cover each listed affected entry point with a targeted drive. A numerical or packaging lane can supplement desktop proof, but cannot establish UI reachability by itself. Record limitations explicitly.
