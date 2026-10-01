# Packaged qualification evidence and gaps

## Current gate

The default `scripts/qualify_worker_journey.py` run is a **bounded core worker gate**. It covers five worker-owned analysis paths. It is not a representative qualification of every supported analysis capability and does not close issue #498 by itself.

Each route runs in a new package process with a 120-second timeout by default. The harness writes progress after every route, records missing samples as `unavailable`, and keeps going after a route fails or times out. A timed-out process tree gets bounded cleanup; evidence retains the worker PID, exit/cleanup state, and the last captured stdout/stderr. The default five-route run is bounded to about twelve minutes including the maximum cleanup allowance. A selected `--route` run reports `gate: selected-routes`; only the exact default set is named `bounded-core-worker`.

The registry now includes 48 route identities: the original twenty plus 28 fixed-method variants. They cover all 44 desktop method/workflow cells in the capability inventory, with additional one-arm, entered-effect, small-study-effects, and plot-edit journeys. The six bootstrap cells are public R API capabilities, not desktop routes. `--all-routes` selects all 48; `--all-additional-routes` selects the 43 outside the default five, so package jobs can retain separate core and additional reports without duplicating runs. Package qualification budgets are 150 minutes, or 180 minutes for build jobs, to accommodate the expanded route timeouts and cleanup. Registration is not a qualification pass. The earlier `a36c169` native evidence covers twenty routes; the downloaded `c5ebb9f` Windows and macOS evidence below covers all 48. The corrected Linux package now passes on Ubuntu 24.04 and 26.04. The corrected macOS source-version provenance passes in the `003e80b` archive below. Its repository link is corrected in source as described below; final release qualification remains outstanding.

| Core registered route | Packaged sample | Route identity | Extra evidence required |
| --- | --- | --- | --- |
| `binary.standard` | `amino.rcms` | Binary, standard, OR, `binary.random` | Stop acknowledges; settings and one draft remain; saved result reopens; stored figure exports offline. |
| `binary.cumulative` | `amino.rcms` | Binary, cumulative, OR, `binary.random` | Same stop, draft, reopen, and offline-export checks. |
| `binary.leave-one-out` | `amino.rcms` | Binary, leave-one-out, OR, `binary.random` | Same stop, draft, reopen, and offline-export checks. |
| `continuous.standard` | `continuous.rcms` | Continuous, standard, SMD, `continuous.random` | Saved result reopens; study order, event-loop responsiveness, and absence of main-process R are recorded. |
| `diagnostic.standard` | `lymph.rcms` | Diagnostic, standard, Sens, `diagnostic.random` | Saved result reopens; study order, event-loop responsiveness, and absence of main-process R are recorded. |

Every completed route must have a saved/reopened result, stable input identity and report hash, non-empty study order, a responsive UI, and no `rpy2.robjects` in the main process. Binary rows additionally qualify cancellation, editable draft retention, and offline export of a stored figure.

Route identity checks the family, workflow, measure, and method. It does not supply an independent expected numerical result.

Each fixed method below has four route suffixes: `standard`, `cumulative`, `leave-one-out`, and `subgroup`. Its route ID is `<method>.<suffix>`, for example `binary.fixed.peto.cumulative`. These 28 routes use the existing numerical, sequence, subgroup, save/reopen, and export checks. The saved specification must match the requested method before evidence is accepted; recorded identity is preserved.

| Method | Measure | Sample |
| --- | --- | --- |
| `binary.fixed.inv.var` | OR | `amino.rcms` |
| `binary.fixed.mh` | OR | `amino.rcms` |
| `binary.fixed.peto` | OR | `amino.rcms` |
| `continuous.fixed` | SMD | `continuous.rcms` |
| `diagnostic.fixed.inv.var` | Sens | `lymph.rcms` |
| `diagnostic.fixed.mh` | DOR | `lymph.rcms` |
| `diagnostic.fixed.peto` | DOR | `lymph.rcms` |

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

## Additional isolated Xvfb source checks

After the deferred-preview and close-ownership fixes, each route below was launched from an isolated source checkout with Qt's `xcb` platform in Xvfb and the local pinned R 4.6.1/RCMetaR 0.4.1 runtime. Most used Git-archive snapshots; the diagnostic subgroup route ran from the shared checkout. These were incremental commits between `b67f3c1` and `66cfc9f`, not one final integrated package. The evidence files are local and uncommitted. Every listed route completed its worker call, saved and reopened at least one complete result, kept the Qt event loop responsive, and reported no R bridge in the main process.

| Route | Local evidence | Additional observation |
| --- | --- | --- |
| `binary.standard` | `/tmp/rcms-snapshot-binary-standard-2.json` | Stop/draft checks and offline PNG export passed. |
| `binary.cumulative` | `/tmp/rcms-xvfb-binary-cumulative.json` | Two results reopened; stop/draft and offline PNG checks passed. |
| `binary.leave-one-out` | `/tmp/rcms-xvfb-binary-loo.json` | Two results reopened; stop/draft and offline PNG checks passed. |
| `continuous.standard` | `/tmp/rcms-xvfb-continuous-standard-2.json` | One result reopened. |
| `diagnostic.standard` | `/tmp/rcms-xvfb-diagnostic-standard-2.json` | One result reopened. |
| `binary.one-arm` | `/tmp/rcms-xvfb-one-arm-5.json` | Typed pooled proportion and 19 source-order studies retained. |
| `continuous.entered-effect` | `/tmp/rcms-xvfb-continuous-entered.json` | Entered-effect provenance retained. |
| `diagnostic.reitsma` | `/tmp/rcms-xvfb-reitsma.json` | Paired sensitivity/specificity report and SROC figure retained. |
| `binary.small-study-effects` | `/tmp/rcms-xvfb-small-study-2.json` | Figure staged by the worker and retained through save/reopen. |
| `binary.meta-regression` | `/tmp/rcms-xvfb-binary-meta-fixed.json` | Zero-cell correction retained all 19 `amino.rcms` studies and moderator rows; result saved and reopened. |
| `continuous.meta-regression` | `/tmp/rcms-xvfb-continuous-meta-final.json` | Result saved and reopened from an isolated `1ab01dd` source snapshot. |
| `diagnostic.subgroup` | `/tmp/diag-subgroup-qualify/verified-observation.json` | Both missing-value policies saved and reopened in the same 17-study order; 15/2 and 17/0 included/excluded; two offline PNG exports and saved Edit a copy passed. |
| `diagnostic.reitsma-meta-regression` | `/tmp/rcms-reitsma-independent-check.json` | Joint report saved and reopened; 15 eligible studies, two named missing-moderator exclusions, sensitivity and false-positive-rate coefficients, overall and moderator ML tests, and 11,995-byte offline figure export. |

An earlier `binary.meta-regression` attempt at `/tmp/rcms-xvfb-binary-meta-regression.json` failed on a raw-effect preview; the corrected route above supersedes it. The Reitsma meta-regression observation was independently rerun on 2026-09-30 after commits `76589b7` and `0721b5e`, using Xvfb and the local R runtime; the shared source worktree also contained later commits and an unrelated uncommitted subgroup refactor. Its JSON labels the numerical values `observed_only_no_independent_expected_value`. No selected-route result above is a native packaged-app qualification or an independent numerical oracle.

