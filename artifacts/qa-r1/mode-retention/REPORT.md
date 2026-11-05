# Calculator mode retention

## Root cause

`_refresh_active_inputs` rendered the newly selected authority into shared line edits before an outstanding draft had necessarily emitted `editingFinished`. #567 restored the stored entered triplet, but could not restore text that had never reached that store. Its E2E used Tab to commit every field, cleared the sample raw data, and called `setCurrentIndex`; this excluded the failing pending-editor path and the coexistence of raw and entered inputs.

There were two further authority problems when preserving raw inputs: binary validation/readouts selected their source from raw completeness rather than the visible mode; acceptance did not persist a source choice for the grid/analysis. Existing entered standard-error and display caches also survived editing the point/bounds. Clear-first tests removed those caches.

The shared edit commit runs before replacing mode fields and on acceptance. Explicit entered mode selection is stored with that metric/comparison's entered record; summaries use the normal raw authority. Group inputs are retained. Editing point/bounds invalidates stale SE/display caches, and supplied bounds remain exact at their original confidence level. The source getter does not create storage entries. No R formula or frozen reference changes.

## Repeatable automated proof

Environment: source `/home/ali/.t3/qa-env/ENV.sh`, override `PYTHONPATH=$PWD/src:$PWD` and `UV_PROJECT_ENVIRONMENT=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/.venv`. Every invocation uses `uv run --no-sync`; no dependency sync. Strict Ty target is win32, GUI/R runtime is Linux/offscreen. Exact commands and inputs are in each retained manifest.

Before runs restore all changed product files from the original HEAD cc55c76c (master 95f8bef7 plus the grid-colour commit), keep the tightened E2E driver, run both scenarios, and restore the fix in a Python `finally` block. The failing paths precede the subsequently tightened grid assertions.

- Before continuous: ../../verification/rcms/20261105T055149Z-517f5c06-calculator-mode-entered-continuous — fails pending 0.5 roundtrip after first setting valid CI bounds.
- Before binary: ../../verification/rcms/20261105T055212Z-7cd1306d-calculator-mode-entered-binary — fails entered editing/validation with sample counts retained, before completing the roundtrip.
- After continuous: see `pr-calculator-mode-entered-continuous.log` and its manifest.
- After binary: see `pr-calculator-mode-entered-binary.log` and its manifest.
- The entered drives type through QTest, preserve sample raw inputs, switch widgets, click OK, compare all three formatted grid fields with typed inputs and the model authority, Cancel a second edit, undo/redo, save/reopen, then compare a real R fit against independent metafor construction.
- Ordinary summary, counts and pre/post drives: `pr-calculator-continuous.log`, `pr-calculator-binary.log`, `pr-calculator-mode-pre-post.log`.
- Strict typing: `typing-pr.log`. Required complete local qualification: `pre-push-isolated.log` and repository `artifacts/verification/pre-push.json`.

## Real-display drive

Driver: `/home/ali/.t3/qa-env/tools/venv/bin/python /home/ali/.t3/qa-env/tools/ui.py --session mode-retention`, launched with `RCMS_QA_APP_SRC=$PWD`; session stopped after each run. Open the worktree's `sample_projects/continuous.rcms` with Ctrl+O, click Carroll's row header, choose Entered estimate with End/Return. Set upper CI to 1 before entering 0.5 (0.5 exceeds the sample's original upper bound 0.4526). Commit each with Tab. Choose summaries with Home/Return, inspect 0.0945; choose entered with End/Return, inspect 0.5000 and preserved bounds; click OK.

- Light/default: `light-typed.png`, `light-switched.png`, `light-return.png`, `light-accepted.png`. This earlier native pass exposed the CI display-cache issue subsequently fixed; do not treat its normalized lower grid bound as final CI proof.
- Dark/large final source: `dark-large-typed.png`, `dark-large-switched.png`, `dark-large-return.png`, `dark-large-accepted.png`. Returns to 0.5000, lower -0.2635, upper 1.0000. Final automated grid proof covers all three accepted columns; large-font native columns extend outside the viewport.
- Original reported before screenshots: `/home/ali/.t3/qa-round4/A/shots/01-switched.png` and `01-return.png`.

## Limits

No release-package/cross-platform qualification, exhaustive native theme/font Cartesian matrix, or complete 142-scenario warm matrix. No numerical golden or authority tolerance changed. CI owns the full statistical-authority gate. The persisted optional calculator source is a string in entered-effect metadata; older builds whose semantic validator only accepts numeric effect metadata may reject a file saved with explicit entered selection.

## Retained final-branch manifests

All file hashes in the following manifests were checked after completion.

| Transcript | Result | Manifest | Source head |
| --- | --- | --- | --- |
| [master-continuous.log](master-continuous.log) | fail | [manifest](../../verification/rcms/20261105T055149Z-517f5c06-calculator-mode-entered-continuous/manifest.json) | cc55c76ca6b7 |
| [master-binary.log](master-binary.log) | fail | [manifest](../../verification/rcms/20261105T055212Z-7cd1306d-calculator-mode-entered-binary/manifest.json) | cc55c76ca6b7 |
| [pr-calculator-mode-entered-continuous.log](pr-calculator-mode-entered-continuous.log) | pass | [manifest](../../verification/rcms/20261105T062925Z-038071f0-calculator-mode-entered-continuous/manifest.json) | ceb6a89f6017 |
| [pr-calculator-mode-entered-binary.log](pr-calculator-mode-entered-binary.log) | pass | [manifest](../../verification/rcms/20261105T062958Z-6e8077be-calculator-mode-entered-binary/manifest.json) | ceb6a89f6017 |
| [pr-calculator-continuous.log](pr-calculator-continuous.log) | pass | [manifest](../../verification/rcms/20261105T063044Z-37563a7c-calculator-continuous/manifest.json) | ceb6a89f6017 |
| [pr-calculator-binary.log](pr-calculator-binary.log) | pass | [manifest](../../verification/rcms/20261105T063111Z-b333bed5-calculator-binary/manifest.json) | ceb6a89f6017 |
| [pr-calculator-mode-pre-post.log](pr-calculator-mode-pre-post.log) | pass | [manifest](../../verification/rcms/20261105T063145Z-9569286b-calculator-mode-pre-post/manifest.json) | ceb6a89f6017 |

The PR branch starts from current master c1654843 and cherry-picks only this task's changes. The original work branch, including the unrelated gold-column commit, remains intact. Before manifests use the original product files at cc55c76c; their failing paths are unchanged by #570.

Qualification history: the initial pre-push found old fake APIs (extended without removing assertions); a later run found a mutating source getter, now read-only; the next found the new-calculator counts panel hidden, now corrected. A focused existing shell test passes. Two concurrent qualification commands were terminated with SIGTERM (143); the final pre-push is isolated with `setsid`. Failed/interrupted transcripts remain available; only a completed final run is qualification.

Final qualification on calculator-only branch ceb6a89f: `setsid uv run --no-sync python scripts/verify.py pre-push` completed successfully. Strict Ty win32, code health, Python fast/golden, GUI and packaging contracts all passed. See `pre-push-isolated.log` and the repository qualification JSON. No source changed after this run.
