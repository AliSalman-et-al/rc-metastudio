# Architecture audit: execution policy and plot ownership

Reviewed recent Qt/R analysis and plot hotspots using the architecture and
codebase-design skills, `CONTEXT.md`, and ADRs 0001, 0003, 0007, 0009 and 0011.
The visual candidate report is retained on this machine at
`%TEMP%/architecture-review-20261029T192210Z.html`. The user authorized fixing
concrete findings, so the three strong candidates were selected directly.

## Findings and changes

| Indicator | Evidence and action |
| --- | --- |
| Implicit coupling | Plot Apply accepted an artifact path but used R globals from whichever plot was loaded most recently. Apply now reloads its own persisted inputs. Complete parameter-load, Apply and export operations reuse the existing reentrant R transaction. |
| Duplication | Binary/continuous execution repeated the same single-request execution policy. One non-diagnostic path now validates cardinality, converts the family and executes the request. Close now uses the existing destructive-action consent guard. |
| Representable illegal states | HR/IRR execution accepted multiple requests and silently ignored all but the first. The execution interface now rejects this configuration before R conversion, preserving diagnostic multi-request execution. |
| Shotgun surgery | Consent and non-diagnostic cardinality each have one policy location, so future changes need not keep separate copies synchronized. |
| Pass-through code | Removed the uncalled `execute_small_study_effects_request` forwarding function and the duplicate binary/continuous private executors. No new adapter was introduced. |
| Validation away from the input seam | Missing plot data/parameter/result files now stop Apply before it writes candidate or persisted artifacts; a missing funnel input also stops export. Cardinality is checked at execution entry. |
| Layering violations | The concrete leak was R operation ordering into plot callers. The plot module now owns that ordering at its existing interface. No new architectural tier is needed. |
| Layer-first folders | The inspected production modules are organized primarily as a flat domain-oriented package. No demonstrated benefit justified moving them into new folders. |
| God files | Large Qt orchestration files exist, but size alone does not establish a useful seam. This pass deletes duplicated policy instead of splitting files into shallow modules. |

The deletion test preserves the plot module: deleting it would spread persistence,
rollback and R-ordering knowledge across callers. Its increased depth gives every
editor leverage through the same interface. Consolidated execution and consent
improve locality without adding an abstraction or changing scientific authority.

## Failure obligations and reproduction

Before implementation, the selected obligations were recorded in the visual
report: plot A must retain its studies/results after B is loaded; B's saved files
must remain unchanged; missing plot inputs must preserve last-good files; extra
HR/IRR requests must be rejected; ordinary and diagnostic execution and
Save/Discard/Cancel must keep working.

Two new production Qt/R scenarios were written before the fixes:

- `project-request-cardinality` captures a complete request through the real
  analysis setup dialog. The pre-fix run at
  `artifacts/verification/rcms/20261029T192633Z-da186f86-project-request-cardinality`
  failed with `Extra analysis request silently ignored: time_to_event`.
- `project-plot-state-ownership` creates two real GUI analyses, loads A then B and
  applies A through the plot interface. The pre-fix run at
  `artifacts/verification/rcms/20261029T192633Z-413f7e8a-project-plot-state-ownership`
  showed A's persisted plot changing from 19 studies and pooled log estimate
  −0.27507354085977564 to B's 18 studies and −0.2582403037419863.

Initial driver setup failures are retained separately and do not count as defect
reproductions. The plot drive calls the production plot interface directly to
control the interleaving; existing editor workflows prove actual buttons,
cancellation, persistence and decoded exports.

After the fixes both scenarios passed, at `20261029T192843Z-aca49a37` and
`20261029T192843Z-5bac2dec` under the same evidence root. The plot scenario also
removes each owned `.data`, `.params` and `.res` file in turn, requires an explicit
error and checks all original hashes after restoring that input. The cardinality
scenario checks both HR and IRR rejection and successful single-request execution.

The shared consent guard was deliberately changed to accept cancelled saves;
`project-unsaved-actions` rejected the unauthorized New action. The candidate
source was restored byte for byte. Command, logs and restored-source hash are in
`artifacts/verification/app-audit/architecture-consent-mutation` and the repeatable
driver is `artifacts/verification/app-audit/consent_mutation.py`.

## Verification and limits

The baseline before these refactors is committed as `f79aee5f`; its
[app audit](ux-audit/2026-10-29-app-verification.md) records the 125-scenario pass,
native checks and numerical evidence. Candidate strict typing passed.

The candidate formal command passed all three bounded models and eight real-code
persistence checks at `%TEMP%/rcms-formal-xpg7ajhj`. The app overview and consent
model still correspond to the shared guard; plot ownership and numerical results
are established by real-code evidence, not those formal models.

Fast verification passed 431 tests with one platform skip, and golden compatibility
passed all 415 numerical fields plus plot/text contracts. Logs are
`artifacts/verification/app-audit/architecture-fast.log`, `architecture-typing.log`
and `architecture-golden.log`; the golden report is
`build/qt6-verification/golden-compatibility-architecture/compatibility-report.json`.
The fresh full profile passed R package build/check, the twice-executed 21-case
Reitsma visual check, all nine live bridge tests, all 127 desktop scenarios in
1670 seconds, the 91-case independent authority matrix and doctor. It is retained at
`artifacts/verification/rcms/20261029T193059Z-8c90f5f9-complete`; native affected
drives are recorded in `artifacts/verification/app-audit/architecture-native.log`.
All 15 native drives passed: eleven plot families, both consent drives, cardinality
and plot ownership. Their editor/persistence/cancellation/export assertions ran
against the real Windows Qt/R composition.

The final teardown audit passed for 10,966 retained artifacts across 143 desktop
and native runs, with complete scenario coverage, matching aggregate and formal
hashes, and every recorded application scratch directory removed. No owned driver
process remained, and the full R lane's temporary library was removed. Retained
commands and results:

- `uv run python artifacts/verification/app-audit/audit_architecture_evidence.py`
- `artifacts/verification/app-audit/architecture-evidence-audit.json`
- `artifacts/verification/app-audit/architecture-process-audit.json`

The checked executable-input digest is
`33bea1146df7c50f0e04ee4b335ab1facb5954e2905f894090eafe1408591f86`.
Documentation updates during the run did not change that digest. This audit does
not assert that all architectural friction is gone or that the current interface
must be preserved. Platform, native-picker, assistive-technology and arbitrary
input limits from the app audit still apply.