On 2026-09-30, six additional source routes passed using an isolated R library built from the working source. The qualification changes were subsequently committed as `a76f5fd`; the observations also included uncommitted renderer changes, so they do not identify a clean final revision. `/tmp/rcms-route-qualify/cumulative-private2.json` records `continuous.cumulative`. `/tmp/rcms-route-qualify/route-remaining.json` records `binary.subgroup`, `continuous.subgroup`, `diagnostic.cumulative`, `continuous.leave-one-out`, and `diagnostic.leave-one-out`. Together they retain eight analysis runs, including both missing-covariate policies for each subgroup route, saved/reopened results, and nonempty exported figures. Sequential evidence checks the frozen study identities and order, cumulative prefixes, and leave-one-out baseline and omission rows. Numerical values remain observations without independent expected values. Missing cumulative analyzed-study counts stay `not_available` with reasons; the input prefix count is checked separately. These Linux Mint source observations require a final packaged rerun on each declared platform.

## Follow-on route matrix

The following capabilities remain outside the bounded core gate. No result below is claimed as qualified by the source-only routes above.

| Work item | Route evidence | Current status |
| --- | --- | --- |
| #483 subgroup analysis | `binary.subgroup`, `continuous.subgroup`, and `diagnostic.subgroup`; fixture with at least two represented subgroups, explicit missing-covariate behavior, subgroup statuses, and no unsupported between-subgroup inference. | All three have source observations for both missing-value policies. Diagnostic subgroup also has preliminary Windows package evidence. Final cross-platform package evidence remains outstanding. |
| #484 meta-regression | `binary.meta-regression` and `continuous.meta-regression`; deterministic `Qualification index` moderator, explicit two-study exclusion, eligibility, and save/reopen identity. | Both have source and selected-route package observations. Their recorded values are observations, not an independent numerical oracle. |
| #485 joint Reitsma | Raw-count diagnostic `diagnostic.reitsma`; retain the paired Sens/Spec operating-point report, section availability and stored SROC figure through save/reopen; export a stored figure offline when present. | Registered for selected-route source/package runs. These route records check semantic presence and retained identity; the independent public-mada tests described in the capability baseline are separate evidence. Final packaged numerical comparisons remain due. |
| #486 Reitsma meta-regression | `diagnostic.reitsma-meta-regression`; paired coefficient views, ML tests, frozen eligibility, and save/reopen identity. | Source and selected-route package observations exist. The recorded numerical values have no independent expected-value oracle. |
| #487 small-study effects | `binary.small-study-effects`; inspect method-specific eligibility, report/section status, and retained figures. | The binary OR route has source and selected-route package observations. Separate authority tests now compare representative supported alternatives and Deeks geometry with public package calls. Final packaged comparisons and the remaining combinations in the inventory are outstanding. |
| #491 worker-owned plotting | Reopen a worker-produced result, regenerate or edit a supported plot, and export it; qualify the actual native viewer path rather than only exporting a stored figure. | `binary.plot-edit` passed a source-only Xvfb journey after commit `231c280`: reopen, regenerate, edit, save, reopen again, and export. The local observation `/tmp/rcms-binary-plot-edit-source-saved-v15.json` reports unchanged scientific report identity, retained figure style and image hash, and a 101,878-byte offline PNG export. The same registered journey also passed preliminary Ubuntu 24/26 package qualification in run 36665875737. These observations predate the no-refit saved renderer correction and do not qualify the final implementation. |
| Additional authority-supported paths | `binary.one-arm` and `continuous.entered-effect`; inspect typed pooled values and entered-effect provenance, then retain and reopen the result. | Registered for selected-route source/package runs. These route records retain observations without claiming numerical parity. Representative one-arm and entered-effect public-package comparisons are recorded separately in the capability baseline. |

The cited Windows package runs requested eight follow-on routes separately from the five-route core gate and passed all thirteen registered routes at those revisions, including diagnostic Reitsma meta-regression. They do not qualify later branch edits. `binary.plot-edit` passed preliminary Linux package qualification in run 36665875737, but that implementation still refits from frozen inputs and does not satisfy the agreed no-refit appearance requirement. The additional six subgroup and sequential routes are registered as of `a76f5fd`, bringing the matrix to twenty routes. Their source observations and the earlier package observations must be replaced by final artifact qualification; registration alone is not a pass.

### Computed figure snapshots

Commits `533a3d2` and `b6f133b` persist validated computed plotting data for supported forest, regression, funnel, SROC, and coefficient figures. New results and reopened history use the same saved-record edit transaction, with presentation overrides scoped to one figure. The completion → appearance edit → history reopen GUI test passed at `0c342ca` with this implementation; it checks retained PNG/SVG assets and unchanged scientific summary and snapshot.

The actual embedded Python/R bridge regression passed for one-study and three-study standard forests and a subgroup forest. It exercises the worker capture and redraw path with `metafor::rma.uni` traced to fail if called. Study arrays, one-column labels, and scalar summary intervals survived the bridge without refitting. The nonforest geometry tests passed 63 assertions at `faaaabd`, including computed coordinate comparisons and label resets under no-fit traces. These are focused source checks, not final native package or usability qualification. The complete suite and final artifact matrix remain required.

At `58653fa`, the full source RCMetaR suite exited successfully with no failures and one optional visual-QA skip, using the pinned R 4.6.1 runtime. The Python/R integration suite passed eighteen tests but failed the Reitsma saved-result journey: the worker rejected the projected figure data as malformed. The R-only geometry checks do not establish that every projected figure survives the Python bridge. That failure required a correction at the Python/R boundary and a complete integration rerun.

The Reitsma failure was corrected in `2bd34db`: SROC marker sizing is the `uniform`/`sample-size` string choice returned by R. Commit `d15ed46` also resolves unset funnel contour levels through the existing renderer default before capture. At `9b2b840`, real worker projection and redraw tests pass for regression, ordinary funnel, SROC, and both Reitsma coefficient figures. They use R 4.6.1 with a private RCMetaR library installed from the committed source, block fitting and prediction calls during redraw, and check unchanged scientific results and frozen state. The full changed-code health gate passes at that revision. A complete rerun on an immutable archive of `9b2b840` passes all 21 Python/R integration tests with exit status 0. The full source RCMetaR suite also exits successfully with no failures and one optional visual-QA skip. The archived fast and golden suite passes 861 tests with 8 skips under warnings-as-errors and exits with status 0. Both archives use snapshot-local generated Qt forms; the fast/golden archive also has Git metadata identifying the exact source commit. A fresh capture of the eleven tagged-source v0.3.1 reference cases passes all 463 comparison rows, with no request-identity or capture-status drift; only the previously documented heterogeneity-label and alignment changes are accepted. All 45 GUI modules pass in their two maintained pytest phases: 544 passed / 12 skipped in the core phase and 54 passed in RemainingSurfaces, each with warnings-as-errors and exit status 0. Those tests use immutable product source `9b2b840` with test-only cleanup commit `02349cc` overlaid. Expanded package-API reference and native package qualification remain required.

