## Summary

Add checks for three surviving statistical/import mutants without changing product code or frozen references:

- Continuous fixed entered estimates → direct metafor FE comparisons for t, Knapp–Hartung and ad hoc inference. Existing continuous authority cases used z; nondefault inference covered binary random effects only.
- Raw IRR preview → direct metafor interval comparison in the existing sheets E2E drive, with variance 0.361111 rather than 1. Pooled-analysis comparisons did not check this transient bridge interval.
- Unmapped XLSX date-year → existing parser test file. The wizard always supplies a mapping, so its date-year scenario bypasses the mutated fallback.

## Evidence

Base → mutant → restored proofs and exact commands are retained in `artifacts/statistical-mutants/`, alongside the three exact patches from origin/ci/planted-bugs. Each mutant is applied individually with git apply and reversed before the next. Desktop inputs, R expression, actual/expected values, screenshots and runtime versions are retained in `artifacts/verification/rcms/`.

Authority: R 4.6.1, metafor 5.0-1, meta 8.5-0. The executable R reference code is in the existing analysis_authorities.R; JSON records independent actual/expected results. No existing oracle was regenerated.

Repository-wide strict Ty passed with --python-platform win32 before GUI execution. Collection: 1011 tests. Desktop proof uses Linux Qt offscreen and a warm pinned runtime; this is targeted source verification, not release or full-matrix qualification.

## Merge Danger

**Door:** two-way

**Blast Radius:** tests

No statistical implementation, assertion tolerance or existing reference values changed. XLSX fallback has no GUI caller without a mapping, hence the focused parser check.

All three proofs completed with exit codes **0 → 1 → 0**:
- ci-z-instead-of-t: fails `entered continuous fixed t pval`.
- bridge-ci-width: fails the independent lower/upper interval comparison.
- xlsx-year-column: fails date-year normalization (date rejected outside the Year column).

Restored authority run: 103 comparisons passed. Both restored Python checks passed. Product source diff is empty after reversal.
