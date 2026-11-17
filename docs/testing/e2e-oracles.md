# Desktop oracle contracts

A passing drive needs an independent expectation and retained output. These
checks protect the observed desktop boundaries:

| ID | Observable contract | Mapped drive |
| --- | --- | --- |
| G6B-001 | Configured precision equals the request; receipt records the observed spinbox | amino |
| G6B-002 | Required screenshot saves return success | sheets; calculator and XLSX paths retain the same assertion |
| G6B-003 | Default/RevMan require at least three capped interval rows; caps cannot cross row bands. BMJ deliberately draws uncapped intervals and uses its other plot geometry checks. | audit-round3-twoarm-proportion; audit-round3-round5 |
| G6B-007 | Entire mapped project, including stable identities, labels, raw data and covariates, survives reopening | ux-improvements |
| G6B-008 | Every imported study year matches the XML fixture, including empty/non-digit years | rm5-import |
| G6B-009 | Generic IV study counts, identities, years and numerical inputs match independent meta read.rm5 output | rm5-import |
| G6B-010 | Each expected interval consumes one line at its named study row | project-axis-others |
| G6B-011 | Header boxes stay inside SVG horizontal viewBox bounds | project-round6-polish |
| G6B-012 | Orders equal independent stable sorts of fixture years, fitted effects and weights; ties retain table order and missing years go last | review-workflows |

Run generated forms and the repository-wide strict win32 typing gate before
GUI work, following the [verification skill](../../.agents/skills/verify-rcms/SKILL.md).
Then run the affected named scenario, for example:

```powershell
uv run python scripts/verify_rcms.py rm5-import
uv run python -m pytest tests/e2e/test_oracle_geometry_controls.py -q
```

The helper retains inputs, commands, runtime, plots, saved projects, action
records, screenshots and hashed manifests. Geometry controls isolate malformed
rendered output; live drives use real Qt/R. Count a fault control only when its
specific defect marker and intended assertion are both observed; startup,
typing or wrapper failures do not prove defect detection.

PDF text inclusion supplements exact DOCX-cell comparisons and does not prove
PDF geometry. Offscreen source checks do not qualify native shell behavior,
other platforms or release packages. Rounded display values cannot serve as
an independent numerical oracle. See [testing](../testing.md) for the maintained
coverage decisions and [sequential analysis](../sequential-analysis-design.md)
for its current ordering/report obligations.
