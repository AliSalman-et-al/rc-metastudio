# Slice 4: per-study calculators

Computed estimate/CI fields use four display decimals, with scientific notation
for extreme magnitudes. The analysis unit retains exact values; unchanged field
commits do not parse the rounded presentation. EditingFinished refreshes the
read-only statistics without replacing text while typing.

The selected effect shows Wald SE, Z and two-sided P from its existing calculation-
scale estimate and interval. Ratio SEs are labelled log scale; Sens/Spec use logit
scale. Complete binary counts also show OR/RR/RD using existing effect computations;
clicking a row selects its metric. No statistical method was added.

Continuous summary columns share the available width. The default width is sized
for the summaries and the scroll area follows the active input panel's height,
removing blank vertical space. Existing alternate input modes remain available.

The arm p-value column is **an input**, not just an output: `fillin.cont.1spell`
in `r/RCMetaR/R/data_transform.R` can derive SE as
`abs(mean)/abs(qnorm(pval/2))`, then SD from SE and N. It stays editable, blank
unless supplied. Computed arm tests against zero are suppressed.

## Evidence and commands

Run in the worktree after `source build/sheets-baseline/ENV.sh`; no environment
synchronization or numerical oracle regeneration was performed.

```sh
uv run --no-sync python scripts/verify_rcms.py --help
uv run --no-sync python scripts/verify_rcms.py calculator-binary
uv run --no-sync python scripts/verify_rcms.py calculator-continuous
uv run --no-sync python scripts/verify_rcms.py calculator-diagnostic
# Repeat for every calculator-mode-* listed by --help and calculator-ratio-precision.
uv run --no-sync python -m pytest tests/e2e -n 2 -q -k calculator
```

The display assertion failed first at
`artifacts/verification/rcms/20261031T171826Z-85534565-calculator-continuous`
with `0.165417277410577`. The original before captures and accepted projects are
in the three `20261031T1556*calculator-*` evidence directories. Their calculator
sources are unchanged between a44c290b and task HEAD cb5fb684. The new accepted-row
fixture copies these projects' first rows; comparisons use float.hex(), including
entered effects and raw inputs, before reopen. Existing numerical oracles remain
untouched.

For counts 7/28 versus 9/27, independent R `metafor::escalc` plus `pnorm` gives:

| Metric | Estimate (calculation scale) | SE | Z | Two-sided P |
|---|---:|---:|---:|---:|
| OR | -0.4054651081081644 | 0.5976143046671968 | -0.6784728962168373 | 0.49747190320929024 |
| RR | -0.2876820724517808 | 0.4256958200604408 | -0.6757925704108049 | 0.4991723524451693 |
| RD | -0.08333333333333331 | 0.1221756164147564 | -0.6820782720705659 | 0.4951894588741752 |

OR and RR display as 0.6667 and 0.7500. The drive records full R numbers and
checks the displayed estimate/CI, clicks each metric row, and checks SE/Z/P.
These are real Qt/R offscreen runs; native DPI/window-manager behavior is outside
this evidence. Before/after captures are in `screens/slice4-calculator-*.png`.

## Final result

All 16 requested serial scenarios passed on the final source, followed by
`17 passed in 234.69s` for the requested pytest selection (including the extra
grid-precision scenario). See `slice4-verification.json` for commands and exact
evidence directories. Serial evidence runs from
`20261031T174032Z-54937804-calculator-binary` through
`20261031T174456Z-5cfe9ae8-calculator-ratio-precision`.

After clicking the comparison rows, numerical comparisons ignore wholly empty
storage slots created by visiting previously unused metrics; every actual saved
raw/entered number is compared bit for bit. An earlier pytest run was invalidated
by a concurrent source edit and was restarted with source frozen. Failed evidence
was retained. No requested verification remains unfinished.
