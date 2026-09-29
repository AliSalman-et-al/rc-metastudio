# Packaged qualification evidence and gaps

## Current gate

The default `scripts/qualify_worker_journey.py` run is a **bounded core worker gate**. It covers five worker-owned analysis paths. It is not a representative qualification of every supported analysis capability and does not close issue #498 by itself.

Each route runs in a new package process with a 120-second timeout by default. The harness writes progress after every route, records missing samples as `unavailable`, and keeps going after a route fails or times out. A timed-out process tree gets bounded cleanup; evidence retains the worker PID, exit/cleanup state, and the last captured stdout/stderr. The default five-route run is bounded to about twelve minutes including the maximum cleanup allowance, within the 30-minute Ubuntu 26.04 qualification job. A selected `--route` run reports `gate: selected-routes`; only the exact default set is named `bounded-core-worker`.

| Registered route | Packaged sample | Frozen analysis | Extra evidence required |
| --- | --- | --- | --- |
| `binary.standard` | `amino.rcms` | Binary, standard, OR, `binary.random` | Stop acknowledges; settings and one draft remain; saved result reopens; stored figure exports offline. |
| `binary.cumulative` | `amino.rcms` | Binary, cumulative, OR, `binary.random` | Same stop, draft, reopen, and offline-export checks. |
| `binary.leave-one-out` | `amino.rcms` | Binary, leave-one-out, OR, `binary.random` | Same stop, draft, reopen, and offline-export checks. |
| `continuous.standard` | `continuous.rcms` | Continuous, standard, SMD, `continuous.random` | Saved result reopens; study order, event-loop responsiveness, and absence of main-process R are recorded. |
| `diagnostic.standard` | `lymph.rcms` | Diagnostic, standard, Sens, `diagnostic.random` | Saved result reopens; study order, event-loop responsiveness, and absence of main-process R are recorded. |

Every completed route must have a saved/reopened result, stable input identity and report hash, non-empty study order, a responsive UI, and no `rpy2.robjects` in the main process. Binary rows additionally qualify cancellation, editable draft retention, and offline export of a stored figure.

## Source-only evidence from Linux Mint

On 2026-09-29, the five routes above completed individually from fresh source processes in the shared working tree based on commit `ae80924`. The working tree was not clean, so these observations do not identify an immutable source revision. The host was Linux Mint 22.3 Zena x86_64, with R 4.6.1 and RCMetaR 0.4.1 from the local bundled-runtime test environment. All five observations reported `worker_completed`, `saved_analysis_status: complete`, saved/reopened evidence, responsive event loops, and no main-process R bridge. The binary routes each retained one editable draft and exported a stored PNG of 102,053 bytes. The observations contained 19 binary studies, 6 continuous studies, and 17 diagnostic studies in their source order.

This is source-only evidence: the tests launched the current checkout's Python worker journey with `uv run --no-sync`, `QT_QPA_PLATFORM=offscreen`, and an extracted local R runtime. They did not launch an installed portable package. No Ubuntu result is inferred from this host; Linux Mint's Ubuntu base is not an Ubuntu runner.

| Route | Source observation | Outcome |
| --- | --- | --- |
| `binary.standard` | Local `/tmp/rcms-498-live/binary-standard-final.json` | Complete; saved/reopened; stop/draft/export checks passed. |
| `binary.cumulative` | Local `/tmp/rcms-498-live/binary-cumulative.json` | Complete; saved/reopened; stop/draft/export checks passed. |
| `binary.leave-one-out` | Local `/tmp/rcms-498-live/binary-loo.json` | Complete; saved/reopened; stop/draft/export checks passed. |
| `continuous.standard` | Local `/tmp/rcms-498-live/continuous-route-2.json` | Complete; saved/reopened; event loop responsive. |
| `diagnostic.standard` | Local `/tmp/rcms-498-live/diagnostic-route.json` | Complete; saved/reopened; event loop responsive. |

Those `/tmp` observations are local qualification artifacts and are not committed. The checked-in CI/package workflows are the mechanism for retaining per-run package evidence.

## Follow-on route matrix

The following capabilities remain outside the bounded core gate. No result below is claimed as qualified by the source-only routes above.

| Work item | Route evidence | Current status |
| --- | --- | --- |
| #483 subgroup analysis | `binary.subgroup`, `continuous.subgroup`, and `diagnostic.subgroup`; fixture with at least two represented subgroups, explicit missing-covariate behavior, subgroup statuses, and no unsupported between-subgroup inference. | Awaiting the #483 implementation commit before registering its route. |
| #485 generic meta-regression | `binary.meta-regression` and `continuous.meta-regression`; deterministic in-process `Qualification index` moderator, coefficient values, eligibility, formula, study order, warnings, and save/reopen identity. | Registered for selected-route source/package runs. No route-specific numerical oracle exists yet; observed values are recorded without claiming parity. The diagnostic joint meta-regression route is not registered. |
| #487 joint Reitsma | Raw-count diagnostic `diagnostic.reitsma`; retain the paired Sens/Spec operating-point report, section availability and stored SROC figure through save/reopen; export a stored figure offline when present. | Registered for selected-route source/package runs. No independent numerical oracle exists yet; the report is checked for semantic presence and retained identity. |
| #491 worker-owned plotting | Reopen a worker-produced result, regenerate or edit a supported plot, and export it; qualify the actual native viewer path rather than only exporting a stored figure. | Not registered or packaged. |
| Additional authority-supported paths | `binary.one-arm`, `continuous.entered-effect`, and `binary.small-study-effects`; inspect typed pooled values, entered-effect provenance, eligibility and report/section status, then retain and reopen the result. | Registered for selected-route source/package runs. No independent numerical oracle exists yet; observed values are recorded without claiming parity. |

