# F1–F3 layout implementation evidence

Branch: fix/qa-r1-layouts. Source-only Linux Qt verification, strict typing target win32. No statistics, numerical references, or forms changed.

## Commands

Source `/home/ali/.t3/qa-env/ENV.sh`, then `export PYTHONPATH=$PWD/src:$PWD`.

- Strict typing: `python -c 'from pathlib import Path; from scripts.verify import run_typing; run_typing(Path("/home/ali/.t3/qa-env/qt6"))'`; transcript `typing-final.log`.
- `python -m pytest -n 1 -q tests/python/gui/test_analysis_configuration_layout.py tests/python/gui/test_publication_bias_dialog.py`; transcript `gui-final.log`.
- `python scripts/verify_rcms.py lymph`: passed, evidence `artifacts/verification/rcms/20261104T083514Z-e55b7dbd-lymph`.
- `python scripts/verify_rcms.py small-study-binary-extended`: passed, evidence `artifacts/verification/rcms/20261104T083611Z-a13fedb2-small-study-binary-extended`.
- `python scripts/verify_rcms.py rm5-import`: tab assertions passed and captured `14-0-rm5-visible-tabs.png`, but complete scenario timed out at 240 seconds under machine overload; evidence `artifacts/verification/rcms/20261104T090437Z-8b291f15-rm5-import`. The final tab minimum-size adjustment followed this capture and still needs a targeted rerun.

Original before images were inspected at `/home/ali/.t3/qa-round1/user-j5/shots/10-imported.png`, contour `20261104T070325Z-8124ebae-plot-workflow-contour/02`, and lymph `20261104T070023Z-8b41d774-lymph/04` under the round-one CI evidence tree.

Real-display attempt: `RCMS_QA_APP_SRC=$PWD /home/ali/.t3/qa-env/tools/venv/bin/python /home/ali/.t3/qa-env/tools/ui.py --session layouts start --size 1024x700`, File → Import RevMan → this worktree's `tests/fixtures/rm5/Fleiss1993.rm5`. Captures in `F1/` contain named tabs but extra input created another empty sheet: these are incomplete proof, not the exact two-sheet acceptance artifact. Session stopped with `ui.py --session layouts stop`.

## Remaining qualification

Full before/after light/dark × default/large-font native screenshot matrix, final sheet sizing rerun, and old-layout red runs remain incomplete. CI owns `scripts/verify.py pre-push` per the user's machine-load instruction. No numerical golden files changed; no golden presentation cases are expected to change because these edits affect widget configuration geometry only.

Final strict typing passed. Final serial GUI run: 33 passed, one skipped; locale subprocess timed out at its unchanged 30-second bound. Focused retry `python -m pytest -n 1 -q tests/python/gui/test_analysis_configuration_layout.py::test_dot_and_comma_decimal_locales_produce_equivalent_analysis_requests` passed (1 passed in 2.07s), transcript `gui-locale-retry.log`.
