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
report duplicates and lower captures remain raw. `curate_inventory.py` retains
completed inventory captures, excluding the duplicated prefix in the remainder
index. Curation is followed by explicit image inspection; it is not acceptance.
