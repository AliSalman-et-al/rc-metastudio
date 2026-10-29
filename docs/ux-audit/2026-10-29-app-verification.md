# App verification and redesign-safe acceptance

## Purpose and acceptance boundaries

The app supports evidence synthesis and interpretation of meta-analysis results.
The verification contract protects that purpose, not the present interface.

| Protected behavior | Presentation/implementation that may change |
| --- | --- |
| Correct study data, stable identities, inclusion, selected effect source and persistence | Table layout, editors, navigation and widget classes |
| Package-authoritative estimators, uncertainty, transformations, method qualifications and independent numerical tolerances | Plot style, typography, colours, report organization and explanatory wording |
| Users can reach and complete supported import, editing, analysis and export tasks | Menus, toolbars, shortcuts, page/dialog organization and click sequences |
| Undo, Cancel, failed operations and explicit discard preserve the promised data/consent behavior | Confirmation design and how drafts are presented |
| Information and controls remain readable, discoverable and operable, including relevant keyboard/focus paths | Exact pixels, window structure and incidental labels |

Drivers and implementation-specific layout checks may need adaptation after an
intentional redesign. Preserve the behavioral assertion or replace it with an
equivalent assertion for the new design. A changed locator is not by itself a
product regression, and an attractive screenshot is not proof of correct data or
statistics. Changes to scientific meaning or supported capabilities need an
explicit requirement/ADR decision; baseline refresh is not authorization.

## Work performed

- Ran the maintained native Qt lane. Its first attempt stopped at a broken
  `pytest.exe` launcher; invoking pytest through the selected Python interpreter
  repaired the entry point without changing the tests. The retry passed 350 core
  GUI cases, 47 additional layout cases, calculator/Results/shell probes, all 14
  remaining native surfaces at 1× and 1.5×, and failure teardown probes.
- Ran current-source R build/check, the twice-executed 21-case Reitsma visual
  release check and all nine live R bridge checks. Stopped that profile before
  desktop completion while new drivers were still being edited. This interrupted
  aggregate is not recorded as a full-profile pass.
- The independent authority matrix passed 91 cases. Golden compatibility passed
  all 415 frozen numerical fields and its plot/text contracts. An initial golden
  invocation used an unsupported output-directory name and was rejected; its log
  is retained alongside the successful retry.
- Ran the retained fast/golden lane: 431 passed and one platform skip. The skip is
  not counted as coverage of a POSIX teardown contract on Windows.
- The repository's strict typing invocation with generated Qt module search paths
  passed, as did both generator and both local skill validations. A bare `ty check`
  invocation lacked those required paths and was not used as the typing gate.
- The fresh complete desktop matrix passed all 125 scenarios in 1810 seconds,
  followed by doctor. Separate real-R native drives passed all eleven editable
  plot families, including persistence, cancellation and decoded exports in four
  formats.

## Added coverage and formal property

`project-unsaved-actions` exercises New/Open keyboard shortcuts, Import/Quit File
menus and window Close. Cancel, cancelled Save As and a genuine filesystem save
failure must retain live data, the destination and dirty state. Successful saves
authorize subsequent actions and are reopened through production persistence.
`project-unsaved-discard` exercises explicit discard with cancelled New/Import
wizards, Open and Quit; the existing file must remain unchanged on discard.
The only substituted boundary is the OS picker path. Real prompts, editors,
actions, serialization and file I/O execute. No numerical fake is used.

The first native run reached a legitimate application close and exposed a recorder
assumption: it tried to capture a deleted MainWindow. The driver now records that
the window closed instead of requiring the old window to remain alive. The test
also avoids requiring the same model object after cancellation; equal data/state
is the protected behavior.

Repeated offscreen drives exposed a second harness race. The unexpected-dialog
watchdog could run after an expected message appeared but before its handler was
scheduled. The shared modal driver now registers its expected message handler
before launch and restores the registration on exit, including nested/error paths.
The watchdog still rejects unexpected messages outside that registered operation.
Both new workflows passed offscreen and natively after the repair. Failed attempts
remain available as evidence; diagnostic instrumentation was removed.

The interactive statechart's embedded SVG maximum width prevented its zoom slider
from enlarging the chart. Removing that cap restored zoom; rendered-browser
measurement confirmed enlargement from 726 to 1089 CSS pixels at 150%.

