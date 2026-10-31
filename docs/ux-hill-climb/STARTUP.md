# Development startup investigation

No product optimization is retained. The measured dominant work is R package
loading, but the empty main-window constructor already requires RCMetaR. Moving
that boundary requires changes reserved for `ux/sheets`; changing numerical
functions or substituting a confidence multiplier is not an acceptable shortcut.

## Reproduce

From repository root, HEAD initially `3d4232a8`, generated forms already present:

```bash
source docs/ux-audit/2026-10-14-round3/ENV.sh
PYTHONPROFILEIMPORTTIME=1 uv run python scripts/verify_rcms.py doctor
for i in 1 2 3 4 5; do
  RCMS_PROFILE_STARTUP=1 uv run python scripts/verify_rcms.py doctor
done
uv run python scripts/verify_rcms.py hillclimb --compare-measures docs/ux-hill-climb/baseline-measures.json
uv run python -m pytest tests/e2e -n auto -q
```

`RCMS_PROFILE_STARTUP=1` retains startup.pstats and startup-phases.json alongside
the usual manifests, screenshots, runtime.json and startup.json. Read cumulative
cost with `uv run python -m pstats <evidence>/startup.pstats`. Profiling ends after
the visible-window assertion, before doctor identity checks. Timestamps distinguish
driver entry, R backend initialization, composition entry, application configured,
each R package load and returned visible window. Subtract driver entry from the
process-start receipt to isolate timeout wrapper/interpreter/early driver overhead.
Import profiling is a separate run (not included in the five-run timing sample).
OS caches were not flushed. Other agents' real R verification jobs were active;
these figures are not directly comparable to the earlier less-busy scoreboard.

## Measurements

Five fresh instrumented doctor processes, seconds (median; min–max):

| Stage | Median | Range |
| --- | ---: | --- |
| Process start to visible main window | 14.651 | 10.459–24.426 |
| Wrapper/interpreter/early driver overhead | 0.413 | 0.343–1.085 |
| R/rpy2 backend initialization | 3.101 | 1.325–4.874 |
| metafor package load | 3.876 | 2.826–7.555 |
| RCMetaR package load | 5.444 | 2.538–8.920 |
| Main window construction/show after grid | 0.837 | 0.314–1.347 |

Startup spread is 13.967 s. Stage medians are not additive. Composition entry to
application configured includes main-window imports and Qt setup; the single
initial cProfile run measured this at 0.401 s and window construction/show at
1.046 s. In that heavily contended initial profile R package loads took 19.50 s
of 27.70 s total. Importtime independently measured r_bridge at 2.384 s cumulative
(including rpy2.robjects 2.308 s); project_adapter at 0.214 s. Form setup/imports
are much smaller than R package loading. Top three contributors are RCMetaR,
metafor, and embedded R/rpy2 initialization.

Five-run evidence IDs under artifacts/verification/rcms:

- 20261030T225302Z-df9a952f-doctor
- 20261030T225318Z-725fb57a-doctor
- 20261030T225331Z-e6465dbe-doctor
- 20261030T225344Z-5a178e74-doctor
- 20261030T225410Z-913723cd-doctor

Importtime: 20261030T225057Z-71533748-doctor.
Initial cProfile: 20261030T225151Z-109044eb-doctor.

## Rejected experiment and deferred fix

The uncommitted experiment constructed/shown a disabled main window with a
loading status before loading R packages, then enabled it after loading. It
failed before showing: MainWindow.__init__ → new_dataset → DatasetTableModel
.__init__ → set_confidence_level → WorkspaceEditingService.confidence_settings
→ get_confidence_multiplier_from_r → missing
`rcmetar.get.mult.from.conf.level`. Evidence:
20261030T225653Z-49062ad0-doctor.
The experiment was reverted completely. No lazy loading or background R thread
is shipped, and missing/broken-R reporting and analysis readiness are unchanged.

Proposed work for `ux/sheets`: make construction of an empty shell independent of
confidence calculations and other R-dependent model work. Paint that shell first,
disable analysis until runtime/package readiness, preserve actionable startup
errors and cleanup. Then move the existing synchronous loader after first paint;
R stays on the main thread. Measure ready-to-interact and process-to-first-result
as well as first paint: this moves cost rather than eliminating it. Eager imports
in main_window/project_adapter are deferred too, but are much smaller here.

## Validation and first result

Before: hillclimb evidence 20261030T225134Z-a0350670-hillclimb; T1 from ready
empty window to first result 28.832 s. Startup is outside that task clock.
No product change remains, so an optimized after median or claimed speedup would
be misleading. Final restored-source verification results are recorded below.

Restored-source doctor: **passed**, 20261030T225725Z-83f54d12-doctor,
startup 17.730 s (one follow-up, not an after median).
Restored-source hillclimb: **passed**, 20261030T225745Z-fe21567c-hillclimb;
`--compare-measures` confirms every count, completion flag, numerical section and
result text matches the committed baseline. T1 first result: **20.553 s** after
ready window versus **28.832 s** before (single runs, unchanged product code,
not evidence of a performance gain).

Full restored-source matrix: **124 passed in 7406.19 s (2:03:26)**,
exit zero. Exact command:

```bash
source docs/ux-audit/2026-10-14-round3/ENV.sh
uv run python -m pytest tests/e2e -n auto -q
```

Aggregate transcript: `artifacts/verification/startup/rcms-final-matrix.log`.
Each case retains its normal per-scenario manifest and captured workflow artifacts
under `artifacts/verification/rcms/`. Resource selection was one worker. An earlier
matrix begun during the rejected experiment was interrupted and is not
qualification evidence. This pass verifies the restored product startup path;
it does not establish a startup performance improvement.
