# QA round 3 batch 2b

Source: 7646d481, branch fix/qa-r3-batch2b. Linux x86_64, real R / PyQt6; strict typing targets win32 as required by the repository. No R, calculator, import, meta-regression labels, or numerical reference changes.

## Startup (A)

Measured before edits with `uptime`: load averages 2.01, 1.81, 2.08. `source /home/ali/.t3/qa-env/ENV.sh; export PYTHONPATH=$PWD/src:$PWD; RCMS_PROFILE_STARTUP=1 python scripts/verify_rcms.py amino` retained phase times in startup-before.json: visible 1793846786.7922602; ready 1793846793.1840916 (6.392 seconds). This machine did not reproduce 64–90 seconds at that initial load. Later load rose above 20.

`compose_application` starts R from a QTimer timeout on the GUI thread. No existing background initialization path exists; embedded R ownership is unchanged. Chosen smallest fix: disable the shell, show the wait cursor and explain that controls become available after startup. Restore controls/cursor on success and failure. The E2E asserts the disabled/wait/message state before processing the startup timer and enabled state once real R is ready.

Before: before-light-startup-qa.png (original A evidence). After state is asserted by the real Qt/R driver; no claim that startup became asynchronous or faster.

## Results focus (F/G)

Before: before-dark-focus-qa.png (original I reproduction). The setup dialog closes *after* delivering its result, restoring focus to the parent. Close the successful setup dialog before delivering results, then show/raise/activate results. E2E asserts the active results window after Run analysis, before evidence capture raises any windows. Initial native attempt found the immediate activation inadequate; a queued activation still raced on the second native fit; final implementation fixes the ordering directly.

After: after-light-result.png and after-dark-large-result.png, opened through real-display ui.py Run analysis.

## Fonts (I)

No fixed label/grid point sizes were found. On xcb, style polish installs class-specific system fonts: requested app font 16 pt; QLabel/QTableView 10 pt, combo 16 pt. Reapplying the application font after installing the shared control style produces 16/16/16. Offscreen did not reproduce the class-specific reset.

Before: before-light-large-setup-qa.png (original I) and before-dark-large-analysis.png (this worktree before font fix). After: after-dark-large-grid-real.png, after-dark-large-setup.png. Default light: after-light-grid.png, after-light-setup.png. Labels, values and grid now scale together. Calculator source is untouched.

## Plot/report (H)

Zoom now restores the horizontal origin after scaling, preventing clipped study names when returning to the initial zoom. E2E explicitly pans right at enlarged zoom and asserts horizontal origin after zooming back. Real-display dark-large zoom sequence: after-dark-large-zoom-return.png.

The on-screen report skips empty sections, prints Supplementary details once, and uses the existing manuscript references once instead of appending them again. After: after-dark-large-settings.png; before: before-light-settings-qa.png. Report content/statistics and exported manuscript model are unchanged.

## Reproduce

Environment: `source /home/ali/.t3/qa-env/ENV.sh && export PYTHONPATH=$PWD/src:$PWD`.
Typing exact command and win32 target: typing-final.log (also pre-push-final.log).
Targeted E2E: `python scripts/verify_rcms.py amino`, evidence manifest/steps/runtime/stdout retained here. Complete raw evidence remains under artifacts/verification/rcms/20261105T025553Z-bf32743f-amino.
Real display: `RCMS_QA_APP_SRC=$PWD /home/ali/.t3/qa-env/tools/venv/bin/python /home/ali/.t3/qa-env/tools/ui.py --session b2b start [--dark --large-font]`; Ctrl+O, amino.rcms, Analysis > Meta-analysis > Run analysis; zoom Up Up Down Down; Settings. Session is stopped after capture. Screenshots marked qa are copied from the provided round-three evidence, not new captures.

Qualification and remaining scope are recorded in the PR. No numerical goldens regenerated; on-screen report presentation changes affect all text-report cases. Request review of those presentation differences rather than updating frozen references.

Pre-push completed successfully in pre-push-passed.log: strict typing, code health, Python fast/golden, GUI, packaging contracts. Full statistical authorities and platform package qualification remain CI-owned. A final committed-head pre-push invocation is also retained separately. Native amino at the default 120-second bound passed first result focus/zoom/report assertions but timed out during its second fit under heavy load (native-timeout-*); a 300-second retry of the queued activation failed the second focus assertion. After fixing close-before-deliver ordering, fresh native xcb proof passed both analyses, focus/zoom/report checks, numerical oracle and PDF export (native-manifest.json/native-steps.jsonl/native-stdout.log). Exact retry command: `DISPLAY=:121 RCMS_PROFILE_STARTUP=1 python -c 'import sys; from scripts import verify_rcms; verify_rcms._scenario_timeout = lambda scenario: 300; sys.argv = ["scripts/verify_rcms.py", "amino", "--native"]; raise SystemExit(verify_rcms.main())'`. The harness limit alone was extended; application behavior and assertions were unchanged.

Final successful native run: artifacts/verification/rcms/20261105T030735Z-3daa90a8-amino (retained native-* files). It exercised both 2-digit and 3-digit analyses, the oracle and PDF export. The source bytes include the close-before-deliver ordering; Git HEAD advanced while the run was active without changing those source bytes. The earlier offscreen e2e-* files establish the first implementation; final native-* files are the final implementation proof.

Before/after evidence also includes light-large startup (disabled controls and waiting text), grid and setup; see after-light-large-*.png. Raw report model and exports remain unchanged; only the interactive text-report document removes duplicate headings/references.

Final display matrix: default light, default dark, large light, large dark. Corresponding after-*-grid/setup/result captures retain each rendered surface. Startup feedback was captured during real startup in after-light-large-start.png and after-dark-start.png. The original before captures do not constitute an exhaustive four-way startup screenshot matrix; the E2E disabled/cursor/readiness checks establish the state transition independently of theme.

## Review follow-up: startup copy

The [startup-copy proof](startup-copy/REPORT.md) supersedes startup text in the original captures: the primary line is `Starting… · Untitled dataset` until R is usable, and the temporary message is exactly `Starting R…`. The existing E2E now checks both strings and the transition to Ready. Fresh dark and light/large-font startup/ready captures and qualification transcripts are in that directory.

## Review follow-up: SVG readability

The [font regression proof](font-regression/REPORT.md) supersedes the old zoom/initial-size implementation: manual zoom is applied once; automatic SVG sizing keeps a 9 pt text floor with horizontal scrolling; explicit Fit width may shrink below the floor. The unchanged ≥9 pt study-label assertion and added +6 pt check passed in both requested scenarios. Master including #568 was merged before qualification.
