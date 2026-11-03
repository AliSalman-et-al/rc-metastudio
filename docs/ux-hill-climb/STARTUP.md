# Development startup

The main window now constructs and paints before embedded R initializes. R stays
on the GUI thread and starts with `QTimer.singleShot(0, ...)`. The status bar says
“Starting R…”; analysis actions and row calculators are unavailable until RCMetaR
loads. Projects and raw-data edits work before R is ready. Raw-effect previews
wait for readiness, then the active model refreshes using the unchanged R
calculations. Confidence settings use the existing Python fallback during loading
and are synchronized with R afterward. Startup errors use the existing backend
error dialog.

The bridge module can be imported without importing rpy2. Explicit backend setup
and direct `RLibraryLoader` callers initialize R. Directory setup no longer sets
R's working directory before initialization. Metric lists are already Python
constants; no numerical implementation or oracle changed.

## Reproduce

Run in the `ux/sheets` worktree with generated forms and its owned installed R
library, as documented in SHEETS.md:

```bash
source build/sheets-baseline/ENV.sh
for i in 1 2 3 4 5; do
  RCMS_PROFILE_STARTUP=1 uv run --no-sync python scripts/verify_rcms.py doctor
done
uv run --no-sync python scripts/verify_rcms.py hillclimb --compare-measures docs/ux-hill-climb/baseline-measures.json
uv run --no-sync python scripts/verify_rcms.py amino
uv run --no-sync python scripts/verify_rcms.py sheets
uv run --no-sync python scripts/verify_golden_compatibility.py --output-root build/qt6-verification/golden-compatibility-startup-final
uv run --no-sync python -m pytest tests/e2e -n 2 -q
```

Doctor's driver no longer initializes R before composition. It asserts the main
window is visible, `rpy2.robjects` has not been imported, and Run is disabled
before processing the timer. `startup.json` uses the `window:visible` phase emitted
after painting the shell, rather than the later return from loading R. Ordinary
runtime identity/doctor assertions still run after real R readiness. The retained
profile now includes deferred loading; phase timestamps distinguish first paint
from runtime readiness. These are offscreen development measurements on a
contended host, with warm OS caches, not packaged native cold-start benchmarks.

## Measurements

Five fresh instrumented doctor processes, seconds:

| Process start to visible window | Median | Min–max | Spread |
| --- | ---: | ---: | ---: |
| Historical before | 14.651 | 10.459–24.426 | 13.967 |
| Deferred R | 1.557 | 0.879–2.397 | 1.518 |

After samples: 1.398453, 0.879188, 1.754696, 2.397477, 1.556868 s.
Evidence under `artifacts/verification/rcms`:

- `20261031T045218Z-3b7067ca-doctor`
- `20261031T045230Z-65661608-doctor`
- `20261031T045246Z-08ff221e-doctor`
- `20261031T045300Z-f6e787e1-doctor`
- `20261031T045317Z-8bdc35b8-doctor`

Historical before evidence: `20261030T225302Z-df9a952f-doctor`,
`20261030T225318Z-725fb57a-doctor`, `20261030T225331Z-e6465dbe-doctor`,
`20261030T225344Z-5a178e74-doctor`, `20261030T225410Z-913723cd-doctor`.
That investigation found median R/rpy2 initialization 3.101 s, metafor loading
3.876 s and RCMetaR loading 5.444 s. Stage medians are not additive. The previously
rejected experiment failed because construction called
`rcmetar.get.mult.from.conf.level` before loading RCMetaR; construction now uses
the existing pre-backend confidence fallback.

Launch to first amino result: **36.581 s before → 20.511 s after**. Each is one
run under contention, measured from the evidence manifest's `started_utc` to its
first `analysis-results` step's `utc` (including screenshots and driver overhead).
This moves startup work after first paint; these single timings do not establish
that R itself got faster.

The before run used an exact `git archive ab5fb8b3` extracted to
`build/startup-before`, with `PYTHONPATH` selecting that archive and the same
absolute R-library/generated-form environment. Command:
`uv run --no-sync python build/startup-before/scripts/verify_rcms.py amino`.
Before evidence: `build/startup-before/artifacts/verification/rcms/20261031T045309Z-caf3047e-amino`;
transcript: `build/startup-before-amino.log`. After:
`artifacts/verification/rcms/20261031T045443Z-32647624-amino`.

## Verification

- Five doctors: passed, including visible-before-rpy2 and disabled-Run assertions.
- Loading probe: passed. `build/startup-loading-probe.py` opens bundled amino,
  changes raw cell (0, 3) from 6 to 7 before rpy2 imports, asserts Run remains
  disabled, then processes startup and asserts readiness/Run enabled. Exact
  command, input and observations: `build/startup-loading-evidence/receipt.json`;
  loading/ready screenshots beside it; transcript `build/startup-loading-probe.log`.
  Derived effect cells wait for R; raw input cells remain editable.
- Hillclimb: passed, `20261031T045332Z-c90fbd69-hillclimb`; committed baseline
  comparison confirms counts, completion, numerical sections and result text
  unchanged. Transcript `build/startup-hillclimb-qualified.log`.
- Amino: passed, `20261031T045443Z-32647624-amino`, frozen numeric contract.
- Sheets: passed, `20261031T045505Z-08e823f5-sheets`.
- Strict golden: passed, 461 pass rows / 13 existing accepted exceptions;
  `build/startup-golden-final.log` and
  `build/qt6-verification/golden-compatibility-startup-final/compatibility-report.json`.
- Full desktop matrix: **125 passed**, `build/startup-matrix-final.log`.
- Injected loader failure: passed, existing backend-error dialog observed, Run
  disabled and project opening still works. Probe/receipt/screenshots:
  `build/startup-failure-probe.py`, `build/startup-failure-evidence/`; transcript
  `build/startup-failure-probe-injected.log`. An earlier invalid-home attempt
  selected the runtime fallback and was terminated; it is not failure proof.

Earlier iterative attempts are retained but are not qualification: the first
strict golden run exposed direct bridge callers relying on eager initialization;
the initial matrix was interrupted after source changes invalidated collection
fingerprints, and an intermediate run exposed Run's initially enabled state.
Both were corrected before the final stable-source run. No oracle was regenerated.
