# Import a RevMan 5 review

Import an `.rm5` file from **File** or the welcome screen. Review the proposed
sheets, method mappings and **Not imported** items before accepting. Cancel
leaves the project unchanged. Review text, references, risk of bias and graphs
are not imported as an analysis report.

## Supported data and methods

| RevMan input | RC MetaStudio mapping |
| --- | --- |
| Binary OR, RR or RD | Binary sheet with ordered intervention/control arms |
| Continuous MD or SMD | Continuous sheet with N, mean and SD per arm |
| Fixed MH | Binary Mantel–Haenszel |
| Fixed IV | Binary or continuous inverse variance |
| Fixed Peto OR | Binary Peto |
| Random IV | Binary or continuous random effects, explicitly DL |
| Random MH | No exact mapping; review discloses the retained default |
| Generic IV HR, OR or MD | Time-to-event, binary or continuous entered effects and SE |
| Diagnostic test counts | One diagnostic sheet per test, TP/FN/FP/TN |
| Subgroup structure | Categorical covariate; ungrouped rows keep blank values |

`CI_TOTAL` and `EFFECT_MEASURE` restore sheet confidence and metric settings.
Generic IV `LOG_DATA=YES` is logged exactly once; `NO` retains the analysis-scale
effect. SE is unchanged. Free-text IV measures and IPD observed-minus-expected
deaths/variance are listed under **Not imported**. Diagnostic analyses and
covariates are not imported with diagnostic counts.

Missing or non-integer years become blank. A named study with no data and both
totals zero remains as a pending row, excluded until completed. Repeated outcome
names receive numbered suffixes. Full sheet names remain in tab tooltips.

## Statistical differences to review

Importing a method setting does not establish exact parity with RevMan. The
continuous SMD calculation uses metafor's exact Hedges correction and variance;
RevMan's adjusted-g approximation can differ beyond displayed precision. The
public Fleiss fixture's Mental health estimate is about -0.344045819413 with
metafor, compared with -0.343445753457489 from `meta::metacr`. Do not change
inputs or silently adjust results to remove that difference.

Fixed-effect subgroup inference uses the supported authority-package behavior.
Historical subgroup-Q discrepancies were superseded by that correction; they
are not an accepted tolerance for current work. Inspect the imported setup and
report rather than inferring the statistical method from a sheet label.

## Sources and verification

[Fixture provenance](../tests/fixtures/rm5/README.md) records pinned upstream
URLs, hashes, licence limits and the distinction between public reviews and
synthetic derivatives. The observed diagnostic XML structure is
`ANALYSES_AND_DATA/TESTS/TEST/TEST_DATA/TEST_DATA_ENTRY`, with `STUDY_ID` and
`TP/FN/FP/TN` attributes. No published legacy schema was located; synthetic
diagnostic fixtures do not establish exhaustive format support.

After the repository-wide strict typing gate, with the pinned Qt/R environment
configured as described in the [verification skill](../.agents/skills/verify-rcms/SKILL.md):

```powershell
uv run python scripts/verify_rcms.py rm5-import
uv run python -m pytest tests/e2e -q -k rm5
```

The drive compares original XML and public-package results, exercises review
Cancel/Import, unsupported items, malformed XML, real setup/Run, and complete
save/reopen equality. Its retained artifacts include inputs, exact commands,
runtime identity, reference CSVs, screenshots and saved projects. Offscreen
results do not qualify native file pickers, exhaustive diagnostic structures,
other platforms or a release package.