The full twenty-route source run at `9b2b840` completed eighteen routes and timed out on `diagnostic.subgroup` and `diagnostic.leave-one-out`. These are failures, not a twenty-route qualification pass. Their workers produced figures, but the diagnostic producers named figure sidecars `Forest Plot` while the saved images had subgroup or leave-one-out identities. Saved-result validation rejected those mismatched identities. Commit `fe69c548` keys sidecars to their actual image names and projects the leave-one-out overall summary from its stored fit without fitting again. An exact-commit worker test passes for both routes: it captures portable saved results, compares leave-one-out row estimates and intervals to the numerical report, and redraws both forests with fitting functions blocked. The focused R test passes all seven assertions. The full source RCMetaR suite reports **1,974 passed, zero failures, zero warnings, and one optional visual-QA skip**; its only subsequent production change removed an unused local assignment, followed by the exact-commit focused rerun. The controlled final run from the same immutable source passes **all twenty routes**, with 23 analysis-run records and harness exit status 0. It uses Linux Mint 22.3 x86_64 under Xvfb/xcb with pinned R 4.6.1 and RCMetaR 0.4.1. Its source archive SHA-256 is `c5e76cdfc7a74f0a7e1b0c4f6580a96ef8ef0d2522165db3fbef8ce89a4f8c74`. A preceding run overlapped the full R verification and timed out on binary plot editing and diagnostic subgroup; isolated traces showed active editor opening and SVG validation, and both routes passed separately before the controlled full rerun. The final raw JSON and source companion are retained locally under `/tmp/rcms-worker-journeys-fe69c54.QdBTPo/`. The companion explicitly distinguishes the source archive from a native package artifact; this pass is source-process evidence, not packaged Windows, macOS, or Ubuntu qualification.

The immutable `41d9cdb` source archive, including the new fourteen-case historical reference pin, passes **873 fast/golden tests with eight skips**, warnings-as-errors and exit status 0. Its archive SHA-256 is `8211281900303890472bbbd7984bac08d4d559383a9be104d3c041757baf1301`. Snapshot-local generated Qt forms and Git metadata identify that revision; RCMetaR is installed from `fe69c548` on the pinned R 4.6.1 runtime. The full required Python/R integration suite passes all **22 tests with zero skips**, using the pinned `Rscript` on `PATH` and `RCMS_R_STACK_REQUIRED=1`. Repository-wide strict typing and the changed-code health gate also pass. Independent review of the diagnostic fix finds no material correctness issue. These are source checks, not native artifact qualification.

[Integration run 36706919107](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36706919107) used source `26d6120`, before that diagnostic fix. Its Windows package smoke and five core worker routes passed. Thirteen of the fifteen selected routes completed; diagnostic subgroup and leave-one-out timed out. Both route records identify archive SHA-256 `5e4befe0ab82be8391c092b8fe9d5768cfb66e16b8c4fce3f2bf46f85fd0704e`. The same run's native Windows core GUI phase reports 538 passed, 12 skipped, and six failed large-font/narrow-panel layout tests. Windows full R integration, RemainingSurfaces, the three source/platform lanes, and packaging contracts passed; the overall integration gate failed. These records establish the remaining failures at that revision and do not qualify the corrected source.

Commit `866565e` attempted to address the Windows layout failures: calculator scroll areas no longer force their content's preferred width onto the outer dialog, and embedded Results panel layouts are activated after the viewport width cap so wrapped labels are measured at their current width. The binary test keeps its synthetic screen provider active after native window creation, matching the existing diagnostic fixture. All six originally failing cases pass in local default/offscreen and Windows-style/offscreen checks, with companion sizing, guidance, overflow, first-show, and resize-burst checks also passing. Configured strict typing and an independent focused review pass. Windows-style Qt on Linux is not the Windows platform plugin. The subsequent native [integration run 36714540211](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36714540211), from PR head `a36c169` and merge checkout `e474166`, still fails five core GUI checks (539 passed, 12 skipped): the four diagnostic dialogs remain 843 pixels wide against an 800-pixel synthetic available screen, and the narrow Results context label still extends past its panel. The binary frame-placement check now passes. The patch therefore does not close native layout qualification; those five failures remain open despite local passing checks. The same run passes all 22 required Windows Python/R integration tests (245.64 seconds) and all 54 RemainingSurfaces tests. Its Windows package job, source/platform lanes, and code-health gate pass; the overall integration gate fails because of the core GUI failures.

The same revision preserves a successful continuous analysis when `supress.output=True` deliberately omits its figure sidecar. An empty sidecar path disables appearance editing for that figure while retaining the scientific result; a nontext path remains an invalid worker response. The focused worker regression and the continuous Python/R authority test passed. A normal drawing request produced a real forest figure and retained its sidecar.

An initial source-only selected-route attempt on this Linux Mint host overlapped a separate package qualification/build and other CPU-heavy work. It recorded timeouts under `/tmp/rcms-498-followon`; those attempts are not qualification passes. The later isolated Xvfb runs above supersede those attempts for the routes they completed.

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

## Native layout retest at `5ccd595`

[Integration run 36726045485](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36726045485) tests PR head `5ccd59565e4ff1c358c56deef23711ce01c62444` through merge checkout `e7e072d116e222f085469ef698b335546b57132e`. Its Windows GUI pytest phase passes **545 tests with twelve skips**, with exit status 0 in 113.14 seconds. The original five sizing failures and the new measured-capacity font/reflow case pass. Dialog minimum widths now come from the external action footer, and results table actions stack when their measured horizontal width will not fit, then return to a row when it does. Temporary geometry probes are removed after preserving the raw native logs.

The whole native job still fails in the later calculator smoke: `OK is not the default calculator action`. That smoke uses a fixed 150-millisecond callback while the worker-backed calculators initially disable Apply and the entry controls. A bounded readiness wait is required before its default/focus/edit assertions. The successful GUI phase does not turn this whole-job failure into a pass. This revision also predates the expanded 48-route method qualification.

## Calculator source retest with the `66ad055` patch

The bounded worker readiness wait exposed a production request error: the binary dialog sent the string `"binary"`, while the calculator service expects the integer `BINARY` enum. The request now uses that enum. The other calculator callers already use their corresponding enum values. A focused test captures the dialog request and passes it through the calculator service boundary.

A source Xvfb/xcb smoke passes all three calculators on Linux Mint with pinned R 4.6.1 and RCMetaR 0.4.1. Binary and continuous Apply commit the expected values; an invalid diagnostic count rolls back, Cancel keeps the model, and model/undo/redo/evidence checks pass. Initial readiness takes 28,789, 25,848, and 26,177 milliseconds; post-edit settling takes 16,593, 27,165, and 15,180 milliseconds. The smoke checks enabled Apply, intended table focus, idle request/worker state, and an empty error status before editing and before capture/commit.

This observation ran at Git head `c7f29f6` with three uncommitted calculator files, then committed as `66ad055`. The observed run used a 30-second readiness deadline; the committed default is 60 seconds to allow startup variation. The two focused tests pass after that deadline adjustment, and independent review reports no material findings. Local evidence and its hashes are preserved in `/tmp/rcms-calculator-smoke-c7-dirty-proof/`; raw stdout was streamed, not saved separately. This source observation does not qualify an immutable native package or replace a passing whole Windows job.

