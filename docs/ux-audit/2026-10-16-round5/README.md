# Round five — implementation and qualification in progress

Baseline df71e82; branch ux/audit-improvements. No PR, force push or rewritten history. Every implementation/evidence commit has been fast-forward pushed.

Read [PLAN](PLAN.md) for the failure modes and proof obligations decided before coding, [CHANGES](CHANGES.md) for behavior and evidence, [TESTS](TESTS.md) and [TEST-RUNS](TEST-RUNS.json) for exact commands/outcomes, [FAILURES](FAILURES.txt) for failed transcripts, and [COMMITS](COMMITS.md) for the commit inventory. The [reproduce script](REPRODUCE.sh) reuses the existing installer, recorder, real desktop driver, full profile and numerical oracle.

[NATIVE](NATIVE.json) binds curated unmodified Linux captures to original manifests, runtime, inputs, observations and SHA-256 values. [SCREENSHOTS](SCREENSHOTS.json) identifies historical before captures. [INSTALLED-SOURCE](INSTALLED-SOURCE.json) binds current RCMetaR to pinned R 4.6.1 and the test-owned library. Raw logs remain ignored in raw/ and artifacts/verification/rcms.

The final-source strict golden preflight passed without refreshing any golden. [Numerical equivalence](NUMERICAL-EQUIVALENCE.json) proves all 415 original fields exactly unchanged, maximum difference 0. The combined diagnostic/reference presentation drive now passes, with same-project before/after captures. The complete fresh profile `full-round5-complete` is running on committed implementation 8c77873; no executable source or test changes are allowed during this run. Final full qualification is pending.

Resume: inspect raw/full-round5-complete.log and its recorded complete-run evidence directory. Once the recorder finishes, collect_full_profile.py full-round5-complete must verify all 112 desktop scenarios plus doctor, R-stack, authorities and strict goldens; rerun numerical_equivalence.py against build/qt6-verification/golden-compatibility-r-stack-v2. Then update EVIDENCE-INTEGRITY, final TESTS/README/CHANGES/COMMITS and HANDOFF, render the inspected contact sheet with T3 html_render, commit/push the final evidence, and confirm a clean worktree and matching remote. Superseded full profiles and every failure remain recorded.


Screen readers, actual OS scaling on Windows/macOS, OS file pickers, all parameter combinations and release packaging remain unqualified. An Opus review and an independent native re-audit follow this implementation handoff.
