# UX audit work: handoff (2026-10-15)

Branch: `ux/audit-improvements` (from `origin/master`). Not merged; no PR.

## Process the user asked for

- GPT 6.1 Sol High does all coding (T3 `delegate_task`, provider `codex`, model `gpt-6.1-sol`, `reasoningEffort: high`).
- Opus reviews every round and sends fixes back until satisfied.
- At the end, GPT 6.1 Sol Low (`reasoningEffort: low`, computer use) re-audits every screen, menu, dialog and results window.

## Scope rules

- No new kinds of statistical analysis. Existing analyses (meta-analysis, subgroup, leave-one-out, cumulative, meta-regression) may be extended with established packages, and workflow features may be improved.
- Presentation of output (report text, tables, figures, aesthetics) is a priority.
- The round-four mandate extends beyond audit IDs: survey launcher, grid/data entry, calculators, menus, dialogs/setup, results, Text/Tables, figures, exports and help; improve existing workflows and design using judgement and standard-tool conventions (RevMan, metafor/meta, Stata, CMA, JASP). Known defects come first, then a ranked plan before implementation. Prefer a few finished changes. No new statistical features or unnecessary abstraction/configuration layers. Retain native before/after evidence for major visible changes. Existing analysis extensions require public-package capabilities and independent proof.
- Existing numbers must stay identical: keep the numerical-equivalence and golden gates green. Any new quantity needs independent verification.
- Follow AGENTS.md and `.agents/skills/verify-rcms/SKILL.md`. Keep commits small. The user requires an ordinary fast-forward push immediately after every round-four commit. If a push fails, wait 30 seconds and retry once before stopping. No force push, history rewrite or PR.

## History

- Original audit: `docs/ux-audit/2026-10-13-native/`
- Round 1: implementation in `2026-10-13-implementation/`, re-audit in `2026-10-13-reaudit/REPORT.md`
- Round 2: plan, changes and tests in `2026-10-14-round2/`, re-audit in `2026-10-14-reaudit/REPORT.md`
- Round 2 re-audit outcome, over 68 findings: 13 fixed, 51 improved, 1 unchanged, 3 regressed

## Round 3: implemented, verification and reviewer handoff

Implementation and proof are in [2026-10-14-round3](2026-10-14-round3/README.md).
The plan and real desktop contracts precede implementation. R2-01 uses explicit
overall-presence metadata; copied/exported reports retain executed identity and
table rows; fixed/diagnostic configuration reflects actual fits; subgroup and
sequential tables reuse fitted package outputs; figures share precision, full
bubble ticks and bounded null references. Native review also caught and fixed
small-effect geometry and sparse weight/estimate overlap before handoff.

The user expanded the round to optimize blocking verification on weak machines.
TIFF now uses a packed raster instead of multiple floating-point images. Five
alternating real exports measured median 51.371→9.007 seconds and peak RSS
5.643→1.199 GiB on the retained 68-million-pixel input. Full dimensions, 600 dpi
and LZW remain; full-image comparison found at most one 8-bit RGB level of
rounding difference. The full profile visits all desktop cases once with bounded independent
offscreen workers. Native driving remains serial. The 300-case gallery retains canonical SVGs and bounded review
previews; publication exports remain checked by real editor drives. Read
[BENCHMARKS](2026-10-14-round3/BENCHMARKS.md) for measurement scope and reproduction.

The pinned R 4.6.1 runtime and persistent library are test-owned under
`build/ux-round3`, with provenance in RUNTIME and INSTALLED-SOURCE. No system R
library or qualified statistical package was modified. Original numerical
oracles/tolerance rows/exceptions remain unchanged; six reviewed report-text
sections and their SHA bindings were refreshed. New fields are independently
verified through public package fits, including package prediction outputs.

The final uncached `273bd6a` profile includes the last spacing correction and
passes all 98 desktop cases, 91 authorities, nine R-stack tests, both 21-case
Reitsma lanes, strict golden checks and exact equality of all 415 original fields.
All twelve final native drives passed; all 26 curated screenshots were inspected;
the final 300-case gallery passed full decoding and SVG checks. The fresh desktop
matrix took 20m13s (earlier serial run 32m16s); these are single observed runs.
The complete warm matrix passed in 35.438 seconds, verifying existing source,
runtime and artifact signatures for every reused case plus a fresh doctor.
`--fresh` requires execution. Source edits and damaged/failed evidence invalidate
reuse. The test-owned exact full-source library is retained for the warm loop;
ENV and both installed-source records document the selections.

