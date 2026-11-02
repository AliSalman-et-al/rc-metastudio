# Recoverable analysis failure verification

`AnalysisSetupDialog._run_analysis` calls `done(Accepted)` only after successful
execution. Failure displays the local error and returns without rebuilding the
configuration or disabling Run.

Command: `source build/sheets-baseline/ENV.sh; uv run --no-sync python scripts/native_analysis_smoke.py --offscreen`

Observed: exit 0 (`build/item4-failure.log`). The smoke changes confidence to
90.5, executes a failing backend through Run, processes deferred deletion, reads
actual dialog visibility and Run enablement, and compares `analysis_requests()`
before/after. The evidence validator requires exact equality and confidence 90.5.
Evidence: `build/qt6-verification/native-analysis/evidence.json`.
This is local offscreen lifecycle proof with a controlled backend, not native
window-manager or live statistical qualification.
