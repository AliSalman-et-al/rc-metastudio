# UX audit work: handoff (2026-10-16)

Branch: `ux/audit-improvements` (from `origin/master`). Not merged; no PR.

**Current state: round six + independent re-audit + release fixes complete; ready for the separate squash merge to master as v0.5.0.** The final release-fix state below supersedes earlier qualification/review checkpoints. No PR or merge was created.


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

Final independent execution inventory: **53 selected maintained native helper scenarios passed**; the 34-case finishing registry completed, including all twelve calculator modes and all eleven plot-editor families with four-format exports. The recorder retains 72 runs (71 exit-zero, one initial options-wrapper failure), plus initial doctor. The corrected diagnostic/HR/IRR options continuation passed. All retained helper manifest hashes verified without mismatch. 209 selected visually reviewed screenshots are committed; incidental frames/logs remain ignored with provenance inventories. The actual exported report was opened in native xedit; its Unicode glyph limitations are distinguished from verified UTF-8 bytes.


## Round five — ready for Opus review

Implementation is complete through 613c2d5 on ux/audit-improvements; later commits retain evidence and collection tooling. Every commit was immediately fast-forward pushed, with no PR or history rewrite. Read [README](2026-10-16-round5/README.md), [PLAN](2026-10-16-round5/PLAN.md), [CHANGES](2026-10-16-round5/CHANGES.md), [TESTS](2026-10-16-round5/TESTS.md) and [contact sheet](2026-10-16-round5/contact-sheet.html).

All eleven priorities are implemented on the exercised paths: panel-clipped bubble guides/data layers, one structured weight representation, readable growing forests/subgroups, editable standalone context and IRR exposure, precision finishing, Linux naming/keyboard/contrast/scaling, labelled Analyses menu with real prerequisite tooltips, calmer structured reports, start/recent recovery and microcopy. The user's high-priority arm-name expansion adds Intervention / Control, neutral Group / Index test, optional real wizard names and actual names across displays/CSV/figures/reports. Stored names/keys remain exact; every remaining Tx source hit is justified as internal or a silent import alias. The bounded pooled-diamond finishing was planned before implementation.

Final `verify_all.py --full --fresh` passed **112 desktop scenarios plus doctor**, current-source R CMD check Status OK, 21 Reitsma visual release cases, nine live bridge checks, strict goldens and **91 independent authorities**. All **415 original numerical fields are exact, maximum difference 0**, with no golden refresh or original fixture/tolerance change. FULL-PROFILE binds all 113 expected receipts and 6,732 artifact hashes. The 25 contact comparisons / 50 frames were inspected; NATIVE retains 48 passed receipts / 5,875 original hashes. All 298 curated PNGs have provenance. Retained GUI launch contracts: 69 passed; other targeted retained checks/types are in TESTS. Every failed or interrupted attempt remains explicit in TEST-RUNS/FAILURES.

Pinned R 4.6.1/test-owned library and installed-source bytes are bound in INSTALLED-SOURCE. R source f3c2911 was frozen before R checks; Qt-only MD text/proof 613c2d5 was frozen before guarded desktop collection. All 112 children share the final source/context hashes in EVIDENCE-INTEGRITY. The collector now selects the owned context and explicit doctor receipt rather than unrelated probes in the broad R/desktop time window; its excluded failed MD probe is retained explicitly, never marked passing.

Next: Opus acceptance review, then the independent native re-audit; neither was started by this implementation agent. Screen readers, actual Windows/macOS OS scaling, native OS picker interaction, every parameter combination and release packaging remain unqualified. Preserve the broader design/statistical-output mandate and the process rules above for follow-up fixes.

## Round five / Opus review 1 — ready for follow-up review

All five findings are implemented and pushed: 0ed0990 gives bundled samples readable arms while preserving every numerical field and explicit legacy fixtures; 932daed fixes caption separation/readability and forest header/footer typography/totals; 8be544f finishes integer count preview, calculator sentence case and inline recent rows; d05df93 repairs the extra subgroup-header rule collision caught in the taste pass. Executable source is frozen at 63b8d0c; later commits are documentation/evidence only. No PR or history rewrite. See [REVIEW1](2026-10-16-round5/REVIEW1.md), TESTS, REVIEW1-VISUAL-REVIEW and the updated contact sheet.

The one final `verify_all.py --full --fresh` passed in 2306.465 seconds: **112 desktop scenarios plus doctor**, R CMD check Status OK, **1,825 R assertions** with one opt-in gallery skip, both **21-case** Reitsma release-visual lanes, **nine** live bridge checks, strict goldens and **91** independent authorities. All **415 original numerical fields are exact, maximum difference 0**. No original fixture, numerical policy or golden archive changed; no golden refresh was needed. BCG's arm direction additionally matches all 13 original event/total rows against pinned metadat.

