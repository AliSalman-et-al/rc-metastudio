# RC MetaStudio native round-five re-audit — 16 October 2026

## 1. Executive summary

**IN PROGRESS. No final verdict counts or all-app qualification yet.** Independent read-and-report audit at `ddeef0a` on `ux/audit-improvements`. No application, test or R package edits. The requested folder/date follows the task; the host clock reports 15 October UTC.

Native doctor passed using DISPLAY=:0, xcb, pinned R 4.6.1 and the round-five test-owned library. All 55 source and 24 installed-file receipt hashes match current bytes; see [provenance](PROVENANCE.json). Implementation claims await fresh driving and inspection.

## 2. Scorecard and independent verification

Pending all 83 baseline IDs plus F11–F15. Unexercised paths will remain explicitly unqualified.

## 3. Regressions and the round-five claims

Early binary standard evidence: [figure](screenshots/matrix-twoarm-proportion-standard-figure.png) and [report](screenshots/matrix-twoarm-proportion-standard-report.png) agree on OR 0.761368, 95% CI 0.458516–1.264253, P 0.292012. Intervention/Control names are readable. Duplicate scene weights are absent; standalone context is present. This is not yet a verdict across all families.

## 4. New and remaining findings

F11 is fixed on the fresh single-arm proportion bubble: [native figure](screenshots/matrix-onearm-proportion-meta-regression-figure.png) has no exterior zero line between ticks and Dose. Remaining metric/explicit-bound/export proof is pending. No new finding yet confirmed.

## 5. Microcopy and information design

Pending live and source-string review.

## 6. Coverage matrix

Native doctor and all five binary matrix workflows passed. The independent public-package authority sweep passed 91/91; [receipt](AUTHORITIES.json). Remaining families and shell/output paths are in progress.

## 7. Accessibility

Keyboard and QT_SCALE_FACTOR=1.5 pending. Screen readers, other platforms and actual OS scaling unqualified.

## 8. Ranked next-round list

Pending observations.

## 9. Limits, replay and evidence inventory

Source `docs/ux-audit/2026-10-14-round3/ENV.sh` and export DISPLAY=:0. Run `uv run python scripts/verify_rcms.py doctor --native` first. Its fresh receipt is `artifacts/verification/rcms/20261015T082425Z-d75ac4d2-doctor` (exit 0). Read-only native wrappers copied from round four own settings and inputs under ignored raw/. Run exact commands through `uv run python docs/ux-audit/2026-10-16-round5-reaudit/run.py LABEL COMMAND...`. No screenshots are yet cited as inspected.

Setup attempt: shell reported `/bin/bash: line 2: python: command not found`; no writes occurred. Corrected to python3 for audit-document setup; application commands use uv run python.
