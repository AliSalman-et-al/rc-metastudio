# Independent round-four re-audit

Read [REPORT](REPORT.md), [MATRIX](MATRIX.md), [OUTCOMES](OUTCOMES.json), [FAILURES](FAILURES.json) and [INSPECTIONS](INSPECTIONS.json). HANDOFF contains the ranked round-five work. Every report/MATRIX screenshot citation was visually inspected. Other inventory entries document execution, not aesthetic acceptance.

## Replay

Use the repository's locked environment and the pinned test-owned R runtime/library recorded in round four. From the repository root:

```bash
source docs/ux-audit/2026-10-14-round3/ENV.sh
export DISPLAY=:0
uv run python scripts/verify_rcms.py doctor --native
bash docs/ux-audit/2026-10-15-round4-reaudit/RUN-MATRIX.sh
```

The matrix builds its owned fixture inputs before analysing. Native runs must be serial; do not run another window-driving job concurrently. `run.py LABEL COMMAND...` retains exact commands, selected environment, timestamps, log and script hashes under ignored `raw/`. Run the following scripts through that recorder with `uv run python`: `native_design.py`, `native_shell.py`, `native_options.py`, `native_extra.py`. The initial options wrapper intentionally remains as the recorded failed version; `native_options_remaining.py` continues diagnostic/HR/IRR with the correct diagnostic selector. `native_editor.py` opens the actual design-run exported text in xedit and then invokes that remaining-options continuation.

`RUN-FINISH.sh` is the selected 34-case native finishing registry and skips passed local receipts. On a fresh checkout with no local receipts it runs every listed case. `RUN-NATIVE.sh` records the original broader queue command, which was stopped between cases after capacity interruptions; it is **not** evidence that the whole registry completed. OUTCOMES explicitly enumerates cases without a fresh helper run. Their equivalent matrix/supplemental coverage, where present, is stated in REPORT; unexecuted combinations remain limits.

`review_matrix.py`, `contact_sheets.py` and `curate_helpers.py` prepare review material; running them does not inspect or approve images. `inventory.py` refreshes outcome/hash inventories after execution. Historical script digests in receipts may differ from later audit-wrapper corrections; application source stayed unchanged. Native helper captures are QWidget grabs of visible xcb windows; audit-owned captures use QScreen native window grabs. File pickers in maintained helpers usually return owned paths. The separate shell drive captures a real GTK template Save picker.

Raw logs, projects, exported files, review sheets and uncurated frames remain ignored under `raw/` or `artifacts/verification/rcms/`; their paths and hashes are retained in inventories. Curated screenshots are committed. A cloned repository can replay the fixtures, but it does not contain the host's installed runtime or ignored raw artifacts. No release-package, all-option-combination or cross-platform qualification is implied.