FULL-PROFILE binds **113 receipts / 6,785 original artifacts**. EVIDENCE-INTEGRITY checks current source/install bytes, all **335 curated frames**, and **15 selected passing native runs**, including all eleven editor families/four decoded exports each. The combined contact sheet has **38 comparisons**, thirteen from this follow-up. All new initial editor views, changed details and relevant before/after frames were inspected. Exact commands/exits and seven recorded nonzero development/integrity attempts remain verbatim, along with the separate evidence-curation failure; first direct integrity output truncation and early capture/source overlaps are stated explicitly. All affected paths have passing replacements.

No requested implementation remains unfinished. Next: parent-owned Opus follow-up, then the independent native re-audit after acceptance. Linux source/Qt proof does not qualify other platforms, actual OS scaling, OS pickers, screen readers, release packages or every parameter combination. Preserve the broader polish mandate and immediate fast-forward push rule.

## Round-five independent re-audit — complete

[Final report](2026-10-16-round5-reaudit/REPORT.md), [scorecard](2026-10-16-round5-reaudit/SCORECARD.json), [findings](2026-10-16-round5-reaudit/FINDINGS.json), [replay/evidence](2026-10-16-round5-reaudit/REPLAY.md).

**83 tracked IDs: 6 fixed / 37 improved / 39 unchanged / 1 regressed. F11–F15: 5 fixed. Combined 88: 11 fixed / 37 improved / 39 unchanged / 1 regressed.** Eleven R5 findings: **1 high / 6 medium / 4 low**. R5-04(long-forest CI-cap overlap) is the sole confirmed round-five regression. The default arm/wizard/CSV/calculator/output naming is much better and legacy researcher names persist, but a reachable built-in `TX Mean: Mean` submenu still violates the all-visible-Tx claim(R5-09).

**First priority: R5-10, high, confirmed stored data loss.** In a real editable QLineEdit/F2 keyboard path, entering SD 0.00001 produces dialog/model SD 0.0; after acknowledging the collapsed-CI warning, Accept/Save/reopen persist 0.0. Independent signal and keyboard probes produced the same saved-project hash. Source fixture bytes were unchanged. Formatter/setter/cell-handler/raw-copy functions and R imputation source match round four; this is a newly discovered source-supported pre-existing defect, not a confirmed new regression. An additional ordinary-mean edit leaves stale derived group CI cells. The observational drives completed with `stored_sd_preserved:false`; do not call them preservation passes. Fix this before more cosmetic finishing or statistical breadth.

All 50 native matrix cells completed; all 100 first figure/report images were visually inspected; 91/91 independent package comparisons passed. All 112 maintained native scenarios were attempted; 111 passed. Unmodified `project-shell` failed two immediate state assertions(normal→maximized; fullscreen→maximized). A separate real-state observation reached correct Qt/EWMH states in 214–296 ms including 200 ms stable observation; shell/guard transactions passed independently. Both maintained failures remain failed. All 12 calculator-mode and 11 editor/four-format workflows completed, with visual control review. Main/setup/results passed at Qt 1.25/1.5/2; targeted pre/post calculator and regression editor also passed at 1.5. Source/install 79 hashes match; application/test/R/sample source bytes were not changed.

There are 153 recorded invocations:145 exit 0 / 8 exit 1. Six failed audit-wrapper entry/setup attempts recovered; two maintained shell assertions remain failed, qualified by separate observed-state evidence. Outer runner exit143 and an ancillary stale-XID activation error are retained separately. [FAILURES](2026-10-16-round5-reaudit/FAILURES.json) keeps verbatim evidence. Qt scaling is not OS-DPI/screen-reader/cross-platform qualification; most picker routes are substituted. Native Gtk template Save and a real text export in xedit were driven. No every-value Cartesian-product or every-export-pixel qualification is claimed. See the final report's full scope, source-label dispositions and inventory.

### Ranked round-six work

