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

`inspect.py SCENARIO ACTION...` retains matching PNGs and builds local inspection
sheets. It does not judge the images. INSPECTIONS.md records human/model review.
Exact child commands, timestamps, observed exits, environment and log hashes are
in raw/*.json. Helper manifests and raw transcripts remain under their printed
artifacts/verification/rcms paths. Only curated PNGs and summary receipts enter git.
