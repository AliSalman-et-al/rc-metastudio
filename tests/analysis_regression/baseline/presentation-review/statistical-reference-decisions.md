# Statistical reference decisions

This records the meaning of specific historical reference changes. It does not
authorize further oracle or tolerance changes. Detailed development transcripts
remain in Git history at `docs/ux-hill-climb/STAT-FIXES.md` before its removal.

## Subgroup difference statistic

The displayed subgroup-difference test uses heterogeneity Q from a fixed-effect
fit of the displayed subgroup estimates and their SEs: inverse squared SE
weights, groups minus one degree of freedom, chi-square P value. It replaced a
moderator fit that estimated a shared residual heterogeneity variance.

| Reference | Earlier output | Authorized output | Independent comparison |
| --- | --- | --- | --- |
| Amino subgroup report | Qm/P 0.187/0.666 | Q/P 0.307/0.579 | `meta::metabin(allstudies=TRUE)`, Q 0.3073583, P 0.5793058 |
| Continuous subgroup report | Qm/P 0.226/0.634 | Q/P 0.293/0.589 | `metafor::escalc` SMD and separate DL fits, Q 0.2926188, P 0.5885472 |
| Fleiss fixed IV subgroup | Q/P 4.852384/0.027608 | Q/P 5.680480/0.017155 | Fixed summary-estimate Q |

The [November Windows provenance](2026-11-03-windows-goldens.md) binds the
reviewed presentation refresh. Different SMD variance conventions can produce a
different Q; do not silently change an authority result to force parity.

## Single-study cumulative P value

The explicitly authorized addition was confined to the amino binary cumulative
Gonzalez row (k=1): absent P value became displayed `0.365`, including the same
text cell and duplicate internal archive text. The independent calculation used
`metafor::escalc` OR for 6/27 versus 9/27, followed by `rma.uni` FE Wald inference.
The numerical-field ledger grew from 415 to 416 fields. Archive identity bindings
were updated for that specific addition; this grants no general regeneration
permission.

## Raw-count pooling references

Binary MH uses original counts and metafor defaults, including repeated/subgroup
fits. Peto separates individual-effect correction from pooled raw counts through
`add=c(.5,0)`, `to=c("only0","none")`; single-study Peto fits use its O−E/V
calculation. The stale sequential helper that corrected pooled counts again was
repaired without changing the product or frozen numerical expectations.

Use direct public-package comparisons alongside the frozen release comparisons.
The [testing guide](../../../../docs/testing.md) and [verification skill](../../../../.agents/skills/verify-rcms/SKILL.md)
describe the required source/runtime identity and retained evidence. Historical
success counts do not qualify a current source revision or release package.
