# Slice 5 — binary and continuous RM5 import

No numerical oracle was regenerated and no statistical method was added.
Diagnostic data and a second public fixture remain outside this slice.

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
| DICH_SUBGROUP / CONT_SUBGROUP | Categorical covariate; ungrouped rows retain blank values |
| IV_OUTCOME HR / OR / MD | Time-to-event fixed / binary fixed IV / continuous fixed entered effects and SE |
| LOG_DATA=YES / NO | Log effect once / retain analysis-scale effect; SE unchanged |
| Free-text IV / IPD O-E variance | Named under “Not imported” |

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

## Live derived subgroup comparison

Six grouped studies, fixed inverse variance, real Subgroup dialog and setup.
Log-OR estimate/lower/upper: earlier [-0.28857647961015254, -0.4857578858213545, -0.09139507339895059], later [0.02113006824755212, -0.140067677181497, 0.18232781367660125]. Maximum absolute difference from meta::metacr is 5e-16.
Between-group RCMS moderator Q=4.852384056279537, p=0.027607948430352695; meta common-effect decomposition Q=5.68048033600663, p=0.0171546707556073. Differences (RCMS minus meta): Q -0.8280962797270925, p +0.010453277674745395. These are explicitly held discrepancies, not parity. The existing plot moderator fit uses params$rm.method independently of the fixed subgroup summaries. No statistical method changed.


## Generic inverse variance implementation

Derived fixture parses with meta::read.rm5. HR maps to time-to-event fixed, storing log effect plus unchanged SE in ratio_inputs. OR and MD entered-effect-only probes both ran end to end without raw data; they map to binary fixed inverse variance and continuous fixed. No new analysis path or statistical method. Custom score is Not imported. O-E/variance is Not imported: inputs are not supported.

Untouched real-setup pooled comparisons, all on analysis scale:

| Metric | RCMS estimate | RCMS lower | RCMS upper | I² (%) |
| --- | ---: | ---: | ---: | ---: |
| HR | -0.12799999999999997 | -0.2943084589219613 | 0.03830845892196133 | 25.062447960033325 |
| OR | -0.12799999999999995 | -0.2943084589219612 | 0.03830845892196136 | 25.062447960033314 |
| MD | -0.12799999999999995 | -0.2943084589219612 | 0.03830845892196136 | 25.062447960033314 |
| metacr (all three) | -0.128 | -0.294308458921961 | 0.0383084589219613 | 25.062447960033303 |

All differences are below 1e-6; save/reopen preserves the complete project values. Test-first failure: 20261031T183943Z-f3998c24-rm5-import (unsupported IV outcomes after successful OR/MD probes). HR ratio+SE initially failed the existing path; storing log estimate+SE corrected it with one logarithm, without constructing rounded CIs. Pass: 20261031T184206Z-98129ec8-rm5-import.


## Fixture provenance and qualification

`generic-derived.rm5` is synthetic, derived from the Fleiss review structure with
invented effects/SEs, not RevMan output. SHA-256:
`4e01e17559b1f3a6ba481668386a9a27eb543e19dc62e2f5a4cacabf999e00d4`.
HR uses LOG_DATA=YES; OR and MD use NO. Both conventions are asserted against
live read.rm5 TE/seTE. The real review excludes Custom score and O-E survival.
The subgroup fixture is also hand-derived, not RevMan output; fixture sources
and hashes are recorded in tests/fixtures/rm5/README.md.

The rm5-import drive exercises File and welcome import, review Cancel/Import,
raw cells, years, pending rows, duplicate names, method mapping, malformed XML,
real setup/Run, held R fits and complete project save/reopen. Subgroup estimates
and CIs compare at 1e-6; the named Q/p differences above are held at 1e-6 rather
than claimed as parity. GIV HR/OR/MD pooled values compare at 1e-6.

Remaining: diagnostic import, another public fixture, exhaustive unsupported-item
preservation, and native UI/file-picker qualification. Offscreen proof does not
qualify native window management or a release package.

Qualification commands source build/sheets-baseline/ENV.sh and use
`uv run --no-sync`: rm5-import, sheets, amino and ratios-hr through
scripts/verify_rcms.py, then
`python -m pytest tests/e2e -n 2 -q -k "rm5 or sheets or ratios"`.
Each helper retains inputs, exact commands, runtime, screenshots, assertions,
reference CSVs and saved projects under artifacts/verification/rcms/.


## Final qualification evidence

Under `artifacts/verification/rcms/`:

- RM5: `20261031T185431Z-5ae1a7ff-rm5-import`.
- Sheets: `20261031T185524Z-ab394c2b-sheets`.
- Amino: `20261031T185156Z-a1e1e0b1-amino`.
- HR: `20261031T185220Z-c8d06c53-ratios-hr`.

All four passed after the last executable change. Qualification first exposed
an O-E reference filter that skipped binary rows because read.rm5 supplies zero
O.E values there (`20261031T184915Z-62ad73b2-rm5-import`). The corrected filter
requires generic-IV type as well as O.E presence; SMD reference selection now
uses outcome identity. No product or statistical behavior changed in this
qualification follow-up. The failure and reference CSVs remain retained.


Final requested pytest selection: **9 passed in 372.73 seconds**, two workers.
Its nine evidence directories (same artifacts/verification/rcms/ root):

- `20261031T185550Z-47b7b24f-sheets`
- `20261031T185550Z-c023e30a-sheets-legacy`
- `20261031T185612Z-0a5dd22f-rm5-import`
- `20261031T185715Z-2223ab18-sheets-persist`
- `20261031T185718Z-7729f65d-sheets-edges`
- `20261031T185728Z-3084f522-sheets-swap`
- `20261031T185742Z-c7366b83-ratios-hr`
- `20261031T185905Z-2db04799-ratios-irr`
- `20261031T185949Z-93f46dd2-ratios-samples`

All thirteen final direct/pytest manifests passed with exit zero and their retained
artifact SHA-256 values were checked after teardown. No uv sync was run.
