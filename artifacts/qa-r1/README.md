# Shell QA round 1 fixes

Branch: fix/qa-r1-shell. Source changes: F4, F5, F15, F21, F22, F24. No R code, numerical references, fitted parameters or result calculations changed.

## Commands and environment

From this worktree, `source /home/ali/.t3/qa-env/ENV.sh; export PYTHONPATH=$PWD/src:$PWD`.

- Strict typing (win32 target on Linux): `python -c 'from scripts.verify import run_typing; from pathlib import Path; import os; run_typing(Path(os.environ["RCMS_QT6_BUILD_ROOT"]))'`. Passed; exact expanded command in typing.log.
- `python -m pytest -n 1 -q tests/python/gui/test_qt6_application_shell.py tests/python/gui/test_analysis_failure_safety.py tests/python/gui/test_csv_import_wizard.py`: 43 passed.
- `python scripts/verify_rcms.py results-window`: initial attempt timed out during startup at 600 seconds under machine overload; retry also reached its 600-second bound after step 59 (matrix-configured). F4/F15 assertions and recovery completed before the timeout; the entire scenario did not pass. Both failures retained.
- Full pre-push was started before the user's load restriction, then terminated during code-health. Not a passed qualification. Full pre-push/authority qualification deferred to CI as explicitly requested.

## Real display actions and observations

Driver: `/home/ali/.t3/qa-env/tools/venv/bin/python /home/ali/.t3/qa-env/tools/ui.py --session shell-fix` (called `$UI` below). Launch: `RCMS_QA_APP_SRC=$PWD $UI start --dark --large-font --size 1024x700`; later `$UI start --size 1024x700` for light/default. Both sessions stopped with `$UI stop`. Linux xcb, Xvfb and window manager, real Qt/R application, native file picker.

- F4/F21: `$UI key F1` opened the compact help; `$UI shot ...` retained light/default and dark/large frames. Dark/large text scrolls while OK remains visible on the 700px screen. Three short entry instructions and the shortcut list replace the tutorial.
- F5: closing help (`$UI click 770 562`) exposed readable light foreground on the dark menu/toolbar. F5/shell-dark-large.png. The CI failure used Window/WindowText palette transition; toolbar now explicitly uses WindowText, avoiding a stale ButtonText role in that partial palette.
- F22: `$UI click 294 88`, `$UI key ctrl+l`, `$UI type /home/ali/.t3/qa-env/src/tests/fixtures/rm5/Fleiss1993.rm5`, `$UI key Return`. The native picker returned the wrong-format file; a short message points to File > Import RevMan file, with no mapping wizard. F22/F22-dark-large.png.
- F21: light/default: close help, `$UI key ctrl+o`, double-click amino.rcms at 224,226, `$UI key ctrl+shift+s`. Save Project picker opened. F21/F21-save-as-light.png. No sample overwritten.
- F15: real R E2E invalid-estimator trigger displays `Unknown 'method' specified.` and change guidance, with Details collapsed; selecting DL recovers and produces results. F15/after-light-default.png. The existing E2E assertion checks cause visibility and Details behavior.
- F24: singular/plural now follows the number of imported rows. Real-display light/default native picker loaded retained `one-study.csv`; the wizard displayed “Ready to import 1 study.” See F24/after-light-default.png. Plural behavior remains covered only by existing multi-row import paths.

Original cited screenshots are retained as each F*/before.png. These are historical evidence, not a fresh baseline qualification. Coverage is incomplete: not every finding has before/after screenshots across all four palette/font combinations; F5's exact partial-palette CI trigger was not re-driven locally. Full authority and supported-platform native/package qualification remain for CI. No golden references were regenerated; no known frozen plot/report presentation cases are changed by these shell-only fixes.
