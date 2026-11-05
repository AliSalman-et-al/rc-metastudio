# Batch 7 qualification

**Formatting policy superseded by [the reviewed correction](../batch7-review/README.md).**
Normal values retain fixed decimals; only adaptive small values trim trailing zeros.

Base: origin/master a1ae1b49709c6b329c024e53a9f176a043816b24. Linux x86_64,
PyQt6 and real embedded R. No statistical implementation or tolerance changed.
Out of scope: subgroup first-view at 1024x700/large font and hyphen/minus.
The 9 pt forest body floor and #574 fit settling are untouched.

## Reproduce

Source `/home/ali/.t3/qa-env/ENV.sh`, then set `PYTHONPATH=$PWD/src:$PWD` and
`UV_PROJECT_ENVIRONMENT=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/.venv`.
Use its generated forms and pinned R dependencies. Install source with
`$RCMS_R_HOME/bin/R CMD INSTALL -l $PWD/build/rcmetar-lib r/RCMetaR`, then prepend
that library to RCMS_R_LIBS, R_LIBS and R_LIBS_USER. Installation logs are retained.

- Typing: `uv run --no-sync python -c 'from scripts.verify import run_typing; from pathlib import Path; run_typing(Path("/home/ali/.t3/qa-env/qt6"))'`.
  Logs retain the full repository source selection and **win32** target.
- `git fetch origin master`, then `uv run --no-sync python scripts/verify.py pre-push`.
  Earlier failed runs are retained; `pre-push-qualified.log` records the final code run.
- `uv run --no-sync python scripts/verify_rcms.py SCENARIO`, for continuous,
  amino, plot-edit, results-window, ratios-hr, editing and project-shell.
- IRR: `xvfb-run -a -s '-screen 0 1600x1000x24' uv run --no-sync python scripts/verify_rcms.py ratios-irr --native`.
  The default 800px offscreen screen cannot fit its existing long editor caption;
  those failures remain in the logs. No assertion was weakened.
- `R_HOME=$RCMS_R_HOME uv run --no-sync python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-batch7-review`.
- `$RCMS_R_HOME/bin/Rscript .agents/skills/verify-rcms/scripts/analysis_authorities.R artifacts/batch7/authorities.json --installed` (103 independent cases).
- `$RCMS_R_HOME/bin/Rscript -e 'testthat::test_local("r/RCMetaR", filter="forest-metafor-renderer|summary-display", reporter="summary")'`.

Scenario receipts retain commands, inputs, runtime provenance, assertions and
screenshots. Sample before/after receipts also retain full R results, input data,
plot data and decoded SVGs. The original evidence paths remain in each log.

## Native actions and observations

Use `/home/ali/.t3/qa-env/tools/venv/bin/python /home/ali/.t3/qa-env/tools/ui.py --session batch7`.
Every start used `RCMS_QA_APP_SRC=$PWD RCMS_QA_R_LIB=$PWD/build/rcmetar-lib`.
The session was stopped after driving it.

1. `start $PWD/sample_projects/continuous.rcms --dark`, immediately `--wait 0 shot`:
   `dark-starting-r.png` shows loaded raw data and blank SMD/lower/upper cells.
   `dark-ready-r.png` shows the calculated values once R is ready.
2. Open continuous via Ctrl+O, its path and Open. Analyses → Meta-analysis → Run:
   `dark-smd.png` shows full-size outward labels even with the null near the left
   axis end. The labels match the axis ticks instead of shrinking to the span.
3. `start --large-font`; Ctrl+O amino, Analyses → Meta-analysis → Run, scroll to
   footer: `light-large-or.png` and `light-large-or-footer.png`. Small limits now
   match the grid (0.004, 0.01); trailing zeros are removed from effect numbers.
4. Edit first study name (double-click, type, Return); Ctrl+O:
   `dark-unsaved-final.png` and `light-large-unsaved.png` show Discard/Cancel/Save
   with Save default. Escape preserves the edited document (`light-escape-preserved.png`).
5. `start $PWD/sample_projects/amino.rcms --large-font`, immediate screenshot:
   `light-large-starting-r.png`, then `light-large-ready-r.png` prove the same
   pending/ready transition with light palette and large font.

Before screenshots supplied by QA: `/home/ali/.t3/qa-round5/opus/00.png`, `12.png`,
`05.png`, `06.png`, and `council/shots/27-results.png`, `16-corrupt.png`.
Intermediate screenshots/logs are retained as attempts, not claimed as final proof.

## Numeric and golden proof

`compare-numerics.R` compares all numeric leaves of saved R model and plot data,
including S4 slots, excluding only elapsed runtime. Before/after numeric leaves:
continuous model **157**, plot data **203**; amino model **593**, plot data **815**;
all identical (`numeric-proof.txt`). `compare-reports.py`, complete before/after
reports, descriptors and `presentation.diff` show the intended presentation changes.

`golden-presentation.diff` lists each changed section: amino standard/cumulative/
leave-one-out/subgroup, continuous standard/cumulative/leave-one-out/subgroup,
and lymph DOR standard. Changes are trailing-zero removal, the shared small
nonzero rule, and sentence case for OR/SMD. Existing meta-regression exceptions
remain untouched. Plot descriptor identities use Forest plot; legacy harness
artifact keys remain as observed. All 11 frozen output and parameter objects and
all original PNG bytes remain identical. Numeric contract values/tolerances are
unchanged; its archive SHA binding was necessarily updated. See `golden-proof.txt`.

Please review the presentation-only golden changes against that diff and proof;
no numerical oracle was regenerated. The before/after golden gate reports are
retained. Long-label geometry is proved by ratio E2E footer bounds/overlap/gap
assertions and the native screenshots, without replacing frozen plot bytes.

Not checked: Windows/macOS native or release packages; every native Save/Discard
entry-point combination; the expressly excluded subgroup first view.

## Final results

- `direction-size-proof.json`: both direction labels and axis ticks are **12.96 px**
  in both sample SVGs; rerun `python3 artifacts/batch7/prove-direction-size.py`.
- `r-contracts-final.log`: forest renderer and summary-display contracts pass.
- `golden-compatibility-batch7-review.json`: passed, **416** numeric metrics.
- `authorities.log` / `authorities.json`: **103** independent authority cases pass.
- `pre-push-qualified.log`: strict win32 typing, fresh-master code health,
  fast/golden **413 passed / 6 skipped**, GUI **364 passed / 1 skipped**, and
  packaging **73 passed / 8 skipped**. Consult the transcript for exact counts/commands.
- Native IRR and offscreen HR both end in workflow-passed; manifests/steps are
  retained under receipts. Earlier offscreen IRR caption failures remain explicit.
