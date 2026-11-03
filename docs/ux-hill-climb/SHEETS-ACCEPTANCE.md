# Sheet acceptance repair evidence

Run in worktree t3-713f0f8a, branch ux/sheets, using
`source build/sheets-baseline/ENV.sh`. Qt offscreen, real R 4.6.1 and the
worktree-owned installed RCMetaR library. QA scratch directories were not committed.

The lazy bridge accessed undefined deferred rpy2 globals. Serialized bridge calls
and direct rpy2 helpers now reject uninitialized R with
AnalysisBackendUnavailableError. Each desktop startup probes that rejection before
processing the deferred startup event, then waits for readiness before doctor.

Swap availability was refreshed only on Dataset menu opening. Sheet refresh now
recomputes it after open, new, tab selection and transaction restoration. The new
deletion drive found a further defect: removing the selected sheet before calling
set_current_sheet let Qt reset observers read a deleted sheet. Selection now moves
to a surviving sheet before removal.

## Commands and results

- `uv run python -m pytest tests/e2e -n 2 -q`: **129 passed in 2914.91s**.
  Transcript: `build/sheets-baseline/full-fixes-final.log`.
- `uv run --no-sync python scripts/verify_golden_compatibility.py --root . --output-root build/qt6-verification/golden-compatibility-sheets-final`:
  **11 cases, 415 numerical fields, 474 comparisons, passed**.
  Report: `build/qt6-verification/golden-compatibility-sheets-final/compatibility-report.json`.

Evidence directories below are relative to `artifacts/verification/rcms/`. Each
contains command/runtime manifests, inputs, step receipts and live widget captures.

| Scenario | Passed evidence |
| --- | --- |
| amino | 20261031T061633Z-0a15a626-amino |
| sheets | 20261031T061648Z-ce3a739e-sheets |
| sheets-legacy | 20261031T061708Z-eb62755f-sheets-legacy |
| sheets-edges | 20261031T061127Z-4ad41414-sheets-edges |
| sheets-swap | 20261031T061203Z-d90ea7fb-sheets-swap |
| sheets-persist | 20261031T061150Z-37c4b5a3-sheets-persist |

The original numerical fixture was copied from
`build/sheets-baseline/original-corpus-complete/numerics.json`, not regenerated.
Legacy driving extracts all seven originals from 322ede26 into owned workflow
storage, compares all recorded numerical sections for eight sheets and verifies
input hashes. The drive's name expectations drop empty placeholders.

The swap drive proves pooled inversion/sign reversal, double-swap restoration,
raw data ownership, headers and exported SVG arm labels. HR has no raw-arm table
headers, so its arm order is checked alongside its pooled analysis. **User-defined
clinical Favours labels are not migrated or exercised by this drive**; they are
not inferred from arm names. This remains an acceptance gap. The corpus also has
no outcome with several populated follow-ups, so that naming branch is not
exercised by these originals.

Earlier interrupted and failed attempts remain in the evidence directory.
They include a stale test model reference after reopen, overly short multi-analysis
timeouts, and input-signature rejections when source changed during collection;
none is claimed as passing proof. Final matrix inputs remained unchanged.
