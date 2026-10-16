# 035ebd3 Windows full-R continuation

Run 38828597592 / job 116742050498 passed R package checking, the two Reitsma
visual lanes and bridge tests, then failed five desktop cases (118 passed in
1,617.31 seconds). The original ANSI-bearing log is retained at
raw/lexer/full-r-035ebd3.log. The integration verification gate correctly failed
because required Windows full-R and package jobs failed; its policy stays intact.

Failure list, recorded before repair:

- `audit-round3-arm-names`: a report containing τ² was written using Windows'
  ambient cp1252 encoding. Evidence text/SVG reads and writes must explicitly
  use UTF-8, preserving complete names and the existing report assertions.
- `review1-design`: the long fixture directory ends in a space. Windows creates
  its normalized spelling but cannot then open the unnormalized intermediate
  path. Trim only the fixture's trailing space; keep the long-path elision,
  missing-file recovery, canonical recent-path and save/reopen assertions.
- `ux-improvements`: the result identity-height bound fails on native Windows.
  The same complete workflow passes offscreen and native xcb at 035ebd3. Observe
  and wait for the actual queued layout refit before asserting the unchanged
  three-line bound; retain initial/settled dimensions, measured text height,
  width, font metrics and wait count. No forced geometry or larger bound.
- `project-axis-proportions` and `project-axis-others`: the text-row parser groups
  SVG labels by Y rounded to one decimal place. Real svglite text baselines vary
  slightly by glyph ascent. A deterministic real-device loop renders six ticks
  (0 through 1) using four fonts and eleven device heights. The existing parser
  mis-groups 11 of 44 real SVGs. In serif-2.02.svg all six labels exist, but “1”
  is at Y=76.78 and most peers at Y=76.69, putting them in adjacent rounding bins.
  It reproduces the exact Windows symptom: apparent ticks only 0 through 0.8.
  Group by direct baseline distance within the original 0.1-point row precision;
  do not change endpoint, spacing, interval projection or numerical assertions.

Receipts `axis-text-render` and `axis-parser-before-configured` retain the real
SVG inputs, command and red verdict. The initial unconfigured parser invocation
failed import resolution and is explicitly not reproduction. `ux-native-before`
passes in 70.89 seconds; it does not qualify Windows.

The Windows full-R job did not upload its retained desktop evidence, so its failed
header's geometry was unavailable after runner cleanup. Persist that job's real
artifacts with the already pinned upload action; keep job/test selection, bounds,
required checks and timeouts unchanged. The final actual Windows full-R run is
required to establish the boundary/layout repairs. Local source proof is separate.


Post-fix local results: all 44 identical SVG inputs pass the parser; the full
source/GUI/comparator/packaging sweep passes 891 cases with 16 existing skips;
strict Windows-target typing passes; strict goldens and all 415 original fields
pass again. Native xcb UX passes in 64.18 seconds after the bounded state wait
and added geometry observations. No endpoint/spacing/height bound was relaxed.
These local results do not establish the final Windows verdict; every actual
final-head check remains required.
