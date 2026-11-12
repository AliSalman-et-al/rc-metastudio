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

Shared report observers compare the complete rows of Pooled effect, Model fit and
Study results with held inputs, including sequential fit identities and diagnostic
metric labels. Every original table row is also retained with its complete field labels and
source section/table identity in the compact Supplementary Detailed results table. Structured notes are retained verbatim as prose beneath their source tables. Prediction-interval notes also accompany the main report prose and Model fit table; the Pooled effect table retains each row's producer SE scale so combined diagnostic metrics remain distinguishable.
References are retained as a numbered prose section rather than a table.
The manuscript export drive checks every prose paragraph in clipboard, PDF and DOCX
and rejects developer-facing “Held” labels.
Both manuscript scenarios set a dark text palette and a +6 pt UI font, and check exported PDF body,
figure-caption and supplementary-heading colours through Poppler XML. Sample
PDF/DOCX filenames include spaces and Unicode. Amino PDF page/word geometry
must match a default-UI-font export exactly; DOCX document/style XML must also
match across UI fonts. Native file-picker overwrite and exhaustive export-format/theme combinations still need a
targeted drive; these colour checks do not establish that coverage.
Unstructured small-study output is
retained line by line; its model comparisons remain distinct from individual study
results. Copy HTML/plain text, DOCX tables and ordered PDF table contents are checked
against the same complete rows. `scripts/audit_report_retention.py` captures real
results and writes per-surface before/after loss inventories; each observed report
also retains its inputs and exports under the workflow's `report-retention/` folder.

## Proof conventions

Pair a user action with its observed result and independent side effect. Menu and toolbar items sharing a QAction are separate entry points when a change touches their reachability. The automated scenarios use the handles documented in each feature; do not claim an unexercised shortcut or native picker is covered.

Evidence is stored per run under `artifacts/verification/rcms/`, outside scratch cleanup. Every run records the command, runtime, exit status, revision/dirty state, action snapshots, and file digests. Failed runs remain inspectable. Check the proof manifest after cleanup.

For a broader feature request, complete affected rows of [coverage.md](../references/coverage.md), including the dataset/metric matrix. Numerical or packaging lanes cannot establish UI reachability by themselves. Record limitations explicitly. The complete desktop command runs the pytest workflow registry and the separate doctor check. Pytest excludes `ui-crawl`, a separate surface inventory; drive it explicitly when that inventory is needed. Ten original baselines alone are not an all-app verification pass.

## Summary of findings (partial slice 9)

`summary-of-findings` opens the real Analysis menu action on a derived
amino/lymph/empty fixture, renders four rows, checks default certainty and empty
reason, writes manuscript DOCX/PDF, checks extracted output and saves/reopens
reviewer judgements. It compares two binary results with direct metafor fits,
checks data-edit refresh, and retains the derived project. Wheel scrolling over a
focused certainty selector must scroll an overflowing table without changing the
judgment; keyboard and popup edits remain available. Native picker gestures,
participant-count definitions and remaining estimator combinations need targeted coverage.

Every desktop driver observes the visible splash and live package status before the main window exists, then the enabled shell with an empty status bar after real R is ready. `tests/e2e/startup_splash_driver.py` adds native scale 1/2 captures, Windows taskbar style and late-package failure with the real error dialog and editable project. R still loads on the GUI thread.