The six follow-on routes above are **not run by the current package workflows**: Windows, macOS, Linux, and the Ubuntu 26.04 qualification job invoke the script without `--route`, so they execute only the five-route bounded core set. A selected-route package job or matrix is still needed to retain these route observations on supported targets. Six selected routes have a nominal maximum of 12 minutes of route time plus up to 10 seconds of process cleanup per timed-out route, before app startup and workflow overhead. Keep any added matrix/job within its explicit workflow timeout; the current Ubuntu 26.04 job is 30 minutes.

An initial source-only selected-route attempt on this Linux Mint host overlapped a separate package qualification/build and other CPU-heavy work. It recorded `timed_out` for `binary.one-arm` while opening the binary sample, `continuous.entered-effect` after analysis and save but before close/reopen evidence, and `binary.meta-regression` before completion. The batch was stopped while `continuous.meta-regression` was running; Reitsma and small-study-effects did not complete. These observations are not qualification passes and may reflect host contention. They are local, uncommitted artifacts under `/tmp/rcms-498-followon`; retry the routes after the deferred-preview MainWindow work and current package qualification settle.

To add a follow-on route, register its sample and expected family/workflow/measure/method and extend its evidence contract in `scripts/qualify_worker_journey.py`; ship the fixture beside the packaged samples. Then run the exact packaged artifact in a fresh process, selecting only that route (or a bounded set of registered routes):

```sh
uv run --no-project --python 3.11.9 python scripts/qualify_worker_journey.py \
  --executable "$PACKAGE_EXECUTABLE" \
  --sample "$PACKAGE_ROOT/sample_projects/amino.rcms" \
  --destination "$QUALIFICATION_DIR/follow-on.rcms" \
  --output "$QUALIFICATION_DIR/follow-on.json" \
  --artifact "$PACKAGE_ARTIFACT" \
  --route "$REGISTERED_ROUTE" \
  --route-timeout 120
```

`$REGISTERED_ROUTE` is a placeholder: an unregistered route is rejected rather than silently skipped or reported as passed. `--route` can be repeated; each selected route still gets its own fresh bounded process. Preserve each JSON result and report `selected-routes` separately from the default core gate.

## Platform and human-evidence gaps

The checked-in package workflows target Windows x64 (`windows-2025`), macOS ARM64 (`macos-15`), Ubuntu 24.04 x86_64, and a separate Ubuntu 26.04 x86_64 qualification job. These are target definitions, not evidence that the current branch passed those jobs.

- Historical [Linux package run 36464538384](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36464538384) succeeded on 2026-09-28. It predates this route-specific gate and is not evidence for the current branch's five worker paths.
- Historical [Windows/macOS unsigned package run 29786816666](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/29786816666) succeeded on 2026-07-20. Its source revision predates the current worker gate and later UX work.
- A preliminary isolated package probe at commit `28a2f13` passed native smoke and the five core worker routes on Linux Mint 22.3 x86_64 (glibc 2.39). The package archive SHA-256 was `1274d7089f4178a7ba216ebba31f93ea16905a89148ce125c4eb6318d8cd0511`; its local evidence is `/tmp/rcms-native-probe.ncSTmM/artifacts/RCMetaStudio-linux-x64-evidence.json`. This is previous-revision Mint package evidence, not a final integrated artifact or Ubuntu runner result.
- No final integrated package artifact was qualified in this task. The local host has `xvfb-run`. `scripts/build-linux-package.sh` uses fixed build and evidence paths, so isolated outputs are required when protecting an existing checkout's build artifacts.
- A macOS 14 Apple Silicon compatibility job is being added to download the exact macOS 15-built artifact, run the package journey, and upload evidence. The job definition is not a passing native macOS 14 result; that evidence remains outstanding until the job runs successfully.
- The automated package smoke records screen scaling and Qt accessibility metadata. No observed screen-reader, assistive-technology, researcher usability, or physical small-screen session was conducted. Do not interpret heuristic inspection or automated metadata as a human accessibility/usability session.

## Inventory relationship

See [capability-parity-baseline.md](capability-parity-baseline.md) and the structured [released capability inventory](../tests/analysis_regression/baseline/released-capability-inventory.json) for the wider authority, input-family, and release-parity gaps. This document records packaged-route evidence and qualification boundaries; it does not replace that statistical inventory.
