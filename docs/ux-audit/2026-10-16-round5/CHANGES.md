# Changes and evidence — in progress

- F11: the bubble renderer suppresses regplot's premature reference and draws a clipped guide only inside the final panel. Native precision drive passed (54.111s); automatic OR/PLO/linear tick coverage and tiny effects retained. Explicit-bound/all-metric exports still due.
- F12 / density: figure pages contain figures; Text/Tables/copy/export own the structured result, weights and references. Removed obsolete scene text/reference producers. Existing real matrix report checks now assert table row preservation instead of requiring duplication.
- Long figures: fixed 1.08 text scale, uncapped height, RevMan height based on displayed rows. Native long/style qualification still due.

The first post-change native drive failed at analysis_matrix.py:209 with `AssertionError`: the old harness required every text block in the scene. Corrected to the intended figure/report contract; the next native precision drive passed. The baseline and first extended runs overlapped briefly and are not used as visual acceptance evidence. Raw receipts retained.

- Standalone context: default entered outcome/comparison/follow-up caption, editable/removable in the existing plot editor, shared by SVG and derived exports. IRR figures include available events/person-time and declared units. HR has no invented event/exposure fields.
- Precision: regression estimates and bounds share a row scale to remove arithmetic residue while preserving genuinely tiny rows; coefficient statistics use the same scale/SE. Diagnostic coefficient ticks remove redundant decimal padding.
- HR/IRR subgroup-difference package printout replaced with the existing structured test table, using the same fit's QM/QMp/df/test. Native IRR drive passed (62.204s); long/all-style and caption editor qualification still in progress.
