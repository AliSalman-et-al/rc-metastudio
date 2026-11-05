# Batch-one native after evidence

All requested surfaces were driven with ui.py on this worktree, using its own generated forms. Light and dark use the default font at 1600×1000 on real Qt/xcb under Xvfb and Metacity. Each screenshot is unmodified and includes the window chrome. Owned sessions were stopped; the sample project was not saved. `manifest.json` records source/build paths and screenshot SHA-256 values; `actions.log` retains the ui.py action sequence (light first, dark, then light focus recapture).

## Reproduce

From the repository root:

```bash
source /home/ali/.t3/qa-env/ENV.sh
export PYTHONPATH=$PWD/src:$PWD
export RCMS_QT6_BUILD_ROOT=$PWD/build/qt6-verification
python scripts/build_qt6.py generate --build-root "$RCMS_QT6_BUILD_ROOT"
python -c 'from scripts.verify import run_typing; from pathlib import Path; run_typing(Path("build/qt6-verification"))'
export RCMS_QA_APP_SRC=$PWD RCMS_QA_BUILD_ROOT=$RCMS_QT6_BUILD_ROOT
UI=/home/ali/.t3/qa-env/tools/ui.py
/home/ali/.t3/qa-env/tools/venv/bin/python "$UI" --session batch1-light start
# Repeat with --session batch1-dark start --dark.
```

Wait for R startup to finish before driving menus. Subsequent calls use the same `--session`. `actions.log` arguments apply after that option; screenshots use paths relative to this checkout.

- On an empty dataset open Analysis: disabled actions are dimmer than Change confidence level.
- Ctrl+N: tiles use sentence case, and Next is disabled. Escape cancels.
- Help → About and licenses: shortened provenance link stays on one line.
- Ctrl+O → amino.rcms in this worktree: untick Prins, capture, and retick it before analysis.
- Analysis → Meta-analysis: from initial focus, four Tabs reach Advanced; the next Tab reaches Run analysis. Both have visible palette outlines. The Run analysis keyboard outline is two pixels, distinct from its default-button outline.
- Run the default binary random-effects analysis; if behind the main window, minimize the main window. Select Text report. Giamarellou shows `0.004 to 1.44`. All 19 studies remain included; pooled OR is 0.77 (0.48 to 1.22).
- Close results and Alt+Tab to restore the main window. Import data → the retained input.csv. Map columns shows the actual `1: study` CSV header, the missing-mapping instruction, and disabled Import.

## Screenshots

| Surface | Light | Dark |
| --- | --- | --- |
| Advanced Tab focus | [light](light/analysis-tab-advanced.png) | [dark](dark/analysis-tab-advanced.png) |
| Run analysis Tab focus | [light](light/analysis-tab-run.png) | [dark](dark/analysis-tab-run.png) |
| Unticked Include (Prins) | [light](light/include-unticked.png) | [dark](dark/include-unticked.png) |
| Disabled menu | [light](light/disabled-menu.png) | [dark](dark/disabled-menu.png) |
| Tiles and disabled Next | [light](light/tiles-disabled-next.png) | [dark](dark/tiles-disabled-next.png) |
| Import mapping/error | [light](light/import-mapping-error.png) | [dark](dark/import-mapping-error.png) |
| About | [light](light/about.png) | [dark](dark/about.png) |
| Text report | [light](light/text-report.png) | [dark](dark/text-report.png) |

## Checks

- Full strict typing, win32 target: passed (`typing.log`).
- `python scripts/code_health.py --base origin/master --head HEAD`: passed (`code-health.log`, `code-health.json`). The flagged outcome-page initialization fell from cognitive/cyclomatic 15/17 to 12/15 by removing redundant label logic. No exceptions/configuration/baseline changes.
- Focused Analysis and wizard GUI checks: 38 passed, one skipped (`gui.log`). The first simplification exposed the direct wizard path's absent metric; that failure is retained compressed in `gui-initial.log.gz`, and the empty-string fallback fixes it.
- Real Qt/R `python scripts/verify_rcms.py amino`: passed, including Return advancement, nonzero report limit, and unchanged frozen numerical contract. Full evidence: `artifacts/verification/rcms/20261105T014131Z-92b22351-amino`.
- No fitted-statistics, R source or golden-number changes.
