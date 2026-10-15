# Changes and evidence — in progress

- F11: the bubble renderer suppresses regplot's premature reference and draws a clipped guide only inside the final panel. Native precision drive passed (54.111s); automatic OR/PLO/linear tick coverage and tiny effects retained. Explicit-bound/all-metric exports still due.
- F12 / density: figure pages contain figures; Text/Tables/copy/export own the structured result, weights and references. Removed obsolete scene text/reference producers. Existing real matrix report checks now assert table row preservation instead of requiring duplication.
- Long figures: fixed 1.08 text scale, uncapped height, RevMan height based on displayed rows. Native long/style qualification still due.

The first post-change native drive failed at analysis_matrix.py:209 with `AssertionError`: the old harness required every text block in the scene. Corrected to the intended figure/report contract; the next native precision drive passed. The baseline and first extended runs overlapped briefly and are not used as visual acceptance evidence. Raw receipts retained.

- Standalone context: default entered outcome/comparison/follow-up caption, editable/removable in the existing plot editor, shared by SVG and derived exports. IRR figures include available events/person-time and declared units. HR has no invented event/exposure fields.
- Precision: regression estimates and bounds share a row scale to remove arithmetic residue while preserving genuinely tiny rows; coefficient statistics use the same scale/SE. Diagnostic coefficient ticks remove redundant decimal padding.
- HR/IRR subgroup-difference package printout replaced with the existing structured test table, using the same fit's QM/QMp/df/test. Native IRR drive passed (62.204s); long/all-style and caption editor qualification still in progress.

- F13/F14/F15: content-height start cards; validated Locate and Remove through existing recent storage; compact labelled Analyses menu reuses all existing actions/shortcuts/prerequisite tooltips; navigator label/value gap and remaining small-study/calculator/editor terminology.
- Report hierarchy: one top result heading, no repeated weight heading, lighter pooled sentence/margins, normalized diagnostic heading separators; removed 150+ lines of obsolete graphics-scene text selection/copy machinery and its retired scene-only test.
- Linux accessibility: named/described toolbar/grid/results controls, deliberate toolbar→navigator→grid and table→navigation tab order, keyboard-focusable toolbar/navigation buttons, Ctrl+Tab exits spreadsheet navigation, result tables use Tab for focus traversal. Gold effect cells also use italic type; selected cells use white on #245a81. Screen readers and real OS scaling on Windows/macOS remain unqualified.

Native keyboard driving exposed the spreadsheet Tab loop and results-table focus trap; fixes are being re-driven before acceptance. The new long-style contract caught BMJ's independent 0.7/18-inch shrinking policy; removed its second shrink pass and height cap too. Default/BMJ row spacing is now 0.30 inches at the same 1.08 text scale as RevMan.
