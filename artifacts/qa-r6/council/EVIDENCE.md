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

## Full R-stack CI follow-up (run 42048349263, job 127318315107)

Downloaded the completed job log with `gh api --allow-escape-sequences repos/AliSalman-et-al/rc-metastudio/actions/jobs/127318315107/logs`; retained as ci576-r-stack.log. The six desktop failures were sheets-legacy, binary and continuous subgroup, diagnostic fixed inverse-variance, manuscript-export-direct and project-reviewer-colours.

- Sentence-case title consumers still expected Sensitivity Summary / Specificity Summary / Diagnostic Odds Ratio Summary. Updated exact display strings in consumers and fixture keys, while leaving R producer keys alone. The in-process R bridge contract also expected the old ordinary-funnel display title. Audited src, r, tests (including both R suites), scripts and .agents; r-stack-consumer-audit.txt retains the search.
- Subgroup results omit input_params. Study values therefore first formatted with the bridge's fallback precision, then were rounded again by manuscript presentation: continuous Carroll became 0.0945 then 0.095. The versioned request now carries its requested study precision to the held forest values; those raw numbers are formatted once, then retained verbatim by the manuscript. Coefficient and matrix precision paths are unchanged. Initial reproduction and complete exact-row difference are in r-stack-continuous-before.log / r-stack-difference.log.
- Mantel–Haenszel/Peto plot values contain None for non-estimable studies. Formatting float(None) raised TypeError and prevented Results opening. Only finite numeric values go to the shared effect formatter; other values retain the existing missing-value formatter and Not estimable row. The real manuscript workflow exercises both estimators and all export formats.
- Report and observer suffix consumers now remove the sentence-case ` summary`. Study-row verification still compares the entire ordered tuple exactly; it compares the already presented held cells instead of rounding them a second time. No cells are omitted and no numeric tolerances or oracle values change.
- r-stack-numeric-proof.txt confirms every numeric value in both changed fixtures is identical (419 + 341 values). Only label strings changed; no numerical reference was regenerated. No plot output changed.

Strict win32 typing passed before the targeted real-R drives (r-stack-typing-final.log). The initial targeted attempt was invalidated by executable-source changes during collection and is retained as failed evidence; the final targeted run freezes executable inputs throughout.

### All four logs from run 42050640242

Read checks 127326291338 and shards 127326291698, 127326291481, 127326291319 before pushing; full downloaded logs retained alongside all-shard-trace-audit.txt and all-shard-failures.txt (34 named E2E scenarios). The failed Results paths are tested by both manuscript modes, summary-of-findings, binary MH, ratio IRR and audit references. The remaining failure traces identify exact report-row comparisons or diagnostic section-title keys. All named E2E scenarios are selected explicitly in all-shard-local.log; no scenario is removed or marked xfail.

Title normalization moved to analysis_results._section_fields, the single final field validator for text and image sections. It changes title only; source_key and value_key are never cased. Existing proper-name handling is retained in result_sections.sentence_case_title. The r_bridge import alias preserves the user's parametrized title test without maintaining a second formatter.

Numeric-contract label strings changed, so its byte count and SHA-256 in baseline/manifest.json were refreshed; the numerical identity proof remains 419 identical values, with tolerances and independent numerical comparisons untouched. The earlier pre-push failure on the integrity check is retained, not called a pass.

### Final verification results

- `all-shard-pre-push-qualified.log`: full `uv run --no-sync python scripts/verify.py pre-push` passed all stages, including win32 typing, fast/golden, 364 GUI passed/1 skipped and 73 packaging passed/8 skipped. No numerical assertion/tolerance was relaxed. The one GUI consumer update changes only the scene heading lookup from Cumulative Forest Plot to Cumulative forest plot; its geometry assertions are identical.
- `all-shard-local-qualified.log`: exact selection of all 34 named failing E2E scenarios plus the explicit-section bridge contract, using `uv run --no-sync python -m pytest <exact nodes> -n 2 -q`. Result: 34 passed, one failed. The 33 other E2Es and bridge contract passed; IRR passed its original missing-results failure but then hit a caption-width assertion on this host's 796×796 offscreen window. The assertion was left unchanged.
- `ratios-irr-native-qualified.log`: reran the complete unchanged IRR scenario with `xvfb-run -a -s '-screen 0 1600x1000x24' uv run --no-sync python scripts/verify_rcms.py ratios-irr --native`. Passed, exit 0, 214 retained action steps. Native IRR screenshot, full steps, logs and runtime copied here. This isolates the extra local offscreen viewport limitation without product changes outside this fix.
- `final-scenario-evidence.tsv`: all 34 named E2Es have passed manifests with exact command, input hashes, runtime, screenshots and retained workflow/export paths. Copies of those manifests are committed in final-manifests/. Full original evidence directories remain on disk. Every checks/shard failure is covered; Linux/native proof does not claim Windows execution.
- During development, superseded runs and the original source/integrity failures are retained separately. `all-shard-local-qualified.log` and the native IRR follow-up are the final results; earlier mixed runs are not called passing evidence.