1. **R5-10, high:** preserve full-precision raw calculator inputs through editing/Accept/Save/reopen; stop formatted previews from overwriting values, and block invalid commits.
2. **R5-09, medium acceptance gap:** remove the built-in TX Mean menu prefix using existing contextual display identity; preserve internal keys and legacy user names.
3. **R5-04, medium regression:** bound long default/subgroup CI caps to actual row spacing; preserve horizontal intervals and fitted values.
4. **R5-06, medium:** finish BMJ header clearance using measured real arm names, including unequal wrapped lengths; check exports.
5. **R5-03 / F04, medium:** route diagnostic meta-regression coefficient and ML-test tables through selected precision, with consistent readable headings.
6. **R5-01, medium:** put fitted SE scale beside clinical-scale sequential/subgroup estimates in Text, Tables and exports.
7. **R5-11, medium:** make bubble legend entries and line samples follow the actual visible regression/CI/PI components.
8. **D04 / R5-07, existing medium finishing gap plus low copy defect:** use actual eligibility reasons; validate contour fields inline and stop busy state after failure while preserving recovery.
9. **R5-08, low:** make subgroup style choices describe the actual supported layout; eliminate silent fallback promises.
10. **R5-05, low:** finish package-owned Intercept/Moderator/Statistic, diagnostic and validation labels at the display boundary.
11. **R5-02, low:** remove identical type/metric repetitions and uninformative generated defaults from new captions; preserve investigator text.
12. **A01/A05, qualification gap:** extend the completed loaded-project keyboard task to other entry points, focus restoration and screen-reader relationships; retain actual Qt-scale proof and OS limits.
13. **F07 / M01 / H01, low:** finish action-labelled Save/Discard prompts, case consistency, concise contextual guidance and existing plot units/identity presentation.
14. **Platform qualification:** exercise remaining native picker routes and supported packaged targets; do not promote Linux source proof into cross-platform release proof.

Audit-only commits were pushed regularly, fast-forward, to `origin/ux/audit-improvements`; no PR or history rewrite. The [commit inventory](2026-10-16-round5-reaudit/COMMITS.md) and final report supersede all interim checkpoints.


## Round six — final qualification in progress

Implementation is pushed through 8416f96. See [round-six README](2026-10-16-round6/README.md), [PLAN](2026-10-16-round6/PLAN.md), [CHANGES](2026-10-16-round6/CHANGES.md) and [contact sheet](2026-10-16-round6/contact-sheet.html). The input data-loss root cause was handled first. Axis conventions were checked against primary documentation before implementation; the extra mandate and source decisions are recorded after R5-09 in PLAN. Small commits were pushed immediately, fast-forward, with no PR.

All requested code paths have implementation and targeted passing proof; final `verify_all.py --full --fresh` is running against frozen executable source 8416f96. A prior full attempt was deliberately interrupted while fixing a native measured BMJ footer collision and is explicitly not qualification. The review packet retains every recorded nonzero attempt verbatim, including an overly broad diagnostic precision attempt caught by the original numerical gate and narrowed before the final run. Do not infer final qualification from this checkpoint; require FULL-PROFILE and EVIDENCE-INTEGRITY. External Opus review and independent native re-audit remain subsequent steps.

Round-six finishing checkpoint: executable source is now 036a1a5. A fresh profile found diagnostic BMJ axis-title clearance below the retained four-point bound. The device character-line-height fix passed twelve native diagnostic configurations and 24 displayed/exported SVG measurements, minimum gap 6.49 points; the unchanged assertion was not relaxed. A new final full fresh replay is running. The prior partial profile and first 3.90-point formula failure remain verbatim in the round-six FAILURES packet. All 415 original fields were exact in the latest completed strict capture.

Round-six final-test checkpoint: 2af53d7 cleans the last stale Odds ratio (log scale) E2E expectation, asserting the actual natural title below its ticks while keeping all numerical comparisons. Its native review-workflows replay passed; 30 selected native workflows now pass. The prior full profile remains failed (one stale assertion, 66 other desktop passes), not qualification. Owned final `full-qualified-4` runs `verify_all.py --full --fresh` with fail-fast and frozen executable/test bytes; R CMD check passed 1,825 assertions with no failures/warnings and one opt-in skip. Final FULL-PROFILE/EVIDENCE-INTEGRITY are still required. Product source remains 036a1a5; no product change accompanied this test cleanup.

Round-six final focus checkpoint: f4fe5bf fixes the offscreen calculator driver's missing focus after an invalid-CI warning. The trace proved zero editingFinished events and no focused widget; the driver now activates its owned dialog and waits for actual editor focus before typing. Production validation and all numerical assertions stay intact. The prior full profile remains failed (109 passes, three entered-mode failures). All three offscreen recovery replays passed, followed by a complete twelve-mode matrix (three native entered modes, nine offscreen modes). Final full-qualified-5 runs against f4fe5bf; its current-source R CMD check passed 1,825 assertions, zero failures/warnings, one opt-in skip. Full desktop/authority/golden completion and final integrity collection remain pending.

