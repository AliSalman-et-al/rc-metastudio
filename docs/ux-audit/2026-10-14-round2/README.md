# RCMS round 2 and Review 1

Local branch `ux/audit-improvements`, baseline `84fdbc57`. No push or PR.

- [CHANGES](CHANGES.md): review items, implementation commits and evidence.
- [TESTS](TESTS.md): exact final commands, results and native screenshot provenance.
- [PLAN](PLAN.md): scope and failure modes decided before implementation.
- [BENCHMARKS](BENCHMARKS.md): presentation references and statistical authorities.
- [NUMERICAL-EQUIVALENCE](NUMERICAL-EQUIVALENCE.json): all 415 original fields,
  their before/after values, and the independently checked authority identity.
- `screenshots/`: curated native before/after views, including Review 1 output.

From the repository root, run `./docs/ux-audit/2026-10-14-round2/REPRODUCE.ps1`.
It selects the existing pinned, test-owned R runtime/library, installs current
RCMetaR source, generates Qt forms, and runs the required lanes. Run `NATIVE.ps1`
for the serial native screenshot drives. `ENV.ps1` lists the local prerequisites;
the full R-stack lane installs the current source in its own temporary library.

`run.py` retains exact commands, revisions, environment, exit status and log hashes
under ignored `raw/`. Complete Qt action/input/runtime/artifact manifests remain
under ignored `artifacts/verification/rcms/`. Raw earlier round-2 runs are kept
locally, outside the Git index; a checkout needs only the scripts and fixtures to
reproduce final evidence. Other audit folders and user files were left alone.

The original implementation history is available with
`git log --oneline 84fdbc57..d685949c`. Review 1 does not rewrite it.
