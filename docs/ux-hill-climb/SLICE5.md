# Slice 5 — binary and continuous RM5 import

No numerical oracle was regenerated and no statistical method was added.
GIV, diagnostic data and a second public fixture remain outside this slice.

| RevMan | RCMS |
| --- | --- |
| DICH_OUTCOME OR/RR/RD | Binary sheet, ordered intervention/control arms |
| CONT_OUTCOME MD/SMD | Continuous sheet, N/mean/SD per arm |
| METHOD=MH, RANDOM=NO | Binary fixed Mantel–Haenszel |
| METHOD=IV, RANDOM=NO | Binary/continuous fixed inverse variance |
| METHOD=PETO, RANDOM=NO, OR | Binary fixed Peto |
| METHOD=IV, RANDOM=YES | Binary/continuous random inverse variance, explicitly DL |
| METHOD=MH, RANDOM=YES | No exact mapping; default retained, review discloses difference |
| CI_TOTAL / EFFECT_MEASURE | Sheet confidence level / metric restored by setup |
| Empty or non-integer YEAR | Blank year |
| No data, both TOTAL=0 | Named pending study, blank cells, excluded until completed |
| Repeated outcome name | Append (2), (3), etc. |
| SUBGROUP | Categorical covariate; public subgroup fixture still needed |

The setup dialog uses its existing saved-method/parameter restoration path, with
sheet settings as the initial configuration for ordinary meta-analysis. Review
shows a compact sheet table, actual differences and the standing disclosure for
review text, references, risk of bias and graphs. Full sheet names remain in tab
tooltips; tabs use scroll buttons without eliding labels.

## Numerical comparison

The unchanged Fleiss1993.rm5 fixture is pinned in tests/fixtures/rm5/README.md.
Aspirin's primary authority is RevMan's own DICH_OUTCOME result attributes.
Mental health has empty result attributes; its reference is meta::metacr 8.5-0.

| Outcome / source | Estimate | CI lower | CI upper | I² (%) |
| --- | ---: | ---: | ---: | ---: |
| Aspirin, RevMan OR | 0.8968655609130709 | 0.8405144008917793 | 0.9569947088336491 | 39.67458045558399 |
| Aspirin, RCMS display | 0.90 | 0.84 | 0.96 | 39.7 |
| Mental health, metacr SMD | -0.343445753457489 | -0.606815161445856 | -0.0800763454691217 | 0 |
| Mental health, RCMS display | -0.34 | -0.61 | -0.08 | 0 |

SMD parity is at default display precision only. RCMS uses metafor's exact
Hedges correction and sampling variance, versus RevMan's adjusted-g approximation.
The equivalent metafor fixed fit gives -0.344045819413 [-0.607104392695,
-0.080987246130], differing from metacr by -0.000600065955 in the pooled estimate.
The review explicitly discloses this difference; no correction was added to hide it.

## Verification

Run sequentially after sourcing build/sheets-baseline/ENV.sh, with uv run --no-sync:

```
python scripts/verify_rcms.py rm5-import
python scripts/verify_rcms.py sheets
python scripts/verify_rcms.py sheets-persist
python scripts/verify_rcms.py amino
python scripts/verify_rcms.py analysis-dialog
python -m pytest tests/e2e -n 2 -q -k "rm5 or sheets or wizard"
```

The rm5-import workflow retains byte-derived XML fixtures, raw-cell metacr
comparison CSVs, real setup/Run and displayed pooled comparisons, dirty cancel
and unsaved-prompt checks, malformed XML errors, welcome-button import and
save/reopen. Each helper retains exact commands, runtime, screenshots and results
under artifacts/verification/rcms. Offscreen Qt does not prove native file pickers.

Remaining: GIV/DTA, second public fixture, public subgroup fixture, exhaustive
unsupported-item preservation/inventory and native UI qualification. Random MH
is deliberately disclosed rather than silently substituted with random IV.

Final-code direct evidence (under artifacts/verification/rcms/):

- RM5 import: `20261031T181150Z-e67e20ab-rm5-import`.
- Sheets: `20261031T181221Z-08783b60-sheets`.
- Sheets persistence: `20261031T181248Z-466d6722-sheets-persist`.
- Amino: `20261031T181304Z-42e56e1c-amino`.
- Analysis dialog: `20261031T181325Z-0f99fd74-analysis-dialog`.

Pre-implementation failures are retained in `20261031T180522Z-4d68293a-rm5-import`
and `20261031T180541Z-9e58d5dd-rm5-import`; the missing SMD disclosure failed in
`20261031T180855Z-48549035-rm5-import`, and pending exclusion failed in
`20261031T181013Z-05b6de86-rm5-import`. The interrupted earlier persistence run
is not counted as passing evidence. Screenshots were refreshed from the final-code
RM5 run and visually inspected: both full tab names fit at the default width.

Final requested pytest selection: **6 passed in 188.91 seconds** after the last
code change. Its RM5 evidence is `20261031T181445Z-3f691982-rm5-import`;
the five direct workflows above also passed independently.