Opus review 1 returned seven findings. Their implementation fixes and proof are
complete at `c335356`, with additive REVIEW1-* records in the round-three directory.
Round display-scale bubble ticks, executed-method references, standard heterogeneity
columns, single omission reporting, shared diagnostic notes, explicit overall-flag
validation and scale-relative collapsed ranges are now checked. All four affected
native families and all 12 inspected final screenshots pass. The final uncached
profile passes all 98 desktop cases, 91 authorities, nine bridge tests, both
21-case Reitsma visual lanes, strict goldens and exact equality of all 415 original
fields. Only three reviewed summary texts and archive SHA bindings were refreshed;
no numerical output, policy or archived figure byte changed. Earlier failures and
the first interrupted full attempt remain recorded. All repair commits were
immediately fast-forward pushed. Opus follow-up review is next; the requested
complete low-effort native re-audit remains due after review acceptance.
Source verification was on Linux only; release/package qualification and the
planned old/new canonical gallery comparison are not claimed (old SVGs absent).
See TESTS, FULL-PROFILE and DX-WARM-PROFILE for exact results and limitations.

The implemented scope was:

1. **R2-01 (high): HR/IRR leave-one-out forest plots put estimates against the wrong study.**
   - Cause: `r/RCMetaR/R/ratio_methods.R` supplies only the omission fits, but the sequential renderer in `forest_metafor.R` assumes the first fit is the overall one.
   - Fix: make the data say explicitly whether an overall fit is present, rather than inferring it from position.
   - Prove it with an end-to-end check that each figure row's name, estimate and CI match the report, for HR and IRR (and the other leave-one-out and cumulative paths).
2. **R2-02:** exported reports lose the clinical identity block (outcome, comparison, analysis).
3. **R2-03:** text export puts every table cell on its own line instead of keeping table rows.
4. Remove τ² from fixed-effect results and drop estimator labels that don't apply.
5. Finish the report tables and make them consistent across workflows.
6. Make numerical precision, axis ticks and no-effect reference lines consistent across figures.

See `2026-10-14-reaudit/REPORT.md` for evidence and screenshots.

## Not in git

Raw round logs (about 440 files under `2026-10-13-implementation/` and `2026-10-14-round2/`) exist only on ALI-ELITEBOOK15. They aren't needed to continue; the curated evidence is committed.

## Independent round-three native re-audit

Read [the report](2026-10-14-round3-reaudit/REPORT.md) before the next implementation round. Audit-only changes; no application, test or R source changed. Against 14 October: 68 inherited IDs = **4 fixed, 7 improved, 55 unchanged, 2 regressed**; R2/F baseline additions = **6 fixed, 1 improved, 3 unchanged**. All three R2 regressions are closed on inspected paths. The 50-cell native figure/report matrix is retained and visually reviewed. Maintained registry: 98 passes / one immediate startup-state assertion failure; settled native check passed. Authorities: 91/91. Failed/interrupted attempts remain in the evidence inventory.

Historical round-three re-audit recommendations (the round-four brief supersedes this list):

1. R3-01 (medium): bound sequential null lines to plotted rows, clear of footer text.
2. R3-02 (medium): compact linear bubble ticks and reserve measured metric-title margin.
3. F10 (high): assign subgroup weights by stable row identity; repeated Jaeger names currently produce 98.3% total.
4. F09 (medium): prevent six-decimal weight/estimate and raw-data annotation collisions.
5. F08 (medium): preserve contextual BMJ entered-effect/coefficient axis labels.
6. F05 (medium): name actual tested null and scale.
7. Qualify keyboard, focus, screen reader and real OS scaling.
8. F06 (medium): simplify active calculator layouts.
9. Improve long-figure reading size and standalone clinical/exposure identity.
10. Finish structured reports and F07 vocabulary/help; qualify native IO/recent/persisted preferences.

Historical round-three status (superseded by round-four CHANGES): Historical round-three status (superseded by round-four CHANGES): F04 is improved, not closed: original coefficient Fixture 2 still prints 1.110223e-16 for a zero bound. F08/F09 introduction is unproven; F10 mapping predates round three. No new statistical analysis is requested. Linux evidence does not qualify other platforms, every option combination, filesystem failures, release packaging or full accessibility. Raw logs remain ignored under the new audit's raw directory.

## Round four / Opus review 1 — ready for review

