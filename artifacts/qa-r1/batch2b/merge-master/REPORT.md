# Merge current master 8ba18fc6 into #566

Final merge commit: c84436cf; parents 426234d9 and 8ba18fc6 (current master including #567/#568/#569). The preceding merge 426234d9 integrated d2d4b277 while #567 was landing. Both are ordinary merge commits; no history rewrite.

Only `.agents/skills/verify-rcms/features/plots.md` conflicted. Kept both the automatic 9 pt SVG floor/manual zoom documentation and #569's plot-edit/cumulative coverage documentation. Product files merged automatically: blocked-action tooltips/status tips, moderator-values note and cumulative caption coexist with Results activation, supplementary-report rendering and the text-size/zoom fix. No readability assertion or numerical reference changed.

Environment: `source /home/ali/.t3/qa-env/ENV.sh && export PYTHONPATH=$PWD/src:$PWD`.
Reinstalled merged R source (`65a17fae545b75eb054d2241815d757de049a5b7` Git tree) with `"$RCMS_R_HOME/bin/R" CMD INSTALL -l "$PWD/build/rcmetar-lib" r/RCMetaR`; current/r-install.log retains output. Scenarios prepend that test-owned library to RCMS_R_LIBS/R_LIBS/R_LIBS_USER; runtime.json records it first.

Typing: repository-wide strict Ty, win32 target, full command/transcript in current/typing.log; completed before GUI drives.
Scenario commands:

- `python scripts/verify_rcms.py ux-improvements`
- `python artifacts/qa-r1/batch2b/font-regression/drive_font.py results-window 15`
- `python scripts/verify_rcms.py plot-edit`
- `python scripts/verify_rcms.py project-axis-sequential`

The first two retain the unchanged ≥9 pt SVG study-label assertion, +6 pt font check, actual Run-analysis focus, zoom, reporting, tables and advanced workflows. The latter two exercise merged tick validation/BMJ toggles and cumulative ordering, including their numerical comparisons. Full raw artifacts remain in artifacts/verification/rcms; selected proof is retained here.

Required local lane: `python scripts/verify.py pre-push`, transcript current/pre-push.log. Native Windows/R DLL package qualification and the full authority matrix remain CI-owned; no local Windows execution is claimed.

The current/ directory is authoritative for the final combined merge; the earlier d2d4b277 qualification finished before the user requested #567 too and is superseded by current/. Current proof records the fresh R library and preserves the original text-size assertion.

Final combined-source targeted runs all passed: ux-improvements, results-window launched at 15 pt, plot-edit and project-axis-sequential. Proof is in current/proof/ with manifests, runtimes, transcripts, observation steps and selected screenshots. Study labels remained 9.340182688 pt in the default run and 9.191489362 pt in the initial 15 pt run; the +6 pt checks passed unchanged. The new plot-edit and cumulative tests retained their numerical comparisons. Full raw evidence retains all generated files beneath artifacts/verification/rcms.

Final combined-source pre-push passed every local stage: strict typing, code health against 8ba18fc6, fast/golden, GUI and packaging contracts (current/pre-push.log). Full Windows R-stack/package qualification remains CI-owned.
