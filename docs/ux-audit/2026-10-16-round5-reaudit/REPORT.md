# RC MetaStudio native round-five re-audit — 16 October 2026

## 1. Executive summary

**IN PROGRESS. No final verdict counts or all-app qualification yet.** Independent read-and-report audit at `ddeef0a` on `ux/audit-improvements`. No application, test or R package edits. The requested folder/date follows the task; the host clock reports 15 October UTC.

Native doctor passed using DISPLAY=:0, xcb, pinned R 4.6.1 and the round-five test-owned library. All 55 source and 24 installed-file receipt hashes match current bytes; see [provenance](PROVENANCE.json). Implementation claims await fresh driving and inspection.

## 2. Scorecard and independent verification

Pending all 83 baseline IDs plus F11–F15. Unexercised paths will remain explicitly unqualified.

## 3. Regressions and the round-five claims

Early binary standard evidence: [figure](screenshots/matrix-twoarm-proportion-standard-figure.png) and [report](screenshots/matrix-twoarm-proportion-standard-report.png) agree on OR 0.761368, 95% CI 0.458516–1.264253, P 0.292012. Intervention/Control names are readable. Duplicate scene weights are absent; standalone context is present. This is not yet a verdict across all families.

## 4. New and remaining findings

F11 is fixed on the fresh single-arm proportion bubble: [native figure](screenshots/matrix-onearm-proportion-meta-regression-figure.png) has no exterior zero line between ticks and Dose. Remaining metric/explicit-bound/export proof is pending. ### R5-01 — Medium: ratio tables leave the standard-error scale implicit

The [OR subgroup table](screenshots/matrix-twoarm-proportion-subgroup-report.png) puts clinical OR 0.746519 beside “Std. error” 0.375206. The estimate/CI are exponentiated; the SE remains on the fitted log scale (`results_display.R`, sequential/subgroup formatters). Sequential rows do the same. A reader copying the table can mistake that number for an SE of the displayed OR. The [round-four counterpart](../2026-10-15-round4-reaudit/screenshots/matrix-twoarm-proportion-subgroup-report.png) already has this label: **pre-existing, not a round-five regression**. No wrong fitted value is alleged.

**Principle:** a quantity's scale belongs with its label. **Recommendation:** label the existing column “SE (log OR)” / corresponding HR, IRR or transformed metric, or add a concise table-local scale note shared by Text, Tables, copy and exports. Preserve existing fitted values and clinical CIs. Regression coefficient tables already explicitly name their log scale.


### R5-02 — Low: the new caption repeats the same identity

The [coefficient figure](screenshots/matrix-reg-coef-standard-figure.png) reads “Regression coefficient · Regression coefficient”. The workspace identity already repeated type and metric; round five carries that duplication into standalone output. “Group: Group” adds little context when defaults are unchanged. The caption itself is a substantial improvement; this is a new copy remnant, not a claim that the old captionless output was better.

**Principle:** every identity fragment should add information. **Recommendation:** collapse identical adjacent type/metric labels in the default caption and preserve investigator-authored captions verbatim. Retain actual outcome, arm and follow-up identity.

Remaining F04 precision detail: the [MD regression report](screenshots/matrix-twoarm-mean-meta-regression-report.png) now prints slope/Z as zero, closing the observed negative-zero case. The [MD subgroup table](screenshots/matrix-twoarm-mean-subgroup-report.png) still prints Qm `1.428745e-31` while its figure uses `0.000000`; round four exported the identical tiny statistic. This is presentation consistency, not a numerical regression. Prefer the selected decimal policy for test statistics, retaining the separate protection for genuinely tiny effects/intervals.

## 5. Microcopy and information design

Pending live and source-string review.

## 6. Coverage matrix

Native doctor and all five binary matrix workflows passed. The independent public-package authority sweep passed 91/91; [receipt](AUTHORITIES.json). Seven of ten matrix families have passed; diagnostic, HR/IRR and shell/output paths are in progress.

## 7. Accessibility

Keyboard and QT_SCALE_FACTOR=1.5 pending. Screen readers, other platforms and actual OS scaling unqualified.

## 8. Ranked next-round list

Pending observations.

## 9. Limits, replay and evidence inventory

Source `docs/ux-audit/2026-10-14-round3/ENV.sh` and export DISPLAY=:0. Run `uv run python scripts/verify_rcms.py doctor --native` first. Its fresh receipt is `artifacts/verification/rcms/20261015T082425Z-d75ac4d2-doctor` (exit 0). Read-only native wrappers copied from round four own settings and inputs under ignored raw/. Run exact commands through `uv run python docs/ux-audit/2026-10-16-round5-reaudit/run.py LABEL COMMAND...`. No screenshots are yet cited as inspected.

Setup attempt: shell reported `/bin/bash: line 2: python: command not found`; no writes occurred. Corrected to python3 for audit-document setup; application commands use uv run python.

Execution interruption: outer matrix shell exit 143 after four completed families; generic-effect orphan briefly overlapped design. Only recorded owned trees were terminated; overlapping partial frames are rejected and the families replayed serially. This is an audit-runner interruption, not a product failure. Native single-invocation replay is now used.