Application source is complete through `ff03295` on `ux/audit-improvements`.
All continuation commits were immediately fast-forward pushed; no PR. The user
recovered the earlier `ca6815c` push before continuation. Original failure and
interruption receipts remain in the [round-four folder](2026-10-15-round4/README.md).

The four review findings and ranked D4-04..07 are implemented: qualified BMJ
3/6-digit/export clearance; measured multiline headers and round transformed
ticks; concise actual-null wording; compact confidence/inference presentation;
a native start page with full/missing recent paths; clearer dataset navigation;
shared native control sizing/icons; result-first report reading and synchronized
sidebar/export actions; publication finishing. CHANGES maps commits and proof.
The [contact sheet](2026-10-15-round4/contact-sheet.html) gives before/after native
comparisons. REVIEW1-VISUAL records actual inspections.

Final `verify_all.py --full --fresh` passed 108 desktop
scenarios plus doctor, R package Status OK, independent authorities/live bridge
and strict goldens. All 415 original numerical fields are exact, maximum
difference 0; no original numerical field, tolerance or exception was changed. Reviewed golden
text only used the sanctioned presentation tool. Retained GUI checks: 186 passed,
one Linux platform skip; changed production Python typing passed. Exact commands,
all failures verbatim and hash-bound artifacts are in TESTS/TEST-RUNS/FULL-PROFILE.
Pinned R 4.6.1 and the test-owned library were used, with installed-source proof.

Next: Opus acceptance review, then the requested independent low-effort native
re-audit. Neither was started by the implementation agent. Accessibility,
OS DPI/file pickers, other platforms and release packages remain unqualified;
no all-option-combinations claim. Preserve the broadened design mandate and the
process rules above for subsequent rounds.

## Round-four independent re-audit — 15 October 2026

The [independent report](2026-10-15-round4-reaudit/REPORT.md) compares against the round-three re-audit. Across 83 tracked IDs: **10 fixed, 30 improved, 43 unchanged, zero confirmed regressions**. The 68 inherited IDs are 4/27/37/0; the additional fifteen are 6/3/6/0. Already-fixed behavior retained is unchanged. New findings: **F11/F12 medium; F13–F16 low**. No new high-severity finding or wrong fitted estimate/CI was established. R3-01/R3-02 and F05/F08/F09/F10 are fixed on inspected paths; F04/F06/F07 remain improved rather than universally closed.

The visible Linux native 50-cell matrix completed, with all 100 first figure/report images inspected. Pinned R 4.6.1, installed-source provenance and doctor passed; independent authorities passed 91/91. Supplemental native shell, calculator, publication, diagnostic, small-study and export outcomes are indexed in the report's OUTCOMES inventory. The options wrapper's initial diagnostic-dialog-class failure is retained verbatim; it is not a product analysis failure. No application, test or R source was changed. Audit commits are pushed individually, with no PR or history rewrite.

Ranked round-five work (existing analyses/workflows only):

1. **F11, medium:** clip/suppress out-of-range bubble null guides.
2. **F12, medium:** unify legacy scene weights with structured Study / Weight (%) output and existing row/component identity.
3. **R03/R17, medium:** improve subgroup/long-forest density without reducing readable type.
4. **R02/R18, medium:** carry available clinical/exposure context into standalone figures and finish existing IRR data presentation.
5. **F04, medium:** finish precision consistently, including negative zero and the separate diagnostic coefficient renderer; preserve genuine small values.
6. **A01/A05, qualification gap:** verify keyboard/focus/screen-reader and actual OS scaling, then repair demonstrated failures.
7. **F14, low:** consistent analysis toolbar labels/grouping at normal widths.
8. **F16/R01, low–medium:** reduce duplicate report headings and structure remaining subgroup-difference prose.
9. **F13, low:** content-height start cards and missing-recent-file recovery.
10. **F07/F15, low:** finish terminology, help/tooltips and label/value spacing.

RCMS is substantially closer to a coherent workbench, but not yet uniformly polished enough to call great software. The next round should finish consistency, output density and accessibility qualification rather than add statistical breadth. The weights concern is real: structured Text/Tables coexist with legacy monospace graphics-scene lines. Heading size alone is reasonable; repetition/margins create the heavy hierarchy. Large start cards and mixed toolbar labelling are unfinished design; Follow-up:first is pre-existing. No claim covers every option combination, OS, release package, filesystem failure or accessibility path. See the report for exact coverage, failed runs and replay/provenance.
