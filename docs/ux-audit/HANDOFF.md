# UX audit work: handoff (2026-10-14)

Branch: `ux/audit-improvements` (from `origin/master`). Not merged; no PR.

## Process the user asked for

- GPT 6.1 Sol High does all coding (T3 `delegate_task`, provider `codex`, model `gpt-6.1-sol`, `reasoningEffort: high`).
- Opus reviews every round and sends fixes back until satisfied.
- At the end, GPT 6.1 Sol Low (`reasoningEffort: low`, computer use) re-audits every screen, menu, dialog and results window.

## Scope rules

- No new kinds of statistical analysis. Existing analyses (meta-analysis, subgroup, leave-one-out, cumulative, meta-regression) may be extended with established packages, and workflow features may be improved.
- Presentation of output (report text, tables, figures, aesthetics) is a priority.
- Existing numbers must stay identical: keep the numerical-equivalence and golden gates green. Any new quantity needs independent verification.
- Follow AGENTS.md and `.agents/skills/verify-rcms/SKILL.md`. Keep commits small. The user authorized an ordinary fast-forward push after every round-three commit, including the previously unpushed nine commits. Stop on any failed push. No force push, history rewrite or PR.

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

Opus review is next; it has not been performed by this implementation agent.
After review fixes, the requested complete low-effort native re-audit remains due.
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
