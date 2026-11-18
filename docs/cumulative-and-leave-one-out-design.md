# Cumulative and leave-one-out analyses

Cumulative analysis fits successive prefixes of an ordered study sequence.
Leave-one-out analysis fits the included studies after omitting one study at a
time. Both use the selected statistical authority package for estimates,
intervals, study counts and heterogeneity.

## Choose the analysis sequence or figure order

In cumulative setup, **Add studies in** selects table, publication-year or
individual study-effect order before fitting. Changing it reruns the prefix
fits: intermediate subsets can change, while the final full fit uses the same
included studies. Missing years go last; ties retain table order. A source with
no publication years is not a chronological sequence. Saved plot editing shows
the stored sequence and explains that changing it requires a rerun. **Change
settings** carries appearance into the new run; Cancel or a failed run preserves
the existing result. A package failure must not silently change the estimator.

Leave-one-out **Row order** changes presentation by table, year, pooled effect
after omission, or I² after omission, lowest first. It never changes subset
membership or fit quantities. A genuine all-studies reference stays first,
including HR/IRR. Older omission-only bundles remain regenerable; their first
omission is not a reference row and must participate in ordering. Weight order
is not a leave-one-out option. Sort unrounded values, preserve table order for
true ties, and put unavailable values last.

## Read the figure and report

Forests retain each style's fonts, markers, colours and banding. Columns show
study label, package-reported k, optional I², forest, and effect/CI. A full-fit
reference has a bold label and separator. Cumulative labels do not repeat k when
it has its own column. I² uses one decimal consistently in the figure and table.
Hiding the figure's I² column does not remove it from the table.

Use each package fit's k; it can differ from the number of defined individual
effects (`k.yi` in metafor). MH/Peto can retain four studies in k when one of four
individual effects is unavailable because of double-zero events. Do not replace
a package-reported singleton I² merely because k equals one. Genuinely missing
fields remain unavailable.

The sequential table identifies **Step / Study added** or **Study omitted** and
retains every fit, confidence interval, k and available I² in analysis order.
Diagnostic metrics stay separately identifiable. Figure captions state the
independently editable display order. Combined interval cells retain their raw
lower and upper quantities for CSV export.

Results prose gives the cumulative sequence and final fit, or the leave-one-out
full fit and descriptive omission range with named endpoints. It counts
successful fits explicitly and retains failed/non-estimable rows in the table.
It does not repeat an ordinary pooled-effect sentence for every row or infer
robustness, causation, study exclusion, or an influence threshold from P values.
Screen, clipboard, PDF and DOCX use the same report content.

For context, [dmetar InfluenceAnalysis](https://dmetar.protectlab.org/reference/influenceanalysis)
illustrates effect- and I²-sorted leave-one-out diagnostics. The project glossary
in [CONTEXT.md](../CONTEXT.md) defines the domain terms.

## Verify a change

Start with the repository-wide strict typing gate and configured real Qt/R
runtime in the [verification skill](../.agents/skills/verify-rcms/SKILL.md).
`r/RCMetaR/tests/testthat/test-sequential-order.R` compares prefix/omission fits
with public metafor calls and checks saved regeneration. Run the complete
R-stack lane for changes shared by statistical families:

```powershell
uv run python scripts/verify.py r-stack
uv run python scripts/verify_rcms.py review-workflows --native
uv run python scripts/verify_rcms.py plot-workflow-cumulative
uv run python scripts/verify_rcms.py plot-workflow-leave-one-out
```

Retain inputs, exact commands, runtime identity, observed authority values,
screenshots, saved plots and decoded exports. Target these distinctions when
they are affected:

- Table/year/effect cumulative prefixes versus direct public-package fits;
  every labelled omission versus its corresponding fit.
- True ties, equal rounded I² with different underlying values, unavailable
  estimates, actual full-fit references and older omission-only bundles.
- Default/RevMan/BMJ geometry with long labels and narrow widths; native 100%
  and 150% displays; all applicable screen, clipboard, PDF, DOCX, CSV and saved
  regeneration content.
- Singleton prefixes, two-study leave-one-out, MH/Peto double-zero cases,
  ratio-scale transforms and combined univariate diagnostic metrics.
- Changed-sequence rerun, appearance preservation, Cancel and actual package
  failure with the existing result intact.

A nearby passing drive does not prove an unexercised combination. Historical
local success counts and ignored review bundles do not qualify another revision,
platform or release package.
