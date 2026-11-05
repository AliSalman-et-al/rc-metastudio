# Corrected body-text readability floor

The earlier screen-width exception is removed. The 9pt automatic floor now applies on every screen, including CI's small offscreen screen. Explicit Fit width still opts out.

Root cause: using the minimum font size in the SVG made fitted-down annotation text drive the entire plot zoom. The retained real-app default continuous SVG has 86 text elements at 12.96px (including `Carroll 1997` and all study rows) and two Favours notes at 5.43px. Thus the old floor overshoots by 12.96/5.43 = 2.38674. Automatic zoom falls from 221% to 93%. Predominant font size identifies the body of these R-generated table plots; the renderer records it as `body_text_size`. This changes the flawed minimum-text floor everywhere, not only on compact screens. The ordinary fit calculation and manual zoom behavior remain unchanged.

Native reproduction: same ui.py launcher and source/R/form paths as ../README.md, session batch6body, `start --dark --large-font --size 1024x700`; Ctrl+O continuous.rcms, Return; Analyses dropdown at (848,115), Meta-analysis at (794,176), Run at (941,559). `dark-forest.png` captures 93% automatic zoom: study names and point estimates visible; the CI/forest portion still requires horizontal scrolling. It is much closer to the 63% width fit without violating study-label readability. Session stopped. `continuous-default.display.svg` was copied from this session's application scratch directory before shutdown. `python3 artifacts/qa-batch6/body-fit/inspect-fonts.py` checks the study-label font and prints exact font counts/ratio.

Commands (repository root, source ENV.sh and configure own source/forms/R library as in ../README.md):

```
uv run --no-sync python -c 'from scripts.verify import run_typing; from pathlib import Path; run_typing(Path("build/qt6-verification"))'
RCMS_R_STACK_REQUIRED=1 uv run --no-sync python -m pytest -v tests/r_stack/test_inprocess_rpy2_backend.py::test_inprocess_rpy2_backend_contract
uv run --no-sync python scripts/verify_rcms.py results-window
git fetch origin master
uv run --no-sync python scripts/verify.py pre-push
```

Typing passed with win32 target. The unchanged r_stack contract passed (1 passed, no skip), including `label_pt >= 9`, horizontal scrolling when needed, explicit Fit width, and zoom/resize checks. Results-window E2E passed with its usual numerical and plot-fit assertions; full original evidence path is in results-window.log. No test assertion, golden, or numerical reference changed.

## Deterministic scrollbar resolution

The second CI failure exposed a separate fit feedback path. Automatic readable fit previously left both bars at AsNeeded, unlike explicit width fit's stable decision. Both now calculate from the full viewport, account for horizontal-bar height when deciding vertical overflow, reserve vertical-bar width when necessary, and set both policies from that calculation within one refit. Narrowing cannot undo the vertical-scroll decision and start a show/hide cycle. Manual zoom still uses AsNeeded.

Final corrected-source checks: settled-typing.log (win32), settled-r-stack.log (unchanged contract), settled-results-window.log, settled-ratios-hr.log, and settled-pre-push.log. The final native capture is settled-dark-forest.png, using the same 1024×700 dark/+6pt input and continuous default. Wait for Ready before Ctrl+O; click the native picker's Open button at (975,672) if Return only completes the filename. The native session is batch6settled.

Final ratios-hr: WORKFLOW PASSED; all 54 viewport-settling probes recorded zero resize events (settling-proof.txt and settled-ratios-hr-receipt/steps.jsonl). Final native session stopped. All required unchanged tests passed, with transcripts and receipts retained.