## Controlled 48-route source run at `66ad055`

The immutable source archive for `66ad05574992b4ad2841d612dc5f1cac34bbf413` passes all **48 registered routes and 58 analysis runs** in one controlled Xvfb/xcb run. Each route runs once with a 120-second timeout; none fails or times out. Every retained analysis has status `complete`, the registered method/workflow/metric identity, a positive figure-export size, and saved/reopened evidence. All 48 journeys report a responsive event loop and no main-process R bridge. The twelve applicable binary offline PNG exports exist and match their reported sizes.

The host is Linux Mint 22.3 x86_64 with Python 3.11.9, PyQt 6.11.0 / Qt 6.11.0, R 4.6.1, and RCMetaR 0.4.1 installed from `fe69c548`. The source archive SHA-256 is `17e9b370a45060bc4d73f8f96997b6564ddc6020675e5a4f992444cdfb07504b`. Raw qualification JSON has SHA-256 `5686253b9f29402b11ac4d90e013f1da8dc8c8a0ca4db5863956c2bbcfb1e3d2`; the source/provenance manifest has SHA-256 `4d17737e01278b0220739b7509f327dcc749457febef211f3e4689d1b7a4123f`. Evidence is retained under `/tmp/rcms-worker-journeys-source48-66ad055.kiMWYR/run/`.

This verifies source-process workflow execution and persistence. It does not establish numerical agreement with an independent oracle, native packaged-app qualification, assistive-technology behavior, or observed researcher usability.

## Published-package numerical pairing

[Historical capture 36740814629](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36740814629) retains nineteen successful direct calls to the verified v0.3.1 release's embedded RCMetaR library. Its manifest SHA-256 is `6ac6cbc2d3e123b01e4cc3cf1b0be606a5f113897459797918588048f0532072`. The original fourteen outputs are unchanged; five additional cases use the exact binary OR, continuous SMD, diagnostic sensitivity, one-arm PLO, and entered continuous SMD journey inputs and settings. The four retained figure hashes/sizes pass integrity checks.

The current backend, installed from `fe69c548` and captured through immutable driver source `0a52d3b`, passes all nineteen cases at absolute/relative `1e-8`. The candidate manifest SHA-256 is `297486e091a7057b4db69da48766c0afd19d0a56e85373118aaa794b12b8287b`. The comparison report is retained locally at `/tmp/rcms-v031-reference-36740814629/current-19-comparison.json`.

`scripts/compare_v031_saved_journeys.py` also passes all five matched saved journeys, with 203 compared identity/semantic/numerical fields per evidence set: the actual unsigned macOS 15 ARM64 package at `a36c169` (report SHA-256 `96f763c07c32780444bbdea856bd3356f14a98e1c1a53e33d8dae87daf80268f`) and the controlled source run at `66ad055` (report SHA-256 `382772bcece1b98629b7ca99deac1365e26a648240170521e1fa64749ca2195d`). Both reports are retained under `/tmp/rcms-v031-reference-36740814629/`. For the source run, the aggregate JSON was copied byte-for-byte beside its saved bundles as `artifacts/worker-results.json` to match their destination prefix; the original raw evidence is unchanged. The checker reads frozen results without fitting a model. Missing saved pooled binary SE, inference degrees of freedom, and the one-arm table p-value remain explicit unavailable fields.

The historical executable smoke **fails by timeout** after 900 seconds. It stops during main-window creation, reports that `sh` is missing, and produces no completed smoke record or numerical summary. Its raw logs and validated timeout result are committed beside the API manifest. The overall capture workflow fails because of that separate executable observation. This does not establish historical GUI or human parity, or qualify a final 0.5.0 artifact.

## Saved-input and history context checks

At `f18b732`, the history formatter audit reads all 48 source journey archives
and finds no missing outcome, time point, group context, measure, or method in
their 66 saved records. Ten focused Qt tests pass with warnings treated as
errors. The formatter handles continuous `follow_up`, cumulative nested inputs,
single-group analyses, and small-study-effects test selections.

At `d4388810ee1af07a117394edee0acd97dfb7b6d6`, reopening a saved result compares
its original input identity with a detached copy of the current project selected
using the saved outcome, time point, groups, measure, and moderators. Changed or
deleted inputs produce a visible accessible notice; the frozen result remains
available. Seventeen focused fast/Qt tests pass, repository-wide configured
typing and code-health gates pass, and independent review finds no material
issues. The pure input audit recognizes all 66 records in the 48 immutable
`66ad055` journey archives and finds they match their saved project data; neither
the analysis worker module nor `rpy2` loads. The retained audit JSON SHA-256 is
`7fbe538d4bd159c79d2ac9e59b1b5aa050fd32d76d876f8796a8cd62a8cc343b`,
with the script, archive hashes, and individual record results under
`/tmp/rcms-saved-input-audit-d4388810ee1af07a117394edee0acd97dfb7b6d6/`.
Only README and changelog edits were uncommitted during that audit. These are
source and frozen-record checks, not final native package or participant evidence.

The candidate version surfaces are now 0.5.0, with the changelog marked
Unreleased. An immutable archive of `c5ebb9f6c2684fa16cf53012b52ceb2e5ac4ed33`
passes the full fast/golden suite with **1,003 passed, eight skipped**, warnings
treated as errors, and exit 0 in 170.84 seconds. The in-process backend verifies
R 4.6.1 and a fresh RCMetaR 0.5.0 source install. The archive SHA-256 is
`c28c1c533872e38e0145d8a77098a3849a832ffa7b3085062857539f3ab72935`;
the passing log SHA-256 is
`e528c04deb47b6085380a3e1afa1a46643638b0d9f8d2ca65bc89475f9b28303`.
The provenance file at `/tmp/rcms-fast-golden-c5ebb9f6-provenance.json` has SHA-256
`2e202e7791a6eb5620fa729b45bb3b049c64062348e0322429bf253fa25bdbfb`.
It also preserves an earlier failed run that mistakenly selected the older
bundled library; that attempt is not counted as a pass.

[Integration run 36751161266](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36751161266)
uses PR head `c5ebb9f` and merge checkout `52dde89`. The Windows core GUI phase
passes **554 tests with twelve skips**, and RemainingSurfaces passes **54 tests**.
The vertical-slice job fails later because its real calculator worker cannot
load `metafor`; that job had not provisioned its R dependencies. The corrected
workflow installs pinned R/dependencies and fresh source RCMetaR before running
the native calculator checks.

[Integration run 36753500352](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36753500352),
at PR head `e80ddb8`, provisions that backend successfully. Its Windows core GUI
phase passes **556 tests with ten skips**. All three native calculator checks
then pass: binary and continuous changes commit with undo available, and an
invalid diagnostic edit cancels without changing the model. The three Windows
screenshots match their recorded hashes; raw calculator evidence has SHA-256
`3a0c9adb1c95af6928f609efa557e3a03b8fa8b777f5d01026fa691c1175233a`.
The whole vertical-slice job still fails afterward: its analysis smoke expects
the settings dialog to be deleted immediately after a backend error, although
the application intentionally retains settings for retry. Progress cleanup
succeeds. The smoke must exercise that retry path, dismiss the error message,
close the settings, and verify complete teardown. The same run passes all
**22 required Windows R integration tests** with fresh RCMetaR 0.5.0.
`R CMD check` reports one NOTE for the existing unused `tiff` import, with no
check error or warning.

