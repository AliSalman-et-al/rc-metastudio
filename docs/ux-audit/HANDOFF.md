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
- Follow AGENTS.md and `.agents/skills/verify-rcms/SKILL.md`. Keep commits small. Do not push or open a PR unless the user asks.

## History

- Original audit: `docs/ux-audit/2026-10-13-native/`
- Round 1: implementation in `2026-10-13-implementation/`, re-audit in `2026-10-13-reaudit/REPORT.md`
- Round 2: plan, changes and tests in `2026-10-14-round2/`, re-audit in `2026-10-14-reaudit/REPORT.md`
- Round 2 re-audit outcome, over 68 findings: 13 fixed, 51 improved, 1 unchanged, 3 regressed

## Next round: three regressions plus the audit's top five

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
