# F1–F3 layout qualification after review and master merge

Source: merge commit c24e1234 (origin/master 6dc1999e). Existing shell/error and calculator changes retained. The calculator report remains REPORT.md; this file owns layout evidence.

## Implementation

- F1: synchronise tab/content geometry after tab creation/removal; activate the strip layout before deciding scrollbar overflow. Keep ElideRight and full-name tooltips. The added 1024×700 visibility check restores window size and active tab before continuing existing drag/reorder checks.
- F2: retain the complete small-study form's minimum height and scroll it. Use required(...) for the content layout.
- F3: stack diagnostic panels; put the second label and selector beside each other, with left-aligned wrapping. Keep horizontal width negotiation so meta-regression stays inside its viewport while row heights remain natural.
- No statistical code or numerical references changed. No golden plot/report cases are expected to change from widget configuration sizing.

## Final local qualification

Linux Qt offscreen with real R, generated forms from /home/ali/.t3/qa-env/qt6. Strict typing targets win32. Source /home/ali/.t3/qa-env/ENV.sh then export PYTHONPATH=$PWD/src:$PWD.

- Strict typing passed: `python -c 'from pathlib import Path; from scripts.verify import run_typing; run_typing(Path("/home/ali/.t3/qa-env/qt6"))'` (`layout-typing-merged.log`, containing full exact Ty command).
- `python -m pytest -n 1 -q tests/python/gui/test_analysis_configuration_layout.py tests/python/gui/test_main_workspace_window.py tests/python/gui/test_publication_bias_dialog.py`: 41 passed, 1 skipped (`layout-gui-merged.log`). Unchanged meta-regression overflow and ElideRight assertions pass.
- Each E2E command below was `python scripts/verify_rcms.py <scenario>`, serially, one owned app at a time. Each evidence directory retains the command, runtime identity, inputs, assertions, screenshots and saved workflow artifacts.

| Scenario | Result | Evidence directory |
| --- | --- | --- |
| `lymph` | passed | `artifacts/verification/rcms/20261104T095226Z-523dcdcf-lymph` |
| `small-study-binary-extended` | passed | `artifacts/verification/rcms/20261104T095320Z-6e8fe63f-small-study-binary-extended` |
| `sheets` | passed | `artifacts/verification/rcms/20261104T095346Z-f8b5ddb1-sheets` |
| `sheets-edges` | passed | `artifacts/verification/rcms/20261104T095421Z-f07ca141-sheets-edges` |
| `sheets-swap` | passed | `artifacts/verification/rcms/20261104T095505Z-89d6b700-sheets-swap` |
| `project-structure` | passed | `artifacts/verification/rcms/20261104T095820Z-2284873d-project-structure` |
| `rm5-import` | passed | `artifacts/verification/rcms/20261104T095852Z-a4713b2d-rm5-import` |

Original before evidence was opened at /home/ali/.t3/qa-round1/user-j5/shots/10-imported.png, contour 20261104T070325Z-8124ebae-plot-workflow-contour/02, and lymph 20261104T070023Z-8b41d774-lymph/04 in the round-one CI evidence tree. The final RM5 frame 14 shows both imported sheet names visibly elided at 1024×700; each tab is clicked and its selected sheet checked. Lymph frame 05 shows the second method label wrapping left-aligned beside its selector.

The exact sheets-edges reorder failure was reproduced in 20261104T093800Z-ead9e03a-sheets-edges. Diagnostic geometry evidence 20261104T094019Z-40f9a9d6-sheets-edges showed four 96px tabs in a stale 208px bar; the fixed merged-source runs pass the original reorder and navigation assertions unchanged.

## Limits

Full native before/after light/dark × default/large-font screenshot matrix remains incomplete. The earlier native session was stopped; final qualification above uses offscreen Qt and does not claim native Windows/macOS/DPI/package proof. Per user instruction, scripts/verify.py pre-push is reserved for CI due shared-machine load. No force push or merge of this PR.