[Package run 36751195198](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36751195198)
starts all three native builds at `c5ebb9f`. Its Linux job fails after installing
RCMetaR 0.5.0 because the package script still expects 0.4.1. The corrected guard
reads the application version from `pyproject.toml`; its exact R check accepts the
fresh 0.5.0 library and rejects a stale 0.4.1 expectation.

The corrected [Linux run 36753636523](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36753636523)
at `e80ddb8` builds and qualifies its package on Ubuntu 24.04. Its Ubuntu 26.04
job fails before extraction: the downloaded artifact preserves `artifacts/` and
`build/` prefixes, while the consumer looks for the tarball at the download root.
A bounded read of the actual ZIP directory confirms the tarball is
`artifacts/RCMetaStudio-linux-x64.tar.gz`. Commit `1fff5b6` corrects extraction
and hash inputs in that workflow and the matching immutable-candidate checks.
The 39 packaging contracts pass with five platform-specific skips; independent
review finds no material issue. The subsequent `e777ca1` run below qualifies
the corrected paths on both Ubuntu versions. Final release artifact and observed usability qualification remain
outstanding; no stable release has been published.

## Unreleased 0.5.0 native packages at `c5ebb9f`

[Manual package run 36751195198](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36751195198)
qualifies its Windows package and the same Apple silicon ZIP on macOS 15 and 14.
The run as a whole fails on the separate Linux version guard described above.
The downloaded outer artifacts match their GitHub API digests. Actual inner
package bytes match the build evidence and both core/additional journey reports.

| Native host | Package SHA-256 | Routes / analyses | Saved v0.3.1 comparisons |
| --- | --- | --- | --- |
| Windows build 26100 x64 | `43a9301f562b5e836abd24166fa2d0eaad561fc430d10aa477e65095d2412223` | 48 / 58 | 5 cases, 203 fields, no differences |
| macOS 15.7.9 ARM64 | `bc5cb15f52d1ed7953716d30986ea55fbe9f835bf8c166ebe7533df96a1302d9` | 48 / 58 | 5 cases, 203 fields, no differences |
| macOS 14.8.9 ARM64 | Same exact ZIP as macOS 15 | 48 / 58 | 5 cases, 203 fields, no differences |

Each host's 58 analyses complete, export nonempty figures, and save/reopen.
All 48 route observations report a responsive event loop and no main-process
R bridge. Each host retains 48 project bundles. The Windows package is
362,744,132 bytes; the macOS ZIP is 423,587,921 bytes. Both contain Python 3.11.9,
PyQt 6.11.0, Qt runtime 6.11.1, R 4.6.1, and RCMetaR 0.5.0. Twelve applicable
Windows route observations independently record offline export and stop/draft
checks; those fields are not claimed for every route.

Fresh pure-data rechecks against the nineteen-case historical reference pass
all five matched cases. Their report SHA-256 values are
`b83bcbdd50d801bb2d4eff320ca8ee4211fc08ce1fc04a35dee61869c38bc995`
(Windows), `6470781670722696db4cae33c75c3305543acfcd224a48476849dea0c4289d64`
(macOS 15), and `54059810159a4f52f2fc6f21ed11115efd72b7ad0a0649cb3afcdc6965b2a01d`
(macOS 14). Downloaded packages, reports, and bundles are retained under
`/tmp/rcms-native-c5ebb9f-windows/`, `/tmp/rcms-native-c5ebb9f-macos15/`, and
`/tmp/rcms-native-c5ebb9f-macos14/`.

The macOS source provenance has a concrete defect: the manifest labels RCMetaR
0.2.0 and names its source archive `RCMetaR-0.2.0-source.tar.gz`, while that
hash-verified archive's actual DESCRIPTION and the installed backend both say
0.5.0. Its source commit is correct. Correcting the stale label requires a new
build; these bytes do not establish corrected provenance. The app has an ad-hoc
signature, so it also does not qualify Developer ID signing, notarization, or
the final trusted DMG. Commits `c5de943` and `ee237e0` replace the stale filename
with `RCMetaR-source.tar.gz`, derive its version from the actual DESCRIPTION,
and reject manifest/archive version drift after validating source input hashes.
Nested tar expansion is capped at 64 MiB and 4,096 members. The unchanged old
archive still parses as 0.5.0; its 0.2.0 manifest is rejected by the new check.
All 136 packaging contracts pass with eight platform skips, and configured
repository-wide typing passes. Independent review finds no remaining material
issue. The subsequent `003e80b` package below qualifies the corrected source-version metadata; its source URL is corrected in the subsequent source patch below.

The previous Linux build and macOS 14 evidence uploads retain portable project
figures and export-byte observations, but omit separately exported PNG files.
The upload globs now retain those PNGs alongside project bundles, including the
matching immutable-candidate and trusted macOS compatibility evidence.

Windows version 1809, platform assistive technology, and researcher usability
remain unobserved.

The later [Windows integration run 36758629130](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36758629130)
at `e777ca1` passes the complete native vertical slice: **557 GUI tests with ten
skips**, all three calculators, the analysis success/failure/cancel/close smoke,
and both startup-failure teardown checks. The failure scenario records visible
retry settings before explicit dismissal, deletion of all three surfaces, and
zero top-level widget delta. This closes the preceding smoke-test expectation
failure; the raw job log is `/tmp/rcms-ci-e777ca1-vertical.log`.

The complete integration run succeeds, including all three source/platform
lanes, packaging contracts, RemainingSurfaces, all 22 required Windows R
integration tests, and the Windows package qualification. Its historical capture
jobs are skipped because capture was not requested.

## Native lifecycle evidence at `003e80b`

[Integration run 36764683689](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36764683689)
passes the native Windows vertical slice: **557 GUI tests with ten skips**, all
three calculators, analysis lifecycle, and startup-error teardown. It also
passes all **22 required R integration tests**, the Windows package job, both
other source/platform lanes, RemainingSurfaces, and packaging contracts.
The Windows platform-neutral lane fails one timeout-runner test: `taskkill`
reports an already-terminated child during process-tree cleanup, causing exit 1
instead of timeout code 124. Its other **1,002 tests pass with eight skips**.
The overall run is therefore a failure, not a complete integration pass.

The downloaded `native-analysis-evidence` artifact is 10,935 bytes, SHA-256
`415ea821edb7b6224028e02740975ce9c1f050433367bbc802d32873b35f1e15`,
and matches its API digest and ZIP CRC. The actual Windows evidence records
visible retry settings and error message after backend failure, followed by
explicit dismissal and deletion of configuration, error, and progress surfaces.
Success, cancel, close, and failure each record zero top-level widget delta.
The retained configuration PNG is 11,262 bytes and matches its recorded SHA-256
`4589900a9aac230c1c8ff2e0122e07126b7ea394abff56521e74284e9c21cc34`.
The JSON SHA-256 is
`65417fa6bfb1de739d6980c98860900ee40cdbb6a5c5f899efbd30d5a60544b2`.
Downloaded evidence is under `/tmp/rcms-native-003e80b-analysis/`; raw logs are
`/tmp/rcms-ci-003e80b-vertical.log` and `/tmp/rcms-ci-003e80b-r-stack.log`.
These are native automated observations, not researcher sessions.

