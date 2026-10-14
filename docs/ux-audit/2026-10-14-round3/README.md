# RCMS audit round 3

Branch: `ux/audit-improvements`. Fast-forward pushes are authorized; no PR.

- [PLAN](PLAN.md) records failure modes and proof obligations before implementation.
- [CHANGES](CHANGES.md) maps findings to commits and observed behavior.
- [TESTS](TESTS.md) records exact commands, results, failures, and coverage limits.
- [INSTALLED-SOURCE](INSTALLED-SOURCE.json) binds the test-owned installation to source and installed file hashes.
- [NUMERICAL-EQUIVALENCE](NUMERICAL-EQUIVALENCE.json) retains all 415 original values and their observed counterparts.
- [OBSERVATIONS](OBSERVATIONS.json) retains every native row comparison, public reference, and copied/exported report payload.
- [SCREENSHOTS](SCREENSHOTS.json) binds curated, unmodified PNGs to their original action captures.
- [DX-WARM-PROFILE](DX-WARM-PROFILE.json) verifies the complete 35.4-second warm matrix.
- [VISUAL-REVIEW](VISUAL-REVIEW.md) records inspection of all final screenshots.
- [DX-RESUME](DX-RESUME.json) proves invalidation, artifact verification and failed-case behavior.
- [FULL-PROFILE](FULL-PROFILE.json) binds all desktop scenarios and current-source statistical gates.
- [COMMITS](COMMITS.md) lists every round commit.
- [BENCHMARKS](BENCHMARKS.md) records resource changes, repeated measurements and output-preservation limits.

`REPRODUCE.sh` runs the required gates and native drives from the repository root.
`ENV.sh` selects the persistent, test-owned R 4.6.1 runtime and dated binary library
under `build/ux-round3/`, including the byte-identical retained full-profile library. `NATIVE.sh` runs the native family scenarios serially.
Raw transcripts remain under ignored `raw/`; desktop manifests, projects, plot
files, and action screenshots remain under ignored `artifacts/verification/rcms/`.
Curated screenshots and compact observations are retained in this directory.
`curate.py` recreates these from the exact passing native run labels in `raw/`.

The Linux setup uses the exact R archive and SHA-256 from
`scripts/build-linux-package.sh`, the Noble binary installer, and a private
`libxcb-cursor0` extracted from the repository's pinned archive. The rpy2 API bridge
is built in `.venv` against that runtime. No system R library or qualified
statistical package is modified. See TESTS for setup commands and launcher details.

The final fresh profile and all twelve native drives pass. All 415 original
numbers are exactly unchanged; all 300 current gallery cases decode successfully.
Opus review and the post-review complete re-audit remain the next process steps.
