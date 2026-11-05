# Run 41956137300 follow-up

Downloaded artifact: RCMetaStudio-0.5.1-windows-x64-diagnostics, artifact ID
13384395013. Original diagnostic files retained in run41956137300-diagnostics.tar.gz.

The missing qualification condition is **locale SVG byte identity**, not an absent
smoke output. The original staged-package English SVG hash is 870b3337…;
German is 29a295fe…. Both locale summary hashes match each other and the pinned
61ea84ba… expected summary. All scale checks, exit statuses and log markers pass.
The exact-extracted archive's English and German SVG hashes both equal 29a295fe….
inspection.log reproduces rejection of the staged smoke and acceptance of the
extracted smoke with the current inspector. No expected hash or equality was changed.

The original upload does not include these SVG bytes, only their hashes and
now-unavailable runner AppData paths. It cannot reveal the rendering difference.
The saved English/German .rcms projects are byte-identical. Replaying both through
the source application's --automation-package-analyze entry produces byte-identical
SVGs (70faa942…), retained here with raw JSON output. This Linux source replay
does NOT establish frozen Windows correctness or explain the Windows difference.

The assembler now copies base/English/German SVG files into packaged-smoke.plots
under qualification before hashing them. Existing qualification upload paths
retain that directory. The inspector reports this specific locale hash mismatch,
instead of the unhelpful generic incomplete-evidence message. The strict check
is retained. A subsequent Windows run is needed; package cause remains unresolved.

Options E2E: assert_report pinned the statistic header to literal z/t. The
intended header t (df = 18) is correct and is now checked exactly using the held
result's df. No fitted values, Methods producer, R code or golden values changed.

Commands:
- source /home/ali/.t3/qa-env/ENV.sh; export PYTHONPATH=$PWD/src:$PWD
- prepend $PWD/build/rcmetar-lib to RCMS_R_LIBS/R_LIBS/R_LIBS_USER.
- strict typing: exact command in typing-package.log, win32 target PASS.
- python -m pytest tests/python/fast/test_packaged_automation_dispatch.py tests/packaging/contract/test_windows_distributable_contract.py -q
  => 19 passed, 5 platform skips (package-tests.log).
- python scripts/verify_rcms.py options-binary initially hit the existing 120s
  timeout on the shared host. Reran each scenario with:
  python -c 'import sys; from scripts import verify_rcms; verify_rcms._scenario_timeout = lambda scenario: 600; sys.exit(verify_rcms.main())' options-binary
  (same command for options-continuous/options-diagnostic).
  Binary and diagnostic PASS. Concurrent continuous was terminated with exit 143,
  no assertion traceback; isolated retry PASS. The repository timeout is unchanged.
  options-proof.tar.gz retains all five runs, including the two incomplete attempts.
- Source --automation-package-analyze replay: QT_QPA_PLATFORM=offscreen and
  RCMS_PACKAGE_LOCALE=en_US/de_DE on the respective downloaded locale projects.

No Windows package pass is claimed. No package comparison was relaxed.
