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


## Partial implementation follow-up (2026-10-31)

Fixed real RevMan typed subgroup tags (DICH_SUBGROUP/CONT_SUBGROUP), replacing
the incorrect generic SUBGROUP lookup. The derived fixture above verifies every
row's group name, including the blank ungrouped row, and compares group labels
with meta::read.rm5. This is import mapping proof only: subgroup setup execution,
per-group estimates and between-group statistics remain unverified.

Split conditional review lists into “Not imported” and “Differs from RevMan”.
The shortened SMD disclosure is under the latter. Aspirin is now checked against
the unrounded retained R fit with absolute tolerance 1e-6: estimate
0.896865560913071, CI [0.8405144008917794, 0.9569947088336492], I²
39.67458045558399. Maximum estimate/bounds error is 1.11e-16; I² error is zero.
SMD remains a display-only comparison with its known disclosed difference.

Installed meta 8.5-0 source inspection: extract_outcomes reads IV_DATA EFFECT_SIZE
and SE unchanged; metacr logs TE when LOG_DATA=YES and leaves it unchanged when
LOG_DATA=NO. Therefore IV effects cannot be assumed to be on a log scale.
This finding has not yet been exercised by a derived IV fixture.

Unfinished: IV and O-E/variance fixture/import/analysis, unsupported IV measure
review coverage, real subgroup analysis numerical comparison, and slice5-giv.png.
No diagnostic changes or statistical methods were added; no oracle regenerated.
The subgroup image shows the sheet after import; its covariate column is offscreen.
Row assignments are retained in steps.jsonl, not established by that image.

Test-first failures: 20261031T182041Z-53dd5ddd-rm5-import (review heading),
20261031T182129Z-0cedfcd6-rm5-import (missing typed subgroup covariate).
Final-code RM5 pass: 20261031T182223Z-dba07a10-rm5-import.
Two intermediate RM5 runs accidentally overlapped; they are not final proof.


Final-code validation after the last executable change (all passed):

- rm5-import: `20261031T182223Z-dba07a10-rm5-import`
- sheets: `20261031T182301Z-1985eb07-sheets`
- amino: `20261031T182318Z-e3880fc7-amino`
- ratios-hr: `20261031T182337Z-d61ede11-ratios-hr`
- `uv run --no-sync python -m pytest tests/e2e -n 2 -q -k "rm5 or sheets or ratios"`:
  **9 passed in 353.55s**. Evidence is under `artifacts/verification/rcms/`.

All commands sourced `build/sheets-baseline/ENV.sh`; no uv sync was run.


## Live derived subgroup comparison

Six grouped studies, fixed inverse variance, real Subgroup dialog and setup.
Log-OR estimate/lower/upper: earlier [-0.28857647961015254, -0.4857578858213545, -0.09139507339895059], later [0.02113006824755212, -0.140067677181497, 0.18232781367660125]. Maximum absolute difference from meta::metacr is 5e-16.
Between-group RCMS moderator Q=4.852384056279537, p=0.027607948430352695; meta common-effect decomposition Q=5.68048033600663, p=0.0171546707556073. Differences (RCMS minus meta): Q -0.8280962797270925, p +0.010453277674745395. These are explicitly held discrepancies, not parity. The existing plot moderator fit uses params$rm.method independently of the fixed subgroup summaries. No statistical method changed.
