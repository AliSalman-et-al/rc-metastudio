# Fixed-effect subgroup correction

The subgroup moderator fit received a missing `params$rm.method`, causing
`metafor::rma.uni` to use its DL default. The pop in `_with_result_identity`
only controls displayed identity, not execution. Fixed subgroup entry points
now explicitly select FE, including when a stale random estimator is present.
Regression already explicitly selects FE; sequential fits dispatch the selected
base estimator for every subset.

Fleiss1993 derived subgroup fixture: Q 4.852384 → 5.680480;
p 0.027608 → 0.017155. Authority: direct metafor FE moderator fit and
meta::metacr(method="Inverse") common subgroup test (desktop comparison 1e-6).

MH and Peto retain the inverse-variance moderator convention, explicitly named
in Results and Methods, rather than the estimator-specific common subgroup Q.
For the authority script's OR fixture, RCMS/metafor FE Q=27.08745;
meta::metabin(subgroup=group, method="MH", common=TRUE) Q=29.23978
(difference −2.152332), and method="Peto" Q=26.63551
(difference +0.4519434). These are convention differences, not equalities.

No frozen oracle values have been edited. The first strict gate compared
474 contracts / 415 numerical fields with no numerical drift (including all
random-effects cases); its only failures were two random subgroup text notes.
The correction note is now limited to fixed analyses to preserve those outputs.

Authority matrix: 96 cases passed in `build/sheets-baseline/stat-authority-green.json`.
The expected desktop failure is retained at
`artifacts/verification/rcms/20261031T191528Z-6d78a0af-rm5-import`.
Installation log and source/installed SHA-256 provenance are under
`build/sheets-baseline/stat-install*`. Final qualification passed after the last code change in one uninterrupted shell:
rm5-import, amino, continuous, results-window, plot-workflow-subgroup,
plot-workflow-regression; strict golden gate (474 comparisons, 415 numerical
fields); full E2E matrix `uv run --no-sync python -m pytest tests/e2e -n 2 -q`
(134 passed in 3062.05s). Logs: `build/sheets-baseline/stat-final-*.log`.
Golden report: `build/qt6-verification/golden-compatibility-stat-final/compatibility-report.json`.
All random frozen numerical contracts remained unchanged; no oracle edits.

Targeted evidence directories under `artifacts/verification/rcms/`:

- 20261031T192445Z-cf0ae46a-rm5-import
- 20261031T192543Z-01f5739c-amino
- 20261031T192556Z-1f4bc003-continuous
- 20261031T192606Z-35b45944-results-window
- 20261031T192700Z-1963377f-plot-workflow-subgroup
- 20261031T192755Z-e8687ca3-plot-workflow-regression

Limitation: new direct sequential/regression authorities use continuous data;
explicit binary sequential/regression authority additions remain unfinished.
Desktop proof uses offscreen Qt, not native OS interaction.