Round-six final contextual-label checkpoint: 4638cf8 removes an OR-only expectation from the shared funnel verification helper. The actual HR/IRR plots were correctly labelled; the failed profile remains failed with 117 passes and two test assertions. Complete native HR and IRR workflows now pass with all six editors/four-format exports. There are 32 selected passing native workflows and 35 before/after pairs / 70 inspected PNGs. Final full-qualified-6 runs against 4638cf8; R CMD check passed 1,825 assertions, zero failures/warnings, one opt-in skip. Product source remains 036a1a5. Desktop completion, numerical/golden/authority gates and final integrity still need their final receipts.


## Round six — ready for Opus review

All requested implementation items are complete on the exercised paths. Product source is frozen at 036a1a5; final executable/test qualification is 4638cf8. Later commits retain evidence/documentation only. All commits were immediately fast-forward pushed to ux/audit-improvements, with no PR or history rewrite. Read [README](2026-10-16-round6/README.md), [PLAN](2026-10-16-round6/PLAN.md), [CHANGES](2026-10-16-round6/CHANGES.md), [TESTS](2026-10-16-round6/TESTS.md), [QUALIFICATION](2026-10-16-round6/QUALIFICATION.md) and the [contact sheet](2026-10-16-round6/contact-sheet.html). This final section supersedes the qualification checkpoints above.

The data-loss root cause was fixed first: full-precision editors/model values are separate from compact painting, supplied/generated input provenance survives undo, unchanged focus commits do not reconvert effects, invalid bounds block Accept, and real keyboard precision survives save/reopen with independent effects/fits. All twelve calculator modes, grid/clipboard/CSV import and all HR/IRR source modes have retained proof. The reachable label sweep covers ten families and every recorded Qt/SVG surface in the full matrix. Source-verified conventional axes persist through Edit plot/reopen/export/rerun; transformed proportions and diagnostic forests are linear natural 0–1 by default, ratios retain log spacing/natural labels, and proportion bubbles retain explicitly labelled fitted scales per the documented decision. Caps, wrapped headers, precision, SE scales, visible legends, contours/eligibility, subgroup style explanations, duplicate/default captions, host contrast/focus and real shell-state waits are addressed. The planned closed-result disposal fix releases retained SVG scenes.

Final `verify_all.py --full --fresh` passed in 2637.782 seconds: **119 desktop scenarios plus doctor**, R CMD check **1,825 assertions**, zero failures/warnings and one documented opt-in gallery skip, both **21-case** Reitsma visual lanes, **nine** live bridge checks, strict goldens and **91** independent authorities. All **415 original numerical fields are exact, maximum difference 0**. All **24 native axis fits/weights are exact**, excluding only elapsed-time metadata. Seven reviewed SE-heading/padding sections were refreshed solely through the sanctioned presentation tool; numerical contracts, tolerances and original fixtures stay unchanged.

FULL-PROFILE binds **120 receipts / 8,298 original artifacts**. EVIDENCE-INTEGRITY verifies current source/install bytes, outer profile logs/authorities, original fixtures, **32 selected passing native workflows**, and **35 comparisons / 70 original PNGs** that were inspected. Diagnostic title/tick clearance is measured in twelve configurations and 24 display/export SVGs: minimum **6.49 points**, unchanged required bound four. The 110 recorded invocations retain all 50 nonzero development/baseline attempts verbatim; three incomplete wrapper interruptions remain separate and unqualified. The final full run has no desktop failures or skips. Earlier profile failures and their passing replacements are explicit, including the last stale/context-free label assertions and the offscreen focus delivery problem; none was relabelled passing.

Next: external Opus acceptance review, then independent native re-audit; neither has been performed by this implementation run. Linux source/native Qt, Qt 1.5/2 scaling and sampled contrast/focus proof do not qualify actual OS DPI, screen readers, Windows/macOS packages, native OS pickers, every parameter/value combination or every exported pixel. The separate 300-case gallery predates the last BMJ physical-width/title correction; final native geometry and the full fresh profile qualify those final bytes. Preserve the broader design/statistical-output mandate and the immediate fast-forward push rule for follow-up fixes.


## Round six — reviewer fixes complete / 0.5.0

The reviewer follow-up and the two additional Default-style requests are implemented
through **06df415**. This section supersedes the old round-six ready-for-review
checkpoint. See the [updated round-six README](2026-10-16-round6/README.md),
[Reviewer fixes PLAN](2026-10-16-round6/PLAN.md),
[CHANGES](2026-10-16-round6/CHANGES.md), [TESTS](2026-10-16-round6/TESTS.md),
[COMMITS](2026-10-16-round6/COMMITS.md) and
[reviewer contact sheet](2026-10-16-round6/reviewer-contact-sheet.html).

