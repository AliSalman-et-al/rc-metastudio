# Shell cleanup

## Agreed behavior

- **Import data** is the single File, toolbar, start-page, and Welcome entry for
  CSV, Excel `.xlsx`, and RevMan `.rm5`. The file determines which existing review
  opens. The spreadsheet mapping page can select another supported file, including
  switching to RevMan review. Pickers no longer advertise `.xls`; selecting one
  through All files explains how to save it as `.xlsx`.
- Save/Discard/Cancel appears only after an import review is accepted. Cancelling
  the picker, wizard, review, or Save As preserves the current project. Imports
  still replace the current project and produce an unsaved project.
- Project/readiness status and confidence share one native status-bar row,
  vertically centered, with project status left and confidence right. Existing
  elision, tooltips, state updates, and font inheritance remain.
- Quick start, its F1 binding, and its unused dialog are removed. Actual application
  shortcuts remain. Help contains About.
- Summary of findings and its dedicated editor, Copy, DOCX, and PDF exports are
  removed. Shared Results export infrastructure remains. Generic project settings
  still preserve previously saved certainty ratings and comments without special
  compatibility code or a schema change.

## Verification

Evidence is under `artifacts/verification/shell-cleanup-20261113/`.
`obligations.md` records expected behavior and failure cases before implementation.
`drive.py` and `commands.sh` retain the repeatable native proof and exact commands.
`native-corrected/` and `native-corrected-1.5/` contain inputs, saved/reopened projects,
step records, and light/dark/menu/import/status screenshots.

- Repository-wide strict Ty, win32 target: passed. Command and transcripts:
  `artifacts/verification/typing/20261113T115724-18b1c33a/`.
- 86 affected GUI checks passed: 84 in the first run, then both native subprocess
  checks passed with the locally unpacked XCB cursor library on their library path.
- Ten retained workspace transaction checks passed, including CSV undo, failure
  rollback, and progress behavior.
- Ninety CSV/parser and project-format checks passed.
- All 133 maintained E2E scenarios collect after removing the obsolete summary
  scenario. Full-suite collection was attempted but failed in three existing
  modules that initialize embedded R during collection.
- Native Linux XCB drives passed at 1× and 1.5×. They use real parsers, Qt widgets,
  mapping/review dialogs, save/reopen, and the repository's explicit R boundary
  double. Proof covers valid CSV/XLSX/RM5 routing and uppercase extensions,
  rejection before save authorization, invalid XLS/XLSX/RM5 and unsupported files,
  cancelled Save As, accepted replacements, Welcome and mapping-to-RevMan routing,
  same-row status geometry, and historical settings retention.

## Limits

The real desktop doctor timed out. The maintained R-stack setup then confirmed
that this host's R 4.3.3 cannot satisfy the pinned R 4.6.1 policy. Full-suite
collection also fails with an embedded-R symbol mismatch. Logs retain these
failures. No statistical, Windows/macOS, package, native OS file-picker, or
screen-reader qualification is claimed. Native drives substitute only test-owned
file-picker paths and the explicit R boundary.

## Independent review

Opus 5.5 Medium approved the shell cleanup with no required GUI changes. Its
review identified two nonblocking evidence defects: the 1× narrow captures were
still maximized, and the test palette left alternate table rows dark. The final
drive explicitly restores the window, waits for native geometry, asserts the
requested width, and sets a contrasting alternate-row palette. Corrected drives
passed at both scales. Earlier captures remain as superseded evidence.
