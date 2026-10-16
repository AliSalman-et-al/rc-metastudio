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


## 19b5fd9: fonts, not a recent-path layout defect

The next actual Windows run (38834551275 / job 116760835848) passed **122 desktop
cases**, including all five previously failing triggers except review1-design.
Windows package qualification, source/platform, native smoke, code health and
packaging contracts pass; the full-R and dependent integration gate fail.
The four original failed workflow records and two PNGs were fetched from artifact
12018789956 by exact HTTP ranges, ZIP CRC-verified and checked against the original
manifest. CI-FONTS.json binds them. The redundant slow complete download was
stopped and is explicitly partial.

The underlying assertion is the recent-path label's empty text. Failure printing
then raises UnicodeEncodeError: the wrapper reads a UTF-8 transcript with replacement
and prints the resulting U+FFFD through cp1252, hiding the actual assertion.
Two pre-implementation console cases (cp1252 / ASCII) both fail. They pass after
console-only backslash escaping; original log bytes remain unchanged. The child
now explicitly writes Python stdout/stderr as UTF-8, matching the log decoder.

**Personal inspection rejected the original Windows screenshot:** all characters
are missing-glyph squares. See [rejected frame](ci-windows/19b5fd9-fontless-rejected.png).
The original manifest/runtime says **offscreen on Windows**, not qwindows. Its
122 functional passes cannot establish readable Windows UI rendering. The
layout-only premise is disproved; the speculative recent-path wait was removed.
The original ellipsis, full accessible path and row-alignment assertions remain.

Qt's [offscreen implementation](https://github.com/qt/qtbase/blob/dev/src/plugins/platforms/offscreen/qoffscreenintegration.cpp)
uses QFreeTypeFontDatabase on Windows. The [FreeType database](https://github.com/qt/qtbase/blob/dev/src/gui/text/freetype/qfreetypefontdatabase.cpp)
reads [fontDir](https://github.com/qt/qtbase/blob/dev/src/gui/text/qplatformfontdatabase.cpp),
which uses QT_QPA_FONTDIR or Qt's lib/fonts directory. The offscreen child now
selects existing WINDIR/Fonts, respecting an explicit override. No system fonts
are installed or copied, and native production startup is untouched. Every
scenario's doctor now requires a nonempty actual font database, a usable QRawFont
and Latin/tau/ellipsis glyph coverage; runtime.json records the resolved family,
style, family count and directory. Evidence context binds the font directory and
its bytes. Child-environment preparation is one stage separate from process
lifecycle, keeping operation order and all timeout/geometry gates intact.

The initial minimal-platform probe showed that a box font can claim a valid
QRawFont even with zero families; it is not a successful absence detector. The
refined probe fails on zero families. The actual real-R minimal-platform doctor
then rejects the same state with **Qt has no usable fonts** (exit 1), while the
font-aware offscreen doctor and unchanged review1 workflow pass. Two earlier
direct doctor attempts failed import/library setup and are not font proof.
Strict Windows typing passes; source/GUI/comparator/package contracts pass
**893 cases / 16 existing skips**; strict goldens and **415 exact fields** pass
again. The final actual Windows full-R run, readable-font evidence and every
required final-head check remain necessary before merge.


### Console fixture newline portability

a030dc3's Windows source check passed 429 cases and failed the two new console
fixtures: TextIOWrapper translated LF to CRLF while their exact assertion expected
LF. The character-escaping behavior passed. Pin the test-owned stream to LF;
retain the original exact encoding and unchanged-log-byte assertions. The focused
replay passes both cases. No production code, gate scope or numerical/visual
assertion changes. CI-CONSOLE-NEWLINE.json binds the actual failed job and replay.
The final head must still pass all required checks.
