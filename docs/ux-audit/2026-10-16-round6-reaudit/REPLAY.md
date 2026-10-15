# Replay

From the repository root, source `docs/ux-audit/2026-10-14-round3/ENV.sh` and
`export DISPLAY=:0`. The library is test-owned; do not use system R.

```
uv run python docs/ux-audit/2026-10-16-round6-reaudit/run.py doctor uv run python scripts/verify_rcms.py doctor --native
uv run python docs/ux-audit/2026-10-16-round6-reaudit/drive.py
```

The queue is serial. It skips existing completed outer receipts, including failed
receipts, so failed attempts remain visible. Use a fresh owned raw directory for
a fresh replay; never remove shared verification artifacts. Each helper itself
runs fresh (no matrix-cache option). SCENARIOS.json records order.

`inspect_frames.py SCENARIO ACTION...` retains matching PNGs and builds local inspection
sheets. It does not judge the images. INSPECTIONS.md records human/model review.
Exact child commands, timestamps, observed exits, environment and log hashes are
in raw/*.json. Helper manifests and raw transcripts remain under their printed
artifacts/verification/rcms paths. Only curated PNGs and summary receipts enter git.

After the main queue finishes its final native_options_remaining receipt,
`after.py` serially runs axis Apply transactions, the RevMan/BMJ five-workflow
matrix and Qt 1.5/2 scaling. Its four-hour waiting bound prevents starting a second
GUI lane if the first never finishes. The initial inactive two-hour waiter was replaced
with this longer bound after verifying its exact command and empty child list;
raw/WAIT-EXTENSION.json retains that operation and after-initial.log is preserved. `native_samples.py` and
`native_guard_keyboard.py` add seven bundled sample save/reopen checks and the
complete loaded-project keyboard/report/dirty-guard task; run them after both
queues close. All drivers use test-owned state. Existing run labels are rejected
rather than overwriting failed or completed receipts.

`report.py` assembles the explicit editorial scorecard/findings; it does not infer
visual acceptance from a success marker. `contact.py` writes reduced JPEG contact
thumbnails linked to unchanged original PNGs. The first HTML preview exceeded the
25 MiB inlining limit; corrected thumbnail preview passed at 728 px, height 888,
with no console messages (HTML-PREVIEW.json). Final gallery additions still need
integrity and layout review before final acceptance.

`extras.py` waits (bounded three hours, 50-second polls) for the final 2× scale
receipt, then serially drives sample reopen, keyboard/dirty guards and native
Open/Save/export/colour chooser cancellation. It starts no GUI before that
receipt. Queue waiting processes are intentionally retained across context
compaction; their recorded owned child commands distinguish them from stale
interruption orphans. `native_controls.py` verifies native chooser window PID
ownership before sending Escape; the shell template chooser does likewise.

`curate_matrix.py` retains Default report/figure pairs and journal figures; journal
report duplicates remain raw. `curate_lowers.py` additionally retains lower
figure/report views when their pixels differ from the top capture; journal
report duplicates remain raw. `curate_inventory.py` retains
completed inventory captures, excluding the duplicated prefix in the remainder
index. Curation is followed by explicit image inspection; it is not acceptance.

The custom Default HR/IRR matrix each stopped after four completed workflows on
an actual `intrcpt` visible-label leak in the fifth, meta-regression workflow
(R6-08). Keep both nonzero receipts. After all active GUI queues close, run
`native_matrix.py hr --ratio-wording` and its IRR counterpart under fresh outer
labels `matrix-hr--wording-recovery` / `matrix-irr--wording-recovery` and the
standard 600-second timeout. This flag selects only the missing workflow in new
owned directories. The recorder narrowly permits this known token only in the
exponentiated HR/IRR table, annotates R6-08, and retains the displayed text; all
other label/statistical checks remain. `recover_ratio_matrices.py` binds the four
retained cells to that one continuation and builds inspection sheets; it does
not turn the original failures into passes.

The first Default diagnostic matrix used whole-scene bottom scrolling. Its five
first-component lower candidates were rejected as selected-component evidence.
`native_matrix.py diagnostic --component-lower`, under fresh label
`matrix-diagnostic--lower-recovery`, records correct per-component bottoms in a
new directory. Keep the original captures/index and curate only the missing
first-component lower views from this continuation. Other completed Default
screens are reused. Future style matrices use corrected component scrolling.

`native_editor_inventory.py` runs after the queues, under label
`native-editor-inventory` and a 600-second timeout. It shows all scroll sections,
checks Cancel preservation and physically selects each figure. SROC additionally
runs all three offered styles and decodes all four exports per style. This fills
entry/view gaps without treating old top-only captures as complete screen proof.

Final toolbar continuation uses native-toolbar-final with 180-second timeout and native_toolbar.py. The earlier native-toolbar receipt failed only its five-button count; four visible tooltip-bearing QAction buttons are recorded in TOOLBAR-RECOVERY.json. Original raw evidence remains intact. Final aggregation commands: collect.py; text_inventory.py; scorecard.py --final; report.py --final; contact.py; summary_html.py; raw_manifest.py; final_check.py (each via uv run python with this audit directory prefix).
