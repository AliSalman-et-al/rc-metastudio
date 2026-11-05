# Round 6 implementation evidence

Base: origin/master 36650a57. Linux xcb, real PyQt6 + embedded R, existing pinned QA runtime. Source supplied through RCMS_QA_APP_SRC=/home/ali/.t3/worktrees/rc-metastudio/t3-609f4836. No R source or golden numerical reference changed.

## Commands

Environment for qualification: source /home/ali/.t3/qa-env/ENV.sh; export UV_PROJECT_ENVIRONMENT=/home/ali/.t3/worktrees/rc-metastudio/t3-713f0f8a/.venv PYTHONPATH=$PWD/src:$PWD RCMS_QT6_BUILD_ROOT=$PWD/build/qt6-verification

- `uv run --no-sync python -c 'from scripts.verify import run_typing; from pathlib import Path; run_typing(Path("build/qt6-verification"))'` (win32 target, typing-final.log).
- `uv run --no-sync python scripts/verify.py pre-push` (qualification.log; earlier attempts retained separately).
- `uv run --no-sync python -m pytest tests/python/gui/test_main_window_automation_launch.py -q` (geometry-tests.log).
- UI driver: `/home/ali/.t3/qa-env/tools/venv/bin/python /home/ali/.t3/qa-env/tools/ui.py --session fix6`.
- Start: `RCMS_QA_APP_SRC=$PWD <driver> start --dark --large-font --size 1600x1000`; stop and restart same session with `--size 1024x700`; also `start --size 1600x1000` for light/default.
- Open amino: Ctrl+O, type `/home/ali/.t3/qa-env/src/sample_projects/amino.rcms`, Return. Analysis menu → Meta-analysis → Run analysis (default DL random OR). Manuscript → scroll to Table 3. Export report → PDF and Word to retained amino.pdf and amino.docx. Source sample not saved.
- Extract PDF: `pdftotext -layout artifacts/qa-r6/amino.pdf artifacts/qa-r6/amino-pdf.txt`. DOCX: extract word/document.xml using zipfile and ElementTree.itertext; retained amino-docx.txt. Assert both texts contain 0.0088 and 0.0086: passed.
- Every session stopped with `<driver> stop`.

## Observations

Original council screenshots copied to before/; implementation screenshots retained in shots/.

- 03-amino and 07-results show unchanged grid/forest lower limits; 10-study-limits shows manuscript Sturm 0.0088 and Van der Auwera 0.0086. Exported PDF and DOCX retain both. Pooled result remains 0.77 [0.48, 1.22]. Text report and Tables use the same manuscript data; no independent native screenshot of those tabs was taken.
- 02-ready: dark/large-font start buttons share height and top baseline. 17-light-ready: light/default start retained.
- 13–15 retain failed intermediate geometry attempts; 18-final-small is the final successful dark/large-font 1024×700 restored shell, with all actions and confidence status on-screen. Native move/resize arrives after initial Show, so the clamp follows maximized native geometry changes. Normal user resizes remain user owned.
- Names are sentence-cased at the presentation boundary, including supplied producer titles. Acronyms remain uppercase. R keys, plot files and numerical payloads remain unchanged. title-consumer-audit.txt lists legacy strings deliberately retained as stable producer/source keys and fixture inputs. No Windows plot references or summary hashes need changing because no plot output changes.
- Missing-column copy omits empty alternatives, with singular for one missing input. Existing CSV GUI coverage passed in qualification; no separate native import drive performed.

## Scope

This is source qualification on Linux, not Windows/macOS package qualification. Full R-stack/authority matrix and Windows exact-package qualification are CI-only in pre-push. Native screenshots cover light/default and dark/large, not every cross-product of theme/font. No native small-study funnel screenshot was taken after the title-only change. Original numeric golden data is untouched.

Final qualification: all local pre-push stages passed (win32 typing, code health, Python fast/golden, GUI 364 passed/1 skipped, packaging contracts 73 passed/8 skipped). Focused normal-resize geometry suite: 64 passed. Fresh `git fetch origin master` before push still resolves to 36650a57. No tests or numerical oracles were loosened.

## Windows clamp follow-up

Fetched the user's ed534400 title correction unchanged. CI run 42048349263 / job 127318316724 rejected a 1024×689 client resize on an already maximized Windows window. Maximized native frames include hidden resize borders outside availableGeometry: clamping that outer frame subtracts decoration space from a client rectangle Windows already manages. Runtime clamping now checks the client geometry for maximized windows and does nothing if it fits; an actually off-screen maximized client returns to normal state before applying the existing outer-frame/client-size conversion. Normal frames retain the outer-frame check. The frame setter skips unchanged client sizes and positions.

The fatal-warning test and warning handling are unchanged. `windows-clamp-pre-push.log` retains the complete `uv run --no-sync python scripts/verify.py pre-push` command and win32 typing transcript. Native Linux dark/large 1024×700 restart retained in shots/19-client-clamp.png and 20-client-clamp-ready.png, using the same RCMS_QA_APP_SRC and ui.py session fix6 command above. Session stopped afterward. Windows native proof must come from CI, not this Linux host.

The initial follow-up pre-push attempt (`windows-clamp-pre-push.log`) was terminated by SIGTERM (exit 143) during fast tests, without an assertion failure or completed summary. It is not a passing qualification. The clean retry is retained separately in `windows-clamp-qualification.log`.

Follow-up clean retry passed all local stages: win32 typing, code health, Python fast/golden, GUI (including the unchanged fatal-warning shell test), and packaging contracts. No test changes or warning suppression. This establishes Linux native behavior and Windows-target typing, not execution on Windows.
