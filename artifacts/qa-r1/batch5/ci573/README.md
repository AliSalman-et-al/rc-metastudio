# PR 573 calculator editor regression

Original head: 0de678d148620d0898196b377c4847910f832cc8.
CI: run 41987950162 / job 127113324868, Required Windows Full R Stack Evidence (3).

Reproduction: unchanged `uv run --no-sync python scripts/verify_rcms.py calculator-mode-pre-post` fails locally with `('raw precision lost', 'pre-post', '1e12', 1e-05)`. See repro.log and its evidence manifest.

Cause: batch-5's `change_row_color_according_to_metric()` calls `_configure_tables()` after each effect refresh to resize the visible rows. That routine unconditionally replaced NumericSummaryDelegate on all tables. A refresh during a Tab commit replaced the delegate while Qt advanced its editor; the next edit failed and the prior value remained. This is not a magnitude validation limit: the same finite value works when the delegate survives.

Fix: install NumericSummaryDelegate only if the table does not already use it. Row measurement still runs on every refresh, keeping the compact layout; the active editor and its delegate remain paired. No tests, R code, numeric references or validation ranges changed.

Environment and exact commands:
```sh
source /home/ali/.t3/qa-env/ENV.sh
export UV_PROJECT_ENVIRONMENT=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/.venv
export PYTHONPATH=$PWD/src:$PWD
uv run --no-sync python -c 'from scripts.verify import run_typing; from pathlib import Path; run_typing(Path("/home/ali/.t3/qa-env/qt6"))'
uv run --no-sync python scripts/verify_rcms.py calculator-mode-pre-post
# Same command for each calculator scenario named by the log files.
uv run --no-sync python scripts/verify.py pre-push
```
Linux/offscreen Qt, real embedded R selected by QA ENV.sh; strict typing targets win32 and runs before GUI. This is source proof, not native Windows package qualification.

Each scenario log names its durable evidence directory (manifest, runtime identity, screenshots, steps, persisted project, and R results). evidence-index.json records outcomes and exact 1e12 precision observations, with manifests/steps copied here. All input fixtures and assertions are unchanged.

Results: original reproduction failed exactly as CI; all 15 post-fix scenarios passed (3 baseline calculators and all 12 calculator-mode scenarios), exit 0. Pre/post, back-continuous, continuous-metrics and one-arm mean each retain `1e12` as `1000000000000.0`. The selected precision screenshots are copied alongside their manifests and steps. Final pre-push passed strict win32 typing, code health, fast/golden (413 passed / 6 existing skips), GUI (364 passed / 1 existing skip) and packaging contracts (73 passed / 8 existing skips). Full Windows R-stack and platform jobs remain CI qualification.