`UnsavedActions.tla` explores 13 states for one clean/dirty action request, Cancel /
Discard / Save, and installed / cancelled / failed save results. Its invariant,
`AuthorizeOnlyWithConsent`, permits destructive continuation only for clean work,
explicit discard, or an installed save. It constrains user consent, not a GUI
layout. The passing chart and shortest failing trace are retained in
[`unsaved-report.md`](../formal-verification/unsaved-report.md) and
[`unsaved-broken-report.md`](../formal-verification/unsaved-broken-report.md).

The deliberately broken model allows continuation after save-picker cancellation.
Its shortest counterexample has four steps: unsaved action request → choose Save
→ cancel Save As → action incorrectly allowed. The corresponding real-code scratch
change (`self.save() is True` → `self.save() is not False` in the two guards) made
the real GUI drive reject an unauthorized New wizard. Original source bytes were
restored, and the ordinary formal command passed again. This is a demonstrated
defect detector, not a bug found in the production consent guards.

## Evidence locations

All commands ran from the repository root with generated forms in
`build/qt6-verification`, R 4.6.1 and the current-source RCMetaR 0.5.0 in the
test-owned `build/verification/skill-proof-library` (or the full R lane's isolated
copy). Pinned package/runtime identity appears in every desktop `runtime.json`.

| Check | Command / evidence |
| --- | --- |
| Native Qt full lane | `./scripts/verify-qt6.ps1 -Section Full`; `artifacts/verification/app-audit/native-qt-full-retry.log`; native capture manifests below `build/qt6-verification/native-*` |
| R package/bridge and Reitsma checks | `verify_all.py --full`; completed stages in `artifacts/verification/rcms/20261029T183003Z-2427be51-complete/00.log` |
| Independent numerical authorities | `analysis_authorities.R artifacts/verification/app-audit/authorities.json`; corresponding `.log` |
| Frozen golden compatibility | `scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-app-audit`; `compatibility-report.json` and `artifacts/verification/app-audit/golden-retry.log` |
| Retained fast/golden checks | `scripts/verify.py fast --skip-r-evidence`; `artifacts/verification/app-audit/fast.log` |
| Fresh desktop matrix | `verify_all.py --fresh`; `artifacts/verification/rcms/20261029T185126Z-c96fde37-complete` |
| Native plot families | `scripts/verify_rcms.py plot-workflow-<family> --native`; exact evidence directories printed in `artifacts/verification/app-audit/native-plots.log` |
| Native consent drives | `artifacts/verification/rcms/20261029T185146Z-408cc5ea-project-unsaved-actions`; `20261029T185231Z-e260c92c-project-unsaved-discard` |
| Consent mutation | `artifacts/verification/app-audit/unsaved-mutation/command.json` and `real-code.log`; child evidence is named in that transcript |
| Formal baseline and broken consent config | `%TEMP%/rcms-formal-vyj22y7m`; model/report copies, TLC output and actual inputs retained there |

The broad suite includes ordinary/advanced analyses, all supported dataset families,
calculators, small-study effects, structure, covariates, save/reopen, menus, report
text/tables, and eleven editable plot families with decoded exports. Its current
scope comes from the maintained feature map; it does not prove every possible
parameter or dataset.

The teardown audit rechecked all 10,824 artifact hashes across 139 passed desktop
and native runs, checked complete scenario coverage and confirmed every recorded
application scratch directory was gone. No owned desktop-driver process remained.
The repeatable command and audit implementation are retained as
`artifacts/verification/app-audit/audit_evidence.py`; its result is
`evidence-audit.json` in the same directory. The aggregate source digest is
`4cc9f63ad059056928f8593a079a8668dee4947c14536642275463b5438fb516`.
Documentation-only corrections during the run did not alter this executable-input
digest. This records the baseline before the subsequent architecture refactor.

## Remaining boundaries

Native OS picker behavior, assistive-technology operation, other operating systems,
release packaging and all data/parameter combinations remain outside this Windows
source audit. Native layout probes with fixture plots do not prove scientific
plotting; real-R plot drives and independent numerical checks provide that separate
evidence. Formal checks cover the named bounded models, not every pixel or the
whole Python/R implementation. New functionality requires new behavioral evidence,
not preservation of old screens.
