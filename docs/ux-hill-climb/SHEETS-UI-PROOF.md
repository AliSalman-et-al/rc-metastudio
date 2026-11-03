# Sheet UI proof

Environment: `source build/sheets-baseline/ENV.sh`, including the worktree-owned
`build/sheets-r-library`. Commands ran from this worktree.

All six scenarios passed. Numerical contracts were unchanged.

| Command | Evidence directory under artifacts/verification/rcms |
| --- | --- |
| `uv run --no-sync python scripts/verify_rcms.py amino` | `20261030T234533Z-0d18d8fb-amino` |
| `uv run --no-sync python scripts/verify_rcms.py continuous` | `20261030T234553Z-163eab39-continuous` |
| `uv run --no-sync python scripts/verify_rcms.py ratios-hr` | `20261030T234609Z-58c220f5-ratios-hr` |
| `uv run --no-sync python scripts/verify_rcms.py ratios-irr` | `20261030T234838Z-a5665745-ratios-irr` |
| `uv run --no-sync python scripts/verify_rcms.py analysis-data-diagnostic` | `20261030T235223Z-777ac3cf-analysis-data-diagnostic` |
| `xvfb-run -a -s '-screen 0 1920x1080x24' uv run --no-sync python scripts/verify_rcms.py sheets --native` | `20261030T235159Z-577f2680-sheets` |

Each directory retains the exact invocation, runtime identity, input project,
widget screenshots, observations and pass manifest. The sheets drive uses actual
Qt widgets under Xvfb/xcb. It exercises add, double-click rename, duplicate-name
feedback, row independence and undo, Ctrl+PageDown, mouse drag reorder, Delete
menu confirmation and undo, reciprocal binary effects with identical counts,
two-swap exact portable state equality, and save/reopen equality. File-picker
results are redirected to a test-owned path; native OS file-picker UI is not tested.

Screenshots: `screens/sheets-after-main.png` (1600×828, amino with two tabs) and
`screens/sheets-after-analysis.png` (631×437), matching the before-shot dimensions.
