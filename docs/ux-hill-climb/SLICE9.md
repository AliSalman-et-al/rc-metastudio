# Slice 9: Summary of findings (partial implementation)

Analysis > Summary of findings opens a cross-sheet table using fresh analysis
requests built by the ordinary setup dialog. The isolated models do not navigate
or mutate the source sheets. Reviewer certainty and comments use sheet settings
and workspace edit transactions. Copy uses HTML and TSV; exports reuse the
manuscript writers. Empty sheets retain an explicit reason.

The real-menu scenario derives a four-sheet fixture from amino and lymph and
retains it in workflow evidence. It exercises default cells, empty data,
diagnostic rendering, DOCX cells, PDF extracted text and reviewer-setting
save/reopen. Light and dark captures use Qt palettes, offscreen.

Unfinished: independent ordinary-Run/direct-metafor cell comparisons; data-edit
refresh assertion; diagnostic patient count (currently Not reported); reduce the
diagnostic Effect cell to sensitivity and specificity only; report participant
counts consistently across data families. The current table reuses manuscript
sentences, including their p-values, rather than a concise effect-only cell.
Export UI picker and Copy interaction assertions also remain. This is not a
completed or qualified slice. No statistical methods or oracles changed.

Verification: the initial real-menu assertion failed as intended. Final standalone
`uv run --no-sync python scripts/verify_rcms.py summary-of-findings` passed with
manifest `artifacts/verification/rcms/20261101T055516Z-596e94d5-summary-of-findings/manifest.json`.
`sheets-persist`, `manuscript-export`, and `amino` each passed. The uninterrupted
`uv run --no-sync python -m pytest tests/e2e -n 2 -q -k "summary or manuscript or sheets"`
passed 7 cases in 270.21 seconds. Every command sourced
`build/sheets-baseline/ENV.sh`; no sync or oracle regeneration was performed.
An intermediate PDF assertion needed NFKC normalization for extracted ligatures;
its failed evidence remains retained. No push: the requested full behavior and
proof obligations above remain unfinished.