Commits `3924d2c` and `4d4a692` correct the timeout-runner race. Only recognized
already-gone child diagnostics are tolerated, and the parent must still exit
within five seconds. Unknown, access-denied, and mixed errors remain fatal.
Seven focused tests pass locally, with the actual Windows grandchild test
skipped on Linux. Configured typing and the full changed-code health gate pass;
independent review finds no material issue. Native execution of this script
change is checked by the Windows platform lane of [PR #499](https://github.com/AliSalman-et-al/rc-metastudio/pull/499).

## Platform typing follow-up at `eff8ad0`

[Run 36771929793](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36771929793)
passes **1,008 Windows fast/golden tests with eight skips**, including the actual
Windows descendant-PID and survival-marker timeout test, and all **22 Windows
R integration tests**. Both other source/platform lanes, packaging contracts,
and RemainingSurfaces pass. The native vertical slice stops before GUI tests:
extracting POSIX cleanup into a helper lost the platform narrowing required by
Windows typing, producing four unresolved `killpg`/`SIGKILL` diagnostics. This
run is not a complete integration pass.

Commits `545654d` and `22d91f3` restore the Windows branch/return before POSIX
cleanup and remove a redundant process-group existence probe. Surviving groups
still receive SIGKILL after the bounded SIGTERM wait; disappeared groups are
accepted and permission failures propagate. Seven timeout tests pass locally,
including the POSIX grandchild that ignores SIGTERM; the Windows-only test is
skipped on Linux. Independent review finds no material issue.

Explicit whole-project macOS typing also detects two nullable values in the
package accessibility harness. Commit `3f8c79f` preserves the empty-string
fallback for a null Cocoa C string and requires a positive integer native root
count without coercion. Its 28 packaged automation dispatch tests pass.
Repository-wide typing now passes for **Windows, macOS, and Linux targets**;
the full changed-code health gate passes with no new complexity violations,
cycles, or forbidden imports. These fixes change qualification code, not
application analysis or RCMetaR source. The corrected native execution gate is
tracked in the current [PR #499 checks](https://github.com/AliSalman-et-al/rc-metastudio/pull/499).

## Corrected macOS source-version provenance at `003e80b`

[Run 36764763792](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36764763792)
succeeds at source `003e80bf9ba4574e7c72b978b10922db5fa80115`: build job
`110056036954` qualifies macOS 15.7.9 ARM64; job `110065771748` qualifies the
same archive on macOS 14.8.9 ARM64. The actual inner ZIP is 423,588,631 bytes,
SHA-256 `b60accc0c0465eccbbda8fddc4c3257fbb2b06fde643a427ab6a54502a857055`.
The downloaded package and both hosts' reports bind to those bytes. All three
outer artifacts match their API digests and pass ZIP integrity/path checks.

Each host passes **48 routes and 58 analyses**: every analysis completes,
exports, and saves/reopens; every route records responsiveness and absent
main-process R. Each evidence set retains 48 projects and 58 nonempty export
PNGs. Fresh pure comparisons of their actual saved projects pass **five cases,
203 fields, and zero differences**, with eight fields explicitly unavailable.
The recheck report hashes are
`01864d701bfe82e775e975c01dc87712c229d917214db24a97151a707e4b779a`
(macOS 15) and `ead1acbdd99890d8207dd7234d712f6472dcb81b2499ca1c0deeca768e332696`
(macOS 14); each equals that host's retained report.

The archive embeds `RCMetaR-source.tar.gz`, 213,074 bytes, SHA-256
`f1442656aad770b48b11523c88e6ea1e872a531df789bdb321b92b3598e3d698`.
Its actual DESCRIPTION and direct-R manifest both identify RCMetaR 0.5.0, and
the source hash agrees. This closes the preceding stale 0.2.0 filename/version
defect for these native bytes. A separate provenance link still names
`ResearchConsultancy/rc-metastudio`, which returns HTTP 404 from the authenticated
GitHub repository API. The canonical repository is `AliSalman-et-al/rc-metastudio`;
that metadata correction does not change application or R source. The downloaded
archive retains its original link; it is not retrospectively relabelled.

Commit `21c81a8` corrects that URL in the producer, strict validator, and existing
behavior fixture. The creator and validator pass with copied actual named inputs,
138 retained PPM archives, and the R bridge extracted from the downloaded package.
All 34 named-input hashes, all dependency archive hashes, the bridge hash, and the
RCMetaR source version/hash remain consistent. The generated manifest SHA-256 is
`7e5e38d47d69a624455bc7bcd2306ec846649b33876bb7a1f80e1e1b5e90c2ff`;
proof files are under `/tmp/rcms-canonical-source-url-proof-003e80bf-21c81a8/`.
All 136 packaging contracts pass with eight platform skips, configured typing
passes, and the full changed-code health gate has no new complexity violations,
cycles, or forbidden imports. This is regenerated metadata validation using
actual inputs; it is not a newly built or natively run package.

Downloaded artifacts, source metadata, reports, and saved projects are under
`/tmp/rcms-native-003e80bf-macos15/` and `/tmp/rcms-native-003e80bf-macos14/`.
The ZIP is ad-hoc signed. It does not qualify a final Developer ID signed,
notarized, stapled DMG, platform assistive technology, or researcher sessions.

## Corrected Linux 0.5.0 package at `e777ca1`

[Linux run 36759146177](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36759146177)
succeeds at source `e777ca164a1fb43e1e0cf3b8a918e90737891b0a`: build job
`110036918567` qualifies Ubuntu 24.04; job `110044696141` qualifies that exact
archive on Ubuntu 26.04.1 x86_64. The downloaded inner TAR is 304,368,648 bytes,
SHA-256 `408e7c03261d99871396ae86134551dd630c8cd23e78e618d18fcea47ea7befe`.
The build evidence, both hosts' core/additional reports, and the Ubuntu 26 runtime
probe all bind to those exact bytes. Both outer artifacts match their API digests.

Each host passes **48 routes and 58 analysis runs**. Every run completes,
exports a figure, and saves/reopens; every route records a responsive event loop
and absent main-process R bridge. Each evidence set retains 48 project bundles.
Ubuntu 26 additionally retains all 58 nonempty export PNGs. The Ubuntu 24 upload
retains export-byte observations and portable project figures, with separate
PNG retention corrected for subsequent runs as described above.

Both pure saved-journey rechecks pass **five matched cases, 203 fields, and zero
differences**. Their report hashes are
`7c5835c1e0cbe5b7b150aedf7d174374fa19003d6973fdb724e76bee7e105a4e`
(Ubuntu 24) and `66576645e8f83a1be3675105d377f0dac58bc0ec64a993f514c3bf432aac2d12`
(Ubuntu 26); each equals its host's retained report. Evidence, downloaded bytes,
raw logs, and the machine-readable summary are retained under
`/tmp/rcms-native-e777ca1-linux/`.

The package uses Python 3.11.9, PyQt 6.11.0, Qt compiled/runtime 6.11.0/6.11.1,
R 4.6.1, and the API-mode rpy2 3.6.7 bridge. The application's Python and R source
trees match `c5ebb9f`; the subsequent changes are qualification scripts,
workflows, tests, and documentation. These are automated native package checks;
researcher usability, platform assistive technology, and the final release
artifact qualification remain outstanding.

## Integrated native package journeys at `a36c169`

[Manual package run 36714741801](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36714741801) succeeds for clean source `a36c169f19973b17e4f0da36d43b451bb2a2fecb`. Downloaded package bytes, build evidence, and core/selected journey reports agree on each archive SHA-256 below. Each listed host passes **twenty routes and 23 analysis runs**: five core routes/runs plus fifteen selected routes/eighteen runs. Every run completes and saves/reopens; every route records a responsive event loop and no main-process R bridge. The three core binary routes also confirm cancellation acknowledgement, retained settings and draft, and offline stored-figure export. These packages contain Python 3.11.9 and R 4.6.1.

| Package | Observed hosts | Archive bytes | Archive SHA-256 |
| --- | --- | ---: | --- |
| Windows x64 ZIP | Windows build 26100 | 362,734,393 | `51e3e4d387ac0eba529add5a3636e4744b7214e392796ca5460954c9e961d148` |
| Linux x64 tar.gz | Ubuntu 24.04.5 and 26.04.1 | 304,361,066 | `54d4de3fee21ebaf17644284a01fb54abbf79cbf7a48a01ef08817e06b7f7612` |
| Unsigned macOS ARM64 ZIP | macOS 15.7.9 and 14.8.9 | 423,574,294 | `324ed6252719247dad8940cea628daa6ee8cd4336747f96044e39f36db354d4c` |

Windows job `109885056856`, Ubuntu 24 job `109885056600`, Ubuntu 26 job `109887940366`, macOS 15 job `109885056877`, and macOS 14 job `109891407910` all succeed. The Ubuntu 26 and macOS 14 jobs qualify the exact archives built on Ubuntu 24 and macOS 15, respectively. The macOS verification also checks all thirteen archive-embedded qualification hashes against the downloaded ZIP. Raw evidence is retained by the workflow artifacts and locally under `/tmp/rcms-native-a36c169-{windows,linux,linux-ubuntu26,macos}/`.

This is an intermediate 0.4.1 package revision: its native Windows core GUI suite still has the five sizing failures described above. The successful route matrix does not qualify a later sizing patch, a final 0.5.0 artifact, a signed/notarized macOS DMG, Windows 10 version 1809, or human usability and assistive-technology sessions.

## Platform and human-evidence gaps

The checked-in package workflows target Windows x64 (`windows-2025`), macOS ARM64 (`macos-15`), Ubuntu 24.04 x86_64, and a separate Ubuntu 26.04 x86_64 qualification job. These are target definitions, not evidence that the current branch passed those jobs.

- Historical [Linux package run 36464538384](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36464538384) succeeded on 2026-09-28. It predates this route-specific gate and is not evidence for the current branch's five worker paths.
- Historical [Windows/macOS unsigned package run 29786816666](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/29786816666) succeeded on 2026-07-20. Its source revision predates the current worker gate and later UX work.
- [Windows package run 36621824235](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36621824235) built the branch's 0.4.1 package and passed its packaged smoke on 2026-09-29. All five core worker routes timed out while requesting methods. The selected binary and continuous meta-regression, diagnostic Reitsma, and binary small-study-effects routes completed and saved results; binary one-arm, continuous entered-effect, and diagnostic subgroup timed out. The run used commit `3ebe246`, before the missing worker snapshot imports and blocking method-failure dialog were fixed. A package rerun on the corrected revision is required; the four completed selected routes do not qualify the full Windows matrix.
- [Windows package run 36625633572](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36625633572) built the branch's 0.4.1 package at commit `863c37d`. The Windows x64 package job and packaged smoke passed, and the downloaded `worker-journey.json` and `worker-journey-selected.json` both report `passed: true` for the same archive SHA-256, `fca3f7c14fd2c6ed9b978ad179c5043cc12c3f343d61415d8962a57799acf66b`. All five core and seven selected routes completed in separate native package processes. Every route recorded a completed worker run, complete saved analysis, reopened result, responsive event loop, and no R bridge in the main process. The three core binary routes also recorded stop acknowledgement, retained settings and draft, and offline figure export. The required Windows full R stack job passed 17 tests. The evidence identifies Windows build 26100; the declared minimum Windows 10 version 1809 was not exercised. These observations qualify the twelve registered routes for this revision and runner, not every supported method, interaction, OS version, or later commit.
- [Qt6 Integration run 36635292290](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36635292290) used PR head `e6f7d8e` and a clean CI merge checkout recorded as `b7f02d1`. Its required Windows R stack and Windows x64 package jobs passed. The downloaded 0.4.1 archive SHA-256 is `12f78107c7b1f11fd76e6975b2139f1973d65d94f6c9cad7497acca3a3dd1b4b`; both worker journey JSON files report `passed: true` against that exact archive. Five core and eight selected routes completed in separate extracted-package processes, including `diagnostic.reitsma-meta-regression`. Their fourteen analysis runs report completed worker execution and saved/reopened results; `diagnostic.subgroup` produces two runs. The package evidence identifies Windows build 26100, so the declared Windows 10 version 1809 minimum remains untested. The overall integration run failed: the vertical slice stopped at repository-wide strict typing, and the remaining-surface validator rejected the single-focusable shared progress dialog. Fixes on the later branch are not qualified by this run.
- [Qt6 Integration run 36638614041](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36638614041) produced a Windows x64 0.4.1 archive with SHA-256 `bfe4569b9f669301301fc9268415f27938122544c8a604a1490cec50c112eeb4`. The downloaded archive qualification records both identify that exact SHA and report `passed: true`: five core routes and eight selected routes completed in separate extracted-package processes, with nine analysis runs across the selected routes. The required Windows R stack, Windows package, remaining-surface, source/platform, and packaging-contract jobs passed. The native vertical-slice job timed out after reaching `test_analysis_failure_safety.py`, so the overall integration gate failed. The evidence identifies Windows build 26100. This run predates the later plot-edit and subgroup-route changes, does not exercise Windows 10 version 1809, and is not a final 0.5.0 candidate.
- [Linux package run 36645635880](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36645635880) built a portable archive on Ubuntu 24.04.5 at source `ecd836c`. The downloaded `RCMetaStudio-linux-x64-evidence.json` identifies the archive SHA-256 as `1d61b827f795c563e07deaed568dc9a3e476e8243f2cf9181d07dd4009068a00`, matching the downloaded `.tar.gz`. Its packaged smoke and five core worker routes passed, as did eight selected routes in extracted-package processes. The separate Ubuntu 26.04.1 job failed on the same archive: all five core routes timed out after 120 seconds while waiting for the first worker method catalogue. The route stderr establishes that the application opened each sample and requested methods; it does not identify the worker startup error. No Ubuntu 26.04 route passed, and this compatibility failure remains open. This source revision predates plot-edit and the additional route matrix; its Ubuntu 24.04 observations do not qualify those changes or a final 0.5.0 candidate.
- [Ubuntu 26 runtime probe 36663954336](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36663954336) passed against the retained Linux archive from run 36645635880, SHA-256 `1d61b827f795c563e07deaed568dc9a3e476e8243f2cf9181d07dd4009068a00`. It loaded the private R 4.6.1 runtime, the rpy2 API bridge, and Qt's xcb platform. This probe does not load every R package or qualify an analysis journey.
- [Ubuntu 26 direct worker probe 36664778459](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36664778459) failed against that same archive. Loading RCMetaR failed because `R/library/xml2/libs/xml2.so` could not resolve `libxml2.so.2`. The failure identifies the package dependency omitted from the portable bundle; a corrected archive and full Ubuntu 26 journey rerun remain required.
- [Corrected Linux package run 36665875737](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36665875737) built source `84fbbb9` with the missing Noble XML/ICU runtime dependencies bundled. Both Ubuntu 24 and Ubuntu 26 jobs passed. The downloaded Ubuntu 26.04.1 x86_64 core and selected records report `passed: true` for archive SHA-256 `8ea8a0943924aa82c48dfed37424ea15aced644c0c1a77faee73014247aa6903`: five core and nine selected routes completed in extracted-package processes, including `binary.plot-edit`. Both runtime and direct-worker probes passed. This resolves the earlier Ubuntu 26 worker startup failure for this archive. It does not qualify the later renderer, six additional routes, or final 0.5.0 candidate; the appearance-edit implementation at this revision still reruns the model, contrary to the agreed no-refit requirement.
- [macOS package run 36645648080](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36645648080) built an unsigned Apple silicon archive on macOS 15 at source `ecd836c`, then qualified that same archive on macOS 14.8.9 ARM64. The build evidence identifies SHA-256 `209057da8db8a4fdb3afb6ffea0f9e3aad04426b20cac63f20c8b92cdbec4f83`; the downloaded macOS 14 core and selected qualification records both identify it and report `passed: true`. Five core and eight selected routes completed in native package processes. This is a preliminary revision, not signed/notarized release evidence or a final 0.5.0 qualification.
- A preliminary isolated package probe at commit `28a2f13` passed native smoke and the five core worker routes on Linux Mint 22.3 x86_64 (glibc 2.39). The package archive SHA-256 was `1274d7089f4178a7ba216ebba31f93ea16905a89148ce125c4eb6318d8cd0511`; its local evidence is `/tmp/rcms-native-probe.ncSTmM/artifacts/RCMetaStudio-linux-x64-evidence.json`. This is previous-revision Mint package evidence, not a final integrated artifact or Ubuntu runner result.
- Vendor documentation supports the declared Windows floor: [Qt 6.11 lists Windows 10 version 1809 or later](https://doc.qt.io/qt-6/windows.html), and [CRAN describes current R binaries as running on Windows 10 or later](https://www.stat.ethz.ch/CRAN/bin/windows/base/rw-FAQ.html). CRAN requires version 1903 for R’s native UTF-8 mode; earlier Windows 10 uses its native code page. These documented requirements do not replace an actual package journey on version 1809.
- No final 0.5.0 release candidate has been qualified across the required platforms. The local host has `xvfb-run`. `scripts/build-linux-package.sh` uses fixed build and evidence paths, so isolated outputs are required when protecting an existing checkout's build artifacts.
- The macOS 14 Apple Silicon compatibility job downloads the exact macOS 15-built artifact. Run 36645648080 supplied passing native package evidence for the earlier `ecd836c` revision. The final revision still needs its own package and compatibility result.
- Local Xvfb `xcb` surface probes completed at 1024×768 with 1× scale and 1280×1024 with 2× scale after supplying the host's missing Qt cursor library in an isolated temporary directory. Both reported a visible main window, the requested device-pixel ratio, and accepted close. Neither reported window exposure or keyboard focus because the Xvfb session had no window manager. These are preliminary source-process surface observations, not packaged-app, assistive-technology, or human usability qualification.
- A separate source-process AT-SPI probe used Xvfb, Metacity, a session D-Bus, and system `pyatspi` to inspect the open `amino.rcms` data grid. AT-SPI exposed the `Study data grid` table as 40 rows by 10 columns, column headers including `Include`, `Study Name`, `Year`, and `Tx A #evts`, and the selected study-name cell as `Gonzalez, Study Name: Gonzalez` with focused and selected states. This is an observed Linux accessibility API tree; no screen reader was operated, no packaged app was involved, and it does not establish Windows or macOS assistive-technology behavior.
- The automated package smoke records screen scaling and Qt accessibility metadata. No observed screen-reader, assistive-technology, researcher usability, or physical small-screen session was conducted. Do not interpret heuristic inspection or automated metadata as a human accessibility/usability session.

The [observed usability protocol](usability-qualification-protocol.md) lists the novice and experienced researcher tasks and the evidence to retain for the remaining human qualification gate.

## Inventory relationship

See [capability-parity-baseline.md](capability-parity-baseline.md) and the structured [released capability inventory](../tests/analysis_regression/baseline/released-capability-inventory.json) for the wider authority, input-family, and release-parity gaps. This document records packaged-route evidence and qualification boundaries; it does not replace that statistical inventory.

## October 1 release publication follow-up

The user explicitly authorized squash merge and v0.5.0 publication after the
outstanding observations were reported. PR #499 was squash merged as
`86ea34b64eedfbd920d498c054651e050a1e2d78`. Immutable candidate run
[36806312655](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36806312655)
passes its Windows, macOS 15/14, Ubuntu 24.04/26.04, and candidate gates with
version `0.5.0-rc.1` and trust profile `macos-trusted`. This does not establish
the outstanding researcher, assistive-technology, or Windows 1809 observations.

Signed publisher run
[36815192625](https://github.com/AliSalman-et-al/rc-metastudio/actions/runs/36815192625)
passes candidate validation, Windows carry qualification, and macOS signing
submission. Linux carry fails at the smoke command with exit 1; its redirected
stderr was not retained, so the original runner failure cannot be attributed
precisely. The run was cancelled before the pending macOS finalization.

A private copy of the previously downloaded Linux package, whose production
Python/R sources match the candidate, reproduces a relative-path problem under
Xvfb with private XDG directories. A relative sample open times out after
45 seconds without a report; the equivalent absolute invocation exits 0 in
12.2 seconds and reports an opened sample with 40 rows. The full relative smoke
replay stalls opening that sample until its 180-second cap. The Linux publisher
commands now resolve the package root to an absolute path and print captured
stdout/stderr on failure. This fixes the reproduced boundary problem; native
rerun evidence is still required to explain any additional runner failure.

Independent review also reproduced the shallow Git ancestry check rejecting
an older source commit after master advances. Candidate initialization and
trusted publication validation now fetch full ancestry before checking master.
The existing immutable candidate source, artifact hashes, stage bindings, and
release tag constraints remain intact; the workflow fixes do not rebuild or
modify its package bytes.
