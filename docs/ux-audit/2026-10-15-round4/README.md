# Round 4 — UX implementation and proof

> Historical draft retained from the interrupted session. The user successfully
> pushed `ca6815c`; origin was observed at that exact commit. `resume-bmj-binary`
> now passes natively at 3/6 digits, with 6-digit four-format exports. Fresh
> captures were inspected: pooled-label/totals and footer/tick clearance are
> correct. See REVIEW1-RESUME.json. Remaining review work and final aggregate
> qualification are still open; statements below describe the earlier session.

Branch: `ux/audit-improvements`, baseline `7938292`. No PR; every commit was
immediately fast-forward pushed through `0f21212`; the push after `ca6815c`
exited 143 with no output. Work stopped under the hard scope rule. Opus review and the independent native re-audit
remain separate, subsequent steps.

[PLAN](PLAN.md) records failure modes before code, including the user's expanded
design mandate. [CHANGES](CHANGES.md) maps each item to commits and evidence.
[TESTS](TESTS.md) and [TEST-RUNS](TEST-RUNS.json) retain commands, exits, hashes and
verbatim failures. [COMMITS](COMMITS.md) lists the commits. [REPRODUCE](REPRODUCE.sh)
uses round-three's runtime, installer, command recorder and numerical oracle.

The changes preserve fits and improve existing output and workflows: bounded
sequential references; compact measured bubble axes; identity-correct subgroup
weights; measured raw/weight/CI columns; contextual axes and row precision;
named fitted nulls; active calculator inputs with pinned results/actions;
consistent vocabulary/help; structured calculation/weight tables and pooled
sentences; consistent actions and a genuinely pristine startup baseline.

Runtime: pinned R 4.6.1 and the persistent, test-owned round-three library.
[INSTALLED-SOURCE](INSTALLED-SOURCE.json) binds source and installed RCMetaR bytes;
[RUNTIME](RUNTIME.json) records the observed native runtime. Statistical authority
packages were not modified, and no system R library was used.

[SCREENSHOTS](SCREENSHOTS.json) binds the unmodified native captures to their
commands and observed state. [VISUAL-REVIEW](VISUAL-REVIEW.md) records which frames were actually
inspected and which remain unreviewed. Curated before/after pairs preserve their original provenance.
Public-package weight comparisons include duplicate HR/IRR and binary/continuous
names, original included-row indexes, individual weights and 100% totals.

**Round four is unfinished.** Final qualification has not passed. Its first run
failed 23 stale presentation assertions, and its next run was deliberately
interrupted after native inspection found two BMJ collisions. The latest BMJ fix
was installed but its native invocation ended without a sealed manifest when the
required push exited 143. Full-profile and current-head numerical proof remain due.
Evidence documentation and curated frames below are local, uncommitted drafts.
See [STOP](STOP.json) and TESTS. The original
415-field comparison is in [NUMERICAL-EQUIVALENCE](NUMERICAL-EQUIVALENCE.json).
Only three reviewed null-description texts were refreshed with the sanctioned
tool; numerical oracle values, tolerances and exceptions remain unchanged.

Limits: Linux source verification only; screen reader, keyboard-only traversal,
OS scaling, long-figure reading size and standalone exposure context remain for
later rounds. These representative drives do not qualify every supported option
combination, file-system failure or release package.
