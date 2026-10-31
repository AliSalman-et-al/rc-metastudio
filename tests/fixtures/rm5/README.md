# Public RevMan fixture

Fleiss1993.rm5 is copied unchanged from the installed meta package's extdata.
Pinned upstream source:
https://raw.githubusercontent.com/guido-s/meta/d100dde2c4aa924cef1399973da72f57904e93dd/inst/extdata/Fleiss1993.rm5

SHA-256: af4215ebcb2c186738fb2fb30abb7366de17678d29efba617f0abe9bb96bfaa7

12 studies, one comparison, seven binary rows and five continuous rows.

Mapping: MH fixed → binary.fixed.mh; IV fixed → binary.fixed.inv.var or
continuous.fixed; Peto fixed OR → binary.fixed.peto; IV random → binary.random
or continuous.random with rm.method=DL. Random MH has no exact RCMS mapping;
the default remains and the review lists it. CI_TOTAL and EFFECT_MEASURE restore
the sheet confidence level and metric.

RevMan's stored Aspirin OR is 0.8968655609130709 [0.8405144008917793,
0.9569947088336491], I² 39.67458045558399%; RCMS displays 0.90 [0.84, 0.96],
39.7%. Mental health has no stored results: metacr gives -0.343445753457489
[-0.606815161445856, -0.0800763454691217], I² 0. RCMS displays -0.34
[-0.61, -0.08], 0%. Its metafor exact Hedges correction/variance gives pooled
-0.344045819413, a -0.000600065955 difference from metacr's RevMan convention;
this is disclosed, not adjusted away. Full comparison and remaining work:
../../../docs/ux-hill-climb/SLICE5.md.

The E2E workflow derives pending, year, duplicate-name and method-combination
XML files in memory and retains those inputs in workflow evidence; it never
changes this upstream fixture. GIV, diagnostic import and a second fixture remain.


## Derived subgroup fixture (2026-10-31)

`Fleiss1993-subgroups-derived.rm5` is a hand-edited derivative of the unchanged
Fleiss1993 source linked above, **not RevMan output**. The first three aspirin
studies are nested in DICH_SUBGROUP “Earlier trials”, the next three in “Later
trials”; the seventh stays outside subgroups. All original numerical cells and
outcome results remain unchanged. meta::read.rm5 8.5-0 parses it (six grouped
binary rows and five continuous rows); its XML reader omits the ungrouped binary
row when subgroups are present. RCMS preserves that row with a blank covariate.

SHA-256: fc6d0dec9b2c155f58f3370c389ad399f30e0cd44e3d21ddb2f9c97967f2db31

Public search found no additional fixture. GitHub code search for IV_OUTCOME
returned HTTP 401 (authentication required); guido-s/meta's public inst/extdata
listing contains only Fleiss1993.rm5. No claim of exhaustive search is made.

The aspirin E2E comparison now reads the actual R fit retained by the real setup
Run, rather than parsing rounded report text. RCMS OR 0.896865560913071,
CI [0.8405144008917794, 0.9569947088336492], I² 39.67458045558399%; absolute
error versus stored RevMan values is at most 1.11e-16 (I² exactly equal).
Assertions use absolute tolerance 1e-6, without rounding.


## Live derived subgroup comparison

Six grouped studies, fixed inverse variance, real Subgroup dialog and setup.
Log-OR estimate/lower/upper: earlier [-0.28857647961015254, -0.4857578858213545, -0.09139507339895059], later [0.02113006824755212, -0.140067677181497, 0.18232781367660125]. Maximum absolute difference from meta::metacr is 5e-16.
Between-group RCMS moderator Q=4.852384056279537, p=0.027607948430352695; meta common-effect decomposition Q=5.68048033600663, p=0.0171546707556073. Differences (RCMS minus meta): Q -0.8280962797270925, p +0.010453277674745395. These are explicitly held discrepancies, not parity. The existing plot moderator fit uses params$rm.method independently of the fixed subgroup summaries. No statistical method changed.
