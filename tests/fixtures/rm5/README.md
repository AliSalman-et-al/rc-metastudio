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