PFT PI presentation now uses the pooled harmonic-mean inverse on proportions,
including subgroup-specific sample sizes; six meta/metafor authority comparisons
agree to less than 1e-12, with explicit undefined-inverse fallback. Unnamed Group
spanners are hidden, diagnostic coefficient bounds name logit/OR scales, Default
forest marks share the existing blue accent, journal ink is preserved, and visible
Default labels retain the internal default key. Version sources, changelog, About,
installed RCMetaR and new project manifests are 0.5.0, dated 2026-10-15. Native old
0.4.2 project/settings and save/reopen proof are retained. Screenshot inspection
found and fixed a real Tables-to-figure navigation bug; a failing native assertion
preceded the fix. Exit-zero but visually rejected frames remain explicit.

The single final `reviewer-full-final` fresh profile **passed**, exit 0 in
**3,484.665 seconds**: **122 desktop scenarios plus doctor**, R CMD check **1,825
passes**, zero failures/warnings and one opt-in skip, both **21-case Reitsma lanes**,
**nine live bridge checks**, strict goldens and **91 independent authorities**.
The final capture preserves all **415 original fields exactly**, maximum difference
**0**. FULL-PROFILE binds **123 receipts / 9,224 artifacts** to the frozen source;
EVIDENCE-INTEGRITY additionally binds current install bytes, 35 selected passing
native workflows, curated frames and the retained synthetic
[saved 0.5.0 project](2026-10-16-round6/release-0.5.0.rcms). No baseline refresh was
needed for these reviewer fixes. Fourteen nonzero reviewer attempts remain
verbatim; exit-zero visual rejections remain separate and unqualified.

All 51 reviewer-curated PNGs, 28 additional SVG footer crops and affected native
primary frames were personally inspected; the exact scope/limitations are in
[REVIEWER-VISUAL](2026-10-16-round6/REVIEWER-VISUAL.md). Previous 70-frame evidence is
retained historically. Linux Qt/R proof does not qualify Windows/macOS packages,
actual OS DPI, native OS file pickers, screen readers or every export pixel. Every
commit is immediately fast-forward pushed; no PR or history rewrite is authorized.


## Round six — re-audit and release fixes complete / ready for squash merge

The independent [round-six re-audit](2026-10-16-round6-reaudit/REPORT.md) completed at c37e427. Its eight R6 findings are now repaired on the exercised Linux native paths. Read the final [PLAN](2026-10-16-round6-release-fixes/PLAN.md), [CHANGES](2026-10-16-round6-release-fixes/CHANGES.md), [TESTS](2026-10-16-round6-release-fixes/TESTS.md), [COMMITS](2026-10-16-round6-release-fixes/COMMITS.md), [inspection journal](2026-10-16-round6-release-fixes/INSPECTIONS.md), [contact sheet](2026-10-16-round6-release-fixes/contact-sheet.html) and [replay](2026-10-16-round6-release-fixes/REPRODUCE.sh).

Generated arm names survive both Qt setup and the R forest normalizer losslessly, including names differing after character 80. All three styles reserve the measured full header block below the caption and device top. The stronger assertions failed before implementation; 65 selected frames, including all 24 long-header export renderings, were personally inspected. BMJ single-arm raw headers, ordinary/small-screen dialog sizing, fitted PLN ticks, diagnostic OR coefficient axes, extreme-value notation and HR/IRR secondary Intercept labels are finished. Beta/logit coefficient axes and statistical values remain unchanged.

The single final `full-release` fresh profile passes on executable/test source **07c4f4a**: **123 desktop scenarios plus doctor**, R package **Status OK**, **nine live bridge checks**, **91/91 authorities**, and strict goldens. All **415 original numerical fields are exact, maximum difference zero**, verified again against the full run's capture. No golden refresh, numerical contract, tolerance, exception or fixture change was needed. FULL-PROFILE binds 124 child receipts and every retained artifact. Failed development attempts and visually rejected/incomplete receipts remain failed or explicitly excluded; no original failure was relabelled passing.

Every commit was immediately fast-forward pushed to ux/audit-improvements. Final evidence/handoff commits after 07c4f4a do not change executable source. No PR, merge, tag, force push or history rewrite. The next action is the separately owned squash merge to master for v0.5.0.

No requested Linux repro remains unproved. This is source/native xcb Qt with private R 4.6.1, not packaged Windows/macOS, actual OS-DPI, screen-reader, every native-picker or arbitrary-option qualification. Small-screen checks use an explicit synthetic available rectangle; ordinary-screen proofs use the actual native screen. Original actual exports and all selected before/after frames are retained; raw logs remain ignored.
