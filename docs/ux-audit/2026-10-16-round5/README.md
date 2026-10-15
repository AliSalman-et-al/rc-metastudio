# Round five — implementation and qualification in progress

Baseline df71e82; branch ux/audit-improvements. No PR, force push or rewritten history. Every implementation/evidence commit has been fast-forward pushed.

Read [PLAN](PLAN.md) for the failure modes and proof obligations decided before coding, [CHANGES](CHANGES.md) for behavior and evidence, [TESTS](TESTS.md) and [TEST-RUNS](TEST-RUNS.json) for exact commands/outcomes, [FAILURES](FAILURES.txt) for failed transcripts, and [COMMITS](COMMITS.md) for the commit inventory. The [reproduce script](REPRODUCE.sh) reuses the existing installer, recorder, real desktop driver, full profile and numerical oracle.

[NATIVE](NATIVE.json) binds curated unmodified Linux captures to original manifests, runtime, inputs, observations and SHA-256 values. [SCREENSHOTS](SCREENSHOTS.json) identifies historical before captures. [INSTALLED-SOURCE](INSTALLED-SOURCE.json) binds current RCMetaR to pinned R 4.6.1 and the test-owned library. Raw logs remain ignored in raw/ and artifacts/verification/rcms.

The initial strict golden gate passed with no text refresh. [Numerical equivalence](NUMERICAL-EQUIVALENCE.json) initially proved all 415 original fields exactly unchanged, maximum difference 0; final-source preflight/full confirmation is pending. Native qualification now includes the combined diagnostic component-heading before/after proof. The superseded full-round5-accepted pass had R Status: OK and nine live bridge passes, then a stale diagnostic heading expectation failed during desktop collection. It was stopped explicitly and is not qualification. Final preflight and references checks precede a new full profile.


Screen readers, actual OS scaling on Windows/macOS, OS file pickers, all parameter combinations and release packaging remain unqualified. An Opus review and an independent native re-audit follow this implementation handoff.
