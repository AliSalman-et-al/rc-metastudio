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

## Round-five independent re-audit — in progress

Read [incremental report](2026-10-16-round5-reaudit/REPORT.md). Started at ddeef0a; product/test/R source untouched. Fresh native xcb doctor passed; all 55 source and 24 installed receipt hashes match. Independent authorities 91/91. All ten native five-workflow matrix families passed and their first figure/report pairs were visually inspected and committed. No final 83-ID verdict counts yet. Early findings: R5-01 medium (implicit log-scale SE in ratio tables, also present in round four); R5-02 low (repeated type/metric in new default captions); R5-03 medium (selected six decimals bypassed in diagnostic regression tables, also present in round four). F11 exterior guide repaired on inspected paths; other round-five claims remain under fresh qualification.

Evidence commits so far: 591d572, 9f6c690, 1e30b74, 8fc2e24, 2565bce. Outer shell exit143 interrupted the matrix after four families; the surviving generic child briefly overlapped design. Only owned trees were stopped; partial overlapping frames rejected; serial generic replay passed. Serial queue lives under ignored `2026-10-16-round5-reaudit/raw/queue.py` with PID/state/log files; do not launch another native drive while its active state is non-null. Its state file records completion per run. Complete it and curate actual frames before final verdicts. Planned round-six ranking is provisional: explicit table scale labels, finish category-aware statistical precision, remove caption redundancy, then remaining accessibility/OS/picker qualification. Preserve the broader all-app/statistical-output mandate.

Re-audit checkpoint: R5-04 is a confirmed medium round-five regression. Long default-style HR subgroup CI caps now span 1.41 row spacings (33.22/23.54 pt), versus about 1.01 before. See HR-CAP-GEOMETRY and inspected same-sample before/after frames. Rank its row-aware cap sizing first for round six. Current new-finding set: three medium (including one regression) and one low; final scorecard still pending.

All 50 matrix first figure/report pairs are now visually inspected and pushed. Fresh shell/design replays passed; native xedit opened the actual export. All seven bundled samples passed open/analyze/save/reopen without changing original archives; BCG independently matches all 13 pinned source rows. Current findings: three medium (R5-04 is a confirmed regression) and two low (R5-02 and R5-05). Full native helper queue resumed after successful sample replay. Final scorecard and scaled/editor/calculator qualification remain in progress.

Long-name re-audit adds R5-06 medium: BMJ's count-header rule crosses the first wrapped clinical arm-name line. Default and RevMan handle the same names cleanly. Native frame and font/vector geometry confirm the intersection; no same-input old-runtime replay, so not labelled a confirmed regression. Current six findings: four medium and two low, including one confirmed round-five regression. Prioritize long HR cap sizing and BMJ actual-name clearance before diagnostic precision/SE scale and copy finishing. The raw primary dispatcher is PID 1245904 (launcher1245901), with QUEUE-STATE; a scaled follow-up dispatcher (launcher1264679) waits for its finished receipt before fresh 1.25/2.0 checks. Do not overlap native drives.

The incremental report now includes every inherited ID and F11–F15. Provisional83-ID counts:6fixed,37improved,39unchanged,1regressed (R17). Five additional F11–F15 provisionally fixed on observed paths; remaining native registry/scaling finishing is explicitly pending. Do not treat these as final counts until qualification finishes.

Supplemental inspection adds R5-07 low: nine-study IRR setup blames the effect measure when the existing report correctly gives the below-ten-study eligibility reason. Same fallback exists at round-four source, so not a regression. Current seven findings:fourmedium,threelow,oneconfirmedround-five regression. Provisional rankedround-sixlist is now in REPORT.

### Round-five independent re-audit — naming/option checkpoint

Audit-only commits through `cf7254d` are pushed. The 50-cell native matrix and all seven bundled sample figure/report pairs are independently inspected. The fresh 175-step arm-name scenario passes: blank defaults, custom names, duplicate rejection, actual calculator/report/CSV labels, three styles, save/reopen and preserved legacy names. Source label review classifies all137 hits in `2026-10-16-round5-reaudit/LABEL-INVENTORY.json`; surviving visible package vocabulary is R5-05 and REPORT §5, not a global-key rename request. The 171 native option/menu states have contact-sheet review and exact inventories. Diagnostic presentation/export sweep has also passed.

Still provisional:83 IDs =6fixed/37improved/39unchanged/1regressed; F11–F15 =5fixed. Seven findings remain4medium/3low, including one confirmed round-five cap-height regression. Remaining native registry, scale1.25/1.5/2 and complete loaded-project keyboard/dirty guard finishing are serially queued; do not report those as passed yet. REPORT is incremental. `REPLAY.md`, embedded driver sources and ignored raw queue-state/receipts support continuation without losing evidence.

### Round-five re-audit — scale checkpoint

Fresh native `review1-design` runs passed at Qt scale1.25,1.5and2.0; start/setup frames were visually inspected and retained in the re-audit `screenshots/`, with `SCALES.json`. Pinned Run/Cancel and scaled start cards remain usable. These qualify application-level Qt scaling on this Linux host, not OS DPI or screen readers. The two sampled grid foreground/background pairs passed4.5:1 contrast assertions, not a universal contrast audit.

Dirty Open Save/Discard and cancelled Save As assertions passed. A complete keyboard continuation has two audit-driver failures (F10 did not open a popup; Home/Down selected Effect-size tools rather than Meta-analysis), retained verbatim. Toolbar Tab/Space entry is reachable; the corrected arrow-selection continuation is queued serially. Do not turn these wrapper assumptions into a product regression or count the unfinished task as passed. Remaining broad native registry continues after the bounded replay.
